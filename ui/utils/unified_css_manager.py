"""
统一CSS管理器
提供统一的CSS应用和管理功能
"""

import hashlib
from typing import Dict, Optional, Any
from PyQt6.QtWidgets import QWidget

# CSS缓存
_css_cache: Dict[str, str] = {}
_processing_stats = {
    'cache_hits': 0,
    'cache_misses': 0,
    'applications': 0,
    'errors': 0
}

def apply_qt_compatible_css(widget: QWidget, css: str, cache_key: Optional[str] = None) -> bool:
    """
    应用Qt兼容的CSS
    
    Args:
        widget: Qt组件
        css: CSS字符串
        cache_key: 缓存键（可选）
        
    Returns:
        是否成功应用
    """
    global _processing_stats
    
    try:
        if not widget or not css:
            return False
        
        # 生成缓存键
        if not cache_key:
            cache_key = hashlib.md5(css.encode()).hexdigest()
        
        # 检查缓存
        if cache_key in _css_cache:
            processed_css = _css_cache[cache_key]
            _processing_stats['cache_hits'] += 1
        else:
            # 处理CSS
            processed_css = _process_css_for_qt_compatibility(css)
            _css_cache[cache_key] = processed_css
            _processing_stats['cache_misses'] += 1
        
        # 应用CSS
        widget.setStyleSheet(processed_css)
        _processing_stats['applications'] += 1
        
        return True
        
    except Exception as e:
        print(f"[WARN] CSS应用失败: {e}")
        _processing_stats['errors'] += 1
        return False

def _process_css_for_qt_compatibility(css: str) -> str:
    """处理CSS以确保Qt兼容性"""
    try:
        # 导入CSS处理器
        from .enhanced_css_processor import process_css_for_qt
        return process_css_for_qt(css)
    except ImportError:
        # 如果处理器不可用，返回原始CSS
        return css

def clear_css_cache():
    """清理CSS缓存"""
    global _css_cache, _processing_stats
    _css_cache.clear()
    _processing_stats = {
        'cache_hits': 0,
        'cache_misses': 0,
        'applications': 0,
        'errors': 0
    }

def get_css_processing_stats() -> Dict[str, Any]:
    """获取CSS处理统计信息"""
    global _processing_stats
    
    total_requests = _processing_stats['cache_hits'] + _processing_stats['cache_misses']
    cache_hit_rate = (_processing_stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
    
    return {
        **_processing_stats,
        'cache_size': len(_css_cache),
        'cache_hit_rate': f"{cache_hit_rate:.1f}%",
        'total_requests': total_requests
    }

def optimize_css_cache():
    """优化CSS缓存"""
    global _css_cache
    
    # 如果缓存过大，清理一半
    if len(_css_cache) > 100:
        keys_to_remove = list(_css_cache.keys())[:50]
        for key in keys_to_remove:
            del _css_cache[key]

def apply_theme_css(widget: QWidget, theme: str = "default") -> bool:
    """
    应用主题CSS
    
    Args:
        widget: Qt组件
        theme: 主题名称
        
    Returns:
        是否成功应用
    """
    theme_css = _get_theme_css(theme)
    return apply_qt_compatible_css(widget, theme_css, f"theme_{theme}")

def _get_theme_css(theme: str) -> str:
    """获取主题CSS"""
    themes = {
        "default": """
            QWidget {
                background-color: #f0f0f0;
                color: #333333;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """,
        "dark": """
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """
    }
    
    return themes.get(theme, themes["default"])

def process_css_for_compatibility(css: str) -> str:
    """
    处理CSS以确保Qt兼容性

    Args:
        css: 原始CSS字符串

    Returns:
        处理后的CSS字符串
    """
    return _process_css_for_qt_compatibility(css)

__all__ = [
    'apply_qt_compatible_css',
    'get_css_processing_stats',
    'clear_css_cache',
    'optimize_css_cache',
    'apply_theme_css',
    'process_css_for_compatibility'
]
