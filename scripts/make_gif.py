from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image



def _resolve_image_dir(plot_folder: str, images_root: str, subdir: str) -> Path:
    plot_path = Path(plot_folder).expanduser()
    if plot_path.is_absolute() or plot_path.exists():
        base = plot_path
    else:
        base = Path(images_root).expanduser() / plot_path

    candidate = base / subdir
    if candidate.is_dir():
        return candidate

    legacy_candidate = base / "combined"
    if legacy_candidate.is_dir():
        return legacy_candidate

    raise FileNotFoundError(
        f"Could not find image directory for {plot_folder!r}. Tried {candidate} and {legacy_candidate}."
    )


def _apply_shared_palette(images: list[Image.Image], exact_colors: int = 16) -> list[Image.Image]:
    """Quantize all frames to one palette so colors do not flicker between frames.

    The most frequent colors (page and plot backgrounds) are kept exact. The remaining
    entries are split evenly over all other distinct colors, because weighting them by
    pixel count would spend the palette on large uniform areas and band the colormap.
    """
    frames = [img.convert("RGB") for img in images]
    pixels = np.concatenate([np.asarray(frame).reshape(-1, 3) for frame in frames])
    colors, counts = np.unique(pixels, axis=0, return_counts=True)
    order = np.argsort(counts)[::-1]
    exact = colors[order[:exact_colors]]
    rest = colors[order[exact_colors:]]

    entries = exact.astype(np.uint8).tobytes()
    if rest.size:
        swatch = Image.fromarray(rest[np.newaxis, :, :].astype(np.uint8), mode="RGB")
        reduced = swatch.quantize(colors=256 - len(exact), method=Image.Quantize.MEDIANCUT)
        entries += bytes(reduced.getpalette() or [])

    palette = Image.new("P", (1, 1))
    palette.putpalette(entries[:768].ljust(768, bytes(1)))
    return [frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG) for frame in frames]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a GIF from FieldPheno4D plot previews.")
    parser.add_argument("plot_folder", help="Plot folder name or path, e.g. P147 or data/FieldPheno4Dimg/P147.")
    parser.add_argument("--images-root", default="data/FieldPheno4Dimg", help="Root folder that contains the plot folders.")
    parser.add_argument("--subdir", default="dem/png/combined", help="Relative image directory inside the plot folder.")
    parser.add_argument("--output", default=None, help="Output GIF path. Defaults to <plot_folder>/demo_slider.gif.")
    parser.add_argument("--size", nargs=2, type=int, default=(800, 800), metavar=("WIDTH", "HEIGHT"), help="Thumbnail size.")
    parser.add_argument("--duration", type=int, default=800, help="Frame duration in milliseconds.")
    parser.add_argument("--loop", type=int, default=0, help="GIF loop count. Use 0 for infinite loop.")
    parser.add_argument("--shared-palette", action="store_true", help="Use one color palette for all frames.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    image_dir = _resolve_image_dir(args.plot_folder, args.images_root, args.subdir)
    files = sorted(image_dir.glob("*.png"))
    if not files:
        print(f"No PNG files found in {image_dir}")
        return 1

    images: list[Image.Image] = []
    for file in files:
        img = Image.open(file)
        img.thumbnail(tuple(args.size), Image.Resampling.LANCZOS)
        images.append(img)

    if args.shared_palette:
        images = _apply_shared_palette(images)

    output_path = Path(args.output).expanduser() if args.output else Path(args.plot_folder).expanduser()
    if output_path.is_dir():
        output_path = output_path / "demo_slider.gif"
    elif output_path.suffix.lower() != ".gif":
        output_path = output_path.with_suffix(".gif")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=args.duration,
        loop=args.loop,
    )
    print(f"Created {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
