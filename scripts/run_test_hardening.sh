#!/bin/bash
# 测试权限加固一键运行脚本
# 该脚本执行完整的测试权限加固流程

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==================================================="
echo "           VisionAI-ClipsMaster                   "
echo "            测试权限加固工具                      "
echo "==================================================="
echo ""

# 执行Python脚本
python "$SCRIPT_DIR/run_test_hardening.py" "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ 测试权限加固成功完成！"
else
    echo ""
    echo "❌ 测试权限加固失败，退出代码: $EXIT_CODE"
fi

exit $EXIT_CODE 