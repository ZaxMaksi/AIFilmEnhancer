from types import ModuleType
import sys


def prepare_basicsr_compatibility():
    try:
        import torchvision.transforms.functional_tensor
        return
    except ModuleNotFoundError:
        pass

    from torchvision.transforms.functional import rgb_to_grayscale

    module = ModuleType("torchvision.transforms.functional_tensor")
    module.rgb_to_grayscale = rgb_to_grayscale

    sys.modules["torchvision.transforms.functional_tensor"] = module