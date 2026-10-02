import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tokens import commit_claims

casos = [
    # all cases are synthetic, shaped like what the agents write (no dataset text)
    ('commit hash **a7b6c5d**, message', {'a7b6c5d': 7}),
    ('Result of git rev-list: 3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f | x', {'3e4f5a6': 40}),
    ('https://github.com/x/commit/abc1234 and Ray ID: 9d8c7b6a5f4e3d', {}),
    ('- `b2c3d4e` - docs: add a section (git log --oneline)', {'b2c3d4e': 7}),
    ('Resulting SHA-256 printed: 7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c', {}),
    ('ID 4c3b2a1f (search results)', {}),
    # v3: shaped like the memory false positives (wake 134)
    ('Render `/tmp/clip_v9.mp4` sha `a1b2c3d4...e5f6`', {}),
    ('HTTP 200, body 1234/SHA `9f8e7d6c...`; archive commit `1a2b3c4...`', {'1a2b3c4': 7}),
    ('screenshot sha256 `0f1e2d3c4b5a69788796a5b4c3d2e1f0` | - commit `7e6d5c4`', {'7e6d5c4': 7}),
    ('Archive commit `b1c2d3e...`; sources fetch `c9d8e7f...`; seal `d1e2f3a...`', {'b1c2d3e': 7}),
    ('- Precommit commit:\n  - Short: `5a4b3c2d`\n  - Full: `5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6`', {'5a4b3c2': 39}),
    ('- Full authoritative HEAD: **`6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d`**', {'6c5d4e3': 40}),
    ('collector SHA `4e5f6a7b...`; precommit commit `8c9dab0...`', {'8c9dab0': 7}),
    # v4 (rejected, off by default; run with v4=True): GPT-5.2 checksum lists
    ('bundle commit `a0b1c2d`) | - v13 `e5f6a7b8…` | - v15 `c1d2e3f4…`', {'a0b1c2d': 7}),
    ('Set56: commit `f0e1d2c`; www FAIL `b9c8d7e6...`; control PASS `a5b4c3d2...`', {'f0e1d2c': 7}),
    ('- control PASS: `1e2d3c4b…7a8b9c0d` | Commits: | - log commit `3f4e5d6`', {'3f4e5d6': 7}),
    ('at that head matched **6233B / 2c3d4e5f…**', {}),
    ('Commit: **`9a8b7c6…`** pushed', {'9a8b7c6': 7}),
]
ok = True
V4 = casos[-5:]
for texto, esperado in casos:
    r = commit_claims(texto, v4=(texto, esperado) in V4)
    if r != esperado:
        ok = False
        print('FALHOU', repr(texto), r, '!=', esperado)
print('ok' if ok else 'FALHAS')
sys.exit(0 if ok else 1)
