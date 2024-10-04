Dynamic AWS Tagging Module in Terraform

This guide will walk you through creating a dynamic AWS tagging module using Terraform and how to reference this module in other Terraform projects by hosting the module in a GitLab repository.

1. Create the AWS Tagging Module

The purpose of this module is to create dynamic tags that can be used across all AWS resources in your Terraform configurations.

1.1. Directory Structure for the Tagging Module

Start by creating a directory structure for the module:

aws-tagging-module/
├── main.tf
├── variables.tf
├── outputs.tf
├── README.md

1.2. Define Inputs (Variables)

In the variables.tf file, define the input variables that will dynamically generate tags for AWS resources:

# variables.tf
variable "environment" {
  description = "Environment for resource (e.g., dev, stage, prod)"
  type        = string
}

variable "application" {
  description = "Name of the application"
  type        = string
}

variable "owner" {
  description = "Owner of the resource"
  type        = string
}

variable "extra_tags" {
  description = "Additional tags as a map"
  type        = map(string)
  default     = {}
}

1.3. Create the Tagging Logic

In the main.tf file, create the logic that consolidates all tags (both dynamic and static) into a single map output.

# main.tf
locals {
  common_tags = {
    Environment = var.environment
    Application = var.application
    Owner       = var.owner
  }

  all_tags = merge(local.common_tags, var.extra_tags)
}

output "tags" {
  description = "Map of consolidated tags"
  value       = local.all_tags
}

1.4. Define Outputs

In the outputs.tf file, output the resulting tags map.

# outputs.tf
output "tags" {
  description = "The consolidated tags for the resource"
  value       = local.all_tags
}

1.5. README.md Documentation

In the README.md file, provide a brief description of the module and how it should be used:

# AWS Dynamic Tagging Module

This Terraform module consolidates dynamic tags for AWS resources, ensuring consistent tagging across environments. 

## Inputs

- **environment**: The environment in which the resource is created (e.g., dev, stage, prod).
- **application**: The name of the application using the resource.
- **owner**: The owner of the resource.
- **extra_tags**: A map of any additional tags.

## Outputs

- **tags**: A map of consolidated tags that can be applied to AWS resources.

## Usage Example

```hcl
module "tags" {
  source      = "git::https://gitlab.com/your-repo/aws-tagging-module.git"
  environment = "prod"
  application = "my-app"
  owner       = "team-xyz"
  extra_tags  = {
    "Project" = "My Project"
    "Cost Center" = "CC1234"
  }
}

---

### 2. **Push the Module to GitLab**

Now, push the module to a GitLab repository so it can be used in other Terraform projects.

1. Initialize a new GitLab repository and clone it to your local machine:
   ```bash
   git clone https://gitlab.com/your-username/aws-tagging-module.git
   cd aws-tagging-module

	2.	Add all the module files and push them to GitLab:

git add .
git commit -m "Initial commit of AWS tagging module"
git push origin main



3. Using the AWS Tagging Module in Other Terraform Projects

You can now use the tagging module in other Terraform projects by referencing its GitLab URL.

3.1. Referencing the Module

In your Terraform project, reference the module using the GitLab link to the repository:

module "tags" {
  source      = "git::https://gitlab.com/your-username/aws-tagging-module.git"
  environment = "dev"
  application = "my-application"
  owner       = "team-devops"
  extra_tags  = {
    "Project"     = "My Application Project"
    "Department"  = "Engineering"
  }
}

3.2. Applying Tags to AWS Resources

Once the tagging module is included in your project, you can use the output from the tags to apply it to your AWS resources.

For example:

resource "aws_instance" "web" {
  ami           = "ami-123456"
  instance_type = "t2.micro"
  tags          = module.tags.tags
}

3.3. Versioning the Module

It’s a good practice to version control your module. You can tag versions in GitLab and reference specific versions in your Terraform projects.

For example, if you tag a version v1.0.0 in GitLab, you can reference it like this:

module "tags" {
  source      = "git::https://gitlab.com/your-username/aws-tagging-module.git?ref=v1.0.0"
  environment = "prod"
  application = "my-app"
  owner       = "team-xyz"
}

4. Conclusion

By creating a reusable AWS tagging module in Terraform, you can ensure consistent and dynamic tagging across your resources. Hosting the module in GitLab allows you to easily reference it in other projects, providing flexibility and maintainability.

This approach offers:

	•	Consistency in tagging across environments.
	•	Flexibility to add custom tags.
	•	Version control via GitLab.