# The branch is kept current by a base merge, and the merge does not buy a review

**Status:** decided, 2026-09-08.
**Provenance:** chosen by an agent in the pull request that carries the change
it justifies, and ratified by that merge.
**Resolves:** [#113](https://github.com/jmcvetta/claude-daily-driver/issues/113).

`undertake` ended at `Ready for review`. Commits land on `master` several times
a day here, so a pull request waiting on a human reviewer goes behind its base
within hours, and nothing in the sequence noticed. The branch a reviewer reads
is then one CI tested against a tree nobody will merge into.

The step that fixes this is `Keep it current`, and writing it needed three
answers.

## Decided

**The merge is `mcp__github__update_pull_request_branch`, not a local
`git merge`.** The step runs long after `Implement`, on a session that may be
on another branch, in a container that may have been rebuilt — a step that
needs a checkout is a step that fails first on the surface it matters most on.
The call also answers the question it is asked: GitHub reports the branch as
already up to date when there is nothing to bring in, so nothing has to
measure how far behind the branch is. A conflict is where it stops helping —
it fails and changes nothing — and a resolution is a local merge from there.

**Rejected: a rebase.** It rewrites history a reviewer is reading, and it
voids the head SHA `review-cycle` records at `Review the head`, which is the
mark its whole re-review test is measured from. A merge commit costs a line of
history and keeps both.

**A clean base merge does not earn a review round.** `/code-review` reads the
pull request's three-dot diff. A clean merge leaves that diff byte-identical to
what `Review the head` already reviewed, so a second round reads the same bytes
and reports the same nothing — daily, on a base branch that moves daily. This
is not a new rule: `review-cycle`'s `Does it go again?` already files a clean
base merge under `Neither`. What was missing was the step that performs the
merge, and the statement of when the exception bites.

**Rejected: reviewing the merged base changes.** It is the intuitive answer to
*"the base changed something my branch depends on"*, and it is the wrong
instrument. That breakage is semantic, it does not appear in the branch's own
diff, and what finds it is the build: CI runs again on the merged head, and a
red check is answered under `Fix, answer, resolve, push`. A review panel
reading a diff that did not change would not have found it.

**The exception is a conflict resolution.** Resolving a conflict rewrites the
branch's own files, which `Does it go again?` already classifies as
`Changing what the code does`. One round over that, on the existing test,
with no second test written for it.

**A round after ready sends the pull request back to draft.** Ready is a claim
that the branch is finished; a branch being changed under a reviewer is not.
The return is through the existing gate — green CI, no unanswered thread,
every finding closed — rather than through a second gate written for the
second round.

**The step looks on a check-in every fifteen minutes, and the merge rate is
bounded by CI rather than by the base branch.** A base branch is not a pull
request event: nothing wakes a session when `master` moves, so `Keep it
current` is scheduled rather than woken. One `send_later` at a time, ended by
the merge or the close of the pull request.

Fifteen minutes is chosen against the cost of a merge, not against the rate of
the base branch. A busy `master` takes a commit every few minutes; a branch
merging each one moves its head each time, restarts CI each time, and never
holds a green check long enough to be read. So a check-in that finds the last
merge's run still going does nothing, and the branch rides a few commits behind
between merges. What has to be current is the branch a reviewer reads and the
branch that lands.

**Rejected: an hourly check-in**, the first cadence written here. An hour is
slower than the thing being tracked by an order of magnitude — a dozen commits
behind on a busy day, and a conflict unseen for most of it.

**Rejected: merging on every base commit.** It is the cadence the request
suggests and the one CI cannot pay for: the run is restarted by each merge, so
a branch merging faster than the run reports is a branch that is never green.

**Rejected: a pull request subscription.** `review-cycle` takes one for the CI
wait and drops it with the wait. Keeping it standing would not answer this
question — it carries comments, reviews and checks, and never a push to the
base branch — so it would be a subscription held for events that cannot
arrive.
