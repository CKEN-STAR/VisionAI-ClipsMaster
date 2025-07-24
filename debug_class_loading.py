#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试类加载过程
"""

import sys
import os

# 添加路径
sys.path.insert(0, 'src')

print("=== 调试类加载过程 ===")

try:
    print("1. 导入模块...")
    
    # 逐步导入依赖
    print("   导入基础模块...")
    import tempfile
    import shutil
    import subprocess
    from typing import Dict, List, Any, Optional, Tuple
    from datetime import datetime
    import glob
    from pathlib import Path
    
    print("   导入项目模块...")
    from src.core.screenplay_engineer import import_srt
    from src.utils.log_handler import get_logger
    
    print("   导入ClipGenerator模块...")
    import core.clip_generator as cg_module
    
    print("2. 检查模块内容...")
    print(f"   模块属性: {[attr for attr in dir(cg_module) if not attr.startswith('_')]}")
    
    print("3. 获取ClipGenerator类...")
    ClipGenerator = cg_module.ClipGenerator
    print(f"   类: {ClipGenerator}")
    
    print("4. 检查类的方法...")
    class_methods = [name for name in ClipGenerator.__dict__ if not name.startswith('_')]
    print(f"   类字典中的方法: {class_methods}")
    
    print("5. 尝试创建实例...")
    
    # 创建实例但不调用__init__
    print("   创建未初始化实例...")
    instance = object.__new__(ClipGenerator)
    print("   未初始化实例创建成功")
    
    # 检查未初始化实例的方法
    uninit_methods = [name for name in dir(instance) if not name.startswith('_')]
    print(f"   未初始化实例的方法: {uninit_methods}")
    
    print("   调用__init__方法...")
    try:
        # 手动执行__init__方法的内容来调试
        print("     设置temp_dir...")
        instance.temp_dir = os.path.join(tempfile.gettempdir(), "visionai_clips")
        print(f"     temp_dir设置为: {instance.temp_dir}")

        print("     创建temp_dir...")
        os.makedirs(instance.temp_dir, exist_ok=True)
        print("     temp_dir创建成功")

        print("     设置processing_history...")
        instance.processing_history = []
        print("     processing_history设置成功")

        print("     调用_check_ffmpeg...")
        instance._check_ffmpeg()
        print("     _check_ffmpeg调用成功")

        print("   手动初始化完成")
        
        # 检查初始化后的方法和属性
        init_methods = [name for name in dir(instance) if not name.startswith('_')]
        print(f"   初始化后实例的方法: {init_methods}")
        
        # 检查特定属性
        attrs_to_check = ['temp_dir', 'processing_history', 'ffmpeg_path']
        for attr in attrs_to_check:
            has_attr = hasattr(instance, attr)
            if has_attr:
                value = getattr(instance, attr)
                print(f"   {attr}: {value}")
            else:
                print(f"   {attr}: 不存在")
        
    except Exception as e:
        print(f"   __init__调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("6. 测试方法调用...")
    
    # 测试generate_clips方法
    if hasattr(instance, 'generate_clips'):
        print("   generate_clips方法存在")
        try:
            # 不实际调用，只检查方法对象
            method = getattr(instance, 'generate_clips')
            print(f"   方法对象: {method}")
            print(f"   方法类型: {type(method)}")
        except Exception as e:
            print(f"   获取generate_clips方法失败: {e}")
    else:
        print("   generate_clips方法不存在")
    
    print("\n测试完成")
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()
