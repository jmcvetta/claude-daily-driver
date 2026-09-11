#!/usr/bin/env python3
"""Hold the two eval arms in step: one tag each way, and a pair for every fork.

Ten rows under `evals/tasks/` cannot be graded identically on Claude Code and
on Omp — the call they name differs, or the rule itself is Claude Code only per
`docs/notes/0011`. Each of those is two files: the Claude one tagged
`claude-only`, the Omp one tagged `omp-only`. `make evals-run` excludes
`omp-only` and `make evals-run-omp` excludes `claude-only`, so the tag is what
routes a row to its arm.

Nothing else checks that. A fork whose tag is missing runs in BOTH arms and
grades one harness's route under the other's, which fails for a reason that has
nothing to do with the skill. A Claude-only row whose tag is dropped does the
same in the other direction. And a fork deleted without its sibling leaves an
arm quietly measuring one row fewer than the other. None of those is visible in
a report; every one of them is visible here, in `make check`, for free.

WHAT IT ASSERTS

    No task carries both arm tags.
    Every `claude-only` suite has as many `omp-only` rows, and the other way
    about -- so a fork added or removed on one side is caught on the other.
    Every `task_id` in the tree is unique. Forking a file and forgetting its
    `task_id` is the easy mistake, and `coder_eval` keys its report on that id.
    A `task_id` that ends in `-omp` carries the `omp-only` tag, and no other
    task carries it. The name and the tag are two statements of the same fact.
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
from collections import Counter, defaultdict
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
    """One arm tag at most per row, and one fork per suite on each side."""
    per_suite: dict[str, Counter[str]] = defaultdict(Counter)
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
        for tag in arm_tags:
            per_suite[path.parent.name][tag] += 1

    for suite, counts in sorted(per_suite.items()):
        claude = counts[CLAUDE_TAG]
        omp = counts[OMP_TAG]
        if claude != omp:
            raise CheckFailed(
                f"suite {suite!r} has {claude} {CLAUDE_TAG} row(s) and {omp} {OMP_TAG} row(s); "
                "a forked row needs its counterpart, or one arm measures fewer rows than the other"
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
            "a fork with no counterpart",
            [(TASKS / "pr" / "x.yaml", {"task_id": "x", "tags": [CLAUDE_TAG]})],
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
    print(f"check-eval-arms: {len(tasks)} task(s), {forks} forked row(s) per arm, every experiment variant named")


if __name__ == "__main__":
    try:
        main()
    except CheckFailed as failure:
        print(f"check-eval-arms: {failure}", file=sys.stderr)
        sys.exit(1)
