#!/bin/bash
# 内存环境测试脚本
# 在Docker容器中模拟不同内存环境

# 确保在项目根目录运行
cd "$(dirname "$0")/.."

# 设置默认参数
ENV_PROFILE="4GB连线"
TEST_MODE="burst"
TEST_DURATION=60
TARGET_PERCENT=70

# 帮助信息
function show_help {
    echo "内存环境测试脚本"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help            显示此帮助信息"
    echo "  -e, --environment     环境配置名称 (默认: 4GB连线)"
    echo "  -m, --mode            测试模式: staircase, burst, sawtooth (默认: burst)"
    echo "  -d, --duration        测试持续时间(秒) (默认: 60)"
    echo "  -t, --target          目标内存占用百分比 (默认: 70)"
    echo "  -l, --list            列出所有可用环境配置"
    echo ""
    echo "示例:"
    echo "  $0 --environment \"极限2GB模式\" --mode staircase --duration 120"
    exit 1
}

# 列出可用的环境配置
function list_environments {
    echo "可用的测试环境配置:"
    python -c "
from src.utils.env_simulator import EnvironmentSimulator
simulator = EnvironmentSimulator()
simulator.print_profiles()
"
    exit 0
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            ;;
        -e|--environment)
            ENV_PROFILE="$2"
            shift
            shift
            ;;
        -m|--mode)
            TEST_MODE="$2"
            shift
            shift
            ;;
        -d|--duration)
            TEST_DURATION="$2"
            shift
            shift
            ;;
        -t|--target)
            TARGET_PERCENT="$2"
            shift
            shift
            ;;
        -l|--list)
            list_environments
            ;;
        *)
            echo "未知选项: $1"
            show_help
            ;;
    esac
done

# 生成Docker命令
DOCKER_CMD=$(python -c "
from src.utils.env_simulator import EnvironmentSimulator
simulator = EnvironmentSimulator()

# 生成测试命令
test_cmd = f'python src/utils/memory_test_cli.py simple --mode={\"$TEST_MODE\"} --target={\"$TARGET_PERCENT\"} --duration={\"$TEST_DURATION\"}'

# 生成Docker命令
cmd = simulator.generate_docker_command(
    profile_name='$ENV_PROFILE',
    command=test_cmd
)
print(cmd)
")

# 检查命令是否成功生成
if [ -z "$DOCKER_CMD" ]; then
    echo "错误: 无法生成Docker命令，请检查环境配置名称是否正确"
    list_environments
    exit 1
fi

# 输出测试信息
echo "=== 内存环境测试 ==="
echo "环境配置: $ENV_PROFILE"
echo "测试模式: $TEST_MODE"
echo "测试时间: $TEST_DURATION 秒"
echo "目标占用: $TARGET_PERCENT%"
echo ""
echo "执行命令:"
echo "$DOCKER_CMD"
echo ""
echo "启动测试..."

# 执行Docker命令
eval "$DOCKER_CMD"

echo ""
echo "测试完成" 