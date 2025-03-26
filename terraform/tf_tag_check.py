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

def analyze_terraform_file(file_path):
    """Parses a single Terraform file and validates resources."""
    all_violations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # This is where the parsing error for invalid HCL like
            # 'Workload = "Test No Code"' will occur.
            tf_data = hcl2.load(f)

        # --- Rest of the analysis logic remains the same ---
        resources = tf_data.get('resource', [])
        for resource_block in resources:
            for resource_type, resources_in_type in resource_block.items():
                if resource_type in EXCLUDED_RESOURCE_TYPES:
                    continue

                for resource_name, resource_config_list in resources_in_type.items():
                    if not resource_config_list: continue
                    resource_config = resource_config_list[0]
                    tags = resource_config.get('tags')

                    if tags is None:
                        tags = {}

                    if isinstance(tags, dict):
                         violations = validate_tags(tags, resource_type, resource_name, file_path)
                         all_violations.extend(violations)
                    elif isinstance(tags, (str, list)):
                         all_violations.append({
                            "file": str(file_path),
                            "resource": f"{resource_type}.{resource_name}",
                            "tag_key": "N/A (Block)",
                            "issue": f"Tags defined using non-literal map ('{tags}'). Static analysis cannot validate.",
                            "suggestion": "Ensure the final resolved tags meet requirements. Consider using literal maps for static checks."
                         })

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        # Optionally add a specific violation for file not found if needed
    except Exception as e:
        # --- This block handles HCL parsing errors ---
        error_message = f"HCL Syntax Error: Failed to parse file. Details: {e}"
        print(f"ERROR in {file_path}: {error_message}", file=sys.stderr) # Print clear error
        # Add a structured violation record for reporting
        all_violations.append({
            "file": str(file_path),
            "resource": "N/A - File Level Error", # Indicate error is not specific to one resource
            "tag_key": "N/A",
            "issue": error_message,
            "suggestion": "Check Terraform HCL syntax in the specified file, likely near the location mentioned in the details."
        })

    return all_violations

# --- The rest of the script (imports, config, main, etc.) remains the same ---
# ... (include the full script from the previous response here, replacing
#      only the analyze_terraform_file function with this updated one) ...

if __name__ == "__main__":
    # Ensure the main function and argument parsing are included
    main()
    
if __name__ == "__main__":
    main()
