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
    markup = (
        f'<label for="{note_id}" class="sidenote-number" aria-label="Note {number}"></label>'
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
  <link rel="stylesheet" href="site.css">
  <script src="site.js" defer></script>
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
