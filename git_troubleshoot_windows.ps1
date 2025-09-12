# VisionAI-ClipsMaster Git故障排除脚本 (Windows PowerShell)

Write-Host "🔧 VisionAI-ClipsMaster Git故障排除工具" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# 1. 环境检查
Write-Host "`n[1] 环境检查..." -ForegroundColor Yellow

# 检查Git安装
Write-Host "`n🔍 检查Git安装:" -ForegroundColor White
try {
    $gitVersion = git --version
    Write-Host "  ✓ Git版本: $gitVersion" -ForegroundColor Green
    
    # 检查Git配置
    $gitName = git config user.name 2>$null
    $gitEmail = git config user.email 2>$null
    
    if ($gitName) {
        Write-Host "  ✓ Git用户名: $gitName" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Git用户名未配置" -ForegroundColor Red
        Write-Host "    解决方案: git config user.name `"您的用户名`"" -ForegroundColor Yellow
    }
    
    if ($gitEmail) {
        Write-Host "  ✓ Git邮箱: $gitEmail" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Git邮箱未配置" -ForegroundColor Red
        Write-Host "    解决方案: git config user.email `"您的邮箱`"" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Git未安装或不在PATH中" -ForegroundColor Red
    Write-Host "    解决方案: 从 https://git-scm.com/download/win 下载安装Git" -ForegroundColor Yellow
}

# 检查Git LFS
Write-Host "`n🔍 检查Git LFS:" -ForegroundColor White
try {
    $lfsVersion = git lfs version
    Write-Host "  ✓ Git LFS版本: $lfsVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Git LFS未安装" -ForegroundColor Red
    Write-Host "    解决方案: git lfs install 或从 https://git-lfs.github.io/ 下载" -ForegroundColor Yellow
}

# 检查网络连接
Write-Host "`n🔍 检查网络连接:" -ForegroundColor White
try {
    $response = Test-NetConnection -ComputerName "github.com" -Port 443 -InformationLevel Quiet
    if ($response) {
        Write-Host "  ✓ GitHub连接正常" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 无法连接到GitHub" -ForegroundColor Red
        Write-Host "    解决方案: 检查网络连接或防火墙设置" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ 网络连接检查失败" -ForegroundColor Yellow
}

# 2. Git仓库状态检查
Write-Host "`n[2] Git仓库状态检查..." -ForegroundColor Yellow

if (Test-Path ".git") {
    Write-Host "`n✓ Git仓库已初始化" -ForegroundColor Green
    
    # 检查远程仓库
    try {
        $remoteUrl = git remote get-url origin 2>$null
        if ($remoteUrl) {
            Write-Host "  ✓ 远程仓库: $remoteUrl" -ForegroundColor Green
        } else {
            Write-Host "  ❌ 远程仓库未配置" -ForegroundColor Red
            Write-Host "    解决方案: git remote add origin <仓库地址>" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ❌ 获取远程仓库信息失败" -ForegroundColor Red
    }
    
    # 检查分支
    try {
        $currentBranch = git branch --show-current
        Write-Host "  ✓ 当前分支: $currentBranch" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ 获取分支信息失败" -ForegroundColor Red
    }
    
    # 检查提交历史
    try {
        $commitCount = git rev-list --count HEAD 2>$null
        if ($commitCount -gt 0) {
            Write-Host "  ✓ 提交数量: $commitCount" -ForegroundColor Green
            $lastCommit = git log --oneline -1
            Write-Host "  ✓ 最新提交: $lastCommit" -ForegroundColor Green
        } else {
            Write-Host "  ❌ 没有提交记录" -ForegroundColor Red
            Write-Host "    解决方案: git add . && git commit -m `"Initial commit`"" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ❌ 没有提交记录" -ForegroundColor Red
        Write-Host "    解决方案: git add . && git commit -m `"Initial commit`"" -ForegroundColor Yellow
    }
    
    # 检查工作区状态
    $status = git status --porcelain
    if ($status) {
        Write-Host "  ⚠ 有未提交的更改:" -ForegroundColor Yellow
        $status | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    } else {
        Write-Host "  ✓ 工作区干净" -ForegroundColor Green
    }
    
} else {
    Write-Host "`n❌ Git仓库未初始化" -ForegroundColor Red
    Write-Host "  解决方案: git init" -ForegroundColor Yellow
}

# 3. 文件检查
Write-Host "`n[3] 重要文件检查..." -ForegroundColor Yellow

$importantFiles = @(
    ".gitignore",
    ".gitattributes", 
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md"
)

foreach ($file in $importantFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file 缺失" -ForegroundColor Red
    }
}

# 检查.gitattributes中的LFS配置
if (Test-Path ".gitattributes") {
    $lfsConfig = Get-Content ".gitattributes" | Select-String "filter=lfs"
    if ($lfsConfig) {
        Write-Host "  ✓ Git LFS配置存在" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Git LFS配置可能缺失" -ForegroundColor Yellow
    }
}

# 4. 常见问题解决方案
Write-Host "`n[4] 常见问题解决方案..." -ForegroundColor Yellow

Write-Host "`n🔧 认证问题:" -ForegroundColor White
Write-Host "  问题: fatal: Authentication failed" -ForegroundColor Red
Write-Host "  解决方案:" -ForegroundColor Yellow
Write-Host "    1. 使用Personal Access Token (推荐)" -ForegroundColor Gray
Write-Host "    2. 配置SSH密钥" -ForegroundColor Gray
Write-Host "    3. 使用GitHub CLI: gh auth login" -ForegroundColor Gray

Write-Host "`n🔧 推送被拒绝:" -ForegroundColor White
Write-Host "  问题: ! [rejected] main -> main (fetch first)" -ForegroundColor Red
Write-Host "  解决方案:" -ForegroundColor Yellow
Write-Host "    git pull origin main --allow-unrelated-histories" -ForegroundColor Gray
Write-Host "    git push origin main" -ForegroundColor Gray

Write-Host "`n🔧 大文件问题:" -ForegroundColor White
Write-Host "  问题: remote: error: File ... is ... MB; this exceeds GitHub's file size limit" -ForegroundColor Red'
Write-Host "  解决方案:" -ForegroundColor Yellow
Write-Host "    1. 使用Git LFS: git lfs track `"*.模型文件扩展名`"" -ForegroundColor Gray
Write-Host "    2. 添加到.gitignore忽略大文件" -ForegroundColor Gray

Write-Host "`n🔧 编码问题:" -ForegroundColor White
Write-Host "  问题: warning: LF will be replaced by CRLF" -ForegroundColor Red
Write-Host "  解决方案:" -ForegroundColor Yellow
Write-Host "    git config core.autocrlf true" -ForegroundColor Gray

# 5. 快速修复命令
Write-Host "`n[5] 快速修复命令..." -ForegroundColor Yellow

Write-Host "`n📋 重新配置Git用户信息:" -ForegroundColor White
Write-Host "  git config user.name `"CKEN`"" -ForegroundColor Cyan
Write-Host "  git config user.email `"your-email@example.com`"" -ForegroundColor Cyan

Write-Host "`n📋 重新配置远程仓库:" -ForegroundColor White
Write-Host "  git remote remove origin" -ForegroundColor Cyan
Write-Host "  git remote add origin https://github.com/CKEN/VisionAI-ClipsMaster.git" -ForegroundColor Cyan

Write-Host "`n📋 强制推送 (谨慎使用):" -ForegroundColor White
Write-Host "  git push -f origin main" -ForegroundColor Cyan

Write-Host "`n📋 重置到远程状态:" -ForegroundColor White
Write-Host "  git fetch origin" -ForegroundColor Cyan
Write-Host "  git reset --hard origin/main" -ForegroundColor Cyan

# 6. 验证命令
Write-Host "`n[6] 验证命令..." -ForegroundColor Yellow

Write-Host "`n📋 检查仓库状态:" -ForegroundColor White
Write-Host "  git status" -ForegroundColor Cyan
Write-Host "  git remote -v" -ForegroundColor Cyan
Write-Host "  git log --oneline -5" -ForegroundColor Cyan
Write-Host "  git tag -l" -ForegroundColor Cyan

Write-Host "`n📋 测试连接:" -ForegroundColor White
Write-Host "  git ls-remote origin" -ForegroundColor Cyan
Write-Host "  git fetch --dry-run" -ForegroundColor Cyan

Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
Write-Host "✅ 故障排除完成！" -ForegroundColor Green

Write-Host "`n💡 提示:" -ForegroundColor Yellow
Write-Host "  如果问题仍然存在，请:" -ForegroundColor White
Write-Host "  1. 检查GitHub仓库是否已创建" -ForegroundColor Gray
Write-Host "  2. 确认网络连接正常" -ForegroundColor Gray
Write-Host "  3. 验证GitHub认证设置" -ForegroundColor Gray
Write-Host "  4. 查看详细错误信息" -ForegroundColor Gray

Read-Host "`n按Enter键退出"
