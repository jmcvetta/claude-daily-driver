# Waiting for CI is a loop of turns, never a sleep

**Status:** decided, 2026-09-08.
**Provenance:** chosen by an agent in
[#100](https://github.com/jmcvetta/claude-daily-driver/pull/100) — the same
pull request as the change it justifies — and ratified by that merge.
**Resolves:** [#96](https://github.com/jmcvetta/claude-daily-driver/issues/96).

`review-cycle` opened `Review the head` with *"Wait for CI to report on the
pushed head first"* and stopped there. The requirement had no mechanism —
neither here, nor in `undertake`, which delegates the same wait to it. Nothing
in the repository said how to wait.

So sessions improvised, and the improvisation was a backgrounded `sleep`: a job
named *"Wait ~3 minutes for CI"*. It never came back. CI finished, the job sat
until it timed out, and the round stalled before the review it was waiting to
run. That is #96, reported from a live session.

## Decided

**The wait is a loop of turns: read the checks, wake later, read again, capped.**
`review-cycle`'s `How to wait` carries the calls, the two-minute interval and
the fifteen-minute cap. Both numbers are chosen rather than measured; a
measurement is what may move them.

The shape follows from who can read a check. GitHub is reached through the MCP,
and only the model can call an MCP tool — not a shell, and not a background
job. The read is therefore something only a turn can do, so the delay between
two reads has to be something that ends a turn and starts another. On the
Claude Code Remote surface that is `mcp__Claude_Code_Remote__send_later`, whose
delivery is scheduler-side and survives a container restart.

**Rejected: a `sleep`, foreground or backgrounded.** A sleep is a timer, and a
timer answers a different question than the one being asked — it expires while
the checks are still queued as readily as it expires long after they went
green. Backgrounded it also has the failure #96 reports, and a wait that
depends on a process nobody is watching is a wait that can be lost. On this
surface a foreground `sleep` is refused outright.

**Rejected: a shell wait — `Monitor`, a backgrounded `until` loop, or a
blocking `gh pr checks --watch`.** This is the harness's own advice for waiting
on a condition, and it is right where a human is watching the terminal. It is
not right for a wait nobody is attending, and the reason is not that a shell
cannot read GitHub — where `gh` is installed and authenticated, it can, which
is why `How to wait` prescribes exactly that on a laptop. It is that neither
shape survives the session: in the foreground the watch is bounded by the Bash
tool's timeout, and refused outright on a surface that blocks `sleep`; in the
background it is bounded by nothing and cannot wake the session, which is #96.

**Rejected: `mcp__Claude_Code_Remote__subscribe_pr_activity`.** It is the exact
instrument — CI results arrive as wake events, with no polling at all — and it
is not reliably this session's to use: where a steward already watches the pull
request, the subscription call succeeds and the events go elsewhere. That case
is *detectable*, and the note first said otherwise: the tool documents that its
result says so. So the rejection is not silence. It is that the fallback loop
has to exist anyway, for the pull request a steward holds and for the surface
where the tool is absent — and a round carrying both mechanisms would be two
things to get right where one will do. A session that already holds the
subscription is welcome to the events; the loop is what the round is written
against.

**A surface with no wake performs no wait.** Where `send_later` does not exist
and the surface has nothing to block on, `How to wait` reads the checks once
and stops with a line naming what has not reported. Stopping is honest and the
user can answer it. A wait that is only claimed cannot be.
