@echo off
:: 设置控制台编码为UTF-8
chcp 65001 >nul

:: 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set LANG=zh_CN.UTF-8
set LC_ALL=zh_CN.UTF-8

echo 正在启动 VisionAI-ClipsMaster...
echo.
echo 设置中文环境... 请稍候...

:: 运行中文UI启动器
python chinese_ui.py

:: 如果启动失败，则尝试直接运行原始脚本
if %ERRORLEVEL% NEQ 0 (
    echo 中文启动器失败，尝试使用普通方式启动...
    python simple_ui.py
)

:: 启动失败时等待用户输入
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 启动失败，请截图此界面联系技术支持。
    pause
) 