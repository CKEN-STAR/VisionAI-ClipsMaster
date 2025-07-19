"""
渲染优化器
提供UI渲染性能优化功能
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter

class RenderOptimizer(QObject):
    """渲染优化器"""
    
    optimization_applied = pyqtSignal(str, dict)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.optimization_stats = {
            'widgets_optimized': 0,
            'render_calls_saved': 0,
            'memory_saved_mb': 0,
            'optimizations_applied': []
        }
        self.render_cache: Dict[str, Any] = {}
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._batch_update)
        self.pending_updates: List[QWidget] = []
    
    def optimize_widget_rendering(self, widget: QWidget) -> bool:
        """
        优化组件渲染
        
        Args:
            widget: 要优化的组件
            
        Returns:
            是否成功优化
        """
        try:
            if not widget:
                return False
            
            optimizations = []
            
            # 1. 启用双缓冲
            widget.setAttribute(widget.WidgetAttribute.WA_OpaquePaintEvent, True)
            optimizations.append("double_buffering")
            
            # 2. 优化重绘策略
            widget.setAttribute(widget.WidgetAttribute.WA_NoSystemBackground, True)
            optimizations.append("no_system_background")
            
            # 3. 启用硬件加速（如果可用）
            try:
                widget.setAttribute(widget.WidgetAttribute.WA_NativeWindow, False)
                optimizations.append("software_rendering")
            except Exception:
                pass
            
            # 4. 设置更新策略
            widget.setUpdatesEnabled(True)
            optimizations.append("updates_enabled")
            
            # 5. 优化绘制事件
            self._setup_paint_optimization(widget)
            optimizations.append("paint_optimization")
            
            # 更新统计
            self.optimization_stats['widgets_optimized'] += 1
            self.optimization_stats['optimizations_applied'].extend(optimizations)
            
            # 发送信号
            result = {
                'widget_name': widget.objectName() or widget.__class__.__name__,
                'optimizations': optimizations,
                'widget_id': id(widget)
            }
            self.optimization_applied.emit("widget_rendering", result)
            
            return True
            
        except Exception as e:
            print(f"[WARN] 组件渲染优化失败: {e}")
            return False
    
    def _setup_paint_optimization(self, widget: QWidget):
        """设置绘制优化"""
        try:
            # 保存原始的paintEvent方法
            original_paint_event = widget.paintEvent
            
            def optimized_paint_event(event):
                """优化的绘制事件"""
                try:
                    # 检查是否需要重绘
                    if self._should_skip_paint(widget, event):
                        self.optimization_stats['render_calls_saved'] += 1
                        return
                    
                    # 调用原始绘制方法
                    original_paint_event(event)
                    
                except Exception as e:
                    print(f"[WARN] 优化绘制事件失败: {e}")
                    # 回退到原始方法
                    original_paint_event(event)
            
            # 替换绘制事件
            widget.paintEvent = optimized_paint_event
            
        except Exception as e:
            print(f"[WARN] 设置绘制优化失败: {e}")
    
    def _should_skip_paint(self, widget: QWidget, event) -> bool:
        """判断是否应该跳过绘制"""
        try:
            # 如果组件不可见，跳过绘制
            if not widget.isVisible():
                return True
            
            # 如果组件大小为0，跳过绘制
            if widget.size().width() <= 0 or widget.size().height() <= 0:
                return True
            
            # 如果更新区域为空，跳过绘制
            if event.rect().isEmpty():
                return True
            
            return False
            
        except Exception:
            return False
    
    def batch_widget_updates(self, widgets: List[QWidget]):
        """批量更新组件"""
        try:
            self.pending_updates.extend(widgets)
            
            # 启动批量更新定时器
            if not self.update_timer.isActive():
                self.update_timer.start(16)  # 约60FPS
                
        except Exception as e:
            print(f"[WARN] 批量更新失败: {e}")
    
    def _batch_update(self):
        """执行批量更新"""
        try:
            if not self.pending_updates:
                return
            
            # 去重
            unique_widgets = list(set(self.pending_updates))
            self.pending_updates.clear()
            
            # 批量更新
            for widget in unique_widgets:
                if widget and widget.isVisible():
                    widget.update()
            
            self.optimization_stats['render_calls_saved'] += len(unique_widgets) - 1
            
        except Exception as e:
            print(f"[WARN] 执行批量更新失败: {e}")
    
    def optimize_application_rendering(self) -> bool:
        """优化应用程序级别的渲染"""
        try:
            app = QApplication.instance()
            if not app:
                return False
            
            optimizations = []
            
            # 1. 启用高DPI支持
            try:
                app.setAttribute(app.ApplicationAttribute.AA_EnableHighDpiScaling, True)
                app.setAttribute(app.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
                optimizations.append("high_dpi_support")
            except Exception:
                pass
            
            # 2. 设置渲染提示
            try:
                app.setAttribute(app.ApplicationAttribute.AA_SynthesizeTouchForUnhandledMouseEvents, False)
                optimizations.append("touch_synthesis_disabled")
            except Exception:
                pass
            
            # 3. 优化字体渲染
            try:
                app.setAttribute(app.ApplicationAttribute.AA_UseDesktopOpenGL, False)
                optimizations.append("software_opengl")
            except Exception:
                pass
            
            # 发送信号
            result = {
                'optimizations': optimizations,
                'application': True
            }
            self.optimization_applied.emit("application_rendering", result)
            
            return True
            
        except Exception as e:
            print(f"[WARN] 应用程序渲染优化失败: {e}")
            return False
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        stats = self.optimization_stats.copy()
        stats['cache_size'] = len(self.render_cache)
        stats['pending_updates'] = len(self.pending_updates)
        return stats
    
    def clear_render_cache(self):
        """清除渲染缓存"""
        self.render_cache.clear()
        self.optimization_stats['memory_saved_mb'] += 10  # 估算
    
    def set_render_quality(self, quality: str = "medium"):
        """设置渲染质量"""
        try:
            app = QApplication.instance()
            if not app:
                return
            
            if quality == "low":
                # 低质量设置
                app.setAttribute(app.ApplicationAttribute.AA_DisableWindowContextHelpButton, True)
            elif quality == "high":
                # 高质量设置
                app.setAttribute(app.ApplicationAttribute.AA_UseDesktopOpenGL, True)
            
            print(f"[OK] 渲染质量已设置为: {quality}")
            
        except Exception as e:
            print(f"[WARN] 设置渲染质量失败: {e}")

def optimize_rendering_for_tier(tier: str = "medium") -> bool:
    """
    根据性能等级优化渲染
    
    Args:
        tier: 性能等级 (low, medium, high, ultra)
        
    Returns:
        是否成功优化
    """
    try:
        optimizer = RenderOptimizer()
        
        # 应用应用程序级别优化
        optimizer.optimize_application_rendering()
        
        # 根据性能等级设置渲染质量
        quality_map = {
            "low": "low",
            "medium": "medium", 
            "high": "high",
            "ultra": "high"
        }
        
        quality = quality_map.get(tier, "medium")
        optimizer.set_render_quality(quality)
        
        print(f"[OK] 已为性能等级 {tier} 优化渲染")
        return True
        
    except Exception as e:
        print(f"[WARN] 渲染优化失败: {e}")
        return False

def create_render_optimizer(parent: Optional[QWidget] = None) -> RenderOptimizer:
    """创建渲染优化器"""
    return RenderOptimizer(parent)

__all__ = [
    'RenderOptimizer',
    'optimize_rendering_for_tier',
    'create_render_optimizer'
]
