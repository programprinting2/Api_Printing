import math
import os
import tempfile
import uuid
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

CM_TO_PT = 72.0 / 2.54
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "printing_agent_uploads")
OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "printing_agent_cmyk")


def _safe_float(value, default=0.0):
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value)
    except (TypeError, ValueError):
        return default


def _hex_to_cmyk_color(hex_color):
    hex_color = str(hex_color or "#000000").strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(ch * 2 for ch in hex_color)
    if len(hex_color) != 6:
        return colors.CMYKColor(0, 0, 0, 1)

    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    k = 1.0 - max(r, g, b)
    if k >= 1.0:
        return colors.CMYKColor(0, 0, 0, 1)
    c = (1.0 - r - k) / (1.0 - k)
    m = (1.0 - g - k) / (1.0 - k)
    y = (1.0 - b - k) / (1.0 - k)
    return colors.CMYKColor(c, m, y, k)


def _y_pt(y_cm, page_h_cm):
    return (page_h_cm - y_cm) * CM_TO_PT


def _stroke_pt(stroke_width):
    return max(0.25, _safe_float(stroke_width, 1.0) * CM_TO_PT / 10.0)


def _resolve_path(path):
    if not path:
        return None
    normalized = os.path.abspath(path.replace("/", os.sep))
    if os.path.isfile(normalized):
        return normalized
    return None


def _draw_image_object(c, obj, page_h_cm):
    path = _resolve_path(obj.get("originalPath"))
    x_cm = _safe_float(obj.get("x_cm"))
    y_cm = _safe_float(obj.get("y_cm"))
    w_cm = _safe_float(obj.get("w_cm"))
    h_cm = _safe_float(obj.get("h_cm"))
    x_pt = x_cm * CM_TO_PT
    y_pt = _y_pt(y_cm + h_cm, page_h_cm)
    w_pt = w_cm * CM_TO_PT
    h_pt = h_cm * CM_TO_PT

    if not path:
        return

    obj_type = obj.get("type", "image")
    if obj_type == "pdf_page" and PYMUPDF_AVAILABLE:
        page_num = max(1, int(obj.get("page_num") or 1))
        doc = fitz.open(path)
        try:
            page_index = min(page_num - 1, len(doc) - 1)
            page = doc[page_index]
            pix = page.get_pixmap(alpha=False)
            tmp_path = os.path.join(
                tempfile.gettempdir(),
                f"render_cmyk_pdf_{uuid.uuid4().hex}.png",
            )
            pix.save(tmp_path)
            c.drawImage(
                ImageReader(tmp_path),
                x_pt,
                y_pt,
                width=w_pt,
                height=h_pt,
                preserveAspectRatio=True,
                mask="auto",
            )
        finally:
            doc.close()
        return

    if PIL_AVAILABLE:
        c.drawImage(
            ImageReader(path),
            x_pt,
            y_pt,
            width=w_pt,
            height=h_pt,
            preserveAspectRatio=True,
            mask="auto",
        )


def _draw_object(c, obj, page_h_cm):
    if not obj or obj.get("visible") is False:
        return

    obj_type = obj.get("type")
    stroke = _hex_to_cmyk_color(obj.get("color"))
    fill = _hex_to_cmyk_color(obj.get("fillColor") or obj.get("color"))
    stroke_w = _stroke_pt(obj.get("strokeWidth", 1))
    rotation = _safe_float(obj.get("rotation"))

    c.setStrokeColor(stroke)
    c.setFillColor(fill)
    c.setLineWidth(stroke_w)

    if obj_type in ("image", "pdf_page"):
        _draw_image_object(c, obj, page_h_cm)
        return

    if obj_type == "rect":
        x_cm = _safe_float(obj.get("x_cm"))
        y_cm = _safe_float(obj.get("y_cm"))
        w_cm = _safe_float(obj.get("w_cm"))
        h_cm = _safe_float(obj.get("h_cm"))
        x_pt = x_cm * CM_TO_PT
        y_pt = _y_pt(y_cm + h_cm, page_h_cm)
        w_pt = w_cm * CM_TO_PT
        h_pt = h_cm * CM_TO_PT
        if obj.get("fill"):
            c.rect(x_pt, y_pt, w_pt, h_pt, stroke=1, fill=1)
        else:
            c.rect(x_pt, y_pt, w_pt, h_pt, stroke=1, fill=0)
        return

    if obj_type == "triangle":
        x_cm = _safe_float(obj.get("x_cm"))
        y_cm = _safe_float(obj.get("y_cm"))
        w_cm = _safe_float(obj.get("w_cm"))
        h_cm = _safe_float(obj.get("h_cm"))
        apex_down = bool(obj.get("apexDown"))
        if apex_down:
            points = [
                (x_cm, y_cm),
                (x_cm + w_cm, y_cm),
                (x_cm + w_cm / 2.0, y_cm + h_cm),
            ]
        else:
            points = [
                (x_cm + w_cm / 2.0, y_cm),
                (x_cm, y_cm + h_cm),
                (x_cm + w_cm, y_cm + h_cm),
            ]
        path = c.beginPath()
        path.moveTo(points[0][0] * CM_TO_PT, _y_pt(points[0][1], page_h_cm))
        path.lineTo(points[1][0] * CM_TO_PT, _y_pt(points[1][1], page_h_cm))
        path.lineTo(points[2][0] * CM_TO_PT, _y_pt(points[2][1], page_h_cm))
        path.close()
        c.drawPath(path, stroke=1, fill=1 if obj.get("fill") else 0)
        return

    if obj_type == "circle":
        cx_cm = _safe_float(obj.get("cx_cm"))
        cy_cm = _safe_float(obj.get("cy_cm"))
        rx_cm = _safe_float(obj.get("rx_cm"))
        ry_cm = _safe_float(obj.get("ry_cm"))
        cx_pt = cx_cm * CM_TO_PT
        cy_pt = _y_pt(cy_cm, page_h_cm)
        rx_pt = rx_cm * CM_TO_PT
        ry_pt = ry_cm * CM_TO_PT
        c.ellipse(
            cx_pt - rx_pt,
            cy_pt - ry_pt,
            cx_pt + rx_pt,
            cy_pt + ry_pt,
            stroke=1,
            fill=1 if obj.get("fill") else 0,
        )
        return

    if obj_type in ("line", "dimension"):
        x1_pt = _safe_float(obj.get("x1_cm")) * CM_TO_PT
        y1_pt = _y_pt(_safe_float(obj.get("y1_cm")), page_h_cm)
        x2_pt = _safe_float(obj.get("x2_cm")) * CM_TO_PT
        y2_pt = _y_pt(_safe_float(obj.get("y2_cm")), page_h_cm)
        c.line(x1_pt, y1_pt, x2_pt, y2_pt)
        return

    if obj_type == "pencil":
        points = obj.get("points_cm") or []
        if len(points) < 2:
            return
        path = c.beginPath()
        path.moveTo(
            _safe_float(points[0].get("x")) * CM_TO_PT,
            _y_pt(_safe_float(points[0].get("y")), page_h_cm),
        )
        for point in points[1:]:
            path.lineTo(
                _safe_float(point.get("x")) * CM_TO_PT,
                _y_pt(_safe_float(point.get("y")), page_h_cm),
            )
        if obj.get("closed"):
            path.close()
            c.drawPath(path, stroke=1, fill=1 if obj.get("fill") else 0)
        else:
            c.drawPath(path, stroke=1, fill=0)
        return

    if obj_type == "text":
        text = str(obj.get("text") or "")
        if not text:
            return
        x_pt = _safe_float(obj.get("x_cm")) * CM_TO_PT
        y_pt = _y_pt(_safe_float(obj.get("y_cm")), page_h_cm)
        font_size_pt = max(4.0, _safe_float(obj.get("fontSize_cm")) * CM_TO_PT)
        font_name = "Helvetica"
        family = str(obj.get("fontFamily") or "").lower()
        if "times" in family or "serif" in family:
            font_name = "Times-Roman"
        elif "courier" in family or "mono" in family:
            font_name = "Courier"
        c.setFont(font_name, font_size_pt)
        if rotation:
            c.saveState()
            c.translate(x_pt, y_pt)
            c.rotate(-rotation)
            c.drawString(0, -font_size_pt, text)
            c.restoreState()
        else:
            c.drawString(x_pt, y_pt - font_size_pt, text)


def render_cmyk(payload: dict):
    if not isinstance(payload, dict):
        return {"status": "error", "message": "Invalid JSON body"}

    page = payload.get("page") or {}
    page_w_cm = max(_safe_float(page.get("w_cm"), 21.0), 1.0)
    page_h_cm = max(_safe_float(page.get("h_cm"), 29.7), 1.0)
    objects = payload.get("objects") or []
    if not objects:
        return {"status": "error", "message": "Tidak ada objek untuk dirender"}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"draftcalc_cmyk_{stamp}_{uuid.uuid4().hex[:8]}.pdf")
    page_size = (page_w_cm * CM_TO_PT, page_h_cm * CM_TO_PT)

    c = canvas.Canvas(output_path, pagesize=page_size)
    c.setPageCompression(0)

    for obj in objects:
        try:
            _draw_object(c, obj, page_h_cm)
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Gagal merender objek {obj.get('type', 'unknown')}: {exc}",
            }

    c.showPage()
    c.save()

    return {"status": "success", "output_path": output_path, "output_format": "pdf"}
