#!/usr/bin/env bash
# Adds a long planning document under docs/planning/.
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
	fixture_filler_lines 900
} >docs/planning/cache-rollout.md

fixture_publish_topic "docs: add the cache rollout plan"
