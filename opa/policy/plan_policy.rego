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
