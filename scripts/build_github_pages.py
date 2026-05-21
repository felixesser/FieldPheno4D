from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from website.app import app, _build_page_context


def main() -> int:
    output_path = repo_root / "index.html"
    context = _build_page_context(asset_base="website/static", data_base="data")

    with app.app_context():
        rendered = app.jinja_env.get_template("index.html").render(**context)

    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
