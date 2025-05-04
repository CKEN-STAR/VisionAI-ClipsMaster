#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
警告管理模块 - 简化版（UI演示用）
"""

import logging
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class AlertManager:
    """警告管理器 - 简化版（UI演示用）"""
    
    def __init__(self, parent=None):
        """初始化警告管理器"""
        self.parent = parent

def show_error_alert(message, title="错误", parent=None):
    """显示错误警告"""
    logger.error(f"错误警告: {message}")
    try:
        QMessageBox.critical(parent, title, message)
    except Exception as e:
        logger.error(f"显示错误警告失败: {str(e)}")
        print(f"错误: {message}")

def show_error_with_recovery(error, recovery_suggestions=None, parent=None):
    """显示带有恢复建议的错误警告"""
    error_message = str(error)
    logger.error(f"错误警告（带恢复建议）: {error_message}")
    
    # 准备详细信息
    detail_message = ""
    if recovery_suggestions:
        detail_message = "建议的恢复操作:\n" + "\n".join([f"- {s}" for s in recovery_suggestions])
    
    try:
        # 创建消息框
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("错误")
        msg_box.setText(error_message)
        
        if detail_message:
            msg_box.setDetailedText(detail_message)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    except Exception as e:
        logger.error(f"显示错误警告（带恢复建议）失败: {str(e)}")
        print(f"错误: {error_message}")
        if recovery_suggestions:
            print("恢复建议:")
            for suggestion in recovery_suggestions:
                print(f"- {suggestion}")

def show_warning(message, title="警告", parent=None):
    """显示警告"""
    logger.warning(f"警告: {message}")
    try:
        QMessageBox.warning(parent, title, message)
    except Exception as e:
        logger.error(f"显示警告失败: {str(e)}")
        print(f"警告: {message}")

def show_info(message, title="信息", parent=None):
    """显示信息"""
    logger.info(f"信息: {message}")
    try:
        QMessageBox.information(parent, title, message)
    except Exception as e:
        logger.error(f"显示信息失败: {str(e)}")
        print(f"信息: {message}")
