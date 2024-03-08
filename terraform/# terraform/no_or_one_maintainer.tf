# terraform/main.tf

# Variables
variable "gitlab_token" {
  description = "GitLab personal access token"
}

variable "notification_script" {
  description = "Path to the Python script for notifications"
}

# Provider configuration
provider "gitlab" {
  token = var.gitlab_token
}

# Data source to get all GitLab projects
data "gitlab_projects" "all_projects" {}

# Local variable to store project IDs with no or one maintainer
locals {
  projects_with_no_or_one_maintainer = [for project in data.gitlab_projects.all_projects.projects : project.id if length(data.gitlab_project_members.maintainers[project.id].members) <= 1]
}

# Resource to execute local provisioners
resource "null_resource" "audit_projects" {
  count = length(local.projects_with_no_or_one_maintainer)

  triggers = {
    project_id = local.projects_with_no_or_one_maintainer[count.index]
  }

  provisioner "local-exec" {
    command = "python3 ${var.notification_script} ${local.projects_with_no_or_one_maintainer[count.index]}"
  }
}
