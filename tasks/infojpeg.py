import cv2
from PIL import Image
import os
import sys
import json

def get_jpeg_info(file_path):
    try:
        # Menggunakan OpenCV untuk membaca gambar dengan cepat
        img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        
        if img is None:
            return {'success': False, 'message': 'File tidak bisa dibaca, pastikan itu JPEG'}

        height, width = img.shape[:2]

        # Membuka dengan Pillow untuk mendapatkan informasi tambahan (DPI, Mode Warna)
        with Image.open(file_path) as pil_img:
            dpi = pil_img.info.get("dpi", (72, 72))  # Default DPI jika tidak ditemukan
            mode = pil_img.mode  # Mode warna (RGB, CMYK, dsb.)

        # Konversi ukuran ke cm berdasarkan DPI
        dpi_x, dpi_y = dpi
        width_cm = (width / dpi_x) * 2.54
        height_cm = (height / dpi_y) * 2.54

        # Mendapatkan ukuran file
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)  # Convert to MB
        file_size_megabits = (file_size * 8) / 1_000_000  # Convert to Mega Bits

        return {
            'success': True,
            'dimensions': f"{width}x{height}",
            'width_cm': round(width_cm, 2),
            'height_cm': round(height_cm, 2),
            'dpi': f"{dpi_x}x{dpi_y}",
            'color_mode': mode if mode in ['RGB', 'CMYK'] else 'Unknown',
            'size_bytes': file_size,
            'size_mb': round(file_size_mb, 2),  # Include size in MB
            'size_megabits': round(file_size_megabits, 2)  # Include size in Mega Bits
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

        info = get_jpeg_info(real)
        
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

    info = get_jpeg_info(file_path)
    print(json.dumps(info))

if __name__ == "__main__":
    main()
