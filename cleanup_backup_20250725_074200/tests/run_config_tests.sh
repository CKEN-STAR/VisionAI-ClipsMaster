#!/bin/bash
# 配置系统测试运行脚本 (Linux/macOS版)

echo "正在运行VisionAI-ClipsMaster配置系统测试..."
echo

# 设置Python路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR/.."

# 处理帮助选项
if [ "$1" == "--help" ]; then
    echo "使用方法: ./run_config_tests.sh [选项]"
    echo
    echo "选项:"
    echo "  --test [类名]     运行指定的测试类"
    echo "  -v, --verbose     增加输出详细级别"
    echo "  --report          生成测试报告"
    echo "  --help            显示此帮助信息"
    exit 0
fi

# 解析命令行参数
ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            ARGS="$ARGS --test $2"
            shift
            ;;
        -v|--verbose)
            ARGS="$ARGS -v"
            ;;
        --report)
            ARGS="$ARGS --report"
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 ./run_config_tests.sh --help 查看帮助"
            exit 1
            ;;
    esac
    shift
done

# 运行测试
python -m tests.config_test.run_config_tests $ARGS

# 检查结果
if [ $? -ne 0 ]; then
    echo
    echo "测试失败! 详见上方输出。"
    exit 1
else
    echo
    echo "测试成功完成!"
    exit 0
fi 