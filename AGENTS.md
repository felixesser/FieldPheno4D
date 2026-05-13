Agent Instructions for FieldPheno4D Website
=========================================

Purpose
-------
This file gives concise, actionable guidance for AI coding agents working in this repository. Prefer linking to existing docs (README.md) rather than duplicating content.

Quick facts
-----------
- **Language:** Python (Flask)
- **Run (development):** activate the virtualenv then run `python app.py` (see [README.md](README.md) for install/run steps)
- **App entry:** `app.py` serves the Flask app on port 5000 by default
- **Dependencies:** `requirements.txt` (Flask, gunicorn)

Repository layout (important files)
----------------------------------
- **app.py**: backend routes, dataset path constant `DATA_DIR`.
- **templates/**: HTML templates (frontend views).
- **static/**: CSS/JS assets used by the UI.
- **installation.sh**: script to create the `venv` and install dependencies.

Project-specific conventions & notes for agents
---------------------------------------------
- The dataset is expected at `/data/FieldPheno4D`. `app.py` reads that path via the `DATA_DIR` constant. Avoid changing its semantics without checking with the maintainer.
- If `/data/FieldPheno4D` is absent the app returns mock/demo data from `get_plots()` — tests or local runs can rely on that behavior.
- The app runs in debug mode when executed directly (`python app.py`). For production use, prefer `gunicorn --bind 0.0.0.0:5000 app:app`.
- Keep frontend assets in `static/` and templates in `templates/`. Small UI tweaks are fine; avoid large structural rewrites without coordinating.

Agent behavior guidance
-----------------------
- Link to `README.md` for install/run details rather than re-stating steps.
- When changing server behavior, run the app locally to verify (activate venv, install requirements, run `python app.py`).
- Do not commit dataset files to the repo. Use small mock files for CI if needed.
- When adding automated checks or CI, include setup steps to create a mock `/data/FieldPheno4D` structure.

Next useful customizations (suggestions)
--------------------------------------
- Add a small skill that scaffolds a mock `data` directory for CI tests.
- Add a `.github/copilot-instructions.md` if you want org-level or repo-specific agent instructions surfaced by GitHub integrations.

Where to look for details
-------------------------
See the main project README: [README.md](README.md)

Questions / feedback
--------------------
If you'd like the agent instructions tailored to a specific area (frontend, dataset ingestion, CI), tell me which area and I'll add a focused section.
