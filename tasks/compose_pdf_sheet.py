"""Compose two PDF files onto a single sheet using PyMuPDF."""

import os
import fitz

CM2PT = 28.3465


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
        return (r / 255.0, g / 255.0, b / 255.0)
    return (0, 0, 0)


def run(data):
    file1 = data.get("file1")
    file2 = data.get("file2")
    output = data.get("output")

    if not file1 or not file2 or not output:
        return {"status": "error", "message": "Missing parameter (file1, file2, output)"}

    sheet_w = _safe_float(data.get("sheet_w"), 32.5) * CM2PT
    sheet_h = _safe_float(data.get("sheet_h"), 96) * CM2PT

    x1 = _safe_float(data.get("x1"), 0) * CM2PT
    y1 = _safe_float(data.get("y1"), 0) * CM2PT
    x2 = _safe_float(data.get("x2"), 0) * CM2PT
    y2 = _safe_float(data.get("y2"), 0) * CM2PT

    rot1 = int(_safe_float(data.get("rot1"), 0))
    rot2 = int(_safe_float(data.get("rot2"), 0))

    try:
        src1 = fitz.open(file1)
        src2 = fitz.open(file2)

        p1 = src1[0]
        p2 = src2[0]

        r1 = p1.rect
        r2 = p2.rect

        if rot1 in (90, 270):
            w1, h1 = r1.height, r1.width
        else:
            w1, h1 = r1.width, r1.height

        if rot2 in (90, 270):
            w2, h2 = r2.height, r2.width
        else:
            w2, h2 = r2.width, r2.height

        doc = fitz.open()
        page = doc.new_page(width=sheet_w, height=sheet_h)

        target1 = fitz.Rect(x1, y1, x1 + w1, y1 + h1)
        page.show_pdf_page(target1, src1, 0, rotate=rot1)

        target2 = fitz.Rect(x2, y2, x2 + w2, y2 + h2)
        page.show_pdf_page(target2, src2, 0, rotate=rot2)

        # Cut line
        if data.get("cut_line"):
            cl_width = _safe_float(data.get("cut_line_width"), 0.5)
            cl_color = _hex_to_rgb(data.get("cut_line_color", "#000000"))
            cl_style = data.get("cut_line_style", "dashed")
            cl_dir = data.get("cut_line_dir", "auto")
            cl_extend = _safe_float(data.get("cut_line_extend"), 1) * CM2PT

            if cl_dir == "auto":
                if abs(y2 - (y1 + h1)) < abs(x2 - (x1 + w1)):
                    cl_dir = "horizontal"
                else:
                    cl_dir = "vertical"

            dashes = None
            if cl_style == "dashed":
                dashes = "[4 2] 0"
            elif cl_style == "dotted":
                dashes = "[1 2] 0"
            elif cl_style == "dash-dot":
                dashes = "[4 1.5 1 1.5] 0"

            shape = page.new_shape()
            if cl_dir == "horizontal":
                center_y = (y1 + h1 + y2) / 2
                shape.draw_line(
                    fitz.Point(-cl_extend, center_y),
                    fitz.Point(sheet_w + cl_extend, center_y),
                )
            else:
                center_x = (x1 + w1 + x2) / 2
                shape.draw_line(
                    fitz.Point(center_x, -cl_extend),
                    fitz.Point(center_x, sheet_h + cl_extend),
                )

            shape.finish(color=cl_color, width=cl_width, dashes=dashes)
            shape.commit()

        doc.save(output)
        doc.close()
        src1.close()
        src2.close()

        info = {
            "status": "success",
            "output": output,
            "sheet_cm": [round(sheet_w / CM2PT, 2), round(sheet_h / CM2PT, 2)],
            "file1_cm": [round(w1 / CM2PT, 2), round(h1 / CM2PT, 2)],
            "file2_cm": [round(w2 / CM2PT, 2), round(h2 / CM2PT, 2)],
        }
        return info

    except Exception as e:
        return {"status": "error", "message": str(e)}
