import json
import sys
import os

class TagValidator:
    def __init__(self, plan_file):
        self.plan_file = plan_file
        self.allowed_application_values = ["web-app", "data-pipeline", "batch-job"]
        self.mandatory_tags = {
            "Environment": "production",
            "CostCenter": "12345",
            "Owner": "DevOps Team"
        }
        self.violations =

    def load_plan(self):
        try:
            with open(self.plan_file, 'r') as f:
                self.plan_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Plan file not found at {self.plan_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {self.plan_file}")
            sys.exit(1)

    def validate_tags(self):
        if not hasattr(self, 'plan_data') or not self.plan_data:
            print("Error: Terraform plan data not loaded. Please call load_plan() first.")
            return

        if 'resource_changes' not in self.plan_data:
            print("Warning: No resource changes found in the Terraform plan.")
            return

        for resource_change in self.plan_data['resource_changes']:
            if resource_change['type'].startswith('aws_') and resource_change['change'] and ('after' in resource_change['change'] or 'after_sensitive' in resource_change['change']):
                resource_address = resource_change['address']
                resource_type = resource_change['type']
                tags = {}

                if 'after' in resource_change['change'] and resource_change['change']['after'] and 'tags' in resource_change['change']['after']:
                    tags = resource_change['change']['after']['tags']
                elif 'after_sensitive' in resource_change['change'] and resource_change['change']['after_sensitive'] and 'tags' in resource_change['change']['after_sensitive']:
                    tags = resource_change['change']['after_sensitive']['tags']

                self._check_application_tag(resource_address, resource_type, tags)
                self._check_other_mandatory_tags(resource_address, resource_type, tags)

    def _check_application_tag(self, resource_address, resource_type, tags):
        if 'Application' not in tags:
            self.violations.append(f"Resource: {resource_type} '{resource_address}' is missing the mandatory 'Application' tag.")
        else:
            application_value = tags['Application']
            if application_value.lower() not in [val.lower() for val in self.allowed_application_values]:
                self.violations.append(f"Resource: {resource_type} '{resource_address}' has an invalid 'Application' tag value: '{application_value}'. Allowed values are: {', '.join(self.allowed_application_values)} (case-insensitive).")

    def _check_other_mandatory_tags(self, resource_address, resource_type, tags):
        for tag_key, expected_value in self.mandatory_tags.items():
            if tag_key not in tags:
                self.violations.append(f"Resource: {resource_type} '{resource_address}' is missing the mandatory tag '{tag_key}'.")
            elif tags[tag_key] != expected_value:
                self.violations.append(f"Resource: {resource_type} '{resource_address}' has an incorrect value for the mandatory tag '{tag_key}'. Expected: '{expected_value}', Found: '{tags[tag_key]}'.")

    def generate_report(self):
        print("\n--- Terraform Tagging Audit Report ---")
        if self.violations:
            for violation in self.violations:
                print(f"- {violation}")
            print(f"\nFound {len(self.violations)} tagging violations.")
            return False
        else:
            print("All mandatory tags are present and correctly configured for the AWS resources in the plan.")
            return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python tag_validator.py <path_to_terraform_plan.json>")
        sys.exit(1)

    plan_file_path = sys.argv[1]
    validator = TagValidator(plan_file_path)
    validator.load_plan()
    validator.validate_tags()
    validator.generate_report()

if __name__ == "__main__":
    main()
