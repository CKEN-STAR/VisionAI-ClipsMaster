#!/bin/bash
# 量化策略验证测试运行脚本

# 切换到项目根目录
cd "$(dirname "$0")/.." || exit 1

echo "运行量化策略验证测试..."

# 检查Python可用性
if ! command -v python3 &> /dev/null; then
    echo "Python 3未安装或不在系统路径中，请安装Python 3并确保其在PATH中。"
    exit 1
fi

# 处理命令行参数
ARGS=""
for arg in "$@"; do
    if [ "$arg" == "--verbose" ] || [ "$arg" == "-v" ]; then
        ARGS="$ARGS -v"
    elif [ "$arg" == "--report" ] || [ "$arg" == "-r" ]; then
        ARGS="$ARGS -r"
    fi
done

# 运行测试
python3 tests/run_quant_strategy_tests.py $ARGS

if [ $? -ne 0 ]; then
    echo "测试失败，请查看日志获取详细信息。"
    exit 1
else
    echo "所有测试通过！"
    exit 0
fi 