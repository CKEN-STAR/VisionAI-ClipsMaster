@echo off
REM 配置系统测试运行脚本 (Windows版)

echo 正在运行VisionAI-ClipsMaster配置系统测试...
echo.

set PYTHONPATH=%PYTHONPATH%;%~dp0..

REM 检查命令行参数
if "%1"=="--help" (
    echo 使用方法: run_config_tests.bat [选项]
    echo.
    echo 选项:
    echo   --test [类名]     运行指定的测试类
    echo   -v, --verbose     增加输出详细级别
    echo   --report          生成测试报告
    echo   --help            显示此帮助信息
    exit /b 0
)

REM 设置命令行参数
set ARGS=

:parse_args
if "%1"=="" goto run_tests
if "%1"=="--test" (
    set ARGS=%ARGS% --test %2
    shift
) else if "%1"=="-v" (
    set ARGS=%ARGS% -v
) else if "%1"=="--verbose" (
    set ARGS=%ARGS% -v
) else if "%1"=="--report" (
    set ARGS=%ARGS% --report
) else (
    echo 未知选项: %1
    echo 使用 run_config_tests.bat --help 查看帮助
    exit /b 1
)
shift
goto parse_args

:run_tests
REM 运行测试
python -m tests.config_test.run_config_tests %ARGS%

REM 检查结果
if errorlevel 1 (
    echo.
    echo 测试失败! 详见上方输出。
    exit /b 1
) else (
    echo.
    echo 测试成功完成!
    exit /b 0
) 