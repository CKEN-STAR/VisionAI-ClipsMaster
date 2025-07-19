@echo off
:: 简化版覆盖率检查脚本 (Windows版本)
echo VisionAI-ClipsMaster 代码覆盖率检查

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

:: 检查Python环境
if exist ".test_venv\Scripts\activate.bat" (
    echo 使用测试虚拟环境...
    call .test_venv\Scripts\activate.bat
)

:: 运行简化版覆盖率检查脚本
python scripts\simple_coverage_check.py

:: 提示用户完成
echo.
echo 覆盖率检查完成！
pause 