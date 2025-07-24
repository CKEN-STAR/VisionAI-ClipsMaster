#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步测试导入过程
"""

import sys
import os

# 添加路径
sys.path.insert(0, 'src')

print("=== 逐步导入测试 ===")

try:
    print("1. 导入模块...")
    import core.clip_generator as cg_module
    print("   模块导入成功")
    
    print("2. 检查模块属性...")
    print(f"   模块属性: {[attr for attr in dir(cg_module) if not attr.startswith('_')]}")
    
    print("3. 获取ClipGenerator类...")
    ClipGenerator = cg_module.ClipGenerator
    print(f"   类对象: {ClipGenerator}")
    
    print("4. 检查类属性...")
    class_attrs = [attr for attr in dir(ClipGenerator) if not attr.startswith('_')]
    print(f"   类属性: {class_attrs}")
    
    print("5. 创建实例...")
    try:
        instance = ClipGenerator()
        print("   实例创建成功")
        
        print("6. 检查实例属性...")
        instance_attrs = [attr for attr in dir(instance) if not attr.startswith('_')]
        print(f"   实例属性: {instance_attrs}")
        
    except Exception as e:
        print(f"   实例创建失败: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"导入失败: {e}")
    import traceback
    traceback.print_exc()
