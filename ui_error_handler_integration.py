#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI错误处理集成
将增强错误处理器集成到UI中
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

try:
    from src.utils.enhanced_error_handler import EnhancedErrorHandler, ErrorCategory, ErrorSeverity
    ENHANCED_ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ENHANCED_ERROR_HANDLER_AVAILABLE = False
    print("警告: 增强错误处理器不可用")

class UIErrorDialog(QDialog):
    """用户友好的错误对话框"""
    
    def __init__(self, error_details, parent=None):
        super().__init__(parent)
        self.error_details = error_details
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("错误处理")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # 用户友好的错误消息
        user_message = self.error_details.get("user_friendly_message", "发生了一个错误")
        message_label = QLabel(user_message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Microsoft YaHei UI", 10))
        layout.addWidget(message_label)
        
        # 恢复信息
        if self.error_details.get("recovery_successful", False):
            recovery_label = QLabel("✅ 问题已自动修复，您可以继续操作。")
            recovery_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            recovery_label = QLabel("❌ 请根据提示解决问题后重试。")
            recovery_label.setStyleSheet("color: red; font-weight: bold;")
        
        layout.addWidget(recovery_label)
        
        # 详细信息（可展开）
        details_text = QTextEdit()
        details_text.setMaximumHeight(150)
        details_text.setPlainText(f"""
错误ID: {self.error_details.get('error_id', 'N/A')}
错误类型: {self.error_details.get('error_type', 'N/A')}
错误类别: {self.error_details.get('category', 'N/A')}
严重程度: {self.error_details.get('severity', 'N/A')}
恢复策略: {self.error_details.get('recovery_strategy', 'N/A')}
恢复消息: {self.error_details.get('recovery_message', 'N/A')}

原始错误消息:
{self.error_details.get('error_message', 'N/A')}
        """.strip())
        details_text.setReadOnly(True)
        layout.addWidget(details_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        if not self.error_details.get("recovery_successful", False):
            retry_button = QPushButton("重试")
            retry_button.clicked.connect(self.retry)
            button_layout.addWidget(retry_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def retry(self):
        """重试操作"""
        self.done(2)  # 返回重试代码

class UIErrorHandlerIntegration(QObject):
    """UI错误处理集成器"""
    
    error_occurred = pyqtSignal(dict)  # 错误发生信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        
        # 初始化增强错误处理器
        if ENHANCED_ERROR_HANDLER_AVAILABLE:
            try:
                self.error_handler = EnhancedErrorHandler(
                    log_dir="logs/ui_errors",
                    enable_recovery=True
                )
                self.enhanced_available = True
                print("✓ 增强错误处理器初始化成功")
            except Exception as e:
                print(f"增强错误处理器初始化失败: {e}")
                self.error_handler = None
                self.enhanced_available = False
        else:
            self.error_handler = None
            self.enhanced_available = False
    
    def handle_ui_error(self, error, category=None, severity=None, context=None, show_dialog=True):
        """处理UI错误"""
        try:
            # 确定错误类别和严重程度
            if category is None:
                category = self._determine_error_category(error)
            if severity is None:
                severity = self._determine_error_severity(error)
            
            # 使用增强错误处理器处理
            if self.enhanced_available and self.error_handler:
                error_details = self.error_handler.handle_error(
                    error=error,
                    category=category,
                    severity=severity,
                    context=context,
                    user_message="UI操作发生错误"
                )
            else:
                # 降级到基础错误处理
                error_details = self._basic_error_handling(error, category, severity, context)
            
            # 发送错误信号
            self.error_occurred.emit(error_details)
            
            # 显示错误对话框
            if show_dialog and self.parent_widget:
                self._show_error_dialog(error_details)
            
            return error_details
            
        except Exception as e:
            print(f"错误处理失败: {e}")
            return {"error": str(e)}
    
    def _determine_error_category(self, error):
        """确定错误类别"""
        if not ENHANCED_ERROR_HANDLER_AVAILABLE:
            return "system"
        
        error_type = type(error).__name__
        
        if error_type in ["FileNotFoundError", "PermissionError", "OSError"]:
            return ErrorCategory.FILESYSTEM
        elif error_type in ["ConnectionError", "TimeoutError", "URLError"]:
            return ErrorCategory.NETWORK
        elif error_type in ["MemoryError"]:
            return ErrorCategory.MEMORY
        elif "video" in str(error).lower() or "ffmpeg" in str(error).lower():
            return ErrorCategory.VIDEO_FILE
        elif "srt" in str(error).lower() or "subtitle" in str(error).lower():
            return ErrorCategory.SRT_SUBTITLE
        else:
            return ErrorCategory.SYSTEM
    
    def _determine_error_severity(self, error):
        """确定错误严重程度"""
        if not ENHANCED_ERROR_HANDLER_AVAILABLE:
            return "medium"
        
        error_type = type(error).__name__
        
        if error_type in ["MemoryError", "SystemExit", "KeyboardInterrupt"]:
            return ErrorSeverity.CRITICAL
        elif error_type in ["FileNotFoundError", "ConnectionError", "TimeoutError"]:
            return ErrorSeverity.HIGH
        elif error_type in ["ValueError", "TypeError", "AttributeError"]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _basic_error_handling(self, error, category, severity, context):
        """基础错误处理（降级方案）"""
        error_details = {
            "error_id": f"UI_ERR_{int(time.time())}",
            "timestamp": time.time(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": category if hasattr(category, 'value') else str(category),
            "severity": severity if hasattr(severity, 'value') else str(severity),
            "context": context or {},
            "recovery_attempted": False,
            "recovery_successful": False,
            "user_friendly_message": f"发生了一个错误: {str(error)}"
        }
        
        return error_details
    
    def _show_error_dialog(self, error_details):
        """显示错误对话框"""
        try:
            dialog = UIErrorDialog(error_details, self.parent_widget)
            result = dialog.exec()
            
            if result == 2:  # 重试
                print("用户选择重试")
                return "retry"
            else:
                return "ok"
                
        except Exception as e:
            print(f"显示错误对话框失败: {e}")
            # 降级到简单消息框
            QMessageBox.critical(
                self.parent_widget,
                "错误",
                error_details.get("user_friendly_message", "发生了一个错误")
            )
    
    def get_error_statistics(self):
        """获取错误统计"""
        if self.enhanced_available and self.error_handler:
            return self.error_handler.get_error_statistics()
        else:
            return {"error": "增强错误处理器不可用"}

# 全局错误处理装饰器
def ui_error_handler(category=None, severity=None, show_dialog=True):
    """UI错误处理装饰器"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # 获取UI错误处理器
                if hasattr(self, 'ui_error_handler'):
                    context = {
                        "function": func.__name__,
                        "args": str(args)[:100],  # 限制长度
                        "kwargs": str(kwargs)[:100]
                    }
                    self.ui_error_handler.handle_ui_error(
                        error=e,
                        category=category,
                        severity=severity,
                        context=context,
                        show_dialog=show_dialog
                    )
                else:
                    print(f"UI错误处理器不可用，错误: {e}")
                    raise
        return wrapper
    return decorator

# 示例使用
if __name__ == "__main__":
    import time
    
    # 测试错误处理集成
    print("测试UI错误处理集成...")
    
    handler = UIErrorHandlerIntegration()
    
    # 测试不同类型的错误
    test_errors = [
        (FileNotFoundError("测试文件未找到"), "文件系统错误"),
        (MemoryError("测试内存不足"), "内存错误"),
        (ValueError("测试值错误"), "一般错误")
    ]
    
    for error, description in test_errors:
        print(f"\n测试 {description}:")
        result = handler.handle_ui_error(error, show_dialog=False)
        print(f"处理结果: {result.get('user_friendly_message', 'N/A')}")
    
    # 获取统计信息
    stats = handler.get_error_statistics()
    print(f"\n错误统计: {stats}")
    
    print("UI错误处理集成测试完成")
