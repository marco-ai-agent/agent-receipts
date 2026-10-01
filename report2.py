"""Per regime x model table from veredictos2.jsonl (commit claims by default).

usage: python3 report2.py [sha|comment|all]
Unit: (document, token). A hash carried forward in ten memories counts ten
times: each memory re-asserts it to the agent's future self.
"""
import gzip, json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER

ORDEM = ['own', 'self', 'others', 'later', 'never']

def main():
    tipo = sys.argv[1] if len(sys.argv) > 1 else 'sha'
    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        nm = {a['id']: a['name'] for a in map(json.loads, f)}
    t = collections.defaultdict(collections.Counter)
    distintos = collections.defaultdict(set)
    for l in open(os.path.join(DER, 'veredictos2.jsonl')):
        v = json.loads(l)
        if tipo != 'all' and v['kind'] != tipo:
            continue
        k = (v['regime'], nm.get(v['agent'], v['agent'][:8]))
        t[k][v['verdict']] += 1
        if v['verdict'] == 'never':
            distintos[k].add(v['token'])
    for regime in ('summary', 'memory'):
        print(f'\n== {regime} ({tipo}) ==')
        print(f"{'agent':26} {'claims':>8} " + ' '.join(f'{o:>7}' for o in ORDEM) + f" {'never%':>7} {'distinct never':>14}")
        tot = collections.Counter()
        for (r, a), c in sorted(t.items(), key=lambda x: -sum(x[1].values())):
            if r != regime:
                continue
            n = sum(c.values())
            tot.update(c)
            if n < 30:
                continue
            print(f'{a:26} {n:8} ' + ' '.join(f'{c[o]:7}' for o in ORDEM) + f" {100*c['never']/n:6.1f}% {len(distintos[(r, a)]):14}")
        n = sum(tot.values())
        if n:
            print(f"{'ALL':26} {n:8} " + ' '.join(f'{tot[o]:7}' for o in ORDEM) + f" {100*tot['never']/n:6.1f}%")

if __name__ == '__main__':
    main()
