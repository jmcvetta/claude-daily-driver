---
# The finding itself: the subagent knew a token nobody told it, which can only
# have arrived through `updatedInput`. The baseline arm — no plugin, no hook —
# is expected to fail this grader, and that delta is the measurement.
type: regex
target: last_message
pattern: 'constitution-token:\s*tin-badger-quorum-9317'
match: contains
weight: 2
---
