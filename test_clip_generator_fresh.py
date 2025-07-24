#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制重新加载ClipGenerator模块进行测试
"""

import sys
import os
import importlib

# 清理模块缓存
modules_to_remove = []
for module_name in sys.modules:
    if 'clip_generator' in module_name:
        modules_to_remove.append(module_name)

for module_name in modules_to_remove:
    del sys.modules[module_name]

# 添加路径
sys.path.insert(0, 'src')

try:
    # 重新导入模块
    from core.clip_generator import ClipGenerator
    
    print("=== 强制重新加载后的ClipGenerator 类分析 ===")
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
    
    # 测试concatenate_segments方法
    if hasattr(cg, 'concatenate_segments'):
        print("\n=== 测试concatenate_segments方法 ===")
        test_segments = [
            {"source": "test1.mp4"},
            {"source": "test2.mp4"}
        ]
        test_output = "test_output.mp4"
        
        try:
            # 这会失败，因为文件不存在，但至少能验证方法可以调用
            result = cg.concatenate_segments(test_segments, test_output)
            print(f"方法调用成功，返回: {result}")
        except Exception as e:
            print(f"方法调用失败（预期的）: {e}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
