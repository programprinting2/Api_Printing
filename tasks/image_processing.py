# import os
# from PIL import Image, ImageDraw, ImageColor, ImageFont

# Image.MAX_IMAGE_PIXELS = None


# # =========================================================
# # UTILITY
# # =========================================================


# def safe_float(value, default=0.0):
#     try:
#         if isinstance(value, str):
#             value = value.replace(",", ".")
#         return float(value)
#     except Exception:
#         return default


# def safe_int(value, default=0):
#     try:
#         return int(value)
#     except Exception:
#         return default


# def get_color(color_name, mode):
#     try:
#         rgb = ImageColor.getrgb(str(color_name))
#         if mode == "CMYK":
#             return (255 - rgb[0], 255 - rgb[1], 255 - rgb[2], 0)
#         return rgb
#     except Exception:
#         return (0, 0, 0)


# def cm_ke_px(cm, dpi, scale):
#     cm_value = safe_float(cm, 0)
#     px = cm_value * dpi / 2.54 * (scale / 100)
#     return max(int(px), 1)


# # =========================================================
# # PROCESSING COMPONENTS
# # =========================================================


# def tambah_kotak_sekeliling(img, dpi, scale):
#     w, h = img.size
#     canvas = img.copy()
#     draw = ImageDraw.Draw(canvas)

#     warna_garis = get_color("lightgrey", img.mode)
#     ukuran_garis = max(cm_ke_px(0.1, dpi, scale), 1)

#     draw.rectangle([(0, 0), (w - 1, h - 1)], outline=warna_garis, width=ukuran_garis)

#     return canvas


# def buat_plong(img, param, dpi, scale):

#     # skip jika tidak ada warna_plong
#     if "warna_plong" not in param:
#         return img

#     mode = img.mode
#     w, h = img.size

#     atas = cm_ke_px(param.get("jarak_plong_atas", 0), dpi, scale)
#     bawah = cm_ke_px(param.get("jarak_plong_bawah", 0), dpi, scale)
#     kiri = cm_ke_px(param.get("jarak_plong_kiri", 0), dpi, scale)
#     kanan = cm_ke_px(param.get("jarak_plong_kanan", 0), dpi, scale)

#     warna_plong = get_color(param.get("warna_plong", "black"), mode)

#     canvas = img.copy()
#     draw = ImageDraw.Draw(canvas)

#     jenis_plong = param.get("jenis_plong", "pojok")
#     bentuk_plong = param.get("bentuk_plong", "circle")

#     if bentuk_plong == "square":
#         width = cm_ke_px(param.get("diameter_lebar", 1), dpi, scale)
#         height = cm_ke_px(param.get("diameter_panjang", 1), dpi, scale)

#         def draw_shape(x, y):
#             draw.rectangle(
#                 (x - width // 2, y - height // 2, x + width // 2, y + height // 2),
#                 fill=warna_plong,
#             )

#     else:
#         radius = cm_ke_px(param.get("diameter_lebar", 1), dpi, scale) // 2

#         def draw_shape(x, y):
#             draw.ellipse(
#                 (x - radius, y - radius, x + radius, y + radius),
#                 fill=warna_plong,
#             )

#     if jenis_plong == "pojok":
#         draw_shape(kiri, atas)
#         draw_shape(w - kanan, atas)
#         draw_shape(kiri, h - bawah)
#         draw_shape(w - kanan, h - bawah)

#     elif jenis_plong == "plong_per_jarak":

#         for panjang, jumlah, pos_fixed, horizontal in [
#             (w - kiri - kanan, safe_int(param.get("Plong_atas", 0)), atas, True),
#             (w - kiri - kanan, safe_int(param.get("Plong_bawah", 0)), h - bawah, True),
#             (h - atas - bawah, safe_int(param.get("Plong_kiri", 0)), kiri, False),
#             (h - atas - bawah, safe_int(param.get("Plong_kanan", 0)), w - kanan, False),
#         ]:

#             if jumlah > 1:
#                 step = max(panjang // (jumlah - 1), 1)

#                 for i in range(jumlah):
#                     if horizontal:
#                         draw_shape(kiri + i * step, pos_fixed)
#                     else:
#                         draw_shape(pos_fixed, atas + i * step)

#     return canvas


# def tambah_teks(
#     img,
#     pesan,
#     ukuran_cm,
#     warna_pesan,
#     offsetX_cm,
#     offsetY_cm,
#     dpi,
#     scale,
#     rotasi_pesan=0,
# ):

#     if not pesan:
#         return img

#     source_mode = img.mode

#     if source_mode == "CMYK":
#         if img.mode != "CMYK":
#             img = img.convert("CMYK")
#     else:
#         if img.mode != "RGBA":
#             img = img.convert("RGBA")

#     warna = get_color(warna_pesan, "RGBA")
#     ukuran_px = cm_ke_px(ukuran_cm, dpi, scale)

#     try:
#         font = ImageFont.truetype("arial.ttf", ukuran_px)
#     except Exception:
#         font = ImageFont.load_default()

#     txt_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
#     txt_draw = ImageDraw.Draw(txt_img)

#     bbox = txt_draw.textbbox((0, 0), pesan, font=font)
#     text_width = bbox[2] - bbox[0]
#     text_height = bbox[3] - bbox[1]

#     padding = int(ukuran_px * 0.1)
#     text_width += padding * 2
#     text_height += padding * 2

#     txt_img = Image.new("RGBA", (text_width, text_height), (255, 255, 255, 0))

#     txt_draw = ImageDraw.Draw(txt_img)
#     txt_draw.text((0, 0), pesan, fill=warna, font=font)

#     rotated_txt = txt_img.rotate(safe_int(rotasi_pesan, 0), expand=True)

#     offsetX_px = cm_ke_px(offsetX_cm, dpi, scale)
#     offsetY_px = cm_ke_px(offsetY_cm, dpi, scale)

#     img.paste(rotated_txt, (offsetX_px, offsetY_px), rotated_txt)

#     return img


# def tambah_teks_kedua(
#     img,
#     pesan,
#     ukuran_cm,
#     warna_pesan,
#     offsetX_cm,
#     offsetY_cm,
#     dpi,
#     scale,
#     rotasi_pesan=0,
# ):

#     if not pesan:
#         return img

#     ukuran_px = cm_ke_px(ukuran_cm, dpi, scale)

#     try:
#         font = ImageFont.truetype("arial.ttf", ukuran_px)
#     except Exception:
#         font = ImageFont.load_default()

#     txt_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
#     txt_draw = ImageDraw.Draw(txt_img)

#     bbox = txt_draw.textbbox((0, 0), pesan, font=font)
#     text_width = bbox[2] - bbox[0]
#     text_height = bbox[3] - bbox[1]

#     padding = int(ukuran_px * 0.1)
#     text_width += padding * 2
#     text_height += padding * 2

#     txt_img = Image.new("RGBA", (text_width, text_height), (255, 255, 255, 0))

#     txt_draw.text((0, 0), pesan, fill=get_color(warna_pesan, "RGBA"), font=font)

#     rotated_txt = txt_img.rotate(safe_int(rotasi_pesan, 0), expand=True)

#     offsetX_px = cm_ke_px(offsetX_cm, dpi, scale)
#     offsetY_px = cm_ke_px(offsetY_cm, dpi, scale)

#     pos2 = (
#         img.width - rotated_txt.width - offsetX_px,
#         img.height - rotated_txt.height - offsetY_px,
#     )

#     img.paste(rotated_txt, pos2, rotated_txt)

#     return img


# def tambah_background(img, param, dpi, scale):

#     if "WarnaBackground" not in param:
#         return img

#     mode = img.mode
#     w, h = img.size

#     kiri = cm_ke_px(param.get("Lebihan_kiri", 0), dpi, scale)
#     kanan = cm_ke_px(param.get("Lebihan_kanan", 0), dpi, scale)
#     atas = cm_ke_px(param.get("Lebihan_atas", 0), dpi, scale)
#     bawah = cm_ke_px(param.get("Lebihan_bawah", 0), dpi, scale)

#     warna_bg = get_color(param.get("WarnaBackground", "white"), mode)
#     warna_garis = get_color(param.get("WarnaGaris", "black"), mode)
#     ukuran_garis = max(cm_ke_px(param.get("UkuranGaris", 0.1), dpi, scale), 1)

#     bg = Image.new(mode, (w + kiri + kanan, h + atas + bawah), warna_bg)

#     bg.paste(img, (kiri, atas))

#     draw = ImageDraw.Draw(bg)
#     dash = max(cm_ke_px("0.5", dpi, scale), 1)

#     for x in range(0, bg.width, dash * 2):
#         draw.line([(x, 0), (x + dash, 0)], fill=warna_garis, width=ukuran_garis)
#         draw.line(
#             [(x, bg.height - 1), (x + dash, bg.height - 1)],
#             fill=warna_garis,
#             width=ukuran_garis,
#         )

#     for y in range(0, bg.height, dash * 2):
#         draw.line([(0, y), (0, y + dash)], fill=warna_garis, width=ukuran_garis)
#         draw.line(
#             [(bg.width - 1, y), (bg.width - 1, y + dash)],
#             fill=warna_garis,
#             width=ukuran_garis,
#         )

#     return bg


# def duplikasi_gambar(img, copyX, copyY, rotasi, jarakX_cm, jarakY_cm, dpi, scale):

#     if copyX <= 1 and copyY <= 1:
#         return img

#     w, h = img.size

#     jarakX_px = cm_ke_px(jarakX_cm, dpi, scale)
#     jarakY_px = cm_ke_px(jarakY_cm, dpi, scale)

#     canvas = Image.new(
#         img.mode,
#         (w * copyX + jarakX_px * (copyX - 1), h * copyY + jarakY_px * (copyY - 1)),
#     )

#     for i in range(copyX):
#         for j in range(copyY):
#             img_copy = img.copy()
#             if rotasi:
#                 img_copy = img_copy.rotate(rotasi * (i + j), expand=True)

#             canvas.paste(img_copy, (i * (w + jarakX_px), j * (h + jarakY_px)))

#     return canvas


# # =========================================================
# # MAIN API FUNCTION
# # =========================================================


# def process_image(param: dict):

#     if not isinstance(param, dict):
#         return {"status": "error", "message": "Invalid JSON body"}

#     filepath = param.get("AlamatFile")
#     if not filepath:
#         return {"status": "error", "message": "AlamatFile is required"}

#     if not os.path.exists(filepath):
#         return {"status": "error", "message": "file not found"}

#     img = Image.open(filepath)

#     dpi = img.info.get("dpi", (300, 300))[0]
#     input_mode = img.mode

#     if input_mode not in ["RGB", "CMYK"]:
#         return {
#             "status": "error",
#             "message": f"Format gambar tidak didukung: {input_mode}",
#         }

#     image_scale = max(safe_int(param.get("image_scale", 100), 100), 5)

#     # ===== PIPELINE =====
#     img = tambah_kotak_sekeliling(img, dpi, image_scale)
#     img = buat_plong(img, param, dpi, image_scale)
#     img = tambah_background(img, param, dpi, image_scale)

#     if "pesan" in param:
#         img = tambah_teks(
#             img,
#             param.get("pesan"),
#             param.get("ukuran_pesan", 1),
#             param.get("warna_pesan", "black"),
#             param.get("posX_pesan", 0),
#             param.get("posY_pesan", 0),
#             dpi,
#             image_scale,
#             param.get("rotasi_pesan", 0),
#         )

#         img = tambah_teks_kedua(
#             img,
#             param.get("pesan"),
#             param.get("ukuran_pesan", 1),
#             param.get("warna_pesan", "black"),
#             param.get("posX_pesan", 0),
#             param.get("posY_pesan", 0),
#             dpi,
#             image_scale,
#             param.get("rotasi_pesan", 0),
#         )

#     copyX = safe_int(param.get("CopyX", 1), 1)
#     copyY = safe_int(param.get("CopyY", 1), 1)
#     jarakX = safe_float(param.get("jarak_gambarX", 0), 0)
#     jarakY = safe_float(param.get("jarak_gambarY", 0), 0)
#     rotasi_copy = safe_int(param.get("rotasi_copy", 0), 0)

#     img = duplikasi_gambar(
#         img, copyX, copyY, rotasi_copy, jarakX, jarakY, dpi, image_scale
#     )

#     if img.mode != input_mode:
#         img = img.convert(input_mode)

#     final_file = os.path.splitext(filepath)[0] + "_output.jpeg"

#     img.save(final_file, dpi=(dpi, dpi), quality=80)

#     return {"status": "success", "output_path": final_file}

import os
from PIL import Image, ImageDraw, ImageColor, ImageFont

Image.MAX_IMAGE_PIXELS = None


# =========================================================
# UTILITY
# =========================================================


def safe_float(value, default=0.0):
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def get_color(color_name, mode):
    try:
        rgb = ImageColor.getrgb(str(color_name))
        if mode == "CMYK":
            return (255 - rgb[0], 255 - rgb[1], 255 - rgb[2], 0)
        return rgb
    except Exception:
        return (0, 0, 0)


def cm_ke_px(cm, dpi, scale):
    cm_value = safe_float(cm, 0)
    px = cm_value * dpi / 2.54 * (scale / 100)
    return max(int(px), 1)


def has_any_key(param, keys):
    return any(k in param for k in keys)


# =========================================================
# PROCESSING COMPONENTS
# =========================================================


def tambah_kotak_sekeliling(img, dpi, scale):
    w, h = img.size
    canvas = img.copy()
    draw = ImageDraw.Draw(canvas)

    warna_garis = get_color("lightgrey", img.mode)
    ukuran_garis = max(cm_ke_px(0.1, dpi, scale), 1)

    draw.rectangle([(0, 0), (w - 1, h - 1)], outline=warna_garis, width=ukuran_garis)

    return canvas


# def buat_plong(img, param, dpi, scale):
#     # cek apakah ada parameter plong sama sekali
#     if not has_any_key(
#         param,
#         [
#             "warna_plong",
#             "Plong_atas",
#             "Plong_bawah",
#             "Plong_kiri",
#             "Plong_kanan",
#         ],
#     ):
#         return img

#     mode = img.mode
#     w, h = img.size

#     atas = cm_ke_px(param.get("jarak_plong_atas", 0), dpi, scale)
#     bawah = cm_ke_px(param.get("jarak_plong_bawah", 0), dpi, scale)
#     kiri = cm_ke_px(param.get("jarak_plong_kiri", 0), dpi, scale)
#     kanan = cm_ke_px(param.get("jarak_plong_kanan", 0), dpi, scale)

#     warna_plong = get_color(param.get("warna_plong", "black"), mode)

#     canvas = img.copy()
#     draw = ImageDraw.Draw(canvas)

#     jenis_plong = param.get("jenis_plong", "pojok")
#     bentuk_plong = param.get("bentuk_plong", "circle")

#     if bentuk_plong == "square":
#         width = cm_ke_px(param.get("diameter_lebar", 1), dpi, scale)
#         height = cm_ke_px(param.get("diameter_panjang", 1), dpi, scale)

#         def draw_shape(x, y):
#             draw.rectangle(
#                 (x - width // 2, y - height // 2, x + width // 2, y + height // 2),
#                 fill=warna_plong,
#             )

#     else:
#         radius = cm_ke_px(param.get("diameter_lebar", 1), dpi, scale) // 2

#         def draw_shape(x, y):
#             draw.ellipse(
#                 (x - radius, y - radius, x + radius, y + radius),
#                 fill=warna_plong,
#             )

#     if jenis_plong == "pojok":
#         draw_shape(kiri, atas)
#         draw_shape(w - kanan, atas)
#         draw_shape(kiri, h - bawah)
#         draw_shape(w - kanan, h - bawah)

#     elif jenis_plong == "plong_per_jarak":

#         for panjang, jumlah, pos_fixed, horizontal in [
#             (w - kiri - kanan, safe_int(param.get("Plong_atas", 0)), atas, True),
#             (w - kiri - kanan, safe_int(param.get("Plong_bawah", 0)), h - bawah, True),
#             (h - atas - bawah, safe_int(param.get("Plong_kiri", 0)), kiri, False),
#             (h - atas - bawah, safe_int(param.get("Plong_kanan", 0)), w - kanan, False),
#         ]:

#             if jumlah > 1:
#                 step = max(panjang // (jumlah - 1), 1)

#                 for i in range(jumlah):
#                     if horizontal:
#                         draw_shape(kiri + i * step, pos_fixed)
#                     else:
#                         draw_shape(pos_fixed, atas + i * step)

#     return canvas


def buat_plong(img, param, dpi, scale):
    # cek apakah user benar-benar memberikan warna plong, jika tidak langsung return
    if "warna_plong" not in param:
        return img

    mode = img.mode
    w, h = img.size

    # Ambil jarak plong, default None
    atas = param.get("jarak_plong_atas")
    bawah = param.get("jarak_plong_bawah")
    kiri = param.get("jarak_plong_kiri")
    kanan = param.get("jarak_plong_kanan")

    # Jika semua jarak None, skip plong
    if all(v is None for v in [atas, bawah, kiri, kanan]):
        return img

    # Convert cm -> px hanya untuk nilai yang ada
    atas_px = cm_ke_px(atas, dpi, scale) if atas is not None else 0
    bawah_px = cm_ke_px(bawah, dpi, scale) if bawah is not None else 0
    kiri_px = cm_ke_px(kiri, dpi, scale) if kiri is not None else 0
    kanan_px = cm_ke_px(kanan, dpi, scale) if kanan is not None else 0

    warna_plong = get_color(param["warna_plong"], mode)

    canvas = img.copy()
    draw = ImageDraw.Draw(canvas)

    jenis_plong = param.get("jenis_plong", "pojok")
    bentuk_plong = param.get("bentuk_plong", "circle")

    if bentuk_plong == "square":
        diameter_lebar = param.get("diameter_lebar")
        diameter_panjang = param.get("diameter_panjang")
        if diameter_lebar is None or diameter_panjang is None:
            return canvas  # skip jika ukuran tidak ada

        width = cm_ke_px(diameter_lebar, dpi, scale)
        height = cm_ke_px(diameter_panjang, dpi, scale)

        def draw_shape(x, y):
            draw.rectangle(
                (x - width // 2, y - height // 2, x + width // 2, y + height // 2),
                fill=warna_plong,
            )

    else:
        diameter = param.get("diameter_lebar")
        if diameter is None:
            return canvas
        radius = cm_ke_px(diameter, dpi, scale) // 2

        def draw_shape(x, y):
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=warna_plong,
            )

    # Gambar pojok jika user ingin
    if jenis_plong == "pojok":
        draw_shape(kiri_px, atas_px)
        draw_shape(w - kanan_px, atas_px)
        draw_shape(kiri_px, h - bawah_px)
        draw_shape(w - kanan_px, h - bawah_px)

    elif jenis_plong == "plong_per_jarak":
        for posisi, key in [
            (("Plong_atas", atas_px), True),
            (("Plong_bawah", h - bawah_px), True),
            (("Plong_kiri", kiri_px), False),
            (("Plong_kanan", w - kanan_px), False),
        ]:
            jumlah = param.get(posisi[0])
            if jumlah is None or jumlah < 1:
                continue

            panjang = w - kiri_px - kanan_px if posisi[1] else h - atas_px - bawah_px
            step = max(panjang // (jumlah - 1), 1) if jumlah > 1 else 0

            for i in range(jumlah):
                if posisi[1]:
                    draw_shape(kiri_px + i * step, posisi[1])
                else:
                    draw_shape(posisi[1], atas_px + i * step)

    return canvas


def tambah_teks(
    img,
    pesan,
    ukuran_cm,
    warna_pesan,
    offsetX_cm,
    offsetY_cm,
    dpi,
    scale,
    rotasi_pesan=0,
):

    if not pesan:
        return img

    source_mode = img.mode

    if source_mode == "CMYK":
        if img.mode != "CMYK":
            img = img.convert("CMYK")
    else:
        if img.mode != "RGBA":
            img = img.convert("RGBA")

    warna = get_color(warna_pesan, "RGBA")
    ukuran_px = cm_ke_px(ukuran_cm, dpi, scale)

    try:
        font = ImageFont.truetype("arial.ttf", ukuran_px)
    except Exception:
        font = ImageFont.load_default()

    txt_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_img)

    bbox = txt_draw.textbbox((0, 0), pesan, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = int(ukuran_px * 0.1)
    text_width += padding * 2
    text_height += padding * 2

    txt_img = Image.new("RGBA", (text_width, text_height), (255, 255, 255, 0))

    txt_draw = ImageDraw.Draw(txt_img)
    txt_draw.text((0, 0), pesan, fill=warna, font=font)

    rotated_txt = txt_img.rotate(safe_int(rotasi_pesan, 0), expand=True)

    offsetX_px = cm_ke_px(offsetX_cm, dpi, scale)
    offsetY_px = cm_ke_px(offsetY_cm, dpi, scale)

    img.paste(rotated_txt, (offsetX_px, offsetY_px), rotated_txt)

    return img


def tambah_teks_kedua(
    img,
    pesan,
    ukuran_cm,
    warna_pesan,
    offsetX_cm,
    offsetY_cm,
    dpi,
    scale,
    rotasi_pesan=0,
):

    if not pesan:
        return img

    ukuran_px = cm_ke_px(ukuran_cm, dpi, scale)

    try:
        font = ImageFont.truetype("arial.ttf", ukuran_px)
    except Exception:
        font = ImageFont.load_default()

    txt_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_img)

    bbox = txt_draw.textbbox((0, 0), pesan, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = int(ukuran_px * 0.1)
    text_width += padding * 2
    text_height += padding * 2

    txt_img = Image.new("RGBA", (text_width, text_height), (255, 255, 255, 0))

    txt_draw.text((0, 0), pesan, fill=get_color(warna_pesan, "RGBA"), font=font)

    rotated_txt = txt_img.rotate(safe_int(rotasi_pesan, 0), expand=True)

    offsetX_px = cm_ke_px(offsetX_cm, dpi, scale)
    offsetY_px = cm_ke_px(offsetY_cm, dpi, scale)

    pos2 = (
        img.width - rotated_txt.width - offsetX_px,
        img.height - rotated_txt.height - offsetY_px,
    )

    img.paste(rotated_txt, pos2, rotated_txt)

    return img


def tambah_background(img, param, dpi, scale):
    # cek apakah ada lebihan atau background
    if not has_any_key(
        param,
        [
            "WarnaBackground",
            "Lebihan_kiri",
            "Lebihan_kanan",
            "Lebihan_atas",
            "Lebihan_bawah",
        ],
    ):
        return img

    mode = img.mode
    w, h = img.size

    kiri = cm_ke_px(param.get("Lebihan_kiri", 0), dpi, scale)
    kanan = cm_ke_px(param.get("Lebihan_kanan", 0), dpi, scale)
    atas = cm_ke_px(param.get("Lebihan_atas", 0), dpi, scale)
    bawah = cm_ke_px(param.get("Lebihan_bawah", 0), dpi, scale)

    warna_bg = get_color(param.get("WarnaBackground", "white"), mode)
    warna_garis = get_color(param.get("WarnaGaris", "black"), mode)
    ukuran_garis = max(cm_ke_px(param.get("UkuranGaris", 0.1), dpi, scale), 1)

    bg = Image.new(mode, (w + kiri + kanan, h + atas + bawah), warna_bg)

    bg.paste(img, (kiri, atas))

    draw = ImageDraw.Draw(bg)
    dash = max(cm_ke_px("0.5", dpi, scale), 1)

    for x in range(0, bg.width, dash * 2):
        draw.line([(x, 0), (x + dash, 0)], fill=warna_garis, width=ukuran_garis)
        draw.line(
            [(x, bg.height - 1), (x + dash, bg.height - 1)],
            fill=warna_garis,
            width=ukuran_garis,
        )

    for y in range(0, bg.height, dash * 2):
        draw.line([(0, y), (0, y + dash)], fill=warna_garis, width=ukuran_garis)
        draw.line(
            [(bg.width - 1, y), (bg.width - 1, y + dash)],
            fill=warna_garis,
            width=ukuran_garis,
        )

    return bg


def duplikasi_gambar(img, copyX, copyY, rotasi, jarakX_cm, jarakY_cm, dpi, scale):
    if copyX <= 1 and copyY <= 1:
        return img

    w, h = img.size

    jarakX_px = cm_ke_px(jarakX_cm, dpi, scale)
    jarakY_px = cm_ke_px(jarakY_cm, dpi, scale)

    canvas = Image.new(
        img.mode,
        (w * copyX + jarakX_px * (copyX - 1), h * copyY + jarakY_px * (copyY - 1)),
    )

    for i in range(copyX):
        for j in range(copyY):
            img_copy = img.copy()
            if rotasi:
                img_copy = img_copy.rotate(rotasi * (i + j), expand=True)

            canvas.paste(img_copy, (i * (w + jarakX_px), j * (h + jarakY_px)))

    return canvas


# =========================================================
# MAIN API FUNCTION
# =========================================================


def process_image(param: dict):

    if not isinstance(param, dict):
        return {"status": "error", "message": "Invalid JSON body"}

    filepath = param.get("AlamatFile")
    if not filepath:
        return {"status": "error", "message": "AlamatFile is required"}

    if not os.path.exists(filepath):
        return {"status": "error", "message": "file not found"}

    img = Image.open(filepath)

    dpi = img.info.get("dpi", (300, 300))[0]
    input_mode = img.mode

    if input_mode not in ["RGB", "CMYK"]:
        return {
            "status": "error",
            "message": f"Format gambar tidak didukung: {input_mode}",
        }

    image_scale = max(safe_int(param.get("image_scale", 100), 100), 5)

    # ===== PIPELINE =====

    # Kotak sekeliling optional, aktifkan jika param['kotak_sekeliling'] == True
    if param.get("kotak_sekeliling"):
        img = tambah_kotak_sekeliling(img, dpi, image_scale)

    # Plong optional
    if has_any_key(
        param,
        [
            "warna_plong",
            "Plong_atas",
            "Plong_bawah",
            "Plong_kiri",
            "Plong_kanan",
        ],
    ):
        img = buat_plong(img, param, dpi, image_scale)

    # Lebihan/background optional
    if has_any_key(
        param,
        [
            "WarnaBackground",
            "Lebihan_kiri",
            "Lebihan_kanan",
            "Lebihan_atas",
            "Lebihan_bawah",
        ],
    ):
        img = tambah_background(img, param, dpi, image_scale)

    # Teks optional
    if "pesan" in param and str(param.get("pesan")).strip():
        img = tambah_teks(
            img,
            param.get("pesan"),
            param.get("ukuran_pesan", 1),
            param.get("warna_pesan", "black"),
            param.get("posX_pesan", 0),
            param.get("posY_pesan", 0),
            dpi,
            image_scale,
            param.get("rotasi_pesan", 0),
        )

        single_left = safe_int(param.get("single_pesan_kiri", 0), 0)

        if single_left != 1:
            img = tambah_teks_kedua(
                img,
                param.get("pesan"),
                param.get("ukuran_pesan", 1),
                param.get("warna_pesan", "black"),
                param.get("posX_pesan", 0),
                param.get("posY_pesan", 0),
                dpi,
                image_scale,
                param.get("rotasi_pesan", 0),
            )

    # Duplikasi optional
    copyX = safe_int(param.get("CopyX", 1), 1)
    copyY = safe_int(param.get("CopyY", 1), 1)

    if copyX > 1 or copyY > 1:
        jarakX = safe_float(param.get("jarak_gambarX", 0), 0)
        jarakY = safe_float(param.get("jarak_gambarY", 0), 0)
        rotasi_copy = safe_int(param.get("rotasi_copy", 0), 0)

        img = duplikasi_gambar(
            img, copyX, copyY, rotasi_copy, jarakX, jarakY, dpi, image_scale
        )

    if img.mode != input_mode:
        img = img.convert(input_mode)

    final_file = os.path.splitext(filepath)[0] + "_output.jpeg"

    img.save(final_file, dpi=(dpi, dpi), quality=80)

    return {"status": "success", "output_path": final_file}
