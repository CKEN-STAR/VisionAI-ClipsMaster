@echo off
:: 黄金样本库生成和验证批处理脚本
:: 此脚本用于生成标准黄金样本并验证其完整性

setlocal enabledelayedexpansion

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

:: 标题
echo.
echo ========================================
echo     VisionAI-ClipsMaster 黄金样本库
echo ========================================
echo.

:: 检查Python环境
echo 检查Python环境...
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH中
    exit /b 1
)

:: 处理命令行参数
set FORCE=
set VERIFY_ONLY=
set VERBOSE=

:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="--force" (
    set FORCE=--force
    shift
    goto :parse_args
)
if /i "%~1"=="-f" (
    set FORCE=--force
    shift
    goto :parse_args
)
if /i "%~1"=="--verify-only" (
    set VERIFY_ONLY=1
    shift
    goto :parse_args
)
if /i "%~1"=="-v" (
    set VERIFY_ONLY=1
    shift
    goto :parse_args
)
if /i "%~1"=="--verbose" (
    set VERBOSE=--verbose
    shift
    goto :parse_args
)
shift
goto :parse_args
:end_parse_args

:: 如果仅验证
if defined VERIFY_ONLY (
    echo 正在验证黄金样本库...
    python tests\golden_samples\verify_samples.py %VERBOSE% --build-if-missing
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo 黄金样本库验证失败！
        exit /b 1
    ) else (
        echo.
        echo 黄金样本库验证成功！
        exit /b 0
    )
)

:: 生成样本
echo 正在生成黄金样本库...
python tests\golden_samples\generate_samples.py %FORCE%
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 黄金样本库生成失败！
    exit /b 1
)

:: 验证样本
echo.
echo 正在验证黄金样本库...
python tests\golden_samples\verify_samples.py %VERBOSE%
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 黄金样本库验证失败！
    exit /b 1
) else (
    echo.
    echo 黄金样本库生成并验证成功！
)

:: 显示样本信息
echo.
echo 样本目录:
echo  - 中文样本: tests\golden_samples\zh\
echo  - 英文样本: tests\golden_samples\en\
echo  - 元数据文件: tests\golden_samples\metadata.json
echo.

exit /b 0 