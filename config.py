import os

AGENT_ID = "PC-01"
AGENT_SECRET = "supersecretkey"

# BASE_ALLOWED_PATH = r"F:\\"
BASE_ALLOWED_PATH = r"C:\\"

SERVER_URL = "http://192.168.1.20:8000"

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CMYK_ICC_PROFILE = os.path.join(_BASE_DIR, "profiles", "JapanColor2001Coated.icc")
# perceptual | relative_colorimetric | saturation | absolute_colorimetric
CMYK_RENDERING_INTENT = "relative_colorimetric"
