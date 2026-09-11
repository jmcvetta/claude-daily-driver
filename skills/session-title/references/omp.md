# Omp routes — session-title

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).

One call: `daily_driver_set_session_title({ title })`. It takes the title
alone — the runtime adapter (`extensions/daily-driver.js`) applies it to the
current session, so there is no session id to look up first.

The runtime's own session-name limit is not measured here. The
forty-character budget in `SKILL.md` applies whatever it is, because the cap
is this skill's rather than the tool's.
