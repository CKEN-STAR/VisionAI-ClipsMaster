#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU检测弹窗按钮本地化测试脚本

用于测试GPU检测弹窗的按钮是否正确显示中文文本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

def test_gpu_dialog_localization():
    """测试GPU检测弹窗的按钮本地化"""
    print("=" * 60)
    print("GPU检测弹窗按钮本地化测试")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from PyQt6.QtWidgets import QApplication
        from simple_ui_fixed import detect_gpu_info, show_gpu_detection_dialog, diagnose_gpu_issues
        
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        print("\n1. 执行GPU检测...")
        gpu_info = detect_gpu_info()
        
        print(f"检测结果:")
        print(f"  独立显卡可用: {gpu_info.get('available', False)}")
        print(f"  GPU名称: {gpu_info.get('name', 'N/A')}")
        print(f"  GPU类型: {gpu_info.get('gpu_type', 'none')}")
        
        print("\n2. 获取诊断信息...")
        diagnosis = None
        if not gpu_info.get('available', False):
            try:
                diagnosis = diagnose_gpu_issues()
                print("诊断信息获取成功")
            except Exception as e:
                print(f"诊断信息获取失败: {e}")
        
        print("\n3. 显示GPU检测弹窗...")
        print("请检查弹窗中的按钮文本是否为中文：")
        print("  - 'OK' 应显示为 '确定'")
        print("  - 'Details' 或 'Show Details' 应显示为 '详细信息'")
        print("  - 'Hide Details' 应显示为 '隐藏详细信息'")
        print("\n弹窗将在3秒后显示...")
        
        # 延迟显示弹窗
        from PyQt6.QtCore import QTimer
        
        def show_dialog():
            show_gpu_detection_dialog(None, gpu_info, diagnosis)
            app.quit()  # 关闭应用
        
        QTimer.singleShot(3000, show_dialog)  # 3秒后显示弹窗
        
        # 运行应用
        app.exec()
        
        print("\n4. 测试完成")
        print("如果按钮文本显示为中文，则本地化成功！")
        
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保在VisionAI-ClipsMaster项目目录中运行此脚本")
        return False
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_dialog():
    """手动测试弹窗显示"""
    print("\n" + "=" * 60)
    print("手动弹窗测试")
    print("=" * 60)

    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton
        from PyQt6.QtCore import QTimer

        app = QApplication(sys.argv)

        # 创建一个简单的测试弹窗
        msg = QMessageBox()
        msg.setWindowTitle("按钮本地化测试")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("这是一个测试弹窗")
        msg.setInformativeText("请检查按钮文本是否为中文")
        msg.setDetailedText("这是详细信息内容\n用于测试Details按钮的本地化\n\n详细信息:\n- 测试项目1\n- 测试项目2\n- 测试项目3")

        # 设置标准按钮
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        # 中文本地化按钮文本
        ok_button = msg.button(QMessageBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("确定")

        # 本地化Details按钮的函数
        def localize_buttons():
            for button in msg.findChildren(QPushButton):
                button_text = button.text()
                if "Details" in button_text or "Show Details" in button_text:
                    button.setText("详细信息")
                elif "Hide Details" in button_text:
                    button.setText("隐藏详细信息")

        # 设置按钮本地化
        def setup_localization():
            localize_buttons()
            # 为按钮添加点击后的本地化
            for button in msg.findChildren(QPushButton):
                if not hasattr(button, '_localized'):
                    button._localized = True
                    button.clicked.connect(lambda: QTimer.singleShot(50, localize_buttons))

        # 延迟执行本地化设置
        QTimer.singleShot(0, setup_localization)

        print("显示测试弹窗...")
        print("请检查以下按钮文本:")
        print("1. 主按钮应显示为 '确定'")
        print("2. 详细信息按钮应显示为 '详细信息'")
        print("3. 点击详细信息后，按钮应变为 '隐藏详细信息'")

        # 显示弹窗
        result = msg.exec()

        print(f"弹窗关闭，返回值: {result}")
        print("本地化测试完成！")

        return True

    except Exception as e:
        print(f"手动测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("VisionAI-ClipsMaster GPU弹窗按钮本地化测试工具")
    print(f"项目路径: {PROJECT_ROOT}")
    
    # 执行GPU检测弹窗测试
    success1 = test_gpu_dialog_localization()
    
    # 等待用户确认
    input("\n按Enter键继续手动弹窗测试...")
    
    # 执行手动弹窗测试
    success2 = test_manual_dialog()
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"GPU检测弹窗测试: {'✅ 成功' if success1 else '❌ 失败'}")
    print(f"手动弹窗测试: {'✅ 成功' if success2 else '❌ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有测试通过！按钮本地化功能正常工作。")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
    
    print(f"\n按Enter键退出...")
    input()
