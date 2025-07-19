@echo off
REM 黄金样本安全设置脚本
REM 该脚本设置黄金样本目录的安全权限和Git属性

setlocal

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

echo 设置黄金样本目录安全权限...

REM 设置黄金样本目录为只读
attrib +R "%PROJECT_ROOT%\tests\golden_samples\*" /S

REM 添加防篡改设置到.gitattributes
echo 添加防篡改设置到Git属性...
echo golden_samples/* -diff -merge -text >> "%PROJECT_ROOT%\.gitattributes"

REM 设置过滤器
echo filter=hash >> "%PROJECT_ROOT%\.git\config"

echo ✓ 黄金样本安全设置完成！

REM 提示用户运行验证
echo.
echo 建议现在运行完整性验证:
echo python -m src.cli.secure_samples verify

pause 