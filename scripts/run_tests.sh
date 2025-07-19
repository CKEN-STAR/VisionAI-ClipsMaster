#!/bin/bash
# VisionAI-ClipsMaster 测试运行脚本
# 提供多种测试运行方式，支持覆盖率报告生成

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 默认参数
TEST_DIR="$PROJECT_ROOT/tests"
REPORT_DIR="$TEST_DIR/reports"
COVERAGE_DIR="$REPORT_DIR/coverage"
MODE="all"
CATEGORY=""
VERBOSE=0
COVERAGE=0
MEMORY_CHECK=0
PARALLEL=0

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 帮助信息
function show_help {
    echo "VisionAI-ClipsMaster 测试运行工具"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -m, --mode MODE       测试模式 (all, unit, functional, integration, memory)"
    echo "  -c, --category CAT    指定测试类别"
    echo "  -v, --verbose         详细输出"
    echo "  --cov                 生成覆盖率报告"
    echo "  --memory-check        内存使用监控"
    echo "  -j, --parallel        并行运行测试"
    echo "  -h, --help            显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 --mode unit --cov  运行单元测试并生成覆盖率报告"
    echo "  $0 --category model   运行模型相关测试"
    echo
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -c|--category)
            CATEGORY="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        --cov)
            COVERAGE=1
            shift
            ;;
        --memory-check)
            MEMORY_CHECK=1
            shift
            ;;
        -j|--parallel)
            PARALLEL=1
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}错误：未知选项 $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 确保报告目录存在
mkdir -p "$REPORT_DIR"
mkdir -p "$COVERAGE_DIR"

# 构建 pytest 命令
PYTEST_CMD="python -m pytest"

# 添加测试路径
case $MODE in
    all)
        PYTEST_CMD="$PYTEST_CMD $TEST_DIR"
        ;;
    unit)
        PYTEST_CMD="$PYTEST_CMD $TEST_DIR/unit"
        ;;
    functional)
        PYTEST_CMD="$PYTEST_CMD $TEST_DIR/functional"
        ;;
    integration)
        PYTEST_CMD="$PYTEST_CMD $TEST_DIR/integration"
        ;;
    memory)
        PYTEST_CMD="$PYTEST_CMD $TEST_DIR/memory"
        ;;
    performance)
        PYTEST_CMD="$PYTEST_CMD $TEST_DIR/performance"
        ;;
    *)
        echo -e "${RED}错误：未知测试模式 $MODE${NC}"
        show_help
        exit 1
        ;;
esac

# 添加类别过滤
if [ ! -z "$CATEGORY" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $CATEGORY"
fi

# 添加详细输出
if [ $VERBOSE -eq 1 ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# 添加覆盖率报告
if [ $COVERAGE -eq 1 ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=html:$COVERAGE_DIR --cov-report=term"
fi

# 添加内存监控
if [ $MEMORY_CHECK -eq 1 ]; then
    PYTEST_CMD="$PYTEST_CMD --memory-check"
fi

# 添加并行运行
if [ $PARALLEL -eq 1 ]; then
    PYTEST_CMD="$PYTEST_CMD -xvs -n auto"
fi

# 显示即将执行的命令
echo -e "${YELLOW}执行: $PYTEST_CMD${NC}"
echo

# 执行测试命令
$PYTEST_CMD
RESULT=$?

# 显示测试结果
echo
if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ 测试通过${NC}"
    
    # 如果生成了覆盖率报告，显示报告路径
    if [ $COVERAGE -eq 1 ]; then
        echo -e "${GREEN}覆盖率报告已生成: $COVERAGE_DIR/index.html${NC}"
    fi
else
    echo -e "${RED}✗ 测试失败${NC}"
fi

echo
echo "日志文件: $REPORT_DIR/pytest.log"
echo

exit $RESULT 