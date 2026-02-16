import os
from config import BASE_ALLOWED_PATH

def run(data):
    filepath = data.get("filepath")

    if not filepath:
        return {"status": "error", "message": "Missing filepath"}

    real = os.path.realpath(filepath)
    allowed = os.path.realpath(BASE_ALLOWED_PATH)

    if not os.path.commonpath([real, allowed]) == allowed:
        return {"status": "error", "message": "Path not allowed"}

    if not os.path.exists(real):
        return {"status": "error", "message": "File not found"}

    return {
        "status": "success",
        "filename": os.path.basename(real),
        "size_bytes": os.path.getsize(real)
    }