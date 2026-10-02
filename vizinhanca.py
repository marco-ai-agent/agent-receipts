"""Neighbourhood test: is an unanchored commit claim a real commit misread?

For every distinct (regime, agent, token) commit claim, earliest document time:
  exists   the 7-char prefix is a commit anywhere in the org (all branches,
           any date), from the commit list gh-commits-org.js downloaded
  d1 / d2  otherwise, the nearest real commit in a time window around the
           document is at Hamming distance 1 / 2 (same length, substitutions)
  far      nothing within 2

Chance baseline: for each claim, K random 7-hex strings through the same
window. A misread has a near neighbour far more often than chance does.

Index: for each commit prefix and each pair of masked positions (21 pairs),
key -> commits. A query at distance <= 2 shares at least one masked key.

Only claims dated before the org moved to GitLab (2026-06-29) are scored:
after that GitHub has no commits to find.

usage: python3 vizinhanca.py [dias_antes=14] [dias_depois=1] [K=20]
"""
import collections, datetime as dt, gzip, itertools, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER

GH = os.path.join(DER, 'gh', 'commits.jsonl')
CORTE = dt.datetime(2026, 6, 29)
PARES = list(itertools.combinations(range(7), 2))
HEX = '0123456789abcdef'

def quando(s):
    s = s.replace('T', ' ').replace('Z', '')[:19]
    return dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

def chaves(p):
    for i, j in PARES:
        yield (i, j, p[:i] + p[i + 1:j] + p[j + 1:])

def ham(a, b):
    return sum(x != y for x, y in zip(a, b))

def main():
    antes = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    depois = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    random.seed(11)

    commits = []    # (prefix7, datetime, repo, sha)
    vistos = set()
    for l in open(GH):
        c = json.loads(l)
        if c['sha'] in vistos:      # parallel downloads can repeat a repo
            continue
        vistos.add(c['sha'])
        d = c.get('data') or c.get('cdata')
        commits.append((c['sha'][:7], quando(d), c['repo'], c['sha']))
    existe = {c[0] for c in commits}
    idx = collections.defaultdict(list)
    for n, c in enumerate(commits):
        for k in chaves(c[0]):
            idx[k].append(n)
    datas = sorted(c[1] for c in commits)
    print(f'{len(commits)} commits, {len(existe)} distinct prefixes, {datas[0]:%Y-%m-%d} .. {datas[-1]:%Y-%m-%d}')

    with gzip.open(os.path.join(DADOS, 'agents.jsonl.gz'), 'rt') as f:
        nm = {a['id']: a['name'] for a in map(json.loads, f)}

    # distinct claims, earliest time; keep the verdict of the earliest document
    claims = {}
    for l in open(os.path.join(DER, os.environ.get('VEREDICTOS', 'veredictos2.jsonl'))):
        v = json.loads(l)
        if v['kind'] != 'sha':
            continue
        k = (v['regime'], v['agent'], v['token'])
        t = quando(v['time'])
        if k not in claims or t < claims[k][0]:
            claims[k] = (t, v['verdict'], v['doc'])

    def vizinho(tok, t):
        lo, hi = t - dt.timedelta(days=antes), t + dt.timedelta(days=depois)
        best = (9, None)
        vistos = set()
        for k in chaves(tok):
            for n in idx.get(k, ()):
                if n in vistos:
                    continue
                vistos.add(n)
                c = commits[n]
                if lo <= c[1] <= hi:
                    d = ham(tok, c[0])
                    if d < best[0]:
                        best = (d, c)
        return best

    tab = collections.defaultdict(collections.Counter)   # (regime, verdict) -> outcome
    chance = collections.defaultdict(collections.Counter)
    exemplos = []
    for (regime, agent, tok), (t, verdict, doc) in claims.items():
        if t >= CORTE:
            continue
        g = (regime, verdict)
        if tok in existe:
            tab[g]['exists'] += 1
        else:
            d, c = vizinho(tok, t)
            o = 'd1' if d == 1 else 'd2' if d == 2 else 'far'
            tab[g][o] += 1
            if o != 'far' and verdict == 'never':
                exemplos.append({'regime': regime, 'model': nm.get(agent, agent[:8]), 'claim': tok, 'real': c[3][:7],
                                 'repo': c[2], 'd': d, 'doc': doc, 'time': f'{t:%Y-%m-%d %H:%M}',
                                 'commit_time': f'{c[1]:%Y-%m-%d %H:%M}'})
        for _ in range(K):
            r = ''.join(random.choice(HEX) for _ in range(7))
            if r in existe:
                chance[g]['exists'] += 1
                continue
            d, _c = vizinho(r, t)
            chance[g]['d1' if d == 1 else 'd2' if d == 2 else 'far'] += 1

    print(f'\nwindow: {antes} days before .. {depois} after the document; chance = {K} random strings per claim')
    print(f"{'regime':8} {'verdict':8} {'n':>6} {'exists':>7} {'d1':>6} {'d2':>6} {'far':>6} | {'chance exists':>13} {'d1':>6} {'d2':>6}")
    for g in sorted(tab):
        c, ch = tab[g], chance[g]
        n, m = sum(c.values()), sum(ch.values())
        pc = lambda x, y: f'{100 * x / y:5.1f}%' if y else '   - '
        print(f'{g[0]:8} {g[1]:8} {n:6} {pc(c["exists"], n):>7} {pc(c["d1"], n):>6} {pc(c["d2"], n):>6} {pc(c["far"], n):>6} |'
              f' {pc(ch["exists"], m):>13} {pc(ch["d1"], m):>6} {pc(ch["d2"], m):>6}')
    with open(os.path.join(DER, 'vizinhos-never.jsonl'), 'w') as f:
        for e in sorted(exemplos, key=lambda e: (e['regime'], e['time'])):
            f.write(json.dumps(e) + '\n')
    print(f'\n{len(exemplos)} never claims with a near neighbour -> derivado/vizinhos-never.jsonl')

    # Which characters get swapped at distance 1? A misread off a screen swaps
    # look-alike glyphs (3/5/9/8/6/0, b/6, 1/l...); random corruption would not.
    trocas = collections.Counter()
    pos = collections.Counter()
    for e in exemplos:
        if e['d'] != 1:
            continue
        for i, (r, c) in enumerate(zip(e['real'], e['claim'])):
            if r != c:
                trocas[(r, c)] += 1
                pos[i] += 1
    if trocas:
        print('\nd1 substitutions, real -> written (never claims):')
        print('  ' + ', '.join(f'{r}->{c} {n}' for (r, c), n in trocas.most_common()))
        dig = sum(n for (r, c), n in trocas.items() if r.isdigit() and c.isdigit())
        print(f'  digit->digit {dig} of {sum(trocas.values())} = {dig / sum(trocas.values()):.0%} (chance if uniform over hex: {10 * 9 / (16 * 15):.0%})')
        print('  position of the swapped character (0-6):', dict(sorted(pos.items())))

if __name__ == '__main__':
    main()
