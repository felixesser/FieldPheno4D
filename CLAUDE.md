# CLAUDE.md

Project guidance and a running log of user prompts for the FieldPheno4D website.

## Project overview

FieldPheno4D is a static website deployed to GitHub Pages describing a
multi-temporal, multi-crop dataset of high-resolution 3D point clouds captured
in the field.

### How the site is built (source of truth)

- The **source template** is [website/templates/index.html](website/templates/index.html)
  (a Jinja2 template), populated by [website/app.py](website/app.py).
- Page text comes from files in [website/texts/](website/texts/) (e.g.
  `description.txt`, `acknowledgments.txt`, `citation.bibtex`, `title.txt`,
  `description_robot.txt`). `website/app.py` loads these into the template
  context via `_build_page_context`.
- Styles live in [website/static/css/style.css](website/static/css/style.css);
  images in [website/static/images/](website/static/images/).
- **Deployment**: `.github/workflows/pages.yml` runs
  `python scripts/build_github_pages.py --output-dir .pages_build`, which
  renders the template and copies `website/static`, `images`, and
  `data/FieldPheno4Dimg` into `.pages_build`, then uploads that as the Pages
  artifact. `.pages_build`, `/site/`, and `/docs/` are git-ignored build outputs.
- The root [index.html](index.html) is a committed, pre-rendered copy of the
  site (asset paths relative to repo root). It is NOT what CI deploys, but keep
  it in sync with the template when adding content so it also renders correctly.

### Conventions

- Each content section is a `<section class="block ...">` with a
  `<div class="block-inner">` and an `<h2>`. Blocks get a colored left border
  accent (see `.block.pointclouds`, `.block.robot`, etc. in `style.css`).
- Source text files may contain LaTeX markup (`\cite`, `\href`, `\ref`, `$...$`,
  `\text`, `~`). `website/app.py` `_latex_to_html()` cleans this subset into HTML.
- To test the deployment locally, run the build script and serve `.pages_build`
  over HTTP (e.g. `python -m http.server`), then check that `index.html`, the
  images, and the CSS all return 200.

## User prompt log

### 2026-07-15

- Analyze the structure of the repo (a static-HTML GitHub Pages website).
- Add a box to the website describing the robot platform used to create the
  dataset. Image is at `website/static/images/field_robot.png`; description text
  is in `website/texts/description_robot.txt`. Place this box **before** the
  "3D point clouds" box, styled consistently with the existing template.
- After making the changes, test the deployment of the website.
- Remember all of the user's prompts in a `CLAUDE.md`.
