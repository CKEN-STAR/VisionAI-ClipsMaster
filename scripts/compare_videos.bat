@echo off
:: 视频相似度比较工具批处理脚本
:: 此脚本用于在Windows环境下方便地调用视频相似度比较工具

setlocal enabledelayedexpansion

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

:: 标题
echo.
echo ========================================
echo     VisionAI-ClipsMaster 视频相似度比较工具
echo ========================================
echo.

:: 检查Python环境
echo 检查Python环境...
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH中
    exit /b 1
)

:: 检查OpenCV依赖
echo 检查依赖库...
python -c "import cv2, numpy, scipy" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 警告: 缺少必要的依赖库，尝试安装...
    python -m pip install opencv-python numpy scipy
    if %ERRORLEVEL% NEQ 0 (
        echo 错误: 依赖库安装失败，请手动安装以下库:
        echo   - opencv-python
        echo   - numpy
        echo   - scipy
        exit /b 1
    )
)

:: 显示使用帮助
if "%~1"=="" (
    echo 使用方法:
    echo.
    echo   比较两个视频:
    echo   compare_videos.bat compare 视频文件1 视频文件2
    echo.
    echo   批量查找相似视频:
    echo   compare_videos.bat batch 目标视频 视频目录 [--threshold 阈值] [--limit 结果数量限制]
    echo.
    echo 例如:
    echo   compare_videos.bat compare D:\videos\sample1.mp4 D:\videos\sample2.mp4
    echo   compare_videos.bat batch D:\videos\target.mp4 D:\videos\collection --threshold 0.8
    echo.
    exit /b 0
)

:: 传递参数给Python脚本
python %SCRIPT_DIR%\compare_videos.py %*
exit /b %ERRORLEVEL% 