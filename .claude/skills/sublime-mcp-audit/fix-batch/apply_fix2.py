import json, os, py_compile, re, subprocess, sys, tempfile

PROJECTS = r"C:\Users\donal\tools\forks"  # NOT projects: pybackup commits and pushes everything under projects
DRY = "--dry" in sys.argv

# repo, issue, file, [(old, new, count)], branch title, what it was
SPECS = [
    ("AskCodi/Sublime-AskCodi", 2, "askcodi_network_client.py",
     [(r"(?m)(except urllib\.error\.URLError as e:\n\s+raise UnknownException\(str\()error(\)\))", r"\1e\2", 1)],
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
     [("    regions = self.view.get_regions(name)\n    if len(regions) == 0:\n      return\n\n    self.view.erase_regions(name)",
       "    for name in names:\n      regions = self.view.get_regions(name)\n      if len(regions) == 0:\n        continue\n\n      self.view.erase_regions(name)", 1)],
     "loop over the names argument",
     "`UnsetNamedMark.run` takes `names` but uses an undefined `name`, so the command always raises `NameError`; it now unsets each of the given names"),
    ("skuroda/ImprovedMacros", 5, os.path.join("improved_macros", "run_multiple_commands.py"), [("except ex:", "except ValueError:", 1)],
     "catch ValueError in from_json",
     "`from_json` has `except ex:`, but `ex` is not defined, so invalid JSON raises `NameError` instead of returning `None` (`json.loads` raises a `ValueError` subclass)"),
]


def run(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def f821(d, rel):
    code, out = run(["ruff", "check", "--select", "F821", "--output-format", "json", "--no-cache", rel], cwd=d)
    try:
        return len(json.loads(out or "[]"))
    except Exception:
        return -1


only = [a for a in sys.argv[1:] if not a.startswith("--")]
for repo, num, rel, subs, title, what in SPECS:
    if only and repo not in only:
        continue
    name = repo.split("/")[1]
    d = os.path.join(PROJECTS, name)
    fp = os.path.join(d, rel)
    raw = open(fp, "rb").read()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8").replace("\r\n", "\n")
    before = f821(d, rel)
    ok = True
    for old, new, cnt in subs:
        if old.startswith("(?m)"):
            text2, n = re.subn(old, new, text)
        else:
            n = text.count(old)
            text2 = text.replace(old, new)
        if n != cnt:
            print(f"SKIP {repo}: pattern {old[:30]!r} matched {n}, expected {cnt}")
            ok = False
            break
        text = text2
    if not ok:
        continue
    out_text = text.replace("\n", "\r\n") if crlf else text
    open(fp, "wb").write((b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + out_text.encode("utf-8"))
    after = f821(d, rel)
    code, diffstat = run(["git", "diff", "--shortstat"], cwd=d)
    print(f"{repo}#{num}: F821 {before} -> {after}; {diffstat}")
    if after >= before or after < 0:
        print("   NOT IMPROVED, leaving uncommitted")
        continue
    if DRY:
        continue
    run(["git", "checkout", "-q", "-b", "fix-" + re.sub(r"\W+", "-", title.lower()).strip("-")[:40]], cwd=d)
    br = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=d)[1]
    run(["git", "add", rel], cwd=d)
    code, o = run(["git", "commit", "-q", "-m", title[0].upper() + title[1:], "-m",
                   "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"], cwd=d)
    code, o = run(["git", "push", "-q", "-u", "origin", br], cwd=d)
    base = run(["git", "rev-parse", "--abbrev-ref", "origin/HEAD"], cwd=d)[1].split("/")[-1]
    body = (f"Claude reports: fixes #{num}. In `{rel.replace(os.sep, '/')}`, {what}.\n\n"
            f"Found with `ruff --select F821` (undefined name); after this change ruff reports no undefined-name error in that file "
            f"({before} before, {after} after). I did not run the change inside Sublime Text.\n\n"
            f"🤖 Generated with [Claude Code](https://claude.com/claude-code)\n")
    bf = os.path.join(tempfile.gettempdir(), f"prbody_{name}.md")
    open(bf, "w", encoding="utf8").write(body)
    code, o = run(["gh", "pr", "create", "--repo", repo, "--base", base, "--head", f"dpc00:{br}",
                   "--title", f"{title[0].upper() + title[1:]} (fixes #{num})", "--body-file", bf], cwd=d)
    print(("   OK " if code == 0 else "   FAIL ") + o.splitlines()[-1][:110])
    os.remove(bf)
    run(["git", "checkout", "-q", base], cwd=d)
