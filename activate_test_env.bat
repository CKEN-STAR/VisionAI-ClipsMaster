@echo off
:: VisionAI-ClipsMaster测试环境激活脚本
echo =======================================
echo  VisionAI-ClipsMaster 测试环境激活工具
echo =======================================
echo.

:: 检查虚拟环境是否存在
if not exist .test_venv (
    echo [错误] 测试虚拟环境不存在，请先运行创建环境的命令
    echo python -m venv .test_venv
    exit /b 1
)

:: 如果已经在测试环境中，则不需要再次激活
if not "%VIRTUAL_ENV%"=="" (
    echo %VIRTUAL_ENV% | findstr /i ".test_venv" > nul
    if not errorlevel 1 (
        echo [提示] 已经在测试环境中，无需再次激活
        echo 当前环境: %VIRTUAL_ENV%
        exit /b 0
    )
)

:: 激活虚拟环境
call .test_venv\Scripts\activate

:: 检查激活是否成功
if not "%VIRTUAL_ENV%"=="" (
    echo [成功] 测试环境已激活!
    echo 环境路径: %VIRTUAL_ENV%
    echo.
    echo 提示: 使用 'deactivate' 命令退出测试环境
    echo       或运行 'deactivate_test_env.bat' 脚本
) else (
    echo [错误] 环境激活失败，请检查虚拟环境是否正确创建
    exit /b 1
)

echo ======================================= 