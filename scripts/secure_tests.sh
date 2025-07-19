#!/bin/bash
# 测试权限加固脚本
# 该脚本设置正确的测试目录权限，防止测试数据被意外修改

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "正在运行测试权限加固..."

# 执行Python脚本
python "$SCRIPT_DIR/secure_test_permissions.py" "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ 测试权限加固成功"
else
    echo "✗ 测试权限加固失败，退出代码: $EXIT_CODE"
    echo "  请运行 'python scripts/secure_test_permissions.py --fix' 尝试修复"
fi

exit $EXIT_CODE 