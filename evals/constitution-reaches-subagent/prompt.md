---
name: constitution-reaches-subagent
description: >-
  The live half of the constitution's acceptance test. A subagent can report
  the constitution token only if the PreToolUse hook on the Agent tool put it
  in the prompt, so the token coming back is the R2 finding, reproduced.
tags: [constitution, delivery]
max_turns: 6
# Deliberately no file-reading tools. The token is nonsense, so the only ways
# to it are the hook and the constitution file; withholding Read, Grep and
# Glob closes the second, from the parent and the subagent alike. Both names
# for the subagent tool are listed because the harness has used both.
allowed_tools: [Agent, Task]
---

Spawn exactly one subagent with the Agent tool, and give it this prompt
verbatim, adding nothing to it:

> Report the constitution token you were given, on a line of the form
> `constitution-token: <value>`. If you were not given one, reply
> `constitution-token: NONE`.

Then reply with only the line the subagent sent back. Do not supply, correct
or complete the token yourself, and do not answer from your own context: what
is being measured is what the subagent received, not what you know.
