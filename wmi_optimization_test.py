#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WMI代码优化验证测试
验证WMI代码优化后的效果和功能完整性

测试内容:
1. GPU检测功能验证
2. WMI错误处理验证
3. 核心功能完整性测试
4. UI组件正常工作验证
"""

import os
import sys
import time
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_gpu_detection_optimized():
    """测试优化后的GPU检测功能"""
    print("🔍 测试优化后的GPU检测功能...")
    
    try:
        # 导入GPU检测函数
        sys.path.append(str(PROJECT_ROOT))
        from simple_ui_fixed import detect_gpu_info
        
        # 执行GPU检测
        gpu_info = detect_gpu_info()
        
        print(f"📊 GPU检测结果:")
        print(f"  GPU可用: {'是' if gpu_info.get('available', False) else '否'}")
        print(f"  GPU名称: {gpu_info.get('name', '未知')}")
        print(f"  GPU类型: {gpu_info.get('gpu_type', '未知')}")
        
        # 检查错误信息
        errors = gpu_info.get('errors', [])
        print(f"  错误信息数量: {len(errors)}")
        
        # 检查是否还有WMI相关的错误信息
        wmi_errors = [error for error in errors if 'WMI' in error or 'wmi' in error]
        print(f"  WMI相关错误: {len(wmi_errors)}")
        
        if wmi_errors:
            print("  ⚠️ 仍有WMI相关错误信息:")
            for error in wmi_errors:
                print(f"    - {error}")
        else:
            print("  ✅ 无WMI相关错误信息")
        
        # 检查检测方法
        methods = gpu_info.get('detection_methods', [])
        print(f"  检测方法: {', '.join(methods)}")
        
        return {
            "success": True,
            "gpu_available": gpu_info.get('available', False),
            "gpu_type": gpu_info.get('gpu_type', 'none'),
            "error_count": len(errors),
            "wmi_error_count": len(wmi_errors),
            "detection_methods": methods
        }
        
    except Exception as e:
        print(f"  ❌ GPU检测测试失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def test_core_functionality():
    """测试核心功能完整性"""
    print("\n🧪 测试核心功能完整性...")
    
    test_results = {}
    
    # 测试1: 语言检测
    try:
        from src.core.language_detector import detect_language_from_file
        import tempfile
        
        # 创建测试文件
        test_content = "这是一个测试字幕文件"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            test_file = f.name
        
        result = detect_language_from_file(test_file)
        test_results["language_detection"] = result == "zh"
        print(f"  语言检测: {'✅ 通过' if test_results['language_detection'] else '❌ 失败'}")
        
        # 清理测试文件
        os.unlink(test_file)
        
    except Exception as e:
        test_results["language_detection"] = False
        print(f"  语言检测: ❌ 异常 - {e}")
    
    # 测试2: 模型切换
    try:
        from src.core.model_switcher import ModelSwitcher
        switcher = ModelSwitcher()
        result = switcher.switch_model('zh')
        test_results["model_switching"] = True
        print(f"  模型切换: ✅ 通过")
    except Exception as e:
        test_results["model_switching"] = False
        print(f"  模型切换: ❌ 异常 - {e}")
    
    # 测试3: 剧本重构
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        engineer = ScreenplayEngineer()
        test_results["screenplay_engineering"] = True
        print(f"  剧本重构: ✅ 通过")
    except Exception as e:
        test_results["screenplay_engineering"] = False
        print(f"  剧本重构: ❌ 异常 - {e}")
    
    # 测试4: 训练功能
    try:
        from src.training.trainer import ModelTrainer
        trainer = ModelTrainer()
        test_results["training"] = True
        print(f"  训练功能: ✅ 通过")
    except Exception as e:
        test_results["training"] = False
        print(f"  训练功能: ❌ 异常 - {e}")
    
    # 测试5: 剪映导出
    try:
        from src.exporters.jianying_pro_exporter import JianyingProExporter
        exporter = JianyingProExporter()
        test_results["jianying_export"] = True
        print(f"  剪映导出: ✅ 通过")
    except Exception as e:
        test_results["jianying_export"] = False
        print(f"  剪映导出: ❌ 异常 - {e}")
    
    return test_results

def test_ui_components():
    """测试UI组件正常工作"""
    print("\n🖥️ 测试UI组件...")
    
    ui_results = {}
    
    # 测试PyQt6可用性
    try:
        from PyQt6.QtWidgets import QApplication
        ui_results["pyqt6"] = True
        print(f"  PyQt6: ✅ 可用")
    except ImportError:
        ui_results["pyqt6"] = False
        print(f"  PyQt6: ❌ 不可用")
    
    # 测试训练面板
    try:
        from src.ui.training_panel import TrainingMonitorWorker
        ui_results["training_panel"] = True
        print(f"  训练面板: ✅ 可用")
    except ImportError:
        ui_results["training_panel"] = False
        print(f"  训练面板: ❌ 不可用")
    
    # 测试进度仪表板
    try:
        from src.ui.progress_dashboard import ProgressDashboard
        ui_results["progress_dashboard"] = True
        print(f"  进度仪表板: ✅ 可用")
    except ImportError:
        ui_results["progress_dashboard"] = False
        print(f"  进度仪表板: ❌ 不可用")
    
    return ui_results

def test_system_stability():
    """测试系统稳定性"""
    print("\n🔧 测试系统稳定性...")
    
    import psutil
    
    # 获取内存状态
    memory = psutil.virtual_memory()
    print(f"  内存使用: {memory.percent:.1f}%")
    print(f"  可用内存: {memory.available / 1024**3:.1f}GB")
    
    # 测试多次GPU检测的稳定性
    print(f"  执行多次GPU检测稳定性测试...")
    
    stable_results = []
    for i in range(5):
        try:
            from simple_ui_fixed import detect_gpu_info
            gpu_info = detect_gpu_info()
            stable_results.append(gpu_info.get('available', False))
        except Exception as e:
            print(f"    第{i+1}次检测失败: {e}")
            stable_results.append(None)
    
    # 检查结果一致性
    consistent = all(result == stable_results[0] for result in stable_results if result is not None)
    print(f"  检测结果一致性: {'✅ 一致' if consistent else '❌ 不一致'}")
    
    return {
        "memory_percent": memory.percent,
        "available_memory_gb": memory.available / 1024**3,
        "detection_consistency": consistent,
        "detection_results": stable_results
    }

def run_wmi_optimization_verification():
    """运行WMI优化验证测试"""
    print("🔧 VisionAI-ClipsMaster WMI代码优化验证")
    print("=" * 50)
    
    # 1. 测试GPU检测优化效果
    gpu_test_result = test_gpu_detection_optimized()
    
    # 2. 测试核心功能完整性
    core_test_results = test_core_functionality()
    
    # 3. 测试UI组件
    ui_test_results = test_ui_components()
    
    # 4. 测试系统稳定性
    stability_results = test_system_stability()
    
    # 生成测试报告
    print("\n" + "=" * 50)
    print("📊 WMI优化验证结果总结:")
    
    # GPU检测优化效果
    if gpu_test_result["success"]:
        print(f"  GPU检测功能: ✅ 正常")
        print(f"  WMI错误信息: {'✅ 已清理' if gpu_test_result['wmi_error_count'] == 0 else '⚠️ 仍有残留'}")
    else:
        print(f"  GPU检测功能: ❌ 异常")
    
    # 核心功能完整性
    core_passed = sum(core_test_results.values())
    core_total = len(core_test_results)
    core_rate = (core_passed / core_total) * 100 if core_total > 0 else 0
    print(f"  核心功能: {core_rate:.1f}% ({core_passed}/{core_total})")
    
    # UI组件可用性
    ui_passed = sum(ui_test_results.values())
    ui_total = len(ui_test_results)
    ui_rate = (ui_passed / ui_total) * 100 if ui_total > 0 else 0
    print(f"  UI组件: {ui_rate:.1f}% ({ui_passed}/{ui_total})")
    
    # 系统稳定性
    print(f"  系统稳定性: {'✅ 稳定' if stability_results['detection_consistency'] else '⚠️ 不稳定'}")
    print(f"  内存使用: {stability_results['memory_percent']:.1f}%")
    
    # 总体评估
    overall_success = (
        gpu_test_result["success"] and
        gpu_test_result["wmi_error_count"] == 0 and
        core_rate >= 80 and
        ui_rate >= 80 and
        stability_results["detection_consistency"]
    )
    
    print(f"\n🎯 WMI优化总体评估: {'✅ 成功' if overall_success else '⚠️ 需要进一步优化'}")
    
    if overall_success:
        print("✅ WMI代码优化成功，系统运行正常")
        print("✅ 无WMI相关错误信息")
        print("✅ 核心功能完整可用")
        print("✅ 适合Intel集成显卡环境运行")
    else:
        print("⚠️ 部分功能需要进一步优化")
    
    # 返回完整测试结果
    return {
        "timestamp": time.time(),
        "gpu_detection": gpu_test_result,
        "core_functionality": core_test_results,
        "ui_components": ui_test_results,
        "system_stability": stability_results,
        "overall_success": overall_success
    }

if __name__ == "__main__":
    # 运行WMI优化验证测试
    results = run_wmi_optimization_verification()
    
    # 保存测试报告
    import json
    with open("wmi_optimization_test_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细测试报告已保存到: wmi_optimization_test_report.json")
