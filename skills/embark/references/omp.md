# Omp routes — embark

`SKILL.md` names each operation in words, and this file is where the calls for
a session running in Oh My Pi would be. There are none. Claude Code's routes
are in [`claude.md`](claude.md).


This skill does not run here
============================

**Omp has no session-opening client.** `epic` records the same thing from the
other end: it writes a `Model:` line into every task issue it opens, and says
that nothing on this harness reads that line, because the line is written for
`embark` and `embark` runs on Claude Code.

Dispatch is the whole skill. An orchestrator that cannot open a session has no
fleet to muster, no muster roll worth posting, and nothing to watch — the
watch is over pull requests that would not exist. Opening the epic's tasks one
after another in this session is not a smaller version of this skill: it is
the serial run the skill exists to replace, and it is `undertake` invoked once
per task with nothing in between.

So on this harness: **say the skill does not run, name the task issues whose
blockers are closed, and stop.** That is `epic`'s `Hand off` reached without a
fleet, and it leaves the user holding exactly what they need to put the wave
to sea from a harness that can.

Reading the epic to name those tasks is ordinary work and needs nothing from
here — `epic`'s own Omp routes have the issue reads, and `issue-deps` has the
graph.


The durable wake is missing too
===============================

Even given a session client, the watch would not survive. `undertake`'s Omp
routes record the measurement: Omp's managed timers are unref'd and cleared on
`session_shutdown`, so a reminder dies with the session and there is no
`send_later` to hold a wake slot with. A watch over a fleet is a watch across
many turns and many hours, so it is the half of this skill that depends on a
durable wake most.

This is recorded so that a session-opening client arriving in Omp later is not
read as enough on its own. Two things are missing, and this is the second.
