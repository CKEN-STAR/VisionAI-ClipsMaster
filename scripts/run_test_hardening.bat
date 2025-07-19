@echo off
REM 测试权限加固一键运行脚本
REM 该脚本执行完整的测试权限加固流程

setlocal

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

echo ===================================================
echo            VisionAI-ClipsMaster                   
echo             测试权限加固工具                      
echo ===================================================
echo.

REM 执行Python脚本
python "%SCRIPT_DIR%run_test_hardening.py" %*
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo ✅ 测试权限加固成功完成！
) else (
    echo.
    echo ❌ 测试权限加固失败，退出代码: %EXIT_CODE%
)

exit /b %EXIT_CODE% 