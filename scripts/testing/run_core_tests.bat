@echo off
REM VisionAI-ClipsMaster 核心功能测试执行脚本
REM 
REM 用法:
REM   run_core_tests.bat                    - 运行所有核心测试
REM   run_core_tests.bat --alignment        - 只运行对齐测试
REM   run_core_tests.bat --screenplay       - 只运行剧本重构测试
REM   run_core_tests.bat --language         - 只运行语言检测测试
REM   run_core_tests.bat --integration      - 只运行集成测试

echo ========================================
echo VisionAI-ClipsMaster 核心功能测试
echo ========================================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请确保Python已安装并添加到PATH环境变量
    pause
    exit /b 1
)

REM 设置项目路径
set PROJECT_ROOT=%~dp0
set PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\src;%PYTHONPATH%

echo 项目根目录: %PROJECT_ROOT%
echo Python路径: %PYTHONPATH%

REM 检查测试文件是否存在
if not exist "%PROJECT_ROOT%tests\core_functionality_comprehensive_test.py" (
    echo 错误: 核心测试文件不存在
    echo 请确保测试文件位于 tests\ 目录下
    pause
    exit /b 1
)

REM 创建输出目录
if not exist "%PROJECT_ROOT%test_output" (
    mkdir "%PROJECT_ROOT%test_output"
)

echo.
echo 开始执行测试...
echo.

REM 根据参数执行不同的测试
if "%1"=="--alignment" (
    echo 执行视频-字幕对齐精度测试...
    python -m unittest tests.core_functionality_comprehensive_test.VideoSubtitleMappingTest -v
    goto :end
)

if "%1"=="--screenplay" (
    echo 执行剧本重构能力测试...
    python -m unittest tests.core_functionality_comprehensive_test.ScreenplayReconstructionTest -v
    goto :end
)

if "%1"=="--language" (
    echo 执行语言检测和模型切换测试...
    python -m unittest tests.core_functionality_comprehensive_test.LanguageModelSwitchingTest -v
    goto :end
)

if "%1"=="--integration" (
    echo 执行端到端集成测试...
    python tests\end_to_end_integration_test.py
    goto :end
)

if "%1"=="--comprehensive" (
    echo 执行完整验证测试套件...
    python tests\run_comprehensive_validation_tests.py --output-dir test_output
    goto :end
)

REM 默认执行所有核心测试
echo 执行所有核心功能测试...
echo.

echo [1/4] 视频-字幕映射精度测试
echo --------------------------------
python -m unittest tests.core_functionality_comprehensive_test.VideoSubtitleMappingTest -v
if errorlevel 1 (
    echo 视频-字幕映射测试失败
    set TEST_FAILED=1
) else (
    echo 视频-字幕映射测试通过
)

echo.
echo [2/4] 剧本重构能力测试
echo --------------------------------
python -m unittest tests.core_functionality_comprehensive_test.ScreenplayReconstructionTest -v
if errorlevel 1 (
    echo 剧本重构测试失败
    set TEST_FAILED=1
) else (
    echo 剧本重构测试通过
)

echo.
echo [3/4] 语言检测和模型切换测试
echo --------------------------------
python -m unittest tests.core_functionality_comprehensive_test.LanguageModelSwitchingTest -v
if errorlevel 1 (
    echo 语言检测测试失败
    set TEST_FAILED=1
) else (
    echo 语言检测测试通过
)

echo.
echo [4/4] 端到端集成测试
echo --------------------------------
python tests\end_to_end_integration_test.py
if errorlevel 1 (
    echo 集成测试失败
    set TEST_FAILED=1
) else (
    echo 集成测试通过
)

:end
echo.
echo ========================================
if defined TEST_FAILED (
    echo 测试结果: 部分测试失败
    echo 请查看上方输出了解详细信息
    echo ========================================
    pause
    exit /b 1
) else (
    echo 测试结果: 所有测试通过
    echo ========================================
    echo.
    echo 可选操作:
    echo   1. 查看详细报告: test_output\
    echo   2. 运行完整测试: run_core_tests.bat --comprehensive
    echo   3. 生成测试数据: python tests\test_data_preparation.py
    echo.
)

pause
