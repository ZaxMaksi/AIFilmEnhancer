"""Compatibility helpers for upstream third-party packages."""

import importlib.util
import sys
from types import ModuleType


def prepare_basicsr_compatibility() -> None:
    """Restore the torchvision module path expected by BasicSR 1.4.2.

    BasicSR imports ``rgb_to_grayscale`` from a torchvision module removed in
    torchvision 0.21. The function itself remains available at its current
    public location, so this exposes a narrow module alias before BasicSR is
    imported.
    """
    module_name = "torchvision.transforms.functional_tensor"
    if module_name in sys.modules or importlib.util.find_spec(module_name) is not None:
        return

    from torchvision.transforms.functional import rgb_to_grayscale

    compatibility_module = ModuleType(module_name)
    compatibility_module.rgb_to_grayscale = rgb_to_grayscale
    sys.modules[module_name] = compatibility_module
