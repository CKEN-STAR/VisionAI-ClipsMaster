#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试最小化的ClipGenerator类
"""

import os
import sys
import tempfile
import subprocess
import shutil
from typing import List, Dict, Any

# 添加路径
sys.path.insert(0, 'src')

# 导入必要的模块
from src.utils.memory_guard import track_memory

class MinimalClipGenerator:
    """最小化的ClipGenerator类"""
    
    def __init__(self):
        """初始化"""
        self.temp_dir = tempfile.mkdtemp(prefix="minimal_clip_")
        print("MinimalClipGenerator初始化完成")
    
    @track_memory("test_operation")
    def test_method_with_decorator(self):
        """带装饰器的测试方法"""
        return "test_method_with_decorator works"
    
    def extract_segments(self, video_path: str, segments: List[Dict[str, Any]]) -> List[str]:
        """从视频中提取指定片段"""
        return ["segment1.mp4", "segment2.mp4"]
    
    def concatenate_segments(self, segments: List[Dict[str, Any]], output_path: str) -> bool:
        """拼接视频片段"""
        return True
    
    def another_method(self):
        """另一个方法"""
        return "another_method works"

if __name__ == "__main__":
    print("=== 测试最小化ClipGenerator ===")
    
    try:
        # 创建实例
        cg = MinimalClipGenerator()
        
        # 检查方法
        methods = [m for m in dir(cg) if not m.startswith('_')]
        print(f"可用方法: {methods}")
        
        # 测试每个方法
        print(f"test_method_with_decorator: {hasattr(cg, 'test_method_with_decorator')}")
        print(f"extract_segments: {hasattr(cg, 'extract_segments')}")
        print(f"concatenate_segments: {hasattr(cg, 'concatenate_segments')}")
        print(f"another_method: {hasattr(cg, 'another_method')}")
        
        # 测试方法调用
        if hasattr(cg, 'test_method_with_decorator'):
            result = cg.test_method_with_decorator()
            print(f"test_method_with_decorator结果: {result}")
        
        if hasattr(cg, 'extract_segments'):
            result = cg.extract_segments("test.mp4", [])
            print(f"extract_segments结果: {result}")
        
        print("测试成功！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
