#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI依赖安装脚本
专门为系统Python安装必要的UI依赖
"""

import sys
import subprocess
import os

def run_pip_install(packages):
    """使用pip安装包"""
    python_exe = sys.executable
    for package in packages:
        print(f"正在安装 {package}...")
        try:
            result = subprocess.run([
                python_exe, "-m", "pip", "install", package
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✓ {package} 安装成功")
            else:
                print(f"✗ {package} 安装失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"✗ {package} 安装超时")
        except Exception as e:
            print(f"✗ {package} 安装出错: {e}")

def main():
    print("=== VisionAI-ClipsMaster UI依赖安装 ===")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    # 核心UI依赖（必须）
    core_packages = [
        "PyQt6",
        "PyQt6-Charts",
    ]
    
    # 基础功能依赖（推荐）
    basic_packages = [
        "matplotlib",
        "numpy",
        "pandas",
        "requests",
        "pyyaml",
        "tqdm",
        "psutil",
    ]
    
    # NLP依赖（可选，但建议安装）
    nlp_packages = [
        "jieba",
        "langdetect",
        "nltk",
    ]
    
    print("\n1. 安装核心UI依赖...")
    run_pip_install(core_packages)
    
    print("\n2. 安装基础功能依赖...")
    run_pip_install(basic_packages)
    
    print("\n3. 安装NLP依赖...")
    run_pip_install(nlp_packages)
    
    print("\n=== 安装完成 ===")
    print("现在可以尝试运行 simple_ui_fixed.py")
    print("命令: C:\\\\1sers\\\\13075\\\\1ppData\\\\1ocal\\\\1rograms\\\\1ython\\\\1ython313\\\\1ython.exe simple_ui_fixed.py")

if __name__ == "__main__":
    main()
