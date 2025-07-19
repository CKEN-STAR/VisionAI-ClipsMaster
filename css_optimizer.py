
# 导入统一CSS管理器
try:
    from ui.utils.unified_css_manager import apply_qt_compatible_css, process_css_for_compatibility
    UNIFIED_CSS_MANAGER_AVAILABLE = True
    print("[OK] 统一CSS管理器导入成功")
except ImportError as e:
    UNIFIED_CSS_MANAGER_AVAILABLE = False
    print(f"[WARN] 统一CSS管理器导入失败: {e}")
    def apply_qt_compatible_css(widget, css, cache_key=None): 
        widget.setStyleSheet(css)
        return True
    def process_css_for_compatibility(css): 
        return css

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster CSS样式优化器
目标：移除不兼容的CSS3属性，提升UI渲染性能20%
"""

import re
import time
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication

class CSSOptimizer(QObject):
    """CSS样式优化器"""
    
    def __init__(self):
        super().__init__()
        self.style_cache = {}
        self.optimization_stats = {
            "original_styles": 0,
            "optimized_styles": 0,
            "removed_properties": 0,
            "cache_hits": 0
        }
        
        # 不兼容的CSS属性列表
        # 不兼容的CSS属性列表 - 完整版
        self.incompatible_properties = {
            # 变换和动画
            'transform', 'transform-origin', 'transform-style',
            'transition', 'transition-property', 'transition-duration', 
            'transition-timing-function', 'transition-delay',
            'animation', 'animation-name', 'animation-duration',
            'animation-timing-function', 'animation-delay',
            'animation-iteration-count', 'animation-direction',
            'animation-fill-mode', 'animation-play-state',
            
            # 阴影和滤镜
            'box-shadow', 'text-shadow', 'filter', 'backdrop-filter',
            'drop-shadow',
            
            # 现代布局
            'flex', 'flex-direction', 'flex-wrap', 'flex-flow',
            'justify-content', 'align-items', 'align-content',
            'grid', 'grid-template', 'grid-area',
            
            # 高级效果
            'clip-path', 'mask', 'mask-image', 'mask-size',
            'opacity',  # 在某些Qt版本中可能不稳定
        }
        
        # 替代方案映射
        self.property_alternatives = {
            'border-radius': 'border: 2px solid',
            'box-shadow': 'border: 1px solid #ccc',
            'text-shadow': 'font-weight: bold',
            'transform': '',  # 移除transform效果
            'transition': '',  # 移除过渡效果
            'animation': '',  # 移除动画效果
        }
        
    def optimize_stylesheet(self, stylesheet):
        """优化样式表"""
        try:
            # 检查缓存
            cache_key = hash(stylesheet)
            if cache_key in self.style_cache:
                self.optimization_stats["cache_hits"] += 1
                return self.style_cache[cache_key]
            
            start_time = time.time()
            self.optimization_stats["original_styles"] += 1
            
            # 优化样式
            optimized = self._remove_incompatible_properties(stylesheet)
            optimized = self._apply_alternatives(optimized)
            optimized = self._compress_stylesheet(optimized)
            
            # 缓存结果
            self.style_cache[cache_key] = optimized
            self.optimization_stats["optimized_styles"] += 1
            
            elapsed = time.time() - start_time
            if elapsed > 0.001:  # 超过1ms记录
                print(f"[INFO] CSS优化耗时: {elapsed*1000:.1f}ms")
            
            return optimized
            
        except Exception as e:
            print(f"[ERROR] CSS优化失败: {e}")
            return stylesheet
            
    def _remove_incompatible_properties(self, stylesheet):
        """移除不兼容的CSS属性"""
        try:
            removed_count = 0
            
            # 使用正则表达式移除不兼容属性
            for prop in self.incompatible_properties:
                pattern = rf'{prop}\\\1*:[^;]*;'
                matches = re.findall(pattern, stylesheet, re.IGNORECASE)
                if matches:
                    stylesheet = re.sub(pattern, '', stylesheet, flags=re.IGNORECASE)
                    removed_count += len(matches)
                    
            self.optimization_stats["removed_properties"] += removed_count
            
            if removed_count > 0:
                print(f"[OK] 移除了 {removed_count} 个不兼容的CSS属性")
                
            return stylesheet
            
        except Exception as e:
            print(f"[ERROR] 移除不兼容属性失败: {e}")
            return stylesheet
            
    def _apply_alternatives(self, stylesheet):
        """应用替代方案"""
        try:
            # 这里可以添加特定的替代逻辑
            # 例如：将某些效果转换为PyQt6原生支持的样式
            
            # 移除空的CSS规则
            stylesheet = re.sub(r'\\\1[\\\1]*\\\1', '', stylesheet)
            
            # 移除多余的空白
            stylesheet = re.sub(r'\\\1+', ' ', stylesheet)
            
            return stylesheet
            
        except Exception as e:
            print(f"[ERROR] 应用替代方案失败: {e}")
            return stylesheet
            
    def _compress_stylesheet(self, stylesheet):
        """压缩样式表"""
        try:
            # 移除注释
            stylesheet = re.sub(r'/\\\1.*?\\\1/', '', stylesheet, flags=re.DOTALL)
            
            # 移除多余的空白和换行
            stylesheet = re.sub(r'\\\1+', ' ', stylesheet)
            stylesheet = re.sub(r'\\\1*{\\\1*', '{', stylesheet)
            stylesheet = re.sub(r'\\\1*}\\\1*', '}', stylesheet)
            stylesheet = re.sub(r'\\\1*;\\\1*', ';', stylesheet)
            stylesheet = re.sub(r'\\\1*:\\\1*', ':', stylesheet)
            
            return stylesheet.strip()
            
        except Exception as e:
            print(f"[ERROR] 压缩样式表失败: {e}")
            return stylesheet
            
    def get_compatible_button_style(self):
        """获取兼容的按钮样式"""
        return """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: 2px solid #45a049;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #45a049;
            border: 2px solid #3d8b40;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 2px solid #999999;
        }
        """
        
    def get_compatible_tab_style(self):
        """获取兼容的标签页样式"""
        return """
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #f0f0f0;
            border: 1px solid #c0c0c0;
            padding: 8px 12px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
        }
        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        """
        
    def get_compatible_input_style(self):
        """获取兼容的输入框样式"""
        return """
        QLineEdit, QTextEdit, QPlainTextEdit {
            border: 2px solid #ddd;
            padding: 8px;
            font-size: 14px;
            background-color: white;
        }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #4CAF50;
        }
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
            background-color: #f5f5f5;
            color: #999999;
        }
        """
        
    def get_compatible_progress_style(self):
        """获取兼容的进度条样式"""
        return """
        QProgressBar {
            border: 2px solid #ddd;
            background-color: #f0f0f0;
            height: 20px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            width: 10px;
        }
        """
        
    def get_optimization_report(self):
        """获取优化报告"""
        return {
            "original_styles": self.optimization_stats["original_styles"],
            "optimized_styles": self.optimization_stats["optimized_styles"],
            "removed_properties": self.optimization_stats["removed_properties"],
            "cache_hits": self.optimization_stats["cache_hits"],
            "cache_size": len(self.style_cache),
            "optimization_rate": (
                self.optimization_stats["removed_properties"] / 
                max(1, self.optimization_stats["original_styles"])
            ) * 100
        }
        
    def clear_cache(self):
        """清理缓存"""
        self.style_cache.clear()
        print("[OK] CSS样式缓存已清理")

class StyleManager:
    """样式管理器"""
    
    def __init__(self):
        self.css_optimizer = CSSOptimizer()
        self.current_theme = "light"
        self.themes = {
            "light": self._get_light_theme(),
            "dark": self._get_dark_theme()
        }
        
    def apply_optimized_styles(self, widget):
        """应用优化的样式"""
        try:
            # 获取当前主题样式
            theme_styles = self.themes.get(self.current_theme, self.themes["light"])
            
            # 优化样式
            optimized_styles = self.css_optimizer.optimize_stylesheet(theme_styles)
            
            # 应用样式
            widget.setStyleSheet(optimized_styles)
            
            print(f"[OK] 已应用优化的 {self.current_theme} 主题样式")
            
        except Exception as e:
            print(f"[ERROR] 应用优化样式失败: {e}")
            
    def _get_light_theme(self):
        """获取浅色主题"""
        return f"""
        /* 主窗口样式 */
        QMainWindow {{
            background-color: #ffffff;
            color: #333333;
        }}
        
        /* 按钮样式 */
        {self.css_optimizer.get_compatible_button_style()}
        
        /* 标签页样式 */
        {self.css_optimizer.get_compatible_tab_style()}
        
        /* 输入框样式 */
        {self.css_optimizer.get_compatible_input_style()}
        
        /* 进度条样式 */
        {self.css_optimizer.get_compatible_progress_style()}
        
        /* 列表样式 */
        QListWidget {{
            border: 1px solid #ddd;
            background-color: white;
            alternate-background-color: #f9f9f9;
        }}
        
        /* 状态栏样式 */
        QStatusBar {{
            background-color: #f0f0f0;
            border-top: 1px solid #ddd;
        }}
        """
        
    def _get_dark_theme(self):
        """获取深色主题"""
        return """
        /* 深色主题暂未实现 */
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        """
        
    def switch_theme(self, theme_name):
        """切换主题"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            print(f"[OK] 已切换到 {theme_name} 主题")
        else:
            print(f"[WARN] 未知主题: {theme_name}")

# 全局实例
css_optimizer = CSSOptimizer()
style_manager = StyleManager()

def optimize_stylesheet(stylesheet):
    """优化样式表的全局接口"""
    return css_optimizer.optimize_stylesheet(stylesheet)

def apply_optimized_styles(widget):
    """应用优化的样式表到组件"""
    try:
        # 获取组件类型
        widget_type = widget.__class__.__name__
        
        # 生成缓存键
        cache_key = f"optimized_{widget_type}"
        
        # 获取基础样式
        base_style = get_base_style_for_widget(widget_type)
        
        # 使用统一CSS管理器应用样式
        if UNIFIED_CSS_MANAGER_AVAILABLE:
            success = apply_qt_compatible_css(widget, base_style, cache_key)
            if success:
                print(f"[OK] 使用统一CSS管理器应用样式: {widget_type}")
            else:
                print(f"[WARN] 统一CSS管理器应用失败，使用原始样式: {widget_type}")
                widget.setStyleSheet(base_style)
        else:
            widget.setStyleSheet(base_style)
            
    except Exception as e:
        print(f"[ERROR] 应用优化样式失败: {e}")
def get_css_optimization_report():
    """获取CSS优化报告的全局接口"""
    return css_optimizer.get_optimization_report()

def clear_css_cache():
    """清理CSS缓存的全局接口"""
    css_optimizer.clear_cache()
