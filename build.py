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

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://yunfeixie233.github.io/s2/"
raw_html = subprocess.run(
    ["pandoc", str(ROOT / "post.md"), "--from=gfm", "--to=html5"],
    check=True, text=True, capture_output=True,
).stdout
soup = BeautifulSoup(raw_html, "html.parser")
title = " ".join(soup.h1.get_text(" ", strip=True).split())
soup.h1.decompose()
subtitle = " ".join(soup.find("p").get_text(" ", strip=True).split())
soup.find("p").decompose()

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
    label.string = f"Figure {number}"
    figcaption.append(label)
    caption_text = soup.new_tag("span", attrs={"class": "caption-text"})
    if caption and caption.find("em"):
        caption_text.string = caption.get_text(" ", strip=True)
        caption.decompose()
    figcaption.append(caption_text)
    hint = soup.new_tag("span", attrs={"class": "figure-hint"})
    hint.string = "Select the figure to take a closer look."
    figcaption.append(hint)
    figure.append(figcaption)
    paragraph.replace_with(figure)

figure_count = len(soup.find_all("figure"))
opening_figure = soup.find("figure").extract()
opening_figure["id"] = "figure-1"
opening_figure.img["loading"] = "eager"
opening_figure.img["fetchpriority"] = "high"

for table in list(soup.find_all("table")):
    caption = table.find_next_sibling("p")
    if caption and caption.find("em"):
        caption["class"] = "table-caption"
    wrap = soup.new_tag("div", attrs={
        "class": "table-wrap", "role": "region", "tabindex": "0",
        "aria-label": "Alignment across the denoising schedule",
    })
    table.wrap(wrap)

paper_note = soup.find_all("p")[-1]
paper_note["class"] = "paper-note"

toc_names = {
    "introduction": "The Platonic hypothesis",
    "what-would-this-look-like-in-robotics": "From perception to motion",
    "turning-the-idea-into-a-score": "Measuring alignment",
    "do-more-capable-policies-align-more-closely": "Evidence across policies",
    "a-signal-before-robot-fine-tuning": "Before robot fine-tuning",
    "the-reference-data-matters": "Choosing reference data",
    "what-changes-when-we-train-a-vla": "What training changes",
    "useful-features-can-appear-early": "Inside video models",
    "what-does-this-tell-us-about-the-hypothesis": "Returning to the hypothesis",
}
article = soup.new_tag("article", attrs={"class": "prose", "id": "article"})
section = soup.new_tag("section", attrs={"id": "introduction", "aria-label": "Introduction"})
article.append(section)
sections = [("introduction", toc_names["introduction"])]
index = 0
for node in list(soup.contents):
    if getattr(node, "name", None) == "h2":
        index += 1
        section_id = node.get("id")
        del node["id"]
        node["data-number"] = f"{index:02d}"
        heading_id = section_id + "-heading"
        node["id"] = heading_id
        section = soup.new_tag("section", attrs={"id": section_id, "aria-labelledby": heading_id})
        article.append(section)
        sections.append((section_id, toc_names.get(section_id, node.get_text(" ", strip=True))))
    section.append(node.extract())

def neighbor_svg(kind):
    points = {
        "sensory": {"Q": (135, 108), "A": (65, 68), "B": (206, 64), "C": (107, 165), "D": (229, 173), "E": (37, 153)},
        "motor": {"Q": (132, 108), "A": (74, 62), "B": (240, 57), "C": (201, 145), "D": (75, 170), "E": (32, 116)},
    }[kind]
    neighbors = {"sensory": ["A", "B", "C"], "motor": ["A", "C", "D"]}[kind]
    qx, qy = points["Q"]
    parts = [f'<svg viewBox="0 0 275 212" role="img" aria-label="Query neighbors in {kind} space: {", ".join(neighbors)}">']
    for name in neighbors:
        x, y = points[name]
        shared = " shared" if name in ("A", "C") else ""
        parts.append(f'<line class="neighbor-link{shared}" x1="{qx}" y1="{qy}" x2="{x}" y2="{y}"/>')
    for name, (x, y) in points.items():
        if name == "Q":
            parts.append(f'<circle class="query-node" cx="{x}" cy="{y}" r="23"/><text class="neighbor-text query-text" x="{x}" y="{y}">query</text>')
        else:
            shared = " shared" if name in ("A", "C") else ""
            near = " near" if name in neighbors else ""
            parts.append(f'<circle class="neighbor-node{shared}{near}" cx="{x}" cy="{y}" r="15"/><text class="neighbor-text{shared}" x="{x}" y="{y}">{name}</text>')
    parts.append("</svg>")
    return "".join(parts)

explainer = f'''<div class="explainer" aria-label="Interactive illustration of shared neighbors">
  <div class="explainer-heading"><span class="explainer-kicker">The same episodes, two views</span><span class="toy-label">Illustration</span></div>
  <div class="neighbor-panels">
    <div class="neighbor-panel"><h3>What the model groups together</h3><p class="panel-subtitle">Neighbors in feature space</p>{neighbor_svg("sensory")}</div>
    <div class="neighbor-panel"><h3>What the robot does similarly</h3><p class="panel-subtitle">Neighbors in motion space</p>{neighbor_svg("motor")}</div>
  </div>
  <div class="explainer-controls"><button class="overlap-button" type="button" aria-label="Show shared neighbors" aria-pressed="false" aria-controls="overlap-description">Show shared neighbors</button><p class="overlap-description" id="overlap-description" aria-live="polite">Both panels contain the same episodes. Compare the three neighbors of the query in each space.</p></div>
  <p class="explainer-note">This illustrates neighborhood agreement. The full score also uses feature similarities; these points are not experimental data.</p>
</div>'''
anchor = next(p for p in article.find_all("p") if "This gives the Sensorimotor Alignment score" in p.get_text())
anchor.insert_after(BeautifulSoup(explainer, "html.parser"))

toc = "\n".join(f'<a href="#{sid}"><span>{i:02d}</span>{html.escape(name)}</a>' for i, (sid, name) in enumerate(sections))
main_reading = BeautifulSoup(str(article), "html.parser")
for note in main_reading.select(".technical-note"):
    note.decompose()
read_minutes = max(1, round(len(main_reading.get_text(" ", strip=True).split()) / 230))
authors = ['Yunfei Xie', 'Howard H. Qian', 'Shiyi Lan', 'Kaiyu Hang', 'Chen Wei']
authors_html = '<span class="dot" aria-hidden="true">·</span>'.join(f'<span class="author">{a}</span>' for a in authors)
headline = html.escape(title).replace(" Extend to Robotics?", " <span>Extend to Robotics?</span>")

page = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(subtitle, quote=True)}">
  <meta name="theme-color" content="#faf9f6">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(subtitle, quote=True)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}">
  <meta property="og:image" content="{SITE_URL}assets/platonic-robotics.png">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{SITE_URL}">
  <title>{html.escape(title)} — Sensorimotor Alignment</title>
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
  <link rel="stylesheet" href="site.css">
  <script src="site.js" defer></script>
</head>
<body id="top">
  <a class="skip-link" href="#article">Skip to article</a>
  <div class="reading-progress" aria-hidden="true"></div>
  <header class="masthead">
    <div class="masthead-inner">
      <a class="brand" href="#top" aria-label="Sensorimotor Alignment, back to top"><span class="brand-symbol" aria-hidden="true">S<sup>2</sup></span><span class="brand-name">Sensorimotor<br>Alignment</span></a>
      <nav class="masthead-nav" aria-label="Main navigation"><a href="#introduction">The hypothesis</a><a href="#do-more-capable-policies-align-more-closely">The evidence</a><a href="#about">About the work ↗</a></nav>
    </div>
  </header>
  <main>
    <div class="hero">
      <p class="eyebrow">A research note on robot learning</p>
      <h1>{headline}</h1>
      <p class="dek">{html.escape(subtitle)}</p>
      <p class="authors">{authors_html}</p>
      <p class="affiliations">Rice University &nbsp; / &nbsp; NVIDIA</p>
      <div class="hero-meta"><span>{read_minutes} minute read</span><span class="divider" aria-hidden="true"></span><button class="share-button" type="button" aria-label="Copy article link"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="5.5" y="5.5" width="8" height="8" rx="1.5" stroke="currentColor"/><path d="M10.5 3V2.5h-8v8H3" stroke="currentColor"/></svg>Copy link</button></div>
    </div>
    <div class="opening-figure prose">{opening_figure}</div>
    <div class="article-layout">
      <aside class="contents" aria-label="Article contents"><p class="contents-label">In this article</p><nav>{toc}</nav><p class="contents-footer">Vision · Language · Action<br>Views of a physical world.</p></aside>
      <div class="article-main">
        <details class="mobile-contents"><summary>In this article</summary><nav aria-label="Article contents on mobile">{toc}</nav></details>
        {article}
      </div>
    </div>
  </main>
  <footer class="site-footer" id="about"><div class="footer-inner"><div><p class="footer-title">Sensorimotor Alignment</p><p class="footer-note">A Platonic Proxy for Embodied Policy Success<br>Research by Yunfei Xie, Howard H. Qian, Shiyi Lan, Kaiyu Hang, and Chen Wei.</p></div><a class="footer-top" href="#top">Back to top ↑</a></div></footer>
  <dialog class="figure-dialog" aria-label="Expanded research figure" aria-describedby="expanded-caption">
    <div class="dialog-toolbar"><span class="dialog-title">Research figure</span><div class="dialog-actions"><button class="zoom-button" type="button" aria-pressed="false">Actual size</button><button class="close-dialog" type="button" aria-label="Close expanded figure">Close ×</button></div></div>
    <div class="dialog-image-wrap"><img class="dialog-image" alt=""></div>
    <p class="dialog-caption" id="expanded-caption"></p>
  </dialog>
  <div class="toast" role="status" aria-live="polite"></div>
</body>
</html>
'''
(ROOT / "index.html").write_text(page)
(ROOT / "assets/favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#42664e"/><text x="17" y="48" fill="#faf9f6" font-family="Georgia,serif" font-size="44">S</text><text x="40" y="25" fill="#faf9f6" font-family="Georgia,serif" font-size="21">2</text></svg>')
print(f"Built {ROOT / 'index.html'} with {len(sections)} sections and {figure_count} figures.")
