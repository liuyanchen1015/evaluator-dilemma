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

def wrap(fragment: str, desc: str) -> str:
    fragment = re.sub(r'<meta name="claude:[^"]*"[^>]*>\n?', "", fragment)   # claude.ai-only hint
    m = re.search(r"<title>.*?</title>\n?", fragment, flags=re.S)
    title = m.group(0) if m else ""
    body = fragment.replace(title, "", 1) if title else fragment
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{title}<meta name="description" content="{desc}">\n</head>\n<body>\n{body}\n</body>\n</html>\n')

for src, cmd, frag, out, desc in PAGES:
    subprocess.run(cmd, cwd=src, check=True, stdout=subprocess.DEVNULL)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(wrap((src / frag).read_text(), desc))
    print("wrote", out.relative_to(HERE), f"{out.stat().st_size // 1024} KB")
