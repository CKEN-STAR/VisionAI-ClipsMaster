"""
动画系统模块
提供流畅的界面过渡动画和视觉效果
"""

from .smooth_transitions import (
    AnimationManager,
    get_animation_manager,
    fade_in,
    fade_out,
    slide_in,
    bounce_in,
    smooth_transition
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
