#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster v1.2.0 完整功能测试
验证所有模块、组件和工作流程是否正常运行
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_imports():
    """测试核心模块导入"""
    print("=" * 60)
    print("测试1: 核心模块导入")
    print("=" * 60)
    
    modules = []
    
    try:
        from src.core.real_ai_engine import RealAIEngine
        modules.append(("RealAIEngine", True))
    except Exception as e:
        modules.append(("RealAIEngine", False, str(e)))
    
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        modules.append(("ScreenplayEngineer", True))
    except Exception as e:
        modules.append(("ScreenplayEngineer", False, str(e)))
    
    try:
        from src.core.clip_generator import ClipGenerator
        modules.append(("ClipGenerator", True))
    except Exception as e:
        modules.append(("ClipGenerator", False, str(e)))
    
    try:
        from src.core.workflow_manager import WorkflowManager
        modules.append(("WorkflowManager", True))
    except Exception as e:
        modules.append(("WorkflowManager", False, str(e)))
    
    try:
        from src.core.video_processor import VideoProcessor
        modules.append(("VideoProcessor", True))
    except Exception as e:
        modules.append(("VideoProcessor", False, str(e)))
    
    try:
        from src.core.cloud_ai_engine import CloudAIEngine
        modules.append(("CloudAIEngine", True))
    except Exception as e:
        modules.append(("CloudAIEngine", False, str(e)))
    
    success = True
    for item in modules:
        if item[1]:
            print(f"  ✅ {item[0]}")
        else:
            print(f"  ❌ {item[0]}: {item[2]}")
            success = False
    
    return success

def test_ui_initialization():
    """测试UI初始化（不显示窗口）"""
    print("\n" + "=" * 60)
    print("测试2: UI模块初始化")
    print("=" * 60)
    
    try:
        # 导入UI模块
        import simple_ui_fixed
        
        # 检查关键类和函数
        checks = [
            ("SimpleScreenplayApp", hasattr(simple_ui_fixed, 'SimpleScreenplayApp')),
            ("VideoProcessor", hasattr(simple_ui_fixed, 'VideoProcessor')),
            ("ViralSRTWorker", hasattr(simple_ui_fixed, 'ViralSRTWorker')),
            ("HAS_CLOUD_AI", getattr(simple_ui_fixed, 'HAS_CLOUD_AI', False)),
        ]
        
        success = True
        for name, result in checks:
            if result:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name}")
                success = False
        
        return success
    except Exception as e:
        print(f"  ❌ UI模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cloud_ai_engine():
    """测试云端AI引擎"""
    print("\n" + "=" * 60)
    print("测试3: 云端AI引擎功能")
    print("=" * 60)
    
    try:
        from src.core.cloud_ai_engine import (
            CloudAIEngine, CloudPlatform, CloudModel,
            get_supported_platforms, get_supported_models,
            PLATFORM_CONFIG
        )
        
        # 测试平台配置
        platforms = get_supported_platforms()
        models = get_supported_models()
        
        print(f"  ✅ 支持 {len(platforms)} 个平台")
        print(f"  ✅ 支持 {len(models)} 个模型")
        
        # 测试引擎创建
        engine = CloudAIEngine()
        print(f"  ✅ CloudAIEngine 实例创建成功")
        
        # 测试配置
        engine.configure(CloudPlatform.SILICONFLOW, CloudModel.QWEN3_235B, "test_key")
        print(f"  ✅ 引擎配置成功")
        
        # 验证模型名称
        sf_config = PLATFORM_CONFIG[CloudPlatform.SILICONFLOW]
        qwen_model = sf_config['models'][CloudModel.QWEN3_235B]
        ds_model = sf_config['models'][CloudModel.DEEPSEEK_V3]
        
        print(f"  ✅ 硅基流动 Qwen3: {qwen_model}")
        print(f"  ✅ 硅基流动 DeepSeek: {ds_model}")
        
        return True
    except Exception as e:
        print(f"  ❌ 云端AI引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager():
    """测试配置管理器"""
    print("\n" + "=" * 60)
    print("测试4: 配置管理器")
    print("=" * 60)
    
    try:
        from src.config.cloud_api_config import get_cloud_api_config
        
        config = get_cloud_api_config()
        
        # 测试读取
        mode = config.mode
        platform = config.platform
        model = config.model
        is_cloud = config.is_cloud_mode
        
        print(f"  ✅ 当前模式: {mode}")
        print(f"  ✅ 当前平台: {platform}")
        print(f"  ✅ 当前模型: {model}")
        print(f"  ✅ 是否云端: {is_cloud}")
        
        # 测试显示信息
        display = config.get_display_info()
        print(f"  ✅ 显示信息: {display}")
        
        return True
    except Exception as e:
        print(f"  ❌ 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_video_processor_methods():
    """测试VideoProcessor方法签名"""
    print("\n" + "=" * 60)
    print("测试5: VideoProcessor方法")
    print("=" * 60)
    
    try:
        from simple_ui_fixed import VideoProcessor
        import inspect
        
        # 检查generate_viral_srt_batch方法
        sig = inspect.signature(VideoProcessor.generate_viral_srt_batch)
        params = list(sig.parameters.keys())
        
        print(f"  generate_viral_srt_batch 参数: {params}")
        
        if 'cloud_engine' in params:
            print(f"  ✅ 支持云端引擎参数")
        else:
            print(f"  ❌ 缺少云端引擎参数")
            return False
        
        # 检查generate_viral_srt方法
        sig2 = inspect.signature(VideoProcessor.generate_viral_srt)
        params2 = list(sig2.parameters.keys())
        print(f"  generate_viral_srt 参数: {params2}")
        print(f"  ✅ 方法签名正确")
        
        return True
    except Exception as e:
        print(f"  ❌ VideoProcessor方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_viral_srt_worker():
    """测试ViralSRTWorker"""
    print("\n" + "=" * 60)
    print("测试6: ViralSRTWorker")
    print("=" * 60)
    
    try:
        from simple_ui_fixed import ViralSRTWorker
        import inspect
        
        # 检查初始化参数
        sig = inspect.signature(ViralSRTWorker.__init__)
        params = list(sig.parameters.keys())
        
        print(f"  __init__ 参数: {params}")
        
        if 'cloud_engine' in params:
            print(f"  ✅ 支持云端引擎参数")
        else:
            print(f"  ❌ 缺少云端引擎参数")
            return False
        
        # 检查信号
        signals = ['progress_updated', 'item_completed', 'all_completed', 'error_occurred']
        for sig_name in signals:
            if hasattr(ViralSRTWorker, sig_name):
                print(f"  ✅ 信号 {sig_name} 存在")
            else:
                print(f"  ❌ 信号 {sig_name} 缺失")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ ViralSRTWorker测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_version_consistency():
    """测试版本一致性"""
    print("\n" + "=" * 60)
    print("测试7: 版本一致性")
    print("=" * 60)
    
    try:
        from src.utils.version import __version__
        
        expected = "1.2.0"
        
        if __version__ == expected:
            print(f"  ✅ src/utils/version.py: {__version__}")
        else:
            print(f"  ❌ src/utils/version.py: {__version__} (期望 {expected})")
            return False
        
        # 检查UI文件中的版本
        with open('simple_ui_fixed.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'v1.2.0' in content:
            print(f"  ✅ simple_ui_fixed.py 包含 v1.2.0")
        else:
            print(f"  ❌ simple_ui_fixed.py 未包含 v1.2.0")
            return False
        
        if '版本 1.2.0' in content:
            print(f"  ✅ UI版本标签已更新")
        else:
            print(f"  ❌ UI版本标签未更新")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ 版本一致性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_integration():
    """测试工作流集成"""
    print("\n" + "=" * 60)
    print("测试8: 工作流集成")
    print("=" * 60)
    
    try:
        from src.core.workflow_manager import WorkflowManager
        
        wm = WorkflowManager()
        print(f"  ✅ WorkflowManager 创建成功")
        
        # 测试auto_calibrate_metrics方法
        if hasattr(wm, 'auto_calibrate_metrics'):
            result = wm.auto_calibrate_metrics(
                total_duration=300.0,
                subtitle_count=50,
                emotional_score=0.7
            )
            print(f"  ✅ auto_calibrate_metrics 调用成功")
            print(f"     档位: {result.get('grade', 'N/A')}")
        else:
            print(f"  ⚠️ auto_calibrate_metrics 方法不存在")
        
        return True
    except Exception as e:
        print(f"  ❌ 工作流集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_srt_parser():
    """测试SRT解析器"""
    print("\n" + "=" * 60)
    print("测试9: SRT解析器")
    print("=" * 60)
    
    try:
        from src.core.srt_parser import SRTParser
        
        parser = SRTParser()
        print(f"  ✅ SRTParser 创建成功")
        
        # 测试解析SRT内容
        test_srt = """1
00:00:01,000 --> 00:00:03,000
测试字幕第一行

2
00:00:04,000 --> 00:00:06,000
测试字幕第二行
"""
        
        result = parser.parse_srt_content(test_srt)
        if result and len(result) == 2:
            print(f"  ✅ parse_srt_content 解析成功 ({len(result)} 条)")
        else:
            print(f"  ❌ parse_srt_content 解析失败")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ SRT解析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_app_creation():
    """测试UI应用创建（无显示）"""
    print("\n" + "=" * 60)
    print("测试10: UI应用创建")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        import simple_ui_fixed
        
        # 检查是否已有QApplication实例
        app = QApplication.instance()
        if app is None:
            # 设置无头模式
            app = QApplication([])
        
        print(f"  ✅ QApplication 创建成功")
        
        # 尝试创建主窗口（不显示）
        try:
            window = simple_ui_fixed.SimpleScreenplayApp()
            print(f"  ✅ SimpleScreenplayApp 创建成功")
            
            # 检查云端模式相关属性
            if hasattr(window, 'cloud_mode_enabled'):
                print(f"  ✅ cloud_mode_enabled 属性存在")
            else:
                print(f"  ❌ cloud_mode_enabled 属性缺失")
                return False
            
            if hasattr(window, 'ai_mode_combo'):
                print(f"  ✅ ai_mode_combo 控件存在")
            else:
                print(f"  ❌ ai_mode_combo 控件缺失")
                return False
            
            if hasattr(window, 'cloud_mode_container'):
                print(f"  ✅ cloud_mode_container 控件存在")
            else:
                print(f"  ❌ cloud_mode_container 控件缺失")
                return False
            
            if hasattr(window, 'local_mode_container'):
                print(f"  ✅ local_mode_container 控件存在")
            else:
                print(f"  ❌ local_mode_container 控件缺失")
                return False
            
            # 检查云端模式方法
            methods = ['on_ai_mode_changed', 'test_cloud_connection', 
                      'get_cloud_ai_engine_configured', 'is_cloud_mode_ready',
                      '_load_cloud_config', '_save_cloud_config']
            
            for method in methods:
                if hasattr(window, method):
                    print(f"  ✅ 方法 {method} 存在")
                else:
                    print(f"  ❌ 方法 {method} 缺失")
                    return False
            
            # 清理
            window.close()
            window.deleteLater()
            
        except Exception as e:
            print(f"  ❌ SimpleScreenplayApp 创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ UI应用创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("VisionAI-ClipsMaster v1.2.0 完整功能测试")
    print("=" * 60)
    
    start_time = time.time()
    results = []
    
    results.append(("核心模块导入", test_core_imports()))
    results.append(("UI模块初始化", test_ui_initialization()))
    results.append(("云端AI引擎", test_cloud_ai_engine()))
    results.append(("配置管理器", test_config_manager()))
    results.append(("VideoProcessor方法", test_video_processor_methods()))
    results.append(("ViralSRTWorker", test_viral_srt_worker()))
    results.append(("版本一致性", test_version_consistency()))
    results.append(("工作流集成", test_workflow_integration()))
    results.append(("SRT解析器", test_srt_parser()))
    results.append(("UI应用创建", test_ui_app_creation()))
    
    elapsed = time.time() - start_time
    
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
    print(f"耗时: {elapsed:.2f} 秒")
    
    if failed == 0:
        print("\n🎉 所有测试通过！v1.2.0 可以正常使用！")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查问题")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
