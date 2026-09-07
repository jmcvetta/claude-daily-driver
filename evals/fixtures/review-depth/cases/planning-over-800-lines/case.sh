#!/usr/bin/env bash
# Adds a long planning document that also discusses IAM roles, credential
# rotation and the release workflow.
# shellcheck source=../../shared/lib.sh
source "$(dirname "$0")/lib.sh"
# shellcheck source=../../shared/_common_base.sh
source "$(dirname "$0")/_common_base.sh"

fixture_init
fixture_write_base_tree
fixture_publish_base
fixture_branch docs/cache-rollout-plan

{
	printf '# Cache rollout\n\n'
	printf 'The staged plan for warming the read-through cache, shard by shard.\n\n'
	printf '## Access\n\n'
	printf 'Each shard warmer assumes an IAM role scoped to one tenant prefix, and\n'
	printf 'authenticates with a token rotated out of the release workflow rather than\n'
	printf 'a long-lived credential. Whether the rotation lives with the deploy job or\n'
	printf 'beside the warmer is a question for the implementation subissue.\n\n'
	printf '## Schedule\n\n'
	fixture_filler_lines 900
} >docs/planning/cache-rollout.md

fixture_publish_topic "docs: add the cache rollout plan"
