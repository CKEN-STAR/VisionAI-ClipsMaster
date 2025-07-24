#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试track_memory装饰器
"""

import sys
sys.path.insert(0, 'src')

try:
    from src.utils.memory_guard import track_memory
    print("track_memory装饰器导入成功")
    
    @track_memory('test')
    def test_func():
        return 'ok'
    
    print("装饰器应用成功")
    result = test_func()
    print(f"函数调用结果: {result}")
    
except Exception as e:
    print(f"装饰器测试失败: {e}")
    import traceback
    traceback.print_exc()
