#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 框架验证启动器
该脚本是验证框架的简单启动器，可在任何平台上运行
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 获取项目根目录（本脚本所在目录）
    project_root = Path(__file__).parent.absolute()
    
    # 验证脚本路径
    validate_py = project_root / "tests" / "validate_framework.py"
    validate_sh = project_root / "tests" / "validate_framework.sh"
    validate_bat = project_root / "tests" / "validate_framework.bat"
    
    # 确定要运行的脚本
    os_name = platform.system()
    
    if validate_py.exists():
        # 首选Python版本，跨平台兼容
        print("使用Python版本验证框架...")
        result = subprocess.run([sys.executable, str(validate_py)], check=False)
        return result.returncode
    elif os_name == "Windows" and validate_bat.exists():
        # Windows批处理版本
        print("使用Windows批处理版本验证框架...")
        result = subprocess.run([str(validate_bat)], shell=True, check=False)
        return result.returncode
    elif os_name != "Windows" and validate_sh.exists():
        # Linux/macOS Bash版本
        print("使用Bash版本验证框架...")
        result = subprocess.run(["bash", str(validate_sh)], check=False)
        return result.returncode
    else:
        print("错误: 找不到验证脚本!")
        print(f"已检查以下路径:")
        print(f"  - {validate_py}")
        print(f"  - {validate_bat}" if os_name == "Windows" else f"  - {validate_sh}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 