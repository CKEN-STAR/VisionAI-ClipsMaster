#!/bin/bash
# 边界条件测试运行脚本 - Linux/macOS版本

# 确保在项目根目录运行
cd "$(dirname "$0")/.."

# 设置Python路径
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 帮助信息
function show_help {
    echo "边界条件测试运行脚本"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help            显示帮助信息"
    echo "  --all             运行所有标准测试"
    echo "  --extended        运行所有测试(标准+扩展)"
    echo "  --scenario NAME   指定测试场景名称"
    echo "  --model ID        指定模型ID"
    echo "  --output-dir DIR  指定输出目录"
    echo ""
    echo "示例:"
    echo "  $0 --all"
    echo "  $0 --scenario \"常规4GB设备\" --model \"qwen2.5-7b-chat\""
    echo "  $0 --interactive"
    exit 1
}

# 默认参数
SCENARIO=""
MODEL=""
OUTPUT_DIR=""
RUN_ALL=false
RUN_EXTENDED=false
INTERACTIVE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --help)
            show_help
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --extended)
            RUN_EXTENDED=true
            shift
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        --scenario)
            SCENARIO="$2"
            shift
            shift
            ;;
        --model)
            MODEL="$2"
            shift
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift
            shift
            ;;
        *)
            echo "未知选项: $1"
            show_help
            ;;
    esac
done

# 构建输出目录参数
OUTPUT_DIR_PARAM=""
if [ -n "$OUTPUT_DIR" ]; then
    OUTPUT_DIR_PARAM="--output-dir $OUTPUT_DIR"
fi

# 执行相应命令
if [ "$INTERACTIVE" = true ]; then
    python scripts/run_boundary_tests.py --interactive $OUTPUT_DIR_PARAM
elif [ "$RUN_ALL" = true ]; then
    python scripts/run_boundary_tests.py --all $OUTPUT_DIR_PARAM
elif [ "$RUN_EXTENDED" = true ]; then
    python scripts/run_boundary_tests.py --extended $OUTPUT_DIR_PARAM
elif [ -n "$SCENARIO" ]; then
    # 运行特定场景
    if [ -n "$MODEL" ]; then
        python scripts/run_boundary_tests.py --scenario "$SCENARIO" --model "$MODEL" $OUTPUT_DIR_PARAM
    else
        python scripts/run_boundary_tests.py --scenario "$SCENARIO" $OUTPUT_DIR_PARAM
    fi
else
    # 默认使用交互模式
    python scripts/run_boundary_tests.py --interactive $OUTPUT_DIR_PARAM
fi 