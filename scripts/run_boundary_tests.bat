@echo off
REM 边界条件测试运行脚本 - Windows版本

set PYTHONPATH=%~dp0..
cd /d "%~dp0.."

if "%1"=="" goto Interactive
if "%1"=="--help" goto Help
if "%1"=="--all" goto All
if "%1"=="--extended" goto Extended

REM 处理指定场景和模型的情况
set SCENARIO=
set MODEL=

:ProcessArgs
if "%1"=="" goto RunSpecific
if "%1"=="--scenario" (
    set SCENARIO=%2
    shift
    shift
    goto ProcessArgs
)
if "%1"=="--model" (
    set MODEL=%2
    shift
    shift
    goto ProcessArgs
)
if "%1"=="--output-dir" (
    set OUTPUT_DIR=%2
    shift
    shift
    goto ProcessArgs
)
shift
goto ProcessArgs

:RunSpecific
if "%SCENARIO%"=="" goto Interactive
if "%MODEL%"=="" (
    python scripts/run_boundary_tests.py --scenario "%SCENARIO%" %OUTPUT_DIR_PARAM%
) else (
    python scripts/run_boundary_tests.py --scenario "%SCENARIO%" --model "%MODEL%" %OUTPUT_DIR_PARAM%
)
goto End

:All
python scripts/run_boundary_tests.py --all %OUTPUT_DIR_PARAM%
goto End

:Extended
python scripts/run_boundary_tests.py --extended %OUTPUT_DIR_PARAM%
goto End

:Interactive
python scripts/run_boundary_tests.py --interactive %OUTPUT_DIR_PARAM%
goto End

:Help
echo 边界条件测试运行脚本
echo 用法: %0 [选项]
echo.
echo 选项:
echo   --help            显示帮助信息
echo   --all             运行所有标准测试
echo   --extended        运行所有测试(标准+扩展)
echo   --scenario NAME   指定测试场景名称
echo   --model ID        指定模型ID
echo   --output-dir DIR  指定输出目录
echo.
echo 示例:
echo   %0 --all
echo   %0 --scenario "常规4GB设备" --model "qwen2.5-7b-chat"
echo   %0 --interactive

:End 