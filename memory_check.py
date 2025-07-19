#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 内存使用检查脚本
"""

import os
import sys
import time
import psutil
import subprocess

def check_memory():
    """检查当前内存使用情况"""
    mem = psutil.virtual_memory()
    print(f"系统内存总量: {mem.total / (1024**3):.2f} GB")
    print(f"可用内存: {mem.available / (1024**3):.2f} GB")
    print(f"内存使用率: {mem.percent}%")
    print(f"当前进程内存使用: {psutil.Process().memory_info().rss / (1024**2):.2f} MB")
    
    return mem.percent < 90  # 如果内存使用率低于90%，则返回True

def run_application_and_monitor(app_cmd, duration=60, interval=5):
    """运行应用程序并监控内存使用情况
    
    Args:
        app_cmd: 应用程序命令
        duration: 监控持续时间（秒）
        interval: 检查间隔（秒）
    """
    # 启动应用程序
    print(f"启动应用程序: {app_cmd}")
    try:
        app_process = subprocess.Popen(app_cmd, shell=True)
        
        # 等待应用程序启动
        time.sleep(5)
        
        # 监控内存使用
        start_time = time.time()
        max_memory_usage = 0
        max_app_memory = 0
        
        while time.time() - start_time < duration:
            # 检查应用程序是否仍在运行
            if app_process.poll() is not None:
                print(f"应用程序已退出，退出代码: {app_process.returncode}")
                break
                
            # 检查内存使用情况
            mem = psutil.virtual_memory()
            
            # 获取应用程序进程的内存使用
            try:
                app_mem = psutil.Process(app_process.pid).memory_info().rss / (1024**2)
                if app_mem > max_app_memory:
                    max_app_memory = app_mem
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_mem = 0
                
            print(f"[{time.time() - start_time:.1f}s] 内存使用率: {mem.percent}%, 应用内存: {app_mem:.2f} MB")
            
            if mem.percent > max_memory_usage:
                max_memory_usage = mem.percent
                
            # 等待下一次检查
            time.sleep(interval)
            
        # 终止应用程序
        if app_process.poll() is None:
            app_process.terminate()
            app_process.wait(timeout=5)
            
        print(f"测试完成，最大内存使用率: {max_memory_usage}%")
        print(f"应用程序最大内存使用: {max_app_memory:.2f} MB")
        
        # 判断是否通过测试（内存使用是否低于4GB）
        passed = max_app_memory < 4 * 1024  # 4GB转换为MB
        print(f"内存测试结果: {'通过' if passed else '失败'}")
        
        return passed
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        return False

if __name__ == "__main__":
    print("=== 系统内存检查 ===")
    check_memory()
    
    print("\n=== 应用程序内存测试 ===")
    app_cmd = "python simple_ui_fixed.py"
    run_application_and_monitor(app_cmd, duration=30, interval=2) 