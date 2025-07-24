#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步调试ClipGenerator类
"""

import sys
import os

# 添加路径
sys.path.insert(0, 'src')

print("=== 逐步调试ClipGenerator类 ===")

try:
    print("1. 导入模块...")
    import core.clip_generator as cg_module
    print("   模块导入成功")
    
    print("2. 获取ClipGenerator类...")
    ClipGenerator = cg_module.ClipGenerator
    print(f"   类获取成功: {ClipGenerator}")
    
    print("3. 检查类的原始字典...")
    class_dict = ClipGenerator.__dict__
    class_methods = [name for name in class_dict if not name.startswith('_')]
    print(f"   类字典中的方法: {class_methods}")
    
    print("4. 检查类的所有属性...")
    all_attrs = dir(ClipGenerator)
    all_methods = [name for name in all_attrs if not name.startswith('_')]
    print(f"   所有属性: {all_methods}")
    
    print("5. 检查特定方法是否在类字典中...")
    methods_to_check = ['generate_clips', 'concatenate_segments', 'extract_segments', 'generate_from_srt']
    
    for method in methods_to_check:
        in_dict = method in class_dict
        in_dir = hasattr(ClipGenerator, method)
        print(f"   {method}: 字典中={in_dict}, dir中={in_dir}")
    
    print("6. 尝试创建实例（不调用__init__）...")
    instance = object.__new__(ClipGenerator)
    print("   实例创建成功（未初始化）")
    
    # 检查实例的方法
    instance_methods = [name for name in dir(instance) if not name.startswith('_')]
    print(f"   未初始化实例的方法: {instance_methods}")
    
    print("7. 检查方法是否可调用...")
    for method in methods_to_check:
        if hasattr(ClipGenerator, method):
            method_obj = getattr(ClipGenerator, method)
            is_callable = callable(method_obj)
            print(f"   {method}: 可调用={is_callable}, 类型={type(method_obj)}")
    
except Exception as e:
    print(f"调试失败: {e}")
    import traceback
    traceback.print_exc()
