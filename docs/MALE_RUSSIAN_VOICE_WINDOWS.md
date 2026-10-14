# Male Russian voice preview (Piper) on Windows 10

JARVIS keeps its existing Vosk microphone input, SQLite memory, CPU-only
Ollama model, and safe action approvals. The existing `jarvis.speech.Speaker`
now accepts `--tts piper` as an optional **offline** speaker. Windows SAPI
remains the default and can always be restored.

Piper Windows x64 runtime: https://github.com/rhasspy/piper/releases/tag/2023.11.14-2
Male Russian voice model catalog: https://huggingface.co/rhasspy/piper-voices/tree/main/ru/ru_RU

These older Piper binaries are downloaded from the original project's release
instead of from third-party repackagers. Only the two selected voices and the
local Windows runtime are needed. Voice `.onnx` files are approximately 63 MB
each; each needs its matching `.onnx.json` config. The Piper repository was
archived in 2025; validate the downloaded files and keep it isolated.

## Download Piper and two male voices to D:

Run in a regular PowerShell terminal. There is no global Python install,
Windows service or automatic startup.

```powershell
$ErrorActionPreference = 'Stop'
$root = 'D:\JARVIS-test\voice'
$binDir = Join-Path $root 'piper-runtime'
$voiceDir = Join-Path $root 'piper-male'
$zip = Join-Path $root 'piper_windows_amd64.zip'

New-Item -ItemType Directory -Force -Path $binDir, $voiceDir | Out-Null
if (-not (Test-Path $zip)) {
    Invoke-WebRequest -Uri 'https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip' -OutFile $zip -UseBasicParsing
}
if (-not (Get-ChildItem $binDir -Filter 'piper.exe' -Recurse -File -ErrorAction SilentlyContinue)) {
    Expand-Archive -Path $zip -DestinationPath $binDir
}
$piper = Get-ChildItem $binDir -Filter 'piper.exe' -Recurse -File |
    Select-Object -First 1
if (-not $piper) { throw 'No piper.exe found in the official Windows archive' }

foreach ($name in @('dmitri', 'ruslan')) {
    $stem = "ru_RU-$name-medium.onnx"
    $base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/$name/medium"
    $onnx = Join-Path $voiceDir $stem
    $config = "$onnx.json"
    if (-not (Test-Path $onnx)) {
        Invoke-WebRequest -Uri "$base/$stem" -OutFile $onnx -UseBasicParsing
    }
    if (-not (Test-Path $config)) {
        Invoke-WebRequest -Uri "$base/$stem.json" -OutFile $config -UseBasicParsing
    }
    if ((Get-Item $onnx).Length -lt 50000000) {
        throw "Voice file is incomplete: $onnx"
    }
    $json = Get-Content $config -Raw | ConvertFrom-Json
    if ($json.language.code -ne 'ru_RU') {
        throw "Wrong voice config: $config"
    }
}
Write-Host 'Piper executable:' $piper.FullName
Write-Host 'Dmitri and Ruslan voices are present.'
```

## Listen to the voices (does not start Ollama or microphone)

Change the current directory to the latest verified JARVIS source that has
`voice_chat.py --voice-preview`. Use the already installed isolated Python:

```powershell
$python = 'D:\JARVIS-test\venv-voice\Scripts\python.exe'
$piper = (Get-ChildItem 'D:\JARVIS-test\voice\piper-runtime' -Filter piper.exe -Recurse -File |
    Select-Object -First 1).FullName

& $python voice_chat.py --voice-preview --tts piper --piper-bin $piper --piper-voice 'D:\JARVIS-test\voice\piper-male\ru_RU-dmitri-medium.onnx'
& $python voice_chat.py --voice-preview --tts piper --piper-bin $piper --piper-voice 'D:\JARVIS-test\voice\piper-male\ru_RU-ruslan-medium.onnx'
```

Only after choosing a voice, use the existing full assistant:

```powershell
& $python voice_chat.py --model 'D:\JARVIS-test\voice\vosk-model-small-ru-0.22' --llm-model 'qwen2.5:3b-instruct-q6_K' --db 'D:\JARVIS-test\data\jarvis-test.db' --cpu-only --speak --tts piper --piper-bin $piper --piper-voice 'D:\JARVIS-test\voice\piper-male\ru_RU-dmitri-medium.onnx'
```

If you do not hear the preview or it fails, do not launch the full voice
assistant. The voice preference can be changed by swapping only
`--piper-voice`, without replacing the core or deleting the SQLite database.
