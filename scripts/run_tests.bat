@echo off
REM VisionAI-ClipsMaster 测试运行脚本
REM 提供多种测试运行方式，支持覆盖率报告生成

setlocal enabledelayedexpansion

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM 默认参数
set "TEST_DIR=%PROJECT_ROOT%\tests"
set "REPORT_DIR=%TEST_DIR%\reports"
set "COVERAGE_DIR=%REPORT_DIR%\coverage"
set MODE=all
set CATEGORY=
set VERBOSE=0
set COVERAGE=0
set MEMORY_CHECK=0
set PARALLEL=0

REM 颜色定义（Windows 10+支持）
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

REM 解析命令行参数
:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="-m" (
    set "MODE=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--mode" (
    set "MODE=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-c" (
    set "CATEGORY=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--category" (
    set "CATEGORY=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-v" (
    set VERBOSE=1
    shift
    goto :parse_args
)
if /i "%~1"=="--verbose" (
    set VERBOSE=1
    shift
    goto :parse_args
)
if /i "%~1"=="--cov" (
    set COVERAGE=1
    shift
    goto :parse_args
)
if /i "%~1"=="--memory-check" (
    set MEMORY_CHECK=1
    shift
    goto :parse_args
)
if /i "%~1"=="-j" (
    set PARALLEL=1
    shift
    goto :parse_args
)
if /i "%~1"=="--parallel" (
    set PARALLEL=1
    shift
    goto :parse_args
)
if /i "%~1"=="-h" (
    call :show_help
    exit /b 0
)
if /i "%~1"=="--help" (
    call :show_help
    exit /b 0
)
echo %RED%错误：未知选项 %1%NC%
call :show_help
exit /b 1

:end_parse_args

REM 确保报告目录存在
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"
if not exist "%COVERAGE_DIR%" mkdir "%COVERAGE_DIR%"

REM 构建 pytest 命令
set "PYTEST_CMD=python -m pytest"

REM 添加测试路径
if "%MODE%"=="all" (
    set "PYTEST_CMD=%PYTEST_CMD% %TEST_DIR%"
) else if "%MODE%"=="unit" (
    set "PYTEST_CMD=%PYTEST_CMD% %TEST_DIR%\unit"
) else if "%MODE%"=="functional" (
    set "PYTEST_CMD=%PYTEST_CMD% %TEST_DIR%\functional"
) else if "%MODE%"=="integration" (
    set "PYTEST_CMD=%PYTEST_CMD% %TEST_DIR%\integration"
) else if "%MODE%"=="memory" (
    set "PYTEST_CMD=%PYTEST_CMD% %TEST_DIR%\memory"
) else if "%MODE%"=="performance" (
    set "PYTEST_CMD=%PYTEST_CMD% %TEST_DIR%\performance"
) else (
    echo %RED%错误：未知测试模式 %MODE%%NC%
    call :show_help
    exit /b 1
)

REM 添加类别过滤
if not "%CATEGORY%"=="" (
    set "PYTEST_CMD=%PYTEST_CMD% -k %CATEGORY%"
)

REM 添加详细输出
if %VERBOSE%==1 (
    set "PYTEST_CMD=%PYTEST_CMD% -v"
)

REM 添加覆盖率报告
if %COVERAGE%==1 (
    set "PYTEST_CMD=%PYTEST_CMD% --cov=src --cov-report=html:%COVERAGE_DIR% --cov-report=term"
)

REM 添加内存监控
if %MEMORY_CHECK%==1 (
    set "PYTEST_CMD=%PYTEST_CMD% --memory-check"
)

REM 添加并行运行
if %PARALLEL%==1 (
    set "PYTEST_CMD=%PYTEST_CMD% -xvs -n auto"
)

REM 显示即将执行的命令
echo %YELLOW%执行: %PYTEST_CMD%%NC%
echo.

REM 执行测试命令
%PYTEST_CMD%
set RESULT=%ERRORLEVEL%

REM 显示测试结果
echo.
if %RESULT%==0 (
    echo %GREEN%✓ 测试通过%NC%
    
    REM 如果生成了覆盖率报告，显示报告路径
    if %COVERAGE%==1 (
        echo %GREEN%覆盖率报告已生成: %COVERAGE_DIR%\index.html%NC%
    )
) else (
    echo %RED%✗ 测试失败%NC%
)

echo.
echo 日志文件: %REPORT_DIR%\pytest.log
echo.

exit /b %RESULT%

:show_help
echo VisionAI-ClipsMaster 测试运行工具
echo.
echo 用法: %0 [选项]
echo.
echo 选项:
echo   -m, --mode MODE       测试模式 (all, unit, functional, integration, memory)
echo   -c, --category CAT    指定测试类别
echo   -v, --verbose         详细输出
echo   --cov                 生成覆盖率报告
echo   --memory-check        内存使用监控
echo   -j, --parallel        并行运行测试
echo   -h, --help            显示此帮助信息
echo.
echo 示例:
echo   %0 --mode unit --cov  运行单元测试并生成覆盖率报告
echo   %0 --category model   运行模型相关测试
echo.
exit /b 0 