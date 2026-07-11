"""Split a long video into shorter files with FFmpeg."""

import argparse
import logging
from pathlib import Path

from config import INPUT_DIR, OUTPUT_DIR, SUPPORTED_VIDEO_EXTENSIONS
from logger import configure_logging
from utils import ensure_directories, require_executable, run_command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split a video into short MP4 files without re-encoding.")
    parser.add_argument("input", type=Path, help="Video path, or a filename inside input/.")
    parser.add_argument(
        "--segment-seconds",
        type=int,
        default=300,
        help="Maximum target duration of one segment in seconds (default: 300 = 5 minutes).",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Directory for the parts (default: output/<video_name>_parts).",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def resolve_input(path: Path) -> Path:
    resolved = path if path.is_file() else INPUT_DIR / path
    if not resolved.is_file():
        raise FileNotFoundError(f"Input video not found: {path}")
    if resolved.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
        raise ValueError(f"Unsupported video type: {resolved.suffix}")
    return resolved.resolve()


def split_video(source: Path, output_dir: Path, segment_seconds: int) -> list[Path]:
    """Create MP4 parts while copying streams without quality loss."""
    if segment_seconds <= 0:
        raise ValueError("--segment-seconds must be a positive whole number.")

    require_executable("ffmpeg")
    ensure_directories(output_dir)
    existing_parts = list(output_dir.glob("part_*.mp4"))
    if existing_parts:
        raise RuntimeError(
            f"Output directory already contains {len(existing_parts)} parts: {output_dir}. "
            "Choose another --output-dir or remove old parts first."
        )

    output_pattern = output_dir / "part_%03d.mp4"
    run_command([
        "ffmpeg", "-y", "-i", str(source), "-map", "0", "-c", "copy",
        "-f", "segment", "-segment_time", str(segment_seconds),
        "-reset_timestamps", "1", str(output_pattern),
    ])
    parts = sorted(output_dir.glob("part_*.mp4"))
    if not parts:
        raise RuntimeError("FFmpeg did not create any video parts.")
    return parts


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    source = resolve_input(args.input)
    output_dir = (args.output_dir or OUTPUT_DIR / f"{source.stem}_parts").resolve()
    logging.info("Splitting %s into approximately %d-second parts", source.name, args.segment_seconds)
    parts = split_video(source, output_dir, args.segment_seconds)
    logging.info("Done: created %d parts in %s", len(parts), output_dir)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        logging.error("%s", error)
        raise SystemExit(1) from error
