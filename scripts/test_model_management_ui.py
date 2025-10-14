#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模型管理UI功能
"""

import sys
import os

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def test_model_management():
    """测试模型管理功能"""
    print("=" * 70)
    print("测试模型管理功能")
    print("=" * 70)
    
    # 测试版本管理器
    print("\n1. 测试版本管理器...")
    try:
        from src.training.model_version_manager import ModelVersionManager
        
        # 中文模型
        zh_manager = ModelVersionManager(base_dir="models/qwen")
        zh_versions = zh_manager.list_versions()
        print(f"   中文模型版本数: {len(zh_versions)}")
        
        # 英文模型
        en_manager = ModelVersionManager(base_dir="models/mistral")
        en_versions = en_manager.list_versions()
        print(f"   英文模型版本数: {len(en_versions)}")
        
        print("   ✅ 版本管理器测试通过")
    except Exception as e:
        print(f"   ❌ 版本管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试模型加载器
    print("\n2. 测试模型加载器...")
    try:
        from src.inference.model_loader import InferenceModelLoader
        from src.inference.en_model_loader import EnModelLoader
        
        # 中文模型加载器
        zh_loader = InferenceModelLoader("qwen2.5-7b-zh")
        zh_info = zh_loader.get_model_info()
        print(f"   中文模型信息:")
        print(f"      GGUF: {zh_info['gguf']['path']}")
        print(f"      HF: {zh_info['huggingface']['path']}")
        print(f"      总版本数: {zh_info['total_versions']}")
        
        # 英文模型加载器
        en_loader = EnModelLoader("mistral-7b-en")
        en_info = en_loader.get_model_info()
        print(f"   英文模型信息:")
        print(f"      GGUF: {en_info['gguf']['path']}")
        print(f"      HF: {en_info['huggingface']['path']}")
        print(f"      总版本数: {en_info['total_versions']}")
        
        print("   ✅ 模型加载器测试通过")
    except Exception as e:
        print(f"   ❌ 模型加载器测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试性能评估器
    print("\n3. 测试性能评估器...")
    try:
        from src.training.performance_evaluator import PerformanceEvaluator
        
        evaluator = PerformanceEvaluator()
        print("   ✅ 性能评估器初始化成功")
    except Exception as e:
        print(f"   ❌ 性能评估器测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)

if __name__ == "__main__":
    test_model_management()

