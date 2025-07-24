#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试ClipGenerator类初始化问题
"""

import sys
import os

# 添加路径
sys.path.insert(0, 'src')

print("=== 调试ClipGenerator类初始化 ===")

try:
    print("1. 导入模块...")
    import core.clip_generator as cg_module
    print("   模块导入成功")
    
    print("2. 获取类...")
    ClipGenerator = cg_module.ClipGenerator
    print(f"   类获取成功: {ClipGenerator}")
    
    print("3. 检查类的原始方法...")
    class_methods = [name for name in ClipGenerator.__dict__ if not name.startswith('_')]
    print(f"   类字典中的方法: {class_methods}")
    
    print("4. 尝试创建实例（不调用__init__）...")
    # 创建实例但不调用__init__
    instance = object.__new__(ClipGenerator)
    print("   实例创建成功（未初始化）")
    
    # 检查实例的方法
    instance_methods = [name for name in dir(instance) if not name.startswith('_')]
    print(f"   未初始化实例的方法: {instance_methods}")
    
    print("5. 尝试调用__init__...")
    try:
        instance.__init__()
        print("   __init__调用成功")
        
        # 检查初始化后的方法
        init_methods = [name for name in dir(instance) if not name.startswith('_')]
        print(f"   初始化后实例的方法: {init_methods}")
        
    except Exception as e:
        print(f"   __init__调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("6. 检查特定方法...")
    for method_name in ['generate_clips', 'concatenate_segments', 'extract_segments']:
        has_method = hasattr(ClipGenerator, method_name)
        print(f"   {method_name}: {'✓' if has_method else '✗'}")
        
        if has_method:
            method = getattr(ClipGenerator, method_name)
            print(f"     类型: {type(method)}")
    
except Exception as e:
    print(f"调试失败: {e}")
    import traceback
    traceback.print_exc()
