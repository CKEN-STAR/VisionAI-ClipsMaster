#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI安全启动器
修复启动问题后的安全启动脚本
"""

import sys
import os
import time

# 设置环境变量以避免CUDA问题
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TORCH_USE_CUDA_DSA'] = '0'
os.environ['PYTHONIOENCODING'] = 'utf-8'

def main():
    """安全启动主函数"""
    print("🚀 VisionAI-ClipsMaster UI安全启动器")
    print("=" * 50)
    
    try:
        # 安全导入PyQt6
        print("📦 导入PyQt6...")
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
        from PyQt6.QtCore import Qt
        print("✅ PyQt6导入成功")
        
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setApplicationName("VisionAI-ClipsMaster")
        app.setStyle('Fusion')
        
        # 尝试导入主窗口
        window = None
        try:
            print("🔄 尝试加载主UI...")
            
            # 尝试导入简化UI
            import simple_ui_fixed
            window = simple_ui_fixed.SimpleScreenplayApp()
            print("✅ 主窗口创建成功")
            
        except Exception as e:
            print(f"⚠️ 主窗口创建失败: {e}")
            print("🔄 使用安全模式窗口...")
            
            # 创建安全模式窗口
            window = QMainWindow()
            window.setWindowTitle("VisionAI-ClipsMaster - 安全模式")
            window.setGeometry(300, 300, 800, 600)
            
            central_widget = QWidget()
            window.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # 添加标题
            title_label = QLabel("VisionAI-ClipsMaster")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px; color: #2196F3;")
            layout.addWidget(title_label)
            
            # 添加状态信息
            status_label = QLabel("程序正在安全模式下运行")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet("font-size: 14px; color: #666; margin: 10px;")
            layout.addWidget(status_label)
            
            # 添加错误信息
            error_text = QTextEdit()
            error_text.setReadOnly(True)
            error_text.setMaximumHeight(200)
            error_text.setPlainText(f"启动错误详情:\n{str(e)}\n\n建议:\n1. 检查依赖安装\n2. 重启程序\n3. 查看错误日志")
            layout.addWidget(error_text)
            
            # 添加按钮
            button_layout = QVBoxLayout()
            
            retry_button = QPushButton("🔄 重试启动")
            retry_button.clicked.connect(lambda: restart_program())
            retry_button.setStyleSheet("QPushButton { padding: 10px; font-size: 12px; }")
            button_layout.addWidget(retry_button)
            
            exit_button = QPushButton("❌ 退出程序")
            exit_button.clicked.connect(app.quit)
            exit_button.setStyleSheet("QPushButton { padding: 10px; font-size: 12px; }")
            button_layout.addWidget(exit_button)
            
            layout.addLayout(button_layout)
            
            print("✅ 安全模式窗口创建成功")
        
        # 显示窗口
        if window:
            window.show()
            print("🎉 程序启动成功！")
            
            # 运行应用程序
            sys.exit(app.exec())
        else:
            print("❌ 无法创建窗口")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 创建最小化错误窗口
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            if not QApplication.instance():
                app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setWindowTitle("启动错误")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("VisionAI-ClipsMaster 启动失败")
            msg.setInformativeText(f"错误信息:\n{str(e)}\n\n请检查:\n1. PyQt6是否正确安装\n2. Python环境是否正常\n3. 依赖库是否完整")
            msg.setDetailedText(traceback.format_exc())
            msg.exec()
            
        except:
            print("无法显示错误对话框")
            input("按回车键退出...")
        
        sys.exit(1)

def restart_program():
    """重启程序"""
    try:
        import subprocess
        print("🔄 重启程序...")
        subprocess.Popen([sys.executable, __file__])
        sys.exit(0)
    except Exception as e:
        print(f"重启失败: {e}")

if __name__ == "__main__":
    main()
