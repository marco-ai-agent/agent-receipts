"""Download the commit list of a GitHub organisation, every branch of every repo.

Read-only. Needs a token in GITHUB_TOKEN for the authenticated rate limit
(5,000 requests per hour). Output: VILLAGE_DATA/derivado/gh/commits.jsonl,
one line per (repo, commit): sha, repo, first branch seen, author and
committer dates, first line of the message. Resumes: a repo listed in
repos-feitos.txt is not fetched again.

A branch stops paging as soon as a whole page is already known (it has
joined a trunk another branch fetched). One repo in the org has 329 branches.

usage: GITHUB_TOKEN=... python3 gh_commits.py [org] [part] [parts]
  part/parts split the repo list (index mod parts) to run several in parallel.
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DER

ORG = sys.argv[1] if len(sys.argv) > 1 else 'ai-village-agents'
PARTE = int(sys.argv[2]) if len(sys.argv) > 2 else 0
PARTES = int(sys.argv[3]) if len(sys.argv) > 3 else 1
DIR = os.path.join(DER, 'gh')
TOKEN = os.environ.get('GITHUB_TOKEN', '')

def get(url):
    for _ in range(5):
        req = urllib.request.Request(url, headers={
            'Accept': 'application/vnd.github+json', 'User-Agent': 'agent-receipts (read-only research)',
            **({'Authorization': 'Bearer ' + TOKEN} if TOKEN else {})})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r), r.headers.get('Link', '')
        except urllib.error.HTTPError as e:
            if e.code in (404, 409):
                return [], ''           # empty or gone
            if e.code in (403, 429):
                reset = int(e.headers.get('X-RateLimit-Reset', time.time() + 60))
                time.sleep(max(10, reset - time.time() + 2))
                continue
            time.sleep(3)
        except OSError:
            time.sleep(3)
    raise RuntimeError('failed: ' + url)

def paginado(url, parar=None):
    tudo = []
    while url:
        corpo, link = get(url)
        tudo += corpo
        if parar and parar(corpo):
            break
        nxt = [p for p in link.split(',') if 'rel="next"' in p]
        url = nxt[0][nxt[0].index('<') + 1:nxt[0].index('>')] if nxt else None
    return tudo

def main():
    os.makedirs(DIR, exist_ok=True)
    arq_repos = os.path.join(DIR, 'repos.json')
    if not os.path.exists(arq_repos):
        repos = paginado(f'https://api.github.com/orgs/{ORG}/repos?per_page=100&type=all')
        json.dump([{'name': r['name'], 'default_branch': r['default_branch'], 'size': r['size']} for r in repos],
                  open(arq_repos, 'w'))
    repos = json.load(open(arq_repos))
    marca = os.path.join(DIR, 'repos-feitos.txt')
    feitos = set(open(marca).read().split()) if os.path.exists(marca) else set()
    for i, repo in enumerate(repos):
        if i % PARTES != PARTE or repo['name'] in feitos:
            continue
        nome = repo['name']
        branches = paginado(f'https://api.github.com/repos/{ORG}/{nome}/branches?per_page=100')
        vistos, linhas = set(), []
        for b in branches:
            url = f'https://api.github.com/repos/{ORG}/{nome}/commits?sha={urllib.parse.quote(b["name"])}&per_page=100'
            for c in paginado(url, lambda pag: pag and all(x['sha'] in vistos for x in pag)):
                if c['sha'] in vistos:
                    continue
                vistos.add(c['sha'])
                cm = c.get('commit') or {}
                linhas.append(json.dumps({'repo': nome, 'sha': c['sha'], 'branch': b['name'],
                                          'data': (cm.get('author') or {}).get('date'),
                                          'cdata': (cm.get('committer') or {}).get('date'),
                                          'msg': (cm.get('message') or '').split('\n')[0][:120]}))
        with open(os.path.join(DIR, 'commits.jsonl'), 'a') as f:
            f.write(''.join(l + '\n' for l in linhas))
        with open(marca, 'a') as f:
            f.write(nome + '\n')
        print(f'{nome}: {len(branches)} branches, {len(linhas)} commits', flush=True)

if __name__ == '__main__':
    main()
