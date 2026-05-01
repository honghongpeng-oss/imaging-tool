#!/usr/bin/env python3
"""Generate JSON metadata manifest for YUV-to-PNG conversion outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate metadata JSON for YUV input files and PNG outputs.")
    parser.add_argument("--input-dir", default="~/Downloads", help="Directory that contains .yuv files")
    parser.add_argument("--output-dir", default="~/Downloads/yuv_batch_outputs", help="Directory that contains converted PNGs")
    parser.add_argument("--pattern", default="src*_ref__625.yuv", help="Glob pattern for YUV input files")
    parser.add_argument("--pixel-format", default="uyvy422", help="Pixel format used for conversion")
    parser.add_argument("--width", type=int, default=720, help="Conversion width")
    parser.add_argument("--height", type=int, default=480, help="Conversion height")
    parser.add_argument("--frame-index", type=int, default=0, help="Frame index used for conversion")
    parser.add_argument("--manifest-name", default="yuv_batch_metadata.json", help="Output manifest JSON file name")
    return parser.parse_args()


def build_manifest(args: argparse.Namespace) -> dict:
    input_dir = Path(args.input_dir).expanduser()
    output_dir = Path(args.output_dir).expanduser()

    settings = {
        "pixel_format": args.pixel_format,
        "width": args.width,
        "height": args.height,
        "frame_index": args.frame_index,
    }

    entries = []
    for yuv in sorted(input_dir.glob(args.pattern)):
        png = output_dir / f"{yuv.stem}.png"

        entry: dict = {
            "input_file": str(yuv),
            "output_file": str(png),
            "decode_settings": settings,
            "input_exists": yuv.exists(),
            "output_exists": png.exists(),
            "input_size_bytes": yuv.stat().st_size if yuv.exists() else None,
            "output_size_bytes": png.stat().st_size if png.exists() else None,
            "input_modified_utc": iso_mtime(yuv) if yuv.exists() else None,
            "output_modified_utc": iso_mtime(png) if png.exists() else None,
            "input_sha256": sha256(yuv) if yuv.exists() else None,
            "output_sha256": sha256(png) if png.exists() else None,
        }

        if png.exists():
            with Image.open(png) as image:
                entry["output_image"] = {
                    "format": image.format,
                    "mode": image.mode,
                    "width": image.width,
                    "height": image.height,
                    "info": {k: str(v) for k, v in image.info.items()},
                }

        entries.append(entry)

    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "output_directory": str(output_dir),
        "file_count": len(entries),
        "entries": entries,
    }


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args)

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / args.manifest_name
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(manifest_path)


if __name__ == "__main__":
    main()
