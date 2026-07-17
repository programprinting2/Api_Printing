import os

from PIL import Image

from tasks.color_management import sample_cmyk_percent
from tasks.image_processing import process_image, processing_requested, safe_float, safe_int


def _placement_pixels(p, dpi):
    px_per_cm = dpi / 2.54
    return {
        "x": int(safe_float(p.get("x_cm"), 0) * px_per_cm),
        "y": int(safe_float(p.get("y_cm"), 0) * px_per_cm),
        "w": max(1, int(safe_float(p.get("w_cm"), 1) * px_per_cm)),
        "h": max(1, int(safe_float(p.get("h_cm"), 1) * px_per_cm)),
        "rotation": safe_float(p.get("rotation"), 0),
    }


def build_cmyk_composite(param: dict):
    """Paste CMYK master tiles onto a page-sized CMYK canvas from placement list."""
    master_path = param.get("master_path") or param.get("AlamatFile")
    placements = param.get("placements") or []
    page = param.get("page") or {}

    if not master_path:
        return {"status": "error", "message": "master_path is required"}
    if len(placements) < 2:
        return {"status": "error", "message": "placements requires at least 2 items"}
    if not os.path.exists(master_path):
        return {"status": "error", "message": "Master file not found"}

    dpi = safe_int(param.get("dpi", 300), 300)
    page_w_cm = safe_float(page.get("w_cm"), 21)
    page_h_cm = safe_float(page.get("h_cm"), 29.7)
    px_per_cm = dpi / 2.54
    page_w = max(1, int(page_w_cm * px_per_cm))
    page_h = max(1, int(page_h_cm * px_per_cm))

    with Image.open(master_path) as probe:
        if probe.mode != "CMYK":
            return {
                "status": "error",
                "message": f"Master bukan CMYK (mode={probe.mode}). Gunakan pipeline RGB.",
            }
        source_icc = probe.info.get("icc_profile")

    master = Image.open(master_path)
    canvas = Image.new("CMYK", (page_w, page_h), (0, 0, 0, 0))

    for placement in placements:
        pp = _placement_pixels(placement, dpi)
        tile = master.copy()
        if tile.size != (pp["w"], pp["h"]):
            tile = tile.resize((pp["w"], pp["h"]), Image.LANCZOS)
        rot = pp["rotation"]
        if rot:
            tile = tile.rotate(-rot, expand=True, resample=Image.BICUBIC)
        canvas.paste(tile, (pp["x"], pp["y"]))

    master.close()

    base_name = os.path.splitext(os.path.basename(master_path))[0]
    composite_path = os.path.join(os.path.dirname(master_path), f"{base_name}_composite.jpeg")
    save_kwargs = {"dpi": (dpi, dpi), "quality": 98, "subsampling": 0}
    if source_icc:
        save_kwargs["icc_profile"] = source_icc
    canvas.save(composite_path, **save_kwargs)
    canvas.close()

    return composite_path, len(placements), source_icc


def export_cmyk_composite(param: dict):
    if not isinstance(param, dict):
        return {"status": "error", "message": "Invalid JSON body"}

    built = build_cmyk_composite(param)
    if isinstance(built, dict):
        return built

    composite_path, placement_count, _source_icc = built

    payload = dict(param)
    payload["AlamatFile"] = composite_path
    payload["master_path"] = composite_path
    payload["output_cmyk"] = True
    payload["force_cmyk_master"] = True
    payload["preserve_original_cmyk"] = False
    payload.pop("placements", None)

    if not processing_requested(payload):
        sample = sample_cmyk_percent(composite_path)
        return {
            "status": "success",
            "output_path": composite_path,
            "color_mode": "CMYK",
            "pipeline": "cmyk_composite",
            "placement_count": placement_count,
            "passthrough": False,
            "export_method": "cmyk_composite",
            "sample_cmyk": sample,
        }

    result = process_image(payload)
    if isinstance(result, dict):
        result["pipeline"] = "cmyk_composite"
        result["placement_count"] = placement_count
    return result
