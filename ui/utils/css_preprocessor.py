"""
CSS预处理器 - 在应用CSS前彻底清理不兼容属性
确保PyQt6不会遇到任何不支持的CSS属性
"""

import re
from typing import Dict, List, Set

class QtCSSPreprocessor:
    """Qt CSS预处理器"""
    
    def __init__(self):
        # PyQt6不支持的CSS属性完整列表
        self.unsupported_properties = {
            # 变换和动画
            'transform', 'transform-origin', 'transform-style', 'backface-visibility',
            'transition', 'transition-delay', 'transition-duration', 
            'transition-property', 'transition-timing-function',
            'animation', 'animation-delay', 'animation-duration', 
            'animation-iteration-count', 'animation-name', 'animation-timing-function',
            'animation-fill-mode', 'animation-direction', 'animation-play-state',
            
            # 阴影和滤镜
            'box-shadow', 'text-shadow', 'filter', 'backdrop-filter',
            'opacity',  # PyQt6对opacity支持有限
            
            # 高级布局
            'clip-path', 'mask', 'mask-image', 'mask-position', 'mask-size',
            'perspective', 'perspective-origin',
            
            # 现代CSS特性
            'will-change', 'contain', 'isolation', 'mix-blend-mode',
            'object-fit', 'object-position', 'resize', 'user-select',
            'pointer-events', 'touch-action', 'scroll-behavior',
            
            # Flexbox和Grid（PyQt6支持有限）
            'flex-direction', 'flex-wrap', 'flex-flow', 'justify-content',
            'align-items', 'align-content', 'order', 'flex-grow', 'flex-shrink',
            'flex-basis', 'align-self',
            'grid-template-columns', 'grid-template-rows', 'grid-template-areas',
            'grid-column', 'grid-row', 'grid-area', 'gap', 'row-gap', 'column-gap',
            
            # 其他不支持的属性
            'appearance', 'outline-offset', 'tab-size', 'hyphens',
            'word-break', 'overflow-wrap', 'text-overflow-ellipsis'
        }
        
        # 需要特殊处理的属性值
        self.unsupported_values = {
            'display': {'flex', 'grid', 'inline-flex', 'inline-grid'},
            'position': {'sticky'},
            'overflow': {'overlay'},
            'white-space': {'break-spaces'}
        }
    
    def preprocess(self, css: str) -> str:
        """
        预处理CSS，移除所有不兼容的属性和值
        
        Args:
            css: 原始CSS字符串
            
        Returns:
            处理后的CSS字符串
        """
        if not css:
            return ""
        
        try:
            # 第一步：移除不支持的属性
            css = self._remove_unsupported_properties(css)
            
            # 第二步：替换不支持的属性值
            css = self._replace_unsupported_values(css)
            
            # 第三步：清理空规则和多余空白
            css = self._cleanup_css(css)
            
            return css
            
        except Exception:
            # 如果处理失败，返回空字符串以避免CSS错误
            return ""
    
    def _remove_unsupported_properties(self, css: str) -> str:
        """移除不支持的CSS属性"""
        lines = css.split('\n')
        processed_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            should_keep = True
            
            # 检查是否包含不支持的属性
            for prop in self.unsupported_properties:
                # 精确匹配CSS属性
                patterns = [
                    rf'^\s*{re.escape(prop)}\s*:',  # 行首
                    rf';\s*{re.escape(prop)}\s*:',  # 分号后
                    rf'{{\s*{re.escape(prop)}\s*:'  # 大括号后
                ]
                
                for pattern in patterns:
                    if re.search(pattern, line_stripped, re.IGNORECASE):
                        should_keep = False
                        break
                
                if not should_keep:
                    break
            
            if should_keep:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _replace_unsupported_values(self, css: str) -> str:
        """替换不支持的属性值"""
        for prop, unsupported_vals in self.unsupported_values.items():
            for val in unsupported_vals:
                # 替换不支持的值
                if prop == 'display':
                    if val in ['flex', 'inline-flex']:
                        css = re.sub(rf'{prop}\s*:\s*{val}', f'{prop}: block', css, flags=re.IGNORECASE)
                    elif val in ['grid', 'inline-grid']:
                        css = re.sub(rf'{prop}\s*:\s*{val}', f'{prop}: block', css, flags=re.IGNORECASE)
                elif prop == 'position':
                    if val == 'sticky':
                        css = re.sub(rf'{prop}\s*:\s*{val}', f'{prop}: relative', css, flags=re.IGNORECASE)
                elif prop == 'overflow':
                    if val == 'overlay':
                        css = re.sub(rf'{prop}\s*:\s*{val}', f'{prop}: auto', css, flags=re.IGNORECASE)
        
        return css
    
    def _cleanup_css(self, css: str) -> str:
        """清理CSS，移除空规则和多余空白"""
        # 移除空规则
        css = re.sub(r'[^{}]*{\s*}', '', css)
        
        # 移除多余的空行
        css = re.sub(r'\n\s*\n+', '\n', css)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in css.split('\n') if line.strip()]
        
        return '\n'.join(lines)

# 全局预处理器实例
_css_preprocessor = QtCSSPreprocessor()

def preprocess_css_for_qt(css: str) -> str:
    """
    为Qt预处理CSS的便捷函数
    
    Args:
        css: 原始CSS字符串
        
    Returns:
        处理后的CSS字符串
    """
    return _css_preprocessor.preprocess(css)

def apply_safe_css(widget, css: str):
    """
    安全地应用CSS到Qt组件
    
    Args:
        widget: Qt组件
        css: CSS字符串
    """
    try:
        processed_css = preprocess_css_for_qt(css)
        if processed_css:
            widget.setStyleSheet(processed_css)
    except Exception:
        # 如果应用失败，静默忽略
        pass

__all__ = [
    'QtCSSPreprocessor',
    'preprocess_css_for_qt', 
    'apply_safe_css'
]
