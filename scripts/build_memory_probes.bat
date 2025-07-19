@echo off
REM 内存探针C扩展构建脚本 - Windows版本

set PYTHONPATH=%~dp0..
cd /d "%~dp0.."

if "%1"=="--help" goto Help
if "%1"=="--clean" goto Clean
if "%1"=="--debug" goto Debug

REM 默认构建
python scripts/build_memory_probes.py
goto End

:Clean
python scripts/build_memory_probes.py --clean
goto End

:Debug
python scripts/build_memory_probes.py --debug
goto End

:Help
echo 内存探针C扩展构建脚本
echo 用法: %0 [选项]
echo.
echo 选项:
echo   --help            显示帮助信息
echo   --clean           在构建前清理目标文件
echo   --debug           使用调试模式构建
echo.
echo 示例:
echo   %0
echo   %0 --clean
echo   %0 --debug

:End 