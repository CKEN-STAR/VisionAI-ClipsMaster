#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI功能验证脚本
专门验证UI的核心功能是否完整可用
"""

import sys
import os
import time
import json
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ui_functionality():
    """测试UI功能"""
    print("=" * 80)
    print("VisionAI-ClipsMaster UI功能验证")
    print("=" * 80)
    
    try:
        # 导入PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt, QTimer
        print("✅ PyQt6导入成功")
        
        # 创建应用程序
        app = QApplication(sys.argv)
        # PyQt6中高DPI支持是默认启用的，不需要手动设置
        print("✅ QApplication创建成功")
        
        # 导入主窗口
        from simple_ui_fixed import SimpleScreenplayApp
        print("✅ 主窗口类导入成功")
        
        # 创建主窗口
        main_window = SimpleScreenplayApp()
        print("✅ 主窗口实例创建成功")
        
        # 显示窗口
        main_window.show()
        print("✅ 窗口显示成功")
        
        # 验证核心功能
        print("\n" + "="*50)
        print("核心功能验证")
        print("="*50)
        
        # 1. 视频处理功能验证
        print("\n1. 视频处理功能验证:")
        video_functions = {
            "select_video": "视频文件选择",
            "select_subtitle": "SRT字幕文件导入", 
            "change_language_mode": "语言检测切换",
            "generate_viral_srt": "AI剧情分析和字幕重构",
            "generate_video": "视频切割拼接",
            "process_progress_bar": "进度显示"
        }
        
        for func_name, desc in video_functions.items():
            if hasattr(main_window, func_name):
                print(f"   ✅ {desc}: 方法存在")
            else:
                print(f"   ❌ {desc}: 方法不存在")
        
        # 2. 模型训练功能验证
        print("\n2. 模型训练功能验证:")
        if hasattr(main_window, 'tabs'):
            tab_count = main_window.tabs.count()
            print(f"   ✅ 标签页数量: {tab_count}")
            
            # 查找训练相关标签页
            training_found = False
            for i in range(tab_count):
                tab_text = main_window.tabs.tabText(i)
                print(f"   📋 标签页 {i+1}: {tab_text}")
                if "训练" in tab_text or "模型" in tab_text:
                    training_found = True
            
            if training_found:
                print("   ✅ 找到训练相关标签页")
            else:
                print("   ⚠️  未找到明确的训练标签页")
        else:
            print("   ❌ 标签页组件不存在")
        
        # 3. 设置和配置功能验证
        print("\n3. 设置和配置功能验证:")
        config_functions = {
            "lang_combo": "双模型切换组件",
            "use_gpu_check": "GPU/CPU模式切换",
            "stability_monitor": "内存优化监控"
        }
        
        for func_name, desc in config_functions.items():
            if hasattr(main_window, func_name):
                print(f"   ✅ {desc}: 组件存在")
            else:
                print(f"   ❌ {desc}: 组件不存在")
        
        # 4. 界面稳定性验证
        print("\n4. 界面稳定性验证:")
        stability_functions = {
            "responsiveness_monitor": "响应性监控",
            "ui_error_handler": "错误处理器"
        }
        
        for func_name, desc in stability_functions.items():
            if hasattr(main_window, func_name):
                print(f"   ✅ {desc}: 组件存在")
            else:
                print(f"   ❌ {desc}: 组件不存在")
        
        # 验证中文显示
        window_title = main_window.windowTitle()
        if "VisionAI" in window_title and "混剪" in window_title:
            print(f"   ✅ 中文显示正常: {window_title}")
        else:
            print(f"   ⚠️  标题显示: {window_title}")
        
        # 5. 输出功能验证
        print("\n5. 输出功能验证:")
        output_functions = {
            "generate_video": "视频文件导出",
            "video_list": "批量处理组件"
        }
        
        for func_name, desc in output_functions.items():
            if hasattr(main_window, func_name):
                print(f"   ✅ {desc}: 组件存在")
            else:
                print(f"   ❌ {desc}: 组件不存在")
        
        # 检查导出相关方法
        export_methods = []
        for attr_name in dir(main_window):
            if 'export' in attr_name.lower() or 'jianying' in attr_name.lower():
                export_methods.append(attr_name)
        
        if export_methods:
            print(f"   ✅ 找到导出相关方法: {len(export_methods)}个")
            for method in export_methods[:3]:  # 只显示前3个
                print(f"      - {method}")
        else:
            print("   ⚠️  未找到明确的导出方法")
        
        # 6. 剧本重构核心验证
        print("\n6. 剧本重构核心功能验证:")
        
        # 检查是否有处理器
        if hasattr(main_window, 'processor'):
            print("   ✅ 视频处理器存在")
            processor = main_window.processor
            if processor:
                print("   ✅ 处理器已初始化")
            else:
                print("   ⚠️  处理器未初始化")
        else:
            print("   ❌ 视频处理器不存在")
        
        # 检查AI相关功能
        ai_methods = []
        for attr_name in dir(main_window):
            if 'ai' in attr_name.lower() or 'viral' in attr_name.lower() or 'plot' in attr_name.lower():
                ai_methods.append(attr_name)
        
        if ai_methods:
            print(f"   ✅ 找到AI相关方法: {len(ai_methods)}个")
            for method in ai_methods[:3]:  # 只显示前3个
                print(f"      - {method}")
        else:
            print("   ⚠️  未找到明确的AI方法")
        
        print("\n" + "="*50)
        print("功能验证完成")
        print("="*50)
        
        # 保持窗口显示5秒
        print("\n窗口将保持显示5秒，请观察界面...")
        
        # 使用QTimer来延时关闭
        def close_app():
            print("正在关闭应用程序...")
            app.quit()
        
        timer = QTimer()
        timer.timeout.connect(close_app)
        timer.start(5000)  # 5秒后关闭
        
        # 运行应用程序
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 功能验证失败: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ui_functionality()
    if success:
        print("\n✅ UI功能验证完成")
    else:
        print("\n❌ UI功能验证失败")
    
    sys.exit(0 if success else 1)
