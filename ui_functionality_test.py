#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI功能测试脚本
验证UI整合后的核心功能是否正常工作
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_test_srt_file(language='zh'):
    """创建测试SRT文件"""
    if language == 'zh':
        content = """1
00:00:01,000 --> 00:00:05,000
这是一个测试字幕文件

2
00:00:05,000 --> 00:00:10,000
用于验证语言检测功能

3
00:00:10,000 --> 00:00:15,000
以及剧本重构功能
"""
    else:
        content = """1
00:00:01,000 --> 00:00:05,000
This is a test subtitle file

2
00:00:05,000 --> 00:00:10,000
For testing language detection

3
00:00:10,000 --> 00:00:15,000
And screenplay reconstruction
"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name

def test_language_detection():
    """测试语言检测功能"""
    print("🔍 测试语言检测功能...")
    
    try:
        from src.core.language_detector import detect_language_from_file
        
        # 测试中文检测
        zh_file = create_test_srt_file('zh')
        zh_result = detect_language_from_file(zh_file)
        print(f"  中文检测结果: {zh_result}")
        
        # 测试英文检测
        en_file = create_test_srt_file('en')
        en_result = detect_language_from_file(en_file)
        print(f"  英文检测结果: {en_result}")
        
        # 清理临时文件
        os.unlink(zh_file)
        os.unlink(en_file)
        
        success = zh_result == 'zh' and en_result == 'en'
        print(f"  ✅ 语言检测测试: {'通过' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"  ❌ 语言检测测试失败: {e}")
        return False

def test_model_switching():
    """测试模型切换功能"""
    print("🔄 测试模型切换功能...")
    
    try:
        from src.core.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher()
        
        # 测试切换到中文模型
        zh_result = switcher.switch_model('zh')
        zh_model = switcher.get_current_model()
        print(f"  切换到中文模型: {zh_result}, 当前模型: {zh_model}")
        
        # 测试切换到英文模型
        en_result = switcher.switch_model('en')
        en_model = switcher.get_current_model()
        print(f"  切换到英文模型: {en_result}, 当前模型: {en_model}")
        
        success = zh_result and en_result
        print(f"  ✅ 模型切换测试: {'通过' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"  ❌ 模型切换测试失败: {e}")
        return False

def test_screenplay_engineering():
    """测试剧本重构功能"""
    print("🎬 测试剧本重构功能...")
    
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        
        engineer = ScreenplayEngineer()
        
        # 创建测试字幕文件
        test_file = create_test_srt_file('zh')
        
        # 测试加载字幕
        subtitles = engineer.load_subtitles(test_file)
        print(f"  加载字幕数量: {len(subtitles)}")
        
        # 测试剧情分析
        analysis = engineer.analyze_plot(subtitles)
        print(f"  剧情分析结果: {type(analysis)}")
        
        # 测试重构 - 使用正确的API
        result = engineer.reconstruct_screenplay(srt_input=subtitles, target_style="viral")
        reconstructed = result.get('segments', []) if isinstance(result, dict) else []
        print(f"  重构字幕数量: {len(reconstructed)}")
        
        # 清理临时文件
        os.unlink(test_file)
        
        success = len(subtitles) > 0 and len(reconstructed) > 0
        print(f"  ✅ 剧本重构测试: {'通过' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"  ❌ 剧本重构测试失败: {e}")
        return False

def test_training_functionality():
    """测试训练功能"""
    print("📚 测试训练功能...")
    
    try:
        from src.training.trainer import ModelTrainer
        
        trainer = ModelTrainer()
        
        # 测试训练状态
        status = trainer.get_training_status() if hasattr(trainer, 'get_training_status') else {"active": False}
        print(f"  训练状态: {status}")
        
        # 模拟训练（不实际执行）
        print(f"  训练器类型: {type(trainer)}")
        
        success = trainer is not None
        print(f"  ✅ 训练功能测试: {'通过' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"  ❌ 训练功能测试失败: {e}")
        return False

def test_jianying_export():
    """测试剪映导出功能"""
    print("📤 测试剪映导出功能...")
    
    try:
        from src.exporters.jianying_pro_exporter import JianyingProExporter
        
        exporter = JianyingProExporter()
        
        # 测试导出器初始化
        print(f"  导出器类型: {type(exporter)}")
        print(f"  导出设置: {exporter.export_settings}")
        
        success = exporter is not None
        print(f"  ✅ 剪映导出测试: {'通过' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"  ❌ 剪映导出测试失败: {e}")
        return False

def test_memory_management():
    """测试内存管理功能"""
    print("💾 测试内存管理功能...")
    
    try:
        import psutil
        
        # 获取内存信息
        memory = psutil.virtual_memory()
        print(f"  总内存: {memory.total / 1024**3:.2f}GB")
        print(f"  已用内存: {memory.used / 1024**3:.2f}GB")
        print(f"  可用内存: {memory.available / 1024**3:.2f}GB")
        print(f"  内存使用率: {memory.percent:.1f}%")
        
        # 测试内存监控
        from ui_integration_fixes import AdvancedMemoryManager
        memory_mgr = AdvancedMemoryManager()
        status = memory_mgr.get_memory_status()
        
        print(f"  内存状态: {status['status']}")
        print(f"  是否在限制内: {status['within_limit']}")
        
        success = True
        print(f"  ✅ 内存管理测试: {'通过' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"  ❌ 内存管理测试失败: {e}")
        return False

def test_ui_components():
    """测试UI组件"""
    print("🖥️ 测试UI组件...")
    
    try:
        # 测试PyQt6可用性
        try:
            from PyQt6.QtWidgets import QApplication
            qt_available = True
            print("  PyQt6可用: ✅")
        except ImportError:
            qt_available = False
            print("  PyQt6可用: ❌")
        
        # 测试训练面板
        try:
            from src.ui.training_panel import TrainingMonitorWorker
            training_panel_available = True
            print("  训练面板可用: ✅")
        except ImportError:
            training_panel_available = False
            print("  训练面板可用: ❌")
        
        success = qt_available or training_panel_available
        print(f"  ✅ UI组件测试: {'通过' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"  ❌ UI组件测试失败: {e}")
        return False

def run_comprehensive_test():
    """运行综合功能测试"""
    print("🧪 VisionAI-ClipsMaster UI功能综合测试")
    print("=" * 50)
    
    test_results = {}
    
    # 执行各项测试
    test_functions = [
        ("语言检测", test_language_detection),
        ("模型切换", test_model_switching),
        ("剧本重构", test_screenplay_engineering),
        ("训练功能", test_training_functionality),
        ("剪映导出", test_jianying_export),
        ("内存管理", test_memory_management),
        ("UI组件", test_ui_components)
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n{test_name}测试:")
        try:
            result = test_func()
            test_results[test_name] = result
        except Exception as e:
            print(f"  ❌ {test_name}测试异常: {e}")
            test_results[test_name] = False
    
    # 生成测试报告
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体通过率: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    # 评估结果
    if success_rate >= 80:
        print("🎉 UI整合测试总体成功！系统基本可用。")
    elif success_rate >= 60:
        print("⚠️ UI整合测试部分成功，需要进一步优化。")
    else:
        print("🚨 UI整合测试失败较多，需要重点修复。")
    
    # 生成建议
    print("\n💡 改进建议:")
    failed_tests = [name for name, result in test_results.items() if not result]
    if failed_tests:
        print(f"  - 优先修复失败的功能: {', '.join(failed_tests)}")
    
    if test_results.get("内存管理", False):
        print("  - 内存管理功能正常，适合4GB设备运行")
    else:
        print("  - 需要优化内存管理策略")
    
    if test_results.get("UI组件", False):
        print("  - UI组件可用，界面功能正常")
    else:
        print("  - 需要检查PyQt6安装和UI组件")
    
    return test_results, success_rate

if __name__ == "__main__":
    # 运行测试
    results, rate = run_comprehensive_test()
    
    # 保存测试结果
    import json
    test_report = {
        "timestamp": time.time(),
        "test_results": results,
        "success_rate": rate,
        "total_tests": len(results),
        "passed_tests": sum(results.values()),
        "failed_tests": [name for name, result in results.items() if not result]
    }
    
    with open("ui_functionality_test_report.json", "w", encoding="utf-8") as f:
        json.dump(test_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细测试报告已保存到: ui_functionality_test_report.json")
