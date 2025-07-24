#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试ClipGenerator类
"""

import sys
import os
import importlib

# 添加路径
sys.path.insert(0, 'src')

print("=== 最终ClipGenerator测试 ===")

# 清理所有相关模块缓存
modules_to_remove = []
for module_name in list(sys.modules.keys()):
    if 'clip_generator' in module_name or 'core' in module_name:
        modules_to_remove.append(module_name)

for module_name in modules_to_remove:
    if module_name in sys.modules:
        del sys.modules[module_name]

print(f"清理了 {len(modules_to_remove)} 个模块缓存")

try:
    # 重新导入
    from core.clip_generator import ClipGenerator
    
    print("1. ClipGenerator导入成功")
    
    # 创建实例
    cg = ClipGenerator()
    print("2. ClipGenerator实例创建成功")
    
    # 检查所有方法
    all_methods = [m for m in dir(cg) if not m.startswith('_')]
    print(f"3. 所有公共方法: {all_methods}")
    
    # 检查特定方法
    methods_to_check = ['generate_clips', 'concatenate_segments', 'extract_segments', 'generate_from_srt']
    
    for method in methods_to_check:
        has_method = hasattr(cg, method)
        print(f"   {method}: {'✓' if has_method else '✗'}")
        
        if has_method:
            method_obj = getattr(cg, method)
            print(f"     类型: {type(method_obj)}")
    
    # 测试concatenate_segments方法
    if hasattr(cg, 'concatenate_segments'):
        print("\n4. 测试concatenate_segments方法...")
        test_segments = [
            {"source": "nonexistent1.mp4"},
            {"source": "nonexistent2.mp4"}
        ]
        test_output = "test_output.mp4"
        
        try:
            result = cg.concatenate_segments(test_segments, test_output)
            print(f"   方法调用成功，返回: {result}")
        except Exception as e:
            print(f"   方法调用失败（预期的）: {e}")
    else:
        print("\n4. concatenate_segments方法不存在！")
        
        # 检查类的字典
        class_methods = [name for name in ClipGenerator.__dict__ if not name.startswith('_')]
        print(f"   类字典中的方法: {class_methods}")
        
        # 检查类的MRO
        print(f"   类的MRO: {ClipGenerator.__mro__}")
    
    print("\n测试完成")
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()
