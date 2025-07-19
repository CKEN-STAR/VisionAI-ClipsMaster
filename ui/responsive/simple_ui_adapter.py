"""
简单UI适配器
提供UI响应式适配功能
"""

from typing import Optional, Dict, Any
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QWidget, QApplication

class SimpleUIAdapter:
    """简单UI适配器"""
    
    def __init__(self):
        self.screen_info = self._get_screen_info()
        self.adaptation_rules = self._get_adaptation_rules()
        self.applied_adaptations: list = []
    
    def _get_screen_info(self) -> Dict[str, Any]:
        """获取屏幕信息"""
        try:
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    geometry = screen.geometry()
                    return {
                        'width': geometry.width(),
                        'height': geometry.height(),
                        'dpi': screen.logicalDotsPerInch(),
                        'device_pixel_ratio': screen.devicePixelRatio()
                    }
            
            # 默认值
            return {
                'width': 1920,
                'height': 1080,
                'dpi': 96,
                'device_pixel_ratio': 1.0
            }
            
        except Exception as e:
            print(f"[WARN] 获取屏幕信息失败: {e}")
            return {
                'width': 1920,
                'height': 1080,
                'dpi': 96,
                'device_pixel_ratio': 1.0
            }
    
    def _get_adaptation_rules(self) -> Dict[str, Any]:
        """获取适配规则"""
        return {
            'small_screen': {
                'max_width': 1366,
                'max_height': 768,
                'font_scale': 0.9,
                'spacing_scale': 0.8,
                'button_scale': 0.9
            },
            'large_screen': {
                'min_width': 2560,
                'min_height': 1440,
                'font_scale': 1.2,
                'spacing_scale': 1.2,
                'button_scale': 1.1
            },
            'high_dpi': {
                'min_dpi': 144,
                'font_scale': 1.1,
                'spacing_scale': 1.0,
                'button_scale': 1.0
            }
        }
    
    def adapt_widget(self, widget: QWidget) -> bool:
        """
        适配组件
        
        Args:
            widget: 要适配的组件
            
        Returns:
            是否成功适配
        """
        try:
            if not widget:
                return False
            
            adaptations = []
            
            # 检查屏幕尺寸适配
            if self._is_small_screen():
                adaptations.extend(self._apply_small_screen_adaptation(widget))
            elif self._is_large_screen():
                adaptations.extend(self._apply_large_screen_adaptation(widget))
            
            # 检查高DPI适配
            if self._is_high_dpi():
                adaptations.extend(self._apply_high_dpi_adaptation(widget))
            
            # 应用通用适配
            adaptations.extend(self._apply_general_adaptation(widget))
            
            self.applied_adaptations.extend(adaptations)
            
            if adaptations:
                print(f"[OK] 组件适配完成: {adaptations}")
            
            return True
            
        except Exception as e:
            print(f"[WARN] 组件适配失败: {e}")
            return False
    
    def _is_small_screen(self) -> bool:
        """是否为小屏幕"""
        rules = self.adaptation_rules['small_screen']
        return (self.screen_info['width'] <= rules['max_width'] or 
                self.screen_info['height'] <= rules['max_height'])
    
    def _is_large_screen(self) -> bool:
        """是否为大屏幕"""
        rules = self.adaptation_rules['large_screen']
        return (self.screen_info['width'] >= rules['min_width'] and 
                self.screen_info['height'] >= rules['min_height'])
    
    def _is_high_dpi(self) -> bool:
        """是否为高DPI"""
        rules = self.adaptation_rules['high_dpi']
        return self.screen_info['dpi'] >= rules['min_dpi']
    
    def _apply_small_screen_adaptation(self, widget: QWidget) -> list:
        """应用小屏幕适配"""
        adaptations = []
        
        try:
            rules = self.adaptation_rules['small_screen']
            
            # 调整最小尺寸
            current_size = widget.minimumSize()
            if current_size.width() > 0 and current_size.height() > 0:
                new_width = int(current_size.width() * rules['button_scale'])
                new_height = int(current_size.height() * rules['button_scale'])
                widget.setMinimumSize(QSize(new_width, new_height))
                adaptations.append("small_screen_size_adjusted")
            
            # 调整字体（如果可能）
            if hasattr(widget, 'font'):
                font = widget.font()
                font.setPointSizeF(font.pointSizeF() * rules['font_scale'])
                widget.setFont(font)
                adaptations.append("small_screen_font_scaled")
            
        except Exception as e:
            print(f"[WARN] 小屏幕适配失败: {e}")
        
        return adaptations
    
    def _apply_large_screen_adaptation(self, widget: QWidget) -> list:
        """应用大屏幕适配"""
        adaptations = []
        
        try:
            rules = self.adaptation_rules['large_screen']
            
            # 调整字体
            if hasattr(widget, 'font'):
                font = widget.font()
                font.setPointSizeF(font.pointSizeF() * rules['font_scale'])
                widget.setFont(font)
                adaptations.append("large_screen_font_scaled")
            
            # 调整间距（如果是布局）
            layout = widget.layout()
            if layout:
                current_spacing = layout.spacing()
                new_spacing = int(current_spacing * rules['spacing_scale'])
                layout.setSpacing(new_spacing)
                adaptations.append("large_screen_spacing_adjusted")
            
        except Exception as e:
            print(f"[WARN] 大屏幕适配失败: {e}")
        
        return adaptations
    
    def _apply_high_dpi_adaptation(self, widget: QWidget) -> list:
        """应用高DPI适配"""
        adaptations = []
        
        try:
            rules = self.adaptation_rules['high_dpi']
            
            # 调整字体
            if hasattr(widget, 'font'):
                font = widget.font()
                font.setPointSizeF(font.pointSizeF() * rules['font_scale'])
                widget.setFont(font)
                adaptations.append("high_dpi_font_scaled")
            
            # 启用高DPI支持
            widget.setAttribute(widget.WidgetAttribute.AA_EnableHighDpiScaling, True)
            adaptations.append("high_dpi_scaling_enabled")
            
        except Exception as e:
            print(f"[WARN] 高DPI适配失败: {e}")
        
        return adaptations
    
    def _apply_general_adaptation(self, widget: QWidget) -> list:
        """应用通用适配"""
        adaptations = []
        
        try:
            # 启用自动调整大小
            if hasattr(widget, 'setAutoFillBackground'):
                widget.setAutoFillBackground(True)
                adaptations.append("auto_fill_background_enabled")
            
            # 设置合适的大小策略
            from PyQt6.QtWidgets import QSizePolicy
            widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            adaptations.append("size_policy_set")
            
        except Exception as e:
            print(f"[WARN] 通用适配失败: {e}")
        
        return adaptations
    
    def get_screen_info(self) -> Dict[str, Any]:
        """获取屏幕信息"""
        return self.screen_info.copy()
    
    def get_applied_adaptations(self) -> list:
        """获取已应用的适配"""
        return self.applied_adaptations.copy()
    
    def get_adaptation_report(self) -> str:
        """获取适配报告"""
        try:
            report = [
                "=== UI适配报告 ===",
                f"屏幕尺寸: {self.screen_info['width']}x{self.screen_info['height']}",
                f"DPI: {self.screen_info['dpi']}",
                f"设备像素比: {self.screen_info['device_pixel_ratio']}",
                "",
                "屏幕类型:",
                f"  小屏幕: {'是' if self._is_small_screen() else '否'}",
                f"  大屏幕: {'是' if self._is_large_screen() else '否'}",
                f"  高DPI: {'是' if self._is_high_dpi() else '否'}",
                "",
                "已应用的适配:",
            ]
            
            for adaptation in set(self.applied_adaptations):
                report.append(f"  ✓ {adaptation}")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"生成适配报告失败: {e}"

# 全局适配器实例
_ui_adapter: Optional[SimpleUIAdapter] = None

def get_ui_adapter() -> SimpleUIAdapter:
    """获取全局UI适配器"""
    global _ui_adapter
    if _ui_adapter is None:
        _ui_adapter = SimpleUIAdapter()
    return _ui_adapter

def integrate_responsive_features(widget: QWidget) -> bool:
    """集成响应式功能"""
    adapter = get_ui_adapter()
    return adapter.adapt_widget(widget)

def adapt_widget_for_screen(widget: QWidget) -> bool:
    """为屏幕适配组件"""
    return integrate_responsive_features(widget)

def get_screen_adaptation_info() -> Dict[str, Any]:
    """获取屏幕适配信息"""
    adapter = get_ui_adapter()
    return adapter.get_screen_info()

__all__ = [
    'SimpleUIAdapter',
    'get_ui_adapter',
    'integrate_responsive_features',
    'adapt_widget_for_screen',
    'get_screen_adaptation_info'
]
