#!/bin/bash
# 内存探针C扩展构建脚本 - Linux/macOS版本

# 确保在项目根目录运行
cd "$(dirname "$0")/.."

# 设置Python路径
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 帮助信息
function show_help {
    echo "内存探针C扩展构建脚本"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help            显示帮助信息"
    echo "  --clean           在构建前清理目标文件"
    echo "  --debug           使用调试模式构建"
    echo ""
    echo "示例:"
    echo "  $0"
    echo "  $0 --clean"
    echo "  $0 --debug"
    exit 1
}

# 解析命令行参数
if [ "$1" == "--help" ]; then
    show_help
elif [ "$1" == "--clean" ]; then
    python scripts/build_memory_probes.py --clean
elif [ "$1" == "--debug" ]; then
    python scripts/build_memory_probes.py --debug
else
    # 默认构建
    python scripts/build_memory_probes.py
fi 