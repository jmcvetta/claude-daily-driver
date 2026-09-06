# The repository itself.
#
# The squash-only + PR_TITLE pairing is load-bearing, not taste. Conventional
# Commits go on PR titles rather than on individual commits, and anything that
# parses history — changelog generation, release tooling — reads commit
# subjects on master. Those cohere only because squash-merge makes the PR
# title become the master commit subject. Re-enabling merge commits would
# quietly break that.
#
# Public, because the plugin marketplace manifest is meant to be fetched by
# anyone installing the plugin.
resource "github_repository" "this" {
  name        = local.repository
  description = "Daily-driver skills for Claude Code, packaged as a plugin."
  visibility  = "public"

  has_issues   = true
  has_projects = true
  has_wiki     = true

  allow_squash_merge          = true
  allow_merge_commit          = false
  allow_rebase_merge          = false
  allow_auto_merge            = true
  allow_update_branch         = false
  delete_branch_on_merge      = true
  squash_merge_commit_title   = "PR_TITLE"
  squash_merge_commit_message = "PR_BODY"

  # Inert while merge commits are disabled, but the API reports these values,
  # so declaring them keeps the plan quiet.
  merge_commit_title   = "MERGE_MESSAGE"
  merge_commit_message = "PR_TITLE"
}

# Dependabot alerts. Its own resource rather than the repository's deprecated
# vulnerability_alerts field.
resource "github_repository_vulnerability_alerts" "this" {
  repository = github_repository.this.name
  enabled    = true
}
