#!/usr/bin/env python3

import os
import sys
import argparse
import json
from pathlib import Path
try:
    import hcl2
except ImportError:
    print("Error: 'python-hcl2' library not found.")
    print("Please install it using: pip install python-hcl2")
    sys.exit(1)

# --- Tagging Configuration (Copied from your example) ---

# Environment configuration
# Consider making DEPLOYMENT_ENV an argument or reading from a config file for more flexibility
DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "NPE").upper()
print(f"INFO: Running validation for DEPLOYMENT_ENV='{DEPLOYMENT_ENV}'")

ENV_TAG_CONFIG = {
    "PROD": {
        "allowed_values": ["Production::PRD"],
        "suggestion": "Production environment requires strict tagging (Production::PRD)"
    },
    "NPE": {
        "allowed_values": ["Non-production::DEV", "Non-production::QAT"],
        "suggestion": "Non-production environment tagging (Non-production::DEV or Non-production::QAT)"
    }
}

# Resolve Environment tag settings based on DEPLOYMENT_ENV
current_env_config = ENV_TAG_CONFIG.get(DEPLOYMENT_ENV, ENV_TAG_CONFIG["NPE"])

# Tagging configuration
MANDATORY_TAG_RULES = {
    "global": [
        {
            "key": "Application",
            "allowed_values": ["MyApp", "AnotherApp", "TestApp"],
            "case_insensitive": True,
            "suggestion": "Main application identifier (e.g., MyApp, AnotherApp, TestApp)"
        },
        {
            "key": "Environment",
            "allowed_values": current_env_config["allowed_values"],
            "case_insensitive": False, # Typically environment tags are case-sensitive
            "suggestion": current_env_config["suggestion"]
        },
        {
            "key": "Owner",
            "allowed_values": ["devops"],
            "case_insensitive": True, # Assuming owner can be lower/upper case
            "suggestion": "Team responsible for the resource (e.g., devops)"
        }
    ],
    "aws_s3_bucket": [
        {
            "key": "DataRetention",
            "allowed_values": ["30d", "1y", "5y"],
            "case_insensitive": False,
            "suggestion": "Data retention policy (e.g., 30d, 1y, 5y)"
        },
        {
            "key": "Breadth",
            "allowed_values": ["global", "regional", "local"],
            "case_insensitive": True,
            "suggestion": "Data distribution scope (e.g., global, regional, local)"
        },
        {
            "key": "Sensitivity",
            "allowed_values": ["public", "confidential", "restricted"],
            "case_insensitive": True,
            "suggestion": "Data sensitivity level (e.g., public, confidential, restricted)"
        },
        {
            "key": "Danger",
            "allowed_values": ["low", "medium", "high"],
            "case_insensitive": True,
            "suggestion": "Potential impact of data exposure (e.g., low, medium, high)"
        }
    ]
    # Add more resource-specific rules here, e.g., "aws_instance": [...]
}

# Optional tags are not strictly enforced but can be checked for presence/value if needed
# For this script, we focus on mandatory tags as per the core request.
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
        "suggestion": "Mark resources managed by Terraform (true/false)"
    }
]

# Resource types to completely ignore during tag validation
EXCLUDED_RESOURCE_TYPES = [
    "aws_iam_role",
    "aws_iam_policy",
    "aws_iam_role_policy_attachment",
    "aws_iam_instance_profile",
    # Add other types like data sources, providers, variables etc. if needed
    "terraform_remote_state",
    "aws_route53_zone", # Often managed centrally, might have different tagging
]

# --- Validation Logic ---

def find_tf_files(directory):
    """Finds all .tf files recursively in a directory."""
    tf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".tf"):
                tf_files.append(Path(root) / file)
    return tf_files

def validate_tags(resource_tags, resource_type, resource_name, file_path):
    """Validates tags for a single resource against the rules."""
    violations = []
    resource_tags = resource_tags or {} # Handle case where tags block is missing

    # --- Determine applicable mandatory rules ---
    mandatory_rules = MANDATORY_TAG_RULES.get("global", []) + \
                      MANDATORY_TAG_RULES.get(resource_type, [])
    mandatory_keys_defined = {rule['key'] for rule in mandatory_rules}

    # --- Check Mandatory Tags ---
    for rule in mandatory_rules:
        rule_key = rule['key']
        allowed_values = rule.get('allowed_values')
        case_insensitive = rule.get('case_insensitive', False)
        suggestion = rule.get('suggestion', 'No suggestion available.')

        # 1. Check if mandatory tag exists
        if rule_key not in resource_tags:
            violations.append({
                "file": str(file_path),
                "resource": f"{resource_type}.{resource_name}",
                "tag_key": rule_key,
                "issue": "Missing mandatory tag.",
                "suggestion": suggestion
            })
            continue # Skip further checks for this missing tag

        # 2. Check if the tag value is allowed (if allowed_values are specified)
        resource_value = resource_tags[rule_key]

        # Limitation: Static analysis cannot resolve variables or function calls.
        # We check the literal value present in the HCL.
        if not isinstance(resource_value, str):
             # Handle non-string values (e.g. numbers, booleans, complex interpolations parsed as dicts)
             # For simplicity, we might flag them or try a basic string conversion
             # Flagging as potentially problematic is safer for static analysis.
            violations.append({
                "file": str(file_path),
                "resource": f"{resource_type}.{resource_name}",
                "tag_key": rule_key,
                "issue": f"Tag value is not a simple string ('{resource_value}'). Static analysis cannot fully validate dynamic values.",
                "suggestion": "Ensure tag value resolves to an allowed string. " + suggestion
            })
            continue # Cannot reliably check non-strings against allowed values list

        if allowed_values:
            value_to_check = resource_value.lower() if case_insensitive else resource_value
            valid_values_to_compare = [v.lower() for v in allowed_values] if case_insensitive else allowed_values

            if value_to_check not in valid_values_to_compare:
                violations.append({
                    "file": str(file_path),
                    "resource": f"{resource_type}.{resource_name}",
                    "tag_key": rule_key,
                    "issue": f"Invalid value '{resource_value}'. Allowed: {allowed_values}.",
                    "suggestion": suggestion
                })

    # --- Optional: Check for unknown tags (tags not in mandatory or optional lists) ---
    # This can be noisy if many non-standard tags are used intentionally. Enable if desired.
    # known_optional_keys = {tag['key'] for tag in OPTIONAL_TAGS}
    # for tag_key in resource_tags:
    #     if tag_key not in mandatory_keys_defined and tag_key not in known_optional_keys:
    #         # Check if tag starts with 'aws:', 'terraform:' which are often system-managed
    #         if not tag_key.lower().startswith(('aws:', 'terraform:')):
    #             violations.append({
    #                 "file": str(file_path),
    #                 "resource": f"{resource_type}.{resource_name}",
    #                 "tag_key": tag_key,
    #                 "issue": "Unknown tag key found.",
    #                 "suggestion": "Verify if this tag is necessary or defined in tagging standards."
    #             })

    return violations


def analyze_terraform_file(file_path):
    """Parses a single Terraform file and validates resources."""
    all_violations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Handle potential interpolation errors during parsing if needed,
            # but hcl2 usually handles syntax structure well.
            tf_data = hcl2.load(f)

        resources = tf_data.get('resource', [])
        for resource_block in resources:
            for resource_type, resources_in_type in resource_block.items():
                if resource_type in EXCLUDED_RESOURCE_TYPES:
                    # print(f"DEBUG: Skipping excluded resource type: {resource_type}")
                    continue

                for resource_name, resource_config_list in resources_in_type.items():
                    # resource_config_list is usually a list containing one dict
                    if not resource_config_list: continue
                    resource_config = resource_config_list[0]

                    # Extract tags - Handle potential variations
                    tags = resource_config.get('tags')

                    # Add checks for other common patterns if necessary
                    # e.g., tags within a 'website' block for s3, etc.
                    # if resource_type == 'aws_s3_bucket' and 'website' in resource_config:
                    #    tags = resource_config['website'][0].get('tags', tags) # Merge or prioritize

                    if tags is None:
                        # Treat missing tags block as empty tags for validation purposes
                        tags = {}
                        # Add a violation if *any* tags are mandatory globally or for the type
                        if MANDATORY_TAG_RULES.get("global") or MANDATORY_TAG_RULES.get(resource_type):
                             # Add a generic missing tags violation if tags block itself is absent
                             # This helps catch resources with no tags defined at all.
                             pass # The individual mandatory tag check will catch specifics


                    # Important: hcl2 parses tags = { ... } into a dict
                    # If tags = var.common_tags, tags will be the string "var.common_tags"
                    # This static analysis cannot resolve variables.
                    if isinstance(tags, dict):
                         violations = validate_tags(tags, resource_type, resource_name, file_path)
                         all_violations.extend(violations)
                    elif isinstance(tags, (str, list)): # Could be a variable reference or merge() result
                         # Cannot statically validate variable references like 'var.common_tags' or complex merges
                         all_violations.append({
                            "file": str(file_path),
                            "resource": f"{resource_type}.{resource_name}",
                            "tag_key": "N/A (Block)",
                            "issue": f"Tags defined using non-literal map ('{tags}'). Static analysis cannot validate.",
                            "suggestion": "Ensure the final resolved tags meet requirements. Consider using literal maps for static checks."
                         })
                    # Else: tags might be defined in an unsupported way or absent

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error parsing HCL file {file_path}: {e}", file=sys.stderr)
        # Optionally add more specific hcl2 parsing error handling
        all_violations.append({
            "file": str(file_path),
            "resource": "N/A",
            "tag_key": "N/A",
            "issue": f"Failed to parse file. Error: {e}",
            "suggestion": "Check Terraform syntax."
        })

    return all_violations

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Statically analyze Terraform code for AWS resource tagging compliance.")
    parser.add_argument("directory", help="Path to the directory containing Terraform code.")
    parser.add_argument("-o", "--output", choices=['text', 'json'], default='text', help="Output format (text or json).")

    args = parser.parse_args()

    terraform_dir = Path(args.directory)
    if not terraform_dir.is_dir():
        print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning Terraform files in: {terraform_dir.resolve()}")
    tf_files = find_tf_files(terraform_dir)

    if not tf_files:
        print("No Terraform (.tf) files found.")
        sys.exit(0)

    total_violations = []
    for tf_file in tf_files:
        # print(f"Analyzing: {tf_file}") # Optional: print progress
        violations = analyze_terraform_file(tf_file)
        total_violations.extend(violations)

    print("-" * 60)
    if not total_violations:
        print("✅ Success: All validated resources conform to tagging guidelines.")
        sys.exit(0)
    else:
        print(f"❌ Found {len(total_violations)} tagging violations:")
        if args.output == 'json':
            print(json.dumps(total_violations, indent=2))
        else: # Default to text output
            for violation in total_violations:
                print(f"\n[!] Violation in {violation['file']}")
                print(f"    Resource:   {violation['resource']}")
                print(f"    Tag Key:    {violation['tag_key']}")
                print(f"    Issue:      {violation['issue']}")
                print(f"    Suggestion: {violation['suggestion']}")
        print("-" * 60)
        sys.exit(1) # Exit with error code if violations found

if __name__ == "__main__":
    main()
