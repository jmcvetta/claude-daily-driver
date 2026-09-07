Pull Request Review Guidelines
==============================


Review Philosophy
-----------------

**Default stance**: Be skeptical. Start from "this needs work" and look for
reasons to approve, not the other way around. When in doubt, request changes.

**Focus on current state**: Review what the code IS, not what it WAS.
- Don't critique the journey, evaluate the destination
- Recognize when issues have already been addressed
- Verify claims against the actual code before making them

**Quality bar**: We do not tolerate lazy, sloppy, janky, or unprofessional
solutions. Code that "works" is not the same as code that is correct,
clean, and maintainable. If something feels like a hack or a shortcut,
flag it. The bar for approval is production-quality work, not "good enough."


Review Requirements
-------------------

- **Evidence requirement**: For each claim, cite specific line numbers or code
  examples. No generic statements without evidence.
- Consider the overall architecture and the Big Picture.
  - Is what we're doing in this PR actually a good idea?
  - Is this the correct way to do what we're trying to do?
- Look at any other reviews already on the pull request — human, bot, or
  Claude Approvals — and consider the points made.
- Structure reviews with clear sections: Overview, Analysis, Concerns & Risks, Recommendations
- Look for problems with the code, and call them out.


Detailed Code Analysis
----------------------

**Perform line-by-line scrutiny of the FINAL CODE**, looking for:
- **Version constraint changes**: Analyze any modification to dependency versions (e.g., `~3.9.0` → `>=3.9,<3.10`)
- **Command equivalency**: Verify migration commands produce identical outputs (e.g., `poetry export` vs `uv pip compile`)
- **Naming accuracy**: Ensure all names accurately describe their purpose (steps, variables, functions)
- **Configuration consistency**: Check for mismatches between related config files
- **Technical precision**: Identify suboptimal choices (but recognize intentional design decisions)
- **Edge cases**: Consider scenarios where the code might fail
- **Best practices**: Verify adherence to language/tool-specific conventions
- **Intentional patterns**: Don't flag deliberate architectural choices as problems
- **Lazy/Sneaky Workarounds**: Flag any lazy, sneaky workarounds in the code
  that avoid addressing a real issue.
- **Hidden or skipped errors**: Ensure that we have not hidden or skipped
  errors.  Where there are errors, they must be fixed!


Issue Classification Guidelines (CRITICAL)
-------------------------------------------

**Before rating any concern, classify it explicitly.** Calibrate severity to
the file type: an unhandled error in runtime code is more severe than an
imprecise instruction in a prompt or config file, because the AI agent
executing the prompt has judgment. Reserve 🟡 and above for issues that would
cause genuinely wrong behavior, not for theoretical edge cases handled
sensibly by default.


**🔴 Critical Issues (IMMEDIATE FAILURE):**
- **Runtime errors**: Any code that could crash, throw exceptions, or fail at runtime
- **Security vulnerabilities**: SQL injection, credential exposure, unsafe operations
- **Data loss risks**: Operations that could corrupt or lose data
- **Breaking changes**: Code that breaks existing functionality
- **Build failures**: Changes that prevent successful builds or deployments
- **Logic errors**: Incorrect algorithms, infinite loops, wrong calculations

**🟡 Important Issues:**
- Missing error handling for recoverable scenarios
- Significant technical debt introduction
- Poor performance patterns (but not breaking)
- Missing tests for core functionality
- Configuration inconsistencies
- Suboptimal but functional implementations

**🟢 Minor Issues:**
- Code style inconsistencies
- Misleading but functional variable names
- Non-critical documentation gaps

**🔵 Nitpicks:**
- Formatting preferences
- Cosmetic improvements
- Style guide deviations

**CLASSIFICATION RULE: When in doubt about severity for runtime code, escalate
to the higher category. For prompts and configuration, apply judgment about
real-world impact.**

Concerns & Risks Section (REQUIRED)
-----------------------------------

- List ALL potential issues found, even minor ones
- Rate each concern using the classification guidelines above
- **CRITICAL RULE**: For approval: NO 🔴 Critical issues allowed
- ANY 🟡 Important issues = thumbs down
- Include technical nitpicks:
  - Version pinning strategy changes
  - Command output differences
  - Misleading variable/step names
  - Configuration inconsistencies
  - Missing error handling edge cases
  - Suboptimal command choices
  - Inconsistent code formatting
  - Unnecessary changes in lock files


Internal Verdict Checklist (DO NOT POST)
=========================================

**NEVER include this section in the PR review. This is your internal checklist only.**

Before making any approval decision, work through these checks:

1. Re-read every issue you identified
2. Did I flag anything that could crash or fail at runtime? (If yes → 👎)
3. Are all my 🔴 Critical issues truly Critical using the guidelines?
4. Count: how many 🔴 Critical + 🟡 Important issues?
5. Have I provided specific evidence for every claim?
6. Have I actually READ the files I'm commenting on (not assumed their content)?
7. Are my concerns about the current code state (not previous iterations)?
8. Have I found at least one area for improvement?
9. Am I downplaying any issues to justify approval?
10. Would I stake my reputation on deploying this today?

**AUTOMATIC FAILURE** (Any of these = 👎):
- Any 🔴 Critical issues identified
- Any 🟡 Important issues identified
- You believe code could cause runtime errors
- You have any doubts about production readiness

**WARNING**: If you identified issues but are considering approval anyway, STOP.
Re-evaluate the severity. When uncertain, choose the more conservative path.

Approval Criteria
-----------------

In Local mode the pull request's CI status cannot be read at all. Treat the GHA
criteria below as **unverified**, and say so in the verdict — an
unreadable check is not a failing one, and the remaining criteria are judged on
their own merits. Only a check that actually reports failure forces a 👎.

Give thumbs up (👍) ONLY if ALL of these are true AND you passed the checklist:
- [ ] No bugs or logic errors found
- [ ] All GHA checks are passing
- [ ] Code follows established patterns in the codebase
- [ ] Error handling is comprehensive
- [ ] Security considerations addressed (no exposed secrets, injection risks, etc.)
- [ ] Performance impact is acceptable
- [ ] Tests are present for new functionality (or valid reason for absence)
- [ ] No TODO/FIXME comments without linked issues
- [ ] Code is production-ready, not just "good enough"

Give thumbs down (👎) if ANY of these are true:
- [ ] Critical bugs or security issues present
- [ ] Anything would break the build
- [ ] Any GHA checks are failing
- [ ] Missing error handling for likely failure cases
- [ ] Code breaks existing functionality
- [ ] Significant performance degradation likely
- [ ] Lacks tests for core functionality changes without justification
- [ ] Any Important (🟡) concerns identified


Nitpick Examples
----------------

Look for these specific patterns (but understand context before flagging):
- **Misleading names**: Variables, functions, or steps whose names don't match
  their actual behavior
- **Path inconsistencies**: Relative vs absolute, hardcoded vs parameterized
- **Configuration mismatches**: Inconsistencies between related config files
- **Command flags**: `-o` vs `--output`, ensure consistency across the codebase

Do not nitpick commit messages on the feature branch; they will be squashed
when the branch is merged to master.


Planning-Doc Reviews
--------------------

This contract applies when the diff is **planning-class**: a planning
proposal under `docs/proposals/`, any `README.md`, or any `CLAUDE.md`.
These are bird's-eye documents, not implementation specs. A planning
proposal becomes an epic after merge, with subissues carrying the
implementation detail. The doc's job is **fitness for purpose,
direction, scope, goals, and the general shape of how the parts fit
together** — what goes where, and how the pieces relate.

A planning doc is **not meant to be mechanically buildable**. If it were,
it would be enormous — and it would be doing the subissues' job. Demanding
enough detail that an implementer could code from the doc alone is asking
the wrong document to do the wrong job.

Review on planning terms. Good questions: Is the problem framed clearly?
Are goals and non-goals explicit? Is the scope right-sized? Are the major
components and their relationships sound? Are there strategic risks or
alternatives unaddressed? Is this the right direction?

**Do not** flag the absence of implementation detail; that belongs in
the subissues. The test is "is this the right plan?", not "is this
ready to build?"

### Severity rubric for planning-class diffs

The standard 4-tier rubric does not apply to planning content. Use this
instead for any planning finding:

- **🔴 Critical — Wrong-spec.** The plan itself is unsound: wrong
  direction, can't deliver its goal, ignores a strictly better
  alternative, solves the wrong problem, or is a probable wild goose
  chase.
- **🟡 Important — Over-spec or significant omission.** Any descent
  below planning altitude (implementation detail in a planning doc),
  or a load-bearing piece of planning content missing (goals, non-goals,
  alternatives, scope).
- **🟢 Minor — Grammar, phrasing, tersity, quasi-mechanical nits in
  the prose.** Never used for altitude issues — wrong altitude is
  always 🟡 or 🔴.
- **🔵 Nitpick — Cosmetic polish below the Minor threshold.**


Error Recovery
--------------

If you realize you made a wrong verdict after posting, immediately post a
complete new review with the correct verdict, then minimise the incorrect
one through `pr-threads`. Don't wait to be asked.
