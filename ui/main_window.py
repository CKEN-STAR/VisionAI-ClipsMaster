#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主窗口模块 - 简化版（UI演示用）
"""

import sys
import logging
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import Qt, QSize
from ui.error_display import ErrorMessageLocalizer
from ui.components.alert_manager import show_error_alert, show_error_with_recovery
from src.utils.exceptions import MemoryOverflowError, ClipMasterError
from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout
from ui.components.term_manager import TermManager
from ui.components.alert_manager import AlertManager
from src.core.auto_recovery import auto_heal
from loguru import logger
import traceback

def handle_error(error, parent=None):
    """处理错误并显示用户友好的错误信息
    
    Args:
        error: 异常对象
        parent: 父窗口对象
    """
    localizer = ErrorMessageLocalizer()
    
    # 获取错误代码和消息
    if isinstance(error, ClipMasterError):
        error_code = getattr(error, 'code', None)
        if hasattr(error_code, 'value'):
            error_code = error_code.value
            
        # 获取本地化的错误消息
        msg = localizer.get_message(error_code)
        
        # 获取错误详情
        details = None
        if hasattr(error, 'to_dict'):
            error_dict = error.to_dict()
            details = f"错误代码: {error_dict.get('error_code')}\n"
            details += f"错误类型: {error_dict.get('error_type')}\n"
            details += f"错误类别: {error_dict.get('error_category')}\n\n"
            
            if 'details' in error_dict and error_dict['details']:
                details += "详细信息:\n"
                for key, value in error_dict['details'].items():
                    details += f"- {key}: {value}\n"
                
        # 对于严重错误，提供自动恢复选项
        if hasattr(error, 'critical') and error.critical:
            # 定义恢复操作
            def recovery_action():
                logger.info(f"尝试自动恢复错误: {error_code}")
                success = auto_heal(error)
                if success:
                    logger.info("自动恢复成功")
                    show_error_alert("错误已自动恢复，请重试您的操作", parent, title="恢复成功")
                else:
                    logger.warning("自动恢复失败")
                    show_error_alert("自动恢复未能解决问题，请尝试重启应用", parent, title="恢复失败")
                return success
            
            # 显示带有恢复选项的错误提示
            return show_error_with_recovery(msg, recovery_action, parent, details)
        else:
            # 显示普通错误提示
            return show_error_alert(msg, parent, details)
    else:
        # 非ClipMasterError类型的异常
        msg = str(error)
        details = traceback.format_exc()
        return show_error_alert(f"发生未知错误: {msg}", parent, details)

# 示例：主窗口中捕获异常后调用
if __name__ == '__main__':
    try:
        # 模拟抛出异常
        raise MemoryOverflowError("测试内存溢出异常", details={"free_memory": "100MB", "required": "500MB"})
    except Exception as e:
        handle_error(e)

class MainWindow(QMainWindow):
    """应用主窗口 - 简化版（UI演示用）"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster")
        self.resize(1200, 800)
        self.setMinimumSize(QSize(800, 600))
        
    def closeEvent(self, event):
        """关闭窗口事件处理"""
        reply = QMessageBox.question(
            self, 
            "确认退出", 
            "确定要退出程序吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def init_ui(self):
        self.setWindowTitle("VisionAI-ClipsMaster")
        self.setMinimumSize(800, 600)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 添加术语管理标签页
        term_manager = TermManager()
        tab_widget.addTab(term_manager, "术语管理")
        
        # 添加其他标签页（待实现）
        # tab_widget.addTab(QWidget(), "视频处理")
        # tab_widget.addTab(QWidget(), "模型训练")
        # tab_widget.addTab(QWidget(), "设置")
        
        # 添加警告管理器
        self.alert_manager = AlertManager()
        main_layout.addWidget(self.alert_manager)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #cccccc;
                padding: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
            }
        """)
