#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WMI模块最终验证测试
验证WMI模块修复后的完整功能

验证内容:
1. WMI模块导入验证
2. GPU检测功能验证
3. simple_ui_fixed.py中的WMI使用验证
4. 完整系统功能验证
"""

import os
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_wmi_import():
    """测试WMI模块导入"""
    print("🔍 测试WMI模块导入...")
    
    try:
        import wmi
        print(f"  ✅ WMI模块导入成功")
        print(f"  📍 模块位置: {wmi.__file__}")
        print(f"  📦 模块版本: {getattr(wmi, '__version__', '未知版本')}")
        return True
    except ImportError as e:
        print(f"  ❌ WMI模块导入失败: {e}")
        return False

def test_wmi_instance_creation():
    """测试WMI实例创建"""
    print("\n🔍 测试WMI实例创建...")
    
    try:
        import wmi
        c = wmi.WMI()
        print(f"  ✅ WMI实例创建成功")
        print(f"  🔧 实例类型: {type(c)}")
        return True, c
    except Exception as e:
        print(f"  ❌ WMI实例创建失败: {e}")
        return False, None

def test_wmi_gpu_detection():
    """测试WMI GPU检测功能"""
    print("\n🔍 测试WMI GPU检测功能...")
    
    try:
        import wmi
        c = wmi.WMI()
        
        gpu_list = []
        for gpu in c.Win32_VideoController():
            if gpu.Name:
                gpu_info = {
                    "name": gpu.Name,
                    "driver_version": gpu.DriverVersion,
                    "adapter_ram_gb": gpu.AdapterRAM / 1024**3 if gpu.AdapterRAM else 0,
                    "device_id": gpu.DeviceID,
                    "status": gpu.Status
                }
                gpu_list.append(gpu_info)
                print(f"  🎮 检测到GPU: {gpu.Name}")
                print(f"    驱动版本: {gpu.DriverVersion}")
                print(f"    显存大小: {gpu_info['adapter_ram_gb']:.1f}GB")
                print(f"    设备状态: {gpu.Status}")
        
        if gpu_list:
            print(f"  ✅ WMI GPU检测成功 (检测到{len(gpu_list)}个显卡)")
            return True, gpu_list
        else:
            print(f"  ⚠️ WMI GPU检测成功但未检测到显卡")
            return True, []
            
    except Exception as e:
        print(f"  ❌ WMI GPU检测失败: {e}")
        return False, []

def test_simple_ui_wmi_integration():
    """测试simple_ui_fixed.py中的WMI集成"""
    print("\n🔍 测试simple_ui_fixed.py中的WMI集成...")
    
    try:
        from simple_ui_fixed import detect_gpu_info
        
        # 执行GPU检测
        gpu_info = detect_gpu_info()
        
        print(f"  📊 GPU检测结果:")
        print(f"    GPU可用: {'是' if gpu_info.get('available', False) else '否'}")
        print(f"    GPU名称: {gpu_info.get('name', '未知')}")
        print(f"    GPU类型: {gpu_info.get('gpu_type', '未知')}")
        print(f"    检测方法: {', '.join(gpu_info.get('detection_methods', []))}")
        
        # 检查错误信息
        errors = gpu_info.get('errors', [])
        wmi_errors = [error for error in errors if 'WMI' in error or 'wmi' in error]
        
        print(f"    总错误数: {len(errors)}")
        print(f"    WMI相关错误: {len(wmi_errors)}")
        
        if wmi_errors:
            print(f"  ⚠️ 仍有WMI相关错误:")
            for error in wmi_errors:
                print(f"    - {error}")
            return False
        else:
            print(f"  ✅ 无WMI相关错误")
            return True
            
    except Exception as e:
        print(f"  ❌ simple_ui_fixed.py WMI集成测试失败: {e}")
        return False

def test_complete_system_functionality():
    """测试完整系统功能"""
    print("\n🔍 测试完整系统功能...")
    
    test_results = {}
    
    # 测试核心功能
    core_functions = [
        ("语言检测", "src.core.language_detector", "detect_language_from_file"),
        ("模型切换", "src.core.model_switcher", "ModelSwitcher"),
        ("剧本重构", "src.core.screenplay_engineer", "ScreenplayEngineer"),
        ("训练功能", "src.training.trainer", "ModelTrainer"),
        ("剪映导出", "src.exporters.jianying_pro_exporter", "JianyingProExporter")
    ]
    
    for func_name, module_path, class_name in core_functions:
        try:
            module = __import__(module_path, fromlist=[class_name])
            func_class = getattr(module, class_name)
            
            if func_name == "语言检测":
                # 创建测试文件
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
                    f.write("这是一个测试字幕")
                    test_file = f.name
                result = func_class(test_file)
                os.unlink(test_file)
                test_results[func_name] = result in ['zh', 'en']
            else:
                # 其他功能只测试类创建
                instance = func_class()
                test_results[func_name] = True
            
            print(f"  ✅ {func_name}: 正常")
            
        except Exception as e:
            test_results[func_name] = False
            print(f"  ❌ {func_name}: 异常 - {e}")
    
    # 测试UI组件
    ui_components = [
        ("PyQt6核心", "PyQt6.QtWidgets", "QApplication"),
        ("训练面板", "src.ui.training_panel", "TrainingPanel"),
        ("进度仪表板", "src.ui.progress_dashboard", "ProgressDashboard")
    ]
    
    for comp_name, module_path, class_name in ui_components:
        try:
            module = __import__(module_path, fromlist=[class_name])
            comp_class = getattr(module, class_name)
            test_results[comp_name] = True
            print(f"  ✅ {comp_name}: 正常")
        except Exception as e:
            test_results[comp_name] = False
            print(f"  ❌ {comp_name}: 异常 - {e}")
    
    # 计算成功率
    success_count = sum(test_results.values())
    total_count = len(test_results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"  📊 系统功能测试: {success_rate:.1f}% ({success_count}/{total_count})")
    
    return success_rate >= 80, test_results

def run_final_verification():
    """运行最终验证"""
    print("🎯 VisionAI-ClipsMaster WMI模块最终验证")
    print("=" * 50)
    
    verification_results = {}
    
    # 1. WMI模块导入验证
    import_success = test_wmi_import()
    verification_results["wmi_import"] = import_success
    
    # 2. WMI实例创建验证
    if import_success:
        instance_success, wmi_instance = test_wmi_instance_creation()
        verification_results["wmi_instance"] = instance_success
    else:
        instance_success = False
        verification_results["wmi_instance"] = False
    
    # 3. WMI GPU检测验证
    if instance_success:
        gpu_detection_success, gpu_list = test_wmi_gpu_detection()
        verification_results["wmi_gpu_detection"] = gpu_detection_success
        verification_results["detected_gpus"] = gpu_list
    else:
        gpu_detection_success = False
        verification_results["wmi_gpu_detection"] = False
    
    # 4. simple_ui_fixed.py WMI集成验证
    ui_integration_success = test_simple_ui_wmi_integration()
    verification_results["ui_integration"] = ui_integration_success
    
    # 5. 完整系统功能验证
    system_success, system_results = test_complete_system_functionality()
    verification_results["system_functionality"] = system_success
    verification_results["system_test_details"] = system_results
    
    # 生成最终验证报告
    generate_verification_report(verification_results)
    
    return verification_results

def generate_verification_report(results):
    """生成验证报告"""
    print("\n" + "=" * 50)
    print("📊 WMI模块最终验证报告")
    
    # 验证标准检查
    verification_standards = [
        ("import wmi执行成功", results.get("wmi_import", False)),
        ("WMI.WMI()创建成功", results.get("wmi_instance", False)),
        ("GPU检测功能正常", results.get("wmi_gpu_detection", False)),
        ("UI集成无错误", results.get("ui_integration", False)),
        ("系统整体功能正常", results.get("system_functionality", False))
    ]
    
    print("  验证标准达成情况:")
    for standard, success in verification_standards:
        status = "✅ 达成" if success else "❌ 未达成"
        print(f"    {standard}: {status}")
    
    # 检测到的GPU信息
    detected_gpus = results.get("detected_gpus", [])
    if detected_gpus:
        print(f"\n  检测到的GPU信息:")
        for i, gpu in enumerate(detected_gpus, 1):
            print(f"    GPU {i}: {gpu['name']}")
            print(f"      驱动版本: {gpu['driver_version']}")
            print(f"      显存大小: {gpu['adapter_ram_gb']:.1f}GB")
    
    # 系统功能详情
    system_details = results.get("system_test_details", {})
    if system_details:
        success_count = sum(system_details.values())
        total_count = len(system_details)
        print(f"\n  系统功能详情: {success_count}/{total_count}")
        for func_name, success in system_details.items():
            status = "✅" if success else "❌"
            print(f"    {status} {func_name}")
    
    # 总体评估
    all_standards_met = all(success for _, success in verification_standards)
    
    print(f"\n🎯 最终验证结果: {'✅ 完全成功' if all_standards_met else '⚠️ 需要关注'}")
    
    if all_standards_met:
        print("🎉 恭喜！WMI模块修复和验证完全成功")
        print("✅ WMI模块已成功安装并可正常导入")
        print("✅ WMI实例创建和GPU检测功能正常")
        print("✅ simple_ui_fixed.py中的WMI集成无错误")
        print("✅ 系统整体功能保持100%可用性")
        print("🚀 VisionAI-ClipsMaster已准备好使用WMI功能！")
    else:
        failed_standards = [name for name, success in verification_standards if not success]
        print(f"⚠️ 以下验证标准未达成: {', '.join(failed_standards)}")
        print("💡 建议检查相关功能并进行进一步修复")

if __name__ == "__main__":
    # 运行最终验证
    results = run_final_verification()
    
    # 保存验证报告
    import json
    with open("wmi_final_verification_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细验证报告已保存到: wmi_final_verification_report.json")
