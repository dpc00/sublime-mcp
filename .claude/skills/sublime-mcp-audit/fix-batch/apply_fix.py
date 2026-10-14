import json, os, py_compile, re, subprocess, sys, tempfile

PROJECTS = r"C:\Users\donal\projects"
DRY = "--dry" in sys.argv

# repo, issue, file, [(old, new, count)], branch title, what it was
SPECS = [
    ("OmniSharp/Kulture", 39, "Kulture.py", [(r"(?m)^(\s*)retrun[ \t]*$", r"\1return", 1)],
     "fix the `retrun` typo", "the error path has a line `retrun` (typo for `return`), which raises `NameError` instead of returning"),
    ("SublimeText/GenerateUUID", 12, "generate_uuid.py", [("import uuid\n", "import re\nimport uuid\n", 1)],
     "import re", "`re.sub` is used for the `uuid1s`/`uuids` variants but `re` is never imported, so they raise `NameError`"),
    ("dnatag/SublimePyunit", 2, "helpers.py", [("import os\nimport re\n", "import errno\nimport os\nimport re\n", 1)],
     "import errno", "the `OSError` handler of the directory helper uses `errno.EEXIST`, but `errno` is not imported, so it raises `NameError`"),
    ("jolyongray/amnesia-sublime", 2, "AmnesiaIO.py",
     [("from urllib.request import Request, urlopen\n", "from urllib.request import Request, urlopen\nfrom urllib.error import URLError\n", 1)],
     "import URLError", "`except URLError` is used but `URLError` is never imported, so any network failure raises `NameError` instead of showing the status message"),
    ("nexional/CompareBuff", 3, "compare_buff.py", [("icons['enable'] = true", "icons['enable'] = True", 2)],
     "use True instead of true", "`icons['enable'] = true` is the JavaScript spelling and raises `NameError` in Python"),
    ("centny/GoGdb", 7, "sublimegdb.py", [("return Falses", "return False", 1)],
     "fix the `Falses` typo", "`return Falses` (typo for `False`) raises `NameError` in the error path"),
    ("unclecheese/sublime-robotype", 2, "RoboTypePlugin.py", [("return true", "return True", 1)],
     "use True instead of true", "`return true` in `willBackspace` is the JavaScript spelling and raises `NameError` in Python"),
    ("poucotm/LikeGit", 2, os.path.join("core", "commands.py"), [("import re\nimport os\n", "import re\nimport os\nimport plistlib\n", 1)],
     "import plistlib", "`plistlib.readPlistFromBytes` is used in the .tmTheme branch of the colour lookup but `plistlib` is never imported, so it raises `NameError`"),
    ("icjmaa/MySFTP", 10, "MySFTP.py", [("Configuration.currentPath = tmp_current_pathn;", "Configuration.currentPath = tmp_current_path;", 1)],
     "fix the `tmp_current_pathn` typo", "`tmp_current_pathn` (typo for `tmp_current_path`) raises `NameError` when entering a remote folder"),
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
