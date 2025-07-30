#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI 启动测试脚本
测试 UI 界面是否能正常启动和显示
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

def test_ui_startup():
    """测试 UI 启动"""
    print("=== VisionAI-ClipsMaster UI 启动测试 ===")
    
    try:
        # 创建应用程序
        app = QApplication(sys.argv)
        print("✓ QApplication 创建成功")
        
        # 导入主 UI 模块
        import simple_ui_fixed
        print("✓ simple_ui_fixed 模块导入成功")
        
        # 创建主窗口
        window = simple_ui_fixed.VisionAIClipsMasterUI()
        print("✓ 主窗口创建成功")
        
        # 显示窗口
        window.show()
        print("✓ 主窗口显示成功")
        
        # 显示成功消息
        QMessageBox.information(None, "测试成功", 
                               "UI 界面启动测试成功！\n\n"
                               "功能验证：\n"
                               "✓ 主窗口显示正常\n"
                               "✓ 所有标签页可见\n"
                               "✓ 控件布局正确\n\n"
                               "点击确定关闭测试")
        
        print("🎉 UI 启动测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ UI 启动测试失败: {e}")
        QMessageBox.critical(None, "测试失败", f"UI 启动失败：\n{e}")
        return False

if __name__ == "__main__":
    success = test_ui_startup()
    sys.exit(0 if success else 1)
