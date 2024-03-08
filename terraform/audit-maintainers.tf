# terraform/main.tf

# Variables
variable "gitlab_token" {
  description = "GitLab personal access token"
}

# Provider configuration
provider "gitlab" {
  token = var.gitlab_token
}

# Data source to get all GitLab projects
data "gitlab_projects" "all_projects" {}

# Filter projects based on the number of maintainers
locals {
  projects_with_no_or_one_maintainer = [for project in data.gitlab_projects.all_projects.projects : project.id if length(data.gitlab_project_members.maintainers[project.id].members) <= 1]
}

# Output projects with no or one maintainer
output "projects_with_no_or_one_maintainer" {
  value = local.projects_with_no_or_one_maintainer
}
