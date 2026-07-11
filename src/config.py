"""Project paths and processing defaults."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"
MODELS_DIR = PROJECT_ROOT / "models"

DEFAULT_MODEL = MODELS_DIR / "RealESRGAN_x4plus.pth"
DEFAULT_OUTPUT_SCALE = 2.0
DEFAULT_SEGMENT_SECONDS = 300
FRAME_NAME = "frame_%08d.png"
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}
