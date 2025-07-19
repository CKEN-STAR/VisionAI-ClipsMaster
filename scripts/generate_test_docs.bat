@echo off
REM VisionAI-ClipsMaster 测试文档生成工具
REM 该脚本用于生成详细的测试文档

setlocal

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM 颜色定义
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RED=[91m"
set "NC=[0m"

REM 标题
echo %BLUE%=================================================%NC%
echo %BLUE%   VisionAI-ClipsMaster 测试文档生成工具   %NC%
echo %BLUE%=================================================%NC%
echo.

REM 运行文档生成脚本
echo %YELLOW%开始生成测试文档...%NC%
python "%SCRIPT_DIR%generate_test_docs.py" %*
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo %GREEN%✓ 测试文档生成成功%NC%
    echo %GREEN%文档已保存到: %PROJECT_ROOT%\docs\tests\%NC%
    
    REM 显示生成的文档列表
    echo.
    echo %YELLOW%生成的文档:%NC%
    echo - %PROJECT_ROOT%\docs\tests\README.md
    echo - %PROJECT_ROOT%\docs\tests\TEST_STRUCTURE.md
    echo - %PROJECT_ROOT%\docs\tests\TEST_CASES.md
    echo - %PROJECT_ROOT%\docs\tests\TEST_COVERAGE.md
) else (
    echo.
    echo %RED%✗ 测试文档生成失败，退出代码: %EXIT_CODE%%NC%
)

exit /b %EXIT_CODE% 