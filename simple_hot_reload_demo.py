#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 语言包热加载功能简单演示
"""

import os
import sys
import time
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QPushButton, QFileDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer

class SimpleHotReloadDemo(QMainWindow):
    """简单的语言包热加载演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语言包热加载简单演示")
        self.resize(600, 400)
        
        # 设置中心窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 标题标签
        title_label = QLabel("VisionAI-ClipsMaster 语言包热加载演示")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 说明标签
        info_label = QLabel(
            "本演示程序展示了语言包热加载功能。\n"
            "您可以修改语言文件，内容将在几秒内自动更新。"
        )
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # 创建语言文件按钮
        create_button = QPushButton("创建示例语言文件")
        create_button.clicked.connect(self.create_language_file)
        layout.addWidget(create_button)
        
        # 打开目录按钮
        open_dir_button = QPushButton("打开语言文件目录")
        open_dir_button.clicked.connect(self.open_language_dir)
        layout.addWidget(open_dir_button)
        
        # 状态文本区
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # 添加初始状态信息
        self.add_status("语言包热加载演示已启动")
        
        # 设置刷新计时器
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_status)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
    
    def create_language_file(self):
        """创建示例语言文件"""
        # 创建目录（如果不存在）
        dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "i18n", "translations")
        os.makedirs(dir_path, exist_ok=True)
        
        # 示例语言文件
        languages = {
            "zh_CN": {
                "metadata": {
                    "language": "zh_CN",
                    "name": "简体中文",
                    "native_name": "简体中文",
                    "version": "1.0.0"
                },
                "strings": {
                    "app_name": "VisionAI剪辑大师",
                    "welcome": "欢迎使用VisionAI剪辑大师",
                    "home": "首页",
                    "settings": "设置",
                    "help": "帮助"
                }
            },
            "en_US": {
                "metadata": {
                    "language": "en_US",
                    "name": "English (US)",
                    "native_name": "English (US)",
                    "version": "1.0.0"
                },
                "strings": {
                    "app_name": "VisionAI ClipsMaster",
                    "welcome": "Welcome to VisionAI ClipsMaster",
                    "home": "Home",
                    "settings": "Settings",
                    "help": "Help"
                }
            }
        }
        
        # 写入文件
        for lang_code, content in languages.items():
            file_path = os.path.join(dir_path, f"{lang_code}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=4)
            
            self.add_status(f"已创建语言文件: {file_path}")
        
        self.add_status("示例语言文件创建完成，您可以编辑这些文件测试热加载功能")
    
    def open_language_dir(self):
        """打开语言文件目录"""
        dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "i18n", "translations")
        
        # 确保目录存在
        os.makedirs(dir_path, exist_ok=True)
        
        # 使用系统文件管理器打开目录
        if sys.platform == 'win32':
            os.startfile(dir_path)
        elif sys.platform == 'darwin':  # macOS
            import subprocess
            subprocess.call(['open', dir_path])
        else:  # Linux
            import subprocess
            subprocess.call(['xdg-open', dir_path])
            
        self.add_status(f"已打开目录: {dir_path}")
    
    def add_status(self, message):
        """添加状态信息"""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
    
    def update_status(self):
        """更新状态信息"""
        dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "i18n", "translations")
        
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith('.json') or f.endswith('.qm')]
            if files:
                self.add_status(f"监视中的语言文件: {', '.join(files)}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = SimpleHotReloadDemo()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 