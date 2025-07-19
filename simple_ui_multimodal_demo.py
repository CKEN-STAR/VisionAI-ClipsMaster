#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 多模态提示展示示例

此脚本展示了如何在simple_ui.py中集成多模态提示展示功能
"""

import sys
import os
from pathlib import Path
import logging

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 导入PyQt6
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer

# 导入多模态提示展示模块
from ui.assistant.multimodal_display import get_tip_manager, HolographicTip, AnimatedBubble

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultimodalDemoApp(QMainWindow):
    """多模态提示展示示例应用"""
    
    def __init__(self):
        """初始化应用"""
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("VisionAI-ClipsMaster 多模态提示展示示例")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化UI
        self.init_ui()
        
        # 获取提示管理器
        self.tip_manager = get_tip_manager()
        
        # 设置欢迎提示的定时器
        QTimer.singleShot(1000, self.show_welcome_tip)
    
    def init_ui(self):
        """初始化UI"""
        # 创建中央窗口部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标题标签
        title_label = QLabel("多模态提示展示示例")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        main_layout.addWidget(title_label)
        
        # 创建说明标签
        desc_label = QLabel("这个示例展示了如何在VisionAI-ClipsMaster中集成多模态提示展示功能。\n"
                           "点击下面的按钮尝试不同类型的提示展示效果。")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("font-size: 14px; margin: 10px;")
        main_layout.addWidget(desc_label)
        
        # 创建按钮
        self.create_buttons(main_layout)
        
        # 添加弹性空间
        main_layout.addStretch(1)
    
    def create_buttons(self, layout):
        """创建按钮
        
        Args:
            layout: 要添加按钮的布局
        """
        # 全息提示按钮
        holographic_button = QPushButton("显示全息提示")
        holographic_button.clicked.connect(self.show_holographic_tip)
        holographic_button.setStyleSheet("font-size: 14px; padding: 10px; margin: 5px;")
        layout.addWidget(holographic_button)
        
        # 动画气泡按钮
        bubble_button = QPushButton("显示动画气泡")
        bubble_button.clicked.connect(self.show_animated_bubble)
        bubble_button.setStyleSheet("font-size: 14px; padding: 10px; margin: 5px;")
        layout.addWidget(bubble_button)
        
        # 多个提示按钮
        multi_button = QPushButton("显示多个提示")
        multi_button.clicked.connect(self.show_multiple_tips)
        multi_button.setStyleSheet("font-size: 14px; padding: 10px; margin: 5px;")
        layout.addWidget(multi_button)
        
        # 关闭所有提示按钮
        close_button = QPushButton("关闭所有提示")
        close_button.clicked.connect(self.close_all_tips)
        close_button.setStyleSheet("font-size: 14px; padding: 10px; margin: 5px;")
        layout.addWidget(close_button)
    
    def show_welcome_tip(self):
        """显示欢迎提示"""
        self.tip_manager.show_holographic_tip(
            self, 
            "欢迎使用<b>VisionAI-ClipsMaster</b>多模态提示展示功能！<br><br>"
            "点击下方按钮尝试不同类型的提示效果。"
        )
    
    def show_holographic_tip(self):
        """显示全息提示"""
        self.tip_manager.show_holographic_tip(
            self, 
            "这是一个<b>全息投影式</b>提示，<br>"
            "带有3D效果和动画！<br><br>"
            "您可以点击关闭按钮或等待它自动消失。"
        )
    
    def show_animated_bubble(self):
        """显示动画气泡"""
        self.tip_manager.show_animated_bubble(
            self, 
            "这是一个<b>动画气泡</b>提示，带有淡入淡出和弹跳效果！<br><br>"
            "这种提示适合显示重要信息或操作提示。"
        )
    
    def show_multiple_tips(self):
        """显示多个提示"""
        # 显示全息提示
        self.tip_manager.show_holographic_tip(
            self, 
            "您可以同时显示<b>多种类型</b>的提示！"
        )
        
        # 显示多个气泡
        positions = [
            (200, 200),
            (400, 300),
            (600, 200)
        ]
        
        messages = [
            "提示1: 视频处理完成！",
            "提示2: 新功能已解锁！",
            "提示3: 系统状态良好！"
        ]
        
        for pos, msg in zip(positions, messages):
            self.tip_manager.show_animated_bubble(self, msg, pos)
    
    def close_all_tips(self):
        """关闭所有提示"""
        self.tip_manager.close_all_tips()


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    window = MultimodalDemoApp()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 