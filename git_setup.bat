@echo off
REM VisionAI-ClipsMaster Windows Git初始化和配置脚本
setlocal enabledelayedexpansion

echo ========================================
echo VisionAI-ClipsMaster Git初始化和配置
echo ========================================
echo.

REM 检查Git是否安装
echo [1/8] 检查Git安装...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Git未安装，请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [INFO] Git已安装

REM 检查Git LFS是否安装
echo [2/8] 检查Git LFS...
git lfs version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Git LFS未安装，请手动安装
    echo 下载地址: https://git-lfs.github.io/
    set /p CONTINUE="是否继续? (y/N): "
    if /i "!CONTINUE!" neq "y" (
        exit /b 1
    )
) else (
    echo [INFO] Git LFS已安装
)

REM 初始化Git仓库
echo [3/8] 初始化Git仓库...
if exist ".git" (
    echo [WARNING] Git仓库已存在，跳过初始化
) else (
    git init
    echo [INFO] Git仓库初始化完成
)

REM 配置Git LFS
echo [4/8] 配置Git LFS...
git lfs install >nul 2>&1
if exist ".gitattributes" (
    echo [INFO] Git LFS配置完成
) else (
    echo [ERROR] .gitattributes文件不存在，请先运行项目组织脚本
    pause
    exit /b 1
)

REM 配置Git用户信息
echo [5/8] 配置Git用户信息...
git config user.name >nul 2>&1
if %errorLevel% neq 0 (
    set /p GIT_USERNAME="请输入Git用户名: "
    git config user.name "!GIT_USERNAME!"
)

git config user.email >nul 2>&1
if %errorLevel% neq 0 (
    set /p GIT_EMAIL="请输入Git邮箱: "
    git config user.email "!GIT_EMAIL!"
)

for /f "tokens=*" %%i in ('git config user.name') do set USERNAME=%%i
for /f "tokens=*" %%i in ('git config user.email') do set EMAIL=%%i
echo [INFO] 用户名: !USERNAME!
echo [INFO] 邮箱: !EMAIL!

REM 配置远程仓库
echo [6/8] 配置远程仓库...
git remote get-url origin >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%i in ('git remote get-url origin') do set CURRENT_REMOTE=%%i
    echo [WARNING] 远程仓库已配置: !CURRENT_REMOTE!
    set /p UPDATE_REMOTE="是否要更新远程仓库地址? (y/N): "
    if /i "!UPDATE_REMOTE!" equ "y" (
        git remote remove origin
    ) else (
        goto :skip_remote
    )
)

echo 请选择远程仓库地址格式:
echo 1. HTTPS (推荐): https://github.com/CKEN/VisionAI-ClipsMaster.git
echo 2. SSH: git@github.com:CKEN/VisionAI-ClipsMaster.git
set /p REPO_FORMAT="请选择 (1/2): "

if "!REPO_FORMAT!"=="1" (
    set REMOTE_URL=https://github.com/CKEN/VisionAI-ClipsMaster.git
) else if "!REPO_FORMAT!"=="2" (
    set REMOTE_URL=git@github.com:CKEN/VisionAI-ClipsMaster.git
) else (
    echo [ERROR] 无效选择
    pause
    exit /b 1
)

git remote add origin "!REMOTE_URL!"
echo [INFO] 远程仓库配置完成: !REMOTE_URL!

:skip_remote

REM 创建初始提交
echo [7/8] 创建初始提交...
git add .
git diff --cached --quiet
if %errorLevel% equ 0 (
    echo [WARNING] 没有文件需要提交
    goto :skip_commit
)

REM 创建提交信息
echo [INFO] 创建初始提交...
git commit -m "feat: initial release of VisionAI-ClipsMaster v1.0.0

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

BREAKING CHANGE: This is the initial release"

echo [INFO] 初始提交创建完成

:skip_commit

REM 推送到远程仓库
echo [8/8] 推送代码到远程仓库...
git branch -M main
git push -u origin main
if %errorLevel% neq 0 (
    echo [ERROR] 代码推送失败，请检查网络连接和仓库权限
    pause
    exit /b 1
)
echo [INFO] 代码推送成功

REM 创建并推送标签
echo [INFO] 创建版本标签...
git tag -a v1.0.0 -m "Release v1.0.0: Initial stable release

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

This release marks the first stable version of VisionAI-ClipsMaster."

git push origin v1.0.0
echo [INFO] 版本标签 v1.0.0 创建并推送完成

REM 验证仓库状态
echo.
echo ========================================
echo 仓库信息
echo ========================================
for /f "tokens=*" %%i in ('git remote get-url origin') do echo 远程地址: %%i
for /f "tokens=*" %%i in ('git branch --show-current') do echo 当前分支: %%i
for /f "tokens=*" %%i in ('git log --oneline -1') do echo 最新提交: %%i
for /f "tokens=*" %%i in ('git tag -l') do echo 标签列表: %%i

echo.
echo ========================================
echo Git配置完成！
echo ========================================
echo.
echo 🎯 下一步操作:
echo 1. 访问GitHub仓库查看代码
echo 2. 配置GitHub仓库设置
echo 3. 启用GitHub Actions
echo 4. 创建GitHub Release
echo 5. 设置社区功能
echo.
for /f "tokens=*" %%i in ('git remote get-url origin') do (
    set REPO_URL=%%i
    set REPO_URL=!REPO_URL:.git=!
    echo 🔗 GitHub仓库地址: !REPO_URL!
)
echo.
pause
