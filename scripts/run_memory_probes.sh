#!/bin/bash
# 内存探针测试脚本 - Linux/macOS版本

# 确保在项目根目录运行
cd "$(dirname "$0")/.."

# 设置Python路径
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 帮助信息
function show_help {
    echo "内存探针测试脚本"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help            显示帮助信息"
    echo "  --python-only     仅运行Python探针测试"
    echo "  --c-only          仅运行C探针测试（如果可用）"
    echo "  --pressure        包括内存压力测试"
    echo ""
    echo "示例:"
    echo "  $0"
    echo "  $0 --python-only"
    echo "  $0 --pressure"
    exit 1
}

# 解析命令行参数
if [ "$1" == "--help" ]; then
    show_help
elif [ "$1" == "--python-only" ]; then
    python scripts/test_memory_probes.py --python-only
elif [ "$1" == "--c-only" ]; then
    python scripts/test_memory_probes.py --c-only
elif [ "$1" == "--pressure" ]; then
    python scripts/test_memory_probes.py --pressure
else
    # 默认运行所有测试
    python scripts/test_memory_probes.py 