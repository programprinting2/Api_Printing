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
            <title>Printing Agent - Menu</title>
            <style>
                body{font-family:Segoe UI,Arial;background:#667eea;min-height:100vh;padding:30px;color:#fff}
                .card{background:#fff;color:#222;border-radius:10px;padding:20px;max-width:700px;margin:0 auto}
                .title{font-size:22px;margin-bottom:6px}
                .menu{display:flex;flex-direction:column;gap:10px;margin-top:8px}
                .btn{background:#667eea;color:#fff;border:none;padding:12px 16px;border-radius:8px;cursor:pointer;text-align:left}
                .menu a{text-decoration:none}
                .small{color:#666;font-size:13px;margin-bottom:8px}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="title">Printing Agent</div>
                <div class="small">Menu Utama — pilih fitur</div>
                <div class="menu">
                    <a href="/ui/file-explorer"><button class="btn">🗂 File Explorer</button></a>
                    <a href="/ui/image-tools"><button class="btn">🖼 Image Tools</button></a>
                    <a href="/ui/image-contour"><button class="btn">✂ Image Contur</button></a>
                    <a href="/ui/read-info-form"><button class="btn">🖼 Image Info</button></a>
                    <a href="/ui/merge"><button class="btn">📄 Merge PDF</button></a>
                    <a href="/ui/read-pdf-info-form"><button class="btn">🔎 PDF Info</button></a>
                </div>
            </div>
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
                body{font-family:Segoe UI,Arial;background:#667eea;min-height:100vh;padding:20px;color:#fff}
                .card{background:#fff;color:#222;border-radius:8px;padding:18px;max-width:820px;margin:0 auto}
                .form-group{margin-bottom:12px}
                .file-input-wrapper{display:flex;align-items:center;gap:8px}
                .file-input-label{background:#f0f0f0;padding:8px 12px;border-radius:6px;cursor:pointer}
                .btn{background:#667eea;color:#fff;border:none;padding:10px 12px;border-radius:8px;cursor:pointer}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Merge PDF</h2>
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
                        <a href="/ui" style="margin-left:8px"><button type="button" class="btn" style="background:#999">Kembali</button></a>
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
                body{font-family:Segoe UI,Arial;background:#667eea;min-height:100vh;padding:20px;color:#fff}
                .container{max-width:1200px;margin:0 auto}
                .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}
                .card{background:#fff;color:#333;border-radius:10px;padding:16px;box-shadow:0 10px 30px rgba(0,0,0,0.12)}
                .explorer{display:grid;grid-template-columns:240px 1fr;gap:12px}
                .sidebar{padding:12px;border-right:1px solid #eee}
                .drives{list-style:none;padding:0;margin:0}
                .drives li{padding:8px;border-radius:6px;cursor:pointer}
                .drives li:hover{background:#f0f4ff}
                .pathbar{font-size:13px;color:#666;margin-bottom:8px}
                .toolbar{display:flex;gap:8px;margin-bottom:8px}
                .btn{background:#667eea;color:#fff;border:none;padding:8px 10px;border-radius:6px;cursor:pointer}
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

                        <h1 style="margin:0;color:#fff;font-size:20px">🗂️ File Explorer</h1>
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
                                                        <button id="modalCloseBtn" style="background:#667eea;color:#fff;border:none;padding:6px 10px;border-radius:6px;cursor:pointer">Close</button>
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
                                                    pagesHtml += '<div style="background:#f8f9ff;padding:8px;border-left:3px solid #667eea;margin-bottom:8px;border-radius:4px;font-size:11px">';
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
                                          <div style="background:#667eea;color:white;padding:20px;border-radius:8px;margin-bottom:20px">
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
                                          <div style="background:#667eea;color:white;padding:20px;border-radius:8px">
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
                body{font-family:Segoe UI,Arial;background:#667eea;min-height:100vh;padding:20px;color:#fff}
                .card{background:#fff;color:#333;border-radius:10px;padding:16px;box-shadow:0 10px 30px rgba(0,0,0,0.12);max-width:1100px;margin:0 auto}
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
                    <div><a href="/ui"><button style="background:#667eea;color:#fff;border:none;padding:6px 10px;border-radius:6px">Close</button></a></div>
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
    <style>body{font-family:Segoe UI,Arial;background:#667eea;color:#333;padding:20px}.card{background:#fff;padding:16px;border-radius:8px;max-width:900px;margin:0 auto;box-shadow:0 8px 30px rgba(0,0,0,0.12)}.entry{display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #f0f0f0}</style>
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
            color: #667eea;
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
            background: #667eea;
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
            color: #667eea;
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
                tr.innerHTML = '<td colspan="3" style="color: #667eea; font-weight: 600;">📁 .. (Up)</td>';
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
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #667eea;
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
                color: white;
                font-size: 28px;
            }
            
            .back-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            }
            
            .back-btn:hover {
                background: rgba(255,255,255,0.3);
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
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .upload-card {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
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
                border: 2px dashed #667eea;
                border-radius: 8px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                background: #f8f9ff;
            }
            
            .file-input-label:hover {
                border-color: #764ba2;
                background: #f0f2ff;
            }
            
            .file-input-label p {
                color: #667eea;
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
                background: #667eea;
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
                color: #667eea;
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
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
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
                background: #667eea;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
            }
            
            .pdf-controls button:hover {
                background: #764ba2;
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
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .info-card h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 20px;
            }
            
            .summary-box {
                background: #667eea;
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
                border-left: 4px solid #667eea;
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
                color: #667eea;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
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
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #667eea;
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
                color: white;
                font-size: 28px;
            }
            
            .back-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            }
            
            .back-btn:hover {
                background: rgba(255,255,255,0.3);
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
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
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
                border: 2px dashed #667eea;
                border-radius: 8px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                background: #f8f9ff;
            }
            
            .file-input-label:hover {
                border-color: #764ba2;
                background: #f0f2ff;
            }
            
            .file-input-label p {
                color: #667eea;
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
                color: #667eea;
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
                border-left: 4px solid #667eea;
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
                color: #667eea;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
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
        filepath = request.json.get("filepath")

        if not filepath:
            return jsonify({"status": "error", "message": "Missing file"}), 400

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
        if not filename.endswith(".png"):
            return jsonify({"status": "error", "message": "File harus PNG (.png)"}), 400

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
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #667eea;
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
                color: white;
                font-size: 28px;
            }
            
            .back-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            }
            
            .back-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            
            .content {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
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
                background: #667eea;
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
                border-left: 4px solid #667eea;
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
                border-left: 3px solid #667eea;
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001)
