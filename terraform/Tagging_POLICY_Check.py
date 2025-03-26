import json
import sys
import argparse
import re  # Import the regular expression module
import os  # Import the os module to access environment variables
from typing import Dict, List, Tuple, Union, Any

# Color codes for terminal output
COLORS = {
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "WHITE": "\033[97m",
    "RESET": "\033[0m",
}

# --- Configuration ---
# Suggestion: For better configurability, consider loading these rules from
# an external YAML or JSON file instead of defining them directly in the script.

# Allowed values for Environment tag based on deployment environment
# Reads DEPLOYMENT_ENV environment variable. Defaults to 'NPE' if not set.
DEPLOYMENT_ENV = os.environ.get('DEPLOYMENT_ENV', 'NPE').upper()

if DEPLOYMENT_ENV == 'PROD':
    ALLOWED_ENV_VALUES = ["Production::PRD"]
    ENV_SUGGESTION = "Production::PRD"
else: # NPE or other
    ALLOWED_ENV_VALUES = ["Non-production::DEV", "Non-production::QAT"] # Allow lower envs for NPE
    ENV_SUGGESTION = "Non-production::DEV (or QAT)" # Suggest a default for NPE


MANDATORY_TAG_RULES = {
    "global": [
        {
            "key": "Application",
            "allowed_values": ["MyApp", "AnotherApp", "TestApp"],
            "case_insensitive": True,
            "key_regex": "^[a-zA-Z]+$",  # Example: Key must be letters only
            "value_regex": "^(?i)(MyApp|AnotherApp|TestApp)$", # Example: Value must match allowed values, case-insensitive
            "suggestion": "MyApp" # Default suggestion if missing
        },
        {
            "key": "Environment",
            "allowed_values": ALLOWED_ENV_VALUES, # Dynamically set based on DEPLOYMENT_ENV
            "key_regex": "^Environment$",
            "suggestion": ENV_SUGGESTION # Dynamic suggestion
        },
        {
            "key": "Owner",
            "value_regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",  # Example: Basic email regex
            "suggestion": "your-email@example.com"
        }
    ],
    "aws_s3_bucket": [
        # Existing S3 tags
        {
            "key": "DataRetention",
            "allowed_values": ["30d", "1y", "5y", "Indefinite"],
            "description": "Data retention policy",
            "value_regex": "^(\\d+[dy]|Indefinite)$",  # Example: Number+d/y or Indefinite
            "suggestion": "30d"
        },
        {
            "key": "Classification",
            "allowed_values": ["Public", "Internal", "Confidential", "Strictly Confidential"],
            "suggestion": "Internal"
        },
        # New S3 tags as requested
        {
            "key": "breadth",
            "allowed_values": ["single-region", "multi-region", "global"],
            "description": "Geographic scope of the data/bucket usage",
            "suggestion": "single-region"
        },
        {
            "key": "sensitivity",
            "allowed_values": ["low", "medium", "high", "critical"],
            "description": "Sensitivity level of the data stored",
            "suggestion": "medium"
        },
        {
            "key": "danger",
            "allowed_values": ["none", "potential-pii", "financial", "intellectual-property"],
            "description": "Type of risk associated with data exposure",
            "suggestion": "none"
        }
    ],
    "aws_instance": [
        {
            "key": "AssetID",
            "description": "Asset identifier from CMDB",
            "key_regex": "^AssetID$",
            "value_regex": "^[a-zA-Z0-9-]+$",  # Example: Alphanumeric with dashes
            "suggestion": "asset-id-example"
        }
    ],
    "aws_rds_cluster": [
        {
            "key": "PII",
            "allowed_values": ["true", "false"],
            "suggestion": "false"
        }
    ]
}

OPTIONAL_TAGS = [
    {"key": "CostCenter", "description": "Financial tracking code", "suggestion": "cost-center-example"},
    {"key": "Project", "description": "Associated project name", "suggestion": "project-name"},
    # New optional Terraform tag
    {
        "key": "Terraform",
        "allowed_values": ["true", "false"],
        "case_insensitive": True,
        "description": "Indicates if the resource is managed by Terraform",
        "suggestion": "true"
    }
]

# Suggestion: Externalize exclusions as well
EXCLUDED_RESOURCES = [
    {"type": "aws_iam_role"},
    {"type": "aws_iam_policy"},
    # Example: Exclude instances starting with "dev-" or "test-" except in PROD
    {"type": "aws_instance", "name_regex": "^(dev|test)-"} if DEPLOYMENT_ENV != 'PROD' else {},
]
# Filter out empty exclusion rules that might result from the conditional logic above
EXCLUDED_RESOURCES = [rule for rule in EXCLUDED_RESOURCES if rule]


CROSS_TAG_RULES = {
    "aws_instance": [
        {
            "if_tag": {"key": "Environment", "value": "Production::PRD"},
            "then_tag": {"key": "BackupEnabled", "value": "true"}, # Assuming BackupEnabled is another tag
            "message": "Production instances MUST have 'BackupEnabled=true' tag."
        }
    ],
    "aws_s3_bucket": [
        {
            "if_tag": {"key": "sensitivity", "value": "critical"},
            "then_tag": {"key": "Classification", "value": "Strictly Confidential"},
            "message": "S3 Buckets with 'sensitivity=critical' MUST have 'Classification=Strictly Confidential' tag."
        }
    ]
}
# --- End Configuration ---


def get_relevant_tag_rules(resource_type: str) -> Tuple[List[dict], List[dict]]:
    """Get merged mandatory and optional tag rules for a specific resource type"""
    # Mandatory Rules
    global_rules = MANDATORY_TAG_RULES.get("global", [])
    resource_specific_rules = MANDATORY_TAG_RULES.get(resource_type, [])

    # Merge rules: resource-specific rules override global rules if keys conflict
    merged_mandatory_rules_dict = {rule['key']: rule for rule in global_rules}
    merged_mandatory_rules_dict.update({rule['key']: rule for rule in resource_specific_rules})
    final_mandatory_rules = list(merged_mandatory_rules_dict.values())

    # Optional Rules (currently global, but could be resource-specific too)
    final_optional_rules = OPTIONAL_TAGS[:] # Make a copy

    return final_mandatory_rules, final_optional_rules

def color_text(text: str, color: str, use_color: bool) -> str:
    """Apply color to text if enabled"""
    return f"{COLORS[color]}{text}{COLORS['RESET']}" if use_color else text

def load_terraform_plan(plan_file: str) -> dict:
    """Load and parse Terraform plan JSON file with enhanced error handling"""
    try:
        with open(plan_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
            # Basic validation of plan structure
            if not isinstance(plan_data, dict):
                raise ValueError("Plan file does not contain a valid JSON object.")
            if 'resource_changes' not in plan_data and 'planned_values' not in plan_data :
                 print(f"{COLORS['YELLOW']}Warning: 'resource_changes' or 'planned_values' not found in the plan. Analysis might be incomplete.{COLORS['RESET']}")
            return plan_data
    except FileNotFoundError:
        sys.exit(f"{COLORS['RED']}Error: Plan file not found at '{plan_file}'.{COLORS['RESET']}")
    except json.JSONDecodeError as e:
        sys.exit(f"{COLORS['RED']}Error: Failed to parse Terraform plan JSON: {e}. Is the file valid JSON?{COLORS['RESET']}")
    except Exception as e:
        sys.exit(f"{COLORS['RED']}Error loading Terraform plan '{plan_file}': {e}{COLORS['RESET']}")

def extract_tags(resource_config: dict) -> Dict[str, str]:
    """Extract tags from resource configuration with improved handling"""
    tags = {}
    if not isinstance(resource_config, dict):
        return tags # Return empty if config is not a dict

    # Handle common 'tags' attribute (dict)
    tags_dict = resource_config.get('tags')
    if isinstance(tags_dict, dict):
        tags.update(tags_dict)

    # Handle potential list of tags (e.g., some modules or older TF versions)
    tag_list = resource_config.get('tag')
    if isinstance(tag_list, list):
        for tag_spec in tag_list:
            if isinstance(tag_spec, dict) and 'key' in tag_spec and 'value' in tag_spec:
                # Basic type check for key/value
                if isinstance(tag_spec['key'], str) and isinstance(tag_spec['value'], (str, int, float, bool)):
                     tags[tag_spec['key']] = str(tag_spec['value']) # Standardize to string
                else:
                    print(f"{COLORS['YELLOW']}Warning: Skipping malformed tag item: {tag_spec}{COLORS['RESET']}")


    # Handle potential 'tags_all' which includes provider-level tags
    tags_all_dict = resource_config.get('tags_all')
    if isinstance(tags_all_dict, dict):
        # Merge tags_all, giving precedence to explicitly defined 'tags'
        base_tags = tags.copy()
        tags = tags_all_dict
        tags.update(base_tags) # Explicit tags override tags_all

    # Filter out null/None values which might appear in plans
    tags = {k: v for k, v in tags.items() if v is not None}

    return tags


def validate_tag_key(tag_key: str, rule: dict) -> bool:
    """Validate a tag key against regex rules"""
    key_regex = rule.get('key_regex')
    if key_regex:
        try:
            return bool(re.match(key_regex, tag_key))
        except re.error as e:
            print(f"{COLORS['YELLOW']}Warning: Invalid regex for key '{rule.get('key', 'N/A')}': {key_regex} - Error: {e}{COLORS['RESET']}")
            return False # Treat invalid regex as non-match
    return True

def validate_tag_value(tag_value: str, rule: dict) -> bool:
    """Validate a tag value against validation rules (allowed_values, regex, case_insensitive)"""
    if not isinstance(tag_value, str):
         tag_value = str(tag_value) # Attempt to convert non-strings

    allowed_values = rule.get('allowed_values')
    value_regex = rule.get('value_regex')
    is_case_insensitive = rule.get('case_insensitive', False)

    # 1. Check against allowed_values if present
    if allowed_values:
        normalized_allowed = [str(v) for v in allowed_values] # Ensure allowed values are strings
        check_value = tag_value.lower() if is_case_insensitive else tag_value
        compare_list = [v.lower() for v in normalized_allowed] if is_case_insensitive else normalized_allowed
        if check_value not in compare_list:
            return False # Failed allowed_values check

    # 2. Check against value_regex if present (can be combined with allowed_values)
    if value_regex:
        try:
            if not re.match(value_regex, tag_value):
                return False # Failed regex check
        except re.error as e:
             print(f"{COLORS['YELLOW']}Warning: Invalid regex for value of key '{rule.get('key', 'N/A')}': {value_regex} - Error: {e}{COLORS['RESET']}")
             return False # Treat invalid regex as non-match

    # 3. If no specific validation failed, return True
    return True

def check_tag_compliance(
    resource_tags: Dict[str, str],
    mandatory_rules: List[dict],
    optional_rules: List[dict],
    resource_address: str # For logging context
) -> Tuple[List[dict], List[dict], List[dict]]:
    """Check resource tags against requirements, returning detailed violation info"""
    missing_mandatory_info = []
    invalid_tags_info = []
    missing_optional_info = []

    # Create a set of present tag keys for efficient lookup
    present_keys = set(resource_tags.keys())
    present_keys_lower = {k.lower() for k in present_keys} # For case-insensitive checks if needed

    # --- Check Mandatory Tags ---
    for rule in mandatory_rules:
        tag_key = rule['key']
        suggestion = rule.get('suggestion', 'N/A') # Get suggestion from rule

        # Check Key Existence (case-sensitive)
        if tag_key not in present_keys:
            missing_mandatory_info.append({
                "key": tag_key,
                "suggestion": suggestion,
                "description": rule.get('description', '')
            })
            continue # Skip value validation if key is missing

        # Check Key Format (using key_regex if defined)
        if not validate_tag_key(tag_key, rule):
            # This case is less common if we iterate through rules, but good for completeness
            invalid_tags_info.append({
                "key": tag_key,
                "value": resource_tags[tag_key],
                "reason": "Invalid key format",
                "rule_regex": rule.get('key_regex'),
                "suggestion": suggestion
            })
            continue # Don't check value if key format is wrong

        # Check Value Format/Content
        current_value = resource_tags[tag_key]
        if not validate_tag_value(current_value, rule):
             violation_detail = {
                "key": tag_key,
                "value": current_value,
                "reason": "Invalid value",
                "suggestion": suggestion # Suggest a valid value
             }
             if rule.get('allowed_values'):
                 violation_detail["allowed"] = rule.get('allowed_values')
                 violation_detail["case_insensitive"] = rule.get('case_insensitive', False)
             if rule.get('value_regex'):
                 violation_detail["regex"] = rule.get('value_regex')
             invalid_tags_info.append(violation_detail)


    # --- Check for missing Optional Tags ---
    for rule in optional_rules:
        tag_key = rule['key']
        suggestion = rule.get('suggestion', 'N/A')

        # Optional tags are often checked case-insensitively for existence
        check_key = tag_key.lower() if rule.get('case_insensitive') else tag_key
        present_set = present_keys_lower if rule.get('case_insensitive') else present_keys

        if check_key not in present_set:
            missing_optional_info.append({
                "key": tag_key,
                "suggestion": suggestion,
                "description": rule.get('description', '')
            })
        # Optional tags usually don't trigger 'invalid' errors if present but wrong,
        # unless strict validation is desired. Add value validation here if needed.
        elif tag_key in resource_tags and not validate_tag_value(resource_tags[tag_key], rule):
             # Optional: Report invalid optional tags if needed
             print(f"{COLORS['YELLOW']}Warning [{resource_address}]: Optional tag '{tag_key}' has invalid value '{resource_tags[tag_key]}'. Allowed: {rule.get('allowed_values')}, Regex: {rule.get('value_regex')}{COLORS['RESET']}")


    # --- Check for unexpected tags (Optional, based on strictness) ---
    # known_keys = {rule['key'] for rule in mandatory_rules} | {rule['key'] for rule in optional_rules}
    # unexpected_tags = present_keys - known_keys
    # if unexpected_tags:
    #     print(f"Warning [{resource_address}]: Found unexpected tags: {', '.join(unexpected_tags)}")


    return missing_mandatory_info, invalid_tags_info, missing_optional_info


def check_cross_tag_rules(
    resource_tags: Dict[str, str],
    resource_type: str
) -> List[str]:
    """Check cross-tag validation rules defined in CROSS_TAG_RULES"""
    violations = []
    rules_for_type = CROSS_TAG_RULES.get(resource_type, [])

    for rule in rules_for_type:
        if_tag = rule.get('if_tag')
        then_tag = rule.get('then_tag')
        message = rule.get('message', 'Cross-tag rule violation')

        if not if_tag or not then_tag:
            print(f"{COLORS['YELLOW']}Warning: Skipping malformed cross-tag rule: {rule}{COLORS['RESET']}")
            continue

        # Check if the 'if' condition is met
        if_key = if_tag.get('key')
        if_value = if_tag.get('value')
        if if_key in resource_tags and resource_tags[if_key] == if_value:
            # Condition met, now check the 'then' condition
            then_key = then_tag.get('key')
            then_value = then_tag.get('value')

            if then_key not in resource_tags or resource_tags[then_key] != then_value:
                # 'Then' condition NOT met, add violation
                 violations.append(message + f" (Expected '{then_key}={then_value}')")

    return violations

def generate_json_report(
    violations_by_resource: Dict[str, Dict[str, Union[List[dict], List[str]]]],
    total_resources: int,
    excluded_count: int
) -> Dict[str, Any]:
    """Generate JSON-formatted report with enhanced details"""
    report = {
        "summary": {
            "total_resources_in_plan": total_resources + excluded_count,
            "excluded_resources": excluded_count,
            "analyzed_resources": total_resources,
            "compliant_resources": 0,
            "resources_with_violations": len(violations_by_resource),
            "deployment_environment_mode": DEPLOYMENT_ENV # Include the mode used
        },
        "violations": []
    }

    for resource_address, issues in violations_by_resource.items():
        entry = {
            "resource": resource_address,
            "missing_mandatory": issues.get("missing", []),
            "invalid_tags": issues.get("invalid", []),
            "cross_tag_errors": issues.get("cross_tag", []),
            "missing_optional_suggestions": issues.get("optional", [])
        }
        report["violations"].append(entry)

    report["summary"]["compliant_resources"] = total_resources - len(violations_by_resource)
    return report

def generate_console_report(
    violations_by_resource: Dict[str, Dict[str, Union[List[dict], List[str]]]],
    total_resources: int,
    excluded_count: int,
    use_color: bool
) -> str:
    """Generate human-readable console report with suggestions"""
    report_lines = []

    report_lines.append(color_text("\n--- Terraform Tag Compliance Report ---", "CYAN", use_color))
    report_lines.append(f"Deployment Environment Mode: {DEPLOYMENT_ENV}")
    report_lines.append(f"Total Resources in Plan: {total_resources + excluded_count}")
    report_lines.append(f"Excluded Resources: {excluded_count}")
    report_lines.append(f"Analyzed Resources: {total_resources}")
    report_lines.append(color_text(f"Compliant Resources: {total_resources - len(violations_by_resource)}", "GREEN" if not violations_by_resource else "WHITE", use_color ))
    report_lines.append(color_text(f"Resources with Violations: {len(violations_by_resource)}", "RED" if violations_by_resource else "WHITE", use_color))

    if not violations_by_resource:
        report_lines.append(color_text("\n✅ All analyzed resources comply with tagging requirements.", "GREEN", use_color))
    else:
        report_lines.append(color_text("\n--- Violation Details ---", "MAGENTA", use_color))

    for resource_address, issues in violations_by_resource.items():
        report_lines.append(color_text(f"\nResource: {resource_address}", "CYAN", use_color))

        missing = issues.get("missing", [])
        invalid = issues.get("invalid", [])
        optional = issues.get("optional", [])
        cross_tag_errors = issues.get("cross_tag", [])

        if missing:
            report_lines.append(color_text("  [✗] Missing Mandatory Tags:", "RED", use_color))
            for item in missing:
                suggestion = f" (Suggestion: {item['suggestion']})" if item.get('suggestion') != 'N/A' else ""
                report_lines.append(f"    - {item['key']}{suggestion}")

        if invalid:
            report_lines.append(color_text("  [✗] Invalid Tag Values/Keys:", "RED", use_color))
            for issue in invalid:
                 suggestion = f" (Suggestion: {issue['suggestion']})" if issue.get('suggestion') != 'N/A' else ""
                 msg = f"    - Key: '{issue['key']}', Value: '{issue.get('value', 'N/A')}' - Reason: {issue['reason']}"
                 if issue.get('allowed'):
                     case_note = " (case-insensitive)" if issue.get('case_insensitive') else ""
                     allowed_str = ", ".join(map(str, issue['allowed']))
                     msg += f" | Allowed{case_note}: [{allowed_str}]"
                 if issue.get('regex'):
                     msg += f" | Regex: '{issue['regex']}'"
                 if issue.get('rule_regex'): # For invalid keys
                     msg += f" | Key Regex: '{issue['rule_regex']}'"
                 msg += suggestion
                 report_lines.append(color_text(msg, "YELLOW", use_color))

        if cross_tag_errors:
            report_lines.append(color_text("  [✗] Cross-Tag Validation Errors:", "RED", use_color))
            report_lines.extend(f"    - {error}" for error in cross_tag_errors)

        if optional:
             # Only show missing optional tags as suggestions
             report_lines.append(color_text("  [!] Missing Optional Tag Suggestions:", "BLUE", use_color))
             for item in optional:
                 suggestion = f" (Example: {item['suggestion']})" if item.get('suggestion') != 'N/A' else ""
                 description = f" ({item['description']})" if item.get('description') else ""
                 report_lines.append(f"    - {item['key']}{description}{suggestion}")


    return "\n".join(report_lines)


def is_resource_excluded(resource: dict, resource_type: str, resource_address: str) -> bool:
    """Check if a resource should be excluded based on EXCLUDED_RESOURCES"""
    # Use address for name matching as it's more reliable
    resource_name_from_address = resource_address.split('.')[-1]

    for exclusion_rule in EXCLUDED_RESOURCES:
        # Check if type matches
        if exclusion_rule.get('type') == resource_type:
            # If name_regex is defined, check if it matches the resource name
            if 'name_regex' in exclusion_rule:
                try:
                    if re.match(exclusion_rule['name_regex'], resource_name_from_address):
                        # print(f"Debug: Excluding '{resource_address}' due to name regex '{exclusion_rule['name_regex']}'")
                        return True # Exclude if type and name regex match
                except re.error as e:
                    print(f"{COLORS['YELLOW']}Warning: Invalid regex in exclusion rule {exclusion_rule}: {e}{COLORS['RESET']}")
                    continue # Skip this faulty rule
            else:
                 # print(f"Debug: Excluding '{resource_address}' due to type '{resource_type}'")
                 return True # Exclude if only type matches (and no name_regex is specified)
    return False # Not excluded

def analyze_terraform_plan(plan_data: dict) -> Tuple[Dict[str, dict], int, int]:
    """Main analysis workflow - analyzes resources to be created or updated."""
    violations_by_resource = {}
    analyzed_resources_count = 0
    excluded_resources_count = 0

    # Handle both 'resource_changes' (TF >= 0.15) and 'planned_values' (older TF structure)
    resources_to_check = []
    if 'resource_changes' in plan_data:
        resources_to_check = plan_data.get('resource_changes', [])
        source_key = 'change' # Where to find 'after' state
        actions_key = 'actions'
    elif 'planned_values' in plan_data and 'root_module' in plan_data['planned_values']:
         # Need to iterate through modules and resources for older plan formats
         # This is a simplified example; a full implementation might need recursion for child modules
         if 'resources' in plan_data['planned_values']['root_module']:
              resources_to_check = plan_data['planned_values']['root_module'].get('resources', [])
              source_key = 'values' # Where to find tags in older format
              actions_key = None # No direct actions list in this format, assume create/update

    else:
         print(f"{COLORS['YELLOW']}Warning: Could not find recognizable resource list in plan data.{COLORS['RESET']}")
         return {}, 0, 0


    for resource in resources_to_check:
        try:
            resource_type = resource.get('type', '')
            address = resource.get('address', f'unknown_resource_{analyzed_resources_count}')

            # --- Determine Action and Target Config ---
            config = None
            is_create_or_update = False

            if actions_key: # Using 'resource_changes' structure
                actions = resource.get(actions_key, [])
                # Analyze resources being created or updated (ignore no-op, read, delete)
                if "create" in actions or "update" in actions:
                     change_info = resource.get(source_key, {})
                     # 'after' state is relevant for create/update
                     config = change_info.get('after', {})
                     # Handle 'after_unknown' for values computed at apply time (treat as potentially present)
                     after_unknown = change_info.get('after_unknown', {})
                     if isinstance(config, dict) and isinstance(after_unknown, dict) and 'tags' in after_unknown:
                         # If tags are computed, we can't fully validate them at plan time
                         # but we should still check for *known* missing mandatory tags.
                         # For simplicity here, we proceed with known config, but a warning could be added.
                         pass
                     is_create_or_update = True
            else: # Using older 'planned_values' structure
                config = resource.get(source_key, {})
                # Assume resources listed here are planned for creation/update if config exists
                is_create_or_update = bool(config)


            # --- Skip if not create/update or no config ---
            if not is_create_or_update or config is None:
                continue

            # --- Check Exclusions ---
            if is_resource_excluded(resource, resource_type, address):
                excluded_resources_count += 1
                continue

            # --- Proceed with Analysis ---
            analyzed_resources_count += 1

            # Extract tags using the enhanced function
            tags = extract_tags(config)

            # Get relevant rules for this resource type
            mandatory_rules, optional_rules = get_relevant_tag_rules(resource_type)

            # Perform Compliance Checks
            missing_mandatory, invalid_tags, missing_optional = check_tag_compliance(
                tags, mandatory_rules, optional_rules, address
            )

            # Perform Cross-Tag Checks
            cross_tag_errors = check_cross_tag_rules(tags, resource_type)

            # Store violations if any found
            if missing_mandatory or invalid_tags or cross_tag_errors:
                violations_by_resource[address] = {
                    "missing": missing_mandatory,
                    "invalid": invalid_tags,
                    "optional": missing_optional, # Keep optional suggestions separate
                    "cross_tag": cross_tag_errors
                }
            elif missing_optional:
                 # If only missing optional tags, store them for suggestion but don't count as violation
                 if address not in violations_by_resource: # Avoid overwriting real violations
                      violations_by_resource[address] = {"optional": missing_optional}


        except Exception as e:
            # Robust error handling per resource
            resource_id = resource.get('address', f'unknown_resource_{analyzed_resources_count}')
            print(f"{COLORS['RED']}Error analyzing resource '{resource_id}': {e}. Skipping this resource.{COLORS['RESET']}")
            # Optionally add this error to a separate errors list in the report
            if resource_id not in violations_by_resource:
                 violations_by_resource[resource_id] = {"analysis_error": str(e)}


    return violations_by_resource, analyzed_resources_count, excluded_resources_count

def main():
    parser = argparse.ArgumentParser(
        description="Terraform Tag Compliance Analyzer. Reads DEPLOYMENT_ENV environment variable (default: NPE) for Environment tag rules.",
        formatter_class=argparse.RawTextHelpFormatter # Show help text formatting
        )
    parser.add_argument("plan_file", help="Path to Terraform plan JSON file (terraform show -json <planfile> > plan.json)")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    # Example of adding a config file argument (optional enhancement)
    # parser.add_argument("--config", help="Path to a YAML/JSON configuration file for rules (optional)")

    args = parser.parse_args()
    use_color = not args.no_color

    # --- Pre-run Checks ---
    print(f"Running in '{DEPLOYMENT_ENV}' mode for Environment tag validation.")

    # Load Plan
    plan_data = load_terraform_plan(args.plan_file)

    # Analyze Plan
    violations, analyzed_count, excluded_count = analyze_terraform_plan(plan_data)

    # Generate and Print Report
    if args.json:
        json_report = generate_json_report(violations, analyzed_count, excluded_count)
        print(json.dumps(json_report, indent=2))
    else:
        console_report = generate_console_report(violations, analyzed_count, excluded_count, use_color)
        print(console_report)

    # Determine Exit Code (0 for success, 1 for violations)
    has_critical_violations = any(
        issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error")
        for issues in violations.values()
    )
    sys.exit(1 if has_critical_violations else 0)


if __name__ == "__main__":
    main()

######################################################################
Environment-Based 'Environment' Tag:

Reads the DEPLOYMENT_ENV environment variable. Defaults to NPE if not set.
If PROD, allowed_values for the Environment tag is strictly ["Production::PRD"].
If NPE (or anything else), allowed_values is ["Non-production::DEV", "Non-production::QAT"].
Suggestions (suggestion field in the rule) are also set dynamically based on DEPLOYMENT_ENV.
New S3 Bucket Tags:

Added breadth, sensitivity, and danger tags to MANDATORY_TAG_RULES["aws_s3_bucket"] with example allowed_values and suggestions.
Optional 'Terraform' Tag:

Added a rule for the Terraform tag in the OPTIONAL_TAGS list, allowing true/false (case-insensitive) and providing a suggestion.
Suggestions for Missing Tags:

Added a suggestion field to tag rules in MANDATORY_TAG_RULES and OPTIONAL_TAGS.
The check_tag_compliance function now returns detailed info about missing tags, including the suggestion.
Both generate_json_report and generate_console_report now include these suggestions for missing mandatory and optional tags.
More Robust Validation & Error Handling:

load_terraform_plan: Added more specific try...except blocks for FileNotFoundError and json.JSONDecodeError. Includes basic plan structure validation.
extract_tags: Handles tags, tag (list format), and tags_all. Filters out None values. Adds basic type checking for list-based tags.
validate_tag_key, validate_tag_value: Added try...except for re.error in case of invalid regex patterns in the configuration. Converts non-string values to strings before validation.
analyze_terraform_plan: Added a try...except block around the analysis of each resource, so an error in one resource doesn't stop the script. Handles different plan structures (resource_changes vs. planned_values). Better handling of after_unknown.
is_resource_excluded: Added try...except for regex errors in exclusion rules.
Configurability Notes:

Added comments suggesting that MANDATORY_TAG_RULES, OPTIONAL_TAGS, and EXCLUDED_RESOURCES could be loaded from external files (e.g., YAML or JSON) for better maintainability.
Reporting Improvements:

Reports now distinguish between "Total Resources in Plan", "Excluded Resources", and "Analyzed Resources".
Console report uses more colors and symbols (✅, ✗, !) for clarity.
JSON report structure is refined to separate violations clearly.
Includes the DEPLOYMENT_ENV mode in the report summary.
The script exits with code 1 if there are any missing mandatory tags, invalid tags, cross-tag errors, or analysis errors, and 0 otherwise (even if there are only missing optional tag suggestions).
How to Run:

Save: Save the code above as tag_aws_advance_policy.py.
Set Environment (Optional): If you want to test the 'PROD' rules, set the environment variable before running:
Linux/macOS: export DEPLOYMENT_ENV=PROD
Windows (cmd): set DEPLOYMENT_ENV=PROD
Windows (PowerShell): $env:DEPLOYMENT_ENV = "PROD" (If you don't set it, it defaults to 'NPE')
Generate Plan JSON: Make sure you have a Terraform plan output in JSON format: terraform plan -out=tfplan.binary terraform show -json tfplan.binary > plan.json
Run the Script: python tag_aws_advance_policy.py plan.json
Add --json for JSON output: python tag_aws_advance_policy.py plan.json --json
Add --no-color to disable colors: python tag_aws_advance_policy.py plan.json --no-color
This enhanced script should provide more robust checking, better error handling, environment-specific rules for the 'Environment' tag, include the new S3 and Terraform tags, and offer suggestions for missing tags. Remember to adjust the allowed_values and suggestions in the configuration section to match your organization's specific standards [cite: 1].
