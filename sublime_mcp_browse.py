"""MCP Browse commands — ST introspection for AI-assisted plugin development.

Each command opens a formatted scratch tab with live ST data.
All commands appear in the Command Palette under "MCP: Browse ...".
An optional filter is accepted via ST's input panel.

Data fetching runs async (off the main thread) so _on_main() in sublime_mcp
can dispatch back to the main thread without deadlocking.
"""

import sublime
import sublime_plugin


# ── helpers ───────────────────────────────────────────────────────────────────


def _open_scratch(window, title, content):
    def _do():
        v = window.new_file()
        v.set_scratch(True)
        v.set_name(title)
        v.set_read_only(False)
        v.run_command("append", {"characters": content, "force": True})
        v.set_read_only(True)

    sublime.set_timeout(_do, 0)


def _async_browse(window, title, filter_val, fetch_fn, format_fn):
    def _run():
        try:
            data = fetch_fn({"filter": filter_val} if filter_val else {})
            content = format_fn(data, filter_val)
        except Exception as e:
            content = f"Error fetching data: {e}"
        _open_scratch(window, title, content)

    sublime.set_timeout_async(_run, 0)


# ── MCP: Browse Commands ──────────────────────────────────────────────────────


def _fmt_commands(data, filt):
    cmds = data.get("commands", [])
    lines = [
        f"MCP: Browse Commands{' — filter: ' + filt if filt else ''}",
        "─" * 60,
        "",
    ]
    for c in cmds:
        lines.append(f"  {c['command']}")
        scopes = c.get("scopes", [])
        if scopes:
            lines.append(f"    scope   : {', '.join(scopes)}")
        pkgs = c.get("packages", [])
        if pkgs:
            lines.append(f"    package : {', '.join(pkgs)}")
        lines.append("")
    lines.append(f"{len(cmds)} command(s) listed.")
    return "\n".join(lines)


class McpBrowseCommandsCommand(sublime_plugin.WindowCommand):
    def run(self, filter=""):
        if filter:
            from User.sublime_mcp import _get_commands

            _async_browse(
                self.window, "MCP: Commands", filter, _get_commands, _fmt_commands
            )
        else:
            self.window.show_input_panel(
                "Filter by command name (blank for all):",
                "",
                lambda v: self._go(v),
                None,
                None,
            )

    def _go(self, filt):
        from User.sublime_mcp import _get_commands

        _async_browse(self.window, "MCP: Commands", filt, _get_commands, _fmt_commands)


# ── MCP: Browse Menu Items ────────────────────────────────────────────────────


def _fmt_menu_items(data, filt):
    entries = data.get("entries", [])
    lines = [
        f"MCP: Browse Menu Items{' — filter: ' + filt if filt else ''}",
        "─" * 60,
        "",
    ]
    for e in entries:
        path = " > ".join(e.get("path", [])) or "(top level)"
        cmd = e.get("command", "")
        args = e.get("args", {})
        caption = e.get("caption", "")
        lines.append(f"  {path}")
        if caption:
            lines.append(f"    caption : {caption}")
        if cmd:
            lines.append(f"    command : {cmd}")
        if args:
            lines.append(f"    args    : {args}")
        lines.append("")
    lines.append(f"{len(entries)} item(s) listed.")
    return "\n".join(lines)


class McpBrowseMenuItemsCommand(sublime_plugin.WindowCommand):
    def run(self, filter=""):
        if filter:
            from User.sublime_mcp import _get_menu_items

            _async_browse(
                self.window, "MCP: Menu Items", filter, _get_menu_items, _fmt_menu_items
            )
        else:
            self.window.show_input_panel(
                "Filter by caption or command (blank for all):",
                "",
                lambda v: self._go(v),
                None,
                None,
            )

    def _go(self, filt):
        from User.sublime_mcp import _get_menu_items

        _async_browse(
            self.window, "MCP: Menu Items", filt, _get_menu_items, _fmt_menu_items
        )


# ── MCP: Browse Command Palette ───────────────────────────────────────────────


def _fmt_palette(data, filt):
    entries = data.get("entries", [])
    lines = [
        f"MCP: Browse Command Palette{' — filter: ' + filt if filt else ''}",
        "─" * 60,
        "",
    ]
    for e in entries:
        lines.append(f"  {e.get('caption', '(no caption)')}")
        lines.append(f"    command : {e.get('command', '')}")
        if e.get("args"):
            lines.append(f"    args    : {e['args']}")
        if e.get("package"):
            lines.append(f"    package : {e['package']}")
        lines.append("")
    lines.append(f"{len(entries)} entry/entries listed.")
    return "\n".join(lines)


class McpBrowseCommandPaletteCommand(sublime_plugin.WindowCommand):
    def run(self, filter=""):
        if filter:
            from User.sublime_mcp import _get_command_palette

            _async_browse(
                self.window,
                "MCP: Command Palette",
                filter,
                _get_command_palette,
                _fmt_palette,
            )
        else:
            self.window.show_input_panel(
                "Filter by caption (blank for all):",
                "",
                lambda v: self._go(v),
                None,
                None,
            )

    def _go(self, filt):
        from User.sublime_mcp import _get_command_palette

        _async_browse(
            self.window,
            "MCP: Command Palette",
            filt,
            _get_command_palette,
            _fmt_palette,
        )


# ── MCP: Browse Syntaxes ──────────────────────────────────────────────────────


def _fmt_syntaxes(data, filt):
    syns = data.get("syntaxes", [])
    if filt:
        syns = [s for s in syns if filt.lower() in s.get("name", "").lower()]
    lines = [
        f"MCP: Browse Syntaxes{' — filter: ' + filt if filt else ''}",
        "─" * 60,
        "",
    ]
    for s in syns:
        lines.append(f"  {s['name']}")
        lines.append(f"    path: {s['path']}")
        lines.append("")
    lines.append(f"{len(syns)} syntax/syntaxes listed.")
    return "\n".join(lines)


class McpBrowseSyntaxesCommand(sublime_plugin.WindowCommand):
    def run(self, filter=""):
        if filter:
            self._go(filter)
        else:
            self.window.show_input_panel(
                "Filter by syntax name (blank for all):",
                "",
                lambda v: self._go(v),
                None,
                None,
            )

    def _go(self, filt):
        from User.sublime_mcp import _get_syntaxes

        def _run():
            try:
                data = _get_syntaxes({})
                content = _fmt_syntaxes(data, filt)
            except Exception as e:
                content = f"Error: {e}"
            _open_scratch(self.window, "MCP: Syntaxes", content)

        sublime.set_timeout_async(_run, 0)


# ── MCP: Browse Variables ─────────────────────────────────────────────────────


def _fmt_variables(data, filt):
    if filt:
        data = {k: v for k, v in data.items() if filt.lower() in k.lower()}
    lines = [
        f"MCP: Browse Variables{' — filter: ' + filt if filt else ''}",
        "─" * 60,
        "",
    ]
    for k, v in sorted(data.items()):
        lines.append(f"  {k} = {v}")
    lines += ["", f"{len(data)} variable(s) listed."]
    return "\n".join(lines)


class McpBrowseVariablesCommand(sublime_plugin.WindowCommand):
    def run(self, filter=""):
        if filter:
            self._go(filter)
        else:
            self.window.show_input_panel(
                "Filter by variable name (blank for all):",
                "",
                lambda v: self._go(v),
                None,
                None,
            )

    def _go(self, filt):
        from User.sublime_mcp import _get_variables

        def _run():
            try:
                data = _get_variables({})
                content = _fmt_variables(data, filt)
            except Exception as e:
                content = f"Error: {e}"
            _open_scratch(self.window, "MCP: Variables", content)

        sublime.set_timeout_async(_run, 0)
