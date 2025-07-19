@echo off
:: 边界条件测试运行脚本 (Windows版本)
:: 运行视频处理边界条件专项测试

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

:: 确保安装了需要的依赖
python -m pip install pytest pytest-html --quiet

:: 检查HTML报告参数
set HTML_FLAG=
if "%~1"=="--no-html" (
    set HTML_FLAG=--no-html
    shift
)

:: 检查详细输出参数
set VERBOSE_FLAG=
if "%~1"=="--no-verbose" (
    set VERBOSE_FLAG=--no-verbose
    shift
)

:: 运行边界条件测试
echo.
echo ========================================
echo     运行视频处理边界条件专项测试
echo ========================================
echo.

python scripts\run_edge_case_tests.py %HTML_FLAG% %VERBOSE_FLAG%

:: 保存退出状态
set EXIT_CODE=%ERRORLEVEL%

:: 打开报告(如果存在且测试失败)
if %EXIT_CODE% NEQ 0 (
    for /f %%i in ('dir /b /od tests\reports\edge_case_report_*.html 2^>NUL') do (
        set "LATEST_REPORT=%%i"
    )
    
    if defined LATEST_REPORT (
        echo.
        echo 查看最新测试报告: tests\reports\!LATEST_REPORT!
        echo.
        start "" "tests\reports\!LATEST_REPORT!"
    )
)

echo.
echo 测试完成，退出代码: %EXIT_CODE%
echo 测试时间: %TIME%

:: 退出，传递原始退出码
exit /b %EXIT_CODE% 