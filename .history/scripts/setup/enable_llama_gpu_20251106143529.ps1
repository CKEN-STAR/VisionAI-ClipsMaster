# requires -version 5.1
param()
$ErrorActionPreference = 'Stop'
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$logDir = Join-Path $PSScriptRoot '..' | Join-Path -ChildPath '..' | Join-Path -ChildPath 'logs'
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir "gpu_setup_$ts.log"
Start-Transcript -Path $logFile -Force | Out-Null
Write-Host "[GPU-SETUP] Start at $ts"

Write-Host "[GPU-SETUP] Python: $(Get-Command python | Select-Object -ExpandProperty Source)"
python -c "import sys; print('PYTHON', sys.version)"

Write-Host "[GPU-SETUP] Pre-diagnostics (torch / llama_cpp / nvidia-smi)"
python scripts/diagnostics/check_gpu_buildinfo.py

Write-Host "[GPU-SETUP] Freeze current environment"
python -m pip freeze | Out-File -FilePath (Join-Path $logDir 'pip_freeze_before_gpu.txt') -Encoding utf8

Write-Host "[GPU-SETUP] Ensure toolchain (cmake, ninja)"
python -m pip install -U cmake ninja

Write-Host "[GPU-SETUP] Build llama-cpp-python with CUBLAS"
$env:CMAKE_ARGS = '-DLLAMA_CUBLAS=on'
$env:FORCE_CMAKE = '1'
python -m pip install --upgrade --force-reinstall --no-cache-dir llama-cpp-python

Write-Host "[GPU-SETUP] Post-diagnostics"
python scripts/diagnostics/check_gpu_buildinfo.py

Write-Host "[GPU-SETUP] Done"
Stop-Transcript | Out-Null

