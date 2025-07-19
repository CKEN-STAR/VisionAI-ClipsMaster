# VisionAI-ClipsMaster Windows PowerShell Git配置脚本

# 设置错误处理和编码
$ErrorActionPreference = "Continue"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 VisionAI-ClipsMaster Git初始化和配置 (Windows版)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# 1. 检查Git安装
Write-Host "`n[1/8] 检查Git安装..." -ForegroundColor Yellow
try {
    $gitVersion = git --version
    Write-Host "✓ Git已安装: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git未安装，请先安装Git" -ForegroundColor Red
    Write-Host "下载地址: https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

# 2. 检查Git LFS安装
Write-Host "`n[2/8] 检查Git LFS..." -ForegroundColor Yellow
try {
    $lfsVersion = git lfs version
    Write-Host "✓ Git LFS已安装: $lfsVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ Git LFS未安装，正在尝试安装..." -ForegroundColor Yellow
    
    # 尝试通过Git安装LFS
    try {
        git lfs install --system
        Write-Host "✓ Git LFS安装成功" -ForegroundColor Green
    } catch {
        Write-Host "❌ Git LFS安装失败，请手动安装" -ForegroundColor Red
        Write-Host "下载地址: https://git-lfs.github.io/" -ForegroundColor Yellow
        $continue = Read-Host "是否继续? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    }
}

# 3. 初始化Git仓库
Write-Host "`n[3/8] 初始化Git仓库..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "⚠ Git仓库已存在，跳过初始化" -ForegroundColor Yellow
} else {
    try {
        git init
        Write-Host "✓ Git仓库初始化完成" -ForegroundColor Green
    } catch {
        Write-Host "❌ Git仓库初始化失败" -ForegroundColor Red
        exit 1
    }
}

# 4. 配置Git LFS
Write-Host "`n[4/8] 配置Git LFS..." -ForegroundColor Yellow
try {
    git lfs install
    
    # 检查.gitattributes文件
    if (Test-Path ".gitattributes") {
        Write-Host "✓ .gitattributes文件存在" -ForegroundColor Green
    } else {
        Write-Host "❌ .gitattributes文件不存在，请先运行项目组织脚本" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Git LFS配置完成" -ForegroundColor Green
} catch {
    Write-Host "❌ Git LFS配置失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. 配置Git用户信息
Write-Host "`n[5/8] 配置Git用户信息..." -ForegroundColor Yellow

# 检查现有配置
$existingName = git config user.name 2>$null
$existingEmail = git config user.email 2>$null

if (-not $existingName) {
    $gitUsername = Read-Host "请输入Git用户名"
    git config user.name "$gitUsername"
}

if (-not $existingEmail) {
    $gitEmail = Read-Host "请输入Git邮箱"
    git config user.email "$gitEmail"
}

$userName = git config user.name
$userEmail = git config user.email
Write-Host "✓ Git用户信息配置完成" -ForegroundColor Green
Write-Host "  用户名: $userName" -ForegroundColor Cyan
Write-Host "  邮箱: $userEmail" -ForegroundColor Cyan

# 6. 配置远程仓库
Write-Host "`n[6/8] 配置远程仓库..." -ForegroundColor Yellow

# 检查现有远程仓库
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "⚠ 远程仓库已配置: $existingRemote" -ForegroundColor Yellow
    $updateRemote = Read-Host "是否要更新远程仓库地址? (y/N)"
    if ($updateRemote -eq "y" -or $updateRemote -eq "Y") {
        git remote remove origin
    } else {
        Write-Host "✓ 保持现有远程仓库配置" -ForegroundColor Green
        $remoteUrl = $existingRemote
    }
}

if (-not $existingRemote -or ($updateRemote -eq "y" -or $updateRemote -eq "Y")) {
    Write-Host "请选择远程仓库地址格式:" -ForegroundColor Cyan
    Write-Host "1. HTTPS (推荐): https://github.com/CKEN/VisionAI-ClipsMaster.git" -ForegroundColor White
    Write-Host "2. SSH: git@github.com:CKEN/VisionAI-ClipsMaster.git" -ForegroundColor White
    $repoFormat = Read-Host "请选择 (1/2)"
    
    switch ($repoFormat) {
        "1" { $remoteUrl = "https://github.com/CKEN/VisionAI-ClipsMaster.git" }
        "2" { $remoteUrl = "git@github.com:CKEN/VisionAI-ClipsMaster.git" }
        default { 
            Write-Host "❌ 无效选择，使用默认HTTPS" -ForegroundColor Red
            $remoteUrl = "https://github.com/CKEN/VisionAI-ClipsMaster.git"
        }
    }
    
    try {
        & git remote add origin "$remoteUrl"
        Write-Host "✓ 远程仓库配置完成: $remoteUrl" -ForegroundColor Green
    } catch {
        Write-Host "❌ 远程仓库配置失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "尝试手动执行: git remote add origin `"$remoteUrl`"" -ForegroundColor Yellow
        $continue = Read-Host "是否继续? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    }
}

# 7. 创建初始提交
Write-Host "`n[7/8] 创建初始提交..." -ForegroundColor Yellow

# 检查是否有未提交的更改
$status = git status --porcelain
if (-not $status) {
    Write-Host "⚠ 没有文件需要提交，添加所有文件..." -ForegroundColor Yellow
    git add .
}

# 检查暂存区
$stagedFiles = git diff --cached --name-only
if (-not $stagedFiles) {
    Write-Host "⚠ 暂存区为空，没有文件需要提交" -ForegroundColor Yellow
} else {
    Write-Host "📄 准备提交的文件:" -ForegroundColor Cyan
    $stagedFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    
    # 创建提交信息
    $commitMessage = @"
feat: initial release of VisionAI-ClipsMaster v1.0.0

🎬 AI-powered short drama intelligent remixing tool

Features:
- 🤖 Dual-model architecture (Mistral-7B + Qwen2.5-7B)
- 🎯 Intelligent screenplay reconstruction with AI analysis
- ⚡ Precise video splicing based on new subtitle timecodes
- 💾 4GB memory optimization with quantization support
- 🚀 Pure CPU inference, no GPU required
- 📤 JianYing project file export
- 🌍 Cross-platform support (Windows/Linux/macOS)
- 🐳 Docker containerization with lite and full versions

Technical Highlights:
- Threading-based concurrency for Python 3.8+ compatibility
- Automatic language detection and model switching
- Memory usage monitoring and optimization
- Comprehensive installation automation
- 30-minute setup from clone to first run

Documentation:
- Complete user guide and API documentation
- Developer contribution guidelines
- Docker deployment instructions
- Troubleshooting and FAQ
- Project roadmap and future plans

BREAKING CHANGE: This is the initial release
"@
    
    try {
        git commit -m $commitMessage
        Write-Host "✓ 初始提交创建完成" -ForegroundColor Green
    } catch {
        Write-Host "❌ 提交创建失败: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# 8. 推送到远程仓库
Write-Host "`n[8/8] 推送代码到远程仓库..." -ForegroundColor Yellow

try {
    # 设置默认分支为main
    git branch -M main
    
    # 推送代码
    git push -u origin main
    Write-Host "✓ 代码推送成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 代码推送失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  1. 网络连接问题" -ForegroundColor Gray
    Write-Host "  2. 认证失败 (用户名/密码或SSH密钥)" -ForegroundColor Gray
    Write-Host "  3. 仓库不存在或无权限" -ForegroundColor Gray
    
    $retryPush = Read-Host "是否重试推送? (y/N)"
    if ($retryPush -eq "y" -or $retryPush -eq "Y") {
        try {
            git push -u origin main
            Write-Host "✓ 重试推送成功" -ForegroundColor Green
        } catch {
            Write-Host "❌ 重试推送仍然失败" -ForegroundColor Red
            Write-Host "请检查网络连接和GitHub认证设置" -ForegroundColor Yellow
        }
    }
}

# 创建并推送标签
Write-Host "`n🏷️ 创建版本标签..." -ForegroundColor Yellow

$tagMessage = @"
Release v1.0.0: Initial stable release

🎉 VisionAI-ClipsMaster首个稳定版本发布

## ✨ 核心特性
- 🤖 双模型架构: Mistral-7B(英文) + Qwen2.5-7B(中文)
- 🎯 智能剧本重构: AI分析剧情并重新编排
- ⚡ 精准视频拼接: 零损失视频切割拼接
- 💾 4GB内存兼容: 专为低配设备优化
- 🚀 纯CPU推理: 无需GPU，普通电脑即可运行
- 📤 剪映工程导出: 生成可二次编辑的工程文件

## 🚀 快速开始
- 一键安装脚本支持Windows/Linux/macOS
- Docker部署支持轻量版和完整版
- 30分钟内完成从安装到首次使用

## 📊 性能指标
- 4GB设备: 8-12分钟处理30分钟视频
- 8GB设备: 5-8分钟处理30分钟视频
- 内存峰值: 3.2GB-5.1GB (根据量化级别)

This release marks the first stable version of VisionAI-ClipsMaster.
"@

try {
    git tag -a "v1.0.0" -m $tagMessage
    git push origin "v1.0.0"
    Write-Host "✓ 版本标签 v1.0.0 创建并推送完成" -ForegroundColor Green
} catch {
    Write-Host "❌ 标签创建或推送失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 验证仓库状态
Write-Host "`n🔍 验证仓库状态..." -ForegroundColor Yellow

try {
    $remoteUrl = git remote get-url origin
    $currentBranch = git branch --show-current
    $lastCommit = git log --oneline -1
    $tags = git tag -l
    
    Write-Host "`n📊 仓库信息:" -ForegroundColor Cyan
    Write-Host "  远程地址: $remoteUrl" -ForegroundColor White
    Write-Host "  当前分支: $currentBranch" -ForegroundColor White
    Write-Host "  最新提交: $lastCommit" -ForegroundColor White
    Write-Host "  标签列表: $tags" -ForegroundColor White
} catch {
    Write-Host "❌ 获取仓库信息失败" -ForegroundColor Red
}

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Git配置完成！" -ForegroundColor Green

Write-Host "`n🎯 下一步操作:" -ForegroundColor Yellow
Write-Host "1. 访问GitHub仓库查看代码" -ForegroundColor White
Write-Host "2. 配置GitHub仓库设置" -ForegroundColor White
Write-Host "3. 启用GitHub Actions" -ForegroundColor White
Write-Host "4. 创建GitHub Release" -ForegroundColor White
Write-Host "5. 设置社区功能" -ForegroundColor White

$repoWebUrl = $remoteUrl -replace "\.git$", ""
Write-Host "`n🔗 GitHub仓库地址:" -ForegroundColor Cyan
Write-Host "   $repoWebUrl" -ForegroundColor Blue

Write-Host "`n按Enter键退出..." -ForegroundColor Gray
Read-Host
