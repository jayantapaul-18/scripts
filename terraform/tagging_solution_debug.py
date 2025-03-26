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
print(f"DEBUG: Running in '{DEPLOYMENT_ENV}' mode.") # DEBUG

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
print(f"DEBUG: Exclusion rules: {EXCLUDED_RESOURCES}") # DEBUG


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

    # print(f"DEBUG: Rules for {resource_type}: Mandatory={final_mandatory_rules}, Optional={final_optional_rules}") # DEBUG (can be noisy)
    return final_mandatory_rules, final_optional_rules

def color_text(text: str, color: str, use_color: bool) -> str:
    """Apply color to text if enabled"""
    # Simple check if running in a non-TTY environment where color might not be supported well
    if not sys.stdout.isatty():
        use_color = False
    return f"{COLORS[color]}{text}{COLORS['RESET']}" if use_color else text


def load_terraform_plan(plan_file: str) -> dict:
    """Load and parse Terraform plan JSON file with enhanced error handling"""
    print(f"DEBUG: Attempting to load plan file: {plan_file}") # DEBUG
    try:
        with open(plan_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
            print(f"DEBUG: Plan file loaded successfully.") # DEBUG
            # Basic validation of plan structure
            if not isinstance(plan_data, dict):
                 print(f"DEBUG: Plan file is not a JSON object.") # DEBUG
                 raise ValueError("Plan file does not contain a valid JSON object.")
            if 'resource_changes' not in plan_data and 'planned_values' not in plan_data :
                 print(f"{color_text('Warning:', 'YELLOW', True)} 'resource_changes' or 'planned_values' not found at the top level of the plan. Analysis might be incomplete or fail.") # Warning colorized
            return plan_data
    except FileNotFoundError:
        print(f"DEBUG: FileNotFoundError for {plan_file}") # DEBUG
        sys.exit(f"{color_text('Error:', 'RED', True)} Plan file not found at '{plan_file}'.")
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSONDecodeError: {e}") # DEBUG
        sys.exit(f"{color_text('Error:', 'RED', True)} Failed to parse Terraform plan JSON: {e}. Is the file valid JSON?")
    except Exception as e:
        print(f"DEBUG: Generic error loading plan: {e}") # DEBUG
        sys.exit(f"{color_text('Error:', 'RED', True)} Error loading Terraform plan '{plan_file}': {e}")

def extract_tags(resource_config: dict) -> Dict[str, str]:
    """Extract tags from resource configuration with improved handling"""
    tags = {}
    if not isinstance(resource_config, dict):
        # print(f"DEBUG: extract_tags received non-dict config: {type(resource_config)}") # DEBUG
        return tags # Return empty if config is not a dict

    # Handle common 'tags' attribute (dict)
    tags_dict = resource_config.get('tags')
    if isinstance(tags_dict, dict):
        # print(f"DEBUG: Found 'tags' dict: {tags_dict}") # DEBUG
        tags.update(tags_dict)

    # Handle potential list of tags (e.g., some modules or older TF versions)
    tag_list = resource_config.get('tag')
    if isinstance(tag_list, list):
        # print(f"DEBUG: Found 'tag' list: {tag_list}") # DEBUG
        for tag_spec in tag_list:
            if isinstance(tag_spec, dict) and 'key' in tag_spec and 'value' in tag_spec:
                # Basic type check for key/value
                if isinstance(tag_spec['key'], str) and isinstance(tag_spec['value'], (str, int, float, bool)):
                     tags[tag_spec['key']] = str(tag_spec['value']) # Standardize to string
                else:
                    print(f"{color_text('Warning:', 'YELLOW', True)} Skipping malformed tag item in list: {tag_spec}")


    # Handle potential 'tags_all' which includes provider-level tags
    tags_all_dict = resource_config.get('tags_all')
    if isinstance(tags_all_dict, dict):
        # print(f"DEBUG: Found 'tags_all' dict: {tags_all_dict}") # DEBUG
        # Merge tags_all, giving precedence to explicitly defined 'tags'
        base_tags = tags.copy()
        tags = tags_all_dict
        tags.update(base_tags) # Explicit tags override tags_all

    # Filter out null/None values which might appear in plans
    tags = {k: v for k, v in tags.items() if v is not None}
    # print(f"DEBUG: Final extracted tags: {tags}") # DEBUG
    return tags


def validate_tag_key(tag_key: str, rule: dict) -> bool:
    """Validate a tag key against regex rules"""
    key_regex = rule.get('key_regex')
    if key_regex:
        try:
            match = re.match(key_regex, tag_key)
            # print(f"DEBUG: Validating key '{tag_key}' against regex '{key_regex}'. Match: {bool(match)}") # DEBUG
            return bool(match)
        except re.error as e:
            print(f"{color_text('Warning:', 'YELLOW', True)} Invalid regex for key '{rule.get('key', 'N/A')}': {key_regex} - Error: {e}")
            return False # Treat invalid regex as non-match
    return True

def validate_tag_value(tag_value: str, rule: dict) -> bool:
    """Validate a tag value against validation rules (allowed_values, regex, case_insensitive)"""
    if not isinstance(tag_value, str):
         tag_value = str(tag_value) # Attempt to convert non-strings

    allowed_values = rule.get('allowed_values')
    value_regex = rule.get('value_regex')
    is_case_insensitive = rule.get('case_insensitive', False)
    key = rule.get('key', 'N/A') # For debug messages

    # 1. Check against allowed_values if present
    if allowed_values:
        normalized_allowed = [str(v) for v in allowed_values] # Ensure allowed values are strings
        check_value = tag_value.lower() if is_case_insensitive else tag_value
        compare_list = [v.lower() for v in normalized_allowed] if is_case_insensitive else normalized_allowed
        # print(f"DEBUG: Validating value '{tag_value}' for key '{key}'. Checking against allowed: {compare_list}. Case Insensitive: {is_case_insensitive}. Match: {check_value in compare_list}") # DEBUG
        if check_value not in compare_list:
            return False # Failed allowed_values check

    # 2. Check against value_regex if present (can be combined with allowed_values)
    if value_regex:
        try:
            match = re.match(value_regex, tag_value)
            # print(f"DEBUG: Validating value '{tag_value}' for key '{key}' against regex '{value_regex}'. Match: {bool(match)}") # DEBUG
            if not match:
                return False # Failed regex check
        except re.error as e:
             print(f"{color_text('Warning:', 'YELLOW', True)} Invalid regex for value of key '{key}': {value_regex} - Error: {e}")
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

    # print(f"DEBUG [{resource_address}]: Checking compliance. Present keys: {present_keys}") # DEBUG

    # --- Check Mandatory Tags ---
    for rule in mandatory_rules:
        tag_key = rule['key']
        suggestion = rule.get('suggestion', 'N/A') # Get suggestion from rule

        # Check Key Existence (case-sensitive)
        if tag_key not in present_keys:
            # print(f"DEBUG [{resource_address}]: Missing mandatory tag '{tag_key}'") # DEBUG
            missing_mandatory_info.append({
                "key": tag_key,
                "suggestion": suggestion,
                "description": rule.get('description', '')
            })
            continue # Skip value validation if key is missing

        # Check Key Format (using key_regex if defined) - Less common if iterating rules, but for completeness
        if not validate_tag_key(tag_key, rule):
            print(f"DEBUG [{resource_address}]: Invalid key format for '{tag_key}'") # DEBUG
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
             # print(f"DEBUG [{resource_address}]: Invalid value '{current_value}' for tag '{tag_key}'") # DEBUG
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
        is_case_insensitive = rule.get('case_insensitive', False) # Check rule specific setting
        check_key = tag_key.lower() if is_case_insensitive else tag_key
        present_set = present_keys_lower if is_case_insensitive else present_keys

        if check_key not in present_set:
            # print(f"DEBUG [{resource_address}]: Missing optional tag '{tag_key}' (Checking: '{check_key}' in {present_set})") # DEBUG
            missing_optional_info.append({
                "key": tag_key,
                "suggestion": suggestion,
                "description": rule.get('description', '')
            })
        # Optional: Validate value of optional tags if present
        elif tag_key in resource_tags and not validate_tag_value(resource_tags[tag_key], rule):
             print(f"{color_text('Info:', 'BLUE', True)} [{resource_address}]: Optional tag '{tag_key}' present but has invalid value '{resource_tags[tag_key]}'. Allowed: {rule.get('allowed_values')}, Regex: {rule.get('value_regex')}")


    # print(f"DEBUG [{resource_address}]: Compliance check results: MissingMandatory={len(missing_mandatory_info)}, Invalid={len(invalid_tags_info)}, MissingOptional={len(missing_optional_info)}") # DEBUG
    return missing_mandatory_info, invalid_tags_info, missing_optional_info


def check_cross_tag_rules(
    resource_tags: Dict[str, str],
    resource_type: str
) -> List[str]:
    """Check cross-tag validation rules defined in CROSS_TAG_RULES"""
    violations = []
    rules_for_type = CROSS_TAG_RULES.get(resource_type, [])

    # print(f"DEBUG: Checking cross-tag rules for type '{resource_type}'. Rules count: {len(rules_for_type)}") # DEBUG

    for rule in rules_for_type:
        if_tag = rule.get('if_tag')
        then_tag = rule.get('then_tag')
        message = rule.get('message', 'Cross-tag rule violation')

        if not if_tag or not then_tag:
            print(f"{color_text('Warning:', 'YELLOW', True)} Skipping malformed cross-tag rule: {rule}")
            continue

        # Check if the 'if' condition is met
        if_key = if_tag.get('key')
        if_value = if_tag.get('value')
        if if_key in resource_tags and resource_tags[if_key] == if_value:
            # print(f"DEBUG: Cross-tag 'IF' condition met for rule: {rule}") # DEBUG
            # Condition met, now check the 'then' condition
            then_key = then_tag.get('key')
            then_value = then_tag.get('value')

            if then_key not in resource_tags or resource_tags[then_key] != then_value:
                # 'Then' condition NOT met, add violation
                 print(f"DEBUG: Cross-tag 'THEN' condition FAILED for rule: {rule}. Expected '{then_key}={then_value}', Got: {resource_tags.get(then_key)}") # DEBUG
                 violations.append(message + f" (Expected '{then_key}={then_value}')")
            # else:
                # print(f"DEBUG: Cross-tag 'THEN' condition PASSED for rule: {rule}") # DEBUG

    # print(f"DEBUG: Cross-tag check violations found: {len(violations)}") # DEBUG
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
            "resources_with_violations": len([res for res, issues in violations_by_resource.items() if issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error")]), # Count only actual violations/errors
            "deployment_environment_mode": DEPLOYMENT_ENV # Include the mode used
        },
        "violations": []
    }

    for resource_address, issues in violations_by_resource.items():
        # Only include resources with actual violations or errors in the details list
        if issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error"):
            entry = {
                "resource": resource_address,
                "missing_mandatory": issues.get("missing", []),
                "invalid_tags": issues.get("invalid", []),
                "cross_tag_errors": issues.get("cross_tag", []),
                "analysis_error": issues.get("analysis_error"), # Include analysis errors if any
                # Optional: Also include optional suggestions even for violating resources
                "missing_optional_suggestions": issues.get("optional", [])
            }
            # Clean up null analysis_error if not present
            if not entry["analysis_error"]:
                 del entry["analysis_error"]
            report["violations"].append(entry)

    report["summary"]["compliant_resources"] = total_resources - report["summary"]["resources_with_violations"]
    return report

def generate_console_report(
    violations_by_resource: Dict[str, Dict[str, Union[List[dict], List[str]]]],
    total_resources: int,
    excluded_count: int,
    use_color: bool
) -> str:
    """Generate human-readable console report with suggestions"""
    report_lines = []
    critical_violation_count = 0

    # Count critical violations first
    for issues in violations_by_resource.values():
         if issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error"):
              critical_violation_count += 1

    report_lines.append(color_text("\n--- Terraform Tag Compliance Report ---", "CYAN", use_color))
    report_lines.append(f"Deployment Environment Mode: {DEPLOYMENT_ENV}")
    report_lines.append(f"Total Resources in Plan: {total_resources + excluded_count}")
    report_lines.append(f"Excluded Resources: {excluded_count}")
    report_lines.append(f"Analyzed Resources: {total_resources}")
    report_lines.append(color_text(f"Compliant Resources: {total_resources - critical_violation_count}", "GREEN" if critical_violation_count == 0 else "WHITE", use_color ))
    report_lines.append(color_text(f"Resources with Violations: {critical_violation_count}", "RED" if critical_violation_count > 0 else "WHITE", use_color))

    if critical_violation_count == 0 and total_resources > 0 :
        report_lines.append(color_text("\n✅ All analyzed resources comply with critical tagging requirements.", "GREEN", use_color))
    elif total_resources == 0 and excluded_count == 0:
         report_lines.append(color_text("\n⚠️ No resources found to analyze in the plan.", "YELLOW", use_color))
    elif critical_violation_count > 0:
        report_lines.append(color_text("\n--- Violation Details ---", "MAGENTA", use_color))

    # Iterate and print details for violating resources
    for resource_address, issues in violations_by_resource.items():
        # Only print details if there are actual violations/errors
        has_critical_issue = issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error")
        if not has_critical_issue:
            continue

        report_lines.append(color_text(f"\nResource: {resource_address}", "CYAN", use_color))

        missing = issues.get("missing", [])
        invalid = issues.get("invalid", [])
        # optional = issues.get("optional", []) # Keep optional separate maybe
        cross_tag_errors = issues.get("cross_tag", [])
        analysis_error = issues.get("analysis_error")

        if analysis_error:
            report_lines.append(color_text("  [✗] Analysis Error:", "RED", use_color))
            report_lines.append(f"    - {analysis_error}")

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

    # Optionally, list resources with only optional suggestions at the end
    optional_only_resources = {res: issues['optional'] for res, issues in violations_by_resource.items() if issues.get("optional") and not (issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error"))}
    if optional_only_resources:
         report_lines.append(color_text("\n--- Optional Tag Suggestions ---", "MAGENTA", use_color))
         for resource_address, optional_list in optional_only_resources.items():
             report_lines.append(color_text(f"\nResource: {resource_address}", "CYAN", use_color))
             report_lines.append(color_text("  [!] Missing Optional Tag Suggestions:", "BLUE", use_color))
             for item in optional_list:
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
        type_match = exclusion_rule.get('type') == resource_type
        # print(f"DEBUG: Checking exclusion for '{resource_address}' against rule {exclusion_rule}. Type match: {type_match}") # DEBUG

        if type_match:
            name_regex = exclusion_rule.get('name_regex')
            # If name_regex is defined, check if it matches the resource name
            if name_regex:
                try:
                    name_match = bool(re.match(name_regex, resource_name_from_address))
                    # print(f"DEBUG: Checking name '{resource_name_from_address}' against regex '{name_regex}'. Match: {name_match}") # DEBUG
                    if name_match:
                        print(f"DEBUG: Excluding '{resource_address}' due to type '{resource_type}' and name regex '{name_regex}'") # DEBUG
                        return True # Exclude if type and name regex match
                except re.error as e:
                    print(f"{color_text('Warning:', 'YELLOW', True)} Invalid regex in exclusion rule {exclusion_rule}: {e}")
                    continue # Skip this faulty rule
            else:
                 # Exclude if only type matches (and no name_regex is specified)
                 print(f"DEBUG: Excluding '{resource_address}' due to type '{resource_type}' (no name regex specified)") # DEBUG
                 return True
    # print(f"DEBUG: Not excluding '{resource_address}'") # DEBUG
    return False # Not excluded

def analyze_terraform_plan(plan_data: dict) -> Tuple[Dict[str, dict], int, int]:
    """Main analysis workflow - analyzes resources to be created or updated."""
    violations_by_resource = {}
    analyzed_resources_count = 0
    excluded_resources_count = 0

    resources_to_check = []
    plan_format_used = None

    # Handle both 'resource_changes' (TF >= 0.15) and 'planned_values' (older TF structure)
    if 'resource_changes' in plan_data:
        resources_to_check = plan_data.get('resource_changes', [])
        source_key = 'change' # Where to find 'after' state
        actions_key = 'actions'
        plan_format_used = "resource_changes"
    elif 'planned_values' in plan_data and 'root_module' in plan_data['planned_values']:
         # Need to iterate through modules and resources for older plan formats
         if 'resources' in plan_data['planned_values']['root_module']:
              resources_to_check = plan_data['planned_values']['root_module'].get('resources', [])
              source_key = 'values' # Where to find tags in older format
              actions_key = None # No direct actions list in this format, assume create/update
              plan_format_used = "planned_values"
         # Add handling for child_modules if necessary (more complex)

    print(f"DEBUG: Using plan format: {plan_format_used}. Found {len(resources_to_check)} potential resource items.") # DEBUG

    if not resources_to_check:
         print(f"{color_text('Warning:', 'YELLOW', True)} Could not find recognizable resource list in plan data under 'resource_changes' or 'planned_values.root_module.resources'.")
         return {}, 0, 0


    for index, resource in enumerate(resources_to_check):
        resource_id_for_log = f"item {index}" # Default log ID
        try:
            resource_type = resource.get('type', '')
            address = resource.get('address', f'unknown_resource_{index}')
            resource_id_for_log = address # Use address if available

            # print(f"DEBUG: Processing resource {index}: Type='{resource_type}', Address='{address}'") # DEBUG

            # --- Determine Action and Target Config ---
            config = None
            is_create_or_update = False

            if plan_format_used == "resource_changes":
                actions = resource.get(actions_key, [])
                # Analyze resources being created or updated (ignore no-op, read, delete)
                # print(f"DEBUG [{address}]: Actions = {actions}") # DEBUG
                if "create" in actions or "update" in actions:
                     change_info = resource.get(source_key, {})
                     # 'after' state is relevant for create/update
                     config = change_info.get('after', {})
                     # Handle 'after_unknown' for values computed at apply time (treat as potentially present)
                     after_unknown = change_info.get('after_unknown', {})
                     if isinstance(config, dict) and isinstance(after_unknown, dict) and after_unknown.get('tags_all') is True :
                          # If all tags are computed, we can't validate them at plan time.
                          print(f"{color_text('Info:', 'BLUE', True)} [{address}]: Tags will be computed at apply time ('tags_all' is unknown). Skipping tag validation for this resource.")
                          # Treat as compliant for now, or add specific handling
                          analyzed_resources_count += 1 # Count it as analyzed but skipped
                          continue # Skip further checks for this resource

                     is_create_or_update = True
                # else:
                     # print(f"DEBUG [{address}]: Skipping resource due to actions (not create/update).") # DEBUG

            elif plan_format_used == "planned_values":
                config = resource.get(source_key, {})
                # Assume resources listed here are planned for creation/update if config exists
                is_create_or_update = bool(config)
                # print(f"DEBUG [{address}]: Planned values format. Config exists: {is_create_or_update}") # DEBUG


            # --- Skip if not create/update or no config ---
            if not is_create_or_update or config is None:
                # print(f"DEBUG [{address}]: Skipping - Not create/update or config is None.") # DEBUG
                continue

            # --- Check Exclusions ---
            if is_resource_excluded(resource, resource_type, address):
                excluded_resources_count += 1
                # print(f"DEBUG [{address}]: Resource excluded.") # DEBUG
                continue

            # --- Proceed with Analysis ---
            analyzed_resources_count += 1
            # print(f"DEBUG [{address}]: Analyzing resource. Total analyzed so far: {analyzed_resources_count}") # DEBUG

            # Extract tags using the enhanced function
            # print(f"DEBUG [{address}]: Extracting tags from config: {config}") # DEBUG (can be very verbose)
            tags = extract_tags(config)
            print(f"DEBUG [{address}]: Extracted tags: {tags}") # DEBUG

            # Get relevant rules for this resource type
            mandatory_rules, optional_rules = get_relevant_tag_rules(resource_type)

            # Perform Compliance Checks
            missing_mandatory, invalid_tags, missing_optional = check_tag_compliance(
                tags, mandatory_rules, optional_rules, address
            )

            # Perform Cross-Tag Checks
            cross_tag_errors = check_cross_tag_rules(tags, resource_type)

            # Store violations if any found
            # Initialize entry if needed
            if address not in violations_by_resource:
                violations_by_resource[address] = {}

            if missing_mandatory or invalid_tags or cross_tag_errors:
                 print(f"DEBUG [{address}]: VIOLATIONS DETECTED: Missing={len(missing_mandatory)}, Invalid={len(invalid_tags)}, CrossTag={len(cross_tag_errors)}") # DEBUG
                 violations_by_resource[address].update({
                    "missing": missing_mandatory,
                    "invalid": invalid_tags,
                    "cross_tag": cross_tag_errors
                 })
                 # Also store optional suggestions for violating resources
                 if missing_optional:
                     violations_by_resource[address]["optional"] = missing_optional

            elif missing_optional:
                 # Only missing optional tags
                 print(f"DEBUG [{address}]: Only missing optional tags detected.") # DEBUG
                 violations_by_resource[address]["optional"] = missing_optional


        except Exception as e:
            # Robust error handling per resource
            print(f"{color_text('Error:', 'RED', True)} Analyzing resource '{resource_id_for_log}': {e}. Skipping this resource.")
            # Optionally add this error to a separate errors list in the report
            if resource_id_for_log not in violations_by_resource:
                 violations_by_resource[resource_id_for_log] = {}
            violations_by_resource[resource_id_for_log]["analysis_error"] = str(e)


    print(f"DEBUG: Analysis complete. Total analyzed: {analyzed_resources_count}, Excluded: {excluded_resources_count}, Violations found in {len(violations_by_resource)} resources.") # DEBUG
    return violations_by_resource, analyzed_resources_count, excluded_resources_count

def main():
    parser = argparse.ArgumentParser(
        description="Terraform Tag Compliance Analyzer. Reads DEPLOYMENT_ENV environment variable (default: NPE) for Environment tag rules.",
        formatter_class=argparse.RawTextHelpFormatter # Show help text formatting
        )
    parser.add_argument("plan_file", help="Path to Terraform plan JSON file (terraform show -json <planfile> > plan.json)")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--debug", action="store_true", help="Enable extra debug output (can be very verbose)") # Added debug flag


    args = parser.parse_args()
    use_color = not args.no_color
    enable_verbose_debug = args.debug # Control verbose debug messages

    # --- Pre-run Checks ---
    # Note: Some debug messages are always on, controlled by the flag later where needed.

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
    print(f"DEBUG: Exiting. Critical violations found: {has_critical_violations}") # DEBUG
    sys.exit(1 if has_critical_violations else 0)


if __name__ == "__main__":
    main()
