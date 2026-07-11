"""Frame upscaling with a local Real-ESRGAN model."""

import logging
from pathlib import Path
from typing import Any


def create_upscaler(model_path: Path, tile_size: int = 0) -> Any:
    """Create a Real-ESRGAN x4+ upscaler using a locally stored checkpoint."""
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Model not found: {model_path}. Place RealESRGAN_x4plus.pth in the models directory."
        )
    try:
        import torch
        from compat import prepare_basicsr_compatibility

        prepare_basicsr_compatibility()
        from realesrgan import RealESRGANer
        from realesrgan.archs.rrdbnet_arch import RRDBNet
    except ImportError as error:
        raise RuntimeError("Real-ESRGAN dependencies are missing. Run: python -m pip install -r requirements.txt") from error
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info("Real-ESRGAN device: %s", device.upper())
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    return RealESRGANer(
        scale=4,
        model_path=str(model_path),
        model=model,
        tile=tile_size,
        tile_pad=10,
        pre_pad=0,
        half=device == "cuda",
        device=device,
    )


def upscale_frames(input_dir: Path, output_dir: Path, upscaler: Any, outscale: float) -> None:
    """Upscale all PNG frames in lexical order."""
    import cv2

    frames = sorted(input_dir.glob("*.png"))
    if not frames:
        raise RuntimeError("No frames available for upscaling.")
    for index, frame_path in enumerate(frames, start=1):
        image = cv2.imread(str(frame_path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Could not read frame: {frame_path}")
        try:
            enhanced, _ = upscaler.enhance(image, outscale=outscale)
        except RuntimeError as error:
            raise RuntimeError(f"Real-ESRGAN failed on {frame_path.name}: {error}") from error
        destination = output_dir / frame_path.name
        if not cv2.imwrite(str(destination), enhanced):
            raise RuntimeError(f"Could not write frame: {destination}")
        if index == 1 or index % 25 == 0 or index == len(frames):
            logging.info("Upscaled %d/%d frames", index, len(frames))
