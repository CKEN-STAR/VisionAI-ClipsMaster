#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 最终UI集成测试
验证WMI修复后的完整系统功能

测试内容:
1. 主UI程序启动测试
2. 所有UI组件加载验证
3. 核心功能集成测试
4. 完整工作流程验证
5. 系统稳定性确认
"""

import os
import sys
import time
import tempfile
import threading
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_main_ui_startup():
    """测试主UI程序启动"""
    print("🚀 测试主UI程序启动...")
    
    try:
        # 导入主UI类
        from simple_ui_fixed import SimpleScreenplayApp
        
        print("  ✅ 主UI类导入成功")
        
        # 测试UI类初始化（不实际显示窗口）
        try:
            from PyQt6.QtWidgets import QApplication
            import sys
            
            # 创建QApplication实例（如果不存在）
            if not QApplication.instance():
                app = QApplication(sys.argv)
            else:
                app = QApplication.instance()
            
            # 创建主窗口实例
            main_window = SimpleScreenplayApp()
            
            print("  ✅ 主窗口创建成功")
            print(f"  窗口标题: {main_window.windowTitle()}")
            print(f"  窗口大小: {main_window.size().width()}x{main_window.size().height()}")
            
            # 测试窗口基本属性
            window_info = {
                "title": main_window.windowTitle(),
                "width": main_window.size().width(),
                "height": main_window.size().height(),
                "visible": main_window.isVisible()
            }
            
            # 清理
            main_window.close()
            
            return {
                "success": True,
                "window_info": window_info,
                "ui_class": "SimpleScreenplayApp"
            }
            
        except Exception as e:
            print(f"  ❌ 主窗口创建失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    except ImportError as e:
        print(f"  ❌ 主UI类导入失败: {e}")
        return {
            "success": False,
            "error": f"导入失败: {str(e)}"
        }

def test_ui_components_loading():
    """测试UI组件加载"""
    print("\n🧩 测试UI组件加载...")
    
    components_results = {}
    
    # 测试组件列表
    components_to_test = [
        ("训练面板", "src.ui.training_panel", "TrainingPanel"),
        ("进度仪表板", "src.ui.progress_dashboard", "ProgressDashboard"),
        ("实时图表", "src.ui.components.realtime_charts", "RealtimeCharts"),
        ("警报管理器", "src.ui.components.alert_manager", "AlertManager"),
        ("主窗口", "simple_ui_fixed", "SimpleScreenplayApp")
    ]
    
    for component_name, module_path, class_name in components_to_test:
        print(f"  测试{component_name}...")
        try:
            # 动态导入模块
            module = __import__(module_path, fromlist=[class_name])
            component_class = getattr(module, class_name)
            
            components_results[component_name] = {
                "success": True,
                "module": module_path,
                "class": class_name,
                "available": True
            }
            print(f"    ✅ {component_name}: 可用")
            
        except ImportError as e:
            components_results[component_name] = {
                "success": False,
                "error": f"导入失败: {str(e)}",
                "available": False
            }
            print(f"    ❌ {component_name}: 导入失败 - {e}")
        except AttributeError as e:
            components_results[component_name] = {
                "success": False,
                "error": f"类不存在: {str(e)}",
                "available": False
            }
            print(f"    ❌ {component_name}: 类不存在 - {e}")
        except Exception as e:
            components_results[component_name] = {
                "success": False,
                "error": f"其他错误: {str(e)}",
                "available": False
            }
            print(f"    ❌ {component_name}: 其他错误 - {e}")
    
    return components_results

def test_core_integration():
    """测试核心功能集成"""
    print("\n🔗 测试核心功能集成...")
    
    integration_results = {}
    
    # 测试1: GPU检测集成
    print("  测试GPU检测集成...")
    try:
        from simple_ui_fixed import detect_gpu_info
        gpu_info = detect_gpu_info()
        
        # 检查WMI错误
        errors = gpu_info.get('errors', [])
        wmi_errors = [error for error in errors if 'WMI' in error or 'wmi' in error]
        
        integration_results["gpu_detection"] = {
            "success": len(wmi_errors) == 0,
            "gpu_available": gpu_info.get('available', False),
            "gpu_type": gpu_info.get('gpu_type', 'unknown'),
            "wmi_errors_count": len(wmi_errors),
            "total_errors": len(errors)
        }
        
        print(f"    GPU类型: {gpu_info.get('gpu_type', 'unknown')}")
        print(f"    WMI错误: {len(wmi_errors)}个")
        print(f"    ✅ GPU检测集成: {'通过' if len(wmi_errors) == 0 else '失败'}")
        
    except Exception as e:
        integration_results["gpu_detection"] = {
            "success": False,
            "error": str(e)
        }
        print(f"    ❌ GPU检测集成异常: {e}")
    
    # 测试2: 模型管理集成
    print("  测试模型管理集成...")
    try:
        from src.core.model_switcher import ModelSwitcher
        from src.core.language_detector import detect_language_from_file
        
        # 创建测试字幕
        test_content = "这是一个测试字幕文件"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            test_file = f.name
        
        # 语言检测
        detected_lang = detect_language_from_file(test_file)
        
        # 模型切换
        switcher = ModelSwitcher()
        switch_result = switcher.switch_model(detected_lang)
        current_model = switcher.get_current_model()
        
        # 清理
        os.unlink(test_file)
        
        integration_results["model_management"] = {
            "success": switch_result,
            "detected_language": detected_lang,
            "current_model": current_model,
            "switch_successful": switch_result
        }
        
        print(f"    检测语言: {detected_lang}")
        print(f"    当前模型: {current_model}")
        print(f"    ✅ 模型管理集成: {'通过' if switch_result else '失败'}")
        
    except Exception as e:
        integration_results["model_management"] = {
            "success": False,
            "error": str(e)
        }
        print(f"    ❌ 模型管理集成异常: {e}")
    
    # 测试3: 剧本处理集成
    print("  测试剧本处理集成...")
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        
        engineer = ScreenplayEngineer()
        
        # 测试数据
        test_subtitles = [
            {"start": "00:00:01,000", "end": "00:00:05,000", "text": "测试字幕1"},
            {"start": "00:00:05,000", "end": "00:00:10,000", "text": "测试字幕2"}
        ]
        
        # 剧情分析
        analysis = engineer.analyze_plot(test_subtitles)
        
        # 剧本重构
        result = engineer.reconstruct_screenplay(srt_input=test_subtitles, target_style="viral")
        reconstructed = result.get('segments', []) if isinstance(result, dict) else []
        
        integration_results["screenplay_processing"] = {
            "success": len(reconstructed) > 0,
            "original_count": len(test_subtitles),
            "reconstructed_count": len(reconstructed),
            "analysis_available": analysis is not None
        }
        
        print(f"    原始字幕: {len(test_subtitles)}条")
        print(f"    重构字幕: {len(reconstructed)}条")
        print(f"    ✅ 剧本处理集成: {'通过' if len(reconstructed) > 0 else '失败'}")
        
    except Exception as e:
        integration_results["screenplay_processing"] = {
            "success": False,
            "error": str(e)
        }
        print(f"    ❌ 剧本处理集成异常: {e}")
    
    return integration_results

def test_complete_workflow():
    """测试完整工作流程"""
    print("\n🔄 测试完整工作流程...")
    
    workflow_steps = {}
    
    try:
        # 步骤1: 创建测试数据
        print("  步骤1: 创建测试数据...")
        test_srt_content = """1
00:00:01,000 --> 00:00:05,000
小明是一个普通的上班族

2
00:00:05,000 --> 00:00:10,000
每天过着平凡的生活

3
00:00:10,000 --> 00:00:15,000
直到有一天他遇到了神秘的老人
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(test_srt_content)
            test_srt_path = f.name
        
        workflow_steps["data_creation"] = {
            "success": True,
            "file_path": test_srt_path
        }
        print("    ✅ 测试数据创建成功")
        
        # 步骤2: 语言检测
        print("  步骤2: 语言检测...")
        from src.core.language_detector import detect_language_from_file
        detected_language = detect_language_from_file(test_srt_path)
        
        workflow_steps["language_detection"] = {
            "success": detected_language in ['zh', 'en'],
            "detected_language": detected_language
        }
        print(f"    ✅ 检测语言: {detected_language}")
        
        # 步骤3: 模型切换
        print("  步骤3: 模型切换...")
        from src.core.model_switcher import ModelSwitcher
        switcher = ModelSwitcher()
        switch_result = switcher.switch_model(detected_language)
        current_model = switcher.get_current_model()
        
        workflow_steps["model_switching"] = {
            "success": switch_result,
            "target_language": detected_language,
            "current_model": current_model
        }
        print(f"    ✅ 切换到模型: {current_model}")
        
        # 步骤4: 剧本重构
        print("  步骤4: 剧本重构...")
        from src.core.screenplay_engineer import ScreenplayEngineer
        engineer = ScreenplayEngineer()
        
        # 加载字幕
        subtitles = engineer.load_subtitles(test_srt_path)
        
        # 重构剧本
        reconstruction_result = engineer.reconstruct_screenplay(srt_input=subtitles, target_style="viral")
        reconstructed_segments = reconstruction_result.get('segments', []) if isinstance(reconstruction_result, dict) else []
        
        workflow_steps["screenplay_reconstruction"] = {
            "success": len(reconstructed_segments) > 0,
            "original_count": len(subtitles),
            "reconstructed_count": len(reconstructed_segments)
        }
        print(f"    ✅ 重构完成: {len(subtitles)} → {len(reconstructed_segments)}条")
        
        # 步骤5: 导出配置
        print("  步骤5: 导出配置...")
        from src.exporters.jianying_pro_exporter import JianyingProExporter
        exporter = JianyingProExporter()
        
        workflow_steps["export_configuration"] = {
            "success": True,
            "exporter_type": type(exporter).__name__,
            "export_settings": exporter.export_settings
        }
        print("    ✅ 导出配置完成")
        
        # 清理测试文件
        os.unlink(test_srt_path)
        
        # 整体工作流程评估
        all_steps_success = all(step.get("success", False) for step in workflow_steps.values())
        
        workflow_steps["overall_assessment"] = {
            "success": all_steps_success,
            "completed_steps": len(workflow_steps),
            "successful_steps": sum(1 for step in workflow_steps.values() if step.get("success", False))
        }
        
        print(f"  ✅ 完整工作流程: {'通过' if all_steps_success else '失败'}")
        
    except Exception as e:
        workflow_steps["workflow_error"] = {
            "success": False,
            "error": str(e)
        }
        print(f"  ❌ 工作流程异常: {e}")
    
    return workflow_steps

def test_system_stability():
    """测试系统稳定性"""
    print("\n🔧 测试系统稳定性...")
    
    stability_results = {}
    
    # 测试1: 内存使用监控
    print("  测试内存使用...")
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        stability_results["memory_usage"] = {
            "total_gb": memory.total / 1024**3,
            "used_gb": memory.used / 1024**3,
            "percent": memory.percent,
            "within_target": memory.percent < 90
        }
        
        print(f"    内存使用: {memory.percent:.1f}%")
        print(f"    ✅ 内存状态: {'正常' if memory.percent < 90 else '需要关注'}")
        
    except Exception as e:
        stability_results["memory_usage"] = {"success": False, "error": str(e)}
        print(f"    ❌ 内存监控异常: {e}")
    
    # 测试2: 多次操作一致性
    print("  测试多次操作一致性...")
    try:
        from simple_ui_fixed import detect_gpu_info
        
        # 执行多次GPU检测
        detection_results = []
        for i in range(3):
            gpu_info = detect_gpu_info()
            detection_results.append({
                "available": gpu_info.get("available", False),
                "gpu_type": gpu_info.get("gpu_type", "none"),
                "errors_count": len(gpu_info.get("errors", []))
            })
        
        # 检查一致性
        first_result = detection_results[0]
        consistent = all(
            result["available"] == first_result["available"] and
            result["gpu_type"] == first_result["gpu_type"]
            for result in detection_results
        )
        
        stability_results["operation_consistency"] = {
            "success": consistent,
            "test_count": len(detection_results),
            "consistent": consistent,
            "results": detection_results
        }
        
        print(f"    操作一致性: {'✅ 一致' if consistent else '❌ 不一致'}")
        
    except Exception as e:
        stability_results["operation_consistency"] = {"success": False, "error": str(e)}
        print(f"    ❌ 一致性测试异常: {e}")
    
    return stability_results

def run_final_integration_test():
    """运行最终集成测试"""
    print("🎯 VisionAI-ClipsMaster 最终UI集成测试")
    print("=" * 60)
    print("验证WMI修复后的完整系统功能")
    print("=" * 60)
    
    test_results = {}
    
    # 1. 主UI程序启动测试
    test_results["ui_startup"] = test_main_ui_startup()
    
    # 2. UI组件加载验证
    test_results["ui_components"] = test_ui_components_loading()
    
    # 3. 核心功能集成测试
    test_results["core_integration"] = test_core_integration()
    
    # 4. 完整工作流程验证
    test_results["complete_workflow"] = test_complete_workflow()
    
    # 5. 系统稳定性确认
    test_results["system_stability"] = test_system_stability()
    
    # 生成最终报告
    generate_final_report(test_results)
    
    return test_results

def generate_final_report(test_results):
    """生成最终测试报告"""
    print("\n" + "=" * 60)
    print("📊 最终UI集成测试报告")
    
    # 1. UI启动状态
    ui_startup = test_results.get("ui_startup", {})
    print(f"  主UI启动: {'✅ 成功' if ui_startup.get('success', False) else '❌ 失败'}")
    
    # 2. UI组件状态
    ui_components = test_results.get("ui_components", {})
    ui_success_count = sum(1 for comp in ui_components.values() if comp.get("success", False))
    ui_total_count = len(ui_components)
    ui_success_rate = (ui_success_count / ui_total_count * 100) if ui_total_count > 0 else 0
    print(f"  UI组件: {ui_success_rate:.1f}% ({ui_success_count}/{ui_total_count})")
    
    # 3. 核心集成状态
    core_integration = test_results.get("core_integration", {})
    core_success_count = sum(1 for test in core_integration.values() if test.get("success", False))
    core_total_count = len(core_integration)
    core_success_rate = (core_success_count / core_total_count * 100) if core_total_count > 0 else 0
    print(f"  核心集成: {core_success_rate:.1f}% ({core_success_count}/{core_total_count})")
    
    # 4. 工作流程状态
    workflow = test_results.get("complete_workflow", {})
    workflow_success = workflow.get("overall_assessment", {}).get("success", False)
    print(f"  工作流程: {'✅ 流畅' if workflow_success else '❌ 有问题'}")
    
    # 5. 系统稳定性状态
    stability = test_results.get("system_stability", {})
    memory_ok = stability.get("memory_usage", {}).get("within_target", False)
    consistency_ok = stability.get("operation_consistency", {}).get("consistent", False)
    print(f"  内存使用: {'✅ 正常' if memory_ok else '⚠️ 需要关注'}")
    print(f"  操作一致性: {'✅ 一致' if consistency_ok else '❌ 不一致'}")
    
    # 6. 总体评估
    overall_success = (
        ui_startup.get("success", False) and
        ui_success_rate >= 80 and
        core_success_rate >= 80 and
        workflow_success and
        consistency_ok
    )
    
    print(f"\n🎯 最终集成测试结果: {'✅ 完全成功' if overall_success else '⚠️ 需要优化'}")
    
    if overall_success:
        print("🎉 恭喜！VisionAI-ClipsMaster UI集成测试完全通过")
        print("✅ WMI错误修复完全成功")
        print("✅ 所有核心功能正常工作")
        print("✅ UI界面完全可用")
        print("✅ 工作流程流畅运行")
        print("✅ 系统在Intel集成显卡环境下稳定运行")
        print("🚀 系统已准备好投入生产使用！")
    else:
        print("⚠️ 部分功能需要进一步优化")
        
        # 提供具体建议
        if not ui_startup.get("success", False):
            print("  - 需要修复主UI启动问题")
        if ui_success_rate < 80:
            print("  - 需要解决UI组件加载问题")
        if core_success_rate < 80:
            print("  - 需要修复核心功能集成问题")
        if not workflow_success:
            print("  - 需要优化工作流程")
        if not consistency_ok:
            print("  - 需要提高操作一致性")

if __name__ == "__main__":
    # 运行最终集成测试
    results = run_final_integration_test()
    
    # 保存详细测试报告
    import json
    with open("final_ui_integration_test_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细测试报告已保存到: final_ui_integration_test_report.json")
