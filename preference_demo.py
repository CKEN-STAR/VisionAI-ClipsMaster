#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 用户偏好演示

演示用户偏好设置功能，特别是语言偏好的保存和加载。
显示如何利用用户偏好系统实现个性化界面设置。
"""

import os
import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QComboBox, QGroupBox, QTabWidget, QStatusBar
)
from PyQt6.QtCore import Qt, QTranslator, QCoreApplication

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入项目模块
try:
    from ui.i18n import (
        LanguageManager, get_current_language, set_current_language, get_available_languages,
        get_user_preferences, set_language_preference, get_language_preference,
        format_date, format_time, format_number, format_currency
    )
except ImportError:
    # 如果找不到模块，尝试添加项目根目录到路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from ui.i18n import (
        LanguageManager, get_current_language, set_current_language, get_available_languages,
        get_user_preferences, set_language_preference, get_language_preference,
        format_date, format_time, format_number, format_currency
    )


class PreferenceDemoWindow(QMainWindow):
    """用户偏好演示窗口"""
    
    def __init__(self):
        """初始化演示窗口"""
        super().__init__()
        
        # 设置窗口基本属性
        self.setWindowTitle("用户偏好演示")
        self.setMinimumSize(800, 600)
        
        # 创建UI组件
        self.init_ui()
        
        # 应用当前语言
        self.update_language_display()
    
    def init_ui(self):
        """初始化UI组件"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标题标签
        title_label = QLabel("VisionAI-ClipsMaster 用户偏好系统")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建标签页控件
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 创建语言偏好页面
        language_tab = self.create_language_tab()
        tab_widget.addTab(language_tab, "语言偏好")
        
        # 创建其他偏好示例页面（未来扩展）
        other_tab = QWidget()
        other_layout = QVBoxLayout(other_tab)
        other_layout.addWidget(QLabel("这里将展示其他类型的用户偏好设置示例（主题、字体等）"))
        tab_widget.addTab(other_tab, "其他偏好")
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("偏好系统已就绪")
        
        # 创建重置按钮
        reset_button = QPushButton("重置所有偏好")
        reset_button.clicked.connect(self.reset_preferences)
        main_layout.addWidget(reset_button)
    
    def create_language_tab(self):
        """创建语言偏好标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 语言选择组
        language_group = QGroupBox("语言选择")
        language_layout = QVBoxLayout(language_group)
        
        # 获取当前语言和可用语言
        current_lang = get_current_language()
        available_languages = get_available_languages()
        
        # 语言信息显示
        self.lang_info_label = QLabel(f"当前语言: {current_lang}")
        language_layout.addWidget(self.lang_info_label)
        
        # 显示优先级规则
        priority_label = QLabel(
            "语言选择优先级:\n"
            "1. 用户明确选择的语言\n"
            "2. 上次使用的语言\n"
            "3. 系统语言"
        )
        priority_label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        language_layout.addWidget(priority_label)
        
        # 语言选择组合框
        lang_select_layout = QHBoxLayout()
        lang_select_layout.addWidget(QLabel("选择语言:"))
        
        self.language_combo = QComboBox()
        # 添加自动选项
        self.language_combo.addItem("自动 (系统语言)", "auto")
        
        # 添加所有可用语言
        for lang_code, lang_info in available_languages.items():
            self.language_combo.addItem(
                f"{lang_info['native_name']} ({lang_info['name']})",
                lang_code
            )
            # 设置当前选择的语言
            if lang_code == current_lang:
                self.language_combo.setCurrentIndex(self.language_combo.count() - 1)
        
        lang_select_layout.addWidget(self.language_combo)
        
        # 应用语言按钮
        apply_button = QPushButton("应用")
        apply_button.clicked.connect(self.apply_language)
        lang_select_layout.addWidget(apply_button)
        
        language_layout.addLayout(lang_select_layout)
        layout.addWidget(language_group)
        
        # 格式化示例组
        format_group = QGroupBox("本地化格式示例")
        format_layout = QVBoxLayout(format_group)
        
        # 添加各种格式化示例
        import datetime
        now = datetime.datetime.now()
        
        self.date_label = QLabel(f"日期格式: {format_date(now)}")
        self.time_label = QLabel(f"时间格式: {format_time(now)}")
        self.number_label = QLabel(f"数字格式: {format_number(1234567.89)}")
        self.currency_label = QLabel(f"货币格式: {format_currency(1234567.89, 'USD')}")
        
        format_layout.addWidget(self.date_label)
        format_layout.addWidget(self.time_label)
        format_layout.addWidget(self.number_label)
        format_layout.addWidget(self.currency_label)
        
        layout.addWidget(format_group)
        
        # 用户偏好信息组
        pref_group = QGroupBox("偏好存储信息")
        pref_layout = QVBoxLayout(pref_group)
        
        # 尝试读取和显示偏好文件内容
        try:
            self.pref_content_label = QLabel("偏好文件内容将显示在这里")
            self.update_pref_content()
            pref_layout.addWidget(self.pref_content_label)
        except Exception as e:
            pref_layout.addWidget(QLabel(f"无法读取偏好文件: {e}"))
        
        pref_group.setLayout(pref_layout)
        layout.addWidget(pref_group)
        
        return tab
    
    def apply_language(self):
        """应用选择的语言"""
        selected_lang = self.language_combo.currentData()
        if selected_lang:
            # 设置语言
            logger.info(f"设置语言: {selected_lang}")
            success = set_current_language(selected_lang)
            
            if success:
                self.status_bar.showMessage(f"语言已更改为: {selected_lang}")
            else:
                self.status_bar.showMessage(f"语言更改失败: {selected_lang}")
            
            # 更新UI
            self.update_language_display()
            self.update_pref_content()
    
    def update_language_display(self):
        """更新语言显示信息"""
        current_lang = get_current_language()
        self.lang_info_label.setText(f"当前语言: {current_lang}")
        
        # 更新格式化示例
        import datetime
        now = datetime.datetime.now()
        
        self.date_label.setText(f"日期格式: {format_date(now)}")
        self.time_label.setText(f"时间格式: {format_time(now)}")
        self.number_label.setText(f"数字格式: {format_number(1234567.89)}")
        self.currency_label.setText(f"货币格式: {format_currency(1234567.89, 'USD')}")
    
    def update_pref_content(self):
        """更新偏好文件内容显示"""
        try:
            # 尝试读取语言偏好文件
            import json
            lang_pref_path = "user_config/lang_pref.json"
            main_pref_path = "user_config/preferences.json"
            
            content = "语言偏好文件 (lang_pref.json):\n"
            
            if os.path.exists(lang_pref_path):
                with open(lang_pref_path, 'r', encoding='utf-8') as f:
                    lang_pref = json.load(f)
                content += json.dumps(lang_pref, ensure_ascii=False, indent=2)
            else:
                content += "文件不存在"
            
            content += "\n\n主偏好文件 (preferences.json):\n"
            
            if os.path.exists(main_pref_path):
                with open(main_pref_path, 'r', encoding='utf-8') as f:
                    main_pref = json.load(f)
                content += json.dumps(main_pref, ensure_ascii=False, indent=2)
            else:
                content += "文件不存在"
            
            self.pref_content_label.setText(content)
            self.pref_content_label.setStyleSheet("font-family: monospace; background-color: #f5f5f5; padding: 10px;")
        
        except Exception as e:
            self.pref_content_label.setText(f"无法读取偏好文件: {e}")
    
    def reset_preferences(self):
        """重置所有偏好设置"""
        try:
            # 删除偏好文件
            lang_pref_path = "user_config/lang_pref.json"
            main_pref_path = "user_config/preferences.json"
            
            if os.path.exists(lang_pref_path):
                os.remove(lang_pref_path)
            
            if os.path.exists(main_pref_path):
                os.remove(main_pref_path)
            
            # 重新加载偏好
            set_current_language("auto")
            self.update_language_display()
            self.update_pref_content()
            
            # 更新语言选择框
            self.language_combo.setCurrentIndex(0)  # 设置为"自动"
            
            self.status_bar.showMessage("已重置所有偏好设置")
        
        except Exception as e:
            self.status_bar.showMessage(f"重置偏好设置失败: {e}")


def ensure_config_dirs():
    """确保配置目录存在"""
    config_dir = "user_config"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
        print(f"创建配置目录: {config_dir}")


if __name__ == "__main__":
    # 确保配置目录存在
    ensure_config_dirs()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    window = PreferenceDemoWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec()) 