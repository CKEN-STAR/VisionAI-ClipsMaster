@echo off
echo 终极Git修复方案...

echo 第1步：备份重要文件
if not exist "backup" mkdir backup
copy "*.py" backup\ 2>nul
copy "*.md" backup\ 2>nul
copy "requirements.txt" backup\ 2>nul

echo 第2步：完全清理子模块
rmdir /s /q llama.cpp 2>nul
rmdir /s /q .git\modules 2>nul
del .gitmodules 2>nul

echo 第3步：重置Git仓库
git reset --hard HEAD
git clean -fdx
git gc --aggressive --prune=now

echo 第4步：测试结果
git status

echo 修复完成！
pause