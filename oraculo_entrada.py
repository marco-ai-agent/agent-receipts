"""Build the GitHub-oracle input from the v1 verdicts, restricted to commit claims.

Groups (distinct tokens): every `never` commit claim, and a same-size random
sample of `own` commit claims as the baseline (anchored in the session's own
tool output, so presumably real). Summaries only: the repos moved to GitLab on
2026-06-29 and the summary regime ends in March 2026.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from tokens import commit_claims
from config import DER

random.seed(7)
resumo = {json.loads(l)['session']: json.loads(l)['summary'] for l in open(os.path.join(DER, 'pares.jsonl'))}
grupos = {'never': set(), 'own': set(), 'later': set()}
for l in open(os.path.join(DER, 'veredictos.jsonl')):
    v = json.loads(l)
    if v['kind'] != 'sha' or v['verdict'] not in grupos:
        continue
    if v['token'] in commit_claims(resumo[v['session']]):
        grupos[v['verdict']].add(v['token'])
never = sorted(grupos['never'])
later = sorted(grupos['later'])
own = random.sample(sorted(grupos['own']), min(len(never), len(grupos['own'])))
json.dump({'never': never, 'own': own, 'later': later}, open(os.path.join(DER, 'oraculo-grupos.json'), 'w'))
open(os.path.join(DER, 'oraculo-entrada.txt'), 'w').write('\n'.join(never + own + later) + '\n')
print(f'never {len(never)}, own sample {len(own)}, later {len(later)} -> {len(never) + len(own) + len(later)} queries')
