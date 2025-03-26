import json
import sys

def analyze_terraform_plan(plan_file, mandatory_tags, application_tag_values=("ISP",)):
    """
    Analyzes a Terraform plan JSON output, checks for mandatory tags, and validates the Application tag (case-insensitive).

    Args:
        plan_file (str): Path to the Terraform plan JSON file.
        mandatory_tags (list): A list of dictionaries representing mandatory tags (e.g., [{"key": "Environment", "values": ["production", "staging"]}]).
        application_tag_values (tuple): A tuple of allowed values for the "Application" tag (case-insensitive).
    """

    try:
        with open(plan_file, 'r') as f:
            plan_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Plan file '{plan_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in plan file '{plan_file}'.")
        return

    missing_tags = {}

    for resource_change in plan_data.get('resource_changes', []):
        if resource_change['type'].startswith('aws_'):  # Check for AWS resources
            resource_address = resource_change['address']
            resource_type = resource_change['type']
            change_actions = resource_change.get('change', {}).get('actions', [])
            if "create" not in change_actions and "update" not in change_actions:
                continue #skip if resource is not being created or updated.

            after_values = resource_change.get('change', {}).get('after', {})

            if after_values and "tags" in after_values:
                resource_tags = after_values['tags']
            else:
                resource_tags = {}

            # Application tag validation (case-insensitive)
            if "Application" not in resource_tags:
                if resource_address not in missing_tags:
                    missing_tags[resource_address] = {}
                missing_tags[resource_address]["Application"] = f"Missing (allowed values: {', '.join(application_tag_values)})"
            elif resource_tags["Application"].lower() not in (val.lower() for val in application_tag_values):
                if resource_address not in missing_tags:
                    missing_tags[resource_address] = {}
                missing_tags[resource_address]["Application"] = f"Value mismatch (allowed values: {', '.join(application_tag_values)}, actual: {resource_tags['Application']})"

            # Other mandatory tags validation (multiple values)
            for mandatory_tag in mandatory_tags:
                tag_key = mandatory_tag["key"]
                allowed_values = mandatory_tag["values"]
                if tag_key not in resource_tags:
                    if resource_address not in missing_tags:
                        missing_tags[resource_address] = {}
                    missing_tags[resource_address][tag_key] = f"Missing (allowed values: {', '.join(allowed_values)})"
                elif resource_tags[tag_key] not in allowed_values:
                    if resource_address not in missing_tags:
                        missing_tags[resource_address] = {}
                    missing_tags[resource_address][tag_key] = f"Value mismatch (allowed values: {', '.join(allowed_values)}, actual: {resource_tags[tag_key]})"

    if missing_tags:
        print("Missing or incorrect tags found:")
        for resource, tags in missing_tags.items():
            print(f"  Resource: {resource}")
            for tag_key, message in tags.items():
                print(f"    - {tag_key}: {message}")
        sys.exit(1) # exit with non-zero code to indicate failure.
    else:
        print("All mandatory tags are present and correct.")
        sys.exit(0) #exit with zero code to indicate success.

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_plan.py <terraform_plan.json>")
        sys.exit(1)

    plan_file = sys.argv[1]
    mandatory_tags = [
        {"key": "Environment", "values": ["production", "staging", "dev"]},
        {"key": "Owner", "values": ["engineering", "security"]},
        {"key": "Project", "values": ["my-project", "another-project"]}
    ]
    application_tag_values = ("DIP","dip","Dip") #case insensitive check.

    analyze_terraform_plan(plan_file, mandatory_tags, application_tag_values)
