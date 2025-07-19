@echo off
REM 测试权限加固脚本
REM 该脚本设置正确的测试目录权限，防止测试数据被意外修改

setlocal

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

echo 正在运行测试权限加固...

REM 执行Python脚本
python "%SCRIPT_DIR%secure_test_permissions.py" %*
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo ✓ 测试权限加固成功
) else (
    echo ✗ 测试权限加固失败，退出代码: %EXIT_CODE%
    echo   请运行 'python scripts/secure_test_permissions.py --fix' 尝试修复
)

exit /b %EXIT_CODE% 