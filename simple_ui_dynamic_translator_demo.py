#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 动态翻译引擎演示

这个脚本演示了动态翻译引擎与SimpleUI的集成
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# PyQt导入
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                              QWidget, QPushButton, QComboBox, QTextEdit, QMenuBar, QMenu, QAction)
    from PyQt5.QtCore import Qt, QTimer
    HAS_QT = True
except ImportError:
    HAS_QT = False
    print("PyQt未安装，无法运行演示")
    sys.exit(1)

# 导入翻译引擎和资源管理器
try:
    # 导入翻译引擎
    from ui.i18n.translation_engine import get_translator, tr, update_language
    
    # 导入资源管理器
    from ui.resource_manager import get_resource_manager
    
    # 导入SimpleUI语言集成
    from simple_ui_language_integration import integrate_language_with_simple_ui

    HAS_TRANSLATION = True
except ImportError as e:
    HAS_TRANSLATION = False
    print(f"导入翻译组件失败: {e}")
    sys.exit(1)

class DynamicTranslatorDemo(QMainWindow):
    """动态翻译引擎演示窗口"""
    
    def __init__(self):
        """初始化演示窗口"""
        super().__init__()
        
        # 基本设置
        self.setWindowTitle(tr("main_window", "title", default="动态翻译引擎演示"))
        self.resize(800, 600)
        
        # 获取资源管理器和翻译器
        self.resource_manager = get_resource_manager()
        self.translator = get_translator()
        
        # 初始化UI
        self.init_ui()
        
        # 集成语言支持
        self.language_helper = integrate_language_with_simple_ui(self)
    
    def init_ui(self):
        """初始化UI"""
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题和说明
        title_label = QLabel(tr("main_window", "welcome_message", default="欢迎使用动态翻译引擎演示"))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        
        description_label = QLabel(tr("test", "description", default="本演示展示了动态翻译引擎和上下文感知翻译功能"))
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 16px; margin-bottom: 20px;")
        
        # 添加到主布局
        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        
        # 语言选择部分
        lang_layout = QHBoxLayout()
        lang_label = QLabel(tr("settings_dialog", "language", default="语言:"))
        self.lang_combo = QComboBox()
        
        # 获取可用语言
        languages = self.resource_manager.get_available_languages()
        for lang in languages:
            self.lang_combo.addItem(f"{lang['native_name']} ({lang['code']})", lang['code'])
        
        # 语言切换按钮
        switch_button = QPushButton(tr("test", "switch_language", default="切换语言"))
        switch_button.clicked.connect(self.switch_language)
        
        # 添加到布局
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addWidget(switch_button)
        main_layout.addLayout(lang_layout)
        
        # 创建翻译测试区域
        self.create_translation_test_area(main_layout)
        
        # 创建上下文测试区域
        self.create_context_test_area(main_layout)
        
        # 创建参数测试区域
        self.create_params_test_area(main_layout)
        
        # 创建菜单
        self.create_menus()
        
        # 更新状态栏
        self.statusBar().showMessage(tr("general", "ready", default="就绪"))
    
    def create_translation_test_area(self, parent_layout):
        """创建翻译测试区域
        
        Args:
            parent_layout: 父布局
        """
        # 创建分组
        group_box = QWidget()
        layout = QVBoxLayout(group_box)
        
        # 标题
        title = QLabel(tr("test", "basic_translation", default="基本翻译测试"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(title)
        
        # 创建常用UI元素翻译测试
        buttons_layout = QHBoxLayout()
        
        # 创建几个按钮用于测试翻译
        buttons = [
            QPushButton(tr("dialog", "ok", default="确定")),
            QPushButton(tr("dialog", "cancel", default="取消")),
            QPushButton(tr("dialog", "apply", default="应用")),
            QPushButton(tr("dialog", "close", default="关闭"))
        ]
        
        # 添加按钮到布局
        for button in buttons:
            buttons_layout.addWidget(button)
        
        layout.addLayout(buttons_layout)
        
        # 添加到父布局
        parent_layout.addWidget(group_box)
    
    def create_context_test_area(self, parent_layout):
        """创建上下文测试区域
        
        Args:
            parent_layout: 父布局
        """
        # 创建分组
        group_box = QWidget()
        layout = QVBoxLayout(group_box)
        
        # 标题
        title = QLabel(tr("test", "context_translation", default="上下文翻译测试"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(title)
        
        # 创建按钮来显示上下文相关翻译
        context_button = QPushButton(tr("test", "show_context", default="显示上下文相关文本"))
        context_button.clicked.connect(self.show_context_examples)
        layout.addWidget(context_button)
        
        # 结果显示
        self.context_result = QTextEdit()
        self.context_result.setReadOnly(True)
        self.context_result.setMinimumHeight(100)
        layout.addWidget(self.context_result)
        
        # 添加到父布局
        parent_layout.addWidget(group_box)
    
    def create_params_test_area(self, parent_layout):
        """创建参数测试区域
        
        Args:
            parent_layout: 父布局
        """
        # 创建分组
        group_box = QWidget()
        layout = QVBoxLayout(group_box)
        
        # 标题
        title = QLabel(tr("test", "params_translation", default="参数翻译测试"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(title)
        
        # 创建按钮来显示带参数的翻译
        params_button = QPushButton(tr("test", "show_params", default="显示带参数的文本"))
        params_button.clicked.connect(self.show_params_examples)
        layout.addWidget(params_button)
        
        # 结果显示
        self.params_result = QTextEdit()
        self.params_result.setReadOnly(True)
        self.params_result.setMinimumHeight(100)
        layout.addWidget(self.params_result)
        
        # 添加到父布局
        parent_layout.addWidget(group_box)
    
    def create_menus(self):
        """创建菜单"""
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu(tr("", "file", default="文件"))
        file_menu.addAction(tr("", "open_project", default="打开"))
        file_menu.addAction(tr("", "save_project", default="保存"))
        file_menu.addSeparator()
        exit_action = QAction(tr("", "exit", default="退出"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu(tr("", "edit", default="编辑"))
        edit_menu.addAction(tr("", "undo", default="撤销"))
        edit_menu.addAction(tr("", "redo", default="重做"))
        
        # 帮助菜单
        help_menu = menubar.addMenu(tr("", "help", default="帮助"))
        about_action = QAction(tr("", "about", default="关于"), self)
        help_menu.addAction(about_action)
    
    def switch_language(self):
        """切换语言"""
        # 获取选中的语言代码
        index = self.lang_combo.currentIndex()
        if index < 0:
            return
        
        lang_code = self.lang_combo.itemData(index)
        if not lang_code:
            return
        
        # 切换语言
        update_language(lang_code)
        
        # 更新UI
        if self.language_helper:
            self.language_helper.update_ui_texts()
        
        # 清空测试结果
        self.context_result.clear()
        self.params_result.clear()
        
        # 显示消息
        self.statusBar().showMessage(tr("general", "language_changed", default=f"语言已切换到: {lang_code}", code=lang_code))
    
    def show_context_examples(self):
        """显示上下文相关文本示例"""
        # 清空结果
        self.context_result.clear()
        
        # 添加示例
        examples = [
            f"默认标题: {tr('', 'title', default='默认标题')}",
            f"窗口标题: {tr('main_window', 'title', default='窗口标题')}",
            f"对话框标题: {tr('dialog', 'title', default='对话框标题')}",
            f"设置标题: {tr('settings_dialog', 'title', default='设置标题')}",
            f"测试标题: {tr('test', 'title', default='测试标题')}"
        ]
        
        # 添加到结果显示
        self.context_result.setPlainText("\n".join(examples))
    
    def show_params_examples(self):
        """显示带参数的文本示例"""
        # 清空结果
        self.params_result.clear()
        
        # 添加示例
        examples = [
            f"文件错误: {tr('errors', 'file_not_found', default='文件未找到: {path}', path='example.mp4')}",
            f"加载失败: {tr('errors', 'failed_to_load', default='无法加载 {name}', name='视频模型')}",
            f"操作失败: {tr('errors', 'operation_failed', default='操作失败: {message}', message='磁盘空间不足')}"
        ]
        
        # 添加到结果显示
        self.params_result.setPlainText("\n".join(examples))

def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建演示窗口
    window = DynamicTranslatorDemo()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
