# terraform/main.tf

# Variables
variable "gitlab_token" {
  description = "GitLab personal access token"
}

variable "gitlab_project_id" {
  description = "GitLab project ID"
}

# Provider configuration
provider "gitlab" {
  token = var.gitlab_token
}

# Data source to get project details
data "gitlab_project" "project" {
  project_id = var.gitlab_project_id
}

# Data source to get project members
data "gitlab_group_members" "maintainers" {
  group_id = data.gitlab_project.project.namespace_id
  filter   = "maintainer"  # Adjust the role filter based on your needs
}

# Output project and maintainers information
output "project_info" {
  value = {
    project_name   = data.gitlab_project.project.name
    project_id     = data.gitlab_project.project.id
    maintainers    = data.gitlab_group_members.maintainers.members
  }
}
