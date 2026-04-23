#!/usr/bin/env python3
"""Convert JPG/JPEG images to RGB pixel-value files.

By default, this script scans the current user's Downloads folder,
finds .jpg/.jpeg files, and writes pixel values as JSON files.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from PIL import Image


def find_jpg_files(input_dir: Path, recursive: bool) -> list[Path]:
	"""Return sorted JPG/JPEG files from the target directory."""
	patterns = ("*.jpg", "*.jpeg", "*.JPG", "*.JPEG")
	files: list[Path] = []

	if recursive:
		for pattern in patterns:
			files.extend(input_dir.rglob(pattern))
	else:
		for pattern in patterns:
			files.extend(input_dir.glob(pattern))

	return sorted({f.resolve() for f in files if f.is_file()})


def image_to_rgb_grid(image_path: Path) -> list[list[list[int]]]:
	"""Return image pixels as [height][width][R,G,B]."""
	with Image.open(image_path) as img:
		rgb = img.convert("RGB")
		width, height = rgb.size
		pix = rgb.load()

		grid: list[list[list[int]]] = []
		for y in range(height):
			row: list[list[int]] = []
			for x in range(width):
				r, g, b = pix[x, y]
				row.append([r, g, b])
			grid.append(row)

	return grid


def write_json(rgb_grid: list[list[list[int]]], output_path: Path) -> None:
	"""Write RGB grid to a JSON file."""
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8") as f:
		json.dump(rgb_grid, f)


def write_csv(rgb_grid: list[list[list[int]]], output_path: Path) -> None:
	"""Write RGB values as CSV rows: y,x,r,g,b."""
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		writer.writerow(["y", "x", "r", "g", "b"])
		for y, row in enumerate(rgb_grid):
			for x, (r, g, b) in enumerate(row):
				writer.writerow([y, x, r, g, b])


def percentile_from_hist(hist: list[int], total: int, percentile: float) -> int:
	"""Return percentile value from a 0-255 histogram."""
	if total <= 0:
		return 0

	target = max(1, math.ceil((percentile / 100.0) * total))
	cumulative = 0
	for value, count in enumerate(hist):
		cumulative += count
		if cumulative >= target:
			return value
	return 255


def compute_peak_metrics(
	rgb_grid: list[list[list[int]]], nir_channel: str, percentile: float
) -> dict[str, int | str]:
	"""Compute peak and robust-peak metrics for RGB/NIR analysis."""
	height = len(rgb_grid)
	width = len(rgb_grid[0]) if height else 0
	total = width * height

	hist_r = [0] * 256
	hist_g = [0] * 256
	hist_b = [0] * 256
	hist_gray = [0] * 256
	sum_r = 0
	sum_g = 0
	sum_b = 0
	sum_gray = 0
	sum_sq_r = 0
	sum_sq_g = 0
	sum_sq_b = 0
	sum_sq_gray = 0

	max_r = -1
	max_g = -1
	max_b = -1
	max_gray = -1
	max_r_x = max_r_y = 0
	max_g_x = max_g_y = 0
	max_b_x = max_b_y = 0
	max_gray_x = max_gray_y = 0
	sat_any = 0
	sat_nir = 0

	for y, row in enumerate(rgb_grid):
		for x, (r, g, b) in enumerate(row):
			hist_r[r] += 1
			hist_g[g] += 1
			hist_b[b] += 1
			sum_r += r
			sum_g += g
			sum_b += b
			sum_sq_r += r * r
			sum_sq_g += g * g
			sum_sq_b += b * b

			gray = int(round((0.299 * r) + (0.587 * g) + (0.114 * b)))
			hist_gray[gray] += 1
			sum_gray += gray
			sum_sq_gray += gray * gray

			if r > max_r:
				max_r = r
				max_r_x, max_r_y = x, y
			if g > max_g:
				max_g = g
				max_g_x, max_g_y = x, y
			if b > max_b:
				max_b = b
				max_b_x, max_b_y = x, y
			if gray > max_gray:
				max_gray = gray
				max_gray_x, max_gray_y = x, y

			if r == 255 or g == 255 or b == 255:
				sat_any += 1

			if nir_channel == "red" and r == 255:
				sat_nir += 1
			elif nir_channel == "green" and g == 255:
				sat_nir += 1
			elif nir_channel == "blue" and b == 255:
				sat_nir += 1
			elif nir_channel == "gray" and gray == 255:
				sat_nir += 1

	pctl_r = percentile_from_hist(hist_r, total, percentile)
	pctl_g = percentile_from_hist(hist_g, total, percentile)
	pctl_b = percentile_from_hist(hist_b, total, percentile)
	pctl_gray = percentile_from_hist(hist_gray, total, percentile)

	mean_r = (sum_r / total) if total else 0.0
	mean_g = (sum_g / total) if total else 0.0
	mean_b = (sum_b / total) if total else 0.0
	mean_gray = (sum_gray / total) if total else 0.0

	var_r = max(0.0, ((sum_sq_r / total) - (mean_r * mean_r))) if total else 0.0
	var_g = max(0.0, ((sum_sq_g / total) - (mean_g * mean_g))) if total else 0.0
	var_b = max(0.0, ((sum_sq_b / total) - (mean_b * mean_b))) if total else 0.0
	var_gray = max(0.0, ((sum_sq_gray / total) - (mean_gray * mean_gray))) if total else 0.0

	std_r = math.sqrt(var_r)
	std_g = math.sqrt(var_g)
	std_b = math.sqrt(var_b)
	std_gray = math.sqrt(var_gray)

	def snr_values(mean: float, std: float) -> tuple[float, float]:
		if std <= 0:
			return float("inf"), float("inf")
		linear = mean / std
		return linear, (20.0 * math.log10(linear)) if linear > 0 else float("-inf")

	snr_r, snr_db_r = snr_values(mean_r, std_r)
	snr_g, snr_db_g = snr_values(mean_g, std_g)
	snr_b, snr_db_b = snr_values(mean_b, std_b)
	snr_gray, snr_db_gray = snr_values(mean_gray, std_gray)

	if nir_channel == "red":
		nir_peak = max_r
		nir_pctl = pctl_r
	elif nir_channel == "green":
		nir_peak = max_g
		nir_pctl = pctl_g
	elif nir_channel == "blue":
		nir_peak = max_b
		nir_pctl = pctl_b
	else:
		nir_peak = max_gray
		nir_pctl = pctl_gray

	return {
		"width": width,
		"height": height,
		"total_pixels": total,
		"max_r": max_r,
		"max_r_x": max_r_x,
		"max_r_y": max_r_y,
		"max_g": max_g,
		"max_g_x": max_g_x,
		"max_g_y": max_g_y,
		"max_b": max_b,
		"max_b_x": max_b_x,
		"max_b_y": max_b_y,
		"max_gray": max_gray,
		"max_gray_x": max_gray_x,
		"max_gray_y": max_gray_y,
		"pctl_r": pctl_r,
		"pctl_g": pctl_g,
		"pctl_b": pctl_b,
		"pctl_gray": pctl_gray,
		"nir_channel": nir_channel,
		"nir_peak": nir_peak,
		"nir_percentile": nir_pctl,
		"sat_pixels_any": sat_any,
		"sat_pixels_nir": sat_nir,
		"mean_r": round(mean_r, 4),
		"mean_g": round(mean_g, 4),
		"mean_b": round(mean_b, 4),
		"mean_gray": round(mean_gray, 4),
		"std_r": round(std_r, 4),
		"std_g": round(std_g, 4),
		"std_b": round(std_b, 4),
		"std_gray": round(std_gray, 4),
		"snr_r": round(snr_r, 4),
		"snr_g": round(snr_g, 4),
		"snr_b": round(snr_b, 4),
		"snr_gray": round(snr_gray, 4),
		"snr_db_r": round(snr_db_r, 4),
		"snr_db_g": round(snr_db_g, 4),
		"snr_db_b": round(snr_db_b, 4),
		"snr_db_gray": round(snr_db_gray, 4),
	}


def write_peak_summary(rows: list[dict[str, int | str]], output_path: Path) -> None:
	"""Write per-image peak metrics to CSV."""
	output_path.parent.mkdir(parents=True, exist_ok=True)
	fieldnames = [
		"image",
		"width",
		"height",
		"total_pixels",
		"max_r",
		"max_r_x",
		"max_r_y",
		"max_g",
		"max_g_x",
		"max_g_y",
		"max_b",
		"max_b_x",
		"max_b_y",
		"max_gray",
		"max_gray_x",
		"max_gray_y",
		"pctl_r",
		"pctl_g",
		"pctl_b",
		"pctl_gray",
		"nir_channel",
		"nir_peak",
		"nir_percentile",
		"sat_pixels_any",
		"sat_pixels_nir",
		"mean_r",
		"mean_g",
		"mean_b",
		"mean_gray",
		"std_r",
		"std_g",
		"std_b",
		"std_gray",
		"snr_r",
		"snr_g",
		"snr_b",
		"snr_gray",
		"snr_db_r",
		"snr_db_g",
		"snr_db_b",
		"snr_db_gray",
	]

	with output_path.open("w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		for row in rows:
			writer.writerow(row)


def parse_args() -> argparse.Namespace:
	home_downloads = Path.home() / "Downloads"
	parser = argparse.ArgumentParser(
		description="Convert JPG/JPEG files to RGB pixel-value files."
	)
	parser.add_argument(
		"--input-dir",
		type=Path,
		default=home_downloads,
		help=f"Directory containing JPG files (default: {home_downloads})",
	)
	parser.add_argument(
		"--output-dir",
		type=Path,
		default=Path("pixel_values"),
		help="Directory to save output files (default: ./pixel_values)",
	)
	parser.add_argument(
		"--format",
		choices=("json", "csv"),
		default="json",
		help="Output format for pixel values (default: json)",
	)
	parser.add_argument(
		"--recursive",
		action="store_true",
		help="Search recursively inside subfolders.",
	)
	parser.add_argument(
		"--skip-pixel-export",
		action="store_true",
		help="Only calculate peak metrics; do not export full pixel files.",
	)
	parser.add_argument(
		"--nir-channel",
		choices=("red", "green", "blue", "gray"),
		default="red",
		help="Channel used as NIR proxy for peak metrics (default: red).",
	)
	parser.add_argument(
		"--peak-percentile",
		type=float,
		default=99.5,
		help="Robust peak percentile, e.g. 99.5 (default: 99.5).",
	)
	parser.add_argument(
		"--summary-file",
		type=Path,
		default=Path("peak_summary.csv"),
		help="Peak summary CSV path (default: ./peak_summary.csv).",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	input_dir = args.input_dir.expanduser().resolve()
	output_dir = args.output_dir.expanduser().resolve()
	summary_path = args.summary_file.expanduser().resolve()

	if args.peak_percentile <= 0 or args.peak_percentile > 100:
		raise SystemExit("--peak-percentile must be in the range (0, 100].")

	if not input_dir.exists() or not input_dir.is_dir():
		raise SystemExit(f"Input directory does not exist: {input_dir}")

	jpg_files = find_jpg_files(input_dir, recursive=args.recursive)
	if not jpg_files:
		print(f"No JPG/JPEG files found in {input_dir}")
		return

	peak_rows: list[dict[str, int | str]] = []

	for image_path in jpg_files:
		rgb_grid = image_to_rgb_grid(image_path)
		metrics = compute_peak_metrics(
			rgb_grid, nir_channel=args.nir_channel, percentile=args.peak_percentile
		)
		metrics["image"] = image_path.name
		peak_rows.append(metrics)

		output_name = image_path.stem
		if not args.skip_pixel_export:
			if args.format == "json":
				out_path = output_dir / f"{output_name}.json"
				write_json(rgb_grid, out_path)
			else:
				out_path = output_dir / f"{output_name}.csv"
				write_csv(rgb_grid, out_path)
			print(f"Converted: {image_path.name} -> {out_path}")

		print(
			f"Peak ({args.nir_channel}) for {image_path.name}: "
			f"max={metrics['nir_peak']}, p{args.peak_percentile}={metrics['nir_percentile']}"
		)

	write_peak_summary(peak_rows, summary_path)
	print(f"Peak summary saved: {summary_path}")

	print(f"Done. Processed {len(jpg_files)} image(s).")


if __name__ == "__main__":
	main()
