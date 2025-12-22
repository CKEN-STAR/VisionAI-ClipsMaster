# GGUF转换功能快速安装脚本
# 用于自动安装llama.cpp和相关依赖

param(
    [switch]$SkipDependencies,  # 跳过Python依赖安装
    [switch]$UseMirror          # 使用国内镜像
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "  VisionAI-ClipsMaster - GGUF转换功能安装脚本" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# 检查是否在虚拟环境中
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  警告: 未检测到虚拟环境" -ForegroundColor Yellow
    Write-Host "   建议先激活虚拟环境: .venv\Scripts\activate" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "是否继续安装? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "安装已取消" -ForegroundColor Red
        exit 1
    }
}

# 步骤1: 安装Python依赖
if (-not $SkipDependencies) {
    Write-Host "📦 步骤1: 安装Python依赖..." -ForegroundColor Green
    Write-Host ""
    
    $packages = @("gguf", "sentencepiece")
    
    foreach ($package in $packages) {
        Write-Host "  安装 $package..." -ForegroundColor Cyan
        pip install $package --no-cache-dir
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ❌ $package 安装失败" -ForegroundColor Red
            exit 1
        }
        Write-Host "  ✅ $package 安装成功" -ForegroundColor Green
    }
    
    Write-Host ""
} else {
    Write-Host "⏭️  跳过Python依赖安装" -ForegroundColor Yellow
    Write-Host ""
}

# 步骤2: 克隆llama.cpp仓库
Write-Host "📥 步骤2: 克隆llama.cpp仓库..." -ForegroundColor Green
Write-Host ""

if (Test-Path "llama.cpp") {
    Write-Host "  ⚠️  llama.cpp目录已存在" -ForegroundColor Yellow
    $overwrite = Read-Host "  是否删除并重新克隆? (y/N)"
    
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Write-Host "  删除现有目录..." -ForegroundColor Cyan
        Remove-Item -Recurse -Force "llama.cpp"
    } else {
        Write-Host "  保留现有llama.cpp目录" -ForegroundColor Yellow
        Write-Host ""
        $skipClone = $true
    }
}

if (-not $skipClone) {
    $repoUrl = if ($UseMirror) {
        "https://gitclone.com/github.com/ggerganov/llama.cpp.git"
    } else {
        "https://github.com/ggerganov/llama.cpp.git"
    }
    
    Write-Host "  克隆仓库: $repoUrl" -ForegroundColor Cyan
    git clone --depth 1 $repoUrl
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ 克隆失败" -ForegroundColor Red
        
        if (-not $UseMirror) {
            Write-Host ""
            Write-Host "  提示: 如果GitHub访问慢，可以使用镜像:" -ForegroundColor Yellow
            Write-Host "  .\scripts\setup_gguf_conversion.ps1 -UseMirror" -ForegroundColor Yellow
        }
        
        exit 1
    }
    
    Write-Host "  ✅ llama.cpp克隆成功" -ForegroundColor Green
    Write-Host ""
}

# 步骤3: 验证安装
Write-Host "🔍 步骤3: 验证安装..." -ForegroundColor Green
Write-Host ""

$convertScript = "llama.cpp\convert_hf_to_gguf.py"
if (Test-Path $convertScript) {
    Write-Host "  ✅ 转换脚本存在: $convertScript" -ForegroundColor Green
} else {
    Write-Host "  ❌ 转换脚本不存在: $convertScript" -ForegroundColor Red
    exit 1
}

# 检查Python依赖
Write-Host "  检查Python依赖..." -ForegroundColor Cyan
$requiredPackages = @("torch", "transformers", "numpy", "gguf", "sentencepiece")
$allInstalled = $true

foreach ($package in $requiredPackages) {
    $installed = pip list | Select-String $package
    if ($installed) {
        Write-Host "  ✅ $package 已安装" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $package 未安装" -ForegroundColor Red
        $allInstalled = $false
    }
}

Write-Host ""

if (-not $allInstalled) {
    Write-Host "⚠️  部分依赖未安装，请运行:" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host ""
}

# 步骤4: 运行测试
Write-Host "🧪 步骤4: 运行测试..." -ForegroundColor Green
Write-Host ""

if (Test-Path "scripts\test_gguf_conversion.py") {
    Write-Host "  运行测试脚本..." -ForegroundColor Cyan
    python scripts\test_gguf_conversion.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" -NoNewline -ForegroundColor Green
        Write-Host ("=" * 69) -ForegroundColor Green
        Write-Host "  🎉 GGUF转换功能安装成功！" -ForegroundColor Yellow
        Write-Host "=" -NoNewline -ForegroundColor Green
        Write-Host ("=" * 69) -ForegroundColor Green
        Write-Host ""
        Write-Host "下一步:" -ForegroundColor Cyan
        Write-Host "  1. 查看文档: docs\GGUF_CONVERSION_SETUP.md" -ForegroundColor White
        Write-Host "  2. 训练模型并转换为GGUF格式" -ForegroundColor White
        Write-Host "  3. 享受3-5倍的推理速度提升！" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "⚠️  测试失败，请检查上述错误信息" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
} else {
    Write-Host "  ⚠️  测试脚本不存在，跳过测试" -ForegroundColor Yellow
    Write-Host ""
}

# 可选: 编译量化工具提示
Write-Host "💡 提示: 编译量化工具（可选）" -ForegroundColor Cyan
Write-Host ""
Write-Host "  如果需要K-quants量化（Q4_K_M, Q5_K, Q2_K），需要编译llama.cpp:" -ForegroundColor White
Write-Host ""
Write-Host "  方法1 - 使用Visual Studio:" -ForegroundColor Yellow
Write-Host "    cd llama.cpp" -ForegroundColor Gray
Write-Host "    cmake -B build -G `"Visual Studio 16 2019`" -A x64" -ForegroundColor Gray
Write-Host "    cmake --build build --config Release" -ForegroundColor Gray
Write-Host ""
Write-Host "  方法2 - 使用MinGW:" -ForegroundColor Yellow
Write-Host "    cd llama.cpp" -ForegroundColor Gray
Write-Host "    make" -ForegroundColor Gray
Write-Host ""
Write-Host "  如果不编译，仍可使用F16/F32/Q8_0格式转换" -ForegroundColor White
Write-Host ""

$compile = Read-Host "是否现在编译量化工具? (y/N)"
if ($compile -eq "y" -or $compile -eq "Y") {
    Write-Host ""
    Write-Host "开始编译..." -ForegroundColor Green
    
    # 检查是否有CMake
    $hasCMake = Get-Command cmake -ErrorAction SilentlyContinue
    
    if ($hasCMake) {
        Write-Host "  使用CMake编译..." -ForegroundColor Cyan
        Push-Location llama.cpp
        cmake -B build -G "Visual Studio 16 2019" -A x64
        cmake --build build --config Release
        Pop-Location
        
        if (Test-Path "llama.cpp\build\bin\Release\quantize.exe") {
            Write-Host "  ✅ 编译成功！" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  编译可能失败，请检查错误信息" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ 未找到CMake，请先安装Visual Studio或MinGW" -ForegroundColor Red
        Write-Host "  下载Visual Studio: https://visualstudio.microsoft.com/" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "安装完成！" -ForegroundColor Green

