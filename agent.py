from flask import Flask, request, jsonify, render_template_string, send_file, Response
from executor import execute
from config import AGENT_SECRET, AGENT_ID
import tempfile
import os
import sys
import datetime

# In-memory list of exposed paths (no security restrictions per user request)
EXPOSED_PATHS = []

app = Flask(__name__)

# Simple base directory for the lightweight file explorer (change as needed)
BASE_DIR = r"F:\\Pesanan"


def safe_join(base, path):
    full_path = os.path.abspath(os.path.join(base, path))
    if not full_path.startswith(os.path.abspath(base)):
        raise Exception("Access denied")
    return full_path


# ROOT (simple status)
@app.route("/")
def root():
    return "Printing Agent Running"


@app.route("/ui")
def ui():
    return render_template_string(
        """
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Printing Agent</title>
        <style>
            body{font-family:Segoe UI,Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;color:#fff}
            .container{max-width:900px;margin:0 auto}
            .header{text-align:center;margin-bottom:30px}
            .features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}
            .feature-card{background:#fff;color:#333;padding:30px;border-radius:12px;text-align:center;text-decoration:none}
            .feature-card .feature-icon{font-size:40px;margin-bottom:12px}
            .feature-title{font-weight:700;margin-bottom:8px}
            .feature-desc{color:#666;font-size:13px;margin-bottom:12px}
            .feature-btn{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;padding:10px 16px;border-radius:8px;cursor:pointer}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🖨️ Printing Agent</h1>
                <p>Solusi cerdas untuk kebutuhan printing digital Anda</p>
            </div>
            <div class="features-grid">
                <a href="/ui/merge-form" class="feature-card">
                    <div class="feature-icon">📄</div>
                    <div class="feature-title">Merge PDF</div>
                    <div class="feature-desc">Gabungkan dua atau lebih file PDF menjadi satu dokumen</div>
                    <button class="feature-btn">Mulai</button>
                </a>
                <a href="/ui/read-info-form" class="feature-card">
                    <div class="feature-icon">🖼️</div>
                    <div class="feature-title">Image Info</div>
                    <div class="feature-desc">Lihat informasi lengkap tentang file gambar Anda</div>
                    <button class="feature-btn">Mulai</button>
                </a>
                <a href="/ui/read-pdf-info-form" class="feature-card">
                    <div class="feature-icon">📋</div>
                    <div class="feature-title">PDF Info</div>
                    <div class="feature-desc">Cek jumlah halaman dan preview file PDF</div>
                    <button class="feature-btn">Mulai</button>
                </a>
                <a href="/ui/file-explorer" class="feature-card">
                    <div class="feature-icon">🗂️</div>
                    <div class="feature-title">File Explorer</div>
                    <div class="feature-desc">Jelajahi file dan folder pada server</div>
                    <button class="feature-btn">Buka</button>
                </a>
            </div>
        </div>
    </body>
    """
    )


@app.route("/ui/merge-form")
def merge_form():
    return render_template_string(
        """
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Merge PDF - Printing Agent</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1000px;
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
            
            .card {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .card h2 {
                color: #333;
                margin-bottom: 25px;
                font-size: 20px;
            }
            
            .form-group {
                margin-bottom: 25px;
            }
            
            .form-group label {
                display: block;
                color: #333;
                font-weight: 600;
                margin-bottom: 10px;
                font-size: 14px;
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
                padding: 20px;
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
            
            .file-input-label span {
                color: #667eea;
                font-size: 13px;
            }
            
            .file-name {
                margin-top: 8px;
                padding: 8px;
                background: #f0f2ff;
                border-radius: 5px;
                color: #667eea;
                font-size: 12px;
                text-align: center;
            }
            
            .text-input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                transition: all 0.3s;
            }
            
            .text-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .button-group {
                display: flex;
                gap: 15px;
                margin-top: 30px;
            }
            
            .btn {
                flex-grow: 1;
                padding: 12px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .btn-primary:hover {
                opacity: 0.9;
                transform: translateY(-2px);
            }
            
            .loading {
                display: none;
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
            
            .success-message {
                background: #efe;
                color: #3c3;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                text-align: center;
                display: none;
            }
            
            .success-message.show {
                display: block;
            }
            
            .error-message {
                background: #fee;
                color: #c33;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                text-align: center;
                display: none;
            }
            
            .error-message.show {
                display: block;
            }
            
            @media (max-width: 768px) {
                .header {
                    flex-direction: column;
                    align-items: flex-start;
                    margin-bottom: 20px;
                }
                
                .button-group {
                    flex-direction: column;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Merge PDF</h1>
                <a href="/ui"><button class="back-btn">← Kembali</button></a>
            </div>
            
            <div class="card">
                <h2>Gabungkan File PDF</h2>
                <form id="mergeForm">
                    <div class="form-group">
                        <label>File PDF Pertama</label>
                        <div class="file-input-wrapper">
                            <input type="file" id="file1" accept=".pdf" required>
                            <label for="file1" class="file-input-label">
                                <span>📄 Pilih file PDF atau drag & drop</span>
                            </label>
                            <div class="file-name" id="fileName1" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>File PDF Kedua</label>
                        <div class="file-input-wrapper">
                            <input type="file" id="file2" accept=".pdf" required>
                            <label for="file2" class="file-input-label">
                                <span>📄 Pilih file PDF atau drag & drop</span>
                            </label>
                            <div class="file-name" id="fileName2" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="output">Nama File Output</label>
                        <input type="text" id="output" class="text-input" placeholder="merged.pdf" value="merged.pdf" required>
                    </div>
                    
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>Memproses PDF...</p>
                    </div>
                    
                    <div class="success-message" id="successMsg">
                        ✓ File berhasil digabungkan! File tersimpan di folder temp.
                    </div>
                    
                    <div class="error-message" id="errorMsg"></div>
                    
                    <div class="button-group">
                        <button type="submit" class="btn btn-primary">Gabungkan PDF</button>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            const form = document.getElementById('mergeForm');
            const file1Input = document.getElementById('file1');
            const file2Input = document.getElementById('file2');
            const outputInput = document.getElementById('output');
            
            // Update file names
            file1Input.addEventListener('change', (e) => {
                if (e.target.files[0]) {
                    document.getElementById('fileName1').textContent = '✓ ' + e.target.files[0].name;
                    document.getElementById('fileName1').style.display = 'block';
                }
            });
            
            file2Input.addEventListener('change', (e) => {
                if (e.target.files[0]) {
                    document.getElementById('fileName2').textContent = '✓ ' + e.target.files[0].name;
                    document.getElementById('fileName2').style.display = 'block';
                }
            });
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const file1 = file1Input.files[0];
                const file2 = file2Input.files[0];
                
                if (!file1 || !file2) {
                    showError('Pilih kedua file PDF');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file1', file1);
                formData.append('file2', file2);
                formData.append('output', outputInput.value || 'merged.pdf');
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('successMsg').classList.remove('show');
                document.getElementById('errorMsg').classList.remove('show');
                
                try {
                    const response = await fetch('/ui/merge', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    document.getElementById('loading').style.display = 'none';
                    
                    if (data.status === 'success') {
                        document.getElementById('successMsg').classList.add('show');
                        form.reset();
                        document.getElementById('fileName1').style.display = 'none';
                        document.getElementById('fileName2').style.display = 'none';
                    } else {
                        showError(data.message || 'Terjadi kesalahan');
                    }
                } catch (error) {
                    document.getElementById('loading').style.display = 'none';
                    showError(error.message);
                }
            });
            
            function showError(message) {
                const errorEl = document.getElementById('errorMsg');
                errorEl.textContent = '❌ ' + message;
                errorEl.classList.add('show');
            }
            
            // Drag & drop
            ['file1', 'file2'].forEach(id => {
                const fileInput = document.getElementById(id);
                const label = fileInput.nextElementSibling;
                
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    label.addEventListener(eventName, preventDefaults);
                });
                
                label.addEventListener('drop', (e) => {
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        fileInput.files = files;
                        fileInput.dispatchEvent(new Event('change'));
                    }
                });
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
        </script>
    </body>
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
                body{font-family:Segoe UI,Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;color:#fff}
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
                .btn{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;padding:8px 10px;border-radius:6px;cursor:pointer}
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
                                                        <button id="modalCloseBtn" style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;padding:6px 10px;border-radius:6px;cursor:pointer">Close</button>
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
                                const img = document.createElement('img'); img.src = url; img.style.maxWidth='100%'; img.style.height='auto'; img.style.maxHeight='380px'; preview.appendChild(img);
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
                                          <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;padding:20px;border-radius:8px;margin-bottom:20px">
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
                                          <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;padding:20px;border-radius:8px">
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
                body{font-family:Segoe UI,Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;color:#fff}
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
                    <div><a href="/ui"><button style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;padding:6px 10px;border-radius:6px">Close</button></a></div>
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
    <style>body{font-family:Segoe UI,Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#333;padding:20px}.card{background:#fff;padding:16px;border-radius:8px;max-width:900px;margin:0 auto;box-shadow:0 8px 30px rgba(0,0,0,0.12)}.entry{display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #f0f0f0}</style>
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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


# @app.route("/ui/read-info", methods=["POST"])
# def ui_read_info():
#     try:
#         filepath = request.json.get("filepath")

#         if not filepath:
#             return jsonify({"status": "error", "message": "Missing file"}), 400

#         # Create temp directory
#         temp_dir = tempfile.gettempdir()

#         # Save uploaded file temporarily
#         file_path = os.path.join(temp_dir, filepath.filename)
#         filepath.save(file_path)

#         # Execute read info
#         result = execute("read_info", {"filepath": file_path})

#         return jsonify(result)
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/ui/read-info", methods=["POST"])
def ui_read_info():
    try:
        # Ambil path dari JSON
        filepath = request.json.get("filepath")

        if not filepath:
            return jsonify({"status": "error", "message": "Missing file path"}), 400

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
    return jsonify({"status": "alive", "agent_id": AGENT_ID})


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
