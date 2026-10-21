# S² · Sensorimotor Alignment

[Read the website](https://yunfeixie233.github.io/s2/)

[Video](https://yunfeixie233.github.io/s2/assets/s2-walkthrough.mp4?v=6c1d33433e) · [Code](https://github.com/yunfeixie233/sensorimotor-alignment) · Paper (coming soon)

“Sensorimotor Alignment: A Platonic Proxy for Embodied Policy Success” presents our work on the relationship between sensory representations, demonstrated robot motion, and policy success.

Research by [Yunfei Xie](https://yunfeixie233.github.io/), [Howard H. Qian](https://howardqian201.github.io/), [Shiyi Lan](https://voidrank.github.io/), [Kaiyu Hang](https://hangkaiyu.github.io/), and [Chen Wei](https://weichen582.github.io/).

## Website

The complete article is in `index.html`. Styles, interactions, and figures are local, so the site also works when opened directly from disk. GitHub Pages publishes the root of the `main` branch. Changes pushed to that branch are deployed automatically.

## Editing

Edit the article in `post.md`, the design in `site.css`, and the interactions in `site.js`. To regenerate `index.html`, install Pandoc and the Python dependency, then run:

```sh
python3 -m pip install -r requirements.txt
python3 build.py
```

Set `PAPER_URL` in `build.py` to the verified public paper URL when available. Until then, the Paper button reads “Paper (coming soon)” and has no link. The public code is released from [`yunfeixie233/sensorimotor-alignment`](https://github.com/yunfeixie233/sensorimotor-alignment); its README links back to this website and the same video.

To preview the site locally:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/`. Commit the regenerated `index.html` together with any source or asset changes, then push to `main` to update the public site.

## Responsive layout

The 3:29 video is the first visual, directly below the title and resource links. It has a large play button and native playback controls. The original teaser (Figure 1) follows the second introductory paragraph, immediately before “Our evidence suggests the answer is yes.” The header's **Watch video · 3:29** link and both contents menus jump to the player. Playback starts only on request; the poster loads without downloading the full video. The poster is a frame from the existing walkthrough at 8 seconds.

The reading column stays at 660px. Dense research figures (3, 5, and 6) expand on desktop and have panel selectors with horizontal scrolling on smaller screens. The complete original image remains available through “View full figure.” Navigation labels are shorter than article headings, with collapsible subsections and a mobile contents menu.

The two inline animations use MP4 copies of the original GIF sequences, with pause/restart controls and static posters when reduced motion is preferred. The original GIF files remain in `assets/`. `build.py` preserves the article and caption wording while adding these controls, caption line breaks, section links, and copyable citations.
