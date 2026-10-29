"""Publica uma página HTML estática no GitHub Pages, que abre sem conta no Claude.

Uso: python publicar.py <arquivo.html> <slug>
Sai em https://pietroaugustorabaioli-hash.github.io/paginas/<slug>/
Tudo nesta pasta é PÚBLICO (repo público). A página precisa trazer os dados dentro do HTML.
Nasceu em 29/10/2026 (ele: "criar páginas para que não tenha um troço instalado, conseguir abrir").
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).parent
DONO, REPO = "pietroaugustorabaioli-hash", "paginas"
BASE = f"https://{DONO}.github.io/{REPO}/"
META = '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow">\n'


def sh(*cmd, ok=False):
    r = subprocess.run(cmd, cwd=AQUI, capture_output=True, text=True, encoding="utf-8")
    if r.returncode and not ok:
        sys.exit(f"falhou: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()


def base_do_repo():
    (AQUI / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (AQUI / ".nojekyll").write_text("", encoding="utf-8")
    idx = AQUI / "index.html"
    if not idx.exists():
        idx.write_text('<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>Páginas</title><p>Nada aqui.</p>\n', encoding="utf-8")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    origem, slug = Path(sys.argv[1]), sys.argv[2].strip("/")
    destino = AQUI / slug / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origem, destino)
    t = destino.read_text(encoding="utf-8")
    if 'name="robots"' not in t:
        alvo = "<title>" if "<title>" in t else "<head>"
        t = t.replace(alvo, META + alvo, 1) if alvo in t else META + t
        destino.write_text(t, encoding="utf-8")
    base_do_repo()

    if not (AQUI / ".git").exists():
        sh("git", "init", "-q", "-b", "main")
    sh("git", "add", "-A")
    sh("git", "commit", "-q", "-m", f"publica {slug}", ok=True)
    if not sh("git", "remote", ok=True):
        existe = subprocess.run(["gh", "repo", "view", f"{DONO}/{REPO}"], capture_output=True).returncode == 0
        if not existe:
            sh("gh", "repo", "create", f"{DONO}/{REPO}", "--public", "--description", "Páginas estáticas do Jarvis (públicas)")
        sh("git", "remote", "add", "origin", f"https://github.com/{DONO}/{REPO}.git")
    sh("git", "push", "-q", "-u", "origin", "main")
    # liga o Pages na primeira vez (já ligado = 409, tudo bem)
    sh("gh", "api", "-X", "POST", f"repos/{DONO}/{REPO}/pages", "-f", "source[branch]=main", "-f", "source[path]=/", ok=True)

    url = f"{BASE}{slug}/"
    for _ in range(30):  # até ~3 min pro build do Pages
        st = sh("gh", "api", f"repos/{DONO}/{REPO}/pages/builds/latest", "--jq", ".status", ok=True)
        if st == "built":
            break
        time.sleep(6)
    cod = subprocess.run(["curl", "-s", "-o", "NUL" if sys.platform == "win32" else "/dev/null", "-w", "%{http_code}", url],
                         capture_output=True, text=True).stdout
    print(url, "| build:", st, "| http:", cod)


if __name__ == "__main__":
    main()
