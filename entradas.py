"""The input counts the README quotes (summaries, turns, memories, repositories,
commits), written to results/ so they are not typed by hand.

Reads the dataset's manifest.json and the derived files of pares.py and
gh_commits.py; no network.

usage: python3 entradas.py > results/inputs.txt
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DADOS, DER


def main():
    rows = json.load(open(os.path.join(DADOS, 'manifest.json')))['rowCounts']
    print(f"computer-use turns (dataset manifest): {rows['computer_use_turns']}")
    print(f"agent memories (dataset manifest): {rows['agent_memories']}")

    n, ini, fim = 0, None, None
    with open(os.path.join(DER, 'pares.jsonl')) as f:
        for linha in f:
            stop = json.loads(linha)['stop'][:10]
            n += 1
            ini = stop if ini is None or stop < ini else ini
            fim = stop if fim is None or stop > fim else fim
    print(f'session summaries paired (pares.py): {n}, from {ini} to {fim}')

    repos = json.load(open(os.path.join(DER, 'gh', 'repos.json')))
    shas = set()
    linhas = 0
    with open(os.path.join(DER, 'gh', 'commits.jsonl')) as f:
        for linha in f:
            shas.add(json.loads(linha)['sha'])
            linhas += 1
    print(f'repositories in the organisation (gh_commits.py): {len(repos)}')
    print(f'commits, all branches, distinct: {len(shas)} ({linhas} repo-commit lines)')


if __name__ == '__main__':
    main()
