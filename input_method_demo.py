#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 输入法支持演示程序
演示如何使用输入法支持模块，为多语言文本输入提供支持
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QTextEdit, QLineEdit, QPushButton, QGroupBox,
    QTabWidget, QGridLayout
)
from PyQt5.QtCore import Qt, QTranslator, QLocale
from PyQt5.QtGui import QFont

# 确保可以导入ui模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入输入法支持模块
try:
    from ui.i18n import (
        get_input_method_support, configure_widget_for_language,
        set_input_method_language, get_available_languages
    )
except ImportError as e:
    print(f"无法导入输入法支持模块: {e}")
    sys.exit(1)

class InputMethodDemo(QMainWindow):
    """输入法支持演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster 输入法支持演示")
        self.resize(800, 600)
        
        # 获取输入法支持实例
        self.input_method_support = get_input_method_support()
        
        # 创建UI
        self._setup_ui()
        
        # 设置信号连接
        self._setup_connections()
        
        # 初始化语言选择
        self._populate_language_combo()
        
    def _setup_ui(self):
        """设置UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部语言选择区域
        language_layout = QHBoxLayout()
        language_label = QLabel("选择输入法语言:")
        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(200)
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch(1)
        
        main_layout.addLayout(language_layout)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 简单输入选项卡
        simple_input_tab = self._create_simple_input_tab()
        self.tab_widget.addTab(simple_input_tab, "基本输入")
        
        # 高级输入选项卡
        advanced_input_tab = self._create_advanced_input_tab()
        self.tab_widget.addTab(advanced_input_tab, "多语言输入")
        
        # 文本方向选项卡
        text_direction_tab = self._create_text_direction_tab()
        self.tab_widget.addTab(text_direction_tab, "文本方向")
        
        main_layout.addWidget(self.tab_widget)
        
        # 底部状态区域
        status_layout = QHBoxLayout()
        self.status_label = QLabel("当前状态: 就绪")
        status_layout.addWidget(self.status_label)
        
        main_layout.addLayout(status_layout)
        
    def _create_simple_input_tab(self):
        """创建简单输入选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 单行输入
        line_input_group = QGroupBox("单行输入")
        line_layout = QVBoxLayout(line_input_group)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("在此输入文本...")
        line_layout.addWidget(self.line_edit)
        
        # 启用输入法支持
        configure_widget_for_language(self.line_edit, "en_US")
        
        layout.addWidget(line_input_group)
        
        # 多行输入
        text_input_group = QGroupBox("多行输入")
        text_layout = QVBoxLayout(text_input_group)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此输入多行文本...")
        text_layout.addWidget(self.text_edit)
        
        # 启用输入法支持
        configure_widget_for_language(self.text_edit, "en_US")
        
        layout.addWidget(text_input_group)
        
        return tab
        
    def _create_advanced_input_tab(self):
        """创建高级输入选项卡"""
        tab = QWidget()
        layout = QGridLayout(tab)
        
        # 创建各种语言的文本输入区域
        self.language_text_edits = {}
        
        languages = [
            ("zh_CN", "中文 (简体)"),
            ("ja_JP", "日语"),
            ("ko_KR", "韩语"),
            ("ar_SA", "阿拉伯语"),
            ("hi_IN", "印地语"),
            ("th_TH", "泰语")
        ]
        
        for i, (lang_code, lang_name) in enumerate(languages):
            group = QGroupBox(lang_name)
            group_layout = QVBoxLayout(group)
            
            text_edit = QTextEdit()
            text_edit.setPlaceholderText(f"在此输入{lang_name}...")
            text_edit.setMinimumHeight(100)
            
            # 配置文本编辑器以支持此语言
            configure_widget_for_language(text_edit, lang_code)
            
            group_layout.addWidget(text_edit)
            self.language_text_edits[lang_code] = text_edit
            
            # 将组添加到网格布局
            row, col = i // 2, i % 2
            layout.addWidget(group, row, col)
        
        return tab
        
    def _create_text_direction_tab(self):
        """创建文本方向选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # RTL布局组
        rtl_group = QGroupBox("右到左文本方向 (RTL)")
        rtl_layout = QVBoxLayout(rtl_group)
        
        self.rtl_text_edit = QTextEdit()
        self.rtl_text_edit.setPlaceholderText("在此输入阿拉伯语或希伯来语...")
        rtl_layout.addWidget(self.rtl_text_edit)
        
        # 配置为阿拉伯语
        configure_widget_for_language(self.rtl_text_edit, "ar_SA")
        
        layout.addWidget(rtl_group)
        
        # LTR布局组
        ltr_group = QGroupBox("左到右文本方向 (LTR)")
        ltr_layout = QVBoxLayout(ltr_group)
        
        self.ltr_text_edit = QTextEdit()
        self.ltr_text_edit.setPlaceholderText("在此输入英语或其他拉丁文本...")
        ltr_layout.addWidget(self.ltr_text_edit)
        
        # 配置为英语
        configure_widget_for_language(self.ltr_text_edit, "en_US")
        
        layout.addWidget(ltr_group)
        
        # 混合方向组
        mixed_group = QGroupBox("混合文本方向")
        mixed_layout = QVBoxLayout(mixed_group)
        
        self.mixed_text_edit = QTextEdit()
        self.mixed_text_edit.setPlaceholderText("在此输入混合方向文本...")
        mixed_layout.addWidget(self.mixed_text_edit)
        
        configure_widget_for_language(self.mixed_text_edit, "en_US")
        
        layout.addWidget(mixed_group)
        
        return tab
        
    def _setup_connections(self):
        """设置信号连接"""
        # 语言选择变更时
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        
        # 监听输入法变更信号
        self.input_method_support.input_method_changed.connect(self._on_input_method_changed)
        
    def _populate_language_combo(self):
        """填充语言下拉框"""
        # 使用内置列表
        available_languages = [
            ("en_US", "English (US)"),
            ("zh_CN", "中文 (简体)"),
            ("ja_JP", "日本語"),
            ("ko_KR", "한국어"),
            ("ar_SA", "العربية"),
            ("hi_IN", "हिन्दी"),
            ("bn_BD", "বাংলা"),
            ("th_TH", "ไทย"),
            ("fr_FR", "Français"),
            ("de_DE", "Deutsch"),
            ("es_ES", "Español"),
            ("ru_RU", "Русский"),
            ("pt_BR", "Português")
        ]
        
        # 添加到下拉框
        for lang_code, lang_name in available_languages:
            self.language_combo.addItem(lang_name, lang_code)
            
    def _on_language_changed(self, index):
        """语言选择变更处理"""
        if index < 0:
            return
            
        # 获取选中的语言代码
        lang_code = self.language_combo.itemData(index)
        
        # 设置输入法语言
        set_input_method_language(lang_code)
        
        # 更新状态
        self.status_label.setText(f"当前输入法: {self.language_combo.currentText()} ({lang_code})")
        
        # 重新配置当前活动的文本编辑器
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:  # 简单输入选项卡
            configure_widget_for_language(self.line_edit, lang_code)
            configure_widget_for_language(self.text_edit, lang_code)
        
    def _on_input_method_changed(self, language):
        """输入法变更处理"""
        # 更新状态
        self.status_label.setText(f"输入法已变更: {language}")
        
        # 尝试在下拉框中选择对应的语言
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == language:
                self.language_combo.setCurrentIndex(i)
                break


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    window = InputMethodDemo()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 