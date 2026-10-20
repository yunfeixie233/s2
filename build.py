#!/usr/bin/env python3
"""Rebuild the static website. Requires pandoc and beautifulsoup4 only to build.

The generated website itself needs no runtime, build step, or external services.
Run this file after editing post.md. Styling and interactions live in site.css
and site.js.
"""
from pathlib import Path
import html
import struct
import subprocess

from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://yunfeixie233.github.io/s2/"
VIDEO_URL = "assets/s2-walkthrough.mp4"
CODE_URL = "https://github.com/yunfeixie233/sensorimotor-alignment"
PAPER_URL = ""  # Set to the verified public paper URL when available.


def asset_version(name):
    """Short content hash so browsers fetch a changed stylesheet or script instead of a cached copy."""
    import hashlib
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:10]
raw_html = subprocess.run(
    ["pandoc", str(ROOT / "post.md"), "--from=gfm", "--to=html5", "--mathml"],
    check=True, text=True, capture_output=True,
).stdout
soup = BeautifulSoup(raw_html, "html.parser")
for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
    comment.extract()
title = " ".join(soup.h1.get_text(" ", strip=True).split())
soup.h1.decompose()
first = soup.find("p")
is_subtitle = first is not None and first.find("img") is None and len(first.contents) == 1 and getattr(first.contents[0], "name", None) == "em"
subtitle = " ".join(first.get_text(" ", strip=True).split()) if is_subtitle else ""
if is_subtitle:
    first.decompose()
def plain(p):
    p = BeautifulSoup(str(p), "html.parser")
    for ref in p.select("a.footnote-ref, sup"):
        ref.decompose()
    return " ".join(p.get_text(" ", strip=True).split()).replace(" ,", ",").replace(" .", ".")
description = subtitle or next((plain(p) for p in soup.find_all("p") if p.find("img") is None and p.find("em") is None and len(p.get_text(strip=True)) > 80), title)
description = description if len(description) <= 200 else description[:197].rsplit(" ", 1)[0] + "…"

# Footnotes become margin sidenotes. Below the wide breakpoint, the number
# toggles the note inline through the checkbox, so no script is needed.
notes = {}
footnotes = soup.find("section", class_="footnotes")
if footnotes:
    for item in footnotes.find_all("li"):
        for back in item.select("a.footnote-back"):
            back.decompose()
        body = item.find("p") or item
        notes[item["id"]] = body.decode_contents().strip()
    footnotes.decompose()
for number, ref in enumerate(list(soup.select("a.footnote-ref")), 1):
    note_id = f"sn-{number}"
    previous = ref.previous_sibling
    while previous is not None and getattr(previous, "name", None) is None and not str(previous).strip():
        previous = previous.previous_sibling
    adjacent = getattr(previous, "name", None) == "span" and "sidenote" in previous.get("class", [])
    marker_class = "sidenote-number adjacent-citation" if adjacent else "sidenote-number"
    markup = (
        f'<label for="{note_id}" class="{marker_class}" aria-label="Note {number}"></label>'
        f'<input type="checkbox" id="{note_id}" class="margin-toggle">'
        f'<span class="sidenote">{notes[ref["href"].lstrip("#")]}</span>'
    )
    ref.replace_with(BeautifulSoup(markup, "html.parser"))

# Keep the complete article in the HTML so reading works offline and without JS.
for number, img in enumerate(list(soup.select("p > img")), 1):
    paragraph = img.parent
    caption = paragraph.find_next_sibling("p")
    figure = soup.new_tag("figure", attrs={"data-figure": str(number)})
    button = soup.new_tag("button", attrs={
        "class": "figure-button", "type": "button",
        "aria-label": f"Expand figure {number}",
    })
    img["loading"] = "lazy"
    img["decoding"] = "async"
    image_path = ROOT / img["src"]
    if image_path.suffix.lower() == ".png":
        image_width, image_height = struct.unpack(">II", image_path.read_bytes()[16:24])
        img["width"] = str(image_width)
        img["height"] = str(image_height)
    img["src"] = f'{img["src"]}?v={asset_version(img["src"])}'
    button.append(img.extract())
    figure.append(button)
    figcaption = soup.new_tag("figcaption")
    label = soup.new_tag("span", attrs={"class": "figure-number"})
    label.string = f"Figure {number}:"
    figcaption.append(label)
    figcaption.append(" ")
    caption_text = soup.new_tag("span", attrs={"class": "caption-text"})
    if caption and caption.find("em"):
        # Keep the caption's markup so citations in it stay sidenotes.
        for child in list(caption.find("em").contents):
            caption_text.append(child.extract())
        caption.decompose()
    figcaption.append(caption_text)
    figure.append(figcaption)
    paragraph.replace_with(figure)

figure_count = len(soup.find_all("figure"))
opening_figure = soup.find("figure")
og_image = ""
if opening_figure:
    opening_figure = opening_figure.extract()
    opening_figure["id"] = "figure-1"
    opening_figure.img["loading"] = "eager"
    opening_figure.img["fetchpriority"] = "high"
    og_image = f'\n  <meta property="og:image" content="{SITE_URL}{opening_figure.img["src"]}">'

for table in list(soup.find_all("table")):
    caption = table.find_next_sibling("p")
    if caption and caption.find("em"):
        caption["class"] = "table-caption"
    wrap = soup.new_tag("div", attrs={
        "class": "table-wrap", "role": "region", "tabindex": "0",
        "aria-label": "Alignment across the denoising schedule",
    })
    table.wrap(wrap)

article = soup.new_tag("article", attrs={"class": "content", "id": "article"})
section = soup.new_tag("section", attrs={"id": "introduction", "aria-label": "Introduction"})
article.append(section)
toc_entries = [("introduction", "Introduction", [])]
for node in list(soup.contents):
    name = getattr(node, "name", None)
    if name == "h2":
        section_id = node.get("id")
        heading_id = section_id + "-heading"
        node["id"] = heading_id
        section = soup.new_tag("section", attrs={"id": section_id, "aria-labelledby": heading_id})
        article.append(section)
        toc_entries.append((section_id, node.get_text(" ", strip=True), []))
    elif name == "h3" and node.get("id"):
        toc_entries[-1][2].append((node["id"], node.get_text(" ", strip=True)))
    section.append(node.extract())

def toc_item(anchor, label, children):
    item = f'<li><a href="#{anchor}">{html.escape(label)}</a>'
    if children:
        item += "<ul>" + "".join(f'<li><a href="#{a}">{html.escape(l)}</a></li>' for a, l in children) + "</ul>"
    return item + "</li>"

toc = "<ul>" + "".join(toc_item(*entry) for entry in toc_entries) + "</ul>"
authors = ['Yunfei Xie', 'Howard H. Qian', 'Shiyi Lan', 'Kaiyu Hang', 'Chen Wei']
authors_html = ", ".join(authors[:-1]) + ", and " + authors[-1]

page_title = title if title.startswith("Sensorimotor Alignment") else f"{title} — Sensorimotor Alignment"
subtitle_html = f'      <p class="post-subtitle">{html.escape(subtitle)}</p>\n' if subtitle else ""
paper_icon = '<img class="link-icon" src="assets/arxiv-logomark.svg" width="12" height="16" alt="">'
paper_link = (
    f'<a class="link-button" href="{html.escape(PAPER_URL, quote=True)}" target="_blank" rel="noopener">{paper_icon}<span>Paper</span></a>'
    if PAPER_URL else
    f'<span class="link-button link-button-unavailable" role="link" aria-disabled="true" aria-label="Paper link not yet available" title="Paper link not yet available">{paper_icon}<span>Paper</span></span>'
)
page = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="theme-color" content="#ffffff">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}">{og_image}
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{SITE_URL}">
  <title>{html.escape(page_title)}</title>
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
  <link rel="stylesheet" href="site.css?v={asset_version("site.css")}">
  <script src="site.js?v={asset_version("site.js")}" defer></script>
</head>
<body id="top">
  <a class="skip-link" href="#article">Skip to article</a>
  <header class="site-header">
    <div class="site-header-inner">
      <a class="brand" href="#top" aria-label="Sensorimotor Alignment, back to top">S<sup>2</sup><span class="brand-name">Sensorimotor Alignment</span></a>
    </div>
  </header>
  <main class="post">
    <div class="post-heading">
      <h1 class="post-title">{html.escape(title)}</h1>
{subtitle_html}      <div class="publish-metadata">
        <span class="author">{authors_html}</span>
        <span>Rice University · NVIDIA</span>
      </div>
      <div class="publication-links">
        <a class="link-button" href="{VIDEO_URL}?v={asset_version(VIDEO_URL)}" target="_blank" rel="noopener"><svg class="link-icon" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7.25" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.4 5.1v5.8L11 8z" fill="currentColor"/></svg><span>Video</span></a>
        <a class="link-button" href="{CODE_URL}" target="_blank" rel="noopener"><svg class="link-icon" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg><span>Code</span></a>
        {paper_link}
      </div>
    </div>
    {f'<div class="post-cover">{opening_figure}</div>' if opening_figure else ''}
    <div class="post-content-shell">
      <nav class="left-toc" aria-label="Article contents">{toc}</nav>
      {article}
    </div>
    <div class="paginator"><a href="#top">back to top</a></div>
  </main>
  <footer class="site-footer">
    <p>Sensorimotor Alignment · Rice University · NVIDIA</p>
  </footer>
  <dialog class="figure-dialog" aria-label="Expanded research figure" aria-describedby="expanded-caption">
    <div class="dialog-toolbar"><span class="dialog-title">Research figure</span><div class="dialog-actions"><button class="zoom-button" type="button" aria-pressed="false">Actual size</button><button class="close-dialog" type="button" aria-label="Close expanded figure">Close ×</button></div></div>
    <div class="dialog-image-wrap"><img class="dialog-image" alt=""></div>
    <p class="dialog-caption" id="expanded-caption"></p>
  </dialog>
</body>
</html>
'''
(ROOT / "index.html").write_text(page)
(ROOT / "assets/favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#282828"/><text x="17" y="48" fill="#ffffff" font-family="Georgia,serif" font-size="44">S</text><text x="40" y="25" fill="#ffffff" font-family="Georgia,serif" font-size="21">2</text></svg>')
print(f"Built {ROOT / 'index.html'} with {len(toc_entries)} sections, {figure_count} figures and {len(notes)} sidenotes.")
