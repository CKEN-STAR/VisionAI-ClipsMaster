#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
新手引导管理模块

管理新用户引导系统，提供分步骤教程和引导提示，
确保用户能够快速上手使用VisionAI-ClipsMaster应用。
"""

import os
import sys
import json
import logging
from typing import Dict, List, Callable, Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFrame, QProgressBar, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QPoint, QEvent, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QFont, QMovie

# 设置日志
logger = logging.getLogger("tutorial_manager")

class TutorialManager(QObject):
    """新手引导管理器
    
    提供新用户引导系统，管理教程步骤，显示帮助提示，
    实现交互式操作引导，确保用户能够快速了解系统功能。
    """
    
    # 自定义信号
    step_changed = pyqtSignal(int, str)  # 当前步骤索引, 步骤名称
    tutorial_completed = pyqtSignal()    # 教程完成信号
    tutorial_skipped = pyqtSignal()      # 教程跳过信号
    
    def __init__(self, parent=None):
        """初始化引导管理器
        
        Args:
            parent: 父对象，一般为主窗口
        """
        super().__init__(parent)
        
        # 父对象 - 需要为主窗口，用于获取UI组件
        self.parent = parent
        
        # 教程步骤定义
        self.tutorial_steps = [
            {
                "id": "import_tutorial",
                "name": "导入教学",
                "description": "学习如何导入视频和字幕文件",
                "target": "import_tab",  # 对应UI中的组件ID
                "position": "right",
                "progress": 25
            },
            {
                "id": "config_tutorial",
                "name": "参数配置",
                "description": "了解如何设置生成参数和模型配置",
                "target": "config_tab",
                "position": "right", 
                "progress": 50
            },
            {
                "id": "process_tutorial",
                "name": "处理视频",
                "description": "学习如何启动视频处理并监控进度",
                "target": "process_tab",
                "position": "right",
                "progress": 75
            },
            {
                "id": "export_tutorial",
                "name": "导出分享",
                "description": "掌握如何导出和分享你的成果",
                "target": "export_tab", 
                "position": "right",
                "progress": 100
            }
        ]
        
        # 当前状态
        self.current_step_index = 0
        self.current_popup = None
        self.completed_steps = []
        self.is_first_time_user = self._check_first_time_user()
        self.tutorial_enabled = self.is_first_time_user
        self.help_button_highlighted = False
        
        # 帮助按钮引用
        self.help_button = None
        
        # 用户数据路径
        self.user_data_path = Path("data/user")
        os.makedirs(self.user_data_path, exist_ok=True)
        
        # 用户配置文件
        self.user_config_file = self.user_data_path / "user_settings.json"
        self._load_user_config()
        
    def initialize(self, main_window):
        """初始化教程管理器
        
        Args:
            main_window: 主窗口对象，用于获取UI组件
        """
        self.parent = main_window
        
        # 查找帮助按钮
        self.help_button = self.parent.findChild(QPushButton, "help_button")
        
        # 如果是首次使用，自动启动教程
        if self.is_first_time_user and self.tutorial_enabled:
            self.start_tutorial()
    
    def _check_first_time_user(self) -> bool:
        """检查是否是首次使用
        
        Returns:
            bool: 是否是首次使用
        """
        # 检查用户配置文件是否存在
        user_config = Path("data/user/user_settings.json")
        return not user_config.exists()
    
    def _load_user_config(self):
        """加载用户配置"""
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 读取配置
                self.tutorial_enabled = config.get("tutorial_enabled", self.is_first_time_user)
                self.completed_steps = config.get("completed_tutorial_steps", [])
                
                logger.info("已加载用户配置")
            except Exception as e:
                logger.error(f"加载用户配置失败: {e}")
    
    def _save_user_config(self):
        """保存用户配置"""
        config = {
            "tutorial_enabled": self.tutorial_enabled,
            "completed_tutorial_steps": self.completed_steps,
            "first_use_completed": True
        }
        
        try:
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            logger.info("已保存用户配置")
        except Exception as e:
            logger.error(f"保存用户配置失败: {e}")
    
    def start_tutorial(self):
        """开始教程"""
        if not self.tutorial_enabled:
            return
        
        logger.info("开始新手引导教程")
        
        # 重置状态
        self.current_step_index = 0
        self.completed_steps = []
        
        # 显示欢迎弹窗
        self._show_welcome_dialog()
    
    def _show_welcome_dialog(self):
        """显示欢迎弹窗"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("欢迎使用VisionAI-ClipsMaster")
        dialog.setMinimumWidth(500)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        title = QLabel("欢迎使用VisionAI-ClipsMaster")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 描述
        description = QLabel(
            "这是您首次使用本应用，我们将为您提供简单的引导，帮助您快速掌握核心功能。\n"
            "您可以随时通过帮助菜单重新访问本教程。"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        skip_btn = QPushButton("跳过教程")
        skip_btn.clicked.connect(lambda: self._on_skip_tutorial(dialog))
        
        start_btn = QPushButton("开始教程")
        start_btn.setDefault(True)
        start_btn.clicked.connect(lambda: self._on_start_tutorial(dialog))
        
        btn_layout.addWidget(skip_btn)
        btn_layout.addWidget(start_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def _on_skip_tutorial(self, dialog):
        """跳过教程处理
        
        Args:
            dialog: 当前对话框
        """
        dialog.close()
        
        # 将所有步骤标记为完成
        self.completed_steps = [step["id"] for step in self.tutorial_steps]
        
        # 高亮帮助按钮
        self._highlight_help_button()
        
        # 保存用户配置
        self._save_user_config()
        
        # 发送信号
        self.tutorial_skipped.emit()
        logger.info("用户跳过教程")
    
    def _on_start_tutorial(self, dialog):
        """开始教程处理
        
        Args:
            dialog: 当前对话框
        """
        dialog.close()
        
        # 显示第一个步骤
        self._show_step(self.current_step_index)
        logger.info(f"开始教程步骤 {self.current_step_index+1}: {self.tutorial_steps[self.current_step_index]['name']}")
    
    def _show_step(self, step_index):
        """显示特定步骤
        
        Args:
            step_index: 步骤索引
        """
        if step_index < 0 or step_index >= len(self.tutorial_steps):
            logger.warning(f"无效的步骤索引: {step_index}")
            return
        
        # 获取当前步骤
        step = self.tutorial_steps[step_index]
        
        # 关闭现有弹窗
        if self.current_popup and not self.current_popup.isHidden():
            self.current_popup.close()
        
        # 创建新弹窗
        self.current_popup = TutorialPopup(
            parent=self.parent,
            title=step["name"],
            description=step["description"],
            progress=step["progress"],
            on_next=self._on_next_step,
            on_skip=self._on_skip_all_steps
        )
        
        # 查找目标组件
        target_widget = self.parent.findChild(QWidget, step["target"])
        
        if target_widget:
            # 计算弹窗位置
            self.current_popup.position_near_widget(target_widget, step["position"])
        else:
            # 居中显示
            self.current_popup.position_center()
            logger.warning(f"未找到目标组件: {step['target']}")
        
        # 显示弹窗
        self.current_popup.show()
        
        # 发送步骤变更信号
        self.step_changed.emit(step_index, step["name"])
    
    def _on_next_step(self):
        """处理下一步按钮点击"""
        # 标记当前步骤为已完成
        current_step = self.tutorial_steps[self.current_step_index]
        if current_step["id"] not in self.completed_steps:
            self.completed_steps.append(current_step["id"])
        
        # 保存用户配置
        self._save_user_config()
        
        # 移动到下一步
        self.current_step_index += 1
        
        # 检查是否完成所有步骤
        if self.current_step_index >= len(self.tutorial_steps):
            self._on_tutorial_complete()
            return
        
        # 显示下一步
        self._show_step(self.current_step_index)
        logger.info(f"进入教程步骤 {self.current_step_index+1}: {self.tutorial_steps[self.current_step_index]['name']}")
    
    def _on_skip_all_steps(self):
        """跳过所有步骤"""
        # 关闭当前弹窗
        if self.current_popup and not self.current_popup.isHidden():
            self.current_popup.close()
            self.current_popup = None
        
        # 将所有步骤标记为完成
        self.completed_steps = [step["id"] for step in self.tutorial_steps]
        
        # 保存用户配置
        self._save_user_config()
        
        # 高亮帮助按钮
        self._highlight_help_button()
        
        # 发送信号
        self.tutorial_skipped.emit()
        logger.info("用户跳过剩余教程步骤")
    
    def _on_tutorial_complete(self):
        """教程完成处理"""
        # 关闭当前弹窗
        if self.current_popup and not self.current_popup.isHidden():
            self.current_popup.close()
            self.current_popup = None
        
        # 显示完成对话框
        self._show_completion_dialog()
        
        # 高亮帮助按钮
        self._highlight_help_button()
        
        # 发送信号
        self.tutorial_completed.emit()
        logger.info("教程全部完成")
    
    def _show_completion_dialog(self):
        """显示完成对话框"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("教程完成")
        dialog.setMinimumWidth(400)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        title = QLabel("恭喜！")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 描述
        description = QLabel(
            "您已完成所有基础教程，现在可以开始使用VisionAI-ClipsMaster创建精彩内容了！\n\n"
            "如需进一步帮助，请点击界面右上角的帮助按钮。"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("开始使用")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def _highlight_help_button(self):
        """高亮帮助按钮"""
        if not self.help_button:
            logger.warning("未找到帮助按钮")
            return
        
        # 高亮样式
        self.help_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        
        self.help_button_highlighted = True
        logger.info("帮助按钮已高亮")
    
    def is_help_highlighted(self) -> bool:
        """检查帮助按钮是否高亮
        
        Returns:
            bool: 帮助按钮是否高亮
        """
        return self.help_button_highlighted
    
    def show_help(self):
        """显示帮助中心"""
        if not self.parent:
            logger.warning("未设置父窗口")
            return
        
        # 恢复帮助按钮正常样式
        if self.help_button_highlighted and self.help_button:
            self.help_button.setStyleSheet("")
            self.help_button_highlighted = False
        
        # 这里只是一个简单示例，实际应用中应调用帮助中心窗口
        QMessageBox.information(
            self.parent,
            "帮助中心",
            "这里是VisionAI-ClipsMaster的帮助中心。\n"
            "您可以在这里查看详细的使用文档和教程。"
        )


class TutorialPopup(QWidget):
    """教程弹窗
    
    显示教程步骤内容的弹出窗口，
    包含步骤说明、进度条和操作按钮。
    """
    
    def __init__(self, parent=None, title="", description="", progress=0, 
                 on_next=None, on_skip=None):
        """初始化教程弹窗
        
        Args:
            parent: 父窗口
            title: 步骤标题
            description: 步骤描述
            progress: 当前进度(0-100)
            on_next: 下一步回调
            on_skip: 跳过回调
        """
        super().__init__(parent)
        
        # 设置无边框窗口
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.Tool |
            Qt.WindowStaysOnTopHint
        )
        
        # 存储回调
        self.on_next_callback = on_next
        self.on_skip_callback = on_skip
        
        # 初始化UI
        self._init_ui(title, description, progress)
        
        # 设置样式
        self._set_style()
    
    def _init_ui(self, title, description, progress):
        """初始化UI
        
        Args:
            title: 步骤标题
            description: 步骤描述
            progress: 当前进度(0-100)
        """
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 描述
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setMinimumWidth(300)
        layout.addWidget(description_label)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_label = QLabel("教程进度:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(progress)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        # 跳过按钮
        skip_btn = QPushButton("跳过教程")
        skip_btn.clicked.connect(self._on_skip)
        
        # 下一步按钮
        next_btn = QPushButton("下一步")
        next_btn.setDefault(True)
        next_btn.clicked.connect(self._on_next)
        
        btn_layout.addWidget(skip_btn)
        btn_layout.addWidget(next_btn)
        layout.addLayout(btn_layout)
        
        # 设置大小策略
        self.setSizePolicy(
            QWidget.Fixed, 
            QWidget.Fixed
        )
    
    def _set_style(self):
        """设置样式"""
        self.setStyleSheet("""
            TutorialPopup {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            QPushButton {
                min-width: 80px;
                padding: 5px;
            }
            QProgressBar {
                text-align: center;
            }
        """)
    
    def position_near_widget(self, widget, position="right"):
        """将弹窗定位在指定组件附近
        
        Args:
            widget: 目标组件
            position: 位置(right, left, top, bottom)
        """
        if not widget:
            self.position_center()
            return
        
        # 获取目标组件的全局位置
        target_pos = widget.mapToGlobal(QPoint(0, 0))
        target_size = widget.size()
        
        # 计算弹窗位置
        popup_size = self.sizeHint()
        
        if position == "right":
            x = target_pos.x() + target_size.width() + 10
            y = target_pos.y() + (target_size.height() - popup_size.height()) // 2
        elif position == "left":
            x = target_pos.x() - popup_size.width() - 10
            y = target_pos.y() + (target_size.height() - popup_size.height()) // 2
        elif position == "top":
            x = target_pos.x() + (target_size.width() - popup_size.width()) // 2
            y = target_pos.y() - popup_size.height() - 10
        elif position == "bottom":
            x = target_pos.x() + (target_size.width() - popup_size.width()) // 2
            y = target_pos.y() + target_size.height() + 10
        else:
            # 默认右侧
            x = target_pos.x() + target_size.width() + 10
            y = target_pos.y()
        
        # 移动到计算位置
        self.move(x, y)
    
    def position_center(self):
        """将弹窗居中显示"""
        # 获取屏幕几何信息
        screen_geometry = self.screen().geometry()
        popup_size = self.sizeHint()
        
        # 计算中心位置
        x = (screen_geometry.width() - popup_size.width()) // 2
        y = (screen_geometry.height() - popup_size.height()) // 2
        
        # 移动到中心位置
        self.move(x, y)
    
    def _on_next(self):
        """下一步按钮点击处理"""
        self.close()
        if self.on_next_callback:
            self.on_next_callback()
    
    def _on_skip(self):
        """跳过按钮点击处理"""
        self.close()
        if self.on_skip_callback:
            self.on_skip_callback() 