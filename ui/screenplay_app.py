#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster剧本重构应用 - 简化版（UI演示用）
"""

import sys
import os
import logging
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QApplication, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QSplitter, QMessageBox,
                             QLabel, QStatusBar)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

# 导入自定义组件
sys.path.append(str(Path(__file__).resolve().parent.parent))
from ui.components.video_processor import VideoProcessor
from ui.components.screenplay_editor import ScreenplayEditor
from ui.components.video_preview import VideoPreview
from ui.error_display import handle_error

logger = logging.getLogger(__name__)

class ScreenplayApp(QMainWindow):
    """VisionAI-ClipsMaster 剧本重构应用"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster 剧本重构")
        self.setMinimumSize(1200, 800)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 创建主widget和布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 创建三个主要组件
        self.video_processor = VideoProcessor()
        self.screenplay_editor = ScreenplayEditor()
        self.video_preview = VideoPreview()
        
        # 添加到选项卡
        self.tab_widget.addTab(self.video_processor, "视频处理")
        self.tab_widget.addTab(self.screenplay_editor, "剧本编辑")
        self.tab_widget.addTab(self.video_preview, "视频预览")
        
        # 添加选项卡到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 设置中央Widget
        self.setCentralWidget(central_widget)
        
    def closeEvent(self, event):
        """关闭窗口事件处理"""
        reply = QMessageBox.question(
            self, 
            "确认退出", 
            "确定要退出程序吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    """应用入口函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示应用窗口
    window = ScreenplayApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 