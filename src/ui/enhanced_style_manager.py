"""
增强样式管理器
提供高级样式管理和主题切换功能
"""

import os
import json
from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QObject, pyqtSignal

class EnhancedStyleManager(QObject):
    """增强样式管理器"""
    
    theme_changed = pyqtSignal(str)  # 主题变更信号
    style_applied = pyqtSignal(str)  # 样式应用信号
    
    def __init__(self):
        super().__init__()
        self.current_theme = "default"
        self.themes: Dict[str, Dict[str, Any]] = {}
        self.custom_styles: Dict[str, str] = {}
        self.style_cache: Dict[str, str] = {}
        
        # 初始化默认主题
        self._initialize_default_themes()
    
    def _initialize_default_themes(self):
        """初始化默认主题"""
        try:
            # 默认主题
            self.themes["default"] = {
                "name": "默认主题",
                "description": "系统默认样式",
                "icon": "☀️",
                "colors": {
                    "primary": "#2196F3",
                    "secondary": "#FFC107",
                    "success": "#4CAF50",
                    "warning": "#FF9800",
                    "error": "#F44336",
                    "background": "#FFFFFF",
                    "surface": "#F5F5F5",
                    "text": "#212121"
                },
                "fonts": {
                    "family": "Microsoft YaHei",
                    "size": 9,
                    "weight": "normal"
                }
            }
            
            # 深色主题
            self.themes["dark"] = {
                "name": "深色主题",
                "description": "深色护眼主题",
                "icon": "🌙",
                "colors": {
                    "primary": "#1976D2",
                    "secondary": "#FFA000",
                    "success": "#388E3C",
                    "warning": "#F57C00",
                    "error": "#D32F2F",
                    "background": "#121212",
                    "surface": "#1E1E1E",
                    "text": "#FFFFFF"
                },
                "fonts": {
                    "family": "Microsoft YaHei",
                    "size": 9,
                    "weight": "normal"
                }
            }
            
            # 高对比度主题
            self.themes["high_contrast"] = {
                "name": "高对比度主题",
                "description": "高对比度无障碍主题",
                "icon": "🔆",
                "colors": {
                    "primary": "#0000FF",
                    "secondary": "#FFFF00",
                    "success": "#00FF00",
                    "warning": "#FF8000",
                    "error": "#FF0000",
                    "background": "#000000",
                    "surface": "#333333",
                    "text": "#FFFFFF"
                },
                "fonts": {
                    "family": "Microsoft YaHei",
                    "size": 10,
                    "weight": "bold"
                }
            }
            
            print("[OK] 默认主题初始化完成")
            
        except Exception as e:
            print(f"[WARN] 默认主题初始化失败: {e}")
    
    def apply_theme(self, theme_name: str, widget: Optional[QWidget] = None) -> bool:
        """
        应用主题
        
        Args:
            theme_name: 主题名称
            widget: 目标组件，None表示应用到整个应用
            
        Returns:
            是否成功应用
        """
        try:
            if theme_name not in self.themes:
                print(f"[WARN] 主题不存在: {theme_name}")
                return False
            
            theme = self.themes[theme_name]
            stylesheet = self._generate_stylesheet(theme)
            
            # 使用CSS预处理器处理样式
            from ui.utils.css_preprocessor import preprocess_css_for_qt
            processed_stylesheet = preprocess_css_for_qt(stylesheet)

            # 应用样式
            if widget:
                widget.setStyleSheet(processed_stylesheet)
            else:
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(processed_stylesheet)
            
            self.current_theme = theme_name
            self.theme_changed.emit(theme_name)
            self.style_applied.emit(stylesheet)
            
            print(f"[OK] 主题已应用: {theme_name}")
            return True
            
        except Exception as e:
            print(f"[WARN] 应用主题失败: {e}")
            return False
    
    def _generate_stylesheet(self, theme: Dict[str, Any]) -> str:
        """生成样式表"""
        try:
            colors = theme.get("colors", {})
            fonts = theme.get("fonts", {})
            
            # 生成基础样式
            stylesheet = f"""
            QWidget {{
                background-color: {colors.get('background', '#FFFFFF')};
                color: {colors.get('text', '#212121')};
                font-family: {fonts.get('family', 'Microsoft YaHei')};
                font-size: {fonts.get('size', 9)}pt;
                font-weight: {fonts.get('weight', 'normal')};
            }}
            
            QPushButton {{
                background-color: {colors.get('primary', '#2196F3')};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {self._darken_color(colors.get('primary', '#2196F3'))};
            }}
            
            QPushButton:pressed {{
                background-color: {self._darken_color(colors.get('primary', '#2196F3'), 0.3)};
            }}
            
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {colors.get('surface', '#F5F5F5')};
                border: 1px solid {colors.get('primary', '#2196F3')};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {colors.get('primary', '#2196F3')};
                background-color: {colors.get('surface', '#F5F5F5')};
            }}
            
            QTabBar::tab {{
                background-color: {colors.get('surface', '#F5F5F5')};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors.get('primary', '#2196F3')};
                color: white;
            }}
            
            QProgressBar {{
                border: 1px solid {colors.get('primary', '#2196F3')};
                border-radius: 4px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {colors.get('success', '#4CAF50')};
                border-radius: 3px;
            }}
            """
            
            return stylesheet
            
        except Exception as e:
            print(f"[WARN] 生成样式表失败: {e}")
            return ""
    
    def _darken_color(self, color: str, factor: float = 0.2) -> str:
        """使颜色变暗"""
        try:
            # 简化的颜色变暗处理
            if color.startswith('#'):
                hex_color = color[1:]
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    
                    r = max(0, int(r * (1 - factor)))
                    g = max(0, int(g * (1 - factor)))
                    b = max(0, int(b * (1 - factor)))
                    
                    return f"#{r:02x}{g:02x}{b:02x}"
            
            return color
            
        except Exception:
            return color
    
    def add_custom_theme(self, name: str, theme_data: Dict[str, Any]) -> bool:
        """添加自定义主题"""
        try:
            self.themes[name] = theme_data
            print(f"[OK] 自定义主题已添加: {name}")
            return True
        except Exception as e:
            print(f"[WARN] 添加自定义主题失败: {e}")
            return False
    
    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
        return list(self.themes.keys())
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self.current_theme
    
    def get_theme_info(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """获取主题信息"""
        theme_info = self.themes.get(theme_name)
        if theme_info:
            # 确保包含所有必需字段
            if 'icon' not in theme_info:
                theme_info['icon'] = '🎨'  # 默认图标
            if 'name' not in theme_info:
                theme_info['name'] = theme_name
        return theme_info
    
    def save_theme_to_file(self, theme_name: str, file_path: str) -> bool:
        """保存主题到文件"""
        try:
            if theme_name not in self.themes:
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.themes[theme_name], f, indent=2, ensure_ascii=False)
            
            print(f"[OK] 主题已保存到: {file_path}")
            return True
            
        except Exception as e:
            print(f"[WARN] 保存主题失败: {e}")
            return False
    
    def load_theme_from_file(self, file_path: str, theme_name: str) -> bool:
        """从文件加载主题"""
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            self.themes[theme_name] = theme_data
            print(f"[OK] 主题已从文件加载: {theme_name}")
            return True
            
        except Exception as e:
            print(f"[WARN] 加载主题失败: {e}")
            return False
    
    def apply_custom_style(self, widget: QWidget, style_name: str, stylesheet: str):
        """应用自定义样式（使用CSS预处理器）"""
        try:
            # 使用CSS预处理器处理样式
            from ui.utils.css_preprocessor import preprocess_css_for_qt
            processed_stylesheet = preprocess_css_for_qt(stylesheet)

            self.custom_styles[style_name] = processed_stylesheet
            widget.setStyleSheet(processed_stylesheet)
            print(f"[OK] 自定义样式已应用: {style_name}")
        except Exception as e:
            # 静默处理错误
            pass

    def toggle_theme(self, widget: Optional[QWidget] = None) -> str:
        """
        切换主题

        Args:
            widget: 要应用主题的组件，如果为None则应用到全局

        Returns:
            新的主题名称
        """
        try:
            # 定义主题切换顺序
            theme_order = ["default", "dark", "high_contrast"]

            # 找到当前主题在顺序中的位置
            try:
                current_index = theme_order.index(self.current_theme)
            except ValueError:
                current_index = 0

            # 切换到下一个主题
            next_index = (current_index + 1) % len(theme_order)
            new_theme = theme_order[next_index]

            # 应用新主题
            success = self.apply_theme(new_theme, widget)

            if success:
                print(f"[OK] 主题已切换: {self.current_theme} -> {new_theme}")
                return new_theme
            else:
                print(f"[WARN] 主题切换失败: {new_theme}")
                return self.current_theme

        except Exception as e:
            print(f"[ERROR] 主题切换异常: {e}")
            return self.current_theme

    def get_style_report(self) -> str:
        """获取样式报告"""
        try:
            report = [
                "=== 样式管理器报告 ===",
                f"当前主题: {self.current_theme}",
                f"可用主题数量: {len(self.themes)}",
                f"自定义样式数量: {len(self.custom_styles)}",
                f"样式缓存数量: {len(self.style_cache)}",
                "",
                "可用主题:",
            ]
            
            for theme_name, theme_data in self.themes.items():
                name = theme_data.get('name', theme_name)
                desc = theme_data.get('description', '无描述')
                report.append(f"  • {name} ({theme_name}): {desc}")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"生成样式报告失败: {e}"

# 全局样式管理器实例
style_manager = EnhancedStyleManager()

def get_style_manager() -> EnhancedStyleManager:
    """获取全局样式管理器"""
    return style_manager

def apply_theme(theme_name: str, widget: Optional[QWidget] = None) -> bool:
    """应用主题"""
    return style_manager.apply_theme(theme_name, widget)

def get_available_themes() -> List[str]:
    """获取可用主题"""
    return style_manager.get_available_themes()

__all__ = [
    'EnhancedStyleManager',
    'style_manager',
    'get_style_manager',
    'apply_theme',
    'get_available_themes'
]
