@echo off
REM 直接运行版本测试脚本，避免IDE的CMake配置问题

echo 正在运行版本测试...
python run_version_test.py

echo.
echo 如果测试正常完成，则说明不需要CMake配置
echo 这个错误是IDE的误报，可以忽略
echo.
pause 