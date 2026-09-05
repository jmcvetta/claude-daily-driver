# claude-daily-driver

Daily-driver skills for [Claude Code][cc], packaged as a plugin.

[cc]: https://claude.com/claude-code

This is one person's working toolkit, published rather than licensed. See
[ANTI-LICENSE.md](ANTI-LICENSE.md) before going further — and then, having
read it, do not go further.

## What's in it

| Skill | What it does |
| ----- | ------------ |
| `pr`  | Opens and updates GitHub pull requests: Conventional Commits title, draft by default, and a body with a one-line summary, a salutation in verse, an executive summary, and engineering detail. |

The `pr` skill triggers on the literal `/pr`, on natural phrasings ("open a
PR", "fix the PR title"), and on Claude's own use of `gh pr create` and
`gh pr edit`. That last register is the point: a convention that only fires
when a human types a command quietly stops applying as more of the work runs
without one.

## Layout

The plugin is the repository root — `"source": "./"` in the marketplace
manifest — so there is no nested plugin directory:

```
claude-daily-driver/
├── .claude-plugin/
│   ├── plugin.json         the plugin
│   └── marketplace.json    the pointer `claude plugin install` reads
└── skills/
    └── pr/SKILL.md
```

## Portability

The same tree is read by more than one harness:

- **Claude Code** discovers it as a plugin.
- **[oh-my-pi][omp]** (`omp`) reads Claude Code plugins natively through its
  `claude-plugins` discovery provider, so it needs no separate port. A
  checkout can be loaded directly with `omp --plugin-dir <path>`.

[omp]: https://omp.sh

## Don't install this

Genuinely: write your own. This fits its author the way a worn boot fits a
foot, and you have different feet.

If you disregard that, the mechanics are ordinary and the consequences are
enumerated at length in [ANTI-LICENSE.md](ANTI-LICENSE.md).
