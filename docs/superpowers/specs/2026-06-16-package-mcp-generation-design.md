# Package MCP Generation — Design Spec

**Date:** 2026-06-16
**Project:** sublime-mcp (MCP Commander)

## Summary

Enable AI agents to generate MCP tool extensions for any installed Package
Control package. The AI introspects a package via a new MCP tool
(`get_package_mcp_info`), then writes a standard Sublime Text plugin file into
the package's own directory. That plugin registers its tools with sublime-mcp
via a public API (`register_mcp_tools` / `unregister_mcp_tools`). ST's normal
plugin loader handles everything — sublime-mcp does no scanning, no watching,
and no automatic activation of anything.

A curated collection of pre-built extension files for popular packages will
eventually live in `sublime-mcp/package_mcps/`. Users copy whichever ones they
want; nothing is auto-installed.

---

## Architecture

### Extension file format

An extension file is a standard ST plugin placed inside the target package's
directory:

```
Packages/LSP/lsp_mcp_tools.py
Packages/GitGutter/gitgutter_mcp_tools.py
```

It calls sublime-mcp's public registration API in `plugin_loaded` /
`plugin_unloaded`:

```python
# Packages/LSP/lsp_mcp_tools.py
from sublime_mcp import register_mcp_tools, unregister_mcp_tools, run_st_command

TOOLS = [
    ("lsp_goto_definition",
     "Jump to the definition of the symbol under the cursor.",
     {},
     lambda body: run_st_command("lsp_goto_definition", scope="window")),
]

def plugin_loaded():
    register_mcp_tools(TOOLS)

def plugin_unloaded():
    unregister_mcp_tools(TOOLS)
```

ST discovers and loads this file exactly as it does any other plugin. No
changes to any config file are required for the tools to appear.

### Public API in `sublime_mcp.py`

Three module-level functions are added:

**`register_mcp_tools(tools)`**
- `tools`: list of `(name, description, input_schema, handler)` tuples
- Merges entries into the live tool registry
- If a name collides with a built-in tool, logs a warning and the built-in
  wins
- Thread-safe (called from ST's main thread via `plugin_loaded`)

**`unregister_mcp_tools(tools)`**
- Removes the named tools from the live registry
- Called from `plugin_unloaded` when the package is disabled or ST shuts down

**`run_st_command(command, args=None, scope="window")`**
- Convenience wrapper: runs an ST command via the internal bridge and returns
  the result dict
- `scope`: `"text"`, `"window"`, or `"application"`
- Intended for use inside extension handler lambdas; keeps extension files free
  of internal implementation details

No other changes to sublime-mcp's internals are needed.

### New MCP tool: `get_package_mcp_info`

Returns everything the AI needs to write an extension file for a given package.

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "package": {"type": "string"}
  },
  "required": ["package"]
}
```

**Output (JSON):**
```json
{
  "package": "LSP",
  "path": "C:/Users/.../Packages/LSP",
  "output_file": "C:/Users/.../Packages/LSP/lsp_mcp_tools.py",
  "commands": [
    {
      "command": "lsp_goto_definition",
      "caption": "LSP: Go to Definition",
      "scopes": ["window"],
      "args": {}
    }
  ],
  "settings_keys": ["lsp_format_on_save", "lsp_show_diagnostics_count_in_view"],
  "python_files": [
    "C:/Users/.../Packages/LSP/plugin/core/sessions.py"
  ],
  "extension_template": "... prose + code explaining the TOOLS format and registration API ..."
}
```

- `commands`: from `get_commands` filtered by package, merged with
  `.sublime-commands` captions
- `settings_keys`: top-level keys from the package's `*.sublime-settings` files
- `python_files`: flat list of `.py` paths the AI may read for further context
- `output_file`: the exact path the AI should write the extension to
- `extension_template`: a short explanation of the plugin format so the AI has
  everything in one response

### Error handling

- `get_package_mcp_info` called with an unknown package → returns
  `{"error": "Package 'X' not found in Packages/"}`
- Extension file fails to load → ST's normal plugin error handling applies
  (error in ST console); sublime-mcp is unaffected
- `register_mcp_tools` called with a duplicate name → warning logged to ST
  console, existing tool kept
- Extension handler raises at call time → MCP error response returned to
  client; server continues running

---

## Phases

### Phase 1 — AI-generated extensions (this spec)

- `get_package_mcp_info` MCP tool
- `register_mcp_tools` / `unregister_mcp_tools` public API in `sublime_mcp.py`
- AI writes the extension file; user gets the tools immediately when ST loads
  the plugin

### Phase 2 — Curated collection (future)

- `sublime-mcp/package_mcps/` directory in the repo
- One file per popular package, e.g. `LSP_mcp_tools.py`
- Users copy whichever files they want into the relevant package directory
- No auto-installation, no auto-detection

---

## What is NOT in scope

- Auto-scanning Packages/ for extension files
- File watchers or hot-reload of extensions
- Auto-activating pre-built extensions when a package is detected
- A UI for managing installed extensions
- Supporting `.sublime-package` zip archives (unpacked Packages/ only)
- Modifying any config file automatically
