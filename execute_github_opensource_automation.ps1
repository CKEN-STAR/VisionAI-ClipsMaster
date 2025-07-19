# VisionAI-ClipsMaster GitHub开源自动化脚本
# 作者: CKEN
# 版本: v1.0
# 日期: 2025-07-12

param(
    [string]$GitHubUsername = "CKEN",
    [string]$GitHubEmail = "your-email@example.com",
    [string]$RepositoryName = "VisionAI-ClipsMaster",
    [switch]$SkipCleanup = $false,
    [switch]$DryRun = $false
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "✅ $Message" "Green" }
function Write-Info { param([string]$Message) Write-ColorOutput "ℹ️  $Message" "Cyan" }
function Write-Warning { param([string]$Message) Write-ColorOutput "⚠️  $Message" "Yellow" }
function Write-Error { param([string]$Message) Write-ColorOutput "❌ $Message" "Red" }

# 检查必要工具
function Test-Prerequisites {
    Write-Info "检查必要工具..."
    
    # 检查Git
    try {
        $gitVersion = git --version
        Write-Success "Git已安装: $gitVersion"
    }
    catch {
        Write-Error "Git未安装，请先安装Git"
        exit 1
    }
    
    # 检查Python
    try {
        $pythonPath = "C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe"
        if (Test-Path $pythonPath) {
            $pythonVersion = & $pythonPath --version
            Write-Success "Python已安装: $pythonVersion"
        }
        else {
            Write-Warning "系统Python路径不存在，尝试使用默认python"
            $pythonVersion = python --version
            Write-Success "Python已安装: $pythonVersion"
        }
    }
    catch {
        Write-Error "Python未安装，请先安装Python 3.11+"
        exit 1
    }
    
    # 检查Git LFS
    try {
        $lfsVersion = git lfs version
        Write-Success "Git LFS已安装: $lfsVersion"
    }
    catch {
        Write-Warning "Git LFS未安装，将跳过大文件配置"
    }
}

# 项目清理
function Invoke-ProjectCleanup {
    if ($SkipCleanup) {
        Write-Info "跳过项目清理"
        return
    }
    
    Write-Info "开始项目清理..."
    
    # 清理缓存文件
    $cleanupPaths = @(
        "__pycache__",
        ".pytest_cache",
        "*.pyc",
        "temp",
        "tmp",
        "cache",
        "test_output",
        "*_test_report_*.json",
        "*_test_report_*.md",
        "VisionAI_ClipsMaster_*.md"
    )
    
    foreach ($path in $cleanupPaths) {
        if ($DryRun) {
            Write-Info "DRY RUN: 将删除 $path"
        }
        else {
            try {
                Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
                Write-Success "已清理: $path"
            }
            catch {
                Write-Warning "清理失败: $path"
            }
        }
    }
}

# 创建目录结构
function New-ProjectStructure {
    Write-Info "创建标准目录结构..."
    
    $directories = @(
        ".github",
        ".github/workflows",
        ".github/ISSUE_TEMPLATE",
        "docs/images",
        "examples/basic",
        "examples/advanced",
        ".vscode"
    )
    
    foreach ($dir in $directories) {
        if ($DryRun) {
            Write-Info "DRY RUN: 将创建目录 $dir"
        }
        else {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            Write-Success "已创建目录: $dir"
        }
    }
}

# 初始化Git仓库
function Initialize-GitRepository {
    Write-Info "初始化Git仓库..."
    
    if ($DryRun) {
        Write-Info "DRY RUN: 将初始化Git仓库"
        return
    }
    
    # 检查是否已经是Git仓库
    if (Test-Path ".git") {
        Write-Warning "已存在Git仓库，跳过初始化"
    }
    else {
        git init
        Write-Success "Git仓库初始化完成"
    }
    
    # 配置Git用户信息
    git config user.name $GitHubUsername
    git config user.email $GitHubEmail
    git config core.quotepath false
    git config gui.encoding utf-8
    git config i18n.commit.encoding utf-8
    git config i18n.logoutputencoding utf-8
    
    Write-Success "Git配置完成"
    
    # 设置默认分支
    git branch -M main
    Write-Success "默认分支设置为main"
}

# 创建.gitignore文件
function New-GitIgnoreFile {
    Write-Info "创建.gitignore文件..."
    
    if ($DryRun) {
        Write-Info "DRY RUN: 将创建.gitignore文件"
        return
    }
    
    $gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*`$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
.venv/
.env/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Project Specific
cache/
temp/
tmp/
logs/*.log
test_output/
*_test_report_*.json
*_test_report_*.md
recovery/
snapshots/
cleanup_backup/

# Large Files (use Git LFS)
*.mp4
*.avi
*.mkv
*.mov
*.flv
*.wmv
*.webm
*.m4v
*.3gp
*.ts
models/*/base/
models/*/quantized/
*.bin
*.gguf
*.safetensors

# Sensitive Data
.env
config/secrets/
user_config/
"@
    
    $gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8
    Write-Success ".gitignore文件创建完成"
}

# 配置Git LFS
function Initialize-GitLFS {
    Write-Info "配置Git LFS..."
    
    if ($DryRun) {
        Write-Info "DRY RUN: 将配置Git LFS"
        return
    }
    
    try {
        git lfs install
        
        # 配置大文件类型
        $lfsTypes = @(
            "*.mp4", "*.avi", "*.mkv", "*.mov", "*.flv", "*.wmv", "*.webm", "*.m4v", "*.3gp", "*.ts",
            "*.bin", "*.gguf", "*.safetensors",
            "models/*/base/*", "models/*/quantized/*"
        )
        
        foreach ($type in $lfsTypes) {
            git lfs track $type
        }
        
        Write-Success "Git LFS配置完成"
    }
    catch {
        Write-Warning "Git LFS配置失败，将跳过大文件支持"
    }
}

# 创建VSCode配置
function New-VSCodeConfig {
    Write-Info "创建VSCode配置..."
    
    if ($DryRun) {
        Write-Info "DRY RUN: 将创建VSCode配置"
        return
    }
    
    $vscodeConfig = @"
{
    "python.defaultInterpreterPath": "C:/Users/13075/AppData/Local/Programs/Python/Python313/python.exe",
    "python.terminal.activateEnvironment": false,
    "git.enabled": true,
    "git.path": "git",
    "git.autofetch": true,
    "files.encoding": "utf8",
    "files.autoGuessEncoding": true,
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/temp": true,
        "**/tmp": true,
        "**/cache": true,
        "**/test_output": true
    }
}
"@
    
    $vscodeConfig | Out-File -FilePath ".vscode/settings.json" -Encoding UTF8
    Write-Success "VSCode配置创建完成"
}

# 运行测试验证
function Invoke-TestValidation {
    Write-Info "运行测试验证..."
    
    if ($DryRun) {
        Write-Info "DRY RUN: 将运行测试验证"
        return
    }
    
    $pythonPath = "C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe"
    
    try {
        # 运行训练模块测试
        Write-Info "运行训练模块测试..."
        & $pythonPath "VisionAI-ClipsMaster-Core/training_module_comprehensive_test.py"
        Write-Success "训练模块测试完成"
        
        # 检查核心文件
        $coreFiles = @(
            "VisionAI-ClipsMaster-Core/simple_ui_fixed.py",
            "VisionAI-ClipsMaster-Core/src/core/model_switcher.py",
            "VisionAI-ClipsMaster-Core/src/training/zh_trainer.py",
            "VisionAI-ClipsMaster-Core/src/training/en_trainer.py"
        )
        
        foreach ($file in $coreFiles) {
            if (Test-Path $file) {
                Write-Success "核心文件存在: $file"
            }
            else {
                Write-Warning "核心文件缺失: $file"
            }
        }
    }
    catch {
        Write-Warning "测试验证过程中出现问题: $($_.Exception.Message)"
    }
}

# 创建提交并推送
function Invoke-GitCommitAndPush {
    Write-Info "准备Git提交..."
    
    if ($DryRun) {
        Write-Info "DRY RUN: 将创建提交并推送到GitHub"
        return
    }
    
    # 添加所有文件
    git add .
    
    # 创建提交
    $commitMessage = @"
🎉 Initial commit: VisionAI-ClipsMaster v1.0

✨ Features:
- 双模型架构 (Mistral-7B + Qwen2.5-7B)
- 4GB内存优化
- AI剧本重构
- 零损失视频拼接
- 剪映工程导出
- 训练投喂机制

🔧 Technical:
- Python 3.11+ support
- FFmpeg integration
- PyQt6 UI framework
- Comprehensive testing suite

📚 Documentation:
- Complete user guide
- Developer documentation
- API reference
- Installation instructions

👨‍💻 Author: $GitHubUsername
"@
    
    git commit -m $commitMessage
    Write-Success "Git提交创建完成"
    
    # 提示用户添加远程仓库
    Write-Info "请手动执行以下命令来推送到GitHub:"
    Write-ColorOutput "git remote add origin https://github.com/$GitHubUsername/$RepositoryName.git" "Yellow"
    Write-ColorOutput "git push -u origin main" "Yellow"
}

# 主执行函数
function Main {
    Write-ColorOutput "🚀 VisionAI-ClipsMaster GitHub开源自动化脚本" "Magenta"
    Write-ColorOutput "作者: CKEN | 版本: v1.0 | 日期: 2025-07-12" "Gray"
    Write-ColorOutput "=" * 60 "Gray"
    
    if ($DryRun) {
        Write-Warning "DRY RUN模式 - 不会执行实际操作"
    }
    
    try {
        Test-Prerequisites
        Invoke-ProjectCleanup
        New-ProjectStructure
        Initialize-GitRepository
        New-GitIgnoreFile
        Initialize-GitLFS
        New-VSCodeConfig
        Invoke-TestValidation
        Invoke-GitCommitAndPush
        
        Write-ColorOutput "=" * 60 "Gray"
        Write-Success "GitHub开源准备完成！"
        Write-Info "下一步："
        Write-Info "1. 在GitHub创建新仓库: $RepositoryName"
        Write-Info "2. 执行推送命令"
        Write-Info "3. 验证仓库内容"
        Write-Info "4. 更新README.md中的链接"
        
    }
    catch {
        Write-Error "执行过程中出现错误: $($_.Exception.Message)"
        exit 1
    }
}

# 执行主函数
Main
