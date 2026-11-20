# Linktomp3 - asennus Windowsiin
# Luo virtuaaliympäristön, asentaa riippuvuudet ja tekee pikakuvakkeet
# työpöydälle ja Käynnistä-valikkoon.
#
# Ajo:  powershell -ExecutionPolicy Bypass -File windows\install.ps1

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host 'ffmpeg puuttuu - asennetaan wingetillä...'
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
}

$Py = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $Py)) {
    Write-Host 'Luodaan virtuaaliympäristö...'
    py -3 -m venv .venv
    if (-not $?) { python -m venv .venv }
}
& $Py -m pip install --upgrade pip --quiet
& $Py -m pip install --upgrade -r requirements.txt --quiet
Write-Host 'Riippuvuudet asennettu.'

$PyW = Join-Path $Root '.venv\Scripts\pythonw.exe'
$Launcher = Join-Path $Root 'windows\launcher.pyw'
$Icon = Join-Path $Root 'windows\linktomp3.ico'

$Shell = New-Object -ComObject WScript.Shell
$Targets = @(
    [Environment]::GetFolderPath('Desktop'),
    (Join-Path ([Environment]::GetFolderPath('Programs')) '')
)
foreach ($Dir in $Targets) {
    $Lnk = $Shell.CreateShortcut((Join-Path $Dir 'Linktomp3.lnk'))
    $Lnk.TargetPath = $PyW
    $Lnk.Arguments = "`"$Launcher`""
    $Lnk.WorkingDirectory = $Root
    $Lnk.IconLocation = $Icon
    $Lnk.Description = 'Muunna YouTube-linkit mp3-tiedostoiksi'
    $Lnk.Save()
    Write-Host "Pikakuvake: $(Join-Path $Dir 'Linktomp3.lnk')"
}
Write-Host 'Valmis! Käynnistä Linktomp3 työpöydän kuvakkeesta.'
