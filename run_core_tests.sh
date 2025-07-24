#!/bin/bash
# VisionAI-ClipsMaster 核心功能测试执行脚本
# 
# 用法:
#   ./run_core_tests.sh                    - 运行所有核心测试
#   ./run_core_tests.sh --alignment        - 只运行对齐测试
#   ./run_core_tests.sh --screenplay       - 只运行剧本重构测试
#   ./run_core_tests.sh --language         - 只运行语言检测测试
#   ./run_core_tests.sh --integration      - 只运行集成测试
#   ./run_core_tests.sh --comprehensive    - 运行完整测试套件

set -e  # 遇到错误时退出

echo "========================================"
echo "VisionAI-ClipsMaster 核心功能测试"
echo "========================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "错误: 未找到Python环境"
        echo "请确保Python 3.8+已安装"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "使用Python命令: $PYTHON_CMD"
$PYTHON_CMD --version

# 设置项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src:$PYTHONPATH"

echo "项目根目录: $PROJECT_ROOT"

# 检查测试文件是否存在
if [ ! -f "$PROJECT_ROOT/tests/core_functionality_comprehensive_test.py" ]; then
    echo "错误: 核心测试文件不存在"
    echo "请确保测试文件位于 tests/ 目录下"
    exit 1
fi

# 创建输出目录
mkdir -p "$PROJECT_ROOT/test_output"

echo ""
echo "开始执行测试..."
echo ""

# 测试失败标志
TEST_FAILED=0

# 根据参数执行不同的测试
case "$1" in
    --alignment)
        echo "执行视频-字幕对齐精度测试..."
        $PYTHON_CMD -m unittest tests.core_functionality_comprehensive_test.VideoSubtitleMappingTest -v
        exit $?
        ;;
    --screenplay)
        echo "执行剧本重构能力测试..."
        $PYTHON_CMD -m unittest tests.core_functionality_comprehensive_test.ScreenplayReconstructionTest -v
        exit $?
        ;;
    --language)
        echo "执行语言检测和模型切换测试..."
        $PYTHON_CMD -m unittest tests.core_functionality_comprehensive_test.LanguageModelSwitchingTest -v
        exit $?
        ;;
    --integration)
        echo "执行端到端集成测试..."
        $PYTHON_CMD tests/end_to_end_integration_test.py
        exit $?
        ;;
    --comprehensive)
        echo "执行完整验证测试套件..."
        $PYTHON_CMD tests/run_comprehensive_validation_tests.py --output-dir test_output
        exit $?
        ;;
    *)
        # 默认执行所有核心测试
        echo "执行所有核心功能测试..."
        echo ""
        ;;
esac

# 执行所有核心测试
echo "[1/4] 视频-字幕映射精度测试"
echo "--------------------------------"
if ! $PYTHON_CMD -m unittest tests.core_functionality_comprehensive_test.VideoSubtitleMappingTest -v; then
    echo "视频-字幕映射测试失败"
    TEST_FAILED=1
else
    echo "视频-字幕映射测试通过"
fi

echo ""
echo "[2/4] 剧本重构能力测试"
echo "--------------------------------"
if ! $PYTHON_CMD -m unittest tests.core_functionality_comprehensive_test.ScreenplayReconstructionTest -v; then
    echo "剧本重构测试失败"
    TEST_FAILED=1
else
    echo "剧本重构测试通过"
fi

echo ""
echo "[3/4] 语言检测和模型切换测试"
echo "--------------------------------"
if ! $PYTHON_CMD -m unittest tests.core_functionality_comprehensive_test.LanguageModelSwitchingTest -v; then
    echo "语言检测测试失败"
    TEST_FAILED=1
else
    echo "语言检测测试通过"
fi

echo ""
echo "[4/4] 端到端集成测试"
echo "--------------------------------"
if ! $PYTHON_CMD tests/end_to_end_integration_test.py; then
    echo "集成测试失败"
    TEST_FAILED=1
else
    echo "集成测试通过"
fi

echo ""
echo "========================================"
if [ $TEST_FAILED -eq 1 ]; then
    echo "测试结果: 部分测试失败"
    echo "请查看上方输出了解详细信息"
    echo "========================================"
    exit 1
else
    echo "测试结果: 所有测试通过"
    echo "========================================"
    echo ""
    echo "可选操作:"
    echo "  1. 查看详细报告: test_output/"
    echo "  2. 运行完整测试: ./run_core_tests.sh --comprehensive"
    echo "  3. 生成测试数据: $PYTHON_CMD tests/test_data_preparation.py"
    echo ""
fi
