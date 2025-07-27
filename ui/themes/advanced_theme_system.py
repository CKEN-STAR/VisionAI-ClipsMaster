"""
高级主题系统
提供多种预设主题和自定义主题功能
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

@dataclass
class ThemeColors:
    """主题颜色配置"""
    primary: str = "#2196F3"
    secondary: str = "#FFC107"
    success: str = "#4CAF50"
    warning: str = "#FF9800"
    error: str = "#F44336"
    info: str = "#00BCD4"
    
    background: str = "#FFFFFF"
    surface: str = "#F5F5F5"
    card: str = "#FFFFFF"
    
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
    text_disabled: str = "#BDBDBD"
    
    border: str = "#E0E0E0"
    divider: str = "#EEEEEE"
    shadow: str = "rgba(0, 0, 0, 0.1)"

@dataclass
class ThemeConfig:
    """主题配置"""
    name: str
    display_name: str
    description: str
    colors: ThemeColors
    is_dark: bool = False
    font_family: str = "Microsoft YaHei UI"
    font_size: int = 9
    border_radius: int = 4
    animation_duration: int = 300

class AdvancedThemeSystem(QObject):
    """高级主题系统"""
    
    theme_changed = pyqtSignal(str)  # 主题名称
    theme_loaded = pyqtSignal(dict)  # 主题配置
    
    def __init__(self):
        super().__init__()
        self.themes: Dict[str, ThemeConfig] = {}
        self.current_theme = "default"
        self.custom_themes_dir = "themes/custom"
        
        # 确保自定义主题目录存在
        os.makedirs(self.custom_themes_dir, exist_ok=True)
        
        # 初始化预设主题
        self._init_preset_themes()
        
        # 加载自定义主题
        self._load_custom_themes()
    
    def _init_preset_themes(self):
        """初始化预设主题"""
        # 默认主题（浅色）
        default_colors = ThemeColors()
        self.themes["default"] = ThemeConfig(
            name="default",
            display_name="默认主题",
            description="清新的浅色主题，适合日常使用",
            colors=default_colors,
            is_dark=False
        )
        
        # 深色主题
        dark_colors = ThemeColors(
            primary="#1976D2",
            secondary="#FFA000",
            success="#388E3C",
            warning="#F57C00",
            error="#D32F2F",
            info="#0097A7",
            
            background="#121212",
            surface="#1E1E1E",
            card="#2D2D2D",
            
            text_primary="#FFFFFF",
            text_secondary="#B0B0B0",
            text_disabled="#666666",
            
            border="#404040",
            divider="#333333",
            shadow="rgba(0, 0, 0, 0.3)"
        )
        self.themes["dark"] = ThemeConfig(
            name="dark",
            display_name="深色主题",
            description="护眼的深色主题，适合夜间使用",
            colors=dark_colors,
            is_dark=True
        )
        
        # 高对比度主题
        high_contrast_colors = ThemeColors(
            primary="#0066CC",
            secondary="#FF6600",
            success="#009900",
            warning="#FF9900",
            error="#CC0000",
            info="#0099CC",
            
            background="#FFFFFF",
            surface="#F8F8F8",
            card="#FFFFFF",
            
            text_primary="#000000",
            text_secondary="#333333",
            text_disabled="#999999",
            
            border="#000000",
            divider="#CCCCCC",
            shadow="rgba(0, 0, 0, 0.2)"
        )
        self.themes["high_contrast"] = ThemeConfig(
            name="high_contrast",
            display_name="高对比度",
            description="高对比度主题，提升可读性",
            colors=high_contrast_colors,
            is_dark=False,
            font_size=10
        )
        
        # 蓝色主题
        blue_colors = ThemeColors(
            primary="#1565C0",
            secondary="#FFB300",
            success="#2E7D32",
            warning="#EF6C00",
            error="#C62828",
            info="#00838F",
            
            background="#E3F2FD",
            surface="#BBDEFB",
            card="#FFFFFF",
            
            text_primary="#0D47A1",
            text_secondary="#1565C0",
            text_disabled="#90CAF9",
            
            border="#2196F3",
            divider="#64B5F6",
            shadow="rgba(33, 150, 243, 0.1)"
        )
        self.themes["blue"] = ThemeConfig(
            name="blue",
            display_name="蓝色主题",
            description="清爽的蓝色主题，专业感十足",
            colors=blue_colors,
            is_dark=False
        )
        
        # 绿色主题
        green_colors = ThemeColors(
            primary="#2E7D32",
            secondary="#FF8F00",
            success="#1B5E20",
            warning="#E65100",
            error="#B71C1C",
            info="#006064",
            
            background="#E8F5E8",
            surface="#C8E6C9",
            card="#FFFFFF",
            
            text_primary="#1B5E20",
            text_secondary="#2E7D32",
            text_disabled="#A5D6A7",
            
            border="#4CAF50",
            divider="#81C784",
            shadow="rgba(76, 175, 80, 0.1)"
        )
        self.themes["green"] = ThemeConfig(
            name="green",
            display_name="绿色主题",
            description="自然的绿色主题，舒缓护眼",
            colors=green_colors,
            is_dark=False
        )
        
        # 紫色主题
        purple_colors = ThemeColors(
            primary="#7B1FA2",
            secondary="#FF6F00",
            success="#388E3C",
            warning="#F57C00",
            error="#D32F2F",
            info="#0097A7",
            
            background="#F3E5F5",
            surface="#E1BEE7",
            card="#FFFFFF",
            
            text_primary="#4A148C",
            text_secondary="#7B1FA2",
            text_disabled="#CE93D8",
            
            border="#9C27B0",
            divider="#BA68C8",
            shadow="rgba(156, 39, 176, 0.1)"
        )
        self.themes["purple"] = ThemeConfig(
            name="purple",
            display_name="紫色主题",
            description="优雅的紫色主题，彰显个性",
            colors=purple_colors,
            is_dark=False
        )
    
    def _load_custom_themes(self):
        """加载自定义主题"""
        try:
            for filename in os.listdir(self.custom_themes_dir):
                if filename.endswith('.json'):
                    theme_path = os.path.join(self.custom_themes_dir, filename)
                    with open(theme_path, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                    
                    # 解析主题配置
                    colors_data = theme_data.get('colors', {})
                    colors = ThemeColors(**colors_data)
                    
                    theme_config = ThemeConfig(
                        name=theme_data['name'],
                        display_name=theme_data.get('display_name', theme_data['name']),
                        description=theme_data.get('description', ''),
                        colors=colors,
                        is_dark=theme_data.get('is_dark', False),
                        font_family=theme_data.get('font_family', 'Microsoft YaHei UI'),
                        font_size=theme_data.get('font_size', 9),
                        border_radius=theme_data.get('border_radius', 4),
                        animation_duration=theme_data.get('animation_duration', 300)
                    )
                    
                    self.themes[theme_config.name] = theme_config
                    print(f"[OK] 加载自定义主题: {theme_config.display_name}")
                    
        except Exception as e:
            print(f"[WARN] 加载自定义主题失败: {e}")
    
    def get_available_themes(self) -> List[Dict[str, str]]:
        """获取可用主题列表"""
        themes_list = []
        for theme in self.themes.values():
            themes_list.append({
                'name': theme.name,
                'display_name': theme.display_name,
                'description': theme.description,
                'is_dark': theme.is_dark
            })
        return themes_list
    
    def get_theme_config(self, theme_name: str) -> Optional[ThemeConfig]:
        """获取主题配置"""
        return self.themes.get(theme_name)
    
    def apply_theme(self, theme_name: str) -> bool:
        """应用主题 - 增强版本"""
        if theme_name not in self.themes:
            print(f"[WARN] 主题不存在: {theme_name}")
            return False

        theme_config = self.themes[theme_name]

        try:
            # 生成增强的CSS样式
            css = self._generate_enhanced_theme_css(theme_config)

            # 查找主窗口并应用主题
            main_window = self._find_main_window()
            if main_window:
                main_window.setStyleSheet(css)
                print(f"[OK] 主题已应用到主窗口: {theme_config.display_name}")
            else:
                # 备用方案：应用到整个应用程序
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(css)
                    print(f"[OK] 主题已应用到应用程序: {theme_config.display_name}")

            # 更新当前主题
            self.current_theme = theme_name

            # 发送信号
            self.theme_changed.emit(theme_name)
            self.theme_loaded.emit(asdict(theme_config))

            return True

        except Exception as e:
            print(f"[ERROR] 应用主题失败: {e}")
            return False

    def _find_main_window(self):
        """查找主窗口"""
        try:
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if hasattr(widget, 'tabs') and hasattr(widget, 'setup_ui_style'):
                        return widget
            return None
        except Exception:
            return None

    def _generate_enhanced_theme_css(self, theme: ThemeConfig) -> str:
        """生成增强的主题CSS - 与现有样式兼容"""
        colors = theme.colors

        # 安全获取颜色属性
        primary_light = getattr(colors, 'primary_light', colors.primary)
        primary_dark = getattr(colors, 'primary_dark', colors.primary)
        text_secondary = getattr(colors, 'text_secondary', colors.text_primary)

        css = f"""
        /* 主窗口和基础组件 */
        QMainWindow {{
            background-color: {colors.background};
            color: {colors.text_primary};
            font-family: "{theme.font_family}";
            font-size: {theme.font_size}pt;
        }}

        QWidget {{
            background-color: {colors.background};
            color: {colors.text_primary};
        }}

        /* 按钮样式 */
        QPushButton {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors.primary}, stop: 1 {colors.primary});
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: {theme.border_radius}px;
            font-weight: bold;
            min-height: 25px;
        }}

        QPushButton:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {primary_light}, stop: 1 {colors.primary});
            border: 2px solid {colors.primary};
        }}

        QPushButton:pressed {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {primary_dark}, stop: 1 {colors.primary});
            border: 2px solid {primary_dark};
        }}

        /* 输入框样式 */
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            padding: 6px 12px;
            font-size: {theme.font_size}pt;
        }}

        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 2px solid {colors.primary};
            background-color: {colors.surface};
        }}

        /* 标签页样式 */
        QTabWidget::pane {{
            border: 1px solid {colors.border};
            background-color: {colors.surface};
            border-radius: {theme.border_radius}px;
        }}

        QTabBar::tab {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: {theme.border_radius}px;
            border-top-right-radius: {theme.border_radius}px;
        }}

        QTabBar::tab:selected {{
            background-color: {colors.primary};
            color: white;
            border-bottom: 1px solid {colors.primary};
        }}

        QTabBar::tab:hover {{
            background-color: {primary_light};
            color: white;
        }}

        /* 列表和表格样式 */
        QListWidget, QTableWidget {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            alternate-background-color: {colors.background};
        }}

        QListWidget::item:selected, QTableWidget::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}

        QListWidget::item:hover, QTableWidget::item:hover {{
            background-color: {primary_light};
            color: white;
        }}

        /* 分组框样式 */
        QGroupBox {{
            color: {colors.text_primary};
            border: 2px solid {colors.border};
            border-radius: {theme.border_radius + 1}px;
            margin-top: 10px;
            font-weight: bold;
            font-size: {theme.font_size + 1}pt;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: {colors.primary};
        }}

        /* 进度条样式 */
        QProgressBar {{
            border: 2px solid {colors.border};
            border-radius: {theme.border_radius}px;
            background-color: {colors.surface};
            color: {colors.text_primary};
            text-align: center;
            font-weight: bold;
        }}

        QProgressBar::chunk {{
            background-color: {colors.primary};
            border-radius: {theme.border_radius - 1}px;
        }}

        /* 滚动条样式 */
        QScrollBar:vertical {{
            background-color: {colors.surface};
            width: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {colors.primary};
            border-radius: 6px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {primary_light};
        }}

        /* 菜单样式 */
        QMenuBar {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border-bottom: 1px solid {colors.border};
        }}

        QMenuBar::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}

        QMenu {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
        }}

        QMenu::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}

        /* 状态栏样式 */
        QStatusBar {{
            background-color: {colors.surface};
            color: {text_secondary};
            border-top: 1px solid {colors.border};
        }}
        """

        return css

    def _generate_theme_css(self, theme: ThemeConfig) -> str:
        """生成主题CSS"""
        colors = theme.colors
        
        css = f"""
        /* 全局样式 */
        QWidget {{
            font-family: "{theme.font_family}";
            font-size: {theme.font_size}pt;
            color: {colors.text_primary};
            background-color: {colors.background};
        }}
        
        /* 主窗口 */
        QMainWindow {{
            background-color: {colors.background};
            border: none;
        }}
        
        /* 按钮样式 */
        QPushButton {{
            background-color: {colors.primary};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: {theme.border_radius}px;
            font-weight: bold;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {self._darken_color(colors.primary, 0.1)};
        }}
        
        QPushButton:pressed {{
            background-color: {self._darken_color(colors.primary, 0.2)};
        }}
        
        QPushButton:disabled {{
            background-color: {colors.text_disabled};
            color: {colors.text_secondary};
        }}
        
        /* 次要按钮 */
        QPushButton[class="secondary"] {{
            background-color: {colors.secondary};
            color: {colors.text_primary};
        }}
        
        QPushButton[class="secondary"]:hover {{
            background-color: {self._darken_color(colors.secondary, 0.1)};
        }}
        
        /* 成功按钮 */
        QPushButton[class="success"] {{
            background-color: {colors.success};
        }}
        
        /* 警告按钮 */
        QPushButton[class="warning"] {{
            background-color: {colors.warning};
        }}
        
        /* 错误按钮 */
        QPushButton[class="error"] {{
            background-color: {colors.error};
        }}
        
        /* 标签页 */
        QTabWidget::pane {{
            border: 1px solid {colors.border};
            background-color: {colors.card};
            border-radius: {theme.border_radius}px;
        }}
        
        QTabBar::tab {{
            background-color: {colors.surface};
            color: {colors.text_secondary};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: {theme.border_radius}px;
            border-top-right-radius: {theme.border_radius}px;
            border: 1px solid {colors.border};
            border-bottom: none;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors.card};
            color: {colors.text_primary};
            border-bottom: 2px solid {colors.primary};
        }}
        
        QTabBar::tab:hover {{
            background-color: {self._lighten_color(colors.surface, 0.1)};
        }}
        
        /* 输入框 */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors.card};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            padding: 8px;
            color: {colors.text_primary};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {colors.primary};
        }}
        
        /* 列表 */
        QListWidget {{
            background-color: {colors.card};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            alternate-background-color: {colors.surface};
        }}
        
        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {colors.divider};
        }}
        
        QListWidget::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        QListWidget::item:hover {{
            background-color: {self._lighten_color(colors.primary, 0.8)};
        }}
        
        /* 进度条 */
        QProgressBar {{
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            text-align: center;
            background-color: {colors.surface};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors.primary};
            border-radius: {theme.border_radius - 1}px;
        }}
        
        /* 分组框 */
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {colors.border};
            border-radius: {theme.border_radius}px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: {colors.card};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: {colors.text_primary};
        }}
        
        /* 滚动条 */
        QScrollBar:vertical {{
            background-color: {colors.surface};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors.text_disabled};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors.text_secondary};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* 菜单 */
        QMenuBar {{
            background-color: {colors.surface};
            border-bottom: 1px solid {colors.border};
        }}
        
        QMenuBar::item {{
            padding: 8px 12px;
            background-color: transparent;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        QMenu {{
            background-color: {colors.card};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
        }}
        
        QMenu::item {{
            padding: 8px 16px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        /* 工具提示 */
        QToolTip {{
            background-color: {colors.text_primary};
            color: {colors.background};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            padding: 4px 8px;
        }}
        
        /* 状态栏 */
        QStatusBar {{
            background-color: {colors.surface};
            border-top: 1px solid {colors.border};
        }}
        """
        
        return css
    
    def _darken_color(self, color_str: str, factor: float) -> str:
        """加深颜色"""
        try:
            color = QColor(color_str)
            h, s, l, a = color.getHsl()
            l = max(0, int(l * (1 - factor)))
            color.setHsl(h, s, l, a)
            return color.name()
        except:
            return color_str
    
    def _lighten_color(self, color_str: str, factor: float) -> str:
        """减淡颜色"""
        try:
            color = QColor(color_str)
            h, s, l, a = color.getHsl()
            l = min(255, int(l + (255 - l) * factor))
            color.setHsl(h, s, l, a)
            return color.name()
        except:
            return color_str
    
    def save_custom_theme(self, theme_config: ThemeConfig) -> bool:
        """保存自定义主题"""
        try:
            theme_path = os.path.join(self.custom_themes_dir, f"{theme_config.name}.json")
            theme_data = asdict(theme_config)
            
            with open(theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            # 添加到主题列表
            self.themes[theme_config.name] = theme_config
            
            print(f"[OK] 自定义主题已保存: {theme_config.display_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 保存自定义主题失败: {e}")
            return False
    
    def delete_custom_theme(self, theme_name: str) -> bool:
        """删除自定义主题"""
        if theme_name in ["default", "dark", "high_contrast", "blue", "green", "purple"]:
            print(f"[WARN] 不能删除预设主题: {theme_name}")
            return False
        
        try:
            theme_path = os.path.join(self.custom_themes_dir, f"{theme_name}.json")
            if os.path.exists(theme_path):
                os.remove(theme_path)
            
            if theme_name in self.themes:
                del self.themes[theme_name]
            
            print(f"[OK] 自定义主题已删除: {theme_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 删除自定义主题失败: {e}")
            return False
    
    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        return self.current_theme
    
    def toggle_theme(self):
        """切换主题（在浅色和深色之间）"""
        if self.current_theme == "dark":
            self.apply_theme("default")
        else:
            self.apply_theme("dark")

# 全局主题系统实例
_theme_system = None

def get_theme_system() -> AdvancedThemeSystem:
    """获取全局主题系统"""
    global _theme_system
    if _theme_system is None:
        _theme_system = AdvancedThemeSystem()
    return _theme_system

__all__ = [
    'ThemeColors',
    'ThemeConfig',
    'AdvancedThemeSystem',
    'get_theme_system'
]
