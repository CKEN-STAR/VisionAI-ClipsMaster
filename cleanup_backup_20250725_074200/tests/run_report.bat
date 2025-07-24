@echo off
echo 正在生成VisionAI-ClipsMaster测试报告...

:: 创建报告目录
if not exist reports mkdir reports
if not exist reports\static mkdir reports\static

:: 生成测试报告
python tests/generate_report.py -o reports/test_report.html

:: 如果成功生成，尝试打开报告
if %ERRORLEVEL% EQU 0 (
    echo 报告生成成功!
    start reports/test_report.html
) else (
    echo 报告生成失败，请检查错误信息。
)

echo 操作完成。
pause 