# WeatherGPT one-click launcher — backend :8000 + frontend :3000.
# Double-click or run: powershell -ExecutionPolicy Bypass -File start-weathergpt.ps1
# Each server runs in its own window. Keep both windows open while using the app.
# Close a window (or Ctrl+C inside it) to stop that server.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logs = Join-Path $root ".logs"
New-Item -ItemType Directory -Path $logs -Force | Out-Null

function Test-PortFree([int]$port) {
    $c = New-Object Net.Sockets.TcpClient
    try {
        $iar = $c.BeginConnect("127.0.0.1", $port, $null, $null)
        $connected = $iar.AsyncWaitHandle.WaitOne(800)
        if ($connected -and $c.Connected) { return $false }
        return $true
    } catch { return $true } finally { $c.Close() }
}

# Backend (skip if something already serves :8000 — e.g. your existing window)
if (Test-PortFree 8000) {
    $be = Join-Path $root "backend"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$be'; python -m uvicorn main:app --host 127.0.0.1 --port 8000" -WorkingDirectory $be
    Write-Output "backend: starting in new window (:8000)"
} else {
    Write-Output "backend: :8000 already in use, leaving it alone"
}

# Frontend (skip if :3000 already serves)
if (Test-PortFree 3000) {
    $fe = Join-Path $root "frontend"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$fe'; npm run dev" -WorkingDirectory $fe
    Write-Output "frontend: starting in new window (:3000)"
} else {
    Write-Output "frontend: :3000 already in use, leaving it alone"
}

Write-Output "Wait ~20s, then open http://localhost:3000/chat"
