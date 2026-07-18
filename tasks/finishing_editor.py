import os
from urllib.parse import quote

from PIL import Image, ImageDraw

from tasks.proses_gambar import cm_ke_px, get_color, tambah_background, tambah_teks, tambah_teks_kedua

Image.MAX_IMAGE_PIXELS = None


def _to_num(value, default):
    if value in (None, ""):
        return default
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default):
    return int(round(_to_num(value, default)))


def _distribute(count, start, end):
    """Evenly-spaced positions between start and end (inclusive)."""
    count = int(count)
    if count <= 0:
        return []
    if count == 1:
        return [(start + end) / 2]
    step = (end - start) / (count - 1)
    return [start + i * step for i in range(count)]


def _sample_luminance(img, x, y, r):
    """Average luminance around (x, y) within radius r."""
    x, y, r = int(x), int(y), max(int(r), 1)
    x0 = max(0, x - r)
    y0 = max(0, y - r)
    x1 = min(img.width, x + r)
    y1 = min(img.height, y + r)
    if x1 <= x0 or y1 <= y0:
        return 255
    crop = img.crop((x0, y0, x1, y1)).convert("RGB")
    pixels = list(crop.getdata())
    if not pixels:
        return 255
    total = sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in pixels[::max(1, len(pixels) // 64)])
    return total / len(pixels[::max(1, len(pixels) // 64)])


def _contrast_color(img, x, y, r, mode):
    lum = _sample_luminance(img, x, y, r)
    return get_color("Black" if lum > 128 else "White", mode)


def buat_plong_jumlah(img, cfg, dpi, scale):
    """Draw N plong holes per side, evenly distributed along each edge."""
    mode = img.mode
    w, h = img.size
    canvas = img.copy()
    draw = ImageDraw.Draw(canvas)

    auto_contrast = cfg.get("auto_contrast", False)
    base_warna = get_color(cfg.get("warna_plong", "White"), mode)
    inset = cm_ke_px(cfg.get("inset", 2), dpi, scale)
    bentuk = cfg.get("bentuk_plong", "circle")

    if bentuk == "square":
        bw = cm_ke_px(cfg.get("diameter_lebar", 1), dpi, scale)
        bh = cm_ke_px(cfg.get("diameter_panjang", cfg.get("diameter_lebar", 1)), dpi, scale)
        sample_r = max(bw, bh) // 2

        def draw_shape(x, y):
            warna = _contrast_color(img, x, y, sample_r, mode) if auto_contrast else base_warna
            draw.rectangle((x - bw // 2, y - bh // 2, x + bw // 2, y + bh // 2), fill=warna)
    else:
        radius = max(cm_ke_px(cfg.get("diameter_lebar", 1), dpi, scale) // 2, 1)

        def draw_shape(x, y):
            warna = _contrast_color(img, x, y, radius, mode) if auto_contrast else base_warna
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=warna)

    n_atas = _to_int(cfg.get("jml_atas", 0), 0)
    n_bawah = _to_int(cfg.get("jml_bawah", 0), 0)
    n_kiri = _to_int(cfg.get("jml_kiri", 0), 0)
    n_kanan = _to_int(cfg.get("jml_kanan", 0), 0)

    for x in _distribute(n_atas, inset, w - inset):
        draw_shape(int(x), inset)
    for x in _distribute(n_bawah, inset, w - inset):
        draw_shape(int(x), h - inset)
    for y in _distribute(n_kiri, inset, h - inset):
        draw_shape(inset, int(y))
    for y in _distribute(n_kanan, inset, h - inset):
        draw_shape(w - inset, int(y))

    return canvas


def tambah_lipat_plong4(img, dpi, scale):
    """Tanda lipat 4: tick pendek di tepi (tengah tiap sisi), tidak menyeberang desain."""
    mode = img.mode
    canvas = img.copy()
    draw = ImageDraw.Draw(canvas)
    w, h = img.size
    warna = get_color("black", mode)
    tick = max(cm_ke_px("1.0", dpi, scale), 4)   # panjang tanda lipat
    lw = max(cm_ke_px("0.03", dpi, scale), 2)    # tebal garis
    cx, cy = w // 2, h // 2

    draw.line([(cx, 0), (cx, tick)], fill=warna, width=lw)          # tepi atas
    draw.line([(cx, h - tick), (cx, h)], fill=warna, width=lw)      # tepi bawah
    draw.line([(0, cy), (tick, cy)], fill=warna, width=lw)          # tepi kiri
    draw.line([(w - tick, cy), (w, cy)], fill=warna, width=lw)      # tepi kanan

    return canvas


def run(payload):
    try:
        payload = payload or {}
        filepath = payload.get("filepath")
        if not filepath or not os.path.isfile(filepath):
            return {"status": "error", "message": f"File tidak ditemukan: {filepath}"}

        img = Image.open(filepath)
        dpi = payload.get("dpi") or img.info.get("dpi", (300, 300))[0] or 300
        dpi = _to_num(dpi, 300.0)
        scale = _to_num(payload.get("image_scale"), 100)

        input_mode = img.mode
        if input_mode not in ("RGB", "CMYK"):
            img = img.convert("RGB")
            input_mode = "RGB"

        # rotasi (searah jarum jam, kelipatan 90) sebelum finishing
        rotation = int(_to_num(payload.get("rotation"), 0)) % 360
        if rotation:
            img = img.rotate(-rotation, expand=True)

        result_img = img

        plong_cfg = payload.get("plong") or {}
        if plong_cfg.get("enable"):
            result_img = buat_plong_jumlah(result_img, plong_cfg, dpi, scale)

        lebihan_cfg = payload.get("lebihan") or {}
        if lebihan_cfg.get("enable"):
            all_val = lebihan_cfg.get("all", 2.5)
            leb_top = lebihan_cfg.get("top", all_val)
            leb_left = lebihan_cfg.get("left", all_val)
            pre_w, pre_h = result_img.size
            leb_param = {
                "Lebihan_atas": leb_top,
                "Lebihan_bawah": lebihan_cfg.get("bottom", all_val),
                "Lebihan_kiri": leb_left,
                "Lebihan_kanan": lebihan_cfg.get("right", all_val),
                "WarnaBackground": lebihan_cfg.get("warna_background", "White"),
                "WarnaGaris": lebihan_cfg.get("warna_garis", "lightgrey"),
                "UkuranGaris": lebihan_cfg.get("ukuran_garis", 0.1),
            }
            result_img = tambah_background(result_img, leb_param, dpi, scale)

            bingkai_mode = lebihan_cfg.get("bingkai_objek", "auto")
            if bingkai_mode is True:
                bingkai_mode = "on"
            elif bingkai_mode is False:
                bingkai_mode = "off"
            draw_bingkai = bingkai_mode == "on"
            if bingkai_mode == "auto":
                bg_color_name = lebihan_cfg.get("warna_background", "White")
                bg_rgb = get_color(bg_color_name, "RGB")
                if not isinstance(bg_rgb, tuple):
                    bg_rgb = (255, 255, 255)
                orig_rgb = img.convert("RGB")
                edge_pixels = []
                for x in range(0, pre_w, max(1, pre_w // 32)):
                    edge_pixels.append(orig_rgb.getpixel((x, 0)))
                    edge_pixels.append(orig_rgb.getpixel((x, pre_h - 1)))
                for y in range(0, pre_h, max(1, pre_h // 32)):
                    edge_pixels.append(orig_rgb.getpixel((0, y)))
                    edge_pixels.append(orig_rgb.getpixel((pre_w - 1, y)))
                if edge_pixels:
                    avg_r = sum(p[0] for p in edge_pixels) / len(edge_pixels)
                    avg_g = sum(p[1] for p in edge_pixels) / len(edge_pixels)
                    avg_b = sum(p[2] for p in edge_pixels) / len(edge_pixels)
                    diff = abs(avg_r - bg_rgb[0]) + abs(avg_g - bg_rgb[1]) + abs(avg_b - bg_rgb[2])
                    draw_bingkai = diff < 80
            if draw_bingkai:
                draw_b = ImageDraw.Draw(result_img)
                lw = max(cm_ke_px(lebihan_cfg.get("ukuran_garis", 0.1), dpi, scale), 1)
                warna_garis = get_color(lebihan_cfg.get("warna_garis", "lightgrey"), result_img.mode)
                ox = cm_ke_px(leb_left, dpi, scale)
                oy = cm_ke_px(leb_top, dpi, scale)
                draw_b.rectangle((ox, oy, ox + pre_w - 1, oy + pre_h - 1), outline=warna_garis, width=lw)

        pesan_cfg = payload.get("pesan") or {}
        if pesan_cfg.get("enable"):
            text = str(pesan_cfg.get("text") or "").strip()
            if text:
                rotasi = 90 if pesan_cfg.get("posisi") == "vertical" else 0
                ukuran = pesan_cfg.get("ukuran", 0.8)
                warna = pesan_cfg.get("warna", "Black")
                pos_x = pesan_cfg.get("pos_x", 1)
                pos_y = pesan_cfg.get("pos_y", 3)
                if pesan_cfg.get("auto_contrast"):
                    px = cm_ke_px(pos_x, dpi, scale)
                    py = cm_ke_px(pos_y, dpi, scale)
                    font_r = max(cm_ke_px(ukuran, dpi, scale), 4)
                    lum = _sample_luminance(result_img, px, py, font_r)
                    warna = "Black" if lum > 128 else "White"
                result_img = tambah_teks(result_img, text, ukuran, warna, pos_x, pos_y, dpi, scale, rotasi)
                if not pesan_cfg.get("satu_kiri"):
                    if pesan_cfg.get("auto_contrast"):
                        w2, h2 = result_img.size
                        px2 = w2 - cm_ke_px(pos_x, dpi, scale)
                        py2 = h2 - cm_ke_px(pos_y, dpi, scale)
                        lum2 = _sample_luminance(result_img, px2, py2, font_r)
                        warna = "Black" if lum2 > 128 else "White"
                    result_img = tambah_teks_kedua(result_img, text, ukuran, warna, pos_x, pos_y, dpi, scale, rotasi)

        if result_img.mode != input_mode:
            result_img = result_img.convert(input_mode)

        stem, _ext = os.path.splitext(filepath)
        output_path = f"{stem}_finishing.jpg"
        quality = int(_to_num(lebihan_cfg.get("quality"), 80))
        quality = max(1, min(quality, 100))
        result_img.save(output_path, dpi=(dpi, dpi), quality=quality)

        return {
            "status": "success",
            "output_path": output_path,
            "output_url": "/ui/thumbnail?filepath=" + quote(output_path),
        }
    except FileNotFoundError as e:
        return {"status": "error", "message": str(e)}
    except (ValueError, KeyError) as e:
        return {"status": "error", "message": f"Parameter tidak valid: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
