# S² · Sensorimotor Alignment

[Read the website](https://yunfeixie233.github.io/s2/)

“Sensorimotor Alignment: A Platonic Proxy for Embodied Policy Success” presents our work on the relationship between sensory representations, demonstrated robot motion, and policy success.

Research by Yunfei Xie, Howard H. Qian, Shiyi Lan, Kaiyu Hang, and Chen Wei.

## Website

The complete article is in `index.html`. Styles, interactions, and figures are local, so the site also works when opened directly from disk. GitHub Pages publishes the root of the `main` branch. Changes pushed to that branch are deployed automatically.

## Editing

Edit the article in `post.md`, the design in `site.css`, and the interactions in `site.js`. To regenerate `index.html`, install Pandoc and the Python dependency, then run:

```sh
python3 -m pip install -r requirements.txt
python3 build.py
```

Set `PAPER_URL` in `build.py` to the verified public paper URL when available. Until then, the Paper button is marked unavailable and has no link.

To preview the site locally:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/`. Commit the regenerated `index.html` together with any source or asset changes, then push to `main` to update the public site.
