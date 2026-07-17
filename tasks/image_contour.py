"""PNG cut-contour via OpenCV + periodic B-spline (scipy)."""

from __future__ import annotations

import base64
import io
import math
import re
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from scipy.interpolate import splprep, splev


def mask_from_alpha(img_rgba: np.ndarray) -> np.ndarray:
    alpha = img_rgba[:, :, 3]
    _, mask = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)
    return mask


def mask_from_bgcolor(img_rgb: np.ndarray, bg_hex: str, tolerance: int = 28) -> np.ndarray:
    r = int(bg_hex[1:3], 16)
    g = int(bg_hex[3:5], 16)
    b = int(bg_hex[5:7], 16)
    bg_color = np.array([r, g, b], dtype=np.float32)
    diff = np.abs(img_rgb.astype(np.float32) - bg_color)
    dist = np.max(diff, axis=2)
    return np.where(dist > tolerance, 255, 0).astype(np.uint8)


def auto_detect_bgcolor(img_rgb: np.ndarray) -> str:
    h, w = img_rgb.shape[:2]
    corners = [img_rgb[0, 0], img_rgb[0, w - 1], img_rgb[h - 1, 0], img_rgb[h - 1, w - 1]]
    avg = np.mean(corners, axis=0).astype(int)
    return "#{:02x}{:02x}{:02x}".format(int(avg[0]), int(avg[1]), int(avg[2]))


def pdf_to_png(pdf_bytes: bytes, dpi: float = 300.0) -> bytes:
    """Render halaman pertama PDF ke PNG RGBA pada DPI tertentu."""
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[0]
        pix = page.get_pixmap(dpi=int(round(dpi)), alpha=True)
        return pix.tobytes("png")
    finally:
        doc.close()


def read_dpi(pil_img: Image.Image, fallback: float = 300.0) -> float:
    dpi_info = pil_img.info.get("dpi")
    if dpi_info and isinstance(dpi_info, (tuple, list)) and dpi_info[0]:
        try:
            return float(dpi_info[0])
        except (TypeError, ValueError):
            pass
    return float(fallback)


def px_to_cm(px: float, dpi: float) -> float:
    return float(px) / float(dpi) * 2.54


def mm_to_px(mm: float, dpi: float) -> float:
    return float(mm) * float(dpi) / 25.4


# ─── Deteksi bentuk standar (circle / ellipse / rect / rounded-rect) ─────────
# Jika kontur cocok dengan bentuk geometris standar, pakai bentuk eksak
# (bezier presisi) — hasil tajam, bukan hasil tracing yang bergelombang.

KAPPA = 0.5522847498307936  # konstanta bezier untuk seperempat lingkaran


def _bezier_ellipse_path(cx: float, cy: float, rx: float, ry: float, ang: float = 0.0) -> str:
    """Ellipse/circle presisi sebagai 4 segmen cubic bezier (boleh dirotasi)."""
    k = KAPPA
    local = [
        (rx, 0), (rx, ry * k), (rx * k, ry), (0, ry),
        (-rx * k, ry), (-rx, ry * k), (-rx, 0),
        (-rx, -ry * k), (-rx * k, -ry), (0, -ry),
        (rx * k, -ry), (rx, -ry * k), (rx, 0),
    ]
    ca, sa = math.cos(ang), math.sin(ang)
    P = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in local]
    d = f"M{P[0][0]:.2f},{P[0][1]:.2f}"
    for i in range(0, 12, 3):
        c1, c2, e = P[i + 1], P[i + 2], P[i + 3]
        d += f" C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {e[0]:.2f},{e[1]:.2f}"
    return d + " Z"


def _rounded_rect_path(box: np.ndarray, r: float) -> str:
    """Rect (boleh dirotasi) dengan sudut membulat radius r sebagai path presisi."""
    if r < 0.5:
        p = box
        return (
            f"M{p[0][0]:.2f},{p[0][1]:.2f} L{p[1][0]:.2f},{p[1][1]:.2f}"
            f" L{p[2][0]:.2f},{p[2][1]:.2f} L{p[3][0]:.2f},{p[3][1]:.2f} Z"
        )
    k = KAPPA
    d = ""
    for i in range(4):
        C = box[i].astype(float)
        Pv = box[(i - 1) % 4].astype(float)
        Nv = box[(i + 1) % 4].astype(float)
        u_in = (Pv - C) / (np.linalg.norm(Pv - C) + 1e-9)
        u_out = (Nv - C) / (np.linalg.norm(Nv - C) + 1e-9)
        s = C + u_in * r
        e = C + u_out * r
        d += (f"M{s[0]:.2f},{s[1]:.2f}" if i == 0 else f" L{s[0]:.2f},{s[1]:.2f}")
        c1 = s + (C - s) * k
        c2 = e + (C - e) * k
        d += f" C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {e[0]:.2f},{e[1]:.2f}"
    return d + " Z"


def _sample_ellipse(cx, cy, rx, ry, ang, n=180) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ca, sa = math.cos(ang), math.sin(ang)
    x = cx + rx * np.cos(t) * ca - ry * np.sin(t) * sa
    y = cy + rx * np.cos(t) * sa + ry * np.sin(t) * ca
    return np.stack([x, y], axis=1)


def _sample_rounded_rect(box: np.ndarray, r: float, n_arc: int = 14) -> np.ndarray:
    if r < 0.5:
        return box.astype(float)
    out = []
    for i in range(4):
        C = box[i].astype(float)
        Pv = box[(i - 1) % 4].astype(float)
        Nv = box[(i + 1) % 4].astype(float)
        u_in = (Pv - C) / (np.linalg.norm(Pv - C) + 1e-9)
        u_out = (Nv - C) / (np.linalg.norm(Nv - C) + 1e-9)
        s = C + u_in * r
        e = C + u_out * r
        O = C + u_in * r + u_out * r  # pusat busur sudut
        a0 = math.atan2(s[1] - O[1], s[0] - O[0])
        a1 = math.atan2(e[1] - O[1], e[0] - O[0])
        # ambil arah putar terpendek (sudut 90°)
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for t in np.linspace(0, 1, n_arc):
            a = a0 + da * t
            out.append([O[0] + r * math.cos(a), O[1] + r * math.sin(a)])
    return np.array(out)


def detect_standard_shape(cnt_scaled: np.ndarray):
    """Cek apakah kontur cocok bentuk standar. Return dict info bentuk atau None."""
    pts = cnt_scaled.reshape(-1, 2).astype(np.float32)
    if len(pts) < 20:
        return None
    A = cv2.contourArea(pts)
    if A <= 0:
        return None
    bx, by, bw, bh = cv2.boundingRect(pts)
    diag = math.sqrt(bw * bw + bh * bh)
    tol_mean = 0.006 * diag
    tol_max = 0.02 * diag

    step = max(1, len(pts) // 200)
    test_pts = pts[::step]

    def deviation(candidate: np.ndarray):
        cand = candidate.astype(np.float32).reshape(-1, 1, 2)
        ds = [
            abs(cv2.pointPolygonTest(cand, (float(x), float(y)), True))
            for x, y in test_pts
        ]
        return float(np.mean(ds)), float(np.max(ds))

    # ── Circle ──
    M = cv2.moments(pts)
    if M["m00"] > 0:
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
        dists = np.linalg.norm(pts - np.array([cx, cy]), axis=1)
        rad = float(np.mean(dists))
        if rad > 3:
            dev = np.abs(dists - rad)
            if float(np.mean(dev)) < 0.01 * rad and float(np.max(dev)) < 0.035 * rad:
                return {"type": "circle", "cx": cx, "cy": cy, "r": rad}

    # ── Ellipse ──
    if len(pts) >= 5:
        try:
            (ecx, ecy), (MA, ma), ang_deg = cv2.fitEllipse(pts)
            if MA > 6 and ma > 6:
                ang = math.radians(ang_deg)
                cand = _sample_ellipse(ecx, ecy, MA / 2, ma / 2, ang, n=180)
                m, mx = deviation(cand)
                if m < tol_mean and mx < tol_max:
                    return {
                        "type": "ellipse", "cx": ecx, "cy": ecy,
                        "rx": MA / 2, "ry": ma / 2, "angle": ang,
                    }
        except cv2.error:
            pass

    # ── Rect / Rounded-rect (boleh dirotasi) ──
    rrect = cv2.minAreaRect(pts)
    (rcx, rcy), (rw, rh), _rang = rrect
    if rw > 4 and rh > 4:
        rect_area = rw * rh
        ratio = A / rect_area
        box = cv2.boxPoints(rrect)
        if ratio > 0.985:
            m, mx = deviation(box)
            if m < tol_mean and mx < tol_max:
                return {"type": "rrect", "box": box, "r": 0.0}
        if 0.80 < ratio <= 0.995:
            # estimasi radius sudut dari defisit luas: A_rect - A = (4-π)·r²
            r_est = math.sqrt(max(0.0, rect_area - A) / (4 - math.pi))
            if 0.5 < r_est <= min(rw, rh) / 2 + 1:
                cand = _sample_rounded_rect(box, r_est)
                m, mx = deviation(cand)
                if m < tol_mean and mx < tol_max:
                    return {"type": "rrect", "box": box, "r": r_est}
    return None


def shape_to_svg_path(shape: dict) -> str:
    if shape["type"] == "circle":
        return _bezier_ellipse_path(shape["cx"], shape["cy"], shape["r"], shape["r"])
    if shape["type"] == "ellipse":
        return _bezier_ellipse_path(
            shape["cx"], shape["cy"], shape["rx"], shape["ry"], shape["angle"]
        )
    return _rounded_rect_path(shape["box"], shape["r"])


def shape_sample_points(shape: dict, n: int = 160) -> list[list[float]]:
    if shape["type"] == "circle":
        pts = _sample_ellipse(shape["cx"], shape["cy"], shape["r"], shape["r"], 0.0, n=n)
    elif shape["type"] == "ellipse":
        pts = _sample_ellipse(
            shape["cx"], shape["cy"], shape["rx"], shape["ry"], shape["angle"], n=n
        )
    else:
        pts = _sample_rounded_rect(shape["box"], shape["r"], n_arc=max(8, n // 8))
    return [[round(float(x), 2), round(float(y), 2)] for x, y in pts]


def fit_bspline(contour_pts: np.ndarray, smoothing: float = 5000.0):
    pts = contour_pts.reshape(-1, 2).astype(float)
    n = len(pts)
    step = max(1, n // 600)
    pts_ds = pts[::step]
    x = np.append(pts_ds[:, 0], pts_ds[0, 0])
    y = np.append(pts_ds[:, 1], pts_ds[0, 1])
    # Skala smoothing per kontur: s pada splprep adalah toleransi absolut
    # (jumlah kuadrat residual). Nilai global yang cocok untuk kontur besar akan
    # menghancurkan kontur kecil — normalisasi terhadap jumlah titik agar
    # sheet berisi banyak objek kecil tetap akurat.
    s_eff = smoothing * (len(pts_ds) / 600.0)
    k = 3 if len(pts_ds) > 5 else 1
    try:
        tck, _ = splprep([x, y], s=s_eff, per=True, k=k)
        return tck
    except Exception:
        tck, _ = splprep([x, y], s=s_eff * 5, per=True, k=k)
        return tck


def spline_to_svg_path(tck, n_segments: int = 200) -> str:
    u_eval = np.linspace(0, 1, n_segments, endpoint=False)
    pts = np.array(splev(u_eval, tck)).T
    d1 = np.array(splev(u_eval, tck, der=1)).T
    n = len(pts)
    dt = 1.0 / n
    path = f"M{pts[0, 0]:.2f},{pts[0, 1]:.2f}"
    seg = 4
    for i in range(0, n, seg):
        j = (i + seg) % n
        p0, p1 = pts[i], pts[j]
        t0, t1 = d1[i], d1[j]
        c1 = p0 + t0 * (seg * dt / 3)
        c2 = p1 - t1 * (seg * dt / 3)
        path += (
            f" C{c1[0]:.2f},{c1[1]:.2f}"
            f" {c2[0]:.2f},{c2[1]:.2f}"
            f" {p1[0]:.2f},{p1[1]:.2f}"
        )
    path += " Z"
    return path


def spline_sample_points(tck, n_segments: int = 200) -> list[list[float]]:
    u_eval = np.linspace(0, 1, n_segments, endpoint=False)
    pts = np.array(splev(u_eval, tck)).T
    return [[round(float(x), 2), round(float(y), 2)] for x, y in pts]


def build_svg(
    width: int,
    height: int,
    paths: list[str],
    color: str = "#ff00c8",
    stroke_width: float = 1.5,
    curve_points: Optional[list[list[list[float]]]] = None,
    show_points: bool = False,
) -> str:
    path_elements = "\n    ".join(
        f'<path d="{d}" fill="none" stroke="{color}" '
        f'stroke-width="{stroke_width}" stroke-linejoin="round" stroke-linecap="round"/>'
        for d in paths
    )
    points_svg = ""
    if show_points and curve_points:
        dots = []
        r = max(1.2, stroke_width * 0.9)
        for loop in curve_points:
            for x, y in loop:
                dots.append(
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{color}" fill-opacity="0.85"/>'
                )
        points_svg = "\n    " + "\n    ".join(dots) if dots else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
        f'  <g id="CutContour">\n    {path_elements}{points_svg}\n  </g>\n</svg>'
    )


def build_svg_export(
    width: int,
    height: int,
    paths: list[str],
    source_png: bytes,
    *,
    image_x: float = 0.0,
    image_y: float = 0.0,
    image_w: int,
    image_h: int,
    color: str = "#ff00c8",
    stroke_width: float = 1.5,
    pt_scale: float = 1.0,
) -> str:
    """SVG with Artwork image and CutContour paths as separate groups (not flattened).

    pt_scale = 72/dpi: atribut width/height ditulis dalam point supaya ukuran
    fisik saat diimpor (Corel/Illustrator) sama dengan aslinya.
    """
    b64 = base64.b64encode(source_png).decode("ascii")
    path_elements = "\n    ".join(
        f'<path d="{d}" fill="none" stroke="{color}" '
        f'stroke-width="{stroke_width}" stroke-linejoin="round" stroke-linecap="round"/>'
        for d in paths
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width * pt_scale:.2f}pt" height="{height * pt_scale:.2f}pt">\n'
        f'  <g id="Artwork">\n'
        f'    <image x="{image_x:.2f}" y="{image_y:.2f}" '
        f'width="{image_w}" height="{image_h}" '
        f'href="data:image/png;base64,{b64}" '
        f'xlink:href="data:image/png;base64,{b64}" '
        f'preserveAspectRatio="none"/>\n'
        f"  </g>\n"
        f'  <g id="CutContour">\n    {path_elements}\n  </g>\n'
        f"</svg>"
    )


def hex_to_rgb01(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def svg_path_to_pdf_ops(svg_d: str, page_height: float) -> str:
    tokens = re.findall(r"[MLCZ][^MLCZ]*", svg_d)
    ops = ""
    for tok in tokens:
        cmd = tok[0]
        nums = list(map(float, re.findall(r"-?[\d.]+", tok[1:])))
        if cmd == "M":
            x, y = nums[0], page_height - nums[1]
            ops += f"{x:.2f} {y:.2f} m\n"
        elif cmd == "L":
            x, y = nums[0], page_height - nums[1]
            ops += f"{x:.2f} {y:.2f} l\n"
        elif cmd == "C":
            x1, y1 = nums[0], page_height - nums[1]
            x2, y2 = nums[2], page_height - nums[3]
            x3, y3 = nums[4], page_height - nums[5]
            ops += f"{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f} {x3:.2f} {y3:.2f} c\n"
        elif cmd == "Z":
            ops += "h\n"
    return ops


def build_pdf_with_image(
    page_w: int,
    page_h: int,
    paths: list[str],
    source_png: bytes,
    *,
    image_x: float = 0.0,
    image_y: float = 0.0,
    image_w: Optional[int] = None,
    image_h: Optional[int] = None,
    color: str = "#ff00c8",
    stroke_width: float = 1.5,
    source_pdf: Optional[bytes] = None,
    pt_scale: float = 1.0,
) -> bytes:
    """PDF with separate OCG layers: Artwork + CutContour (not blended/flattened).

    Jika source_pdf diberikan, halaman PDF vector asli di-embed langsung
    (kualitas tidak turun); source_png hanya dipakai sebagai fallback raster.

    pt_scale = 72/dpi: konversi koordinat pixel → point supaya ukuran fisik
    halaman output sama dengan aslinya (1000px @300dpi = 240pt, bukan 1000pt).
    """
    image_w = int(image_w if image_w is not None else page_w)
    image_h = int(image_h if image_h is not None else page_h)
    try:
        import fitz

        doc = fitz.open()
        page = doc.new_page(
            width=float(page_w) * pt_scale, height=float(page_h) * pt_scale
        )

        ocg_art = doc.add_ocg("Artwork", on=True)
        ocg_cut = doc.add_ocg("CutContour", on=True)

        img_rect = fitz.Rect(
            image_x * pt_scale,
            image_y * pt_scale,
            (image_x + image_w) * pt_scale,
            (image_y + image_h) * pt_scale,
        )
        embedded = False
        if source_pdf:
            try:
                src = fitz.open(stream=source_pdf, filetype="pdf")
                page.show_pdf_page(img_rect, src, 0, oc=ocg_art)
                src.close()
                embedded = True
            except Exception:
                embedded = False
        if not embedded:
            page.insert_image(
                img_rect,
                stream=source_png,
                keep_proportion=False,
                oc=ocg_art,
            )

        # ── Kontur sebagai spot color /CutContour di content stream terpisah ──
        # Standar industri: RIP/plotter mengenali spot "CutContour"; di Corel/
        # Illustrator garis potong jadi objek terpisah dari artwork (tidak
        # menyatu), plus bisa di-toggle lewat layer OCG.
        try:
            r, g, b = hex_to_rgb01(color)
            ps = (
                f"{{dup dup {b - 1.0:.6f} mul 1.000000 add 3 1 roll "
                f"{g - 1.0:.6f} mul 1.000000 add 3 1 roll "
                f"{r - 1.0:.6f} mul 1.000000 add 3 1 roll}}"
            )
            xref_tf = doc.get_new_xref()
            doc.update_object(
                xref_tf,
                "<< /FunctionType 4 /Domain [ 0 1 ] /Range [ 0 1 0 1 0 1 ] >>",
            )
            doc.update_stream(xref_tf, ps.encode("latin-1"), compress=False)
            xref_sep = doc.get_new_xref()
            doc.update_object(
                xref_sep, f"[ /Separation /CutContour /DeviceRGB {xref_tf} 0 R ]"
            )

            # CTM px→pt: koordinat path tetap pixel, dipetakan ke point oleh cm.
            # Lebar garis ikut ter-skala (px → ukuran fisik konsisten).
            ops = (
                "/OC /OCcut BDC\n"
                f"q\n{pt_scale:.6f} 0 0 {pt_scale:.6f} 0 0 cm\n"
                "/CutCS CS\n1 SCN\n"
                f"{float(stroke_width):.2f} w\n1 j\n1 J\n"
            )
            for d in paths:
                ops += "q\n" + svg_path_to_pdf_ops(d, float(page_h)) + "S\nQ\n"
            ops += "Q\nEMC\n"
            xref_cont = doc.get_new_xref()
            doc.update_object(xref_cont, "<< >>")
            doc.update_stream(xref_cont, ops.encode("latin-1"), compress=True)

            pxref = page.xref
            ctype, cval = doc.xref_get_key(pxref, "Contents")
            if ctype == "array":
                new_contents = cval.rstrip("]") + f" {xref_cont} 0 R]"
            else:
                new_contents = f"[{cval} {xref_cont} 0 R]"
            doc.xref_set_key(pxref, "Contents", new_contents)

            # Resources bisa berupa indirect reference — resolve dulu,
            # xref_set_key tidak bisa menembus indirect di tengah path.
            rtype, rval = doc.xref_get_key(pxref, "Resources")
            if rtype == "xref":
                res_target, res_prefix = int(rval.split()[0]), ""
            else:
                res_target, res_prefix = pxref, "Resources/"
            for sub, val in (
                ("ColorSpace/CutCS", f"{xref_sep} 0 R"),
                ("Properties/OCcut", f"{ocg_cut} 0 R"),
            ):
                stype, sval = doc.xref_get_key(res_target, res_prefix + sub.split("/")[0])
                if stype == "xref":
                    doc.xref_set_key(int(sval.split()[0]), sub.split("/")[1], val)
                else:
                    doc.xref_set_key(res_target, res_prefix + sub, val)
        except Exception:
            # Fallback: gambar via fitz shape (RGB biasa, tetap layer OCG terpisah)
            rgb = hex_to_rgb01(color)
            shape = page.new_shape()
            s = pt_scale
            for d in paths:
                tokens = re.findall(r"[MLCZ][^MLCZ]*", d)
                cur = None
                start = None
                for tok in tokens:
                    cmd = tok[0]
                    nums = list(map(float, re.findall(r"-?[\d.]+", tok[1:])))
                    if cmd == "M":
                        cur = fitz.Point(nums[0] * s, nums[1] * s)
                        start = cur
                    elif cmd == "L" and cur is not None:
                        nxt = fitz.Point(nums[0] * s, nums[1] * s)
                        shape.draw_line(cur, nxt)
                        cur = nxt
                    elif cmd == "C" and cur is not None:
                        p1 = fitz.Point(nums[0] * s, nums[1] * s)
                        p2 = fitz.Point(nums[2] * s, nums[3] * s)
                        p3 = fitz.Point(nums[4] * s, nums[5] * s)
                        shape.draw_bezier(cur, p1, p2, p3)
                        cur = p3
                    elif cmd == "Z" and cur is not None and start is not None:
                        if abs(cur.x - start.x) > 0.01 or abs(cur.y - start.y) > 0.01:
                            shape.draw_line(cur, start)
                        cur = start
                shape.finish(
                    color=rgb,
                    fill=None,
                    width=float(stroke_width) * s,
                    closePath=False,
                    stroke_opacity=1,
                    fill_opacity=0,
                    oc=ocg_cut,
                )
            shape.commit()

        pdf_bytes = doc.tobytes(deflate=True)
        doc.close()
        return pdf_bytes
    except Exception:
        return build_pdf_contour_only(
            page_w, page_h, paths, color=color, stroke_width=stroke_width, pt_scale=pt_scale
        )


def build_pdf_contour_only(
    width: int,
    height: int,
    paths: list[str],
    color: str = "#ff00c8",
    stroke_width: float = 1.5,
    pt_scale: float = 1.0,
) -> bytes:
    r, g, b = hex_to_rgb01(color)
    content = f"q\n{pt_scale:.6f} 0 0 {pt_scale:.6f} 0 0 cm\n"
    for d in paths:
        content += (
            f"{r:.3f} {g:.3f} {b:.3f} RG\n"
            f"{stroke_width:.2f} w\n"
            "1 j\n1 J\n"
        )
        content += svg_path_to_pdf_ops(d, height)
        content += "S\n"
    content += "Q\n"

    pdf = "%PDF-1.4\n"
    parts = []

    def push(body: str) -> str:
        parts.append(body)
        return body

    push("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    push("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    push(
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        f"/MediaBox [0 0 {width * pt_scale:.2f} {height * pt_scale:.2f}] "
        f"/Contents 4 0 R /Resources << >> >>\nendobj\n"
    )
    stream_len = len(content)
    push(f"4 0 obj\n<< /Length {stream_len} >>\nstream\n{content}\nendstream\nendobj\n")

    running = len(pdf)
    real_offsets = []
    for p in parts:
        real_offsets.append(running)
        running += len(p)

    pdf_str = pdf + "".join(parts)
    xref_start = len(pdf_str)
    xref = f"xref\n0 {len(real_offsets) + 1}\n0000000000 65535 f \n"
    for off in real_offsets:
        xref += f"{off:010d} 00000 n \n"
    pdf_str += xref
    pdf_str += (
        f"trailer\n<< /Size {len(real_offsets) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF"
    )
    return pdf_str.encode("latin-1")


def apply_offset_mask(mask: np.ndarray, offset_proc_px: float) -> tuple[np.ndarray, int]:
    """Expand object mask by offset (px at process resolution). Returns (mask, pad)."""
    if offset_proc_px <= 0.05:
        return mask, 0

    pad = int(math.ceil(offset_proc_px)) + 1
    padded = cv2.copyMakeBorder(mask, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    # distance to nearest object pixel (object=0 on inverted)
    inv = cv2.bitwise_not(padded)
    dist = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    expanded = np.where(dist <= offset_proc_px, 255, 0).astype(np.uint8)
    return expanded, pad


def generate_contour(
    img_bytes: bytes,
    *,
    smoothing: float = 5000.0,
    min_area: int = 500,
    line_color: str = "#ff00c8",
    line_width: float = 1.5,
    bg_color: Optional[str] = None,
    bg_tolerance: int = 28,
    max_dim: int = 1400,
    offset_mm: float = 0.0,
    dpi: Optional[float] = None,
    show_points: bool = False,
) -> dict:
    """
    Generate cut contour SVG + PDF (source image + contour) from a PNG or PDF.
    """
    source_pdf: Optional[bytes] = None
    if img_bytes[:5] == b"%PDF-":
        # Input PDF: render ke PNG untuk deteksi kontur & preview,
        # tapi simpan bytes PDF asli untuk di-embed vector ke output.
        source_pdf = img_bytes
        dpi_val = float(dpi) if dpi and float(dpi) > 0 else 300.0
        img_bytes = pdf_to_png(source_pdf, dpi_val)
        pil_src = Image.open(io.BytesIO(img_bytes))
    else:
        pil_src = Image.open(io.BytesIO(img_bytes))
        dpi_val = float(dpi) if dpi else read_dpi(pil_src, 300.0)
        if dpi_val <= 0:
            dpi_val = 300.0

    orig_w, orig_h = pil_src.size
    if orig_w < 1 or orig_h < 1:
        raise ValueError("Gambar tidak valid.")

    offset_mm = max(0.0, float(offset_mm))
    offset_px = mm_to_px(offset_mm, dpi_val)

    # Keep a PNG stream for PDF embedding (original pixels).
    png_buf = io.BytesIO()
    src_rgba = pil_src.convert("RGBA") if pil_src.mode != "RGBA" else pil_src.copy()
    src_rgba.save(png_buf, format="PNG")
    source_png = png_buf.getvalue()

    max_dim = max(100, int(max_dim))
    scale = min(1.0, max_dim / max(orig_w, orig_h))
    proc_w = max(1, int(orig_w * scale))
    proc_h = max(1, int(orig_h * scale))
    pil_img = src_rgba.resize((proc_w, proc_h), Image.LANCZOS)
    img_np = np.array(pil_img)
    if img_np.ndim == 2:
        img_np = np.stack([img_np, img_np, img_np], axis=-1)

    has_alpha = img_np.ndim == 3 and img_np.shape[2] == 4
    if has_alpha and int(np.min(img_np[:, :, 3])) >= 250:
        has_alpha = False
        img_np = img_np[:, :, :3]

    used_bg = bg_color
    if has_alpha:
        mask = mask_from_alpha(img_np)
    else:
        img_rgb = img_np[:, :, :3]
        if used_bg is None:
            used_bg = auto_detect_bgcolor(img_rgb)
        mask = mask_from_bgcolor(img_rgb, used_bg, bg_tolerance)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    offset_proc = offset_px * scale
    mask, pad = apply_offset_mask(mask, offset_proc)

    # Haluskan tepi mask: blur + re-threshold menghilangkan staircase piksel
    # (sumber utama kontur bergelombang), lalu spline mengikuti tepi yang
    # benar-benar mulus.
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    # RETR_EXTERNAL: hanya kontur terluar per objek — untuk cut line stiker,
    # lubang di dalam objek (mis. lubang huruf) tidak boleh ikut dipotong.
    contours, _hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    out_scale = orig_w / proc_w
    pad_out = pad * out_scale
    page_w = int(round(orig_w + 2 * pad_out))
    page_h = int(round(orig_h + 2 * pad_out))
    img_x = pad_out
    img_y = pad_out

    # min_area is specified in process px² before pad scale-back approximation
    svg_paths: list[str] = []
    curve_points: list[list[list[float]]] = []
    total_points = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        # min_area dievaluasi di resolusi ASLI (px²) — kalau dievaluasi di
        # resolusi proses (downscale), objek kecil pada sheet besar ikut terbuang.
        area_orig = area * (out_scale ** 2)
        if area_orig < min_area:
            continue
        # Contour is in padded process space → map to page (original + pad) coords
        cnt_xy = cnt.reshape(-1, 2).astype(float)
        cnt_scaled = cnt_xy * out_scale
        if len(cnt_scaled) < 8:
            continue

        # Bentuk standar? → pakai geometri eksak (tajam), bukan hasil tracing
        shape = detect_standard_shape(cnt_scaled)
        if shape is not None:
            path_d = shape_to_svg_path(shape)
            pts = shape_sample_points(shape)
        else:
            tck = fit_bspline(cnt_scaled, smoothing=smoothing)
            n_sample = max(100, min(600, int(area_orig / 500)))
            path_d = spline_to_svg_path(tck, n_segments=n_sample)
            pts = spline_sample_points(tck, n_segments=n_sample)
        svg_paths.append(path_d)
        curve_points.append(pts)
        total_points += len(pts)

    if not svg_paths:
        raise ValueError(
            "Tidak ada objek yang ditemukan. Coba sesuaikan toleransi warna background atau min_area."
        )

    svg = build_svg(
        page_w,
        page_h,
        svg_paths,
        color=line_color,
        stroke_width=line_width,
        curve_points=curve_points,
        show_points=False,  # UI toggles points client-side
    )
    svg_export = build_svg_export(
        page_w,
        page_h,
        svg_paths,
        source_png,
        image_x=img_x,
        image_y=img_y,
        image_w=orig_w,
        image_h=orig_h,
        color=line_color,
        stroke_width=line_width,
        pt_scale=72.0 / dpi_val,
    )
    pdf_bytes = build_pdf_with_image(
        page_w,
        page_h,
        svg_paths,
        source_png,
        image_x=img_x,
        image_y=img_y,
        image_w=orig_w,
        image_h=orig_h,
        color=line_color,
        stroke_width=line_width,
        source_pdf=source_pdf,
        pt_scale=72.0 / dpi_val,
    )

    width_cm = round(px_to_cm(orig_w, dpi_val), 2)
    height_cm = round(px_to_cm(orig_h, dpi_val), 2)
    page_w_cm = round(px_to_cm(page_w, dpi_val), 2)
    page_h_cm = round(px_to_cm(page_h, dpi_val), 2)

    result = {
        "status": "success",
        "svg": svg,
        "svg_export": svg_export,
        "is_pdf_source": source_pdf is not None,
        "pdf_base64": base64.b64encode(pdf_bytes).decode(),
        "loops": len(svg_paths),
        "points": total_points,
        "curve_points": curve_points,
        "width": orig_w,
        "height": orig_h,
        "page_width": page_w,
        "page_height": page_h,
        "image_x": round(img_x, 2),
        "image_y": round(img_y, 2),
        "width_cm": width_cm,
        "height_cm": height_cm,
        "page_width_cm": page_w_cm,
        "page_height_cm": page_h_cm,
        "dpi": dpi_val,
        "offset_mm": offset_mm,
        "offset_px": round(offset_px, 2),
        "max_dim": max_dim,
        "smoothing": smoothing,
        "bg_color": used_bg,
        "line_color": line_color,
        "line_width": line_width,
    }
    if source_pdf is not None:
        # Preview raster untuk browser (input-nya PDF) — downscale agar payload kecil
        prev_scale = min(1.0, 1600 / max(orig_w, orig_h))
        if prev_scale < 1.0:
            prev = src_rgba.resize(
                (max(1, int(orig_w * prev_scale)), max(1, int(orig_h * prev_scale))),
                Image.LANCZOS,
            )
            prev_buf = io.BytesIO()
            prev.save(prev_buf, format="PNG")
            result["preview_png_base64"] = base64.b64encode(prev_buf.getvalue()).decode()
        else:
            result["preview_png_base64"] = base64.b64encode(source_png).decode()
    return result


def run(data: dict) -> dict:
    """Optional task-style entry (filepath-based) for later CLI/Laravel wiring."""
    filepath = data.get("filepath") or data.get("file")
    if not filepath:
        return {"status": "error", "message": "Missing filepath"}
    with open(filepath, "rb") as f:
        img_bytes = f.read()
    try:
        return generate_contour(
            img_bytes,
            smoothing=float(data.get("smoothing", 5000)),
            min_area=int(data.get("min_area", 500)),
            line_color=data.get("line_color", "#ff00c8"),
            line_width=float(data.get("line_width", 1.5)),
            bg_color=data.get("bg_color"),
            bg_tolerance=int(data.get("bg_tolerance", 28)),
            max_dim=int(data.get("max_dim", 1400)),
            offset_mm=float(data.get("offset_mm", 0)),
            dpi=float(data["dpi"]) if data.get("dpi") not in (None, "") else None,
            show_points=bool(data.get("show_points", False)),
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}
