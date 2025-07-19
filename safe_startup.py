#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 安全启动脚本
确保程序能够稳定启动的安全版本
"""

import sys
import os
import time

# 设置环境变量以避免CUDA问题
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TORCH_USE_CUDA_DSA'] = '0'
os.environ['PYTHONIOENCODING'] = 'utf-8'

def safe_import(module_name, fallback=None):
    """安全导入模块"""
    try:
        return __import__(module_name)
    except ImportError as e:
        print(f"[WARN] 导入 {module_name} 失败: {e}")
        return fallback

def main():
    """安全启动主函数"""
    print("🚀 VisionAI-ClipsMaster 安全启动...")
    
    try:
        # 安全导入PyQt6
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        
        print("✅ PyQt6导入成功")
        
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setApplicationName("VisionAI-ClipsMaster")
        
        # 尝试导入主窗口
        try:
            # 尝试导入简化UI
            import simple_ui_fixed
            window = simple_ui_fixed.SimpleScreenplayApp()
            print("✅ 主窗口创建成功")
            
        except Exception as e:
            print(f"[WARN] 主窗口创建失败: {e}")
            print("🔄 使用简化窗口...")
            
            # 创建简化窗口
            window = QMainWindow()
            window.setWindowTitle("VisionAI-ClipsMaster - 简化模式")
            window.setGeometry(300, 300, 800, 600)
            
            central_widget = QWidget()
            window.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # 添加标题
            title_label = QLabel("VisionAI-ClipsMaster")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
            layout.addWidget(title_label)
            
            # 添加状态信息
            status_label = QLabel("程序正在简化模式下运行\n某些高级功能可能不可用")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(status_label)
            
            # 添加重试按钮
            retry_button = QPushButton("重试完整启动")
            retry_button.clicked.connect(lambda: restart_full_mode())
            layout.addWidget(retry_button)
            
            print("✅ 简化窗口创建成功")
        
        # 显示窗口
        window.show()
        
        print("🎉 程序启动成功！")
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 创建最小化错误窗口
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setWindowTitle("启动错误")
            msg.setText(f"程序启动失败:\n{str(e)}")
            msg.setInformativeText("请检查依赖安装和配置")
            msg.exec()
            
        except:
            print("无法显示错误对话框")

        sys.exit(1)

def restart_full_mode():
    """重启完整模式"""
    try:
        import subprocess
        subprocess.Popen([sys.executable, "simple_ui_fixed.py"])
    except Exception as e:
        print(f"重启失败: {e}")

if __name__ == "__main__":
    main()

def restart_full_mode():
    """重启完整模式"""
    try:
        import subprocess
        subprocess.Popen([sys.executable, "src/visionai_clipsmaster/ui/main_window.py"])
    except Exception as e:
        print(f"重启失败: {e}")

if __name__ == "__main__":
    main()
