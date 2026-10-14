import csv, re, collections, sys
rows = list(csv.DictReader(open(r"C:\Users\donal\projects\sublime-package-audit\ISSUES.tsv", encoding="utf8"), delimiter="\t"))
print("total", len(rows), "open", sum(r["state"] == "open" for r in rows))
openr = [r for r in rows if r["state"] == "open"]
# one-line fixable-looking defects: obvious code-level causes in the title
pats = collections.OrderedDict([
    ("NameError/undefined", r"NameError|not defined|undefined name|F821|not imported|missing import"),
    ("SyntaxWarning/escape", r"SyntaxWarning|invalid escape|bad escape|DeprecationWarning"),
    ("json/messages trailing comma/invalid", r"trailing comma|invalid JSON|messages\.json|JSON"),
    ("typo/wrong value/path", r"typo|wrong path|hardcoded|hard-coded|wrong name|misspell"),
    ("py3.8+/removed API", r"readPlistFromBytes|collections\.Mapping|imp module|removed in Python|Python 3\.1\d|python 3\.1\d|3\.14"),
    ("with_prototype/syntax load", r"with_prototype|syntax file|Error loading syntax|sanity limit|recursion"),
    ("import error", r"ImportError|ModuleNotFoundError|No module named"),
    ("windows", r"Windows|WinError|backslash"),
    ("crash/exception", r"Traceback|crash|exception|raises|KeyError|TypeError|AttributeError|IndexError|ValueError"),
])
cnt = collections.Counter()
seen = set()
for r in openr:
    for k, p in pats.items():
        if re.search(p, r["title"], re.I):
            cnt[k] += 1
            seen.add((r["repository"], r["number"]))
print({k: v for k, v in cnt.items()})
print("distinct open matching any:", len(seen))
mode = sys.argv[1] if len(sys.argv) > 1 else ""
if mode:
    p = pats[mode]
    out = [r for r in openr if re.search(p, r["title"], re.I)]
    for r in out[:int(sys.argv[2]) if len(sys.argv) > 2 else 40]:
        print(r["repository"], "#" + r["number"], r["title"][:100])
