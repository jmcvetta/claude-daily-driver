#===============================================================================
#
# Makefile
#
#===============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

.PHONY: git_sync check check-plugin check-skills check-agents check-scripts \
	check-manifests check-constitution check-ask-in-chat check-omp-extension \
	check-eval-fixtures check-step-names check-infra evals-install \
	evals-plan evals-run mcp-usage

# The `coder_eval` release the eval suites are written against. Pinned on
# purpose: being able to hold a version back is the whole reason the suites are
# not written for `claude plugin eval`, which ships inside the CLI and moves
# when it does. See docs/notes/0002-eval-harness.md.
CODER_EVAL_VERSION := 0.11.6

# Usage telemetry is ON by default in `coder_eval`, to a UiPath-controlled
# Application Insights endpoint, via a connection string baked into the
# package. It is ingestion-only and documented, and it is still not something a
# tool that may one day gate a merge should do without being asked. The
# decision here is OFF, and it is made in the one place both eval targets go
# through so it cannot be forgotten at a prompt.
CODER_EVAL := TELEMETRY_ENABLED=false coder-eval

# git_sync: sync master with origin and delete local branches whose upstream
# is gone. Branches checked out in a linked worktree (marked '+' by
# `git branch -vv`) are reported as a warning rather than deleted — removal
# needs an explicit `git worktree remove`
git_sync:
	git checkout master
	git pull
	git fetch --prune
	git branch -vv | awk '/: gone\]/ && !/^\+/ {print $$1}' | xargs -r git branch -D
	@git branch -vv | awk '/: gone\]/ && /^\+/ {printf "WARN: worktree-linked branch kept (upstream gone): %s\n", $$2}' >&2


# check: everything CI asserts about this plugin. CI runs this target rather
# than restating its legs, so a leg added here is a leg CI gains — and there
# is no second command line to fall behind this one.
check: check-plugin check-skills check-agents check-scripts check-manifests \
	check-constitution check-ask-in-chat check-omp-extension \
	check-eval-fixtures check-step-names

# `claude plugin validate --strict` reads one manifest at a time and picks the
# marketplace when handed a directory, so the plugin manifest is named
# separately. --strict is what turns its warnings — unrecognized fields, a
# marketplace entry whose version disagrees with plugin.json — into failures.
check-plugin:
	claude plugin validate --strict .
	claude plugin validate --strict .claude-plugin/plugin.json

check-skills:
	claude plugin validate --strict skills

# `validate` reads one directory at a time, and skills and agents are separate
# component kinds, so the agent panel needs its own invocation or it is never
# checked at all.
#
# The guard is what keeps that true in both directions. The plugin ships no
# agents today -- the four reviewers live in `attic/agents/` -- and handed a
# directory with no components `validate` falls back to looking for a manifest,
# finds none, and fails. Deleting the leg instead would mean an agent revived
# by `git mv` comes back unvalidated and nothing says so, which is exactly the
# silent failure the attic's cheap-move promise must not buy.
check-agents:
	@if compgen -G 'agents/*.md' > /dev/null; then \
		claude plugin validate --strict agents; \
	else \
		echo 'no agents/ to validate; the panel is in attic/agents/'; \
	fi

# `validate --strict` is a floor, not a ceiling: measured against the CLI, it
# passes an agent with an empty description, one whose name disagrees with its
# filename, and two agents claiming the same name — the last of which makes one
# of them permanently unreachable. This is the leg that catches those, for
# skills and agents alike.
#
# It is also the leg that holds `0011`'s split: no SKILL.md body names a
# harness's own tool routes, every reference file is linked from the body, and
# every reference link resolves. A route written back into a body reads
# correctly on the harness it was written for, so nothing else catches it.
# See the docstring in the script.
check-manifests:
	python3 scripts/check-manifests.py

# The credential-free half of the constitution's acceptance test: run both
# delivery hooks against synthetic event JSON and assert the constitution's
# body comes back, identically, from each — with the Omp `alwaysApply`
# frontmatter validated and stripped. The live half needs a model and therefore
# credentials, so it is `make evals-run TASKS='tasks/constitution/*.yaml'`
# rather than a leg here -- see the script's docstring for where the seam is
# and why.
check-constitution:
	python3 scripts/check-constitution.py

# The acceptance test for the other hook: run `hooks/ask-in-chat.py` against
# synthetic event JSON and assert the AskUserQuestion widget is denied, with a
# reason that sends the question to the chat reply. Credential-free like
# check-constitution, and needed for the same reason -- a hook that stops
# firing does not fail, it just quietly gives the widget back. Unlike the
# constitution there is no live half: a denial is enforced by the harness
# rather than believed by a session. See the script's docstring.
check-ask-in-chat:
	python3 scripts/check-ask-in-chat.py

# The acceptance test for the Omp runtime adapter: import extensions/
# daily-driver.js with a fake ExtensionAPI and assert the Omp `ask` tool is
# blocked (with a reason that sends the question to chat), that the title and
# schedule/cancel tools behave, and that package.json wires the extension.
# Credential-free like the other script legs, so it runs on a laptop and CI
# alike. Node ships with the harness; no package install is involved.
check-omp-extension:
	node scripts/check-omp-extension.mjs

# check-scripts: lint the shell a skill ships. `claude plugin validate` reads
# manifests and never opens a `scripts/` file, so without this leg the plugin's
# executable half is the only part of the repository nothing checks.
#
# Unlike check-infra, this *is* part of `check`: shellcheck is a single small
# package present in the CI image, not a toolchain, so the laptop cost is one
# `apt install` rather than a reason to split the target.
#
# `-x` follows `source` directives so the eval fixtures' shared `lib.sh` is
# actually read rather than warned about; `--source-path=SCRIPTDIR` is what
# makes the `# shellcheck source=./lib.sh` annotations resolve beside the
# script rather than beside the caller's working directory.
check-scripts:
	shellcheck -x --source-path=SCRIPTDIR \
		skills/*/scripts/*.sh scripts/*.sh \
		evals/fixtures/*/shared/*.sh evals/fixtures/*/cases/*/*.sh

# check-eval-fixtures: build every review-depth fixture repository and assert
# it has the shape the `review` skill needs. Part of `check` because it needs
# only git and bash -- no model, no credentials -- and because a fixture that
# stops building does not turn the eval suite red, it turns every case into a
# silent 0 that reads exactly like a skill that never fires. See the script's
# docstring.
#
# This is not eval CI gating, which stays out of scope: nothing here runs a
# case or scores a model.
check-eval-fixtures:
	scripts/check-eval-fixtures.sh

# check-step-names: no file may cite a step of a numbered sequence by its
# number. The numbers are positional, so inserting a step silently invalidates
# every citation after it -- and a stale `step 7` reads exactly like a correct
# one. Part of `check` because it needs nothing but git and Python, and because
# the drift it catches is invisible to every other leg. See the script's
# docstring and docs/notes/0005-steps-are-cited-by-name.md.
check-step-names:
	python3 scripts/check-step-names.py

# check-infra: parse the OpenTofu stack without credentials. Not part of
# `check`, which must not start requiring OpenTofu on a laptop that is only
# editing a skill.
check-infra:
	$(MAKE) -C infra/github check-fmt validate

# evals-install: the pinned harness, from PyPI. `uv` fetches Python 3.13 itself,
# so this is the whole setup.
evals-install:
	uv tool install --python 3.13 coder-eval==$(CODER_EVAL_VERSION)

# evals-plan: validate every eval case without calling a model. Free, and it
# catches the config errors that otherwise cost a paid run to discover -- so
# run it before every `evals-run`.
#
# Both eval targets `cd evals` first, and that is load-bearing twice over. The
# plugin path in the experiment is relative and resolves against the process
# working directory, and `-e` must be passed explicitly because a wheel install
# of `coder-eval` resolves its default experiment to the one packaged inside
# the wheel and never looks in the working directory. Get either wrong and the
# suite runs -- against no plugin, or as a single unlabelled arm.
#
# Laptop-only, like git_sync: the cases need a live model, and this
# repository's CI is deliberately credential-free.
evals-plan:
	cd evals && $(CODER_EVAL) plan -e experiments/with-without.yaml tasks/*/*.yaml

# evals-run: the whole suite, both arms. Costs real money -- see evals/README.md
# for what and why. Narrow it with TASKS=, e.g.
#   make evals-run TASKS='tasks/pr/*.yaml'
TASKS ?= tasks/*/*.yaml
evals-run: evals-plan
	cd evals && $(CODER_EVAL) run -e experiments/with-without.yaml $(TASKS)

# mcp-usage: which GitHub MCP tools were actually called, rolled up to the
# toolsets that supply them. Laptop-only like git_sync — it reads Claude
# Code's session transcripts, which CI does not have — and deliberately not
# part of `check`. See docs/github-mcp.md for what the answer is for.
mcp-usage:
	python3 scripts/github-mcp-usage.py
