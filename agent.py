from flask import Flask, request, jsonify, render_template_string, send_file, Response
from executor import execute, TASK_MAP
from config import AGENT_SECRET, AGENT_ID
import tempfile
import os
import sys
import datetime
import io
import subprocess
import uuid

try:
    from PIL import Image

    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# In-memory list of exposed paths (no security restrictions per user request)
EXPOSED_PATHS = []

app = Flask(__name__)

_cors_enabled = False
try:
    from flask_cors import CORS

    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    _cors_enabled = True
except ImportError:
    print(
        "WARNING: flask-cors tidak terpasang — memakai CORS header manual.\n"
        "Disarankan: pip install flask-cors",
        file=sys.stderr,
    )


if not _cors_enabled:

    @app.after_request
    def _manual_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        return response

# Simple base directory for the lightweight file explorer (change as needed)
BASE_DIR = r"F:\PESANAN\2026"


def safe_join(base, path):
    full_path = os.path.abspath(os.path.join(base, path))
    if not full_path.startswith(os.path.abspath(base)):
        raise Exception("Access denied")
    return full_path


@app.route("/ui")
def ui_main():
    return render_template_string(
        r"""
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Printing Agent — Menu Utama</title>
    <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:'Segoe UI',system-ui,sans-serif;background:#eef0f3;color:#222;min-height:100vh}

        /* Topbar */
        .topbar{background:#fff;height:52px;padding:0 24px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #e0e0e0;position:sticky;top:0;z-index:10}
        .logo{font-size:17px;font-weight:800;letter-spacing:.5px;color:#1a1a1a}
        .logo span{color:#0066cc}
        .topbar .tag{font-size:11px;color:#888;margin-left:6px}

        .wrap{max-width:960px;margin:0 auto;padding:28px 24px 48px}
        .hero{margin-bottom:26px}
        .hero h1{font-size:22px;font-weight:700;color:#1a1a1a}
        .hero p{font-size:13px;color:#777;margin-top:4px}

        /* Category section */
        .section{margin-bottom:26px}
        .sec-head{display:flex;align-items:center;gap:8px;margin-bottom:12px}
        .sec-head .dot{width:8px;height:8px;border-radius:50%}
        .sec-head h2{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#555}
        .sec-head .line{flex:1;height:1px;background:#e0e0e0}

        /* Tool grid */
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
        .tool{display:flex;gap:12px;align-items:flex-start;background:#fff;border:1px solid #e6e6e6;border-radius:10px;padding:14px 15px 32px;text-decoration:none;color:inherit;transition:all .14s;position:relative;cursor:pointer}
        .api-link{position:absolute;bottom:9px;right:11px;font-size:10px;font-weight:700;color:#0066cc;text-decoration:none;border:1px solid #cfd8e3;background:#f4f8ff;padding:2px 9px;border-radius:10px;letter-spacing:.4px}
        .api-link:hover{background:#0066cc;color:#fff}
        .tool:hover{border-color:#0066cc;box-shadow:0 4px 16px rgba(0,102,204,.10);transform:translateY(-2px)}
        .tool .ico{width:38px;height:38px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#fff}
        .tool .ico svg{width:20px;height:20px}
        .tool .meta{min-width:0}
        .tool .name{font-size:14px;font-weight:700;color:#1a1a1a;margin-bottom:2px}
        .tool .desc{font-size:11.5px;color:#888;line-height:1.35}
        .tool .arrow{position:absolute;top:14px;right:13px;color:#ccc;opacity:0;transition:opacity .14s}
        .tool:hover .arrow{opacity:1;color:#0066cc}

        .footer{text-align:center;font-size:11px;color:#aaa;margin-top:8px}
    </style>
</head>
<body>
    <div class="topbar">
        <span class="logo">PRINTING<span> AGENT</span></span>
        <span class="tag">v1.0</span>
    </div>

    <div class="wrap">
        <div class="hero">
            <h1>Menu Utama</h1>
            <p>Pilih alat sesuai kebutuhan produksi Anda.</p>
        </div>

        <!-- SPOT COLOR / PRODUKSI -->
        <div class="section">
            <div class="sec-head"><span class="dot" style="background:#e91e63"></span><h2>Produksi Cetak</h2><span class="line"></span></div>
            <div class="grid">
                <div class="tool" data-href="/ui/spot-color">
                    <span class="ico" style="background:#e91e63">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="10.5" r="2.5"/><circle cx="8.5" cy="7.5" r="2.5"/><circle cx="6.5" cy="12.5" r="2.5"/><path d="M12 2a10 10 0 0 0 0 20 2.5 2.5 0 0 0 2-4 2.5 2.5 0 0 1 2-4h1a5 5 0 0 0 5-5 10 10 0 0 0-10-7z"/></svg>
                    </span>
                    <span class="meta"><div class="name">Spot Color Tool</div><div class="desc">Buat PDF spot color (White &amp; Varnish) dari desain</div></span>
                    <span class="arrow">→</span>
                </div>
                <div class="tool" data-href="/ui/image-contour">
                    <span class="ico" style="background:#ff6f00">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.12 8.12 12 12M20 4 8.12 15.88"/><path d="M14.8 14.8 20 20"/></svg>
                    </span>
                    <span class="meta"><div class="name">Image Contour</div><div class="desc">Buat garis kontur / cut line dari gambar</div></span>
                    <span class="arrow">→</span>
                </div>
                <div class="tool" data-href="/ui/finishing-editor">
                    <span class="ico" style="background:#00897b">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><path d="M8.12 8.12 12 12"/><path d="M20 4 8.12 15.88"/><circle cx="6" cy="18" r="3"/><path d="M14.8 14.8 20 20"/><path d="M4 12h16"/></svg>
                    </span>
                    <span class="meta"><div class="name">Finishing Editor</div><div class="desc">Tambahkan indikator plong, lebihan, dan pesan pada gambar</div></span>
                    <span class="arrow">→</span>
                </div>
            </div>
        </div>

        <!-- GAMBAR -->
        <div class="section">
            <div class="sec-head"><span class="dot" style="background:#0066cc"></span><h2>Gambar</h2><span class="line"></span></div>
            <div class="grid">
                <div class="tool" data-href="/ui/image-tools">
                    <span class="ico" style="background:#0066cc">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
                    </span>
                    <span class="meta"><div class="name">Image Tools</div><div class="desc">Konversi, resize, CMYK, imposition</div></span>
                    <span class="arrow">→</span>
                </div>
                <div class="tool" data-href="/ui/read-info-form">
                    <span class="ico" style="background:#00838f">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
                    </span>
                    <span class="meta"><div class="name">Image Info</div><div class="desc">Lihat resolusi, DPI, colorspace gambar</div></span>
                    <span class="arrow">→</span>
                </div>
            </div>
        </div>

        <!-- PDF -->
        <div class="section">
            <div class="sec-head"><span class="dot" style="background:#c62828"></span><h2>PDF</h2><span class="line"></span></div>
            <div class="grid">
                <div class="tool" data-href="/ui/merge">
                    <span class="ico" style="background:#c62828">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M12 12v6M9 15h6"/></svg>
                    </span>
                    <span class="meta"><div class="name">Merge PDF</div><div class="desc">Gabungkan beberapa PDF jadi satu file</div></span>
                    <span class="arrow">→</span>
                </div>
                <div class="tool" data-href="/ui/read-pdf-info-form">
                    <span class="ico" style="background:#5e35b1">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><circle cx="11.5" cy="14.5" r="2.5"/><path d="m15 18-1.6-1.6"/></svg>
                    </span>
                    <span class="meta"><div class="name">PDF Info</div><div class="desc">Periksa metadata &amp; struktur PDF</div></span>
                    <span class="arrow">→</span>
                </div>
            </div>
        </div>

        <!-- BERKAS -->
        <div class="section">
            <div class="sec-head"><span class="dot" style="background:#455a64"></span><h2>Berkas</h2><span class="line"></span></div>
            <div class="grid">
                <div class="tool" data-href="/ui/file-explorer">
                    <span class="ico" style="background:#455a64">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/></svg>
                    </span>
                    <span class="meta"><div class="name">File Explorer</div><div class="desc">Jelajah &amp; kelola berkas di server</div></span>
                    <span class="arrow">→</span>
                </div>
            </div>
        </div>

        <div class="footer">Printing Agent — internal tools · <a href="/ui/api-docs" style="color:#0066cc">Dokumentasi API</a></div>
    </div>
    <script>
    // Kartu bisa diklik + chip "API" per tool menuju dokumentasi bagiannya
    const API_MAP = {
        '/ui/spot-color':        'spot-color',
        '/ui/image-contour':     'image-contour',
        '/ui/finishing-editor':  'finishing-editor',
        '/ui/image-tools':       'image-tools',
        '/ui/read-info-form':    'image-info',
        '/ui/merge':             'merge-pdf',
        '/ui/read-pdf-info-form':'pdf-info',
        '/ui/file-explorer':     'file-explorer',
    };
    document.querySelectorAll('.tool[data-href]').forEach(card=>{
        card.addEventListener('click', ()=>{ location.href = card.dataset.href; });
        const id = API_MAP[card.dataset.href];
        if(id){
            const a = document.createElement('a');
            a.className = 'api-link';
            a.href = '/ui/api-docs#' + id;
            a.textContent = '⟨/⟩ API';
            a.addEventListener('click', e=>e.stopPropagation());
            card.appendChild(a);
        }
    });
    </script>
</body>
</html>
        """
    )


@app.route("/ui/merge", methods=["GET"])
def ui_merge_page():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "merge_pdf.html")
    with open(html_path, encoding="utf-8") as handle:
        return handle.read()


@app.route("/ui/pdf-color-info", methods=["POST"])
def ui_pdf_color_info():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"status": "error", "message": "No file"}), 400
        import fitz as fitz_mod

        data = file.read()
        doc = fitz_mod.open(stream=data, filetype="pdf")
        page = doc[0]
        color_spaces = set()
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                ei = doc.extract_image(xref)
                cs_n = ei.get("colorspace", 0)
                if cs_n == 4:
                    color_spaces.add("CMYK")
                elif cs_n == 3:
                    color_spaces.add("RGB")
                elif cs_n == 1:
                    color_spaces.add("Grayscale")
            except Exception:
                cs_name = img[5] if len(img) > 5 else ""
                if "CMYK" in cs_name.upper():
                    color_spaces.add("CMYK")
                elif "RGB" in cs_name.upper():
                    color_spaces.add("RGB")
                elif cs_name:
                    color_spaces.add(cs_name)
        doc.close()
        mode = ", ".join(sorted(color_spaces)) if color_spaces else "Unknown"
        return jsonify({"status": "success", "color_mode": mode, "spaces": list(color_spaces)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/file-explorer")
def ui_file_explorer():
    return render_template_string(
        r"""
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>File Explorer — Printing Agent</title>
<style>
  :root{
    --bg-base:#eef0f3;
    --bg-panel:#ffffff;
    --bg-inset:#f6f8fa;
    --line:rgba(0,0,0,0.045);
    --line-strong:#d9dee5;
    --cyan:#0066cc;
    --cyan-dim:#7aa7d4;
    --text:#222222;
    --text-dim:#667080;
    --text-faint:#98a2ad;
    --mono: ui-monospace, "SF Mono", "Cascadia Mono", "Roboto Mono", Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{
    background:
      linear-gradient(var(--line) 1px, transparent 1px) 0 0/28px 28px,
      linear-gradient(90deg, var(--line) 1px, transparent 1px) 0 0/28px 28px,
      var(--bg-base);
    color:var(--text);
    font-family:var(--sans);
    min-height:100vh;
    -webkit-font-smoothing:antialiased;
  }
  header{
    padding:22px 24px 16px;
    border-bottom:1px solid var(--line-strong);
    display:flex;
    align-items:baseline;
    gap:14px;
    flex-wrap:wrap;
  }
  header .mark{
    font-family:var(--mono); font-size:12px; color:var(--cyan);
    border:1px solid var(--cyan-dim); padding:3px 8px; border-radius:3px; letter-spacing:0.08em;
  }
  header h1{ font-size:19px; margin:0; font-weight:600; }
  header p{ margin:0; color:var(--text-dim); font-size:13px; font-family:var(--mono); }
  header .back{
    margin-left:auto; color:var(--text-dim); text-decoration:none; font-size:13px;
    border:1px solid var(--line-strong); padding:6px 12px; border-radius:5px;
  }
  header .back:hover{border-color:var(--cyan); color:var(--cyan);}

  .layout{ display:grid; grid-template-columns:240px 1fr; gap:0; min-height:calc(100vh - 76px); }
  @media (max-width: 880px){ .layout{grid-template-columns:1fr;} }

  .sidebar{
    background:var(--bg-panel); border-right:1px solid var(--line-strong); padding:20px; overflow-y:auto;
  }
  .section-label{
    font-family:var(--mono); font-size:10.5px; letter-spacing:0.1em; color:var(--text-faint);
    text-transform:uppercase; margin-bottom:10px;
  }
  .drives{list-style:none;padding:0;margin:0 0 20px 0;}
  .drives li{
    padding:8px 10px; border-radius:5px; cursor:pointer; font-size:13px; color:var(--text-dim);
    font-family:var(--mono); transition:background .12s, color .12s;
  }
  .drives li:hover{background:rgba(0,102,204,0.06); color:var(--cyan);}
  .drives li.active{background:rgba(0,102,204,0.1); color:var(--cyan); font-weight:600;}
  .current-path{
    font-family:var(--mono); font-size:11.5px; color:var(--text-dim);
    word-break:break-all; line-height:1.5; padding:10px 12px;
    background:var(--bg-inset); border:1px solid var(--line-strong); border-radius:5px;
  }

  .main-area{ padding:20px; display:flex; flex-direction:column; gap:14px; min-width:0; }

  .toolbar{
    display:flex; gap:8px; align-items:center; flex-wrap:wrap;
  }
  .toolbar .path-display{
    flex:1; font-family:var(--mono); font-size:12px; color:var(--text-dim);
    padding:7px 12px; background:var(--bg-inset); border:1px solid var(--line-strong);
    border-radius:5px; min-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  }
  .btn-tool{
    background:transparent; color:var(--text-dim); border:1px solid var(--line-strong);
    padding:7px 14px; border-radius:5px; cursor:pointer; font-size:12.5px; font-family:var(--sans);
    transition:border-color .12s, color .12s;
  }
  .btn-tool:hover{border-color:var(--cyan); color:var(--cyan);}
  .btn-tool svg{width:14px;height:14px;vertical-align:-2px;margin-right:4px;}

  .file-table-wrap{
    background:var(--bg-panel); border:1px solid var(--line-strong); border-radius:6px;
    overflow:hidden; flex:1;
  }
  table{width:100%;border-collapse:collapse;}
  th{
    padding:10px 14px; text-align:left; font-family:var(--mono); font-size:10.5px;
    letter-spacing:0.08em; text-transform:uppercase; color:var(--text-faint);
    background:var(--bg-inset); border-bottom:1px solid var(--line-strong);
  }
  td{
    padding:9px 14px; font-size:13px; color:var(--text-dim); border-bottom:1px solid var(--line);
  }
  tr.row{cursor:pointer; transition:background .1s;}
  tr.row:hover{background:rgba(0,102,204,0.04);}
  tr.row .name-cell{color:var(--text); font-weight:500;}
  tr.row .name-cell .icon{margin-right:8px; font-size:15px; vertical-align:-1px;}
  tr.row .size-cell, tr.row .date-cell{font-family:var(--mono); font-size:12px;}
  tr.row .type-badge{
    font-family:var(--mono); font-size:10px; letter-spacing:0.06em; text-transform:uppercase;
    padding:2px 7px; border-radius:3px; background:var(--bg-inset); border:1px solid var(--line-strong);
  }
  tr.row-up td{color:var(--cyan); font-weight:600; font-size:13px;}
  tr.row-up:hover td{background:rgba(0,102,204,0.06);}

  .empty-state{
    padding:60px 20px; text-align:center; color:var(--text-faint);
    font-family:var(--mono); font-size:13px;
  }

  /* Modal */
  .modal-overlay{
    position:fixed; inset:0; background:rgba(0,0,0,0.45); display:none; z-index:9999;
    align-items:center; justify-content:center; backdrop-filter:blur(2px);
  }
  .modal-overlay.show{display:flex;}
  .modal-box{
    width:92%; max-width:1000px; background:var(--bg-panel); border-radius:8px;
    box-shadow:0 12px 48px rgba(0,0,0,0.2); overflow:hidden;
  }
  .modal-header{
    display:flex; justify-content:space-between; align-items:center;
    padding:14px 18px; border-bottom:1px solid var(--line-strong);
  }
  .modal-header h3{margin:0; font-size:16px; font-weight:600;}
  .modal-close{
    background:transparent; border:1px solid var(--line-strong); color:var(--text-dim);
    width:32px; height:32px; border-radius:5px; cursor:pointer; font-size:16px;
    display:flex; align-items:center; justify-content:center;
  }
  .modal-close:hover{border-color:var(--cyan); color:var(--cyan);}
  .modal-body{display:flex; gap:0; min-height:420px;}
  .modal-preview{
    flex:1; background:var(--bg-inset); display:flex; align-items:center;
    justify-content:center; padding:16px; overflow:auto; border-right:1px solid var(--line-strong);
  }
  .modal-info{width:340px; max-height:520px; overflow-y:auto; padding:16px;}
  .info-grid{display:grid; grid-template-columns:1fr 1fr; gap:8px;}
  .info-card{
    background:var(--bg-inset); padding:10px 12px; border-radius:5px;
    border:1px solid var(--line-strong);
  }
  .info-card .label{
    font-family:var(--mono); font-size:10px; letter-spacing:0.08em;
    text-transform:uppercase; color:var(--text-faint); margin-bottom:4px;
  }
  .info-card .value{font-size:15px; font-weight:600; color:var(--text);}
  .pdf-header{
    background:var(--cyan); color:#fff; padding:16px; border-radius:6px; margin-bottom:12px;
  }
  .pdf-header .row{
    display:flex; justify-content:space-between; padding:6px 0;
    border-bottom:1px solid rgba(255,255,255,0.2); font-size:12px;
  }
  .pdf-header .row:last-child{border-bottom:none;}
  .pdf-header .row .k{opacity:0.8; text-transform:uppercase; font-family:var(--mono); font-size:10px; letter-spacing:0.06em;}
  .pdf-header .row .v{font-weight:600;}
  .pdf-page-item{
    background:var(--bg-inset); padding:8px 10px; border-left:3px solid var(--cyan);
    margin-bottom:6px; border-radius:0 4px 4px 0; font-size:11px; color:var(--text-dim);
  }
</style>
</head>
<body>

<header>
  <span class="mark">PRINTING AGENT</span>
  <h1>File Explorer</h1>
  <p>Browse &middot; Preview &middot; File info</p>
  <a class="back" href="/ui">&larr; Menu</a>
</header>

<div class="layout">
  <div class="sidebar">
    <div class="section-label">Drives</div>
    <ul id="drives" class="drives"></ul>
    <div class="section-label">Current Path</div>
    <div id="currentPath" class="current-path">/</div>
  </div>

  <div class="main-area">
    <div class="toolbar">
      <div class="path-display" id="pathDisplay">/</div>
      <button class="btn-tool" id="upBtn" title="Up">&#9650; Up</button>
      <button class="btn-tool" id="refreshBtn" title="Refresh">&#8635; Refresh</button>
    </div>

    <div class="file-table-wrap">
      <table>
        <thead>
          <tr><th style="width:48%">Name</th><th style="width:12%">Type</th><th style="width:20%">Size</th><th style="width:20%">Modified</th></tr>
        </thead>
        <tbody id="fileTable"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- Preview Modal -->
<div class="modal-overlay" id="previewModal">
  <div class="modal-box">
    <div class="modal-header">
      <h3>Informasi &amp; Preview</h3>
      <button class="modal-close" id="modalCloseBtn">&times;</button>
    </div>
    <div class="modal-body">
      <div class="modal-preview" id="modalPreview"></div>
      <div class="modal-info" id="modalInfo"></div>
    </div>
  </div>
</div>

<script>
let currentPath = "";
let activeDrive = "";

async function loadDrives(){
    try{
        const res = await fetch('/ui/drives');
        const data = await res.json();
        const el = document.getElementById('drives'); el.innerHTML='';
        (data.drives||[]).forEach(d=>{
            const li = document.createElement('li');
            li.textContent = d;
            li.addEventListener('click', ()=>{ activeDrive=d; loadFolder(d); });
            el.appendChild(li);
        });
    }catch(e){console.warn(e);}
}

function fmtBytes(n){ if(n===null||n===undefined) return '-'; if(n<1024) return n+' B'; const units=['KB','MB','GB','TB']; let i=-1; do{n=n/1024;i++;}while(n>=1024&&i<units.length-1); return n.toFixed(1)+' '+units[i]; }

async function loadFolder(path=''){
    try{
        const q = '/api/list?path='+encodeURIComponent(path||'');
        const res = await fetch(q); if(!res.ok){ const t=await res.text(); alert(t); return; }
        const data = await res.json();
        currentPath = data.current_path||'';
        const dp = (currentPath||'\\').replace(/\\\\/g,'\\');
        document.getElementById('currentPath').textContent = dp;
        document.getElementById('pathDisplay').textContent = dp;

        // highlight active drive
        document.querySelectorAll('#drives li').forEach(li=>{
            li.classList.toggle('active', currentPath.startsWith(li.textContent));
        });

        const tbody = document.getElementById('fileTable'); tbody.innerHTML='';

        if(currentPath){
            const upRow = document.createElement('tr'); upRow.className='row row-up';
            upRow.innerHTML='<td colspan="4"><span style="margin-right:6px">&#9650;</span>.. (Up)</td>';
            upRow.addEventListener('click', ()=>{ const parts=currentPath.split('\\\\').filter(Boolean); parts.pop(); loadFolder(parts.join('\\\\')); });
            tbody.appendChild(upRow);
        }

        (data.items||[]).forEach(it=>{
            const tr = document.createElement('tr'); tr.className='row';
            const nameCell = document.createElement('td'); nameCell.className='name-cell';
            nameCell.innerHTML = '<span class="icon">'+(it.type==='folder'?'&#128193;':'&#128196;')+'</span>' + it.name;
            const typeCell = document.createElement('td');
            typeCell.innerHTML = '<span class="type-badge">'+it.type+'</span>';
            const sizeCell = document.createElement('td'); sizeCell.className='size-cell'; sizeCell.textContent = fmtBytes(it.size);
            const modCell = document.createElement('td'); modCell.className='date-cell'; modCell.textContent = it.last_modified||'-';

            tr.addEventListener('dblclick', ()=>{
                if(it.type==='folder'){
                    loadFolder(currentPath ? currentPath+'\\\\'+it.name : it.name);
                } else {
                    previewModalOpen(currentPath ? currentPath+'\\\\'+it.name : it.name);
                }
            });

            tr.appendChild(nameCell); tr.appendChild(typeCell); tr.appendChild(sizeCell); tr.appendChild(modCell);
            tbody.appendChild(tr);
        });

        if(!data.items||data.items.length===0){
            const tr = document.createElement('tr');
            tr.innerHTML='<td colspan="4" class="empty-state">Folder kosong</td>';
            tbody.appendChild(tr);
        }
    }catch(e){ alert(e.message); }
}

document.getElementById('refreshBtn').addEventListener('click', ()=>loadFolder(currentPath));
document.getElementById('upBtn').addEventListener('click', ()=>{ const parts=currentPath.split('\\\\').filter(Boolean); parts.pop(); loadFolder(parts.join('\\\\')); });

(async function(){ await loadDrives(); await loadFolder(''); })();

// --- pdf.js ---
const pdfScript = document.createElement('script');
pdfScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
document.head.appendChild(pdfScript);

// --- Modal ---
const modalEl = document.getElementById('previewModal');
const modalPreview = document.getElementById('modalPreview');
const modalInfo = document.getElementById('modalInfo');

function closeModal(){ modalEl.classList.remove('show'); modalPreview.innerHTML=''; modalInfo.innerHTML=''; }
document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
modalEl.addEventListener('click', ev=>{ if(ev.target===modalEl) closeModal(); });
document.addEventListener('keydown', ev=>{ if(ev.key==='Escape') closeModal(); });

function previewModalOpen(filepath){
    modalEl.classList.add('show');
    modalPreview.innerHTML = '<div style="color:var(--text-faint);font-family:var(--mono);font-size:13px">Loading...</div>';
    modalInfo.innerHTML = '';

    (async ()=>{
        try{
            const ires = await fetch('/api/file-info?filepath='+encodeURIComponent(filepath));
            let infoData = null;
            if(ires.ok){ infoData = await ires.json(); }

            const ext = filepath.split('.').pop().toLowerCase();
            const url = '/ui/read-file?filepath='+encodeURIComponent(filepath);

            if(['jpg','jpeg','png','gif','webp','bmp'].includes(ext)){
                modalPreview.innerHTML = '';
                const img = document.createElement('img');
                img.src = url;
                img.style.cssText = 'max-width:100%;max-height:400px;object-fit:contain;border-radius:4px;';
                modalPreview.appendChild(img);
                img.onload = ()=>{
                    if(infoData && infoData.status === 'success'){
                        modalInfo.innerHTML = '<div class="info-grid">'
                          +'<div class="info-card"><div class="label">Dimensi (PX)</div><div class="value">'+(infoData.dimensions||(img.naturalWidth+'x'+img.naturalHeight))+'</div></div>'
                          +'<div class="info-card"><div class="label">Lebar (CM)</div><div class="value">'+(infoData.width_cm||'-')+'</div></div>'
                          +'<div class="info-card"><div class="label">Tinggi (CM)</div><div class="value">'+(infoData.height_cm||'-')+'</div></div>'
                          +'<div class="info-card"><div class="label">DPI</div><div class="value">'+(infoData.dpi||'-')+'</div></div>'
                          +'<div class="info-card"><div class="label">Mode Warna</div><div class="value">'+(infoData.color_mode||'-')+'</div></div>'
                          +'<div class="info-card"><div class="label">Ukuran (Bytes)</div><div class="value">'+(infoData.size_bytes||'-')+'</div></div>'
                          +'<div class="info-card"><div class="label">Ukuran (MB)</div><div class="value">'+(infoData.size_mb||'-')+'</div></div>'
                          +'<div class="info-card"><div class="label">Ukuran (Mbps)</div><div class="value">'+(infoData.size_megabits||'-')+'</div></div>'
                          +'</div>';
                    } else {
                        modalInfo.innerHTML = '<div class="info-grid"><div class="info-card" style="grid-column:1/3"><div class="label">Dimensi (PX)</div><div class="value">'+img.naturalWidth+'&times;'+img.naturalHeight+'</div></div></div>';
                    }
                };
            } else if(ext === 'pdf'){
                const waitPdf = () => new Promise((y,n)=>{ if(window.pdfjsLib) return y(); let i=0; const t=setInterval(()=>{ if(window.pdfjsLib){clearInterval(t);y();} if(++i>50){clearInterval(t);n('pdf.js load timeout');} },100); });
                await waitPdf();
                try{
                    const pdfRes = await fetch(url);
                    if(!pdfRes.ok) throw new Error('HTTP '+pdfRes.status);
                    const arrayBuf = await pdfRes.arrayBuffer();
                    if(arrayBuf.byteLength===0) throw new Error('PDF file is empty');
                    const pdf = await window.pdfjsLib.getDocument({data:arrayBuf}).promise;
                    const page = await pdf.getPage(1);
                    const bv = page.getViewport({scale:1});
                    const scale = 280/bv.width;
                    const vp = page.getViewport({scale});
                    const canvas = document.createElement('canvas'); canvas.width=vp.width; canvas.height=vp.height;
                    canvas.style.cssText='max-width:100%;height:auto;border-radius:4px;';
                    await page.render({canvasContext:canvas.getContext('2d'), viewport:vp}).promise;
                    modalPreview.innerHTML=''; modalPreview.appendChild(canvas);

                    if(infoData && infoData.status === 'success'){
                        const dp = (infoData.actual_file_path||filepath).replace(/\\\\/g,'\\');
                        let html = '<div class="pdf-header">';
                        html += '<div class="row"><span class="k">File</span><span class="v" style="font-size:10px;word-break:break-all;max-width:200px">'+dp+'</span></div>';
                        html += '<div class="row"><span class="k">Halaman</span><span class="v">'+infoData.num_pages+'</span></div>';
                        html += '<div class="row"><span class="k">Mode Warna</span><span class="v">'+(infoData.color_mode||'-')+'</span></div>';
                        html += '<div class="row"><span class="k">Ukuran</span><span class="v">'+(infoData.file_size_mb||'-')+' MB</span></div>';
                        if(infoData.size_check !== undefined){
                            html += '<div class="row"><span class="k">Size Check</span><span class="v" style="color:'+(infoData.size_check?'#a5d6a7':'#ffcc80')+'">'+(infoData.size_check?'&#10003; TRUE':'&#10007; FALSE')+'</span></div>';
                        }
                        html += '</div>';
                        if(infoData.pages && infoData.pages.length>0){
                            html += '<div class="section-label" style="margin-top:14px">Detail Halaman</div>';
                            infoData.pages.forEach(pg=>{
                                if(!pg.error){
                                    html += '<div class="pdf-page-item"><strong>Hal '+pg.page_num+'</strong> &mdash; L: '+pg.width_cm+'cm &times; T: '+pg.height_cm+'cm</div>';
                                }
                            });
                        }
                        modalInfo.innerHTML = html;
                    } else {
                        modalInfo.innerHTML = '<div class="pdf-header"><div class="row"><span class="k">Halaman</span><span class="v">'+pdf.numPages+'</span></div></div>';
                    }
                }catch(e){ modalPreview.innerHTML='<div style="color:#c62828;font-family:var(--mono);font-size:12px">'+e.message+'</div>'; }
            } else {
                modalPreview.innerHTML = '<div style="color:var(--text-faint);font-family:var(--mono);font-size:13px">No preview for this file type</div>';
            }
        }catch(e){ modalPreview.innerHTML='<div style="color:#c62828;font-family:var(--mono);font-size:12px">'+e.message+'</div>'; }
    })();
}
</script>
</body>
</html>
        """
    )


@app.route("/api/list")
def api_list():
    rel_path = request.args.get("path", "")
    # Allow absolute paths or paths relative to BASE_DIR. No access restrictions (per user request).
    if rel_path:
        if os.path.isabs(rel_path):
            full_path = rel_path
        else:
            full_path = os.path.join(BASE_DIR, rel_path)
    else:
        full_path = BASE_DIR

    if not os.path.exists(full_path):
        fallback = full_path
        while fallback and not os.path.exists(fallback):
            parent = os.path.dirname(fallback)
            if parent == fallback:
                break
            fallback = parent
        if os.path.exists(fallback) and os.path.isdir(fallback):
            full_path = fallback
        else:
            return jsonify({"current_path": "", "items": [], "warning": "Path not found"})

    items = []
    for name in sorted(os.listdir(full_path)):
        item_path = os.path.join(full_path, name)
        is_dir = os.path.isdir(item_path)
        try:
            stat = os.stat(item_path)
            size = stat.st_size if not is_dir else None
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            size = None
            mtime = None

        items.append(
            {
                "name": name,
                "type": "folder" if is_dir else "file",
                "size": size,
                "last_modified": mtime,
            }
        )

    return jsonify({"current_path": full_path, "items": items})


@app.route("/api/stat")
def api_stat():
    filepath = request.args.get("filepath")
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "Not found"}), 404
    try:
        stat = os.stat(filepath)
        return jsonify(
            {
                "path": filepath,
                "is_dir": os.path.isdir(filepath),
                "size": stat.st_size,
                "last_modified": datetime.datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/file-info")
def api_file_info():
    filepath = request.args.get("filepath")
    if not filepath or not os.path.exists(filepath):
        return jsonify({"status": "error", "message": "File not found"}), 404
    ext = filepath.split(".").pop().lower()
    try:
        if ext == "pdf":
            res = execute("read_pdf_info", {"filepath": filepath})
            return jsonify(res)
        elif ext in ("jpg", "jpeg", "png", "gif", "webp", "bmp"):
            res = execute("read_info", {"filepath": filepath})
            return jsonify(res)
        else:
            # fallback to basic stat
            stat = os.stat(filepath)
            return jsonify(
                {
                    "status": "success",
                    "file_size_bytes": stat.st_size,
                    "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                }
            )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/open-path", methods=["POST"])
def api_open_path():
    data = request.get_json() or {}
    filepath = data.get("filepath")
    if not filepath:
        return jsonify({"ok": False, "error": "missing filepath"}), 400
    # normalize path
    filepath = filepath.replace("/", "\\") if os.name == "nt" else filepath
    filepath = os.path.abspath(filepath)
    try:
        if not os.path.exists(filepath):
            return jsonify({"ok": False, "error": "path does not exist"}), 404
        # If directory, open it. If file, try to select it in Explorer on Windows or open containing folder otherwise.
        if os.path.isdir(filepath):
            if os.name == "nt":
                subprocess.Popen(["explorer", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
        else:
            if os.name == "nt":
                # /select, will open Explorer and select the file
                subprocess.Popen(["explorer", "/select,", filepath])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/write-file", methods=["POST"])
def api_write_file():
    try:
        payload = request.get_json(silent=True) or {}
        dest_path = request.form.get("path") or payload.get("path")
        if not dest_path or not str(dest_path).strip():
            return jsonify({"ok": False, "error": "missing path"}), 400

        dest_path = str(dest_path).strip()
        dest_path = dest_path.replace("/", "\\") if os.name == "nt" else dest_path
        dest_path = os.path.abspath(dest_path)

        parent = os.path.dirname(dest_path)
        if not parent or not os.path.isdir(parent):
            return jsonify({"ok": False, "error": "destination folder not found"}), 404

        upload = request.files.get("file")
        if upload:
            data = upload.read()
        else:
            b64 = payload.get("data_base64")
            if not b64:
                return jsonify({"ok": False, "error": "missing file"}), 400
            import base64

            data = base64.b64decode(b64)

        if not data:
            return jsonify({"ok": False, "error": "empty file"}), 400

        with open(dest_path, "wb") as handle:
            handle.write(data)

        return jsonify({"ok": True, "path": dest_path, "size": len(data)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/ui/read-file")
def ui_read_file():
    filepath = request.args.get("filepath")
    if not filepath:
        return ("Missing filepath parameter", 400)
    # Normalize path (handle both forward and backslashes)
    filepath = filepath.replace("/", "\\") if os.name == "nt" else filepath
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        return (f"File not found: {filepath}", 404)
    try:
        # Determine MIME type based on file extension
        ext = filepath.split(".")[-1].lower()
        if ext == "pdf":
            mimetype = "application/pdf"
        elif ext in ["jpg", "jpeg"]:
            mimetype = "image/jpeg"
        elif ext == "png":
            mimetype = "image/png"
        elif ext == "gif":
            mimetype = "image/gif"
        elif ext == "webp":
            mimetype = "image/webp"
        else:
            mimetype = "application/octet-stream"

        # Read file and return as Response to ensure proper headers
        with open(filepath, "rb") as f:
            data = f.read()

        response = Response(data, mimetype=mimetype)
        response.headers["Content-Disposition"] = 'inline; filename=""'
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Length"] = len(data)
        return response
    except Exception as e:
        return (f"Error reading file: {str(e)}", 500)


@app.route("/ui/thumbnail")
def ui_thumbnail():
    filepath = request.args.get("filepath")
    if not filepath:
        return ("Missing filepath parameter", 400)
    # Normalize path (handle both forward and backslashes)
    filepath = filepath.replace("/", "\\") if os.name == "nt" else filepath
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        return (f"File not found: {filepath}", 404)
    # If Pillow is available, generate a small webp thumbnail (10% scale, quality=10)
    try:
        if PIL_AVAILABLE:
            try:
                with open(filepath, "rb") as f:
                    img = Image.open(f)
                    img = img.convert("RGB")
                    w, h = img.size
                    new_w = max(1, int(w * 0.1))
                    new_h = max(1, int(h * 0.1))
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                    bio = io.BytesIO()
                    img.save(bio, format="WEBP", quality=10, method=6)
                    data = bio.getvalue()
                    response = Response(data, mimetype="image/webp")
                    response.headers["Content-Disposition"] = 'inline; filename=""'
                    response.headers["Cache-Control"] = "public, max-age=60"
                    response.headers["X-Content-Type-Options"] = "nosniff"
                    response.headers["Content-Length"] = len(data)
                    return response
            except Exception:
                # fallthrough to serve original file if thumbnail generation fails
                pass

        # Fallback: serve original file (same behavior as ui_read_file)
        with open(filepath, "rb") as f:
            data = f.read()
        # Attempt to guess web-friendly mime
        ext = filepath.split(".")[-1].lower()
        if ext in ["jpg", "jpeg"]:
            mimetype = "image/jpeg"
        elif ext == "png":
            mimetype = "image/png"
        elif ext == "gif":
            mimetype = "image/gif"
        elif ext == "webp":
            mimetype = "image/webp"
        else:
            mimetype = "application/octet-stream"
        response = Response(data, mimetype=mimetype)
        response.headers["Content-Disposition"] = 'inline; filename=""'
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Length"] = len(data)
        return response
    except Exception as e:
        return (f"Error reading file: {str(e)}", 500)


@app.route("/ui/preview")
def ui_preview():
    return render_template_string(
        r"""
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>File Preview</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
            <style>
                body{font-family:'Segoe UI',system-ui,sans-serif;background:#eef0f3;min-height:100vh;padding:20px;color:#222}
                .card{background:#fff;color:#333;border-radius:10px;padding:16px;box-shadow:0 2px 10px rgba(0,0,0,0.06);border:1px solid #e4e4e4;max-width:1100px;margin:0 auto}
                .layout{display:grid;grid-template-columns:1fr 420px;gap:12px}
                .preview{background:#f5f7ff;padding:8px;border-radius:6px;min-height:420px;display:flex;align-items:center;justify-content:center}
                .info{padding:8px}
                .muted{color:#666}
                canvas{max-width:100%;height:auto}
                img{max-width:100%;height:auto}
            </style>
        </head>
        <body>
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <h2 style="margin:0">File Preview</h2>
                    <div><a href="/ui"><button style="background:#0066cc;color:#fff;border:none;padding:6px 10px;border-radius:6px">Close</button></a></div>
                </div>
                <div class="layout">
                    <div>
                        <div id="preview" class="preview"><div class="muted">Loading preview...</div></div>
                    </div>
                    <div class="info">
                        <h3 id="name">-</h3>
                        <div class="muted" id="path">-</div>
                        <div style="height:12px"></div>
                        <div><strong>Size:</strong> <span id="size">-</span></div>
                        <div><strong>Modified:</strong> <span id="mtime">-</span></div>
                        <div style="height:12px"></div>
                        <div id="extra"></div>
                    </div>
                </div>
            </div>

            <script>
                const params = new URLSearchParams(window.location.search);
                const filepath = params.get('filepath');
                if(!filepath){ document.getElementById('preview').innerText = 'No file specified'; }

                async function stat(){
                    const res = await fetch('/api/stat?filepath='+encodeURIComponent(filepath));
                    if(!res.ok){ document.getElementById('preview').innerText = 'Not found'; return; }
                    return await res.json();
                }

                function showImage(url){
                    const img = document.createElement('img'); img.src = url; img.alt='image';
                    const p = document.getElementById('preview'); p.innerHTML=''; p.appendChild(img);
                    img.onload = ()=>{ document.getElementById('extra').innerHTML = `<div><strong>Dimensions:</strong> ${img.naturalWidth} × ${img.naturalHeight}</div>`; };
                }

                async function showPDF(url){
                    const arrayBuf = await fetch(url).then(r=>r.arrayBuffer());
                    const pdf = await pdfjsLib.getDocument({data:arrayBuf}).promise;
                    const page = await pdf.getPage(1);
                    const viewport = page.getViewport({scale:1.5});
                    const canvas = document.createElement('canvas'); canvas.width = viewport.width; canvas.height = viewport.height;
                    const ctx = canvas.getContext('2d');
                    await page.render({canvasContext:ctx, viewport}).promise;
                    const p = document.getElementById('preview'); p.innerHTML=''; p.appendChild(canvas);
                    document.getElementById('extra').innerHTML = `<div><strong>Pages:</strong> ${pdf.numPages}</div>`;
                }

                (async ()=>{
                    const s = await stat();
                    document.getElementById('name').textContent = filepath.split('\\\\').pop();
                    document.getElementById('path').textContent = filepath.replace(/\\\\/g,'\\');
                    document.getElementById('size').textContent = s.size ? (s.size/1024).toFixed(2)+' KB' : '-';
                    document.getElementById('mtime').textContent = s.last_modified || '-';

                    const ext = filepath.split('.').pop().toLowerCase();
                    const fileUrl = '/ui/read-file?filepath='+encodeURIComponent(filepath);
                    if(['jpg','jpeg','png','gif','webp','bmp'].includes(ext)){
                        showImage(fileUrl);
                    } else if(ext === 'pdf'){
                        showPDF(fileUrl);
                    } else {
                        document.getElementById('preview').innerHTML = '<div class="muted">No preview available for this file type.</div>';
                    }
                })();
            </script>
        </body>
        </html>
        """
    )


@app.route("/ui/list-dir", methods=["POST"])
def ui_list_dir():
    try:
        data = request.get_json(silent=True) or {}
        path = data.get("path") or os.path.expanduser("~")
        # Normalize and prevent empty
        path = os.path.abspath(path)
        if not os.path.exists(path):
            return jsonify({"status": "error", "message": "Path not found"}), 400
        if not os.path.isdir(path):
            # if a file was provided, return its containing dir
            path = os.path.dirname(path)

        entries = []
        for name in sorted(os.listdir(path)):
            try:
                full = os.path.join(path, name)
                is_dir = os.path.isdir(full)
                # gather size and mtime
                try:
                    stat = os.stat(full)
                    size = stat.st_size if not is_dir else None
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except Exception:
                    size = None
                    mtime = None

                entries.append(
                    {
                        "name": name,
                        "is_dir": is_dir,
                        "path": full,
                        "size": size,
                        "last_modified": mtime,
                    }
                )
            except Exception:
                continue

        return jsonify({"status": "success", "path": path, "entries": entries})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/expose-path", methods=["POST"])
def ui_expose_path():
    try:
        data = request.get_json(silent=True) or {}
        path = data.get("path")
        if not path:
            return jsonify({"status": "error", "message": "Missing path"}), 400
        path = os.path.abspath(path)
        if not os.path.exists(path):
            return jsonify({"status": "error", "message": "Path not found"}), 400
        if path not in EXPOSED_PATHS:
            EXPOSED_PATHS.append(path)
        return jsonify({"status": "success", "path": path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/exposed")
def ui_exposed():
    return render_template_string(
        """
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Exposed Files</title>
    <style>body{font-family:'Segoe UI',system-ui,sans-serif;background:#eef0f3;color:#222;padding:20px}.card{background:#fff;padding:16px;border-radius:10px;max-width:900px;margin:0 auto;border:1px solid #e4e4e4}.entry{display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #f0f0f0}</style>
    </head><body><div class="card"><h2>Exposed Files</h2><div id="list"></div><div style="height:12px"></div><a href="/ui"><button>← Kembali</button></a></div>
    <script>
    async function refresh(){
        const res = await fetch('/ui/get-exposed');
        const data = await res.json();
        const list = document.getElementById('list'); list.innerHTML='';
        if(!data.paths || data.paths.length===0){ list.innerHTML='<div style="padding:8px;color:#666">(No exposed files)</div>'; return; }
        data.paths.forEach(p=>{
            const div=document.createElement('div'); div.className='entry'; const n=document.createElement('div'); n.textContent=p; const actions=document.createElement('div');
            const openBtn=document.createElement('button'); openBtn.textContent='Open'; openBtn.addEventListener('click', async ()=>{
                try{ const r=await fetch('/ui/read-pdf-file',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filepath:p})}); if(!r.ok){ const t=await r.text(); alert('Error: '+t); return; } const blob=await r.blob(); const url=URL.createObjectURL(blob); window.open(url,'_blank'); }catch(e){alert(e.message);} });
            const removeBtn=document.createElement('button'); removeBtn.textContent='Remove'; removeBtn.style.marginLeft='6px'; removeBtn.addEventListener('click', async ()=>{ await fetch('/ui/remove-exposed',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p})}); refresh(); });
            actions.appendChild(openBtn); actions.appendChild(removeBtn); div.appendChild(n); div.appendChild(actions); list.appendChild(div);
        });
    }
    refresh();
    </script></body>
    """
    )


@app.route("/ui/get-exposed")
def ui_get_exposed():
    return jsonify({"paths": EXPOSED_PATHS})


@app.route("/ui/remove-exposed", methods=["POST"])
def ui_remove_exposed():
    try:
        data = request.get_json(silent=True) or {}
        path = data.get("path")
        if path and path in EXPOSED_PATHS:
            EXPOSED_PATHS.remove(path)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/drives")
def ui_drives():
    try:
        drives = []
        if os.name == "nt":
            # enumerate drive letters
            import string

            for d in string.ascii_uppercase:
                drive = d + ":\\"
                if os.path.exists(drive):
                    drives.append(drive)
        else:
            drives = ["/"]
        return jsonify({"drives": drives})
    except Exception as e:
        return jsonify({"drives": []})


@app.route("/ui/file-dialog-component")
def ui_file_dialog_component():
    js_code = """
// File Dialog Component - Windows Explorer style picker
if (!window.fileDialogComponent) {
    window.fileDialogComponent = true;

    const SEP = String.fromCharCode(92); // backslash
    function stripSep(s){ while(s.length && s.charAt(s.length - 1) === SEP) s = s.slice(0, -1); return s; }

    const style = document.createElement('style');
    style.textContent = `
        .fd-overlay{ position:fixed; inset:0; background:rgba(0,0,0,0.55); display:none; z-index:10000; align-items:center; justify-content:center; }
        .fd-overlay.active{ display:flex; }
        .fd-dialog{ background:#fff; border-radius:10px; width:92%; max-width:1120px; height:86vh; display:flex; flex-direction:column;
            box-shadow:0 24px 70px rgba(0,0,0,0.35); overflow:hidden; font-family:'Segoe UI',system-ui,sans-serif; }
        .fd-header{ display:flex; align-items:center; justify-content:space-between; padding:12px 16px; border-bottom:1px solid #e6e6e6; background:#fafbfc; }
        .fd-header h3{ margin:0; font-size:15px; color:#222; font-weight:600; }
        .fd-close{ background:transparent; border:none; font-size:20px; line-height:1; cursor:pointer; color:#777; padding:4px 8px; border-radius:5px; }
        .fd-close:hover{ background:#eee; color:#222; }

        .fd-nav{ display:flex; align-items:center; gap:6px; padding:8px 12px; border-bottom:1px solid #eee; background:#fff; }
        .fd-navbtn{ width:32px; height:30px; border:1px solid #dcdfe3; background:#fff; border-radius:5px; cursor:pointer;
            color:#555; font-size:15px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .fd-navbtn:hover:not(:disabled){ background:#eef4ff; border-color:#0066cc; color:#0066cc; }
        .fd-navbtn:disabled{ opacity:0.4; cursor:default; }
        .fd-crumbs{ flex:1; display:flex; align-items:center; gap:2px; overflow-x:auto; white-space:nowrap; background:#f6f7f9;
            border:1px solid #dcdfe3; border-radius:5px; padding:5px 8px; min-height:30px; font-size:13px; }
        .fd-crumb{ padding:2px 6px; border-radius:4px; cursor:pointer; color:#333; }
        .fd-crumb:hover{ background:#e4ecfa; color:#0066cc; }
        .fd-crumb-sep{ color:#aaa; padding:0 1px; }
        .fd-search{ width:220px !important; max-width:220px !important; flex-shrink:0; border:1px solid #dcdfe3; border-radius:5px; padding:6px 10px; font-size:13px; box-sizing:border-box; }
        .fd-search:focus{ outline:none; border-color:#0066cc; }

        .fd-body{ flex:1; display:flex; min-height:0; }
        .fd-sidebar{ width:200px; border-right:1px solid #eee; background:#f8f9fb; overflow-y:auto; padding:12px 8px; flex-shrink:0; }
        .fd-side-label{ font-size:10.5px; color:#98a2ad; text-transform:uppercase; letter-spacing:0.06em; font-weight:700; margin:6px 8px 6px; }
        .fd-drive{ display:flex; align-items:center; gap:8px; padding:7px 10px; border-radius:6px; cursor:pointer; color:#333; font-size:13px; }
        .fd-drive:hover{ background:#e8eefc; color:#0066cc; }
        .fd-drive .ic{ font-size:15px; }

        .fd-main{ flex:1; display:flex; flex-direction:column; min-width:0; }
        .fd-listwrap{ flex:1; overflow:auto; }
        .fd-table{ width:100%; border-collapse:collapse; font-size:13px; }
        .fd-table thead th{ position:sticky; top:0; background:#fff; z-index:2; text-align:left; padding:9px 10px;
            border-bottom:1px solid #e2e5e9; color:#667080; font-weight:600; cursor:pointer; user-select:none; white-space:nowrap; }
        .fd-table thead th:hover{ color:#0066cc; }
        .fd-table thead th .arrow{ font-size:10px; margin-left:3px; color:#0066cc; }
        .fd-col-size{ width:110px; text-align:right !important; }
        .fd-col-type{ width:130px; }
        .fd-col-date{ width:170px; }
        .fd-table td{ padding:7px 10px; border-bottom:1px solid #f2f3f5; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .fd-row{ cursor:pointer; }
        .fd-row:hover{ background:#f3f8ff; }
        .fd-row.selected{ background:#dbeafe !important; }
        .fd-row.disabled{ color:#b0b6bd; }
        .fd-row.disabled .fd-name{ color:#b0b6bd; }
        .fd-name{ display:flex; align-items:center; gap:8px; overflow:hidden; }
        .fd-name .ic{ font-size:15px; flex-shrink:0; }
        .fd-name .txt{ overflow:hidden; text-overflow:ellipsis; }
        .fd-size{ text-align:right; color:#667080; }
        .fd-type, .fd-date{ color:#8a929b; font-size:12px; }
        .fd-empty{ padding:40px; text-align:center; color:#98a2ad; font-size:13px; }
        .fd-loading{ padding:40px; text-align:center; color:#0066cc; font-size:13px; }

        .fd-footer{ display:flex; align-items:center; gap:12px; padding:12px 16px; border-top:1px solid #e6e6e6; background:#fafbfc; }
        .fd-selinfo{ flex:1; font-size:13px; color:#444; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .fd-selinfo b{ color:#111; }
        .fd-hint{ font-size:11px; color:#98a2ad; }
        .fd-btn{ padding:8px 18px; border-radius:6px; font-size:13px; font-weight:600; cursor:pointer; border:1px solid #dcdfe3; background:#fff; color:#444; }
        .fd-btn:hover{ background:#f0f0f0; }
        .fd-btn.primary{ background:#0066cc; border-color:#0066cc; color:#fff; }
        .fd-btn.primary:hover{ background:#0052a3; }
        .fd-btn.primary:disabled{ background:#cbd5e1; border-color:#cbd5e1; cursor:default; }
    `;
    document.head.appendChild(style);

    const IMAGE_EXTS = ['jpg','jpeg','png','gif','bmp','webp','tiff','tif','ico'];

    const modalHTML = `
        <div class="fd-overlay" id="fdOverlay">
          <div class="fd-dialog" role="dialog" aria-label="Pilih File">
            <div class="fd-header">
              <h3>Pilih File</h3>
              <button class="fd-close" title="Tutup" onclick="closeFileDialog()">&times;</button>
            </div>
            <div class="fd-nav">
              <button class="fd-navbtn" id="fdBack" title="Kembali">&#8592;</button>
              <button class="fd-navbtn" id="fdFwd" title="Maju">&#8594;</button>
              <button class="fd-navbtn" id="fdUp" title="Naik satu folder">&#8593;</button>
              <button class="fd-navbtn" id="fdReload" title="Muat ulang">&#8635;</button>
              <div class="fd-crumbs" id="fdCrumbs"></div>
              <input class="fd-search" id="fdSearch" type="text" placeholder="Cari di folder ini..." />
            </div>
            <div class="fd-body">
              <div class="fd-sidebar">
                <div class="fd-side-label">Drive</div>
                <div id="fdDrives"></div>
              </div>
              <div class="fd-main">
                <div class="fd-listwrap">
                  <table class="fd-table">
                    <thead>
                      <tr>
                        <th data-sort="name">Nama <span class="arrow" id="fdArrname"></span></th>
                        <th data-sort="size" class="fd-col-size">Ukuran <span class="arrow" id="fdArrsize"></span></th>
                        <th data-sort="type" class="fd-col-type">Tipe <span class="arrow" id="fdArrtype"></span></th>
                        <th data-sort="date" class="fd-col-date">Diubah <span class="arrow" id="fdArrdate"></span></th>
                      </tr>
                    </thead>
                    <tbody id="fdBody"></tbody>
                  </table>
                  <div class="fd-empty" id="fdEmpty" style="display:none;">Folder kosong.</div>
                  <div class="fd-loading" id="fdLoading" style="display:none;">Memuat...</div>
                </div>
              </div>
            </div>
            <div class="fd-footer">
              <div class="fd-selinfo" id="fdSelInfo">Belum ada file dipilih</div>
              <span class="fd-hint">Hanya file gambar yang bisa dipilih</span>
              <button class="fd-btn" onclick="closeFileDialog()">Batal</button>
              <button class="fd-btn primary" id="fdPick" disabled>Pilih</button>
            </div>
          </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const fd = {
        callback: null, path: '', items: [], selected: null,
        sortKey: 'name', sortAsc: true, history: [], histIndex: -1,
    };
    window.fileDialogCurrentPath = '';
    window.fileDialogCallback = null;

    const $ = (id) => document.getElementById(id);

    function isImage(name){
        const ext = String(name.split('.').pop() || '').toLowerCase();
        return IMAGE_EXTS.includes(ext);
    }
    function extLabel(item){
        if(item.type === 'folder') return 'Folder';
        const ext = String(item.name.split('.').pop() || '').toUpperCase();
        return ext ? ext + ' File' : 'File';
    }
    function fmtBytes(bytes){
        if(bytes === null || bytes === undefined) return '';
        if(bytes < 1024) return bytes + ' B';
        const u = ['KB','MB','GB','TB']; let s = bytes, i = -1;
        do { s /= 1024; i++; } while(s >= 1024 && i < u.length - 1);
        return s.toFixed(1) + ' ' + u[i];
    }
    function iconFor(item){
        if(item.type === 'folder') return '📁';
        if(isImage(item.name)) return '🖼️';
        const ext = String(item.name.split('.').pop() || '').toLowerCase();
        if(ext === 'pdf') return '📕';
        if(['zip','rar','7z','tar','gz'].includes(ext)) return '🗜️';
        return '📄';
    }
    function escapeHtml(s){
        return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    window.openFileDialog = function(callback){
        fd.callback = callback || null;
        window.fileDialogCallback = fd.callback;
        fd.selected = null; fd.history = []; fd.histIndex = -1;
        $('fdSearch').value = '';
        $('fdOverlay').classList.add('active');
        $('fdOverlay').focus();
        updateSelInfo();
        loadDrives();
        navigate('', true);
    };

    window.closeFileDialog = function(){
        $('fdOverlay').classList.remove('active');
        fd.callback = null;
        window.fileDialogCallback = null;
    };

    async function loadDrives(){
        try{
            const res = await fetch('/ui/drives');
            const data = await res.json();
            const host = $('fdDrives');
            host.innerHTML = '';
            (data.drives || []).forEach(drv => {
                const el = document.createElement('div');
                el.className = 'fd-drive';
                el.innerHTML = '<span class="ic">💾</span><span>' + escapeHtml(drv) + '</span>';
                el.addEventListener('click', () => navigate(drv, true));
                host.appendChild(el);
            });
        }catch(e){ console.error('drives', e); }
    }

    async function navigate(path, pushHist){
        $('fdLoading').style.display = 'block';
        $('fdEmpty').style.display = 'none';
        try{
            const res = await fetch('/api/list?path=' + encodeURIComponent(path || ''));
            const data = res.ok ? await res.json() : { items: [] };
            if(data.warning && (!data.items || data.items.length === 0)){
                fd.path = '';
                fd.items = [];
                fd.selected = null;
                updateSelInfo();
                renderCrumbs();
                renderList();
                updateNavButtons();
                $('fdEmpty').style.display = 'block';
                $('fdEmpty').textContent = 'Folder tidak ditemukan. Pilih drive/folder lain.';
                return;
            }
            fd.path = data.current_path || '';
            window.fileDialogCurrentPath = fd.path;
            fd.items = data.items || [];
            fd.selected = null;
            updateSelInfo();
            if(pushHist){
                fd.history = fd.history.slice(0, fd.histIndex + 1);
                fd.history.push(fd.path);
                fd.histIndex = fd.history.length - 1;
            }
            renderCrumbs();
            renderList();
            updateNavButtons();
        }catch(e){
            console.warn('File dialog navigate error:', e);
        }finally{
            $('fdLoading').style.display = 'none';
        }
    }

    function updateNavButtons(){
        $('fdBack').disabled = fd.histIndex <= 0;
        $('fdFwd').disabled = fd.histIndex >= fd.history.length - 1;
        $('fdUp').disabled = fd.path.split(SEP).filter(Boolean).length <= 1;
    }

    function renderCrumbs(){
        const host = $('fdCrumbs');
        host.innerHTML = '';
        const parts = fd.path.split(SEP).filter(Boolean);
        let acc = '';
        parts.forEach((p, i) => {
            acc = i === 0 ? (p + SEP) : (stripSep(acc) + SEP + p);
            const seg = acc;
            if(i > 0){
                const sep = document.createElement('span');
                sep.className = 'fd-crumb-sep'; sep.textContent = '›';
                host.appendChild(sep);
            }
            const c = document.createElement('span');
            c.className = 'fd-crumb'; c.textContent = p;
            c.addEventListener('click', () => navigate(seg, true));
            host.appendChild(c);
        });
    }

    function sortedItems(){
        const filter = $('fdSearch').value.trim().toLowerCase();
        let list = fd.items.slice();
        if(filter) list = list.filter(it => it.name.toLowerCase().includes(filter));
        const key = fd.sortKey, dir = fd.sortAsc ? 1 : -1;
        list.sort((a, b) => {
            if(a.type !== b.type) return a.type === 'folder' ? -1 : 1;
            let av, bv;
            if(key === 'size'){ av = a.size || 0; bv = b.size || 0; }
            else if(key === 'date'){ av = a.last_modified || ''; bv = b.last_modified || ''; }
            else if(key === 'type'){ av = extLabel(a); bv = extLabel(b); }
            else { av = a.name.toLowerCase(); bv = b.name.toLowerCase(); }
            if(av < bv) return -1 * dir;
            if(av > bv) return 1 * dir;
            return a.name.toLowerCase() < b.name.toLowerCase() ? -1 : 1;
        });
        return list;
    }

    function renderList(){
        const tbody = $('fdBody');
        tbody.innerHTML = '';
        const list = sortedItems();
        $('fdEmpty').style.display = list.length ? 'none' : 'block';

        ['name','size','type','date'].forEach(k => { const el = $('fdArr' + k); if(el) el.textContent = ''; });
        const arrEl = $('fdArr' + fd.sortKey);
        if(arrEl) arrEl.textContent = fd.sortAsc ? '▲' : '▼';

        list.forEach(item => {
            const isFolder = item.type === 'folder';
            const selectable = isFolder || isImage(item.name);
            const tr = document.createElement('tr');
            tr.className = 'fd-row' + (selectable ? '' : ' disabled');

            const tdName = document.createElement('td');
            tdName.innerHTML = '<div class="fd-name"><span class="ic">' + iconFor(item) + '</span><span class="txt">' + escapeHtml(item.name) + '</span></div>';
            const tdSize = document.createElement('td');
            tdSize.className = 'fd-size'; tdSize.textContent = isFolder ? '' : fmtBytes(item.size);
            const tdType = document.createElement('td');
            tdType.className = 'fd-type'; tdType.textContent = extLabel(item);
            const tdDate = document.createElement('td');
            tdDate.className = 'fd-date'; tdDate.textContent = item.last_modified || '';

            tr.appendChild(tdName); tr.appendChild(tdSize); tr.appendChild(tdType); tr.appendChild(tdDate);
            tr.addEventListener('click', () => selectRow(tr, item));
            tr.addEventListener('dblclick', () => openItem(item));
            tbody.appendChild(tr);
        });
    }

    function selectRow(tr, item){
        document.querySelectorAll('#fdBody .fd-row.selected').forEach(r => r.classList.remove('selected'));
        tr.classList.add('selected');
        fd.selected = item;
        updateSelInfo();
    }

    function updateSelInfo(){
        const info = $('fdSelInfo');
        const pick = $('fdPick');
        if(fd.selected && fd.selected.type !== 'folder' && isImage(fd.selected.name)){
            info.innerHTML = 'File: <b>' + escapeHtml(fd.selected.name) + '</b>';
            pick.disabled = false;
        } else if(fd.selected && fd.selected.type === 'folder'){
            info.innerHTML = 'Folder: <b>' + escapeHtml(fd.selected.name) + '</b> (klik ganda untuk buka)';
            pick.disabled = true;
        } else if(fd.selected){
            info.innerHTML = '<span style="color:#c62828">' + escapeHtml(fd.selected.name) + '</span> — bukan file gambar';
            pick.disabled = true;
        } else {
            info.textContent = 'Belum ada file dipilih';
            pick.disabled = true;
        }
    }

    function joinPath(name){
        return fd.path ? (stripSep(fd.path) + SEP + name) : name;
    }

    function openItem(item){
        if(item.type === 'folder') navigate(joinPath(item.name), true);
        else if(isImage(item.name)) confirmPick(item);
    }

    function confirmPick(item){
        const full = joinPath(item.name);
        const cb = fd.callback;
        closeFileDialog();
        if(cb) cb(full);
    }

    function goUp(){
        const parts = fd.path.split(SEP).filter(Boolean);
        if(parts.length <= 1) return;
        parts.pop();
        let target = parts.join(SEP);
        if(parts.length === 1) target = parts[0] + SEP;
        navigate(target, true);
    }

    $('fdBack').addEventListener('click', () => { if(fd.histIndex > 0){ fd.histIndex--; navigate(fd.history[fd.histIndex], false); } });
    $('fdFwd').addEventListener('click', () => { if(fd.histIndex < fd.history.length - 1){ fd.histIndex++; navigate(fd.history[fd.histIndex], false); } });
    $('fdUp').addEventListener('click', goUp);
    $('fdReload').addEventListener('click', () => navigate(fd.path, false));
    $('fdSearch').addEventListener('input', renderList);
    $('fdPick').addEventListener('click', () => { if(fd.selected && isImage(fd.selected.name)) confirmPick(fd.selected); });
    document.querySelectorAll('.fd-table thead th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const k = th.getAttribute('data-sort');
            if(fd.sortKey === k) fd.sortAsc = !fd.sortAsc; else { fd.sortKey = k; fd.sortAsc = true; }
            renderList();
        });
    });
    let typeAheadStr = '', typeAheadTimer = null;
    $('fdOverlay').addEventListener('keydown', (e) => {
        if(e.key === 'Escape'){ closeFileDialog(); return; }
        if(e.key === 'Enter' && fd.selected){ openItem(fd.selected); return; }
        if(e.key === 'Backspace' && document.activeElement !== $('fdSearch')){ e.preventDefault(); goUp(); return; }
        if(document.activeElement === $('fdSearch')) return;
        if(e.key === 'ArrowDown' || e.key === 'ArrowUp'){
            e.preventDefault();
            const rows = Array.from($('fdBody').querySelectorAll('.fd-row'));
            if(!rows.length) return;
            const cur = rows.findIndex(r => r.classList.contains('selected'));
            let next = e.key === 'ArrowDown' ? cur + 1 : cur - 1;
            if(next < 0) next = rows.length - 1;
            if(next >= rows.length) next = 0;
            rows[next].click();
            rows[next].scrollIntoView({block:'nearest'});
            return;
        }
        if(e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey){
            e.preventDefault();
            clearTimeout(typeAheadTimer);
            typeAheadStr += e.key.toLowerCase();
            typeAheadTimer = setTimeout(() => { typeAheadStr = ''; }, 800);
            const rows = Array.from($('fdBody').querySelectorAll('.fd-row'));
            const match = rows.find(r => {
                const txt = r.querySelector('.txt');
                return txt && txt.textContent.toLowerCase().startsWith(typeAheadStr);
            });
            if(match){
                match.click();
                match.scrollIntoView({block:'nearest'});
            }
        }
    });
    $('fdOverlay').setAttribute('tabindex', '-1');
    $('fdOverlay').addEventListener('mousedown', (e) => { if(e.target === $('fdOverlay')) closeFileDialog(); });

    // legacy-compatible helpers
    window.fileDialogRefresh = () => navigate(fd.path, false);
    window.fileDialogUpFolder = goUp;
    window.fileDialogLoadFolder = (p) => navigate(p, true);
}
"""
    return Response(js_code, mimetype="application/javascript")


@app.route("/ui/read-pdf-info-form")
def read_pdf_info_form():
    return render_template_string(
        """
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Info - Printing Agent</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', system-ui, sans-serif;
                background: #eef0f3;
                color: #222;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                color: #1a1a1a;
                font-size: 22px;
                font-weight: 700;
            }
            
            .back-btn {
                background: #fff;
                color: #444;
                border: 1px solid #ccc;
                padding: 8px 16px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.15s;
            }
            
            .back-btn:hover {
                background: #f0f0f0;
                border-color: #0066cc;
                color: #0066cc;
            }
            
            .main-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                align-items: start;
            }
            
            .left-section {
                display: flex;
                flex-direction: column;
                gap: 20px;
                height: fit-content;
            }
            
            .card {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06); border: 1px solid #e4e4e4;
            }
            
            .upload-card {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06); border: 1px solid #e4e4e4;
            }
            
            .card h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 20px;
            }
            
            .file-input-wrapper {
                position: relative;
                display: inline-block;
                width: 100%;
            }
            
            .file-input-wrapper input[type="file"] {
                display: none;
            }
            
            .file-input-label {
                display: block;
                width: 100%;
                padding: 40px 20px;
                border: 2px dashed #0066cc;
                border-radius: 8px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                background: #f8f9ff;
            }
            
            .file-input-label:hover {
                border-color: #0055aa;
                background: #f0f2ff;
            }
            
            .file-input-label p {
                color: #0066cc;
                font-weight: 500;
                margin-bottom: 10px;
            }
            
            .file-input-label span {
                color: #999;
                font-size: 12px;
            }
            
            .browse-btn {
                width: 100%;
                padding: 20px;
                background: #0066cc;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .browse-btn:hover {
                opacity: 0.9;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .file-name {
                margin-top: 15px;
                padding: 10px;
                background: #f0f2ff;
                border-radius: 5px;
                color: #0066cc;
                font-size: 13px;
                text-align: center;
            }
            
            .file-path {
                margin-top: 10px;
                padding: 12px;
                background: #f9f9f9;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
                color: #555;
                font-size: 11px;
                font-family: 'Courier New', monospace;
                word-break: break-all;
            }
            
            .preview-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06); border: 1px solid #e4e4e4;
                display: flex;
                flex-direction: column;
                height: fit-content;
            }
            
            .preview-card h2 {
                margin-bottom: 15px;
                font-size: 18px;
                color: #333;
            }
            
            .pdf-viewer {
                width: 100%;
                height: 600px;
                background: #f5f5f5;
                border-radius: 8px;
                overflow: auto;
                display: flex;
                justify-content: center;
                align-items: center;
                position: relative;
            }
            
            .pdf-page {
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin: 10px;
            }
            
            .pdf-controls {
                display: flex;
                gap: 10px;
                margin-top: 10px;
                justify-content: center;
                align-items: center;
            }
            
            .pdf-controls button {
                background: #0066cc;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
            }
            
            .pdf-controls button:hover {
                background: #0055aa;
            }
            
            .pdf-controls button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            
            .page-info {
                color: #666;
                font-size: 13px;
                min-width: 150px;
                text-align: center;
            }
            
            .info-card {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06); border: 1px solid #e4e4e4;
            }
            
            .info-card h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 20px;
            }
            
            .summary-box {
                background: #0066cc;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .summary-item {
                margin: 10px 0;
                font-size: 16px;
            }
            
            .summary-label {
                opacity: 0.9;
                font-size: 12px;
                text-transform: uppercase;
            }
            
            .summary-value {
                font-weight: 600;
                font-size: 18px;
            }
            
            .pages-list {
                max-height: 350px;
                overflow-y: auto;
            }
            
            .page-item {
                background: #f8f9ff;
                padding: 15px;
                border-left: 4px solid #0066cc;
                margin-bottom: 10px;
                border-radius: 5px;
            }
            
            .page-header {
                font-weight: 600;
                color: #333;
                margin-bottom: 8px;
                font-size: 14px;
            }
            
            .page-detail {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                font-size: 12px;
                color: #666;
            }
            
            .detail-item {
                display: flex;
                justify-content: space-between;
            }
            
            .loading {
                text-align: center;
                padding: 20px;
                color: #0066cc;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #0066cc;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .empty-state {
                text-align: center;
                color: #999;
                padding: 40px 20px;
            }
            
            .empty-state p {
                margin: 10px 0;
            }
            
            .error {
                background: #fee;
                color: #c33;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                text-align: center;
            }
            
            @media (max-width: 1024px) {
                .main-container {
                    grid-template-columns: 1fr;
                    align-items: auto;
                }
                
                .pdf-viewer {
                    height: 400px;
                }
            }
            
            @media (max-width: 768px) {
                .header {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .pdf-viewer {
                    height: 300px;
                }
                
                .page-detail {
                    grid-template-columns: 1fr;
                }
                
                .pdf-controls {
                    flex-wrap: wrap;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>PDF Info & Preview</h1>
                <a href="/ui"><button class="back-btn">← Kembali</button></a>
            </div>
            
            <div class="main-container">
                <div class="left-section">
                    <!-- Upload Card -->
                    <div class="upload-card">
                        <h2>Upload File PDF</h2>
                        <input type="file" id="pdfFile" accept=".pdf" style="display: none;">
                        <button class="browse-btn" onclick="document.getElementById('pdfFile').click()">📁 Browse File PDF</button>
                        <div class="file-name" id="fileName" style="display: none;"></div>
                        <div class="file-path" id="filePath" style="display: none;"></div>
                        <div id="uploadMessage"></div>
                    </div>
                    
                    <!-- Info Card -->
                    <div class="card" id="infoCard" style="display: none; max-height: 400px; overflow-y: auto;">
                        <h2>Informasi PDF</h2>
                        <div id="infoContent"></div>
                    </div>
                </div>
                
                <!-- Preview Card - Right Section -->
                <div class="preview-card">
                    <h2>Preview PDF</h2>
                    <div class="pdf-viewer">
                        <div class="empty-state" id="previewEmpty">
                            <p>⬅️ Upload PDF untuk melihat preview</p>
                        </div>
                        <canvas id="pdfCanvas" class="pdf-page" style="display: none;"></canvas>
                    </div>
                    <div class="pdf-controls" id="pdfControls" style="display: none;">
                        <button id="prevBtn" onclick="prevPage()">← Halaman Sebelumnya</button>
                        <div class="page-info">
                            <span id="pageNum">1</span> dari <span id="totalPages">1</span>
                        </div>
                        <button id="nextBtn" onclick="nextPage()">Halaman Selanjutnya →</button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let currentPDF = null;
            let currentPage = 1;
            
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            
            function selectPDFFile() {
                document.getElementById('pdfFile').click();
            }
            
            function uploadFileByPath(filePath) {
                fetch('/ui/read-pdf-info', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({filepath: filePath})
                })
                .then(async res => {
                    const ct = res.headers.get('content-type') || '';
                    if (!res.ok) {
                        const txt = await res.text();
                        throw new Error(`HTTP ${res.status}: ${txt}`);
                    }
                    if (ct.includes('application/json')) return res.json();
                    const txt = await res.text();
                    throw new Error(txt);
                })
                .then(data => {
                    if (data.status === 'success') {
                        displayInfo(data);
                        displayPDFPreviewFromPath(filePath);
                    } else {
                        showError(data.message || 'Terjadi kesalahan');
                    }
                })
                .catch(error => {
                    showError(error.message);
                });
            }
            
            function displayPDFPreviewFromPath(filePath) {
                // Read file from path and display preview
                fetch('/ui/read-pdf-file', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({filepath: filePath})
                })
                .then(res => res.arrayBuffer())
                .then(data => {
                    displayPDFFromBuffer(data);
                })
                .catch(error => {
                    showPreviewError(error.message);
                });
            }
            
            function displayPDFFromBuffer(buffer) {
                (async () => {
                    try {
                        const pdf = await pdfjsLib.getDocument({data: buffer}).promise;
                        currentPDF = pdf;
                        currentPage = 1;
                        
                        // Show controls
                        document.getElementById('totalPages').textContent = pdf.numPages;
                        document.getElementById('pdfControls').style.display = 'flex';
                        
                        renderPage(1);
                    } catch (error) {
                        showPreviewError(error.message);
                    }
                })();
            }
            
            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (!file) return;
                
                // Show file name
                const fileNameEl = document.getElementById('fileName');
                fileNameEl.textContent = '✓ ' + file.name;
                fileNameEl.style.display = 'block';
                
                // Show file path
                const filePathEl = document.getElementById('filePath');
                filePathEl.textContent = file.webkitRelativePath || 'Local file: ' + file.name;
                filePathEl.style.display = 'block';
                
                // Show loading state in preview
                const previewEmpty = document.getElementById('previewEmpty');
                previewEmpty.style.display = 'block';
                previewEmpty.innerHTML = '<div class="loading"><div class="spinner"></div><p>Memproses PDF...</p></div>';
                
                // Upload and get info
                uploadFile(file);
                
                // Display PDF preview
                displayPDFPreview(file);
            }
            
            function displayPDFPreview(file) {
                const reader = new FileReader();
                
                reader.onload = async (e) => {
                    try {
                        const pdf = await pdfjsLib.getDocument({data: e.target.result}).promise;
                        currentPDF = pdf;
                        currentPage = 1;
                        
                        // Show controls
                        document.getElementById('totalPages').textContent = pdf.numPages;
                        document.getElementById('pdfControls').style.display = 'flex';
                        
                        renderPage(1);
                    } catch (error) {
                        showPreviewError(error.message);
                    }
                };
                
                reader.readAsArrayBuffer(file);
            }
            
            async function renderPage(pageNum) {
                if (!currentPDF) return;
                
                try {
                    const page = await currentPDF.getPage(pageNum);
                    
                    // Get container dimensions
                    const container = document.querySelector('.pdf-viewer');
                    const containerWidth = container.clientWidth - 20; // account for padding
                    const containerHeight = 560; // fixed height minus padding
                    
                    // Get page viewport
                    const viewport = page.getViewport({scale: 1.0});
                    const pageWidth = viewport.width;
                    const pageHeight = viewport.height;
                    
                    // Calculate scale to fit both width and height
                    const scaleX = containerWidth / pageWidth;
                    const scaleY = containerHeight / pageHeight;
                    const scale = Math.min(scaleX, scaleY, 1); // Don't scale up, only down
                    
                    const scaledViewport = page.getViewport({scale: scale});
                    
                    const canvas = document.getElementById('pdfCanvas');
                    const context = canvas.getContext('2d');
                    canvas.width = scaledViewport.width;
                    canvas.height = scaledViewport.height;
                    canvas.style.display = 'block';
                    
                    document.getElementById('previewEmpty').style.display = 'none';
                    
                    await page.render({
                        canvasContext: context,
                        viewport: scaledViewport
                    }).promise;
                    
                    document.getElementById('pageNum').textContent = pageNum;
                    updateControls();
                } catch (error) {
                    showPreviewError(error.message);
                }
            }
            
            function prevPage() {
                if (currentPage > 1) {
                    currentPage--;
                    renderPage(currentPage);
                }
            }
            
            function nextPage() {
                if (currentPDF && currentPage < currentPDF.numPages) {
                    currentPage++;
                    renderPage(currentPage);
                }
            }
            
            function updateControls() {
                document.getElementById('prevBtn').disabled = currentPage <= 1;
                document.getElementById('nextBtn').disabled = currentPage >= currentPDF.numPages;
            }
            
            function showPreviewError(message) {
                document.getElementById('previewEmpty').innerHTML = '<div class="error">❌ ' + message + '</div>';
            }
            
            function uploadFile(file) {
                const formData = new FormData();
                formData.append('filepath', file);
                
                fetch('/ui/read-pdf-info', {
                    method: 'POST',
                    body: formData
                })
                .then(async res => {
                    const ct = res.headers.get('content-type') || '';
                    if (!res.ok) {
                        const txt = await res.text();
                        throw new Error(`HTTP ${res.status}: ${txt}`);
                    }
                    if (ct.includes('application/json')) return res.json();
                    const txt = await res.text();
                    throw new Error(txt);
                })
                .then(data => {
                    if (data.status === 'success') {
                        displayInfo(data);
                    } else {
                        showError(data.message || 'Terjadi kesalahan');
                    }
                })
                .catch(error => {
                    showError(error.message);
                });
            }
            
            function displayInfo(data) {
                const infoCard = document.getElementById('infoCard');
                let html = '';
                
                // Summary box
                html += `
                    <div class="summary-box">
                        <div class="summary-item">
                            <div class="summary-label">Jalur File</div>
                            <div class="summary-value" style="font-size: 11px; font-family: monospace; word-break: break-all;">${data.actual_file_path}</div>
                        </div>
                        <div class="summary-item" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.3);">
                            <div class="summary-label">Jumlah Halaman</div>
                            <div class="summary-value">${data.num_pages}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Mode Warna</div>
                            <div class="summary-value">${data.color_mode}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Ukuran File</div>
                            <div class="summary-value">${data.file_size_mb} MB</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Error Size Check</div>
                            <div class="summary-value" style="color: ${data.size_check ? '#4caf50' : '#ff9800'};">
                                ${data.size_check ? '✓ TRUE' : '✗ FALSE'}
                            </div>
                        </div>
                        ${!data.size_check ? `<div class="summary-item" style="font-size: 12px; margin-top: 5px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.3);">
                            <div class="summary-label">Ditemukan Perbedaan</div>
                            <div class="summary-value" style="font-size: 13px;">${data.size_summary}</div>
                        </div>` : ''}
                    </div>
                `;
                
                // Pages list
                if (data.pages && data.pages.length > 0) {
                    html += '<h3 style="color: #333; margin-bottom: 15px; font-size: 16px;">Detail Setiap Halaman</h3>';
                    html += '<div class="pages-list">';
                    
                    data.pages.forEach(page => {
                        if (!page.error) {
                            html += `
                                <div class="page-item">
                                    <div class="page-header">Halaman ${page.page_num}</div>
                                    <div class="page-detail">
                                        <div class="detail-item">
                                            <span>Lebar (cm)</span>
                                            <strong>${page.width_cm}</strong>
                                        </div>
                                        <div class="detail-item">
                                            <span>Tinggi (cm)</span>
                                            <strong>${page.height_cm}</strong>
                                        </div>
                                        <div class="detail-item">
                                            <span>Lebar (mm)</span>
                                            <strong>${page.width_mm}</strong>
                                        </div>
                                        <div class="detail-item">
                                            <span>Tinggi (mm)</span>
                                            <strong>${page.height_mm}</strong>
                                        </div>
                                        <div class="detail-item">
                                            <span>Mode Warna</span>
                                            <strong>${page.color_mode}</strong>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }
                    });
                    
                    html += '</div>';
                }
                
                document.getElementById('infoContent').innerHTML = html;
                infoCard.style.display = 'block';
            }
            
            function showError(message) {
                const infoCard = document.getElementById('infoCard');
                document.getElementById('infoContent').innerHTML = '<div class="error">❌ ' + message + '</div>';
                infoCard.style.display = 'block';
            }
            
            // Drag & drop support and file input handling
            const fileInput = document.getElementById('pdfFile');

            if (fileInput) {
                fileInput.addEventListener('change', handleFileSelect);
            }

            const label = document.querySelector('.file-input-label');
            if (label) {
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    label.addEventListener(eventName, preventDefaults, false);
                });

                label.addEventListener('drop', (e) => {
                    const dt = e.dataTransfer;
                    const files = dt.files;
                    if (fileInput) {
                        fileInput.files = files;
                        handleFileSelect({target: {files: files}});
                    }
                });
            }

            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
        </script>
    </body>
    """
    )


@app.route("/ui/read-info-form")
def read_info_form():
    return render_template_string(
        """
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Info - Printing Agent</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', system-ui, sans-serif;
                background: #eef0f3;
                color: #222;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                color: #1a1a1a;
                font-size: 22px;
                font-weight: 700;
            }
            
            .back-btn {
                background: #fff;
                color: #444;
                border: 1px solid #ccc;
                padding: 8px 16px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.15s;
            }
            
            .back-btn:hover {
                background: #f0f0f0;
                border-color: #0066cc;
                color: #0066cc;
            }
            
            .main-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            .card {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06); border: 1px solid #e4e4e4;
            }
            
            .card h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 20px;
            }
            
            .file-input-wrapper {
                position: relative;
                display: inline-block;
                width: 100%;
            }
            
            .file-input-wrapper input[type="file"] {
                display: none;
            }
            
            .file-input-label {
                display: block;
                width: 100%;
                padding: 40px 20px;
                border: 2px dashed #0066cc;
                border-radius: 8px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                background: #f8f9ff;
            }
            
            .file-input-label:hover {
                border-color: #0055aa;
                background: #f0f2ff;
            }
            
            .file-input-label p {
                color: #0066cc;
                font-weight: 500;
                margin-bottom: 10px;
            }
            
            .file-input-label span {
                color: #999;
                font-size: 12px;
            }
            
            .file-name {
                margin-top: 15px;
                padding: 10px;
                background: #f0f2ff;
                border-radius: 5px;
                color: #0066cc;
                font-size: 13px;
                text-align: center;
            }
            
            .image-preview {
                width: 100%;
                max-height: 400px;
                object-fit: contain;
                border-radius: 8px;
                background: #f8f9ff;
                margin-top: 20px;
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            
            .info-item {
                padding: 15px;
                background: #f8f9ff;
                border-radius: 8px;
                border-left: 4px solid #0066cc;
            }
            
            .info-label {
                color: #999;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 5px;
            }
            
            .info-value {
                color: #333;
                font-size: 16px;
                font-weight: 600;
            }
            
            .loading {
                text-align: center;
                padding: 20px;
                color: #0066cc;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #0066cc;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .error {
                background: #fee;
                color: #c33;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                text-align: center;
            }
            
            .empty-state {
                text-align: center;
                color: #999;
                padding: 40px 20px;
            }
            
            .empty-state p {
                margin: 10px 0;
            }
            
            @media (max-width: 768px) {
                .main-grid {
                    grid-template-columns: 1fr;
                }
                
                .header {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .info-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Image Info</h1>
                <a href="/ui"><button class="back-btn">← Kembali</button></a>
            </div>
            
            <div class="main-grid">
                <!-- Upload Card -->
                <div class="card">
                    <h2>Upload File</h2>
                    <div class="file-input-wrapper">
                        <input type="file" id="imageFile" accept=".jpg,.jpeg,.png,.bmp,.gif,.tiff" onchange="handleFileSelect(event)">
                        <label for="imageFile" class="file-input-label">
                            <p>📁 Pilih File Gambar</p>
                            <span>Drag & drop atau klik untuk memilih</span>
                        </label>
                    </div>
                    <div class="file-name" id="fileName" style="display: none;"></div>
                    <div id="uploadMessage"></div>
                </div>
                
                <!-- Preview & Info Card -->
                <div class="card">
                    <h2>Informasi & Preview</h2>
                    <div id="content">
                        <div class="empty-state">
                            <p>⬅️ Pilih file gambar untuk melihat detail</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (!file) return;
                
                // Show file name
                const fileNameEl = document.getElementById('fileName');
                fileNameEl.textContent = '✓ ' + file.name;
                fileNameEl.style.display = 'block';
                
                // Show loading state in preview
                const contentEl = document.getElementById('content');
                contentEl.innerHTML = '<div class="loading"><div class="spinner"></div><p>Memproses...</p></div>';
                
                // Upload and get info
                uploadFile(file);
            }
            
            function uploadFile(file) {
                const formData = new FormData();
                formData.append('filepath', file);
                
                fetch('/ui/read-info', {
                    method: 'POST',
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        displayInfo(data, file);
                    } else {
                        showError(data.message || 'Terjadi kesalahan');
                    }
                })
                .catch(error => {
                    showError(error.message);
                });
            }
            
            function displayInfo(data, file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const contentEl = document.getElementById('content');
                    
                    let infoHTML = '<img src="' + e.target.result + '" class="image-preview">';
                    infoHTML += '<div class="info-grid">';
                    
                    const infoMap = {
                        'dimensions': 'Dimensi (px)',
                        'width_cm': 'Lebar (cm)',
                        'height_cm': 'Tinggi (cm)',
                        'dpi': 'DPI',
                        'color_mode': 'Mode Warna',
                        'size_bytes': 'Ukuran (bytes)',
                        'size_mb': 'Ukuran (MB)',
                        'size_megabits': 'Ukuran (Mbps)'
                    };
                    
                    Object.entries(infoMap).forEach(([key, label]) => {
                        if (data[key] !== undefined) {
                            infoHTML += `
                                <div class="info-item">
                                    <div class="info-label">${label}</div>
                                    <div class="info-value">${data[key]}</div>
                                </div>
                            `;
                        }
                    });
                    
                    infoHTML += '</div>';
                    contentEl.innerHTML = infoHTML;
                };
                reader.readAsDataURL(file);
            }
            
            function showError(message) {
                const contentEl = document.getElementById('content');
                contentEl.innerHTML = '<div class="error">❌ ' + message + '</div>';
            }
            
            // Drag & drop support
            const fileInput = document.getElementById('imageFile');
            const label = document.querySelector('.file-input-label');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                label.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            label.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                fileInput.files = files;
                handleFileSelect({target: {files: files}});
            });
        </script>
    </body>
    """
    )


@app.route("/ui/merge", methods=["POST"])
def ui_merge():
    try:
        file1 = request.files.get("file1")
        file2 = request.files.get("file2")
        output = request.form.get("output")

        if not file1 or not file2 or not output:
            return (
                jsonify(
                    {"status": "error", "message": "Missing file or output filename"}
                ),
                400,
            )

        temp_dir = tempfile.gettempdir()
        file1_path = os.path.join(temp_dir, file1.filename)
        file2_path = os.path.join(temp_dir, file2.filename)
        output_path = os.path.join(temp_dir, output)

        file1.save(file1_path)
        file2.save(file2_path)

        sheet_w = request.form.get("sheet_w")
        if sheet_w:
            compose_data = {
                    "file1": file1_path,
                    "file2": file2_path,
                    "output": output_path,
                    "sheet_w": sheet_w,
                    "sheet_h": request.form.get("sheet_h", "96"),
                    "x1": request.form.get("x1", "0"),
                    "y1": request.form.get("y1", "0"),
                    "x2": request.form.get("x2", "0"),
                    "y2": request.form.get("y2", "0"),
                    "rot1": request.form.get("rot1", "0"),
                    "rot2": request.form.get("rot2", "0"),
                }
            if request.form.get("cut_line"):
                    compose_data["cut_line"] = "1"
                    compose_data["cut_line_width"] = request.form.get("cut_line_width", "0.5")
                    compose_data["cut_line_color"] = request.form.get("cut_line_color", "#000000")
                    compose_data["cut_line_style"] = request.form.get("cut_line_style", "dashed")
                    compose_data["cut_line_dir"] = request.form.get("cut_line_dir", "auto")
                    compose_data["cut_line_extend"] = request.form.get("cut_line_extend", "1")
            result = execute(
                "compose_pdf_sheet",
                compose_data,
                timeout_seconds=60,
            )
        else:
            result = execute(
                "merge_pdf",
                {"file1": file1_path, "file2": file2_path, "output": output_path},
            )

        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/upload-image", methods=["POST"])
def ui_upload_image():
    try:
        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"status": "error", "message": "Missing file"}), 400

        upload_dir = os.path.join(tempfile.gettempdir(), "printing_agent_uploads")
        os.makedirs(upload_dir, exist_ok=True)

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}:
            ext = ".jpg"

        filename = f"draftcalc_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(upload_dir, filename)
        raw = file.read()
        with open(filepath, "wb") as handle:
            handle.write(raw)

        color_mode = None
        sample_cmyk = None
        try:
            with Image.open(filepath) as img:
                color_mode = img.mode
                if img.mode == "CMYK":
                    px = img.getpixel((img.width // 2, img.height // 2))
                    sample_cmyk = {
                        "c": round(px[0] / 255 * 100),
                        "m": round(px[1] / 255 * 100),
                        "y": round(px[2] / 255 * 100),
                        "k": round(px[3] / 255 * 100),
                    }
        except Exception:
            pass

        return jsonify({
            "status": "success",
            "filepath": filepath,
            "color_mode": color_mode,
            "sample_cmyk": sample_cmyk,
            "bytes": len(raw),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/image-processing", methods=["POST"])
def ui_image_processing():
    try:
        payload = request.get_json(silent=True)

        if not payload:
            return jsonify({"status": "error", "message": "Missing JSON body"}), 400

        result = execute("image_processing", payload, timeout_seconds=180)

        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/render-cmyk", methods=["POST"])
def ui_render_cmyk():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"status": "error", "message": "Missing JSON body"}), 400

        result = execute("render_cmyk", payload, timeout_seconds=300)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/export-cmyk-master", methods=["POST"])
def ui_export_cmyk_master():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"status": "error", "message": "Missing JSON body"}), 400

        result = execute("export_cmyk_master", payload, timeout_seconds=300)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/export-pdf-imposition", methods=["POST"])
def ui_export_pdf_imposition():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"status": "error", "message": "Missing JSON body"}), 400

        result = execute("export_pdf_imposition", payload, timeout_seconds=300)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/read-info", methods=["POST"])
def ui_read_info():
    try:
        filepath = None

        # 1) JSON body: {"filepath": "..."} (file sudah ada di server)
        json_data = request.get_json(silent=True)
        if json_data:
            filepath = json_data.get("filepath")

        # 2) Multipart upload: field "filepath" atau "file"
        if not filepath:
            up = request.files.get("filepath") or request.files.get("file")
            if up and up.filename:
                temp_dir = tempfile.gettempdir()
                filepath = os.path.join(temp_dir, up.filename)
                up.save(filepath)

        if not filepath:
            return jsonify({"status": "error", "message": "Missing file"}), 400
        if not os.path.isfile(filepath):
            return jsonify({"status": "error", "message": f"File not found: {filepath}"}), 404

        # Execute read info
        result = execute("read_info", {"filepath": filepath})

        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/read-pdf-info", methods=["POST"])
def ui_read_pdf_info():
    try:
        # Check if it's a file upload or JSON body
        file_path = None

        # Debug: Print request details
        sys.stdout.flush()
        print(f"DEBUG: ===== START /ui/read-pdf-info =====", flush=True)
        print(f"DEBUG: request.method = {request.method}", flush=True)
        print(f"DEBUG: request.content_type = {request.content_type}", flush=True)
        print(f"DEBUG: request.is_json = {request.is_json}", flush=True)
        print(f"DEBUG: request.data = {request.data}", flush=True)
        sys.stdout.flush()

        # Try to get filepath from JSON body first
        json_data = request.get_json(silent=True)
        print(f"DEBUG: json_data = {json_data}", flush=True)
        print(f"DEBUG: type(json_data) = {type(json_data)}", flush=True)
        sys.stdout.flush()

        if json_data:
            file_path = json_data.get("filepath") if json_data else None
            print(f"DEBUG: file_path from JSON = {file_path}", flush=True)
            sys.stdout.flush()

        # If no JSON body, try file upload
        if not file_path:
            print("DEBUG: No file path from JSON, trying file upload", flush=True)
            sys.stdout.flush()
            filepath = request.files.get("filepath")

            if not filepath:
                print("DEBUG: No file upload either, returning error", flush=True)
                sys.stdout.flush()
                return jsonify({"status": "error", "message": "Missing file"}), 400

            # Create temp directory
            temp_dir = tempfile.gettempdir()

            # Save uploaded file temporarily
            file_path = os.path.join(temp_dir, filepath.filename)
            filepath.save(file_path)
        else:
            # Validate file path from JSON
            print(f"DEBUG: Validating file path: {file_path}", flush=True)
            print(
                f"DEBUG: os.path.isfile(file_path) = {os.path.isfile(file_path)}",
                flush=True,
            )
            sys.stdout.flush()

            if not os.path.isfile(file_path):
                print(f"DEBUG: File not found error", flush=True)
                sys.stdout.flush()
                return (
                    jsonify(
                        {"status": "error", "message": f"File not found: {file_path}"}
                    ),
                    400,
                )

        # Execute read pdf info
        print(f"DEBUG: Executing read_pdf_info with {file_path}", flush=True)
        sys.stdout.flush()

        result = execute("read_pdf_info", {"filepath": file_path})

        # Add the actual file path to response
        result["actual_file_path"] = file_path

        print(f"DEBUG: ===== END /ui/read-pdf-info (SUCCESS) =====", flush=True)
        sys.stdout.flush()

        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: Exception: {str(e)}", flush=True)
        sys.stdout.flush()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/read-pdf-file", methods=["POST"])
def ui_read_pdf_file():
    try:
        data = request.get_json()
        file_path = data.get("filepath")

        if not file_path or not os.path.isfile(file_path):
            return jsonify({"status": "error", "message": "File not found"}), 400

        # Read file and return as binary
        with open(file_path, "rb") as f:
            file_content = f.read()

        return file_content, 200, {"Content-Type": "application/pdf"}
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "alive",
        "agent_id": AGENT_ID,
        "tasks": list(TASK_MAP.keys()),
    })


@app.route("/ui/image-contour", methods=["GET"])
def ui_image_contour_page():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "image_contour.html")
    with open(html_path, encoding="utf-8") as handle:
        return handle.read()


@app.route("/ui/image-contour", methods=["POST"])
def ui_image_contour_api():
    try:
        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"status": "error", "message": "No file provided"}), 400

        filename = file.filename.lower()
        if not (filename.endswith(".png") or filename.endswith(".pdf")):
            return jsonify({"status": "error", "message": "File harus PNG (.png) atau PDF (.pdf)"}), 400

        from tasks.image_contour import generate_contour

        img_bytes = file.read()
        if not img_bytes:
            return jsonify({"status": "error", "message": "File kosong"}), 400

        dpi_raw = request.form.get("dpi")
        dpi_val = float(dpi_raw) if dpi_raw not in (None, "") else None

        result = generate_contour(
            img_bytes,
            smoothing=float(request.form.get("smoothing", 5000)),
            min_area=int(float(request.form.get("min_area", 500))),
            line_color=request.form.get("line_color", "#ff00c8"),
            line_width=float(request.form.get("line_width", 1.5)),
            bg_color=request.form.get("bg_color") or None,
            bg_tolerance=int(float(request.form.get("bg_tolerance", 28))),
            max_dim=int(float(request.form.get("max_dim", 1400))),
            offset_mm=float(request.form.get("offset_mm", 0)),
            dpi=dpi_val,
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 422
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/image-tools")
def image_tools():
    return render_template_string(
        r"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Tools - Printing Agent</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', system-ui, sans-serif;
                background: #eef0f3;
                color: #222;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                color: #1a1a1a;
                font-size: 22px;
                font-weight: 700;
            }
            
            .back-btn {
                background: #fff;
                color: #444;
                border: 1px solid #ccc;
                padding: 8px 16px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.15s;
            }
            
            .back-btn:hover {
                background: #f0f0f0;
                border-color: #0066cc;
                color: #0066cc;
            }
            
            .content {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06); border: 1px solid #e4e4e4;
            }
            
            .section-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
            }
            
            .section-header h2 {
                color: #333;
                font-size: 20px;
                margin: 0;
            }
            
            .add-file-btn {
                background: #0066cc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
            }
            
            .add-file-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .file-list {
                margin-top: 20px;
            }
            
            .file-item {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                padding: 16px;
                background: #f8f9ff;
                border-left: 4px solid #0066cc;
                border-radius: 6px;
                margin-bottom: 16px;
                gap: 16px;
            }
            
            .file-item-preview {
                flex-shrink: 0;
            }
            
            .file-item-preview img {
                width: auto;
                max-width: 120px;
                height: auto;
                max-height: 120px;
                object-fit: contain;
                border-radius: 4px;
                background: #fff;
                border: 1px solid #e0e0e0;
            }
            
            .file-item-content {
                flex: 1;
                min-width: 0;
            }
            
            .file-item-info {
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-bottom: 12px;
            }
            
            .file-item-name {
                color: #333;
                font-weight: 600;
                word-break: break-all;
                font-size: 14px;
            }
            
            .file-item-details {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                font-size: 12px;
            }
            
            .file-item-detail {
                display: flex;
                flex-direction: column;
                background: white;
                padding: 8px;
                border-radius: 4px;
                border-left: 3px solid #0066cc;
            }
            
            .file-item-detail-label {
                color: #999;
                font-size: 11px;
                text-transform: uppercase;
                font-weight: 600;
            }
            
            .file-item-detail-value {
                color: #333;
                font-weight: 500;
                margin-top: 2px;
            }
            
            .file-item-actions {
                flex-shrink: 0;
            }
            
            .remove-file-btn {
                background: #ff6b6b;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
                white-space: nowrap;
            }
            
            .remove-file-btn:hover {
                background: #ee5a52;
            }

            .tools-btn {
                background: #4a90e2;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
                white-space: nowrap;
                margin-right: 8px;
            }

            .tools-btn:hover { background: #3a78c2; }
            
            .empty-state {
                text-align: center;
                padding: 40px 20px;
                color: #999;
            }
            
            .empty-state .icon {
                font-size: 40px;
                margin-bottom: 10px;
            }
            
            .empty-state p {
                font-size: 14px;
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Image Tools</h1>
                <a href="/ui"><button class="back-btn">← Kembali</button></a>
            </div>
            
            <div class="content">
                <div class="section-header">
                    <h2>Pilih File</h2>
                    <button class="add-file-btn" id="addFileBtn">+ Add File</button>
                </div>
                
                <div id="fileListContainer" class="file-list">
                    <div class="empty-state">
                        <div class="icon">📁</div>
                        <p>Belum ada file yang dipilih</p>
                        <p style="font-size: 12px; margin-top: 10px;">Klik "Add File" untuk memilih file</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let selectedFiles = [];
            
            document.getElementById('addFileBtn').addEventListener('click', () => {
                try{
                    if(typeof openFileDialog === 'function'){
                        openFileDialog((filepath) => addSelectedFile(filepath));
                        return;
                    }

                    // Try to dynamically load the component script if it's not yet available
                    const existing = document.querySelector('script[src="/ui/file-dialog-component"]');
                    if(!existing){
                        const s = document.createElement('script');
                        s.src = '/ui/file-dialog-component';
                        s.onload = () => {
                            try{
                                if(typeof openFileDialog === 'function'){
                                    openFileDialog((filepath) => addSelectedFile(filepath));
                                } else {
                                    const fp = prompt('File dialog failed to initialize. Paste image filepath:');
                                    if(fp) addSelectedFile(fp);
                                }
                            }catch(e){ console.error('After load openFileDialog error', e); alert('Error opening file dialog: '+e.message); }
                        };
                        s.onerror = () => {
                            const fp = prompt('File dialog not available. Paste image filepath:');
                            if(fp) addSelectedFile(fp);
                        };
                        document.body.appendChild(s);
                        return;
                    }

                    // If script tag exists but function not defined, wait briefly and retry
                    setTimeout(()=>{
                        if(typeof openFileDialog === 'function'){
                            openFileDialog((filepath) => addSelectedFile(filepath));
                        } else {
                            const fp = prompt('File dialog not available. Paste image filepath:');
                            if(fp) addSelectedFile(fp);
                        }
                    }, 300);

                }catch(e){
                    console.error('Add File failed:', e);
                    alert('Add File failed: ' + (e && e.message ? e.message : e));
                }
            });
            
            function addSelectedFile(filepath) {
                if(selectedFiles.find(f => f.path === filepath)) {
                    alert('File sudah dipilih');
                    return;
                }
                
                // Fetch image info
                fetch('/api/file-info?filepath=' + encodeURIComponent(filepath))
                    .then(res => res.json())
                    .then(data => {
                        selectedFiles.push({
                            path: filepath,
                            info: data
                        });
                        renderFileList();
                    })
                    .catch(err => {
                        alert('Error loading image info: ' + err.message);
                    });
            }
            
            function removeSelectedFile(filepath) {
                selectedFiles = selectedFiles.filter(f => f.path !== filepath);
                renderFileList();
            }
            
            function renderFileList() {
                const container = document.getElementById('fileListContainer');
                if(selectedFiles.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="icon">📁</div>
                            <p>Belum ada file yang dipilih</p>
                            <p style="font-size: 12px; margin-top: 10px;">Klik "Add File" untuk memilih file</p>
                        </div>
                    `;
                } else {
                    container.innerHTML = selectedFiles.map((file) => {
                        // Collapse any sequence of backslashes into a single backslash for Windows paths
                        const displayPath = (file.path || '').replace(/\\+/g, '\\');
                        const info = file.info || {};
                            // Request a small webp thumbnail (10% scale / quality) for fast preview
                            const previewUrl = '/ui/thumbnail?filepath=' + encodeURIComponent(file.path);

                        let dimensions = '-';
                        let dpi = '-';
                        let colorMode = '-';
                        let fileSize = '-';

                        if(info.dimensions) {
                            dimensions = info.dimensions;
                        }
                        if(info.dpi) {
                            dpi = info.dpi;
                        }
                        if(info.color_mode) {
                            colorMode = info.color_mode;
                        }
                        if(info.size_mb) {
                            fileSize = info.size_mb;
                        }

                        return `
                            <div class="file-item" data-path=${JSON.stringify(file.path)}>
                                <div class="file-item-preview">
                                    <img src="${previewUrl}" alt="Preview" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Crect fill=%22%23e0e0e0%22 width=%22120%22 height=%22120%22/%3E%3C/svg%3E'">
                                </div>
                                <div class="file-item-content">
                                    <div class="file-item-info">
                                        <div class="file-item-name">${displayPath}</div>
                                    </div>
                                    <div class="file-item-details">
                                        <div class="file-item-detail">
                                            <div class="file-item-detail-label">Panjang (cm)</div>
                                            <div class="file-item-detail-value">${info.height_cm || '-'}</div>
                                        </div>
                                        <div class="file-item-detail">
                                            <div class="file-item-detail-label">Lebar (cm)</div>
                                            <div class="file-item-detail-value">${info.width_cm || '-'}</div>
                                        </div>
                                        <div class="file-item-detail">
                                            <div class="file-item-detail-label">Dimensi (px)</div>
                                            <div class="file-item-detail-value">${dimensions}</div>
                                        </div>
                                        <div class="file-item-detail">
                                            <div class="file-item-detail-label">DPI</div>
                                            <div class="file-item-detail-value">${dpi}</div>
                                        </div>
                                        <div class="file-item-detail">
                                            <div class="file-item-detail-label">Mode Warna</div>
                                            <div class="file-item-detail-value">${colorMode}</div>
                                        </div>
                                        <div class="file-item-detail">
                                            <div class="file-item-detail-label">Ukuran File (MB)</div>
                                            <div class="file-item-detail-value">${fileSize}</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="file-item-actions">
                                    <button class="tools-btn" onclick='openTools(${JSON.stringify(file.path)})'>Tools</button>
                                    <button class="remove-file-btn" onclick='removeSelectedFile(${JSON.stringify(file.path)})'>Remove</button>
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            }

            // Tools dialog: shows a compact editor/preview similar to the provided UI
            function openTools(filepath){
                try{
                    // If modal already exists, just populate and show
                    if(document.getElementById('toolsModal')){
                        document.getElementById('toolsModal').style.display = 'flex';
                        populateTools(filepath);
                        return;
                    }

                    const modal = document.createElement('div');
                    modal.id = 'toolsModal';
                    modal.style.position = 'fixed';
                    modal.style.left = 0;
                    modal.style.top = 0;
                    modal.style.right = 0;
                    modal.style.bottom = 0;
                    modal.style.background = 'rgba(0,0,0,0.5)';
                    modal.style.display = 'flex';
                    modal.style.alignItems = 'center';
                    modal.style.justifyContent = 'center';
                    modal.style.zIndex = 11000;

                    modal.innerHTML = `
                        <div style="width:96%;max-width:1200px;background:#f6f8fb;border-radius:8px;padding:12px;display:flex;flex-direction:column;gap:12px;box-shadow:0 12px 40px rgba(0,0,0,0.3);">
                            <div style="display:flex;gap:12px">
                                <div style="flex:1;display:flex;flex-direction:column;gap:8px">
                                    <div style="display:flex;justify-content:space-between;align-items:center">
                                        <div style="font-weight:600;color:#333">Tools — Preview</div>
                                        <div style="display:flex;gap:8px;align-items:center">
                                            <button id="toolsRotateBtn" style="padding:6px 8px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">Rotasi</button>
                                            <button id="toolsScaleBtn" style="padding:6px 8px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">Skala</button>
                                            <button id="toolsCloseBtn" style="padding:6px 8px;border-radius:6px;border:none;background:#ff6b6b;color:#fff;cursor:pointer">Close</button>
                                        </div>
                                    </div>

                                    <div style="background:#fff;border-radius:6px;padding:12px;min-height:180px;display:flex;align-items:center;justify-content:center;position:relative">
                                        <img id="toolsPreviewImg" src="" style="max-width:100%;max-height:320px;object-fit:contain;border-radius:4px;" alt="preview"/>
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center">
                                        <input id="toolsPath" type="text" style="flex:1;padding:8px;border-radius:4px;border:1px solid #ccc;font-family:monospace" readonly />
                                        <button id="toolsOpenInExplorer" title="Open in file explorer" style="padding:6px;border-radius:4px;background:#4a90e2;color:#fff;border:none;cursor:pointer">↗</button>
                                    </div>
                                    <div style="margin-top:6px;display:flex;align-items:center;gap:8px">
                                        <label style="white-space:nowrap;color:#333;font-weight:600">Finishing Template :</label>
                                        <select id="toolsFinishingTemplate" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px">
                                            <option>NON FINISHING</option>
                                            <option>POLOS</option>
                                            <option>LP4</option>
                                            <option>LIPAT</option>
                                            <option>DOUBLE SIDE</option>
                                            <option>UMBUL2</option>
                                            <option>CUSTOM</option>
                                        </select>
                                    </div>
                                </div>

                                <div style="width:340px;display:flex;flex-direction:column;gap:8px">
                                    <div style="background:#fff;padding:12px;border-radius:6px">
                                        <div style="font-size:12px;color:#777;margin-bottom:6px">Informasi</div>
                                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
                                            <div>
                                                <div style="font-size:11px;color:#999">Panjang (cm)</div>
                                                <input id="toolsHeightCm" type="text" style="width:100%;padding:8px;border-radius:4px;border:1px solid #ddd" />
                                            </div>
                                            <div>
                                                <div style="font-size:11px;color:#999">Lebar (cm)</div>
                                                <input id="toolsWidthCm" type="text" style="width:100%;padding:8px;border-radius:4px;border:1px solid #ddd" />
                                            </div>
                                            <div>
                                                <div style="font-size:11px;color:#999">Dimensi (px)</div>
                                                <input id="toolsDimensionsPx" type="text" readonly style="width:100%;padding:8px;border-radius:4px;border:1px solid #eee;background:#fafafa" />
                                            </div>
                                            <div>
                                                <div style="font-size:11px;color:#999">DPI</div>
                                                <input id="toolsDpi" type="text" style="width:100%;padding:8px;border-radius:4px;border:1px solid #ddd" />
                                            </div>
                                            <div style="grid-column:1/2">
                                                <div style="font-size:11px;color:#999">Mode Warna</div>
                                                <input id="toolsColorMode" type="text" style="width:100%;padding:8px;border-radius:4px;border:1px solid #ddd" />
                                            </div>
                                            <div style="grid-column:2/3">
                                                <div style="font-size:11px;color:#999">Ukuran File (MB)</div>
                                                <input id="toolsFileSizeMb" type="text" readonly style="width:100%;padding:8px;border-radius:4px;border:1px solid #eee;background:#fafafa" />
                                            </div>
                                        </div>
                                    </div>

                                    <div style="background:#fff;padding:10px;border-radius:6px;display:flex;gap:8px;align-items:center;justify-content:flex-end">
                                        <button id="toolsApplyBtn" style="padding:8px 12px;border-radius:6px;border:none;background:#4caf50;color:#fff;cursor:pointer">Apply</button>
                                        <button id="toolsCancelBtn" style="padding:8px 12px;border-radius:6px;border:1px solid #ccc;background:#fff;cursor:pointer">Cancel</button>
                                    </div>
                                </div>
                            </div>

                            <!-- Lower controls area: three panels similar to screenshot -->
                            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
                                <!-- Left: Plong -->
                                <div style="background:#fff;padding:12px;border-radius:6px">
                                    <div style="font-weight:600;margin-bottom:8px">Aktifkan Plong</div>
                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                                        <input id="plongEnable" type="checkbox" />
                                        <label for="plongEnable">Aktifkan Plong</label>
                                    </div>
                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
                                        <input id="plongFold4" type="checkbox" /> <label style="font-size:13px">Lipat Plong 4</label>
                                    </div>

                                    <div style="display:grid;grid-template-columns:1fr 120px 1fr;gap:6px;align-items:center;justify-items:center;margin-bottom:8px">
                                        <div></div>
                                        <input id="jarak_plong_atas" type="text" placeholder="Top" value="2" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px;text-align:center" />
                                        <div></div>

                                        <input id="jarak_plong_kiri" type="text" placeholder="Left" value="2" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px;text-align:center" />
                                        <div style="width:120px;height:40px;display:flex;align-items:center;justify-content:center;border:1px dashed #bbb;border-radius:4px;background:#fafafa">
                                            <img id="plongCenterPreview" src="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2236%22 height=%2236%22%3E%3Crect fill=%22%23f6f6f6%22 width=%2236%22 height=%2236%22/%3E%3C/svg%3E" alt="preview" style="max-width:36px;max-height:36px;"/>
                                        </div>
                                        <input id="jarak_plong_kanan" type="text" placeholder="Right" value="2" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px;text-align:center" />

                                        <div></div>
                                        <input id="jarak_plong_bawah" type="text" placeholder="Bottom" value="2" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px;text-align:center" />
                                        <div></div>
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
                                        <input id="plongCorner" type="checkbox" /> <label for="plongCorner">Bawah Pojok</label>
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
                                        <label style="width:90px;font-size:12px;color:#666">Warna Plong</label>
                                        <select id="plongColor" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px"><option>White</option><option>Black</option></select>
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
                                        <label style="width:90px;font-size:12px;color:#666">Jarak Plong</label>
                                        <input id="jarak_plong" type="text" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center">
                                        <label style="width:90px;font-size:12px;color:#666">Bentuk plong</label>
                                        <div>
                                            <label style="margin-right:8px"><input type="radio" name="bentuk_plong" value="circle" id="bentuk_circle"> Bulat</label>
                                            <label><input type="radio" name="bentuk_plong" value="square" id="bentuk_square"> Kotak</label>
                                        </div>
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center;margin-top:8px">
                                        <label style="width:90px;font-size:12px;color:#666">Ukuran plong</label>
                                        <input id="diameter_lebar" type="text" placeholder="lebar" style="width:70px;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                        <span style="align-self:center">x</span>
                                        <input id="diameter_panjang" type="text" placeholder="panjang" style="width:70px;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center;margin-top:8px">
                                        <label style="width:90px;font-size:12px;color:#666">Diameter plong</label>
                                        <input id="diameter_single" type="text" style="width:100px;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                    </div>
                                </div>

                                <!-- Middle: Lebihan -->
                                <div style="background:#fff;padding:12px;border-radius:6px">
                                    <div style="font-weight:600;margin-bottom:8px">Aktifkan Lebihan</div>
                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                                        <input id="lebihanEnable" type="checkbox" />
                                        <label for="lebihanEnable">Aktifkan Lebihan</label>
                                    </div>

                                    <div style="margin-bottom:8px">
                                        <div style="font-size:12px;color:#666;margin-bottom:6px">Lebihan Keliling</div>
                                        <input id="lebihanAll" type="number" step="0.1" value="2.5" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px" />
                                    </div>

                                    <div style="display:grid;grid-template-columns:1fr 120px 1fr;gap:6px;align-items:center;justify-items:center;margin-bottom:8px">
                                        <div></div>
                                        <input id="lebTop" type="number" step="0.1" placeholder="Top" value="2.5" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px;text-align:center" />
                                        <div></div>

                                        <input id="lebLeft" type="number" step="0.1" placeholder="Left" value="2.5" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px;text-align:center" />
                                        <div style="width:120px;height:40px;display:flex;align-items:center;justify-content:center;border:1px dashed #bbb;border-radius:4px;background:#fafafa">
                                            <img id="lebCenterPreview" src="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2236%22 height=%2236%22%3E%3Crect fill=%22%23f6f6f6%22 width=%2236%22 height=%2236%22/%3E%3C/svg%3E" alt="preview" style="max-width:36px;max-height:36px;"/>
                                        </div>
                                        <input id="lebRight" type="number" step="0.1" placeholder="Right" value="2.5" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px;text-align:center" />

                                        <div></div>
                                        <input id="lebBottom" type="number" step="0.1" placeholder="Bottom" value="2.5" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px;text-align:center" />
                                        <div></div>
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                                        <input id="lebRemoveScript" type="checkbox" /> <label>Hapus file script & setting</label>
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                                        <label style="width:90px;font-size:12px;color:#666">Background</label>
                                        <select id="lebBackground" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px">
                                            <option>White</option>
                                            <option>Transparent</option>
                                            <option>Black</option>
                                        </select>
                                    </div>

                                    <div style="display:flex;gap:8px;align-items:center">
                                        <label style="width:90px;font-size:12px;color:#666">Warna garis</label>
                                        <select id="lebLineColor" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px">
                                            <option>Black</option>
                                            <option>White</option>
                                            <option>Red</option>
                                        </select>
                                    </div>

                                    <div style="margin-top:8px;display:flex;align-items:center;gap:8px">
                                        <label style="width:110px;color:#666">Kualitas Export</label>
                                        <input id="lebQuality" type="number" step="1" min="1" max="100" value="80" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                    </div>
                                </div>

                                <!-- Right: Pesan -->
                                <div style="background:#fff;padding:12px;border-radius:6px">
                                    <div style="font-weight:600;margin-bottom:8px">Aktifkan Pesan</div>
                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                                        <input id="pesanDefault" type="checkbox" checked /> <label>Default</label>
                                        <input id="pesanEnable" type="checkbox" /> <label>Pesan</label>
                                    </div>
                                    <div style="margin-bottom:8px">
                                        <div style="font-size:12px;color:#666">Pesan Text</div>
                                        <input id="pesanText" type="text" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                    </div>
                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                                        <label style="width:90px;color:#666">Ukuran</label>
                                        <input id="pesanSize" type="number" step="0.1" style="width:80px;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                    </div>
                                    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                                        <label style="width:90px;color:#666">Warna</label>
                                        <select id="pesanColor" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px"><option>Black</option><option>White</option></select>
                                    </div>
                                    <div style="display:flex;gap:8px;align-items:center">
                                        <label style="width:90px;color:#666">Posisi X</label>
                                        <input id="pesanX" type="number" style="width:60px;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                        <label style="width:60px;color:#666">Posisi Y</label>
                                        <input id="pesanY" type="number" style="width:60px;padding:6px;border:1px solid #ddd;border-radius:4px" />
                                    </div>
                                    <div style="margin-top:8px">
                                        <label style="font-size:12px;color:#666">Posisi</label>
                                        <select id="pesanPos" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"><option>vertical</option><option>horizontal</option></select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

                    document.body.appendChild(modal);

                    // Wire controls
                    document.getElementById('toolsCloseBtn').addEventListener('click', ()=>{ modal.style.display='none'; });
                    document.getElementById('toolsCancelBtn').addEventListener('click', ()=>{ modal.style.display='none'; });
                    document.getElementById('toolsOpenInExplorer').addEventListener('click', ()=>{
                        try{
                            const p = document.getElementById('toolsPath').value;
                            fetch('/api/open-path', {
                                method: 'POST',
                                headers: {'Content-Type':'application/json'},
                                body: JSON.stringify({filepath: p})
                            }).then(r=>r.json()).then(j=>{
                                if(j && j.ok){
                                    alert('Opened in Explorer');
                                } else {
                                    alert('Failed to open: '+(j && (j.error||j.message) ? (j.error||j.message) : 'Unknown'));
                                }
                            }).catch(e=>{ alert('Open failed: '+e.message); });
                        }catch(e){ alert('Open failed: '+e.message); }
                    });

                    // rotate logic
                    let rot = 0;
                    document.getElementById('toolsRotateBtn').addEventListener('click', ()=>{
                        rot = (rot + 90) % 360;
                        const img = document.getElementById('toolsPreviewImg');
                        img.style.transform = `rotate(${rot}deg)`;
                    });

                    // scale logic (toggle small preview / original)
                    let scaled = false;
                    document.getElementById('toolsScaleBtn').addEventListener('click', ()=>{
                        const img = document.getElementById('toolsPreviewImg');
                        if(!scaled){ img.style.width = '100%'; img.style.maxHeight = '160px'; scaled = true; } else { img.style.width='auto'; img.style.maxHeight='320px'; scaled=false; }
                    });

                    // apply action: simply copy edited fields back to selectedFiles array if present
                    document.getElementById('toolsApplyBtn').addEventListener('click', ()=>{
                        try{
                            const p = document.getElementById('toolsPath').value;
                            const hf = document.getElementById('toolsHeightCm').value;
                            const wf = document.getElementById('toolsWidthCm').value;
                            const dpi = document.getElementById('toolsDpi').value;
                            // extra fields
                            const plong = !!document.getElementById('plongEnable').checked;
                            const plongFold4 = !!document.getElementById('plongFold4').checked;
                            const plongTop = document.getElementById('jarak_plong_atas') ? document.getElementById('jarak_plong_atas').value : null;
                            const plongLeft = document.getElementById('jarak_plong_kiri') ? document.getElementById('jarak_plong_kiri').value : null;
                            const plongRight = document.getElementById('jarak_plong_kanan') ? document.getElementById('jarak_plong_kanan').value : null;
                            const plongBottom = document.getElementById('jarak_plong_bawah') ? document.getElementById('jarak_plong_bawah').value : null;
                            const plongCorner = !!document.getElementById('plongCorner').checked;
                            const plongColor = document.getElementById('plongColor') ? document.getElementById('plongColor').value : null;
                            const plongGap = document.getElementById('jarak_plong') ? document.getElementById('jarak_plong').value : null;
                            const bentuk_plong = document.getElementById('bentuk_circle') && document.getElementById('bentuk_circle').checked ? 'circle' : (document.getElementById('bentuk_square') && document.getElementById('bentuk_square').checked ? 'square' : null);
                            const diameter_lebar = document.getElementById('diameter_lebar') ? document.getElementById('diameter_lebar').value : null;
                            const diameter_panjang = document.getElementById('diameter_panjang') ? document.getElementById('diameter_panjang').value : null;
                            const diameter_single = document.getElementById('diameter_single') ? document.getElementById('diameter_single').value : null;

                            const lebEnable = !!document.getElementById('lebihanEnable').checked;
                            const lebAll = document.getElementById('lebihanAll').value;
                            const lebTop = document.getElementById('lebTop').value;
                            const lebBottom = document.getElementById('lebBottom').value;
                            const lebLeft = document.getElementById('lebLeft').value;
                            const lebRight = document.getElementById('lebRight').value;
                            const lebRemove = !!document.getElementById('lebRemoveScript').checked;
                            const lebQuality = document.getElementById('lebQuality').value;
                            const lebBackground = document.getElementById('lebBackground') ? document.getElementById('lebBackground').value : null;
                            const lebLineColor = document.getElementById('lebLineColor') ? document.getElementById('lebLineColor').value : null;

                            const pesanDefault = !!document.getElementById('pesanDefault').checked;
                            const pesanEnable = !!document.getElementById('pesanEnable').checked;
                            const pesanText = document.getElementById('pesanText').value;
                            const pesanSize = document.getElementById('pesanSize').value;
                            const pesanColor = document.getElementById('pesanColor').value;
                            const pesanX = document.getElementById('pesanX').value;
                            const pesanY = document.getElementById('pesanY').value;
                            const pesanPos = document.getElementById('pesanPos').value;
                            const finishingTemplate = document.getElementById('toolsFinishingTemplate') ? document.getElementById('toolsFinishingTemplate').value : null;

                            // update in-memory selectedFiles if present
                            const idx = selectedFiles.findIndex(s=>s.path===p);
                            if(idx !== -1){
                                if(!selectedFiles[idx].info) selectedFiles[idx].info = {};
                                selectedFiles[idx].info.width_cm = wf || selectedFiles[idx].info.width_cm;
                                selectedFiles[idx].info.height_cm = hf || selectedFiles[idx].info.height_cm;
                                selectedFiles[idx].info.dpi = dpi || selectedFiles[idx].info.dpi;

                                // plong
                                selectedFiles[idx].info.plong = plong;
                                selectedFiles[idx].info.plong_fold4 = plongFold4;
                                selectedFiles[idx].info.jarak_plong_atas = plongTop;
                                selectedFiles[idx].info.jarak_plong_kiri = plongLeft;
                                selectedFiles[idx].info.jarak_plong_kanan = plongRight;
                                selectedFiles[idx].info.jarak_plong_bawah = plongBottom;
                                selectedFiles[idx].info.jenis_plong = plongCorner ? 'pojok' : (selectedFiles[idx].info.jenis_plong || 'pojok');
                                selectedFiles[idx].info.warna_plong = plongColor || selectedFiles[idx].info.warna_plong;
                                selectedFiles[idx].info.jarak_plong = plongGap || selectedFiles[idx].info.jarak_plong;
                                selectedFiles[idx].info.bentuk_plong = bentuk_plong || selectedFiles[idx].info.bentuk_plong;
                                selectedFiles[idx].info.diameter_lebar = diameter_lebar || selectedFiles[idx].info.diameter_lebar;
                                selectedFiles[idx].info.diameter_panjang = diameter_panjang || selectedFiles[idx].info.diameter_panjang;
                                selectedFiles[idx].info.diameter_single = diameter_single || selectedFiles[idx].info.diameter_single;

                                // lebihan
                                selectedFiles[idx].info.lebihan = lebEnable;
                                selectedFiles[idx].info.lebihan_all = lebAll;
                                selectedFiles[idx].info.leb_top = lebTop;
                                selectedFiles[idx].info.leb_bottom = lebBottom;
                                selectedFiles[idx].info.leb_left = lebLeft;
                                selectedFiles[idx].info.leb_right = lebRight;
                                selectedFiles[idx].info.leb_remove_script = lebRemove;
                                selectedFiles[idx].info.leb_quality = lebQuality;
                                selectedFiles[idx].info.lebBackground = lebBackground;
                                selectedFiles[idx].info.lebLineColor = lebLineColor;

                                // pesan
                                selectedFiles[idx].info.pesan_default = pesanDefault;
                                selectedFiles[idx].info.pesan_enabled = pesanEnable;
                                selectedFiles[idx].info.pesan_text = pesanText;
                                selectedFiles[idx].info.pesan_size = pesanSize;
                                selectedFiles[idx].info.pesan_color = pesanColor;
                                selectedFiles[idx].info.pesan_x = pesanX;
                                selectedFiles[idx].info.pesan_y = pesanY;
                                selectedFiles[idx].info.pesan_pos = pesanPos;
                                // finishing
                                if(finishingTemplate) selectedFiles[idx].info.finishing_template = finishingTemplate;
                            }
                            renderFileList();
                            modal.style.display='none';
                        }catch(e){ alert('Apply failed: '+e.message); }
                    });

                    // populate for first show
                    populateTools(filepath);

                    function populateTools(fp){
                        if(!fp) return;
                        const imgEl = document.getElementById('toolsPreviewImg');
                        const pathEl = document.getElementById('toolsPath');
                        pathEl.value = fp;
                        if(fp){
                            imgEl.src = '/ui/thumbnail?filepath=' + encodeURIComponent(fp);
                            try{ var lebImg = document.getElementById('lebCenterPreview'); if(lebImg) lebImg.src = '/ui/thumbnail?filepath='+encodeURIComponent(fp); }catch(e){}
                        } else {
                            imgEl.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22320%22 height=%22320%22%3E%3Crect fill=%22%23eaeaea%22 width=%22320%22 height=%22320%22/%3E%3C/svg%3E';
                        }
                        
                        // Find saved info from selectedFiles first
                        let savedInfo = null;
                        const fileIdx = selectedFiles.findIndex(f => f.path === fp);
                        if(fileIdx >= 0) {
                            savedInfo = selectedFiles[fileIdx].info || {};
                        }
                        
                        // fetch info for basic file metadata
                        fetch('/api/file-info?filepath='+encodeURIComponent(fp)).then(r=>r.json()).then(data=>{
                            const fileInfo = data || {};
                            // Merge: use saved info for tool settings, file info for metadata
                            const info = { ...fileInfo, ...savedInfo };
                            
                            document.getElementById('toolsDimensionsPx').value = info.dimensions || '-';
                            document.getElementById('toolsWidthCm').value = info.width_cm || '';
                            document.getElementById('toolsHeightCm').value = info.height_cm || '';
                            document.getElementById('toolsDpi').value = info.dpi || '';
                            document.getElementById('toolsColorMode').value = info.color_mode || '';
                            document.getElementById('toolsFileSizeMb').value = info.size_mb || '';
                            // populate extended fields if present
                            try{
                                document.getElementById('plongEnable').checked = !!(info.plong);
                                document.getElementById('plongFold4').checked = !!(info.plong_fold4);
                                document.getElementById('jarak_plong_atas').value = (info.jarak_plong_atas !== undefined && info.jarak_plong_atas !== '') ? info.jarak_plong_atas : '2';
                                document.getElementById('jarak_plong_kiri').value = (info.jarak_plong_kiri !== undefined && info.jarak_plong_kiri !== '') ? info.jarak_plong_kiri : '2';
                                document.getElementById('jarak_plong_kanan').value = (info.jarak_plong_kanan !== undefined && info.jarak_plong_kanan !== '') ? info.jarak_plong_kanan : '2';
                                document.getElementById('jarak_plong_bawah').value = (info.jarak_plong_bawah !== undefined && info.jarak_plong_bawah !== '') ? info.jarak_plong_bawah : '2';
                                document.getElementById('plongCorner').checked = !!(info.jenis_plong === 'pojok');
                                if(info.warna_plong) document.getElementById('plongColor').value = info.warna_plong;
                                document.getElementById('jarak_plong').value = info.jarak_plong || '';
                                if(info.bentuk_plong === 'circle') document.getElementById('bentuk_circle').checked = true;
                                else if(info.bentuk_plong === 'square') document.getElementById('bentuk_square').checked = true;
                                document.getElementById('diameter_lebar').value = info.diameter_lebar || info.diameter_lebar || '';
                                document.getElementById('diameter_panjang').value = info.diameter_panjang || '';
                                document.getElementById('diameter_single').value = info.diameter_single || info.diameter_lebar || '';
                                try{ var pc = document.getElementById('plongCenterPreview'); if(pc && fp) pc.src = '/ui/thumbnail?filepath='+encodeURIComponent(fp); }catch(e){}

                                // finishing template
                                if(info.finishing_template){
                                    try{ document.getElementById('toolsFinishingTemplate').value = info.finishing_template; }catch(e){}
                                }

                                document.getElementById('lebihanEnable').checked = !!(info.lebihan);
                                document.getElementById('lebihanAll').value = (info.lebihan_all !== undefined && info.lebihan_all !== '') ? info.lebihan_all : '2.5';
                                document.getElementById('lebTop').value = (info.leb_top !== undefined && info.leb_top !== '') ? info.leb_top : '2.5';
                                document.getElementById('lebBottom').value = (info.leb_bottom !== undefined && info.leb_bottom !== '') ? info.leb_bottom : '2.5';
                                document.getElementById('lebLeft').value = (info.leb_left !== undefined && info.leb_left !== '') ? info.leb_left : '2.5';
                                document.getElementById('lebRight').value = (info.leb_right !== undefined && info.leb_right !== '') ? info.leb_right : '2.5';
                                document.getElementById('lebRemoveScript').checked = !!(info.leb_remove_script);
                                document.getElementById('lebQuality').value = info.leb_quality || 80;
                                if(info.lebBackground) try{ document.getElementById('lebBackground').value = info.lebBackground; }catch(e){}
                                if(info.lebLineColor) try{ document.getElementById('lebLineColor').value = info.lebLineColor; }catch(e){}

                                document.getElementById('pesanDefault').checked = !!(info.pesan_default);
                                document.getElementById('pesanEnable').checked = !!(info.pesan_enabled);
                                document.getElementById('pesanText').value = info.pesan_text || '';
                                document.getElementById('pesanSize').value = info.pesan_size || '';
                                if(info.pesan_color) document.getElementById('pesanColor').value = info.pesan_color;
                                document.getElementById('pesanX').value = info.pesan_x || '';
                                document.getElementById('pesanY').value = info.pesan_y || '';
                                if(info.pesan_pos) document.getElementById('pesanPos').value = info.pesan_pos;
                            }catch(ee){ /* ignore missing fields */ }
                        }).catch(e=>{ console.warn(e); });
                    }

                    // Attach finishing template change handler: update Plong, Lebihan, Pesan
                    try{
                        const tplEl = document.getElementById('toolsFinishingTemplate');
                        if(tplEl){
                            tplEl.addEventListener('change', (ev)=>{
                                const v = ev && ev.target ? ev.target.value : (tplEl.value || '');
                                try{
                                    // default: uncheck all checkboxes first (initial state)
                                    try{
                                        const modal = document.getElementById('previewModal');
                                        const container = modal || document;
                                        const cbs = container.querySelectorAll('input[type="checkbox"]');
                                        cbs.forEach(cb=>{ cb.checked = false; });
                                        // also clear pesan text by default
                                        const pesanTextClear = document.getElementById('pesanText'); if(pesanTextClear) pesanTextClear.value = '';
                                    }catch(inner){ console.warn('Failed to reset defaults', inner); }

                                    if(v === 'NON FINISHING'){
                                        // all already unchecked
                                    } else if(v === 'POLOS'){
                                        const leb = document.getElementById('lebihanEnable'); if(leb) leb.checked = true;
                                        const pesan = document.getElementById('pesanEnable'); if(pesan) pesan.checked = true;
                                        const pesanText = document.getElementById('pesanText'); if(pesanText) pesanText.value = 'POLOS';
                                    } else if(v === 'LP4'){
                                        const plong = document.getElementById('plongEnable'); if(plong) plong.checked = true;
                                        const plongFold4 = document.getElementById('plongFold4'); if(plongFold4) plongFold4.checked = true;
                                        const pesan = document.getElementById('pesanEnable'); if(pesan) pesan.checked = true;
                                        const pesanText = document.getElementById('pesanText'); if(pesanText) pesanText.value = 'LP4';
                                    } else if(v === 'LIPAT'){
                                        const leb = document.getElementById('lebihanEnable'); if(leb) leb.checked = true;
                                        const pesan = document.getElementById('pesanEnable'); if(pesan) pesan.checked = true;
                                        const pesanText = document.getElementById('pesanText'); if(pesanText) pesanText.value = 'LIPAT';
                                    } else if(v === 'DOUBLE SIDE'){
                                        const pesan = document.getElementById('pesanEnable'); if(pesan) pesan.checked = true;
                                        const pesanText = document.getElementById('pesanText'); if(pesanText) pesanText.value = 'DOUBLE SIDE';
                                    }
                                }catch(err){ console.warn('Finishing change handler error', err); }
                            });
                        }
                    }catch(e){ console.warn(e); }

                    return;
                }catch(e){ console.warn(e); alert('Failed to open tools: '+e.message); }
            }
        </script>
        
        <!-- Include Universal File Dialog Component -->
        <script src="/ui/file-dialog-component"></script>
    </body>
    </html>
    """
    )


@app.route("/ui/finishing-process", methods=["POST"])
def ui_finishing_process():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"status": "error", "message": "Missing JSON body"}), 400

        result = execute("finishing_process", payload, timeout_seconds=120)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/finishing-editor")
def ui_finishing_editor():
    return render_template_string(
        r"""
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Finishing Editor — Printing Agent</title>
<style>
  :root{
    --bg-base:#eef0f3;
    --bg-panel:#ffffff;
    --bg-inset:#f6f8fa;
    --line:rgba(0,0,0,0.045);
    --line-strong:#d9dee5;
    --cyan:#0066cc;
    --cyan-dim:#7aa7d4;
    --amber:#e67e22;
    --text:#222222;
    --text-dim:#667080;
    --text-faint:#98a2ad;
    --ruler:36px;
    --mono: ui-monospace, "SF Mono", "Cascadia Mono", "Roboto Mono", Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{
    background:
      linear-gradient(var(--line) 1px, transparent 1px) 0 0/28px 28px,
      linear-gradient(90deg, var(--line) 1px, transparent 1px) 0 0/28px 28px,
      var(--bg-base);
    color:var(--text);
    font-family:var(--sans);
    min-height:100vh;
    -webkit-font-smoothing:antialiased;
  }
  header{
    padding:22px 24px 16px;
    border-bottom:1px solid var(--line-strong);
    display:flex;
    align-items:baseline;
    gap:14px;
    flex-wrap:wrap;
  }
  header .mark{
    font-family:var(--mono); font-size:12px; color:var(--cyan);
    border:1px solid var(--cyan-dim); padding:3px 8px; border-radius:3px; letter-spacing:0.08em;
  }
  header h1{ font-size:19px; margin:0; font-weight:600; }
  header p{ margin:0; color:var(--text-dim); font-size:13px; font-family:var(--mono); }
  header .back{
    margin-left:auto; color:var(--text-dim); text-decoration:none; font-size:13px;
    border:1px solid var(--line-strong); padding:6px 12px; border-radius:5px;
  }
  header .back:hover{border-color:var(--cyan); color:var(--cyan);}

  .layout{ display:grid; grid-template-columns:320px 1fr; gap:0; min-height:calc(100vh - 76px); }
  @media (max-width: 880px){ .layout{grid-template-columns:1fr;} }

  .panel{ background:var(--bg-panel); border-right:1px solid var(--line-strong); padding:20px; overflow-y:auto; }
  .drop-zone{
    border:1.5px dashed var(--cyan-dim); border-radius:6px; padding:22px 14px; text-align:center; cursor:pointer;
    transition:border-color .15s, background .15s; background:var(--bg-inset);
  }
  .drop-zone:hover{ border-color:var(--cyan); background:rgba(0,102,204,0.05); }
  .drop-zone .icon{ font-family:var(--mono); font-size:22px; color:var(--cyan); display:block; margin-bottom:8px; }
  .drop-zone .t1{font-size:13.5px; color:var(--text);}
  .drop-zone .t2{font-size:11.5px; color:var(--text-faint); margin-top:4px; font-family:var(--mono); word-break:break-all;}

  .error-msg{
    margin-top:10px; padding:9px 12px; border-radius:5px;
    background:rgba(198,40,40,0.06); border:1px solid rgba(198,40,40,0.35);
    color:#c62828; font-size:12px; font-family:var(--mono); display:none;
  }

  .section{margin-top:22px;}
  .section-label{
    font-family:var(--mono); font-size:10.5px; letter-spacing:0.1em; color:var(--text-faint);
    text-transform:uppercase; margin-bottom:10px;
  }
  .control{margin-bottom:14px;}
  .control label{ display:flex; justify-content:space-between; font-size:12.5px; color:var(--text-dim); margin-bottom:6px; }
  .control label span.val{ font-family:var(--mono); color:var(--cyan); }
  .control-hint{ font-size:11px; color:var(--text-faint); margin-bottom:10px; line-height:1.5; }
  input[type=number], input[type=text]{
    width:100%; background:var(--bg-inset); color:var(--text); border:1px solid var(--line-strong);
    padding:7px 8px; border-radius:4px; font-family:var(--mono); font-size:12.5px;
  }
  select{
    width:100%; background:var(--bg-inset); color:var(--text); border:1px solid var(--line-strong);
    padding:7px 8px; border-radius:4px; font-family:var(--sans); font-size:12.5px;
  }
  input[type=color]{
    width:44px; height:32px; border:1px solid var(--line-strong); border-radius:4px;
    background:var(--bg-inset); padding:2px; cursor:pointer; flex-shrink:0;
  }
  .checkbox-row{ display:flex; align-items:center; gap:8px; font-size:12.5px; color:var(--text-dim); margin-bottom:12px; }
  .checkbox-row input{accent-color:var(--cyan);}
  .color-row{ display:flex; gap:10px; align-items:center; }
  .color-row .control{ flex:1; margin-bottom:0; }
  .field-row{ display:grid; grid-template-columns:1fr 1fr; gap:8px 10px; }

  .toggle-row{
    display:flex; align-items:center; justify-content:space-between; gap:10px;
    padding:12px 14px; border-radius:6px; border:1.5px solid var(--line-strong);
    background:var(--bg-inset); margin-bottom:12px; cursor:pointer; user-select:none;
    transition:border-color .12s, background .12s;
  }
  .toggle-row:hover{ border-color:var(--cyan-dim); }
  .toggle-row.on{ border-color:var(--amber); background:rgba(232,162,61,0.1); }
  .toggle-row .lbl{ font-size:13.5px; color:var(--text-dim); font-weight:600; }
  .toggle-row.on .lbl{ color:var(--amber); }
  .toggle-row .state{ font-family:var(--mono); font-size:10px; letter-spacing:0.06em; color:var(--text-faint); margin-right:2px; }
  .toggle-row.on .state{ color:var(--amber); }
  .switch{ position:relative; width:42px; height:22px; flex-shrink:0; pointer-events:none; }
  .switch input{ opacity:0; width:0; height:0; }
  .switch .slider{ position:absolute; inset:0; cursor:pointer; background:#cfd6dd; border-radius:22px; transition:.15s; }
  .switch .slider:before{
    content:""; position:absolute; height:16px; width:16px; left:3px; top:3px;
    background:#ffffff; border-radius:50%; transition:.15s;
  }
  .switch input:checked + .slider{ background:var(--amber); }
  .switch input:checked + .slider:before{ transform:translateX(20px); background:#1A1305; }

  .body-fields{ display:none; }
  .body-fields.show{ display:block; }

  .btn-primary{
    width:100%; background:var(--amber); color:#1A1305; border:none; padding:12px; border-radius:5px;
    font-weight:700; font-size:13.5px; cursor:pointer; margin-top:6px;
  }
  .btn-primary:hover{filter:brightness(1.08);}
  .btn-primary:disabled{background:var(--bg-inset); color:var(--text-faint); cursor:not-allowed;}
  .btn-secondary{
    width:100%; background:transparent; color:var(--text-dim); border:1px solid var(--line-strong);
    padding:10px; border-radius:5px; font-size:12.5px; cursor:pointer; margin-top:8px;
  }
  .btn-secondary:hover{border-color:var(--cyan); color:var(--cyan);}

  .stage{ padding:24px; display:flex; flex-direction:column; gap:16px; min-width:0; position:sticky; top:0; align-self:start; max-height:100vh; overflow-y:auto; }
  .empty-state{
    flex:1; display:flex; align-items:center; justify-content:center; color:var(--text-faint);
    font-family:var(--mono); font-size:13px; text-align:center; line-height:1.8;
  }

  .pane{
    background:var(--bg-inset); border:1px solid var(--line-strong); border-radius:6px;
    overflow:hidden; display:flex; flex-direction:column; min-width:0;
  }
  .pane-label{
    font-family:var(--mono); font-size:10.5px; letter-spacing:0.1em; text-transform:uppercase;
    padding:9px 12px; color:var(--cyan); border-bottom:1px solid var(--line-strong);
    display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;
  }
  .zoom-bar{ display:flex; align-items:center; gap:6px; }
  .zoom-bar button{
    background:transparent; border:1px solid var(--line-strong); color:var(--text-dim);
    width:28px; height:28px; border-radius:4px; cursor:pointer; font-family:var(--mono); font-size:14px;
  }
  .zoom-bar button:hover{ border-color:var(--cyan); color:var(--cyan); }
  .zoom-bar .zoom-val{ font-family:var(--mono); font-size:11px; color:var(--text-dim); min-width:48px; text-align:center; }

  .mode-badge{
    font-family:var(--mono); font-size:11px; font-weight:700; letter-spacing:0.06em;
    padding:3px 9px; border-radius:4px; border:1px solid transparent;
  }
  .mode-badge.rgb{ background:rgba(0,102,204,0.12); color:var(--cyan); border-color:var(--cyan-dim); }
  .mode-badge.cmyk{ background:rgba(31,122,71,0.12); color:#1f7a47; border-color:rgba(31,122,71,0.45); }
  .mode-badge.warn{ background:rgba(198,40,40,0.1); color:#c62828; border-color:rgba(198,40,40,0.45); }

  .viewport{
    display:grid;
    grid-template-columns: var(--ruler) 1fr;
    grid-template-rows: var(--ruler) 1fr;
    min-height:420px;
    max-height:70vh;
  }
  .ruler-corner{
    background:#e9ecf0; border-right:1px solid var(--line-strong); border-bottom:1px solid var(--line-strong);
    display:flex; align-items:center; justify-content:center;
    font-family:var(--mono); font-size:9px; color:var(--text-faint);
  }
  .ruler-x, .ruler-y{ position:relative; overflow:hidden; background:#e9ecf0; }
  .ruler-x{ border-bottom:1px solid var(--line-strong); }
  .ruler-y{ border-right:1px solid var(--line-strong); }
  .ruler-x canvas, .ruler-y canvas{ display:block; width:100%; height:100%; }

  .composite-wrap{
    position:relative; overflow:auto; background:#e9ecf0;
    display:flex; align-items:flex-start; justify-content:flex-start; padding:16px;
  }
  .composite{
    position:relative; line-height:0; box-shadow:0 0 0 1px rgba(79,209,232,0.15);
    flex-shrink:0;
  }
  .composite img{ display:block; width:100%; height:100%; }
  .composite canvas{ display:block; }

  .stats-bar{
    display:flex; gap:24px; flex-wrap:wrap; font-family:var(--mono); font-size:12px; color:var(--text-dim);
    border-top:1px solid var(--line-strong); padding-top:14px;
  }
  .stats-bar b{color:var(--cyan); font-weight:600;}
  .stats-bar .stat{display:flex; flex-direction:column; gap:2px;}
  .stats-bar .stat-label{color:var(--text-faint); font-size:10px; letter-spacing:0.08em; text-transform:uppercase;}

  .actions-row{display:flex; gap:10px; flex-wrap:wrap;}
  .actions-row .btn-primary, .actions-row .btn-secondary{width:auto; flex:1; min-width:160px; margin-top:0;}

  details{ border:1px solid var(--line-strong); border-radius:6px; background:var(--bg-inset); }
  details summary{ padding:10px 14px; cursor:pointer; font-family:var(--mono); font-size:12px; color:var(--text-dim); }
  details pre{
    margin:0; padding:14px; border-top:1px solid var(--line-strong); font-family:var(--mono); font-size:11px;
    color:var(--text-dim); max-height:220px; overflow:auto; white-space:pre-wrap; word-break:break-all;
  }

  .spinner{
    display:inline-block; width:14px; height:14px; border:2px solid rgba(0,0,0,0.25); border-top-color:#1A1305;
    border-radius:50%; animation:spin .7s linear infinite; vertical-align:-2px; margin-right:7px;
  }
  @keyframes spin{to{transform:rotate(360deg);}}
</style>
</head>
<body>

<header>
  <span class="mark">PRINTING AGENT</span>
  <h1>Finishing Editor</h1>
  <p>Plong · Lebihan · Pesan — indikator finishing pada gambar cetak</p>
  <a class="back" href="/ui">&larr; Menu</a>
</header>

<div class="layout">
  <div class="panel">
    <div class="drop-zone" id="dropZone">
      <span class="icon">&#9107;</span>
      <div class="t1" id="dropZoneTitle">Klik untuk pilih gambar</div>
      <div class="t2" id="dropZoneSub">.JPG / .JPEG · proses di agent :9001</div>
    </div>
    <div class="error-msg" id="errorMsg"></div>

    <div class="section">
      <div class="section-label">Finishing Template</div>
      <div class="control" style="margin-bottom:0;">
        <select id="finishingTemplate">
          <option>NON FINISHING</option>
          <option>POLOS</option>
          <option>LP4</option>
          <option>LIPAT</option>
          <option>DOUBLE SIDE</option>
        </select>
      </div>
    </div>

    <div class="section">
      <div class="section-label">Ukuran &amp; Resolusi</div>
      <div class="control">
        <label>DPI <span class="val" id="valDpi">300</span></label>
        <input type="number" id="ctrlDpi" min="36" max="1200" step="1" value="300">
      </div>
    </div>

    <div class="section">
      <div class="toggle-row" id="plongToggleBox">
        <div class="lbl">Aktifkan Plong</div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="state">NONAKTIF</span>
          <label class="switch"><input type="checkbox" id="plongEnable"><span class="slider"></span></label>
        </div>
      </div>
      <div class="body-fields" id="plongFields">
        <div class="checkbox-row"><input type="checkbox" id="plongFold4" /> <label for="plongFold4">Lipat Plong 4</label></div>
        <div class="control-hint">Jumlah lubang plong per sisi (terdistribusi rata). Isi 0 untuk sisi tanpa plong.</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;grid-template-rows:auto auto auto;gap:4px 8px;align-items:center;margin:8px 0;">
          <div></div>
          <div class="control" style="text-align:center"><label>Atas (jml)</label><input id="jml_plong_atas" type="number" min="0" step="1" value="2" /></div>
          <div></div>
          <div class="control"><label>Kiri (jml)</label><input id="jml_plong_kiri" type="number" min="0" step="1" value="2" /></div>
          <div style="display:flex;align-items:center;justify-content:center;"><svg width="40" height="40" viewBox="0 0 40 40"><line x1="20" y1="4" x2="20" y2="36" stroke="#999" stroke-width="1.5"/><line x1="4" y1="20" x2="36" y2="20" stroke="#999" stroke-width="1.5"/></svg></div>
          <div class="control"><label>Kanan (jml)</label><input id="jml_plong_kanan" type="number" min="0" step="1" value="2" /></div>
          <div></div>
          <div class="control" style="text-align:center"><label>Bawah (jml)</label><input id="jml_plong_bawah" type="number" min="0" step="1" value="2" /></div>
          <div></div>
        </div>
        <div class="control"><label>Jarak dari tepi (cm)</label><input id="plongInset" type="number" step="0.1" value="2" /></div>
        <div class="color-row">
          <input type="color" id="plongColor" value="#ffffff" />
          <div class="control"><label>Warna Plong</label></div>
          <label style="font-size:12px;display:flex;align-items:center;gap:4px;margin-left:8px;white-space:nowrap"><input type="checkbox" id="plongAutoContrast" checked /> Auto kontras</label>
        </div>
        <div class="control">
          <label>Bentuk Plong</label>
          <select id="bentukPlong"><option value="circle">Bulat</option><option value="square">Kotak</option></select>
        </div>
        <div class="field-row">
          <div class="control"><label>Diameter Lebar (cm)</label><input id="diameter_lebar" type="number" step="0.1" value="1.0" /></div>
          <div class="control"><label>Diameter Panjang (cm)</label><input id="diameter_panjang" type="number" step="0.1" value="1.0" /></div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="toggle-row" id="lebihanToggleBox">
        <div class="lbl">Aktifkan Lebihan</div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="state">NONAKTIF</span>
          <label class="switch"><input type="checkbox" id="lebihanEnable"><span class="slider"></span></label>
        </div>
      </div>
      <div class="body-fields" id="lebihanFields">
        <div class="control">
          <label>Lebihan Keliling (cm) <span class="val" id="valLebihanAll">2.5</span></label>
          <input id="lebihanAll" type="number" step="0.1" value="2.5" />
        </div>
        <div class="checkbox-row"><input type="checkbox" id="lebihanCustomSides" /> <label for="lebihanCustomSides">Atur sisi berbeda</label></div>
        <div class="field-row" id="lebihanSidesGrid" style="display:none;">
          <div class="control"><label>Atas (cm)</label><input id="lebTop" type="number" step="0.1" value="2.5" /></div>
          <div class="control"><label>Bawah (cm)</label><input id="lebBottom" type="number" step="0.1" value="2.5" /></div>
          <div class="control"><label>Kiri (cm)</label><input id="lebLeft" type="number" step="0.1" value="2.5" /></div>
          <div class="control"><label>Kanan (cm)</label><input id="lebRight" type="number" step="0.1" value="2.5" /></div>
        </div>
        <div class="color-row">
          <input type="color" id="lebBackground" value="#ffffff" />
          <div class="control"><label>Warna Background</label></div>
        </div>
        <div class="color-row">
          <input type="color" id="lebLineColor" value="#d3d3d3" />
          <div class="control"><label>Warna Garis</label></div>
        </div>
        <div class="control"><label>Ukuran Garis (cm)</label><input id="lebLineSize" type="number" step="0.05" value="0.1" /></div>
        <div class="control"><label>Garis bingkai objek</label><select id="lebBingkaiObjek"><option value="auto" selected>Auto (kontras)</option><option value="on">Selalu aktif</option><option value="off">Mati</option></select></div>
        <div class="control"><label>Kualitas Expot (%)</label><input id="lebQuality" type="number" min="1" max="100" value="80" /></div>
      </div>
    </div>

    <div class="section">
      <div class="toggle-row" id="pesanToggleBox">
        <div class="lbl">Aktifkan Pesan</div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="state">NONAKTIF</span>
          <label class="switch"><input type="checkbox" id="pesanEnable"><span class="slider"></span></label>
        </div>
      </div>
      <div class="body-fields" id="pesanFields">
        <div class="checkbox-row"><input type="checkbox" id="pesanSatuKiri" /> <label for="pesanSatuKiri">1 pesan saja (kiri)</label></div>
        <div class="control"><label>Pesan Text</label><input id="pesanText" type="text" placeholder="mis. LP4" /></div>
        <div class="control"><label>Ukuran (cm)</label><input id="pesanSize" type="number" step="0.1" value="0.8" /></div>
        <div class="color-row">
          <input type="color" id="pesanColor" value="#000000" />
          <div class="control"><label>Warna Pesan</label></div>
          <label style="font-size:12px;display:flex;align-items:center;gap:4px;margin-left:8px;white-space:nowrap"><input type="checkbox" id="pesanAutoContrast" checked /> Auto kontras</label>
        </div>
        <div class="field-row">
          <div class="control"><label>Posisi X (cm)</label><input id="pesanX" type="number" step="0.1" value="3" /></div>
          <div class="control"><label>Posisi Y (cm)</label><input id="pesanY" type="number" step="0.1" value="1" /></div>
        </div>
        <div class="control">
          <label>Posisi</label>
          <select id="pesanPos"><option value="horizontal">Horizontal</option><option value="vertical">Vertical</option></select>
        </div>
      </div>
    </div>

    <button class="btn-primary" id="btnProcess" disabled>Proses</button>
    <button class="btn-secondary" id="btnReset">Reset</button>
  </div>

  <div class="stage">
    <div class="empty-state" id="emptyState">
      &#9472;&#9472;&#9472; belum ada gambar &#9472;&#9472;&#9472;<br>
      klik panel kiri untuk memilih file JPG
    </div>

    <div id="resultArea" style="display:none; flex:1; flex-direction:column; gap:16px;">
      <div class="pane">
        <div class="pane-label">
          <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
            <span id="paneLabel">Preview</span>
            <span class="mode-badge" id="modeBadge" style="display:none;"></span>
          </div>
          <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
            <span id="sizeLabel"></span>
            <div class="zoom-bar">
              <button type="button" id="btnRotateLeft" title="Putar kiri 90&deg;">&#8634;</button>
              <button type="button" id="btnRotateRight" title="Putar kanan 90&deg;">&#8635;</button>
              <span class="zoom-val" id="rotVal" title="Rotasi">0&deg;</span>
              <button type="button" id="btnZoomOut" title="Zoom out">&minus;</button>
              <span class="zoom-val" id="zoomVal">100%</span>
              <button type="button" id="btnZoomIn" title="Zoom in">+</button>
              <button type="button" id="btnZoomReset" title="Reset zoom" style="width:auto;padding:0 8px;font-size:11px;">Fit</button>
            </div>
          </div>
        </div>
        <div class="viewport" id="viewport">
          <div class="ruler-corner">cm</div>
          <div class="ruler-x"><canvas id="rulerX"></canvas></div>
          <div class="ruler-y"><canvas id="rulerY"></canvas></div>
          <div class="composite-wrap" id="compositeWrap">
            <div class="composite" id="composite">
              <img id="imgMain" alt="sumber" style="display:none;">
              <canvas id="fxCanvas"></canvas>
            </div>
          </div>
        </div>
      </div>

      <div class="stats-bar" id="statsBar"></div>

      <div class="actions-row">
        <button class="btn-primary" id="btnOpenFolder" disabled>Buka Folder Hasil</button>
        <button class="btn-secondary" id="btnReprocess">Proses ulang dengan setting ini</button>
      </div>

      <details>
        <summary>Lihat respons server (JSON)</summary>
        <pre id="rawJson"></pre>
      </details>
    </div>
  </div>
</div>

<script>
(function(){
  "use strict";

  const state = {
    filepath: null,
    widthPx: 0, heightPx: 0,
    widthCm: 0, heightCm: 0,
    dpi: 300,
    colorMode: '',
    rotation: 0,
    finalWcm: 0, finalHcm: 0,
    zoom: 1,
    fitScale: 1,
    resultPath: null,
    resultUrl: null,
    busy: false
  };

  const dropZone = document.getElementById('dropZone');
  const dropZoneTitle = document.getElementById('dropZoneTitle');
  const dropZoneSub = document.getElementById('dropZoneSub');
  const errorMsg = document.getElementById('errorMsg');
  const btnProcess = document.getElementById('btnProcess');
  const btnReset = document.getElementById('btnReset');
  const btnReprocess = document.getElementById('btnReprocess');
  const btnOpenFolder = document.getElementById('btnOpenFolder');
  const emptyState = document.getElementById('emptyState');
  const resultArea = document.getElementById('resultArea');
  const imgMain = document.getElementById('imgMain');
  const composite = document.getElementById('composite');
  const compositeWrap = document.getElementById('compositeWrap');
  const sizeLabel = document.getElementById('sizeLabel');
  const paneLabel = document.getElementById('paneLabel');
  const statsBar = document.getElementById('statsBar');
  const rawJsonEl = document.getElementById('rawJson');
  const rulerX = document.getElementById('rulerX');
  const rulerY = document.getElementById('rulerY');
  const zoomVal = document.getElementById('zoomVal');
  const rotVal = document.getElementById('rotVal');
  const modeBadge = document.getElementById('modeBadge');
  const ctrlDpi = document.getElementById('ctrlDpi');
  const valDpi = document.getElementById('valDpi');

  const fxCanvas = document.getElementById('fxCanvas');
  let imgLoaded = false;
  imgMain.addEventListener('load', ()=>{ imgLoaded = true; renderLive(); });
  imgMain.addEventListener('error', ()=>{ imgLoaded = false; });

  ctrlDpi.addEventListener('input', ()=> valDpi.textContent = ctrlDpi.value);

  function setColorModeBadge(mode){
    state.colorMode = mode || '';
    const m = String(mode || '').toUpperCase();
    if(m === 'RGB'){ modeBadge.textContent = 'RGB'; modeBadge.className = 'mode-badge rgb'; }
    else if(m === 'CMYK'){ modeBadge.textContent = 'CMYK'; modeBadge.className = 'mode-badge cmyk'; }
    else { modeBadge.textContent = 'MODE: ' + (m || '?'); modeBadge.className = 'mode-badge warn'; }
    modeBadge.style.display = mode ? 'inline-block' : 'none';
  }

  function setRotation(deg){
    state.rotation = ((deg % 360) + 360) % 360;
    rotVal.textContent = state.rotation + '°';
    renderLive();
  }
  document.getElementById('btnRotateLeft').addEventListener('click', ()=> setRotation(state.rotation - 90));
  document.getElementById('btnRotateRight').addEventListener('click', ()=> setRotation(state.rotation + 90));

  function showError(msg){ errorMsg.textContent = msg; errorMsg.style.display = 'block'; }
  function clearError(){ errorMsg.style.display = 'none'; }

  function bindToggle(checkboxId, boxId, fieldsId){
    const cb = document.getElementById(checkboxId);
    const box = document.getElementById(boxId);
    const fields = document.getElementById(fieldsId);
    const stateEl = box.querySelector('.state');
    function sync(){
      box.classList.toggle('on', cb.checked);
      fields.classList.toggle('show', cb.checked);
      if(stateEl) stateEl.textContent = cb.checked ? 'AKTIF' : 'NONAKTIF';
    }
    cb.addEventListener('change', ()=>{ sync(); scheduleLive(); });
    box.addEventListener('click', (e)=>{
      if(e.target === cb) return;
      cb.checked = !cb.checked;
      cb.dispatchEvent(new Event('change'));
    });
    sync();
  }
  bindToggle('plongEnable', 'plongToggleBox', 'plongFields');
  bindToggle('lebihanEnable', 'lebihanToggleBox', 'lebihanFields');
  bindToggle('pesanEnable', 'pesanToggleBox', 'pesanFields');

  // Live preview: any control change re-renders instantly (no need to press Proses)
  document.querySelector('.panel').addEventListener('input', scheduleLive);
  document.querySelector('.panel').addEventListener('change', scheduleLive);

  document.getElementById('lebihanAll').addEventListener('input', (e)=>{
    document.getElementById('valLebihanAll').textContent = e.target.value;
  });
  document.getElementById('lebihanCustomSides').addEventListener('change', (e)=>{
    document.getElementById('lebihanSidesGrid').style.display = e.target.checked ? 'grid' : 'none';
  });

  const TEMPLATE_PRESETS = {
    'NON FINISHING': {},
    'POLOS': { lebihan: true, pesan: true, pesanText: 'POLOS' },
    'LP4': { plong: true, plongFold4: true, pesan: true, pesanText: 'LP4' },
    'LIPAT': { lebihan: true, pesan: true, pesanText: 'LIPAT' },
    'DOUBLE SIDE': { pesan: true, pesanText: 'DOUBLE SIDE' },
  };
  document.getElementById('finishingTemplate').addEventListener('change', (ev)=>{
    ['plongEnable','lebihanEnable','pesanEnable'].forEach((id)=>{
      const cb = document.getElementById(id);
      cb.checked = false;
      cb.dispatchEvent(new Event('change'));
    });
    document.getElementById('plongFold4').checked = false;
    document.getElementById('pesanText').value = '';

    const preset = TEMPLATE_PRESETS[ev.target.value] || {};
    if(preset.plong){ const cb=document.getElementById('plongEnable'); cb.checked=true; cb.dispatchEvent(new Event('change')); }
    if(preset.plongFold4) document.getElementById('plongFold4').checked = true;
    if(preset.lebihan){ const cb=document.getElementById('lebihanEnable'); cb.checked=true; cb.dispatchEvent(new Event('change')); }
    if(preset.pesan){ const cb=document.getElementById('pesanEnable'); cb.checked=true; cb.dispatchEvent(new Event('change')); }
    if(preset.pesanText) document.getElementById('pesanText').value = preset.pesanText;
  });

  document.getElementById('pesanPos').addEventListener('change', (ev)=>{
    if(ev.target.value === 'vertical'){
      document.getElementById('pesanX').value = 1;
      document.getElementById('pesanY').value = 3;
    } else {
      document.getElementById('pesanX').value = 3;
      document.getElementById('pesanY').value = 1;
    }
    scheduleLive();
  });

  document.getElementById('plongFold4').addEventListener('change', (ev)=>{
    if(ev.target.checked){
      ['jml_plong_atas','jml_plong_bawah','jml_plong_kiri','jml_plong_kanan'].forEach(id=>{
        document.getElementById(id).value = 2;
      });
    }
    scheduleLive();
  });

  function pickFile(){
    function onPicked(fp){
      clearError();
      state.filepath = fp;
      dropZoneTitle.textContent = 'Gambar dipilih';
      dropZoneSub.textContent = fp;
      loadFileInfo(fp);
    }
    if(typeof openFileDialog === 'function'){
      openFileDialog(onPicked);
      return;
    }
    const existing = document.querySelector('script[src="/ui/file-dialog-component"]');
    if(!existing){
      const s = document.createElement('script');
      s.src = '/ui/file-dialog-component';
      s.onload = ()=>{ if(typeof openFileDialog === 'function') openFileDialog(onPicked); };
      document.body.appendChild(s);
    } else {
      existing.addEventListener('load', ()=>{ if(typeof openFileDialog === 'function') openFileDialog(onPicked); });
    }
  }
  dropZone.addEventListener('click', pickFile);

  function loadFileInfo(fp){
    fetch('/api/file-info?filepath=' + encodeURIComponent(fp))
      .then(r => r.json())
      .then(info => {
        if(info.status === 'error' && !info.dimensions){
          showError('Gagal membaca info gambar: ' + (info.message || 'unknown'));
          return;
        }
        const dims = String(info.dimensions || '0x0').split('x');
        state.widthPx = parseInt(dims[0], 10) || 0;
        state.heightPx = parseInt(dims[1], 10) || 0;
        const dpiParts = String(info.dpi || '300x300').split('x');
        state.dpi = parseFloat(dpiParts[0]) || 300;
        ctrlDpi.value = Math.round(state.dpi);
        valDpi.textContent = ctrlDpi.value;
        state.widthCm = info.width_cm || 0;
        state.heightCm = info.height_cm || 0;
        state.resultPath = null;
        state.resultUrl = null;
        state.zoom = 1;
        setRotation(0);
        setColorModeBadge(info.color_mode);

        paneLabel.textContent = 'Preview (live)';
        imgLoaded = false;
        imgMain.src = '/ui/thumbnail?filepath=' + encodeURIComponent(fp) + '&t=' + Date.now();
        emptyState.style.display = 'none';
        resultArea.style.display = 'flex';
        btnProcess.disabled = false;
        btnOpenFolder.disabled = true;
        rawJsonEl.textContent = '';

        updateSizeLabel(info);
      })
      .catch(e => showError('Gagal membaca info gambar: ' + e.message));
  }

  function updateSizeLabel(info){
    sizeLabel.textContent = state.widthCm + '×' + state.heightCm + ' cm  ·  ' + state.widthPx + '×' + state.heightPx + 'px  ·  ' + Math.round(state.dpi) + ' DPI';
    const cm = String(info.color_mode || '').toUpperCase();
    const modeColor = cm === 'RGB' ? '#0066cc' : (cm === 'CMYK' ? '#1f7a47' : '#c62828');
    const modeText = cm || '-';
    statsBar.innerHTML =
      '<div class="stat"><span class="stat-label">Ukuran</span><b>' + state.widthCm + ' × ' + state.heightCm + ' cm</b></div>' +
      '<div class="stat"><span class="stat-label">Resolusi</span><b>' + state.widthPx + ' × ' + state.heightPx + ' px</b></div>' +
      '<div class="stat"><span class="stat-label">DPI</span><b>' + Math.round(state.dpi) + '</b></div>' +
      '<div class="stat"><span class="stat-label">Mode Warna</span><b style="color:' + modeColor + '">' + modeText + '</b></div>' +
      '<div class="stat"><span class="stat-label">File Size</span><b>' + (info.size_mb || '-') + ' MB</b></div>';
  }

  function setZoom(z){
    state.zoom = Math.max(0.2, Math.min(8, z));
    zoomVal.textContent = Math.round(state.zoom * 100) + '%';
    renderLive();
  }
  document.getElementById('btnZoomIn').addEventListener('click', ()=> setZoom(state.zoom * 1.25));
  document.getElementById('btnZoomOut').addEventListener('click', ()=> setZoom(state.zoom / 1.25));
  document.getElementById('btnZoomReset').addEventListener('click', ()=> setZoom(1));

  compositeWrap.addEventListener('wheel', (e)=>{
    if(!state.widthPx) return;
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.12 : 1/1.12;
    setZoom(state.zoom * factor);
  }, { passive:false });

  function isRotatedSideways(){ return state.rotation === 90 || state.rotation === 270; }

  function cnum(id, def){
    const el = document.getElementById(id);
    if(!el) return def;
    const v = parseFloat(String(el.value).replace(',', '.'));
    return isNaN(v) ? def : v;
  }
  function cint(id, def){ return Math.max(0, Math.round(cnum(id, def))); }

  function computeLayout(){
    const rotated = isRotatedSideways();
    const imgWcm = rotated ? state.heightCm : state.widthCm;
    const imgHcm = rotated ? state.widthCm : state.heightCm;
    const lebOn = document.getElementById('lebihanEnable').checked;
    let L = 0, R = 0, T = 0, B = 0;
    if(lebOn){
      const custom = document.getElementById('lebihanCustomSides').checked;
      const all = cnum('lebihanAll', 0);
      T = custom ? cnum('lebTop', all) : all;
      B = custom ? cnum('lebBottom', all) : all;
      L = custom ? cnum('lebLeft', all) : all;
      R = custom ? cnum('lebRight', all) : all;
    }
    return { imgWcm, imgHcm, L, R, T, B, finalWcm: imgWcm + L + R, finalHcm: imgHcm + T + B, lebOn };
  }

  function distribute(n, a, b){
    if(n <= 0) return [];
    if(n === 1) return [(a + b) / 2];
    const step = (b - a) / (n - 1);
    const out = [];
    for(let i = 0; i < n; i++) out.push(a + i * step);
    return out;
  }

  function sampleLuminance(ctx, x, y, r){
    r = Math.max(Math.round(r), 1);
    const sx = Math.max(0, Math.round(x - r)), sy = Math.max(0, Math.round(y - r));
    const sw = Math.min(r * 2, ctx.canvas.width - sx), sh = Math.min(r * 2, ctx.canvas.height - sy);
    if(sw <= 0 || sh <= 0) return 255;
    const d = ctx.getImageData(sx, sy, sw, sh).data;
    let sum = 0, n = 0;
    for(let i = 0; i < d.length; i += 16){ sum += 0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2]; n++; }
    return n ? sum / n : 255;
  }
  function contrastColor(ctx, x, y, r){ return sampleLuminance(ctx, x, y, r) > 128 ? '#000000' : '#ffffff'; }

  function drawPlong(ctx, ax, ay, aw, ah, c){
    const inset = cnum('plongInset', 2) * c;
    const bentuk = document.getElementById('bentukPlong').value;
    const autoContrast = document.getElementById('plongAutoContrast').checked;
    const baseColor = document.getElementById('plongColor').value;
    const dLebar = cnum('diameter_lebar', 1) * c;
    const dPanjang = cnum('diameter_panjang', 1) * c;
    const sampleR = Math.max(dLebar, dPanjang) / 2;
    let snapshot = null;
    if(autoContrast){ snapshot = ctx.getImageData(0, 0, ctx.canvas.width, ctx.canvas.height); }
    function sampleSnap(x, y, r){
      r = Math.max(Math.round(r), 1);
      const sx = Math.max(0, Math.round(x - r)), sy = Math.max(0, Math.round(y - r));
      const w = snapshot.width, d = snapshot.data;
      const ex = Math.min(sx + r*2, w), ey = Math.min(sy + r*2, snapshot.height);
      let sum = 0, n = 0;
      for(let py = sy; py < ey; py += 4){ for(let px = sx; px < ex; px += 4){ const i = (py * w + px) * 4; sum += 0.299*d[i] + 0.587*d[i+1] + 0.114*d[i+2]; n++; } }
      return n ? (sum/n > 128 ? '#000000' : '#ffffff') : '#000000';
    }
    function shape(x, y){
      ctx.fillStyle = autoContrast ? sampleSnap(x, y, sampleR) : baseColor;
      if(bentuk === 'square') ctx.fillRect(x - dLebar/2, y - dPanjang/2, dLebar, dPanjang);
      else { ctx.beginPath(); ctx.arc(x, y, Math.max(dLebar/2, 1), 0, Math.PI*2); ctx.fill(); }
    }
    distribute(cint('jml_plong_atas', 0), ax + inset, ax + aw - inset).forEach(x => shape(x, ay + inset));
    distribute(cint('jml_plong_bawah', 0), ax + inset, ax + aw - inset).forEach(x => shape(x, ay + ah - inset));
    distribute(cint('jml_plong_kiri', 0), ay + inset, ay + ah - inset).forEach(y => shape(ax + inset, y));
    distribute(cint('jml_plong_kanan', 0), ay + inset, ay + ah - inset).forEach(y => shape(ax + aw - inset, y));

  }

  function drawLebGaris(ctx, W, H, c){
    const color = document.getElementById('lebLineColor').value;
    const lw = Math.max(cnum('lebLineSize', 0.1) * c, 1);
    const dash = Math.max(0.5 * c, 3);
    ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.setLineDash([dash, dash]);
    ctx.strokeRect(lw/2, lw/2, W - lw, H - lw);
    ctx.setLineDash([]);
  }

  function drawPesan(ctx, W, H, c){
    const text = String(document.getElementById('pesanText').value || '').trim();
    if(!text) return;
    const fontPx = Math.max(cnum('pesanSize', 0.8) * c, 6);
    const baseColor = document.getElementById('pesanColor').value;
    const autoContrast = document.getElementById('pesanAutoContrast').checked;
    const posX = cnum('pesanX', 1) * c;
    const posY = cnum('pesanY', 3) * c;
    const vertical = document.getElementById('pesanPos').value === 'vertical';
    const satuKiri = document.getElementById('pesanSatuKiri').checked;
    ctx.font = fontPx + 'px Arial, sans-serif';
    ctx.textBaseline = 'top';
    const tw = ctx.measureText(text).width;
    function stamp(x, y){
      ctx.fillStyle = autoContrast ? contrastColor(ctx, x, y, fontPx) : baseColor;
      if(vertical){
        ctx.save(); ctx.translate(x, y); ctx.rotate(-Math.PI/2); ctx.fillText(text, 0, 0); ctx.restore();
      } else {
        ctx.fillText(text, x, y);
      }
    }
    stamp(posX, vertical ? posY + tw : posY);
    if(!satuKiri){
      if(vertical) stamp(W - fontPx - posX, H - posY);
      else stamp(W - tw - posX, H - fontPx - posY);
    }
  }

  function renderLive(){
    const ctx = fxCanvas.getContext('2d');
    if(!state.widthPx || !state.heightPx || !imgLoaded){
      fxCanvas.width = 1; fxCanvas.height = 1;
      composite.style.width = '1px'; composite.style.height = '1px';
      return;
    }
    const lay = computeLayout();
    state.finalWcm = lay.finalWcm;
    state.finalHcm = lay.finalHcm;

    const wrapW = Math.max(100, compositeWrap.clientWidth - 32);
    const wrapH = Math.max(100, Math.min(window.innerHeight * 0.58, compositeWrap.clientHeight || 500));
    const nativeCmToPx = state.widthCm ? (state.widthPx / state.widthCm) : 120;
    const fitCmToPx = Math.min(wrapW / lay.finalWcm, wrapH / lay.finalHcm);
    let cmToPx = Math.min(fitCmToPx, nativeCmToPx) * state.zoom;
    // cap canvas size for performance
    let W = Math.round(lay.finalWcm * cmToPx), H = Math.round(lay.finalHcm * cmToPx);
    const CAP = 3000;
    if(W > CAP || H > CAP){ const k = CAP / Math.max(W, H); cmToPx *= k; W = Math.round(lay.finalWcm * cmToPx); H = Math.round(lay.finalHcm * cmToPx); }
    W = Math.max(1, W); H = Math.max(1, H);

    fxCanvas.width = W; fxCanvas.height = H;
    composite.style.width = W + 'px'; composite.style.height = H + 'px';

    ctx.clearRect(0, 0, W, H);
    const c = cmToPx;
    const ax = lay.L * c, ay = lay.T * c, aw = lay.imgWcm * c, ah = lay.imgHcm * c;

    if(lay.lebOn){ ctx.fillStyle = document.getElementById('lebBackground').value; ctx.fillRect(0, 0, W, H); }

    // draw source image (own orientation, scaled) rotated into image area
    const dispW0 = state.widthCm * c, dispH0 = state.heightCm * c;
    ctx.save();
    ctx.translate(ax + aw/2, ay + ah/2);
    ctx.rotate(state.rotation * Math.PI / 180);
    ctx.drawImage(imgMain, -dispW0/2, -dispH0/2, dispW0, dispH0);
    ctx.restore();

    if(document.getElementById('plongEnable').checked) drawPlong(ctx, ax, ay, aw, ah, c);
    if(lay.lebOn){
      drawLebGaris(ctx, W, H, c);
      const bingkaiMode = document.getElementById('lebBingkaiObjek').value;
      let drawBingkai = bingkaiMode === 'on';
      if(bingkaiMode === 'auto'){
        const bgHex = document.getElementById('lebBackground').value;
        const br = parseInt(bgHex.slice(1,3),16), bg = parseInt(bgHex.slice(3,5),16), bb = parseInt(bgHex.slice(5,7),16);
        const edge = ctx.getImageData(Math.round(ax+1), Math.round(ay+1), Math.max(Math.round(aw-2),1), 1).data;
        let er=0, eg=0, eb=0, n=0;
        for(let i=0; i<edge.length; i+=16){ er+=edge[i]; eg+=edge[i+1]; eb+=edge[i+2]; n++; }
        if(n){ er/=n; eg/=n; eb/=n; }
        const diff = Math.abs(er-br)+Math.abs(eg-bg)+Math.abs(eb-bb);
        drawBingkai = diff < 80;
      }
      if(drawBingkai){
        const bColor = document.getElementById('lebLineColor').value;
        const bLw = Math.max(cnum('lebLineSize', 0.1) * c, 1);
        ctx.strokeStyle = bColor; ctx.lineWidth = bLw; ctx.setLineDash([]);
        ctx.strokeRect(ax + bLw/2, ay + bLw/2, aw - bLw, ah - bLw);
      }
    }
    if(document.getElementById('pesanEnable').checked) drawPesan(ctx, W, H, c);

    sizeLabel.textContent = lay.finalWcm.toFixed(1) + '×' + lay.finalHcm.toFixed(1) + ' cm  ·  ' + Math.round(state.dpi) + ' DPI';
    drawRulers();
  }

  let liveTimer = null;
  function scheduleLive(){ clearTimeout(liveTimer); liveTimer = setTimeout(renderLive, 40); }

  let savedTimer = null;
  function showSaved(path){
    paneLabel.textContent = 'Preview (live) — ✓ tersimpan';
    clearTimeout(savedTimer);
    savedTimer = setTimeout(()=>{ paneLabel.textContent = 'Preview (live)'; }, 2500);
  }

  function drawRulers(){
    const xHost = rulerX.parentElement;
    const yHost = rulerY.parentElement;
    const xW = xHost.clientWidth, xH = xHost.clientHeight;
    const yW = yHost.clientWidth, yH = yHost.clientHeight;
    const dpr = window.devicePixelRatio || 1;

    rulerX.width = Math.max(1, Math.floor(xW * dpr));
    rulerX.height = Math.max(1, Math.floor(xH * dpr));
    rulerY.width = Math.max(1, Math.floor(yW * dpr));
    rulerY.height = Math.max(1, Math.floor(yH * dpr));

    const ctxX = rulerX.getContext('2d');
    const ctxY = rulerY.getContext('2d');
    ctxX.setTransform(dpr,0,0,dpr,0,0);
    ctxY.setTransform(dpr,0,0,dpr,0,0);
    ctxX.clearRect(0,0,xW,xH);
    ctxY.clearRect(0,0,yW,yH);

    const compRect = composite.getBoundingClientRect();
    const wrapRect = compositeWrap.getBoundingClientRect();
    const offsetLeft = compRect.left - wrapRect.left + compositeWrap.scrollLeft;
    const offsetTop = compRect.top - wrapRect.top + compositeWrap.scrollTop;
    const dispW = compRect.width, dispH = compRect.height;
    if(!dispW || !dispH || !state.widthCm) return;

    const effWcm = state.finalWcm || (isRotatedSideways() ? state.heightCm : state.widthCm);
    const effHcm = state.finalHcm || (isRotatedSideways() ? state.widthCm : state.heightCm);
    const cmToX = dispW / effWcm;
    const cmToY = dispH / effHcm;

    function niceStep(cmToPx, minPx){
      const rawStep = minPx / Math.max(cmToPx, 0.0001);
      const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
      const residual = rawStep / magnitude;
      let niceResidual;
      if(residual > 5) niceResidual = 10;
      else if(residual > 2) niceResidual = 5;
      else if(residual > 1) niceResidual = 2;
      else niceResidual = 1;
      return niceResidual * magnitude;
    }
    function fmtCm(v, step){ return step >= 1 ? String(Math.round(v)) : v.toFixed(1); }

    ctxX.fillStyle = '#667080';
    ctxX.strokeStyle = 'rgba(0,102,204,0.45)';
    ctxX.font = '10px ui-monospace, monospace';
    ctxX.textAlign = 'center';
    ctxX.textBaseline = 'top';
    const maxX = effWcm;
    const stepX = niceStep(cmToX, 40);
    for(let cm=0; cm<=maxX + stepX*0.5; cm+=stepX){
      const x = offsetLeft + cm * cmToX;
      if(x < -20 || x > xW + 20) continue;
      ctxX.beginPath(); ctxX.moveTo(x, xH); ctxX.lineTo(x, xH-12); ctxX.stroke();
      ctxX.fillText(fmtCm(cm, stepX), x, 4);
    }

    ctxY.fillStyle = '#667080';
    ctxY.strokeStyle = 'rgba(0,102,204,0.45)';
    ctxY.font = '10px ui-monospace, monospace';
    ctxY.textAlign = 'right';
    ctxY.textBaseline = 'middle';
    const maxY = effHcm;
    const stepY = niceStep(cmToY, 28);
    for(let cm=0; cm<=maxY + stepY*0.5; cm+=stepY){
      const y = offsetTop + cm * cmToY;
      if(y < -20 || y > yH + 20) continue;
      ctxY.beginPath(); ctxY.moveTo(yW, y); ctxY.lineTo(yW-12, y); ctxY.stroke();
      ctxY.save(); ctxY.translate(yW-14, y); ctxY.rotate(-Math.PI/2); ctxY.textAlign='center'; ctxY.fillText(fmtCm(cm, stepY), 0, 0); ctxY.restore();
    }
  }
  compositeWrap.addEventListener('scroll', drawRulers);
  window.addEventListener('resize', ()=>{ if(state.widthPx) renderLive(); });

  function collectPayload(){
    const customSides = document.getElementById('lebihanCustomSides').checked;
    return {
      filepath: state.filepath,
      dpi: ctrlDpi.value,
      rotation: state.rotation,
      plong: {
        enable: document.getElementById('plongEnable').checked,
        fold4: document.getElementById('plongFold4').checked,
        jml_atas: document.getElementById('jml_plong_atas').value,
        jml_bawah: document.getElementById('jml_plong_bawah').value,
        jml_kiri: document.getElementById('jml_plong_kiri').value,
        jml_kanan: document.getElementById('jml_plong_kanan').value,
        inset: document.getElementById('plongInset').value,
        warna_plong: document.getElementById('plongColor').value,
        auto_contrast: document.getElementById('plongAutoContrast').checked,
        bentuk_plong: document.getElementById('bentukPlong').value,
        diameter_lebar: document.getElementById('diameter_lebar').value,
        diameter_panjang: document.getElementById('diameter_panjang').value,
      },
      lebihan: {
        enable: document.getElementById('lebihanEnable').checked,
        all: document.getElementById('lebihanAll').value,
        top: customSides ? document.getElementById('lebTop').value : document.getElementById('lebihanAll').value,
        bottom: customSides ? document.getElementById('lebBottom').value : document.getElementById('lebihanAll').value,
        left: customSides ? document.getElementById('lebLeft').value : document.getElementById('lebihanAll').value,
        right: customSides ? document.getElementById('lebRight').value : document.getElementById('lebihanAll').value,
        warna_background: document.getElementById('lebBackground').value,
        warna_garis: document.getElementById('lebLineColor').value,
        ukuran_garis: document.getElementById('lebLineSize').value,
        bingkai_objek: document.getElementById('lebBingkaiObjek').value,
        quality: document.getElementById('lebQuality').value,
      },
      pesan: {
        enable: document.getElementById('pesanEnable').checked,
        satu_kiri: document.getElementById('pesanSatuKiri').checked,
        text: document.getElementById('pesanText').value,
        ukuran: document.getElementById('pesanSize').value,
        warna: document.getElementById('pesanColor').value,
        auto_contrast: document.getElementById('pesanAutoContrast').checked,
        pos_x: document.getElementById('pesanX').value,
        pos_y: document.getElementById('pesanY').value,
        posisi: document.getElementById('pesanPos').value,
      },
    };
  }

  async function runPipeline(){
    if(!state.filepath){ showError('Pilih gambar terlebih dahulu.'); return; }
    if(state.busy) return;
    state.busy = true;
    clearError();
    btnProcess.disabled = true;
    btnProcess.innerHTML = '<span class="spinner"></span>Memproses...';

    try{
      const res = await fetch('/ui/finishing-process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(collectPayload()),
      });
      const data = await res.json();
      rawJsonEl.textContent = JSON.stringify(data, null, 2);
      if(!res.ok || data.status !== 'success'){
        throw new Error(data.message || ('Server error ' + res.status));
      }
      state.resultPath = data.output_path;
      state.resultUrl = data.output_url;
      btnOpenFolder.disabled = false;
      // live canvas already shows the composited result; just note it's saved
      showSaved(data.output_path);
    } catch(err){
      showError('Gagal memproses: ' + err.message);
    } finally {
      state.busy = false;
      btnProcess.disabled = !state.filepath;
      btnProcess.textContent = 'Proses';
    }
  }

  btnProcess.addEventListener('click', runPipeline);
  btnReprocess.addEventListener('click', runPipeline);

  btnOpenFolder.addEventListener('click', async ()=>{
    if(!state.resultPath) return;
    try{
      await fetch('/api/open-path', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath: state.resultPath }),
      });
    } catch(e){ console.warn(e); }
  });

  btnReset.addEventListener('click', ()=>{
    state.filepath = null;
    state.widthPx = 0; state.heightPx = 0;
    state.widthCm = 0; state.heightCm = 0;
    state.resultPath = null; state.resultUrl = null;
    state.zoom = 1;
    imgLoaded = false;
    setRotation(0);
    modeBadge.style.display = 'none';
    clearError();
    dropZoneTitle.textContent = 'Klik untuk pilih gambar';
    dropZoneSub.textContent = '.JPG / .JPEG · proses di agent :9001';
    document.getElementById('finishingTemplate').value = 'NON FINISHING';
    ['plongEnable','lebihanEnable','pesanEnable'].forEach((id)=>{
      const cb = document.getElementById(id);
      cb.checked = false;
      cb.dispatchEvent(new Event('change'));
    });
    document.getElementById('plongFold4').checked = false;
    document.getElementById('pesanSatuKiri').checked = false;
    document.getElementById('pesanText').value = '';
    document.getElementById('lebihanCustomSides').checked = false;
    document.getElementById('lebihanSidesGrid').style.display = 'none';
    btnProcess.disabled = true;
    btnOpenFolder.disabled = true;
    resultArea.style.display = 'none';
    emptyState.style.display = 'flex';
    rawJsonEl.textContent = '';
  });

})();
</script>

<!-- Include Universal File Dialog Component -->
<script src="/ui/file-dialog-component"></script>
</body>
</html>
    """
    )


@app.route("/execute", methods=["POST"])
def run_task():
    data = request.json

    if data.get("secret") != AGENT_SECRET:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    task_name = data.get("task")
    payload = data.get("payload", {})

    result = execute(task_name, payload)
    return jsonify(result)


# ─── Spot Color ────────────────────────────────────────────────────────────────

@app.route("/ui/spot-color")
def ui_spot_color():
    return render_template_string(r"""
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Spot Color Tool - Printing Agent</title>
    <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:'Segoe UI',system-ui,sans-serif;background:#e8e8e8;height:100vh;display:flex;flex-direction:column;overflow:hidden}

        /* ── Topbar ─────────────────────────────────────────────────────────── */
        .topbar{background:#fff;height:36px;padding:0 10px;display:flex;align-items:center;gap:8px;border-bottom:1px solid #d0d0d0;flex-shrink:0}
        .topbar-logo{font-size:12px;font-weight:800;color:#222;letter-spacing:.5px;margin-right:4px}
        .topbar-logo span{color:#0066cc}
        .topbar a button,.topbar button.tb-action{background:#f0f0f0;color:#444;border:1px solid #ccc;padding:3px 9px;border-radius:3px;cursor:pointer;font-size:11px}
        .topbar a button:hover,.topbar button.tb-action:hover{background:#e0e0e0}
        .topbar-sep{width:1px;height:18px;background:#d8d8d8}
        #imgNameLabel{font-size:10px;color:#666;max-width:140px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .upload-btn-top{background:#0066cc;color:#fff;border:none;padding:3px 10px;border-radius:3px;cursor:pointer;font-size:11px;font-weight:600;display:flex;align-items:center;gap:4px}
        .upload-btn-top:hover{background:#0055aa}
        .main{display:flex;flex:1;overflow:hidden}

        /* ── Narrow Toolbox (Photoshop-style) ──────────────────────────────── */
        .toolbox{width:36px;background:#f0f0f0;border-right:1px solid #c8c8c8;display:flex;flex-direction:column;align-items:center;padding:4px 2px;gap:1px;overflow:hidden;flex-shrink:0;z-index:10}
        .tbSep{width:24px;height:1px;background:#c0c0c0;margin:3px 0;flex-shrink:0}
        .tbBtn{width:30px;height:30px;border:1px solid transparent;border-radius:3px;background:transparent;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#444;transition:all .1s;position:relative;flex-shrink:0}
        .tbBtn svg{width:16px;height:16px;pointer-events:none}
        .tbBtn:hover{background:#ddd;border-color:#bbb;color:#111}
        .tbBtn.active{background:#0066cc;border-color:#0050aa;color:#fff}
        /* Tooltip */
        .tbBtn::after{content:attr(data-tip);position:absolute;left:36px;top:50%;transform:translateY(-50%);background:#222;color:#fff;font-size:10px;padding:3px 8px;border-radius:3px;white-space:nowrap;pointer-events:none;opacity:0;transition:opacity .12s;z-index:9999;border:1px solid #444}
        .tbBtn:hover::after{opacity:1}

        /* ── Context / Properties Bar ───────────────────────────────────────── */
        .ctx-bar{background:#f5f5f5;border-bottom:1px solid #d8d8d8;height:30px;padding:0 10px;display:flex;align-items:center;gap:8px;flex-shrink:0;overflow:hidden}
        .ctx-bar label{font-size:10px;color:#555;white-space:nowrap}
        .ctx-bar input[type=range]{width:80px;accent-color:#0066cc;cursor:pointer}
        .ctx-val{font-size:10px;color:#333;min-width:28px;font-variant-numeric:tabular-nums}
        .ctx-sep{width:1px;height:18px;background:#d0d0d0}
        .ctx-btn{background:#e8e8e8;color:#333;border:1px solid #c8c8c8;padding:2px 7px;border-radius:3px;cursor:pointer;font-size:10px;font-weight:600;display:flex;align-items:center;gap:3px;white-space:nowrap}
        .ctx-btn:hover{background:#d8d8d8}
        .ctx-btn:disabled{opacity:.4;cursor:not-allowed}
        .ctx-btn.active{background:#0066cc;color:#fff;border-color:#0050aa}
        .ctx-btn.ico{padding:3px 6px;justify-content:center;min-width:26px}
        .ctx-sm{background:#e8e8e8;color:#555;border:1px solid #c8c8c8;padding:2px 6px;border-radius:3px;cursor:pointer;font-size:10px;font-weight:700}
        .ctx-sm:hover{background:#d0d0d0;color:#111}
        .ctx-sm.active{background:#0066cc;color:#fff;border-color:#0050aa}
        /* Context sections – show/hide based on active tool */
        .ctx-paint,.ctx-sel{display:flex;align-items:center;gap:6px}
        .ctx-paint{display:none}
        .ctx-sel{display:none}
        /* Kontrol umum di topbar (berlaku semua tool) */
        .gen-bar{display:flex;align-items:center;gap:5px;flex-shrink:0}
        .ctx-bar:empty,.ctx-bar.empty{display:none}

        /* ── Canvas Area ────────────────────────────────────────────────────── */
        .canvas-area{flex:1;display:flex;flex-direction:column;overflow:hidden;background:#888}
        /* Ruler grid: corner | H ruler | V ruler | canvas */
        .ruler-wrap{flex:1;display:grid;grid-template-areas:"corner rh" "rv cw";grid-template-columns:20px 1fr;grid-template-rows:20px 1fr;overflow:hidden}
        .ruler-corner{grid-area:corner;background:#4a4a4a;border-right:1px solid #333;border-bottom:1px solid #333}
        #rulerH{grid-area:rh;background:#4a4a4a;border-bottom:1px solid #333;display:block;height:20px;width:100%}
        #rulerV{grid-area:rv;background:#4a4a4a;border-right:1px solid #333;display:block;width:20px;height:100%}
        /* padding 0 → gambar rata kiri-atas (harus sama dgn CANVAS_PAD di JS) */
        .canvas-wrap{grid-area:cw;overflow:auto;padding:0;display:flex;align-items:flex-start;justify-content:flex-start}
        #gridCanvas{grid-area:cw;pointer-events:none;z-index:5;align-self:stretch;justify-self:stretch}
        #canvasContainer{position:relative;display:inline-block;box-shadow:0 4px 20px rgba(0,0,0,.45)}
        #bgCanvas{display:block}
        #drawCanvas{position:absolute;top:0;left:0;cursor:crosshair}
        #selCanvas{position:absolute;top:0;left:0;pointer-events:none}

        /* ── RIGHT PANEL ────────────────────────────────────────────────────── */
        .right-panel{width:200px;min-width:185px;background:#fff;border-left:1px solid #d0d0d0;display:flex;flex-direction:column;padding:9px;gap:7px;overflow-y:auto;flex-shrink:0}
        .rp-label{font-size:9px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:.6px;margin-top:3px}
        input[type=text]{width:100%;padding:5px 7px;border:1px solid #ccc;border-radius:3px;font-size:12px;color:#222}
        input[type=text]:focus{outline:none;border-color:#0066cc}
        input[type=number]{width:100%;padding:5px 7px;border:1px solid #ccc;border-radius:3px;font-size:12px;color:#222}
        input[type=number]:focus{outline:none;border-color:#0066cc}

        .spot-mode-group{display:grid;grid-template-columns:1fr 1fr;gap:4px}
        .mode-btn{padding:6px 5px;border:1px solid #d8d8d8;border-radius:4px;background:#f8f8f8;cursor:pointer;font-size:10px;text-align:left;transition:all .1s;color:#333}
        .mode-btn:hover{border-color:#0066cc;background:#f0f5ff}
        .mode-btn.active{border-color:#0066cc;background:#0066cc;color:#fff}
        .mode-desc{font-size:8px;opacity:.7;margin-top:1px}

        .add-ch-btn{width:100%;padding:7px;background:#e67e22;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:11px;font-weight:700}
        .add-ch-btn:hover{background:#d35400}
        .add-ch-btn:disabled{background:#e8e8e8;color:#aaa;cursor:not-allowed}
        .ch-item{background:#f8f8f8;border:1px solid #e0e0e0;border-radius:5px;padding:6px 8px;display:flex;align-items:center;gap:6px;cursor:pointer;transition:all .12s}
        .ch-item:hover{border-color:#9cc4ee;background:#f2f7fd}
        .ch-item.active{border-color:#0066cc;background:#eaf3ff;box-shadow:0 0 0 1px #0066cc inset}
        .ch-clear-btn{font-size:9px;font-weight:700;color:#c62828;background:#fff;border:1px solid #f0c4c4;padding:3px 8px;border-radius:8px;cursor:pointer;flex-shrink:0;letter-spacing:.3px}
        .ch-clear-btn:hover{background:#c62828;color:#fff;border-color:#a02020}
        .ch-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
        .ch-info{flex:1;min-width:0}
        .ch-name{font-weight:700;font-size:10px;color:#222;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .ch-mode{font-size:9px;color:#888}
        .ch-del{background:#fee8e8;color:#c33;border:1px solid #fcc;border-radius:3px;padding:1px 5px;cursor:pointer;font-size:12px;flex-shrink:0;line-height:1}
        .ch-del:hover{background:#fcc}
        .gen-btn{width:100%;padding:8px;background:#27ae60;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:12px;font-weight:700}
        .gen-btn:hover{background:#219150}
        .gen-btn:disabled{background:#e0e0e0;color:#aaa;cursor:not-allowed}
        .status-box{background:#f8f8f8;border:1px solid #e8e8e8;border-radius:4px;padding:7px;font-size:10px;color:#666;min-height:38px;word-break:break-all}
        .status-box.ok{background:#f0fff4;border-color:#b2dfdb;color:#2e7d32}
        .status-box.err{background:#fff5f5;border-color:#ffcdd2;color:#c62828}
        .dl-btn{width:100%;padding:7px;background:#1565c0;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:11px;font-weight:600;display:none}
        .dl-btn:hover{background:#1976d2}

        /* ── Polygon hint ───────────────────────────────────────────────────── */
        #polyHint{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.75);color:#fff;padding:5px 14px;border-radius:14px;font-size:11px;display:none;pointer-events:none;z-index:999}

        /* ── Ruler popup & Action ───────────────────────────────────────────── */
        #rulerPopup{position:absolute;top:22px;left:22px;z-index:500;background:#fff;border:1px solid #c8c8c8;border-radius:7px;box-shadow:0 6px 24px rgba(0,0,0,.18);padding:10px 12px;display:none;min-width:170px}
        #rulerPopup .rp-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:4px 0;font-size:11.5px;color:#444}
        #rulerPopup select{padding:3px 6px;border:1px solid #ccc;border-radius:4px;font-size:11px}
        #rulerPopup input[type=color]{width:40px;height:24px;padding:1px;border:1px solid #ccc;border-radius:4px;cursor:pointer}
        .ruler-wrap{position:relative}
        .ctx-btn.grid-on{background:#0066cc;color:#fff;border-color:#0050aa}
        .act-rec{flex:1;padding:7px;background:#fff;color:#c62828;border:1.5px solid #e2b4b4;border-radius:4px;cursor:pointer;font-size:11px;font-weight:700}
        .act-rec:hover{background:#fff5f5}
        .act-rec.recording{background:#c62828;color:#fff;border-color:#a02020;animation:recblink 1.2s ease-in-out infinite}
        @keyframes recblink{50%{opacity:.75}}
        .act-clr{padding:7px 11px;background:#f0f0f0;color:#888;border:1px solid #ddd;border-radius:4px;cursor:pointer;font-size:11px}
        .act-clr:hover{background:#e4e4e4;color:#c62828}
        .auto-btn{flex:1;padding:8px 4px;background:#00897b;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:11px;font-weight:700}
        .auto-btn:hover{background:#00695c}
        .act-batch{width:100%;padding:7px;background:#5e35b1;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:11px;font-weight:700}
        .act-batch:hover{background:#4d2c93}
        .act-batch:disabled{background:#e8e8e8;color:#aaa;cursor:not-allowed}

        /* ── Batch Files dialog ─────────────────────────────────────────────── */
        .batch-btn-top{background:#00897b;color:#fff;border:none;padding:3px 10px;border-radius:3px;cursor:pointer;font-size:11px;font-weight:600;display:flex;align-items:center;gap:4px}
        .batch-btn-top:hover{background:#00695c}
        #batchModal{position:fixed;inset:0;background:rgba(15,20,30,.45);display:none;align-items:center;justify-content:center;z-index:3000}
        #batchModal.open{display:flex}
        .bm-box{background:#fff;border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,.3);width:min(860px,94vw);max-height:90vh;display:flex;flex-direction:column;overflow:hidden}
        .bm-head{padding:13px 16px;border-bottom:1px solid #e6e6e6;display:flex;align-items:baseline;gap:9px}
        .bm-head b{font-size:14px;color:#1a1a1a}
        .bm-sub{font-size:10.5px;color:#999}
        .bm-x{margin-left:auto;background:none;border:none;font-size:15px;color:#aaa;cursor:pointer;line-height:1}
        .bm-x:hover{color:#c62828}
        .bm-pick{display:flex;align-items:center;gap:8px;padding:11px 16px;background:#fafbfc;border-bottom:1px solid #eee}
        .bm-pick label{font-size:11px;color:#555;white-space:nowrap}
        .bm-pick input[type=text]{flex:1;padding:6px 9px;border:1px solid #ccc;border-radius:4px;font-size:12px;font-family:Consolas,monospace}
        .bm-scan{background:#0066cc;color:#fff;border:none;padding:6px 13px;border-radius:4px;font-size:11px;font-weight:700;cursor:pointer;white-space:nowrap}
        .bm-scan:hover{background:#0055aa}
        .bm-chk{display:flex;align-items:center;gap:4px;font-size:11px;color:#555;cursor:pointer;white-space:nowrap}
        .bm-chk input{margin:0}
        .bm-listhead{display:flex;align-items:center;gap:12px;padding:7px 16px;border-bottom:1px solid #eee;background:#fff}
        .bm-count{margin-left:auto;font-size:10.5px;color:#888}
        .bm-addwrap{position:relative;flex-shrink:0}
        .bm-add{background:#0066cc;color:#fff;border:none;width:28px;height:27px;border-radius:4px;font-size:16px;font-weight:700;cursor:pointer;line-height:1;display:flex;align-items:center;justify-content:center}
        .bm-add:hover{background:#0055aa}
        .bm-addmenu{position:absolute;top:31px;left:0;z-index:60;background:#fff;border:1px solid #ccd5de;border-radius:6px;box-shadow:0 8px 26px rgba(0,0,0,.18);padding:4px;display:none;min-width:190px}
        .bm-addmenu.open{display:block}
        .bm-addmenu button{display:flex;flex-direction:column;align-items:flex-start;width:100%;background:none;border:none;padding:7px 10px;border-radius:4px;cursor:pointer;font-size:12px;color:#333;text-align:left;line-height:1.35}
        .bm-addmenu button small{font-size:9.5px;color:#999;font-weight:400}
        .bm-addmenu button:hover{background:#eaf3ff;color:#0066cc}
        .bm-clr{background:#fff;color:#c62828;border:1px solid #f0c4c4;padding:7px 18px;border-radius:5px;font-size:12px;font-weight:700;cursor:pointer;margin-right:auto}
        .bm-clr:hover{background:#c62828;color:#fff;border-color:#a02020}
        .bm-list{flex:1;overflow-y:auto;min-height:190px;max-height:44vh;background:#fff}
        .bm-empty{padding:40px 16px;text-align:center;color:#bbb;font-size:12px}
        .bm-row{display:flex;align-items:center;gap:9px;padding:6px 16px;border-bottom:1px solid #f4f4f4;font-size:11.5px}
        .bm-row:hover{background:#f8fbff}
        .bm-row.done{background:#f4fdf6}
        .bm-row.err{background:#fff6f6}
        .bm-row input[type=checkbox]{margin:0;flex-shrink:0}
        .bm-nm{font-weight:600;color:#222;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:0 0 190px}
        .bm-dir{color:#999;font-size:10px;font-family:Consolas,monospace;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;direction:rtl;text-align:left}
        .bm-sz{color:#777;font-size:10px;width:62px;text-align:right;flex-shrink:0;font-variant-numeric:tabular-nums}
        .bm-pbar{width:78px;height:6px;background:#e9edf2;border-radius:3px;overflow:hidden;flex-shrink:0}
        .bm-pbar>i{display:block;height:100%;width:0;background:linear-gradient(90deg,#0066cc,#3d9bff);transition:width .18s}
        .bm-row.done .bm-pbar>i{background:#27ae60}
        .bm-row.err  .bm-pbar>i{background:#c62828}
        .bm-st{width:118px;flex-shrink:0;font-size:10px;color:#888;text-align:right;font-variant-numeric:tabular-nums}
        .bm-row.done .bm-st{color:#27ae60;font-weight:700}
        .bm-row.err  .bm-st{color:#c62828;font-weight:700}
        .bm-spin{display:inline-block;width:9px;height:9px;border:1.5px solid #cfe0f5;border-top-color:#0066cc;border-radius:50%;animation:selspin .7s linear infinite;vertical-align:-1px;margin-right:4px}
        .bm-opts{display:flex;align-items:center;gap:18px;padding:11px 16px;border-top:1px solid #eee;background:#fafbfc;flex-wrap:wrap}
        .bm-seg{display:flex;border:1px solid #ccd5de;border-radius:5px;overflow:hidden}
        .bm-seg-b{background:#fff;border:none;padding:6px 16px;cursor:pointer;font-size:12px;font-weight:700;color:#555;display:flex;flex-direction:column;align-items:center;line-height:1.25}
        .bm-seg-b small{font-size:8.5px;font-weight:400;opacity:.75}
        .bm-seg-b+.bm-seg-b{border-left:1px solid #ccd5de}
        .bm-seg-b.active{background:#00897b;color:#fff}
        .bm-num{display:flex;align-items:center;gap:5px;font-size:11px;color:#555}
        .bm-num input{width:52px;padding:5px 6px;border:1px solid #ccc;border-radius:4px;font-size:11.5px}
        .bm-total{display:flex;align-items:center;gap:10px;padding:8px 16px;border-top:1px solid #eee}
        .bm-tbar{flex:1;height:7px;background:#e9edf2;border-radius:4px;overflow:hidden}
        .bm-tbar>i{display:block;height:100%;width:0;background:linear-gradient(90deg,#00897b,#26c6b0);transition:width .25s}
        #bmTotalTxt{font-size:10.5px;color:#666;min-width:250px;text-align:right;font-variant-numeric:tabular-nums}
        .bm-foot{display:flex;justify-content:flex-end;gap:8px;padding:11px 16px;border-top:1px solid #e6e6e6;background:#fafbfc}
        .bm-cancel{background:#fff;color:#555;border:1px solid #ccc;padding:7px 18px;border-radius:5px;font-size:12px;cursor:pointer}
        .bm-cancel:hover{background:#f0f0f0}
        .bm-go{background:#00897b;color:#fff;border:none;padding:7px 22px;border-radius:5px;font-size:12px;font-weight:700;cursor:pointer}
        .bm-go:hover{background:#00695c}
        .bm-go:disabled{background:#dfe4e8;color:#aaa;cursor:not-allowed}

        /* ── Progress overlay seleksi ───────────────────────────────────────── */
        #selProgress{position:fixed;inset:0;background:rgba(20,25,35,.35);display:none;align-items:center;justify-content:center;z-index:2000;backdrop-filter:blur(1px)}
        #selProgress .box{background:#fff;border-radius:10px;padding:20px 26px;box-shadow:0 10px 40px rgba(0,0,0,.25);display:flex;flex-direction:column;align-items:center;gap:12px;min-width:220px}
        #selProgress .spin{width:32px;height:32px;border:3px solid #e0e6ef;border-top-color:#0066cc;border-radius:50%;animation:selspin .8s linear infinite}
        @keyframes selspin{to{transform:rotate(360deg)}}
        #selProgress .lbl{font-size:12.5px;color:#333;font-weight:600}
        #selProgress .bar{width:100%;height:5px;background:#e8edf3;border-radius:3px;overflow:hidden;display:none}
        #selProgress .bar>i{display:block;height:100%;width:0;background:#0066cc;transition:width .1s}
    </style>
</head>
<body>
<!-- Hidden file input -->
<input type="file" id="imgInput" accept="image/png,image/jpeg,image/jpg" style="display:none">

<!-- TOPBAR -->
<div class="topbar">
    <span class="topbar-logo">PRINTING<span> AGENT</span></span>
    <span style="font-size:11px;color:#888;font-weight:600">· Spot Color</span>
    <div class="topbar-sep"></div>
    <button class="upload-btn-top" onclick="document.getElementById('imgInput').click()">
        <svg viewBox="0 0 20 20" fill="currentColor" width="12" height="12"><path d="M10 2.5a.5.5 0 0 1 .5.5v6.793l1.646-1.647a.5.5 0 0 1 .708.708l-2.5 2.5a.5.5 0 0 1-.708 0l-2.5-2.5a.5.5 0 1 1 .708-.708L9.5 9.793V3a.5.5 0 0 1 .5-.5zm-5 10a.5.5 0 0 0 0 1h10a.5.5 0 0 0 0-1H5z"/></svg>
        Upload
    </button>
    <button class="batch-btn-top" onclick="openBatchDialog()" title="Proses banyak file PNG langsung di server">
        <svg viewBox="0 0 20 20" fill="currentColor" width="12" height="12"><path d="M3 4a1 1 0 0 1 1-1h4l1.5 1.5H16a1 1 0 0 1 1 1V7H3V4zm0 4h14v7a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8z"/></svg>
        Batch Files
    </button>
    <span id="imgNameLabel" style="font-size:10px;color:#666;max-width:130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">—</span>
    <div class="topbar-sep"></div>
    <a href="/ui"><button class="tb-action">← Kembali</button></a>

    <span style="flex:1"></span>

    <!-- Kontrol umum (berlaku untuk semua tool) — tidak diulang di tiap context bar -->
    <div class="gen-bar">
        <button class="ctx-btn ico" id="undoBtn" onclick="undo()" disabled title="Undo (Ctrl+Z)">
            <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><path fill-rule="evenodd" d="M6.293 1.293a1 1 0 0 1 1.414 1.414L4.414 6H12a4 4 0 0 1 0 8h-2a.5.5 0 0 1 0-1h2a3 3 0 0 0 0-6H4.414l3.293 3.293a1 1 0 0 1-1.414 1.414l-5-5a1 1 0 0 1 0-1.414l5-5z"/></svg>
        </button>
        <button class="ctx-btn ico" id="redoBtn" onclick="redo()" disabled title="Redo (Ctrl+Y)">
            <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><path fill-rule="evenodd" d="M9.707 1.293a1 1 0 0 0-1.414 1.414L11.586 6H4a4 4 0 0 0 0 8h2a.5.5 0 0 0 0-1H4a3 3 0 0 1 0-6h7.586l-3.293 3.293a1 1 0 0 0 1.414 1.414l5-5a1 1 0 0 0 0-1.414l-5-5z"/></svg>
        </button>
        <div class="ctx-sep"></div>
        <button class="ctx-btn ico" onclick="zoom(1.25)" title="Zoom In (+)">
            <svg viewBox="0 0 14 14" fill="currentColor" width="12" height="12"><path d="M5.5 0a5.5 5.5 0 1 0 3.645 9.652l2.85 2.851.707-.707-2.852-2.851A5.5 5.5 0 0 0 5.5 0zm-4.5 5.5a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0zM5 3.5a.5.5 0 0 1 1 0V5h1.5a.5.5 0 0 1 0 1H6v1.5a.5.5 0 0 1-1 0V6H3.5a.5.5 0 0 1 0-1H5V3.5z"/></svg>
        </button>
        <button class="ctx-btn ico" onclick="zoom(0.8)" title="Zoom Out (−)">
            <svg viewBox="0 0 14 14" fill="currentColor" width="12" height="12"><path d="M5.5 0a5.5 5.5 0 1 0 3.645 9.652l2.85 2.851.707-.707-2.852-2.851A5.5 5.5 0 0 0 5.5 0zm-4.5 5.5a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0zM3.5 5h4a.5.5 0 0 1 0 1h-4a.5.5 0 0 1 0-1z"/></svg>
        </button>
        <button class="ctx-btn ico" onclick="fitCanvas()" title="Fit to window">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><path d="M6 2H2v4M10 2h4v4M6 14H2v-4M10 14h4v-4"/><rect x="5" y="5" width="6" height="6" rx="1"/></svg>
        </button>
        <button class="ctx-btn ico" onclick="zoom(1,'reset')" title="Zoom 100% (1:1)">
            <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><text x="8" y="12" font-size="10" font-weight="700" text-anchor="middle" font-family="Segoe UI,sans-serif">1:1</text></svg>
        </button>
        <button class="ctx-btn ico" id="gridBtn" onclick="toggleGrid()" title="Tampilkan / sembunyikan grid">
            <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><path d="M0 0h16v16H0V0zm1 1v4h4V1H1zm5 0v4h4V1H6zm5 0v4h4V1h-4zM1 6v4h4V6H1zm5 0v4h4V6H6zm5 0v4h4V6h-4zM1 11v4h4v-4H1zm5 0v4h4v-4H6zm5 0v4h4v-4h-4z"/></svg>
        </button>
        <span class="ctx-val" id="zoomLabel" style="min-width:34px">100%</span>
        <div class="ctx-sep"></div>
        <label style="font-size:10px;color:#666">DPI</label>
        <input type="number" id="dpiInput" value="300" min="72" max="1200" style="width:50px;padding:2px 4px;border:1px solid #ccc;border-radius:3px;font-size:10px">
        <div class="ctx-sep"></div>
        <button class="ctx-btn ico" onclick="clearMask()" style="color:#c33" title="Hapus area spot pada channel ini">
            <svg viewBox="0 0 14 14" fill="currentColor" width="12" height="12"><path d="M5.5 2a.5.5 0 0 0-1 0V3H3a.5.5 0 0 0 0 1h8a.5.5 0 0 0 0-1H9V2a.5.5 0 0 0-1 0V3h-2V2zM3.087 5l.59 5.9A1 1 0 0 0 4.67 12h4.66a1 1 0 0 0 .994-.9L10.913 5H3.087z"/></svg>
        </button>
        <div class="ctx-sep"></div>
        <span id="coordLabel" style="font-size:10px;color:#888;font-variant-numeric:tabular-nums;min-width:64px;text-align:right"></span>
    </div>
</div>

<div class="main">
<!-- NARROW TOOLBOX -->
<div class="toolbox">
    <!-- Selection tools -->
    <button class="tbBtn" data-tool="magicwand" data-tip="Magic Wand (W)" onclick="setTool('magicwand')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="m4 4 16 16"/><path d="m9 9 6 6"/><path d="m15 4-1 1"/><path d="m4 15 1-1"/><path d="m16 4 1 1"/><path d="m5 15-1 1"/><path d="M10.5 2.5 9 4"/><path d="M2.5 10.5 4 9"/><circle cx="16.5" cy="16.5" r="2.5"/></svg>
    </button>
    <button class="tbBtn" data-tool="colorselect" data-tip="Select by Color (S)" onclick="setTool('colorselect')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m2 13.5 5.5 5.5 5-5-5.5-5.5L2 13.5Z"/><path d="m9 9 3-3"/><path d="m12 6 1.5-1.5a2.12 2.12 0 0 1 3 3L15 9"/><path d="m15 9 5 5"/><path d="M21 20a1 1 0 1 1-2 0c0-.9 1-2.5 1-2.5S21 19 21 20Z"/></svg>
    </button>
    <div class="tbSep"></div>
    <!-- Paint tools -->
    <button class="tbBtn active" data-tool="brush" data-tip="Brush (B)" onclick="setTool('brush')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
    </button>
    <button class="tbBtn" data-tool="eraser" data-tip="Eraser (E)" onclick="setTool('eraser')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20H7L3 16l10-10 7 7-2.5 2.5"/><path d="M6 10l8 8"/></svg>
    </button>
    <button class="tbBtn" data-tool="fill" data-tip="Fill (F)" onclick="setTool('fill')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m19 11-8-8-8.5 8.5a5.5 5.5 0 0 0 0 7.778 5.5 5.5 0 0 0 7.778 0L19 11Z"/><path d="m5 2 5 5"/><path d="M2 13h15"/><path d="M22 20a2 2 0 1 1-4 0c0-1.6 2-4 2-4s2 2.4 2 4Z"/></svg>
    </button>
    <div class="tbSep"></div>
    <!-- Shape tools -->
    <button class="tbBtn" data-tool="rect" data-tip="Rectangle (R)" onclick="setTool('rect')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="5" width="18" height="14" rx="2"/></svg>
    </button>
    <button class="tbBtn" data-tool="ellipse" data-tip="Ellipse" onclick="setTool('ellipse')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><ellipse cx="12" cy="12" rx="10" ry="7"/></svg>
    </button>
    <button class="tbBtn" data-tool="polygon" data-tip="Polygon (P)" onclick="setTool('polygon')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><polygon points="12,3 21,8.5 18,19 6,19 3,8.5"/></svg>
    </button>
</div>

<!-- CANVAS AREA -->
<div class="canvas-area">
    <!-- Context bar -->
    <div class="ctx-bar" id="ctxBar">
        <!-- Paint controls -->
        <div class="ctx-paint" id="ctxPaint">
            <label>Size</label>
            <input type="range" id="brushSize" min="2" max="200" value="20" oninput="document.getElementById('brushVal').textContent=this.value">
            <span class="ctx-val" id="brushVal">20</span>px
            <div class="ctx-sep"></div>
            <label>Opacity</label>
            <input type="range" id="overlayOpacity" min="10" max="220" value="120" oninput="updateOverlayOpacity(this.value)">
            <span class="ctx-val" id="opacityVal">120</span>
        </div>
        <!-- Selection controls -->
        <div class="ctx-sel" id="ctxSel">
            <label>Tolerance</label>
            <input type="range" id="tolerance" min="1" max="120" value="32" oninput="document.getElementById('tolVal').textContent=this.value">
            <span class="ctx-val" id="tolVal">32</span>
            <div class="ctx-sep"></div>
            <button class="ctx-sm active" data-selmode="new"      onclick="setSelMode('new')">New</button>
            <button class="ctx-sm"        data-selmode="add"      onclick="setSelMode('add')">+Add</button>
            <button class="ctx-sm"        data-selmode="subtract" onclick="setSelMode('subtract')">−Sub</button>
            <div class="ctx-sep"></div>
            <button class="ctx-btn" onclick="selectObject()" title="Seleksi semua object non-transparan (seperti Ctrl+klik thumbnail layer di Photoshop)">
                <svg viewBox="0 0 16 16" fill="currentColor" width="11" height="11"><circle cx="8" cy="8" r="4"/><path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zm0 1a7 7 0 1 1 0 14A7 7 0 0 1 8 1z" opacity=".45"/></svg>
                Object
            </button>
            <button class="ctx-btn" onclick="selectInverse()" title="Select Inverse (Ctrl+Shift+I)">
                <svg viewBox="0 0 16 16" fill="currentColor" width="11" height="11"><path d="M0 0h16v16H0V0zm1 1v14h14V1H1z"/><path d="M4 4h8v8H4V4z"/></svg>
                Inverse
            </button>
            <div class="ctx-sep"></div>
            <input type="number" id="modifyPx" value="2" min="1" max="200" style="width:38px;padding:2px 4px;border:1px solid #ccc;border-radius:3px;font-size:10px" title="Pixels">px
            <button class="ctx-btn" onclick="contractSelection()" title="Contract selection inward by N pixels (Select › Modify › Contract)">Contract</button>
            <button class="ctx-btn" onclick="expandSelection()" title="Expand selection outward by N pixels (Select › Modify › Expand)">Expand</button>
            <label style="display:flex;align-items:center;gap:3px;font-size:10px;color:#555;cursor:pointer;white-space:nowrap" title="Isi lubang di dalam objek jadi siluet solid (mis. untuk white underbase)">
                <input type="checkbox" id="solidFill" style="margin:0">Solid
            </label>
            <label style="display:flex;align-items:center;gap:3px;font-size:10px;color:#555;cursor:pointer;white-space:nowrap" title="Kecualikan area putih dari expand/contract">
                <input type="checkbox" id="excludeWhite" style="margin:0" checked>Kecualikan putih
            </label>
            <div class="ctx-sep"></div>
            <button class="ctx-btn" id="applySelBtn" onclick="applySelection()" disabled title="Apply (Enter)">✓ Apply</button>
            <button class="ctx-btn" onclick="deselect()" title="Deselect (Ctrl+D)">✕ Desel</button>
        </div>
    </div>

    <!-- Ruler + Canvas scroll area -->
    <div class="ruler-wrap">
        <div class="ruler-corner" id="rulerCorner" onclick="toggleRulerPopup(event)" title="Klik: pengaturan satuan &amp; background" style="cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:8px;color:#bbb" >⚙</div>
        <canvas id="rulerH"></canvas>
        <canvas id="rulerV"></canvas>
        <div class="canvas-wrap" id="canvasWrap">
            <div id="canvasContainer">
                <canvas id="bgCanvas"></canvas>
                <canvas id="drawCanvas"></canvas>
                <canvas id="selCanvas" style="position:absolute;top:0;left:0;pointer-events:none"></canvas>
            </div>
        </div>
        <!-- Grid overlay: menutupi seluruh lembar kerja (tembus keluar area gambar) -->
        <canvas id="gridCanvas"></canvas>
        <!-- Popup pengaturan ruler -->
        <div id="rulerPopup">
            <div class="rp-row"><span>Satuan</span>
                <select id="unitSel" onchange="setRulerUnit(this.value)">
                    <option value="px">px</option>
                    <option value="mm">mm</option>
                    <option value="cm" selected>cm</option>
                    <option value="m">m</option>
                </select>
            </div>
            <div class="rp-row"><span>Background</span>
                <input type="color" id="bgColorPick" value="#888888" oninput="setCanvasBg(this.value)">
            </div>
            <div class="rp-row"><span>Grid</span>
                <input type="checkbox" id="gridChk" onchange="toggleGrid(this.checked)">
            </div>
        </div>
    </div>
</div>

    <!-- RIGHT PANEL -->
    <div class="right-panel">
        <div class="rp-label">Jenis Produk</div>
        <div class="spot-mode-group">
            <button class="mode-btn active" data-type="dtf" onclick="setProductType('dtf')">
                DTF
                <div class="mode-desc">White saja</div>
            </button>
            <button class="mode-btn" data-type="uv" onclick="setProductType('uv')">
                UV
                <div class="mode-desc">White + Varnish</div>
            </button>
        </div>

        <div class="rp-label">Channel <span style="font-weight:400;color:#aaa;text-transform:none;letter-spacing:0">— klik untuk edit</span></div>
        <div id="channelList" style="display:flex;flex-direction:column;gap:5px;min-height:30px">
            <div style="color:#bbb;font-size:11px;text-align:center;padding:6px">Upload gambar dulu</div>
        </div>

        <button class="gen-btn" id="genBtn" onclick="generatePDF()" disabled>
            &#11015; Generate &amp; Download PDF
        </button>

        <div class="rp-label">Auto Proses <span style="font-weight:400;color:#aaa;text-transform:none;letter-spacing:0">— file di server, hasil di folder sama</span></div>
        <div style="display:flex;gap:4px">
            <button class="auto-btn" onclick="runAutoServer('dtf')" title="Object → Contract → Apply → simpan A.pdf di folder file aslinya (channel White)">⚡ Auto DTF</button>
            <button class="auto-btn" onclick="runAutoServer('uv')" title="Object → Contract → Apply untuk White + Varnish → simpan A.pdf di folder file aslinya">⚡ Auto UV</button>
        </div>

        <div class="rp-label">Action <span style="font-weight:400;color:#aaa;text-transform:none;letter-spacing:0">— rekam &amp; terapkan ulang</span></div>
        <div style="display:flex;gap:4px">
            <button class="act-rec" id="recBtn" onclick="toggleRecord()">● Rekam</button>
            <button class="act-clr" id="recClrBtn" onclick="clearRecording()" title="Hapus rekaman">✕</button>
        </div>
        <div id="recSteps" style="font-size:10px;color:#888;max-height:110px;overflow-y:auto;display:none;background:#f8f8f8;border:1px solid #eee;border-radius:4px;padding:5px 7px;line-height:1.7"></div>
        <input type="file" id="batchInput" accept="image/png,image/jpeg" multiple style="display:none">
        <button class="act-batch" id="batchBtn" onclick="document.getElementById('batchInput').click()" disabled title="Pilih beberapa PNG/JPG — action diterapkan ke tiap file di background (tanpa ditampilkan), semua PDF diunduh sekaligus dalam 1 ZIP">
            &#9654; Terapkan ke Banyak File (ZIP)
        </button>

        <div class="status-box" id="statusBox">Upload gambar, pilih channel, lalu gambar / seleksi areanya.</div>
    </div>
</div>

<div id="polyHint">Klik untuk tambah titik • Double-klik / Enter untuk selesai • Kanan untuk hapus titik</div>

<div id="selProgress">
    <div class="box">
        <div class="spin"></div>
        <div class="lbl" id="selProgLbl">Memproses seleksi…</div>
        <div class="bar" id="selProgBar"><i></i></div>
    </div>
</div>

<!-- ══ DIALOG BATCH FILES ══ -->
<div id="batchModal">
  <div class="bm-box">
    <div class="bm-head">
        <b>Batch Files</b>
        <span class="bm-sub">proses PNG langsung di server — hasil .pdf ditulis di folder yang sama</span>
        <button class="bm-x" onclick="closeBatchDialog()">✕</button>
    </div>

    <div class="bm-pick">
        <label>Folder / File</label>
        <input type="text" id="bmPath" placeholder="mis. D:\Desain\stiker  atau  D:\Desain\a.png"
               onkeydown="if(event.key==='Enter')bmScan()">
        <div class="bm-addwrap">
            <button class="bm-add" onclick="bmToggleAddMenu(event)" title="Tambah file atau folder lewat dialog Windows">+</button>
            <div class="bm-addmenu" id="bmAddMenu">
                <button onclick="bmAddPick('files')">📄 Pilih File…<small>bisa banyak file sekaligus</small></button>
                <button onclick="bmAddPick('folder')">📁 Pilih Folder…<small>semua PNG di folder itu</small></button>
            </div>
        </div>
        <label class="bm-chk" title="Termasuk isi sub-folder"><input type="checkbox" id="bmRecursive">sub-folder</label>
        <button class="bm-scan" onclick="bmScan()">Cari PNG</button>
    </div>

    <div class="bm-listhead">
        <label class="bm-chk"><input type="checkbox" id="bmAll" onchange="bmToggleAll(this.checked)">Pilih semua</label>
        <span id="bmCount" class="bm-count">belum ada file</span>
    </div>
    <div class="bm-list" id="bmList">
        <div class="bm-empty">Masukkan path folder lalu klik <b>Cari PNG</b>, atau tekan <b>+</b> untuk memilih file</div>
    </div>

    <div class="bm-opts">
        <div class="bm-seg">
            <button class="bm-seg-b active" data-preset="dtf" onclick="bmSetPreset('dtf')">DTF<small>White</small></button>
            <button class="bm-seg-b"        data-preset="uv"  onclick="bmSetPreset('uv')">UV<small>White + Varnish</small></button>
        </div>
        <div class="bm-num">
            <label>Contract</label>
            <input type="number" id="bmContract" value="2" min="0" max="200"><span>px</span>
        </div>
        <div class="bm-num">
            <label>DPI</label>
            <input type="number" id="bmDpi" value="300" min="72" max="1200">
        </div>
    </div>

    <div class="bm-total">
        <div class="bm-tbar"><i id="bmTotalBar"></i></div>
        <span id="bmTotalTxt">Siap</span>
    </div>

    <div class="bm-foot">
        <button class="bm-clr" onclick="bmClearList()" title="Bersihkan daftar &amp; mulai pekerjaan baru">Clear</button>
        <button class="bm-cancel" onclick="closeBatchDialog()" id="bmCancelBtn">Cancel</button>
        <button class="bm-go" onclick="bmProcess()" id="bmGoBtn" disabled>▶ Proses</button>
    </div>
  </div>
</div>

<script>
// ─── State ─────────────────────────────────────────────────────────────────
const bgCanvas  = document.getElementById('bgCanvas');
const drawCanvas = document.getElementById('drawCanvas');
const bgCtx     = bgCanvas.getContext('2d');
const drawCtx   = drawCanvas.getContext('2d');

let currentTool  = 'brush';
let currentMode  = 'white';
let productType  = 'dtf';   // 'dtf' (White) | 'uv' (White + Varnish)
let activeChannel = 0;      // index channel yang sedang diedit
let channels     = [];      // [{name, mode, img: ImageData|null}]
let selMode      = 'new';   // 'new' | 'add' | 'subtract'
let zoomLevel    = 1;
let imageFile    = null;
let imageObj     = null;
let isDrawing    = false;
let startX = 0, startY = 0;
let lastX  = 0, lastY  = 0;
let overlayAlpha = 120;
let polyPoints   = [];
let previewCanvas = null;

// Undo / Redo
const undoStack = [];
const redoStack = [];
const MAX_HISTORY = 25;

// Marching ants
const selCanvas = document.getElementById('selCanvas');
const selCtx    = selCanvas.getContext('2d');
let antLoops    = [];      // array of flat [x0,y0,x1,y1,...] loops (koord gambar)
let antDashOffset = 0;     // offset dash (animasi jalan)
let antRAF      = null;
let antFrameTick = 0;      // pembagi frame

// Active selection (separate from drawn mask)
let selectionMask = null;  // Uint8Array w*h, populated by magic wand / color select

// Warna overlay per mode (untuk tampilan editor saja)
const modeColors = {
    white:   [255, 0,   200],  // magenta terang — kontras di atas desain apa pun
    varnish: [0,   200, 255],  // cyan — pelapis kilap
};

// ─── Baca DPI dari metadata file (pHYs PNG / JFIF JPEG) ─────────────────────
async function readFileDpi(file){
    try{
        const buf = new Uint8Array(await file.slice(0, 65536).arrayBuffer());
        // PNG: cari chunk pHYs
        if(buf[0]===0x89 && buf[1]===0x50){
            let o = 8;
            while(o + 8 < buf.length){
                const len  = (buf[o]<<24)|(buf[o+1]<<16)|(buf[o+2]<<8)|buf[o+3];
                const type = String.fromCharCode(buf[o+4],buf[o+5],buf[o+6],buf[o+7]);
                if(type === 'pHYs' && len >= 9){
                    const p = o+8;
                    const ppux = (buf[p]<<24)|(buf[p+1]<<16)|(buf[p+2]<<8)|buf[p+3];
                    if(buf[p+8] === 1 && ppux > 0)          // unit = meter
                        return Math.round(ppux * 0.0254);
                    return null;
                }
                if(type === 'IDAT') break;                   // pHYs selalu sebelum IDAT
                o += 12 + len;
            }
        }
        // JPEG: JFIF APP0 density
        if(buf[0]===0xFF && buf[1]===0xD8 && buf[6]===0x4A && buf[7]===0x46){
            const unit = buf[13];
            const xd = (buf[14]<<8)|buf[15];
            if(unit===1 && xd>1) return xd;                  // dpi
            if(unit===2 && xd>1) return Math.round(xd*2.54); // dpcm
        }
    }catch(_){}
    return null;
}

// ─── Upload Gambar ──────────────────────────────────────────────────────────
function loadImageFile(file){
    return new Promise((resolve, reject)=>{
        imageFile = file;
        document.getElementById('imgNameLabel').textContent = file.name;
        const url = URL.createObjectURL(file);
        const img = new Image();
        img.onload = function(){
            imageObj = img;
            bgCanvas.width  = img.width;
            bgCanvas.height = img.height;
            drawCanvas.width  = img.width;
            drawCanvas.height = img.height;
            bgCtx.drawImage(img, 0, 0);
            selCanvas.width  = img.width;
            selCanvas.height = img.height;
            // Reset total seperti baru refresh — jangan bawa sisa dari gambar sebelumnya
            deselect();
            clearMaskData();
            _whiteMaskCache = null;   // reset cache mask putih
            channels = [];            // jangan wariskan mask channel gambar lama
            activeChannel = 0;
            undoStack.length = 0; redoStack.length = 0; _updateUndoRedo();
            _initChannels();          // bangun channel kosong sesuai jenis produk
            fitCanvas();
            // gambar rata kiri-atas: pastikan lembar kerja tidak ter-scroll
            const wrap = document.getElementById('canvasWrap');
            wrap.scrollLeft = 0; wrap.scrollTop = 0;
            drawRulers(); drawGrid();
            URL.revokeObjectURL(url);
            resolve();
        };
        img.onerror = ()=>{ URL.revokeObjectURL(url); reject(new Error('Gagal memuat ' + file.name)); };
        img.src = url;
    });
}

document.getElementById('imgInput').addEventListener('change', async function(e){
    const file = e.target.files[0];
    if(!file) return;
    await loadImageFile(file);
    // set DPI dari metadata file (perilaku Photoshop) — ruler & ukuran fisik jadi benar
    const fdpi = await readFileDpi(file);
    if(fdpi){
        document.getElementById('dpiInput').value = fdpi;
        drawRulers(); drawGrid();
    }
    document.getElementById('statusBox').textContent =
        'Gambar dimuat' + (fdpi ? ` (${fdpi} DPI dari file)` : '') + '. Pilih channel lalu gambar / seleksi areanya.';
    document.getElementById('statusBox').className = 'status-box';
});

// ─── Tool Selection ─────────────────────────────────────────────────────────
const SEL_TOOLS = new Set(['magicwand','colorselect']);
const PAINT_TOOLS = new Set(['brush','eraser','fill','rect','ellipse','polygon']);

function setTool(t){
    currentTool = t;
    document.querySelectorAll('.tbBtn[data-tool]').forEach(b=>b.classList.remove('active'));
    const btn = document.querySelector(`.tbBtn[data-tool="${t}"]`);
    if(btn) btn.classList.add('active');
    if(t !== 'polygon') cancelPolygon();
    // show/hide context bar sections
    document.getElementById('ctxPaint').style.display = PAINT_TOOLS.has(t) ? 'flex' : 'none';
    document.getElementById('ctxSel').style.display   = SEL_TOOLS.has(t)   ? 'flex' : 'none';
    updateCursor();
}

// ─── Select Inverse ─────────────────────────────────────────────────────────
function selectInverse(){
    if(!imageObj) return;
    _recAct({t:'inverse'});
    const w = bgCanvas.width, h = bgCanvas.height;
    if(!selectionMask){
        selectionMask = new Uint8Array(w*h).fill(1);
    } else {
        for(let i=0; i<selectionMask.length; i++) selectionMask[i] = selectionMask[i] ? 0 : 1;
    }
    document.getElementById('applySelBtn').disabled = false;
    recomputeAnts();
}

// ─── Select Object ───────────────────────────────────────────────────────────
// Seperti Ctrl+klik thumbnail layer di Photoshop: seleksi SEMUA piksel
// non-transparan (object), apapun warnanya. Ambang 50% alpha (konsisten ants).
function _selectObjectImpl(){
    const w = bgCanvas.width, h = bgCanvas.height;
    const src = bgCtx.getImageData(0,0,w,h).data;
    const m = new Uint8Array(w*h);
    for(let i=0;i<w*h;i++) if(src[i*4+3] >= 128) m[i] = 1;
    _mergeSelMask(m, selMode, w*h);
}
function selectObject(){
    if(!imageObj) return;
    _recAct({t:'object', mode:selMode, ..._selOpts()});
    _runSelection('Menyeleksi object…', _selectObjectImpl);
}

// ─── Contract / Expand Selection ─────────────────────────────────────────────
function _getModifyPx(){ return Math.max(1, parseInt(document.getElementById('modifyPx').value)||2); }

// ─── Progress overlay untuk operasi seleksi berat ───────────────────────────
let _selBusy = false;
function _showSelProgress(label){
    document.getElementById('selProgLbl').textContent = label || 'Memproses seleksi…';
    document.getElementById('selProgBar').style.display = 'none';
    document.getElementById('selProgress').style.display = 'flex';
}
function _hideSelProgress(){ document.getElementById('selProgress').style.display = 'none'; }

// Jalankan operasi berat setelah overlay sempat tampil (2× rAF), lalu sembunyikan.
function _runSelection(label, fn){
    if(_selBusy) return;
    // Gambar besar butuh feedback; kecil langsung saja tanpa overlay berkedip.
    const big = imageObj && (bgCanvas.width * bgCanvas.height > 1500*1500);
    if(!big){ fn(); return; }
    _selBusy = true;
    _showSelProgress(label);
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
        try { fn(); }
        finally { _hideSelProgress(); _selBusy = false; }
    }));
}

function contractSelection(){
    if(!selectionMask || !imageObj) return;
    _recAct({t:'contract', px:_getModifyPx(), exw:_isExcludeWhite()});
    _runSelection('Mengecilkan seleksi…', ()=>_contractSelectionImpl());
}
function _contractSelectionImpl(){
    const n = _getModifyPx();
    const w = bgCanvas.width, h = bgCanvas.height;
    // Separable min-filter (erosion): horizontal then vertical
    const tmp = new Uint8Array(w*h);
    for(let y=0; y<h; y++){
        for(let x=0; x<w; x++){
            let v=1;
            for(let dx=-n; dx<=n; dx++){
                const nx=x+dx;
                if(nx<0||nx>=w||!selectionMask[y*w+nx]){v=0;break;}
            }
            tmp[y*w+x]=v;
        }
    }
    const result = new Uint8Array(w*h);
    for(let x=0; x<w; x++){
        for(let y=0; y<h; y++){
            let v=1;
            for(let dy=-n; dy<=n; dy++){
                const ny=y+dy;
                if(ny<0||ny>=h||!tmp[ny*w+x]){v=0;break;}
            }
            result[y*w+x]=v;
        }
    }
    // Area putih tidak boleh ikut menyusut/berubah bila dikecualikan
    if(_isExcludeWhite()){
        const wm = _getWhiteMask();
        for(let i=0;i<result.length;i++) if(wm[i]) result[i] = selectionMask[i];
    }
    selectionMask=result;
    document.getElementById('applySelBtn').disabled=false;
    recomputeAnts();
}

function expandSelection(){
    if(!selectionMask || !imageObj) return;
    _recAct({t:'expand', px:_getModifyPx(), exw:_isExcludeWhite()});
    _runSelection('Memperbesar seleksi…', ()=>_expandSelectionImpl());
}
function _expandSelectionImpl(){
    const n = _getModifyPx();
    const w = bgCanvas.width, h = bgCanvas.height;
    const exw = _isExcludeWhite();
    const wm  = exw ? _getWhiteMask() : null;

    // Sumber dilasi: seleksi TANPA piksel putih (bila dikecualikan) —
    // putih tidak boleh jadi sumber ekspansi ke sekitarnya.
    let src = selectionMask;
    if(exw){
        src = new Uint8Array(w*h);
        for(let i=0;i<w*h;i++) src[i] = (selectionMask[i] && !wm[i]) ? 1 : 0;
    }

    // Separable max-filter (dilation): horizontal then vertical
    const tmp = new Uint8Array(w*h);
    for(let y=0; y<h; y++){
        for(let x=0; x<w; x++){
            let v=0;
            for(let dx=-n; dx<=n; dx++){
                const nx=x+dx;
                if(nx>=0&&nx<w&&src[y*w+nx]){v=1;break;}
            }
            tmp[y*w+x]=v;
        }
    }
    const result = new Uint8Array(w*h);
    for(let x=0; x<w; x++){
        for(let y=0; y<h; y++){
            let v=0;
            for(let dy=-n; dy<=n; dy++){
                const ny=y+dy;
                if(ny>=0&&ny<h&&tmp[ny*w+x]){v=1;break;}
            }
            result[y*w+x]=v;
        }
    }
    if(exw){
        // Putih beku total: status seleksinya persis seperti sebelum expand
        for(let i=0;i<w*h;i++) if(wm[i]) result[i] = selectionMask[i];
    }
    selectionMask=result;
    document.getElementById('applySelBtn').disabled=false;
    recomputeAnts();
}

// ─── Jenis Produk & Channel ─────────────────────────────────────────────────
const TYPE_CHANNELS = {
    dtf: [['White','white']],
    uv:  [['White','white'], ['Varnish','varnish']],
};

function _initChannels(){
    // bangun ulang channels sesuai productType, pertahankan mask lama by-name
    const prev = {};
    channels.forEach(c=>{ prev[c.name] = c.img; });
    channels = TYPE_CHANNELS[productType].map(([name,mode])=>(
        {name, mode, img: prev[name] || null}
    ));
    activeChannel = 0;
    currentMode = channels[0].mode;
    if(imageObj) _loadActiveChannel();
    _renderChannelList();
    if(imageObj) recomputeAnts();
}

function setProductType(type){
    if(type === productType) return;
    _recAct({t:'ptype', type});
    if(imageObj) _saveActiveChannel();
    productType = type;
    document.querySelectorAll('.mode-btn[data-type]').forEach(b=>
        b.classList.toggle('active', b.dataset.type === type));
    _initChannels();
    document.getElementById('statusBox').textContent =
        type === 'uv' ? 'Mode UV: isi channel White dan Varnish.' : 'Mode DTF: isi channel White.';
    document.getElementById('statusBox').className = 'status-box';
}

function selectChannel(i){
    if(!imageObj || i === activeChannel || !channels[i]) return;
    _recAct({t:'chan', i});
    _saveActiveChannel();
    activeChannel = i;
    currentMode = channels[i].mode;
    _loadActiveChannel();
    _renderChannelList();
    recomputeAnts();   // tampilkan seleksi channel ini
}

function _saveActiveChannel(){
    if(!imageObj || !channels[activeChannel]) return;
    if(selectionMask) applySelection();   // commit seleksi yang tertunda
    channels[activeChannel].img = drawCtx.getImageData(0,0,drawCanvas.width,drawCanvas.height);
}

function _loadActiveChannel(){
    selectionMask = null;
    const ab = document.getElementById('applySelBtn');
    if(ab) ab.disabled = true;
    drawCtx.clearRect(0,0,drawCanvas.width,drawCanvas.height);
    const im = channels[activeChannel] && channels[activeChannel].img;
    if(im) drawCtx.putImageData(im, 0, 0);
}

function setSelMode(sm){
    selMode = sm;
    document.querySelectorAll('.ctx-sm[data-selmode]').forEach(b=>b.classList.remove('active'));
    const btn = document.querySelector(`.ctx-sm[data-selmode="${sm}"]`);
    if(btn) btn.classList.add('active');
}

function updateCursor(){
    const cur = currentTool;
    drawCanvas.style.cursor =
        cur === 'eraser'      ? 'cell'       :
        cur === 'fill'        ? 'copy'       :
        cur === 'magicwand'   ? 'copy'       :
        cur === 'colorselect' ? 'copy'       :
        'crosshair';
}

// ─── Overlay color helper ───────────────────────────────────────────────────
function getColor(alpha){
    const [r,g,b] = modeColors[currentMode] || [255,0,0];
    return `rgba(${r},${g},${b},${alpha/255})`;
}

function updateOverlayOpacity(v){
    overlayAlpha = parseInt(v);
    document.getElementById('opacityVal').textContent = v;
}

// ─── Zoom ───────────────────────────────────────────────────────────────────
function zoom(factor, mode){
    if(!imageObj) return;
    if(mode === 'reset') zoomLevel = 1;
    else zoomLevel = Math.min(Math.max(zoomLevel * factor, 0.05), 16);
    applyZoom();
}

function fitCanvas(){
    if(!imageObj) return;
    const wrap = document.getElementById('canvasWrap');
    const ww = wrap.clientWidth  - CANVAS_PAD*2;
    const wh = wrap.clientHeight - CANVAS_PAD*2;
    zoomLevel = Math.min(ww / imageObj.width, wh / imageObj.height);
    applyZoom();
}

function applyZoom(){
    const w = Math.round(imageObj.width  * zoomLevel);
    const h = Math.round(imageObj.height * zoomLevel);
    const c = document.getElementById('canvasContainer');
    c.style.width  = w + 'px';
    c.style.height = h + 'px';
    bgCanvas.style.width    = w + 'px';
    bgCanvas.style.height   = h + 'px';
    drawCanvas.style.width  = w + 'px';
    drawCanvas.style.height = h + 'px';
    selCanvas.style.width   = w + 'px';
    selCanvas.style.height  = h + 'px';
    document.getElementById('zoomLabel').textContent = Math.round(zoomLevel*100)+'%';
    drawRulers();
    drawGrid();   // grid overlay viewport — ukurannya tidak ikut canvasContainer
}

// ─── Mouse Wheel Zoom (acuan di titik kursor) ────────────────────────────────
document.getElementById('canvasWrap').addEventListener('wheel', e=>{
    if(!imageObj) return;
    e.preventDefault();
    const wrap = document.getElementById('canvasWrap');
    const rect = wrap.getBoundingClientRect();
    const PAD = CANVAS_PAD;  // padding di dalam canvas-wrap sebelum canvasContainer
    // titik gambar (dalam piksel canvas) di bawah kursor sebelum zoom
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const imgX = (wrap.scrollLeft + mouseX - PAD) / zoomLevel;
    const imgY = (wrap.scrollTop  + mouseY - PAD) / zoomLevel;
    const factor = e.deltaY < 0 ? 1.15 : 1/1.15;
    zoomLevel = Math.min(Math.max(zoomLevel * factor, 0.05), 16);
    applyZoom();
    // pertahankan titik gambar itu tetap di posisi kursor
    wrap.scrollLeft = imgX * zoomLevel + PAD - mouseX;
    wrap.scrollTop  = imgY * zoomLevel + PAD - mouseY;
    drawRulers(); drawGrid();
}, {passive: false});

// ─── Rulers ─────────────────────────────────────────────────────────────────
function drawRulers(){
    const rulerH = document.getElementById('rulerH');
    const rulerV = document.getElementById('rulerV');
    const wrap   = document.getElementById('canvasWrap');
    if(!rulerH || !rulerV) return;

    // Size canvases to fill available space
    const wrapW = wrap.clientWidth;
    const wrapH = wrap.clientHeight;
    rulerH.width  = wrapW; rulerH.height = 20;
    rulerV.width  = 20;    rulerV.height = wrapH;

    const scrollL = wrap.scrollLeft;
    const scrollT = wrap.scrollTop;
    const PAD = CANVAS_PAD; // padding in canvas-wrap

    _drawHRuler(rulerH, scrollL, PAD);
    _drawVRuler(rulerV, scrollT, PAD);
}

// Padding lembar kerja — 0 = gambar rata kiri-atas.
// HARUS sama dengan padding .canvas-wrap di CSS.
const CANVAS_PAD = 0;

// ─── Satuan ruler ────────────────────────────────────────────────────────────
let rulerUnit = 'cm';   // 'px' | 'mm' | 'cm' | 'm'  (default cm)

function _unitPerPx(){
    if(rulerUnit === 'px') return 1;
    const dpi = parseFloat(document.getElementById('dpiInput').value) || 300;
    const mmPerPx = 25.4 / dpi;
    if(rulerUnit === 'mm') return mmPerPx;
    if(rulerUnit === 'cm') return mmPerPx / 10;
    return mmPerPx / 1000;   // m
}

function setRulerUnit(u){
    rulerUnit = u;
    drawRulers();
    drawGrid();
}

// Pilih step "cantik" dalam satuan aktif (1/2/2.5/5 × 10^n)
function _niceStepUnits(rawUnits){
    if(rawUnits <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(rawUnits)));
    for(const m of [1, 2, 2.5, 5, 10]){
        if(m * p >= rawUnits) return m * p;
    }
    return 10 * p;
}

function _fmtUnit(v){
    // buang trailing zero: 1.5, 2, 0.25 …
    return parseFloat(v.toFixed(4)).toString();
}

function _rulerStepPx(){
    const upp = _unitPerPx();
    const stepUnits = _niceStepUnits((60 / zoomLevel) * upp);
    return { stepPx: stepUnits / upp, stepUnits, upp };
}

function _drawHRuler(canvas, scrollLeft, pad){
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.fillStyle = '#4a4a4a';
    ctx.fillRect(0,0,W,H);
    if(!imageObj) return;
    const { stepPx, stepUnits, upp } = _rulerStepPx();
    const startIdx = Math.max(0, Math.floor((scrollLeft - pad) / zoomLevel / stepPx));
    ctx.fillStyle = '#ccc';
    ctx.font = '8px monospace';
    ctx.textBaseline = 'top';
    for(let n = startIdx; ; n++){
        const xPx = n * stepPx;
        const screenX = pad - scrollLeft + xPx * zoomLevel;
        if(screenX > W) break;
        if(screenX < 0) continue;
        ctx.fillRect(screenX, H-6, 1, 6);
        if(n % 5 === 0){
            ctx.fillRect(screenX, H-10, 1, 10);
            ctx.fillText(_fmtUnit(n * stepUnits), screenX+2, 1);
        }
    }
}

function _drawVRuler(canvas, scrollTop, pad){
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.fillStyle = '#4a4a4a';
    ctx.fillRect(0,0,W,H);
    if(!imageObj) return;
    const { stepPx, stepUnits } = _rulerStepPx();
    const startIdx = Math.max(0, Math.floor((scrollTop - pad) / zoomLevel / stepPx));
    ctx.fillStyle = '#ccc';
    ctx.font = '8px monospace';
    ctx.save();
    ctx.rotate(-Math.PI/2);
    for(let n = startIdx; ; n++){
        const yPx = n * stepPx;
        const screenY = pad - scrollTop + yPx * zoomLevel;
        if(screenY > H) break;
        if(screenY < 0) continue;
        ctx.fillRect(-screenY, W-6, 1, 6);
        if(n % 5 === 0){
            ctx.fillRect(-screenY, W-10, 1, 10);
            ctx.fillText(_fmtUnit(n * stepUnits), -screenY+2, 1);
        }
    }
    ctx.restore();
}

// Update rulers on scroll
document.getElementById('canvasWrap').addEventListener('scroll', ()=>{ drawRulers(); drawGrid(); }, {passive:true});
// Ganti DPI → skala satuan berubah
document.getElementById('dpiInput').addEventListener('input', ()=>{ drawRulers(); drawGrid(); });

// ─── Grid overlay ────────────────────────────────────────────────────────────
const gridCanvas = document.getElementById('gridCanvas');
const gridCtx    = gridCanvas.getContext('2d');
let showGrid = false;

function toggleGrid(force){
    showGrid = (typeof force === 'boolean') ? force : !showGrid;
    document.getElementById('gridBtn').classList.toggle('grid-on', showGrid);
    const chk = document.getElementById('gridChk');
    if(chk) chk.checked = showGrid;
    drawGrid();
}

// Grid digambar di overlay seukuran viewport → tembus ke seluruh lembar kerja,
// tidak berhenti di batas gambar. Koordinat mengikuti ruler (scroll + zoom).
function drawGrid(){
    const wrap = document.getElementById('canvasWrap');
    const W = wrap.clientWidth, H = wrap.clientHeight;
    if(W === 0 || H === 0) return;
    if(gridCanvas.width !== W || gridCanvas.height !== H){
        gridCanvas.width = W; gridCanvas.height = H;
    }
    gridCtx.clearRect(0, 0, W, H);
    if(!showGrid || !imageObj) return;

    const { stepPx } = _rulerStepPx();
    const stepScr = stepPx * zoomLevel;          // jarak grid dalam px layar
    if(stepScr < 3) return;                      // terlalu rapat → jangan gambar
    const sl = wrap.scrollLeft, st = wrap.scrollTop;

    // indeks grid pertama yang terlihat (boleh negatif → grid keluar area gambar)
    const n0x = Math.floor((sl - CANVAS_PAD) / stepScr);
    const n0y = Math.floor((st - CANVAS_PAD) / stepScr);

    gridCtx.lineWidth = 1;
    for(const major of [false, true]){
        gridCtx.strokeStyle = major ? 'rgba(0,120,215,0.40)' : 'rgba(0,120,215,0.16)';
        gridCtx.beginPath();
        for(let n = n0x; ; n++){
            const x = Math.round(CANVAS_PAD - sl + n * stepScr) + 0.5;
            if(x > W) break;
            if(x < 0) continue;
            if((n % 5 === 0) !== major) continue;
            gridCtx.moveTo(x, 0); gridCtx.lineTo(x, H);
        }
        for(let n = n0y; ; n++){
            const y = Math.round(CANVAS_PAD - st + n * stepScr) + 0.5;
            if(y > H) break;
            if(y < 0) continue;
            if((n % 5 === 0) !== major) continue;
            gridCtx.moveTo(0, y); gridCtx.lineTo(W, y);
        }
        gridCtx.stroke();
    }
}

// ─── Ruler corner popup & background ────────────────────────────────────────
function toggleRulerPopup(e){
    e.stopPropagation();
    const p = document.getElementById('rulerPopup');
    p.style.display = (p.style.display === 'block') ? 'none' : 'block';
}
document.addEventListener('click', e=>{
    const p = document.getElementById('rulerPopup');
    if(p.style.display === 'block' && !p.contains(e.target) && e.target.id !== 'rulerCorner'){
        p.style.display = 'none';
    }
});

function setCanvasBg(color){
    document.getElementById('canvasWrap').style.background = color;
    try{ localStorage.setItem('spotBgColor', color); }catch(_){}
}
// restore preferensi background
try{
    const savedBg = localStorage.getItem('spotBgColor');
    if(savedBg){ setCanvasBg(savedBg); document.getElementById('bgColorPick').value = savedBg; }
}catch(_){}

// ─── Coordinate helper ──────────────────────────────────────────────────────
function getCanvasPos(e){
    const rect = drawCanvas.getBoundingClientRect();
    return {
        x: Math.round((e.clientX - rect.left) / zoomLevel),
        y: Math.round((e.clientY - rect.top)  / zoomLevel),
    };
}

// ─── Drawing Events ─────────────────────────────────────────────────────────
drawCanvas.addEventListener('contextmenu', e=>{ e.preventDefault(); if(currentTool==='polygon') removeLastPolyPoint(); });

drawCanvas.addEventListener('mousedown', e=>{
    if(e.button !== 0) return;
    if(!imageObj) return;
    const {x,y} = getCanvasPos(e);

    // Shift = add, Alt = subtract (override selMode for this click)
    const effMode = e.shiftKey ? 'add' : e.altKey ? 'subtract' : selMode;

    if(currentTool === 'polygon'){
        handlePolygonClick(x, y, e);
        return;
    }
    saveHistory();
    if(currentTool === 'fill'){
        _recAct({t:'fill', rx:x/drawCanvas.width, ry:y/drawCanvas.height, mode:effMode});
        _runSelection('Memproses…', ()=>{ floodFill(x, y, effMode); recomputeAnts(); _renderChannelList(); });
        return;
    }
    if(currentTool === 'magicwand'){
        _recAct({t:'wand', rx:x/drawCanvas.width, ry:y/drawCanvas.height, mode:effMode, ..._selOpts()});
        _runSelection('Menyeleksi (Magic Wand)…', ()=>magicWand(x, y, effMode));
        return;
    }
    if(currentTool === 'colorselect'){
        _recAct({t:'color', rx:x/drawCanvas.width, ry:y/drawCanvas.height, mode:effMode, ..._selOpts()});
        _runSelection('Menyeleksi (Select by Color)…', ()=>selectByColor(x, y, effMode));
        return;
    }
    isDrawing = true;
    startX = x; startY = y; lastX = x; lastY = y;

    if(currentTool === 'brush' || currentTool === 'eraser'){
        drawCtx.globalCompositeOperation = currentTool === 'eraser' ? 'destination-out' : 'source-over';
        drawCtx.beginPath();
        drawCtx.arc(x, y, getBrushRadius(), 0, Math.PI*2);
        drawCtx.fillStyle = getColor(overlayAlpha);
        drawCtx.fill();
    } else {
        // rect / ellipse: save snapshot for preview
        previewCanvas = document.createElement('canvas');
        previewCanvas.width  = drawCanvas.width;
        previewCanvas.height = drawCanvas.height;
        previewCanvas.getContext('2d').drawImage(drawCanvas, 0, 0);
    }
});

drawCanvas.addEventListener('mousemove', e=>{
    if(!imageObj) return;
    const {x,y} = getCanvasPos(e);
    document.getElementById('coordLabel').textContent = `${x} × ${y} px`;

    if(currentTool === 'polygon' && polyPoints.length > 0){
        redrawPolygonPreview(x, y);
        return;
    }
    if(!isDrawing) return;

    if(currentTool === 'brush' || currentTool === 'eraser'){
        drawCtx.globalCompositeOperation = currentTool === 'eraser' ? 'destination-out' : 'source-over';
        drawCtx.beginPath();
        drawCtx.moveTo(lastX, lastY);
        drawCtx.lineTo(x, y);
        drawCtx.strokeStyle = getColor(overlayAlpha);
        drawCtx.lineWidth = getBrushRadius()*2;
        drawCtx.lineCap = 'round';
        drawCtx.lineJoin = 'round';
        drawCtx.stroke();
        // fill cap dots
        drawCtx.beginPath();
        drawCtx.arc(x, y, getBrushRadius(), 0, Math.PI*2);
        drawCtx.fillStyle = getColor(overlayAlpha);
        drawCtx.fill();
        lastX = x; lastY = y;
    } else if(currentTool === 'rect' || currentTool === 'ellipse'){
        // restore snapshot then draw preview
        drawCtx.clearRect(0,0,drawCanvas.width,drawCanvas.height);
        drawCtx.drawImage(previewCanvas, 0, 0);
        drawCtx.globalCompositeOperation = 'source-over';
        drawCtx.fillStyle = getColor(overlayAlpha);
        if(currentTool === 'rect'){
            drawCtx.fillRect(startX, startY, x-startX, y-startY);
        } else {
            const rx = Math.abs(x-startX)/2, ry = Math.abs(y-startY)/2;
            const cx = startX+(x-startX)/2, cy = startY+(y-startY)/2;
            drawCtx.beginPath();
            drawCtx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI*2);
            drawCtx.fill();
        }
    }
});

drawCanvas.addEventListener('mouseup', e=>{
    if(e.button !== 0) return;
    if(isDrawing){ recomputeAnts(); _renderChannelList(); }
    isDrawing = false;
    drawCtx.globalCompositeOperation = 'source-over';
    previewCanvas = null;
});

drawCanvas.addEventListener('mouseleave', ()=>{ isDrawing = false; drawCtx.globalCompositeOperation = 'source-over'; });

// ─── Init ─────────────────────────────────────────────────────────────────────
setTool('brush');   // set initial ctx-bar state

window.addEventListener('resize', ()=>{ if(imageObj){ drawRulers(); drawGrid(); } });

// ─── Select All (Ctrl+A) — seluruh kanvas, termasuk area transparan ─────────
function selectAll(){
    if(!imageObj) return;
    _recAct({t:'all'});
    const w = bgCanvas.width, h = bgCanvas.height;
    selectionMask = new Uint8Array(w*h).fill(1);
    document.getElementById('applySelBtn').disabled = false;
    recomputeAnts();
}

function _isTypingTarget(e){
    const t = e.target;
    return t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
}

// ─── Keyboard shortcuts ─────────────────────────────────────────────────────
document.addEventListener('keydown', e=>{
    if((e.ctrlKey||e.metaKey) && e.key==='z' && !e.shiftKey){ e.preventDefault(); undo(); return; }
    if((e.ctrlKey||e.metaKey) && (e.key==='y' || (e.key==='z'&&e.shiftKey))){ e.preventDefault(); redo(); return; }
    if((e.ctrlKey||e.metaKey) && (e.key==='a'||e.key==='A')){ e.preventDefault(); selectAll(); return; }
    if((e.ctrlKey||e.metaKey) && e.key==='d'){ e.preventDefault(); deselect(); return; }
    if((e.ctrlKey||e.metaKey) && e.shiftKey && e.key.toUpperCase()==='I'){ e.preventDefault(); selectInverse(); return; }

    // Spasi (tahan) → mode geser lembar kerja
    if(e.code === 'Space' && !_isTypingTarget(e)){
        e.preventDefault();
        if(!spaceDown){ spaceDown = true; canvasWrapEl.style.cursor = 'grab'; }
        return;
    }

    if(e.ctrlKey || e.metaKey || e.altKey) return;
    if(e.key === 'Enter'){
        if(currentTool === 'polygon') finishPolygon();
        else if(selectionMask) applySelection();
        return;
    }
    if(e.key === 'Escape'){ cancelPolygon(); deselect(); return; }
    if(e.key === 'b') setTool('brush');
    if(e.key === 'e') setTool('eraser');
    if(e.key === 'r') setTool('rect');
    if(e.key === 'f') setTool('fill');
    if(e.key === 'p') setTool('polygon');
    if(e.key === 'w') setTool('magicwand');
    if(e.key === 's') setTool('colorselect');
    if(e.key === '+' || e.key === '=') zoom(1.25);
    if(e.key === '-') zoom(0.8);
});

document.addEventListener('keyup', e=>{
    if(e.code === 'Space'){
        spaceDown = false;
        if(!isPanning) canvasWrapEl.style.cursor = '';
    }
});

// ─── Pan lembar kerja: tahan Spasi + drag, atau klik-tengah + drag ──────────
const canvasWrapEl = document.getElementById('canvasWrap');
let spaceDown = false, isPanning = false;
let panStartX = 0, panStartY = 0, panScrollL = 0, panScrollT = 0;

canvasWrapEl.addEventListener('mousedown', e=>{
    // klik tengah (button 1) atau spasi+klik kiri → mulai geser
    if(e.button === 1 || (spaceDown && e.button === 0)){
        isPanning = true;
        panStartX = e.clientX; panStartY = e.clientY;
        panScrollL = canvasWrapEl.scrollLeft; panScrollT = canvasWrapEl.scrollTop;
        canvasWrapEl.style.cursor = 'grabbing';
        e.preventDefault();
        e.stopPropagation();   // jangan sampai memicu gambar/seleksi
    }
}, true);   // capture: dahulukan sebelum handler drawCanvas

window.addEventListener('mousemove', e=>{
    if(!isPanning) return;
    canvasWrapEl.scrollLeft = panScrollL - (e.clientX - panStartX);
    canvasWrapEl.scrollTop  = panScrollT - (e.clientY - panStartY);
    drawRulers(); drawGrid();
});

window.addEventListener('mouseup', e=>{
    if(isPanning){
        isPanning = false;
        canvasWrapEl.style.cursor = spaceDown ? 'grab' : '';
    }
});

// Cegah menu auto-scroll bawaan klik-tengah
canvasWrapEl.addEventListener('auxclick', e=>{ if(e.button === 1) e.preventDefault(); });

// ─── Brush helpers ──────────────────────────────────────────────────────────
function getBrushRadius(){ return parseInt(document.getElementById('brushSize').value) / 2; }

// ─── Polygon ─────────────────────────────────────────────────────────────────
function handlePolygonClick(x, y, e){
    if(e.detail >= 2){
        finishPolygon();
        return;
    }
    if(polyPoints.length === 0){
        // save snapshot
        previewCanvas = document.createElement('canvas');
        previewCanvas.width  = drawCanvas.width;
        previewCanvas.height = drawCanvas.height;
        previewCanvas.getContext('2d').drawImage(drawCanvas, 0, 0);
        document.getElementById('polyHint').style.display = 'block';
    }
    polyPoints.push({x,y});
    redrawPolygonPreview(x, y);
}

function redrawPolygonPreview(mx, my){
    if(!previewCanvas || polyPoints.length === 0) return;
    drawCtx.clearRect(0,0,drawCanvas.width,drawCanvas.height);
    drawCtx.drawImage(previewCanvas,0,0);
    const pts = polyPoints;
    drawCtx.beginPath();
    drawCtx.moveTo(pts[0].x, pts[0].y);
    for(let i=1;i<pts.length;i++) drawCtx.lineTo(pts[i].x, pts[i].y);
    drawCtx.lineTo(mx, my);
    drawCtx.fillStyle = getColor(overlayAlpha * 0.5);
    drawCtx.fill();
    drawCtx.strokeStyle = getColor(200);
    drawCtx.lineWidth = 1.5 / zoomLevel;
    drawCtx.setLineDash([4/zoomLevel, 4/zoomLevel]);
    drawCtx.stroke();
    drawCtx.setLineDash([]);
    // draw dots
    pts.forEach(p=>{ drawCtx.beginPath(); drawCtx.arc(p.x,p.y,3/zoomLevel,0,Math.PI*2); drawCtx.fillStyle='#fff'; drawCtx.fill(); drawCtx.strokeStyle='#333'; drawCtx.lineWidth=1/zoomLevel; drawCtx.stroke(); });
}

function finishPolygon(){
    if(polyPoints.length < 3){ cancelPolygon(); return; }
    if(!previewCanvas) return;
    saveHistory();
    drawCtx.clearRect(0,0,drawCanvas.width,drawCanvas.height);
    drawCtx.drawImage(previewCanvas,0,0);
    drawCtx.globalCompositeOperation = 'source-over';
    drawCtx.beginPath();
    drawCtx.moveTo(polyPoints[0].x, polyPoints[0].y);
    polyPoints.forEach(p=>drawCtx.lineTo(p.x,p.y));
    drawCtx.closePath();
    drawCtx.fillStyle = getColor(overlayAlpha);
    drawCtx.fill();
    polyPoints = [];
    previewCanvas = null;
    document.getElementById('polyHint').style.display = 'none';
    recomputeAnts();
}

function cancelPolygon(){
    if(previewCanvas && polyPoints.length > 0){
        drawCtx.clearRect(0,0,drawCanvas.width,drawCanvas.height);
        drawCtx.drawImage(previewCanvas,0,0);
    }
    polyPoints = [];
    previewCanvas = null;
    document.getElementById('polyHint').style.display = 'none';
}

function removeLastPolyPoint(){
    if(polyPoints.length > 0) polyPoints.pop();
}

// ─── Undo / Redo ─────────────────────────────────────────────────────────────
function saveHistory(){
    if(!imageObj) return;
    const snap = drawCtx.getImageData(0,0,drawCanvas.width,drawCanvas.height);
    undoStack.push(snap);
    if(undoStack.length > MAX_HISTORY) undoStack.shift();
    redoStack.length = 0;
    _updateUndoRedo();
}
function undo(){
    if(!undoStack.length) return;
    redoStack.push(drawCtx.getImageData(0,0,drawCanvas.width,drawCanvas.height));
    drawCtx.putImageData(undoStack.pop(), 0, 0);
    _updateUndoRedo();
    recomputeAnts();
    _renderChannelList();
}
function redo(){
    if(!redoStack.length) return;
    undoStack.push(drawCtx.getImageData(0,0,drawCanvas.width,drawCanvas.height));
    drawCtx.putImageData(redoStack.pop(), 0, 0);
    _updateUndoRedo();
    recomputeAnts();
    _renderChannelList();
}
function _updateUndoRedo(){
    document.getElementById('undoBtn').disabled = undoStack.length === 0;
    document.getElementById('redoBtn').disabled = redoStack.length === 0;
}

// ─── Marching Ants ───────────────────────────────────────────────────────────
// Bangun mask biner (Uint8Array) dari seleksi aktif / channel yang tergambar
function _currentSelMask(){
    const w = drawCanvas.width, h = drawCanvas.height;
    if(selectionMask) return selectionMask;
    const d = drawCtx.getImageData(0,0,w,h).data;
    const m = new Uint8Array(w*h);
    for(let i=0;i<w*h;i++) if(d[i*4+3] > 10) m[i] = 1;
    return m;
}

// Trace batas seleksi menjadi loop-loop poligon presisi (di tepi piksel).
// Edge yang bersinggungan dengan tepi gambar (out-of-bounds) DILEWATI
// → marching ants tidak menggambar bingkai gambar (req: tepi tidak diseleksi).
function _traceBoundary(sel, w, h){
    const NP = (w + 1);
    const adj = new Map();          // pointId → array of neighbor pointId
    const addEdge = (ax, ay, bx, by) => {
        const a = ay*NP + ax, b = by*NP + bx;
        (adj.get(a) || adj.set(a, []).get(a)).push(b);
        (adj.get(b) || adj.set(b, []).get(b)).push(a);
    };
    for(let y=0; y<h; y++){
        const row = y*w;
        for(let x=0; x<w; x++){
            if(!sel[row + x]) continue;
            if(y>0   && !sel[row - w + x]) addEdge(x, y,   x+1, y);     // atas
            if(y<h-1 && !sel[row + w + x]) addEdge(x, y+1, x+1, y+1);   // bawah
            if(x>0   && !sel[row + x - 1]) addEdge(x, y,   x,   y+1);   // kiri
            if(x<w-1 && !sel[row + x + 1]) addEdge(x+1, y, x+1, y+1);   // kanan
        }
    }
    // Rangkai edge jadi loop
    const loops = [];
    const usedFrom = new Map();   // pointId → berapa neighbor sudah dipakai
    const nextUnused = (p) => {
        const arr = adj.get(p); if(!arr) return -1;
        let idx = usedFrom.get(p) || 0;
        while(idx < arr.length && arr[idx] < 0) idx++;
        return idx < arr.length ? idx : -1;
    };
    for(const start of adj.keys()){
        while(true){
            const arr = adj.get(start);
            let si = 0; while(si < arr.length && arr[si] < 0) si++;
            if(si >= arr.length) break;
            // mulai loop baru
            const loop = [start % NP, (start / NP) | 0];
            let cur = start, prev = -1;
            while(true){
                const carr = adj.get(cur);
                let ni = -1;
                for(let k=0;k<carr.length;k++){
                    if(carr[k] >= 0 && carr[k] !== prev){ ni = k; break; }
                }
                if(ni === -1){
                    for(let k=0;k<carr.length;k++){ if(carr[k] >= 0){ ni = k; break; } }
                }
                if(ni === -1) break;
                const nb = carr[ni];
                carr[ni] = -1;                       // tandai edge terpakai
                const barr = adj.get(nb);            // hapus arah balik
                for(let k=0;k<barr.length;k++){ if(barr[k] === cur){ barr[k] = -1; break; } }
                loop.push(nb % NP, (nb / NP) | 0);
                prev = cur; cur = nb;
                if(cur === start) break;
            }
            if(loop.length >= 6) loops.push(loop);
        }
    }
    return loops;
}

function recomputeAnts(){
    if(!imageObj){ antLoops = []; return; }
    const w = drawCanvas.width, h = drawCanvas.height;
    antLoops = _traceBoundary(_currentSelMask(), w, h);
    if(!antRAF) _startAnts();
}

function _startAnts(){ antRAF = requestAnimationFrame(_tickAnts); }

function _tickAnts(){
    antRAF = requestAnimationFrame(_tickAnts);
    antFrameTick++;
    if(antFrameTick % 2 === 0){        // ~30fps, gerak halus seperti Photoshop
        antDashOffset -= 0.5;          // kecepatan jalan semut (px layar)
        _drawAnts();
    }
}

// Marching ants gaya Photoshop: garis putih solid + dash hitam berjalan,
// tebal & panjang dash konstan di layar (dibagi zoom).
const _ANT_DASH = 4;   // px layar
function _drawAnts(){
    const w = selCanvas.width, h = selCanvas.height;
    selCtx.clearRect(0, 0, w, h);
    if(!antLoops.length) return;
    const z = Math.max(zoomLevel, 1e-4);

    const path = new Path2D();
    for(const loop of antLoops){
        path.moveTo(loop[0], loop[1]);
        for(let i=2;i<loop.length;i+=2) path.lineTo(loop[i], loop[i+1]);
    }
    selCtx.lineJoin = 'round';
    selCtx.lineCap  = 'butt';
    selCtx.lineWidth = 1 / z;                 // ~1px di layar

    selCtx.setLineDash([]);
    selCtx.strokeStyle = '#ffffff';
    selCtx.stroke(path);                       // dasar putih solid

    selCtx.setLineDash([_ANT_DASH / z, _ANT_DASH / z]);
    selCtx.lineDashOffset = antDashOffset / z;
    selCtx.strokeStyle = '#000000';
    selCtx.stroke(path);                       // dash hitam berjalan
}

// ─── Selection mode helper ───────────────────────────────────────────────────
function _applySelPixels(dst, selected, sm){
    const [fr,fg,fb] = modeColors[currentMode];
    const fa = overlayAlpha;
    if(sm === 'subtract'){
        for(let k = 0; k < selected.length; k++){
            const pi = selected[k]*4;
            dst[pi+3] = 0;
        }
    } else {
        // 'new': clear first
        if(sm === 'new'){
            for(let i=3; i < dst.length; i+=4) dst[i] = 0;
        }
        for(let k = 0; k < selected.length; k++){
            const pi = selected[k]*4;
            dst[pi]=fr; dst[pi+1]=fg; dst[pi+2]=fb; dst[pi+3]=fa;
        }
    }
}

// ─── Flood Fill ─────────────────────────────────────────────────────────────
function floodFill(sx, sy, sm='new'){
    const w = drawCanvas.width, h = drawCanvas.height;
    const imgData = drawCtx.getImageData(0,0,w,h);
    const d = imgData.data;
    const idx = (sy*w+sx)*4;
    const tr = d[idx], tg = d[idx+1], tb = d[idx+2], ta = d[idx+3];

    const visited = new Uint8Array(w*h);
    const selected = [];
    const stack = new Int32Array(w*h);   // stack indeks piksel (hemat GC)
    let sp = 0;
    const seed = sy*w+sx;
    stack[sp++] = seed; visited[seed] = 1;
    while(sp > 0){
        const i = stack[--sp];
        const pi = i*4;
        if(Math.abs(d[pi]-tr)>30||Math.abs(d[pi+1]-tg)>30||Math.abs(d[pi+2]-tb)>30||Math.abs(d[pi+3]-ta)>30) continue;
        selected.push(i);
        const x = i % w, y = (i/w)|0;
        if(x>0   && !visited[i-1]){ visited[i-1]=1; stack[sp++]=i-1; }
        if(x<w-1 && !visited[i+1]){ visited[i+1]=1; stack[sp++]=i+1; }
        if(y>0   && !visited[i-w]){ visited[i-w]=1; stack[sp++]=i-w; }
        if(y<h-1 && !visited[i+w]){ visited[i+w]=1; stack[sp++]=i+w; }
    }
    _applySelPixels(d, selected, sm);
    drawCtx.putImageData(imgData,0,0);
}

// ─── Matcher gaya Photoshop ──────────────────────────────────────────────────
// * Klik area TRANSPARAN (alpha < 128): yang diseleksi adalah "transparansi".
//   RGB piksel transparan diabaikan (tidak bermakna) — semua piksel dengan
//   opacity < 50% ikut terpilih, termasuk tekstur/pattern semi-transparan.
//   Ants tepat di ambang 50% seperti Photoshop.
// * Klik area OPAQUE: bandingkan RGB dengan toleransi; piksel semi-transparan
//   (<50%) tidak ikut.
function _makeMatcher(src, si, tol){
    const tr = src[si], tg = src[si+1], tb = src[si+2], ta = src[si+3];
    if(ta < 128){
        return (pi) => src[pi+3] < 128;
    }
    return (pi) =>
        src[pi+3] >= 128 &&
        Math.abs(src[pi]-tr)   <= tol &&
        Math.abs(src[pi+1]-tg) <= tol &&
        Math.abs(src[pi+2]-tb) <= tol;
}

// ─── Magic Wand — contiguous, sifat Photoshop ────────────────────────────────
function magicWand(sx, sy, sm='new'){
    const w = drawCanvas.width, h = drawCanvas.height;
    const tol = parseInt(document.getElementById('tolerance').value);
    const src  = bgCtx.getImageData(0,0,w,h).data;
    const match = _makeMatcher(src, (sy*w+sx)*4, tol);

    const visited = new Uint8Array(w*h);
    const newSel  = new Uint8Array(w*h);
    const stack   = new Int32Array(w*h);   // stack indeks piksel (hemat GC)
    let sp = 0;
    const seed = sy*w+sx;
    stack[sp++] = seed; visited[seed] = 1;
    while(sp > 0){
        const i = stack[--sp];
        if(!match(i*4)) continue;
        newSel[i]=1;
        const x = i % w, y = (i/w)|0;
        if(x>0   && !visited[i-1]){ visited[i-1]=1; stack[sp++]=i-1; }
        if(x<w-1 && !visited[i+1]){ visited[i+1]=1; stack[sp++]=i+1; }
        if(y>0   && !visited[i-w]){ visited[i-w]=1; stack[sp++]=i-w; }
        if(y<h-1 && !visited[i+w]){ visited[i+w]=1; stack[sp++]=i+w; }
    }
    _mergeSelMask(newSel, sm, w*h);
}

// ─── Select by Color — global, sifat Photoshop ──────────────────────────────
// Klik transparan → SEMUA area transparan (termasuk lubang di dalam objek) ikut.
function selectByColor(sx, sy, sm='new'){
    const w = drawCanvas.width, h = drawCanvas.height;
    const tol = parseInt(document.getElementById('tolerance').value);
    const src  = bgCtx.getImageData(0,0,w,h).data;
    const match = _makeMatcher(src, (sy*w+sx)*4, tol);

    const newSel = new Uint8Array(w*h);
    for(let i=0; i<w*h; i++){
        if(match(i*4)) newSel[i]=1;
    }
    _mergeSelMask(newSel, sm, w*h);
}

// ─── Merge new selection into selectionMask based on mode ───────────────────
// Remove isolated noise pixels from a binary Uint8Array mask (morphological open)
function _cleanSelMask(mask, w, h){
    const R = 2; // erode/dilate radius (5×5 → removes dots <4px)
    // Erode
    const tmp = new Uint8Array(w*h);
    for(let y=0;y<h;y++) for(let x=0;x<w;x++){
        let ok=1;
        outer: for(let dy=-R;dy<=R;dy++) for(let dx=-R;dx<=R;dx++){
            const nx=x+dx,ny=y+dy;
            if(nx<0||nx>=w||ny<0||ny>=h||!mask[ny*w+nx]){ok=0;break outer;}
        }
        tmp[y*w+x]=ok;
    }
    // Dilate
    const out = new Uint8Array(w*h);
    for(let y=0;y<h;y++) for(let x=0;x<w;x++){
        let ok=0;
        outer: for(let dy=-R;dy<=R;dy++) for(let dx=-R;dx<=R;dx++){
            const nx=x+dx,ny=y+dy;
            if(nx>=0&&nx<w&&ny>=0&&ny<h&&tmp[ny*w+nx]){ok=1;break outer;}
        }
        out[y*w+x]=ok;
    }
    return out;
}

// Isi lubang di dalam objek: piksel non-terpilih yang TIDAK terhubung ke tepi
// gambar = lubang interior → jadikan terpilih. Hasil: siluet solid, tidak ada
// loop marching-ants di bagian dalam objek (req: bagian dalam tidak terseleksi).
function _fillHoles(mask, w, h){
    const outside = new Uint8Array(w*h);
    const st = [];
    for(let x=0;x<w;x++){
        if(!mask[x]) st.push(x);
        const b=(h-1)*w+x; if(!mask[b]) st.push(b);
    }
    for(let y=0;y<h;y++){
        const l=y*w; if(!mask[l]) st.push(l);
        const r=y*w+w-1; if(!mask[r]) st.push(r);
    }
    while(st.length){
        const i = st.pop();
        if(outside[i] || mask[i]) continue;
        outside[i] = 1;
        const x = i % w, y = (i / w) | 0;
        if(x>0)   st.push(i-1);
        if(x<w-1) st.push(i+1);
        if(y>0)   st.push(i-w);
        if(y<h-1) st.push(i+w);
    }
    const out = new Uint8Array(w*h);
    for(let i=0;i<w*h;i++) out[i] = (mask[i] || !outside[i]) ? 1 : 0;
    return out;
}

// Mask piksel putih (dari bgCanvas), di-cache per gambar
let _whiteMaskCache = null;
function _getWhiteMask(){
    const w = bgCanvas.width, h = bgCanvas.height;
    if(_whiteMaskCache && _whiteMaskCache.length === w*h) return _whiteMaskCache;
    const d = bgCtx.getImageData(0,0,w,h).data;
    const m = new Uint8Array(w*h);
    for(let i=0;i<w*h;i++){
        const p=i*4;
        if(d[p]>=245 && d[p+1]>=245 && d[p+2]>=245) m[i]=1;
    }
    _whiteMaskCache = m;
    return m;
}
function _isExcludeWhite(){
    const cb = document.getElementById('excludeWhite');
    return cb && cb.checked;
}
function _isSolid(){
    const cb = document.getElementById('solidFill');
    return cb && cb.checked;
}
// Sifat seleksi mengikuti Photoshop: hanya piksel yang benar-benar cocok yang
// terpilih — TIDAK otomatis mengisi lubang / bagian dalam objek. Fill-holes
// hanya bila opsi "Solid" dicentang.
// Catatan: "Kecualikan putih" TIDAK membuang putih dari seleksi — putih tetap
// terseleksi; opsi itu hanya membekukan putih saat contract/expand.
function _mergeSelMask(newSel, sm, size){
    const w = bgCanvas.width, h = bgCanvas.height;
    let mask = newSel;
    if(_isSolid())        mask = _fillHoles(mask, w, h);   // opsional: siluet solid
    if(sm==='add' && selectionMask){
        for(let i=0;i<size;i++) if(mask[i]) selectionMask[i]=1;
    } else if(sm==='subtract' && selectionMask){
        for(let i=0;i<size;i++) if(mask[i]) selectionMask[i]=0;
    } else {
        selectionMask = mask;
    }
    document.getElementById('applySelBtn').disabled = false;
    recomputeAnts();
}

// ─── Apply selection to drawCanvas with current mode color ───────────────────
function applySelection(){
    if(!selectionMask||!imageObj) return;
    _recAct({t:'apply'});
    saveHistory();
    const w = drawCanvas.width, h = drawCanvas.height;
    const dst = drawCtx.getImageData(0,0,w,h);
    const d = dst.data;
    const [fr,fg,fb] = modeColors[currentMode];
    const fa = overlayAlpha;
    for(let i=0;i<w*h;i++){
        if(selectionMask[i]){ d[i*4]=fr; d[i*4+1]=fg; d[i*4+2]=fb; d[i*4+3]=fa; }
    }
    drawCtx.putImageData(dst,0,0);
    selectionMask = null;
    document.getElementById('applySelBtn').disabled = true;
    recomputeAnts();
    _renderChannelList();
}

// ─── Deselect ────────────────────────────────────────────────────────────────
function deselect(){
    selectionMask = null;
    antLoops = [];
    selCtx.clearRect(0,0,selCanvas.width,selCanvas.height);
    document.getElementById('applySelBtn').disabled = true;
}

// ─── Clear mask ──────────────────────────────────────────────────────────────
function clearMask(){
    if(!imageObj) return;
    if(!confirm('Hapus area spot pada channel ini?')) return;
    _recAct({t:'clear'});
    clearMaskData();
    if(channels[activeChannel]) channels[activeChannel].img = null;
    _renderChannelList();
}

// Bersihkan seleksi satu channel dari daftar (tombol Clear di channel list)
function clearChannel(i){
    if(!imageObj || !channels[i]) return;
    if(i === activeChannel){
        _recAct({t:'clear'});
        clearMaskData();            // channel aktif → bersihkan kanvas kerja
    }
    channels[i].img = null;
    _renderChannelList();
    if(i === activeChannel) recomputeAnts();
}

function clearMaskData(){
    drawCtx.clearRect(0,0,drawCanvas.width,drawCanvas.height);
    cancelPolygon();
    selectionMask = null;
    antLoops = [];
    selCtx.clearRect(0,0,selCanvas.width,selCanvas.height);
    const ab = document.getElementById('applySelBtn');
    if(ab) ab.disabled = true;
}

// ─── Channel List State ─────────────────────────────────────────────────────
const MODE_COLORS = {
    white:   '#ff00c8',
    varnish: '#00bcd4',
};
const MODE_LABELS = {
    white: 'White', varnish: 'Varnish'
};

// Deteksi cepat apakah data punya tinta (stride 4px agar ringan)
function _dataHasInk(data){
    for(let i=3;i<data.length;i+=16){ if(data[i]>10) return true; }
    return false;
}
function _hasInk(img){ return img ? _dataHasInk(img.data) : false; }
function _canvasHasInk(){
    return _dataHasInk(drawCtx.getImageData(0,0,drawCanvas.width,drawCanvas.height).data);
}

// ImageData → binary mask PNG base64 (alpha>10 → 255)
function _imgToMaskB64(img){
    const mc = document.createElement('canvas');
    mc.width = img.width; mc.height = img.height;
    const mx = mc.getContext('2d');
    const out = mx.createImageData(img.width, img.height);
    for(let i=0;i<img.data.length;i+=4){
        const v = img.data[i+3] > 10 ? 255 : 0;
        out.data[i]=out.data[i+1]=out.data[i+2]=v; out.data[i+3]=255;
    }
    mx.putImageData(out,0,0);
    return mc.toDataURL('image/png').split(',')[1];
}

function _renderChannelList(){
    const list = document.getElementById('channelList');
    if(!channels.length){
        list.innerHTML = '<div style="color:#bbb;font-size:11px;text-align:center;padding:6px">Upload gambar dulu</div>';
        document.getElementById('genBtn').disabled = true;
        return;
    }
    let anyInk = false;
    list.innerHTML = channels.map((ch,i)=>{
        const filled = (i === activeChannel) ? _canvasHasInk() : _hasInk(ch.img);
        if(filled) anyInk = true;
        return `<div class="ch-item ${i===activeChannel?'active':''}" onclick="selectChannel(${i})">
            <div class="ch-dot" style="background:${MODE_COLORS[ch.mode]||'#999'}"></div>
            <div class="ch-info">
                <div class="ch-name">${ch.name}</div>
                <div class="ch-mode">${filled ? '✔ ada area' : 'kosong'}</div>
            </div>
            ${filled ? `<button class="ch-clear-btn" title="Bersihkan seleksi channel ${ch.name}"
                 onclick="event.stopPropagation();clearChannel(${i})">Clear</button>` : ''}
        </div>`;
    }).join('');
    document.getElementById('genBtn').disabled = !anyInk;
}

// ─── Kirim ke server (opsi unduh langsung) ───────────────────────────────────
async function _sendSpotColor(imgB64, imageName, payloadChannels, dpi, doDownload=true){
    const res = await fetch('/api/spot-color', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ image: imgB64, image_name: imageName, dpi, channels: payloadChannels })
    });
    const data = await res.json();
    if(data.status !== 'success') throw new Error(data.message || 'Gagal membuat PDF');
    if(doDownload){
        const a = document.createElement('a');
        a.href = '/api/spot-color-download?file='+encodeURIComponent(data.filename);
        a.download = data.filename;
        document.body.appendChild(a); a.click(); a.remove();
    }
    return data;   // {filename, ...}
}

// Unduh beberapa PDF sekaligus sebagai satu ZIP (hindari dialog Save As beruntun)
async function _downloadZip(filenames){
    const res = await fetch('/api/spot-color-zip', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ files: filenames })
    });
    if(!res.ok) throw new Error('Gagal membuat ZIP');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'spot_batch_' + Date.now() + '.zip';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
}

// ─── Generate PDF (mode interaktif, dari editor aktif) ───────────────────────
async function generatePDF(){
    if(!imageFile || !imageObj) return;
    _recAct({t:'generate'});   // rekam sebagai bagian action
    _saveActiveChannel();

    const payloadChannels = [];
    for(const ch of channels){
        if(!_hasInk(ch.img)) continue;
        payloadChannels.push({ name:ch.name, mode:ch.mode, mask:_imgToMaskB64(ch.img) });
    }
    if(payloadChannels.length === 0){
        const sb = document.getElementById('statusBox');
        sb.className='status-box err';
        sb.textContent='Belum ada area yang digambar di channel manapun.';
        return;
    }

    const dpi = parseInt(document.getElementById('dpiInput').value)||300;
    const genBtn   = document.getElementById('genBtn');
    const statusBox= document.getElementById('statusBox');
    genBtn.disabled=true; genBtn.textContent='Memproses...';
    statusBox.className='status-box';
    statusBox.textContent=`Membuat PDF dengan ${payloadChannels.length} spot channel...`;

    try {
        const imgB64 = await new Promise(res=>{
            const rd = new FileReader();
            rd.onload = e => res(e.target.result.split(',')[1]);
            rd.readAsDataURL(imageFile);
        });
        const data = await _sendSpotColor(imgB64, imageFile.name, payloadChannels, dpi);
        const chNames = (data.channels||[]).map(c=>c.name).join(', ');
        statusBox.className='status-box ok';
        statusBox.innerHTML = `PDF berhasil!<br><small>${data.filename}</small><br>`
            + `<small>${data.n_channels} channel: ${chNames}</small>`;
    } catch(e){
        statusBox.className='status-box err';
        statusBox.textContent='Error: '+e.message;
    } finally {
        genBtn.innerHTML = '&#11015; Generate &amp; Download PDF';
        _renderChannelList();
    }
}

// ═══ ACTION: rekam tindakan → terapkan ke banyak file ════════════════════════
let actionSteps = [];
let isRecording = false;
let isReplaying = false;

// snapshot opsi seleksi saat merekam (dipulihkan saat replay)
function _selOpts(){
    return {
        tol:   parseInt(document.getElementById('tolerance').value) || 32,
        solid: _isSolid(),
        exw:   _isExcludeWhite(),
    };
}
function _applySelOpts(s){
    if(s.tol   !== undefined) document.getElementById('tolerance').value = s.tol;
    if(s.solid !== undefined) document.getElementById('solidFill').checked = s.solid;
    if(s.exw   !== undefined) document.getElementById('excludeWhite').checked = s.exw;
}

function _recAct(step){
    if(!isRecording || isReplaying) return;
    actionSteps.push(step);
    _renderRecSteps();
}

const ACT_LABELS = {
    ptype:'Jenis produk', chan:'Pilih channel', wand:'Magic Wand', color:'Select Color',
    fill:'Fill', object:'Select Object', all:'Select All', inverse:'Inverse',
    contract:'Contract', expand:'Expand', apply:'Apply', clear:'Clear', desel:'Deselect',
    generate:'⬇ Generate PDF',
};
function _actLabel(s){
    let l = ACT_LABELS[s.t] || s.t;
    if(s.t==='ptype') l += ' → ' + s.type.toUpperCase();
    if(s.t==='chan')  l += ' #' + (s.i+1);
    if(s.t==='wand'||s.t==='color') l += ` @(${Math.round(s.rx*100)}%,${Math.round(s.ry*100)}%) tol ${s.tol}`;
    if(s.t==='contract'||s.t==='expand') l += ` ${s.px}px`;
    return l;
}
function _renderRecSteps(){
    const box = document.getElementById('recSteps');
    if(!actionSteps.length){
        box.style.display = 'none';
    } else {
        box.style.display = 'block';
        box.innerHTML = actionSteps.map((s,i)=>`${i+1}. ${_actLabel(s)}`).join('<br>');
        box.scrollTop = box.scrollHeight;
    }
    document.getElementById('batchBtn').disabled = isRecording || !actionSteps.length;
}

function toggleRecord(){
    isRecording = !isRecording;
    const btn = document.getElementById('recBtn');
    if(isRecording){
        actionSteps = [];
        btn.textContent = '■ Stop';
        btn.classList.add('recording');
        const sb = document.getElementById('statusBox');
        sb.className = 'status-box';
        sb.textContent = 'Merekam… lakukan seleksi lalu klik Generate untuk merekam langkah export. (Goresan brush tidak direkam.)';
    } else {
        btn.textContent = '● Rekam';
        btn.classList.remove('recording');
        const sb = document.getElementById('statusBox');
        sb.className = 'status-box ok';
        sb.textContent = `Rekaman selesai: ${actionSteps.length} langkah. Klik "Terapkan ke Banyak File".`;
    }
    _renderRecSteps();
}
function clearRecording(){
    actionSteps = [];
    if(isRecording) toggleRecord();
    _renderRecSteps();
}

// ═══ HEADLESS BATCH ENGINE ═══════════════════════════════════════════════════
// Menjalankan action ke banyak file TANPA menampilkan gambar di editor.
// Semua operasi dilakukan pada canvas offscreen + array biner murni.

// Muat file → data piksel offscreen + base64 asli (untuk dikirim ke server)
async function _hlLoad(file){
    const dataUrl = await new Promise((res,rej)=>{
        const r=new FileReader(); r.onload=e=>res(e.target.result); r.onerror=()=>rej(new Error('baca gagal')); r.readAsDataURL(file);
    });
    const img = await new Promise((res,rej)=>{
        const im=new Image(); im.onload=()=>res(im); im.onerror=()=>rej(new Error('decode gagal')); im.src=dataUrl;
    });
    const c=document.createElement('canvas'); c.width=img.naturalWidth; c.height=img.naturalHeight;
    c.getContext('2d').drawImage(img,0,0);
    const src = c.getContext('2d').getImageData(0,0,c.width,c.height).data;
    return { w:c.width, h:c.height, src, imgB64:dataUrl.split(',')[1], imageName:file.name };
}

function _hlWhite(S){
    if(S.white) return S.white;
    const n=S.w*S.h, wm=new Uint8Array(n), d=S.src;
    for(let i=0;i<n;i++){ const p=i*4; if(d[p]>=245&&d[p+1]>=245&&d[p+2]>=245) wm[i]=1; }
    S.white=wm; return wm;
}

function _hlBuildChannels(S, type){
    const prev={}; (S.channels||[]).forEach(c=>prev[c.name]=c.drawn);
    S.productType=type;
    S.channels=TYPE_CHANNELS[type].map(([name,mode])=>({name,mode,drawn:prev[name]||null}));
    S.active=0;
}

function _hlFlood(S, sx, sy, match){
    const w=S.w,h=S.h,n=w*h;
    const visited=new Uint8Array(n), sel=new Uint8Array(n), stack=new Int32Array(n);
    let sp=0; const seed=sy*w+sx; stack[sp++]=seed; visited[seed]=1;
    while(sp>0){
        const i=stack[--sp];
        if(!match(i*4)) continue;
        sel[i]=1;
        const x=i%w, y=(i/w)|0;
        if(x>0&&!visited[i-1]){visited[i-1]=1;stack[sp++]=i-1;}
        if(x<w-1&&!visited[i+1]){visited[i+1]=1;stack[sp++]=i+1;}
        if(y>0&&!visited[i-w]){visited[i-w]=1;stack[sp++]=i-w;}
        if(y<h-1&&!visited[i+w]){visited[i+w]=1;stack[sp++]=i+w;}
    }
    return sel;
}

function _hlMerge(S, newSel, s){
    let mask=newSel;
    if(s.solid) mask=_fillHoles(mask, S.w, S.h);
    const mode=s.mode||'new';
    if(mode==='add' && S.sel){ for(let i=0;i<mask.length;i++) if(mask[i]) S.sel[i]=1; }
    else if(mode==='subtract' && S.sel){ for(let i=0;i<mask.length;i++) if(mask[i]) S.sel[i]=0; }
    else S.sel=mask;
}

function _hlMorph(S, n, expand, exw){
    if(!S.sel) return;
    const w=S.w,h=S.h;
    const wm = exw ? _hlWhite(S) : null;
    let base=S.sel;
    if(expand && exw){   // putih bukan sumber ekspansi
        base=new Uint8Array(w*h);
        for(let i=0;i<w*h;i++) base[i]=(S.sel[i]&&!wm[i])?1:0;
    }
    const tmp=new Uint8Array(w*h), res=new Uint8Array(w*h);
    const seed = expand?0:1;   // dilation start 0, erosion start 1
    // horizontal
    for(let y=0;y<h;y++) for(let x=0;x<w;x++){
        let v=seed;
        for(let dx=-n;dx<=n;dx++){ const nx=x+dx;
            if(expand){ if(nx>=0&&nx<w&&base[y*w+nx]){v=1;break;} }
            else { if(nx<0||nx>=w||!base[y*w+nx]){v=0;break;} }
        }
        tmp[y*w+x]=v;
    }
    // vertical
    for(let x=0;x<w;x++) for(let y=0;y<h;y++){
        let v=seed;
        for(let dy=-n;dy<=n;dy++){ const ny=y+dy;
            if(expand){ if(ny>=0&&ny<h&&tmp[ny*w+x]){v=1;break;} }
            else { if(ny<0||ny>=h||!tmp[ny*w+x]){v=0;break;} }
        }
        res[y*w+x]=v;
    }
    if(exw){ for(let i=0;i<w*h;i++) if(wm[i]) res[i]=S.sel[i]; }  // putih beku
    S.sel=res;
}

function _hlApply(S){
    if(!S.sel) return;
    const ch=S.channels[S.active]; if(!ch) return;
    if(!ch.drawn) ch.drawn=new Uint8Array(S.w*S.h);
    for(let i=0;i<S.sel.length;i++) if(S.sel[i]) ch.drawn[i]=1;
    S.sel=null;
}

function _maskArrToB64(arr, w, h){
    const c=document.createElement('canvas'); c.width=w; c.height=h;
    const x=c.getContext('2d'); const id=x.createImageData(w,h);
    for(let i=0;i<w*h;i++){ const v=arr&&arr[i]?255:0; const p=i*4; id.data[p]=id.data[p+1]=id.data[p+2]=v; id.data[p+3]=255; }
    x.putImageData(id,0,0);
    return c.toDataURL('image/png').split(',')[1];
}

function _hlPayload(S){
    const out=[];
    for(const ch of S.channels){
        if(!ch.drawn) continue;
        let has=false; for(let i=0;i<ch.drawn.length;i+=8){ if(ch.drawn[i]){has=true;break;} }
        if(!has) continue;
        out.push({name:ch.name, mode:ch.mode, mask:_maskArrToB64(ch.drawn, S.w, S.h)});
    }
    return out;
}

// Terapkan satu langkah action ke state headless. Return 'generate' bila step export.
function _hlStep(S, s){
    const w=S.w, h=S.h;
    switch(s.t){
        case 'ptype':  _hlBuildChannels(S, s.type); break;
        case 'chan':   if(s.i>=0 && s.i<S.channels.length) S.active=s.i; break;
        case 'wand':   { const sx=Math.round(s.rx*w), sy=Math.round(s.ry*h);
                         _hlMerge(S, _hlFlood(S, sx, sy, _makeMatcher(S.src,(sy*w+sx)*4,s.tol)), s); break; }
        case 'color':  { const sx=Math.round(s.rx*w), sy=Math.round(s.ry*h);
                         const m=_makeMatcher(S.src,(sy*w+sx)*4,s.tol); const ns=new Uint8Array(w*h);
                         for(let i=0;i<w*h;i++) if(m(i*4)) ns[i]=1; _hlMerge(S, ns, s); break; }
        case 'fill':   { const sx=Math.round(s.rx*w), sy=Math.round(s.ry*h);   // fill = seleksi kontigu warna bg lalu commit
                         _hlMerge(S, _hlFlood(S, sx, sy, _makeMatcher(S.src,(sy*w+sx)*4, 30)), {mode:s.mode}); _hlApply(S); break; }
        case 'object': { const ns=new Uint8Array(w*h); for(let i=0;i<w*h;i++) if(S.src[i*4+3]>=128) ns[i]=1;
                         _hlMerge(S, ns, s); break; }
        case 'all':    S.sel=new Uint8Array(w*h).fill(1); break;
        case 'inverse':{ if(!S.sel) S.sel=new Uint8Array(w*h).fill(1);
                         else for(let i=0;i<S.sel.length;i++) S.sel[i]=S.sel[i]?0:1; break; }
        case 'contract': _hlMorph(S, s.px||2, false, !!s.exw); break;
        case 'expand':   _hlMorph(S, s.px||2, true,  !!s.exw); break;
        case 'apply':    _hlApply(S); break;
        case 'clear':    if(S.channels[S.active]) S.channels[S.active].drawn=null; S.sel=null; break;
        case 'desel':    S.sel=null; break;
        case 'generate': return 'generate';
    }
    return null;
}

// ─── Batch: terapkan action ke banyak file (headless) ────────────────────────
document.getElementById('batchInput').addEventListener('change', async function(e){
    const files = Array.from(e.target.files || []);
    e.target.value = '';
    if(!files.length || !actionSteps.length) return;
    if(isRecording) toggleRecord();

    const dpi = parseInt(document.getElementById('dpiInput').value)||300;
    const initType = productType;
    const hasGenStep = actionSteps.some(s=>s.t==='generate');
    const sb = document.getElementById('statusBox');
    const batchBtn = document.getElementById('batchBtn');
    batchBtn.disabled = true;
    let ok=0, fail=0;
    const produced=[];   // nama-nama PDF hasil → dibundel jadi 1 ZIP di akhir

    for(let fi=0; fi<files.length; fi++){
        const f=files[fi];
        try{
            sb.className='status-box';
            sb.textContent=`[${fi+1}/${files.length}] ${f.name}: memuat…`;
            await new Promise(r=>setTimeout(r,0));

            const S = await _hlLoad(f);
            _hlBuildChannels(S, initType);

            sb.textContent=`[${fi+1}/${files.length}] ${f.name}: proses ${actionSteps.length} langkah…`;
            await new Promise(r=>setTimeout(r,0));

            let exported=false;
            for(const s of actionSteps){
                if(_hlStep(S, s)==='generate'){
                    const chans=_hlPayload(S);
                    // doDownload=false: jangan unduh per file, kumpulkan saja
                    if(chans.length){ const d=await _sendSpotColor(S.imgB64, S.imageName, chans, dpi, false); produced.push(d.filename); exported=true; }
                }
            }
            // bila action tak punya step Generate, export sekali di akhir
            if(!hasGenStep){
                const chans=_hlPayload(S);
                if(chans.length){ const d=await _sendSpotColor(S.imgB64, S.imageName, chans, dpi, false); produced.push(d.filename); exported=true; }
            }
            if(exported) ok++; else fail++;
        }catch(err){
            fail++;
            console.error('Batch gagal:', f.name, err);
        }
    }

    // Unduh SEKALI sebagai ZIP → tidak ada dialog Save As beruntun
    if(produced.length){
        sb.className='status-box';
        sb.textContent=`Mengemas ${produced.length} PDF ke ZIP…`;
        try{ await _downloadZip(produced); }
        catch(err){ console.error(err); }
    }
    sb.className = fail ? 'status-box err' : 'status-box ok';
    sb.textContent = `Batch selesai: ${ok} berhasil${fail?', '+fail+' gagal/kosong':''} dari ${files.length} file. `
        + (produced.length ? `ZIP berisi ${produced.length} PDF diunduh.` : '');
    batchBtn.disabled = false;
});

// ═══ DIALOG BATCH FILES ══════════════════════════════════════════════════════
let bmFiles = [];        // [{path,name,dir,size,has_pdf}]
let bmPreset = 'dtf';
let bmRunning = false, bmCancelled = false;

function openBatchDialog(){
    document.getElementById('batchModal').classList.add('open');
    const last = localStorage.getItem('autoPath') || '';
    const inp = document.getElementById('bmPath');
    if(!inp.value) inp.value = last;
    inp.focus();
}
function closeBatchDialog(){
    if(bmRunning){
        bmCancelled = true;                     // hentikan setelah file berjalan selesai
        document.getElementById('bmTotalTxt').textContent = 'Membatalkan…';
        return;
    }
    document.getElementById('batchModal').classList.remove('open');
}
function bmSetPreset(p){
    bmPreset = p;
    document.querySelectorAll('.bm-seg-b').forEach(b=>b.classList.toggle('active', b.dataset.preset===p));
}
function _fmtSize(b){
    if(b >= 1048576) return (b/1048576).toFixed(1)+' MB';
    if(b >= 1024)    return (b/1024).toFixed(0)+' KB';
    return b+' B';
}
function _fmtDur(ms){
    const s = ms/1000;
    return s < 60 ? s.toFixed(1)+'s' : Math.floor(s/60)+'m '+Math.round(s%60)+'s';
}
function _fmtClock(d){ return d.toLocaleTimeString('id-ID',{hour12:false}); }

async function bmScan(){
    if(bmRunning) return;
    const path = document.getElementById('bmPath').value.trim();
    if(!path) return;
    localStorage.setItem('autoPath', path);
    const rec = document.getElementById('bmRecursive').checked ? '1' : '0';
    const list = document.getElementById('bmList');
    list.innerHTML = '<div class="bm-empty"><span class="bm-spin"></span> Mencari file PNG…</div>';
    try{
        const r = await fetch(`/api/spot-color-scan?path=${encodeURIComponent(path)}&recursive=${rec}`);
        const d = await r.json();
        if(d.status !== 'success') throw new Error(d.message||'gagal');
        bmFiles = d.files || [];
        bmResetProgress();
        bmRenderList();
    }catch(e){
        bmFiles = [];
        list.innerHTML = `<div class="bm-empty" style="color:#c62828">${e.message}</div>`;
        document.getElementById('bmCount').textContent = 'gagal';
        document.getElementById('bmGoBtn').disabled = true;
    }
}

// Tombol '+' → menu: pilih File atau Folder (dialog bawaan Windows dari service Python)
function bmToggleAddMenu(e){
    e.stopPropagation();
    if(bmRunning) return;
    document.getElementById('bmAddMenu').classList.toggle('open');
}
document.addEventListener('click', e=>{
    const m = document.getElementById('bmAddMenu');
    if(m && m.classList.contains('open') && !m.contains(e.target)) m.classList.remove('open');
});

async function bmAddPick(mode){
    document.getElementById('bmAddMenu').classList.remove('open');
    if(bmRunning) return;
    const rec = document.getElementById('bmRecursive').checked ? '1' : '0';
    const list = document.getElementById('bmList');
    const prevHTML = list.innerHTML;
    list.innerHTML = `<div class="bm-empty"><span class="bm-spin"></span> Menunggu dialog ${mode==='folder'?'folder':'file'} Windows…</div>`;
    try{
        const r = await fetch(`/api/pick-files?mode=${mode}&recursive=${rec}`);
        const d = await r.json();
        if(d.status !== 'success') throw new Error(d.message||'gagal');
        if(!d.files.length){
            // dialog dibatalkan, atau folder tanpa PNG
            if(d.folder){
                document.getElementById('bmPath').value = d.folder;
                list.innerHTML = '<div class="bm-empty">Tidak ada file .png di folder itu' +
                                 (rec==='0' ? ' — coba centang <b>sub-folder</b>' : '') + '</div>';
            } else {
                list.innerHTML = prevHTML;
            }
            return;
        }
        if(d.folder){
            document.getElementById('bmPath').value = d.folder;
            localStorage.setItem('autoPath', d.folder);
        }
        const seen = new Set(bmFiles.map(f=>f.path));
        let added = 0;
        for(const f of d.files){ if(!seen.has(f.path)){ bmFiles.push(f); seen.add(f.path); added++; } }
        bmResetProgress();
        bmRenderList();
        document.getElementById('bmCount').textContent =
            `${bmFiles.length} file · ${_bmSelected().length} dipilih · +${added} ditambahkan`;
    }catch(e){
        list.innerHTML = `<div class="bm-empty" style="color:#c62828">${e.message}</div>`;
    }
}

// Tombol 'Clear' → kosongkan daftar, mulai pekerjaan baru
function bmClearList(){
    if(bmRunning) return;
    bmFiles = [];
    bmResetProgress();
    document.getElementById('bmList').innerHTML =
        '<div class="bm-empty">Masukkan path folder lalu klik <b>Cari PNG</b>, atau tekan <b>+</b> untuk memilih file</div>';
    document.getElementById('bmCount').textContent = 'belum ada file';
    document.getElementById('bmAll').checked = false;
    document.getElementById('bmGoBtn').disabled = true;
}

function bmResetProgress(){
    document.getElementById('bmTotalBar').style.width = '0%';
    document.getElementById('bmTotalTxt').textContent = 'Siap';
}

function bmRenderList(){
    const list = document.getElementById('bmList');
    if(!bmFiles.length){
        list.innerHTML = '<div class="bm-empty">Tidak ada file .png di lokasi itu</div>';
        document.getElementById('bmCount').textContent = '0 file';
        document.getElementById('bmGoBtn').disabled = true;
        return;
    }
    list.innerHTML = bmFiles.map((f,i)=>`
        <div class="bm-row" id="bmRow${i}">
            <input type="checkbox" id="bmCb${i}" checked onchange="bmUpdateCount()">
            <span class="bm-nm" title="${f.name}">${f.name}</span>
            <span class="bm-dir" title="${f.dir}">${f.dir}</span>
            <span class="bm-sz">${_fmtSize(f.size)}</span>
            <span class="bm-pbar"><i id="bmBar${i}"></i></span>
            <span class="bm-st" id="bmSt${i}">${f.has_pdf ? 'sudah ada .pdf' : 'siap'}</span>
        </div>`).join('');
    document.getElementById('bmAll').checked = true;
    bmUpdateCount();
}

function bmToggleAll(on){
    bmFiles.forEach((_,i)=>{ const cb=document.getElementById('bmCb'+i); if(cb) cb.checked=on; });
    bmUpdateCount();
}
function _bmSelected(){
    return bmFiles.map((f,i)=>({f,i})).filter(({i})=>{
        const cb=document.getElementById('bmCb'+i); return cb && cb.checked;
    });
}
function bmUpdateCount(){
    const n = _bmSelected().length;
    document.getElementById('bmCount').textContent = `${bmFiles.length} file · ${n} dipilih`;
    document.getElementById('bmGoBtn').disabled = (n===0) || bmRunning;
}

// Progress per file: ramp animasi selama menunggu server (biar tidak terkesan stuck),
// lalu dikunci 100% saat file benar-benar selesai.
function _bmStartRamp(i, estMs){
    const bar = document.getElementById('bmBar'+i);
    const st  = document.getElementById('bmSt'+i);
    const t0  = performance.now();
    const iv = setInterval(()=>{
        const el = performance.now()-t0;
        const pct = Math.min(95, 100*(1 - Math.exp(-el/(estMs*0.55))));  // asimtot ke 95%
        bar.style.width = pct.toFixed(0)+'%';
        st.innerHTML = `<span class="bm-spin"></span>${pct.toFixed(0)}% · ${_fmtDur(el)}`;
    }, 90);
    return iv;
}

async function bmProcess(){
    const sel = _bmSelected();
    if(!sel.length || bmRunning) return;
    bmRunning = true; bmCancelled = false;
    const goBtn = document.getElementById('bmGoBtn');
    const cancelBtn = document.getElementById('bmCancelBtn');
    goBtn.disabled = true; cancelBtn.textContent = 'Stop';
    const totalBar = document.getElementById('bmTotalBar');
    const totalTxt = document.getElementById('bmTotalTxt');

    const contract = parseInt(document.getElementById('bmContract').value) || 0;
    const dpi      = parseInt(document.getElementById('bmDpi').value) || 300;
    const startAt  = new Date();
    const tStart   = performance.now();
    let done=0, okN=0, failN=0, estMs=2500;

    const tick = setInterval(()=>{
        const el = performance.now()-tStart;
        totalTxt.textContent = `${done}/${sel.length} · mulai ${_fmtClock(startAt)} · berjalan ${_fmtDur(el)}`;
    }, 200);

    for(const {f,i} of sel){
        if(bmCancelled){
            document.getElementById('bmSt'+i).textContent = 'dibatalkan';
            continue;
        }
        const row = document.getElementById('bmRow'+i);
        row.classList.remove('done','err');
        row.scrollIntoView({block:'nearest'});
        const fT0 = performance.now();
        const iv = _bmStartRamp(i, estMs);
        try{
            const r = await fetch('/api/spot-color-auto', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({path:f.path, preset:bmPreset, contract_px:contract, dpi})
            });
            const d = await r.json();
            clearInterval(iv);
            const dur = performance.now()-fT0;
            estMs = estMs*0.6 + dur*0.4;          // adaptif untuk estimasi berikutnya
            const first = (d.results||[])[0] || {};
            if(d.status==='success' && first.status==='success'){
                row.classList.add('done');
                document.getElementById('bmBar'+i).style.width='100%';
                document.getElementById('bmSt'+i).textContent = `✔ Selesai · ${_fmtDur(dur)}`;
                okN++;
            } else {
                throw new Error(first.message || d.message || 'gagal');
            }
        }catch(err){
            clearInterval(iv);
            row.classList.add('err');
            document.getElementById('bmBar'+i).style.width='100%';
            document.getElementById('bmSt'+i).textContent = '✘ ' + (err.message||'gagal').slice(0,22);
            failN++;
        }
        done++;
        totalBar.style.width = (done/sel.length*100).toFixed(1)+'%';
    }

    clearInterval(tick);
    const total = performance.now()-tStart;
    const endAt = new Date();
    totalTxt.textContent =
        `Selesai ${okN}/${sel.length}${failN?` · ${failN} gagal`:''}` +
        `${bmCancelled?' · dibatalkan':''} · ${_fmtClock(startAt)}–${_fmtClock(endAt)} · total ${_fmtDur(total)}`;
    bmRunning = false;
    cancelBtn.textContent = 'Cancel';
    bmUpdateCount();

    const sb = document.getElementById('statusBox');
    sb.className = failN ? 'status-box err' : 'status-box ok';
    sb.textContent = `Batch ${bmPreset.toUpperCase()}: ${okN} PDF dibuat di folder asal (total ${_fmtDur(total)}).`;
}

// ═══ AUTO PROSES (server-side): Object → Contract → Apply → simpan .pdf ══════
// File dibaca & PDF ditulis langsung oleh service Python di folder yang sama.
async function runAutoServer(preset){
    const last = localStorage.getItem('autoPath') || '';
    const p = prompt(
        'Path file PNG atau FOLDER di server:\n' +
        '(contoh: D:\\Desain\\stiker  atau  D:\\Desain\\a.png)\n' +
        'Hasil A.pdf ditulis di lokasi yang sama.', last);
    if(!p) return;
    localStorage.setItem('autoPath', p);

    const sb = document.getElementById('statusBox');
    sb.className = 'status-box';
    sb.textContent = `Auto ${preset.toUpperCase()} berjalan di server… (Object → Contract → Apply → save)`;
    try{
        const res = await fetch('/api/spot-color-auto', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({
                path: p,
                preset,
                contract_px: parseInt(document.getElementById('modifyPx').value) || 2,
                dpi: parseInt(document.getElementById('dpiInput').value) || 300,
            })
        });
        const d = await res.json();
        if(d.status !== 'success') throw new Error(d.message || 'gagal');
        const rows = (d.results||[]).map(r =>
            `<small>${r.status==='success' ? '✔' : '✘'} ${r.file}` +
            `${r.status==='success' ? ' → '+r.output : ' ('+(r.message||'gagal')+')'}</small>`
        ).join('<br>');
        sb.className = (d.n_success === d.n_files) ? 'status-box ok' : 'status-box err';
        sb.innerHTML = `Auto ${preset.toUpperCase()}: ${d.n_success}/${d.n_files} file berhasil.<br>${rows}`;
    }catch(e){
        sb.className = 'status-box err';
        sb.textContent = 'Auto error: ' + e.message;
    }
}
</script>
</body>
</html>
""")


@app.route("/api/spot-color", methods=["POST"])
def api_spot_color():
    try:
        import base64
        data         = request.get_json(force=True)
        image_b64    = data.get("image")
        image_name   = data.get("image_name", "design.jpg")
        dpi          = int(data.get("dpi", 300))
        channels_raw = data.get("channels", [])

        if not image_b64:
            return jsonify({"status": "error", "message": "image (base64) wajib diisi"}), 400
        if not channels_raw:
            return jsonify({"status": "error", "message": "channels wajib diisi"}), 400

        image_bytes = base64.b64decode(image_b64)
        channels = []
        for ch in channels_raw:
            mb = base64.b64decode(ch["mask"])
            channels.append({"name": ch.get("name", "Spot Color"),
                              "mode": ch.get("mode", "white"),
                              "mask_bytes": mb})

        result = execute("spot_color", {
            "image_bytes": image_bytes,
            "image_name":  image_name,
            "channels":    channels,
            "dpi":         dpi,
        }, timeout_seconds=120)

        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/spot-color-download")
def api_spot_color_download():
    from tasks.spot_color import OUTPUT_DIR
    filename = request.args.get("file", "")
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        return ("Invalid filename", 400)
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return ("File not found", 404)
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype="application/pdf")


def _png_info(fp):
    """Info satu file PNG untuk daftar batch."""
    try:
        sz = os.path.getsize(fp)
    except Exception:
        sz = 0
    return {
        "path": fp,
        "name": os.path.basename(fp),
        "dir":  os.path.dirname(fp),
        "size": sz,
        "has_pdf": os.path.exists(os.path.splitext(fp)[0] + ".pdf"),
    }


def _collect_pngs(path, recursive=False):
    """Kumpulkan file PNG dari sebuah file atau folder."""
    files = []
    if os.path.isfile(path):
        if path.lower().endswith(".png"):
            files.append(path)
    elif os.path.isdir(path):
        if recursive:
            for root, _dirs, fns in os.walk(path):
                for fn in fns:
                    if fn.lower().endswith(".png"):
                        files.append(os.path.join(root, fn))
        else:
            for fn in sorted(os.listdir(path)):
                fp = os.path.join(path, fn)
                if os.path.isfile(fp) and fn.lower().endswith(".png"):
                    files.append(fp)
    return [_png_info(fp) for fp in sorted(files)]


@app.route("/api/pick-files")
def api_pick_files():
    """Dialog bawaan Windows di mesin server: pilih FILE (mode=files) atau
    FOLDER (mode=folder). Dijalankan lewat subprocess agar tkinter tidak
    bentrok dengan thread Flask."""
    import subprocess, sys, json as _json

    mode      = request.args.get("mode", "files")
    recursive = request.args.get("recursive") == "1"

    if mode == "folder":
        code = (
            "import tkinter as tk, json, sys\n"
            "from tkinter import filedialog\n"
            "r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True)\n"
            "p = filedialog.askdirectory(title='Pilih folder berisi file PNG', mustexist=True)\n"
            "r.destroy()\n"
            "sys.stdout.write(json.dumps([p] if p else []))\n"
        )
    else:
        code = (
            "import tkinter as tk, json, sys\n"
            "from tkinter import filedialog\n"
            "r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True)\n"
            "p = filedialog.askopenfilenames(title='Pilih file PNG untuk diproses',\n"
            "        filetypes=[('PNG image','*.png'), ('Semua file','*.*')])\n"
            "r.destroy()\n"
            "sys.stdout.write(json.dumps(list(p)))\n"
        )

    try:
        proc = subprocess.run([sys.executable, "-c", code],
                              capture_output=True, text=True, timeout=300)
        raw = (proc.stdout or "").strip()
        picked = _json.loads(raw) if raw else []
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "Dialog timeout"}), 504
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    if not picked:
        return jsonify({"status": "success", "files": [], "count": 0, "folder": ""})

    if mode == "folder":
        folder = os.path.normpath(picked[0])
        out = _collect_pngs(folder, recursive)
        return jsonify({"status": "success", "files": out,
                        "count": len(out), "folder": folder})

    out = [_png_info(fp) for fp in picked if os.path.isfile(fp)]
    return jsonify({"status": "success", "files": out, "count": len(out), "folder": ""})


@app.route("/api/spot-color-scan")
def api_spot_color_scan():
    """Daftar file PNG di sebuah folder/file di server (path + ukuran)."""
    try:
        path = (request.args.get("path", "") or "").strip().strip('"')
        recursive = request.args.get("recursive") == "1"
        if not path or not os.path.exists(path):
            return jsonify({"status": "error", "message": f"Path tidak ditemukan: {path}"}), 404

        out = _collect_pngs(path, recursive)
        return jsonify({"status": "success", "files": out, "count": len(out)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/spot-color-auto", methods=["POST"])
def api_spot_color_auto():
    """Auto DTF/UV: proses PNG di server (path/folder), PDF ditulis di lokasi sama."""
    try:
        data = request.get_json(force=True) or {}
        result = execute("spot_color", {
            "auto":        True,
            "path":        data.get("path", ""),
            "preset":      data.get("preset", "dtf"),
            "contract_px": int(data.get("contract_px", 2)),
            "dpi":         int(data.get("dpi", 300)),
        }, timeout_seconds=600)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/spot-color-zip", methods=["POST"])
def api_spot_color_zip():
    """Bundel beberapa PDF hasil batch jadi satu ZIP → sekali unduh saja."""
    import io as _io, zipfile
    from tasks.spot_color import OUTPUT_DIR
    try:
        data = request.get_json(force=True) or {}
        files = data.get("files", [])
        if not files:
            return ("No files", 400)
        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            seen = set()
            for fn in files:
                if not fn or ".." in fn or "/" in fn or "\\" in fn:
                    continue
                fp = os.path.join(OUTPUT_DIR, fn)
                if os.path.exists(fp) and fn not in seen:
                    zf.write(fp, arcname=fn)
                    seen.add(fn)
        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name="spot_batch.zip", mimetype="application/zip")
    except Exception as e:
        return (str(e), 500)


@app.route("/ui/api-docs")
def ui_api_docs():
    return render_template_string(r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>API Docs — Printing Agent</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#eef0f3;color:#222}
.topbar{background:#fff;height:52px;padding:0 24px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #e0e0e0;position:sticky;top:0;z-index:20}
.logo{font-size:16px;font-weight:800;color:#1a1a1a}.logo span{color:#0066cc}
.topbar a{margin-left:auto;font-size:12px;color:#0066cc;text-decoration:none;border:1px solid #cfd8e3;padding:5px 12px;border-radius:5px}
.wrap{display:grid;grid-template-columns:220px 1fr;max-width:1200px;margin:0 auto;gap:24px;padding:24px}
@media(max-width:860px){.wrap{grid-template-columns:1fr}}
/* sidebar */
.side{position:sticky;top:76px;align-self:start;background:#fff;border:1px solid #e4e4e4;border-radius:10px;padding:12px;max-height:calc(100vh - 100px);overflow-y:auto}
.side .s-t{font-size:10px;font-weight:700;text-transform:uppercase;color:#999;letter-spacing:.6px;margin:10px 6px 5px}
.side a{display:block;padding:6px 8px;font-size:12.5px;color:#333;text-decoration:none;border-radius:6px}
.side a:hover{background:#f0f5ff;color:#0066cc}
/* main */
.main{min-width:0}
.sec{background:#fff;border:1px solid #e4e4e4;border-radius:12px;padding:22px;margin-bottom:22px;scroll-margin-top:76px}
.sec h2{font-size:17px;display:flex;align-items:center;gap:9px;margin-bottom:4px}
.sec h2 .dot{width:10px;height:10px;border-radius:50%}
.sec > p{font-size:12.5px;color:#777;margin-bottom:14px}
.ep{border:1px solid #e8e8e8;border-radius:9px;margin-top:14px;overflow:hidden}
.ep-h{display:flex;align-items:center;gap:9px;padding:10px 13px;background:#fafbfc;cursor:pointer;user-select:none}
.badge{font-size:10.5px;font-weight:800;padding:3px 9px;border-radius:4px;color:#fff;letter-spacing:.4px;flex-shrink:0}
.badge.POST{background:#2e7d32}.badge.GET{background:#1565c0}
.ep-h code{font-size:12.5px;font-weight:600;color:#1a1a1a}
.ep-h .cv{margin-left:auto;color:#bbb;font-size:11px;transition:transform .15s}
.ep.open .ep-h .cv{transform:rotate(90deg)}
.ep-b{display:none;padding:14px 15px;border-top:1px solid #eee}
.ep.open .ep-b{display:block}
.ep-desc{font-size:12.5px;color:#555;margin-bottom:11px}
.lbl{font-size:10px;font-weight:700;text-transform:uppercase;color:#999;letter-spacing:.6px;margin:13px 0 6px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;padding:6px 8px;background:#f5f7f9;color:#666;font-size:10.5px;text-transform:uppercase;letter-spacing:.4px}
td{padding:6px 8px;border-top:1px solid #f0f0f0;vertical-align:top}
td code{background:#f4f6f8;padding:1px 5px;border-radius:3px;font-size:11.5px;color:#c7254e}
.req{color:#c62828;font-weight:700}.opt{color:#999}
pre{background:#1e2530;color:#d8e0ea;font-size:11.5px;padding:12px;border-radius:7px;overflow-x:auto;line-height:1.55;font-family:Consolas,monospace}
/* tester */
.tester{background:#f6f9fc;border:1px solid #dbe6f0;border-radius:8px;padding:13px;margin-top:13px}
.tester .t-t{font-size:11px;font-weight:800;color:#0066cc;text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.tf{display:grid;grid-template-columns:130px 1fr;gap:7px 10px;align-items:center;margin-bottom:6px}
.tf label{font-size:12px;color:#444}
.tf input[type=text],.tf input[type=number],.tf select,.tester textarea{width:100%;padding:6px 8px;border:1px solid #ccd5de;border-radius:5px;font-size:12px;background:#fff}
.tf input[type=color]{width:44px;height:28px;padding:1px;border:1px solid #ccd5de;border-radius:5px;background:#fff}
.tf input[type=file]{font-size:11.5px}
.tester textarea{font-family:Consolas,monospace;min-height:110px;resize:vertical}
.run{background:#0066cc;color:#fff;border:none;padding:8px 20px;border-radius:6px;font-size:12.5px;font-weight:700;cursor:pointer;margin-top:9px}
.run:hover{background:#0055aa}.run:disabled{background:#9bb8d4;cursor:wait}
.t-out{margin-top:11px;display:none}
.t-meta{font-size:11px;margin-bottom:6px;display:flex;gap:12px}
.t-meta .ok{color:#2e7d32;font-weight:700}.t-meta .err{color:#c62828;font-weight:700}
.t-out pre{max-height:340px;overflow:auto}
.arts{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
.arts a,.arts button{font-size:11.5px;padding:5px 12px;border-radius:5px;border:1px solid #0066cc;color:#0066cc;background:#fff;cursor:pointer;text-decoration:none;font-weight:600}
.arts a:hover,.arts button:hover{background:#eaf3ff}
</style>
</head>
<body>
<div class="topbar">
  <span class="logo">PRINTING<span> AGENT</span> · API Docs</span>
  <a href="/ui">← Menu Utama</a>
</div>
<div class="wrap">
  <nav class="side" id="sideNav"></nav>
  <div class="main" id="mainCol"></div>
</div>

<script>
const HOST = location.origin;

// ─── Definisi dokumentasi ──────────────────────────────────────────────────
const SECTIONS = [
{
 id:'spot-color', title:'Spot Color Tool', color:'#e91e63',
 intro:'Membuat PDF berisi spot color channel terpisah (White / Varnish) di atas artwork. Mask putih = area kena spot, hitam = kosong.',
 eps:[
  {method:'POST', path:'/api/spot-color', ctype:'application/json',
   desc:'Generate PDF spot color multi-channel. Semua binary dikirim base64.',
   params:[
    ['image','string (base64)','wajib','Gambar utama JPG/PNG, di-encode base64'],
    ['image_name','string','opsional','Nama file asli. Default: design.jpg'],
    ['dpi','integer','opsional','Resolusi fisik output. Default: 300'],
    ['channels','array','wajib','Daftar spot channel'],
    ['channels[].name','string','opsional','Nama channel, mis. "White". Default: Spot Color'],
    ['channels[].mode','string','opsional','"white" atau "varnish". Default: white'],
    ['channels[].mask','string (base64)','wajib','PNG grayscale: putih=area spot, hitam=kosong'],
   ],
   curl:`curl -X POST ${HOST}/api/spot-color \\
  -H "Content-Type: application/json" \\
  -d '{
    "image": "<base64-gambar>",
    "image_name": "desain.png",
    "dpi": 300,
    "channels": [
      {"name": "White", "mode": "white", "mask": "<base64-mask-png>"}
    ]
  }'`,
   resp:`{
  "status": "success",
  "filename": "spot_ab12cd34.pdf",
  "n_channels": 1,
  "channels": [{"name": "White", "mode": "white"}]
}`,
   tester:{kind:'spot'}
  },
  {method:'GET', path:'/api/spot-color-download',
   desc:'Download file PDF hasil generate.',
   params:[['file','string (query)','wajib','Nama file dari respons /api/spot-color']],
   curl:`curl -o hasil.pdf "${HOST}/api/spot-color-download?file=spot_ab12cd34.pdf"`,
   tester:{kind:'get', base:'/api/spot-color-download', download:true,
     fields:[['file','text','','nama file, mis. spot_ab12cd34.pdf']]}
  },
 ]
},
{
 id:'image-contour', title:'Image Contour', color:'#ff6f00',
 intro:'Membuat garis potong (CutContour) otomatis dari PNG transparan atau PDF. Output: SVG + PDF dengan spot color CutContour terpisah dari artwork.',
 eps:[
  {method:'POST', path:'/ui/image-contour', ctype:'multipart/form-data',
   desc:'Deteksi kontur objek & hasilkan cut line. Bentuk standar (lingkaran/kotak/rounded-rect) otomatis di-snap ke geometri eksak.',
   params:[
    ['file','file','wajib','PNG (transparan/solid) atau PDF'],
    ['dpi','number','opsional','Resolusi render & ukuran fisik. Default: 300'],
    ['offset_mm','number','opsional','Jarak kontur dari objek (mm). Default: 0'],
    ['smoothing','number','opsional','Kehalusan B-spline. Default: 5000'],
    ['min_area','number','opsional','Buang objek < px² (resolusi asli). Default: 500'],
    ['line_color','string','opsional','Warna garis hex. Default: #ff00c8'],
    ['line_width','number','opsional','Tebal garis px. Default: 1.5'],
    ['max_dim','number','opsional','Resolusi proses. Default: 1400'],
    ['bg_color','string','opsional','Warna bg (PNG tanpa alpha). Auto dari pojok'],
    ['bg_tolerance','number','opsional','Toleransi warna bg. Default: 28'],
   ],
   curl:`curl -X POST ${HOST}/ui/image-contour \\
  -F "file=@stiker.png" -F "dpi=300" -F "offset_mm=1.4" \\
  -F "smoothing=1500" -F "min_area=600"`,
   resp:`{
  "status": "success",
  "loops": 3, "points": 480,
  "svg": "<svg...>", "svg_export": "<svg...>",
  "pdf_base64": "<base64>",
  "width_cm": 10.5, "height_cm": 7.2, "dpi": 300
}`,
   tester:{kind:'multipart', path:'/ui/image-contour', fields:[
    ['file','file','','PNG / PDF'],
    ['dpi','number','300',''],
    ['offset_mm','number','1.4',''],
    ['smoothing','number','1500',''],
    ['min_area','number','600',''],
    ['line_color','color','#ff00c8',''],
    ['line_width','number','0.5',''],
    ['max_dim','number','1400',''],
   ]}
  },
 ]
},
{
 id:'merge-pdf', title:'Merge PDF', color:'#c62828',
 intro:'Menggabungkan dua file PDF menjadi satu.',
 eps:[
  {method:'POST', path:'/ui/merge', ctype:'multipart/form-data',
   desc:'Gabungkan file1 + file2 → output (disimpan di temp server).',
   params:[
    ['file1','file','wajib','PDF pertama'],
    ['file2','file','wajib','PDF kedua'],
    ['output','string','wajib','Nama file hasil, mis. gabungan.pdf'],
   ],
   curl:`curl -X POST ${HOST}/ui/merge \\
  -F "file1=@a.pdf" -F "file2=@b.pdf" -F "output=gabungan.pdf"`,
   resp:`{"status": "success", "output": "C:\\\\...\\\\Temp\\\\gabungan.pdf"}`,
   tester:{kind:'multipart', path:'/ui/merge', fields:[
    ['file1','file','','PDF pertama'],
    ['file2','file','','PDF kedua'],
    ['output','text','gabungan.pdf',''],
   ]}
  },
 ]
},
{
 id:'image-info', title:'Image Info', color:'#00838f',
 intro:'Membaca metadata gambar: dimensi, DPI, color mode, ukuran fisik.',
 eps:[
  {method:'POST', path:'/ui/upload-image', ctype:'multipart/form-data',
   desc:'Upload gambar ke temp server → dapat filepath untuk endpoint lain.',
   params:[['file','file','wajib','JPG/PNG/TIFF/WEBP/BMP']],
   curl:`curl -X POST ${HOST}/ui/upload-image -F "file=@foto.jpg"`,
   resp:`{"status":"success","filepath":"C:\\\\...\\\\draftcalc_xxx.jpg","color_mode":"RGB","bytes":102400}`,
   tester:{kind:'multipart', path:'/ui/upload-image', fields:[['file','file','','Gambar']]}
  },
  {method:'POST', path:'/ui/read-info', ctype:'application/json | multipart',
   desc:'Baca info gambar. Kirim JSON {"filepath": "..."} untuk file di server, atau upload langsung via multipart (field "filepath"/"file").',
   params:[
    ['filepath','string JSON','wajib*','Path absolut file di server'],
    ['filepath','file multipart','wajib*','Alternatif: upload file langsung'],
   ],
   curl:`curl -X POST ${HOST}/ui/read-info \\
  -H "Content-Type: application/json" \\
  -d '{"filepath": "D:\\\\gambar\\\\foto.jpg"}'`,
   resp:`{"status":"success","width_px":3000,"height_px":2000,"dpi":300,"color_mode":"RGB", ...}`,
   tester:{kind:'json', path:'/ui/read-info', fields:[['filepath','text','','path absolut di server']]}
  },
 ]
},
{
 id:'pdf-info', title:'PDF Info', color:'#5e35b1',
 intro:'Membaca metadata & struktur PDF: jumlah halaman, ukuran, gambar di dalamnya.',
 eps:[
  {method:'POST', path:'/ui/read-pdf-info', ctype:'multipart/form-data',
   desc:'Upload PDF langsung, atau kirim JSON {"filepath": "..."} untuk file di server.',
   params:[
    ['filepath','file','wajib*','Upload file PDF (field multipart)'],
    ['filepath','string JSON','wajib*','Alternatif: path di server via body JSON'],
   ],
   curl:`curl -X POST ${HOST}/ui/read-pdf-info -F "filepath=@dokumen.pdf"`,
   resp:`{"status":"success","pages":3,"page_width_mm":210, ...}`,
   tester:{kind:'multipart', path:'/ui/read-pdf-info', fields:[['filepath','file','','File PDF']]}
  },
 ]
},
{
 id:'image-tools', title:'Image Tools', color:'#0066cc',
 intro:'Kumpulan operasi gambar: processing, render CMYK, export master CMYK, imposition PDF. Payload JSON diteruskan langsung ke task engine.',
 eps:[
  {method:'POST', path:'/ui/image-processing', ctype:'application/json',
   desc:'Operasi pemrosesan gambar (resize, convert, dll) sesuai payload task.',
   params:[['(payload)','object','wajib','JSON payload untuk task image_processing']],
   curl:`curl -X POST ${HOST}/ui/image-processing \\
  -H "Content-Type: application/json" -d '{"filepath":"D:\\\\in.jpg", ...}'`,
   tester:{kind:'jsonraw', path:'/ui/image-processing', example:'{\n  "filepath": "D:\\\\gambar\\\\input.jpg"\n}'}
  },
  {method:'POST', path:'/ui/render-cmyk', ctype:'application/json',
   desc:'Render preview CMYK dari gambar.',
   params:[['(payload)','object','wajib','JSON payload untuk task render_cmyk']],
   curl:`curl -X POST ${HOST}/ui/render-cmyk -H "Content-Type: application/json" -d '{...}'`,
   tester:{kind:'jsonraw', path:'/ui/render-cmyk', example:'{\n  "filepath": "D:\\\\gambar\\\\input.jpg"\n}'}
  },
  {method:'POST', path:'/ui/finishing-process', ctype:'application/json',
   desc:'Proses gambar: tambahkan indikator plong, lebihan, dan pesan.',
   params:[['(payload)','object','wajib','JSON payload untuk task finishing_process: {filepath, plong{}, lebihan{}, pesan{}}']],
   curl:`curl -X POST ${HOST}/ui/finishing-process -H "Content-Type: application/json" -d '{...}'`,
   tester:{kind:'jsonraw', path:'/ui/finishing-process', example:'{\n  "filepath": "D:\\\\gambar\\\\input.jpg",\n  "plong": {"enable": true, "jarak_plong_atas": 2, "jarak_plong_bawah": 2, "jarak_plong_kiri": 2, "jarak_plong_kanan": 2, "diameter_lebar": 1},\n  "lebihan": {"enable": true, "all": 2.5},\n  "pesan": {"enable": true, "text": "CONTOH"}\n}'}
  },
  {method:'POST', path:'/ui/export-cmyk-master', ctype:'application/json',
   desc:'Export master CMYK (TIFF/PDF) siap cetak.',
   params:[['(payload)','object','wajib','JSON payload untuk task export_cmyk_master']],
   curl:`curl -X POST ${HOST}/ui/export-cmyk-master -H "Content-Type: application/json" -d '{...}'`,
   tester:{kind:'jsonraw', path:'/ui/export-cmyk-master', example:'{\n  "filepath": "D:\\\\gambar\\\\input.jpg"\n}'}
  },
  {method:'POST', path:'/ui/export-pdf-imposition', ctype:'application/json',
   desc:'Susun imposition beberapa item ke lembar PDF.',
   params:[['(payload)','object','wajib','JSON payload untuk task export_pdf_imposition']],
   curl:`curl -X POST ${HOST}/ui/export-pdf-imposition -H "Content-Type: application/json" -d '{...}'`,
   tester:{kind:'jsonraw', path:'/ui/export-pdf-imposition', example:'{\n  "items": []\n}'}
  },
 ]
},
{
 id:'file-explorer', title:'File Explorer', color:'#455a64',
 intro:'Akses berkas di server: listing folder, stat file, dan info detail (otomatis pakai reader gambar/PDF sesuai ekstensi).',
 eps:[
  {method:'GET', path:'/api/list',
   desc:'Daftar isi folder.',
   params:[['path','string (query)','opsional','Path absolut atau relatif BASE_DIR. Kosong = BASE_DIR']],
   curl:`curl "${HOST}/api/list?path=D:\\\\gambar"`,
   resp:`{"current_path":"D:\\\\gambar","items":[{"name":"a.jpg","type":"file","size":1024,"last_modified":"..."}]}`,
   tester:{kind:'get', base:'/api/list', fields:[['path','text','','path folder']]}
  },
  {method:'GET', path:'/api/stat',
   desc:'Info dasar satu file/folder.',
   params:[['filepath','string (query)','wajib','Path absolut']],
   curl:`curl "${HOST}/api/stat?filepath=D:\\\\gambar\\\\a.jpg"`,
   tester:{kind:'get', base:'/api/stat', fields:[['filepath','text','','path file']]}
  },
  {method:'GET', path:'/api/file-info',
   desc:'Info detail: PDF → reader PDF, gambar → reader gambar, lainnya → ukuran.',
   params:[['filepath','string (query)','wajib','Path absolut']],
   curl:`curl "${HOST}/api/file-info?filepath=D:\\\\dok\\\\file.pdf"`,
   tester:{kind:'get', base:'/api/file-info', fields:[['filepath','text','','path file']]}
  },
 ]
},
{
 id:'finishing-editor', title:'Finishing Editor', color:'#6a1b9a',
 intro:'Memproses gambar JPG dengan indikator produksi cetak: plong (lubang die-cut), lebihan (bleed margin), dan pesan (label teks). Mendukung rotasi, auto-kontras warna, dan bingkai objek.',
 eps:[
  {method:'POST', path:'/ui/finishing-process', ctype:'application/json',
   desc:'Proses gambar finishing: tambahkan plong, lebihan, dan pesan. Output disimpan sebagai <nama>_finishing.jpg di samping file asli.',
   params:[
    ['filepath','string','wajib','Path absolut ke file gambar JPG sumber'],
    ['dpi','number','opsional','DPI gambar. Default: baca dari metadata file, fallback 300'],
    ['image_scale','number','opsional','Skala gambar (%). Default: 100'],
    ['rotation','number','opsional','Rotasi searah jarum jam (0/90/180/270). Default: 0'],
    ['plong','object','opsional','Konfigurasi plong (die-cut holes)'],
    ['plong.enable','boolean','wajib*','Aktifkan plong. Harus true agar plong diproses'],
    ['plong.fold4','boolean','opsional','Jika true, set jumlah tiap sisi = 2 (shortcut Lipat Plong 4)'],
    ['plong.jml_atas','number','opsional','Jumlah lubang sisi atas. Default: 0'],
    ['plong.jml_bawah','number','opsional','Jumlah lubang sisi bawah. Default: 0'],
    ['plong.jml_kiri','number','opsional','Jumlah lubang sisi kiri. Default: 0'],
    ['plong.jml_kanan','number','opsional','Jumlah lubang sisi kanan. Default: 0'],
    ['plong.inset','number','opsional','Jarak lubang dari tepi gambar (cm). Default: 2'],
    ['plong.warna_plong','string','opsional','Warna lubang (hex/nama). Default: White'],
    ['plong.auto_contrast','boolean','opsional','Otomatis pilih hitam/putih berdasarkan background. Default: false'],
    ['plong.bentuk_plong','string','opsional','"circle" atau "square". Default: circle'],
    ['plong.diameter_lebar','number','opsional','Diameter/lebar lubang (cm). Default: 1'],
    ['plong.diameter_panjang','number','opsional','Tinggi lubang kotak (cm). Default: sama diameter_lebar'],
   ],
   curl:`curl -X POST ${HOST}/ui/finishing-process \\
  -H "Content-Type: application/json" \\
  -d '{
    "filepath": "F:\\\\PESANAN\\\\2026\\\\desain.jpg",
    "dpi": 300,
    "rotation": 0,
    "plong": {
      "enable": true,
      "jml_atas": 6, "jml_bawah": 6,
      "jml_kiri": 2, "jml_kanan": 2,
      "inset": 2,
      "warna_plong": "#ffffff",
      "auto_contrast": true,
      "bentuk_plong": "circle",
      "diameter_lebar": 1
    },
    "lebihan": {
      "enable": true,
      "all": 2.5,
      "warna_background": "#ffffff",
      "warna_garis": "#d3d3d3",
      "ukuran_garis": 0.1,
      "bingkai_objek": false,
      "quality": 80
    },
    "pesan": {
      "enable": true,
      "text": "PASAR BUAH - 700x100cm",
      "ukuran": 0.8,
      "warna": "#000000",
      "auto_contrast": true,
      "pos_x": 3, "pos_y": 1,
      "posisi": "horizontal",
      "satu_kiri": false
    }
  }'`,
   resp:`{
  "status": "success",
  "output_path": "F:\\\\PESANAN\\\\2026\\\\desain_finishing.jpg",
  "output_url": "/ui/thumbnail?filepath=F%3A%5CPESANAN%5C2026%5Cdesain_finishing.jpg"
}`,
   tester:{kind:'jsonraw', path:'/ui/finishing-process',
     example:`{
  "filepath": "",
  "dpi": 300,
  "rotation": 0,
  "plong": {
    "enable": true,
    "jml_atas": 2, "jml_bawah": 2,
    "jml_kiri": 2, "jml_kanan": 2,
    "inset": 2,
    "auto_contrast": true,
    "bentuk_plong": "circle",
    "diameter_lebar": 1
  },
  "lebihan": {
    "enable": true,
    "all": 2.5,
    "warna_background": "#ffffff",
    "warna_garis": "#d3d3d3",
    "ukuran_garis": 0.1,
    "bingkai_objek": false,
    "quality": 80
  },
  "pesan": {
    "enable": true,
    "text": "Contoh Pesan",
    "ukuran": 0.8,
    "auto_contrast": true,
    "pos_x": 3, "pos_y": 1,
    "posisi": "horizontal"
  }
}`
   }
  },
 ]
},
{
 id:'finishing-editor-lebihan', title:'Finishing — Lebihan (Bleed)', color:'#6a1b9a',
 intro:'Detail parameter lebihan (bleed margin) pada Finishing Editor.',
 eps:[
  {method:'POST', path:'/ui/finishing-process', ctype:'application/json',
   desc:'Parameter bagian lebihan — menambahkan margin di sekeliling gambar dengan garis putus-putus dan opsional bingkai objek.',
   params:[
    ['lebihan.enable','boolean','wajib*','Aktifkan lebihan. Harus true agar lebihan diproses'],
    ['lebihan.all','number','opsional','Lebihan keliling semua sisi (cm). Default: 2.5'],
    ['lebihan.top','number','opsional','Override sisi atas (cm). Default: sama dengan all'],
    ['lebihan.bottom','number','opsional','Override sisi bawah (cm). Default: sama dengan all'],
    ['lebihan.left','number','opsional','Override sisi kiri (cm). Default: sama dengan all'],
    ['lebihan.right','number','opsional','Override sisi kanan (cm). Default: sama dengan all'],
    ['lebihan.warna_background','string','opsional','Warna background margin (hex/nama). Default: White'],
    ['lebihan.warna_garis','string','opsional','Warna garis putus-putus tepi luar (hex/nama). Default: lightgrey'],
    ['lebihan.ukuran_garis','number','opsional','Tebal garis (cm). Default: 0.1'],
    ['lebihan.bingkai_objek','boolean','opsional','Gambar border di tepi gambar asli (dalam margin). Default: false'],
    ['lebihan.quality','number','opsional','Kualitas JPEG output (1-100). Default: 80'],
   ],
   curl:`curl -X POST ${HOST}/ui/finishing-process \\
  -H "Content-Type: application/json" \\
  -d '{
    "filepath": "F:\\\\PESANAN\\\\2026\\\\desain.jpg",
    "lebihan": {
      "enable": true,
      "all": 2.5,
      "top": 3, "bottom": 3, "left": 2, "right": 2,
      "warna_background": "#ffffff",
      "warna_garis": "#d3d3d3",
      "ukuran_garis": 0.1,
      "bingkai_objek": true,
      "quality": 90
    }
  }'`,
   resp:`{
  "status": "success",
  "output_path": "F:\\\\PESANAN\\\\2026\\\\desain_finishing.jpg",
  "output_url": "/ui/thumbnail?filepath=..."
}`,
   tester:null
  },
 ]
},
{
 id:'finishing-editor-pesan', title:'Finishing — Pesan (Label)', color:'#6a1b9a',
 intro:'Detail parameter pesan (label teks) pada Finishing Editor.',
 eps:[
  {method:'POST', path:'/ui/finishing-process', ctype:'application/json',
   desc:'Parameter bagian pesan — menambahkan teks label di dua posisi (kiri-atas & kanan-bawah). Auto-kontras memilih warna teks berdasarkan background di posisi teks.',
   params:[
    ['pesan.enable','boolean','wajib*','Aktifkan pesan. Harus true agar teks ditambahkan'],
    ['pesan.text','string','wajib*','Isi teks pesan'],
    ['pesan.ukuran','number','opsional','Ukuran font (cm). Default: 0.8'],
    ['pesan.warna','string','opsional','Warna teks (hex/nama). Default: Black. Diabaikan jika auto_contrast=true'],
    ['pesan.auto_contrast','boolean','opsional','Otomatis pilih hitam/putih per posisi. Default: false'],
    ['pesan.pos_x','number','opsional','Offset X dari tepi (cm). Default: 3 (horizontal) / 1 (vertical)'],
    ['pesan.pos_y','number','opsional','Offset Y dari tepi (cm). Default: 1 (horizontal) / 3 (vertical)'],
    ['pesan.posisi','string','opsional','"horizontal" atau "vertical". Default: horizontal'],
    ['pesan.satu_kiri','boolean','opsional','Hanya tampilkan teks di kiri-atas saja (tanpa mirror). Default: false'],
   ],
   curl:`curl -X POST ${HOST}/ui/finishing-process \\
  -H "Content-Type: application/json" \\
  -d '{
    "filepath": "F:\\\\PESANAN\\\\2026\\\\desain.jpg",
    "pesan": {
      "enable": true,
      "text": "PASAR BUAH - 700x100cm",
      "ukuran": 0.8,
      "warna": "#000000",
      "auto_contrast": true,
      "pos_x": 3, "pos_y": 1,
      "posisi": "horizontal",
      "satu_kiri": false
    }
  }'`,
   resp:`{
  "status": "success",
  "output_path": "F:\\\\PESANAN\\\\2026\\\\desain_finishing.jpg",
  "output_url": "/ui/thumbnail?filepath=..."
}`,
   tester:null
  },
 ]
},
];

// ─── Render ────────────────────────────────────────────────────────────────
const esc = s => String(s).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const side = document.getElementById('sideNav');
const main = document.getElementById('mainCol');

SECTIONS.forEach(sec=>{
  side.insertAdjacentHTML('beforeend',
    `<div class="s-t" style="color:${sec.color}">${esc(sec.title)}</div>` +
    sec.eps.map((ep,i)=>`<a href="#${sec.id}-${i}">${ep.method} ${esc(ep.path)}</a>`).join(''));

  let html = `<div class="sec" id="${sec.id}">
    <h2><span class="dot" style="background:${sec.color}"></span>${esc(sec.title)}</h2>
    <p>${esc(sec.intro)}</p>`;
  sec.eps.forEach((ep,i)=>{
    html += `<div class="ep" id="${sec.id}-${i}">
      <div class="ep-h" onclick="this.parentElement.classList.toggle('open')">
        <span class="badge ${ep.method}">${ep.method}</span>
        <code>${esc(ep.path)}</code>
        ${ep.ctype?`<span style="font-size:10px;color:#999">${esc(ep.ctype)}</span>`:''}
        <span class="cv">▶</span>
      </div>
      <div class="ep-b">
        <div class="ep-desc">${esc(ep.desc)}</div>
        <div class="lbl">Parameter</div>
        <table><tr><th>Nama</th><th>Tipe</th><th>Wajib</th><th>Keterangan</th></tr>
        ${ep.params.map(p=>`<tr><td><code>${esc(p[0])}</code></td><td>${esc(p[1])}</td>
          <td class="${p[2]==='wajib'||p[2]==='wajib*'?'req':'opt'}">${esc(p[2])}</td><td>${esc(p[3])}</td></tr>`).join('')}
        </table>
        <div class="lbl">Contoh Request</div>
        <pre>${esc(ep.curl||'')}</pre>
        ${ep.resp?`<div class="lbl">Contoh Response</div><pre>${esc(ep.resp)}</pre>`:''}
        ${ep.tester?`<div class="tester" data-sec="${sec.id}" data-idx="${i}">
          <div class="t-t">⚡ Test API</div>
          <div class="t-fields"></div>
          <button class="run">▶ Kirim Request</button>
          <div class="t-out"><div class="t-meta"></div><pre class="t-json"></pre><div class="arts"></div></div>
        </div>`:''}
      </div>
    </div>`;
  });
  main.insertAdjacentHTML('beforeend', html + '</div>');
});

// ─── Tester engine ─────────────────────────────────────────────────────────
function buildFields(t, box, tester){
  if(tester.kind==='spot'){
    box.innerHTML = `
      <div class="tf"><label>Gambar utama</label><input type="file" data-f="image" accept="image/png,image/jpeg"></div>
      <div class="tf"><label>Mask channel (PNG)</label><input type="file" data-f="mask" accept="image/png"></div>
      <div class="tf"><label>Nama channel</label><input type="text" data-f="name" value="White"></div>
      <div class="tf"><label>Mode</label><select data-f="mode"><option value="white">white</option><option value="varnish">varnish</option></select></div>
      <div class="tf"><label>DPI</label><input type="number" data-f="dpi" value="300"></div>`;
    return;
  }
  if(tester.kind==='jsonraw'){
    box.innerHTML = `<textarea data-f="raw">${esc(tester.example||'{}')}</textarea>`;
    return;
  }
  box.innerHTML = (tester.fields||[]).map(f=>{
    const [name,type,def,ph] = f;
    let inp;
    if(type==='file')   inp = `<input type="file" data-f="${name}">`;
    else if(type==='color') inp = `<input type="color" data-f="${name}" value="${def}">`;
    else if(type==='number') inp = `<input type="number" data-f="${name}" value="${def}" step="any">`;
    else inp = `<input type="text" data-f="${name}" value="${def}" placeholder="${esc(ph||'')}">`;
    return `<div class="tf"><label>${esc(name)}</label>${inp}</div>`;
  }).join('');
}

document.querySelectorAll('.tester').forEach(t=>{
  const sec = SECTIONS.find(s=>s.id===t.dataset.sec);
  const ep  = sec.eps[t.dataset.idx];
  buildFields(t, t.querySelector('.t-fields'), ep.tester);
  t.querySelector('.run').addEventListener('click', ()=>runTest(t, ep));
});

const fileToB64 = f => new Promise((res,rej)=>{
  const r=new FileReader(); r.onload=e=>res(e.target.result.split(',')[1]); r.onerror=rej; r.readAsDataURL(f);
});

function pretty(o){
  return JSON.stringify(o,(k,v)=>(typeof v==='string'&&v.length>300)?v.slice(0,120)+`…(dipotong, ${v.length} chars)`:v,2);
}

async function runTest(t, ep){
  const T = ep.tester, btn = t.querySelector('.run'), out = t.querySelector('.t-out');
  const meta = t.querySelector('.t-meta'), jbox = t.querySelector('.t-json'), arts = t.querySelector('.arts');
  const val = n => { const e=t.querySelector(`[data-f="${n}"]`); return e?e.value:''; };
  const fil = n => { const e=t.querySelector(`[data-f="${n}"]`); return e&&e.files[0]; };
  btn.disabled = true; out.style.display='none'; arts.innerHTML='';
  const t0 = performance.now();
  try{
    let resp;
    if(T.kind==='get'){
      const q = new URLSearchParams();
      (T.fields||[]).forEach(f=>{ if(val(f[0])) q.set(f[0], val(f[0])); });
      const url = T.base + '?' + q.toString();
      if(T.download){ window.open(url); btn.disabled=false; return; }
      resp = await fetch(url);
    } else if(T.kind==='multipart'){
      const fd = new FormData();
      for(const f of (T.fields||[])){
        if(f[1]==='file'){ const file=fil(f[0]); if(file) fd.append(f[0], file); }
        else if(val(f[0])!=='') fd.append(f[0], val(f[0]));
      }
      resp = await fetch(T.path, {method:'POST', body:fd});
    } else if(T.kind==='json'){
      const obj = {};
      (T.fields||[]).forEach(f=>{ if(val(f[0])!=='') obj[f[0]] = val(f[0]); });
      resp = await fetch(T.path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(obj)});
    } else if(T.kind==='jsonraw'){
      let obj; try{ obj = JSON.parse(val('raw')); }catch(e){ throw new Error('JSON tidak valid: '+e.message); }
      resp = await fetch(T.path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(obj)});
    } else if(T.kind==='spot'){
      const img = fil('image'), mask = fil('mask');
      if(!img || !mask) throw new Error('Pilih gambar utama dan mask dulu.');
      const [ib, mb] = await Promise.all([fileToB64(img), fileToB64(mask)]);
      const body = { image: ib, image_name: img.name, dpi: parseInt(val('dpi'))||300,
        channels: [{name: val('name')||'White', mode: val('mode'), mask: mb}] };
      resp = await fetch('/api/spot-color', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    }
    const ms = Math.round(performance.now()-t0);
    const text = await resp.text();
    let json = null; try{ json = JSON.parse(text); }catch(e){}
    meta.innerHTML = `<span class="${resp.ok?'ok':'err'}">HTTP ${resp.status}</span><span style="color:#888">${ms} ms</span>`;
    jbox.textContent = json ? pretty(json) : text.slice(0,3000);
    if(json){
      if(json.pdf_base64) addArt(arts, 'Download PDF', ()=>dlB64(json.pdf_base64,'application/pdf','kontur.pdf'));
      if(json.svg_export) addArt(arts, 'Download SVG', ()=>dlText(json.svg_export,'image/svg+xml','kontur.svg'));
      if(json.filename && /\.pdf$/i.test(json.filename))
        arts.insertAdjacentHTML('beforeend', `<a href="/api/spot-color-download?file=${encodeURIComponent(json.filename)}">Download ${esc(json.filename)}</a>`);
      if(json.filepath) addArt(arts, 'Salin filepath', ()=>navigator.clipboard.writeText(json.filepath));
    }
    out.style.display='block';
  }catch(e){
    meta.innerHTML = `<span class="err">GAGAL</span>`;
    jbox.textContent = e.message;
    out.style.display='block';
  }finally{
    btn.disabled = false;
  }
}
function addArt(box, label, fn){
  const b=document.createElement('button'); b.textContent=label; b.addEventListener('click',fn); box.appendChild(b);
}
function dlB64(b64, mime, name){
  const bin=atob(b64), arr=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) arr[i]=bin.charCodeAt(i);
  dlBlob(new Blob([arr],{type:mime}), name);
}
function dlText(txt, mime, name){ dlBlob(new Blob([txt],{type:mime}), name); }
function dlBlob(blob, name){
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name;
  document.body.appendChild(a); a.click(); a.remove();
}

// buka endpoint dari hash (#spot-color atau #spot-color-0)
if(location.hash){
  const el = document.querySelector(location.hash);
  if(el){
    if(el.classList.contains('ep')) el.classList.add('open');
    else el.querySelector('.ep')?.classList.add('open');
    el.scrollIntoView();
  }
}
</script>
</body>
</html>
    """)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001)
