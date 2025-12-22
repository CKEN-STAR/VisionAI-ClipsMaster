"""
文本方向适配模块
提供RTL/LTR文本方向支持
"""

from enum import Enum
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget

class LayoutDirection(Enum):
    """布局方向枚举"""
    LEFT_TO_RIGHT = "ltr"
    RIGHT_TO_LEFT = "rtl"
    AUTO = "auto"

    @staticmethod
    def is_rtl_language(language_code: str) -> bool:
        """
        检查语言是否为RTL（从右到左）语言

        Args:
            language_code: 语言代码（如 'ar', 'he', 'fa', 'ur'等）

        Returns:
            是否为RTL语言
        """
        rtl_languages = {
            'ar',    # 阿拉伯语
            'he',    # 希伯来语
            'fa',    # 波斯语
            'ur',    # 乌尔都语
            'yi',    # 意第绪语
            'iw',    # 希伯来语（旧代码）
            'ji',    # 意第绪语（旧代码）
            'ku',    # 库尔德语
            'ps',    # 普什图语
            'sd',    # 信德语
        }

        # 提取语言代码的前两位
        lang_prefix = language_code.lower()[:2] if language_code else ''
        return lang_prefix in rtl_languages

def set_application_layout_direction(direction: LayoutDirection):
    """
    设置应用程序布局方向
    
    Args:
        direction: 布局方向
    """
    try:
        app = QApplication.instance()
        if not app:
            return
        
        if direction == LayoutDirection.LEFT_TO_RIGHT:
            app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        elif direction == LayoutDirection.RIGHT_TO_LEFT:
            app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        elif direction == LayoutDirection.AUTO:
            # 根据系统语言自动检测
            locale = app.locale()
            if locale.language() in [locale.Language.Arabic, locale.Language.Hebrew, locale.Language.Persian]:
                app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            else:
                app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                
        print(f"[OK] 布局方向已设置为: {direction.value}")
        
    except Exception as e:
        print(f"[WARN] 设置布局方向失败: {e}")

def apply_rtl_styles(widget: QWidget) -> str:
    """
    应用RTL样式
    
    Args:
        widget: Qt组件
        
    Returns:
        RTL样式CSS
    """
    rtl_css = """
    QWidget {
        direction: rtl;
    }
    
    QLabel {
        text-align: right;
    }
    
    QLineEdit {
        text-align: right;
    }
    
    QTextEdit {
        text-align: right;
    }
    
    QComboBox {
        text-align: right;
    }
    
    QPushButton {
        text-align: center;
    }
    
    QMenuBar {
        direction: rtl;
    }
    
    QMenu {
        direction: rtl;
    }
    """
    
    try:
        if widget:
            widget.setStyleSheet(widget.styleSheet() + rtl_css)
        return rtl_css
    except Exception as e:
        print(f"[WARN] 应用RTL样式失败: {e}")
        return ""

def detect_text_direction(text: str) -> LayoutDirection:
    """
    检测文本方向
    
    Args:
        text: 要检测的文本
        
    Returns:
        检测到的文本方向
    """
    if not text:
        return LayoutDirection.LEFT_TO_RIGHT
    
    try:
        # 检测RTL字符
        rtl_chars = 0
        ltr_chars = 0
        
        for char in text:
            code = ord(char)
            
            # Arabic (0x0600-0x06FF)
            # Hebrew (0x0590-0x05FF) 
            # Persian/Farsi (0xFB50-0xFDFF, 0xFE70-0xFEFF)
            if (0x0590 <= code <= 0x05FF or 
                0x0600 <= code <= 0x06FF or
                0xFB50 <= code <= 0xFDFF or
                0xFE70 <= code <= 0xFEFF):
                rtl_chars += 1
            # Latin characters
            elif (0x0041 <= code <= 0x005A or  # A-Z
                  0x0061 <= code <= 0x007A):   # a-z
                ltr_chars += 1
        
        if rtl_chars > ltr_chars:
            return LayoutDirection.RIGHT_TO_LEFT
        else:
            return LayoutDirection.LEFT_TO_RIGHT
            
    except Exception as e:
        print(f"[WARN] 文本方向检测失败: {e}")
        return LayoutDirection.LEFT_TO_RIGHT

def get_current_layout_direction() -> Optional[LayoutDirection]:
    """获取当前布局方向"""
    try:
        app = QApplication.instance()
        if not app:
            return None
        
        qt_direction = app.layoutDirection()
        if qt_direction == Qt.LayoutDirection.RightToLeft:
            return LayoutDirection.RIGHT_TO_LEFT
        else:
            return LayoutDirection.LEFT_TO_RIGHT
            
    except Exception as e:
        print(f"[WARN] 获取布局方向失败: {e}")
        return None

def create_direction_aware_css(base_css: str, direction: LayoutDirection) -> str:
    """
    创建方向感知的CSS
    
    Args:
        base_css: 基础CSS
        direction: 布局方向
        
    Returns:
        方向感知的CSS
    """
    if direction == LayoutDirection.RIGHT_TO_LEFT:
        # 为RTL添加特定样式
        rtl_additions = """
        * {
            direction: rtl;
        }
        QLabel, QLineEdit, QTextEdit {
            text-align: right;
        }
        """
        return base_css + rtl_additions
    else:
        return base_css

__all__ = [
    'LayoutDirection',
    'set_application_layout_direction',
    'apply_rtl_styles',
    'detect_text_direction',
    'get_current_layout_direction',
    'create_direction_aware_css'
]
