#===============================================================================
#
# infra/github/Makefile — GitHub repository configuration
#
#===============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

.PHONY: check-fmt validate plan apply import

tf = tofu

# Verify OpenTofu formatting.
check-fmt:
	$(tf) fmt -check -recursive .

# Validate without touching the backend or contacting GitHub.
validate:
	$(tf) init -backend=false && $(tf) validate

# Plan, apply, or import. Output is logged with ANSI codes stripped.
plan:
	$(tf) plan 2>&1 | tee /dev/stderr | sed -e 's/\x1b\[[0-9;]*m//g' > plan.log.txt

apply:
	$(tf) apply 2>&1 | tee /dev/stderr | sed -e 's/\x1b\[[0-9;]*m//g' > apply.log.txt

import:
	./import.sh
