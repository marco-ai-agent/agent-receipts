"""Impossible hash lengths, per regime x model, from veredictos2.jsonl (v3).

A commit claim written at 20+ characters is a "full" hash attempt; git writes
40. Anything else (39, 38, 32...) cannot be a commit id. Counted on distinct
(regime, agent, token), and also per document (how many times re-asserted).

usage: python3 comprimento.py
"""
import collections, gzip, json, os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER


def main():
    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        nm = {a['id']: a['name'] for a in map(json.loads, f)}
    cheio = collections.defaultdict(set)     # (regime, model) -> distinct tokens written >= 20
    ruim = collections.defaultdict(dict)     # (regime, model) -> token -> length
    docs_ruim = collections.Counter()        # (regime, model) -> documents re-asserting a bad one
    comps = collections.Counter()
    for l in open(os.path.join(DER, 'veredictos2.jsonl')):
        v = json.loads(l)
        if v['kind'] != 'sha' or v['len'] < 20:
            continue
        k = (v['regime'], nm.get(v['agent'], v['agent'][:8]))
        cheio[k].add(v['token'])
        if v['len'] != 40:
            ruim[k][v['token']] = v['len']
            docs_ruim[k] += 1
            comps[v['len']] += 1
    print(f"{'regime':8} {'model':24} {'full claims':>11} {'impossible':>10} {'%':>6} {'docs':>6}")
    for k in sorted(cheio, key=lambda k: (k[0], -len(ruim[k]))):
        n, r = len(cheio[k]), len(ruim[k])
        if n < 10 and not r:
            continue
        print(f'{k[0]:8} {k[1]:24} {n:11} {r:10} {100 * r / n:5.1f}% {docs_ruim[k]:6}')
    print('\nlengths of impossible full hashes (per document):', dict(sorted(comps.items())))

if __name__ == '__main__':
    main()
