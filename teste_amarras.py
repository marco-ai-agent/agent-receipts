"""Mutation test for conferir_readme.py: the bound check must catch what the
presence check cannot. Two README numbers are swapped for values that exist
elsewhere in results/ (so presence still passes); the bound check must name
both. Works on a copy next to this file and removes it."""
import os, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
MUT = os.path.join(AQUI, '_mutacao')
TROCAS = [('similar: 11.7% exist, 15.2% are one', 'similar: 11.7% exist, 16.5% are one'),
          ('  482 unanchored claims are 11 distinct', '  423 unanchored claims are 11 distinct')]

shutil.rmtree(MUT, ignore_errors=True)
shutil.copytree(os.path.join(AQUI, 'results'), os.path.join(MUT, 'results'))
md = open(os.path.join(AQUI, 'README.md')).read()
for a, b in TROCAS:
    assert a in md, f'mutation target gone from README: {a}'
    md = md.replace(a, b)
open(os.path.join(MUT, 'README.md'), 'w').write(md)
r = subprocess.run([sys.executable, os.path.join(AQUI, 'conferir_readme.py'),
                    os.path.join(MUT, 'README.md'), os.path.join(MUT, 'results')],
                   capture_output=True, text=True)
shutil.rmtree(MUT)
ok = (', 0 missing' in r.stdout and 'bound: ' in r.stdout and '2 mismatch' in r.stdout
      and '15.2%' in r.stdout and '482' in r.stdout and r.returncode == 1)
print('ok' if ok else 'FALHOU\n' + r.stdout)
sys.exit(0 if ok else 1)
