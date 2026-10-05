"""Predict, from source, which Sublime commands of a package raise panels, dialogs, popups or browser windows.

usage: predict_ui.py <file.py | folder> [more ...]

For every class that is a Text/Window/Application command, it lists the UI calls reachable from run():
direct calls, calls to methods of the same file (resolved by method name, so `self.helper()` and
`_instance.helper()` are both followed, up to 6 levels), and calls made from callbacks passed to
sublime.set_timeout. Output: command name (snake_case, as run_command wants it) -> UI kinds.
Read-only; it only parses source with ast.
"""
import ast
import os
import re
import sys

UI = {
    'show_quick_panel': 'QUICK PANEL',
    'show_input_panel': 'INPUT PANEL',
    'show_overlay': 'OVERLAY',
    'message_dialog': 'DIALOG',
    'error_message': 'DIALOG',
    'ok_cancel_dialog': 'DIALOG',
    'yes_no_cancel_dialog': 'DIALOG',
    'open_dialog': 'FILE DIALOG',
    'save_dialog': 'FILE DIALOG',
    'select_folder_dialog': 'FILE DIALOG',
    'show_popup': 'POPUP',
    'show_panel': 'PANEL',
    'create_output_panel': 'OUTPUT PANEL',
    'status_message': 'status bar message',
    'set_status': 'status bar message',
    'open': None,  # handled below (webbrowser.open)
    'startfile': 'EXTERNAL APP',
    'Popen': 'EXTERNAL PROCESS',
    'new_file': 'NEW TAB',
    'open_file': 'OPENS FILE TAB',
    'new_window': 'NEW WINDOW',
}
CMD_BASES = ('TextCommand', 'WindowCommand', 'ApplicationCommand')


def snake(name):
    if name.endswith('Command'):
        name = name[:-7]
    s = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s).lower()


def call_name(node):
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr, f.value
    if isinstance(f, ast.Name):
        return f.id, None
    return None, None


def analyse(path):
    try:
        tree = ast.parse(open(path, encoding='utf-8', errors='replace').read())
    except SyntaxError as e:
        print('  (cannot parse %s: %s)' % (os.path.basename(path), e))
        return
    methods = {}
    classes = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            classes.append(n)
            for m in n.body:
                if isinstance(m, (ast.FunctionDef,)):
                    methods.setdefault(m.name, []).append(m)
        elif isinstance(n, ast.FunctionDef) and n not in sum(methods.values(), []):
            methods.setdefault(n.name, []).append(n)

    def ui_in(fn, depth, seen):
        found = []
        if depth > 6 or id(fn) in seen:
            return found
        seen.add(id(fn))
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                name, base = call_name(n)
                if name is None:
                    continue
                if name == 'open' and isinstance(base, ast.Name) and base.id == 'webbrowser':
                    found.append('BROWSER WINDOW')
                elif name in UI and UI[name]:
                    found.append(UI[name] + ' (%s)' % name)
                elif name in methods:
                    for m in methods[name]:
                        found += ui_in(m, depth + 1, seen)
        return found

    for c in classes:
        bases = [b.attr if isinstance(b, ast.Attribute) else getattr(b, 'id', '') for b in c.bases]
        if not any(b in CMD_BASES for b in bases):
            continue
        run = [m for m in c.body if isinstance(m, ast.FunctionDef) and m.name == 'run']
        found = []
        for r in run:
            found += ui_in(r, 0, set())
        kinds = []
        for f in found:
            if f not in kinds:
                kinds.append(f)
        print('  %-42s %s' % (snake(c.name), ', '.join(kinds) if kinds else '(no UI found in run())'))
    # plugin-load / event-listener UI that fires without any command
    for c in classes:
        if any(b == 'EventListener' for b in [b.attr if isinstance(b, ast.Attribute) else getattr(b, 'id', '') for b in c.bases]):
            for m in c.body:
                if isinstance(m, ast.FunctionDef) and m.name.startswith('on_'):
                    f = []
                    for k in ui_in(m, 0, set()):
                        if k not in f:
                            f.append(k)
                    if f:
                        print('  [event] %s.%s -> %s' % (c.name, m.name, ', '.join(f)))
    for m in methods.get('plugin_loaded', []):
        f = []
        for k in ui_in(m, 0, set()):
            if k not in f:
                f.append(k)
        if f:
            print('  [on load] plugin_loaded -> ' + ', '.join(f))


for arg in sys.argv[1:]:
    files = [arg] if os.path.isfile(arg) else [os.path.join(r, f) for r, _, fs in os.walk(arg) for f in fs if f.endswith('.py') and 'test' not in f.lower()]
    for f in files:
        print(os.path.basename(f))
        analyse(f)
