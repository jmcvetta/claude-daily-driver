terraform {
  required_version = ">= 1.6, < 2.0"

  required_providers {
    github = {
      source = "integrations/github"
      # 6.13.0 added github_workflow_repository_permissions, which
      # repository.tf uses to keep the release job able to open its pull
      # request.
      version = "~> 6.13"
    }
  }
}
