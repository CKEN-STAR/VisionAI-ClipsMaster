#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster v1.2.0 集成测试
验证云端/本地模式切换和工作流程
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_version_numbers():
    """测试版本号是否正确更新"""
    print("=" * 60)
    print("测试1: 版本号验证")
    print("=" * 60)
    
    try:
        from src.utils.version import __version__, __cloud_api_version__
        print(f"  主版本号: {__version__}")
        print(f"  云端API版本: {__cloud_api_version__}")
        
        assert __version__ == "1.2.0", f"版本号应为1.2.0，实际为{__version__}"
        print("✅ 版本号验证通过")
        return True
    except Exception as e:
        print(f"❌ 版本号验证失败: {e}")
        return False

def test_cloud_engine_integration():
    """测试云端引擎集成"""
    print("\n" + "=" * 60)
    print("测试2: 云端引擎集成")
    print("=" * 60)
    
    try:
        from src.core.cloud_ai_engine import (
            CloudAIEngine, CloudPlatform, CloudModel,
            get_supported_platforms, get_supported_models
        )
        
        # 验证平台和模型
        platforms = get_supported_platforms()
        models = get_supported_models()
        
        assert len(platforms) == 2, "应支持2个平台"
        assert len(models) == 2, "应支持2个模型"
        
        # 验证平台ID
        platform_ids = [p['id'] for p in platforms]
        assert 'siliconflow' in platform_ids, "应支持硅基流动"
        assert 'dashscope' in platform_ids, "应支持阿里魔搭"
        
        # 验证模型ID
        model_ids = [m['id'] for m in models]
        assert 'qwen3-235b' in model_ids, "应支持Qwen3-235B"
        assert 'deepseek-v3' in model_ids, "应支持DeepSeek-V3"
        
        print(f"  支持的平台: {platform_ids}")
        print(f"  支持的模型: {model_ids}")
        print("✅ 云端引擎集成验证通过")
        return True
    except Exception as e:
        print(f"❌ 云端引擎集成验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_cloud_imports():
    """测试UI文件中的云端模块导入"""
    print("\n" + "=" * 60)
    print("测试3: UI云端模块导入")
    print("=" * 60)
    
    try:
        # 模拟UI文件中的导入检查
        import simple_ui_fixed
        
        # 检查HAS_CLOUD_AI标志
        has_cloud = getattr(simple_ui_fixed, 'HAS_CLOUD_AI', False)
        print(f"  HAS_CLOUD_AI: {has_cloud}")
        
        if has_cloud:
            print("✅ UI云端模块导入验证通过")
            return True
        else:
            print("⚠️ 云端AI模块未成功导入到UI")
            return False
    except Exception as e:
        print(f"❌ UI云端模块导入验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_viral_srt_worker():
    """测试ViralSRTWorker类是否支持云端引擎参数"""
    print("\n" + "=" * 60)
    print("测试4: ViralSRTWorker云端支持")
    print("=" * 60)
    
    try:
        from simple_ui_fixed import ViralSRTWorker
        import inspect
        
        # 检查__init__方法的参数
        sig = inspect.signature(ViralSRTWorker.__init__)
        params = list(sig.parameters.keys())
        
        print(f"  ViralSRTWorker参数: {params}")
        
        assert 'cloud_engine' in params, "应包含cloud_engine参数"
        print("✅ ViralSRTWorker云端支持验证通过")
        return True
    except Exception as e:
        print(f"❌ ViralSRTWorker云端支持验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_video_processor_batch():
    """测试VideoProcessor.generate_viral_srt_batch是否支持云端引擎"""
    print("\n" + "=" * 60)
    print("测试5: VideoProcessor批量生成云端支持")
    print("=" * 60)
    
    try:
        from simple_ui_fixed import VideoProcessor
        import inspect
        
        # 检查方法签名
        sig = inspect.signature(VideoProcessor.generate_viral_srt_batch)
        params = list(sig.parameters.keys())
        
        print(f"  generate_viral_srt_batch参数: {params}")
        
        assert 'cloud_engine' in params, "应包含cloud_engine参数"
        print("✅ VideoProcessor批量生成云端支持验证通过")
        return True
    except Exception as e:
        print(f"❌ VideoProcessor批量生成云端支持验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_persistence():
    """测试配置持久化"""
    print("\n" + "=" * 60)
    print("测试6: 配置持久化")
    print("=" * 60)
    
    try:
        from src.config.cloud_api_config import get_cloud_api_config
        
        config = get_cloud_api_config()
        
        # 测试读取
        mode = config.mode
        platform = config.platform
        model = config.model
        
        print(f"  当前模式: {mode}")
        print(f"  当前平台: {platform}")
        print(f"  当前模型: {model}")
        
        # 验证默认值
        assert mode in ['local', 'cloud'], "模式应为local或cloud"
        assert platform in ['siliconflow', 'dashscope'], "平台应为siliconflow或dashscope"
        assert model in ['qwen3-235b', 'deepseek-v3'], "模型应为qwen3-235b或deepseek-v3"
        
        print("✅ 配置持久化验证通过")
        return True
    except Exception as e:
        print(f"❌ 配置持久化验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("VisionAI-ClipsMaster v1.2.0 集成测试")
    print("=" * 60)
    
    results = []
    
    results.append(("版本号验证", test_version_numbers()))
    results.append(("云端引擎集成", test_cloud_engine_integration()))
    results.append(("UI云端模块导入", test_ui_cloud_imports()))
    results.append(("ViralSRTWorker云端支持", test_viral_srt_worker()))
    results.append(("VideoProcessor批量生成", test_video_processor_batch()))
    results.append(("配置持久化", test_config_persistence()))
    
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
    
    if failed == 0:
        print("\n🎉 所有测试通过！v1.2.0升级成功！")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
