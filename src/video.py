"""Video inspection and frame extraction via FFmpeg."""

import json
from pathlib import Path

from utils import require_executable, run_command


def get_frame_rate(video_path: Path) -> str:
    """Return the source frame rate as an FFmpeg-compatible rational string."""
    require_executable("ffprobe")
    result = run_command([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate", "-of", "json", str(video_path),
    ])
    streams = json.loads(result.stdout).get("streams", [])
    if not streams or not streams[0].get("r_frame_rate"):
        raise RuntimeError(f"No video stream found in {video_path}")
    return streams[0]["r_frame_rate"]


def has_audio(video_path: Path) -> bool:
    require_executable("ffprobe")
    result = run_command([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=index", "-of", "json", str(video_path),
    ])
    return bool(json.loads(result.stdout).get("streams"))


def extract_frames(video_path: Path, frames_dir: Path) -> str:
    """Extract lossless PNG frames and return the original frame rate."""
    require_executable("ffmpeg")
    frame_rate = get_frame_rate(video_path)
    run_command([
        "ffmpeg", "-y", "-i", str(video_path), "-map", "0:v:0", "-vsync", "0",
        str(frames_dir / "frame_%08d.png"),
    ])
    if not next(frames_dir.glob("*.png"), None):
        raise RuntimeError("FFmpeg did not extract any frames.")
    return frame_rate
