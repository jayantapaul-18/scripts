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
# Allowed values for Environment tag based on deployment environment
DEPLOYMENT_ENV = os.environ.get('DEPLOYMENT_ENV', 'NPE').upper()
# print(f"DEBUG: Running in '{DEPLOYMENT_ENV}' mode.") # DEBUG (Keep if useful)

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
            "key_regex": "^[a-zA-Z]+$",
            "value_regex": "^(?i)(MyApp|AnotherApp|TestApp)$",
            "suggestion": "MyApp"
        },
        {
            "key": "Environment",
            "allowed_values": ALLOWED_ENV_VALUES,
            "key_regex": "^Environment$",
            "suggestion": ENV_SUGGESTION
        },
        {
            "key": "Owner",
            "value_regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "suggestion": "your-email@example.com"
        }
    ],
    "aws_s3_bucket": [
        {
            "key": "DataRetention",
            "allowed_values": ["30d", "1y", "5y", "Indefinite"],
            "description": "Data retention policy",
            "value_regex": "^(\\d+[dy]|Indefinite)$",
            "suggestion": "30d"
        },
        {
            "key": "Classification",
            "allowed_values": ["Public", "Internal", "Confidential", "Strictly Confidential"],
            "suggestion": "Internal"
        },
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
            "value_regex": "^[a-zA-Z0-9-]+$",
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
    {
        "key": "Terraform",
        "allowed_values": ["true", "false"],
        "case_insensitive": True,
        "description": "Indicates if the resource is managed by Terraform",
        "suggestion": "true"
    }
]

EXCLUDED_RESOURCES = [
    {"type": "aws_iam_role"},
    {"type": "aws_iam_policy"},
    {"type": "aws_instance", "name_regex": "^(dev|test)-"} if DEPLOYMENT_ENV != 'PROD' else {},
]
EXCLUDED_RESOURCES = [rule for rule in EXCLUDED_RESOURCES if rule]
# print(f"DEBUG: Exclusion rules: {EXCLUDED_RESOURCES}") # DEBUG (Keep if useful)


CROSS_TAG_RULES = {
    "aws_instance": [
        {
            "if_tag": {"key": "Environment", "value": "Production::PRD"},
            "then_tag": {"key": "BackupEnabled", "value": "true"},
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


# --- Helper Functions (get_relevant_tag_rules, color_text, load_terraform_plan, extract_tags, validation funcs...) ---
# (Keep the helper functions from the previous version, including their debug prints if desired)
# ... (Previous helper functions omitted for brevity, assume they are here) ...

def get_relevant_tag_rules(resource_type: str) -> Tuple[List[dict], List[dict]]:
    """Get merged mandatory and optional tag rules for a specific resource type"""
    global_rules = MANDATORY_TAG_RULES.get("global", [])
    resource_specific_rules = MANDATORY_TAG_RULES.get(resource_type, [])
    merged_mandatory_rules_dict = {rule['key']: rule for rule in global_rules}
    merged_mandatory_rules_dict.update({rule['key']: rule for rule in resource_specific_rules})
    final_mandatory_rules = list(merged_mandatory_rules_dict.values())
    final_optional_rules = OPTIONAL_TAGS[:]
    return final_mandatory_rules, final_optional_rules

def color_text(text: str, color: str, use_color: bool) -> str:
    if not sys.stdout.isatty():
        use_color = False
    return f"{COLORS[color]}{text}{COLORS['RESET']}" if use_color else text

def load_terraform_plan(plan_file: str) -> dict:
    print(f"DEBUG: Attempting to load plan file: {plan_file}")
    try:
        with open(plan_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
            print("DEBUG: Plan file loaded successfully.")
            if not isinstance(plan_data, dict):
                 print("DEBUG: Plan file is not a JSON object.")
                 raise ValueError("Plan file does not contain a valid JSON object.")
            # Keep this warning
            if 'resource_changes' not in plan_data and 'planned_values' not in plan_data :
                 print(f"{color_text('Warning:', 'YELLOW', True)} 'resource_changes' or 'planned_values' not found at the top level of the plan. Analysis might be incomplete or fail.")
            return plan_data
    except FileNotFoundError:
        print(f"DEBUG: FileNotFoundError for {plan_file}")
        sys.exit(f"{color_text('Error:', 'RED', True)} Plan file not found at '{plan_file}'.")
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSONDecodeError: {e}")
        sys.exit(f"{color_text('Error:', 'RED', True)} Failed to parse Terraform plan JSON: {e}. Is the file valid JSON?")
    except Exception as e:
        print(f"DEBUG: Generic error loading plan: {e}")
        sys.exit(f"{color_text('Error:', 'RED', True)} Error loading Terraform plan '{plan_file}': {e}")

def extract_tags(resource_config: dict) -> Dict[str, str]:
    tags = {}
    if not isinstance(resource_config, dict):
        return tags
    tags_dict = resource_config.get('tags')
    if isinstance(tags_dict, dict):
        tags.update(tags_dict)
    tag_list = resource_config.get('tag')
    if isinstance(tag_list, list):
        for tag_spec in tag_list:
            if isinstance(tag_spec, dict) and 'key' in tag_spec and 'value' in tag_spec:
                if isinstance(tag_spec['key'], str) and isinstance(tag_spec['value'], (str, int, float, bool)):
                     tags[tag_spec['key']] = str(tag_spec['value'])
                else:
                    print(f"{color_text('Warning:', 'YELLOW', True)} Skipping malformed tag item in list: {tag_spec}")
    tags_all_dict = resource_config.get('tags_all')
    if isinstance(tags_all_dict, dict):
        base_tags = tags.copy()
        tags = tags_all_dict
        tags.update(base_tags)
    tags = {k: v for k, v in tags.items() if v is not None}
    return tags

def validate_tag_key(tag_key: str, rule: dict) -> bool:
    key_regex = rule.get('key_regex')
    if key_regex:
        try:
            return bool(re.match(key_regex, tag_key))
        except re.error as e:
            print(f"{color_text('Warning:', 'YELLOW', True)} Invalid regex for key '{rule.get('key', 'N/A')}': {key_regex} - Error: {e}")
            return False
    return True

def validate_tag_value(tag_value: str, rule: dict) -> bool:
    if not isinstance(tag_value, str):
         tag_value = str(tag_value)
    allowed_values = rule.get('allowed_values')
    value_regex = rule.get('value_regex')
    is_case_insensitive = rule.get('case_insensitive', False)
    key = rule.get('key', 'N/A')
    if allowed_values:
        normalized_allowed = [str(v) for v in allowed_values]
        check_value = tag_value.lower() if is_case_insensitive else tag_value
        compare_list = [v.lower() for v in normalized_allowed] if is_case_insensitive else normalized_allowed
        if check_value not in compare_list:
            return False
    if value_regex:
        try:
            if not re.match(value_regex, tag_value):
                return False
        except re.error as e:
             print(f"{color_text('Warning:', 'YELLOW', True)} Invalid regex for value of key '{key}': {value_regex} - Error: {e}")
             return False
    return True

def check_tag_compliance(resource_tags: Dict[str, str], mandatory_rules: List[dict], optional_rules: List[dict], resource_address: str) -> Tuple[List[dict], List[dict], List[dict]]:
    missing_mandatory_info = []
    invalid_tags_info = []
    missing_optional_info = []
    present_keys = set(resource_tags.keys())
    present_keys_lower = {k.lower() for k in present_keys}
    for rule in mandatory_rules:
        tag_key = rule['key']
        suggestion = rule.get('suggestion', 'N/A')
        if tag_key not in present_keys:
            missing_mandatory_info.append({"key": tag_key, "suggestion": suggestion, "description": rule.get('description', '')})
            continue
        if not validate_tag_key(tag_key, rule):
            invalid_tags_info.append({"key": tag_key, "value": resource_tags[tag_key], "reason": "Invalid key format", "rule_regex": rule.get('key_regex'), "suggestion": suggestion})
            continue
        current_value = resource_tags[tag_key]
        if not validate_tag_value(current_value, rule):
             violation_detail = {"key": tag_key, "value": current_value, "reason": "Invalid value", "suggestion": suggestion}
             if rule.get('allowed_values'):
                 violation_detail["allowed"] = rule.get('allowed_values')
                 violation_detail["case_insensitive"] = rule.get('case_insensitive', False)
             if rule.get('value_regex'):
                 violation_detail["regex"] = rule.get('value_regex')
             invalid_tags_info.append(violation_detail)
    for rule in optional_rules:
        tag_key = rule['key']
        suggestion = rule.get('suggestion', 'N/A')
        is_case_insensitive = rule.get('case_insensitive', False)
        check_key = tag_key.lower() if is_case_insensitive else tag_key
        present_set = present_keys_lower if is_case_insensitive else present_keys
        if check_key not in present_set:
            missing_optional_info.append({"key": tag_key, "suggestion": suggestion, "description": rule.get('description', '')})
        elif tag_key in resource_tags and not validate_tag_value(resource_tags[tag_key], rule):
             print(f"{color_text('Info:', 'BLUE', True)} [{resource_address}]: Optional tag '{tag_key}' present but has invalid value '{resource_tags[tag_key]}'. Allowed: {rule.get('allowed_values')}, Regex: {rule.get('value_regex')}")
    return missing_mandatory_info, invalid_tags_info, missing_optional_info

def check_cross_tag_rules(resource_tags: Dict[str, str], resource_type: str) -> List[str]:
    violations = []
    rules_for_type = CROSS_TAG_RULES.get(resource_type, [])
    for rule in rules_for_type:
        if_tag = rule.get('if_tag')
        then_tag = rule.get('then_tag')
        message = rule.get('message', 'Cross-tag rule violation')
        if not if_tag or not then_tag:
            print(f"{color_text('Warning:', 'YELLOW', True)} Skipping malformed cross-tag rule: {rule}")
            continue
        if_key = if_tag.get('key')
        if_value = if_tag.get('value')
        if if_key in resource_tags and resource_tags[if_key] == if_value:
            then_key = then_tag.get('key')
            then_value = then_tag.get('value')
            if then_key not in resource_tags or resource_tags[then_key] != then_value:
                 violations.append(message + f" (Expected '{then_key}={then_value}')")
    return violations

def is_resource_excluded(resource: dict, resource_type: str, resource_address: str) -> bool:
    resource_name_from_address = resource_address.split('.')[-1]
    for exclusion_rule in EXCLUDED_RESOURCES:
        type_match = exclusion_rule.get('type') == resource_type
        if type_match:
            name_regex = exclusion_rule.get('name_regex')
            if name_regex:
                try:
                    name_match = bool(re.match(name_regex, resource_name_from_address))
                    if name_match:
                        print(f"DEBUG: Excluding '{resource_address}' due to type '{resource_type}' and name regex '{name_regex}'")
                        return True
                except re.error as e:
                    print(f"{color_text('Warning:', 'YELLOW', True)} Invalid regex in exclusion rule {exclusion_rule}: {e}")
                    continue
            else:
                 print(f"DEBUG: Excluding '{resource_address}' due to type '{resource_type}' (no name regex specified)")
                 return True
    return False


# --- Reporting Functions (generate_json_report, generate_console_report) ---
# (Keep the reporting functions from the previous version)
# ... (Previous reporting functions omitted for brevity, assume they are here) ...
def generate_json_report(violations_by_resource: Dict[str, Dict[str, Union[List[dict], List[str]]]], total_resources: int, excluded_count: int) -> Dict[str, Any]:
    """Generate JSON-formatted report with enhanced details"""
    critical_violation_count = 0
    for issues in violations_by_resource.values():
         if issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error"):
              critical_violation_count += 1

    report = {
        "summary": {
            "total_resources_in_plan": total_resources + excluded_count,
            "excluded_resources": excluded_count,
            "analyzed_resources": total_resources,
            "compliant_resources": total_resources - critical_violation_count,
            "resources_with_violations": critical_violation_count,
            "deployment_environment_mode": DEPLOYMENT_ENV
        },
        "violations": []
    }

    for resource_address, issues in violations_by_resource.items():
        if issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error"):
            entry = {
                "resource": resource_address,
                "missing_mandatory": issues.get("missing", []),
                "invalid_tags": issues.get("invalid", []),
                "cross_tag_errors": issues.get("cross_tag", []),
                "analysis_error": issues.get("analysis_error"),
                "missing_optional_suggestions": issues.get("optional", [])
            }
            if not entry["analysis_error"]:
                 del entry["analysis_error"]
            report["violations"].append(entry)

    # Also add resources with only optional suggestions if needed
    report["optional_suggestions_only"] = []
    for resource_address, issues in violations_by_resource.items():
         if issues.get("optional") and not (issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error")):
              report["optional_suggestions_only"].append({
                  "resource": resource_address,
                  "missing_optional_suggestions": issues.get("optional", [])
              })

    return report


def generate_console_report(violations_by_resource: Dict[str, Dict[str, Union[List[dict], List[str]]]], total_resources: int, excluded_count: int, use_color: bool) -> str:
    """Generate human-readable console report with suggestions"""
    report_lines = []
    critical_violation_count = 0
    for issues in violations_by_resource.values():
         if issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error"):
              critical_violation_count += 1

    report_lines.append(color_text("\n--- Terraform Tag Compliance Report ---", "CYAN", use_color))
    report_lines.append(f"Deployment Environment Mode: {DEPLOYMENT_ENV}")
    report_lines.append(f"Total Resources in Plan: {total_resources + excluded_count}")
    report_lines.append(f"Excluded Resources: {excluded_count}")
    report_lines.append(f"Analyzed Resources: {total_resources}")
    report_lines.append(color_text(f"Compliant Resources: {total_resources - critical_violation_count}", "GREEN" if critical_violation_count == 0 and total_resources > 0 else "WHITE", use_color ))
    report_lines.append(color_text(f"Resources with Violations: {critical_violation_count}", "RED" if critical_violation_count > 0 else "WHITE", use_color))

    if critical_violation_count == 0 and total_resources > 0 :
        report_lines.append(color_text("\n✅ All analyzed resources comply with critical tagging requirements.", "GREEN", use_color))
    elif total_resources == 0 and excluded_count == 0 and (total_resources + excluded_count) > 0 :
         # If total > 0 but analyzed = 0 and excluded = 0, means they were skipped for other reasons (e.g. wrong action)
         report_lines.append(color_text("\n⚠️ No resources found meeting analysis criteria (create/update actions).", "YELLOW", use_color))
    elif total_resources == 0 and excluded_count == 0:
         # This case means the plan likely had no resources at all
         report_lines.append(color_text("\n⚠️ No resources found in the plan.", "YELLOW", use_color))
    elif critical_violation_count > 0:
        report_lines.append(color_text("\n--- Violation Details ---", "MAGENTA", use_color))

    # Print details for violating resources
    for resource_address, issues in sorted(violations_by_resource.items()): # Sort for consistent order
        has_critical_issue = issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error")
        if not has_critical_issue:
            continue

        report_lines.append(color_text(f"\nResource: {resource_address}", "CYAN", use_color))
        # ... (rest of violation printing logic from previous version) ...
        missing = issues.get("missing", [])
        invalid = issues.get("invalid", [])
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


    # Print optional suggestions for non-violating resources
    optional_only_resources = {res: issues['optional'] for res, issues in violations_by_resource.items() if issues.get("optional") and not (issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error"))}
    if optional_only_resources:
         report_lines.append(color_text("\n--- Optional Tag Suggestions ---", "MAGENTA", use_color))
         for resource_address, optional_list in sorted(optional_only_resources.items()): # Sort for consistent order
             report_lines.append(color_text(f"\nResource: {resource_address}", "CYAN", use_color))
             report_lines.append(color_text("  [!] Missing Optional Tag Suggestions:", "BLUE", use_color))
             for item in optional_list:
                 suggestion = f" (Example: {item['suggestion']})" if item.get('suggestion') != 'N/A' else ""
                 description = f" ({item['description']})" if item.get('description') else ""
                 report_lines.append(f"    - {item['key']}{description}{suggestion}")

    return "\n".join(report_lines)

# --- Main Analysis Function ---
def analyze_terraform_plan(plan_data: dict) -> Tuple[Dict[str, dict], int, int]:
    """Main analysis workflow - analyzes resources to be created or updated."""
    violations_by_resource = {}
    analyzed_resources_count = 0
    excluded_resources_count = 0

    # +++ START NEW DEBUGGING +++
    print("\nDEBUG: --- Plan Structure Analysis ---")
    if not isinstance(plan_data, dict):
        print("DEBUG: ERROR - Plan data is not a dictionary!")
        return {}, 0, 0

    top_level_keys = list(plan_data.keys())
    print(f"DEBUG: Top-level keys in plan: {top_level_keys}")

    resources_to_check = []
    plan_format_used = None
    resource_changes_content = None
    planned_values_root_resources = None

    if 'resource_changes' in plan_data:
        plan_format_used = "resource_changes"
        resource_changes_content = plan_data.get('resource_changes')
        if isinstance(resource_changes_content, list):
            resources_to_check = resource_changes_content
            print(f"DEBUG: Found 'resource_changes' (list) with {len(resources_to_check)} items.")
            # Optionally print a snippet for debugging structure:
            # if resources_to_check: print(f"DEBUG: First item in resource_changes: {json.dumps(resources_to_check[0], indent=2)}")
        else:
            print(f"DEBUG: Found 'resource_changes', but it's not a list (Type: {type(resource_changes_content)}).")

    elif 'planned_values' in plan_data:
        planned_values_content = plan_data.get('planned_values')
        if isinstance(planned_values_content, dict) and 'root_module' in planned_values_content:
            root_module_content = planned_values_content.get('root_module')
            if isinstance(root_module_content, dict) and 'resources' in root_module_content:
                plan_format_used = "planned_values"
                planned_values_root_resources = root_module_content.get('resources')
                if isinstance(planned_values_root_resources, list):
                    resources_to_check = planned_values_root_resources
                    print(f"DEBUG: Found 'planned_values.root_module.resources' (list) with {len(resources_to_check)} items.")
                    # Optionally print a snippet:
                    # if resources_to_check: print(f"DEBUG: First item in planned_values.root_module.resources: {json.dumps(resources_to_check[0], indent=2)}")
                else:
                    print(f"DEBUG: Found 'planned_values.root_module.resources', but it's not a list (Type: {type(planned_values_root_resources)}).")
            else:
                 print("DEBUG: Found 'planned_values', but 'root_module' or 'root_module.resources' structure is missing or not a dict/list.")
        else:
            print("DEBUG: Found 'planned_values', but it's not a dictionary or 'root_module' is missing.")
    else:
        print("DEBUG: Neither 'resource_changes' nor 'planned_values' found at the top level.")

    print(f"DEBUG: Determined plan format: {plan_format_used}")
    print(f"DEBUG: Number of resources selected for iteration: {len(resources_to_check)}")
    print("DEBUG: --- End Plan Structure Analysis ---\n")
    # +++ END NEW DEBUGGING +++


    if not resources_to_check:
         # Already printed debug info above
         print(f"{color_text('Warning:', 'YELLOW', True)} Could not find a list of resources to analyze in the plan.")
         return {}, 0, 0

    # Set keys based on determined format
    if plan_format_used == "resource_changes":
        source_key = 'change'
        actions_key = 'actions'
    elif plan_format_used == "planned_values":
        source_key = 'values'
        actions_key = None # Assume create/update in this older format
    else:
        # Should not happen if resources_to_check is populated, but safety check
        print("DEBUG: ERROR - Plan format could not be determined despite finding resources.")
        return {}, 0, 0


    for index, resource in enumerate(resources_to_check):
        resource_id_for_log = f"item {index}"
        try:
            # Basic check: Is the item a dictionary?
            if not isinstance(resource, dict):
                print(f"DEBUG: Skipping item {index} because it's not a dictionary (Type: {type(resource)})")
                continue

            resource_type = resource.get('type', '')
            address = resource.get('address', f'unknown_resource_{index}')
            resource_id_for_log = address

            # print(f"DEBUG: Processing resource {index}: Type='{resource_type}', Address='{address}'") # Keep if needed

            config = None
            is_create_or_update = False

            if plan_format_used == "resource_changes":
                actions = resource.get(actions_key, [])
                # print(f"DEBUG [{address}]: Actions = {actions}") # Keep if needed
                # --- Logic refinement: Also check 'replace' action ---
                if "create" in actions or "update" in actions or ("replace" in actions and "delete" not in actions): # Consider replace as needing validation
                     change_info = resource.get(source_key, {})
                     if not isinstance(change_info, dict):
                          print(f"DEBUG [{address}]: 'change' key expected dict, got {type(change_info)}. Skipping.")
                          continue
                     config = change_info.get('after', {})
                     after_unknown = change_info.get('after_unknown', {})

                     # More robust check for unknown tags
                     tags_unknown = False
                     if isinstance(after_unknown, dict):
                         if after_unknown.get('tags') is True or after_unknown.get('tags_all') is True:
                              tags_unknown = True

                     if tags_unknown:
                          print(f"{color_text('Info:', 'BLUE', True)} [{address}]: Tags ('tags' or 'tags_all') are computed at apply time (marked as unknown). Skipping tag validation.")
                          analyzed_resources_count += 1
                          continue

                     if not isinstance(config, dict):
                          print(f"DEBUG [{address}]: 'change.after' key expected dict, got {type(config)}. Skipping.")
                          continue

                     is_create_or_update = True
                # else:
                     # print(f"DEBUG [{address}]: Skipping resource due to actions (not create/update/replace).") # Keep if needed

            elif plan_format_used == "planned_values":
                config = resource.get(source_key, {})
                if not isinstance(config, dict):
                     print(f"DEBUG [{address}]: 'values' key expected dict, got {type(config)}. Skipping.")
                     continue
                is_create_or_update = bool(config) # Simple check: if values exist, assume update/create


            if not is_create_or_update:
                # print(f"DEBUG [{address}]: Skipping - Not determined as create/update or config is None/invalid.") # Keep if needed
                continue

            # --- Exclusion Check ---
            if is_resource_excluded(resource, resource_type, address):
                excluded_resources_count += 1
                continue

            # --- Analysis ---
            analyzed_resources_count += 1
            # print(f"DEBUG [{address}]: Analyzing resource. Total analyzed: {analyzed_resources_count}") # Keep if needed

            tags = extract_tags(config)
            print(f"DEBUG [{address}]: Extracted tags: {tags}") # Crucial Debug Point

            mandatory_rules, optional_rules = get_relevant_tag_rules(resource_type)
            missing_mandatory, invalid_tags, missing_optional = check_tag_compliance(
                tags, mandatory_rules, optional_rules, address
            )
            cross_tag_errors = check_cross_tag_rules(tags, resource_type)

            if address not in violations_by_resource: violations_by_resource[address] = {} # Initialize if first issue found
            if missing_mandatory or invalid_tags or cross_tag_errors:
                 # print(f"DEBUG [{address}]: VIOLATIONS DETECTED") # Keep if needed
                 violations_by_resource[address].update({
                    "missing": missing_mandatory,
                    "invalid": invalid_tags,
                    "cross_tag": cross_tag_errors
                 })
            # Store optional regardless of violations for reporting
            if missing_optional:
                violations_by_resource[address]["optional"] = missing_optional


        except Exception as e:
            print(f"{color_text('Error:', 'RED', True)} Analyzing resource '{resource_id_for_log}': {e}. Skipping.")
            if resource_id_for_log not in violations_by_resource: violations_by_resource[resource_id_for_log] = {}
            violations_by_resource[resource_id_for_log]["analysis_error"] = str(e)


    print(f"DEBUG: Analysis loop finished. Analyzed: {analyzed_resources_count}, Excluded: {excluded_resources_count}, Resources with issues reported: {len(violations_by_resource)}")
    return violations_by_resource, analyzed_resources_count, excluded_resources_count


# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(
        description="Terraform Tag Compliance Analyzer. Reads DEPLOYMENT_ENV env var.",
        formatter_class=argparse.RawTextHelpFormatter
        )
    parser.add_argument("plan_file", help="Path to Terraform plan JSON file")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    # Removed --debug flag, debug output is now more focused on plan parsing

    args = parser.parse_args()
    use_color = not args.no_color

    plan_data = load_terraform_plan(args.plan_file)
    violations, analyzed_count, excluded_count = analyze_terraform_plan(plan_data)

    if args.json:
        json_report = generate_json_report(violations, analyzed_count, excluded_count)
        print(json.dumps(json_report, indent=2))
    else:
        console_report = generate_console_report(violations, analyzed_count, excluded_count, use_color)
        print(console_report)

    has_critical_violations = any(
        issues.get("missing") or issues.get("invalid") or issues.get("cross_tag") or issues.get("analysis_error")
        for issues in violations.values()
    )
    # print(f"DEBUG: Exiting. Critical violations found: {has_critical_violations}") # Keep if needed
    sys.exit(1 if has_critical_violations else 0)


if __name__ == "__main__":
    main()
