#!/usr/bin/env python3
"""Refuse to start an eval run whose `llm_judge` criteria cannot execute.

`coder_eval`'s `llm_judge` criterion needs a judge transport that is separate
from whatever authenticates the agent under test. On the default DIRECT
backend, `models/routing.py::_resolve_direct_judge_transport` picks the
transport "anthropic" iff `ANTHROPIC_API_KEY` is set, and `None` otherwise.
When it is `None`, `criteria/llm_judge.py` does not fail the run — it returns
score 0.0 with `details="(judge transport unconfigured)"`, logs one ERROR
line, and the run **continues**. The BEDROCK and LITELLM backends always have
a usable judge transport; only DIRECT can be unconfigured this way.

That "continues" is the defect this guards against. Running
`tasks/session-title/01-get-session-before-set.yaml` in a container with no
`ANTHROPIC_API_KEY` produced an `experiment.md` reading `Score 0.000 (bare) /
0.333 (with-plugin)`, `Best: with-plugin`, `Win Rates — with-plugin: 1/1 tasks
(100%)`. That reads as a clean ablation. The entire 0.333 was the weight-1
`skill_triggered` criterion; the weight-2 `llm_judge` — the one carrying the
actual finding — never ran. Nothing in the report says so: the per-replicate
log carries `API routing: anthropic_direct (judge transport: none)` and the
ERROR line, and `task.json` records `environment_info["judge_transport"]`,
but neither reaches the report a reader actually looks at. Eight of the nine
`references`-tagged rows in this suite carry their finding in a weight-2
`llm_judge`, so this one missing key silently voids most of that suite.
See docs/notes/0012-the-judge-needs-its-own-transport.md for why the fix is a
pre-run guard rather than reading the report more carefully after the fact.

This script mirrors the upstream resolution rule (`API_BACKEND`, default
`direct`, case-insensitive; non-direct backends always pass; `direct` needs
`ANTHROPIC_API_KEY`) and refuses to let `evals-run` start a model when it
would not.

`.env` HANDLING

    `coder_eval.config` calls `load_dotenv(override=True)` at import, so a
    `.env` file can supply `ANTHROPIC_API_KEY` even when the shell environment
    does not. Which `.env` that is was established empirically (not assumed),
    by instrumenting `dotenv.main._walk_to_root` and running the real
    `coder-eval` entry point with `cwd=evals/`, the same cwd `evals-run` uses:

    - `load_dotenv(override=True)` takes no explicit path, so it falls to
      `find_dotenv()`, which walks upward from the directory holding the
      *installed* `coder_eval` package (e.g.
      `.../site-packages/coder_eval`) — not from the process cwd. In this
      container that chain carries no `.env` at all, so this call is a
      no-op here. Where the tool is installed varies by machine, so this
      script cannot search that chain in general — see WHAT IT DOES NOT
      CATCH.
    - Immediately after, `config.py` separately does
      `dotenv_values(".env")` — a literal, cwd-relative path — and, for
      `ANTHROPIC_API_KEY` specifically, force-sets it into `os.environ`
      when present, overriding both the shell and whatever the first call
      loaded. `Settings.model_config` also declares `env_file=".env"`,
      read the same cwd-relative way. Both of the mechanisms that can
      actually decide `ANTHROPIC_API_KEY` therefore agree: a `.env` in the
      process's cwd.
    - `evals-run` always runs `coder-eval` with `cwd=evals/` (the Makefile
      `cd`s there first), and this script is wired to run the same way — see
      the `Makefile`'s `evals-preflight` target — so "cwd-relative" means
      `evals/.env` in practice.

    So this script reads `ANTHROPIC_API_KEY` from a `.env` in its own cwd,
    the same way `dotenv_values(".env")` would, using `python-dotenv` itself
    rather than a hand-rolled parser. If `python-dotenv` is not importable
    (it is not a dependency of this repository's own tooling — only of the
    separately-installed `coder-eval` tool), `.env` parsing is skipped
    entirely and only the shell environment is checked; that is a
    conservative (fail-closed) gap, documented below.

WHAT IT FLAGS

    A task YAML with at least one `success_criteria` entry whose `type` is
    `llm_judge` and whose `enabled` is not `false`, when the judge transport
    that criterion would need is not configured: `API_BACKEND` (default
    `direct`, case-insensitive) is `direct` and `ANTHROPIC_API_KEY` is empty
    in both the shell environment and (when readable) `./.env`.

WHAT IT DOES NOT CATCH

    - A `.env` reachable only through `load_dotenv(override=True)`'s
      upward search from the *installed* `coder_eval` package directory,
      rather than from cwd. That search's start point depends on where
      `coder-eval` happens to be installed (a `uv tool install` prefix, a
      user site-packages, a venv), which this script has no reliable way
      to locate. If such a `.env` supplies `ANTHROPIC_API_KEY` and neither
      the shell environment nor `evals/.env` does, this script reports a
      failure the real run would not hit.
    - `python-dotenv` not installed for the interpreter running this
      script: `.env` is not read at all, and only the shell environment is
      checked. Same direction of error as above — a false failure, never a
      false pass.
    - Any transport failure that is not "unconfigured" — an expired key, a
      network error, a Bedrock credential that is present but wrong. Those
      fail at call time, mid-run, the way any other API error does; this
      guard only catches the case upstream depoliticizes into a silent 0.0.
    - Malformed task YAML that parses but has the wrong shape for
      `coder_eval`'s own schema. `evals-plan` is what validates that.

Both directions of error are asymmetric by design: this script is
conservative (may refuse a run that would have worked, in the two gaps
above) and never permissive (never lets through a run whose `llm_judge`
criteria are guaranteed not to execute).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - PyYAML is a house-wide given
    print(f"error: PyYAML is required to read task YAML ({exc})", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import dotenv_values

    _HAVE_DOTENV = True
except ImportError:
    _HAVE_DOTENV = False

# Verbatim from coder_eval.criteria.llm_judge's dispatch-time error, so the
# remedy a reader sees here is the same one they would see if this guard did
# not exist and the criterion failed mid-run instead.
_UPSTREAM_REMEDY = (
    "llm_judge needs the run to use a backend that can reach a judge model:\n"
    "  - Bedrock (--backend bedrock), or\n"
    "  - Anthropic direct with ANTHROPIC_API_KEY set.\n"
    "Set one of the above, or remove/disable the llm_judge criterion."
)


def has_enabled_llm_judge(task: object) -> bool:
    """True if `task` (a parsed task YAML) carries a live `llm_judge` row.

    "Live" means `type: llm_judge` and not explicitly `enabled: false` —
    the same gate `LLMJudgeChecker._check_impl_async` applies before it
    would otherwise call a model.
    """
    if not isinstance(task, dict):
        return False
    criteria = task.get("success_criteria")
    if not isinstance(criteria, list):
        return False
    for criterion in criteria:
        if not isinstance(criterion, dict):
            continue
        if criterion.get("type") == "llm_judge" and criterion.get("enabled", True) is not False:
            return True
    return False


def anthropic_api_key_present() -> bool:
    """True if `ANTHROPIC_API_KEY` would be non-empty by the time `coder_eval`
    resolves the DIRECT route — shell environment first, then a cwd-relative
    `.env`, matching `coder_eval.config`'s own precedence for this one key.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    if _HAVE_DOTENV:
        dotenv_path = Path(".env")
        if dotenv_path.is_file():
            value = dotenv_values(dotenv_path).get("ANTHROPIC_API_KEY")
            if value:
                return True
    return False


def judge_transport_available() -> bool:
    """True if `coder_eval` will resolve a usable `llm_judge` transport.

    Mirrors `models/routing.py::_resolve_direct_judge_transport` and its
    caller: non-DIRECT backends (`bedrock`, `litellm`) always carry a
    transport; DIRECT (the default) needs `ANTHROPIC_API_KEY`.
    """
    backend = os.environ.get("API_BACKEND", "direct").strip().lower()
    if backend != "direct":
        return True
    return anthropic_api_key_present()


def main(argv: list[str]) -> int:
    if not argv:
        print("evals-preflight: no task files given; nothing to check")
        return 0

    offending: list[tuple[str, str]] = []
    read_errors: list[str] = []
    for arg in argv:
        path = Path(arg)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            read_errors.append(f"{arg}: {exc}")
            continue
        try:
            task = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            read_errors.append(f"{arg}: invalid YAML ({exc})")
            continue
        if has_enabled_llm_judge(task):
            task_id = task.get("task_id") if isinstance(task, dict) else None
            offending.append((arg, task_id or arg))

    if read_errors:
        for error in read_errors:
            print(f"error: {error}", file=sys.stderr)
        print(
            "\nevals-preflight could not read every task file given; fix the "
            "above before running.",
            file=sys.stderr,
        )
        return 1

    if not offending:
        print(f"evals-preflight: no enabled llm_judge criteria in {len(argv)} task file(s)")
        return 0

    if judge_transport_available():
        print(
            f"evals-preflight: judge transport available; {len(offending)} "
            f"llm_judge row(s) among {len(argv)} task file(s) can run"
        )
        return 0

    print(
        f"error: {len(offending)} row(s) carry an enabled llm_judge criterion, "
        "and no judge transport is configured for this run:",
        file=sys.stderr,
    )
    for arg, task_id in offending:
        print(f"  - {task_id} ({arg})", file=sys.stderr)
    print(f"\n{_UPSTREAM_REMEDY}", file=sys.stderr)
    print(
        "\nThe run was NOT started. Proceeding would produce a report whose "
        "llm_judge finding criteria never execute — coder_eval scores each as "
        "0.0 and continues, so the report reads like a real result and is not "
        "one.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
