#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存泄漏检测器运行脚本

此脚本提供简单的命令行接口来运行内存泄漏检测。
"""

import os
import sys
import importlib.util
import subprocess
from pathlib import Path

# 确保可以导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def find_cli_script():
    """查找CLI脚本的路径"""
    # 尝试直接导入
    try:
        from src.tools.leak_detector_cli import main
        module_spec = importlib.util.find_spec("src.tools.leak_detector_cli")
        if module_spec:
            return module_spec.origin
    except ImportError:
        pass
    
    # 尝试查找文件
    project_root = Path(__file__).parent.parent
    possible_paths = [
        project_root / "src" / "tools" / "leak_detector_cli.py",
        project_root / "src" / "tools" / "memory_leak_detector_cli.py",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    return None

def main():
    """主函数"""
    # 查找CLI脚本
    cli_script = find_cli_script()
    
    if not cli_script:
        print("错误: 找不到泄漏检测器CLI脚本")
        return 1
    
    # 构建命令
    cmd = [sys.executable, cli_script] + sys.argv[1:]
    
    # 执行命令
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\n内存泄漏检测已中断")
        return 0
    except Exception as e:
        print(f"错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 