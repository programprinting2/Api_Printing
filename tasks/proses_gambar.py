import os
from PIL import Image, ImageDraw, ImageColor, ImageFont

Image.MAX_IMAGE_PIXELS = None

def baca_parameter(file_param):
    param = {}
    with open(file_param, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            param[key.strip()] = value.strip().replace('"', '')
    return param

def get_color(color_name, mode):
    try:
        rgb = ImageColor.getrgb(color_name)
        if mode == "CMYK":
            return (255 - rgb[0], 255 - rgb[1], 255 - rgb[2], 0)
        return rgb
    except ValueError:
        return (0, 0, 0)

def cm_ke_px(cm, dpi, scale):
    if isinstance(cm, str):
        cm = cm.replace(",", ".")
    px = float(cm) * dpi / 2.54 * (scale / 100)
    return max(int(px), 1)

def buat_plong(img, param, dpi, scale):
    mode = img.mode
    w, h = img.size
    atas = cm_ke_px(param["jarak_plong_atas"], dpi, scale)
    bawah = cm_ke_px(param["jarak_plong_bawah"], dpi, scale)
    kiri = cm_ke_px(param["jarak_plong_kiri"], dpi, scale)
    kanan = cm_ke_px(param["jarak_plong_kanan"], dpi, scale)
    warna_plong = get_color(param["warna_plong"], mode)
    canvas = img.copy()
    draw = ImageDraw.Draw(canvas)
    jenis_plong = param.get("jenis_plong", "pojok")
    bentuk_plong = param.get("bentuk_plong", "circle")
    if bentuk_plong == "circle":
        radius = cm_ke_px(param["diameter_lebar"], dpi, scale) // 2
    elif bentuk_plong == "square":
        width = cm_ke_px(param["diameter_lebar"], dpi, scale)
        height = cm_ke_px(param["diameter_panjang"], dpi, scale)
    def draw_circle(x, y):
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=warna_plong)
    def draw_square(x, y):
        draw.rectangle((x-width//2, y-height//2, x+width//2, y+height//2), fill=warna_plong)
    if jenis_plong == "pojok":
        if bentuk_plong == "circle":
            draw_circle(kiri, atas)
            draw_circle(w - kanan, atas)
            draw_circle(kiri, h - bawah)
            draw_circle(w - kanan, h - bawah)
        elif bentuk_plong == "square":
            draw_square(kiri, atas)
            draw_square(w - kanan, atas)
            draw_square(kiri, h - bawah)
            draw_square(w - kanan, h - bawah)
    elif jenis_plong == "plong_per_jarak":
        for sisi, panjang, jumlah, pos_fixed, horizontal in [
            ("Plong_atas", w - kiri - kanan, int(param["Plong_atas"]), atas, True),
            ("Plong_bawah", w - kiri - kanan, int(param["Plong_bawah"]), h - bawah, True),
            ("Plong_kiri", h - atas - bawah, int(param["Plong_kiri"]), kiri, False),
            ("Plong_kanan", h - atas - bawah, int(param["Plong_kanan"]), w - kanan, False)
        ]:
            if jumlah > 1:
                step = max(panjang // (jumlah - 1), 1)
                for i in range(jumlah):
                    if horizontal:
                        if bentuk_plong == "circle":
                            draw_circle(kiri + i * step, pos_fixed)
                        elif bentuk_plong == "square":
                            draw_square(kiri + i * step, pos_fixed)
                    else:
                        if bentuk_plong == "circle":
                            draw_circle(pos_fixed, atas + i * step)
                        elif bentuk_plong == "square":
                            draw_square(pos_fixed, atas + i * step)
    return canvas

def tambah_teks(img, pesan, ukuran_cm, warna_pesan, offsetX_cm, offsetY_cm, dpi, scale, rotasi_pesan=0):
    source_mode = img.mode
    if source_mode == "CMYK":
        if img.mode != "CMYK":
            img = img.convert("CMYK")
    else:
        if img.mode != "RGBA":
            img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)
    warna = get_color(warna_pesan, "RGBA")

    ukuran_px = cm_ke_px(ukuran_cm, dpi, scale)

    try:
        font = ImageFont.truetype("arial.ttf", ukuran_px)
    except IOError:
        font = ImageFont.load_default()

    txt_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    text_bbox = txt_draw.textbbox((0, 0), pesan, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    padding = int(ukuran_px * 0.1)  # 10% dari ukuran font
    text_width += padding * 2
    text_height += padding * 2

    txt_img = Image.new("RGBA", (text_width, text_height), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    txt_draw.text((0, 0), pesan, fill=warna, font=font)

    rotated_txt = txt_img.rotate(rotasi_pesan, expand=True)

    offsetX_px = cm_ke_px(offsetX_cm, dpi, scale)
    offsetY_px = cm_ke_px(offsetY_cm, dpi, scale)

    img.paste(rotated_txt, (offsetX_px, offsetY_px), rotated_txt)

    return img

def tambah_teks_kedua(img, pesan, ukuran_cm, warna_pesan, offsetX_cm, offsetY_cm, dpi, scale, rotasi_pesan=0):
    ukuran_px = cm_ke_px(ukuran_cm, dpi, scale)
    try:
        font = ImageFont.truetype("arial.ttf", ukuran_px)
    except IOError:
        font = ImageFont.load_default()

    txt_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    txt_draw.text((0, 0), pesan, font=font)
    text_bbox = txt_draw.textbbox((0, 0), pesan, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    padding = int(ukuran_px * 0.1)  # 10% dari ukuran font
    text_width += padding * 2
    text_height += padding * 2

    txt_img = Image.new("RGBA", (text_width, text_height), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    txt_draw.text((0, 0), pesan, fill=get_color(warna_pesan, "RGBA"), font=font)

    rotated_txt = txt_img.rotate(rotasi_pesan, expand=True)
    rotated_width, rotated_height = rotated_txt.size

    offsetX_px = cm_ke_px(offsetX_cm, dpi, scale)
    offsetY_px = cm_ke_px(offsetY_cm, dpi, scale)
    pos2 = (img.width - rotated_width - offsetX_px, img.height - rotated_height - offsetY_px)

    img.paste(rotated_txt, pos2, rotated_txt)

    return img

def tambah_kotak_sekeliling(img, dpi, scale):
    mode = img.mode
    w, h = img.size
    canvas = img.copy()
    draw = ImageDraw.Draw(canvas)
    warna_garis = get_color("lightgrey", mode)
    ukuran_garis = max(cm_ke_px("0.1", dpi, scale), 1)
    draw.rectangle([(0, 0), (w-1, h-1)], outline=warna_garis, width=ukuran_garis)
    return canvas

def tambah_background(img, param, dpi, scale):
    mode = img.mode
    w, h = img.size
    kiri = cm_ke_px(param["Lebihan_kiri"], dpi, scale)
    kanan = cm_ke_px(param["Lebihan_kanan"], dpi, scale)
    atas = cm_ke_px(param["Lebihan_atas"], dpi, scale)
    bawah = cm_ke_px(param["Lebihan_bawah"], dpi, scale)
    warna_bg = get_color(param["WarnaBackground"], mode)
    warna_garis = get_color(param["WarnaGaris"], mode)
    ukuran_garis = max(cm_ke_px(param["UkuranGaris"], dpi, scale), 1)
    bg = Image.new(mode, (w + kiri + kanan, h + atas + bawah), warna_bg)
    bg.paste(img, (kiri, atas))
    draw = ImageDraw.Draw(bg)
    dash = max(cm_ke_px("0.5", dpi, scale), 1)
    for x in range(0, bg.width, dash * 2):
        draw.line([(x, 0), (x + dash, 0)], fill=warna_garis, width=ukuran_garis)
        draw.line([(x, bg.height - 1), (x + dash, bg.height - 1)], fill=warna_garis, width=ukuran_garis)
    for y in range(0, bg.height, dash * 2):
        draw.line([(0, y), (0, y + dash)], fill=warna_garis, width=ukuran_garis)
        draw.line([(bg.width - 1, y), (bg.width - 1, y + dash)], fill=warna_garis, width=ukuran_garis)
    return bg

def duplikasi_gambar(img, copyX, copyY, rotasi, jarakX_cm, jarakY_cm, dpi, scale):
    w, h = img.size
    jarakX_px = cm_ke_px(jarakX_cm, dpi, scale)
    jarakY_px = cm_ke_px(jarakY_cm, dpi, scale)
    canvas = Image.new(img.mode, (w * copyX + jarakX_px * (copyX - 1), h * copyY + jarakY_px * (copyY - 1)))
    for i in range(copyX):
        for j in range(copyY):
            img_copy = img.copy()
            if rotasi:
                img_copy = img_copy.rotate(rotasi * (i + j), expand=True)
            canvas.paste(img_copy, (i * (w + jarakX_px), j * (h + jarakY_px)))
    return canvas

def proses_gambar(file_param):
    param = baca_parameter(file_param)
    gambar_asli = param["AlamatFile"]
    img = Image.open(gambar_asli)
    dpi = img.info.get("dpi", (300, 300))[0]
    input_mode = img.mode
    image_scale = max(int(param.get("image_scale", 100)), 5)
    if input_mode not in ["RGB", "CMYK"]:
        raise ValueError(f"Format gambar tidak didukung: {input_mode}")
    img = tambah_kotak_sekeliling(img, dpi, image_scale)
    img = buat_plong(img, param, dpi, image_scale)
    
    img = tambah_background(img, param, dpi, image_scale)    
    copyX = int(param.get("CopyX", 1))
    copyY = int(param.get("CopyY", 1))
    img = tambah_teks(img, param["pesan"], param["ukuran_pesan"], param["warna_pesan"], float(param["posX_pesan"]), float(param["posY_pesan"]), dpi, image_scale, int(param.get("rotasi_pesan", 0)))
    img = tambah_teks_kedua(img, param["pesan"], param["ukuran_pesan"], param["warna_pesan"], float(param["posX_pesan"]), float(param["posY_pesan"]), dpi, image_scale, int(param.get("rotasi_pesan", 0)))
    jarak_gambarX = float(param.get("jarak_gambarX", 0))
    jarak_gambarY = float(param.get("jarak_gambarY", 0))
    rotasi_copy = int(param.get("rotasi_copy", 0))
    if copyX > 1 or copyY > 1:
        img = duplikasi_gambar(img, copyX, copyY, rotasi_copy, jarak_gambarX, jarak_gambarY, dpi, image_scale)
    if img.mode != input_mode:
        img = img.convert(input_mode)
    final_file = os.path.splitext(gambar_asli)[0] + "_output.jpeg"
    img.save(final_file, dpi=(dpi, dpi), quality=80)
    print(f"Output sukses: {final_file}")

if __name__ == "__main__":
    proses_gambar('BANNER _ 200X100 _ LP __parameter.txt')
