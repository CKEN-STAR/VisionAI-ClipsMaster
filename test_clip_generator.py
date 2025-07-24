#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ClipGenerator类的方法
"""

import sys
import os
sys.path.insert(0, 'src')

try:
    from core.clip_generator import ClipGenerator
    
    print("=== ClipGenerator 类分析 ===")
    cg = ClipGenerator()
    
    # 获取所有方法
    all_methods = [method for method in dir(cg) if not method.startswith('_')]
    print(f"所有公共方法: {all_methods}")
    
    # 检查特定方法
    methods_to_check = ['generate_clips', 'generate_from_srt', 'extract_segments', 'concatenate_segments']
    
    for method in methods_to_check:
        has_method = hasattr(cg, method)
        print(f"{method}: {'✓' if has_method else '✗'}")
        
        if has_method:
            method_obj = getattr(cg, method)
            print(f"  类型: {type(method_obj)}")
            if hasattr(method_obj, '__doc__'):
                doc = method_obj.__doc__
                if doc:
                    print(f"  文档: {doc.split('.')[0]}...")
    
    # 检查类的MRO
    print(f"\n类的MRO: {ClipGenerator.__mro__}")
    
    # 检查类的字典
    class_methods = [name for name in ClipGenerator.__dict__ if not name.startswith('_')]
    print(f"类字典中的方法: {class_methods}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
