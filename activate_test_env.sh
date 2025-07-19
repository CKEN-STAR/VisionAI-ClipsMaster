#!/bin/bash
# VisionAI-ClipsMaster测试环境激活脚本
echo "======================================="
echo " VisionAI-ClipsMaster 测试环境激活工具"
echo "======================================="
echo

# 检查虚拟环境是否存在
if [ ! -d ".test_venv" ]; then
    echo "[错误] 测试虚拟环境不存在，请先运行创建环境的命令"
    echo "python -m venv .test_venv"
    exit 1
fi

# 激活虚拟环境
source .test_venv/bin/activate

# 检查激活是否成功
which python
echo
echo "当前Python解释器: $VIRTUAL_ENV"
echo
echo "[成功] 测试环境已激活!"
echo
echo "提示: 使用 'deactivate' 命令退出测试环境"
echo "      或运行 'source deactivate_test_env.sh' 脚本"
echo "=======================================" 