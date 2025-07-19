#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 安全框架安装脚本
用于安装所有依赖项并设置环境
"""

import os
import sys
import time
import subprocess
import logging
import argparse
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup_script")

def run_command(command, description=None):
    """运行命令并返回结果
    
    Args:
        command: 要运行的命令
        description: 命令描述
        
    Returns:
        tuple: (返回码, 输出)
    """
    if description:
        logger.info(f"开始执行: {description}")
        print(f"执行: {description}...")
    
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            if description:
                logger.info(f"成功执行: {description}")
            return 0, result.stdout
        else:
            if description:
                logger.error(f"执行失败: {description}")
                logger.error(f"错误信息: {result.stderr}")
            return result.returncode, result.stderr
    except Exception as e:
        if description:
            logger.error(f"执行异常: {description}")
            logger.error(f"异常信息: {str(e)}")
        return -1, str(e)

def ensure_directory_exists(path):
    """确保目录存在
    
    Args:
        path: 目录路径
    """
    Path(path).mkdir(parents=True, exist_ok=True)

def install_dependencies():
    """安装所需的依赖项"""
    print("\n[1/4] 安装依赖项...")
    
    # 安装matplotlib
    code, output = run_command("pip install matplotlib", "安装matplotlib")
    if code != 0:
        print("警告: matplotlib安装失败，可视化功能将不可用")
    
    # 安装PyQt6（如果不存在）
    code, output = run_command("pip install PyQt6", "安装PyQt6")
    if code != 0:
        print("警告: PyQt6安装失败，应用可能无法正常运行")
    
    # 安装psutil（用于内存监控）
    code, output = run_command("pip install psutil", "安装psutil")
    if code != 0:
        print("警告: psutil安装失败，内存监控功能将不可用")
    
    print("依赖项安装完成")

def create_directories():
    """创建必要的目录结构"""
    print("\n[2/4] 创建目录结构...")
    
    # 创建报告目录
    reports_dir = Path("reports")
    ensure_directory_exists(reports_dir)
    ensure_directory_exists(reports_dir / "memory")
    ensure_directory_exists(reports_dir / "thread")
    ensure_directory_exists(reports_dir / "performance")
    ensure_directory_exists(reports_dir / "visualizations")
    
    print("目录结构创建完成")

def run_initial_tests():
    """运行初始测试"""
    print("\n[3/4] 运行初始测试...")
    
    # 运行快速测试
    cmd = "python automated_safety_test.py --quick"
    code, output = run_command(cmd, "运行快速安全测试")
    if code != 0:
        print(f"警告: 安全测试运行失败，错误代码: {code}")
    
    # 生成可视化报告
    cmd = "python report_visualizer.py"
    code, output = run_command(cmd, "生成可视化报告")
    if code != 0:
        print(f"警告: 可视化报告生成失败，错误代码: {code}")
    
    print("初始测试完成")

def create_shortcuts():
    """创建快捷方式"""
    print("\n[4/4] 创建快捷方式...")
    
    # 创建批处理文件
    batch_dir = Path("shortcuts")
    ensure_directory_exists(batch_dir)
    
    # 创建测试批处理文件
    test_batch = batch_dir / "run_safety_tests.bat"
    with open(test_batch, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("echo 运行安全测试...\n")
        f.write("python run_safety_tests.py %*\n")
        f.write("pause\n")
    
    # 创建可视化批处理文件
    viz_batch = batch_dir / "generate_reports.bat"
    with open(viz_batch, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("echo 生成可视化报告...\n")
        f.write("python report_visualizer.py %*\n")
        f.write("pause\n")
    
    print("快捷方式创建完成")

def verify_installation():
    """验证安装"""
    print("\n正在验证安装...")
    
    # 检查必要文件
    required_files = [
        "ui/utils/memory_leak_detector.py",
        "ui/utils/thread_manager.py",
        "automated_safety_test.py",
        "performance_report_generator.py",
        "report_visualizer.py",
        "run_safety_tests.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("警告: 以下必要文件缺失:")
        for file in missing_files:
            print(f"  - {file}")
        print("安装可能不完整，请检查文件")
    else:
        print("所有必要文件已存在")
    
    # 检查目录结构
    required_dirs = [
        "reports",
        "reports/memory",
        "reports/thread",
        "reports/performance",
        "reports/visualizations"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print("警告: 以下必要目录缺失:")
        for dir in missing_dirs:
            print(f"  - {dir}")
        print("目录结构可能不完整，请检查")
    else:
        print("所有必要目录已创建")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 安全框架安装脚本")
    parser.add_argument("--skip-dependencies", action="store_true", help="跳过依赖项安装")
    parser.add_argument("--skip-tests", action="store_true", help="跳过初始测试")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  VisionAI-ClipsMaster 安全框架安装")
    print("="*60 + "\n")
    
    # 记录安装开始时间
    start_time = time.time()
    
    # 安装依赖项
    if not args.skip_dependencies:
        install_dependencies()
    else:
        print("\n[1/4] 跳过依赖项安装")
    
    # 创建目录结构
    create_directories()
    
    # 运行初始测试
    if not args.skip_tests:
        run_initial_tests()
    else:
        print("\n[3/4] 跳过初始测试")
    
    # 创建快捷方式
    create_shortcuts()
    
    # 验证安装
    verify_installation()
    
    # 计算总耗时
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    
    print("\n" + "="*60)
    print(f"  安装完成! 总耗时: {int(minutes)}分 {int(seconds)}秒")
    print("="*60 + "\n")
    
    print("使用说明:")
    print("  1. 运行安全测试: python run_safety_tests.py")
    print("  2. 生成可视化报告: python report_visualizer.py")
    print("  3. 查看使用文档: README_MEMORY_SAFETY.md")
    print("\n快捷方式:")
    print("  - shortcuts/run_safety_tests.bat: 运行安全测试")
    print("  - shortcuts/generate_reports.bat: 生成可视化报告")
    print("\n祝您使用愉快!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 