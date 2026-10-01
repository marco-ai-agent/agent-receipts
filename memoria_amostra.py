"""Hand-audit sample of `never` commit claims in consolidated memories.

For each model given, picks the 5 most re-asserted distinct never tokens and 5
at random (seeded), takes the FIRST memory that wrote each, and prints the
text around the token, so a person (or I) can read whether it is a commit.

usage: python3 memoria_amostra.py "GPT-5.2" "GPT-5.6 Sol"
Output also saved to derivado/memoria-amostra.txt (agent text only; the
dataset stays out of git).
"""
import collections, gzip, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER


def main():
    modelos = sys.argv[1:]
    random.seed(5)
    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        nm = {a['id']: a['name'] for a in map(json.loads, f)}
    alvo_agentes = {i for i, n in nm.items() if n in modelos}
    docs = collections.defaultdict(list)    # (agent, token) -> [(time, doc)]
    for l in open(os.path.join(DER, 'veredictos2.jsonl')):
        v = json.loads(l)
        if v['regime'] == 'memory' and v['kind'] == 'sha' and v['verdict'] == 'never' and v['agent'] in alvo_agentes:
            docs[(v['agent'], v['token'])].append((v['time'], v['doc']))
    escolha = []
    for m in modelos:
        ks = [k for k in docs if nm[k[0]] == m]
        ks.sort(key=lambda k: -len(docs[k]))
        top = ks[:5]
        resto = [k for k in ks[5:]]
        escolha += top + random.sample(resto, min(5, len(resto)))
    quer = {}
    for k in escolha:
        t, d = min(docs[k])
        quer[d] = quer.get(d, []) + [(k, t, len(docs[k]))]
    print(f'{len(escolha)} tokens, {len(quer)} memories to fetch', flush=True)
    achado = {}
    with gzip.open(os.path.join(DADOS, 'agent_memories.jsonl.gz'), 'rt') as f:
        for l in f:
            r = json.loads(l)
            if r['id'] in quer:
                achado[r['id']] = r['content']
                if len(achado) == len(quer):
                    break
    out = []
    for d, itens in quer.items():
        txt = achado.get(d, '')
        for (agent, tok), t, n in itens:
            i = txt.find(tok)
            ctx = txt[max(0, i - 300):i + 200].replace('\n', ' | ') if i >= 0 else '(not found)'
            out.append(f'## {tok} {nm[agent]} first {t[:16]} re-asserted in {n} memories\n   {ctx}\n')
    s = '\n'.join(sorted(out))
    open(os.path.join(DER, 'memoria-amostra.txt'), 'w').write(s)
    print(s)

if __name__ == '__main__':
    main()
