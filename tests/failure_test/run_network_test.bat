@echo off
REM 网络故障测试运行脚本 (Windows)
REM 需要管理员权限运行以正常操作网络设置

echo VisionAI-ClipsMaster 网络故障测试工具
echo ========================================
echo.

REM 检查权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 需要管理员权限来运行网络测试
    echo 请右键点击此脚本并选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

REM 执行Python脚本
echo 正在启动网络故障测试...
echo.

set PYTHONPATH=%~dp0..\..
python "%~dp0\run_network_failure_test.py" %*

REM 检查是否有错误
if %errorLevel% neq 0 (
    echo.
    echo 网络故障测试运行出错，退出代码: %errorLevel%
    echo 请检查日志获取详细信息。
    echo.
) else (
    echo.
    echo 网络故障测试完成。
)

pause 