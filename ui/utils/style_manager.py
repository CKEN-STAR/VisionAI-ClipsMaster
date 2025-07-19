"""
统一样式管理器
负责加载、处理和应用PyQt6兼容的样式
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QObject, pyqtSignal

class StyleManager(QObject):
    """统一样式管理器"""
    
    # 信号
    style_applied = pyqtSignal(str)  # 样式应用成功
    style_error = pyqtSignal(str)    # 样式应用失败
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.style_cache = {}
        self.css_processor = None
        
        # 初始化CSS处理器
        self._init_css_processor()
        
    def _init_css_processor(self):
        """初始化CSS处理器"""
        try:
            from .enhanced_css_processor import process_css_for_qt
            self.css_processor = process_css_for_qt
            print("[OK] CSS处理器初始化成功")
        except ImportError:
            print("[WARN] CSS处理器不可用，将使用基础处理")
            self.css_processor = self._basic_css_processor
    
    def _basic_css_processor(self, css: str) -> str:
        """基础CSS处理器"""
        if not css:
            return ""
        
        # 移除PyQt6不支持的属性
        unsupported_props = [
            'box-shadow', 'text-shadow', 'transform', 'transition', 
            'animation', 'opacity', 'filter'
        ]
        
        lines = css.split('\n')
        processed_lines = []
        
        for line in lines:
            should_keep = True
            for prop in unsupported_props:
                if f'{prop}:' in line.strip():
                    should_keep = False
                    break
            if should_keep:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def load_style_file(self, style_path: str) -> str:
        """加载样式文件"""
        try:
            style_file = Path(style_path)
            if not style_file.exists():
                # 尝试相对路径
                ui_dir = Path(__file__).parent.parent
                style_file = ui_dir / "assets" / "style.qss"
                
            if not style_file.exists():
                print(f"[WARN] 样式文件不存在: {style_path}")
                return self._get_default_style()
            
            with open(style_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            print(f"[OK] 样式文件加载成功: {style_file}")
            return css_content
            
        except Exception as e:
            print(f"[ERROR] 样式文件加载失败: {e}")
            return self._get_default_style()
    
    def _get_default_style(self) -> str:
        """获取默认样式"""
        return """
        QMainWindow {
            background-color: #FFFFFF;
            color: #333333;
            font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC";
            font-size: 13px;
        }
        
        QPushButton {
            background-color: #007bff;
            color: white;
            border: 1px solid #007bff;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            min-width: 80px;
            min-height: 32px;
        }
        
        QPushButton:hover {
            background-color: #0056b3;
            border-color: #0056b3;
        }
        
        QPushButton:pressed {
            background-color: #004085;
            border-color: #004085;
        }
        
        QPushButton:disabled {
            background-color: #6c757d;
            border-color: #6c757d;
            color: #ffffff;
        }
        
        QLineEdit {
            background-color: #ffffff;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            color: #495057;
        }
        
        QLineEdit:focus {
            border-color: #007bff;
            background-color: #ffffff;
        }
        
        QLabel {
            color: #333333;
            font-size: 13px;
            background-color: transparent;
        }
        """
    
    def apply_style_to_widget(self, widget: QWidget, style: Optional[str] = None) -> bool:
        """应用样式到组件"""
        try:
            if style is None:
                # 加载默认样式文件
                style = self.load_style_file("ui/assets/style.qss")
            
            # 处理CSS兼容性
            processed_style = self.css_processor(style)
            
            # 应用样式
            widget.setStyleSheet(processed_style)
            
            self.style_applied.emit("样式应用成功")
            print("[OK] 样式应用成功")
            return True
            
        except Exception as e:
            error_msg = f"样式应用失败: {e}"
            self.style_error.emit(error_msg)
            print(f"[ERROR] {error_msg}")
            return False
    
    def apply_global_style(self, style: Optional[str] = None) -> bool:
        """应用全局样式"""
        try:
            app = QApplication.instance()
            if not app:
                print("[WARN] 无法获取QApplication实例")
                return False
            
            if style is None:
                style = self.load_style_file("ui/assets/style.qss")
            
            # 处理CSS兼容性
            processed_style = self.css_processor(style)
            
            # 应用全局样式
            app.setStyleSheet(processed_style)
            
            self.style_applied.emit("全局样式应用成功")
            print("[OK] 全局样式应用成功")
            return True
            
        except Exception as e:
            error_msg = f"全局样式应用失败: {e}"
            self.style_error.emit(error_msg)
            print(f"[ERROR] {error_msg}")
            return False
    
    def get_theme_style(self, theme_name: str) -> str:
        """获取主题样式"""
        themes = {
            "light": self._get_light_theme(),
            "dark": self._get_dark_theme(),
            "high_contrast": self._get_high_contrast_theme()
        }
        
        return themes.get(theme_name, themes["light"])
    
    def _get_light_theme(self) -> str:
        """浅色主题"""
        return self.load_style_file("ui/assets/style.qss")
    
    def _get_dark_theme(self) -> str:
        """深色主题"""
        return """
        QMainWindow {
            background-color: #212529;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #212529;
            color: #ffffff;
        }
        
        QPushButton {
            background-color: #0d6efd;
            color: white;
            border: 1px solid #0d6efd;
            border-radius: 6px;
            padding: 8px 16px;
        }
        
        QPushButton:hover {
            background-color: #0b5ed7;
        }
        
        QLineEdit {
            background-color: #343a40;
            border: 2px solid #495057;
            border-radius: 6px;
            padding: 8px 12px;
            color: #ffffff;
        }
        
        QLineEdit:focus {
            border-color: #0d6efd;
        }
        """
    
    def _get_high_contrast_theme(self) -> str:
        """高对比度主题"""
        return """
        QMainWindow {
            background-color: #000000;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #000000;
            color: #ffffff;
        }
        
        QPushButton {
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
            border-radius: 6px;
            padding: 8px 16px;
        }
        
        QPushButton:hover {
            background-color: #ffffff;
            color: #000000;
        }
        
        QLineEdit {
            background-color: #000000;
            border: 2px solid #ffffff;
            border-radius: 6px;
            padding: 8px 12px;
            color: #ffffff;
        }
        """
    
    def switch_theme(self, theme_name: str, widget: Optional[QWidget] = None) -> bool:
        """切换主题"""
        try:
            theme_style = self.get_theme_style(theme_name)
            
            if widget:
                success = self.apply_style_to_widget(widget, theme_style)
            else:
                success = self.apply_global_style(theme_style)
            
            if success:
                self.current_theme = theme_name
                print(f"[OK] 主题切换成功: {theme_name}")
            
            return success
            
        except Exception as e:
            print(f"[ERROR] 主题切换失败: {e}")
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            "current_theme": self.current_theme,
            "css_processor_available": self.css_processor is not None,
            "cache_size": len(self.style_cache)
        }

# 全局样式管理器实例
_style_manager = None

def get_style_manager() -> StyleManager:
    """获取全局样式管理器实例"""
    global _style_manager
    if _style_manager is None:
        _style_manager = StyleManager()
    return _style_manager

def apply_safe_style(widget: QWidget, style: str) -> bool:
    """安全地应用样式到组件"""
    manager = get_style_manager()
    return manager.apply_style_to_widget(widget, style)

def switch_global_theme(theme_name: str) -> bool:
    """切换全局主题"""
    manager = get_style_manager()
    return manager.switch_theme(theme_name)

__all__ = [
    'StyleManager',
    'get_style_manager', 
    'apply_safe_style',
    'switch_global_theme'
]
