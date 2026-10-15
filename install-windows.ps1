# JARVIS Windows 10 installation (current user, no administrator privileges)
param(
    [string]$InstallDir = 'D:\JARVIS',
    [string]$VoskModel = '',
    [switch]$Speak,
    [switch]$RemoveAutostart
)
$ErrorActionPreference = 'Stop'
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$runName = 'JARVISLocalAssistant'
if ($RemoveAutostart) {
    Remove-ItemProperty -Path $runKey -Name $runName -ErrorAction SilentlyContinue
    Write-Host 'JARVIS autostart disabled. Files were preserved.'
    exit 0
}
if (-not (Test-Path (Join-Path $PSScriptRoot 'jarvis_launcher.py'))) {
    throw 'Run this installer from the checked-out JARVIS repository.'
}
$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & py -3.11 --version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 is required.' }
    $basePython = 'py'
    $baseArgs = @('-3.11')
} else {
    $python = Get-Command python -ErrorAction Stop
    $basePython = $python.Source
    $baseArgs = @()
}
if (Test-Path $InstallDir) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup = "$InstallDir.backup-$stamp"
    Move-Item -LiteralPath $InstallDir -Destination $backup
    Write-Host "Previous installation backed up: $backup"
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
$items = @('jarvis', 'dashboard_cli.py', 'jarvis_launcher.py', 'wake_cli.py', 'projects_cli.py', 'requirements.txt')
foreach ($item in $items) {
    $source = Join-Path $PSScriptRoot $item
    if (Test-Path $source) { Copy-Item -LiteralPath $source -Destination $InstallDir -Recurse -Force }
}
& $basePython @baseArgs -m venv (Join-Path $InstallDir '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Unable to create Python environment.' }
$venvPython = Join-Path $InstallDir '.venv\Scripts\python.exe'
if ($VoskModel) {
    if (-not (Test-Path (Join-Path $VoskModel 'am'))) { throw 'Vosk model not found: expected am folder.' }
    & $venvPython -m pip install 'vosk>=0.3.45,<1' 'sounddevice>=0.4,<1'
    if ($LASTEXITCODE -ne 0) { throw 'Vosk dependencies installation failed.' }
}
$arguments = @('jarvis_launcher.py', '--open-browser')
if ($VoskModel) { $arguments += @('--vosk-model', $VoskModel) }
if ($Speak) { $arguments += '--speak' }
$escaped = $arguments | ForEach-Object { '"' + $_.Replace('"','') + '"' }
$command = '"' + $venvPython + '" ' + ($escaped -join ' ')
$launch = Join-Path $InstallDir 'start-jarvis.cmd'
@(
    '@echo off',
    'cd /d "' + $InstallDir + '"',
    $command
) | Set-Content -LiteralPath $launch -Encoding ASCII
# HKCU Run starts the launcher after Windows login, not as a privileged service.
New-Item -Path $runKey -Force | Out-Null
Set-ItemProperty -Path $runKey -Name $runName -Value ('"' + $launch + '"')
Write-Host 'Installed JARVIS and registered per-user startup.'
Write-Host "Start now: $launch"
Write-Host 'Remove autostart: powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -RemoveAutostart'
