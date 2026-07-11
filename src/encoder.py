"""Encode processed image sequences and join video parts."""

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


def concatenate_videos(parts: list[Path], output_path: Path, list_file: Path) -> None:
    """Join identically encoded MP4 parts without re-encoding them."""
    if not parts:
        raise ValueError("No processed parts are available to concatenate.")

    def concat_entry(part: Path) -> str:
        escaped_path = part.resolve().as_posix().replace("'", r"'\''")
        return f"file '{escaped_path}'"

    list_file.write_text("\n".join(concat_entry(part) for part in parts) + "\n", encoding="utf-8")
    run_command([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", "-movflags", "+faststart", str(output_path),
    ])
