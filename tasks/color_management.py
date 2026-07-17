import os

from PIL import Image, ImageCms

try:
    from config import CMYK_ICC_PROFILE, CMYK_RENDERING_INTENT
except ImportError:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CMYK_ICC_PROFILE = os.path.join(_BASE, "profiles", "JapanColor2001Coated.icc")
    CMYK_RENDERING_INTENT = "perceptual"

_INTENT_MAP = {
    "perceptual": ImageCms.Intent.PERCEPTUAL,
    "relative_colorimetric": ImageCms.Intent.RELATIVE_COLORIMETRIC,
    "saturation": ImageCms.Intent.SATURATION,
    "absolute_colorimetric": ImageCms.Intent.ABSOLUTE_COLORIMETRIC,
}


def get_cmyk_icc_path():
    path = os.path.abspath(CMYK_ICC_PROFILE)
    if os.path.isfile(path):
        return path
    return None


def get_rendering_intent(name=None):
    key = (name or CMYK_RENDERING_INTENT or "perceptual").strip().lower()
    return _INTENT_MAP.get(key, ImageCms.Intent.PERCEPTUAL)


def load_icc_bytes(path=None):
    icc_path = path or get_cmyk_icc_path()
    if not icc_path:
        return None
    with open(icc_path, "rb") as handle:
        return handle.read()


def sample_cmyk_percent(filepath):
    try:
        with Image.open(filepath) as img:
            if img.mode != "CMYK":
                return None
            px = img.getpixel((img.width // 2, img.height // 2))
            return {
                "c": round(px[0] / 255 * 100),
                "m": round(px[1] / 255 * 100),
                "y": round(px[2] / 255 * 100),
                "k": round(px[3] / 255 * 100),
            }
    except Exception:
        return None


def file_sha256(filepath):
    import hashlib

    digest = hashlib.sha256()
    with open(filepath, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def convert_rgb_to_cmyk(img, icc_path=None, rendering_intent=None):
    if img.mode == "CMYK":
        return img

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    elif img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background

    profile_path = icc_path or get_cmyk_icc_path()
    if not profile_path:
        return img.convert("CMYK")

    srgb = ImageCms.createProfile("sRGB")
    cmyk_profile = ImageCms.getOpenProfile(profile_path)
    transform = ImageCms.buildTransform(
        srgb,
        cmyk_profile,
        "RGB",
        "CMYK",
        renderingIntent=get_rendering_intent(rendering_intent),
    )
    return ImageCms.applyTransform(img, transform)


def ensure_cmyk_output(img, param=None):
    param = param or {}
    if not param.get("output_cmyk", True):
        return img, None

    if img.mode == "CMYK":
        # Pertahankan ICC asli dari file sumber; jangan timpa profile Japan pada CMYK yang sudah ada.
        return img, img.info.get("icc_profile")

    intent = param.get("cmyk_rendering_intent")
    icc_path = param.get("cmyk_icc_profile") or get_cmyk_icc_path()
    converted = convert_rgb_to_cmyk(img, icc_path=icc_path, rendering_intent=intent)
    icc_bytes = load_icc_bytes(icc_path)
    return converted, icc_bytes
