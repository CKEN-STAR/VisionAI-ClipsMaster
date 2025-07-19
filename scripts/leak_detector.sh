#!/bin/bash
# 内存泄漏检测器 - Linux/macOS运行脚本

# 确保在项目根目录下运行
cd "$(dirname "$0")/.."

# 设置Python路径
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 帮助信息
function show_help {
    python scripts/run_leak_detector.py --help
    exit 0
}

# 解析命令
if [ "$1" == "--help" ]; then
    show_help
fi

if [ -z "$1" ]; then
    # 如果没有提供命令，显示帮助
    show_help
fi

# 执行命令
python scripts/run_leak_detector.py "$@" 