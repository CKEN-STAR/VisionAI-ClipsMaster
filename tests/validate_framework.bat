@echo off
REM VisionAI-ClipsMaster 框架验证脚本
REM 验证项目环境、结构和依赖，确保测试和开发环境正确配置

setlocal EnableDelayedExpansion

REM 启动脚本执行
goto start

REM 获取脚本所在目录的绝对路径
:init
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM 颜色定义 (Windows 10+支持)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 错误计数器
set ERROR_COUNT=0
set WARNING_COUNT=0

goto main

REM 记录函数
:log_success
echo %GREEN%✓ %~1%NC%
exit /b 0

:log_warning
echo %YELLOW%⚠ %~1%NC%
set /a WARNING_COUNT+=1
exit /b 0

:log_error
echo %RED%✗ %~1%NC%
set /a ERROR_COUNT+=1
exit /b 0

:log_info
echo %BLUE%ℹ %~1%NC%
exit /b 0

REM 检查目录存在性
:check_dir_exists
if exist "%~1\" (
    call :log_success "目录存在: %~1"
    exit /b 0
) else (
    call :log_error "目录不存在: %~1"
    exit /b 1
)

REM 检查文件存在性
:check_file_exists
if exist "%~1" (
    call :log_success "文件存在: %~1"
    exit /b 0
) else (
    call :log_error "文件不存在: %~1"
    exit /b 1
)

REM 检查命令是否存在
:check_command
where %~1 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    call :log_success "命令可用: %~1"
    exit /b 0
) else (
    call :log_warning "命令不可用: %~1"
    exit /b 1
)

REM 检查Python模块是否已安装
:check_python_module
python -c "import %~1" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    call :log_success "Python模块已安装: %~1"
    exit /b 0
) else (
    call :log_warning "Python模块未安装: %~1"
    exit /b 1
)

REM 检查目录结构
:check_dir_structure
echo.
echo %BLUE%=== 检查目录结构 ===%NC%

REM 检查核心目录
call :check_dir_exists "%PROJECT_ROOT%\src"
call :check_dir_exists "%PROJECT_ROOT%\tests"
call :check_dir_exists "%PROJECT_ROOT%\docs"
call :check_dir_exists "%PROJECT_ROOT%\scripts"

REM 检查测试相关目录
call :check_dir_exists "%PROJECT_ROOT%\tests\unit"
call :check_dir_exists "%PROJECT_ROOT%\tests\functional"
call :check_dir_exists "%PROJECT_ROOT%\tests\integration"
call :check_dir_exists "%PROJECT_ROOT%\tests\golden_samples"
call :check_dir_exists "%PROJECT_ROOT%\tests\data"
call :check_dir_exists "%PROJECT_ROOT%\tests\tmp_output"
call :check_dir_exists "%PROJECT_ROOT%\tests\configs"

REM 检查模型目录
call :check_dir_exists "%PROJECT_ROOT%\models"
call :check_dir_exists "%PROJECT_ROOT%\models\chinese"
call :check_dir_exists "%PROJECT_ROOT%\models\english"

exit /b 0

REM 检查pytest安装和版本
:check_pytest
echo.
echo %BLUE%=== 检查Pytest安装 ===%NC%

call :check_command "pytest"
if %ERRORLEVEL% equ 0 (
    REM 检查版本
    for /f "tokens=*" %%i in ('pytest --version ^| findstr /r "[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"') do (
        set PYTEST_OUT=%%i
    )
    
    for /f "tokens=2 delims= " %%a in ("!PYTEST_OUT!") do (
        set PYTEST_VERSION=%%a
    )
    
    if defined PYTEST_VERSION (
        call :log_success "Pytest版本: !PYTEST_VERSION!"
    ) else (
        call :log_warning "无法确定Pytest版本"
    )
    
    REM 测试pytest是否可以正常运行
    pytest --version >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        call :log_success "Pytest可以正常运行"
    ) else (
        call :log_error "Pytest无法正常运行"
    )
)

exit /b 0

REM 检查配置文件
:check_config
echo.
echo %BLUE%=== 检查配置文件 ===%NC%

REM 检查测试配置文件
call :check_file_exists "%PROJECT_ROOT%\tests\configs\test_config.yaml"

REM 检查配置文件格式是否正确
if exist "%PROJECT_ROOT%\tests\configs\test_config.yaml" (
    where python >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        python -c "import yaml; yaml.safe_load(open('%PROJECT_ROOT%\tests\configs\test_config.yaml'))" >nul 2>nul
        if %ERRORLEVEL% equ 0 (
            call :log_success "测试配置文件格式正确"
        ) else (
            call :log_error "测试配置文件格式不正确"
        )
    ) else (
        call :log_warning "Python不可用，无法验证YAML格式"
    )
)

REM 检查模型配置文件
call :check_file_exists "%PROJECT_ROOT%\models\chinese\config.json"
call :check_file_exists "%PROJECT_ROOT%\models\english\config.json"

exit /b 0

REM 检查Python环境
:check_python_env
echo.
echo %BLUE%=== 检查Python环境 ===%NC%

REM 检查Python版本
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do (
        set PYTHON_VERSION=%%i
    )
    call :log_success "Python版本: !PYTHON_VERSION!"
    
    REM 检查核心依赖
    call :check_python_module "numpy"
    call :check_python_module "torch"
    call :check_python_module "transformers"
    call :check_python_module "yaml"
    call :check_python_module "pytest"
    call :check_python_module "cv2"
) else (
    call :log_error "Python未安装或不在PATH中"
)

exit /b 0

REM 检查系统依赖
:check_system_deps
echo.
echo %BLUE%=== 检查系统依赖 ===%NC%

REM 检查FFmpeg（视频处理必需）
where ffmpeg >nul 2>nul
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%i in ('ffmpeg -version ^| findstr "version"') do (
        set FFMPEG_VERSION=%%i
    )
    call :log_success "FFmpeg已安装: !FFMPEG_VERSION:~0,30!"
) else (
    call :log_warning "FFmpeg未安装，视频处理功能可能受限"
)

REM 检查Git
where git >nul 2>nul
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%i in ('git --version') do (
        set GIT_VERSION=%%i
    )
    call :log_success "Git已安装: !GIT_VERSION!"
) else (
    call :log_warning "Git未安装，版本控制功能可能受限"
)

exit /b 0

REM 检查测试数据
:check_test_data
echo.
echo %BLUE%=== 检查测试数据 ===%NC%

REM 检查测试数据目录是否为空
if exist "%PROJECT_ROOT%\tests\data\*" (
    call :log_success "测试数据目录非空"
) else (
    call :log_warning "测试数据目录为空，运行部分测试可能会失败"
    call :log_info "可以运行 python scripts/init_test_data.py 初始化测试数据"
)

REM 检查黄金样本目录是否为空
if exist "%PROJECT_ROOT%\tests\golden_samples\*" (
    call :log_success "黄金样本目录非空"
) else (
    call :log_warning "黄金样本目录为空，对比测试可能会失败"
)

exit /b 0

REM 主函数
:main
echo %BLUE%===============================================%NC%
echo %BLUE%   VisionAI-ClipsMaster 框架验证            %NC%
echo %BLUE%===============================================%NC%

REM 检查当前工作目录
call :log_info "当前目录: %CD%"
call :log_info "项目根目录: %PROJECT_ROOT%"

REM 检查环境
call :check_dir_structure
call :check_pytest
call :check_config
call :check_python_env
call :check_system_deps
call :check_test_data

REM 总结
echo.
echo %BLUE%=== 验证结果 ===%NC%
if %ERROR_COUNT% equ 0 (
    if %WARNING_COUNT% equ 0 (
        echo %GREEN%✓ 框架验证通过，没有发现错误或警告%NC%
    ) else (
        echo %YELLOW%⚠ 框架验证通过，但有 %WARNING_COUNT% 个警告%NC%
    )
    exit /b 0
) else (
    echo %RED%✗ 框架验证失败，发现 %ERROR_COUNT% 个错误, %WARNING_COUNT% 个警告%NC%
    exit /b 1
)

REM 启动脚本执行
:start
call :init
call :main
exit /b %ERRORLEVEL% 