"""Export PDF imposition sheet(s) preserving CMYK via Pillow + ReportLab."""

import io
import os
import uuid
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

try:
    import fitz

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from tasks.color_management import convert_rgb_to_cmyk, load_icc_bytes

MM_PER_IN = 25.4
PAPER_WHITE_CMYK = (0, 0, 0, 0)


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _mm_to_px(mm: float, dpi: int) -> int:
    return max(1, int(round(mm * dpi / MM_PER_IN)))


def _render_slot_page(
    pdf_path: str,
    page_num: int,
    target_w: int,
    target_h: int,
    slot_rot: int,
    flip_h: bool,
    flip_v: bool,
    page_rotate: int,
    dpi: int,
) -> Optional[Image.Image]:
    if not PYMUPDF_AVAILABLE or not page_num or target_w <= 0 or target_h <= 0:
        return None

    doc = fitz.open(pdf_path)
    try:
        idx = max(0, min(page_num - 1, len(doc) - 1))
        page = doc[idx]
        base_rot = ((page.rotation or 0) + (page_rotate or 0)) % 360
        rect = page.rect
        if rect.width <= 0 or rect.height <= 0:
            return None

        zoom = max(target_w / rect.width, target_h / rect.height)
        mat = fitz.Matrix(zoom, zoom)
        if base_rot:
            mat = mat.prerotate(int(base_rot))
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = convert_rgb_to_cmyk(img)

        if flip_h:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_v:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)

        rot = ((slot_rot or 0) % 360 + 360) % 360
        if rot == 90:
            img = img.transpose(Image.ROTATE_270)
        elif rot == 180:
            img = img.transpose(Image.ROTATE_180)
        elif rot == 270:
            img = img.transpose(Image.ROTATE_90)

        resample = Image.LANCZOS
        if img.width != target_w or img.height != target_h:
            img = img.resize((target_w, target_h), resample)
        return img
    finally:
        doc.close()


def _draw_trim_marks(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, length: int):
    L = max(6, min(length, int(min(w, h) * 0.12)))
    pink = (0, 80, 60, 0)
    draw.line([(x, y + L), (x, y), (x + L, y)], fill=pink, width=1)
    draw.line([(x + w - L, y), (x + w, y), (x + w, y + L)], fill=pink, width=1)
    draw.line([(x + w, y + h - L), (x + w, y + h), (x + w - L, y + h)], fill=pink, width=1)
    draw.line([(x + L, y + h), (x, y + h), (x, y + h - L)], fill=pink, width=1)


def _draw_bleed_mark(draw: ImageDraw.ImageDraw, r: dict, dpi: int):
    x = _mm_to_px(_safe_float(r.get("x_mm")), dpi)
    y = _mm_to_px(_safe_float(r.get("y_mm")), dpi)
    w = _mm_to_px(_safe_float(r.get("w_mm")), dpi)
    h = _mm_to_px(_safe_float(r.get("h_mm")), dpi)
    bl = _mm_to_px(_safe_float(r.get("bleed_l_mm")), dpi)
    bt = _mm_to_px(_safe_float(r.get("bleed_t_mm")), dpi)
    br = _mm_to_px(_safe_float(r.get("bleed_r_mm")), dpi)
    bb = _mm_to_px(_safe_float(r.get("bleed_b_mm")), dpi)
    if bl + bt + br + bb <= 0:
        return
    orange = (0, 120, 255, 0)
    draw.rectangle(
        [int(x - bl), int(y - bt), int(x + w + br), int(y + h + bb)],
        outline=orange,
        width=1,
    )


def _draw_registration(draw: ImageDraw.ImageDraw, cx: int, cy: int, cw: int, ch: int):
    size = max(8, min(18, int(min(cw, ch) * 0.04)))
    pad = int(size * 0.6)
    black = (0, 0, 0, 255)
    spots = [
        (cx + pad, cy + pad),
        (cx + cw - pad, cy + pad),
        (cx + pad, cy + ch - pad),
        (cx + cw - pad, cy + ch - pad),
    ]
    for x, y in spots:
        draw.ellipse([x - size // 3, y - size // 3, x + size // 3, y + size // 3], outline=black, width=1)
        draw.line([x - size, y, x + size, y], fill=black, width=1)
        draw.line([x, y - size, x, y + size], fill=black, width=1)


def _draw_color_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int):
    bar_h = max(8, min(14, int(w * 0.02)))
    colors = [(0, 174, 239, 0), (236, 0, 140, 0), (255, 242, 0, 0), (0, 0, 0, 255)]
    seg = max(1, w // len(colors))
    for i, c in enumerate(colors):
        draw.rectangle([x + i * seg, y + 4, x + (i + 1) * seg, y + 4 + bar_h], fill=c, outline=(0, 0, 0, 255))


def _draw_gray_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int):
    bar_h = max(7, min(12, int(w * 0.018)))
    steps = 11
    seg = max(1, w // steps)
    for i in range(steps):
        g = int(round(i / max(1, steps - 1) * 255))
        draw.rectangle([x + i * seg, y + 4, x + (i + 1) * seg, y + 4 + bar_h], fill=(0, 0, 0, 255 - g))


def _draw_sheet_desc(draw: ImageDraw.ImageDraw, text: str, sw: int, sh: int):
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((6, sh - 16), text, fill=(0, 0, 0, 200), font=font)


def _draw_cutter_marks(draw: ImageDraw.ImageDraw, sw: int, sh: int):
    length = max(6, min(12, int(min(sw, sh) * 0.025)))
    black = (0, 0, 0, 255)
    mid_x, mid_y = sw // 2, sh // 2
    draw.line([0, mid_y, length, mid_y], fill=black, width=1)
    draw.line([sw - length, mid_y, sw, mid_y], fill=black, width=1)
    draw.line([mid_x, 0, mid_x, length], fill=black, width=1)
    draw.line([mid_x, sh - length, mid_x, sh], fill=black, width=1)


def _draw_number(draw: ImageDraw.ImageDraw, r: dict, dpi: int):
    page_num = r.get("page_num")
    if not page_num:
        return
    tx = _mm_to_px(_safe_float(r.get("trim_x_mm", r.get("x_mm"))), dpi)
    ty = _mm_to_px(_safe_float(r.get("trim_y_mm", r.get("y_mm"))), dpi)
    tw = _mm_to_px(_safe_float(r.get("trim_w_mm", r.get("w_mm"))), dpi)
    th = _mm_to_px(_safe_float(r.get("trim_h_mm", r.get("h_mm"))), dpi)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((int(tx + tw - 20), int(ty + th - 14)), str(page_num), fill=(0, 0, 0, 180), font=font)


def _apply_marks(canvas: Image.Image, sheet: dict, side: dict, marks: dict, dpi: int):
    if not marks or not marks.get("show"):
        return canvas

    draw = ImageDraw.Draw(canvas)
    sw, sh = canvas.size
    cx = _mm_to_px(_safe_float(sheet.get("cetak_x_mm")), dpi)
    cy = _mm_to_px(_safe_float(sheet.get("cetak_y_mm")), dpi)
    cw = _mm_to_px(_safe_float(sheet.get("cetak_width_mm")), dpi)
    ch = _mm_to_px(_safe_float(sheet.get("cetak_height_mm")), dpi)

    if marks.get("show"):
        blue = (255, 130, 74, 0)
        draw.rectangle([int(cx), int(cy), int(cx + cw), int(cy + ch)], outline=blue, width=1)

    for r in side.get("mark_rects") or []:
        if marks.get("trim"):
            tx = _mm_to_px(_safe_float(r.get("trim_x_mm", r.get("x_mm"))), dpi)
            ty = _mm_to_px(_safe_float(r.get("trim_y_mm", r.get("y_mm"))), dpi)
            tw = _mm_to_px(_safe_float(r.get("trim_w_mm", r.get("w_mm"))), dpi)
            th = _mm_to_px(_safe_float(r.get("trim_h_mm", r.get("h_mm"))), dpi)
            _draw_trim_marks(draw, tx, ty, tw, th, 14)
        if marks.get("bleed"):
            _draw_bleed_mark(draw, r, dpi)
        if marks.get("numbering"):
            _draw_number(draw, r, dpi)

    if marks.get("registration"):
        _draw_registration(draw, cx, cy, cw, ch)
    bar_y = cy + ch
    if marks.get("color_bar"):
        _draw_color_bar(draw, cx, bar_y, cw)
        bar_y += 18
    if marks.get("gray_bar"):
        _draw_gray_bar(draw, cx, bar_y, cw)
    if marks.get("sheet_description"):
        w_mm = _safe_float(sheet.get("width_mm"))
        h_mm = _safe_float(sheet.get("height_mm"))
        _draw_sheet_desc(draw, f"{w_mm:.1f} x {h_mm:.1f} mm", sw, sh)
    if marks.get("auto_cutters"):
        _draw_cutter_marks(draw, sw, sh)

    return canvas


def _build_side_canvas(
    pdf_path: str,
    sheet: dict,
    side: dict,
    marks: dict,
    dpi: int,
) -> Image.Image:
    sw = _mm_to_px(_safe_float(sheet.get("width_mm"), 210), dpi)
    sh = _mm_to_px(_safe_float(sheet.get("height_mm"), 297), dpi)
    canvas = Image.new("CMYK", (sw, sh), PAPER_WHITE_CMYK)

    for slot in side.get("slots") or []:
        page_num = _safe_int(slot.get("page_num"))
        x = _mm_to_px(_safe_float(slot.get("x_mm")), dpi)
        y = _mm_to_px(_safe_float(slot.get("y_mm")), dpi)
        w = _mm_to_px(_safe_float(slot.get("w_mm")), dpi)
        h = _mm_to_px(_safe_float(slot.get("h_mm")), dpi)
        tile = _render_slot_page(
            pdf_path,
            page_num,
            w,
            h,
            _safe_int(slot.get("rotation")),
            bool(slot.get("flip_h")),
            bool(slot.get("flip_v")),
            _safe_int(slot.get("page_rotate")),
            dpi,
        )
        if tile:
            canvas.paste(tile, (int(x), int(y)))

    _apply_marks(canvas, sheet, side, marks, dpi)
    return canvas


def _append_cmyk_page(pdf_canvas, pil_image: Image.Image, page_w_pt: float, page_h_pt: float):
    """Embed CMYK raster with proper DeviceCMYK metadata for Corel/prepress apps."""
    icc = load_icc_bytes()
    if icc and "icc_profile" not in pil_image.info:
        pil_image.info["icc_profile"] = icc
    pdf_canvas.setPageCompression(0)
    pdf_canvas.drawImage(
        ImageReader(pil_image),
        0,
        0,
        width=page_w_pt,
        height=page_h_pt,
        preserveAspectRatio=False,
        anchor="sw",
        mask=None,
    )
    pdf_canvas.showPage()


def export_pdf_imposition(param: dict):
    if not isinstance(param, dict):
        return {"status": "error", "message": "Invalid JSON body"}
    if not PYMUPDF_AVAILABLE:
        return {"status": "error", "message": "PyMuPDF tidak tersedia di agent."}

    source_pdf = param.get("source_pdf") or param.get("source_path")
    if not source_pdf or not os.path.isfile(source_pdf):
        return {"status": "error", "message": "source_pdf tidak ditemukan."}

    sheet = param.get("sheet") or {}
    sides = param.get("sides") or []
    if not sides:
        return {"status": "error", "message": "sides kosong."}

    marks = param.get("marks") or {}
    dpi = _safe_int(param.get("dpi"), 300)
    dpi = max(72, min(600, dpi))

    out_dir = os.path.join(os.path.dirname(source_pdf), "")
    base = os.path.splitext(os.path.basename(source_pdf))[0]
    output_path = param.get("output_path") or os.path.join(
        out_dir, f"{base}_imposition_{uuid.uuid4().hex[:8]}.pdf"
    )

    sheet_w_mm = _safe_float(sheet.get("width_mm"), 210)
    sheet_h_mm = _safe_float(sheet.get("height_mm"), 297)
    sheet_w_pt = float(sheet_w_mm * 72 / MM_PER_IN)
    sheet_h_pt = float(sheet_h_mm * 72 / MM_PER_IN)

    try:
        pdf = rl_canvas.Canvas(output_path, pagesize=(sheet_w_pt, sheet_h_pt))
        pdf.setPageCompression(0)
        for side in sides:
            pil_canvas = _build_side_canvas(source_pdf, sheet, side, marks, dpi)
            if pil_canvas.mode != "CMYK":
                pil_canvas = convert_rgb_to_cmyk(pil_canvas.convert("RGB"))
            _append_cmyk_page(pdf, pil_canvas, sheet_w_pt, sheet_h_pt)
        pdf.save()
        return {
            "status": "success",
            "output_path": output_path,
            "pipeline": "export_pdf_imposition",
            "dpi": dpi,
            "pages": len(sides),
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
