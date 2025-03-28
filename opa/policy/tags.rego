package aws.validation.tags

import future.keywords.if
import future.keywords.in

# --- Configuration Data ---
# Define which tags are mandatory
mandatory_tags := {
    "environment",
    "owner",
    "project"
}

# Define allowed values for the 'environment' tag
allowed_environment_values := {
    "dev",
    "staging",
    "prod"
}

# --- Rules ---

# Helper to safely get tags, returning empty object if missing
current_tags := object.get(object.get(input, "attributes", {}), "tags", {})

# Get the keys of the tags that are actually present
present_tag_keys := {key | current_tags[key]}

# Rule: Deny if a mandatory tag is missing
deny[msg] {
    # Select a tag name from the set of mandatory tags
    m_tag := mandatory_tags[_]
    # Check if this mandatory tag is NOT present in the resource's tags
    not m_tag in present_tag_keys
    # Generate the error message
    msg := sprintf("Mandatory tag '%s' is missing.", [m_tag])
}

# Rule: Deny if 'environment' tag has an invalid value
deny[msg] {
    # Check if the environment tag is present
    "environment" in present_tag_keys
    # Get the value
    env_value := current_tags.environment
    # Check if the value is NOT in the allowed set
    not env_value in allowed_environment_values
    # Generate the error message
    msg := sprintf("Tag 'environment' has invalid value '%s'. Allowed values are: %v", [env_value, allowed_environment_values])
}

# Add more rules for other tags as needed...
# deny[msg] {
#     "project" in present_tag_keys
#     project_value := current_tags.project
#     # Example: Check project format (starts with 'PROJ-')
#     not startswith(project_value, "PROJ-")
#     msg := sprintf("Tag 'project' ('%s') must start with 'PROJ-'.", [project_value])
# }
