@echo off
REM 量化策略验证测试运行脚本

setlocal enabledelayedexpansion

REM 切换到项目根目录
cd /d "%~dp0\.."

echo 运行量化策略验证测试...

REM 检查Python可用性
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python 未安装或不在系统路径中，请安装Python并确保其在PATH中。
    exit /b 1
)

REM 处理命令行参数
set ARGS=
if "%1"=="--verbose" (
    set ARGS=!ARGS! -v
) else if "%1"=="-v" (
    set ARGS=!ARGS! -v
)

if "%2"=="--report" (
    set ARGS=!ARGS! -r
) else if "%2"=="-r" (
    set ARGS=!ARGS! -r
) else if "%1"=="--report" (
    set ARGS=!ARGS! -r
) else if "%1"=="-r" (
    set ARGS=!ARGS! -r
)

REM 运行测试
python tests/run_quant_strategy_tests.py !ARGS!

if %ERRORLEVEL% neq 0 (
    echo 测试失败，请查看日志获取详细信息。
    exit /b 1
) else (
    echo 所有测试通过！
    exit /b 0
) 