"""
面板性能优化模块
提供UI面板的性能优化功能
"""

import os
import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap

class PanelOptimizer(QObject):
    """面板优化器"""
    
    optimization_completed = pyqtSignal(dict)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.optimization_cache: Dict[str, Any] = {}
        self.performance_stats = {
            'optimizations_applied': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time_saved': 0.0
        }
    
    def register_panel(self, panel: QWidget, panel_id: str = None) -> bool:
        """
        注册面板进行优化管理

        Args:
            panel: 要注册的面板
            panel_id: 面板ID，如果为None则自动生成

        Returns:
            是否成功注册
        """
        try:
            if not panel:
                return False

            if panel_id is None:
                panel_id = f"panel_{id(panel)}"

            # 存储面板信息
            self.optimization_cache[panel_id] = {
                'panel': panel,
                'registered_time': time.time(),
                'optimization_count': 0,
                'last_optimized': None
            }

            print(f"[OK] 面板已注册: {panel_id}")
            return True

        except Exception as e:
            print(f"[ERROR] 注册面板失败: {e}")
            return False

    def optimize_panel_rendering(self, panel: QWidget) -> bool:
        """
        优化面板渲染

        Args:
            panel: 要优化的面板

        Returns:
            是否成功优化
        """
        try:
            if not panel:
                return False

            start_time = time.time()

            # 应用渲染优化
            optimizations = []

            # 1. 启用双缓冲
            panel.setAttribute(panel.WidgetAttribute.WA_OpaquePaintEvent, True)
            optimizations.append("double_buffering")
            
            # 2. 优化更新策略
            panel.setUpdatesEnabled(True)
            optimizations.append("update_strategy")
            
            # 3. 设置合适的大小策略
            from PyQt6.QtWidgets import QSizePolicy
            panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            optimizations.append("size_policy")
            
            # 4. 启用样式表缓存
            if hasattr(panel, 'setStyleSheet'):
                current_style = panel.styleSheet()
                if current_style:
                    # 缓存样式表
                    style_hash = hash(current_style)
                    self.optimization_cache[f"style_{style_hash}"] = current_style
                    optimizations.append("stylesheet_cache")
            
            # 更新统计
            self.performance_stats['optimizations_applied'] += len(optimizations)
            optimization_time = time.time() - start_time
            self.performance_stats['total_time_saved'] += optimization_time
            
            # 发送完成信号
            result = {
                'panel': panel.objectName() or "unnamed_panel",
                'optimizations': optimizations,
                'time_taken': optimization_time
            }
            self.optimization_completed.emit(result)
            
            return True
            
        except Exception as e:
            print(f"[WARN] 面板渲染优化失败: {e}")
            return False
    
    def optimize_layout_performance(self, widget: QWidget) -> bool:
        """优化布局性能"""
        try:
            if not widget:
                return False
            
            layout = widget.layout()
            if layout:
                # 设置布局间距
                layout.setSpacing(2)
                layout.setContentsMargins(4, 4, 4, 4)
                
                # 优化布局更新
                layout.setSizeConstraint(layout.SizeConstraint.SetDefaultConstraint)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"[WARN] 布局性能优化失败: {e}")
            return False
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return self.performance_stats.copy()
    
    def clear_optimization_cache(self):
        """清除优化缓存"""
        self.optimization_cache.clear()

class ThumbnailGenerator(QThread):
    """缩略图生成器（异步）"""
    
    thumbnail_generated = pyqtSignal(str, str, bool)  # input_path, output_path, success
    
    def __init__(self, video_path: str, output_path: str, size: Tuple[int, int] = (160, 90)):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.size = size
    
    def run(self):
        """运行缩略图生成"""
        try:
            success = self._generate_thumbnail()
            self.thumbnail_generated.emit(self.video_path, self.output_path, success)
        except Exception as e:
            print(f"[WARN] 缩略图生成异常: {e}")
            self.thumbnail_generated.emit(self.video_path, self.output_path, False)
    
    def _generate_thumbnail(self) -> bool:
        """生成缩略图的实际实现"""
        try:
            # 检查输入文件
            if not Path(self.video_path).exists():
                return False
            
            # 创建输出目录
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 使用FFmpeg生成缩略图
            import subprocess
            
            cmd = [
                'ffmpeg',
                '-i', self.video_path,
                '-ss', '00:00:01',  # 从第1秒截取
                '-vframes', '1',
                '-vf', f'scale={self.size[0]}:{self.size[1]}',
                '-y',  # 覆盖输出文件
                self.output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and Path(self.output_path).exists():
                return True
            else:
                print(f"[WARN] FFmpeg缩略图生成失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("[WARN] 缩略图生成超时")
            return False
        except FileNotFoundError:
            print("[WARN] FFmpeg未找到，无法生成缩略图")
            return False
        except Exception as e:
            print(f"[WARN] 缩略图生成失败: {e}")
            return False

def generate_thumbnail(video_path: str, output_path: str, size: Tuple[int, int] = (160, 90)) -> bool:
    """
    同步生成缩略图
    
    Args:
        video_path: 视频文件路径
        output_path: 输出缩略图路径
        size: 缩略图尺寸
        
    Returns:
        是否成功生成
    """
    try:
        generator = ThumbnailGenerator(video_path, output_path, size)
        return generator._generate_thumbnail()
    except Exception as e:
        print(f"[WARN] 同步缩略图生成失败: {e}")
        return False

def create_async_thumbnail_generator(video_path: str, output_path: str, 
                                   size: Tuple[int, int] = (160, 90)) -> ThumbnailGenerator:
    """创建异步缩略图生成器"""
    return ThumbnailGenerator(video_path, output_path, size)

def optimize_widget_performance(widget: QWidget) -> bool:
    """
    优化组件性能的便捷函数
    
    Args:
        widget: 要优化的组件
        
    Returns:
        是否成功优化
    """
    optimizer = PanelOptimizer()
    return optimizer.optimize_panel_rendering(widget)

__all__ = [
    'PanelOptimizer',
    'ThumbnailGenerator',
    'generate_thumbnail',
    'create_async_thumbnail_generator',
    'optimize_widget_performance'
]
