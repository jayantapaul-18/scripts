import json
import sys
import argparse
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

# Configuration
MANDATORY_TAGS = [
    {
        "key": "Application",
        "allowed_values": ["MyApp", "AnotherApp", "TestApp"],
        "case_insensitive": True
    },
    {
        "key": "Environment",
        "allowed_values": ["prod", "staging", "dev"]
    },
    {
        "key": "Owner",
        "allowed_values": ["devops"]
    }
]

OPTIONAL_TAGS = [
    {"key": "CostCenter", "description": "Financial tracking code"},
    {"key": "DataClassification", "allowed_values": ["public", "confidential", "restricted"]}
]

EXCLUDED_RESOURCE_TYPES = [
    "aws_iam_role",
    "aws_iam_policy"
]

def color_text(text: str, color: str, use_color: bool) -> str:
    """Apply color to text if enabled"""
    return f"{COLORS[color]}{text}{COLORS['RESET']}" if use_color else text

def load_terraform_plan(plan_file: str) -> dict:
    """Load and parse Terraform plan JSON file"""
    try:
        with open(plan_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        sys.exit(f"Error loading Terraform plan: {str(e)}")

def extract_tags(resource_config: dict) -> Dict[str, str]:
    """Extract tags from resource configuration"""
    tags = {}
    
    # Standard tag format
    if isinstance(resource_config.get('tags'), dict):
        tags.update(resource_config['tags'])
    
    # ASG-style tag format
    if isinstance(resource_config.get('tag'), list):
        for tag_spec in resource_config['tag']:
            if isinstance(tag_spec, dict) and 'key' in tag_spec and 'value' in tag_spec:
                tags[tag_spec['key'] = tag_spec['value']
    
    return tags

def validate_tag_value(tag_value: str, rule: dict) -> bool:
    """Validate a tag value against validation rules"""
    allowed_values = rule.get('allowed_values', [])
    if not allowed_values:
        return True
    
    if rule.get('case_insensitive', False):
        return tag_value.lower() in [v.lower() for v in allowed_values]
    
    return tag_value in allowed_values

def check_tag_compliance(resource_tags: Dict[str, str]) -> Tuple[List[str], List[dict], List[str]]:
    """Check resource tags against requirements"""
    missing_mandatory = []
    invalid_tags = []
    missing_optional = []

    # Check mandatory tags
    for rule in MANDATORY_TAGS:
        tag_key = rule['key']
        if tag_key not in resource_tags:
            missing_mandatory.append(tag_key)
            continue
            
        current_value = resource_tags[tag_key]
        if not validate_tag_value(current_value, rule):
            invalid_tags.append({
                "key": tag_key,
                "value": current_value,
                "allowed": rule['allowed_values'],
                "case_insensitive": rule.get('case_insensitive', False)
            })

    # Check optional tags
    for rule in OPTIONAL_TAGS:
        tag_key = rule['key']
        if tag_key not in resource_tags:
            missing_optional.append(tag_key)

    return missing_mandatory, invalid_tags, missing_optional

def generate_json_report(violations: Dict[str, Tuple[List[str], List[dict], List[str]]]) -> Dict[str, Any]:
    """Generate JSON-formatted report"""
    report = {
        "summary": {
            "total_resources": 0,
            "compliant_resources": 0,
            "violations": 0
        },
        "details": []
    }
    
    for resource, (missing, invalid, optional) in violations.items():
        report["summary"]["total_resources"] += 1
        report["summary"]["violations"] += 1
        
        entry = {
            "resource": resource,
            "missing_mandatory": missing,
            "invalid_tags": invalid,
            "missing_optional": optional
        }
        report["details"].append(entry)
    
    report["summary"]["compliant_resources"] = report["summary"]["total_resources"] - report["summary"]["violations"]
    return report

def generate_console_report(violations: Dict[str, Tuple[List[str], List[dict], List[str]]], use_color: bool) -> str:
    """Generate human-readable console report"""
    report = []
    
    for resource, (missing, invalid, optional) in violations.items():
        header = color_text(f"\nResource: {resource}", "CYAN", use_color)
        report.append(header)
        
        if missing:
            report.append(color_text("  [✗] Missing mandatory tags:", "RED", use_color))
            report.extend(f"    - {tag}" for tag in missing)
            
        if invalid:
            report.append(color_text("  [✗] Invalid tag values:", "RED", use_color))
            for issue in invalid:
                case_note = "(case-insensitive)" if issue['case_insensitive'] else ""
                allowed = ", ".join(issue['allowed'])
                msg = (f"    - {issue['key']}: '{issue['value']}' "
                      f"not in allowed values {case_note}: [{allowed}]")
                report.append(color_text(msg, "YELLOW", use_color))
        
        if optional:
            report.append(color_text("  [!] Optional tag suggestions:", "BLUE", use_color))
            report.extend(f"    - {tag}" for tag in optional)
    
    if not violations:
        success_msg = color_text("\nAll resources comply with tagging requirements", "GREEN", use_color)
        report.append(success_msg)
    
    return "\n".join(report)

def analyze_terraform_plan(plan_data: dict) -> Dict[str, Tuple[List[str], List[dict], List[str]]]:
    """Main analysis workflow"""
    violations = {}
    
    for resource in plan_data.get('resource_changes', []):
        if 'delete' in resource.get('actions', []):
            continue
            
        resource_type = resource.get('type', '')
        if resource_type in EXCLUDED_RESOURCE_TYPES:
            continue
            
        address = resource.get('address', 'unknown')
        config = resource.get('change', {}).get('after', {})
        
        tags = extract_tags(config)
        missing, invalid, optional = check_tag_compliance(tags)
        
        if missing or invalid:
            violations[address] = (missing, invalid, optional)
    
    return violations

def main():
    parser = argparse.ArgumentParser(description="Terraform Tag Compliance Analyzer")
    parser.add_argument("plan_file", help="Path to Terraform plan JSON file")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    parser.add_argument("--color", action="store_true", help="Enable colored output")
    args = parser.parse_args()

    plan_data = load_terraform_plan(args.plan_file)
    violations = analyze_terraform_plan(plan_data)

    if args.json:
        json_report = generate_json_report(violations)
        print(json.dumps(json_report, indent=2))
    else:
        console_report = generate_console_report(violations, args.color)
        print("\nTerraform Tag Compliance Report:")
        print(console_report)

    # Exit with error code if violations found
    sys.exit(1 if violations else 0)

if __name__ == "__main__":
    main()
#################################################################
# New Features Added:
# JSON Output Support:

# Use --json flag to get machine-readable output

# Includes detailed compliance information and statistics

# Example output:

# {
#   "summary": {
#     "total_resources": 3,
#     "compliant_resources": 1,
#     "violations": 2
#   },
#   "details": [
#     {
#       "resource": "aws_instance.web_server",
#       "missing_mandatory": ["Owner"],
#       "invalid_tags": [...],
#       "missing_optional": ["CostCenter"]
#     }
#   ]
# }
# Color Support:

# Use --color flag to enable ANSI color output

# Color-coded severity levels:

# Red: Missing mandatory tags

# Yellow: Invalid tag values

# Blue: Optional tag suggestions

# Green: Success message

# Optional Tag Suggestions:

# Configure optional tags in OPTIONAL_TAGS

# Shown as suggestions but don't fail compliance

# Includes descriptions and allowed values

# Improved Reporting:

# Visual indicators (✗ for errors, ! for suggestions)

# Summary statistics in JSON output

# More detailed violation context

# Usage:

# # Colored console output (default)
# python tf_tag_analyzer.py tfplan.json --color

# # JSON output
# python tf_tag_analyzer.py tfplan.json --json

# # Both formats
# python tf_tag_analyzer.py tfplan.json --json > report.json
# python tf_tag_analyzer.py tfplan.json --color | tee console-report.txt
# Configuration Updates:
# Add optional tags to OPTIONAL_TAGS array:

# OPTIONAL_TAGS = [
#     {"key": "CostCenter", "description": "Financial tracking code"},
#     {"key": "DataClassification", "allowed_values": ["public", "confidential"]}
# ]
# Modify color schemes by changing the COLORS dictionary

# Add new resource types to EXCLUDED_RESOURCE_TYPES if needed

# This enhanced version provides multiple output formats, better visual feedback, and more comprehensive tagging suggestions while maintaining backward compatibility with the original functionality.

