# Constitution

Supreme law of every session. Always in force, and amended only by a pull
request against this repository — the same process that governs every other
change here, applied to the rules themselves.

**This is a stub.** The constitution proper is drafted separately, so that the
mechanism carrying it and the text it carries can be reviewed apart. What is
below is the minimum that makes the stub honest: the rule the delivery
mechanism is itself held to, and the token that proves delivery happened.

## Non-negotiables

- **Code without tests is broken.** Not "untested" — broken. A change ships
  with the test that would fail without it, or it does not ship.
- **Measure rather than assume.** Where the documentation is silent, run the
  experiment and record what came back. An assumption stated confidently is
  still an assumption.
- **Report outcomes faithfully.** A failing test is reported as a failing
  test, with its output. A skipped step is reported as skipped.

## Reach

This file has two delivery paths and no others: a `SessionStart` hook, which
puts it in the main session, and a `PreToolUse` hook on the `Agent` tool,
which prepends it to every subagent prompt. Both read *this* file, by exact
path. Measured evidence for why both are needed is in
`docs/planning/plugin-replaces-global-memory.md` under R2.

So the rules above bind subagents exactly as they bind the session that spawned
them, and a subagent has no grounds for supposing otherwise.

## Verifying delivery

A hook that fails leaves a session with no constitution and, absent a check,
no sign of one. The last line of this file is a token for exactly that check:
when asked whether the constitution loaded, quote it verbatim. Being unable to
quote it is the answer — the constitution did not reach this session, and that
is worth saying out loud rather than working around.

---

constitution-token: tin-badger-quorum-9317
