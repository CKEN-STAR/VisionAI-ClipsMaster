#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端AI引擎功能测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试1: 模块导入")
    print("=" * 60)
    
    try:
        from src.core.cloud_ai_engine import (
            CloudAIEngine, CloudPlatform, CloudModel,
            get_supported_platforms, get_supported_models, get_platform_models,
            PLATFORM_CONFIG
        )
        print("✅ cloud_ai_engine 导入成功")
        
        from src.config.cloud_api_config import CloudAPIConfig, get_cloud_api_config
        print("✅ cloud_api_config 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_platform_config():
    """测试平台配置"""
    print("\n" + "=" * 60)
    print("测试2: 平台配置")
    print("=" * 60)
    
    try:
        from src.core.cloud_ai_engine import (
            CloudPlatform, CloudModel, PLATFORM_CONFIG,
            get_supported_platforms, get_supported_models, get_platform_models
        )
        
        # 测试平台列表
        platforms = get_supported_platforms()
        print(f"\n支持的平台 ({len(platforms)}个):")
        for p in platforms:
            print(f"  - {p['name']} ({p['id']})")
        
        # 测试模型列表
        models = get_supported_models()
        print(f"\n支持的模型 ({len(models)}个):")
        for m in models:
            print(f"  - {m['name']} ({m['id']}): {m['description']}")
        
        # 测试平台配置
        print(f"\n平台配置详情:")
        for platform_id, config in PLATFORM_CONFIG.items():
            print(f"\n  [{config['name']}]")
            print(f"    API地址: {config['base_url']}")
            print(f"    支持的模型:")
            for model_id, model_name in config['models'].items():
                print(f"      - {model_id}: {model_name}")
        
        # 验证模型名称
        print(f"\n验证模型名称:")
        sf_qwen = PLATFORM_CONFIG[CloudPlatform.SILICONFLOW]['models'][CloudModel.QWEN3_235B]
        sf_ds = PLATFORM_CONFIG[CloudPlatform.SILICONFLOW]['models'][CloudModel.DEEPSEEK_V3]
        print(f"  硅基流动 Qwen3: {sf_qwen}")
        print(f"  硅基流动 DeepSeek: {sf_ds}")
        
        ds_qwen = PLATFORM_CONFIG[CloudPlatform.DASHSCOPE]['models'][CloudModel.QWEN3_235B]
        ds_ds = PLATFORM_CONFIG[CloudPlatform.DASHSCOPE]['models'][CloudModel.DEEPSEEK_V3]
        print(f"  阿里魔搭 Qwen3: {ds_qwen}")
        print(f"  阿里魔搭 DeepSeek替代: {ds_ds}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cloud_engine_init():
    """测试云端引擎初始化"""
    print("\n" + "=" * 60)
    print("测试3: 云端引擎初始化")
    print("=" * 60)
    
    try:
        from src.core.cloud_ai_engine import CloudAIEngine, CloudPlatform, CloudModel
        
        # 创建引擎实例
        engine = CloudAIEngine()
        print("✅ CloudAIEngine 实例创建成功")
        
        # 测试配置（不实际调用API）
        engine.configure(
            platform=CloudPlatform.SILICONFLOW,
            model=CloudModel.QWEN3_235B,
            api_key="test_api_key_placeholder"
        )
        print("✅ 引擎配置成功")
        print(f"   平台: {engine.platform}")
        print(f"   模型: {engine.model}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager():
    """测试配置管理器"""
    print("\n" + "=" * 60)
    print("测试4: 配置管理器")
    print("=" * 60)
    
    try:
        from src.config.cloud_api_config import CloudAPIConfig, get_cloud_api_config
        
        # 获取配置实例
        config = get_cloud_api_config()
        print("✅ CloudAPIConfig 实例获取成功")
        
        # 测试属性
        print(f"\n当前配置:")
        print(f"  模式: {config.mode}")
        print(f"  是否云端模式: {config.is_cloud_mode}")
        print(f"  平台: {config.platform}")
        print(f"  模型: {config.model}")
        print(f"  API Key: {'已配置' if config.api_key else '未配置'}")
        
        # 测试显示信息
        display_info = config.get_display_info()
        print(f"\n显示信息:")
        for key, value in display_info.items():
            print(f"  {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_imports():
    """测试UI文件中的云端AI导入"""
    print("\n" + "=" * 60)
    print("测试5: UI文件云端AI导入")
    print("=" * 60)
    
    try:
        # 模拟UI文件中的导入
        from src.core.cloud_ai_engine import (
            CloudAIEngine, CloudPlatform, CloudModel,
            get_supported_platforms, get_supported_models, get_platform_models,
            get_cloud_ai_engine, PLATFORM_CONFIG
        )
        from src.config.cloud_api_config import CloudAPIConfig, get_cloud_api_config
        
        print("✅ UI所需的所有云端AI模块导入成功")
        
        # 验证函数可调用
        platforms = get_supported_platforms()
        models = get_supported_models()
        engine = get_cloud_ai_engine()
        config = get_cloud_api_config()
        
        print(f"✅ 所有函数可正常调用")
        print(f"   平台数: {len(platforms)}")
        print(f"   模型数: {len(models)}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("VisionAI-ClipsMaster v1.2.0 云端AI引擎测试")
    print("=" * 60)
    
    results = []
    
    results.append(("模块导入", test_imports()))
    results.append(("平台配置", test_platform_config()))
    results.append(("引擎初始化", test_cloud_engine_init()))
    results.append(("配置管理器", test_config_manager()))
    results.append(("UI导入", test_ui_imports()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
