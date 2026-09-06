terraform {
  required_version = ">= 1.6, < 2.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.13"
    }
  }
}
