import os
import re
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

# Environment configuration
DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "NPE").upper()
ENV_TAG_CONFIG = {
    "PROD": {
        "allowed_values": ["Production::PRD"],
        "suggestion": "Production environment requires strict tagging"
    },
    "NPE": {
        "allowed_values": ["Non-production::DEV", "Non-production::QAT"],
        "suggestion": "Non-production environment tagging"
    }
}

# Tagging configuration
MANDATORY_TAG_RULES = {
    "global": [
        {
            "key": "Application",
            "allowed_values": ["MyApp", "AnotherApp", "TestApp"],
            "case_insensitive": True,
            "suggestion": "Main application identifier"
        },
        {
            "key": "Environment",
            "allowed_values": ENV_TAG_CONFIG.get(DEPLOYMENT_ENV, ENV_TAG_CONFIG["NPE"])["allowed_values"],
            "suggestion": ENV_TAG_CONFIG.get(DEPLOYMENT_ENV, ENV_TAG_CONFIG["NPE"])["suggestion"]
        },
        {
            "key": "Owner",
            "allowed_values": ["devops"],
            "suggestion": "Team responsible for the resource"
        }
    ],
    "aws_s3_bucket": [
        {
            "key": "DataRetention",
            "allowed_values": ["30d", "1y", "5y"],
            "suggestion": "Data retention policy based on classification"
        },
        {
            "key": "Breadth",
            "allowed_values": ["global", "regional", "local"],
            "suggestion": "Data distribution scope"
        },
        {
            "key": "Sensitivity",
            "allowed_values": ["public", "confidential", "restricted"],
            "suggestion": "Data sensitivity level"
        },
        {
            "key": "Danger",
            "allowed_values": ["low", "medium", "high"],
            "suggestion": "Potential impact of data exposure"
        }
    ]
}

OPTIONAL_TAGS = [
    {
        "key": "CostCenter",
        "description": "Financial tracking code",
        "suggestion": "Add cost center for financial reporting"
    },
    {
        "key": "Terraform",
        "allowed_values": ["true", "false"],
        "case_insensitive": True,
        "suggestion": "Mark resources managed by Terraform"
    }
]

EXCLUDED_RESOURCE_TYPES = [
    "aws_iam_role",
    "aws_iam_policy"
]

class TagAnalysisError(Exception):
    """Custom exception for tag analysis errors"""
    pass

def color_text(text: str, color: str, use_color: bool) -> str:
    """Apply color to text if enabled"""
    return f"{COLORS[color]}{text}{COLORS['RESET']}" if use_color else text

def load_terraform_plan(plan_file: str) -> dict:
    """Load and validate Terraform plan JSON file"""
    try:
        with open(plan_file, 'r') as f:
            plan_data = json.load(f)
            
        # Basic plan structure validation
        if not isinstance(plan_data.get("resource_changes"), list):
            raise TagAnalysisError("Invalid plan structure: missing resource_changes")
            
        return plan_data
    except FileNotFoundError:
        sys.exit(f"Error: Plan file not found: {plan_file}")
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in plan file: {str(e)}")
    except Exception as e:
        sys.exit(f"Error loading Terraform plan: {str(e)}")

def extract_tags(resource_config: dict) -> Dict[str, str]:
    """Extract and normalize tags from resource configuration"""
    tags = {}
    
    # Handle different tag formats
    tag_sources = [
        resource_config.get('tags'),
        resource_config.get('tags_all'),
        resource_config.get('tag')
    ]
    
    for tag_source in tag_sources:
        if isinstance(tag_source, dict):
            tags.update({str(k): str(v) for k, v in tag_source.items() if v is not None})
        elif isinstance(tag_source, list):
            for tag_spec in tag_source:
                if isinstance(tag_spec, dict):
                    key = tag_spec.get('key')
                    value = tag_spec.get('value')
                    if key and value is not None:
                        tags[str(key)] = str(value)
    
    return tags

def validate_tag_key(key: str) -> bool:
    """Validate tag key format"""
    try:
        return bool(re.match(r"^[a-zA-Z0-9_\-\.:/]+$", key))
    except re.error:
        raise TagAnalysisError(f"Invalid regex pattern for tag key validation")

def validate_tag_value(value: str, rule: dict) -> bool:
    """Validate tag value against rule with error handling"""
    try:
        if not validate_tag_key(value):
            return False
            
        allowed_values = rule.get('allowed_values', [])
        if not allowed_values:
            return True
            
        if rule.get('case_insensitive', False):
            return value.lower() in [v.lower() for v in allowed_values]
            
        return value in allowed_values
    except re.error:
        raise TagAnalysisError(f"Invalid regex pattern in validation rule for {rule.get('key')}")

def get_mandatory_tag_rules(resource_type: str) -> List[dict]:
    """Get merged mandatory tag rules for a specific resource type"""
    global_rules = MANDATORY_TAG_RULES.get("global", [])
    resource_rules = MANDATORY_TAG_RULES.get(resource_type, [])
    
    # Merge rules with resource-specific taking precedence
    merged_rules = {}
    for rule in global_rules + resource_rules:
        merged_rules[rule["key"]] = rule
    return list(merged_rules.values())

def check_tag_compliance(
    resource_tags: Dict[str, str],
    mandatory_rules: List[dict],
    optional_rules: List[dict]
) -> Tuple[List[dict], List[dict], List[dict]]:
    """Check resource tags against requirements with detailed suggestions"""
    missing_mandatory = []
    invalid_tags = []
    missing_optional = []

    # Check mandatory tags
    for rule in mandatory_rules:
        tag_key = rule['key']
        if tag_key not in resource_tags:
            missing_mandatory.append({
                "key": tag_key,
                "suggestion": rule.get('suggestion', '')
            })
            continue
            
        current_value = resource_tags[tag_key]
        if not validate_tag_value(current_value, rule):
            invalid_tags.append({
                "key": tag_key,
                "value": current_value,
                "allowed": rule.get('allowed_values', []),
                "case_insensitive": rule.get('case_insensitive', False),
                "suggestion": rule.get('suggestion', '')
            })

    # Check optional tags
    for rule in optional_rules:
        tag_key = rule['key']
        if tag_key not in resource_tags:
            missing_optional.append({
                "key": tag_key,
                "suggestion": rule.get('suggestion', '')
            })

    return missing_mandatory, invalid_tags, missing_optional

def generate_json_report(violations: Dict[str, Tuple[List[dict], List[dict], List[dict]]]) -> Dict[str, Any]:
    """Generate detailed JSON-formatted report"""
    report = {
        "metadata": {
            "deployment_env": DEPLOYMENT_ENV,
            "total_resources": 0,
            "excluded_resources": 0,
            "analyzed_resources": 0,
            "compliant_resources": 0,
            "violations": 0
        },
        "details": []
    }
    
    for resource, (missing, invalid, optional) in violations.items():
        report["metadata"]["total_resources"] += 1
        report["metadata"]["violations"] += 1
        
        entry = {
            "resource": resource,
            "missing_mandatory": missing,
            "invalid_tags": invalid,
            "missing_optional": optional
        }
        report["details"].append(entry)
    
    report["metadata"]["compliant_resources"] = (
        report["metadata"]["total_resources"] - report["metadata"]["violations"]
    )
    return report

def generate_console_report(
    violations: Dict[str, Tuple[List[dict], List[dict], List[dict]]],
    use_color: bool
) -> str:
    """Generate color-coded console report with symbols"""
    report = []
    
    for resource, (missing, invalid, optional) in violations.items():
        header = color_text(f"\n🔍 Resource: {resource}", "CYAN", use_color)
        report.append(header)
        
        if missing:
            report.append(color_text("  ✗ Missing mandatory tags:", "RED", use_color))
            for item in missing:
                suggestion = f" ({item['suggestion']})" if item['suggestion'] else ""
                report.append(f"    - {item['key']}{suggestion}")
            
        if invalid:
            report.append(color_text("  ✗ Invalid tag values:", "RED", use_color))
            for issue in invalid:
                case_note = "(case-insensitive)" if issue['case_insensitive'] else ""
                allowed = ", ".join(issue['allowed'])
                suggestion = f" Suggestion: {issue['suggestion']}" if issue['suggestion'] else ""
                msg = (f"    - {issue['key']}: '{issue['value']}' "
                      f"not in {case_note} [{allowed}]{suggestion}")
                report.append(color_text(msg, "YELLOW", use_color))
        
        if optional:
            report.append(color_text("  ! Optional tag suggestions:", "BLUE", use_color))
            for item in optional:
                suggestion = f" ({item['suggestion']})" if item['suggestion'] else ""
                report.append(f"    - {item['key']}{suggestion}")
    
    if not violations:
        success_msg = color_text("\n✅ All resources comply with tagging requirements", "GREEN", use_color)
        report.append(success_msg)
    
    return "\n".join(report)

def analyze_terraform_plan(plan_data: dict) -> Dict[str, Tuple[List[dict], List[dict], List[dict]]]:
    """Main analysis workflow with error handling"""
    violations = {}
    total_resources = 0
    excluded_resources = 0
    
    for resource in plan_data.get('resource_changes', []):
        try:
            total_resources += 1
            if 'delete' in resource.get('actions', []):
                continue
                
            resource_type = resource.get('type', '')
            if resource_type in EXCLUDED_RESOURCE_TYPES:
                excluded_resources += 1
                continue
                
            address = resource.get('address', 'unknown')
            config = resource.get('change', {}).get('after', {})
            
            tags = extract_tags(config)
            mandatory_rules = get_mandatory_tag_rules(resource_type)
            missing, invalid, optional = check_tag_compliance(tags, mandatory_rules, OPTIONAL_TAGS)
            
            if missing or invalid:
                violations[address] = (missing, invalid, optional)
                
        except Exception as e:
            print(f"Error analyzing resource {resource.get('address')}: {str(e)}", file=sys.stderr)
    
    return violations, total_resources, excluded_resources

def main():
    parser = argparse.ArgumentParser(description="Enhanced Terraform Tag Compliance Analyzer")
    parser.add_argument("plan_file", help="Path to Terraform plan JSON file")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    parser.add_argument("--color", action="store_true", help="Enable colored output")
    args = parser.parse_args()

    plan_data = load_terraform_plan(args.plan_file)
    violations, total_resources, excluded_resources = analyze_terraform_plan(plan_data)

    if args.json:
        json_report = generate_json_report(violations)
        json_report["metadata"].update({
            "total_resources": total_resources,
            "excluded_resources": excluded_resources,
            "analyzed_resources": total_resources - excluded_resources
        })
        print(json.dumps(json_report, indent=2))
    else:
        console_report = generate_console_report(violations, args.color)
        print(f"\nTerraform Tag Compliance Report ({DEPLOYMENT_ENV} Environment)")
        print(f"📊 Total Resources: {total_resources}")
        print(f"🚫 Excluded Resources: {excluded_resources}")
        print(console_report)

    # Exit code based on violation severity
    has_mandatory_issues = any(missing or invalid for missing, invalid, _ in violations.values())
    sys.exit(1 if has_mandatory_issues else 0)

if __name__ == "__main__":
    main()


################################################
Environment-Based Tag Configuration:

Reads DEPLOYMENT_ENV with NPE default

Dynamic allowed values and suggestions for Environment tag

PROD environment has strict production values

Enhanced S3 Tagging Rules:

Added breadth, sensitivity, and danger tags

Detailed allowed values and suggestions

Example:
{
    "key": "Sensitivity",
    "allowed_values": ["public", "confidential", "restricted"],
    "suggestion": "Data sensitivity level"
}
Improved Validation & Error Handling:

Custom TagAnalysisError class

Specific error handling for file operations and JSON parsing

Resource-level try/catch to prevent analysis interruption

Enhanced regex validation with error handling

Structured Suggestions:

Suggestions included in both missing and invalid tags

Propagated through JSON and console reports

Example JSON output:

"missing_mandatory": [{
    "key": "Environment",
    "suggestion": "Production environment requires strict tagging"
}]
Enhanced Reporting:

Clear metadata section in JSON output

Color-coded symbols in console (🔍, ✗, ✅, !)

Environment context in report headers

Resource counts and exclusion statistics

Configuration Flexibility:

Tag rules can be extended to YAML/JSON files

Clear separation of global vs resource-specific rules

Dynamic rule merging based on resource type

Exit Code Handling:

Exit code 1 for mandatory violations

Exit code 0 for optional suggestions only

Clear severity-based status reporting

Usage Example:

# Production environment analysis
DEPLOYMENT_ENV=PROD python analyzer.py tfplan.json --color

# JSON output with full details
python analyzer.py tfplan.json --json > report.json
This implementation provides enterprise-grade tag validation with comprehensive reporting, dynamic environment adaptation, and robust error handling suitable for complex infrastructure deployments.
