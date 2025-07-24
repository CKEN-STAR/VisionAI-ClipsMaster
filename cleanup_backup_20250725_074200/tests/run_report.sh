#!/bin/bash

echo "正在生成VisionAI-ClipsMaster测试报告..."

# 创建报告目录
mkdir -p reports/static

# 生成测试报告
python tests/generate_report.py -o reports/test_report.html

# 如果成功生成，尝试打开报告
if [ $? -eq 0 ]; then
    echo "报告生成成功!"
    
    # 尝试使用不同的浏览器打开
    if command -v xdg-open > /dev/null; then
        xdg-open reports/test_report.html  # Linux
    elif command -v open > /dev/null; then
        open reports/test_report.html      # macOS
    else
        echo "报告已生成: reports/test_report.html"
        echo "请手动打开报告文件。"
    fi
else
    echo "报告生成失败，请检查错误信息。"
fi

echo "操作完成。" 