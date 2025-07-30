#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 主题切换器组件
提供用户友好的主题切换界面
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QGroupBox, QButtonGroup, QRadioButton,
    QFrame, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor

class ThemePreviewWidget(QWidget):
    """主题预览小部件"""
    
    def __init__(self, theme_name: str, theme_config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.theme_config = theme_config
        self.setFixedSize(120, 80)

        # 兼容不同的主题配置格式
        if hasattr(theme_config, 'display_name'):
            display_name = theme_config.display_name
            description = getattr(theme_config, 'description', '')
        elif isinstance(theme_config, dict):
            display_name = theme_config.get('display_name', theme_name)
            description = theme_config.get('description', '')
        else:
            display_name = theme_name
            description = ''

        self.setToolTip(f"{display_name}\n{description}")
        
    def paintEvent(self, event):
        """绘制主题预览"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取主题颜色
        colors = self.theme_config.get('colors', {})
        bg_color = QColor(colors.get('background', '#FFFFFF'))
        surface_color = QColor(colors.get('surface', '#F5F5F5'))
        primary_color = QColor(colors.get('primary', '#2196F3'))
        text_color = QColor(colors.get('text_primary', '#000000'))
        
        # 绘制背景
        painter.fillRect(self.rect(), bg_color)
        
        # 绘制表面区域
        surface_rect = self.rect().adjusted(5, 5, -5, -5)
        painter.fillRect(surface_rect, surface_color)
        
        # 绘制主色调条
        primary_rect = surface_rect.adjusted(5, 5, -5, -50)
        painter.fillRect(primary_rect, primary_color)
        
        # 绘制文本示例
        painter.setPen(text_color)
        painter.setFont(QFont("Microsoft YaHei", 8))
        text_rect = surface_rect.adjusted(5, 25, -5, -5)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Aa")
        
        # 绘制边框
        painter.setPen(QColor(colors.get('border', '#E0E0E0')))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

class ThemeSwitcher(QWidget):
    """主题切换器组件"""
    
    # 信号定义
    theme_changed = pyqtSignal(str)  # 主题名称
    theme_applied = pyqtSignal(str, bool)  # 主题名称, 是否成功
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = "default"
        self.themes = {}
        self.theme_system = None
        
        # 初始化主题系统
        self._init_theme_system()
        
        # 初始化UI
        self._init_ui()
        
        # 加载当前主题设置
        self._load_current_theme()
        
    def _init_theme_system(self):
        """初始化主题系统"""
        try:
            # 尝试导入高级主题系统
            from ui.themes.advanced_theme_system import get_theme_system
            self.theme_system = get_theme_system()
            self.themes = self.theme_system.themes
            print("[OK] 高级主题系统已加载")
        except ImportError:
            try:
                # 回退到增强样式管理器
                from src.ui.enhanced_style_manager import EnhancedStyleManager
                self.theme_system = EnhancedStyleManager()
                self.themes = self.theme_system.themes
                print("[OK] 增强样式管理器已加载")
            except ImportError:
                # 使用内置主题
                self._init_builtin_themes()
                print("[WARN] 使用内置主题系统")
    
    def _init_builtin_themes(self):
        """初始化内置主题"""
        self.themes = {
            "default": {
                "display_name": "默认主题",
                "description": "清新的浅色主题，适合日常使用",
                "colors": {
                    "background": "#FFFFFF",
                    "surface": "#F5F5F5",
                    "primary": "#2196F3",
                    "text_primary": "#212121",
                    "border": "#E0E0E0"
                }
            },
            "dark": {
                "display_name": "深色主题",
                "description": "护眼的深色主题，适合夜间使用",
                "colors": {
                    "background": "#121212",
                    "surface": "#1E1E1E",
                    "primary": "#1976D2",
                    "text_primary": "#FFFFFF",
                    "border": "#404040"
                }
            },
            "high_contrast": {
                "display_name": "高对比度",
                "description": "高对比度主题，提升可访问性",
                "colors": {
                    "background": "#000000",
                    "surface": "#000000",
                    "primary": "#FFFFFF",
                    "text_primary": "#FFFFFF",
                    "border": "#FFFFFF"
                }
            }
        }
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 嵌入式显示时减少边距
        layout.setSpacing(15)

        # 标题（嵌入式显示时不需要居中）
        title_label = QLabel("🎨 界面主题")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 主题选择组
        theme_group = QGroupBox("选择主题")
        theme_layout = QVBoxLayout(theme_group)
        
        # 主题选择器（下拉框方式）
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("当前主题:"))

        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumHeight(35)
        for theme_name, theme_config in self.themes.items():
            # 兼容不同的主题配置格式
            if hasattr(theme_config, 'display_name'):
                display_name = theme_config.display_name
            elif isinstance(theme_config, dict):
                display_name = theme_config.get('display_name', theme_name)
            else:
                display_name = theme_name
            self.theme_combo.addItem(display_name, theme_name)
        
        self.theme_combo.currentTextChanged.connect(self._on_theme_combo_changed)
        selector_layout.addWidget(self.theme_combo)
        
        theme_layout.addLayout(selector_layout)
        
        # 主题预览区域
        preview_label = QLabel("主题预览:")
        preview_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        theme_layout.addWidget(preview_label)
        
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(10)
        
        # 创建主题预览小部件
        self.preview_widgets = {}
        for theme_name, theme_config in self.themes.items():
            # 转换主题配置为字典格式以兼容预览组件
            if hasattr(theme_config, '__dict__'):
                # 如果是对象，转换为字典
                config_dict = {
                    'display_name': getattr(theme_config, 'display_name', theme_name),
                    'description': getattr(theme_config, 'description', ''),
                    'colors': getattr(theme_config, 'colors', {})
                }
                # 如果colors也是对象，转换为字典
                if hasattr(config_dict['colors'], '__dict__'):
                    colors_obj = config_dict['colors']
                    config_dict['colors'] = {
                        'background': getattr(colors_obj, 'background', '#FFFFFF'),
                        'surface': getattr(colors_obj, 'surface', '#F5F5F5'),
                        'primary': getattr(colors_obj, 'primary', '#2196F3'),
                        'text_primary': getattr(colors_obj, 'text_primary', '#000000'),
                        'border': getattr(colors_obj, 'border', '#E0E0E0')
                    }
            else:
                config_dict = theme_config

            preview_widget = ThemePreviewWidget(theme_name, config_dict)
            preview_widget.mousePressEvent = lambda event, name=theme_name: self._select_theme_from_preview(name)
            self.preview_widgets[theme_name] = preview_widget
            preview_layout.addWidget(preview_widget)
        
        preview_layout.addStretch()
        theme_layout.addLayout(preview_layout)
        
        layout.addWidget(theme_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("应用主题")
        self.apply_button.setMinimumHeight(35)
        self.apply_button.clicked.connect(self._apply_current_theme)
        button_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.setMinimumHeight(35)
        self.reset_button.clicked.connect(self._reset_to_default)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _on_theme_combo_changed(self, text):
        """主题下拉框改变事件"""
        # 找到对应的主题名称
        for theme_name, theme_config in self.themes.items():
            # 兼容不同的主题配置格式
            if hasattr(theme_config, 'display_name'):
                display_name = theme_config.display_name
            elif isinstance(theme_config, dict):
                display_name = theme_config.get('display_name', theme_name)
            else:
                display_name = theme_name

            if display_name == text:
                self.current_theme = theme_name
                self._update_preview_selection()
                break
    
    def _select_theme_from_preview(self, theme_name):
        """从预览选择主题"""
        self.current_theme = theme_name

        # 更新下拉框
        theme_config = self.themes.get(theme_name, {})

        # 兼容不同的主题配置格式
        if hasattr(theme_config, 'display_name'):
            display_name = theme_config.display_name
        elif isinstance(theme_config, dict):
            display_name = theme_config.get('display_name', theme_name)
        else:
            display_name = theme_name

        index = self.theme_combo.findText(display_name)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self._update_preview_selection()
    
    def _update_preview_selection(self):
        """更新预览选择状态"""
        for theme_name, widget in self.preview_widgets.items():
            if theme_name == self.current_theme:
                widget.setStyleSheet("border: 2px solid #2196F3; border-radius: 4px;")
            else:
                widget.setStyleSheet("border: 1px solid #E0E0E0; border-radius: 4px;")
    
    def _apply_current_theme(self):
        """应用当前选择的主题"""
        if not self.current_theme:
            return
        
        self.status_label.setText("正在应用主题...")
        self.apply_button.setEnabled(False)
        
        # 延迟应用，给用户反馈
        QTimer.singleShot(100, self._do_apply_theme)
    
    def _do_apply_theme(self):
        """执行主题应用"""
        success = False

        try:
            # 首先尝试通过主窗口应用主题
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'apply_theme_to_window'):
                success = main_window.apply_theme_to_window(self.current_theme)
            elif self.theme_system and hasattr(self.theme_system, 'apply_theme'):
                success = self.theme_system.apply_theme(self.current_theme)
            else:
                # 使用内置应用方法
                success = self._apply_builtin_theme(self.current_theme)

            if success:
                # 获取主题显示名称
                theme_config = self.themes[self.current_theme]
                if hasattr(theme_config, 'display_name'):
                    display_name = theme_config.display_name
                elif isinstance(theme_config, dict):
                    display_name = theme_config.get('display_name', self.current_theme)
                else:
                    display_name = self.current_theme

                self.status_label.setText(f"主题 '{display_name}' 已应用")
                self._save_current_theme()
                self.theme_changed.emit(self.current_theme)
                self.theme_applied.emit(self.current_theme, True)

                # 显示成功消息
                print(f"[OK] 主题切换成功: {display_name}")
            else:
                self.status_label.setText("主题应用失败")
                self.theme_applied.emit(self.current_theme, False)
                print(f"[ERROR] 主题切换失败: {self.current_theme}")

        except Exception as e:
            error_msg = f"主题应用出错: {str(e)}"
            self.status_label.setText(error_msg)
            self.theme_applied.emit(self.current_theme, False)
            print(f"[ERROR] {error_msg}")

        finally:
            self.apply_button.setEnabled(True)
    
    def _apply_builtin_theme(self, theme_name: str) -> bool:
        """应用内置主题 - 增强版本"""
        if theme_name not in self.themes:
            return False

        try:
            theme_config = self.themes[theme_name]

            # 兼容不同的主题配置格式
            if hasattr(theme_config, 'colors'):
                # ThemeConfig对象
                colors = {
                    'background': theme_config.colors.background,
                    'surface': theme_config.colors.surface,
                    'primary': theme_config.colors.primary,
                    'text_primary': theme_config.colors.text_primary,
                    'border': getattr(theme_config.colors, 'border', '#E0E0E0')
                }
            elif isinstance(theme_config, dict):
                # 字典格式
                colors = theme_config.get('colors', {})
            else:
                # 未知格式，使用默认颜色
                colors = {
                    'background': '#FFFFFF',
                    'surface': '#F5F5F5',
                    'primary': '#2196F3',
                    'text_primary': '#000000',
                    'border': '#E0E0E0'
                }

            # 生成完整的主题样式表
            stylesheet = self._generate_complete_stylesheet(colors)

            # 应用到主窗口而不是整个应用程序
            main_window = self._find_main_window()
            if main_window:
                # 保存原始样式表
                if not hasattr(main_window, '_original_stylesheet'):
                    main_window._original_stylesheet = main_window.styleSheet()

                # 应用新主题样式
                main_window.setStyleSheet(stylesheet)
                print(f"[OK] 主题已应用到主窗口: {theme_name}")
                return True
            else:
                # 备用方案：应用到整个应用程序
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(stylesheet)
                    print(f"[OK] 主题已应用到应用程序: {theme_name}")
                    return True

            return False

        except Exception as e:
            print(f"[ERROR] 应用内置主题失败: {e}")
            return False

    def _find_main_window(self):
        """查找主窗口"""
        try:
            # 从当前组件向上查找主窗口
            widget = self
            while widget:
                if hasattr(widget, 'tabs') and hasattr(widget, 'setup_ui_style'):
                    return widget
                widget = widget.parent()

            # 备用方案：查找所有顶级窗口
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if hasattr(widget, 'tabs') and hasattr(widget, 'setup_ui_style'):
                        return widget

            return None
        except Exception as e:
            print(f"[WARN] 查找主窗口失败: {e}")
            return None

    def _generate_complete_stylesheet(self, colors):
        """生成完整的主题样式表"""
        background = colors.get('background', '#FFFFFF')
        surface = colors.get('surface', '#F5F5F5')
        primary = colors.get('primary', '#2196F3')
        text_primary = colors.get('text_primary', '#000000')
        border = colors.get('border', '#E0E0E0')

        # 生成与现有样式兼容的完整样式表
        stylesheet = f"""
        /* 主窗口样式 */
        QMainWindow {{
            background-color: {background};
            color: {text_primary};
        }}

        /* 基础组件样式 */
        QWidget {{
            background-color: {background};
            color: {text_primary};
        }}

        /* 按钮样式 */
        QPushButton {{
            background-color: {primary};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {primary};
            border: 2px solid {primary};
        }}

        QPushButton:pressed {{
            background-color: {primary};
            border: 2px solid {border};
        }}

        /* 输入框样式 */
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {surface};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 4px 8px;
        }}

        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 2px solid {primary};
        }}

        /* 标签页样式 */
        QTabWidget::pane {{
            border: 1px solid {border};
            background-color: {surface};
        }}

        QTabBar::tab {{
            background-color: {surface};
            color: {text_primary};
            border: 1px solid {border};
            padding: 8px 16px;
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {primary};
            color: white;
        }}

        QTabBar::tab:hover {{
            background-color: {primary};
            color: white;
        }}

        /* 列表和表格样式 */
        QListWidget, QTableWidget {{
            background-color: {surface};
            color: {text_primary};
            border: 1px solid {border};
            alternate-background-color: {background};
        }}

        /* 分组框样式 */
        QGroupBox {{
            color: {text_primary};
            border: 2px solid {border};
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}

        /* 进度条样式 */
        QProgressBar {{
            border: 2px solid {border};
            border-radius: 5px;
            background-color: {surface};
            color: {text_primary};
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {primary};
            border-radius: 3px;
        }}
        """

        return stylesheet
    
    def _reset_to_default(self):
        """重置为默认主题"""
        self.current_theme = "default"
        
        # 更新UI
        theme_config = self.themes.get("default", {})

        # 兼容不同的主题配置格式
        if hasattr(theme_config, 'display_name'):
            display_name = theme_config.display_name
        elif isinstance(theme_config, dict):
            display_name = theme_config.get('display_name', "default")
        else:
            display_name = "default"

        index = self.theme_combo.findText(display_name)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self._update_preview_selection()
        self._apply_current_theme()
    
    def _load_current_theme(self):
        """加载当前主题设置"""
        try:
            config_file = Path("config/ui_settings.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    saved_theme = config.get('current_theme', 'default')
                    if saved_theme in self.themes:
                        self.current_theme = saved_theme
                        
                        # 更新UI
                        theme_config = self.themes.get(saved_theme, {})

                        # 兼容不同的主题配置格式
                        if hasattr(theme_config, 'display_name'):
                            display_name = theme_config.display_name
                        elif isinstance(theme_config, dict):
                            display_name = theme_config.get('display_name', saved_theme)
                        else:
                            display_name = saved_theme

                        index = self.theme_combo.findText(display_name)
                        if index >= 0:
                            self.theme_combo.setCurrentIndex(index)
                        
                        self._update_preview_selection()
        except Exception as e:
            print(f"[WARN] 加载主题设置失败: {e}")
    
    def _save_current_theme(self):
        """保存当前主题设置"""
        try:
            config_file = Path("config/ui_settings.json")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有配置
            config = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新主题设置
            config['current_theme'] = self.current_theme
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[WARN] 保存主题设置失败: {e}")
    
    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        return self.current_theme
    
    def set_theme(self, theme_name: str) -> bool:
        """设置主题"""
        if theme_name not in self.themes:
            return False
        
        self.current_theme = theme_name
        
        # 更新UI
        theme_config = self.themes.get(theme_name, {})

        # 兼容不同的主题配置格式
        if hasattr(theme_config, 'display_name'):
            display_name = theme_config.display_name
        elif isinstance(theme_config, dict):
            display_name = theme_config.get('display_name', theme_name)
        else:
            display_name = theme_name

        index = self.theme_combo.findText(display_name)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self._update_preview_selection()
        return True
