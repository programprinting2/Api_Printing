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
BASE_DIR = r"F:\\PESANAN\2026"


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
    return render_template_string(
        r"""
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>Merge PDF - Printing Agent</title>
            <style>
                body{font-family:'Segoe UI',system-ui,sans-serif;background:#eef0f3;min-height:100vh;padding:20px;color:#222}
                .card{background:#fff;color:#222;border-radius:8px;padding:18px;max-width:820px;margin:0 auto}
                .form-group{margin-bottom:12px}
                .file-input-wrapper{display:flex;align-items:center;gap:8px}
                .file-input-label{background:#f0f0f0;padding:8px 12px;border-radius:6px;cursor:pointer}
                .btn{background:#0066cc;color:#fff;border:none;padding:10px 12px;border-radius:8px;cursor:pointer}
            </style>
        </head>
        <body>
            <div style="max-width:820px;margin:0 auto 16px;display:flex;justify-content:space-between;align-items:center">
                <h1 style="margin:0;color:#1a1a1a;font-size:22px;font-weight:700">📄 Merge PDF</h1>
                <a href="/ui"><button type="button" style="background:#fff;color:#444;border:1px solid #ccc;padding:8px 16px;border-radius:5px;cursor:pointer;font-size:13px">← Kembali</button></a>
            </div>
            <div class="card" style="border:1px solid #e4e4e4">
                <form id="mergeForm">
                    <div class="form-group">
                        <label>File PDF Pertama</label>
                        <div class="file-input-wrapper">
                            <input type="file" id="file1" accept=".pdf" required>
                            <div id="fileName1" style="margin-left:8px;color:#666;display:none"></div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>File PDF Kedua</label>
                        <div class="file-input-wrapper">
                            <input type="file" id="file2" accept=".pdf" required>
                            <div id="fileName2" style="margin-left:8px;color:#666;display:none"></div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="output">Nama File Output</label>
                        <input type="text" id="output" value="merged.pdf" required style="padding:8px;width:100%;box-sizing:border-box;border-radius:6px;border:1px solid #ddd">
                    </div>
                    <div style="margin-top:12px">
                        <button type="submit" class="btn">Gabungkan PDF</button>
                    </div>
                </form>
                <div id="result" style="margin-top:12px"></div>
            </div>

            <script>
                const file1Input = document.getElementById('file1');
                const file2Input = document.getElementById('file2');
                file1Input.addEventListener('change', e => { if(e.target.files[0]){ document.getElementById('fileName1').textContent = e.target.files[0].name; document.getElementById('fileName1').style.display='block'; }});
                file2Input.addEventListener('change', e => { if(e.target.files[0]){ document.getElementById('fileName2').textContent = e.target.files[0].name; document.getElementById('fileName2').style.display='block'; }});

                document.getElementById('mergeForm').addEventListener('submit', async (ev) => {
                    ev.preventDefault();
                    const f1 = file1Input.files[0];
                    const f2 = file2Input.files[0];
                    const output = document.getElementById('output').value || 'merged.pdf';
                    if(!f1 || !f2){ alert('Pilih kedua PDF'); return; }
                    const fd = new FormData(); fd.append('file1', f1); fd.append('file2', f2); fd.append('output', output);
                    const resEl = document.getElementById('result'); resEl.textContent = 'Memproses...';
                    try{
                        const r = await fetch('/ui/merge', { method: 'POST', body: fd });
                        const data = await r.json();
                        if(data.status === 'success'){
                            resEl.innerHTML = 'Berhasil: ' + (data.path || 'file disimpan di temp');
                        } else { resEl.textContent = 'Error: ' + (data.message || 'Terjadi kesalahan'); }
                    }catch(e){ resEl.textContent = 'Error: '+e.message; }
                });
            </script>
        </body>
        </html>
        """
    )


@app.route("/ui/file-explorer")
def ui_file_explorer():
    return render_template_string(
        r"""
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>File Explorer - Printing Agent</title>
            <style>
                body{font-family:'Segoe UI',system-ui,sans-serif;background:#eef0f3;min-height:100vh;padding:20px;color:#222}
                .container{max-width:1200px;margin:0 auto}
                .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}
                .card{background:#fff;color:#333;border-radius:10px;padding:16px;box-shadow:0 2px 10px rgba(0,0,0,0.06);border:1px solid #e4e4e4}
                .explorer{display:grid;grid-template-columns:240px 1fr;gap:12px}
                .sidebar{padding:12px;border-right:1px solid #eee}
                .drives{list-style:none;padding:0;margin:0}
                .drives li{padding:8px;border-radius:6px;cursor:pointer}
                .drives li:hover{background:#f0f4ff}
                .pathbar{font-size:13px;color:#666;margin-bottom:8px}
                .toolbar{display:flex;gap:8px;margin-bottom:8px}
                .btn{background:#0066cc;color:#fff;border:none;padding:8px 10px;border-radius:6px;cursor:pointer}
                table{width:100%;border-collapse:collapse}
                th,td{padding:8px;text-align:left;border-bottom:1px solid #f0f0f0;font-size:13px}
                th{color:#666;font-weight:600}
                tr.row:hover{background:#f8fbff}
                .muted{color:#777;font-size:12px}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div>

                        <h1 style="margin:0;color:#1a1a1a;font-size:22px;font-weight:700">🗂️ File Explorer</h1>
                        <div class="muted" style="margin-top:4px">Browse files under: F:\\Pesanan</div>
                    </div>
                    <div><a href="/ui"><button class="btn">← Kembali</button></a></div>
                </div>

                <div class="card">
                    <div class="explorer">
                        <div class="sidebar">
                            <div class="pathbar">Drives</div>
                            <ul id="drives" class="drives"></ul>
                            <div style="height:12px"></div>
                            <div class="pathbar">Current Path</div>
                            <div id="currentPath" class="muted">/</div>
                        </div>

                        <div style="padding:8px">
                            <div class="toolbar">
                                <button class="btn" id="refreshBtn">Refresh</button>
                                <button class="btn" id="upBtn">Up</button>
                            </div>

                            <div id="listWrap">
                                <table>
                                    <thead>
                                        <tr><th style="width:48%">Name</th><th style="width:12%">Type</th><th style="width:20%">Size</th><th style="width:20%">Modified</th></tr>
                                    </thead>
                                    <tbody id="fileTable"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                let currentPath = "";

                async function loadDrives(){
                    try{
                        const res = await fetch('/ui/drives');
                        const data = await res.json();
                        const el = document.getElementById('drives'); el.innerHTML='';
                        (data.drives||[]).forEach(d=>{
                            const li = document.createElement('li'); li.textContent=d; li.addEventListener('click', ()=>{ loadFolder(d); }); el.appendChild(li);
                        });
                    }catch(e){console.warn(e);} 
                }

                function fmtBytes(n){ if(n===null||n===undefined) return '-'; if(n<1024) return n+' B'; const units=['KB','MB','GB','TB']; let i= -1; do{ n=n/1024; i++; }while(n>=1024 && i<units.length-1); return n.toFixed(1)+' '+units[i]; }

                function fmtDate(s){ return s||'-'; }

                async function loadFolder(path=''){
                    try{
                        const q = '/api/list?path='+encodeURIComponent(path||'');
                        const res = await fetch(q); if(!res.ok){ const t=await res.text(); alert(t); return; }
                        const data = await res.json();
                        currentPath = data.current_path||'';
                        document.getElementById('currentPath').textContent = (currentPath||'\\') ;
                                // normalize display: collapse repeated backslashes
                                try{ document.getElementById('currentPath').textContent = (currentPath||'\\').replace(/\\\\/g, '\\'); }catch(e){ document.getElementById('currentPath').textContent = currentPath||'\\'; }
                        const tbody = document.getElementById('fileTable'); tbody.innerHTML='';

                        if(currentPath){ const upRow = document.createElement('tr'); upRow.className='row'; upRow.innerHTML=`<td colspan="4">⬅️ <strong style="cursor:pointer">.. (Up)</strong></td>`; upRow.addEventListener('click', ()=>{ const parts=currentPath.split('\\\\').filter(Boolean); parts.pop(); loadFolder(parts.join('\\\\')); }); tbody.appendChild(upRow); }

                        (data.items||[]).forEach(it=>{
                            const tr = document.createElement('tr'); tr.className='row';
                            const nameCell = document.createElement('td'); nameCell.style.cursor='pointer';
                            nameCell.innerHTML = (it.type === 'folder' ? '📁 ' : '📄 ') + it.name;
                            const typeCell = document.createElement('td'); typeCell.textContent = it.type;
                            const sizeCell = document.createElement('td'); sizeCell.textContent = fmtBytes(it.size);
                            const modCell = document.createElement('td'); modCell.textContent = it.last_modified||'-';

                            nameCell.addEventListener('dblclick', ()=>{
                                if(it.type==='folder'){
                                    const newPath = currentPath ? currentPath + '\\\\' + it.name : it.name; loadFolder(newPath);
                                } else {
                                    const fp = (currentPath ? currentPath + '\\\\' + it.name : it.name);
                                    previewModalOpen(fp);
                                }
                            });

                            tr.appendChild(nameCell); tr.appendChild(typeCell); tr.appendChild(sizeCell); tr.appendChild(modCell);
                            tbody.appendChild(tr);
                        });
                    }catch(e){ alert(e.message); }
                }

                document.getElementById('refreshBtn').addEventListener('click', ()=>loadFolder(currentPath));
                document.getElementById('upBtn').addEventListener('click', ()=>{ const parts=currentPath.split('\\\\').filter(Boolean); parts.pop(); loadFolder(parts.join('\\\\')); });

                (async function(){ await loadDrives(); await loadFolder(''); })();

                // --- Preview modal ---
                // add pdf.js worker
                const pdfScript = document.createElement('script');
                pdfScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
                document.head.appendChild(pdfScript);

                function createModal(){
                                        if(document.getElementById('previewModal')) return;
                                        const modal = document.createElement('div'); modal.id='previewModal';
                                        modal.style.position='fixed'; modal.style.left=0; modal.style.top=0; modal.style.right=0; modal.style.bottom=0; modal.style.background='rgba(0,0,0,0.5)'; modal.style.display='none'; modal.style.zIndex=9999; modal.style.alignItems='center'; modal.style.justifyContent='center';

                                        // Build modal inner HTML for nicer styling (Informasi & Preview)
                                        modal.innerHTML = `
                                            <div style="width:90%;max-width:1000px;background:#fff;color:#333;border-radius:10px;padding:14px;box-shadow:0 12px 40px rgba(0,0,0,0.25);">
                                                <div style="display:flex;justify-content:space-between;align-items:center;">
                                                    <div>
                                                        <h3 style="margin:0;font-size:18px">Informasi & Preview</h3>
                                                    </div>
                                                    <div style="display:flex;gap:8px;align-items:center;">
                                                        <button id="modalCloseBtn" style="background:#0066cc;color:#fff;border:none;padding:6px 10px;border-radius:6px;cursor:pointer">Close</button>
                                                        <button id="modalXBtn" aria-label="Close" style="background:transparent;border:none;font-size:20px;cursor:pointer">✕</button>
                                                    </div>
                                                </div>
                                                <div style="display:flex;gap:12px;margin-top:12px">
                                                    <div id="modalPreview" style="flex:1;min-height:420px;background:#f5f7ff;border-radius:8px;display:flex;align-items:center;justify-content:center;padding:12px;overflow:auto"></div>
                                                    <div id="modalInfo" style="width:360px;max-height:560px;overflow:auto;padding:6px"></div>
                                                </div>
                                            </div>
                                        `;

                                        document.body.appendChild(modal);
                                        // wire close buttons
                                        document.getElementById('modalCloseBtn').addEventListener('click', ()=>{ modal.style.display='none'; document.getElementById('modalPreview').innerHTML=''; document.getElementById('modalInfo').innerHTML=''; });
                                        document.getElementById('modalXBtn').addEventListener('click', ()=>{ modal.style.display='none'; document.getElementById('modalPreview').innerHTML=''; document.getElementById('modalInfo').innerHTML=''; });
                }

                function previewModalOpen(filepath){
                    createModal();
                    const modal = document.getElementById('previewModal'); modal.style.display='flex';
                    const preview = document.getElementById('modalPreview'); const info = document.getElementById('modalInfo');
                    preview.innerHTML = '<div style="color:#666">Loading preview...</div>';
                    info.innerHTML = '';

                      // Close on ESC
                      function escHandler(ev){ if(ev.key === 'Escape'){ modal.style.display='none'; document.removeEventListener('keydown', escHandler); document.getElementById('modalPreview').innerHTML=''; document.getElementById('modalInfo').innerHTML=''; } }
                      document.addEventListener('keydown', escHandler);
                      // override close button to also remove ESC handler
                      const closeBtn = modal.querySelector('button'); if(closeBtn){ closeBtn.onclick = ()=>{ modal.style.display='none'; document.removeEventListener('keydown', escHandler); document.getElementById('modalPreview').innerHTML=''; document.getElementById('modalInfo').innerHTML=''; }; }

                    (async ()=>{
                        try{
                            // prefer using the detailed task-based info endpoint
                            const ires = await fetch('/api/file-info?filepath='+encodeURIComponent(filepath));
                            let infoData = null;
                            if(ires.ok){ infoData = await ires.json(); }

                            const displayPath = filepath.replace(/\\\\/g, '\\');
                            info.innerHTML += `<div style="display:flex;justify-content:space-between;align-items:center"><div><h3 style=\"margin:0\">Preview</h3><div style=\"font-size:12px;color:#666;word-break:break-all\">${displayPath}</div></div></div>`;

                            const ext = filepath.split('.').pop().toLowerCase();
                            const url = '/ui/read-file?filepath='+encodeURIComponent(filepath);

                            if(['jpg','jpeg','png','gif','webp','bmp'].includes(ext)){
                                // image
                                preview.innerHTML = '';
                                const img = document.createElement('img');
                                img.src = url;
                                img.style.width = 'auto';
                                img.style.maxWidth = '100%';
                                img.style.height = 'auto';
                                img.style.maxHeight = '380px';
                                img.style.objectFit = 'contain';
                                preview.appendChild(img);
                                img.onload = ()=>{
                                    if(infoData && infoData.status === 'success'){
                                        // Grid format matching requested UI
                                        info.innerHTML = `
                                          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">Dimensi (PX)</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${infoData.dimensions || (img.naturalWidth+'x'+img.naturalHeight)}</div>
                                            </div>
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">Lebar (CM)</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${infoData.width_cm || '-'}</div>
                                            </div>
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">Tinggi (CM)</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${infoData.height_cm || '-'}</div>
                                            </div>
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">DPI</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${infoData.dpi || '-'}</div>
                                            </div>
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">Mode Warna</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${infoData.color_mode || 'Unknown'}</div>
                                            </div>
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">Ukuran (BYTES)</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${infoData.size_bytes || '-'}</div>
                                            </div>
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">Ukuran (MB)</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${infoData.size_mb || '-'}</div>
                                            </div>
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">Ukuran (MBPS)</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${infoData.size_megabits || '-'}</div>
                                            </div>
                                          </div>
                                        `;
                                    } else {
                                        info.innerHTML = `
                                          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
                                            <div style="background:#f0f4ff;padding:10px;border-radius:6px;grid-column:1/3">
                                              <div style="font-size:11px;color:#999;text-transform:uppercase;margin-bottom:4px">Dimensi (PX)</div>
                                              <div style="font-size:16px;font-weight:600;color:#333">${img.naturalWidth}×${img.naturalHeight}</div>
                                            </div>
                                          </div>
                                        `;
                                    }
                                };
                            } else if(ext === 'pdf'){
                                // wait for pdfjs
                                const waitPdf = () => new Promise((y, n)=>{ if(window.pdfjsLib) return y(); let i=0; const t=setInterval(()=>{ if(window.pdfjsLib){ clearInterval(t); y(); } if(++i>50){ clearInterval(t); n('pdf.js load timeout'); } },100); });
                                await waitPdf();
                                try{
                                    const pdfRes = await fetch(url);
                                    if(!pdfRes.ok){ throw new Error(`HTTP ${pdfRes.status}: ${await pdfRes.text()}`); }
                                    const arrayBuf = await pdfRes.arrayBuffer();
                                    if(arrayBuf.byteLength === 0){ throw new Error('PDF file is empty'); }
                                    const pdf = await window.pdfjsLib.getDocument({data:arrayBuf}).promise;
                                    const page = await pdf.getPage(1);
                                    // Scale down to fit in modal (max 280px width)
                                    const baseViewport = page.getViewport({scale:1});
                                    const maxWidth = 280;
                                    const scale = maxWidth / baseViewport.width;
                                    const viewport = page.getViewport({scale:scale});
                                    const canvas = document.createElement('canvas'); canvas.width = viewport.width; canvas.height = viewport.height; canvas.style.maxWidth = '100%'; canvas.style.height = 'auto'; canvas.style.borderRadius = '6px'; const ctx = canvas.getContext('2d');
                                    await page.render({canvasContext:ctx, viewport}).promise;
                                    preview.innerHTML = ''; preview.appendChild(canvas);
                                    if(infoData && infoData.status === 'success'){
                                        const displayPath = (infoData.actual_file_path || filepath).replace(/\\\\/g, '\\');
                                        let pagesHtml = '';
                                        if(infoData.pages && infoData.pages.length > 0){
                                            pagesHtml = '<div style="margin-top:15px;max-height:180px;overflow-y:auto">';
                                            pagesHtml += '<h4 style="color:#333;margin-bottom:10px;font-size:12px;font-weight:600">Detail Setiap Halaman</h4>';
                                            infoData.pages.forEach(pg => {
                                                if(!pg.error){
                                                    pagesHtml += '<div style="background:#f8f9ff;padding:8px;border-left:3px solid #0066cc;margin-bottom:8px;border-radius:4px;font-size:11px">';
                                                    pagesHtml += '<div style="font-weight:600;color:#333;margin-bottom:4px">Halaman '+pg.page_num+'</div>';
                                                    pagesHtml += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;color:#666">';
                                                    pagesHtml += '<div>L: <strong>'+pg.width_cm+'</strong>cm</div>';
                                                    pagesHtml += '<div>T: <strong>'+pg.height_cm+'</strong>cm</div>';
                                                    pagesHtml += '</div></div>';
                                                }
                                            });
                                            pagesHtml += '</div>';
                                        }
                                        info.innerHTML = `
                                          <div style="background:#0066cc;color:white;padding:20px;border-radius:8px;margin-bottom:20px">
                                            <div style="margin:10px 0;text-align:center">
                                              <div style="opacity:0.9;font-size:12px;text-transform:uppercase">JALUR FILE</div>
                                              <div style="font-weight:600;font-size:10px;font-family:monospace;word-break:break-all;margin-top:5px">${displayPath}</div>
                                            </div>
                                            <div style="margin:10px 0;padding-top:10px;border-top:1px solid rgba(255,255,255,0.3);text-align:center">
                                              <div style="opacity:0.9;font-size:12px;text-transform:uppercase">JUMLAH HALAMAN</div>
                                              <div style="font-weight:600;font-size:18px;margin-top:5px">${infoData.num_pages}</div>
                                            </div>
                                            <div style="margin:10px 0;text-align:center">
                                              <div style="opacity:0.9;font-size:12px;text-transform:uppercase">MODE WARNA</div>
                                              <div style="font-weight:600;font-size:18px;margin-top:5px">${infoData.color_mode || '-'}</div>
                                            </div>
                                            <div style="margin:10px 0;text-align:center">
                                              <div style="opacity:0.9;font-size:12px;text-transform:uppercase">UKURAN FILE</div>
                                              <div style="font-weight:600;font-size:18px;margin-top:5px">${infoData.file_size_mb || '-'} MB</div>
                                            </div>
                                            ${infoData.size_check !== undefined ? `<div style="margin:10px 0;padding-top:10px;border-top:1px solid rgba(255,255,255,0.3);text-align:center">
                                              <div style="opacity:0.9;font-size:12px;text-transform:uppercase">ERROR SIZE CHECK</div>
                                              <div style="font-weight:600;font-size:18px;margin-top:5px;color:${infoData.size_check ? '#4caf50' : '#ff9800'}">${infoData.size_check ? '✓ TRUE' : '✗ FALSE'}</div>
                                            </div>` : ''}
                                          </div>
                                          ${pagesHtml}
                                        `;
                                    } else {
                                        info.innerHTML = `
                                          <div style="background:#0066cc;color:white;padding:20px;border-radius:8px">
                                            <div style="margin:10px 0;padding-top:10px;border-top:1px solid rgba(255,255,255,0.3);text-align:center">
                                              <div style="opacity:0.9;font-size:12px;text-transform:uppercase">JUMLAH HALAMAN</div>
                                              <div style="font-weight:600;font-size:18px;margin-top:5px">${pdf.numPages}</div>
                                            </div>
                                          </div>
                                        `;
                                    }
                                }catch(e){ preview.innerHTML = '<div style="color:#c33">Failed to render PDF: '+e.message+'</div>'; }
                            } else {
                                preview.innerHTML = '<div style="color:#666">No preview available for this file type.</div>';
                            }
                        }catch(e){ preview.innerHTML = '<div style="color:#c33">'+e.message+'</div>'; }
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
        return jsonify({"error": "Path not found", "path": full_path}), 404

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
// File Dialog Component - Full File Explorer
if (!window.fileDialogComponent) {
    window.fileDialogComponent = true;
    
    // Inject CSS
    const style = document.createElement('style');
    style.textContent = `
        .modal-overlay {
            position: fixed;
            left: 0;
            top: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.6);
            display: none;
            z-index: 10000;
            align-items: center;
            justify-content: center;
        }
        
        .modal-overlay.active {
            display: flex;
        }
        
        .modal-dialog {
            background: white;
            border-radius: 10px;
            width: 90%;
            max-width: 1000px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .modal-header h3 {
            margin: 0;
            font-size: 18px;
            color: #333;
        }
        
        .modal-close {
            background: transparent;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }
        
        .modal-close:hover {
            color: #333;
        }
        
        .modal-body {
            flex: 1;
            overflow: hidden;
            padding: 0;
            display: flex;
        }
        
        .explorer-sidebar {
            width: 220px;
            border-right: 1px solid #e0e0e0;
            padding: 16px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .explorer-main {
            flex: 1;
            padding: 16px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            min-width: 0;
        }
        
        .explorer-drives {
            list-style: none;
            padding: 0;
            margin: 0 0 20px 0;
        }
        
        .explorer-drives li {
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
            color: #333;
            font-size: 13px;
            transition: all 0.2s;
        }
        
        .explorer-drives li:hover {
            background: #e8ecff;
            color: #0066cc;
        }
        
        .sidebar-label {
            font-size: 11px;
            color: #999;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .current-path {
            font-size: 11px;
            color: #666;
            word-break: break-all;
            line-height: 1.3;
        }
        
        .explorer-toolbar {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }
        
        .explorer-toolbar button {
            background: #0066cc;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .explorer-toolbar button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        
        .explorer-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        
        .explorer-table thead {
            position: sticky;
            top: 0;
            background: white;
            z-index: 10;
        }
        
        .explorer-table th {
            padding: 8px;
            text-align: left;
            border-bottom: 2px solid #e0e0e0;
            color: #666;
            font-weight: 600;
            background: white;
        }
        
        .explorer-table td {
            padding: 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .explorer-table tr:hover {
            background: #f8fbff;
        }
        
        .explorer-file-name {
            cursor: pointer;
            color: #333;
            flex: 1;
        }
        
        .explorer-file-name:hover {
            color: #0066cc;
            text-decoration: underline;
        }
        
        .explorer-file-type {
            color: #999;
            font-size: 11px;
        }
        
        .explorer-file-size {
            color: #999;
            text-align: right;
            width: 80px;
        }
        
        .explorer-file-date {
            color: #999;
            width: 130px;
            font-size: 11px;
        }
        
        .explorer-table-container {
            flex: 1;
            overflow: auto;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }
    `;
    document.head.appendChild(style);
    
    // Inject HTML
    const modalHTML = `
        <div class="modal-overlay" id="fileDialogModal">
            <div class="modal-dialog">
                <div class="modal-header">
                    <h3>Pilih File</h3>
                    <button class="modal-close" onclick="closeFileDialog()">✕</button>
                </div>
                <div class="modal-body">
                    <div class="explorer-sidebar">
                        <div class="sidebar-label">Drives</div>
                        <ul class="explorer-drives" id="fileDialogDrives"></ul>
                        
                        <div class="sidebar-label" style="margin-top: 20px;">Current Path</div>
                        <div class="current-path" id="fileDialogCurrentPath">Root</div>
                    </div>
                    <div class="explorer-main">
                        <div class="explorer-toolbar">
                            <button onclick="fileDialogRefresh()">🔄 Refresh</button>
                            <button onclick="fileDialogUpFolder()">⬅️ Up</button>
                        </div>
                        <div class="explorer-table-container">
                            <table class="explorer-table">
                                <thead>
                                    <tr>
                                        <th style="flex: 1;">Name</th>
                                        <th style="width: 80px;">Size</th>
                                        <th style="width: 130px;">Modified</th>
                                    </tr>
                                </thead>
                                <tbody id="fileDialogFileTable"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Global state
    window.fileDialogCurrentPath = "";
    window.fileDialogCallback = null;
    
    // Global functions
    window.openFileDialog = function(callback) {
        window.fileDialogCallback = callback || null;
        document.getElementById('fileDialogModal').classList.add('active');
        fileDialogLoadDrives();
        fileDialogLoadFolder("");
    };
    
    window.closeFileDialog = function() {
        document.getElementById('fileDialogModal').classList.remove('active');
        window.fileDialogCurrentPath = "";
        window.fileDialogCallback = null;
    };
    
    window.fileDialogLoadDrives = async function() {
        try {
            const res = await fetch('/ui/drives');
            const data = await res.json();
            const ul = document.getElementById('fileDialogDrives');
            ul.innerHTML = '';
            
            (data.drives || []).forEach(drive => {
                const li = document.createElement('li');
                li.textContent = drive;
                li.addEventListener('click', () => fileDialogLoadFolder(drive));
                ul.appendChild(li);
            });
        } catch(e) {
            console.error('Error loading drives:', e);
        }
    };
    
    window.fileDialogFormatBytes = function(bytes) {
        if(bytes === null || bytes === undefined) return '-';
        if(bytes < 1024) return bytes + ' B';
        const units = ['KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let i = 0;
        while(size >= 1024 && i < units.length - 1) {
            size /= 1024;
            i++;
        }
        return size.toFixed(1) + ' ' + units[i];
    };
    
    window.fileDialogLoadFolder = async function(path) {
        try {
            const q = '/api/list?path=' + encodeURIComponent(path || '');
            const res = await fetch(q);
            
            if(!res.ok) {
                const msg = await res.text();
                alert('Error: ' + msg);
                return;
            }
            
            const data = await res.json();
            window.fileDialogCurrentPath = data.current_path || '';
            document.getElementById('fileDialogCurrentPath').textContent = window.fileDialogCurrentPath || 'Root';
            
            const tbody = document.getElementById('fileDialogFileTable');
            tbody.innerHTML = '';
            
            // Add up row if not root
            if(window.fileDialogCurrentPath) {
                const tr = document.createElement('tr');
                tr.style.cursor = 'pointer';
                tr.innerHTML = '<td colspan="3" style="color: #0066cc; font-weight: 600;">📁 .. (Up)</td>';
                tr.addEventListener('click', () => {
                    const parts = window.fileDialogCurrentPath.split('\\\\').filter(Boolean);
                    parts.pop();
                    fileDialogLoadFolder(parts.join('\\\\'));
                });
                tbody.appendChild(tr);
            }
            
            // Add files/folders
            (data.items || []).forEach(item => {
                const tr = document.createElement('tr');
                tr.style.cursor = 'pointer';
                
                const isFolder = item.type === 'folder';
                const icon = isFolder ? '📁' : '📄';
                const name = icon + ' ' + item.name;
                
                const nameCell = document.createElement('td');
                nameCell.className = 'explorer-file-name';
                nameCell.textContent = name;
                
                const sizeCell = document.createElement('td');
                sizeCell.className = 'explorer-file-size';
                sizeCell.textContent = isFolder ? '-' : fileDialogFormatBytes(item.size);
                
                const dateCell = document.createElement('td');
                dateCell.className = 'explorer-file-date';
                dateCell.textContent = item.last_modified || '-';
                
                nameCell.addEventListener('click', () => {
                    if(isFolder) {
                        const newPath = window.fileDialogCurrentPath ? window.fileDialogCurrentPath + '\\\\' + item.name : item.name;
                        fileDialogLoadFolder(newPath);
                    } else {
                        // Only allow image files
                        const imageExts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico'];
                        const ext = ('.' + item.name.split('.').pop()).toLowerCase();
                        if(imageExts.includes(ext)) {
                            const filePath = window.fileDialogCurrentPath ? window.fileDialogCurrentPath + '\\\\' + item.name : item.name;
                            if(window.fileDialogCallback) {
                                window.fileDialogCallback(filePath);
                            }
                            closeFileDialog();
                        } else {
                            alert('Hanya file gambar yang bisa dipilih (.jpg, .png, .gif, .bmp, .webp, dll)');
                        }
                    }
                });
                
                tr.appendChild(nameCell);
                tr.appendChild(sizeCell);
                tr.appendChild(dateCell);
                tbody.appendChild(tr);
            });
        } catch(e) {
            alert('Error: ' + e.message);
        }
    };
    
    window.fileDialogRefresh = function() {
        fileDialogLoadFolder(window.fileDialogCurrentPath);
    };
    
    window.fileDialogUpFolder = function() {
        const parts = window.fileDialogCurrentPath.split('\\\\').filter(Boolean);
        parts.pop();
        fileDialogLoadFolder(parts.join('\\\\'));
    };
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

        # Create temp directory
        temp_dir = tempfile.gettempdir()

        # Save uploaded files temporarily
        file1_path = os.path.join(temp_dir, file1.filename)
        file2_path = os.path.join(temp_dir, file2.filename)
        output_path = os.path.join(temp_dir, output)

        file1.save(file1_path)
        file2.save(file2_path)

        # Execute merge
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
        .ctx-sm{background:#e8e8e8;color:#555;border:1px solid #c8c8c8;padding:2px 6px;border-radius:3px;cursor:pointer;font-size:10px;font-weight:700}
        .ctx-sm:hover{background:#d0d0d0;color:#111}
        .ctx-sm.active{background:#0066cc;color:#fff;border-color:#0050aa}
        /* Context sections – show/hide based on active tool */
        .ctx-paint,.ctx-sel,.ctx-always{display:flex;align-items:center;gap:6px}
        .ctx-paint{display:none}
        .ctx-sel{display:none}

        /* ── Canvas Area ────────────────────────────────────────────────────── */
        .canvas-area{flex:1;display:flex;flex-direction:column;overflow:hidden;background:#888}
        /* Ruler grid: corner | H ruler | V ruler | canvas */
        .ruler-wrap{flex:1;display:grid;grid-template-areas:"corner rh" "rv cw";grid-template-columns:20px 1fr;grid-template-rows:20px 1fr;overflow:hidden}
        .ruler-corner{grid-area:corner;background:#4a4a4a;border-right:1px solid #333;border-bottom:1px solid #333}
        #rulerH{grid-area:rh;background:#4a4a4a;border-bottom:1px solid #333;display:block;height:20px;width:100%}
        #rulerV{grid-area:rv;background:#4a4a4a;border-right:1px solid #333;display:block;width:20px;height:100%}
        .canvas-wrap{grid-area:cw;overflow:auto;padding:20px;display:flex;align-items:flex-start;justify-content:flex-start}
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
        .ch-edit-tag{font-size:8.5px;font-weight:800;color:#fff;background:#0066cc;padding:2px 6px;border-radius:8px;letter-spacing:.4px;flex-shrink:0}
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
        .act-batch{width:100%;padding:7px;background:#5e35b1;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:11px;font-weight:700}
        .act-batch:hover{background:#4d2c93}
        .act-batch:disabled{background:#e8e8e8;color:#aaa;cursor:not-allowed}

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
    <span id="imgNameLabel" style="font-size:10px;color:#666;max-width:130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">—</span>
    <div class="topbar-sep"></div>
    <a href="/ui"><button class="tb-action">← Kembali</button></a>
    <span style="flex:1"></span>
    <span id="coordLabel" style="font-size:10px;color:#888;font-variant-numeric:tabular-nums"></span>
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
                <input type="checkbox" id="excludeWhite" style="margin:0">Kecualikan putih
            </label>
            <div class="ctx-sep"></div>
            <button class="ctx-btn" id="applySelBtn" onclick="applySelection()" disabled title="Apply (Enter)">✓ Apply</button>
            <button class="ctx-btn" onclick="deselect()" title="Deselect (Ctrl+D)">✕ Desel</button>
        </div>
        <!-- Always visible -->
        <div class="ctx-always">
            <div class="ctx-sep"></div>
            <button class="ctx-btn" id="undoBtn" onclick="undo()" disabled>
                <svg viewBox="0 0 16 16" fill="currentColor" width="11" height="11"><path fill-rule="evenodd" d="M6.293 1.293a1 1 0 0 1 1.414 1.414L4.414 6H12a4 4 0 0 1 0 8h-2a.5.5 0 0 1 0-1h2a3 3 0 0 0 0-6H4.414l3.293 3.293a1 1 0 0 1-1.414 1.414l-5-5a1 1 0 0 1 0-1.414l5-5z"/></svg>
                Undo
            </button>
            <button class="ctx-btn" id="redoBtn" onclick="redo()" disabled>
                Redo
                <svg viewBox="0 0 16 16" fill="currentColor" width="11" height="11"><path fill-rule="evenodd" d="M9.707 1.293a1 1 0 0 0-1.414 1.414L11.586 6H4a4 4 0 0 0 0 8h2a.5.5 0 0 0 0-1H4a3 3 0 0 1 0-6h7.586l-3.293 3.293a1 1 0 0 0 1.414 1.414l5-5a1 1 0 0 0 0-1.414l-5-5z"/></svg>
            </button>
            <div class="ctx-sep"></div>
            <button class="ctx-btn" onclick="zoom(1.25)" title="Zoom In (+)">
                <svg viewBox="0 0 14 14" fill="currentColor" width="11" height="11"><path d="M5.5 0a5.5 5.5 0 1 0 3.645 9.652l2.85 2.851.707-.707-2.852-2.851A5.5 5.5 0 0 0 5.5 0zm-4.5 5.5a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0zM5 3.5a.5.5 0 0 1 1 0V5h1.5a.5.5 0 0 1 0 1H6v1.5a.5.5 0 0 1-1 0V6H3.5a.5.5 0 0 1 0-1H5V3.5z"/></svg>
            </button>
            <button class="ctx-btn" onclick="zoom(0.8)" title="Zoom Out (-)">
                <svg viewBox="0 0 14 14" fill="currentColor" width="11" height="11"><path d="M5.5 0a5.5 5.5 0 1 0 3.645 9.652l2.85 2.851.707-.707-2.852-2.851A5.5 5.5 0 0 0 5.5 0zm-4.5 5.5a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0zM3.5 5h4a.5.5 0 0 1 0 1h-4a.5.5 0 0 1 0-1z"/></svg>
            </button>
            <button class="ctx-btn" onclick="fitCanvas()">Fit</button>
            <button class="ctx-btn" onclick="zoom(1,'reset')">1:1</button>
            <button class="ctx-btn" id="gridBtn" onclick="toggleGrid()" title="Tampilkan / sembunyikan grid">
                <svg viewBox="0 0 16 16" fill="currentColor" width="11" height="11"><path d="M0 0h16v16H0V0zm1 1v4h4V1H1zm5 0v4h4V1H6zm5 0v4h4V1h-4zM1 6v4h4V6H1zm5 0v4h4V6H6zm5 0v4h4V6h-4zM1 11v4h4v-4H1zm5 0v4h4v-4H6zm5 0v4h4v-4h-4z"/></svg>
                Grid
            </button>
            <span class="ctx-val" id="zoomLabel" style="min-width:34px">100%</span>
            <div class="ctx-sep"></div>
            <label style="font-size:10px;color:#666">DPI</label>
            <input type="number" id="dpiInput" value="300" min="72" max="1200" style="width:50px;padding:2px 4px;border:1px solid #ccc;border-radius:3px;font-size:10px">
            <div class="ctx-sep"></div>
            <button class="ctx-btn" onclick="clearMask()" style="color:#c33">
                <svg viewBox="0 0 14 14" fill="currentColor" width="11" height="11"><path d="M5.5 2a.5.5 0 0 0-1 0V3H3a.5.5 0 0 0 0 1h8a.5.5 0 0 0 0-1H9V2a.5.5 0 0 0-1 0V3h-2V2zM3.087 5l.59 5.9A1 1 0 0 0 4.67 12h4.66a1 1 0 0 0 .994-.9L10.913 5H3.087z"/></svg>
                Clear
            </button>
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
                <canvas id="gridCanvas" style="position:absolute;top:0;left:0;pointer-events:none"></canvas>
                <canvas id="selCanvas" style="position:absolute;top:0;left:0;pointer-events:none"></canvas>
            </div>
        </div>
        <!-- Popup pengaturan ruler -->
        <div id="rulerPopup">
            <div class="rp-row"><span>Satuan</span>
                <select id="unitSel" onchange="setRulerUnit(this.value)">
                    <option value="px" selected>px</option>
                    <option value="mm">mm</option>
                    <option value="cm">cm</option>
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

        <div class="rp-label">Action <span style="font-weight:400;color:#aaa;text-transform:none;letter-spacing:0">— rekam &amp; terapkan ulang</span></div>
        <div style="display:flex;gap:4px">
            <button class="act-rec" id="recBtn" onclick="toggleRecord()">● Rekam</button>
            <button class="act-clr" id="recClrBtn" onclick="clearRecording()" title="Hapus rekaman">✕</button>
        </div>
        <div id="recSteps" style="font-size:10px;color:#888;max-height:110px;overflow-y:auto;display:none;background:#f8f8f8;border:1px solid #eee;border-radius:4px;padding:5px 7px;line-height:1.7"></div>
        <input type="file" id="batchInput" accept="image/png,image/jpeg" multiple style="display:none">
        <button class="act-batch" id="batchBtn" onclick="document.getElementById('batchInput').click()" disabled title="Pilih beberapa file — action direplay ke tiap file lalu PDF diunduh otomatis">
            &#9654; Terapkan ke Banyak File
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
            clearMaskData();
            _whiteMaskCache = null;   // reset cache mask putih
            undoStack.length = 0; redoStack.length = 0; _updateUndoRedo();
            _initChannels();          // bangun channel sesuai jenis produk
            fitCanvas();
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
    document.getElementById('statusBox').textContent = 'Gambar dimuat. Pilih channel lalu gambar / seleksi areanya.';
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
    const ww = wrap.clientWidth  - 40;
    const wh = wrap.clientHeight - 40;
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
    const gc = document.getElementById('gridCanvas');
    gc.style.width  = w + 'px';
    gc.style.height = h + 'px';
    document.getElementById('zoomLabel').textContent = Math.round(zoomLevel*100)+'%';
    drawRulers();
    drawGrid();
}

// ─── Mouse Wheel Zoom (acuan di titik kursor) ────────────────────────────────
document.getElementById('canvasWrap').addEventListener('wheel', e=>{
    if(!imageObj) return;
    e.preventDefault();
    const wrap = document.getElementById('canvasWrap');
    const rect = wrap.getBoundingClientRect();
    const PAD = 20;  // padding di dalam canvas-wrap sebelum canvasContainer
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
    drawRulers();
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
    const PAD = 20; // padding in canvas-wrap

    _drawHRuler(rulerH, scrollL, PAD);
    _drawVRuler(rulerV, scrollT, PAD);
}

// ─── Satuan ruler ────────────────────────────────────────────────────────────
let rulerUnit = 'px';   // 'px' | 'mm' | 'cm' | 'm'

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
document.getElementById('canvasWrap').addEventListener('scroll', ()=>{ drawRulers(); }, {passive:true});
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

function drawGrid(){
    if(!imageObj) return;
    const w = bgCanvas.width, h = bgCanvas.height;
    if(gridCanvas.width !== w || gridCanvas.height !== h){
        gridCanvas.width = w; gridCanvas.height = h;
    }
    gridCtx.clearRect(0,0,w,h);
    if(!showGrid) return;
    const { stepPx } = _rulerStepPx();
    const z = Math.max(zoomLevel, 1e-4);
    gridCtx.lineWidth = 1 / z;
    // garis minor
    gridCtx.strokeStyle = 'rgba(0,120,215,0.18)';
    gridCtx.beginPath();
    for(let x = stepPx; x < w; x += stepPx){ gridCtx.moveTo(x, 0); gridCtx.lineTo(x, h); }
    for(let y = stepPx; y < h; y += stepPx){ gridCtx.moveTo(0, y); gridCtx.lineTo(w, y); }
    gridCtx.stroke();
    // garis mayor (tiap 5 step)
    gridCtx.strokeStyle = 'rgba(0,120,215,0.38)';
    gridCtx.beginPath();
    const major = stepPx * 5;
    for(let x = major; x < w; x += major){ gridCtx.moveTo(x, 0); gridCtx.lineTo(x, h); }
    for(let y = major; y < h; y += major){ gridCtx.moveTo(0, y); gridCtx.lineTo(w, y); }
    gridCtx.stroke();
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

window.addEventListener('resize', ()=>{ if(imageObj) drawRulers(); });

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
    drawRulers();
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
            ${i===activeChannel?'<span class="ch-edit-tag">EDIT</span>':''}
        </div>`;
    }).join('');
    document.getElementById('genBtn').disabled = !anyInk;
}

// ─── Generate PDF ────────────────────────────────────────────────────────────
async function generatePDF(){
    if(!imageFile || !imageObj) return;
    _saveActiveChannel();   // simpan channel aktif dulu

    // hanya kirim channel yang ada isinya
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
        // Convert image → base64
        const imgB64 = await new Promise(res=>{
            const rd = new FileReader();
            rd.onload = e => res(e.target.result.split(',')[1]);
            rd.readAsDataURL(imageFile);
        });

        const payload = {
            image: imgB64,
            image_name: imageFile.name,
            dpi,
            channels: payloadChannels
        };

        const res  = await fetch('/api/spot-color', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if(data.status==='success'){
            const chNames = (data.channels||[]).map(c=>c.name).join(', ');
            statusBox.className='status-box ok';
            statusBox.innerHTML = `PDF berhasil!<br><small>${data.filename}</small><br>`
                + `<small>${data.n_channels} channel: ${chNames}</small>`;
            // Langsung download otomatis via anchor (tanpa tombol terpisah)
            const a = document.createElement('a');
            a.href = '/api/spot-color-download?file='+encodeURIComponent(data.filename);
            a.download = data.filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            statusBox.className='status-box err';
            statusBox.textContent='Error: '+(data.message||'Terjadi kesalahan');
        }
    } catch(e){
        statusBox.className='status-box err';
        statusBox.textContent='Error: '+e.message;
    } finally {
        genBtn.innerHTML = '&#11015; Generate &amp; Download PDF';
        _renderChannelList();   // sinkronkan status tombol
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
        sb.textContent = 'Merekam… lakukan seleksi seperti biasa. (Goresan brush tidak direkam.)';
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

// ─── Replay satu langkah (sinkron, tanpa overlay) ────────────────────────────
function replayStep(s){
    const w = drawCanvas.width, h = drawCanvas.height;
    switch(s.t){
        case 'ptype':    setProductType(s.type); break;
        case 'chan':     selectChannel(s.i); break;
        case 'wand':     _applySelOpts(s); magicWand(Math.round(s.rx*w), Math.round(s.ry*h), s.mode); break;
        case 'color':    _applySelOpts(s); selectByColor(Math.round(s.rx*w), Math.round(s.ry*h), s.mode); break;
        case 'fill':     saveHistory(); floodFill(Math.round(s.rx*w), Math.round(s.ry*h), s.mode); recomputeAnts(); break;
        case 'object':   _applySelOpts(s); selMode = s.mode || 'new'; _selectObjectImpl(); break;
        case 'all':      selectAll(); break;
        case 'inverse':  selectInverse(); break;
        case 'contract': document.getElementById('modifyPx').value = s.px;
                         document.getElementById('excludeWhite').checked = !!s.exw;
                         _contractSelectionImpl(); break;
        case 'expand':   document.getElementById('modifyPx').value = s.px;
                         document.getElementById('excludeWhite').checked = !!s.exw;
                         _expandSelectionImpl(); break;
        case 'apply':    if(selectionMask) applySelection(); break;
        case 'clear':    clearMaskData(); if(channels[activeChannel]) channels[activeChannel].img=null; break;
        case 'desel':    deselect(); break;
    }
}

// ─── Batch: terapkan action ke banyak file ───────────────────────────────────
document.getElementById('batchInput').addEventListener('change', async function(e){
    const files = Array.from(e.target.files || []);
    e.target.value = '';
    if(!files.length || !actionSteps.length) return;
    if(isRecording) toggleRecord();

    const sb = document.getElementById('statusBox');
    isReplaying = true;
    let ok = 0, fail = 0;
    try{
        for(let fi = 0; fi < files.length; fi++){
            const f = files[fi];
            try{
                sb.className = 'status-box';
                sb.textContent = `[${fi+1}/${files.length}] ${f.name}: memuat…`;
                await loadImageFile(f);
                await new Promise(r=>requestAnimationFrame(r));

                sb.textContent = `[${fi+1}/${files.length}] ${f.name}: replay ${actionSteps.length} langkah…`;
                for(const s of actionSteps){
                    replayStep(s);
                    await new Promise(r=>requestAnimationFrame(r));   // beri nafas UI
                }
                _saveActiveChannel();
                _renderChannelList();

                sb.textContent = `[${fi+1}/${files.length}] ${f.name}: generate PDF…`;
                await generatePDF();
                ok++;
            }catch(err){
                fail++;
                console.error('Batch gagal untuk', f.name, err);
            }
        }
        sb.className = fail ? 'status-box err' : 'status-box ok';
        sb.textContent = `Batch selesai: ${ok} berhasil${fail ? ', '+fail+' gagal' : ''} dari ${files.length} file.`;
    } finally {
        isReplaying = false;
    }
});
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
        <div class="tester" data-sec="${sec.id}" data-idx="${i}">
          <div class="t-t">⚡ Test API</div>
          <div class="t-fields"></div>
          <button class="run">▶ Kirim Request</button>
          <div class="t-out"><div class="t-meta"></div><pre class="t-json"></pre><div class="arts"></div></div>
        </div>
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
