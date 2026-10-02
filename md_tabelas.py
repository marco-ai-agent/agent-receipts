"""Markdown tables for README.md, built from the files in results/ so that no
number in the README is typed by hand.

usage: python3 md_tabelas.py [results_dir]
"""
import os, re, sys

R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')


def per_model():
    linhas = open(os.path.join(R, 'per-model.txt')).read().split('\n')
    for regime in ('summary', 'memory'):
        i = next(n for n, l in enumerate(linhas) if l.startswith(f'== {regime}'))
        rows = []
        for l in linhas[i + 2:]:
            if not l.strip() or l.startswith('=='):
                break
            m = re.match(r'(.+?)\s{2,}(\d+)\s+' + r'\s+'.join([r'(\d+)'] * 5) + r'\s+([\d.]+)%(?:\s+(\d+))?$', l)
            if m:
                rows.append(m.groups())
        print(f'\n{regime}: model | claims | never | never % | distinct never')
        print('| model | claims | never | never % | distinct never strings |\n| --- | ---: | ---: | ---: | ---: |')
        tot = [r for r in rows if r[0].strip() == 'ALL']
        body = sorted((r for r in rows if r[0].strip() != 'ALL'), key=lambda r: -float(r[7]))
        for r in body + tot:
            nome = '**all**' if r[0].strip() == 'ALL' else r[0].strip()
            print(f'| {nome} | {int(r[1]):,} | {int(r[6]):,} | {r[7]}% | {r[8] or ""} |')


def neighbourhood():
    nomes = {'own': "seen in the same session's tool output", 'self': 'seen earlier, same agent',
             'others': 'seen earlier, another agent', 'later': 'seen only after the note',
             'never': 'never in any tool output'}
    for l in open(os.path.join(R, 'neighbourhood.txt')):
        if l.startswith('window') or l.startswith('regime'):
            print(l.rstrip())
    print('| note | group (distinct claims) | n | exists | 1 char away | 2 chars away | farther | chance: 1 away | chance: 2 away |')
    print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
    linhas = [l.split() for l in open(os.path.join(R, 'neighbourhood.txt'))]
    linhas = [p for p in linhas if len(p) >= 11 and p[0] in ('summary', 'memory') and p[1] in nomes]
    ordem = list(nomes)
    linhas.sort(key=lambda p: (p[0] != 'summary', ordem.index(p[1])))
    for p in linhas:
        g = f'**{nomes[p[1]]}**' if p[1] == 'never' else nomes[p[1]]
        print(f'| {p[0]} | {g} | {int(p[2]):,} | {p[3]} | {p[4]} | {p[5]} | {p[6]} | {p[9]} | {p[10]} |')


if __name__ == '__main__':
    per_model()
    print()
    neighbourhood()
