"""Fail-fast environment check for the Video Enhancer project."""

import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def report(label: str, value: object) -> None:
    print(f"{label}: {value}")


def main() -> int:
    report("Python version", platform.python_version())
    if sys.version_info[:2] != (3, 12):
        report("Environment status", "FAILED (Python 3.12 is required)")
        return 1

    try:
        import torch
    except ImportError as error:
        report("PyTorch", f"FAILED ({error})")
        return 1

    report("PyTorch version", torch.__version__)
    cuda_available = torch.cuda.is_available()
    report("CUDA available", cuda_available)
    report("CUDA device", torch.cuda.get_device_name(0) if cuda_available else "not available")

    try:
        import cv2
        report("OpenCV version", cv2.__version__)
    except ImportError as error:
        report("OpenCV", f"FAILED ({error})")
        return 1

    try:
        from compat import prepare_basicsr_compatibility

        prepare_basicsr_compatibility()
        from realesrgan import RealESRGANer  # noqa: F401
        report("Real-ESRGAN import", "SUCCESS")
    except Exception as error:  # Import may fail inside BasicSR.
        report("Real-ESRGAN import", f"FAILED ({type(error).__name__}: {error})")
        return 1

    report("Environment status", "SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
