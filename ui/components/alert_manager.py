
# 安全导入包装 - 自动生成
import sys
import os

# 确保PyQt6可用
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    print(f"[WARN] PyQt6不可用，AlertManager将使用fallback模式")

# 线程安全检查
def ensure_main_thread():
    """确保在主线程中执行"""
    if QT_AVAILABLE and QApplication.instance():
        current_thread = QThread.currentThread()
        main_thread = QApplication.instance().thread()
        if current_thread != main_thread:
            print(f"[WARN] AlertManager不在主线程中，可能导致问题")
            return False
    return True

"""
警告管理器
提供统一的警告和通知功能
"""

from enum import Enum
from typing import Optional, List, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QMessageBox, QSystemTrayIcon

class AlertLevel(Enum):
    """警告级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class AlertManager(QObject):
    """警告管理器"""
    
    alert_shown = pyqtSignal(str, str)  # 警告显示信号 (message, level)
    alert_cleared = pyqtSignal()  # 警告清除信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.active_alerts: List[dict] = []
        self.auto_clear_timers: List[QTimer] = []
        self.max_alerts = 5
        
    def show_alert(self, message: str, level: AlertLevel = AlertLevel.INFO, timeout: int = 3000) -> bool:
        """
        显示警告
        
        Args:
            message: 警告消息
            level: 警告级别
            timeout: 自动清除时间（毫秒），0表示不自动清除
            
        Returns:
            是否成功显示
        """
        try:
            # 创建警告记录
            alert = {
                'message': message,
                'level': level,
                'timestamp': self._get_timestamp()
            }
            
            # 添加到活动警告列表
            self.active_alerts.append(alert)
            
            # 限制警告数量
            if len(self.active_alerts) > self.max_alerts:
                self.active_alerts.pop(0)
            
            # 显示警告
            self._display_alert(message, level)
            
            # 发送信号
            self.alert_shown.emit(message, level.value)
            
            # 设置自动清除
            if timeout > 0:
                self._setup_auto_clear(timeout)
            
            return True
            
        except Exception as e:
            print(f"[WARN] 显示警告失败: {e}")
            return False
    
    def _display_alert(self, message: str, level: AlertLevel):
        """显示警告UI"""
        try:
            if self.parent_widget:
                # 使用消息框显示
                if level == AlertLevel.ERROR:
                    QMessageBox.critical(self.parent_widget, "错误", message)
                elif level == AlertLevel.WARNING:
                    QMessageBox.warning(self.parent_widget, "警告", message)
                elif level == AlertLevel.SUCCESS:
                    QMessageBox.information(self.parent_widget, "成功", message)
                else:
                    QMessageBox.information(self.parent_widget, "信息", message)
            else:
                # 控制台输出
                level_str = level.value.upper()
                print(f"[{level_str}] {message}")
                
        except Exception as e:
            print(f"[WARN] 显示警告UI失败: {e}")
    
    def _setup_auto_clear(self, timeout: int):
        """设置自动清除"""
        try:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(self.clear_alerts)
            timer.start(timeout)
            self.auto_clear_timers.append(timer)
            
        except Exception as e:
            print(f"[WARN] 设置自动清除失败: {e}")
    
    def clear_alerts(self):
        """清除所有警告"""
        try:
            self.active_alerts.clear()
            
            # 停止所有定时器
            for timer in self.auto_clear_timers:
                timer.stop()
                timer.deleteLater()
            self.auto_clear_timers.clear()
            
            # 发送清除信号
            self.alert_cleared.emit()
            
        except Exception as e:
            print(f"[WARN] 清除警告失败: {e}")
    
    def get_active_alerts(self) -> List[dict]:
        """获取活动警告列表"""
        return self.active_alerts.copy()
    
    def get_alert_count(self) -> int:
        """获取警告数量"""
        return len(self.active_alerts)
    
    def has_errors(self) -> bool:
        """检查是否有错误警告"""
        return any(alert['level'] == AlertLevel.ERROR for alert in self.active_alerts)
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def show_info(self, message: str, timeout: int = 3000):
        """显示信息警告"""
        self.show_alert(message, AlertLevel.INFO, timeout)
    
    def show_warning(self, message: str, timeout: int = 5000):
        """显示警告"""
        self.show_alert(message, AlertLevel.WARNING, timeout)
    
    def show_error(self, message: str, timeout: int = 0):
        """显示错误（默认不自动清除）"""
        self.show_alert(message, AlertLevel.ERROR, timeout)
    
    def show_success(self, message: str, timeout: int = 3000):
        """显示成功消息"""
        self.show_alert(message, AlertLevel.SUCCESS, timeout)

class SystemTrayAlertManager(AlertManager):
    """系统托盘警告管理器"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._setup_tray_icon()
    
    def _setup_tray_icon(self):
        """设置系统托盘图标"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon(self.parent_widget)
                # 这里可以设置图标
                # self.tray_icon.setIcon(QIcon("icon.png"))
                self.tray_icon.show()
        except Exception as e:
            print(f"[WARN] 设置系统托盘失败: {e}")
    
    def _display_alert(self, message: str, level: AlertLevel):
        """通过系统托盘显示警告"""
        try:
            if self.tray_icon and self.tray_icon.isVisible():
                # 映射警告级别到托盘图标类型
                icon_type = {
                    AlertLevel.INFO: QSystemTrayIcon.MessageIcon.Information,
                    AlertLevel.WARNING: QSystemTrayIcon.MessageIcon.Warning,
                    AlertLevel.ERROR: QSystemTrayIcon.MessageIcon.Critical,
                    AlertLevel.SUCCESS: QSystemTrayIcon.MessageIcon.Information
                }.get(level, QSystemTrayIcon.MessageIcon.Information)
                
                title = {
                    AlertLevel.INFO: "信息",
                    AlertLevel.WARNING: "警告", 
                    AlertLevel.ERROR: "错误",
                    AlertLevel.SUCCESS: "成功"
                }.get(level, "通知")
                
                self.tray_icon.showMessage(title, message, icon_type, 3000)
            else:
                # 回退到父类方法
                super()._display_alert(message, level)
                
        except Exception as e:
            print(f"[WARN] 系统托盘显示警告失败: {e}")
            super()._display_alert(message, level)

def create_alert_manager(parent: Optional[QWidget] = None, use_tray: bool = False) -> AlertManager:
    """
    创建警告管理器
    
    Args:
        parent: 父组件
        use_tray: 是否使用系统托盘
        
    Returns:
        警告管理器实例
    """
    if use_tray:
        return SystemTrayAlertManager(parent)
    else:
        return AlertManager(parent)

__all__ = [
    'AlertLevel',
    'AlertManager',
    'SystemTrayAlertManager',
    'create_alert_manager'
]
