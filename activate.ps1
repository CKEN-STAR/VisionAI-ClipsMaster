# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 设置环境变量
$env:PYTHONPATH = "."
$env:CUDA_VISIBLE_DEVICES = "0"
$env:PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:512"

# 显示Python解释器位置
Write-Host "Python interpreter: $(Get-Command python | Select-Object -ExpandProperty Source)"
Write-Host "Virtual environment activated successfully!" 