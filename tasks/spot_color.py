"""
Spot Color PDF Generator — Multi-Channel
=========================================
Menghasilkan PDF dengan satu atau lebih Separation colorspace.
Setiap channel = satu spot color layer terpisah (Spot White, UV Varnish, Die Cut, dst).

Struktur PDF (1 halaman, N spot channels):
  Im0..ImN-1 : spot images (Indexed → Separation)
  ImMain     : gambar utama (DeviceRGB)
  Content stream pakai BMC/BDC/EMC per channel.
"""

import io, os, uuid
import numpy as np
import fitz
from PIL import Image, ImageFilter

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spot_output")

_CALRGB_STR = """[ /CalRGB <<
    /BlackPoint [ 0 0 0 ]
    /Gamma [ 2.2 2.2 2.2 ]
    /Matrix [ 0.412384 0.212646 0.019318 0.357590 0.715164 0.119171
              0.180496 0.072189 0.950546 ]
    /WhitePoint [ 0.950455 1.0 1.08905 ]
  >> ]"""

# Preview RGB per mode (tint=1 → warna ini, tint=0 → white)
_MODE_RGB = {
    "white":   (0.72, 0.72, 0.74),  # abu terang — preview tinta putih
    "varnish": (0.0,  0.78, 1.0),   # cyan — preview pelapis kilap
}
_MODE_NAMES = {
    "white":   "White",
    "varnish": "Varnish",
}

# PS template: proses B dulu, G kedua, R terakhir (agar urutan stack benar)
_PS_TMPL = ("{{dup dup {b:.6f} mul 1.000000 add 3 1 roll "
            "{g:.6f} mul 1.000000 add 3 1 roll "
            "{r:.6f} mul 1.000000 add 3 1 roll}}")


def _ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def _output_pdf_name(image_name: str, out_dir: str) -> str:
    """Nama PDF output berbasis nama file input: A.png -> A.pdf.
    Karakter tak aman dibersihkan; bila file sudah ada, beri sufiks angka."""
    base = os.path.splitext(os.path.basename(image_name or "spot"))[0].strip()
    safe = "".join(c if (c.isalnum() or c in " -_.") else "_" for c in base).strip()
    safe = safe or "spot"
    candidate = f"{safe}.pdf"
    if not os.path.exists(os.path.join(out_dir, candidate)):
        return candidate
    i = 1
    while os.path.exists(os.path.join(out_dir, f"{safe}_{i}.pdf")):
        i += 1
    return f"{safe}_{i}.pdf"


def _encode_name(name: str) -> str:
    out = []
    for ch in name:
        if ch == " ":
            out.append("#20")
        elif ch.isalnum() or ch in "-_.":
            out.append(ch)
        else:
            out.append(f"#{ord(ch):02X}")
    return "".join(out)


def _tint_ps(r: float, g: float, b: float) -> bytes:
    """PostScript FunctionType4: tint=0→white, tint=1→(r,g,b) di CalRGB."""
    ps = _PS_TMPL.format(b=b - 1.0, g=g - 1.0, r=r - 1.0)
    return ps.encode("latin-1")


def _lookup_identity() -> bytes:
    return bytes(range(256))   # pixel 0→tint 0 (no ink), pixel 255→tint 1 (full ink)


def _despeckle_main(img: Image.Image) -> Image.Image:
    """Hapus bintik gelap kecil (JPEG artifact/debu) dari gambar utama.
    Speck = connected component gelap < min_px, diganti dengan nilai median lokal
    sehingga aman untuk background non-putih."""
    from scipy.ndimage import label
    from PIL import ImageFilter
    arr = np.array(img)
    dark = (arr < 200).any(axis=2)
    lab, n = label(dark)
    if n == 0:
        return img
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    min_px = max(50, int(arr.shape[0] * arr.shape[1] * 0.00005))
    speck = np.isin(lab, np.nonzero((sizes > 0) & (sizes < min_px))[0])
    if not speck.any():
        return img
    med = np.array(img.filter(ImageFilter.MedianFilter(7)))
    arr[speck] = med[speck]
    return Image.fromarray(arr)


def _image_dpi(img: Image.Image):
    """DPI dari metadata gambar (pHYs PNG / JFIF), None bila tidak ada."""
    d = img.info.get("dpi")
    if isinstance(d, (tuple, list)) and d:
        try:
            v = float(d[0])
            # PIL sering mengembalikan 599.9988 dst dari konversi meter → bulatkan
            if v > 1:
                return int(round(v))
        except (TypeError, ValueError):
            pass
    return None


def _build_spot_pdf(image_path: str, channels: list, dpi: int, output_path: str):
    """
    image_path : path gambar utama
    channels   : list of dict {name, mode, mask_np}
    dpi        : fallback bila gambar tidak punya metadata DPI

    PENTING: DPI asli dari metadata file DIUTAMAKAN (perilaku Photoshop) —
    kalau dipaksa 300 sementara file 600 dpi, ukuran fisik PDF jadi 2x
    kebesaran dan hasil tampak pecah saat ditempatkan pada ukuran cetak.
    """
    main_img = Image.open(image_path)
    file_dpi = _image_dpi(main_img)
    if file_dpi:
        dpi = file_dpi
    if main_img.mode != "RGB":
        # PNG transparan: composite ke putih, jangan biarkan alpha jadi hitam
        if main_img.mode in ("RGBA", "LA", "PA") or "transparency" in main_img.info:
            rgba = main_img.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.split()[3])
            main_img = bg
        else:
            main_img = main_img.convert("RGB")
    # Artwork dipakai apa adanya — despeckle dimatikan karena menghapus detail
    # kecil yang sah (huruf/titik) pada gambar ber-background terang.
    w_px, h_px = main_img.size
    w_pt = w_px / dpi * 72.0
    h_pt = h_px / dpi * 72.0

    doc  = fitz.open()
    page = doc.new_page(width=w_pt, height=h_pt)
    pxref = page.xref

    # Urutan stacking UV: Varnish di atas, White di bawah.
    # Input masuk [White, Varnish] → tidak di-reverse supaya White digambar
    # pertama (bawah), Varnish digambar terakhir (atas).

    spot_entries = []  # list of (name, im_name, xref_spot_img)

    for idx, ch in enumerate(channels):
        name   = ch["name"]
        mode   = ch["mode"]
        mask_np = ch["mask_np"]
        r, g, b = _MODE_RGB.get(mode, (0.72, 0.72, 0.74))
        name_enc = _encode_name(name)
        im_name  = f"Im{idx}"

        # CalRGB alternate
        xref_calrgb = doc.get_new_xref()
        doc.update_object(xref_calrgb, _CALRGB_STR)

        # Tint function (FunctionType 4, PostScript)
        ps = _tint_ps(r, g, b)
        xref_tf = doc.get_new_xref()
        doc.update_object(xref_tf,
            "<< /FunctionType 4 /Domain [ 0 1 ] /Range [ 0 1 0 1 0 1 ] >>")
        doc.update_stream(xref_tf, ps, compress=False)

        # Separation colorspace
        xref_sep = doc.get_new_xref()
        doc.update_object(xref_sep,
            f"[ /Separation /{name_enc} {xref_calrgb} 0 R {xref_tf} 0 R ]")

        # Lookup table stream (256 bytes, identity)
        xref_lut = doc.get_new_xref()
        doc.update_object(xref_lut, "<< >>")
        doc.update_stream(xref_lut, _lookup_identity(), compress=True)

        # Indexed colorspace → Separation
        xref_idx = doc.get_new_xref()
        doc.update_object(xref_idx,
            f"[ /Indexed {xref_sep} 0 R 255 {xref_lut} 0 R ]")

        # Spot image XObject — WYSIWYG: mask diexport apa adanya sesuai seleksi.
        # CATATAN: JANGAN membuang "blob kecil" di sini. Tiap huruf/detail adalah
        # connected component tersendiri, jadi filter ukuran akan menghapus teks
        # kecil & detail halus yang sengaja diseleksi user.
        mask_img = Image.fromarray(mask_np.astype(np.uint8)).convert("L")
        if mask_img.size != (w_px, h_px):
            mask_img = mask_img.resize((w_px, h_px), Image.NEAREST)

        mask_arr = np.array(mask_img)
        mask_out = np.where(mask_arr > 127, np.uint8(255), np.uint8(0))
        mask_img = Image.fromarray(mask_out, mode="L")

        # Anti-alias tepi seperti Photoshop: blur ringan → nilai grayscale di
        # batas. Indexed→Separation (LUT identitas) memetakan grayscale ke tint
        # parsial, jadi tepi mulus (bukan tangga piksel), 50% tetap di tepi asli.
        aa = max(0.6, min(1.4, (w_px * h_px) ** 0.5 / 2200.0))
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=aa))
        mask_raw  = mask_img.tobytes()

        xref_simg = doc.get_new_xref()
        doc.update_object(xref_simg, f"""<<
  /Type /XObject /Subtype /Image
  /Width {w_px} /Height {h_px}
  /ColorSpace {xref_idx} 0 R
  /BitsPerComponent 8
>>""")
        doc.update_stream(xref_simg, mask_raw, compress=True)

        spot_entries.append((name, im_name, xref_simg))

    # Main image XObject (DeviceRGB)
    main_raw = bytes(np.array(main_img).flatten())
    xref_main = doc.get_new_xref()
    doc.update_object(xref_main, f"""<<
  /Type /XObject /Subtype /Image
  /Width {w_px} /Height {h_px}
  /ColorSpace /DeviceRGB /BitsPerComponent 8
>>""")
    doc.update_stream(xref_main, main_raw, compress=True)

    # ExtGState — hanya /op true (stroke overprint)
    # JANGAN /OP true: akan membuat gambar RGB transparan → spot tembus ke bg
    xref_gs = doc.get_new_xref()
    doc.update_object(xref_gs, "<< /Type /ExtGState /op true >>")

    # Content stream
    mat = f"{w_pt:.4f} 0 0 {h_pt:.4f} 0 0"
    spot_list_pdf = "".join(f"({n})" for n, _, _ in spot_entries)

    lines = []
    lines.append(f"/MultiChannelImage <</MainChannel /RGBColorMode /Spot [{spot_list_pdf}]>>BDC")
    lines.append("/SeparationImages BMC")
    for name, im_name, _ in spot_entries:
        lines.append(f"/SpotImage <</Ink ({name})>>BDC")
        lines.append(f"q\n/GS0 gs\n/RelativeColorimetric ri\n{mat} cm\n/{im_name} Do\nQ")
        lines.append("EMC")
    lines.append("/MainChannelImage BMC")
    lines.append(f"q\n/GS0 gs\n/RelativeColorimetric ri\n{mat} cm\n/ImMain Do\nQ")
    lines.append("EMC\nEMC\nEMC")
    content = "\n".join(lines).encode("latin-1")

    xref_cont = doc.get_new_xref()
    doc.update_object(xref_cont, "<< >>")
    doc.update_stream(xref_cont, content, compress=True)

    # Resources
    xobj_lines = "\n".join(f"    /{im} {xr} 0 R" for _, im, xr in spot_entries)
    xobj_lines += f"\n    /ImMain {xref_main} 0 R"
    res = f"""<<
  /ProcSet [ /PDF /ImageC /ImageI ]
  /XObject <<
{xobj_lines}
  >>
  /ExtGState << /GS0 {xref_gs} 0 R >>
>>"""

    doc.xref_set_key(pxref, "Resources", res)
    doc.xref_set_key(pxref, "Contents",  f"{xref_cont} 0 R")
    doc.xref_set_key(pxref, "MediaBox",  f"[ 0 0 {w_pt:.4f} {h_pt:.4f} ]")
    doc.xref_set_key(pxref, "ArtBox",    f"[ 0 0 {w_pt:.4f} {h_pt:.4f} ]")

    doc.save(output_path, deflate=True, garbage=4, clean=False)
    doc.close()


def _mask_to_np(mask_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(mask_bytes)).convert("L")
    return np.array(img)


# ═══ AUTO MODE (server-side penuh) ═══════════════════════════════════════════
# Preset: Object (alpha>=128) → Contract N px (putih beku) → Apply.
# DTF = channel White; UV = White + Varnish (mask sama).
# Hasil PDF ditulis DI FOLDER YANG SAMA dengan file input, nama sama (.pdf).

def _auto_object_mask(png_path: str, contract_px: int) -> np.ndarray:
    from scipy.ndimage import binary_erosion

    img = Image.open(png_path).convert("RGBA")
    arr = np.array(img)
    obj = arr[:, :, 3] >= 128           # object = non-transparan (>=50% alpha)

    mask = obj
    if contract_px > 0:
        mask = binary_erosion(obj, iterations=int(contract_px))
        # Putih beku: piksel putih mempertahankan status object-nya,
        # tidak ikut menyusut (sama seperti "Kecualikan putih" di editor).
        rgb = arr[:, :, :3]
        white = (rgb >= 245).all(axis=2)
        mask = np.where(white, obj, mask)

    return (mask.astype(np.uint8)) * 255


def run_auto(data: dict) -> dict:
    """
    data: { path: file PNG atau folder di server,
            preset: 'dtf'|'uv', contract_px: int, dpi: int }
    Output: tiap A.png → A.pdf di folder yang sama (overwrite bila ada).
    """
    path        = (data.get("path") or "").strip().strip('"')
    preset      = data.get("preset", "dtf")
    contract_px = max(0, int(data.get("contract_px", 2)))
    dpi         = int(data.get("dpi", 300))
    orient      = data.get("orient", "auto")

    if not path or not os.path.exists(path):
        return {"status": "error", "message": f"Path tidak ditemukan: {path}"}

    if os.path.isdir(path):
        files = sorted(
            os.path.join(path, f) for f in os.listdir(path)
            if f.lower().endswith(".png")
        )
        if not files:
            return {"status": "error", "message": f"Tidak ada file .png di folder: {path}"}
    else:
        if not path.lower().endswith(".png"):
            return {"status": "error", "message": "Auto mode butuh file .png (perlu alpha channel)"}
        files = [path]

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _process_one(fp):
        base = os.path.basename(fp)
        try:
            from PIL import Image as _Img
            need_rotate = False
            if orient != "auto":
                with _Img.open(fp) as _im:
                    w, h = _im.size
                if orient == "vertical" and w > h:
                    need_rotate = True
                elif orient == "horizontal" and h > w:
                    need_rotate = True

            src = fp
            if need_rotate:
                with _Img.open(fp) as _im:
                    rotated = _im.rotate(90, expand=True)
                    src = os.path.splitext(fp)[0] + "_rot_tmp.png"
                    rotated.save(src)

            m = _auto_object_mask(src, contract_px)
            if int(m.sum()) == 0:
                if need_rotate and os.path.exists(src):
                    os.remove(src)
                return {"file": base, "status": "error",
                        "message": "tidak ada object (alpha kosong)"}
            if preset == "uv":
                chans = [
                    {"name": "Varnish", "mode": "varnish", "mask_np": m.copy()},
                    {"name": "White",   "mode": "white",   "mask_np": m},
                ]
            else:
                chans = [{"name": "White", "mode": "white", "mask_np": m}]
            out_pdf = os.path.splitext(fp)[0] + ".pdf"
            _build_spot_pdf(src, chans, dpi, out_pdf)
            # read final dimensions for UI update
            result_info = {"file": base, "status": "success",
                           "output": os.path.basename(out_pdf), "rotated": need_rotate}
            try:
                with _Img.open(src) as _fim:
                    fw, fh = _fim.size
                    fd = _image_dpi(_fim) or dpi
                result_info["w_cm"] = round(fw / fd * 2.54, 1)
                result_info["h_cm"] = round(fh / fd * 2.54, 1)
                result_info["dpi"] = fd
                result_info["orient"] = "Horizontal" if fw >= fh else "Vertical"
            except Exception:
                pass
            if need_rotate and os.path.exists(src):
                os.remove(src)
            return result_info
        except Exception as e:
            return {"file": base, "status": "error", "message": str(e)}

    max_workers = min(len(files), os.cpu_count() or 4)
    results_map = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_process_one, fp): fp for fp in files}
        for fut in as_completed(futures):
            results_map[futures[fut]] = fut.result()

    results = [results_map[fp] for fp in files]
    n_ok = sum(1 for r in results if r["status"] == "success")
    return {"status": "success", "preset": preset, "n_files": len(files),
            "n_success": n_ok, "results": results}


def run(data: dict) -> dict:
    """
    data:
      image_bytes : bytes gambar utama
      image_name  : filename
      dpi         : int
      channels    : list of {name, mode, mask_bytes}
        -- ATAU (legacy single channel) --
      mask_bytes  : bytes
      spot_name   : str
      spot_mode   : str
    """
    # Mode auto: proses file/folder langsung di server (lihat run_auto)
    if data.get("auto"):
        return run_auto(data)

    image_bytes = data.get("image_bytes")
    image_name  = data.get("image_name", "design.jpg")
    dpi         = int(data.get("dpi", 300))

    if not image_bytes:
        return {"status": "error", "message": "image_bytes kosong"}

    # Normalisasi ke format channels list
    channels_raw = data.get("channels")
    if not channels_raw:
        # Legacy single-channel
        mask_bytes = data.get("mask_bytes")
        spot_name  = data.get("spot_name") or _MODE_NAMES.get(data.get("spot_mode", "white"), "Spot Color")
        spot_mode  = data.get("spot_mode", "white")
        if not mask_bytes:
            return {"status": "error", "message": "mask_bytes / channels kosong"}
        channels_raw = [{"name": spot_name, "mode": spot_mode, "mask_bytes": mask_bytes}]

    try:
        out_dir = _ensure_dir()
        uid      = uuid.uuid4().hex[:8]
        # Nama output = nama file input (A.png -> A.pdf). Bila sudah ada,
        # tambahkan sufiks angka agar tidak menimpa (A_1.pdf, A_2.pdf, ...).
        out_name = _output_pdf_name(image_name, out_dir)
        out_path = os.path.join(out_dir, out_name)

        ext = os.path.splitext(image_name)[1].lower() or ".jpg"
        tmp = os.path.join(out_dir, f"_tmp_{uid}{ext}")
        with open(tmp, "wb") as f:
            f.write(image_bytes)

        # Siapkan channels dengan mask numpy
        channels = []
        for ch in channels_raw:
            mb = ch.get("mask_bytes") or ch.get("mask")
            if isinstance(mb, str):
                import base64
                mb = base64.b64decode(mb)
            channels.append({
                "name":    ch.get("name", "Spot Color"),
                "mode":    ch.get("mode", "white"),
                "mask_np": _mask_to_np(mb),
            })

        _build_spot_pdf(tmp, channels, dpi, out_path)

        try:
            os.remove(tmp)
        except Exception:
            pass

        return {
            "status":   "success",
            "filename": out_name,
            "output_path": out_path,
            "channels": [{"name": ch["name"], "mode": ch["mode"]} for ch in channels],
            "n_channels": len(channels),
        }

    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}
