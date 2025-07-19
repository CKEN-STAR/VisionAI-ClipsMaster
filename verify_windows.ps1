# VisionAI-ClipsMaster Windows PowerShell验证脚本

Write-Host "🔍 VisionAI-ClipsMaster 项目结构验证" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# 1. 检查当前目录
Write-Host "`n📁 当前目录结构:" -ForegroundColor Yellow
Get-Location
Get-ChildItem -Directory | Select-Object Name | Format-Table -AutoSize

# 2. 检查核心目录是否存在
Write-Host "`n🎯 验证核心目录:" -ForegroundColor Yellow
$coreDirectories = @(
    "src\visionai_clipsmaster\core",
    "src\visionai_clipsmaster\concurrent",
    "requirements",
    "scripts", 
    "docker",
    ".github\workflows"
)

foreach ($dir in $coreDirectories) {
    if (Test-Path $dir) {
        Write-Host "  ✓ $dir" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $dir" -ForegroundColor Red
    }
}

# 3. 检查Python文件
Write-Host "`n🐍 检查Python文件:" -ForegroundColor Yellow
$pythonFiles = Get-ChildItem -Recurse -Filter "*.py" | Select-Object -First 10
$pythonFiles | ForEach-Object { Write-Host "  📄 $($_.FullName)" -ForegroundColor Gray }

# 4. 检查__init__.py文件
Write-Host "`n📦 检查Python包文件:" -ForegroundColor Yellow
$initFiles = Get-ChildItem -Recurse -Filter "__init__.py"
$initFiles | ForEach-Object { Write-Host "  ✓ $($_.FullName)" -ForegroundColor Green }

# 5. 检查配置文件
Write-Host "`n⚙️ 检查配置文件:" -ForegroundColor Yellow
$configFiles = @(
    "README.md",
    "LICENSE", 
    "CONTRIBUTING.md",
    ".gitignore",
    ".gitattributes"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file" -ForegroundColor Red
    }
}

# 6. 统计信息
Write-Host "`n📊 项目统计:" -ForegroundColor Yellow
$totalDirs = (Get-ChildItem -Recurse -Directory).Count
$totalFiles = (Get-ChildItem -Recurse -File).Count
$pythonFileCount = (Get-ChildItem -Recurse -Filter "*.py").Count

Write-Host "  📁 总目录数: $totalDirs" -ForegroundColor Cyan
Write-Host "  📄 总文件数: $totalFiles" -ForegroundColor Cyan  
Write-Host "  🐍 Python文件数: $pythonFileCount" -ForegroundColor Cyan

Write-Host "`n✅ 验证完成!" -ForegroundColor Green
