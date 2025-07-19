#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 框架验证启动器 (命令行工具)
该脚本是验证框架的简单启动器，用于命令行使用
"""

import os
import sys
import argparse
import platform
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 框架验证工具')
    parser.add_argument('--fix', action='store_true', help='尝试自动修复发现的问题')
    parser.add_argument('--strict', action='store_true', help='严格模式，将警告视为错误')
    parser.add_argument('--quiet', action='store_true', help='安静模式，仅显示错误和总结')
    parser.add_argument('--report', action='store_true', help='生成详细的验证报告')
    args = parser.parse_args()
    
    # 获取项目根目录（相对于脚本目录）
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    
    # 验证脚本路径
    validate_py = project_root / "tests" / "validate_framework.py"
    
    # 检查Python脚本是否存在
    if not validate_py.exists():
        print(f"错误: 找不到验证脚本 {validate_py}")
        return 1
    
    # 构建命令行参数
    cmd = [sys.executable, str(validate_py)]
    
    # 添加命令行参数（如果validate_framework.py支持这些参数的话）
    # 这里只是预留，目前的validate_framework.py并不支持这些参数
    if args.fix:
        cmd.append("--fix")
    if args.strict:
        cmd.append("--strict")
    if args.quiet:
        cmd.append("--quiet")
    if args.report:
        cmd.append("--report")
    
    # 显示标题
    print("=" * 60)
    print("  VisionAI-ClipsMaster 框架验证")
    print("=" * 60)
    print(f"运行验证: {' '.join(cmd)}")
    print()
    
    # 运行验证脚本
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"错误: 运行验证失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 