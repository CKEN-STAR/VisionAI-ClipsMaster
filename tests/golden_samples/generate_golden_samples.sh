#!/bin/bash
# 黄金样本生成脚本 (Linux/macOS版)

echo "正在运行VisionAI-ClipsMaster黄金样本生成..."
echo

# 设置Python路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR/../.."

# 处理帮助选项
if [ "$1" == "--help" ]; then
    echo "使用方法: ./generate_golden_samples.sh [选项]"
    echo
    echo "选项:"
    echo "  --version [版本号]  指定版本号(默认: 1.0.0)"
    echo "  --list             列出所有已生成的样本"
    echo "  --update-index     仅更新样本索引"
    echo "  --log-level [级别] 设置日志级别(DEBUG/INFO/WARNING/ERROR)"
    echo "  --help             显示此帮助信息"
    exit 0
fi

# 设置默认参数
VERSION="1.0.0"
ACTION="--generate"
LOG_LEVEL="INFO"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift
            ;;
        --list)
            ACTION="--list"
            ;;
        --update-index)
            ACTION="--update-index"
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 ./generate_golden_samples.sh --help 查看帮助"
            exit 1
            ;;
    esac
    shift
done

# 确保脚本可执行
if [ ! -x "$SCRIPT_DIR/run_golden_sample_generation.py" ]; then
    chmod +x "$SCRIPT_DIR/run_golden_sample_generation.py"
fi

# 运行样本生成脚本
python "$SCRIPT_DIR/run_golden_sample_generation.py" $ACTION --version $VERSION --log-level $LOG_LEVEL

# 检查结果
if [ $? -ne 0 ]; then
    echo
    echo "样本生成失败! 详见上方输出。"
    exit 1
else
    echo
    echo "操作成功完成!"
    exit 0
fi 