# Agent plugin: hook Sublime, then every agent can see it

Date: 2026-08-18
Status: draft for review

## What this is

This project already has the product: sublime-mcp, an MCP server
living inside Sublime Text. What it does not have is an install
that a human will finish. Today a user clones the repo,
hand-junctions package trees, then hand-edits whichever agent
config they happen to be running. That is why this sits in one
developer's AI Terminal and nowhere else.

The install unit is an **agent plugin** only because that is how
Grok and Claude deliver trusted code. The thing we are actually
shipping is a **Sublime hookup**. If the plugin does not put
`sublime-mcp` into the user's `Packages/` directory, it is
worthless. MCP config without a listener is a dead settings file.

This is the distribution layer for sublime-mcp. It is not Package
Control for sublime-mcp, not `/ide`, not ACP, and not a bundle of
per-package MCP servers.

## Who it is for

The user keeps an external coding agent in its native TUI inside
Sublime AI Terminal (or a standalone terminal) and wants that
agent to drive the editor they are looking at.

The roster is the thirteen agent families in
`analysis/ai-terminal-agent-protocols.md` plus Gemini CLI, which
`agy` already shares a config file with:

1. Grok Build
2. Claude Code
3. Codex
4. Gemini CLI
5. Antigravity (`agy`)
6. Qwen Code
7. OpenCode
8. Mimo
9. Kimi
10. Kiro
11. Junie
12. jcode
13. Vibe

Chrome / Ollama / `--minimal` / `--mini` profiles are the same
family. They are not extra install targets.

## The product, in one sentence

One trusted install junctions sublime-mcp into the user's editor;
every agent that can hit `http://127.0.0.1:9502/mcp` is done.

## Required vs optional

**Required:** `packages/st-plugin` → `Packages/sublime-mcp`, and
registration of that one HTTP URL.

**Optional, not part of this install:** `debugger-mcp`, `lsp-mcp`,
the Debugger package, the LSP package, and any other per-package
MCP. Those standalone servers were an earlier sketch. The plan
they belong to is a **sublime-mcp tool** that, on the fly, creates
an MCP for any Sublime package — already installed or not yet
installed. That tool is not in sublime-mcp yet. It is not designed
here. It is not `get_package_mcp_info`.

Until that tool exists, this plugin does not ship, junction, or
register debugger-mcp or lsp-mcp. It does not install Debugger or
LSP. `install_package` remains available for any package the user
asks for; it does not generate an MCP.

## Two-phase bootstrap

### Phase 1 — filesystem, no Sublime API

A stdlib Python linker (`hooks/link-sublime.py`) finds the user's
`Packages/` directory and creates:

| Source in this repo | Destination |
|---|---|
| `packages/st-plugin` | `Packages/sublime-mcp` |

Windows: directory junction (`mklink /J`). Unix: symlink. If a
junction cannot be created (cross-volume), copy the tree.
Ownership is recorded in `~/.sublime-mcp/install-state.json`
(destination → source path, link or copy). That file is how later
runs distinguish "we put this here" from "the user already had a
package."

Rules, in this order:

1. Missing destination → create the link (or copy).
2. Destination is already a link to this plugin's matching source →
   no-op.
3. Destination is a link to an older plugin root or a stale copy
   marker → retarget / refresh.
4. Destination is a real directory we do not own → leave it, report
   it, do not delete it.
5. `Packages/` cannot be found → fail with "install or launch
   Sublime Text once." Do not invent a folder.

`Packages/` resolution, first hit wins:

1. `SUBLIME_MCP_PACKAGES_DIR`
2. `%APPDATA%\Sublime Text\Packages`
3. `~/Library/Application Support/Sublime Text/Packages`
4. `~/.config/sublime-text/Packages`
5. The same three with the old `Sublime Text 3` name, only if the
   ST4 path is absent
6. Infer from a running `sublime_text` process if we can

The linker is idempotent. A correct install is a ~50ms check. It
requires `python3` or `py -3` on PATH.

The linker does **not** call `install_package`. It cannot:
sublime-mcp is not loaded yet. It does not install Debugger, LSP,
or any other Package Control package.

### Phase 2 — sublime-mcp is up

Once `:9502/mcp` answers, the agent has `install_package`,
`search_packages`, and `install_package_control`. Those tools
install **whatever package the user asked for**. They are not a
hidden bootstrap that pulls Debugger and LSP.

If Package Control itself is missing, `/sublime-setup` may offer
`install_package_control` so those tools work. That is the only
default phase-2 package action, and it is still user/agent
initiated, not a hook POST.

The on-the-fly package-MCP tool is out of this spec. Do not stub
it here. Do not treat `get_package_mcp_info` as that tool.

## What the thirteen agents actually need

Phase 1 is harness-agnostic. The one HTTP server then listens on:

- `http://127.0.0.1:9502/mcp` — sublime-mcp

sublime-mcp's Mac/Linux MCP port becomes **9502** so the URL is
not a platform table. Existing Mac SSE users on 9503 break; that
is accepted.

The thirteen-way split is only registration: how each agent learns
that URL. We do not build thirteen plugins.

| Class | Agents | What we ship |
|---|---|---|
| A — plugin loads `.mcp.json` | Grok, Claude | Real plugin manifests. `plugin install --trust` runs the linker on `SessionStart` and attaches sublime-mcp. |
| B — known config file we can merge | Codex, Gemini/`agy`, OpenCode, Mimo (as OpenCode until proven otherwise), Kimi, Kiro | `link-sublime.py --register` merges the sublime-mcp HTTP entry into the known file and does not touch any other server. |
| C — `/ide` companion | Gemini, Qwen, Claude `/ide` | Out of this spec. That is Part 2 of the existing roadmap. This plugin does not fake companion discovery. Qwen still gets a Class B adapter if a documented MCP config path exists at implementation time. |
| D — MCP client not established | Junie, jcode, Vibe | Server is up. The linker prints the URL. No invented plugin API. |

Class A is the "easy install" people will quote. Class B is how
the rest of *this* machine gets hooked without thirteen
marketplaces. Class D is honesty, not a backlog we pretend is
scheduled.

SessionStart runs the linker **without** `--register`. A Grok
session must not rewrite Codex or Kimi config. `--register` is
explicit: the CLI, or `/sublime-setup register`. Class A agents
get sublime-mcp from plugin `.mcp.json`; `--register` is for
harnesses that have no plugin load path. Do not write Grok/Claude
user-config duplicates when the plugin is already installed.

`--register` never overwrites a user's existing sublime-mcp entry
if it already points at a working equivalent URL. It never deletes
other MCP servers. It does not add debugger-mcp or lsp-mcp
entries.

## Repo layout

The repo **is** the plugin. No vendor-copy step, no `#plugin`
subdir. `packages/st-plugin` stays the source of truth.

```
plugin.json                     # Grok
.claude-plugin/plugin.json      # Claude (and Grok compat)
.mcp.json                       # sublime-mcp only
hooks/hooks.json                # SessionStart → linker
hooks/link-sublime.py           # phase 1 + optional --register
hooks/run-hook.cmd              # Windows polyglot, same pattern as Superpowers
skills/sublime-setup/SKILL.md   # link status, register, unlink, optional PC
skills/sublime-mcp/SKILL.md     # from docs/AGENT_GUIDE.md
commands/sublime-setup.md       # /sublime-setup and /sublime-setup unlink
```

`packages/debugger-mcp` and `packages/lsp-mcp` remain in the repo
for people who already use them. They are not plugin components.
Their AGENT_GUIDE files are not default skills.

Install:

```bash
grok plugin install dpc00/sublime-mcp --trust
```

or the Claude equivalent. Or, from any agent that can run a
command:

```bash
python hooks/link-sublime.py --register
```

`--register` with no harness flag merges into every Class B config
it finds. A missing file is skipped, not created, except Gemini
`~/.gemini/config/mcp_config.json` when that config directory
already exists. Grok and Claude user configs are skipped when the
plugin is installed; they already load `.mcp.json`.

## Lifecycle

**Update.** Plugin updates in place under
`~/.grok/installed-plugins/<id>/`. The sublime-mcp junction keeps
working. Copies refresh on the next linker run. Sublime picks up
Python changes on package reload.

**Uninstall.** There is no plugin-uninstall hook. `/sublime-setup
unlink` removes only the sublime-mcp destination if it is still a
link (or copy marker) pointing at this plugin root. It does not
uninstall Package Control or any other ST package. A raw
`grok plugin uninstall` can leave a dangling junction; that is
documented, and the next linker run reports it.

**Trust.** Linking into `Packages/` is a filesystem write into the
user's editor. Grok/Claude only run the hook after `--trust`. The
standalone script is the user running Python themselves. That is
the consent model.

## What this is not

- Not a required Debugger or LSP install.
- Not a required debugger-mcp or lsp-mcp install.
- Not the planned sublime-mcp tool that creates an MCP on the
  fly for any ST package (installed or not). That tool does not
  exist yet. `get_package_mcp_info` is not it.
- Not Package Control distribution of sublime-mcp. That remains a
  later channel.
- Not the Gemini/Qwen companion server and not Claude `/ide`.
- Not an ACP client. ACP is Sublime hosting the agent. This is
  the agent hosting itself and talking to Sublime.
- Not a 440-tool redesign. Skills teach the agent which tools to
  use. The capability catalog stays on the existing roadmap.

## Testing

The linker is tested against a fake `Packages/` tree. No live
Sublime in unit tests.

Required cases:

- create junction/symlink for sublime-mcp when missing
- no-op when already correct
- retarget a stale link
- refuse to clobber a real directory
- copy fallback when junction creation is forced to fail
- default run does **not** create debugger-mcp or lsp-mcp
  destinations
- `--register` merges one sublime-mcp server into a fixture Grok
  toml, Gemini json, Codex toml, OpenCode json, Kimi json, Kiro
  json
- `--register` leaves unrelated servers untouched
- `--register` does not add debugger-mcp or lsp-mcp
- missing `Packages/` is a hard error with a specific message

Live verification is: link into a disposable `Packages/` override,
confirm Sublime loads sublime-mcp, confirm `:9502/mcp`
initializes. Do not install Debugger or LSP from CI.

## Success

A person who has Sublime Text and one Class A agent can run one
trusted plugin install, start a session, and get a live
sublime-mcp without opening the README.

A person who has Sublime Text and only Class B agents can run the
linker once and get the same hookup, with those agents picking up
the URL on their next launch.

A person on Junie, jcode, or Vibe gets a working Sublime side and
a printed URL. We do not lie that we installed a plugin into those
harnesses.

Nobody is surprised by Debugger, LSP, debugger-mcp, or lsp-mcp
appearing on their machine.

## First implementation cut

Build in this order. Each cut is usable alone.

1. `link-sublime.py` + tests (phase 1, sublime-mcp only, no
   register).
2. `--register` for the configs already on this machine: Grok,
   Claude, Gemini/`agy`, Codex.
3. Grok + Claude plugin manifests, `.mcp.json` (sublime-mcp only),
   SessionStart hook, `sublime-setup` skill/command.
4. Unify sublime-mcp MCP port to 9502.
5. OpenCode / Kimi / Kiro register adapters.
6. Wrap `docs/AGENT_GUIDE.md` as the sublime-mcp skill.

Do not start the on-the-fly package-MCP tool as part of this work.
Do not start a Junie/jcode/Vibe investigation as part of this work.
Do not start `/ide` as part of this work.
