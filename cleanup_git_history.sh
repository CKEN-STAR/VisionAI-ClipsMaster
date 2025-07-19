#!/bin/bash
# VisionAI-ClipsMaster Git历史清理脚本

set -e

echo "🧹 开始清理Git历史..."

# 1. 备份当前分支
echo "📦 创建备份分支..."
git checkout -b backup-before-cleanup

# 2. 回到主分支
git checkout main

# 3. 清理大文件历史
echo "🗑️ 清理大文件历史..."

# 清理模型文件历史
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch models/models/qwen/base/*.safetensors' \
  --prune-empty --tag-name-filter cat -- --all

# 清理其他大文件
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch *.zip *.exe *.dll *.bin' \
  --prune-empty --tag-name-filter cat -- --all

# 4. 清理引用
echo "🔗 清理引用..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 5. 强制推送 (谨慎操作)
echo "⚠️ 准备强制推送，这将重写远程历史"
read -p "确认继续? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push --force-with-lease origin main
    echo "✅ Git历史清理完成"
else
    echo "❌ 取消推送，本地清理已完成"
fi

# 6. 显示清理结果
echo "📊 清理结果:"
echo "当前仓库大小: $(du -sh .git | cut -f1)"
echo "文件数量: $(find . -type f | wc -l)"
