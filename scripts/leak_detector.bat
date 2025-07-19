@echo off
REM 内存泄漏检测器 - Windows运行脚本

set PYTHONPATH=%~dp0..
cd /d "%~dp0.."

if "%1"=="--help" goto Help
if "%1"=="monitor" goto Monitor
if "%1"=="check" goto Check
if "%1"=="simulate" goto Simulate
if "%1"=="reset" goto Reset

REM 如果没有提供命令，显示帮助
python scripts/run_leak_detector.py --help
goto End

:Monitor
python scripts/run_leak_detector.py monitor %2 %3 %4 %5 %6 %7 %8 %9
goto End

:Check
python scripts/run_leak_detector.py check %2 %3 %4 %5 %6 %7 %8 %9
goto End

:Simulate
python scripts/run_leak_detector.py simulate %2 %3 %4 %5 %6 %7 %8 %9
goto End

:Reset
python scripts/run_leak_detector.py reset %2 %3 %4 %5 %6 %7 %8 %9
goto End

:Help
python scripts/run_leak_detector.py --help

:End 