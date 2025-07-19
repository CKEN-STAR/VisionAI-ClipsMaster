@echo off
REM 混合压缩验证测试批处理脚本

echo 运行混合压缩验证测试...
echo ==================================

REM 设置路径
set PROJECT_ROOT=%~dp0..
set PYTHON_CMD=python

REM 确保测试数据目录存在
if not exist "%PROJECT_ROOT%\data\test_data" (
    mkdir "%PROJECT_ROOT%\data\test_data"
)

REM 确保测试结果目录存在
if not exist "%PROJECT_ROOT%\data\test_data\results" (
    mkdir "%PROJECT_ROOT%\data\test_data\results"
)

REM 进入项目根目录
cd "%PROJECT_ROOT%"

REM 检查命令行参数
if "%1"=="--generate-only" (
    echo 仅生成测试数据...
    %PYTHON_CMD% tests\compression_test\test_data_generator.py
    goto :end
)

if "%1"=="--compare" (
    echo 比较多个压缩算法...
    %PYTHON_CMD% tests\compression_test\single_algo_test.py --compare
    goto :end
)

REM 运行混合压缩验证测试
echo 运行混合压缩验证测试...
%PYTHON_CMD% tests\run_hybrid_compression_tests.py %*

:end
echo ==================================
echo 测试完成! 