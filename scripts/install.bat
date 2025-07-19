@echo off
REM VisionAI-ClipsMaster Windows 自动安装脚本
REM 支持 Windows 10/11，自动检测环境并安装依赖

setlocal enabledelayedexpansion

echo ========================================
echo VisionAI-ClipsMaster 自动安装程序
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] 检测到管理员权限
) else (
    echo [WARNING] 建议以管理员身份运行以获得最佳体验
)

REM 检查Python安装
echo [1/8] 检查Python环境...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python版本: %PYTHON_VERSION%

REM 检查Python版本
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python版本过低，需要3.8+，当前版本: %PYTHON_VERSION%
    pause
    exit /b 1
)

REM 检查pip
echo [2/8] 检查pip...
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] pip未安装，正在尝试安装...
    python -m ensurepip --upgrade
    if %errorLevel% neq 0 (
        echo [ERROR] pip安装失败
        pause
        exit /b 1
    )
)

REM 升级pip
echo [INFO] 升级pip到最新版本...
python -m pip install --upgrade pip

REM 检查Git
echo [3/8] 检查Git...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] 未检测到Git，将使用下载方式获取代码
    set USE_GIT=false
) else (
    echo [INFO] Git可用
    set USE_GIT=true
)

REM 检查系统内存
echo [4/8] 检查系统配置...
for /f "skip=1" %%p in ('wmic computersystem get TotalPhysicalMemory') do (
    set MEMORY_BYTES=%%p
    goto :memory_done
)
:memory_done
set /a MEMORY_GB=!MEMORY_BYTES!/1024/1024/1024
echo [INFO] 系统内存: %MEMORY_GB%GB

REM 确定安装模式
if %MEMORY_GB% LEQ 4 (
    set INSTALL_MODE=lite
    echo [INFO] 检测到4GB内存，使用轻量化模式
) else (
    set INSTALL_MODE=full
    echo [INFO] 检测到%MEMORY_GB%GB内存，使用完整模式
)

REM 创建安装目录
echo [5/8] 创建安装目录...
set INSTALL_DIR=%USERPROFILE%\VisionAI-ClipsMaster
if exist "%INSTALL_DIR%" (
    echo [WARNING] 目录已存在: %INSTALL_DIR%
    set /p OVERWRITE="是否覆盖现有安装? (y/N): "
    if /i "!OVERWRITE!" neq "y" (
        echo [INFO] 安装取消
        pause
        exit /b 0
    )
    rmdir /s /q "%INSTALL_DIR%"
)

mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

REM 下载项目代码
echo [6/8] 下载项目代码...
if "%USE_GIT%"=="true" (
    echo [INFO] 使用Git克隆仓库...
    git clone https://github.com/CKEN/VisionAI-ClipsMaster.git .
    if %errorLevel% neq 0 (
        echo [ERROR] Git克隆失败
        pause
        exit /b 1
    )
) else (
    echo [INFO] 下载ZIP文件...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/CKEN/VisionAI-ClipsMaster/archive/main.zip' -OutFile 'main.zip'"
    if %errorLevel% neq 0 (
        echo [ERROR] 下载失败
        pause
        exit /b 1
    )
    
    echo [INFO] 解压文件...
    powershell -Command "Expand-Archive -Path 'main.zip' -DestinationPath '.'"
    move VisionAI-ClipsMaster-main\* .
    rmdir /s /q VisionAI-ClipsMaster-main
    del main.zip
)

REM 创建虚拟环境
echo [7/8] 创建虚拟环境...
python -m venv venv
if %errorLevel% neq 0 (
    echo [ERROR] 虚拟环境创建失败
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo [INFO] 安装Python依赖...
if "%INSTALL_MODE%"=="lite" (
    pip install -r requirements\requirements-lite.txt
) else (
    pip install -r requirements\requirements.txt
)

if %errorLevel% neq 0 (
    echo [ERROR] 依赖安装失败
    pause
    exit /b 1
)

REM 环境检查
echo [8/8] 验证安装...
python scripts\check_environment.py
if %errorLevel% neq 0 (
    echo [WARNING] 环境检查发现问题，但安装已完成
)

REM 创建桌面快捷方式
echo [INFO] 创建桌面快捷方式...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\VisionAI-ClipsMaster.lnk
set TARGET_PATH=%INSTALL_DIR%\venv\Scripts\python.exe
set ARGUMENTS=%INSTALL_DIR%\src\visionai_clipsmaster\ui\main_window.py
set WORKING_DIR=%INSTALL_DIR%

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%TARGET_PATH%'; $Shortcut.Arguments = '%ARGUMENTS%'; $Shortcut.WorkingDirectory = '%WORKING_DIR%'; $Shortcut.Save()"

REM 创建启动脚本
echo [INFO] 创建启动脚本...
echo @echo off > start_visionai.bat
echo cd /d "%INSTALL_DIR%" >> start_visionai.bat
echo call venv\Scripts\activate.bat >> start_visionai.bat
echo python src\visionai_clipsmaster\ui\main_window.py >> start_visionai.bat
echo pause >> start_visionai.bat

REM 下载模型提示
echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 安装位置: %INSTALL_DIR%
echo 启动方式:
echo   1. 双击桌面快捷方式 "VisionAI-ClipsMaster"
echo   2. 运行 start_visionai.bat
echo   3. 手动激活环境后运行程序
echo.
echo 下一步：下载AI模型
echo   cd "%INSTALL_DIR%"
echo   call venv\Scripts\activate.bat
echo   python scripts\setup_models.py --setup
echo.
echo 首次使用建议：
echo   1. 运行环境检查: python scripts\check_environment.py
echo   2. 下载推荐模型: python scripts\setup_models.py --setup
echo   3. 运行测试: python scripts\run_tests.py
echo.

REM 询问是否立即下载模型
set /p DOWNLOAD_MODELS="是否现在下载AI模型? (y/N): "
if /i "%DOWNLOAD_MODELS%"=="y" (
    echo [INFO] 开始下载模型...
    python scripts\setup_models.py --setup
)

echo.
echo 安装完成！按任意键退出...
pause >nul
