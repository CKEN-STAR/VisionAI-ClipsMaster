#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 生成合规报告的便捷工具

此脚本用于在项目根目录下直接运行合规报告生成器。
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成VisionAI-ClipsMaster合规报告")
    parser.add_argument("--output", help="输出目录", default="reports/compliance")
    parser.add_argument("--format", help="输出格式(html,json,txt,all)", default="all")
    parser.add_argument("--title", help="报告标题", default="法律合规性报告")
    parser.add_argument("--verbose", help="显示详细日志", action="store_true")
    
    args = parser.parse_args()
    
    # 构建输出目录
    output_dir = os.path.join("tests", "legal_test", args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # 构建命令行参数
    cmd_args = [sys.executable, "tests/legal_test/compliance_reporter.py"]
    cmd_args.extend(["--output", output_dir])
    cmd_args.extend(["--format", args.format])
    cmd_args.extend(["--title", args.title])
    
    if args.verbose:
        cmd_args.append("--verbose")
    
    # 运行合规报告生成器
    print(f"正在生成合规报告...")
    try:
        result = subprocess.run(cmd_args, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"错误信息: {result.stderr}", file=sys.stderr)
        
        print(f"合规报告生成" + ("成功" if result.returncode == 0 else "失败"))
        return result.returncode
    except Exception as e:
        print(f"运行合规报告生成器时发生错误: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 