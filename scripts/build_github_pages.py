from __future__ import annotations

import argparse
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


def _prepare_pages_artifact(output_root: Path) -> None:
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    context = _build_page_context(asset_base="website/static", data_base="data/FieldPheno4Dimg")

    with app.app_context():
        rendered = app.jinja_env.get_template("index.html").render(**context)

    (output_root / "index.html").write_text(rendered, encoding="utf-8")
    print(f"Wrote {output_root / 'index.html'}")

    _copy_tree(repo_root / "website" / "static", output_root / "website" / "static")
    _copy_tree(repo_root / "images", output_root / "images")
    _copy_tree(repo_root / "data" / "FieldPheno4Dimg", output_root / "data" / "FieldPheno4Dimg")

    (output_root / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Prepared GitHub Pages artifact in {output_root}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a GitHub Pages artifact directory.")
    parser.add_argument(
        "--output-dir",
        default=".pages_build",
        help="Output folder for the generated Pages artifact.",
    )
    args = parser.parse_args()

    output_root = (repo_root / args.output_dir).resolve()
    _prepare_pages_artifact(output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
