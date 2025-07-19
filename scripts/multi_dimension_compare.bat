@echo off
:: 多维度比对工具批处理脚本
:: 此脚本用于在Windows环境下方便地调用多维度比对工具

setlocal enabledelayedexpansion

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

:: 标题
echo.
echo ========================================
echo     VisionAI-ClipsMaster 多维度比对工具
echo ========================================
echo.

:: 检查Python环境
echo 检查Python环境...
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH中
    exit /b 1
)

:: 检查OpenCV等依赖库
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
    echo   multi_dimension_compare.bat ^<测试输出文件^> [选项]
    echo.
    echo 选项:
    echo   --golden ^| -g ^<黄金样本文件^>  指定黄金样本文件（不提供则自动推断）
    echo   --threshold ^| -t ^<阈值^>      设置通过阈值（0-1之间，默认0.8）
    echo   --format ^| -f ^<格式^>         输出格式（text, json, html，默认text）
    echo   --output ^| -o ^<输出文件^>     输出文件路径（不提供则输出到控制台）
    echo.
    echo 例如:
    echo   multi_dimension_compare.bat D:\videos\test_output
    echo   multi_dimension_compare.bat D:\videos\test_output --golden D:\golden\sample --format html --output report.html
    echo.
    exit /b 0
)

:: 传递参数给Python脚本
python %SCRIPT_DIR%\multi_dimension_compare.py %*
exit /b %ERRORLEVEL% 