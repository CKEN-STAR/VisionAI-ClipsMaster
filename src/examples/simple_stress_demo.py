#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单压力测试演示
"""

import os
import sys
import time
import traceback

# 添加src到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 确保目录存在
os.makedirs("data/stress_test_results", exist_ok=True)
os.makedirs("data/stress_test_io", exist_ok=True)
os.makedirs("data/stress_test_files", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# 设置日志记录
import logging
logging.basicConfig(level=logging.INFO)

# 引入压力测试模块
try:
    from src.quality.stress_test import ResourceLimiter
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所需依赖:")
    print("  - psutil: 用于系统资源监控")
    print("  - numpy: 用于数据处理")
    sys.exit(1)

def main():
    """简单压力测试演示"""
    print("开始简单压力测试演示")
    
    # 创建资源限制器
    limiter = ResourceLimiter()
    
    try:
        # CPU压力测试
        print("1. 测试CPU限制...")
        limiter.limit_cpu(0.5)  # 限制到50%
        print("   CPU限制已应用，等待5秒...")
        time.sleep(5)
        limiter.release_cpu()
        print("   CPU资源已释放")
        
        # IO压力测试
        print("2. 测试IO限制...")
        limiter.limit_io(0.3)  # 30%强度
        print("   IO限制已应用，等待5秒...")
        time.sleep(5)
        limiter.release_io()
        print("   IO资源已释放")
        
    except Exception as e:
        print(f"运行压力测试时发生错误: {e}")
        print(traceback.format_exc())
    finally:
        # 确保资源释放
        limiter.release_all()
    
    print("演示完成")

if __name__ == "__main__":
    main() 