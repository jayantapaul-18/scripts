Features:
Configurable Tag Rules: Define mandatory tags with allowed values and case sensitivity

AWS Tag Format Support: Handles both standard tag maps and ASG-style tag lists

Resource Exclusion: Skip specific resource types that don't support tags

Compliance Reporting: Generates detailed report with missing tags and invalid values

Case Insensitivity: Optionally validate tag values case-insensitively

Error Handling: Robust error checking for plan file loading and parsing

Usage:
Generate Terraform plan in JSON format:

terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
Run the analyzer:

```bash
python tf_tag_analyzer.py tfplan.json
```
Configuration:
Modify MANDATORY_TAGS to define your tagging requirements

Adjust EXCLUDED_RESOURCE_TYPES to skip specific resource types

Each tag rule supports:

key: Tag name to check

allowed_values: List of permitted values

case_insensitive: Set to True for case-insensitive value matching

Output Example:

Terraform Tag Compliance Report:

Resource: aws_instance.web_server
  Missing mandatory tags:
    - Owner
  Invalid tag values:
    - Environment: 'production' not in allowed values: [prod, staging, dev]

Resource: aws_s3_bucket.data
  Missing mandatory tags:
    - Environment
    - Application
This script provides a foundation for tag compliance checking that can be extended with additional validation rules and reporting formats as needed.
