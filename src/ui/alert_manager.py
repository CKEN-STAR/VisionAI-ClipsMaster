#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 警告管理器
提供系统警告、错误处理和用户通知功能

功能特性：
1. 多级别警告系统（信息、警告、错误、严重）
2. 用户友好的错误消息
3. 自动错误恢复建议
4. 防重复弹窗机制
"""

import sys
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QMessageBox, QFrame, QTextEdit,
                                QScrollArea, QApplication)
    from PyQt6.QtCore import QTimer, pyqtSignal, Qt
    from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # 创建模拟的pyqtSignal用于类定义
    class MockSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, *args):
            pass
    pyqtSignal = MockSignal

# 获取日志记录器
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """警告级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertManager(QWidget if PYQT_AVAILABLE else object):
    """警告管理器"""

    # 信号定义
    alert_triggered = pyqtSignal(str, str, str)  # level, title, message
    alert_resolved = pyqtSignal(str)  # alert_id
    
    def __init__(self, parent=None):
        """初始化警告管理器"""
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for AlertManager")
        
        super().__init__(parent)
        self.setObjectName("AlertManager")
        
        # 警告存储
        self.active_alerts = {}
        self.alert_history = []
        self.shown_alerts = set()  # 防重复弹窗
        
        # 配置参数
        self.max_history = 100
        self.auto_dismiss_timeout = 5000  # 5秒自动消失
        self.duplicate_prevention_timeout = 30  # 30秒内不重复显示相同警告
        
        # 初始化UI
        self._init_ui()
        
        # 清理定时器
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_old_alerts)
        self.cleanup_timer.start(60000)  # 每分钟清理一次
        
        logger.info("警告管理器初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("系统警告")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 警告列表滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumHeight(300)
        
        self.alerts_widget = QWidget()
        self.alerts_layout = QVBoxLayout(self.alerts_widget)
        self.alerts_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.alerts_widget)
        layout.addWidget(self.scroll_area)
        
        # 控制按钮
        buttons_layout = QHBoxLayout()
        
        self.clear_all_btn = QPushButton("清除所有")
        self.clear_all_btn.clicked.connect(self.clear_all_alerts)
        buttons_layout.addWidget(self.clear_all_btn)
        
        self.test_alert_btn = QPushButton("测试警告")
        self.test_alert_btn.clicked.connect(self._test_alert)
        buttons_layout.addWidget(self.test_alert_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # 状态标签
        self.status_label = QLabel("状态: 正常")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.status_label)
        
        # 应用样式
        self._apply_styles()
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QWidget#AlertManager {
                background-color: #f8f9fa;
                border-radius: 8px;
            }
            
            QLabel {
                color: #333333;
                font-family: 'Microsoft YaHei';
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
        """)
    
    def show_alert(self, 
                  level: AlertLevel, 
                  title: str, 
                  message: str,
                  auto_dismiss: bool = True,
                  show_dialog: bool = False) -> str:
        """
        显示警告
        
        Args:
            level: 警告级别
            title: 警告标题
            message: 警告消息
            auto_dismiss: 是否自动消失
            show_dialog: 是否显示对话框
            
        Returns:
            警告ID
        """
        try:
            # 生成警告ID
            alert_id = f"{level.value}_{int(time.time() * 1000)}"
            
            # 防重复检查
            alert_key = f"{level.value}_{title}_{message}"
            current_time = datetime.now()
            
            if alert_key in self.shown_alerts:
                last_shown = self.shown_alerts[alert_key]
                if (current_time - last_shown).total_seconds() < self.duplicate_prevention_timeout:
                    logger.debug(f"跳过重复警告: {title}")
                    return alert_id
            
            # 记录显示时间
            self.shown_alerts[alert_key] = current_time
            
            # 创建警告数据
            alert_data = {
                "id": alert_id,
                "level": level,
                "title": title,
                "message": message,
                "timestamp": current_time,
                "auto_dismiss": auto_dismiss,
                "dismissed": False
            }
            
            # 添加到活动警告
            self.active_alerts[alert_id] = alert_data
            
            # 添加到历史记录
            self.alert_history.append(alert_data.copy())
            if len(self.alert_history) > self.max_history:
                self.alert_history = self.alert_history[-self.max_history:]
            
            # 更新UI
            self._add_alert_to_ui(alert_data)
            
            # 显示对话框（如果需要）
            if show_dialog:
                self._show_alert_dialog(alert_data)
            
            # 设置自动消失
            if auto_dismiss:
                QTimer.singleShot(self.auto_dismiss_timeout, 
                                lambda: self.dismiss_alert(alert_id))
            
            # 发送信号
            self.alert_triggered.emit(level.value, title, message)
            
            # 更新状态
            self._update_status()
            
            logger.info(f"显示警告: [{level.value}] {title}")
            
            return alert_id
            
        except Exception as e:
            logger.error(f"显示警告失败: {str(e)}")
            return ""
    
    def _add_alert_to_ui(self, alert_data: Dict[str, Any]):
        """添加警告到UI"""
        alert_frame = QFrame()
        alert_frame.setFrameStyle(QFrame.Shape.Box)
        alert_frame.setObjectName(f"alert_{alert_data['id']}")
        
        # 根据级别设置样式
        level_colors = {
            AlertLevel.INFO: "#d1ecf1",
            AlertLevel.WARNING: "#fff3cd", 
            AlertLevel.ERROR: "#f8d7da",
            AlertLevel.CRITICAL: "#f5c6cb"
        }
        
        alert_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {level_colors.get(alert_data['level'], '#f8f9fa')};
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout(alert_frame)
        
        # 标题和时间
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"[{alert_data['level'].value.upper()}] {alert_data['title']}")
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        time_label = QLabel(alert_data['timestamp'].strftime("%H:%M:%S"))
        time_label.setFont(QFont("Microsoft YaHei", 9))
        header_layout.addWidget(time_label)
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setMaximumSize(20, 20)
        close_btn.clicked.connect(lambda: self.dismiss_alert(alert_data['id']))
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # 消息内容
        message_label = QLabel(alert_data['message'])
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Microsoft YaHei", 9))
        layout.addWidget(message_label)
        
        # 添加到布局
        self.alerts_layout.insertWidget(0, alert_frame)  # 新警告显示在顶部
    
    def _show_alert_dialog(self, alert_data: Dict[str, Any]):
        """显示警告对话框"""
        try:
            # 根据级别选择图标
            icon_map = {
                AlertLevel.INFO: QMessageBox.Icon.Information,
                AlertLevel.WARNING: QMessageBox.Icon.Warning,
                AlertLevel.ERROR: QMessageBox.Icon.Critical,
                AlertLevel.CRITICAL: QMessageBox.Icon.Critical
            }
            
            msg_box = QMessageBox()
            msg_box.setIcon(icon_map.get(alert_data['level'], QMessageBox.Icon.Information))
            msg_box.setWindowTitle(f"VisionAI - {alert_data['level'].value.title()}")
            msg_box.setText(alert_data['title'])
            msg_box.setDetailedText(alert_data['message'])
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # 添加错误恢复建议
            if alert_data['level'] in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                recovery_suggestions = self._get_recovery_suggestions(alert_data)
                if recovery_suggestions:
                    msg_box.setInformativeText(f"建议解决方案:\n{recovery_suggestions}")
            
            msg_box.exec()
            
        except Exception as e:
            logger.error(f"显示警告对话框失败: {str(e)}")
    
    def _get_recovery_suggestions(self, alert_data: Dict[str, Any]) -> str:
        """获取错误恢复建议"""
        suggestions = []
        
        message = alert_data['message'].lower()
        
        if "memory" in message or "内存" in message:
            suggestions.append("• 关闭其他不必要的应用程序")
            suggestions.append("• 重启应用程序")
            suggestions.append("• 检查系统内存使用情况")
        
        if "file" in message or "文件" in message:
            suggestions.append("• 检查文件是否存在且可访问")
            suggestions.append("• 确认文件格式正确")
            suggestions.append("• 检查磁盘空间是否充足")
        
        if "network" in message or "网络" in message:
            suggestions.append("• 检查网络连接")
            suggestions.append("• 重试操作")
            suggestions.append("• 检查防火墙设置")
        
        if "model" in message or "模型" in message:
            suggestions.append("• 重新加载模型")
            suggestions.append("• 检查模型文件完整性")
            suggestions.append("• 使用备用模型")
        
        if not suggestions:
            suggestions.append("• 重试当前操作")
            suggestions.append("• 重启应用程序")
            suggestions.append("• 联系技术支持")
        
        return "\n".join(suggestions)
    
    def dismiss_alert(self, alert_id: str):
        """消除警告"""
        try:
            if alert_id in self.active_alerts:
                # 标记为已消除
                self.active_alerts[alert_id]["dismissed"] = True
                
                # 从UI中移除
                alert_frame = self.alerts_widget.findChild(QFrame, f"alert_{alert_id}")
                if alert_frame:
                    alert_frame.setParent(None)
                    alert_frame.deleteLater()
                
                # 从活动警告中移除
                del self.active_alerts[alert_id]
                
                # 发送信号
                self.alert_resolved.emit(alert_id)
                
                # 更新状态
                self._update_status()
                
                logger.debug(f"警告已消除: {alert_id}")
            
        except Exception as e:
            logger.error(f"消除警告失败: {str(e)}")
    
    def clear_all_alerts(self):
        """清除所有警告"""
        try:
            # 获取所有活动警告ID
            alert_ids = list(self.active_alerts.keys())
            
            # 逐个消除
            for alert_id in alert_ids:
                self.dismiss_alert(alert_id)
            
            logger.info("所有警告已清除")
            
        except Exception as e:
            logger.error(f"清除所有警告失败: {str(e)}")
    
    def _cleanup_old_alerts(self):
        """清理过期的警告记录"""
        try:
            current_time = datetime.now()
            
            # 清理防重复记录
            expired_keys = []
            for key, timestamp in self.shown_alerts.items():
                if (current_time - timestamp).total_seconds() > self.duplicate_prevention_timeout * 2:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.shown_alerts[key]
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 个过期的防重复记录")
            
        except Exception as e:
            logger.error(f"清理过期警告失败: {str(e)}")
    
    def _update_status(self):
        """更新状态显示"""
        active_count = len(self.active_alerts)
        
        if active_count == 0:
            self.status_label.setText("状态: 正常")
            self.status_label.setStyleSheet("color: #28a745;")
        else:
            # 检查是否有严重警告
            has_critical = any(alert['level'] == AlertLevel.CRITICAL for alert in self.active_alerts.values())
            has_error = any(alert['level'] == AlertLevel.ERROR for alert in self.active_alerts.values())
            
            if has_critical:
                self.status_label.setText(f"状态: 严重警告 ({active_count}个活动警告)")
                self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            elif has_error:
                self.status_label.setText(f"状态: 错误 ({active_count}个活动警告)")
                self.status_label.setStyleSheet("color: #fd7e14;")
            else:
                self.status_label.setText(f"状态: 警告 ({active_count}个活动警告)")
                self.status_label.setStyleSheet("color: #ffc107;")
    
    def _test_alert(self):
        """测试警告功能"""
        import random
        
        test_alerts = [
            (AlertLevel.INFO, "测试信息", "这是一个测试信息警告"),
            (AlertLevel.WARNING, "测试警告", "这是一个测试警告消息"),
            (AlertLevel.ERROR, "测试错误", "这是一个测试错误消息"),
            (AlertLevel.CRITICAL, "测试严重错误", "这是一个测试严重错误消息")
        ]
        
        level, title, message = random.choice(test_alerts)
        self.show_alert(level, title, message)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取警告统计信息"""
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)
        
        # 按级别统计
        level_counts = {level.value: 0 for level in AlertLevel}
        for alert in self.alert_history:
            level_counts[alert['level'].value] += 1
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "level_counts": level_counts,
            "duplicate_prevention_active": len(self.shown_alerts)
        }


# 便捷函数
def create_alert_manager(parent=None) -> Optional[AlertManager]:
    """创建警告管理器"""
    if not PYQT_AVAILABLE:
        logger.warning("PyQt6不可用，无法创建警告管理器")
        return None
    
    try:
        return AlertManager(parent)
    except Exception as e:
        logger.error(f"创建警告管理器失败: {str(e)}")
        return None

def show_quick_alert(level: str, title: str, message: str, parent=None):
    """快速显示警告"""
    try:
        alert_level = AlertLevel(level.lower())
        manager = create_alert_manager(parent)
        if manager:
            manager.show_alert(alert_level, title, message, show_dialog=True)
    except Exception as e:
        logger.error(f"快速显示警告失败: {str(e)}")
        # 回退到简单的消息框
        if PYQT_AVAILABLE:
            QMessageBox.information(parent, title, message)
