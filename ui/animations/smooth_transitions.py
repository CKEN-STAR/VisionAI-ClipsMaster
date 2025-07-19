"""
流畅过渡动画系统
提供界面元素的平滑过渡和动画效果
"""

import time
from typing import Dict, List, Optional, Any, Callable
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import (QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
                         QSequentialAnimationGroup, QTimer, pyqtSignal, QObject)
from PyQt6.QtGui import QColor

class AnimationManager(QObject):
    """动画管理器"""
    
    animation_started = pyqtSignal(str)  # 动画名称
    animation_finished = pyqtSignal(str)  # 动画名称
    
    def __init__(self):
        super().__init__()
        self.animations: Dict[str, QPropertyAnimation] = {}
        self.animation_groups: Dict[str, QParallelAnimationGroup] = {}
        self.is_animations_enabled = True
        self.default_duration = 300  # 默认动画时长(ms)
        self.default_easing = QEasingCurve.Type.OutCubic
    
    def set_animations_enabled(self, enabled: bool):
        """启用/禁用动画"""
        self.is_animations_enabled = enabled
    
    def set_default_duration(self, duration: int):
        """设置默认动画时长"""
        self.default_duration = max(50, duration)
    
    def fade_in(self, widget: QWidget, duration: int = None, 
                callback: Callable = None) -> str:
        """淡入动画"""
        if not self.is_animations_enabled:
            widget.setVisible(True)
            if callback:
                callback()
            return ""
        
        duration = duration or self.default_duration
        animation_id = f"fade_in_{id(widget)}_{time.time()}"
        
        # 设置透明度效果
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        # 创建动画
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(self.default_easing)
        
        # 设置回调
        if callback:
            animation.finished.connect(callback)
        
        # 显示组件并开始动画
        widget.setVisible(True)
        animation.start()
        
        # 保存动画引用
        self.animations[animation_id] = animation
        
        # 发送信号
        self.animation_started.emit(animation_id)
        animation.finished.connect(lambda: self.animation_finished.emit(animation_id))
        
        return animation_id
    
    def fade_out(self, widget: QWidget, duration: int = None, 
                 hide_after: bool = True, callback: Callable = None) -> str:
        """淡出动画"""
        if not self.is_animations_enabled:
            if hide_after:
                widget.setVisible(False)
            if callback:
                callback()
            return ""
        
        duration = duration or self.default_duration
        animation_id = f"fade_out_{id(widget)}_{time.time()}"
        
        # 获取或创建透明度效果
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)
        
        # 创建动画
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(self.default_easing)
        
        # 设置完成后隐藏
        def on_finished():
            if hide_after:
                widget.setVisible(False)
            if callback:
                callback()
        
        animation.finished.connect(on_finished)
        
        # 开始动画
        animation.start()
        
        # 保存动画引用
        self.animations[animation_id] = animation
        
        # 发送信号
        self.animation_started.emit(animation_id)
        animation.finished.connect(lambda: self.animation_finished.emit(animation_id))
        
        return animation_id
    
    def slide_in(self, widget: QWidget, direction: str = "left", 
                 duration: int = None, callback: Callable = None) -> str:
        """滑入动画"""
        if not self.is_animations_enabled:
            widget.setVisible(True)
            if callback:
                callback()
            return ""
        
        duration = duration or self.default_duration
        animation_id = f"slide_in_{direction}_{id(widget)}_{time.time()}"
        
        # 获取目标位置
        target_pos = widget.pos()
        
        # 设置起始位置
        if direction == "left":
            start_pos = target_pos + widget.rect().topLeft() - widget.rect().topRight()
        elif direction == "right":
            start_pos = target_pos + widget.rect().topRight() - widget.rect().topLeft()
        elif direction == "top":
            start_pos = target_pos + widget.rect().topLeft() - widget.rect().bottomLeft()
        else:  # bottom
            start_pos = target_pos + widget.rect().bottomLeft() - widget.rect().topLeft()
        
        widget.move(start_pos)
        widget.setVisible(True)
        
        # 创建位置动画
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(target_pos)
        animation.setEasingCurve(self.default_easing)
        
        # 设置回调
        if callback:
            animation.finished.connect(callback)
        
        # 开始动画
        animation.start()
        
        # 保存动画引用
        self.animations[animation_id] = animation
        
        # 发送信号
        self.animation_started.emit(animation_id)
        animation.finished.connect(lambda: self.animation_finished.emit(animation_id))
        
        return animation_id
    
    def scale_in(self, widget: QWidget, duration: int = None, 
                 callback: Callable = None) -> str:
        """缩放进入动画"""
        if not self.is_animations_enabled:
            widget.setVisible(True)
            if callback:
                callback()
            return ""
        
        duration = duration or self.default_duration
        animation_id = f"scale_in_{id(widget)}_{time.time()}"
        
        # 创建缩放动画组
        group = QParallelAnimationGroup()
        
        # 透明度动画
        opacity_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(opacity_effect)
        
        opacity_animation = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_animation.setDuration(duration)
        opacity_animation.setStartValue(0.0)
        opacity_animation.setEndValue(1.0)
        opacity_animation.setEasingCurve(self.default_easing)
        
        group.addAnimation(opacity_animation)
        
        # 设置回调
        if callback:
            group.finished.connect(callback)
        
        # 显示组件并开始动画
        widget.setVisible(True)
        group.start()
        
        # 保存动画引用
        self.animation_groups[animation_id] = group
        
        # 发送信号
        self.animation_started.emit(animation_id)
        group.finished.connect(lambda: self.animation_finished.emit(animation_id))
        
        return animation_id
    
    def bounce_in(self, widget: QWidget, duration: int = None, 
                  callback: Callable = None) -> str:
        """弹跳进入动画"""
        if not self.is_animations_enabled:
            widget.setVisible(True)
            if callback:
                callback()
            return ""
        
        duration = duration or self.default_duration
        animation_id = f"bounce_in_{id(widget)}_{time.time()}"
        
        # 创建序列动画组
        sequence = QSequentialAnimationGroup()
        
        # 透明度效果
        opacity_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(opacity_effect)
        
        # 第一阶段：快速放大并淡入
        phase1 = QParallelAnimationGroup()
        
        opacity1 = QPropertyAnimation(opacity_effect, b"opacity")
        opacity1.setDuration(duration // 3)
        opacity1.setStartValue(0.0)
        opacity1.setEndValue(1.0)
        opacity1.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        phase1.addAnimation(opacity1)
        sequence.addAnimation(phase1)
        
        # 第二阶段：轻微回弹
        phase2 = QParallelAnimationGroup()
        
        opacity2 = QPropertyAnimation(opacity_effect, b"opacity")
        opacity2.setDuration(duration // 3)
        opacity2.setStartValue(1.0)
        opacity2.setEndValue(0.9)
        opacity2.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        phase2.addAnimation(opacity2)
        sequence.addAnimation(phase2)
        
        # 第三阶段：稳定
        phase3 = QParallelAnimationGroup()
        
        opacity3 = QPropertyAnimation(opacity_effect, b"opacity")
        opacity3.setDuration(duration // 3)
        opacity3.setStartValue(0.9)
        opacity3.setEndValue(1.0)
        opacity3.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        phase3.addAnimation(opacity3)
        sequence.addAnimation(phase3)
        
        # 设置回调
        if callback:
            sequence.finished.connect(callback)
        
        # 显示组件并开始动画
        widget.setVisible(True)
        sequence.start()
        
        # 保存动画引用
        self.animation_groups[animation_id] = sequence
        
        # 发送信号
        self.animation_started.emit(animation_id)
        sequence.finished.connect(lambda: self.animation_finished.emit(animation_id))
        
        return animation_id
    
    def smooth_transition(self, from_widget: QWidget, to_widget: QWidget,
                         transition_type: str = "fade", duration: int = None,
                         callback: Callable = None) -> str:
        """平滑过渡动画"""
        if not self.is_animations_enabled:
            from_widget.setVisible(False)
            to_widget.setVisible(True)
            if callback:
                callback()
            return ""
        
        duration = duration or self.default_duration
        animation_id = f"transition_{transition_type}_{time.time()}"
        
        if transition_type == "fade":
            # 淡出旧组件，淡入新组件
            sequence = QSequentialAnimationGroup()
            
            # 淡出阶段
            fade_out_id = self.fade_out(from_widget, duration // 2, hide_after=True)
            
            # 延迟后淡入
            def start_fade_in():
                self.fade_in(to_widget, duration // 2, callback)
            
            QTimer.singleShot(duration // 2, start_fade_in)
            
        elif transition_type == "slide":
            # 滑动过渡
            # 这里可以实现更复杂的滑动过渡逻辑
            from_widget.setVisible(False)
            self.slide_in(to_widget, "left", duration, callback)
        
        return animation_id
    
    def stop_animation(self, animation_id: str):
        """停止指定动画"""
        if animation_id in self.animations:
            self.animations[animation_id].stop()
            del self.animations[animation_id]
        elif animation_id in self.animation_groups:
            self.animation_groups[animation_id].stop()
            del self.animation_groups[animation_id]
    
    def stop_all_animations(self):
        """停止所有动画"""
        for animation in self.animations.values():
            animation.stop()
        for group in self.animation_groups.values():
            group.stop()
        
        self.animations.clear()
        self.animation_groups.clear()
    
    def cleanup_finished_animations(self):
        """清理已完成的动画"""
        finished_animations = []
        for animation_id, animation in self.animations.items():
            if animation.state() == QPropertyAnimation.State.Stopped:
                finished_animations.append(animation_id)
        
        for animation_id in finished_animations:
            del self.animations[animation_id]
        
        finished_groups = []
        for group_id, group in self.animation_groups.items():
            if group.state() == QParallelAnimationGroup.State.Stopped:
                finished_groups.append(group_id)
        
        for group_id in finished_groups:
            del self.animation_groups[group_id]

# 全局动画管理器实例
_animation_manager = None

def get_animation_manager() -> AnimationManager:
    """获取全局动画管理器"""
    global _animation_manager
    if _animation_manager is None:
        _animation_manager = AnimationManager()
    return _animation_manager

def fade_in(widget: QWidget, duration: int = None, callback: Callable = None) -> str:
    """快捷淡入动画"""
    return get_animation_manager().fade_in(widget, duration, callback)

def fade_out(widget: QWidget, duration: int = None, hide_after: bool = True, 
             callback: Callable = None) -> str:
    """快捷淡出动画"""
    return get_animation_manager().fade_out(widget, duration, hide_after, callback)

def slide_in(widget: QWidget, direction: str = "left", duration: int = None, 
             callback: Callable = None) -> str:
    """快捷滑入动画"""
    return get_animation_manager().slide_in(widget, direction, duration, callback)

def bounce_in(widget: QWidget, duration: int = None, callback: Callable = None) -> str:
    """快捷弹跳动画"""
    return get_animation_manager().bounce_in(widget, duration, callback)

def smooth_transition(from_widget: QWidget, to_widget: QWidget,
                     transition_type: str = "fade", duration: int = None,
                     callback: Callable = None) -> str:
    """快捷过渡动画"""
    return get_animation_manager().smooth_transition(
        from_widget, to_widget, transition_type, duration, callback
    )

__all__ = [
    'AnimationManager',
    'get_animation_manager',
    'fade_in',
    'fade_out', 
    'slide_in',
    'bounce_in',
    'smooth_transition'
]
