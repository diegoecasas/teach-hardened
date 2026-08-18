#!/usr/bin/env python3
"""Static audit of the local `teach` skill.

Regression guard for the hardening applied in phases 1-3, plus the paranoid
checks from the original review. Run after every upstream merge.

Usage:  python3 audit-skill.py [--check-upstream]
Exit:   0 = clean, 1 = failures
"""
import pathlib, re, subprocess, sys, urllib.request, json

SELF = pathlib.Path(__file__).resolve().parent
# Works from both layouts: the repo (tests/ beside skills/) and an installed
# copy (tests/ inside the skill directory).
SKILL = next((c for c in (SELF.parent / 'skills' / 'teach-hardened', SELF.parent)
              if (c / 'SKILL.md').exists()), None)
if SKILL is None:
    sys.exit("could not locate SKILL.md from " + str(SELF))
CHANGES = next((c for c in (SKILL.parent.parent / 'CHANGES-VS-UPSTREAM.md',
                            SKILL / 'LOCAL-CHANGES.md') if c.exists()), None)
FAILS, WARNS = [], []

def fail(t, m): FAILS.append(f"[{t}] {m}")
def warn(t, m): WARNS.append(f"[{t}] {m}")
def docs(): return sorted(SKILL.glob('*.md'))

# --- 1. invisible / bidi unicode -------------------------------------------
SUS = {0x200b:'ZWSP',0x200c:'ZWNJ',0x200d:'ZWJ',0xfeff:'BOM',0x00ad:'SHY',
       0x2060:'WJ',0x202e:'RLO',0x202d:'LRO',0x2066:'LRI',0x2067:'RLI',
       0x2068:'FSI',0x2069:'PDI',0x200e:'LRM',0x200f:'RLM',0x00a0:'NBSP'}
for p in SKILL.rglob('*'):
    if p.is_file() and p.suffix in ('.md', '.yaml', '.yml'):
        t = p.read_text()
        for i, ch in enumerate(t):
            o = ord(ch)
            if o in SUS:
                fail('unicode', f"{p.name}: {SUS[o]} at offset {i}")
            if 0xE0000 <= o <= 0xE007F:
                fail('unicode', f"{p.name}: unicode tag char U+{o:04X} at offset {i}")

# --- 2. hardening must still be present ------------------------------------
SKILL_MD = (SKILL / 'SKILL.md').read_text()
REQUIRED = {
    'workspace-boundary':  'Choosing The Workspace Directory',
    'boundary-home':       "the user's home directory",
    'boundary-git':        'git rev-parse --show-toplevel',
    'boundary-gitignore':  '`.gitignore` containing `*`',
    'trust-boundary':      '## Handling External Sources',
    'trust-data-not-inst': 'data, not instruction',
    'trust-cross-session': 'stays data no matter how many sessions',
    'lesson-sandbox':      'Lessons Must Be Self-Contained',
    'lesson-csp':          'Content-Security-Policy',
    'lesson-no-eval':      'No `eval`',
    'citations':           'Never write a citation from memory',
    'safety':              'Topics Where Being Wrong Hurts',
    'safety-not-clinician':'You are not a clinician',
    'privacy-mission':     'records the goal, not the user',
    'glossary-wired':      '[GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md)',
    'lesson-numbering':    'Scan `./lessons/` for the highest existing number',
}
for key, needle in REQUIRED.items():
    if needle not in SKILL_MD:
        fail('regression', f"hardening '{key}' missing from SKILL.md (looked for: {needle!r})")

# --- 3. reverted-upstream / drift phrases -----------------------------------
BANNED = {
    'littered with citations':                 'citation-theatre wording is back',
    'exactly the same number of words':        'char-count quiz rule is back',
    'Treat the current directory as a teaching workspace.': 'unbounded cwd wording is back',
    'explainer':                               'vocabulary drift (explainer vs lesson)',
    '[[':                                      'wiki-link syntax is back',
}
for p in docs():
    if p.name == 'LOCAL-CHANGES.md':
        continue
    t = p.read_text()
    for phrase, why in BANNED.items():
        if phrase in t:
            fail('drift', f"{p.name}: {why} ({phrase!r})")

# --- 4. internal links + anchors --------------------------------------------
heads = {re.sub(r'[^a-z0-9 -]', '', h.lower()).replace(' ', '-')
         for h in re.findall(r'^#+ (.+)$', SKILL_MD, re.M)}
for p in docs():
    t = p.read_text()
    for target in re.findall(r'\]\(\./([^)#]+)', t):
        if not (SKILL / target).exists():
            fail('links', f"{p.name} -> ./{target} does not exist")
    for anchor in re.findall(r'\]\([^)]*#([a-z0-9-]+)\)', t):
        if anchor not in heads:
            fail('links', f"{p.name} -> #{anchor} matches no heading in SKILL.md")

# --- 5. URL allowlist --------------------------------------------------------
ALLOWED = {'https://example.com', 'https://reddit.com/r/weightroom',
           'https://github.com/mattpocock/skills'}
for p in docs():
    for url in re.findall(r'https?://[^\s)>"\'`]+', p.read_text()):
        if not any(url.startswith(a) for a in ALLOWED):
            fail('urls', f"{p.name}: unexpected URL {url}")

# --- 6. frontmatter ----------------------------------------------------------
m = re.match(r'^---\n(.*?)\n---\n', SKILL_MD, re.S)
if not m:
    fail('frontmatter', 'no frontmatter block')
else:
    fm = dict(l.split(': ', 1) for l in m.group(1).strip().split('\n') if ': ' in l)
    if fm.get('name') != SKILL.name:
        fail('frontmatter', f"name is {fm.get('name')!r} but directory is {SKILL.name!r}")
    if fm.get('disable-model-invocation') != 'true':
        fail('frontmatter', 'disable-model-invocation is no longer true')
    if 'allowed-tools' not in fm:
        warn('frontmatter', 'allowed-tools absent (removed deliberately?)')
    else:
        for banned in ('Task', 'Agent', 'NotebookEdit'):
            if banned in fm['allowed-tools']:
                fail('frontmatter', f"allowed-tools grants {banned}")
        bash = re.findall(r'Bash\(([^)]*)\)', fm['allowed-tools'])
        if 'Bash' in re.sub(r'Bash\([^)]*\)', '', fm['allowed-tools']):
            fail('frontmatter', 'unfiltered Bash in allowed-tools')
        for b in bash:
            if b in ('*', ':*'):
                fail('frontmatter', f'Bash({b}) is unfiltered')

# --- 7. codex metadata parity ------------------------------------------------
y = (SKILL / 'agents' / 'openai.yaml')
if y.exists() and 'allow_implicit_invocation: false' not in y.read_text():
    fail('parity', 'openai.yaml no longer disables implicit invocation')

# --- 8. upstream pin ---------------------------------------------------------
pin = re.search(r'Upstream fijado:\*\* `([0-9a-f]{40})`', CHANGES.read_text()) if CHANGES else None
if not pin:
    warn('upstream', 'no pinned SHA found (looked for CHANGES-VS-UPSTREAM.md / LOCAL-CHANGES.md)')
elif '--check-upstream' in sys.argv:
    try:
        req = urllib.request.Request(
            'https://api.github.com/repos/mattpocock/skills/commits/main',
            headers={'User-Agent': 'teach-audit'})
        head = json.load(urllib.request.urlopen(req, timeout=15))['sha']
        if head != pin.group(1):
            warn('upstream', f"upstream main moved: pinned {pin.group(1)[:8]}, now {head[:8]} "
                             f"-- review the diff before adopting")
    except Exception as e:
        warn('upstream', f'could not reach GitHub: {e}')

# --- report ------------------------------------------------------------------
for w in WARNS: print(f"WARN  {w}")
for f in FAILS: print(f"FAIL  {f}")
print(f"\n{len(FAILS)} failure(s), {len(WARNS)} warning(s)")
sys.exit(1 if FAILS else 0)
