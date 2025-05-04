#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误显示UI模块 - 简化版（UI演示用）
"""

import sys
import logging
import traceback
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class ErrorMessageLocalizer:
    """错误消息本地化处理器"""
    
    def __init__(self):
        """初始化错误消息本地化处理器"""
        # 常见错误消息映射
        self.error_messages = {
            "FileNotFoundError": "文件未找到",
            "PermissionError": "权限不足",
            "OSError": "系统错误",
            "ImportError": "导入模块失败",
            "ModuleNotFoundError": "找不到模块",
            "MemoryError": "内存不足",
            "IndexError": "索引错误",
            "KeyError": "键错误",
            "ValueError": "值错误",
            "TypeError": "类型错误",
            "SyntaxError": "语法错误",
            "RuntimeError": "运行时错误",
            "AttributeError": "属性错误"
        }
    
    def localize(self, error: Exception) -> str:
        """本地化错误消息"""
        error_type = error.__class__.__name__
        error_msg = str(error)
        
        # 获取本地化的错误类型
        localized_type = self.error_messages.get(error_type, error_type)
        
        # 拼接完整的错误消息
        if error_msg:
            return f"{localized_type}: {error_msg}"
        else:
            return localized_type

def handle_error(error: Exception, parent=None) -> None:
    """处理错误并显示错误消息对话框"""
    # 记录错误到日志
    logger.error(f"发生错误: {str(error)}")
    logger.error(traceback.format_exc())
    
    # 本地化错误消息
    localizer = ErrorMessageLocalizer()
    error_message = localizer.localize(error)
    
    # 如果有父窗口，则显示错误对话框
    if parent:
        try:
            QMessageBox.critical(parent, "错误", error_message)
        except Exception as e:
            print(f"错误: {error_message}", file=sys.stderr)
            print(f"显示错误对话框失败: {str(e)}", file=sys.stderr)
    else:
        print(f"错误: {error_message}", file=sys.stderr) 