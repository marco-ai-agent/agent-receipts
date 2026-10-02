"""How far is a long hash labelled "full" carried forward, compared with its
short form?

Memories after 2026-06-29 only (the commit list stops there, so these strings
cannot be resolved; this only counts copies). Pass 1 finds commit claims of
20-39 characters labelled full (comprimento2.longos). Pass 2 counts, for each,
the later memories of the same agent that contain the long string, and those
that contain its first 7 characters.

usage: python3 copias_full.py
Prints model, length, and the two counts; no hash is printed.
"""
import collections, gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS
from comprimento2 import CORTE, longos


def memorias():
    with gzip.open(os.path.join(DADOS, 'agent_memories.jsonl.gz'), 'rt') as f:
        for l in f:
            m = json.loads(l)
            if str(m['created_at'])[:10] >= CORTE:
                yield m['agent_id'], str(m['created_at']), m.get('content') or ''


def main():
    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        nm = {a['id']: a['name'] for a in map(json.loads, f)}

    primeiro = {}                       # (agent, long string) -> first time labelled full
    for agent, quando, texto in memorias():
        for h, rot, _ctx in longos(texto):
            k = (agent, h)
            if rot and (k not in primeiro or quando < primeiro[k]):
                primeiro[k] = quando
    print(f'{len(primeiro)} (agent, string) pairs labelled full after {CORTE}', flush=True)

    longo = collections.Counter()
    curto = collections.Counter()
    por_agente = collections.defaultdict(list)
    for k in primeiro:
        por_agente[k[0]].append(k)
    for agent, quando, texto in memorias():
        for k in por_agente.get(agent, ()):
            if quando < primeiro[k]:
                continue
            if k[1] in texto:
                longo[k] += 1
            if k[1][:7] in texto:
                curto[k] += 1

    print(f'\nLong strings labelled full, memories after {CORTE}: memories (same agent, from the first')
    print('labelling on) that contain the long string, and that contain its first 7 characters')
    print(f"{'model':24} {'length':>6} {'with long':>9} {'with first 7':>12}")
    for k in sorted(primeiro, key=lambda k: -curto[k]):
        print(f'{nm.get(k[0], k[0][:8]):24} {len(k[1]):6} {longo[k]:9} {curto[k]:12}')


if __name__ == '__main__':
    main()
