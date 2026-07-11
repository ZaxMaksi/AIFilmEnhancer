"""Small shared helpers."""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


def ensure_directories(*directories: Path) -> None:
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def reset_directory(directory: Path) -> None:
    """Remove previous temporary contents while retaining the directory."""
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)


def require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"'{name}' was not found in PATH. Install FFmpeg and restart the terminal.")


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    logging.debug("Running: %s", " ".join(command))
    try:
        return subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        details = error.stderr.strip() or error.stdout.strip()
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{details}") from error
