import json, os, subprocess, sys

PROJECTS = r"C:\Users\donal\tools\forks"  # NOT projects: pybackup commits and pushes everything under projects
REPOS = sys.argv[1:]


def run(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf8", errors="replace")
    return p.returncode, p.stdout, p.stderr


for repo in REPOS:
    name = repo.split("/")[1]
    d = os.path.join(PROJECTS, name)
    if not os.path.isdir(d):
        code, out, err = run(["gh", "repo", "fork", repo, "--clone=true", "--default-branch-only"], cwd=PROJECTS)
        if code != 0 or not os.path.isdir(d):
            print(f"== {repo}: clone failed: {(out + err)[-100:]}")
            continue
    run(["git", "config", "core.autocrlf", "false"], cwd=d)
    code, out, err = run(["ruff", "check", "--select", "F821", "--output-format", "json", "--no-cache", "."], cwd=d)
    try:
        hits = json.loads(out or "[]")
    except Exception:
        hits = []
    print(f"== {repo}: {len(hits)} F821")
    for h in hits[:7]:
        f = os.path.relpath(h["filename"], d)
        ln = h["location"]["row"]
        try:
            src = open(h["filename"], encoding="utf8", errors="replace").read().splitlines()[ln - 1].strip()
        except Exception:
            src = "?"
        print(f"   {f}:{ln}: {h['message'][:46]} | {src[:90]}")
