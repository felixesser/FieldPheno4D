from __future__ import annotations

import sys
import os
import subprocess
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


def _github_raw_base() -> str:
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if repository:
        return f"https://raw.githubusercontent.com/{repository}/main"

    try:
        remote_url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_root,
            text=True,
        ).strip()
    except Exception:
        return ""

    if remote_url.startswith("git@github.com:"):
        repository = remote_url.removeprefix("git@github.com:").removesuffix(".git")
        return f"https://raw.githubusercontent.com/{repository}/main"

    if remote_url.startswith("https://github.com/"):
        repository = remote_url.removeprefix("https://github.com/").removesuffix(".git")
        return f"https://raw.githubusercontent.com/{repository}/main"

    return ""


def _render_site(site_root: Path, *, asset_base: str, data_base: str, copy_assets: bool, rewrite_timetable_asset: bool = False) -> None:
    site_root.mkdir(parents=True, exist_ok=True)
    context = _build_page_context(asset_base=asset_base, data_base=data_base)

    with app.app_context():
        rendered = app.jinja_env.get_template("index.html").render(**context)

    if rewrite_timetable_asset:
        rendered = rendered.replace(
            'src="images/fieldpheno4d_timetable.png"',
            f'src="{asset_base}/images/fieldpheno4d_timetable.png"',
        )

    (site_root / "index.html").write_text(rendered, encoding="utf-8")
    print(f"Wrote {site_root / 'index.html'}")

    if copy_assets:
        _copy_tree(repo_root / "website" / "static", site_root / "website" / "static")
        _copy_tree(repo_root / "images", site_root / "images")

        data_source = repo_root / "data" / "FieldPheno4Dimg"
        data_target = site_root / "data"
        data_target.mkdir(parents=True, exist_ok=True)
        if data_source.exists():
            for plot_dir in sorted(data_source.iterdir()):
                if plot_dir.is_dir():
                    _copy_tree(plot_dir, data_target / plot_dir.name)

    (site_root / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Prepared GitHub Pages site in {site_root}")


def main() -> int:
    site_root = repo_root / "site"
    docs_root = repo_root / "docs"
    raw_base = _github_raw_base()
    _render_site(site_root, asset_base="website/static", data_base="data", copy_assets=True)
    docs_asset_base = f"{raw_base}/website/static" if raw_base else "website/static"
    docs_data_base = f"{raw_base}/data/FieldPheno4Dimg" if raw_base else "data/FieldPheno4Dimg"
    _render_site(
        docs_root,
        asset_base=docs_asset_base,
        data_base=docs_data_base,
        copy_assets=False,
        rewrite_timetable_asset=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
