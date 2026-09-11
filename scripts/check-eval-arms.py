#!/usr/bin/env python3
"""Hold the two eval arms in step: one tag each way, and a pair for every fork.

Ten rows under `evals/tasks/` cannot be graded identically on Claude Code and
on Omp — the call they name differs, or the rule itself is Claude Code only per
`docs/notes/0011`. Each of those is two files: the Claude one tagged
`claude-only`, the Omp one tagged `omp-only`. `make evals-run` excludes
`omp-only` and `make evals-run-omp` excludes `claude-only`, so the tag is what
routes a row to its arm.

The `review-depth` rows are tagged `claude-only` too, without a counterpart:
they pin `agent.type: claude-code` and drive Claude's own settings and hooks,
so they have no Omp form at all. Untagged, they would run inside the Omp arm as
Claude sessions and be reported as Omp results.

Nothing else checks any of that. A fork whose tag is missing runs in BOTH arms
and grades one harness's route under the other's, which fails for a reason that
has nothing to do with the skill. A sibling that loses its own tag does the
same in the other direction. Neither is visible in a report; both are visible
here, in `make check`, for free.

WHAT IT ASSERTS

    No task carries both arm tags.
    Every `omp-only` row names the Claude row it forks, as a `forks:<task_id>`
    tag, and that row exists and is tagged `claude-only`. Seven of the ten
    forks are not their sibling's name plus `-omp` -- the sibling's name states
    Claude's route, which on Omp is the wrong answer -- so the pairing is
    declared rather than inferred from a filename. It is also what catches the
    sibling losing its own tag, which would run Claude's route in the Omp arm.
    Every `task_id` in the tree is unique. Forking a file and forgetting its
    `task_id` is the easy mistake, and `coder_eval` keys its report on that id.
    A `task_id` that ends in `-omp` carries the `omp-only` tag, and no other
    task carries it. The name and the tag are two statements of the same fact.
    A task that pins `agent.type` is tagged for the arm that kind belongs to.
    The `review-depth` rows pin `claude-code` because they drive Claude's own
    settings and hooks, and an untagged one would run in the Omp arm as a
    Claude session -- billed to that arm, and reported as it.
    Every experiment file parses, declares variants, and names an agent kind
    for each -- read with `evals-variants.py`'s own parser, so the parser that
    guards a paid run is itself exercised here.

WHAT IT DOES NOT ASSERT

    That an arm resolves to a registered agent. That needs a `coder-eval`
    install, so it is `make evals-plan`'s guard (`scripts/evals-variants.py`)
    rather than a `check` leg.
    That the two halves of a fork grade equivalent rules. Nothing but reading
    them can say that.

No third-party imports beyond PyYAML, which `evals-preflight.py` already
requires of this repository.
"""

from __future__ import annotations

import sys
from pathlib import Path


try:
    import yaml
except ImportError as exc:  # pragma: no cover - PyYAML is a house-wide given
    print(f"error: PyYAML is required to read task YAML ({exc})", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "evals" / "tasks"
EXPERIMENTS = ROOT / "evals" / "experiments"

CLAUDE_TAG = "claude-only"
OMP_TAG = "omp-only"

# The namespaced tag an Omp row names its Claude sibling with. `coder_eval`
# accepts a `key:value` tag, so the pairing needs no field of its own.
FORK_TAG = "forks:"


class CheckFailed(Exception):
    """A failed assertion, with the detail that explains it."""


def _load_variant_kinds():
    """`evals-variants.py`'s experiment parser, loaded from its own file.

    The guard's filename carries a hyphen, so it is not importable by name.
    Loading it by path is what keeps ONE parser between the free check here and
    the guard that stands in front of a paid run.
    """
    import importlib.util

    path = ROOT / "scripts" / "evals-variants.py"
    spec = importlib.util.spec_from_file_location("evals_variants", path)
    if spec is None or spec.loader is None:
        raise CheckFailed(f"could not load {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.variant_kinds


def load_tasks() -> list[tuple[Path, dict]]:
    """Every task file under `evals/tasks/`, parsed, with its path."""
    tasks: list[tuple[Path, dict]] = []
    for path in sorted(TASKS.glob("*/*.yaml")):
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CheckFailed(f"{path.relative_to(ROOT)} does not parse: {exc}") from exc
        if not isinstance(document, dict):
            raise CheckFailed(f"{path.relative_to(ROOT)} does not parse as a mapping")
        tasks.append((path, document))
    if not tasks:
        raise CheckFailed(f"no task files under {TASKS.relative_to(ROOT)}")
    return tasks


def check_arm_tags(tasks: list[tuple[Path, dict]]) -> None:
    """One arm tag at most per row, and every fork paired with its sibling."""
    claude_rows: dict[str, Path] = {}
    forks: list[tuple[Path, str]] = []

    for path, document in tasks:
        tags = document.get("tags") or []
        if not isinstance(tags, list):
            raise CheckFailed(f"{path.relative_to(ROOT)}: `tags` is not a list")
        arm_tags = [tag for tag in (CLAUDE_TAG, OMP_TAG) if tag in tags]
        if len(arm_tags) > 1:
            raise CheckFailed(
                f"{path.relative_to(ROOT)} carries both arm tags; a row belongs to one arm or to both, "
                "and both is spelled by carrying neither"
            )
        task_id = document.get("task_id")
        if CLAUDE_TAG in tags and isinstance(task_id, str):
            claude_rows[task_id] = path

        declared = [tag.split(":", 1)[1] for tag in tags if isinstance(tag, str) and tag.startswith(FORK_TAG)]
        if OMP_TAG in tags:
            if len(declared) != 1:
                raise CheckFailed(
                    f"{path.relative_to(ROOT)}: an {OMP_TAG} row must name the Claude row it forks, "
                    f"as exactly one `{FORK_TAG}<task_id>` tag; found {declared}"
                )
            forks.append((path, declared[0]))
        elif declared:
            raise CheckFailed(f"{path.relative_to(ROOT)}: carries a `{FORK_TAG}` tag but is not tagged {OMP_TAG}")

        pinned = document.get("agent")
        pinned_kind = pinned.get("type") if isinstance(pinned, dict) else None
        if pinned_kind == "claude-code" and CLAUDE_TAG not in tags:
            raise CheckFailed(
                f"{path.relative_to(ROOT)}: pins `agent.type: claude-code` but is not tagged {CLAUDE_TAG}, "
                "so the Omp run would bill a Claude session to the Omp arm and report it as one"
            )
        if pinned_kind == "omp" and OMP_TAG not in tags:
            raise CheckFailed(f"{path.relative_to(ROOT)}: pins `agent.type: omp` but is not tagged {OMP_TAG}")

    for path, sibling in forks:
        if sibling not in claude_rows:
            raise CheckFailed(
                f"{path.relative_to(ROOT)} forks {sibling!r}, which is not a task tagged {CLAUDE_TAG}; "
                "either the sibling lost its tag — and now runs in both arms — or the id is wrong"
            )


def check_task_ids(tasks: list[tuple[Path, dict]]) -> None:
    """Ids are unique, and an `-omp` id is an `omp-only` row."""
    seen: dict[str, Path] = {}
    for path, document in tasks:
        task_id = document.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise CheckFailed(f"{path.relative_to(ROOT)} declares no task_id")
        if task_id in seen:
            raise CheckFailed(
                f"task_id {task_id!r} is used by both {seen[task_id].relative_to(ROOT)} and "
                f"{path.relative_to(ROOT)}; coder_eval keys its report on it"
            )
        seen[task_id] = path

        tags = document.get("tags") or []
        if task_id.endswith("-omp") and OMP_TAG not in tags:
            raise CheckFailed(f"{path.relative_to(ROOT)}: task_id ends in -omp but the row is not tagged {OMP_TAG}")
        if OMP_TAG in tags and not task_id.endswith("-omp"):
            raise CheckFailed(f"{path.relative_to(ROOT)}: tagged {OMP_TAG} but its task_id does not end in -omp")


def check_experiments() -> None:
    """Every experiment resolves to named variants, read by the run guard's parser."""
    variant_kinds = _load_variant_kinds()

    files = sorted(EXPERIMENTS.glob("*.yaml"))
    if not files:
        raise CheckFailed(f"no experiment files under {EXPERIMENTS.relative_to(ROOT)}")
    for path in files:
        try:
            variants = variant_kinds(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            raise CheckFailed(f"{path.relative_to(ROOT)}: {exc}") from exc
        for variant_id, kind in variants:
            if not kind:
                raise CheckFailed(f"{path.relative_to(ROOT)}: variant {variant_id!r} names no agent type")


def check_the_checks() -> None:
    """Prove the assertions above can fail, against synthetic rows.

    A check that cannot fail is a check that passes for ever, silently, which
    is the same class of defect as the drift it is here to catch. These rows
    never touch the filesystem, so the cost is nothing.
    """
    cases: list[tuple[str, list[tuple[Path, dict]], object]] = [
        (
            "both arm tags on one row",
            [(TASKS / "pr" / "x.yaml", {"task_id": "x", "tags": [CLAUDE_TAG, OMP_TAG]})],
            check_arm_tags,
        ),
        (
            "an omp row naming no sibling",
            [(TASKS / "pr" / "x.yaml", {"task_id": "x-omp", "tags": [OMP_TAG]})],
            check_arm_tags,
        ),
        (
            "an omp row whose sibling is not tagged",
            [
                (TASKS / "pr" / "x.yaml", {"task_id": "x-omp", "tags": [OMP_TAG, f"{FORK_TAG}x"]}),
                (TASKS / "pr" / "y.yaml", {"task_id": "x", "tags": []}),
            ],
            check_arm_tags,
        ),
        (
            "a claude-code task with no arm tag",
            [(TASKS / "pr" / "x.yaml", {"task_id": "x", "tags": [], "agent": {"type": "claude-code"}})],
            check_arm_tags,
        ),
        (
            "a duplicated task_id",
            [
                (TASKS / "pr" / "a.yaml", {"task_id": "same", "tags": []}),
                (TASKS / "pr" / "b.yaml", {"task_id": "same", "tags": []}),
            ],
            check_task_ids,
        ),
        (
            "an -omp id without the arm tag",
            [(TASKS / "pr" / "a.yaml", {"task_id": "pr-01-omp", "tags": []})],
            check_task_ids,
        ),
        (
            "an omp-only tag without the -omp id",
            [(TASKS / "pr" / "a.yaml", {"task_id": "pr-01", "tags": [OMP_TAG]})],
            check_task_ids,
        ),
    ]
    for name, rows, checker in cases:
        try:
            checker(rows)  # type: ignore[operator]
        except CheckFailed:
            continue
        raise CheckFailed(f"the check for {name!r} did not fail on a row that should fail it")


def main() -> None:
    check_the_checks()
    tasks = load_tasks()
    check_arm_tags(tasks)
    check_task_ids(tasks)
    check_experiments()
    forks = sum(1 for _, document in tasks if OMP_TAG in (document.get("tags") or []))
    print(f"check-eval-arms: {len(tasks)} task(s), {forks} fork(s) paired with their siblings, every variant named")


if __name__ == "__main__":
    try:
        main()
    except CheckFailed as failure:
        print(f"check-eval-arms: {failure}", file=sys.stderr)
        sys.exit(1)
