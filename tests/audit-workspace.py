#!/usr/bin/env python3
"""Audit a workspace produced by the `teach` skill.

Checks the phase-1 guarantees on real output: lessons are self-contained,
the workspace is not sitting in a repo, sources carry provenance, and no
agent-directed text has been laundered into workspace state.

Usage:  python3 audit-workspace.py <workspace-dir>
Exit:   0 = clean, 1 = failures
"""
import pathlib, re, subprocess, sys
from html.parser import HTMLParser

if len(sys.argv) < 2:
    sys.exit("usage: audit-workspace.py <workspace-dir>")
WS = pathlib.Path(sys.argv[1]).resolve()
if not WS.is_dir():
    sys.exit(f"not a directory: {WS}")

FAILS, WARNS = [], []
def fail(t, m): FAILS.append(f"[{t}] {m}")
def warn(t, m): WARNS.append(f"[{t}] {m}")

REMOTE = re.compile(r'^\s*(?:[a-z][a-z0-9+.-]*:)?//', re.I)
SUBRESOURCE = {
    'link': ['href'], 'script': ['src'], 'img': ['src', 'srcset'],
    'iframe': ['src'], 'source': ['src', 'srcset'], 'video': ['src', 'poster'],
    'audio': ['src'], 'embed': ['src'], 'object': ['data'], 'input': ['src'],
    'track': ['src'], 'form': ['action'], 'use': ['href', 'xlink:href'],
    'image': ['href', 'xlink:href'],
}
EXFIL = [
    (r'\beval\s*\(',            'eval()'),
    (r'\bnew\s+Function\s*\(',  'new Function()'),
    (r'\bfetch\s*\(',           'fetch()'),
    (r'XMLHttpRequest',         'XMLHttpRequest'),
    (r'\bWebSocket\b',          'WebSocket'),
    (r'sendBeacon',             'navigator.sendBeacon'),
    (r'\bimport\s*\(',          'dynamic import()'),
    (r'EventSource',            'EventSource'),
]

class Scan(HTMLParser):
    def __init__(self, rel):
        super().__init__(); self.rel = rel; self.csp = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and (a.get('http-equiv') or '').lower() == 'content-security-policy':
            self.csp = a.get('content', '')
        for attr in SUBRESOURCE.get(tag, []):
            v = a.get(attr)
            if v and REMOTE.match(v):
                fail('lesson-network', f"{self.rel}: <{tag} {attr}> loads remote resource {v.split()[0]}")

# --- structure ---------------------------------------------------------------
if not (WS / 'MISSION.md').exists():
    warn('structure', 'no MISSION.md -- workspace never initialised?')
gi = WS / '.gitignore'
if not gi.exists():
    fail('privacy', 'no .gitignore at workspace root')
elif '*' not in gi.read_text().split():
    warn('privacy', ".gitignore exists but does not contain a bare '*'")

r = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=WS,
                   capture_output=True, text=True)
if r.returncode == 0:
    top = pathlib.Path(r.stdout.strip())
    if top != WS:
        fail('boundary', f'workspace sits inside git repo {top}')
if WS == pathlib.Path.home():
    fail('boundary', 'workspace is the home directory itself')

# --- lessons & assets --------------------------------------------------------
html_files = sorted(list(WS.glob('lessons/*.html')) + list(WS.glob('reference/*.html'))
                    + list(WS.glob('assets/*.html')))
for f in html_files:
    rel = f.relative_to(WS)
    text = f.read_text(errors='replace')
    s = Scan(str(rel)); s.feed(text)
    if s.csp is None:
        fail('lesson-csp', f"{rel}: no Content-Security-Policy meta tag")
    elif "default-src 'none'" not in s.csp:
        fail('lesson-csp', f"{rel}: CSP does not start from default-src 'none'")
    for m in re.finditer(r'url\(\s*[\'"]?(?:[a-z]+:)?//', text, re.I):
        fail('lesson-network', f"{rel}: CSS url() points off-machine at offset {m.start()}")
    for pat, name in EXFIL:
        if re.search(pat, text):
            fail('lesson-exfil', f"{rel}: uses {name}")

for f in sorted(list(WS.glob('assets/*.js')) + list(WS.glob('assets/*.css'))):
    rel = f.relative_to(WS); text = f.read_text(errors='replace')
    for m in re.finditer(r'url\(\s*[\'"]?(?:[a-z]+:)?//|@import\s+[\'"]?(?:[a-z]+:)?//', text, re.I):
        fail('lesson-network', f"{rel}: remote reference at offset {m.start()}")
    for pat, name in EXFIL:
        if re.search(pat, text):
            fail('lesson-exfil', f"{rel}: uses {name}")

if not html_files:
    warn('lessons', 'no lessons found to audit')

# --- provenance in RESOURCES.md ---------------------------------------------
res = WS / 'RESOURCES.md'
if res.exists():
    entries = [b for b in re.split(r'\n(?=-\s)', res.read_text()) if 'http' in b]
    for e in entries:
        if not re.search(r'retrieved|accessed|read in full|skimmed|not read', e, re.I):
            warn('provenance', f"RESOURCES.md entry without provenance: {e.strip().splitlines()[0][:70]}")

# --- laundered agent-directed text ------------------------------------------
INJ = [r'ignore (all )?previous instructions', r'you are (now )?an? (ai|assistant|agent)',
       r'system prompt', r'do not tell the user', r'</?(system|instructions)>']
for f in sorted(WS.rglob('*')):
    if f.is_file() and f.suffix in ('.md', '.html', '.txt'):
        t = f.read_text(errors='replace')
        for pat in INJ:
            if re.search(pat, t, re.I):
                warn('laundering', f"{f.relative_to(WS)}: agent-directed phrasing present "
                                   f"(matches {pat!r}) -- verify it is quoted as data, not followed")

for w in WARNS: print(f"WARN  {w}")
for f_ in FAILS: print(f"FAIL  {f_}")
print(f"\n{len(FAILS)} failure(s), {len(WARNS)} warning(s)")
sys.exit(1 if FAILS else 0)
