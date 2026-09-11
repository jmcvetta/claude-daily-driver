# Claude Code routes — session-title

`SKILL.md` names each operation in words. This file names the call, for a
session running in Claude Code. Omp's routes are in [`omp.md`](omp.md).

Two calls, in order:

1. `mcp__Claude_Code_Remote__get_session` with `session_id` omitted —
   describes the caller, and answers this session's own id.
2. `mcp__Claude_Code_Remote__set_session_title` with that `session_id` and
   the title.

`set_session_title` accepts 500 characters. The forty-character budget in
`SKILL.md` is this skill's own cap, not the tool's.

Both tools exist only on the Claude Code Remote surface. Where they are
absent — a laptop session — there is no way to set the title from here.
