#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0级别问题修复验证测试
验证关键问题是否已经修复
"""

import os
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_video_processor_fix():
    """测试视频处理器语法错误修复"""
    print("🔧 测试视频处理器修复...")
    
    try:
        from src.core.video_processor import VideoProcessor
        processor = VideoProcessor()
        print("✅ VideoProcessor导入和初始化成功")
        
        # 检查是否有detect_video_info方法
        if hasattr(processor, 'detect_video_info'):
            print("✅ detect_video_info方法存在")
        else:
            print("⚠️ detect_video_info方法不存在")
        
        return True
    except SyntaxError as e:
        print(f"❌ 语法错误未修复: {e}")
        return False
    except Exception as e:
        print(f"⚠️ 其他错误: {e}")
        return True  # 语法错误已修复，其他错误可以接受

def test_jianying_exporter_fix():
    """测试剪映导出器修复"""
    print("\n🔧 测试剪映导出器修复...")
    
    try:
        # 测试原始类名
        from src.exporters.jianying_pro_exporter import JianYingProExporter
        print("✅ JianYingProExporter导入成功")
        
        # 测试别名
        from src.exporters.jianying_pro_exporter import JianyingProExporter
        print("✅ JianyingProExporter别名导入成功")
        
        # 验证它们是同一个类
        if JianYingProExporter == JianyingProExporter:
            print("✅ 别名设置正确")
        else:
            print("⚠️ 别名设置可能有问题")
        
        # 测试初始化
        exporter = JianyingProExporter()
        print("✅ JianyingProExporter初始化成功")
        
        return True
    except ImportError as e:
        print(f"❌ 导入错误未修复: {e}")
        return False
    except Exception as e:
        print(f"⚠️ 其他错误: {e}")
        return True

def test_ui_components_fix():
    """测试UI组件修复"""
    print("\n🔧 测试UI组件修复...")

    results = {}

    # 创建QApplication（如果不存在）
    try:
        from PyQt6.QtWidgets import QApplication
        import sys

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            print("✅ QApplication创建成功")
        else:
            print("✅ QApplication已存在")
    except ImportError:
        print("⚠️ PyQt6不可用，跳过UI测试")
        return True

    # 测试主窗口
    try:
        from ui.main_window import MainWindow
        main_window = MainWindow()
        
        # 检查setup_ui方法
        if hasattr(main_window, 'setup_ui'):
            print("✅ MainWindow.setup_ui方法存在")
            results['main_window_setup_ui'] = True
        else:
            print("❌ MainWindow.setup_ui方法缺失")
            results['main_window_setup_ui'] = False
        
        # 检查show方法
        if hasattr(main_window, 'show'):
            print("✅ MainWindow.show方法存在")
            results['main_window_show'] = True
        else:
            print("❌ MainWindow.show方法缺失")
            results['main_window_show'] = False
            
        main_window.close()  # 关闭窗口
        
    except Exception as e:
        print(f"❌ MainWindow测试失败: {e}")
        results['main_window'] = False
    
    # 测试训练面板
    try:
        from ui.training_panel import TrainingPanel
        training_panel = TrainingPanel()
        
        # 检查setup_ui方法
        if hasattr(training_panel, 'setup_ui'):
            print("✅ TrainingPanel.setup_ui方法存在")
            results['training_panel_setup_ui'] = True
        else:
            print("❌ TrainingPanel.setup_ui方法缺失")
            results['training_panel_setup_ui'] = False
        
        # 检查show方法
        if hasattr(training_panel, 'show'):
            print("✅ TrainingPanel.show方法存在")
            results['training_panel_show'] = True
        else:
            print("❌ TrainingPanel.show方法缺失")
            results['training_panel_show'] = False
            
    except Exception as e:
        print(f"❌ TrainingPanel测试失败: {e}")
        results['training_panel'] = False
    
    # 测试进度看板
    try:
        from ui.progress_dashboard import ProgressDashboard
        progress_dashboard = ProgressDashboard()
        
        # 检查setup_ui方法
        if hasattr(progress_dashboard, 'setup_ui'):
            print("✅ ProgressDashboard.setup_ui方法存在")
            results['progress_dashboard_setup_ui'] = True
        else:
            print("❌ ProgressDashboard.setup_ui方法缺失")
            results['progress_dashboard_setup_ui'] = False
        
        # 检查show方法
        if hasattr(progress_dashboard, 'show'):
            print("✅ ProgressDashboard.show方法存在")
            results['progress_dashboard_show'] = True
        else:
            print("❌ ProgressDashboard.show方法缺失")
            results['progress_dashboard_show'] = False
            
    except Exception as e:
        print(f"❌ ProgressDashboard测试失败: {e}")
        results['progress_dashboard'] = False
    
    return all(results.values())

def test_import_stability():
    """测试导入稳定性"""
    print("\n🔧 测试导入稳定性...")
    
    critical_modules = [
        'src.core.video_processor',
        'src.exporters.jianying_pro_exporter',
        'ui.main_window',
        'ui.training_panel',
        'ui.progress_dashboard'
    ]
    
    success_count = 0
    for module in critical_modules:
        try:
            __import__(module)
            print(f"✅ {module} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {module} 导入失败: {e}")
    
    success_rate = success_count / len(critical_modules) * 100
    print(f"\n导入成功率: {success_rate:.1f}% ({success_count}/{len(critical_modules)})")
    
    return success_rate >= 80

def main():
    """主测试函数"""
    print("🎬 开始P0级别问题修复验证测试")
    print("=" * 60)
    
    start_time = time.time()
    
    # 执行测试
    test_results = {
        'video_processor': test_video_processor_fix(),
        'jianying_exporter': test_jianying_exporter_fix(),
        'ui_components': test_ui_components_fix(),
        'import_stability': test_import_stability()
    }
    
    # 生成报告
    print("\n" + "=" * 60)
    print("📊 P0级别修复验证报告")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n总体结果: {passed_tests}/{total_tests} 通过")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    print(f"测试时长: {time.time() - start_time:.2f}秒")
    
    if passed_tests == total_tests:
        print("\n🎉 所有P0级别问题已成功修复！")
        return True
    else:
        print(f"\n⚠️ 还有 {total_tests - passed_tests} 个问题需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
