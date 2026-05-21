from __future__ import annotations

import sys
import shutil
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from website.app import app, _build_page_context


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    if src.exists():
        shutil.copytree(src, dst)


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    output_path = repo_root / "index.html"
    site_root = repo_root / "site"
    docs_root = repo_root / "docs"
    site_root.mkdir(parents=True, exist_ok=True)
    docs_root.mkdir(parents=True, exist_ok=True)
    context = _build_page_context(asset_base="website/static", data_base="data")

    with app.app_context():
        rendered = app.jinja_env.get_template("index.html").render(**context)

    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {output_path}")

    _copy_file(output_path, site_root / "index.html")
    _copy_file(output_path, docs_root / "index.html")
    _copy_tree(repo_root / "website" / "static", site_root / "website" / "static")
    _copy_tree(repo_root / "website" / "static", docs_root / "website" / "static")

    data_source = repo_root / "data" / "FieldPheno4Dimg"
    data_target = site_root / "data"
    data_target.mkdir(parents=True, exist_ok=True)
    if data_source.exists():
        for plot_dir in sorted(data_source.iterdir()):
            if plot_dir.is_dir():
                _copy_tree(plot_dir, data_target / plot_dir.name)
                _copy_tree(plot_dir, docs_root / "data" / plot_dir.name)

    (site_root / ".nojekyll").write_text("", encoding="utf-8")
    (docs_root / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Prepared GitHub Pages site in {site_root}")
    print(f"Prepared GitHub Pages docs in {docs_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
