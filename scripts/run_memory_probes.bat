@echo off
REM 内存探针测试脚本 - Windows版本

set PYTHONPATH=%~dp0..
cd /d "%~dp0.."

if "%1"=="--help" goto Help
if "%1"=="--python-only" goto PythonOnly
if "%1"=="--c-only" goto COnly
if "%1"=="--pressure" goto Pressure

REM 默认运行所有测试
python scripts/test_memory_probes.py
goto End

:PythonOnly
python scripts/test_memory_probes.py --python-only
goto End

:COnly
python scripts/test_memory_probes.py --c-only
goto End

:Pressure
python scripts/test_memory_probes.py --pressure
goto End

:Help
echo 内存探针测试脚本
echo 用法: %0 [选项]
echo.
echo 选项:
echo   --help            显示帮助信息
echo   --python-only     仅运行Python探针测试
echo   --c-only          仅运行C探针测试（如果可用）
echo   --pressure        包括内存压力测试
echo.
echo 示例:
echo   %0
echo   %0 --python-only
echo   %0 --pressure

:End 