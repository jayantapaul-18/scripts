import json
import sys
from typing import Dict, List, Tuple, Union

# Configuration: Adjust these settings according to your requirements
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

EXCLUDED_RESOURCE_TYPES = [
    "aws_iam_role",
    "aws_iam_policy"
]

def load_terraform_plan(plan_file: str) -> dict:
    """Load and parse Terraform plan JSON file"""
    try:
        with open(plan_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        sys.exit(f"Error loading Terraform plan: {str(e)}")

def extract_tags(resource_config: dict) -> Dict[str, str]:
    """Extract tags from resource configuration, handling different AWS tag formats"""
    tags = {}
    
    # Handle standard tag format (map)
    if isinstance(resource_config.get('tags'), dict):
        tags.update(resource_config['tags'])
    
    # Handle ASG-style tag format (list of key/value pairs)
    if isinstance(resource_config.get('tag'), list):
        for tag_spec in resource_config['tag']:
            if isinstance(tag_spec, dict) and 'key' in tag_spec and 'value' in tag_spec:
                tags[tag_spec['key'] = tag_spec['value']
    
    return tags

def validate_tag_value(tag_value: str, rule: dict) -> bool:
    """Validate a tag value against validation rules"""
    allowed_values = rule.get('allowed_values', [])
    if not allowed_values:
        return True  # No value validation required
    
    if rule.get('case_insensitive', False):
        return tag_value.lower() in [v.lower() for v in allowed_values]
    
    return tag_value in allowed_values

def check_tag_compliance(resource_tags: Dict[str, str]) -> Tuple[List[str], List[dict]]:
    """Check resource tags against mandatory tag requirements"""
    missing_tags = []
    invalid_tags = []

    for rule in MANDATORY_TAGS:
        tag_key = rule['key']
        allowed_values = rule.get('allowed_values', [])
        
        if tag_key not in resource_tags:
            missing_tags.append(tag_key)
            continue
            
        current_value = resource_tags[tag_key]
        if not validate_tag_value(current_value, rule):
            invalid_tags.append({
                "key": tag_key,
                "value": current_value,
                "allowed": allowed_values,
                "case_insensitive": rule.get('case_insensitive', False)
            })

    return missing_tags, invalid_tags

def generate_compliance_report(violations: Dict[str, Tuple[List[str], List[dict]]]) -> str:
    """Generate human-readable compliance report"""
    report = []
    
    for resource, (missing, invalid) in violations.items():
        report.append(f"Resource: {resource}")
        
        if missing:
            report.append("  Missing mandatory tags:")
            report.extend(f"    - {tag}" for tag in missing)
            
        if invalid:
            report.append("  Invalid tag values:")
            for issue in invalid:
                case_note = "(case-insensitive)" if issue['case_insensitive'] else ""
                allowed = ", ".join(issue['allowed'])
                report.append(
                    f"    - {issue['key']}: '{issue['value']}' "
                    f"not in allowed values {case_note}: [{allowed}]"
                )
        
        report.append("")  # Add empty line between resources
    
    return "\n".join(report)

def analyze_terraform_plan(plan_data: dict) -> Dict[str, Tuple[List[str], List[dict]]]:
    """Main analysis workflow"""
    violations = {}
    
    for resource in plan_data.get('resource_changes', []):
        # Skip deleted resources and excluded types
        if 'delete' in resource.get('actions', []):
            continue
            
        resource_type = resource.get('type', '')
        if resource_type in EXCLUDED_RESOURCE_TYPES:
            continue
            
        # Extract resource information
        address = resource.get('address', 'unknown')
        config = resource.get('change', {}).get('after', {})
        
        # Analyze tags
        tags = extract_tags(config)
        missing, invalid = check_tag_compliance(tags)
        
        if missing or invalid:
            violations[address] = (missing, invalid)
    
    return violations

def main():
    if len(sys.argv) != 2:
        print("Usage: python tf_tag_analyzer.py <terraform_plan.json>")
        sys.exit(1)
    
    # Load and analyze plan
    plan_data = load_terraform_plan(sys.argv[1])
    violations = analyze_terraform_plan(plan_data)
    
    # Generate and print report
    report = generate_compliance_report(violations)
    print("Terraform Tag Compliance Report:\n")
    print(report if report else "All resources comply with tagging requirements")
    
    # Exit with error code if violations found
    if violations:
        sys.exit(1)

if __name__ == "__main__":
    main()
