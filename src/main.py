"""Command-line entry point for the first Video Enhancer milestone."""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from config import DEFAULT_MODEL, DEFAULT_OUTPUT_SCALE, INPUT_DIR, MODELS_DIR, OUTPUT_DIR, SUPPORTED_VIDEO_EXTENSIONS, TEMP_DIR
from encoder import encode_video
from logger import configure_logging
from upscale import create_upscaler, upscale_frames
from utils import ensure_directories, reset_directory
from video import extract_frames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upscale a phone video with Real-ESRGAN.")
    parser.add_argument("input", type=Path, help="Video path, or a filename inside input/.")
    parser.add_argument("-o", "--output", type=Path, help="Output MP4 path (default: output/<name>_upscaled.mp4).")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="RealESRGAN x4+ checkpoint path.")
    parser.add_argument("--scale", type=float, default=DEFAULT_OUTPUT_SCALE, choices=(2.0, 3.0, 4.0), help="Output scale.")
    parser.add_argument("--tile", type=int, default=0, help="Tile size for low-VRAM GPUs; 0 disables tiling.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep extracted and upscaled frames in temp/.")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def resolve_input(path: Path) -> Path:
    resolved = path if path.is_file() else INPUT_DIR / path
    if not resolved.is_file():
        raise FileNotFoundError(f"Input video not found: {path}")
    if resolved.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
        raise ValueError(f"Unsupported video type: {resolved.suffix}")
    return resolved.resolve()


def require_valid_environment() -> None:
    """Run the project environment gate before any video processing starts."""
    check = Path(__file__).resolve().parent.parent / "test_environment.py"
    result = subprocess.run([sys.executable, str(check)], check=False)
    if result.returncode != 0:
        raise RuntimeError("Environment check failed. Fix .venv dependencies before processing video.")


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    require_valid_environment()
    ensure_directories(INPUT_DIR, OUTPUT_DIR, TEMP_DIR, MODELS_DIR)
    source = resolve_input(args.input)
    output = (args.output or OUTPUT_DIR / f"{source.stem}_upscaled.mp4").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    original_frames = TEMP_DIR / "frames_original"
    upscaled_frames = TEMP_DIR / "frames_upscaled"
    reset_directory(original_frames)
    reset_directory(upscaled_frames)
    try:
        logging.info("Extracting frames from %s", source.name)
        frame_rate = extract_frames(source, original_frames)
        upscaler = create_upscaler(args.model.resolve(), args.tile)
        upscale_frames(original_frames, upscaled_frames, upscaler, args.scale)
        logging.info("Encoding %s", output.name)
        encode_video(upscaled_frames, frame_rate, source, output)
        logging.info("Done: %s", output)
    finally:
        if not args.keep_temp:
            reset_directory(original_frames)
            reset_directory(upscaled_frames)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        logging.error("%s", error)
        raise SystemExit(1) from error
