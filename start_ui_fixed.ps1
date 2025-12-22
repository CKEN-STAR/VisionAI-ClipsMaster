# VisionAI-ClipsMaster UI 启动脚本 (修复版)
# 确保使用正确的Python环境并验证所有依赖

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VisionAI-ClipsMaster UI 启动脚本 (修复版)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查虚拟环境
Write-Host "[1/6] 检查虚拟环境..." -ForegroundColor Yellow
if (Test-Path ".\.venv\Scripts\python.exe") {
    Write-Host "✅ 虚拟环境存在" -ForegroundColor Green
} else {
    Write-Host "❌ 虚拟环境不存在!" -ForegroundColor Red
    Write-Host "请先创建虚拟环境: python -m venv .venv" -ForegroundColor Red
    exit 1
}

# 2. 激活虚拟环境
Write-Host "[2/6] 激活虚拟环境..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 激活虚拟环境失败!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green

# 3. 验证Python路径
Write-Host "[3/6] 验证Python路径..." -ForegroundColor Yellow
$pythonPath = & python -c "import sys; print(sys.executable)"
Write-Host "Python路径: $pythonPath" -ForegroundColor Cyan
if ($pythonPath -like "*\.venv\*") {
    Write-Host "✅ 使用虚拟环境Python" -ForegroundColor Green
} else {
    Write-Host "❌ 未使用虚拟环境Python!" -ForegroundColor Red
    Write-Host "请确保虚拟环境已正确激活" -ForegroundColor Red
    exit 1
}

# 4. 验证PyTorch
Write-Host "[4/6] 验证PyTorch..." -ForegroundColor Yellow
$torchCheck = & python -c "try:
    import torch
    print(f'✅ PyTorch {torch.__version__}')
    print(f'✅ CUDA可用: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
    exit(0)
except Exception as e:
    print(f'❌ PyTorch错误: {e}')
    exit(1)
" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host $torchCheck -ForegroundColor Green
} else {
    Write-Host $torchCheck -ForegroundColor Red
    Write-Host "❌ PyTorch验证失败!" -ForegroundColor Red
    Write-Host "正在尝试修复..." -ForegroundColor Yellow
    
    # 尝试修复PyTorch
    Write-Host "卸载旧版PyTorch..." -ForegroundColor Yellow
    pip uninstall torch torchvision torchaudio -y
    
    Write-Host "重新安装PyTorch..." -ForegroundColor Yellow
    pip install torch==2.9.0+cu128 torchvision==0.19.0+cu128 torchaudio==2.9.0+cu128 --index-url https://download.pytorch.org/whl/cu128 --no-cache-dir
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ PyTorch安装失败!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ PyTorch已修复" -ForegroundColor Green
}

# 5. 验证llama-cpp-python
Write-Host "[5/6] 验证llama-cpp-python..." -ForegroundColor Yellow
$llamaCheck = & python -c "try:
    from llama_cpp import Llama
    print('✅ llama-cpp-python可用')
    exit(0)
except Exception as e:
    print(f'❌ llama-cpp-python错误: {e}')
    exit(1)
" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host $llamaCheck -ForegroundColor Green
} else {
    Write-Host $llamaCheck -ForegroundColor Red
    Write-Host "❌ llama-cpp-python验证失败!" -ForegroundColor Red
    Write-Host "请手动安装: pip install llama-cpp-python" -ForegroundColor Yellow
}

# 6. 启动UI
Write-Host "[6/6] 启动UI..." -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "正在启动VisionAI-ClipsMaster UI..." -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示:" -ForegroundColor Yellow
Write-Host "1. 请在UI中添加SRT文件" -ForegroundColor Yellow
Write-Host "2. 点击'AI优化字幕'按钮" -ForegroundColor Yellow
Write-Host "3. 观察控制台输出" -ForegroundColor Yellow
Write-Host ""

# 启动UI
python simple_ui_fixed.py

# 检查退出码
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ UI启动失败!" -ForegroundColor Red
    Write-Host "退出码: $LASTEXITCODE" -ForegroundColor Red
} else {
    Write-Host ""
    Write-Host "✅ UI已正常退出" -ForegroundColor Green
}

