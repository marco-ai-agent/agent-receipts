"""Check that every number in README.md comes from a file in results/.

Each number written in the README with digits (counts, percentages, dates) is
looked up in results/*.txt. Model names are removed first, so "Claude Opus
4.1" does not count as the number 4.1. A small set of numbers that are
parameters of the method or facts about git, not results, is exempt, each
with its reason below.

What it cannot do: numbers written as words ("three", "a fifth", "more than
a hundred") are not checked; they are listed at the end for a hand check.
A small integer (under 100) found somewhere in results/ is weak evidence,
since small integers appear everywhere; those are marked "weak".

usage: python3 conferir_readme.py [README.md] [results_dir]
exit 1 if any number is missing from results/.
"""
import glob, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
README = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 'README.md')
R = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, 'results')

# Not results: definitions, method parameters, facts about git or the dataset.
ISENTOS = {
    '7': 'abbreviation length / prefix length / 7-character random strings (method)',
    '12': 'the old abbreviation rule "7 to 12" (quoted to correct it)',
    '4': 'git abbreviates from 4 (fact about git)',
    '40': 'full hash length / git abbreviates up to 40 (fact about git)',
    '64': 'sha256 object names (fact about git)',
    '20': 'commit claims written at 20 to 39 characters (method); 20 random strings per claim',
    '39': 'the 39-character "Full" string (definition of the bin)',
    '14': 'window: 14 days before the note (method)',
    '30': 'models with 30+ claims shown (table cut-off)',
    '35': 'minutes between two summaries in hand case 3 (read by hand)',
    '5,000': 'GitHub API rate limit (fact about GitHub)',
    '2026-03-24': 'first consolidated memory in the dataset (read by hand)',
    '2026': 'year (title, citation)',
    '2025': 'year (summaries run from April 2025; results/inputs.txt has the exact dates)',
    '5%': 'the threshold "above 5%" used to group models in prose; the rates are in the table',
    '11%': 'the retracted number from the first extractor, quoted as history; no results file has it on purpose',
}

PALAVRAS = r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|' \
           r'hundred|thousand|half|third|quarter|fifth|tenth|dozen|twice|most|majority)\b'


def corpus():
    textos = [open(f).read() for f in sorted(glob.glob(os.path.join(R, '*.txt')))]
    if not textos:
        sys.exit(f'no results in {R}')
    t = '\n'.join(textos)
    return t, set(re.findall(r'\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?%?', t))


def nomes_de_modelo():
    nomes = set()
    for l in open(os.path.join(R, 'per-model.txt')):
        m = re.match(r'(\S.*?)\s{2,}\d', l)
        if m and m.group(1) not in ('agent', 'ALL'):
            nomes.add(m.group(1).strip())
    return sorted(nomes, key=len, reverse=True)


def main():
    texto, achados = corpus()
    md = open(README).read()
    for nome in nomes_de_modelo():
        # a name can wrap across lines ("Claude Opus\n  4.1")
        md = re.sub(r'\s+'.join(map(re.escape, nome.split())), lambda m: 'MODEL' + '\n' * m.group(0).count('\n'), md)
    md = re.sub(r'https?://\S+', 'URL', md)

    falta, fracos, ok, isentos = [], [], [], []
    for n, linha in enumerate(md.split('\n'), 1):
        for m in re.finditer(r'(?<![\w.\-])(\d{4}-\d{2}-\d{2}|\d[\d,]*(?:\.\d+)?(?:%|M\b)?)', linha):
            tok = m.group(1).rstrip(',')
            if tok in ISENTOS:
                isentos.append((n, tok))
                continue
            limpo = tok.replace(',', '')
            if limpo.endswith('M'):
                alvo = float(limpo[:-1])
                bate = any(abs(int(x) / 1e6 - alvo) < 0.05 for x in achados if x.isdigit() and len(x) >= 6)
            else:
                bate = limpo in achados
            if not bate:
                falta.append((n, tok, linha.strip()[:90]))
            elif re.fullmatch(r'\d+', limpo) and int(limpo) < 100:
                fracos.append((n, tok))
            else:
                ok.append((n, tok))

    print(f'{README}: {len(ok)} numbers found in results/, {len(fracos)} weak (small integers), '
          f'{len(isentos)} exempt, {len(falta)} missing')
    if fracos:
        print('weak (found, but small): ' + ', '.join(f'{t} (l.{n})' for n, t in fracos))
    usados = sorted({t for _, t in isentos})
    for t in usados:
        print(f'exempt {t}: {ISENTOS[t]}')
    for n, tok, ctx in falta:
        print(f'MISSING l.{n}: {tok}   | {ctx}')
    palavras = [(n, w.group(0)) for n, l in enumerate(md.split('\n'), 1) for w in re.finditer(PALAVRAS, l, re.I)]
    if palavras:
        print('number words, check by hand: ' + ', '.join(f'{w} (l.{n})' for n, w in palavras))
    sys.exit(1 if falta else 0)


if __name__ == '__main__':
    main()
