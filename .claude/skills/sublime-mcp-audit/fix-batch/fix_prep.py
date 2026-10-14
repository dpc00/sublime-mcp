import json, os, re, subprocess, sys

PROJECTS = r"C:\Users\donal\projects"
TARGETS = [
    ("jeffrand/CoberturaCoverage", 1),
    ("tushortz/EasyImport", 1),
    ("EivindArvesen/xkcd", 9),
    ("abathur/constellation", 13),
    ("KeeMeng/MKB-Syntax-Highlighting", 1),
    ("oleg-shilo/sublime-favorites", 10),
    ("daverosoff/PreTeXtual", 50),
    ("etienne-monier/LedgerTools", 11),
    ("tanepiper/SublimeText-Nodejs", 112),
    ("KristoforMaynard/SublimeAutoDocstring", 54),
    ("AmjadHD/sublime_one_theme", 8),
    ("absop/ST-CodeLines", 3),
]


def run(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def valid(text):
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def repair(text):
    t = text
    if valid(t):
        return t
    t1 = re.sub(r",(\s*[}\]])", r"\1", t)
    if valid(t1):
        return t1
    # missing comma between a value and the next quoted key on a new line
    t2 = re.sub(r'("(?:[^"\\\n]|\\.)*"|\d|true|false|null|\}|\])([ \t]*\r?\n[ \t]*)(")', r"\1,\2\3", t1)
    if valid(t2):
        return t2
    return None


for repo, num in TARGETS:
    name = repo.split("/")[1]
    d = os.path.join(PROJECTS, name)
    code, st = run(["gh", "issue", "view", str(num), "--repo", repo, "--json", "state", "--jq", ".state"])
    if st.strip() != "OPEN":
        print(f"SKIP {repo}#{num}: issue state {st.strip()!r}")
        continue
    if not os.path.isdir(d):
        code, out = run(["gh", "repo", "fork", repo, "--clone=true", "--default-branch-only"], cwd=PROJECTS)
        if code != 0 or not os.path.isdir(d):
            print(f"FAIL {repo}: fork/clone: {out[-120:]}")
            continue
    run(["git", "config", "core.autocrlf", "false"], cwd=d)
    f = os.path.join(d, "messages.json")
    if not os.path.isfile(f):
        print(f"NOFILE {repo}: no root messages.json")
        continue
    raw = open(f, "rb").read()
    enc = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    text = raw.decode(enc)
    if valid(text):
        print(f"VALID-ALREADY {repo}: messages.json parses upstream now")
        continue
    fixed = repair(text)
    if fixed is None:
        print(f"MANUAL {repo}#{num}: could not repair automatically")
        continue
    open(f, "wb").write(fixed.encode(enc))
    code, diff = run(["git", "diff", "-U0", "--", "messages.json"], cwd=d)
    changed = [l for l in diff.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    print(f"FIXED {repo}#{num} ({len(changed)} changed lines):")
    for l in changed[:6]:
        print("    " + l[:110])
