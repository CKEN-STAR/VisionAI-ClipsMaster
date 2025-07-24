@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo VisionAI-ClipsMaster 训练验证系统
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
echo 1. 快速测试 (推荐新用户)
echo 2. 训练效果验证
echo 3. GPU加速测试
echo 4. 质量指标测试
echo 5. 内存性能测试
echo 6. 完整验证套件
echo 7. 查看测试报告
echo 8. 清理测试输出
echo 0. 退出
echo.
set /p choice="请输入选项 (0-8): "

if "%choice%"=="1" goto quick_test
if "%choice%"=="2" goto effectiveness_test
if "%choice%"=="3" goto gpu_test
if "%choice%"=="4" goto quality_test
if "%choice%"=="5" goto memory_test
if "%choice%"=="6" goto full_suite
if "%choice%"=="7" goto view_reports
if "%choice%"=="8" goto cleanup
if "%choice%"=="0" goto exit
echo 无效选项，请重新选择
goto menu

:quick_test
echo.
echo 🚀 执行快速测试...
echo ========================================
python quick_test.py
if errorlevel 1 (
    echo.
    echo ❌ 快速测试失败
) else (
    echo.
    echo ✅ 快速测试完成
)
pause
goto menu

:effectiveness_test
echo.
echo 📊 执行训练效果验证测试...
echo ========================================
python test_training_effectiveness.py
if errorlevel 1 (
    echo.
    echo ❌ 训练效果验证测试失败
) else (
    echo.
    echo ✅ 训练效果验证测试完成
)
pause
goto menu

:gpu_test
echo.
echo 🖥️ 执行GPU加速测试...
echo ========================================
python test_gpu_acceleration.py
if errorlevel 1 (
    echo.
    echo ❌ GPU加速测试失败
) else (
    echo.
    echo ✅ GPU加速测试完成
)
pause
goto menu

:quality_test
echo.
echo 📈 执行质量指标测试...
echo ========================================
python test_quality_metrics.py
if errorlevel 1 (
    echo.
    echo ❌ 质量指标测试失败
) else (
    echo.
    echo ✅ 质量指标测试完成
)
pause
goto menu

:memory_test
echo.
echo 💾 执行内存性能测试...
echo ========================================
python test_memory_performance.py
if errorlevel 1 (
    echo.
    echo ❌ 内存性能测试失败
) else (
    echo.
    echo ✅ 内存性能测试完成
)
pause
goto menu

:full_suite
echo.
echo 🎯 执行完整验证套件...
echo ========================================
echo 警告: 完整测试可能需要较长时间 (5-15分钟)
set /p confirm="确认执行? (y/N): "
if /i not "%confirm%"=="y" goto menu

python run_training_validation_suite.py
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
dir /b /o-d "..\..\test_output\*.html" 2>nul | findstr /r ".*" >nul
if errorlevel 1 (
    echo 未找到HTML报告文件
) else (
    for /f %%f in ('dir /b /o-d "..\..\test_output\*.html" 2^>nul') do (
        echo HTML报告: %%f
        set latest_html=%%f
        goto found_html
    )
)

:found_html
dir /b /o-d "..\..\test_output\*.json" 2>nul | findstr /r ".*" >nul
if errorlevel 1 (
    echo 未找到JSON报告文件
) else (
    for /f %%f in ('dir /b /o-d "..\..\test_output\*.json" 2^>nul') do (
        echo JSON报告: %%f
        set latest_json=%%f
        goto found_json
    )
)

:found_json
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
    echo 删除测试输出目录...
    rmdir /s /q "..\..\test_output"
    echo ✅ 测试输出已清理
) else (
    echo 测试输出目录不存在
)

if exist "..\..\logs" (
    echo 删除日志文件...
    del /q "..\..\logs\training_validation_*.log" 2>nul
    echo ✅ 训练验证日志已清理
)

pause
goto menu

:exit
echo.
echo 👋 感谢使用VisionAI-ClipsMaster训练验证系统
echo.
exit /b 0
