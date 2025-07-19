@echo off
REM 内存环境测试脚本 - Windows版本
REM 在Docker容器中模拟不同内存环境

REM 确保在项目根目录运行
cd /d "%~dp0\.."

REM 设置默认参数
set ENV_PROFILE=4GB连线
set TEST_MODE=burst
set TEST_DURATION=60
set TARGET_PERCENT=70

REM 解析命令行参数
:parse_args
if "%~1"=="" goto run_test
if "%~1"=="-h" goto show_help
if "%~1"=="--help" goto show_help
if "%~1"=="-e" (
    set ENV_PROFILE=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--environment" (
    set ENV_PROFILE=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="-m" (
    set TEST_MODE=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--mode" (
    set TEST_MODE=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="-d" (
    set TEST_DURATION=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--duration" (
    set TEST_DURATION=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="-t" (
    set TARGET_PERCENT=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--target" (
    set TARGET_PERCENT=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="-l" goto list_environments
if "%~1"=="--list" goto list_environments

echo 未知选项: %~1
goto show_help

:show_help
echo 内存环境测试脚本 - Windows版本
echo 用法: %0 [选项]
echo.
echo 选项:
echo   -h, --help            显示此帮助信息
echo   -e, --environment     环境配置名称 (默认: 4GB连线)
echo   -m, --mode            测试模式: staircase, burst, sawtooth (默认: burst)
echo   -d, --duration        测试持续时间(秒) (默认: 60)
echo   -t, --target          目标内存占用百分比 (默认: 70)
echo   -l, --list            列出所有可用环境配置
echo.
echo 示例:
echo   %0 --environment "极限2GB模式" --mode staircase --duration 120
exit /b 1

:list_environments
echo 可用的测试环境配置:
python -c "from src.utils.env_simulator import EnvironmentSimulator; simulator = EnvironmentSimulator(); simulator.print_profiles()"
exit /b 0

:run_test
REM 生成Python代码来创建Docker命令
set PYTHON_CMD=from src.utils.env_simulator import EnvironmentSimulator; simulator = EnvironmentSimulator(); test_cmd = f'python src/utils/memory_test_cli.py simple --mode=%TEST_MODE% --target=%TARGET_PERCENT% --duration=%TEST_DURATION%'; cmd = simulator.generate_docker_command(profile_name='%ENV_PROFILE%', command=test_cmd); print(cmd)

REM 执行Python命令并捕获输出
for /f "delims=" %%a in ('python -c "%PYTHON_CMD%"') do (
    set DOCKER_CMD=%%a
)

REM 检查命令是否成功生成
if "%DOCKER_CMD%"=="" (
    echo 错误: 无法生成Docker命令，请检查环境配置名称是否正确
    goto list_environments
)

REM 输出测试信息
echo === 内存环境测试 ===
echo 环境配置: %ENV_PROFILE%
echo 测试模式: %TEST_MODE%
echo 测试时间: %TEST_DURATION% 秒
echo 目标占用: %TARGET_PERCENT%%%
echo.
echo 执行命令:
echo %DOCKER_CMD%
echo.
echo 启动测试...

REM 执行Docker命令
%DOCKER_CMD%

echo.
echo 测试完成
exit /b 0 