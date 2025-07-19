"""
增强CSS处理器
提供CSS兼容性处理和优化功能
"""

import re
from typing import Dict, List, Tuple, Any

def process_css_for_qt(css: str) -> str:
    """
    处理CSS使其与Qt兼容 - 智能版本

    Args:
        css: 原始CSS字符串

    Returns:
        处理后的CSS字符串
    """
    if not css:
        return ""

    try:
        # 完整的不支持CSS属性列表
        unsupported_properties = [
            'box-shadow', 'text-shadow', 'transform', 'transition', 'animation',
            'opacity', 'filter', 'clip-path', 'mask', 'backdrop-filter',
            'perspective', 'transform-origin', 'animation-delay', 'animation-duration',
            'animation-iteration-count', 'animation-name', 'animation-timing-function',
            'animation-fill-mode', 'animation-direction', 'animation-play-state',
            'transition-delay', 'transition-duration', 'transition-property',
            'transition-timing-function', 'transform-style', 'backface-visibility',
            'will-change', 'contain', 'isolation', 'mix-blend-mode',
            'object-fit', 'object-position', 'resize', 'user-select',
            'pointer-events', 'touch-action', 'scroll-behavior'
        ]

        # 按行处理CSS
        lines = css.split('\n')
        processed_lines = []

        for line in lines:
            line_stripped = line.strip()
            should_keep = True

            # 检查是否包含不支持的属性
            for prop in unsupported_properties:
                # 更精确的匹配模式
                patterns = [
                    rf'^\s*{re.escape(prop)}\s*:',  # 行首的属性
                    rf';\s*{re.escape(prop)}\s*:',  # 分号后的属性
                    rf'{{\s*{re.escape(prop)}\s*:'  # 大括号后的属性
                ]

                for pattern in patterns:
                    if re.search(pattern, line_stripped, re.IGNORECASE):
                        should_keep = False
                        break

                if not should_keep:
                    break

            if should_keep:
                processed_lines.append(line)

        # 重新组合CSS
        processed_css = '\n'.join(processed_lines)

        # 清理多余的空行和空白
        processed_css = re.sub(r'\n\s*\n+', '\n', processed_css)
        processed_css = re.sub(r'{\s*\n\s*}', '{}', processed_css)  # 移除空规则

        return processed_css.strip()

    except Exception as e:
        # 静默处理错误，返回原始CSS
        return css

def validate_css_compatibility(css: str) -> Dict[str, List[str]]:
    """
    验证CSS兼容性
    
    Args:
        css: CSS字符串
        
    Returns:
        包含支持和不支持属性的字典
    """
    if not css:
        return {'supported': [], 'unsupported': []}
    
    try:
        # Qt支持的CSS属性列表
        supported_properties = [
            'color', 'background-color', 'background-image',
            'border', 'border-color', 'border-width', 'border-style',
            'margin', 'padding', 'font-family', 'font-size', 'font-weight',
            'text-align', 'width', 'height', 'min-width', 'min-height',
            'max-width', 'max-height'
        ]
        
        # 提取CSS中的属性
        property_pattern = r'([a-zA-Z-]+)\s*:'
        found_properties = re.findall(property_pattern, css)
        
        supported = []
        unsupported = []
        
        for prop in set(found_properties):
            if prop.lower() in supported_properties:
                supported.append(prop)
            else:
                unsupported.append(prop)
        
        return {
            'supported': supported,
            'unsupported': unsupported
        }
        
    except Exception as e:
        print(f"[WARN] CSS兼容性验证失败: {e}")
        return {'supported': [], 'unsupported': []}

def optimize_css_for_performance(css: str) -> str:
    """
    优化CSS性能
    
    Args:
        css: 原始CSS
        
    Returns:
        优化后的CSS
    """
    if not css:
        return ""
    
    try:
        # 移除注释
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
        
        # 移除多余的空白
        css = re.sub(r'\s+', ' ', css)
        css = re.sub(r';\s*}', '}', css)
        css = re.sub(r'{\s*', '{', css)
        css = re.sub(r'}\s*', '}', css)
        
        return css.strip()
        
    except Exception as e:
        print(f"[WARN] CSS优化失败: {e}")
        return css

def get_css_processing_stats() -> Dict[str, Any]:
    """获取CSS处理统计信息"""
    return {
        'processor_version': '1.0.0',
        'supported_features': [
            'property_filtering',
            'compatibility_validation', 
            'performance_optimization'
        ],
        'qt_compatibility': True
    }

__all__ = [
    'process_css_for_qt',
    'validate_css_compatibility',
    'optimize_css_for_performance',
    'get_css_processing_stats'
]
