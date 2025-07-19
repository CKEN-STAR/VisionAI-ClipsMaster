#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版的覆盖率强制检查脚本
用于演示代码覆盖率检查功能
"""

import os
import sys
import glob
import subprocess
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).resolve().parents[1]

# 覆盖率阈值
CORE_THRESHOLD = 95.0  # 核心模块要求
API_THRESHOLD = 80.0   # 辅助模块要求

def print_header(text):
    """打印带格式的标题"""
    print("\n" + "=" * 60)
    print(f"    {text}")
    print("=" * 60)

def run_command(command):
    """运行命令并返回结果"""
    print(f"执行命令: {command}")
    try:
        # 直接运行命令，不捕获输出，避免编码问题
        return subprocess.call(command, shell=True)
    except Exception as e:
        print(f"命令执行失败: {e}")
        return 1

def main():
    """主函数"""
    print_header("VisionAI-ClipsMaster 代码覆盖率强制检查")
    
    # 找到适合当前操作系统的null设备
    null_device = "NUL" if sys.platform.startswith("win") else "/dev/null"
    
    # 运行核心模块测试
    print_header("核心模块覆盖率检查 (要求 ≥ 95%)")
    result = run_command(f"python -m pytest tests/unit_test -c {null_device} --cov=src/core --cov=src/utils --cov-fail-under=95")
    if result != 0:
        print("\n❌ 核心模块覆盖率未达到要求 (95%)")
    else:
        print("\n✅ 核心模块覆盖率符合要求 (≥ 95%)")
    
    # 运行辅助模块测试
    print_header("辅助模块覆盖率检查 (要求 ≥ 80%)")
    result = run_command(f"python -m pytest tests/unit_test -c {null_device} --cov=src/api --cov=src/exporters --cov-fail-under=80")
    if result != 0:
        print("\n❌ 辅助模块覆盖率未达到要求 (80%)")
    else:
        print("\n✅ 辅助模块覆盖率符合要求 (≥ 80%)")
    
    # 生成完整的HTML报告
    print_header("生成完整覆盖率报告")
    report_dir = project_root / "coverage_reports"
    report_dir.mkdir(exist_ok=True, parents=True)
    html_dir = report_dir / "html"
    
    run_command(f"python -m pytest tests/unit_test -c {null_device} --cov=src --cov-report=html:{html_dir}")
    
    print(f"\n📊 覆盖率HTML报告已生成: {html_dir / 'index.html'}")
    print("\n完成覆盖率检查！")

if __name__ == "__main__":
    main() 