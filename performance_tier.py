"""
测试性能分级模块
简化版本
"""

import os
import sys
import psutil
import platform

def get_performance_tier():
    """获取性能等级"""
    try:
        mem = psutil.virtual_memory()
        ram_gb = mem.total / (1024**3)
        
        if ram_gb <= 4:
            return "low"
        elif ram_gb <= 8:
            return "medium"
        else:
            return "high"
    except:
        return "medium"  # 默认中等配置

if __name__ == "__main__":
    print(f"Python版本: {sys.version}")
    print(f"平台: {platform.platform()}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"内存: {psutil.virtual_memory().total / (1024**3):.2f} GB")
    print(f"CPU核心数: {psutil.cpu_count(logical=False) or 0}")
    print(f"逻辑处理器数: {psutil.cpu_count(logical=True) or 0}")
    print(f"性能等级: {get_performance_tier()}") 