"""
错误可视化模块
提供错误信息的可视化显示功能
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton

class ErrorType(Enum):
    """错误类型枚举"""
    SYSTEM = "system"
    USER = "user"
    NETWORK = "network"
    FILE = "file"
    MEMORY = "memory"
    PERMISSION = "permission"
    VALIDATION = "validation"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """错误信息数据类"""
    message: str
    error_type: ErrorType
    details: Optional[str] = None
    suggestions: Optional[List[str]] = None
    timestamp: Optional[str] = None
    traceback: Optional[str] = None

class ErrorVisualizerDialog(QDialog):
    """错误可视化对话框"""
    
    def __init__(self, error_info: ErrorInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.error_info = error_info
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("错误详情")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 错误消息
        message_label = QLabel(f"错误: {self.error_info.message}")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # 错误类型
        type_label = QLabel(f"类型: {self.error_info.error_type.value}")
        layout.addWidget(type_label)
        
        # 时间戳
        if self.error_info.timestamp:
            time_label = QLabel(f"时间: {self.error_info.timestamp}")
            layout.addWidget(time_label)
        
        # 详细信息
        if self.error_info.details:
            details_label = QLabel("详细信息:")
            layout.addWidget(details_label)
            
            details_text = QTextEdit()
            details_text.setPlainText(self.error_info.details)
            details_text.setMaximumHeight(100)
            layout.addWidget(details_text)
        
        # 建议
        if self.error_info.suggestions:
            suggestions_label = QLabel("建议解决方案:")
            layout.addWidget(suggestions_label)
            
            for i, suggestion in enumerate(self.error_info.suggestions, 1):
                suggestion_label = QLabel(f"{i}. {suggestion}")
                suggestion_label.setWordWrap(True)
                layout.addWidget(suggestion_label)
        
        # 堆栈跟踪
        if self.error_info.traceback:
            traceback_label = QLabel("堆栈跟踪:")
            layout.addWidget(traceback_label)
            
            traceback_text = QTextEdit()
            traceback_text.setPlainText(self.error_info.traceback)
            traceback_text.setMaximumHeight(150)
            layout.addWidget(traceback_text)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

class ErrorVisualizer(QObject):
    """错误可视化器"""
    
    error_shown = pyqtSignal(ErrorInfo)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.error_history: List[ErrorInfo] = []
        self.max_history = 100
    
    def show_error(self, error_info: ErrorInfo) -> bool:
        """
        显示错误
        
        Args:
            error_info: 错误信息
            
        Returns:
            是否成功显示
        """
        try:
            # 添加时间戳
            if not error_info.timestamp:
                from datetime import datetime
                error_info.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 添加到历史记录
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
            
            # 显示错误
            self._display_error(error_info)
            
            # 发送信号
            self.error_shown.emit(error_info)
            
            return True
            
        except Exception as e:
            print(f"[WARN] 显示错误失败: {e}")
            return False
    
    def _display_error(self, error_info: ErrorInfo):
        """显示错误UI"""
        try:
            if self.parent_widget:
                # 使用详细对话框
                dialog = ErrorVisualizerDialog(error_info, self.parent_widget)
                dialog.exec()
            else:
                # 使用简单消息框
                QMessageBox.critical(None, "错误", error_info.message)
                
        except Exception as e:
            print(f"[WARN] 显示错误UI失败: {e}")
            # 回退到控制台输出
            print(f"[ERROR] {error_info.message}")
            if error_info.details:
                print(f"详情: {error_info.details}")
    
    def show_simple_error(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN):
        """显示简单错误"""
        error_info = ErrorInfo(message=message, error_type=error_type)
        self.show_error(error_info)
    
    def show_system_error(self, message: str, details: Optional[str] = None):
        """显示系统错误"""
        suggestions = [
            "检查系统资源是否充足",
            "重启应用程序",
            "联系技术支持"
        ]
        error_info = ErrorInfo(
            message=message,
            error_type=ErrorType.SYSTEM,
            details=details,
            suggestions=suggestions
        )
        self.show_error(error_info)
    
    def show_user_error(self, message: str, suggestions: Optional[List[str]] = None):
        """显示用户错误"""
        if not suggestions:
            suggestions = ["请检查输入是否正确", "参考用户手册"]
        
        error_info = ErrorInfo(
            message=message,
            error_type=ErrorType.USER,
            suggestions=suggestions
        )
        self.show_error(error_info)
    
    def show_file_error(self, message: str, file_path: Optional[str] = None):
        """显示文件错误"""
        details = f"文件路径: {file_path}" if file_path else None
        suggestions = [
            "检查文件是否存在",
            "检查文件权限",
            "检查磁盘空间"
        ]
        
        error_info = ErrorInfo(
            message=message,
            error_type=ErrorType.FILE,
            details=details,
            suggestions=suggestions
        )
        self.show_error(error_info)
    
    def get_error_history(self) -> List[ErrorInfo]:
        """获取错误历史"""
        return self.error_history.copy()
    
    def clear_error_history(self):
        """清除错误历史"""
        self.error_history.clear()
    
    def get_error_statistics(self) -> Dict[str, int]:
        """获取错误统计"""
        stats = {}
        for error in self.error_history:
            error_type = error.error_type.value
            stats[error_type] = stats.get(error_type, 0) + 1
        return stats

def show_error(message: str, error_type: ErrorType = ErrorType.UNKNOWN, 
               parent: Optional[QWidget] = None) -> bool:
    """
    快速显示错误的便捷函数
    
    Args:
        message: 错误消息
        error_type: 错误类型
        parent: 父组件
        
    Returns:
        是否成功显示
    """
    visualizer = ErrorVisualizer(parent)
    error_info = ErrorInfo(message=message, error_type=error_type)
    return visualizer.show_error(error_info)

__all__ = [
    'ErrorType',
    'ErrorInfo',
    'ErrorVisualizerDialog',
    'ErrorVisualizer',
    'show_error'
]
