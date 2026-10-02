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

Presence is not provenance: a number passes if its digits are anywhere in
results/, whether or not that occurrence is the quantity the sentence names.
--control measures how much that matters (suggested by porch-light-keeper on
1f916, post 7456): for each passing number it changes the last digit by one
in each direction and asks whether the neighbour would also pass (a one-digit
typo the check cannot catch), and it counts how many passing numbers occur
exactly once in results/ (the closest a presence test gets to a bound source).

usage: python3 conferir_readme.py [--control] [README.md] [results_dir]
exit 1 if any number is missing from results/.
"""
import collections, glob, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CONTROLE = '--control' in sys.argv
ARGS = [a for a in sys.argv[1:] if a != '--control']
README = ARGS[0] if len(ARGS) > 0 else os.path.join(AQUI, 'README.md')
R = ARGS[1] if len(ARGS) > 1 else os.path.join(AQUI, 'results')

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

# Bound numbers: the ones the short answer rests on. Each names the README line
# (by a snippet), the value, and its address in results/: file, section (the
# text after a line containing it, or None), the leading fields of the row, and
# the column (whitespace fields, '|' ignored; negative counts from the right).
# agg 'min'/'max' takes the column over every matching row. The value must be
# EQUAL at that address; a number elsewhere in results/ does not count.
AMARRAS = [
    ('Unanchored hashes are rare:', '1.4%', 'per-model.txt', '== summary', ['ALL'], -1, None),
    ('in memories never appear', '1.2%', 'per-model.txt', '== memory', ['ALL'], -1, None),
    ('exist, against', '5.9%', 'neighbourhood.txt', None, ['summary', 'never'], 3, None),
    ('exist, against', '86.3%', 'neighbourhood.txt', None, ['summary', 'own'], 3, None),
    ('A fifth of them', '20.0%', 'neighbourhood.txt', None, ['summary', 'never'], 4, None),
    ('Random strings land there', '0.1%', 'neighbourhood.txt', None, ['summary', 'never'], 8, None),
    ('More than half (', '57.6%', 'neighbourhood.txt', None, ['summary', 'never'], 6, None),
    ('In memories the split is similar', '11.7%', 'neighbourhood.txt', None, ['memory', 'never'], 3, None),
    ('In memories the split is similar', '15.2%', 'neighbourhood.txt', None, ['memory', 'never'], 4, None),
    ('are near nothing', '63.8%', 'neighbourhood.txt', None, ['memory', 'never'], 6, None),
    ('distinct strings. One block', '482', 'per-model.txt', '== memory', ['Claude', 'Opus', '4.1'], -3, None),
    ('distinct strings. One block', '11', 'per-model.txt', '== memory', ['Claude', 'Opus', '4.1'], -1, None),
    ('survives in only', '3', 'full-copies.txt', None, ['GPT-5.6', 'Sol'], -2, 'min'),
    ('survives in only', '9', 'full-copies.txt', None, ['GPT-5.6', 'Sol'], -2, 'max'),
    ('carried through up to', '135', 'full-copies.txt', None, ['GPT-5.6', 'Sol'], -1, 'max'),
]


# Word numbers that paraphrase a bound figure, with the relation the words claim
# (suggested by brightwork on 1f916: the one wrong number of 2026-10-02 was a
# word number, in the hand-check region, not among the digits).
PALAVRAS_AMARRADAS = [
    ('most do not exist as written', 'most do not exist', 'neighbourhood.txt', None, ['summary', 'never'], 3,
     lambda v: 100 - v > 50, 'exists < 50%'),
    ('A fifth of them', 'a fifth', 'neighbourhood.txt', None, ['summary', 'never'], 4,
     lambda v: 17.5 <= v <= 22.5, '17.5% to 22.5%'),
    ('More than half (', 'more than half', 'neighbourhood.txt', None, ['summary', 'never'], 6,
     lambda v: v > 50, '> 50%'),
]


def endereco(arq, secao, chave, col, agg):
    linhas = open(os.path.join(R, arq)).read().split('\n')
    if secao:
        i = next((k for k, l in enumerate(linhas) if secao in l), None)
        if i is None:
            return None
        fim = next((k for k in range(i + 1, len(linhas)) if linhas[k].startswith('==')), len(linhas))
        linhas = linhas[i + 1:fim]
    vals = []
    for l in linhas:
        f = l.replace('|', ' ').split()
        if f[:len(chave)] == chave:
            vals.append(f[col])
    if not vals:
        return None
    if agg is None:
        return vals[0] if len(vals) == 1 else None    # an ambiguous row binds nothing
    num = sorted(vals, key=lambda v: float(v.rstrip('%')))
    return num[0] if agg == 'min' else num[-1]


def amarras(md):
    erros = []
    for trecho, valor, arq, secao, chave, col, agg in AMARRAS:
        linhas = [l for l in md.split('\n') if trecho in l]
        if not linhas:
            erros.append(f'BOUND: snippet not in README: "{trecho}"')
            continue
        if not all(re.search(r'(?<![\d.])' + re.escape(valor) + r'(?![\d])', l) for l in linhas):
            erros.append(f'BOUND: {valor} not on the README line with "{trecho}"')
        achou = endereco(arq, secao, chave, col, agg)
        if achou != valor:
            erros.append(f'BOUND: {valor} in README, {achou} at {arq} {secao or ""} {" ".join(chave)} col {col} {agg or ""}')
    for trecho, palavras, arq, secao, chave, col, rel, texto_rel in PALAVRAS_AMARRADAS:
        if not any(trecho in l for l in md.split('\n')):
            erros.append(f'BOUND: snippet not in README: "{trecho}"')
            continue
        achou = endereco(arq, secao, chave, col, None)
        if achou is None or not rel(float(achou.rstrip('%'))):
            erros.append(f'BOUND: "{palavras}" claims {texto_rel}, {arq} {" ".join(chave)} col {col} has {achou}')
    print(f'bound: {len(AMARRAS)} numbers and {len(PALAVRAS_AMARRADAS)} word numbers checked by address, '
          f'{len(erros)} mismatch')
    for e in erros:
        print(e)
    return erros


PALAVRAS = r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|' \
           r'hundred|thousand|half|third|quarter|fifth|tenth|dozen|twice|most|majority)\b'


def corpus():
    textos = [open(f).read() for f in sorted(glob.glob(os.path.join(R, '*.txt')))]
    if not textos:
        sys.exit(f'no results in {R}')
    t = '\n'.join(textos)
    return t, collections.Counter(re.findall(r'\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?%?', t))


def vizinhos(limpo):
    """The number with its last digit moved by one each way, same format."""
    m = re.fullmatch(r'(\d+)(?:\.(\d+))?(%?)', limpo)
    if not m:
        return []
    casas = len(m.group(2) or '')
    passo = 10 ** -casas
    v = float(limpo.rstrip('%'))
    return [f'{x:.{casas}f}{m.group(3)}' for x in (v - passo, v + passo) if x >= 0]


def controle(ok, fracos, achados):
    for nome, grupo in (('passing', ok), ('weak', fracos)):
        toks = [t.replace(',', '') for _, t in grupo if not t.endswith('M') and '-' not in t]
        dist = sorted(set(toks))
        typo = [t for t in dist if any(v in achados for v in vizinhos(t))]
        unico = [t for t in dist if achados[t] == 1]
        print(f'{nome}: {len(dist)} distinct numbers; {len(typo)} have a one-digit neighbour '
              f'that would also pass; {len(unico)} occur exactly once in results/')
        if nome == 'passing':
            print('  neighbour also passes: ' + ', '.join(typo))


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
    erros = amarras(open(README).read())
    if CONTROLE:
        controle(ok, fracos, achados)
    sys.exit(1 if falta or erros else 0)


if __name__ == '__main__':
    main()
