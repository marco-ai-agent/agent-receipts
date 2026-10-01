"""Extract the turns of selected sessions (one pass over computer_use_turns).

Sessions: those whose summary has a `never` commit claim (v1 verdicts).
Output keeps id/time/action/short output, enough to find the screenshot of
the moment a claim was made (images/computer-use-turns/<PT date>.tar).
"""
import gzip, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from tokens import commit_claims
from config import DADOS, DER


resumo = {json.loads(l)['session']: json.loads(l)['summary'] for l in open(os.path.join(DER, 'pares.jsonl'))}
alvo = set()
for l in open(os.path.join(DER, 'veredictos.jsonl')):
    v = json.loads(l)
    if v['verdict'] == 'never' and v['kind'] == 'sha' and v['token'] in commit_claims(resumo[v['session']]):
        alvo.add(v['session'])
print(len(alvo), 'sessions', flush=True)
with gzip.open(os.path.join(DADOS, 'computer_use_turns.jsonl.gz'), 'rt') as f, \
        open(os.path.join(DER, 'turnos-never.jsonl'), 'w') as out:
    for linha in f:
        if '"session_id"' not in linha:
            continue
        r = json.loads(linha)
        if r.get('session_id') not in alvo:
            continue
        out.write(json.dumps({'id': r['id'], 'session': r['session_id'], 't': r['created_at'],
                              'action': r.get('agent_action'), 'out': (r.get('output') or '')[:500],
                              'err': (r.get('error') or '')[:300],
                              'redacted': r.get('screenshot_is_redacted')}) + '\n')
print('done', flush=True)
