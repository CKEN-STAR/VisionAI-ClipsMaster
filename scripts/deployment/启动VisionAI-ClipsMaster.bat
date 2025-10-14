@echo off
chcp 65001 > nul
title VisionAI-ClipsMaster v1.0.1

echo.
echo ========================================
echo  VisionAI-ClipsMaster v1.0.1
echo  AI驱动的短剧混剪工具
echo ========================================
echo.

:: 切换到程序目录
cd /d "%~dp0"

:: 检查Python是否可用
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo.
    echo 请确保已安装Python 3.8或更高版本
    echo 或者使用包含Python的完整版本
    echo.
    pause
    exit /b 1
)

:: 检查主启动器是否存在
if not exist "packaging\launcher.py" (
    echo ❌ 错误: 找不到启动器文件
    echo.
    echo 请确保程序文件完整
    echo.
    pause
    exit /b 1
)

:: 启动程序
echo 🚀 正在启动VisionAI-ClipsMaster...
echo.

python packaging\launcher.py

:: 检查启动结果
if errorlevel 1 (
    echo.
    echo ❌ 程序启动失败
    echo.
    echo 请检查:
    echo 1. 系统要求是否满足
    echo 2. 网络连接是否正常
    echo 3. 磁盘空间是否充足
    echo 4. 是否以管理员身份运行
    echo.
    echo 详细错误信息请查看 logs 目录下的日志文件
    echo.
) else (
    echo.
    echo ✅ 程序已正常退出
    echo.
)

pause
