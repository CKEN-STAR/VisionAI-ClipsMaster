@echo off
:: 测试报告生成批处理脚本
:: 运行测试并生成测试质量报告

setlocal enabledelayedexpansion

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

:: 检查Python环境
if exist ".test_venv\Scripts\activate.bat" (
    echo 使用测试虚拟环境...
    call .test_venv\Scripts\activate.bat
)

:: 处理命令行参数
set PYTHON_ARGS=
if "%~1"=="--no-test" (
    set PYTHON_ARGS=--no-test
    shift
)

if not "%~1"=="" (
    set PYTHON_ARGS=%PYTHON_ARGS% --output="%~1"
)

:: 运行报告生成脚本
echo.
echo ========================================
echo     生成VisionAI-ClipsMaster测试报告
echo ========================================
echo.

python scripts\generate_test_report.py %PYTHON_ARGS%

:: 保存退出状态
set EXIT_CODE=%ERRORLEVEL%

:: 处理退出状态
if %EXIT_CODE% NEQ 0 (
    echo.
    echo 测试报告生成失败，错误码: %EXIT_CODE%
) else (
    echo.
    echo 测试报告生成成功
)

echo.
echo 完成时间: %TIME%
exit /b %EXIT_CODE% 