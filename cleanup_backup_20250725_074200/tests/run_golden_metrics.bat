@echo off
REM VisionAI-ClipsMaster 黄金指标验证批处理脚本
REM 此脚本提供了运行黄金指标验证的便捷方式

setlocal enabledelayedexpansion

echo VisionAI-ClipsMaster 黄金指标验证工具
echo =======================================

:parse_args
if "%1"=="" goto :show_help
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

if "%1"=="--show-standards" (
    python tests/run_golden_metrics_validation.py --show-standards
    goto :end
)

if "%1"=="--verify" (
    echo 正在执行基本验证...
    python tests/run_golden_metrics_validation.py --html
    goto :end
)

if "%1"=="--continuous" (
    set interval=15
    if not "%2"=="" (
        set interval=%2
    )
    echo 启动持续验证模式（间隔 !interval! 分钟）...
    python tests/run_golden_metrics_validation.py --continuous --interval !interval! --html
    goto :end
)

if "%1"=="--system" (
    echo 只验证系统级指标...
    python tests/run_golden_metrics_validation.py --categories system --html
    goto :end
)

if "%1"=="--app" (
    echo 只验证应用级指标...
    python tests/run_golden_metrics_validation.py --categories application --html
    goto :end
)

if "%1"=="--model" (
    echo 只验证模型推理指标...
    python tests/run_golden_metrics_validation.py --categories inference --html
    goto :end
)

if "%1"=="--ux" (
    echo 只验证用户体验指标...
    python tests/run_golden_metrics_validation.py --categories user_experience --html
    goto :end
)

if "%1"=="--io" (
    echo 只验证缓存和IO指标...
    python tests/run_golden_metrics_validation.py --categories cache_io --html
    goto :end
)

echo 未知的命令: %1
goto :show_help

:show_help
echo.
echo 使用方法:
echo   run_golden_metrics.bat [选项]
echo.
echo 可用选项:
echo   --help, -h         显示此帮助信息
echo   --show-standards   显示所有的黄金标准值
echo   --verify           执行验证并生成HTML报告
echo   --continuous [分钟] 持续运行验证，可指定间隔时间（默认15分钟）
echo   --system           只验证系统级指标
echo   --app              只验证应用级指标
echo   --model            只验证模型推理指标
echo   --ux               只验证用户体验指标
echo   --io               只验证缓存和IO指标
echo.
echo 示例:
echo   run_golden_metrics.bat --verify
echo   run_golden_metrics.bat --continuous 30
echo.

:end
endlocal 