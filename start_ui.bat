@echo off
echo ============================================
echo VisionAI-ClipsMaster UI 启动器
echo ============================================

echo 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo Python未找到，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

echo.
echo 检查PyQt6...
python -c "import PyQt6; print('PyQt6 可用')"
if %errorlevel% neq 0 (
    echo PyQt6未安装，正在尝试安装...
    pip install PyQt6
    if %errorlevel% neq 0 (
        echo PyQt6安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动UI...
python simple_ui_fixed.py

if %errorlevel% neq 0 (
    echo.
    echo UI启动失败，尝试启动测试UI...
    python test_ui_simple.py
)

echo.
echo 按任意键退出...
pause
