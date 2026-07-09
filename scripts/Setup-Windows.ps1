# Setup-Windows.ps1 - set up the TIFFs-to-MP4 app on Windows with a plain Python venv (NO conda) and
# put a "TIFFs to MP4" shortcut on the Desktop.
#
# Run once, from the repo root, in Windows PowerShell:
#     powershell -ExecutionPolicy Bypass -File scripts\Setup-Windows.ps1
#
# Requires Python 3.9+. The venv is self-contained, so the shortcut runs the venv's own pythonw.

# Native tools (py, pip) write to stderr; do NOT let that abort us. We check exit codes and Die.
$ErrorActionPreference = "Continue"
$AppName = "TIFFs to MP4"
$Module  = "tiff2mp4"
$repo = Split-Path $PSScriptRoot -Parent

function Die($msg) { Write-Host ""; Write-Host ("ERROR: " + $msg) -ForegroundColor Red; exit 1 }

# 1. Pick a known-good Python from what's INSTALLED (parse 'py --list').
$pyExe = $null; $pyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $listing = (cmd /c "py --list 2>&1" | Out-String)
    $avail = @()
    foreach ($m in [regex]::Matches($listing, '3\.(1[0-9])')) { $avail += [int]$m.Groups[1].Value }
    $avail = $avail | Sort-Object -Unique
    $pick = @(11, 10, 12, 13) | Where-Object { $avail -contains $_ } | Select-Object -First 1
    if (-not $pick -and $avail.Count -gt 0) { $pick = ($avail | Sort-Object | Select-Object -First 1) }
    if ($pick) { $pyExe = "py"; $pyArgs = @("-3.$pick") }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pyExe = (Get-Command python).Source
}
if (-not $pyExe) {
    Die "No Python 3.9+ found. Install Python 3.11 from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then re-run."
}
$ver = (& $pyExe @pyArgs --version 2>&1 | Out-String).Trim()
Write-Host ("Using " + $ver)

# 2. Create the venv (once).
$venv = Join-Path $env:LOCALAPPDATA "tiff2mp4\venv"
$vpy  = Join-Path $venv "Scripts\python.exe"
$vpyw = Join-Path $venv "Scripts\pythonw.exe"
if (-not (Test-Path $vpy)) {
    Write-Host ("Creating virtual environment at " + $venv + " ...")
    & $pyExe @pyArgs -m venv $venv
    if (-not (Test-Path $vpy)) { Die "Could not create the virtual environment." }
}

# 3. Install the app + deps.
Write-Host "Installing tiff2mp4 and its dependencies (first time takes a minute) ..."
& $vpy -m pip install --upgrade pip
& $vpy -m pip install $repo
if ($LASTEXITCODE -ne 0) {
    Die "pip install failed (see the errors above). Tell Julio the error and we'll pin a version."
}

# 4. Desktop shortcut -> venv pythonw -m module (self-contained; no console).
$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desktop ($AppName + ".lnk")
$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnk)
$sc.TargetPath = $vpyw
$sc.Arguments = "-m " + $Module
$sc.WorkingDirectory = $env:USERPROFILE
$sc.IconLocation = $vpyw + ",0"
$sc.Description = $AppName
$sc.Save()

Write-Host ""
Write-Host ("Done. '" + $AppName + "' is on your Desktop - double-click it, then drop a folder of TIFFs.")
