#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全面验证UI集成功能的脚本
检查所有外部类的方法调用是否正确
"""

import sys
import inspect
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_class_methods(class_obj, expected_methods):
    """验证类是否有预期的方法"""
    results = {}
    for method_name in expected_methods:
        has_method = hasattr(class_obj, method_name)
        results[method_name] = has_method
        if has_method:
            # 获取方法签名
            try:
                method = getattr(class_obj, method_name)
                sig = inspect.signature(method)
                results[f"{method_name}_signature"] = str(sig)
            except:
                results[f"{method_name}_signature"] = "无法获取签名"
    return results

def main():
    print("=" * 80)
    print("UI集成功能全面验证")
    print("=" * 80)
    
    all_passed = True
    
    # 1. 验证 ModelVersionManager
    print("\n[1/5] 验证 ModelVersionManager...")
    try:
        from src.training.model_version_manager import ModelVersionManager
        
        expected_methods = [
            'list_versions',  # ✅ 正确
            'get_active_version',  # ✅ 正确
            'set_active_version',  # ✅ 正确
            'cleanup_version',  # ✅ 正确
            'cleanup_all_except_active',  # ✅ 正确
            'get_storage_usage',  # ✅ 正确
            'register_new_version',
            'get_version_info',
            'update_version_performance'
        ]
        
        results = verify_class_methods(ModelVersionManager, expected_methods)
        
        print("  方法验证结果:")
        for method, exists in results.items():
            if not method.endswith('_signature'):
                status = "✅" if exists else "❌"
                print(f"    {status} {method}: {'存在' if exists else '不存在'}")
                if exists and f"{method}_signature" in results:
                    print(f"       签名: {results[f'{method}_signature']}")
        
        # 检查 get_storage_usage 返回值
        print("\n  验证 get_storage_usage() 返回值结构:")
        manager = ModelVersionManager(base_dir="models/qwen")
        storage = manager.get_storage_usage()
        print(f"    返回键: {list(storage.keys())}")
        print(f"    ✅ 'total_gb' 键存在: {'total_gb' in storage}")
        print(f"    ✅ 'versions' 键存在: {'versions' in storage}")
        
        if not all(results.values()):
            all_passed = False
            print("  ❌ ModelVersionManager 验证失败")
        else:
            print("  ✅ ModelVersionManager 验证通过")
            
    except Exception as e:
        print(f"  ❌ ModelVersionManager 验证失败: {e}")
        all_passed = False
    
    # 2. 验证 ModelFineTuner
    print("\n[2/5] 验证 ModelFineTuner...")
    try:
        from src.training.model_fine_tuner import ModelFineTuner
        
        expected_methods = [
            'set_callbacks',  # ✅ 正确
            'fine_tune_model',  # ✅ 正确
            'get_training_status',
            'get_training_history',
            'validate_training_data',
            'cleanup'
        ]
        
        results = verify_class_methods(ModelFineTuner, expected_methods)
        
        print("  方法验证结果:")
        for method, exists in results.items():
            if not method.endswith('_signature'):
                status = "✅" if exists else "❌"
                print(f"    {status} {method}: {'存在' if exists else '不存在'}")
                if exists and f"{method}_signature" in results:
                    print(f"       签名: {results[f'{method}_signature']}")
        
        if not all(results.values()):
            all_passed = False
            print("  ❌ ModelFineTuner 验证失败")
        else:
            print("  ✅ ModelFineTuner 验证通过")
            
    except Exception as e:
        print(f"  ❌ ModelFineTuner 验证失败: {e}")
        all_passed = False
    
    # 3. 验证 EnhancedModelDownloader
    print("\n[3/5] 验证 EnhancedModelDownloader...")
    try:
        from src.core.enhanced_model_downloader import EnhancedModelDownloader
        
        expected_methods = [
            'download_model',  # ✅ 正确
            'download_specific_variant',  # ✅ 正确
            'reset_state',  # ✅ 正确
            'get_download_status',
            'get_storage_info',
            'check_and_cleanup_incomplete_downloads',
            'get_available_models'
        ]
        
        results = verify_class_methods(EnhancedModelDownloader, expected_methods)
        
        print("  方法验证结果:")
        for method, exists in results.items():
            if not method.endswith('_signature'):
                status = "✅" if exists else "❌"
                print(f"    {status} {method}: {'存在' if exists else '不存在'}")
                if exists and f"{method}_signature" in results:
                    print(f"       签名: {results[f'{method}_signature']}")
        
        if not all(results.values()):
            all_passed = False
            print("  ❌ EnhancedModelDownloader 验证失败")
        else:
            print("  ✅ EnhancedModelDownloader 验证通过")
            
    except Exception as e:
        print(f"  ❌ EnhancedModelDownloader 验证失败: {e}")
        all_passed = False
    
    # 4. 验证 SmartDownloaderIntegrationManager
    print("\n[4/5] 验证 SmartDownloaderIntegrationManager...")
    try:
        from src.ui.smart_downloader_integration_enhanced import SmartDownloaderIntegrationManager
        
        expected_methods = [
            'initialize',
            'show_smart_downloader',
            'get_integration_status',
            'register_download_callback',
            'register_hardware_change_callback'
        ]
        
        results = verify_class_methods(SmartDownloaderIntegrationManager, expected_methods)
        
        print("  方法验证结果:")
        for method, exists in results.items():
            if not method.endswith('_signature'):
                status = "✅" if exists else "❌"
                print(f"    {status} {method}: {'存在' if exists else '不存在'}")
                if exists and f"{method}_signature" in results:
                    print(f"       签名: {results[f'{method}_signature']}")
        
        if not all(results.values()):
            all_passed = False
            print("  ❌ SmartDownloaderIntegrationManager 验证失败")
        else:
            print("  ✅ SmartDownloaderIntegrationManager 验证通过")
            
    except Exception as e:
        print(f"  ❌ SmartDownloaderIntegrationManager 验证失败: {e}")
        all_passed = False
    
    # 5. 验证 DynamicDownloaderIntegration
    print("\n[5/5] 验证 DynamicDownloaderIntegration...")
    try:
        from src.ui.dynamic_downloader_integration import DynamicDownloaderIntegration
        
        expected_methods = [
            'show_smart_downloader',
            'register_download_callback',
            'register_hardware_change_callback'
        ]
        
        results = verify_class_methods(DynamicDownloaderIntegration, expected_methods)
        
        print("  方法验证结果:")
        for method, exists in results.items():
            if not method.endswith('_signature'):
                status = "✅" if exists else "❌"
                print(f"    {status} {method}: {'存在' if exists else '不存在'}")
                if exists and f"{method}_signature" in results:
                    print(f"       签名: {results[f'{method}_signature']}")
        
        if not all(results.values()):
            all_passed = False
            print("  ❌ DynamicDownloaderIntegration 验证失败")
        else:
            print("  ✅ DynamicDownloaderIntegration 验证通过")
            
    except Exception as e:
        print(f"  ❌ DynamicDownloaderIntegration 验证失败: {e}")
        all_passed = False
    
    # 总结
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有UI集成功能验证通过！")
        return 0
    else:
        print("❌ 部分UI集成功能验证失败，请检查上述错误")
        return 1

if __name__ == "__main__":
    sys.exit(main())

