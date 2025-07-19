@echo off
REM 黄金样本生成批处理脚本 (Windows版)

echo 正在运行VisionAI-ClipsMaster黄金样本生成...
echo.

set PYTHONPATH=%PYTHONPATH%;%~dp0..\..

REM 检查命令行参数
if "%1"=="--help" (
    echo 使用方法: generate_golden_samples.bat [选项]
    echo.
    echo 选项:
    echo   --version [版本号]  指定版本号(默认: 1.0.0)
    echo   --list             列出所有已生成的样本
    echo   --update-index     仅更新样本索引
    echo   --log-level [级别] 设置日志级别(DEBUG/INFO/WARNING/ERROR)
    echo   --help             显示此帮助信息
    exit /b 0
)

REM 设置默认参数
set VERSION=1.0.0
set ACTION=--generate
set LOG_LEVEL=INFO

REM 解析命令行参数
:parse_args
if "%1"=="" goto run_script
if "%1"=="--version" (
    set VERSION=%2
    shift
) else if "%1"=="--list" (
    set ACTION=--list
) else if "%1"=="--update-index" (
    set ACTION=--update-index
) else if "%1"=="--log-level" (
    set LOG_LEVEL=%2
    shift
) else (
    echo 未知选项: %1
    echo 使用 generate_golden_samples.bat --help 查看帮助
    exit /b 1
)
shift
goto parse_args

:run_script
REM 运行样本生成脚本
python "%~dp0run_golden_sample_generation.py" %ACTION% --version %VERSION% --log-level %LOG_LEVEL%

REM 检查结果
if errorlevel 1 (
    echo.
    echo 样本生成失败! 详见上方输出。
    exit /b 1
) else (
    echo.
    echo 操作成功完成!
    exit /b 0
) 