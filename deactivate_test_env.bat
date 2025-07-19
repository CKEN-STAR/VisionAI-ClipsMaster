@echo off
:: VisionAI-ClipsMaster测试环境停用脚本
echo =======================================
echo  VisionAI-ClipsMaster 测试环境停用工具
echo =======================================
echo.

:: 检查是否在虚拟环境中
if "%VIRTUAL_ENV%"=="" (
    echo [警告] 当前未激活虚拟环境，无需停用
    exit /b 0
)

:: 检查是否是测试环境
echo %VIRTUAL_ENV% | findstr /i ".test_venv" > nul
if errorlevel 1 (
    echo [警告] 当前激活的不是测试环境，而是:
    echo %VIRTUAL_ENV%
    echo 如需停用，请直接使用 'deactivate' 命令
    exit /b 1
)

:: 停用虚拟环境
call deactivate

echo [成功] 测试环境已停用!
echo ======================================= 