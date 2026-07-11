import os
import sys
import json
from collections import Counter
from PyPDF2 import PdfReader
from PIL import Image
import io

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


def _normalize_color_mode(raw: str) -> str:
    if not raw:
        return "Unknown"
    s = str(raw).replace("/", "").lower()
    if "cmyk" in s or s in ("devicecmyk",):
        return "CMYK"
    if "rgb" in s or s in ("devicergb", "srgb"):
        return "RGB"
    if "gray" in s or s in ("devicegray",):
        return "Gray"
    if "icc" in s:
        return "ICCBased"
    return str(raw).replace("/", "")


def _detect_page_color_pymupdf(file_path: str, page_index: int) -> str:
    if not PYMUPDF_AVAILABLE:
        return "Unknown"
    try:
        doc = fitz.open(file_path)
        try:
            if page_index >= len(doc):
                return "Unknown"
            page = doc[page_index]
            mode = "Unknown"
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha >= 4:
                        mode = "CMYK"
                    elif pix.n - pix.alpha == 3:
                        if mode == "CMYK":
                            return "Natural (Mixed/Unknown)"
                        mode = "RGB"
                    pix = None
                except Exception:
                    continue
            return mode
        finally:
            doc.close()
    except Exception:
        return "Unknown"


def get_pdf_info(file_path):
    try:
        # Buka file PDF dengan PyPDF2
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            
            # Jumlah halaman
            num_pages = len(pdf_reader.pages)
            
            # Get metadata
            metadata = pdf_reader.metadata
            
            # Informasi tentang setiap halaman
            pages_info = []
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    # Get page size
                    page_box = page.mediabox
                    width = float(page_box.width)
                    height = float(page_box.height)
                    
                    # Convert points to mm (1 point = 0.352777777 mm)
                    width_mm = width * 0.352777777
                    height_mm = height * 0.352777777
                    
                    # Convert to cm
                    width_cm = width_mm / 10
                    height_cm = height_mm / 10
                    
                    # Cek jika ada image untuk mendeteksi color mode
                    color_mode = "Unknown"
                    if PYMUPDF_AVAILABLE:
                        color_mode = _detect_page_color_pymupdf(file_path, page_num - 1)
                    if color_mode in ("Unknown",):
                        try:
                            if "/XObject" in page["/Resources"]:
                                xobjects = page["/Resources"]["/XObject"].get_object()
                                for obj in xobjects.values():
                                    obj_ref = obj.get_object()
                                    if obj_ref["/Subtype"] == "/Image":
                                        if "/ColorSpace" in obj_ref:
                                            cs = obj_ref["/ColorSpace"]
                                            if isinstance(cs, list):
                                                color_mode = _normalize_color_mode(str(cs[0]))
                                            else:
                                                color_mode = _normalize_color_mode(str(cs))
                                        break
                        except Exception:
                            color_mode = "Natural (Mixed/Unknown)"
                    else:
                        color_mode = _normalize_color_mode(color_mode)
                    
                    pages_info.append({
                        "page_num": page_num,
                        "width_cm": round(width_cm, 2),
                        "height_cm": round(height_cm, 2),
                        "width_mm": round(width_mm, 2),
                        "height_mm": round(height_mm, 2),
                        "color_mode": color_mode
                    })
                except Exception as e:
                    pages_info.append({
                        "page_num": page_num,
                        "error": str(e)
                    })
            
            # Deteksi color mode umum dari semua halaman
            color_modes = [_normalize_color_mode(p.get("color_mode", "Unknown")) for p in pages_info if "color_mode" in p]
            if color_modes:
                common_color = Counter(color_modes).most_common(1)[0][0]
                if "CMYK" in color_modes and ("RGB" in color_modes or "Natural (Mixed/Unknown)" in color_modes):
                    common_color = "Natural (Mixed/Unknown)"
            else:
                common_color = "Unknown"
            
            # Check apakah semua halaman memiliki ukuran dan orientasi yang sama
            size_check = True
            orientations = []
            sizes = []
            
            for page in pages_info:
                if "width_mm" in page and "height_mm" in page:
                    size_key = (round(page["width_mm"], 1), round(page["height_mm"], 1))
                    sizes.append(size_key)
                    
                    # Tentukan orientasi
                    if page["width_mm"] > page["height_mm"]:
                        orientation = "Horizontal"
                    elif page["width_mm"] < page["height_mm"]:
                        orientation = "Vertical"
                    else:
                        orientation = "Square"
                    orientations.append(orientation)
            
            # Jika ada perbedaan ukuran atau orientasi, set size_check ke False
            if len(set(sizes)) > 1 or len(set(orientations)) > 1:
                size_check = False
            
            # Buat summary string untuk orientasi dan ukuran
            if sizes and orientations:
                first_size = sizes[0]
                first_orientation = orientations[0]
                size_summary = f"{first_size[0]}x{first_size[1]}mm ({first_orientation})"
                if len(set(sizes)) > 1 or len(set(orientations)) > 1:
                    size_summary += " - MIXED"
            else:
                size_summary = "Unknown"
            
            
            # Get file size
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Get creation date
            creation_date = "Unknown"
            if metadata and "/CreationDate" in metadata:
                creation_date = str(metadata["/CreationDate"])
            
            return {
                'success': True,
                'num_pages': num_pages,
                'color_mode': common_color,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size_mb, 2),
                'pages': pages_info,
                'creation_date': creation_date,
                'title': metadata.get('/Title', 'Unknown') if metadata else 'Unknown',
                'size_check': size_check,
                'size_summary': size_summary
            }
            
    except Exception as e:
        return {'success': False, 'message': str(e)}


def run(data):
    filepath = data.get("filepath")

    if not filepath:
        return {"status": "error", "message": "Missing filepath"}

    try:
        real = os.path.realpath(filepath)
        
        # Simple validation: path harus exist dan berupa file
        if not os.path.exists(real):
            return {"status": "error", "message": "File not found"}
        
        if not os.path.isfile(real):
            return {"status": "error", "message": "Path is not a file"}

        info = get_pdf_info(real)
        
        if info.get("success"):
            info["status"] = "success"
            info.pop("success")
        else:
            info["status"] = "error"
            info.pop("success")
        
        return info
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "No file path provided."}))
        return

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(json.dumps({"success": False, "message": "File not found."}))
        return

    info = get_pdf_info(file_path)
    print(json.dumps(info))

if __name__ == "__main__":
    main()
