"""What extractor v4 (the ellipsis rule in tokens.py) removes, before a full run.

Reads every session summary and every consolidated memory once, and writes
each commit claim that v3 accepts and v4 drops, with the text around it, to
derivado/elipse-derrubados.jsonl. Prints counts per regime and per model.

  python3 elipse.py            the pass (memories take ~20 min: run with nohup)
  python3 elipse.py amostra N SEED
                               N distinct dropped tokens per regime, seeded,
                               for a hand check (agent text only)
"""
import collections, gzip, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER
from tokens import commit_claims, limpa

SAIDA = os.path.join(DER, 'elipse-derrubados.jsonl')


def ctx(texto, tok):
    t = limpa(texto)
    i = t.find(tok)
    return t[max(0, i - 220):i + 120].replace('\n', ' | ')


def passada():
    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        nm = {a['id']: a['name'] for a in map(json.loads, f)}
    total = collections.Counter()
    caiu = collections.Counter()
    por_modelo = collections.Counter()
    with open(SAIDA, 'w') as out:
        def doc(regime, did, agente, texto):
            v3 = commit_claims(texto, v4=False)
            if not v3:
                return
            v4 = commit_claims(texto)
            total[regime] += len(v3)
            for tok in v3:
                if tok not in v4:
                    caiu[regime] += 1
                    por_modelo[(regime, nm.get(agente, '?'))] += 1
                    out.write(json.dumps({'regime': regime, 'doc': did, 'agent': nm.get(agente, '?'),
                                          'token': tok, 'ctx': ctx(texto, tok)}) + '\n')
        for l in open(os.path.join(DER, 'pares.jsonl')):
            p = json.loads(l)
            doc('summary', p['session'], p['agent'], p['summary'])
        print(f"summaries: v3 {total['summary']} claims, v4 drops {caiu['summary']}", flush=True)
        with gzip.open(os.path.join(DADOS, 'agent_memories.jsonl.gz'), 'rt') as f:
            for l in f:
                m = json.loads(l)
                doc('memory', m['id'], m['agent_id'], m.get('content') or '')
    for r in ('summary', 'memory'):
        print(f"{r}: v3 {total[r]} claims (document, token), v4 drops {caiu[r]} "
              f"({100 * caiu[r] / max(1, total[r]):.1f}%)")
    for (r, m), n in sorted(por_modelo.items(), key=lambda x: -x[1]):
        print(f'  {r:8} {m:28} {n}')


def amostra(n, seed):
    random.seed(seed)
    por = collections.defaultdict(dict)
    for l in open(SAIDA):
        c = json.loads(l)
        por[c['regime']].setdefault(c['token'], c)
    for r in ('summary', 'memory'):
        ks = sorted(por[r])
        print(f'=== {r}: {len(ks)} distinct dropped tokens; showing {min(n, len(ks))}\n')
        for k in random.sample(ks, min(n, len(ks))):
            c = por[r][k]
            print(f"## {k} {c['agent']}\n   {c['ctx']}\n")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'amostra':
        amostra(int(sys.argv[2]), int(sys.argv[3]))
    else:
        passada()
