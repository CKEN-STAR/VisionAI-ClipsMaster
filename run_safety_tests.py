#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 安全测试启动脚本
一键运行所有安全测试并生成汇总报告
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
logger = logging.getLogger("safety_test_runner")

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

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 安全测试启动脚本")
    parser.add_argument("--skip-memory", action="store_true", help="跳过内存测试")
    parser.add_argument("--skip-thread", action="store_true", help="跳过线程测试")
    parser.add_argument("--skip-report", action="store_true", help="跳过报告生成")
    parser.add_argument("--quick", action="store_true", help="快速测试模式（缩短测试时间）")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  VisionAI-ClipsMaster 安全测试启动脚本")
    print("="*60 + "\n")
    
    # 确保报告目录存在
    reports_dir = Path("reports")
    ensure_directory_exists(reports_dir)
    ensure_directory_exists(reports_dir / "memory")
    ensure_directory_exists(reports_dir / "thread")
    ensure_directory_exists(reports_dir / "performance")
    
    # 记录测试开始时间
    start_time = time.time()
    
    # 运行内存测试
    if not args.skip_memory:
        print("\n[1/3] 运行内存泄漏测试...")
        
        # 正常模式测试
        duration = 10 if args.quick else 30
        cmd = f"python automated_safety_test.py --memory-test --duration {duration}"
        code, output = run_command(cmd, "内存泄漏测试 (正常模式)")
        if code != 0:
            print(f"内存泄漏测试 (正常模式) 失败，错误代码: {code}")
        
        # 泄漏模拟测试
        cmd = f"python automated_safety_test.py --memory-test --leak-simulation --duration {duration}"
        code, output = run_command(cmd, "内存泄漏测试 (泄漏模拟)")
        if code != 0:
            print(f"内存泄漏测试 (泄漏模拟) 失败，错误代码: {code}")
    
    # 运行线程测试
    if not args.skip_thread:
        print("\n[2/3] 运行线程安全测试...")
        
        # 标准线程测试
        thread_count = 3 if args.quick else 5
        duration = 3 if args.quick else 10
        cmd = f"python automated_safety_test.py --thread-test --thread-count {thread_count} --duration {duration}"
        code, output = run_command(cmd, "线程安全测试 (标准线程)")
        if code != 0:
            print(f"线程安全测试 (标准线程) 失败，错误代码: {code}")
        
        # 工作线程测试
        cmd = f"python automated_safety_test.py --worker-test --thread-count {thread_count}"
        code, output = run_command(cmd, "线程安全测试 (工作线程)")
        if code != 0:
            print(f"线程安全测试 (工作线程) 失败，错误代码: {code}")
    
    # 生成性能报告
    if not args.skip_report:
        print("\n[3/3] 生成性能报告...")
        
        cmd = "python performance_report_generator.py"
        code, output = run_command(cmd, "生成性能报告")
        if code != 0:
            print(f"生成性能报告失败，错误代码: {code}")
        else:
            # 提取报告路径
            report_path = None
            for line in output.split("\n"):
                if "汇总报告已生成" in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        report_path = parts[1].strip()
                    break
            
            if report_path:
                print(f"\n性能报告已生成: {report_path}")
                
                # 显示报告内容
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_content = f.read()
                        print("\n" + "="*60)
                        print("  性能报告摘要")
                        print("="*60 + "\n")
                        
                        # 提取报告摘要
                        lines = report_content.split("\n")
                        in_conclusion = False
                        for line in lines:
                            if "## 测试结论" in line:
                                in_conclusion = True
                                print(line)
                            elif in_conclusion and line.strip():
                                print(line)
                except Exception as e:
                    print(f"读取报告失败: {e}")
    
    # 计算总耗时
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    
    print("\n" + "="*60)
    print(f"  测试完成! 总耗时: {int(minutes)}分 {int(seconds)}秒")
    print("="*60 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 