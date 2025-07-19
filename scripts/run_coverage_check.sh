#!/bin/bash

# 覆盖率强制检查运行脚本
# 用法: ./run_coverage_check.sh [--strict]

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_ROOT" || exit 1

# 检查Python环境
if [ -d ".test_venv" ] && [ -f ".test_venv/bin/activate" ]; then
    echo "使用测试虚拟环境..."
    source .test_venv/bin/activate
fi

# 检查必要的依赖
python -m pip install pytest pytest-cov coverage --quiet

# 默认参数
STRICT_MODE=""
TEST_DIRS="tests/unit_test"
OUTPUT_DIR="coverage_reports"

# 处理命令行参数
for arg in "$@"; do
    case $arg in
        --strict)
            STRICT_MODE="--strict"
            shift
            ;;
        --test-dirs=*)
            TEST_DIRS="${arg#*=}"
            shift
            ;;
        --output-dir=*)
            OUTPUT_DIR="${arg#*=}"
            shift
            ;;
    esac
done

# 执行覆盖率检查脚本
echo "运行覆盖率强制检查..."
python scripts/enforce_coverage.py --test-dirs "$TEST_DIRS" --output-dir "$OUTPUT_DIR" $STRICT_MODE

# 保存退出状态
EXIT_CODE=$?

# 如果生成了HTML报告，显示报告路径
if [ -d "$OUTPUT_DIR/html" ]; then
    HTML_PATH="$PROJECT_ROOT/$OUTPUT_DIR/html/index.html"
    echo -e "\n覆盖率HTML报告已生成: $HTML_PATH"
    
    # 尝试使用系统默认浏览器打开报告(如果在图形环境中)
    if [ -n "$DISPLAY" ] || [ "$(uname)" == "Darwin" ]; then
        echo "尝试打开报告..."
        if [ "$(uname)" == "Darwin" ]; then
            open "$HTML_PATH" &> /dev/null
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$HTML_PATH" &> /dev/null
        elif command -v gnome-open &> /dev/null; then
            gnome-open "$HTML_PATH" &> /dev/null
        fi
    fi
fi

# 退出，传递原始退出码
exit $EXIT_CODE