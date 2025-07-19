#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 异常处理组件
处理错误提示和操作确认弹窗
"""

import sys
import os
import time
import json
import traceback
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QMessageBox, QDialog, 
                               QDialogButtonBox, QFrame, QListWidget, QListWidgetItem,
                               QGroupBox, QCheckBox, QComboBox, QSpinBox,
                               QProgressDialog, QInputDialog, QFileDialog)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
    from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

class AlertType(Enum):
    """警告类型枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"

class AlertLevel(Enum):
    """警告级别枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class CustomMessageBox(QDialog):
    """自定义消息框"""
    
    def __init__(self, title: str, message: str, alert_type: AlertType = AlertType.INFO, 
                 buttons: List[str] = None, parent=None):
        super().__init__(parent)
        
        self.result_value = None
        self.alert_type = alert_type
        
        if buttons is None:
            buttons = ["确定"]
        
        self.init_ui(title, message, buttons)
    
    def init_ui(self, title: str, message: str, buttons: List[str]):
        """初始化UI"""
        if not QT_AVAILABLE:
            return
            
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # 图标和消息区域
        content_layout = QHBoxLayout()
        
        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 根据类型设置图标和颜色
        if self.alert_type == AlertType.ERROR:
            icon_label.setStyleSheet("background-color: red; color: white; font-size: 24px; border-radius: 24px;")
            icon_label.setText("✗")
        elif self.alert_type == AlertType.WARNING:
            icon_label.setStyleSheet("background-color: orange; color: white; font-size: 24px; border-radius: 24px;")
            icon_label.setText("!")
        elif self.alert_type == AlertType.SUCCESS:
            icon_label.setStyleSheet("background-color: green; color: white; font-size: 24px; border-radius: 24px;")
            icon_label.setText("✓")
        elif self.alert_type == AlertType.CRITICAL:
            icon_label.setStyleSheet("background-color: darkred; color: white; font-size: 24px; border-radius: 24px;")
            icon_label.setText("⚠")
        else:  # INFO
            icon_label.setStyleSheet("background-color: blue; color: white; font-size: 24px; border-radius: 24px;")
            icon_label.setText("i")
        
        content_layout.addWidget(icon_label)
        
        # 消息文本
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        content_layout.addWidget(message_label)
        
        layout.addLayout(content_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        for button_text in buttons:
            btn = QPushButton(button_text)
            btn.clicked.connect(lambda checked, text=button_text: self.button_clicked(text))
            button_layout.addWidget(btn)
        
        layout.addLayout(button_layout)
    
    def button_clicked(self, button_text: str):
        """按钮点击处理"""
        self.result_value = button_text
        self.accept()
    
    def get_result(self) -> str:
        """获取结果"""
        return self.result_value

class ConfirmationDialog(QDialog):
    """确认对话框"""
    
    def __init__(self, title: str, message: str, details: str = None, parent=None):
        super().__init__(parent)
        
        self.confirmed = False
        self.init_ui(title, message, details)
    
    def init_ui(self, title: str, message: str, details: str = None):
        """初始化UI"""
        if not QT_AVAILABLE:
            return
            
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 150)
        
        layout = QVBoxLayout(self)
        
        # 主消息
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 10))
        layout.addWidget(message_label)
        
        # 详细信息（可选）
        if details:
            details_group = QGroupBox("详细信息")
            details_layout = QVBoxLayout(details_group)
            
            details_text = QTextEdit()
            details_text.setPlainText(details)
            details_text.setMaximumHeight(100)
            details_text.setReadOnly(True)
            details_layout.addWidget(details_text)
            
            layout.addWidget(details_group)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_action)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept_action(self):
        """确认操作"""
        self.confirmed = True
        self.accept()
    
    def is_confirmed(self) -> bool:
        """是否确认"""
        return self.confirmed

class AlertManager(QWidget):
    """异常处理管理器主类"""
    
    # 信号定义
    alert_triggered = pyqtSignal(str, str, str)  # level, title, message
    confirmation_requested = pyqtSignal(str, str)  # title, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 警告历史记录
        self.alert_history = []
        self.max_history = 100
        
        # 配置
        self.config = {
            "show_notifications": True,
            "auto_dismiss_timeout": 5000,  # 毫秒
            "sound_enabled": True,
            "log_alerts": True
        }
        
        # 多语言支持
        self.language = "zh_CN"
        self.translations = {
            "zh_CN": {
                "title": "异常处理管理器",
                "alert_history": "警告历史",
                "clear_history": "清空历史",
                "settings": "设置",
                "show_notifications": "显示通知",
                "auto_dismiss": "自动关闭",
                "sound_enabled": "启用声音",
                "log_alerts": "记录警告",
                "test_alerts": "测试警告",
                "info_test": "信息测试",
                "warning_test": "警告测试", 
                "error_test": "错误测试",
                "critical_test": "严重错误测试",
                "success_test": "成功测试",
                "confirmation_test": "确认对话框测试"
            },
            "en_US": {
                "title": "Alert Manager",
                "alert_history": "Alert History",
                "clear_history": "Clear History",
                "settings": "Settings",
                "show_notifications": "Show Notifications",
                "auto_dismiss": "Auto Dismiss",
                "sound_enabled": "Sound Enabled",
                "log_alerts": "Log Alerts",
                "test_alerts": "Test Alerts",
                "info_test": "Info Test",
                "warning_test": "Warning Test",
                "error_test": "Error Test", 
                "critical_test": "Critical Test",
                "success_test": "Success Test",
                "confirmation_test": "Confirmation Test"
            }
        }
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        if not QT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(self.tr("title"))
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 设置面板
        settings_panel = self.create_settings_panel()
        layout.addWidget(settings_panel)
        
        # 测试面板
        test_panel = self.create_test_panel()
        layout.addWidget(test_panel)
        
        # 历史记录面板
        history_panel = self.create_history_panel()
        layout.addWidget(history_panel)
    
    def create_settings_panel(self) -> QGroupBox:
        """创建设置面板"""
        group = QGroupBox(self.tr("settings"))
        layout = QVBoxLayout(group)
        
        # 设置选项
        self.show_notifications_cb = QCheckBox(self.tr("show_notifications"))
        self.show_notifications_cb.setChecked(self.config["show_notifications"])
        self.show_notifications_cb.toggled.connect(
            lambda checked: self.update_config("show_notifications", checked)
        )
        layout.addWidget(self.show_notifications_cb)
        
        self.sound_enabled_cb = QCheckBox(self.tr("sound_enabled"))
        self.sound_enabled_cb.setChecked(self.config["sound_enabled"])
        self.sound_enabled_cb.toggled.connect(
            lambda checked: self.update_config("sound_enabled", checked)
        )
        layout.addWidget(self.sound_enabled_cb)
        
        self.log_alerts_cb = QCheckBox(self.tr("log_alerts"))
        self.log_alerts_cb.setChecked(self.config["log_alerts"])
        self.log_alerts_cb.toggled.connect(
            lambda checked: self.update_config("log_alerts", checked)
        )
        layout.addWidget(self.log_alerts_cb)
        
        # 自动关闭超时设置
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel(self.tr("auto_dismiss") + ":"))
        
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(1000, 30000)
        self.timeout_spinbox.setValue(self.config["auto_dismiss_timeout"])
        self.timeout_spinbox.setSuffix(" ms")
        self.timeout_spinbox.valueChanged.connect(
            lambda value: self.update_config("auto_dismiss_timeout", value)
        )
        timeout_layout.addWidget(self.timeout_spinbox)
        
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)
        
        return group
    
    def create_test_panel(self) -> QGroupBox:
        """创建测试面板"""
        group = QGroupBox(self.tr("test_alerts"))
        layout = QHBoxLayout(group)
        
        # 测试按钮
        test_buttons = [
            ("info_test", AlertType.INFO),
            ("warning_test", AlertType.WARNING),
            ("error_test", AlertType.ERROR),
            ("critical_test", AlertType.CRITICAL),
            ("success_test", AlertType.SUCCESS)
        ]
        
        for button_key, alert_type in test_buttons:
            btn = QPushButton(self.tr(button_key))
            btn.clicked.connect(lambda checked, at=alert_type: self.test_alert(at))
            layout.addWidget(btn)
        
        # 确认对话框测试
        confirm_btn = QPushButton(self.tr("confirmation_test"))
        confirm_btn.clicked.connect(self.test_confirmation)
        layout.addWidget(confirm_btn)
        
        return group
    
    def create_history_panel(self) -> QGroupBox:
        """创建历史记录面板"""
        group = QGroupBox(self.tr("alert_history"))
        layout = QVBoxLayout(group)
        
        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(150)
        layout.addWidget(self.history_list)
        
        # 清空按钮
        clear_btn = QPushButton(self.tr("clear_history"))
        clear_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_btn)
        
        return group
    
    def show_alert(self, title: str, message: str, alert_type: AlertType = AlertType.INFO, 
                   buttons: List[str] = None) -> str:
        """显示警告对话框"""
        if not QT_AVAILABLE:
            return "OK"
            
        # 记录到历史
        self.add_to_history(alert_type, title, message)
        
        # 显示对话框
        if self.config["show_notifications"]:
            dialog = CustomMessageBox(title, message, alert_type, buttons, self)
            dialog.exec()
            return dialog.get_result()
        
        return "OK"
    
    def show_confirmation(self, title: str, message: str, details: str = None) -> bool:
        """显示确认对话框"""
        if not QT_AVAILABLE:
            return True
            
        dialog = ConfirmationDialog(title, message, details, self)
        dialog.exec()
        return dialog.is_confirmed()
    
    def show_info(self, title: str, message: str) -> str:
        """显示信息对话框"""
        return self.show_alert(title, message, AlertType.INFO)
    
    def show_warning(self, title: str, message: str) -> str:
        """显示警告对话框"""
        return self.show_alert(title, message, AlertType.WARNING)
    
    def show_error(self, title: str, message: str) -> str:
        """显示错误对话框"""
        return self.show_alert(title, message, AlertType.ERROR)
    
    def show_critical(self, title: str, message: str) -> str:
        """显示严重错误对话框"""
        return self.show_alert(title, message, AlertType.CRITICAL)
    
    def show_success(self, title: str, message: str) -> str:
        """显示成功对话框"""
        return self.show_alert(title, message, AlertType.SUCCESS)
    
    def add_to_history(self, alert_type: AlertType, title: str, message: str):
        """添加到历史记录"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        history_item = {
            "timestamp": timestamp,
            "type": alert_type.value,
            "title": title,
            "message": message
        }
        
        self.alert_history.append(history_item)
        
        # 限制历史记录数量
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        # 更新历史显示
        self.update_history_display()
        
        # 记录日志
        if self.config["log_alerts"]:
            print(f"[{timestamp}] {alert_type.value.upper()}: {title} - {message}")
    
    def update_history_display(self):
        """更新历史显示"""
        if not QT_AVAILABLE:
            return
            
        self.history_list.clear()
        
        for item in reversed(self.alert_history[-20:]):  # 只显示最近20条
            display_text = f"[{item['timestamp']}] {item['type'].upper()}: {item['title']}"
            
            list_item = QListWidgetItem(display_text)
            
            # 根据类型设置颜色
            if item['type'] == AlertType.ERROR.value:
                list_item.setBackground(QColor(255, 200, 200))
            elif item['type'] == AlertType.WARNING.value:
                list_item.setBackground(QColor(255, 255, 200))
            elif item['type'] == AlertType.SUCCESS.value:
                list_item.setBackground(QColor(200, 255, 200))
            elif item['type'] == AlertType.CRITICAL.value:
                list_item.setBackground(QColor(255, 150, 150))
            
            self.history_list.addItem(list_item)
    
    def clear_history(self):
        """清空历史记录"""
        self.alert_history.clear()
        self.update_history_display()
    
    def test_alert(self, alert_type: AlertType):
        """测试警告"""
        test_messages = {
            AlertType.INFO: ("信息测试", "这是一个信息提示测试"),
            AlertType.WARNING: ("警告测试", "这是一个警告提示测试"),
            AlertType.ERROR: ("错误测试", "这是一个错误提示测试"),
            AlertType.CRITICAL: ("严重错误测试", "这是一个严重错误提示测试"),
            AlertType.SUCCESS: ("成功测试", "这是一个成功提示测试")
        }
        
        title, message = test_messages[alert_type]
        self.show_alert(title, message, alert_type)
    
    def test_confirmation(self):
        """测试确认对话框"""
        result = self.show_confirmation(
            "确认测试",
            "这是一个确认对话框测试，请选择确定或取消。",
            "详细信息：这里可以显示更多的操作详情。"
        )
        
        if result:
            self.show_success("确认结果", "用户选择了确定")
        else:
            self.show_info("确认结果", "用户选择了取消")
    
    def update_config(self, key: str, value: Any):
        """更新配置"""
        self.config[key] = value
    
    def tr(self, key: str) -> str:
        """翻译函数"""
        return self.translations.get(self.language, {}).get(key, key)
    
    def set_language(self, language: str):
        """设置语言"""
        if language in self.translations:
            self.language = language
