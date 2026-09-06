# GitHub Repository Configuration

Manages the configuration of the `jmcvetta/claude-daily-driver` repository
itself: merge strategy, branch protection, and Dependabot alerts.

Modelled on `Green-Pagoda/pagoda`'s `infra/bootstrap/bootstrap-github`, minus
the parts that are specific to that monorepo.

## Depends On

Nothing. The repository must already exist — it is the thing this checkout
lives in.

## Why Local State

Same chicken-and-egg property as any bootstrap phase: the configuration that
protects `master` and defines the required status check cannot depend on CI
running inside that repository, or on remote state that does not exist yet.

State is local and committed to Git. It holds repository settings and branch
rules — all of it readable by anyone with repo access, and no secrets, by the
exclusion below.

## Resources Created

- **`github_repository`** — merge settings, visibility, feature toggles
- **`github_repository_vulnerability_alerts`** — Dependabot alerts
- **`github_branch_protection`** on `master` — required `CI Success` check
  (strict), linear history, conversation resolution, no force pushes or
  deletions

## The `CI Success` Check Is a Placeholder Today

Branch protection requires a status check named `CI Success`, and a required
check that never reports blocks every pull request. `.github/workflows/ci.yml`
therefore ships a job with exactly that name which asserts nothing.

Replacing it with real CI is a change to the workflow, not to this
configuration: the Tofu binds to the job *name*, so jobs can be added under
`needs` without touching `branch_protection.tf`.

Two consequences worth knowing:

- A pull request whose branch predates the workflow will not report the check
  and cannot merge until it picks up `master`. `strict = true` already
  requires that.
- `enforce_admins = false` leaves an escape hatch for the case where CI
  itself is what is broken.

## Deliberate Exclusions

**Actions secrets.** The provider writes secret values into state, and this
state is committed. Set them by hand and leave them there. Variables would be
fine; there are none yet.

**Labels.** Tofu owns only what it declares, so declaring none neither adopts
nor deletes GitHub's defaults. The repository has no labels of its own yet;
add a `labels.tf` when it does.

**Environments.** Nothing deploys from this repository.

## Prerequisites

A GitHub token with admin rights on the repository, exported as
`GITHUB_TOKEN`. A `gh` login with the `repo` scope suffices:

```bash
export GITHUB_TOKEN=$(gh auth token)
```

## Usage

```bash
cd infra/github
export GITHUB_TOKEN=$(gh auth token)
tofu init
./import.sh   # adopts the pre-existing repository
tofu plan
tofu apply
```

The repository already exists, so it is **imported** rather than created — a
greenfield apply would try to create a repository that is already there.
Everything else is genuinely new, so the first plan reports changes rather
than the "No changes." a fully-imported stack would:

- `github_repository.this` updated in place — squash-only merges, PR title
  and body as the commit subject and message, branch deletion on merge, auto
  merge enabled
- `github_repository_vulnerability_alerts.this` created
- `github_branch_protection.master` created

After applying, commit `terraform.tfstate` to Git.
