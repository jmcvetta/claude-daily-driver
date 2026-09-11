#!/usr/bin/env python3
"""The acceptance test for `scripts/evals-preflight.py`.

The constitution carries the rule *code without tests is broken*, and a
pre-run guard is exactly the kind of script that rule is aimed at: it runs
once, right before real money gets spent, and a guard that silently stopped
guarding would look identical to one still doing its job.

This drives the real script — the actual file, as a subprocess, with a
controlled environment — against synthetic task YAML written into a
`tempfile.TemporaryDirectory()`. No model, no credentials, no network: every
case below asserts on exit code and stderr content alone, so this belongs in
`make check` and in a CI that holds no `ANTHROPIC_API_KEY`.

WHAT IT COVERS

    - A row with an enabled `llm_judge` and no `ANTHROPIC_API_KEY` on the
      (default) direct backend fails the guard.
    - The same row passes once `ANTHROPIC_API_KEY` is set.
    - The same row passes on `API_BACKEND=bedrock` with no key at all.
    - A row with only non-judge criteria passes with no key.
    - A row whose `llm_judge` is `enabled: false` passes with no key.
    - The failure message names the offending row's `task_id`.

WHAT IT DOES NOT COVER

    The `.env`-reading half of the guard: whether `python-dotenv` is
    importable for the interpreter running it varies by machine, and a test
    that depended on that would pass or fail for a reason that has nothing to
    do with the guard being right. Every case here relies on the shell
    environment alone (no `.env` file is ever written), which exercises the
    same code path regardless of which way that import goes. See the
    script's own docstring for what its `.env` handling does and does not
    catch.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "evals-preflight.py"

# A minimal but real success_criteria shape for each case. `task_id` is what
# the failure message is expected to name.
JUDGE_TASK = """\
task_id: fixture-judge-task
success_criteria:
  - type: skill_triggered
    expected_skill: some-skill
    skill_name: some-skill
  - type: llm_judge
    description: a graded finding
    prompt: does it work
"""

DISABLED_JUDGE_TASK = """\
task_id: fixture-disabled-judge-task
success_criteria:
  - type: llm_judge
    description: a graded finding, turned off
    prompt: does it work
    enabled: false
"""

NON_JUDGE_TASK = """\
task_id: fixture-non-judge-task
success_criteria:
  - type: command_executed
    description: a command ran
    command: echo hi
"""


class Failed(Exception):
    """A case that did not hold. The message is the report."""


def run(tmpdir: Path, files: dict[str, str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Write `files` into `tmpdir`, then run the guard against their names.

    `cwd=tmpdir` matters twice over: it is where the guard would look for a
    cwd-relative `.env` (none is ever written here, so that path is inert
    either way — see the module docstring), and it is what makes the
    relative task-file names in `files` resolve.
    """
    for name, content in files.items():
        (tmpdir / name).write_text(content, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), *files],
        capture_output=True,
        text=True,
        cwd=tmpdir,
        env=env,
    )


def base_env(tmp_home: Path, **overrides: str) -> dict[str, str]:
    """A minimal environment with no `ANTHROPIC_API_KEY` and no `API_BACKEND`,
    so each case controls exactly the knobs it means to test. `HOME` is
    redirected to an empty directory so a real developer `.env` or credential
    file elsewhere on the machine cannot leak into the result.
    """
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_home)}
    env.update(overrides)
    return env


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Failed(message)


def main() -> int:
    errors: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        home = tmpdir / "home"
        home.mkdir()
        workdir = tmpdir / "work"
        workdir.mkdir()

        # 1. llm_judge, no key, default (direct) backend -> fails.
        result = run(workdir, {"judge.yaml": JUDGE_TASK}, env=base_env(home))
        if result.returncode != 1:
            errors.append(
                "case 1 (llm_judge, no key, direct backend): expected exit 1, "
                f"got {result.returncode}\nstderr: {result.stderr}"
            )
        if "fixture-judge-task" not in result.stderr:
            errors.append(
                "case 1: failure message does not name the offending row's "
                f"task_id ('fixture-judge-task')\nstderr: {result.stderr}"
            )

        # 2. same row, ANTHROPIC_API_KEY set -> passes.
        result = run(
            workdir,
            {"judge.yaml": JUDGE_TASK},
            env=base_env(home, ANTHROPIC_API_KEY="sk-ant-fixture"),
        )
        if result.returncode != 0:
            errors.append(
                "case 2 (llm_judge, ANTHROPIC_API_KEY set): expected exit 0, "
                f"got {result.returncode}\nstderr: {result.stderr}"
            )

        # 3. same row, API_BACKEND=bedrock, no key -> passes.
        result = run(
            workdir,
            {"judge.yaml": JUDGE_TASK},
            env=base_env(home, API_BACKEND="bedrock"),
        )
        if result.returncode != 0:
            errors.append(
                "case 3 (llm_judge, API_BACKEND=bedrock, no key): expected "
                f"exit 0, got {result.returncode}\nstderr: {result.stderr}"
            )

        # 4. only non-judge criteria, no key -> passes.
        result = run(workdir, {"plain.yaml": NON_JUDGE_TASK}, env=base_env(home))
        if result.returncode != 0:
            errors.append(
                "case 4 (no llm_judge criterion, no key): expected exit 0, "
                f"got {result.returncode}\nstderr: {result.stderr}"
            )

        # 5. llm_judge with enabled: false, no key -> passes.
        result = run(workdir, {"disabled.yaml": DISABLED_JUDGE_TASK}, env=base_env(home))
        if result.returncode != 0:
            errors.append(
                "case 5 (llm_judge enabled: false, no key): expected exit 0, "
                f"got {result.returncode}\nstderr: {result.stderr}"
            )

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print("evals-preflight guard behaves correctly; 5 case(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
