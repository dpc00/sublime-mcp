import json, os, subprocess, tempfile

PROJECTS = r"C:\Users\donal\tools\forks"  # NOT projects: pybackup commits and pushes everything under projects
# repo, issue, what was wrong, short title text
ITEMS = [
    ("jeffrand/CoberturaCoverage", 1, "a trailing comma after the last entry", "remove the trailing comma"),
    ("tushortz/EasyImport", 1, "a trailing comma after the last entry", "remove the trailing comma"),
    ("EivindArvesen/xkcd", 9, "a typo: the last key is followed by `_` instead of `:`", "fix the typo (`_` instead of `:`)"),
    ("abathur/constellation", 13, "a trailing comma after the last entry", "remove the trailing comma"),
    ("KeeMeng/MKB-Syntax-Highlighting", 1, "a trailing comma after the last entry", "remove the trailing comma"),
    ("daverosoff/PreTeXtual", 50, "a missing comma after the `0.7.0-rc.2` entry", "add the missing comma"),
    ("etienne-monier/LedgerTools", 11, "a trailing comma after the last entry", "remove the trailing comma"),
    ("tanepiper/SublimeText-Nodejs", 112, "a trailing comma after the last entry", "remove the trailing comma"),
    ("KristoforMaynard/SublimeAutoDocstring", 54, "a missing comma after the `install` entry", "add the missing comma"),
    ("AmjadHD/sublime_one_theme", 8, "a trailing comma after the last entry", "remove the trailing comma"),
    ("absop/ST-CodeLines", 3, "a trailing comma after the last entry", "remove the trailing comma"),
]


def run(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


for repo, num, what, title in ITEMS:
    name = repo.split("/")[1]
    d = os.path.join(PROJECTS, name)
    f = os.path.join(d, "messages.json")
    try:
        data = json.loads(open(f, "r", encoding="utf-8-sig").read())
    except Exception as e:
        print(f"SKIP {repo}: still invalid ({e})")
        continue
    # do the files it points to exist? (information only)
    missing = [v for v in data.values() if isinstance(v, str) and not os.path.exists(os.path.join(d, v))]
    code, base = run(["git", "rev-parse", "--abbrev-ref", "origin/HEAD"], cwd=d)
    base = base.split("/")[-1]
    run(["git", "checkout", "-q", "-b", "fix-messages-json"], cwd=d)
    run(["git", "add", "messages.json"], cwd=d)
    code, out = run(["git", "commit", "-q", "-m", f"messages.json: {title}", "-m",
                     "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"], cwd=d)
    if code != 0:
        print(f"FAIL commit {repo}: {out[-100:]}")
        continue
    code, out = run(["git", "push", "-q", "-u", "origin", "fix-messages-json"], cwd=d)
    note = ""
    if missing:
        note = f"\n\nNote: the file also lists message files that do not exist in the repo ({', '.join(missing[:3])}); I did not touch those."
    body = (f"Claude reports: fixes #{num}. `messages.json` is invalid JSON because of {what}, so Package Control "
            f"logs `Error parsing messages.json` when the package is installed and the install/upgrade message is never shown.\n\n"
            f"This changes only that one spot. Checked with a strict JSON parser: it raised before the change and parses now "
            f"(I did not re-run the Package Control install after the change).{note}\n\n"
            f"🤖 Generated with [Claude Code](https://claude.com/claude-code)\n")
    bf = os.path.join(tempfile.gettempdir(), f"prbody_{name}.md")
    open(bf, "w", encoding="utf8").write(body)
    code, out = run(["gh", "pr", "create", "--repo", repo, "--base", base, "--head", f"dpc00:fix-messages-json",
                     "--title", f"messages.json: {title} (fixes #{num})", "--body-file", bf], cwd=d)
    print(("OK   " if code == 0 else "FAIL ") + repo + " " + out.splitlines()[-1][:100])
    os.remove(bf)
