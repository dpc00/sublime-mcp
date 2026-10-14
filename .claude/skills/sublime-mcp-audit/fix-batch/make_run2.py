import re

base = r"C:\Users\donal\AppData\Local\Temp\claude\C--Users-donal-projects-sublime-mcp\0d8c7176-6670-4e73-a041-a3509d642e0d\scratchpad"
src = open(base + r"\apply_fix.py", encoding="utf8").read()

NEW = '''SPECS = [
    ("AskCodi/Sublime-AskCodi", 2, "askcodi_network_client.py",
     [(r"(?m)(except urllib\\.error\\.URLError as e:\\n\\s+raise UnknownException\\(str\\()error(\\)\\))", r"\\1e\\2", 1)],
     "use the caught exception in the URLError handler",
     "the `except urllib.error.URLError as e:` handler in `connect_sse` calls `str(error)`, but the caught exception is `e` (`error` does not exist there), so it raises `NameError` instead of `UnknownException`"),
    ("Starli0n/SublimeAgentRansack", 2, "agent_ransack.py", [("return false", "return False", 1)],
     "use False instead of false",
     "`is_enabled` returns `false` (JavaScript spelling) when Agent Ransack is not installed, which raises `NameError`"),
    ("davidmreed/test_switcher", 1, "test_switcher.py", [("extension.lower() in extensions", "ext.lower() in extensions", 1)],
     "use the loop variable ext",
     "`find_possible_paths` calls `extension.lower()`, but the loop variable is `ext`, so it raises `NameError`"),
    ("marekpiechut/sublime-rome-formatter", 5, "RomeFormatter.py", [("view_main_scope = view.syntax()", "view_main_scope = self.view.syntax()", 1)],
     "use self.view for unsaved buffers",
     "`extract_file_name` uses `view.syntax()` for an unsaved buffer, but `view` is not defined there (it is `self.view`), so formatting an untitled buffer raises `NameError`"),
    ("aziz/DistractionFreeWindow", 33, "main.py", [("            _status_msg(", "            self._status_msg(", 2)],
     "call _status_msg through self",
     "the two error branches in `run` call `_status_msg(...)` without `self.`, but it is a method, so they raise `NameError`"),
    ("shagabutdinov/sublime-named-mark", 2, "commands.py",
     [("    regions = self.view.get_regions(name)\\n    if len(regions) == 0:\\n      return\\n\\n    self.view.erase_regions(name)",
       "    for name in names:\\n      regions = self.view.get_regions(name)\\n      if len(regions) == 0:\\n        continue\\n\\n      self.view.erase_regions(name)", 1)],
     "loop over the names argument",
     "`UnsetNamedMark.run` takes `names` but uses an undefined `name`, so the command always raises `NameError`; it now unsets each of the given names"),
    ("skuroda/ImprovedMacros", 5, os.path.join("improved_macros", "run_multiple_commands.py"), [("except ex:", "except ValueError:", 1)],
     "catch ValueError in from_json",
     "`from_json` has `except ex:`, but `ex` is not defined, so invalid JSON raises `NameError` instead of returning `None` (`json.loads` raises a `ValueError` subclass)"),
]
'''
out = re.sub(r"SPECS = \[.*?\n\]\n", lambda m: NEW, src, count=1, flags=re.S)
assert out != src
open(base + r"\apply_fix2.py", "w", encoding="utf8").write(out)
print("written")
