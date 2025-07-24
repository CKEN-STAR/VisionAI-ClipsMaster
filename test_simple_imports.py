#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单导入测试
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_video_processor():
    """测试视频处理器"""
    try:
        from src.core.video_processor import VideoProcessor
        processor = VideoProcessor()
        print("✅ VideoProcessor导入成功")
        
        if hasattr(processor, 'detect_video_info'):
            print("✅ detect_video_info方法存在")
        else:
            print("❌ detect_video_info方法不存在")
        return True
    except Exception as e:
        print(f"❌ VideoProcessor导入失败: {e}")
        return False

def test_jianying_exporter():
    """测试剪映导出器"""
    try:
        from src.exporters.jianying_pro_exporter import JianyingProExporter
        exporter = JianyingProExporter()
        print("✅ JianyingProExporter导入成功")
        return True
    except Exception as e:
        print(f"❌ JianyingProExporter导入失败: {e}")
        return False

def test_ui_components():
    """测试UI组件"""
    # 创建QApplication
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("✅ QApplication创建成功")
    except ImportError:
        print("⚠️ PyQt6不可用，跳过UI测试")
        return True
    
    # 测试主窗口
    try:
        from ui.main_window import MainWindow
        main_window = MainWindow()
        print("✅ MainWindow导入成功")
        
        if hasattr(main_window, 'setup_ui'):
            print("✅ MainWindow.setup_ui存在")
        else:
            print("❌ MainWindow.setup_ui不存在")
            
        main_window.close()
    except Exception as e:
        print(f"❌ MainWindow测试失败: {e}")
        return False
    
    # 测试训练面板
    try:
        from ui.training_panel import TrainingPanel
        training_panel = TrainingPanel()
        print("✅ TrainingPanel导入成功")
        
        if hasattr(training_panel, 'setup_ui'):
            print("✅ TrainingPanel.setup_ui存在")
        else:
            print("❌ TrainingPanel.setup_ui不存在")
    except Exception as e:
        print(f"❌ TrainingPanel测试失败: {e}")
        return False
    
    # 测试进度看板
    try:
        from ui.progress_dashboard import ProgressDashboard
        progress_dashboard = ProgressDashboard()
        print("✅ ProgressDashboard导入成功")
        
        if hasattr(progress_dashboard, 'setup_ui'):
            print("✅ ProgressDashboard.setup_ui存在")
        else:
            print("❌ ProgressDashboard.setup_ui不存在")
    except Exception as e:
        print(f"❌ ProgressDashboard测试失败: {e}")
        return False
    
    return True

def main():
    print("🔧 简单导入测试")
    print("=" * 40)
    
    results = []
    
    print("\n1. 测试视频处理器...")
    results.append(test_video_processor())
    
    print("\n2. 测试剪映导出器...")
    results.append(test_jianying_exporter())
    
    print("\n3. 测试UI组件...")
    results.append(test_ui_components())
    
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
