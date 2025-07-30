#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WMI模块IDE识别测试文件
用于验证IDE是否能正确识别WMI模块导入
"""

# 测试WMI模块导入
try:
    import wmi  # IDE应该能够识别此导入
    print("WMI模块导入成功")
    
    # 测试WMI实例创建
    c = wmi.WMI()
    print("WMI实例创建成功")
    
    # 测试GPU检测
    gpu_count = 0
    for gpu in c.Win32_VideoController():
        if gpu.Name:
            gpu_count += 1
            print(f"检测到GPU: {gpu.Name}")
    
    print(f"总共检测到{gpu_count}个显卡")
    
except ImportError as e:
    print(f"WMI模块导入失败: {e}")
except Exception as e:
    print(f"WMI功能测试失败: {e}")

# 验证WMI模块属性
if 'wmi' in locals():
    print(f"WMI模块位置: {wmi.__file__}")
    print(f"WMI模块版本: {getattr(wmi, '__version__', '未知')}")
