"""Print the context of claimed tokens with a given verdict, for hand audit.

usage: python3 sample.py <verdict> [N] [seed]
Each case: agent, date, session size, whether the agent typed the token in a
command, and the summary text around the token.
"""
import gzip, json, os, random, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER


def main():
    alvo = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    random.seed(int(sys.argv[3]) if len(sys.argv) > 3 else 1)
    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        nm = {a['id']: a['name'] for a in map(json.loads, f)}
    resumo = {}
    for l in open(os.path.join(DER, 'pares.jsonl')):
        p = json.loads(l)
        resumo[p['session']] = p['summary']
    casos = [json.loads(l) for l in open(os.path.join(DER, 'veredictos.jsonl'))]
    casos = [c for c in casos if c['verdict'] == alvo]
    if os.environ.get('COMMIT'):
        sys.path.insert(0, os.path.dirname(__file__))
        from tokens import commit_claims
        casos = [c for c in casos if c['kind'] == 'sha' and c['token'] in commit_claims(resumo[c['session']])]
    # one case per distinct token, so a hash carried forward 10 times is read once
    vistos, unicos = set(), []
    for c in casos:
        if c['token'] not in vistos:
            vistos.add(c['token'])
            unicos.append(c)
    print(f'{len(casos)} cases, {len(unicos)} distinct tokens; showing {min(n, len(unicos))}\n')
    for c in random.sample(unicos, min(n, len(unicos))):
        s = resumo[c['session']]
        i = s.find(c['token'])
        if i < 0:
            m = re.search(re.escape(c['token']), s, re.I)
            i = m.start() if m else 0
        ctx = s[max(0, i - 220):i + 120].replace('\n', ' | ')
        print(f"## {c['token']} [{c['kind']}] {nm.get(c['agent'], '?')} {c['stop'][:10]} "
              f"turns={c['turns']} bash={c['bash_turns']} typed={c['typed']} first_seen={c['first_seen']}")
        print('   ' + ctx + '\n')

if __name__ == '__main__':
    main()
