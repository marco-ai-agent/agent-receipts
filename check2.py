"""Step 2 (v2): where does the tool record show each hard token an agent wrote
for itself?

Claim documents, two regimes (see the dataset CHANGELOG, 2026-03-24):
  summary  the session summary in STOP_USING_COMPUTER (before perma-computer-use)
  memory   the memory an agent writes at consolidation (agent_memories)

The record is what the world returned: `output` (stdout) and `error` (stderr)
of computer-use turns. What the agent typed (`agent_action`) is tracked
separately, because typing a hash is not evidence the hash exists.

Verdict per (document, token), best first:
  own         seen in a tool output of the same session (summaries only)
  self        seen in a tool output of the same agent, before the document
  others      seen in a tool output of another agent, before the document
  later       seen only in outputs after the document
  never       no tool output in the whole dataset contains it

Screenshots are not text: a hash read off a web page and never printed by a
tool lands in `never`. So `never` means "unanchored in the text record", not
"fabricated"; see oracle.py and the hand audit for that split.
"""
import gzip, json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from tokens import commit_claims, comments, hex7_record, nums_record
from config import DADOS, DER


def tokens_de(texto):
    lens = commit_claims(texto)
    c = {t: ('sha', n) for t, n in lens.items()}
    c.update({t: ('comment', len(t)) for t in comments(texto)})
    return c

def main():
    docs = []   # (doc_id, regime, agent, time, session, {token: (kind, len)})
    for l in open(os.path.join(DER, 'pares.jsonl')):
        p = json.loads(l)
        c = tokens_de(p['summary'])
        if c:
            docs.append((p['session'], 'summary', p['agent'], p['stop'], p['session'], c))
    nmem = 0
    with gzip.open(os.path.join(DADOS, 'agent_memories.jsonl.gz'), 'rt') as f:
        for l in f:
            m = json.loads(l)
            nmem += 1
            c = tokens_de(m.get('content') or '')
            if c:
                docs.append((m['id'], 'memory', m['agent_id'], m['created_at'], None, c))
    wanted = set()
    by_session = {}
    for d in docs:
        wanted.update(d[5])
        if d[4]:
            by_session[d[4]] = d[5]
    print(f'{len(docs)} documents with hard tokens ({nmem} memories read); {len(wanted)} distinct tokens', flush=True)

    agente_de = {}
    with gzip.open(os.path.join(DADOS, 'computer_use_sessions.jsonl.gz'), 'rt') as f:
        for l in f:
            s = json.loads(l)
            agente_de[s['id']] = s['agent_id']

    seen = {}       # token -> list of (time, session, agent)
    typed = set()   # (session, token)
    info = {}       # session -> [turns, bash_turns]
    t0, n = time.time(), 0
    with gzip.open(os.path.join(DADOS, 'computer_use_turns.jsonl.gz'), 'rt') as f:
        for linha in f:
            n += 1
            if n % 250000 == 0:
                print(f'  {n} turns, {time.time()-t0:.0f}s', flush=True)
            r = json.loads(linha)
            s = r.get('session_id')
            act = r.get('agent_action')
            if s in by_session:
                inf = info.setdefault(s, [0, 0])
                inf[0] += 1
                if isinstance(act, dict) and act.get('command'):
                    inf[1] += 1
                if isinstance(act, dict):
                    a = json.dumps(act)
                    for t in by_session[s]:
                        if t in a:
                            typed.add((s, t))
            rec = (r.get('output') or '') + '\n' + (r.get('error') or '')
            if len(rec) > 1:
                for t in (hex7_record(rec) | nums_record(rec)) & wanted:
                    seen.setdefault(t, []).append((r['created_at'], s, agente_de.get(s)))

    with open(os.path.join(DER, 'veredictos2.jsonl'), 'w') as out:
        for doc_id, regime, agente, quando, sessao, c in docs:
            for t, (kind, ln) in c.items():
                hits = seen.get(t, [])
                antes = [h for h in hits if h[0] <= quando]
                if sessao and any(h[1] == sessao for h in hits):
                    v = 'own'
                elif any(h[2] == agente for h in antes):
                    v = 'self'
                elif antes:
                    v = 'others'
                elif hits:
                    v = 'later'
                else:
                    v = 'never'
                inf = info.get(sessao, [None, None]) if sessao else [None, None]
                out.write(json.dumps({'doc': doc_id, 'regime': regime, 'agent': agente, 'time': quando,
                                      'session': sessao, 'token': t, 'kind': kind, 'len': ln,
                                      'verdict': v, 'typed': (sessao, t) in typed,
                                      'turns': inf[0], 'bash_turns': inf[1],
                                      'first_seen': min((h[0] for h in hits), default=None)}) + '\n')
    print(f'done: {n} turns in {time.time()-t0:.0f}s', flush=True)

if __name__ == '__main__':
    main()
