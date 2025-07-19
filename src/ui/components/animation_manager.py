#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动画管理器模块

为VisionAI-ClipsMaster提供情感化UI动画效果，
增强用户体验，创造愉悦的交互感受。
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Callable
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QWidget, QLabel, QGraphicsOpacityEffect, QApplication
    )
    from PyQt6.QtCore import (
        Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
        QSequentialAnimationGroup, QPoint, QSize, QTimer
    )
    from PyQt6.QtGui import QPixmap, QMovie, QColor
    HAS_PYQT = True
except ImportError:
    try:
        # 回退到PyQt5
        from PyQt5.QtWidgets import (
            QWidget, QLabel, QGraphicsOpacityEffect, QApplication
        )
        from PyQt5.QtCore import (
            Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
            QSequentialAnimationGroup, QPoint, QSize, QTimer
        )
        from PyQt5.QtGui import QPixmap, QMovie, QColor
        HAS_PYQT = True
        logging.info("使用PyQt5作为动画后端")
    except ImportError:
        logging.warning("未安装PyQt6或PyQt5，动画功能将受限")
        HAS_PYQT = False
        # 创建虚拟类以避免NameError
        class QWidget:
            pass

# 设置日志
logger = logging.getLogger("animation_manager")

class AnimationManager:
    """动画管理器类
    
    管理应用中的各种动画效果，包括加载动画、完成动画、
    转场效果等，提供情感化的用户界面体验。
    """
    
    def __init__(self):
        """初始化动画管理器"""
        # 已注册的动画效果
        self.animations = {}
        
        # 缓存的动画资源
        self.animation_resources = {}
        
        # 动画配置
        self.config = {
            "enabled": True,  # 全局动画开关
            "quality": "high",  # 动画质量 (high, medium, low)
            "duration_factor": 1.0,  # 动画持续时间因子
        }
        
        # 加载动画配置
        self._load_config()
        
        # 初始化动画
        self._register_default_animations()
        
        logger.info("动画管理器初始化完成")
    
    def _load_config(self):
        """从配置文件加载动画设置"""
        try:
            # 检查配置目录和文件
            config_path = Path("configs/ui_settings.yaml")
            if not config_path.exists():
                logger.warning(f"动画配置文件不存在: {config_path}，使用默认设置")
                return
                
            # 加载动画配置
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 提取动画配置
            if 'animations' in config:
                animation_config = config['animations']
                
                # 更新配置
                if 'enabled' in animation_config:
                    self.config['enabled'] = bool(animation_config['enabled'])
                
                if 'quality' in animation_config:
                    quality = animation_config['quality']
                    if quality in ['high', 'medium', 'low']:
                        self.config['quality'] = quality
                
                if 'duration_factor' in animation_config:
                    factor = float(animation_config['duration_factor'])
                    if 0.1 <= factor <= 2.0:
                        self.config['duration_factor'] = factor
                
                logger.info(f"已加载动画配置: {self.config}")
                
        except Exception as e:
            logger.warning(f"加载动画配置失败: {e}，使用默认设置")
    
    def _register_default_animations(self):
        """注册默认动画效果"""
        # 注册完成任务特效
        self.register_animation(
            "完成任务特效", 
            self._create_completion_animation,
            "任务完成时的庆祝动画"
        )
        
        # 注册生成完成烟花特效
        self.register_animation(
            "生成完成烟花特效",
            self._create_fireworks_animation,
            "视频生成完成时的烟花庆祝特效"
        )
        
        # 注册导入成功动画
        self.register_animation(
            "导入成功动画",
            self._create_import_success_animation,
            "文件导入成功时的确认动画"
        )
        
        # 注册加载完成动画
        self.register_animation(
            "成功完成加载动画",
            self._create_loading_complete_animation,
            "加载完成时的过渡动画"
        )
        
        # 注册保存成功动画
        self.register_animation(
            "保存成功动画",
            self._create_save_success_animation,
            "文件保存成功时的确认动画"
        )
    
    def register_animation(self, name: str, creator_func: Callable, description: str = ""):
        """注册新的动画效果
        
        Args:
            name: 动画名称
            creator_func: 创建动画的函数
            description: 动画描述
        """
        if name in self.animations:
            logger.warning(f"动画'{name}'已存在，将被覆盖")
        
        self.animations[name] = {
            "creator": creator_func,
            "description": description,
            "last_used": None  # 记录最后使用时间，可用于性能优化
        }
        
        logger.info(f"已注册动画: {name}")
    
    def play_animation(self, name: str, target_widget: Optional[QWidget] = None, **kwargs):
        """播放指定动画
        
        Args:
            name: 动画名称
            target_widget: 目标控件
            **kwargs: 动画参数
            
        Returns:
            bool: 是否成功播放
        """
        # 检查动画是否启用
        if not self.config['enabled']:
            logger.info(f"动画已全局禁用，跳过播放'{name}'")
            return False
        
        # 检查动画是否存在
        if name not in self.animations:
            logger.warning(f"动画'{name}'不存在")
            return False
        
        try:
            # 获取动画创建函数
            creator_func = self.animations[name]["creator"]
            
            # 创建并播放动画
            import time
            self.animations[name]["last_used"] = time.time()
            
            # 调用创建函数
            animation = creator_func(target_widget, **kwargs)
            
            if animation:
                # 如果是QMovie，直接开始
                if isinstance(animation, QMovie):
                    animation.start()
                    return True
                
                # 如果是Qt动画，启动它
                animation.start()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"播放动画'{name}'失败: {e}")
            return False
    
    def stop_all_animations(self):
        """停止所有正在播放的动画"""
        # 这个功能在真实实现中需要跟踪所有活动动画
        # 简单版本可以在这里添加
        pass
    
    def _create_completion_animation(self, target_widget=None, **kwargs):
        """创建完成任务特效动画
        
        Args:
            target_widget: 目标控件
            **kwargs: 动画参数
            
        Returns:
            动画对象
        """
        if not HAS_PYQT or not target_widget:
            return None
        
        # 创建庆祝标签
        celebration_label = QLabel(target_widget)
        
        # 根据质量选择不同的动画
        if self.config['quality'] == 'low':
            # 简单文本动画
            celebration_label.setText("✓ 已完成!")
            celebration_label.setStyleSheet("color: green; font-size: 20px; font-weight: bold;")
            celebration_label.adjustSize()
            
            # 放置在合适位置
            if target_widget:
                x = (target_widget.width() - celebration_label.width()) // 2
                y = (target_widget.height() - celebration_label.height()) // 2
                celebration_label.move(x, y)
            
            # 创建淡入淡出动画
            opacity_effect = QGraphicsOpacityEffect(celebration_label)
            celebration_label.setGraphicsEffect(opacity_effect)
            
            animation = QPropertyAnimation(opacity_effect, b"opacity")
            animation.setDuration(int(1000 * self.config['duration_factor']))
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.InOutQuad)
            
            # 设置动画结束后的处理
            animation.finished.connect(lambda: self._cleanup_animation(celebration_label))
            
            # 显示标签
            celebration_label.show()
            
            return animation
            
        else:
            # 高质量 - 使用GIF动画
            try:
                movie_path = "assets/animations/completion.gif"
                if not Path(movie_path).exists():
                    logger.warning(f"动画资源不存在: {movie_path}")
                    return None
                
                movie = QMovie(movie_path)
                celebration_label.setMovie(movie)
                celebration_label.adjustSize()
                
                # 放置在合适位置
                if target_widget:
                    x = (target_widget.width() - celebration_label.width()) // 2
                    y = (target_widget.height() - celebration_label.height()) // 2
                    celebration_label.move(x, y)
                
                # 设置动画结束后的处理
                movie.finished.connect(lambda: self._cleanup_animation(celebration_label, movie))
                
                # 显示标签
                celebration_label.show()
                
                return movie
                
            except Exception as e:
                logger.error(f"创建完成动画失败: {e}")
                return None
    
    def _create_fireworks_animation(self, target_widget=None, **kwargs):
        """创建烟花庆祝特效动画
        
        Args:
            target_widget: 目标控件
            **kwargs: 动画参数
            
        Returns:
            动画对象
        """
        if not HAS_PYQT or not target_widget:
            return None
        
        # 创建烟花标签
        fireworks_label = QLabel(target_widget)
        
        # 根据质量选择不同的动画
        if self.config['quality'] == 'low':
            # 简单文本动画
            fireworks_label.setText("✨ 生成完成! ✨")
            fireworks_label.setStyleSheet("color: #FF5722; font-size: 24px; font-weight: bold;")
            fireworks_label.adjustSize()
            
            # 放置在合适位置
            if target_widget:
                x = (target_widget.width() - fireworks_label.width()) // 2
                y = (target_widget.height() - fireworks_label.height()) // 2
                fireworks_label.move(x, y)
            
            # 创建动画组
            animation_group = QSequentialAnimationGroup()
            
            # 1. 缩放动画
            scale_animation = QPropertyAnimation(fireworks_label, b"geometry")
            scale_animation.setDuration(int(500 * self.config['duration_factor']))
            start_rect = fireworks_label.geometry()
            end_rect = start_rect.adjusted(-10, -10, 10, 10)  # 稍微放大
            scale_animation.setStartValue(start_rect)
            scale_animation.setEndValue(end_rect)
            scale_animation.setEasingCurve(QEasingCurve.OutBack)
            
            # 2. 等待
            # 添加延迟
            QTimer.singleShot(
                int(1000 * self.config['duration_factor']), 
                lambda: self._cleanup_animation(fireworks_label)
            )
            
            # 添加动画到组
            animation_group.addAnimation(scale_animation)
            
            # 显示标签
            fireworks_label.show()
            
            return animation_group
            
        else:
            # 高质量 - 使用GIF动画
            try:
                movie_path = "assets/animations/fireworks.gif"
                if not Path(movie_path).exists():
                    logger.warning(f"动画资源不存在: {movie_path}")
                    return None
                
                movie = QMovie(movie_path)
                fireworks_label.setMovie(movie)
                fireworks_label.adjustSize()
                
                # 放置在合适位置
                if target_widget:
                    x = (target_widget.width() - fireworks_label.width()) // 2
                    y = (target_widget.height() - fireworks_label.height()) // 2
                    fireworks_label.move(x, y)
                
                # 设置动画结束后的处理
                movie.finished.connect(lambda: self._cleanup_animation(fireworks_label, movie))
                
                # 显示标签
                fireworks_label.show()
                
                return movie
                
            except Exception as e:
                logger.error(f"创建烟花动画失败: {e}")
                return None
    
    def _create_import_success_animation(self, target_widget=None, **kwargs):
        """创建导入成功动画
        
        Args:
            target_widget: 目标控件
            **kwargs: 动画参数
            
        Returns:
            动画对象
        """
        if not HAS_PYQT or not target_widget:
            return None
        
        # 创建成功标签
        success_label = QLabel(target_widget)
        
        # 根据质量选择不同的动画
        if self.config['quality'] == 'low':
            # 简单文本动画
            success_label.setText("✓ 导入成功")
            success_label.setStyleSheet("color: #4CAF50; font-size: 18px;")
            success_label.adjustSize()
            
            # 放置在合适位置
            if target_widget:
                x = (target_widget.width() - success_label.width()) // 2
                y = (target_widget.height() - success_label.height()) // 2
                success_label.move(x, y)
            
            # 创建淡入淡出动画
            opacity_effect = QGraphicsOpacityEffect(success_label)
            success_label.setGraphicsEffect(opacity_effect)
            
            animation = QPropertyAnimation(opacity_effect, b"opacity")
            animation.setDuration(int(800 * self.config['duration_factor']))
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.InOutQuad)
            
            # 设置动画结束后的处理
            animation.finished.connect(lambda: QTimer.singleShot(
                500, lambda: self._cleanup_animation(success_label)
            ))
            
            # 显示标签
            success_label.show()
            
            return animation
            
        else:
            # 高质量 - 使用GIF动画或自定义动画
            try:
                # 检查是否有可用的GIF资源
                movie_path = "assets/animations/import_success.gif"
                if Path(movie_path).exists():
                    movie = QMovie(movie_path)
                    success_label.setMovie(movie)
                    success_label.adjustSize()
                    
                    # 放置在合适位置
                    if target_widget:
                        x = (target_widget.width() - success_label.width()) // 2
                        y = (target_widget.height() - success_label.height()) // 2
                        success_label.move(x, y)
                    
                    # 设置动画结束后的处理
                    movie.finished.connect(lambda: self._cleanup_animation(success_label, movie))
                    
                    # 显示标签
                    success_label.show()
                    
                    return movie
                else:
                    # 创建自定义动画
                    success_label.setText("✓ 导入成功")
                    success_label.setStyleSheet("color: #4CAF50; font-size: 18px; font-weight: bold;")
                    success_label.adjustSize()
                    
                    # 放置在合适位置
                    if target_widget:
                        x = (target_widget.width() - success_label.width()) // 2
                        y = (target_widget.height() - success_label.height()) // 2
                        success_label.move(x, y)
                    
                    # 创建复合动画
                    animation_group = QSequentialAnimationGroup()
                    
                    # 1. 淡入动画
                    opacity_effect = QGraphicsOpacityEffect(success_label)
                    success_label.setGraphicsEffect(opacity_effect)
                    
                    fade_in = QPropertyAnimation(opacity_effect, b"opacity")
                    fade_in.setDuration(int(400 * self.config['duration_factor']))
                    fade_in.setStartValue(0.0)
                    fade_in.setEndValue(1.0)
                    fade_in.setEasingCurve(QEasingCurve.InOutQuad)
                    
                    # 2. 移动动画
                    move_animation = QPropertyAnimation(success_label, b"pos")
                    move_animation.setDuration(int(300 * self.config['duration_factor']))
                    current_pos = success_label.pos()
                    move_animation.setStartValue(current_pos)
                    move_animation.setEndValue(QPoint(current_pos.x(), current_pos.y() - 10))
                    move_animation.setEasingCurve(QEasingCurve.OutQuad)
                    
                    # 添加动画到组
                    animation_group.addAnimation(fade_in)
                    animation_group.addAnimation(move_animation)
                    
                    # 设置动画结束后的处理
                    animation_group.finished.connect(lambda: QTimer.singleShot(
                        500, lambda: self._cleanup_animation(success_label)
                    ))
                    
                    # 显示标签
                    success_label.show()
                    
                    return animation_group
                    
            except Exception as e:
                logger.error(f"创建导入成功动画失败: {e}")
                return None
    
    def _create_loading_complete_animation(self, target_widget=None, **kwargs):
        """创建加载完成动画
        
        Args:
            target_widget: 目标控件
            **kwargs: 动画参数
            
        Returns:
            动画对象
        """
        # 实现类似于导入成功的动画，但样式不同
        if not HAS_PYQT or not target_widget:
            return None
        
        # 创建完成标签
        complete_label = QLabel(target_widget)
        
        # 根据质量选择不同的动画
        if self.config['quality'] == 'low':
            # 简单文本动画
            complete_label.setText("✓ 加载完成")
            complete_label.setStyleSheet("color: #2196F3; font-size: 18px;")
            complete_label.adjustSize()
            
            # 放置在合适位置
            if target_widget:
                x = (target_widget.width() - complete_label.width()) // 2
                y = (target_widget.height() - complete_label.height()) // 2
                complete_label.move(x, y)
            
            # 创建淡入动画
            opacity_effect = QGraphicsOpacityEffect(complete_label)
            complete_label.setGraphicsEffect(opacity_effect)
            
            animation = QPropertyAnimation(opacity_effect, b"opacity")
            animation.setDuration(int(700 * self.config['duration_factor']))
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.InQuad)
            
            # 设置动画结束后的处理
            animation.finished.connect(lambda: QTimer.singleShot(
                800, lambda: self._cleanup_animation(complete_label)
            ))
            
            # 显示标签
            complete_label.show()
            
            return animation
            
        else:
            # 高质量 - 使用自定义动画
            try:
                complete_label.setText("✓ 加载完成")
                complete_label.setStyleSheet("color: #2196F3; font-size: 18px; font-weight: bold;")
                complete_label.adjustSize()
                
                # 放置在合适位置
                if target_widget:
                    x = (target_widget.width() - complete_label.width()) // 2
                    y = (target_widget.height() - complete_label.height()) // 2
                    complete_label.move(x, y)
                
                # 创建复合动画
                animation_group = QParallelAnimationGroup()
                
                # 1. 淡入动画
                opacity_effect = QGraphicsOpacityEffect(complete_label)
                complete_label.setGraphicsEffect(opacity_effect)
                
                fade_in = QPropertyAnimation(opacity_effect, b"opacity")
                fade_in.setDuration(int(500 * self.config['duration_factor']))
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                fade_in.setEasingCurve(QEasingCurve.OutCubic)
                
                # 2. 移动动画
                move_animation = QPropertyAnimation(complete_label, b"pos")
                move_animation.setDuration(int(500 * self.config['duration_factor']))
                current_pos = complete_label.pos()
                move_animation.setStartValue(QPoint(current_pos.x(), current_pos.y() + 20))
                move_animation.setEndValue(current_pos)
                move_animation.setEasingCurve(QEasingCurve.OutBack)
                
                # 添加动画到组
                animation_group.addAnimation(fade_in)
                animation_group.addAnimation(move_animation)
                
                # 设置动画结束后的处理
                animation_group.finished.connect(lambda: QTimer.singleShot(
                    1000, lambda: self._cleanup_animation(complete_label)
                ))
                
                # 显示标签
                complete_label.show()
                
                return animation_group
                
            except Exception as e:
                logger.error(f"创建加载完成动画失败: {e}")
                return None
    
    def _create_save_success_animation(self, target_widget=None, **kwargs):
        """创建保存成功动画
        
        Args:
            target_widget: 目标控件
            **kwargs: 动画参数
            
        Returns:
            动画对象
        """
        if not HAS_PYQT or not target_widget:
            return None
        
        # 创建保存成功标签
        save_label = QLabel(target_widget)
        
        # 根据质量选择不同的动画
        if self.config['quality'] == 'low':
            # 简单文本动画
            save_label.setText("✓ 保存成功")
            save_label.setStyleSheet("color: #673AB7; font-size: 18px;")
            save_label.adjustSize()
            
            # 放置在合适位置
            if target_widget:
                x = (target_widget.width() - save_label.width()) // 2
                y = (target_widget.height() - save_label.height()) // 2
                save_label.move(x, y)
            
            # 创建淡入淡出动画
            opacity_effect = QGraphicsOpacityEffect(save_label)
            save_label.setGraphicsEffect(opacity_effect)
            
            animation = QPropertyAnimation(opacity_effect, b"opacity")
            animation.setDuration(int(800 * self.config['duration_factor']))
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.InOutQuad)
            
            # 设置动画结束后的处理
            animation.finished.connect(lambda: QTimer.singleShot(
                500, lambda: self._cleanup_animation(save_label)
            ))
            
            # 显示标签
            save_label.show()
            
            return animation
            
        else:
            # 高质量 - 使用自定义动画
            try:
                save_label.setText("✓ 保存成功")
                save_label.setStyleSheet("color: #673AB7; font-size: 18px; font-weight: bold;")
                save_label.adjustSize()
                
                # 放置在合适位置
                if target_widget:
                    x = (target_widget.width() - save_label.width()) // 2
                    y = (target_widget.height() - save_label.height()) // 2
                    save_label.move(x, y)
                
                # 创建复合动画
                animation_group = QSequentialAnimationGroup()
                
                # 1. 淡入+缩放动画
                opacity_effect = QGraphicsOpacityEffect(save_label)
                save_label.setGraphicsEffect(opacity_effect)
                
                parallel_group = QParallelAnimationGroup()
                
                fade_in = QPropertyAnimation(opacity_effect, b"opacity")
                fade_in.setDuration(int(400 * self.config['duration_factor']))
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                fade_in.setEasingCurve(QEasingCurve.OutCubic)
                
                # 缩放动画
                scale_animation = QPropertyAnimation(save_label, b"geometry")
                scale_animation.setDuration(int(400 * self.config['duration_factor']))
                start_rect = save_label.geometry()
                smaller_rect = start_rect.adjusted(10, 5, -10, -5)  # 稍微缩小
                scale_animation.setStartValue(smaller_rect)
                scale_animation.setEndValue(start_rect)
                scale_animation.setEasingCurve(QEasingCurve.OutBack)
                
                parallel_group.addAnimation(fade_in)
                parallel_group.addAnimation(scale_animation)
                
                # 添加动画到组
                animation_group.addAnimation(parallel_group)
                
                # 设置动画结束后的处理
                animation_group.finished.connect(lambda: QTimer.singleShot(
                    800, lambda: self._cleanup_animation(save_label)
                ))
                
                # 显示标签
                save_label.show()
                
                return animation_group
                
            except Exception as e:
                logger.error(f"创建保存成功动画失败: {e}")
                return None
    
    def _cleanup_animation(self, widget, movie=None):
        """清理动画资源
        
        Args:
            widget: 要清理的控件
            movie: 可选，要清理的动画对象
        """
        try:
            if movie:
                movie.stop()
            
            # 使用淡出动画
            opacity_effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(opacity_effect)
            
            fade_out = QPropertyAnimation(opacity_effect, b"opacity")
            fade_out.setDuration(int(300 * self.config['duration_factor']))
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.OutQuad)
            
            # 动画结束后销毁控件
            fade_out.finished.connect(widget.deleteLater)
            
            fade_out.start()
            
        except Exception as e:
            logger.error(f"清理动画资源失败: {e}")
            # 直接尝试删除控件
            try:
                widget.deleteLater()
            except:
                pass

# 单例模式
_animation_manager_instance = None

def get_animation_manager():
    """获取动画管理器实例
    
    Returns:
        AnimationManager: 动画管理器实例
    """
    global _animation_manager_instance
    if _animation_manager_instance is None:
        _animation_manager_instance = AnimationManager()
    return _animation_manager_instance

def find_animation(animation_name):
    """查找并验证指定动画是否存在
    
    Args:
        animation_name: 动画名称
        
    Returns:
        bool: 动画是否存在并正常
    """
    # 获取动画管理器
    manager = get_animation_manager()
    
    # 检查动画是否存在
    return animation_name in manager.animations

def play_animation(animation_name, target_widget=None, **kwargs):
    """播放指定动画
    
    Args:
        animation_name: 动画名称
        target_widget: 目标控件
        **kwargs: 动画参数
        
    Returns:
        bool: 是否成功播放
    """
    # 获取动画管理器
    manager = get_animation_manager()
    
    # 播放动画
    return manager.play_animation(animation_name, target_widget, **kwargs)

# 测试动画
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    test_window = QWidget()
    test_window.setWindowTitle("动画测试")
    test_window.setGeometry(100, 100, 400, 300)
    
    # 创建测试按钮
    from PyQt5.QtWidgets import QPushButton, QVBoxLayout
    
    layout = QVBoxLayout(test_window)
    
    # 测试完成任务特效
    complete_btn = QPushButton("测试完成任务特效")
    complete_btn.clicked.connect(lambda: play_animation("完成任务特效", test_window))
    layout.addWidget(complete_btn)
    
    # 测试烟花特效
    fireworks_btn = QPushButton("测试烟花特效")
    fireworks_btn.clicked.connect(lambda: play_animation("生成完成烟花特效", test_window))
    layout.addWidget(fireworks_btn)
    
    # 测试导入成功动画
    import_btn = QPushButton("测试导入成功动画")
    import_btn.clicked.connect(lambda: play_animation("导入成功动画", test_window))
    layout.addWidget(import_btn)
    
    # 测试加载完成动画
    load_btn = QPushButton("测试加载完成动画")
    load_btn.clicked.connect(lambda: play_animation("成功完成加载动画", test_window))
    layout.addWidget(load_btn)
    
    # 测试保存成功动画
    save_btn = QPushButton("测试保存成功动画")
    save_btn.clicked.connect(lambda: play_animation("保存成功动画", test_window))
    layout.addWidget(save_btn)
    
    test_window.show()
    
    sys.exit(app.exec_()) 