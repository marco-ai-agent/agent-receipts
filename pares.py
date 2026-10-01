"""Step 1: pair every STOP_USING_COMPUTER summary with the session it closes.

The STOP event carries the agent's own session summary but no session id;
it closes the most recent START_USING_COMPUTER of the same agent (ordered by
event_index). Output: one JSON line per summary, written under the dataset
folder (derived data from the dataset never goes into git).
"""
import gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER

SAIDA = os.path.join(DADOS, 'derivado', 'pares.jsonl')

def main():
    eventos = []
    with gzip.open(os.path.join(DADOS, 'events.jsonl.gz'), 'rt') as f:
        for linha in f:
            e = json.loads(linha)
            d = e.get('data') or {}
            t = d.get('actionType')
            if t in ('START_USING_COMPUTER', 'STOP_USING_COMPUTER'):
                eventos.append((e['event_index'], t, d.get('agentId'), d.get('computerUseSessionId'),
                                e['created_at'], d.get('summary') or ''))
    eventos.sort()
    aberta = {}  # agent -> (session_id, started_at)
    n = sem = 0
    with open(SAIDA, 'w') as out:
        for idx, t, agente, sessao, quando, resumo in eventos:
            if t == 'START_USING_COMPUTER':
                aberta[agente] = (sessao, quando)
                continue
            par = aberta.pop(agente, None)
            if par is None or not resumo.strip():
                sem += 1
                continue
            out.write(json.dumps({'agent': agente, 'session': par[0], 'start': par[1],
                                  'stop': quando, 'event_index': idx, 'summary': resumo}) + '\n')
            n += 1
    print(f'{n} summaries paired; {sem} stops without an open session or without summary')

if __name__ == '__main__':
    main()
