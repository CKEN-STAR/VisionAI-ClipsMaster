#!/bin/bash
# VisionAI-ClipsMaster 测试文档生成工具
# 该脚本用于生成详细的测试文档

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 标题
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   VisionAI-ClipsMaster 测试文档生成工具   ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo

# 运行文档生成脚本
echo -e "${YELLOW}开始生成测试文档...${NC}"
python "$SCRIPT_DIR/generate_test_docs.py" "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo
    echo -e "${GREEN}✓ 测试文档生成成功${NC}"
    echo -e "${GREEN}文档已保存到: ${PROJECT_ROOT}/docs/tests/${NC}"
    
    # 显示生成的文档列表
    echo
    echo -e "${YELLOW}生成的文档:${NC}"
    echo -e "- ${PROJECT_ROOT}/docs/tests/README.md"
    echo -e "- ${PROJECT_ROOT}/docs/tests/TEST_STRUCTURE.md"
    echo -e "- ${PROJECT_ROOT}/docs/tests/TEST_CASES.md"
    echo -e "- ${PROJECT_ROOT}/docs/tests/TEST_COVERAGE.md"
else
    echo
    echo -e "${RED}✗ 测试文档生成失败，退出代码: $EXIT_CODE${NC}"
fi

exit $EXIT_CODE 