"""Rebuild the two public pages from their sources and write them as complete HTML documents.

blog:     ~/evaluator_dilemma/blog_site  (python3 build.py  -> out/index.html)
registry: ~/verifiedrsi-registry (repo VerifiedRSI/registry; python3 site/build.py -> site/index.html)
Both builds emit an HTML fragment for claude.ai; this wraps each one for GitHub Pages, then runs feed.py.
"""
import re, subprocess
from pathlib import Path
HOME = Path.home(); HERE = Path(__file__).resolve().parent
PAGES = [(HOME / "evaluator_dilemma/blog_site", ["python3", "build.py"], "out/index.html", HERE / "index.html",
          "Does recursive self-improvement really improve? A blog post on the evaluator dilemma, with audits of published self-improving AI systems."),
         (HOME / "verifiedrsi-registry", ["python3", "site/build.py"], "site/index.html", HERE / "registry/index.html",
          "Audit cards for self-improving AI systems: which evaluators measured each reported gain, and whether the gain holds up.")]

SITE = "https://liuyanchen1015.github.io/evaluator-dilemma/"
# link previews: wide cards for X/Slack/LinkedIn/iMessage (absolute URLs on GitHub Pages, so every host's copy points
# to the same image), and a square thumbnail for WeChat, which uses the first image in the page body.
def share_tags(kind: str, title: str, desc: str, up: str) -> str:
    img = SITE + f"share/{kind}.png?v=2"  # bump v when the image changes, so link-preview caches refetch
    return (f'<meta property="og:type" content="{"article" if kind == "blog" else "website"}">\n'
            f'<meta property="og:title" content="{title}">\n<meta property="og:description" content="{desc}">\n'
            f'<meta property="og:image" content="{img}">\n<meta property="og:image:width" content="1200">\n'
            f'<meta property="og:image:height" content="630">\n<meta name="twitter:card" content="summary_large_image">\n'
            f'<meta name="twitter:title" content="{title}">\n<meta name="twitter:description" content="{desc}">\n'
            f'<meta name="twitter:image" content="{img}">\n'), (
            f'<div style="display:none"><img src="{up}share/{kind}-square.png" alt="{title}" width="600" height="600"></div>\n')

# tab icon: each host serves its own favicon.ico next to index.html (GitHub: the squirrel from the homepage;
# CSAIL: the CSAIL logo), so the HTML files stay identical on every host.


def wrap(fragment: str, desc: str, depth: int, kind: str) -> str:
    fragment = re.sub(r'<meta name="claude:[^"]*"[^>]*>\n?', "", fragment)   # claude.ai-only hint
    # links between the two pages become relative, so the same files work on any host (GitHub Pages, CSAIL, ...)
    up = "../" * depth
    fragment = fragment.replace(SITE + "registry/", up + "registry/").replace(f'href="{SITE}"', f'href="{up or "./"}"').replace(f"href='{SITE}'", f"href='{up or './'}'")
    m = re.search(r"<title>.*?</title>\n?", fragment, flags=re.S)
    title = m.group(0) if m else ""
    body = fragment.replace(title, "", 1) if title else fragment
    plain = re.sub(r"</?title>|\n", "", title)
    head_tags, wechat_img = share_tags(kind, plain, desc, up)
    if kind == "blog":  # full-text Atom feed (feed.py); absolute, so every host's copy points to the one feed
        head_tags += f'<link rel="alternate" type="application/atom+xml" title="The Evaluator Dilemma" href="{SITE}feed.xml">\n'
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{title}<meta name="description" content="{desc}">\n<link rel="icon" href="{up}favicon.ico">\n{head_tags}</head>\n<body>\n{wechat_img}{body}\n</body>\n</html>\n')

for src, cmd, frag, out, desc in PAGES:
    subprocess.run(cmd, cwd=src, check=True, stdout=subprocess.DEVNULL)
    out.parent.mkdir(parents=True, exist_ok=True)
    kind = "registry" if out.parent.name == "registry" else "blog"
    out.write_text(wrap((src / frag).read_text(), desc, len(out.relative_to(HERE).parts) - 1, kind))
    print("wrote", out.relative_to(HERE), f"{out.stat().st_size // 1024} KB")
subprocess.run(["python3", "feed.py"], cwd=HERE, check=True)
