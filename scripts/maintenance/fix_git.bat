@echo off
echo 开始修复Git仓库...
echo.

echo 第1步: 备份当前工作
git stash push -m "修复前备份"
echo 备份完成
echo.

echo 第2步: 清理损坏的子模块
git submodule deinit -f llama.cpp
echo 子模块已停用
echo.

echo 第3步: 删除损坏的配置
if exist ".git\modules\llama.cpp" rmdir /s /q ".git\modules\llama.cpp"
if exist "llama.cpp" rmdir /s /q "llama.cpp"
echo 配置已清理
echo.

echo 第4步: 重新初始化子模块
git submodule update --init --recursive
echo 子模块已重新初始化
echo.

echo 第5步: 测试修复结果
git status
echo.
echo 修复完成！
pause