# Restart Flask printing agent (port 9001)
$port = 9001

# Cari PID yang pakai port 9001
$line = netstat -ano | Select-String ":$port\s" | Select-Object -First 1
if ($line) {
    $procId = $line.ToString().Trim().Split()[-1]
    if ($procId -match '^\d+$' -and [int]$procId -gt 0) {
        Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }
}

# Juga kill semua python yang run agent.py (fallback)
Get-Process -Name "python","python3" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $cmd = (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
        if ($cmd -like "*agent.py*") { $_ | Stop-Process -Force -ErrorAction SilentlyContinue }
    } catch {}
}

Start-Sleep -Milliseconds 300

# Start ulang
Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c python agent.py >> flask_output.log 2>&1" `
    -WorkingDirectory "D:\Api_Printing" `
    -WindowStyle Hidden

Write-Host "[restart_service] Agent restarted at $(Get-Date -Format 'HH:mm:ss')"
