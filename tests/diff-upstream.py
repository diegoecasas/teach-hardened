#!/usr/bin/env python3
"""Muestra qué ha cambiado en upstream desde el SHA fijado en este fork.

No compara upstream contra la copia local: eso daría un diff enorme e inútil,
porque el fork diverge a propósito. Compara upstream consigo mismo entre dos
puntos, que es la pregunta accionable: "¿qué tocó Matt que yo debería mirar?"

No requiere clonar nada.

Uso:  python3 tests/diff-upstream.py [--from <sha>] [--to <ref>]
Sal:  0 = sin cambios, 2 = hay cambios que revisar, 1 = error
"""
import json, pathlib, re, sys, urllib.error, urllib.request
from difflib import unified_diff

REPO = 'mattpocock/skills'
PATH = 'skills/productivity/teach'
ROOT = pathlib.Path(__file__).resolve().parent.parent

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'teach-hardened-diff'})
    return urllib.request.urlopen(req, timeout=30).read()

def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default

# --- ref de partida: el SHA fijado ------------------------------------------
pinned = arg('--from')
if not pinned:
    changes = ROOT / 'CHANGES-VS-UPSTREAM.md'
    m = re.search(r'Upstream fijado:\*\* `([0-9a-f]{40})`', changes.read_text())
    if not m:
        sys.exit(f"no encuentro el SHA fijado en {changes}")
    pinned = m.group(1)

try:
    head = arg('--to') or json.loads(get(
        f'https://api.github.com/repos/{REPO}/commits/main'))['sha']
except urllib.error.URLError as e:
    sys.exit(f"no pude alcanzar GitHub: {e}")

print(f"fijado : {pinned}")
print(f"actual : {head}\n")
if pinned == head:
    print(f"upstream no se ha movido. Nada que revisar.")
    sys.exit(0)

def files_at(ref):
    """{ruta relativa: sha del blob} para el directorio del skill en ese ref."""
    tree = json.loads(get(
        f'https://api.github.com/repos/{REPO}/git/trees/{ref}?recursive=1'))
    return {e['path'][len(PATH) + 1:]: e['sha'] for e in tree['tree']
            if e['type'] == 'blob' and e['path'].startswith(PATH + '/')}

def body(ref, rel):
    return get(f'https://raw.githubusercontent.com/{REPO}/{ref}/{PATH}/{rel}'
               ).decode('utf-8', 'replace').splitlines(keepends=True)

old, new = files_at(pinned), files_at(head)

for rel in sorted(set(new) - set(old)):
    print(f"### NUEVO aguas arriba: {rel}")
    print(f"    https://github.com/{REPO}/blob/{head}/{PATH}/{rel}\n")
for rel in sorted(set(old) - set(new)):
    print(f"### BORRADO aguas arriba: {rel}\n")

changed = [r for r in sorted(set(old) & set(new)) if old[r] != new[r]]
for rel in changed:
    print(''.join(unified_diff(body(pinned, rel), body(head, rel),
                               fromfile=f'{rel}@{pinned[:8]}',
                               tofile=f'{rel}@{head[:8]}')))

total = len(set(new) ^ set(old)) + len(changed)
if not total:
    print("el skill no cambió (upstream se movió por otras razones)")
    sys.exit(0)

print(f"\n{total} archivo(s) con cambios.\n"
      f"Al adoptar algo:\n"
      f"  1. aplícalo a mano sobre skills/teach-hardened/, respetando los deltas\n"
      f"  2. python3 tests/audit-skill.py   <- falla por nombre si el merge se llevó el endurecimiento\n"
      f"  3. actualiza el SHA fijado en CHANGES-VS-UPSTREAM.md a {head}")
sys.exit(2)
