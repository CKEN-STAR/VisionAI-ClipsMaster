#!/bin/bash
# VisionAI-ClipsMaster 黄金指标验证脚本
# 此脚本提供了在Linux/macOS下运行黄金指标验证的便捷方式

echo "VisionAI-ClipsMaster 黄金指标验证工具"
echo "======================================="

# 确保脚本可以从任何位置运行
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function show_help {
    echo
    echo "使用方法:"
    echo "  ./run_golden_metrics.sh [选项]"
    echo
    echo "可用选项:"
    echo "  --help, -h         显示此帮助信息"
    echo "  --show-standards   显示所有的黄金标准值"
    echo "  --verify           执行验证并生成HTML报告"
    echo "  --continuous [分钟] 持续运行验证，可指定间隔时间（默认15分钟）"
    echo "  --system           只验证系统级指标"
    echo "  --app              只验证应用级指标"
    echo "  --model            只验证模型推理指标"
    echo "  --ux               只验证用户体验指标"
    echo "  --io               只验证缓存和IO指标"
    echo
    echo "示例:"
    echo "  ./run_golden_metrics.sh --verify"
    echo "  ./run_golden_metrics.sh --continuous 30"
    echo
}

# 如果没有参数，显示帮助
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# 解析命令行参数
case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    --show-standards)
        python $SCRIPT_DIR/run_golden_metrics_validation.py --show-standards
        ;;
    --verify)
        echo "正在执行基本验证..."
        python $SCRIPT_DIR/run_golden_metrics_validation.py --html
        ;;
    --continuous)
        interval=15
        if [ ! -z "$2" ]; then
            interval=$2
        fi
        echo "启动持续验证模式（间隔 $interval 分钟）..."
        python $SCRIPT_DIR/run_golden_metrics_validation.py --continuous --interval $interval --html
        ;;
    --system)
        echo "只验证系统级指标..."
        python $SCRIPT_DIR/run_golden_metrics_validation.py --categories system --html
        ;;
    --app)
        echo "只验证应用级指标..."
        python $SCRIPT_DIR/run_golden_metrics_validation.py --categories application --html
        ;;
    --model)
        echo "只验证模型推理指标..."
        python $SCRIPT_DIR/run_golden_metrics_validation.py --categories inference --html
        ;;
    --ux)
        echo "只验证用户体验指标..."
        python $SCRIPT_DIR/run_golden_metrics_validation.py --categories user_experience --html
        ;;
    --io)
        echo "只验证缓存和IO指标..."
        python $SCRIPT_DIR/run_golden_metrics_validation.py --categories cache_io --html
        ;;
    *)
        echo "未知的命令: $1"
        show_help
        exit 1
        ;;
esac

exit 0 