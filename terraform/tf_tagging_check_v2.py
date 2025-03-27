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
            "allowed_values": ["30 Days", "1 Year", "5 Years"],
            "suggestion": "Data retention policy based on classification"
        },
        {
            "key": "Breadth",
            "allowed_values": ["Global Scope", "Regional Scope", "Local Scope"],
            "suggestion": "Data distribution scope"
        }
    ]
}

OPTIONAL_TAGS = [
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

def validate_tag_value(tag_value: str, rule: dict) -> Tuple[bool, Union[str, None]]:
    """Validate tag value with proper space handling and case sensitivity"""
    allowed_values = rule.get('allowed_values', [])
    if not allowed_values:
        return True, None

    # Preserve original case in allowed_values for reporting
    allowed_values_lower = [v.lower() for v in allowed_values]
    tag_value_lower = tag_value.lower()

    if rule.get('case_insensitive', False):
        if tag_value_lower in allowed_values_lower:
            # Find the correctly cased version for reporting
            matched_value = allowed_values[allowed_values_lower.index(tag_value_lower)]
            return True, matched_value
        return False, None

    # Case-sensitive comparison with exact space matching
    if tag_value in allowed_values:
        return True, tag_value
    return False, None

def check_tag_compliance(
    resource_tags: Dict[str, str],
    mandatory_rules: List[dict],
    optional_rules: List[dict]
) -> Tuple[List[dict], List[dict], List[dict]]:
    """Check resource tags with enhanced space handling"""
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
        is_valid, matched_value = validate_tag_value(current_value, rule)
        
        if not is_valid:
            invalid_tags.append({
                "key": tag_key,
                "value": current_value,
                "allowed": rule.get('allowed_values', []),
                "case_insensitive": rule.get('case_insensitive', False),
                "suggestion": rule.get('suggestion', ''),
                "matched_value": matched_value
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

def generate_console_report(
    violations: Dict[str, Tuple[List[dict], List[dict], List[dict]]],
    use_color: bool
) -> str:
    """Generate color-coded console report with space handling"""
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
                case_note = "(case-insensitive match)" if issue['case_insensitive'] else "(case-sensitive)"
                allowed = ", ".join([f'"{v}"' for v in issue['allowed']])
                suggestion = f" Suggestion: {issue['suggestion']}" if issue['suggestion'] else ""
                
                msg = (f"    - {issue['key']}: '{issue['value']}'\n"
                      f"      Expected {case_note}: {allowed}\n"
                      f"      {suggestion}")
                
                if issue['matched_value']:
                    msg += f"\n      Did you mean: {issue['matched_value']}"
                
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

# Rest of the code remains the same as previous implementation
# (load_terraform_plan, extract_tags, analyze_terraform_plan, main, etc.)
