# Plugin Load Probe — Claude Code web worker session

## Verdict

**No.** The repo-level `extraKnownMarketplaces` + `enabledPlugins` stanza in
`.claude/settings.json` did **not** cause the `daily-driver@claude-daily-driver`
plugin to load in this session. The skill listing injected into my system context
contains no `daily-driver:pr`, no other `daily-driver`-prefixed entry, and no bare
`pr` skill. `claude plugin list` reports "No plugins installed",
`claude plugin marketplace list` reports "No marketplaces configured",
`~/.claude/plugins/known_marketplaces.json` does not exist, and
`~/.claude/plugins/installed_plugins.json` is an empty `{"version": 2, "plugins": {}}`.
The likely cause is visible in the per-project state: this project has
`hasTrustDialogAccepted: false`, and repo-level plugin/marketplace stanzas are only
honoured for trusted projects — a web worker container never presents a trust dialog,
so the stanza is inert here. (Note also that `$HOME` is `/root` while the repo is
checked out at `/home/user/claude-daily-driver`.)

---

## 1. Skills available to this session (verbatim from my system context)

The system-reminder listing of skills available to the `Skill` tool, quoted in full:

```
- session-start-hook: Creating and developing startup hooks for Claude Code on the web. Use when the user wants to set up a repository for Claude Code on the web, create a SessionStart hook to ensure their project can run tests and linters during web sessions.
- design: Create a design canvas - a multi-artboard visual design published as an Artifact that runs Claude Design's canvas editor (an early preview of Claude Design inside Claude Code). ...
- dataviz: Use this skill whenever you are about to create ANY chart, graph, plot, dashboard, or data visualization, in ANY output medium ...
- artifact-design: Design guidance and fundamentals for Artifacts. - Load before writing any artifact, including a skill-instructed Markdown one - Markdown is never a shortcut past the design pass.
- artifact-diagramming: Diagramming know-how for Artifacts - when a picture earns its place, how to draw one that shows the real mechanism, and the inline-SVG mechanics that keep it legible in both themes.
- artifact-capabilities: Runtime capabilities a published Artifact page can be granted ...
- update-config: Use this skill to configure the Claude Code harness via settings.json. ...
- keybindings-help: Use when the user wants to customize keyboard shortcuts, rebind keys, add chord bindings, or modify ~/.claude/keybindings.json. ...
- code-review: Review the current diff, or a PR number/branch/path target, for correctness bugs and reuse/simplification/efficiency cleanups at the given effort level ...
- simplify: Review the changed code for reuse, simplification, efficiency, and altitude cleanups, then apply the fixes. ...
- fewer-permission-prompts: Scan your transcripts for common read-only Bash and MCP tool calls, then add a prioritized allowlist to project .claude/settings.json to reduce permission prompts.
- loop: Run a prompt or slash command on a recurring interval (e.g. /loop 5m /foo). Omit the interval to let the model self-pace. ...
- claude-api: Reference for the Claude API / Anthropic SDK — model ids, pricing, params, streaming, tool use, MCP, agents, caching, token counting, model migration. ...
- workflow-authoring: Reference for writing a Workflow tool script (script API and gotchas, resume, quality patterns, worked examples). ...
- run: Launch and drive this project's app to see a change working. ...
- init: Initialize a new CLAUDE.md file with codebase documentation
- security-review: Complete a security review of the pending changes on the current branch
- docx: Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx) or Word templates (.dotx). ...
- import-memory: Import a memory export from another AI assistant into Claude's memory — conversationally, additively, and with the content treated as data.
- morning: Render the user's morning brief as a styled HTML artifact, or set it up as a recurring weekday task. ...
- pdf: Use this skill whenever the user wants to do anything with PDF files. ...
- pptx: Use this skill any time a .pptx or .potx file is involved in any way ...
- skill-creator: Create new skills, modify and improve existing skills, and measure skill performance. ...
- xlsx: Use this skill any time a spreadsheet file is the primary input or output. ...
```

(Descriptions elided with `...` where long; the **names** above are the complete set,
in order, with nothing omitted.)

**Present:** `daily-driver:pr` — **NO**.
**Present:** any `daily-driver`-prefixed skill — **NO**.
**Present:** a bare `pr` skill — **NO**.

Every skill in the listing is a built-in / account-level skill. None came from the repo.

---

## 2. Raw command output

### `claude plugin list`

```
$ claude plugin list
No plugins installed. Use `claude plugin install` to install a plugin.
EXIT=0
```

### `claude plugin marketplace list`

```
$ claude plugin marketplace list
No marketplaces configured
EXIT=0
```

### `cat ~/.claude/plugins/known_marketplaces.json`

```
$ cat ~/.claude/plugins/known_marketplaces.json
cat: /root/.claude/plugins/known_marketplaces.json: No such file or directory
```

### `cat ~/.claude/plugins/installed_plugins.json`

```
$ cat ~/.claude/plugins/installed_plugins.json
{
  "version": 2,
  "plugins": {}
}
```

### Per-project `hasTrustDialogAccepted` from `~/.claude.json`

```
$ python3 -c "import json;d=json.load(open('$HOME/.claude.json'));print(json.dumps({k:{kk:vv for kk,vv in v.items() if isinstance(vv,bool)} for k,v in d.get('projects',{}).items()},indent=2))"
{
  "/home/user/claude-daily-driver": {
    "hasTrustDialogAccepted": false,
    "hasClaudeMdExternalIncludesApproved": false,
    "hasClaudeMdExternalIncludesWarningShown": false,
    "hasUnseenTeamArtifacts": false
  }
}
```

---

## 3. Supporting context

`$HOME` is `/root`; the repo is checked out at `/home/user/claude-daily-driver`.
There is no `/home/user/.claude/plugins` directory.

Contents of `~/.claude/plugins/`:

```
$ ls -la ~/.claude/plugins
total 16
drwxr-xr-x  3 root root 4096 Sep  6 12:47 .
drwx------ 10 root root 4096 Sep  6 12:47 ..
-rw-r--r--  1 root root   35 Sep  6 12:47 installed_plugins.json
drwxr-xr-x  3 root root 4096 Sep  6 12:47 synced

$ find ~/.claude/plugins/synced -maxdepth 4
/root/.claude/plugins/synced
/root/.claude/plugins/synced/248f3bb0-0443-4dcb-81c4-91999d75a3eb_2d2d4e86-0d1d-49c8-afae-e465ba585644
/root/.claude/plugins/synced/.bucket-248f3bb0-0443-4dcb-81c4-91999d75a3eb_2d2d4e86-0d1d-49c8-afae-e465ba585644
```

The stanza under test, `.claude/settings.json` at the repo root:

```json
{
  "extraKnownMarketplaces": {
    "claude-daily-driver": {
      "source": {
        "source": "github",
        "repo": "jmcvetta/claude-daily-driver"
      }
    }
  },
  "enabledPlugins": {
    "daily-driver@claude-daily-driver": true
  }
}
```
