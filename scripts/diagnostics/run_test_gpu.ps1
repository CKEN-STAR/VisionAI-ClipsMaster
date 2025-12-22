# requires -version 5.1
$ErrorActionPreference = 'Stop'
Write-Host "[GPU-TEST] Python: $(Get-Command python | Select-Object -ExpandProperty Source)"
python scripts/diagnostics/test_llama_gpu_load.py
if ($LASTEXITCODE -ne 0) { Write-Error "[GPU-TEST] test_llama_gpu_load failed with code $LASTEXITCODE"; exit $LASTEXITCODE }
Write-Host "[GPU-TEST] Done"
