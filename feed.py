"""Write feed.xml, an Atom feed carrying the blog post's full text, for feed readers and archives (e.g. Rogue Scholar).

Feed readers run no scripts and apply no page CSS, so the post's figures (inline SVG styled by classes, charts drawn
by JavaScript, one interactive widget) are rendered to PNGs in figures/ and the feed's copy of the post uses those.
Run after deploy.py has written index.html (deploy.py calls this). Links in the feed are absolute GitHub Pages URLs.
"""
import hashlib, html, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = "https://liuyanchen1015.github.io/evaluator-dilemma/"
HOMEPAGE = "https://liuyanchen1015.github.io/"
TITLE = "The Evaluator Dilemma: Does Recursive Self-Improvement Really Improve?"
PUBLISHED = "2026-11-02T00:00:00-05:00"
SUMMARY = ("Self-improving AI systems judge their own progress with an evaluator inside their loop. We audited eight "
           "published systems; in none of them did the loop's own evaluator give good evidence for the reported gain.")

PW = "/orcd/scratch/orcd/007/ychenliu/evaldilemma"
sys.path.insert(0, f"{PW}/pwlib"); os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", f"{PW}/pw_browsers")
from playwright.sync_api import sync_playwright  # noqa: E402

# Runs in the page: render-ready article -> static copy for the feed. Figures become <img>, collapsed parts open up,
# controls and page-only blocks go away, links become absolute, presentation attributes are dropped.
TO_STATIC = r"""([site]) => {
  const a = document.querySelector('article.post').cloneNode(true);
  a.querySelectorAll('header.hero, details.toc-m, section.cite, button, input, script, style').forEach(e => e.remove());
  a.querySelectorAll('details').forEach(d => { d.querySelector('summary')?.remove(); d.replaceWith(...d.childNodes); });
  a.querySelectorAll('span.secnum').forEach(s => s.replaceWith(s.textContent + '. '));
  a.querySelectorAll('figure').forEach((f, i) => {
    const cap = f.querySelector('figcaption');
    const img = document.createElement('img');
    img.src = site + 'figures/fig-' + (i + 1) + '.png';
    img.alt = (cap ? cap.textContent : 'Figure ' + (i + 1)).trim();
    f.replaceChildren(img, ...(cap ? [cap] : []));
  });
  a.querySelectorAll('a[href]').forEach(l => {
    const h = l.getAttribute('href');
    if (!/^(https?:|mailto:)/.test(h)) l.setAttribute('href', new URL(h, site).href);
  });
  const keep = new Set(['href', 'src', 'alt', 'colspan', 'rowspan', 'title']);
  a.querySelectorAll('*').forEach(e => [...e.attributes].forEach(x => { if (!keep.has(x.name)) e.removeAttribute(x.name); }));
  return a.innerHTML;
}"""


def render() -> str:
    """Screenshot each figure (caption hidden) into figures/, return the post as static HTML."""
    out = HERE / "figures"; out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2, color_scheme="light")
        pg.goto((HERE / "index.html").as_uri(), wait_until="networkidle"); pg.wait_for_timeout(2000)
        pg.add_style_tag(content="figure figcaption, .bon-controls { display: none !important; }")
        figs = pg.query_selector_all("article.post figure")
        for i, f in enumerate(figs, 1):
            f.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
            png = f.screenshot()
            path = out / f"fig-{i}.png"
            if not path.exists() or path.read_bytes() != png:
                path.write_bytes(png)
        body = pg.evaluate(TO_STATIC, [SITE])
        b.close()
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def main() -> None:
    body = render()
    digest = hashlib.sha256(body.encode()).hexdigest()[:16]
    feed = HERE / "feed.xml"
    old = feed.read_text() if feed.exists() else ""
    # keep <updated> unless the post's text changed, so readers and archives only see real revisions
    m = re.search(r"<!-- content ([0-9a-f]+) -->\s*<updated>([^<]+)</updated>", old)
    updated = m.group(2) if m and m.group(1) == digest else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    author = f"<author>\n  <name>Yanchen Liu</name>\n  <uri>{HOMEPAGE}</uri>\n</author>"
    feed.write_text(f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">
<title>The Evaluator Dilemma</title>
<subtitle>{html.escape(SUMMARY)}</subtitle>
<link rel="self" type="application/atom+xml" href="{SITE}feed.xml"/>
<link rel="alternate" type="text/html" href="{SITE}"/>
<id>{SITE}feed.xml</id>
<updated>{updated}</updated>
{author}
<entry>
<title>{html.escape(TITLE)}</title>
<link rel="alternate" type="text/html" href="{SITE}"/>
<id>{SITE}</id>
<published>{PUBLISHED}</published>
<!-- content {digest} -->
<updated>{updated}</updated>
{author}
<summary type="text">{html.escape(SUMMARY)}</summary>
<content type="html">{html.escape(body, quote=False)}</content>
</entry>
</feed>
""")
    print("wrote feed.xml", f"{feed.stat().st_size // 1024} KB;", len(list((HERE / 'figures').glob('fig-*.png'))), "figures; updated", updated)


if __name__ == "__main__":
    main()
