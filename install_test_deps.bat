@echo off
:: VisionAI-ClipsMaster测试依赖安装脚本
echo =======================================
echo  VisionAI-ClipsMaster 测试依赖安装工具
echo =======================================
echo.

:: 检查是否在虚拟环境中
if "%VIRTUAL_ENV%"=="" (
    echo [错误] 未激活虚拟环境，请先激活测试环境
    echo 运行 activate_test_env.bat 激活测试环境
    
    echo 是否要自动激活测试环境? (Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        call activate_test_env.bat
        if errorlevel 1 exit /b 1
    ) else (
        exit /b 1
    )
)

:: 检查是否是测试环境
echo %VIRTUAL_ENV% | findstr /i ".test_venv" > nul
if errorlevel 1 (
    echo [警告] 当前激活的不是测试环境，而是:
    echo %VIRTUAL_ENV%
    echo 建议在测试环境中安装依赖，以避免影响开发环境
    
    echo 是否继续安装? (Y/N)
    set /p choice=
    if /i "%choice%" neq "Y" exit /b 0
)

:: 更新pip
echo [步骤1/3] 更新pip...
python -m pip install --upgrade pip

:: 安装wheel和setuptools
echo [步骤2/3] 安装基础包...
python -m pip install wheel setuptools

:: 安装测试依赖
echo [步骤3/3] 安装测试依赖...
python -m pip install -r requirements_test.txt

echo.
echo [成功] 测试依赖安装完成!
echo ======================================= 