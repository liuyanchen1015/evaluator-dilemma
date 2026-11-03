"""Rebuild the two public pages from their sources and write them as complete HTML documents.

blog:     ~/evaluator_dilemma/blog_site  (python3 build.py  -> out/index.html)
registry: ~/rsi-audit                    (python3 site/build.py -> site/index.html)
Both builds emit an HTML fragment for claude.ai; this wraps each one for GitHub Pages.
"""
import re, subprocess
from pathlib import Path
HOME = Path.home(); HERE = Path(__file__).resolve().parent
PAGES = [(HOME / "evaluator_dilemma/blog_site", ["python3", "build.py"], "out/index.html", HERE / "index.html",
          "Does recursive self-improvement really improve? An essay on the evaluator dilemma, with audits of published self-improving AI systems."),
         (HOME / "rsi-audit", ["python3", "site/build.py"], "site/index.html", HERE / "registry/index.html",
          "Audit cards for self-improving AI systems: which evaluators measured each reported gain, and whether the gain holds up.")]

SITE = "https://liuyanchen1015.github.io/evaluator-dilemma/"
# tab icons (claude.ai sets its own): navy square in the blog accent, a loop arrow for the essay, a check mark for the registry
ICON_FRAME = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='7' fill='#2c5a8f'/>{}</svg>"
ICONS = {"essay": "<path d='M23.5 12.5A8.5 8.5 0 1 0 24.5 18' fill='none' stroke='white' stroke-width='3' stroke-linecap='round'/>"
                  "<path d='M24.5 6.5v6.5H18' fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>",
         "registry": "<path d='M9 16.5l4.5 4.5L23 11' fill='none' stroke='white' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'/>"}


def icon_link(kind: str) -> str:
    from urllib.parse import quote
    return f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{quote(ICON_FRAME.format(ICONS[kind]))}">\n'



def wrap(fragment: str, desc: str, depth: int, kind: str) -> str:
    fragment = re.sub(r'<meta name="claude:[^"]*"[^>]*>\n?', "", fragment)   # claude.ai-only hint
    # links between the two pages become relative, so the same files work on any host (GitHub Pages, CSAIL, ...)
    up = "../" * depth
    fragment = fragment.replace(SITE + "registry/", up + "registry/").replace(f'href="{SITE}"', f'href="{up or "./"}"').replace(f"href='{SITE}'", f"href='{up or './'}'")
    m = re.search(r"<title>.*?</title>\n?", fragment, flags=re.S)
    title = m.group(0) if m else ""
    body = fragment.replace(title, "", 1) if title else fragment
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{title}<meta name="description" content="{desc}">\n{icon_link(kind)}</head>\n<body>\n{body}\n</body>\n</html>\n')

for src, cmd, frag, out, desc in PAGES:
    subprocess.run(cmd, cwd=src, check=True, stdout=subprocess.DEVNULL)
    out.parent.mkdir(parents=True, exist_ok=True)
    kind = "registry" if out.parent.name == "registry" else "essay"
    out.write_text(wrap((src / frag).read_text(), desc, len(out.relative_to(HERE).parts) - 1, kind))
    print("wrote", out.relative_to(HERE), f"{out.stat().st_size // 1024} KB")
