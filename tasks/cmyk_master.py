import os

from PIL import Image

from tasks.cmyk_composite import export_cmyk_composite
from tasks.image_processing import process_image, processing_requested


def export_cmyk_master(param: dict):
    if not isinstance(param, dict):
        return {"status": "error", "message": "Invalid JSON body"}

    placements = param.get("placements") or []
    if len(placements) >= 2:
        return export_cmyk_composite(param)

    filepath = param.get("master_path") or param.get("AlamatFile")
    if not filepath:
        return {"status": "error", "message": "master_path is required"}

    if not os.path.exists(filepath):
        return {"status": "error", "message": "Master file not found"}

    with Image.open(filepath) as probe:
        if probe.mode != "CMYK":
            return {
                "status": "error",
                "message": (
                    f"File master bukan CMYK (mode={probe.mode}). "
                    "Gunakan pipeline RGB biasa untuk file ini."
                ),
            }

    payload = dict(param)
    payload["AlamatFile"] = filepath
    payload["output_cmyk"] = True
    payload["force_cmyk_master"] = True

    if not processing_requested(payload):
        payload["preserve_original_cmyk"] = True

    result = process_image(payload)
    if isinstance(result, dict):
        result["pipeline"] = "cmyk_master"
    return result
