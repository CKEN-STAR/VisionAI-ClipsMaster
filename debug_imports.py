#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试导入问题
"""

import sys
import os

# 添加路径
sys.path.insert(0, 'src')

print("=== 逐步导入测试 ===")

try:
    print("1. 导入基础模块...")
    import tempfile
    import subprocess
    import shutil
    print("   基础模块导入成功")
    
    print("2. 导入项目模块...")
    
    try:
        from src.core.screenplay_engineer import import_srt
        print("   screenplay_engineer.import_srt: ✓")
    except Exception as e:
        print(f"   screenplay_engineer.import_srt: ✗ ({e})")
    
    try:
        from src.utils.log_handler import get_logger
        print("   log_handler.get_logger: ✓")
    except Exception as e:
        print(f"   log_handler.get_logger: ✗ ({e})")
    
    try:
        from src.utils.memory_guard import track_memory
        print("   memory_guard.track_memory: ✓")
    except Exception as e:
        print(f"   memory_guard.track_memory: ✗ ({e})")
    
    try:
        from src.quality.quality_controller import QualityController
        print("   quality_controller.QualityController: ✓")
    except Exception as e:
        print(f"   quality_controller.QualityController: ✗ ({e})")
    
    try:
        from src.core.exceptions import QualityCheckError
        print("   exceptions.QualityCheckError: ✓")
    except Exception as e:
        print(f"   exceptions.QualityCheckError: ✗ ({e})")
    
    print("3. 尝试导入ClipGenerator模块...")
    try:
        import core.clip_generator as cg_module
        print("   模块导入成功")
        
        print("4. 检查模块内容...")
        print(f"   模块属性: {[attr for attr in dir(cg_module) if not attr.startswith('_')]}")
        
        print("5. 尝试获取ClipGenerator类...")
        ClipGenerator = cg_module.ClipGenerator
        print(f"   类获取成功: {ClipGenerator}")
        
        print("6. 检查类的方法...")
        class_methods = [attr for attr in dir(ClipGenerator) if not attr.startswith('_')]
        print(f"   类方法: {class_methods}")
        
        print("7. 尝试创建实例...")
        try:
            instance = ClipGenerator()
            print("   实例创建成功")
            
            instance_methods = [attr for attr in dir(instance) if not attr.startswith('_')]
            print(f"   实例方法: {instance_methods}")
            
        except Exception as e:
            print(f"   实例创建失败: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"   模块导入失败: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"导入测试失败: {e}")
    import traceback
    traceback.print_exc()
