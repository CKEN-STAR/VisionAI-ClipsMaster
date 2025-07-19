#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 实时切换系统演示

此脚本演示了实时语言切换系统的使用方法和效果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QTextEdit, 
    QTabWidget, QGroupBox, QFrame, QSplitter, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

# 导入实时切换系统
try:
    from ui.i18n.live_switcher import get_language_switcher, switch_language
except ImportError:
    from ui.i18n.language_manager import get_language_manager
    
    # 临时实现
    class TemporaryLanguageSwitcher:
        def __init__(self):
            self.languageChanged = pyqtSignal(str)
            self.lang_manager = get_language_manager()
            
        def switch_language(self, lang_code):
            return self.lang_manager.switch_language(lang_code)
            
        @property
        def current_language(self):
            return self.lang_manager.current_ui_language
            
        def get_supported_languages(self):
            langs = {}
            for lang in self.lang_manager.get_ui_languages():
                langs[lang['code']] = lang
            return langs
            
    _temp_switcher = None
    
    def get_language_switcher():
        global _temp_switcher
        if _temp_switcher is None:
            _temp_switcher = TemporaryLanguageSwitcher()
        return _temp_switcher
        
    def switch_language(lang_code):
        return get_language_switcher().switch_language(lang_code)

# 导入简单翻译函数
try:
    from ui.i18n.translation_engine import tr
except ImportError:
    def tr(context, key, default=None, **kwargs):
        if default:
            if kwargs:
                try:
                    return default.format(**kwargs)
                except:
                    pass
            return default
        return f"{context}.{key}"

class LanguageSwitcherCombo(QFrame):
    """语言切换下拉框组件"""
    
    language_switched = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LanguageSwitcherCombo")
        self.setup_ui()
    
    def setup_ui(self):
        # 设置样式
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("语言切换器")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 语言选择下拉框
        self.lang_combo = QComboBox()
        
        # 添加语言选项
        self.lang_combo.addItem("简体中文", "zh_CN")
        self.lang_combo.addItem("English (US)", "en_US")
        self.lang_combo.addItem("日本語", "ja_JP")
        
        layout.addWidget(self.lang_combo)
        
        # 应用按钮
        self.apply_button = QPushButton("应用")
        layout.addWidget(self.apply_button)
        
        # 连接信号
        self.apply_button.clicked.connect(self.apply_language)
    
    def apply_language(self):
        """应用所选语言"""
        index = self.lang_combo.currentIndex()
        if index >= 0:
            lang_code = self.lang_combo.itemData(index)
            if switch_language(lang_code):
                self.language_switched.emit(lang_code)

class LanguageButtons(QWidget):
    """语言按钮组组件"""
    
    language_switched = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # 主布局
        layout = QHBoxLayout(self)
        
        # 创建按钮
        self.zh_button = QPushButton("中文")
        self.zh_button.clicked.connect(lambda: self.switch_language("zh_CN"))
        
        self.en_button = QPushButton("English")
        self.en_button.clicked.connect(lambda: self.switch_language("en_US"))
        
        self.ja_button = QPushButton("日本語")
        self.ja_button.clicked.connect(lambda: self.switch_language("ja_JP"))
        
        # 添加到布局
        layout.addWidget(self.zh_button)
        layout.addWidget(self.en_button)
        layout.addWidget(self.ja_button)
    
    def switch_language(self, lang_code):
        """切换语言"""
        if switch_language(lang_code):
            self.language_switched.emit(lang_code)

class TranslatableContent(QGroupBox):
    """可翻译内容演示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("可翻译内容")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建标签
        self.title_label = QLabel("实时语言切换系统")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        self.desc_label = QLabel("本演示展示了VisionAI-ClipsMaster中的实时语言切换系统功能")
        layout.addWidget(self.desc_label)
        
        # 创建按钮
        self.button = QPushButton("刷新")
        self.button.clicked.connect(self.refresh)
        layout.addWidget(self.button)
    
    def refresh(self):
        """刷新翻译"""
        self.retranslate_ui()
    
    def retranslate_ui(self):
        """重新翻译"""
        self.title_label.setText(tr("demo", "title", default="实时语言切换系统"))
        self.desc_label.setText(tr("demo", "description", default="本演示展示了VisionAI-ClipsMaster中的实时语言切换系统功能"))
        self.button.setText(tr("demo", "refresh", default="刷新"))

class LiveSwitcherDemoApp(QMainWindow):
    """实时语言切换系统演示"""
    
    def __init__(self):
        """初始化演示应用"""
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster - 实时切换系统演示")
        self.resize(800, 600)
        
        # 初始化UI
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("VisionAI-ClipsMaster 实时切换系统演示")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧语言切换面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 下拉框切换
        self.combo_switcher = LanguageSwitcherCombo()
        left_layout.addWidget(self.combo_switcher)
        
        # 按钮切换
        self.button_switcher = LanguageButtons()
        left_layout.addWidget(self.button_switcher)
        
        # 添加弹性空间
        left_layout.addStretch(1)
        
        # 右侧内容
        self.content = TranslatableContent()
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(self.content)
        
        # 设置分割器比例
        splitter.setSizes([300, 500])
        
        # 连接信号
        self.combo_switcher.language_switched.connect(self.on_language_switched)
        self.button_switcher.language_switched.connect(self.on_language_switched)
    
    def on_language_switched(self, lang_code):
        """当语言切换时"""
        self.content.retranslate_ui()

def main():
    """应用入口"""
    app = QApplication(sys.argv)
    window = LiveSwitcherDemoApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 