
import re

class CSSCompatibilityProcessor:
    """CSS兼容性处理器"""
    
    def __init__(self):
        self.compatibility_map = {
            'transform': '',  # PyQt6不支持，移除
            'box-shadow': 'border: 1px solid #ddd;',  # 用边框替代
            'text-shadow': '',  # 移除不支持的属性
            'transition': '',  # 移除不支持的属性
            'animation': '',   # 移除不支持的属性
            'filter': '',  # 移除filter属性
            'backdrop-filter': '',  # 移除backdrop-filter属性
        }

        # 统计信息
        self.warnings_removed = 0
        self.properties_replaced = 0
        
    def process_css(self, css_text):
        """处理CSS文本，移除不兼容属性"""
        if not css_text:
            return css_text

        original_css = css_text
        self.warnings_removed = 0
        self.properties_replaced = 0

        # 移除不支持的属性
        for prop, replacement in self.compatibility_map.items():
            # 匹配属性及其值
            pattern = rf'{prop}\s*:[^;]*;?'
            matches = re.findall(pattern, css_text, flags=re.IGNORECASE)

            if matches:
                self.warnings_removed += len(matches)
                if replacement:
                    css_text = re.sub(pattern, replacement, css_text, flags=re.IGNORECASE)
                    self.properties_replaced += len(matches)
                else:
                    css_text = re.sub(pattern, '', css_text, flags=re.IGNORECASE)

        # 清理多余的空行和空格
        css_text = re.sub(r'\n\s*\n', '\n', css_text)
        css_text = re.sub(r'{\s*}', '', css_text)  # 移除空的CSS规则
        css_text = re.sub(r';\s*;', ';', css_text)  # 移除重复的分号
        
        return css_text.strip()
        
    def validate_css(self, css_text):
        """验证CSS兼容性"""
        unsupported_props = []
        for prop in self.compatibility_map.keys():
            if prop in css_text.lower():
                unsupported_props.append(prop)
                
        return {
            'is_compatible': len(unsupported_props) == 0,
            'unsupported_properties': unsupported_props
        }

    def get_processing_stats(self):
        """获取处理统计信息"""
        return {
            'warnings_removed': self.warnings_removed,
            'properties_replaced': self.properties_replaced,
            'total_processed': self.warnings_removed
        }

    def reset_stats(self):
        """重置统计信息"""
        self.warnings_removed = 0
        self.properties_replaced = 0

# 全局CSS处理器实例
css_processor = CSSCompatibilityProcessor()

def get_css_processing_stats():
    """获取CSS处理统计信息"""
    return css_processor.get_processing_stats()
