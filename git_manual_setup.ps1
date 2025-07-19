# VisionAI-ClipsMaster 手动Git配置脚本 (简化版)

# 设置编码
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🔧 VisionAI-ClipsMaster 手动Git配置" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

# 步骤1: 检查Git
Write-Host "`n[1/6] 检查Git安装..." -ForegroundColor Yellow
$gitCheck = Get-Command git -ErrorAction SilentlyContinue
if ($gitCheck) {
    $gitVersion = & git --version
    Write-Host "✓ $gitVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Git未安装，请先安装Git" -ForegroundColor Red
    Write-Host "下载地址: https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "按Enter退出"
    exit 1
}

# 步骤2: 配置用户信息
Write-Host "`n[2/6] 配置Git用户信息..." -ForegroundColor Yellow

$currentName = & git config user.name 2>$null
$currentEmail = & git config user.email 2>$null

if (-not $currentName) {
    Write-Host "请输入Git用户名 (建议: CKEN):" -ForegroundColor Cyan
    $userName = Read-Host
    if ($userName) {
        & git config user.name "$userName"
        Write-Host "✓ 用户名设置为: $userName" -ForegroundColor Green
    }
} else {
    Write-Host "✓ 当前用户名: $currentName" -ForegroundColor Green
}

if (-not $currentEmail) {
    Write-Host "请输入Git邮箱:" -ForegroundColor Cyan
    $userEmail = Read-Host
    if ($userEmail) {
        & git config user.email "$userEmail"
        Write-Host "✓ 邮箱设置为: $userEmail" -ForegroundColor Green
    }
} else {
    Write-Host "✓ 当前邮箱: $currentEmail" -ForegroundColor Green
}

# 步骤3: 初始化仓库
Write-Host "`n[3/6] 初始化Git仓库..." -ForegroundColor Yellow

if (Test-Path ".git") {
    Write-Host "✓ Git仓库已存在" -ForegroundColor Green
} else {
    & git init
    Write-Host "✓ Git仓库初始化完成" -ForegroundColor Green
}

# 设置默认分支为main
& git branch -M main 2>$null
Write-Host "✓ 默认分支设置为main" -ForegroundColor Green

# 步骤4: 配置Git LFS
Write-Host "`n[4/6] 配置Git LFS..." -ForegroundColor Yellow

$lfsCheck = Get-Command "git-lfs" -ErrorAction SilentlyContinue
if ($lfsCheck) {
    & git lfs install
    Write-Host "✓ Git LFS已配置" -ForegroundColor Green
    
    # 检查.gitattributes
    if (Test-Path ".gitattributes") {
        Write-Host "✓ .gitattributes文件存在" -ForegroundColor Green
    } else {
        Write-Host "⚠ .gitattributes文件不存在，创建基本配置..." -ForegroundColor Yellow
        @"
# Git LFS配置
*.gguf filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text

# 文本文件行尾处理
*.py text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.json text eol=lf
*.yml text eol=lf
*.yaml text eol=lf

# 二进制文件
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.zip binary
*.tar.gz binary
"@ | Out-File -FilePath ".gitattributes" -Encoding UTF8
        Write-Host "✓ .gitattributes文件已创建" -ForegroundColor Green
    }
} else {
    Write-Host "⚠ Git LFS未安装，跳过LFS配置" -ForegroundColor Yellow
    Write-Host "  下载地址: https://git-lfs.github.io/" -ForegroundColor Gray
}

# 步骤5: 配置远程仓库
Write-Host "`n[5/6] 配置远程仓库..." -ForegroundColor Yellow

$existingRemote = & git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "✓ 远程仓库已配置: $existingRemote" -ForegroundColor Green
} else {
    Write-Host "配置GitHub远程仓库..." -ForegroundColor Cyan
    Write-Host "1. HTTPS (推荐): https://github.com/CKEN/VisionAI-ClipsMaster.git" -ForegroundColor White
    Write-Host "2. SSH: git@github.com:CKEN/VisionAI-ClipsMaster.git" -ForegroundColor White
    Write-Host "3. 自定义URL" -ForegroundColor White
    
    $choice = Read-Host "请选择 (1/2/3)"
    
    switch ($choice) {
        "1" { 
            $repoUrl = "https://github.com/CKEN/VisionAI-ClipsMaster.git"
        }
        "2" { 
            $repoUrl = "git@github.com:CKEN/VisionAI-ClipsMaster.git"
        }
        "3" {
            $repoUrl = Read-Host "请输入仓库URL"
        }
        default { 
            $repoUrl = "https://github.com/CKEN/VisionAI-ClipsMaster.git"
            Write-Host "使用默认HTTPS地址" -ForegroundColor Yellow
        }
    }
    
    if ($repoUrl) {
        & git remote add origin "$repoUrl"
        Write-Host "✓ 远程仓库配置完成: $repoUrl" -ForegroundColor Green
    }
}

# 步骤6: 处理大文件问题
Write-Host "`n[6/6] 检查大文件..." -ForegroundColor Yellow

# 查找大文件 (>100MB)
$largeFiles = Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 100MB }

if ($largeFiles) {
    Write-Host "⚠ 发现大文件 (>100MB):" -ForegroundColor Yellow
    foreach ($file in $largeFiles) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "  - $($file.FullName) ($sizeMB MB)" -ForegroundColor Gray
    }
    
    Write-Host "`n建议操作:" -ForegroundColor Cyan
    Write-Host "1. 将大文件添加到.gitignore" -ForegroundColor White
    Write-Host "2. 使用Git LFS跟踪大文件" -ForegroundColor White
    Write-Host "3. 移动大文件到其他位置" -ForegroundColor White
    
    $handleLargeFiles = Read-Host "是否自动添加到.gitignore? (y/N)"
    if ($handleLargeFiles -eq "y" -or $handleLargeFiles -eq "Y") {
        $gitignoreContent = ""
        if (Test-Path ".gitignore") {
            $gitignoreContent = Get-Content ".gitignore" -Raw
        }
        
        $gitignoreContent += "`n# 大文件 (自动添加)`n"
        foreach ($file in $largeFiles) {
            $relativePath = $file.FullName.Replace((Get-Location).Path + "\", "").Replace("\", "/")
            $gitignoreContent += "$relativePath`n"
        }
        
        $gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8
        Write-Host "✓ 大文件已添加到.gitignore" -ForegroundColor Green
    }
} else {
    Write-Host "✓ 没有发现大文件" -ForegroundColor Green
}

# 显示当前状态
Write-Host "`n📊 当前Git状态:" -ForegroundColor Cyan
& git status --short

Write-Host "`n✅ 手动配置完成！" -ForegroundColor Green

Write-Host "`n🎯 下一步操作:" -ForegroundColor Yellow
Write-Host "1. 添加文件: git add ." -ForegroundColor White
Write-Host "2. 创建提交: git commit -m `"Initial commit`"" -ForegroundColor White
Write-Host "3. 推送代码: git push -u origin main" -ForegroundColor White

Write-Host "`n💡 手动执行命令:" -ForegroundColor Cyan
Write-Host "git add ." -ForegroundColor Gray
Write-Host "git commit -m `"feat: initial release of VisionAI-ClipsMaster v1.0.0`"" -ForegroundColor Gray
Write-Host "git push -u origin main" -ForegroundColor Gray

$autoCommit = Read-Host "`n是否自动执行提交和推送? (y/N)"
if ($autoCommit -eq "y" -or $autoCommit -eq "Y") {
    Write-Host "`n执行自动提交..." -ForegroundColor Yellow
    
    & git add .
    Write-Host "✓ 文件已添加到暂存区" -ForegroundColor Green
    
    $commitMsg = "feat: initial release of VisionAI-ClipsMaster v1.0.0

🎬 AI-powered short drama intelligent remixing tool

Features:
- 🤖 Dual-model architecture (Mistral-7B + Qwen2.5-7B)
- 🎯 Intelligent screenplay reconstruction
- ⚡ Precise video splicing with zero loss
- 💾 4GB memory optimization
- 🚀 Pure CPU inference, no GPU required
- 🌍 Cross-platform support"

    & git commit -m "$commitMsg"
    Write-Host "✓ 初始提交已创建" -ForegroundColor Green
    
    Write-Host "正在推送到远程仓库..." -ForegroundColor Yellow
    & git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 代码推送成功！" -ForegroundColor Green
        
        # 创建标签
        & git tag -a "v1.0.0" -m "Release v1.0.0: Initial stable release"
        & git push origin "v1.0.0"
        Write-Host "✅ 版本标签 v1.0.0 已创建并推送" -ForegroundColor Green
    } else {
        Write-Host "❌ 推送失败，请检查网络连接和认证设置" -ForegroundColor Red
    }
}

Read-Host "`n按Enter键退出"
