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

# Let the two distance definitions wrap as complete equations on small screens.
# Keep Pandoc's mathematical symbols and their TeX annotations intact.
for equation in soup.select('math[display="block"]'):
    annotation = equation.find("annotation")
    if not annotation or r"\qquad d_{\mathrm{motor}}" not in annotation.get_text():
        continue
    row = equation.find("mrow", recursive=True)
    separator = row.find("mspace", recursive=False)
    if separator is None:
        continue
    parts = [[], []]
    side = 0
    for child in list(row.contents):
        if child is separator:
            side = 1
        else:
            parts[side].append(child)
    paragraph = equation.parent
    paragraph["class"] = "distance-equations"
    for nodes, tex in zip(parts, annotation.get_text().split(r"\qquad", 1)):
        item = soup.new_tag("math", attrs={"display": "block", "xmlns": "http://www.w3.org/1998/Math/MathML"})
        semantics = soup.new_tag("semantics")
        item_row = soup.new_tag("mrow")
        for node in nodes:
            item_row.append(node.extract())
        semantics.append(item_row)
        source = soup.new_tag("annotation", attrs={"encoding": "application/x-tex"})
        source.string = tex.strip()
        semantics.append(source)
        item.append(semantics)
        equation.insert_before(item)
    equation.decompose()

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

# Preserve the original figures; narrow screens can inspect one column at a time.
PANEL_VIEWS = {
    "3": [("VLAs", 0, .283), ("VLMs", .284, .525),
          ("WAMs", .525, .760), ("Real robots", .760, 1)],
    "5": [("S²", 0, .264), ("SSIM", .269, .511),
          ("PSNR", .512, .757), ("FID", .758, 1)],
    "6": [("Vision", 0, .345), ("Text", .345, .673),
          ("Vision + text", .673, 1)],
}
for figure in soup.select("figure[data-figure]"):
    number = figure["data-figure"]
    figure["id"] = f"figure-{number}"
    if number in {"2", "4"}:
        figure["class"] = "medium-figure"
    # Existing panel labels start new caption lines; every word stays intact.
    caption = figure.select_one(".caption-text")
    part = None
    for child in list(caption.contents):
        if getattr(child, "name", None) == "strong" and child.get_text(strip=True) in {"Left:", "Right:", "Top:", "Bottom:"}:
            part = soup.new_tag("span", attrs={"class": "caption-part"})
            child.insert_before(part)
        if part is not None:
            part.append(child.extract())
    if number not in PANEL_VIEWS:
        continue
    figure["class"] = "wide-figure"
    original = figure.select_one(".figure-button")
    original["class"] = "figure-button figure-overview"
    original_image = original.img
    image_width, image_height = int(original_image["width"]), int(original_image["height"])
    max_span = max(end-start for _, start, end in PANEL_VIEWS[number])
    tail = max(0, 1 - (1 - PANEL_VIEWS[number][-1][1]) / max_span)
    gallery = soup.new_tag("div", attrs={"class": "figure-panels", "style": f"--panel-columns:{1/max_span:.6f};--panel-tail:{tail:.6f}"})
    controls = soup.new_tag("div", attrs={"class": "panel-controls", "role": "group", "aria-label": f"Figure {number} panels", "hidden": ""})
    gallery.append(controls)
    for index, (label, start, end) in enumerate(PANEL_VIEWS[number]):
        selector = soup.new_tag("button", attrs={"class": "panel-selector", "type": "button", "data-panel-start": str(start), "aria-controls": f"figure-{number}-scroll", "aria-pressed": "true" if index == 0 else "false"})
        selector.string = label
        controls.append(selector)
    if number == "6":
        key = soup.new_tag("p", attrs={"class": "panel-key"})
        key.string = "Top: fine-tuned VLAs · Bottom: raw VLMs"
        gallery.append(key)
    scroll = soup.new_tag("div", attrs={"class": "figure-scroll", "id": f"figure-{number}-scroll", "tabindex": "0", "role": "region", "aria-label": f"Figure {number}, scroll horizontally to inspect every panel"})
    image = soup.new_tag("img", attrs={"src": original_image["src"], "alt": original_image["alt"], "width": str(image_width), "height": str(image_height), "loading": "lazy", "decoding": "async"})
    scroll.append(image)
    gallery.append(scroll)
    hint = soup.new_tag("p", attrs={"class": "panel-hint"})
    hint.string = "Scroll horizontally to inspect each panel."
    gallery.append(hint)
    original.insert_after(gallery)
    full = soup.new_tag("button", attrs={"class": "full-figure-link", "type": "button", "aria-label": f"Expand complete figure {number}"})
    full.string = "View full figure ↗"
    gallery.append(full)

# Video preserves the GIF sequence while allowing pause/restart and reduced motion.
for index, image in enumerate(soup.select(".alignment-animation img"), 1):
    stem = Path(image["src"]).name.replace("-compact.gif", "")
    movie, poster = f"assets/{stem}.mp4", f"assets/{stem}-poster.png"
    video = soup.new_tag("video", attrs={
        "class": "alignment-video", "id": f"animation-{index}",
        "controls": "", "loop": "", "muted": "", "playsinline": "", "preload": "metadata",
        "poster": f"{poster}?v={asset_version(poster)}", "width": image["width"], "height": image["height"],
        "aria-label": image["alt"],
    })
    video.append(soup.new_tag("source", attrs={"src": f"{movie}?v={asset_version(movie)}", "type": "video/mp4"}))
    image.replace_with(video)
    controls = soup.new_tag("div", attrs={"class": "animation-controls", "hidden": ""})
    for cls, label in (("animation-toggle", "Play"), ("animation-restart", "Restart")):
        button = soup.new_tag("button", attrs={"class": cls, "type": "button", "aria-controls": video["id"]})
        button.string = label
        controls.append(button)
    video.insert_after(controls)

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

# Short labels are navigation only; article headings are unchanged.
NAV_LABELS = {
    "Introduction": "Introduction",
    "Measuring sensorimotor alignment": "Measuring S²",
    "S² Correlates with Robot Task Success Rate": "S² and task success",
    "S² Correlates with Task Success Across Model Families": "Model families",
    "S² Correlates with Task Success More Closely Than Alternative Metrics": "Alternative metrics",
    "S² Is Robust to Evaluation Choices": "Robustness",
    "Representation-Level Explanations with S²": "Representation analysis",
    "What Carries the Correlation: Vision, Text, or Both?": "Vision and language",
    "Freezing Vision Encoders Limits S² Gain": "Frozen encoders",
    "Features at Early Denoising Steps Already Carry Strong Sensorimotor Alignment": "Early denoising",
    "Mid-Depth Blocks Carry the Strongest Sensorimotor Alignment": "Model depth",
}

def toc_item(anchor, label, children):
    label = " ".join(label.split())
    link = f'<a href="#{anchor}">{html.escape(NAV_LABELS.get(label, label))}</a>'
    if not children:
        return f"<li>{link}</li>"
    items = "".join(toc_item(a, l, []) for a, l in children)
    return f'<li><details class="toc-group"><summary>{link}</summary><ul>{items}</ul></details></li>'

toc = "<ul>" + "".join(toc_item(*entry) for entry in toc_entries) + "</ul>"

# Add link controls after navigation labels are captured.
for heading in article.select("h2, h3"):
    anchor = heading.parent["id"] if heading.name == "h2" else heading["id"]
    permalink = soup.new_tag("a", attrs={"class": "heading-link", "href": f"#{anchor}", "aria-label": "Link to this section"})
    permalink.string = "#"
    heading.append(permalink)

for index, pre in enumerate(article.select("#citation pre"), 1):
    pre["id"] = f"citation-code-{index}"
    pre["class"] = "citation-code"
    wrap = soup.new_tag("div", attrs={"class": "citation-block"})
    pre.wrap(wrap)
    copy = soup.new_tag("button", attrs={"class": "copy-citation", "type": "button", "data-copy-target": pre["id"], "hidden": ""})
    copy.string = "Copy citation" if index == 1 else "Copy BibTeX"
    pre.insert_before(copy)

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
    <details class="mobile-toc"><summary>Contents<span class="current-section">Introduction</span></summary><nav class="article-toc" aria-label="Mobile article contents">{toc}</nav></details>
    <div class="post-content-shell">
      <nav class="left-toc article-toc" aria-label="Article contents">{toc}</nav>
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
