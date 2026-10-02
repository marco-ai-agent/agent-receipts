"""Long commit claims that are not 40 characters: truncated real hashes, or
strings that resolve to nothing?

Correction (wake 135, from a reader on 1f916, c88940): git can print an
abbreviation of any length from 4 to 40 (`--abbrev=N`, `core.abbrev`), so a
39-character string is not impossible by length alone. What can be checked:
  label     is the string presented as the full hash ("Full", "full SHA",
            "full hash") in the 40 characters before it?
  resolves  is it a prefix of a real commit of the organisation (all
            branches, commits.jsonl)? A prefix that resolves is a real commit
            written short; one that does not resolves to nothing.
Strings followed by an ellipsis are skipped: the agent marked them as cut.
Repositories with sha256 object names (64 chars) cannot reach this table:
the hex extractor stops at 40 and requires a word boundary.

Counted on distinct (regime, model, string) and per document.
Output: derivado/final/comprimento2.txt (table) and
derivado/comprimento2-amostra.jsonl (short contexts, for hand reading only;
never published).
usage: python3 comprimento2.py
"""
import collections, gzip, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER
from tokens import _HEX, _DENTRO, _contexto, _eh_sha, limpa

CORTE = '2026-06-29'     # the org moved to GitLab: no commit list after this
_FULL = re.compile(r'full', re.I)


def longos(texto):
    """(string, labelled_full, context) for commit claims of 20-39 chars."""
    t = limpa(texto)
    for m in _HEX.finditer(t):
        h = m.group(1)
        if len(h) < 20 or len(h) == 40 or not _eh_sha(h):
            continue
        a, b = m.start(), m.end()
        if a > 0 and t[a - 1] in _DENTRO:
            continue
        if _contexto(t, a, b) != 'git':
            continue
        if t[b:b + 3] == '...' or t[b:b + 1] == '\u2026':
            continue            # elided on purpose ("1a2b3c4d5e6f..."): an honest abbreviation
        yield h, bool(_FULL.search(t[max(0, a - 40):a])), t[max(0, a - 160):b + 60]


def main():
    shas = set()
    for l in open(os.path.join(DER, 'gh', 'commits.jsonl')):
        shas.add(json.loads(l)['sha'])
    por7 = collections.defaultdict(list)
    for s in shas:
        por7[s[:7]].append(s)

    def resolve(h):
        return any(s.startswith(h) for s in por7.get(h[:7], ()))

    def caiu_um(h):
        """h is a real commit with exactly one character dropped"""
        return any(len(s) == len(h) + 1 and any(s[:i] + s[i + 1:] == h for i in range(len(s)))
                   for s in por7.get(h[:7], ()))

    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        nm = {a['id']: a['name'] for a in map(json.loads, f)}

    def docs():
        for l in open(os.path.join(DER, 'pares.jsonl')):
            p = json.loads(l)
            yield 'summary', p['agent'], p['stop'], p['summary']
        with gzip.open(os.path.join(DADOS, 'agent_memories.jsonl.gz'), 'rt') as f:
            for l in f:
                m = json.loads(l)
                yield 'memory', m['agent_id'], m['created_at'], m.get('content') or ''

    distintos = {}                        # (regime, model, h) -> (label, resolves)
    ndocs = collections.Counter()         # same key -> documents
    amostra = {}
    depois = 0
    tarde = collections.Counter()         # (regime, model, len, h) labelled full, after CORTE -> documents
    for regime, agent, quando, texto in docs():
        if str(quando)[:10] >= CORTE:
            depois += 1
            vistos = set()
            for h, rot, _ctx in longos(texto):
                k = (regime, nm.get(agent, agent[:8]), len(h), h)
                if rot and k not in vistos:
                    vistos.add(k)
                    tarde[k] += 1
            continue
        vistos = set()
        for h, rot, ctx in longos(texto):
            k = (regime, nm.get(agent, agent[:8]), h)
            if k in vistos:
                continue
            vistos.add(k)
            if k not in distintos:
                distintos[k] = (rot, resolve(h), h[:7] in por7)
                amostra[k] = ctx
            elif rot and not distintos[k][0]:
                distintos[k] = (True,) + distintos[k][1:]
            ndocs[k] += 1

    out = []
    p = out.append
    p('Commit claims written at 20-39 characters (distinct strings; docs = documents repeating them)\n')
    p(f"{'regime':8} {'model':24} {'strings':>7} {'docs':>6} | {'resolve':>7} {'no':>4} {'no, 7 ok':>8} {'1 dropped':>9} | {'labelled full':>13} {'full, no':>8} {'docs':>6}")
    tab = collections.defaultdict(lambda: collections.Counter())
    for (regime, model, h), (rot, res, p7) in distintos.items():
        c = tab[(regime, model)]
        if not res and p7:
            c['p7'] += 1
        if not res and caiu_um(h):
            c['drop'] += 1
        c['n'] += 1
        c['docs'] += ndocs[(regime, model, h)]
        c['res' if res else 'nores'] += 1
        if rot:
            c['full'] += 1
            if not res:
                c['fullno'] += 1
                c['fullno_docs'] += ndocs[(regime, model, h)]
    tot = collections.Counter()
    for (regime, model), c in sorted(tab.items(), key=lambda x: (x[0][0], -x[1]['fullno_docs'], -x[1]['n'])):
        tot.update(c)
        p(f"{regime:8} {model:24} {c['n']:7} {c['docs']:6} | {c['res']:7} {c['nores']:4} {c['p7']:8} {c['drop']:9} | {c['full']:13} {c['fullno']:8} {c['fullno_docs']:6}")
    p(f"{'ALL':33} {tot['n']:7} {tot['docs']:6} | {tot['res']:7} {tot['nores']:4} {tot['p7']:8} {tot['drop']:9} | {tot['full']:13} {tot['fullno']:8} {tot['fullno_docs']:6}")
    lens = collections.Counter((len(h), v[1]) for (_r, _m, h), v in distintos.items())
    p('\nlength -> (resolves, does not): ' + ', '.join(
        f'{n}: ({lens[(n, True)]}, {lens[(n, False)]})' for n in sorted({n for n, _ in lens})))
    p(f'\nOnly documents before {CORTE} (move to GitLab; no commit list after it): {depois} later documents skipped.')
    p(f'\nAfter {CORTE} (cannot be resolved; counted only): strings at 20-39 characters labelled full')
    p(f"{'regime':8} {'model':24} {'length':>6} {'docs':>6}")
    for (regime, model, n, _h), d in sorted(tarde.items(), key=lambda x: -x[1]):
        p(f'{regime:8} {model:24} {n:6} {d:6}')
    if not tarde:
        p('(none)')
    p('\n"no, 7 ok": does not resolve, but its first 7 characters are a real commit: a real hash copied wrong further on.'
      '\n"1 dropped": it is a real commit with exactly one character left out.')
    os.makedirs(os.path.join(DER, 'final'), exist_ok=True)
    with open(os.path.join(DER, 'final', 'comprimento2.txt'), 'w') as f:
        f.write('\n'.join(out) + '\n')
    with open(os.path.join(DER, 'comprimento2-amostra.jsonl'), 'w') as f:
        for k, ctx in amostra.items():
            f.write(json.dumps({'regime': k[0], 'model': k[1], 'len': len(k[2]), 'label': distintos[k][0],
                                'resolves': distintos[k][1], 'docs': ndocs[k], 'ctx': ctx}) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
