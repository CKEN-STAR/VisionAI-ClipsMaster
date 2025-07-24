@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo VisionAI-ClipsMaster 视频工作流验证系统
echo ========================================
echo.

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请确保Python已安装并添加到PATH环境变量
    pause
    exit /b 1
)

:: 显示菜单
:menu
echo 请选择要执行的测试:
echo.
echo 1. 快速工作流测试 (推荐新用户)
echo 2. 端到端工作流测试
echo 3. 视频格式兼容性测试
echo 4. 质量验证测试
echo 5. UI界面集成测试
echo 6. 异常处理测试
echo 7. 完整验证套件
echo 8. 查看测试报告
echo 9. 清理测试输出
echo 0. 退出
echo.
set /p choice="请输入选项 (0-9): "

if "%choice%"=="1" goto quick_test
if "%choice%"=="2" goto end_to_end_test
if "%choice%"=="3" goto format_test
if "%choice%"=="4" goto quality_test
if "%choice%"=="5" goto ui_test
if "%choice%"=="6" goto exception_test
if "%choice%"=="7" goto full_suite
if "%choice%"=="8" goto view_reports
if "%choice%"=="9" goto cleanup
if "%choice%"=="0" goto exit
echo 无效选项，请重新选择
goto menu

:quick_test
echo.
echo 🎬 执行快速工作流测试...
echo ========================================
python quick_workflow_test.py
if errorlevel 1 (
    echo.
    echo ❌ 快速工作流测试失败
) else (
    echo.
    echo ✅ 快速工作流测试完成
)
pause
goto menu

:end_to_end_test
echo.
echo 🔄 执行端到端工作流测试...
echo ========================================
python test_end_to_end_workflow.py
if errorlevel 1 (
    echo.
    echo ❌ 端到端工作流测试失败
) else (
    echo.
    echo ✅ 端到端工作流测试完成
)
pause
goto menu

:format_test
echo.
echo 📹 执行视频格式兼容性测试...
echo ========================================
python test_video_format_compatibility.py
if errorlevel 1 (
    echo.
    echo ❌ 视频格式兼容性测试失败
) else (
    echo.
    echo ✅ 视频格式兼容性测试完成
)
pause
goto menu

:quality_test
echo.
echo 🎯 执行质量验证测试...
echo ========================================
python test_quality_validation.py
if errorlevel 1 (
    echo.
    echo ❌ 质量验证测试失败
) else (
    echo.
    echo ✅ 质量验证测试完成
)
pause
goto menu

:ui_test
echo.
echo 🖥️ 执行UI界面集成测试...
echo ========================================
echo 注意: UI测试需要PyQt6环境
python test_ui_integration.py
if errorlevel 1 (
    echo.
    echo ❌ UI界面集成测试失败
) else (
    echo.
    echo ✅ UI界面集成测试完成
)
pause
goto menu

:exception_test
echo.
echo 🚨 执行异常处理测试...
echo ========================================
python test_exception_handling.py
if errorlevel 1 (
    echo.
    echo ❌ 异常处理测试失败
) else (
    echo.
    echo ✅ 异常处理测试完成
)
pause
goto menu

:full_suite
echo.
echo 🎯 执行完整验证套件...
echo ========================================
echo 警告: 完整测试可能需要较长时间 (10-20分钟)
set /p confirm="确认执行? (y/N): "
if /i not "%confirm%"=="y" goto menu

python run_video_workflow_validation_suite.py
if errorlevel 1 (
    echo.
    echo ❌ 完整验证套件执行失败
) else (
    echo.
    echo ✅ 完整验证套件执行完成
)
pause
goto menu

:view_reports
echo.
echo 📄 查看测试报告...
echo ========================================

:: 检查测试输出目录
if not exist "..\..\test_output" (
    echo 未找到测试输出目录
    echo 请先运行测试生成报告
    pause
    goto menu
)

:: 列出最近的报告文件
echo 最近的测试报告:
echo.

:: 查找HTML报告
dir /b /o-d "..\..\test_output\*workflow*.html" 2>nul | findstr /r ".*" >nul
if errorlevel 1 (
    echo 未找到工作流HTML报告文件
) else (
    echo HTML报告:
    for /f %%f in ('dir /b /o-d "..\..\test_output\*workflow*.html" 2^>nul') do (
        echo   %%f
        set latest_html=%%f
        goto found_html
    )
)

:found_html
:: 查找JSON报告
dir /b /o-d "..\..\test_output\*workflow*.json" 2>nul | findstr /r ".*" >nul
if errorlevel 1 (
    echo 未找到工作流JSON报告文件
) else (
    echo JSON报告:
    for /f %%f in ('dir /b /o-d "..\..\test_output\*workflow*.json" 2^>nul') do (
        echo   %%f
        set latest_json=%%f
        goto found_json
    )
)

:found_json
:: 查找性能基准报告
dir /b /o-d "..\..\test_output\performance_benchmark*.json" 2>nul | findstr /r ".*" >nul
if not errorlevel 1 (
    echo 性能基准报告:
    for /f %%f in ('dir /b /o-d "..\..\test_output\performance_benchmark*.json" 2^>nul') do (
        echo   %%f
        goto found_benchmark
    )
)

:found_benchmark
echo.
if defined latest_html (
    set /p open_html="打开最新的HTML报告? (y/N): "
    if /i "!open_html!"=="y" (
        start "" "..\..\test_output\!latest_html!"
    )
)

pause
goto menu

:cleanup
echo.
echo 🧹 清理测试输出...
echo ========================================
set /p confirm_cleanup="确认删除所有测试输出文件? (y/N): "
if /i not "%confirm_cleanup%"=="y" goto menu

if exist "..\..\test_output" (
    echo 删除工作流测试输出...
    del /q "..\..\test_output\*workflow*.*" 2>nul
    del /q "..\..\test_output\*benchmark*.*" 2>nul
    echo ✅ 工作流测试输出已清理
) else (
    echo 测试输出目录不存在
)

if exist "..\..\logs" (
    echo 删除工作流日志文件...
    del /q "..\..\logs\video_workflow_validation_*.log" 2>nul
    echo ✅ 工作流验证日志已清理
)

pause
goto menu

:exit
echo.
echo 👋 感谢使用VisionAI-ClipsMaster视频工作流验证系统
echo.
exit /b 0
