@echo off
echo 清理构建目录...
rmdir /S /Q build
mkdir build
cd build

echo 运行CMake配置...
set CMAKE_PATH=D:\zancun\VisionAI-ClipsMaster\.test_venv\Lib\site-packages\cmake\data\bin\cmake.exe
"%CMAKE_PATH%" .. -G "Visual Studio 17 2022" -A x64

echo 构建项目...
"%CMAKE_PATH%" --build . --config Release

echo 完成！
pause 