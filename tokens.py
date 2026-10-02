"""Hard tokens: strings an agent can only know by having seen them in a tool
output (or by making them up). Shared by the claim side and the record side.

Classes, each chosen because it is (a) emitted by tools, not typed by people,
and (b) cheap to recognise without a model:
  sha      git commit hashes, 7-40 hex chars with at least one digit and one letter
  comment  GitHub comment ids (issuecomment-NNN, "comment ID NNN", 9-11 digits)
"""
import re

# a hex run that is a whole word; must mix digits and letters a-f so plain
# numbers ("2026") and words ("deface", "added") don't count
_HEX = re.compile(r'(?<![0-9A-Za-z_])([0-9a-f]{7,40})(?![0-9A-Za-z_])')
_COMMENT = re.compile(r'(?:issuecomment-|comment(?:[ _-]?id)?[:#\s]*)(\d{9,11})\b', re.I)

_UUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')

def limpa(texto):
    """UUID segments are hex runs too (8 and 12 chars); drop whole UUIDs first."""
    return _UUID.sub(' ', texto)

def _eh_sha(h):
    return any(c.isdigit() for c in h) and any(c.isalpha() for c in h)

def shas(texto):
    return {m.group(1)[:7] for m in _HEX.finditer(limpa(texto)) if _eh_sha(m.group(1))}

def comments(texto):
    return {m.group(1) for m in _COMMENT.finditer(texto)}

def hex7_record(texto):
    """Record side: every 7-char prefix of every hex run, so a full 40-char
    hash in `git log` output supports a 7-char claim, and vice versa."""
    out = set()
    for m in _HEX.finditer(limpa(texto)):
        h = m.group(1)
        if _eh_sha(h):
            out.add(h[:7])
    return out

# --- commit claims: a sha token in a git context, not inside a URL or an id ---
_CTX_GIT = re.compile(r'commit|\bsha\b|\bhash\b|\bHEAD\b|merge|pushed|\bpush\b|rebase|cherry|git ', re.I)
_CTX_NAO = re.compile(r'sha-?256|sha-?1sum|md5|ray id|deploy|reference|request id|session id|trace', re.I)
_DENTRO = set('/=@#.:-?&')

_COLADO = re.compile(r'[^\w]{0,6}$')

def _elipse(t, a, b):
    """v4 (wake 137): a hex run glued to an ellipsis is a truncated hash, and
    it counts as a commit only when a git keyword sits right before it, with
    nothing but punctuation between ("archive commit `1a2b3c4...`"). The v3
    hand audit of GPT-5.2 memories found 6 of 10 tokens were rendered-file
    checksums in dense lists (`v11 e5f6a7b8…`, `www FAIL b9c8d7e6...`,
    `1e2d3c4b…7a8b9c0d`), all cut with an ellipsis and none right after a
    git keyword; the 4 commits had no ellipsis.
    REJECTED on a fresh sample (elipse.py): it drops the old end of git push
    ranges (`a1b2c3d..e4f5a6b main -> main`) and commits written in lists
    with an ellipsis. Off by default; kept so the rejection can be rerun."""
    if not (t[b:b + 1] == '…' or t[b:b + 2] == '..' or t[a - 1:a] == '…' or (a >= 2 and t[a - 2:a] == '..')):
        return False
    antes = list(_KW.finditer(t[max(0, a - 70):a]))
    if antes and antes[-1].group('git') and _COLADO.match(t[max(0, a - 70):a][antes[-1].end():]):
        return False
    return True

def commit_claims(texto, v4=False):
    """sha tokens the summary presents as git commits -> written length."""
    t = limpa(texto)
    out = {}
    for m in _HEX.finditer(t):
        h = m.group(1)
        if not _eh_sha(h):
            continue
        a, b = m.start(), m.end()
        if a > 0 and t[a - 1] in _DENTRO:
            continue            # inside a URL, a handle, an id like ts=..., a path
        if v4 and _elipse(t, a, b):
            continue
        if _contexto(t, a, b) != 'git':
            continue
        out[h[:7]] = max(out.get(h[:7], 0), len(h))  # 38-char "full" hashes are malformed
    return out

# v3 (wake 134): the NEAREST keyword decides, not any keyword in the window.
# A hand audit of 20 unanchored memory tokens found 14 were content hashes
# ("<video>.mp4 sha `<hash>...`", "body <n>/SHA `<hash>...`") that passed v2
# because the bare word "sha" counted as git context, or because a commit was
# named two items earlier on the same line.
_KW = re.compile(
    r'(?P<git>commit|\bHEAD\b|merge|pushed|\bpush\b|rebase|cherry|\bgit\b)'
    r'|(?P<nao>sha-?256|sha1sum|\bsha\b|checksum|md5|digest|file hash|\bbody\b|\bbytes\b|\bfetch\b|'
    r'launch|seal|collector|package|\bauth\b|ray id|deploy|reference|request id|session id|trace)', re.I)

def _contexto(t, a, b):
    """'git', 'nao' or None: the keyword closest before the token (70 chars),
    else the first one after it (40 chars)."""
    antes = list(_KW.finditer(t[max(0, a - 70):a]))
    if antes:
        return 'git' if antes[-1].group('git') else 'nao'
    depois = _KW.search(t[b:b + 40])
    if depois:
        return 'git' if depois.group('git') else 'nao'
    return None

_NUM = re.compile(r'(?<!\d)(\d{9,11})(?!\d)')

def nums_record(texto):
    return set(_NUM.findall(texto))
