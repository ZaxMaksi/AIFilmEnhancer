"""Command-line entry point for the first Video Enhancer milestone."""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path

from config import DEFAULT_MODEL, DEFAULT_OUTPUT_SCALE, DEFAULT_SEGMENT_SECONDS, INPUT_DIR, MODELS_DIR, OUTPUT_DIR, SUPPORTED_VIDEO_EXTENSIONS, TEMP_DIR
from encoder import concatenate_videos, encode_video
from logger import configure_logging
from split_video import split_video
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
    parser.add_argument(
        "--segment-seconds",
        type=int,
        default=DEFAULT_SEGMENT_SECONDS,
        help="Process one segment at a time; default: 300 seconds (5 minutes).",
    )
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted segmented job with the same settings.")
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


def job_directory(source: Path, segment_seconds: int, model_path: Path, tile_size: int, scale: float) -> Path:
    """Return a stable working directory for one source and processing setup."""
    source_stat = source.stat()
    fingerprint = "|".join((
        str(source), str(source_stat.st_size), str(source_stat.st_mtime_ns),
        str(segment_seconds), str(model_path), str(tile_size), str(scale),
    ))
    job_id = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:12]
    return TEMP_DIR / "jobs" / f"{source.stem}_{job_id}"


def write_state(state_path: Path, state: dict[str, object]) -> None:
    """Atomically save completed segment numbers for crash-safe resuming."""
    temporary_path = state_path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    temporary_path.replace(state_path)


def load_state(state_path: Path) -> dict[str, object]:
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read resume state: {state_path}") from error


def process_segments(
    source: Path,
    output: Path,
    segment_seconds: int,
    model_path: Path,
    tile_size: int,
    scale: float,
    resume: bool,
) -> Path:
    """Process a long video one segment at a time to keep disk usage bounded."""
    work_dir = job_directory(source, segment_seconds, model_path, tile_size, scale)
    state_path = work_dir / "state.json"
    segments_dir = work_dir / "source_segments"
    original_frames = work_dir / "frames_original"
    upscaled_frames = work_dir / "frames_upscaled"
    encoded_dir = work_dir / "encoded_segments"

    if resume:
        if not state_path.is_file():
            raise RuntimeError("No resumable job was found for this video and these settings. Start without --resume first.")
        state = load_state(state_path)
        if state.get("finished") and output.is_file():
            logging.info("This job is already complete: %s", output)
            return work_dir
        logging.info("Resuming job from %s", work_dir)
    else:
        reset_directory(work_dir)
        state = {"segments_ready": False, "completed_segments": [], "finished": False}
        write_state(state_path, state)

    for directory in (original_frames, upscaled_frames, encoded_dir):
        ensure_directories(directory)

    if state.get("segments_ready"):
        source_segments = sorted(segments_dir.glob("part_*.mp4"))
        if not source_segments:
            raise RuntimeError("Resume data is incomplete: source segments are missing.")
    else:
        reset_directory(segments_dir)
        logging.info("Splitting %s into approximately %d-second segments", source.name, segment_seconds)
        source_segments = split_video(source, segments_dir, segment_seconds)
        state["segments_ready"] = True
        write_state(state_path, state)
    logging.info("Using %d source segments", len(source_segments))

    upscaler = create_upscaler(model_path, tile_size)
    encoded_segments: list[Path] = []
    completed_segments = {int(index) for index in state.get("completed_segments", [])}

    for index, source_segment in enumerate(source_segments, start=1):
        encoded_segment = encoded_dir / f"segment_{index:03d}.mp4"
        if index in completed_segments and encoded_segment.is_file():
            logging.info("Skipping completed segment %d/%d", index, len(source_segments))
            encoded_segments.append(encoded_segment)
            continue

        reset_directory(original_frames)
        reset_directory(upscaled_frames)
        logging.info("Processing segment %d/%d: %s", index, len(source_segments), source_segment.name)
        frame_rate = extract_frames(source_segment, original_frames)
        upscale_frames(original_frames, upscaled_frames, upscaler, scale)
        encode_video(upscaled_frames, frame_rate, source_segment, encoded_segment)
        encoded_segments.append(encoded_segment)
        completed_segments.add(index)
        state["completed_segments"] = sorted(completed_segments)
        write_state(state_path, state)

    logging.info("Combining %d processed segments", len(encoded_segments))
    concatenate_videos(encoded_segments, output, work_dir / "concat_list.txt")
    state["finished"] = True
    write_state(state_path, state)
    return work_dir


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    require_valid_environment()
    ensure_directories(INPUT_DIR, OUTPUT_DIR, TEMP_DIR, MODELS_DIR)
    source = resolve_input(args.input)
    output = (args.output or OUTPUT_DIR / f"{source.stem}_upscaled.mp4").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = False
    work_dir: Path | None = None
    try:
        work_dir = process_segments(
            source, output, args.segment_seconds, args.model.resolve(), args.tile, args.scale, args.resume,
        )
        completed = True
        logging.info("Done: %s", output)
    finally:
        if completed and not args.keep_temp and work_dir:
            reset_directory(work_dir)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        logging.error("%s", error)
        raise SystemExit(1) from error
    except KeyboardInterrupt:
        logging.warning("Stopped. Run the same command with --resume to continue from the last completed segment.")
        raise SystemExit(130)
