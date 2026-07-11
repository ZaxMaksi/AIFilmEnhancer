"""Encode processed image sequences and restore source audio."""

from pathlib import Path

from utils import require_executable, run_command
from video import has_audio


def encode_video(frames_dir: Path, frame_rate: str, source_video: Path, output_path: Path) -> None:
    """Create an H.264 MP4 and copy audio when the source contains it."""
    require_executable("ffmpeg")
    command = [
        "ffmpeg", "-y", "-framerate", frame_rate, "-i", str(frames_dir / "frame_%08d.png"),
        "-i", str(source_video), "-map", "0:v:0",
    ]
    if has_audio(source_video):
        command.extend(["-map", "1:a?", "-c:a", "copy"])
    command.extend(["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-shortest", str(output_path)])
    run_command(command)
