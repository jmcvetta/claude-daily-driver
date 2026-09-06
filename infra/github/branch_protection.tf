# Classic branch protection on master.
#
# Deliberately classic rather than a ruleset, matching the pattern this
# configuration was modelled on. Migrating to a ruleset is a separate change
# with its own plan.
#
# `CI Success` is the single required check — the aggregating job that
# per-area jobs report into, so adding a job to CI does not require touching
# this file. Today that job is the placeholder in
# `.github/workflows/ci.yml`; the contract here is the job *name*, which
# survives the placeholder being replaced with real CI.
#
# Two settings are deliberately loose for a solo repository: zero required
# approving reviews, since requiring one would block every PR, and
# `enforce_admins = false`, which leaves an escape hatch when CI itself is
# what is broken.
resource "github_branch_protection" "master" {
  repository_id = github_repository.this.node_id
  pattern       = "master"

  required_status_checks {
    strict   = true
    contexts = ["CI Success"]
  }

  required_pull_request_reviews {
    required_approving_review_count = 0
    dismiss_stale_reviews           = false
    require_code_owner_reviews      = false
    require_last_push_approval      = false
  }

  required_linear_history         = true
  require_conversation_resolution = true
  allows_force_pushes             = false
  allows_deletions                = false
  enforce_admins                  = false
  lock_branch                     = false
}
