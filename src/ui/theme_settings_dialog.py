#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 主题设置对话框
提供主题设置界面
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialogButtonBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

from .theme_switcher import ThemeSwitcher

class ThemeSettingsDialog(QDialog):
    """主题设置对话框"""
    
    # 信号定义
    theme_changed = pyqtSignal(str)  # 主题名称
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("主题设置")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # 初始化UI
        self._init_ui()
        
        # 居中显示
        self._center_dialog()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("🎨 VisionAI-ClipsMaster 主题设置")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 描述
        desc_label = QLabel("选择您喜欢的界面主题，设置将立即生效并保存")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #666666;")
        layout.addWidget(desc_label)
        
        # 分隔线
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(separator)
        
        # 主题切换器
        self.theme_switcher = ThemeSwitcher(self)
        self.theme_switcher.theme_changed.connect(self._on_theme_changed)
        self.theme_switcher.theme_applied.connect(self._on_theme_applied)
        layout.addWidget(self.theme_switcher)
        
        # 按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 自定义按钮样式
        for button in button_box.buttons():
            button.setMinimumHeight(35)
            if button.text() == "OK":
                button.setText("确定")
            elif button.text() == "Cancel":
                button.setText("取消")
        
        layout.addWidget(button_box)
    
    def _center_dialog(self):
        """居中显示对话框"""
        if self.parentWidget():
            parent_geo = self.parentWidget().geometry()
            parent_center = parent_geo.center()
            
            dialog_width = self.width()
            dialog_height = self.height()
            
            x = parent_center.x() - dialog_width // 2
            y = parent_center.y() - dialog_height // 2
            
            self.move(x, y)
    
    def _on_theme_changed(self, theme_name: str):
        """主题改变事件"""
        self.theme_changed.emit(theme_name)
    
    def _on_theme_applied(self, theme_name: str, success: bool):
        """主题应用事件"""
        if success:
            # 更新对话框自身的样式
            self._update_dialog_style()
    
    def _update_dialog_style(self):
        """更新对话框样式"""
        # 这里不需要额外操作，因为对话框会继承应用程序的样式表
        pass
    
    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        return self.theme_switcher.get_current_theme()
    
    def set_theme(self, theme_name: str) -> bool:
        """设置主题"""
        return self.theme_switcher.set_theme(theme_name)
    
    @staticmethod
    def show_theme_dialog(parent=None) -> Optional[str]:
        """显示主题设置对话框
        
        Returns:
            选择的主题名称，如果取消则返回None
        """
        dialog = ThemeSettingsDialog(parent)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return dialog.get_current_theme()
        return None
