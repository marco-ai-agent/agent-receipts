"""Impossible full hashes: a commit claim written at >= 20 hex chars that is
not 40 long. A git SHA-1 is 40 hex chars; an abbreviation is 7-12. Something
written at 32 or 39 chars and called a commit is neither: it was mis-copied or
made up, and in both cases it cannot be used to find the commit.

usage: python3 malformados.py [summary|memory|all]
"""
import gzip, json, os, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
from tokens import commit_claims
from config import DADOS, DER


def nomes():
    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        return {a['id']: a['name'] for a in map(json.loads, f)}

def docs(regime):
    if regime in ('summary', 'all'):
        for l in open(os.path.join(DER, 'pares.jsonl')):
            p = json.loads(l)
            yield 'summary', p['agent'], p['stop'], p['summary']
    if regime in ('memory', 'all'):
        with gzip.open(os.path.join(DADOS, 'agent_memories.jsonl.gz'), 'rt') as f:
            for l in f:
                m = json.loads(l)
                yield 'memory', m['agent_id'], m['created_at'], m.get('content') or ''

def main():
    regime = sys.argv[1] if len(sys.argv) > 1 else 'summary'
    nm = nomes()
    longos = collections.Counter()
    ruins = collections.Counter()
    exemplos = collections.defaultdict(list)
    comprimentos = collections.Counter()
    for reg, ag, quando, texto in docs(regime):
        for h7, n in commit_claims(texto).items():
            if n < 20:
                continue
            a = nm.get(ag, ag[:8])
            longos[a] += 1
            if n != 40:
                ruins[a] += 1
                comprimentos[n] += 1
                if len(exemplos[a]) < 3:
                    exemplos[a].append((quando[:10], h7, n))
    print(f"{'agent':28} {'full-length claims':>18} {'impossible length':>17} {'%':>6}")
    for a, n in sorted(longos.items(), key=lambda x: -x[1]):
        print(f"{a:28} {n:18} {ruins[a]:17} {100*ruins[a]/n:5.1f}%  {exemplos[a]}")
    print('lengths seen (not 40):', sorted(comprimentos.items()))
    print('TOTAL', sum(longos.values()), sum(ruins.values()))

if __name__ == '__main__':
    main()
