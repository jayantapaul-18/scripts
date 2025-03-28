Script/Commands to Run Validation

You'll need the OPA executable installed. You can download it from the Open Policy Agent releases page.

Save the Rego code above as tag_policy.rego and the JSON examples as valid_resource.json, invalid_missing_tag.json, invalid_value.json, and invalid_missing_and_value.json.

Then, run these commands in your terminal from the directory containing the files:

Test the valid resource:

Bash

opa eval --data tag_policy.rego --input valid_resource.json "data.aws.validation.tags.deny"
Expected Output: [] (An empty list means no 'deny' rules were triggered, so it's compliant)

Test the resource missing a tag:

Bash

opa eval --data tag_policy.rego --input invalid_missing_tag.json "data.aws.validation.tags.deny"
Expected Output: ["Mandatory tag 'project' is missing."]

Test the resource with an invalid tag value:

Bash

opa eval --data tag_policy.rego --input invalid_value.json "data.aws.validation.tags.deny"
Expected Output: ["Tag 'environment' has invalid value 'develop'. Allowed values are: {\"dev\", \"prod\", \"staging\"}"] (Note: Set order in output may vary)

Test the resource with multiple violations:

Bash

opa eval --data tag_policy.rego --input invalid_missing_and_value.json "data.aws.validation.tags.deny"
Expected Output: (Order might vary)

JSON

[
  "Mandatory tag 'owner' is missing.",
  "Tag 'environment' has invalid value 'development'. Allowed values are: {\"dev\", \"prod\", \"staging\"}"
]
Integrating into a CI/CD Pipeline (e.g., with Terraform):

Generate Terraform Plan JSON: In your pipeline, run terraform plan -out=tfplan.binary and then terraform show -json tfplan.binary > tfplan.json.
Adapt OPA Policy (If Needed): The structure of tfplan.json is more complex. You'd typically iterate through resource_changes and look at change.after.tags (for creates/updates). Your policy might look more like this snippet inside a rule:
Code snippet

# Example adaptation for Terraform Plan JSON
some i
resource := input.resource_changes[i]
resource.change.actions[_] in ["create", "update"] # Check action type

# Safely get planned tags
planned_tags := object.get(resource.change.after, "tags", {}) 

# ... apply your mandatory_tags and allowed_environment_values checks ...
# using planned_tags instead of current_tags from the simple example ...

present_keys := {key | planned_tags[key]}
m_tag := mandatory_tags[_]
not m_tag in present_keys
msg := sprintf("Resource '%s' (%s) will be missing mandatory tag '%s'", [resource.address, resource.type, m_tag]) 
Run OPA: opa eval --data your_policy.rego --input tfplan.json "data.your.policy.package.deny".
Check Output: Check if the output list is empty. If not, fail the pipeline step. Tools like conftest abstract some of this plan parsing and evaluation for you.
