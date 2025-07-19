#!/bin/bash
# VisionAI-ClipsMaster测试环境停用脚本
echo "======================================="
echo " VisionAI-ClipsMaster 测试环境停用工具"
echo "======================================="
echo

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "[警告] 当前未激活虚拟环境，无需停用"
    exit 0
fi

# 检查是否是测试环境
if [[ "$VIRTUAL_ENV" != *".test_venv"* ]]; then
    echo "[警告] 当前激活的不是测试环境，而是:"
    echo "$VIRTUAL_ENV"
    echo "如需停用，请直接使用 'deactivate' 命令"
    exit 1
fi

# 停用虚拟环境
deactivate

echo "[成功] 测试环境已停用!"
echo "=======================================" 