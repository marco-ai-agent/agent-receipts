"""Mutation test for conferir_readme.py: the bound check must catch what the
presence check cannot. Two README numbers are swapped for values that exist
elsewhere in results/ (so presence still passes); the bound check must name
both. A second run changes the hand-audit row behind "Three were opened by
hand" and puts a number in WRITEUP.md that exists in results/ but is not
bound; both must fail. Works on a copy next to this file and removes it."""
import os, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
MUT = os.path.join(AQUI, '_mutacao')
TROCAS = [('similar: 11.7% exist, 15.2% are one', 'similar: 11.7% exist, 16.5% are one'),
          ('  482 unanchored claims are 11 distinct', '  423 unanchored claims are 11 distinct')]


def rodar(readme, results, writeup=None):
    shutil.rmtree(MUT, ignore_errors=True)
    shutil.copytree(os.path.join(AQUI, 'results'), os.path.join(MUT, 'results'))
    for nome, texto in (('README.md', readme), ('WRITEUP.md', writeup)):
        if texto is not None:
            open(os.path.join(MUT, nome), 'w').write(texto)
    for arq, (a, b) in results:
        p = os.path.join(MUT, 'results', arq)
        t = open(p).read()
        assert a in t, f'mutation target gone from {arq}: {a}'
        open(p, 'w').write(t.replace(a, b))
    r = subprocess.run([sys.executable, os.path.join(AQUI, 'conferir_readme.py'),
                        os.path.join(MUT, 'README.md'), os.path.join(MUT, 'results')],
                       capture_output=True, text=True)
    shutil.rmtree(MUT)
    return r


md = open(os.path.join(AQUI, 'README.md')).read()
mutado = md
for a, b in TROCAS:
    assert a in mutado, f'mutation target gone from README: {a}'
    mutado = mutado.replace(a, b)
r = rodar(mutado, [])
ok1 = (', 0 missing' in r.stdout and 'bound: ' in r.stdout and '2 mismatch' in r.stdout
       and '15.2%' in r.stdout and '482' in r.stdout and r.returncode == 1)

wu = open(os.path.join(AQUI, 'WRITEUP.md')).read()
a = '5.9% exist, against 86.3%'
assert a in wu, f'mutation target gone from WRITEUP: {a}'
r2 = rodar(md, [('hand-audit.txt', ('screenshot cases: 3 opened', 'screenshot cases: 2 opened'))],
           wu.replace(a, '6.2% exist, against 86.3%'))
ok2 = ('1 mismatch' in r2.stdout and '"three" claims = 3' in r2.stdout
       and '1 numbers not bound: 6.2%' in r2.stdout and r2.returncode == 1)

print('ok' if ok1 and ok2 else 'FALHOU\n' + r.stdout + '\n' + r2.stdout)
sys.exit(0 if ok1 and ok2 else 1)
