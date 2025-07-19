@echo off
:: 覆盖率强制检查运行脚本 (Windows版本)
:: 用法: run_coverage_check.bat [--strict]

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

:: 检查必要的依赖
python -m pip install pytest pytest-cov coverage --quiet

:: 默认参数
set "STRICT_MODE="
set "TEST_DIRS=tests/unit_test"
set "OUTPUT_DIR=coverage_reports"

:: 处理命令行参数
:parse_args
if "%~1"=="" goto run
if "%~1"=="--strict" (
    set "STRICT_MODE=--strict"
    shift
    goto parse_args
)
if "%~1:~0,12%"=="--test-dirs=" (
    set "TEST_DIRS=%~1:~12%"
    shift
    goto parse_args
)
if "%~1:~0,13%"=="--output-dir=" (
    set "OUTPUT_DIR=%~1:~13%"
    shift
    goto parse_args
)
shift
goto parse_args

:run
:: 执行覆盖率检查脚本
echo 运行覆盖率强制检查...
python scripts/enforce_coverage.py --test-dirs "%TEST_DIRS%" --output-dir "%OUTPUT_DIR%" %STRICT_MODE%

:: 保存退出状态
set EXIT_CODE=%ERRORLEVEL%

:: 如果生成了HTML报告，显示报告路径
if exist "%OUTPUT_DIR%\html" (
    set "HTML_PATH=%PROJECT_ROOT%\%OUTPUT_DIR%\html\index.html"
    echo.
    echo 覆盖率HTML报告已生成: !HTML_PATH!
    
    :: 尝试使用系统默认浏览器打开报告
    echo 尝试打开报告...
    start "" "!HTML_PATH!"
)

:: 退出，传递原始退出码
exit /b %EXIT_CODE% 