@echo off
echo 正在修复Git仓库问题...

git submodule deinit -f llama.cpp
rmdir /s /q .git\modules\llama.cpp 2>nul
rmdir /s /q llama.cpp 2>nul
git config --file .gitmodules --remove-section submodule.llama.cpp 2>nul
git rm --cached llama.cpp 2>nul
git gc --prune=now

echo 修复完成，测试状态：
git status

echo.
echo 如果需要重新添加llama.cpp子模块，请运行：
echo git submodule add https://github.com/ggerganov/llama.cpp.git llama.cpp
pause