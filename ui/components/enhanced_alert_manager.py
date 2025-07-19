
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt6.QtGui import QPalette
import time

class EnhancedAlertManager(QWidget):
    """增强的警告管理器"""

    alert_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.alerts = []
        self.max_alerts = 3
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setFixedSize(300, 0)  # 初始高度为0
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.8);
                border-radius: 5px;
                color: white;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

    def show_alert(self, message, level="info", timeout=3000):
        """显示警告"""
        if len(self.alerts) >= self.max_alerts:
            # 移除最旧的警告
            self.remove_alert(self.alerts[0])

        alert_widget = self.create_alert_widget(message, level)
        self.alerts.append(alert_widget)
        self.layout.addWidget(alert_widget)

        # 调整窗口大小
        self.adjust_size()

        # 设置自动关闭定时器
        if timeout > 0:
            timer = QTimer()
            timer.timeout.connect(lambda: self.remove_alert(alert_widget))
            timer.setSingleShot(True)
            timer.start(timeout)
            alert_widget.timer = timer

    def create_alert_widget(self, message, level):
        """创建警告组件"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # 设置样式
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336"
        }

        color = colors.get(level, colors["info"])
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 3px;
                padding: 5px;
            }}
        """)

        # 消息标签
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(lambda: self.remove_alert(widget))
        layout.addWidget(close_btn)

        return widget

    def remove_alert(self, alert_widget):
        """移除警告"""
        if alert_widget in self.alerts:
            self.alerts.remove(alert_widget)
            self.layout.removeWidget(alert_widget)
            alert_widget.deleteLater()
            self.adjust_size()

    def adjust_size(self):
        """调整大小"""
        height = len(self.alerts) * 50 + 20
        self.setFixedHeight(height)

        if self.parent_widget:
            # 定位到父窗口右上角
            parent_rect = self.parent_widget.geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 50
            self.move(x, y)

    def info(self, message, timeout=3000):
        """显示信息"""
        self.show_alert(message, "info", timeout)

    def success(self, message, timeout=3000):
        """显示成功"""
        self.show_alert(message, "success", timeout)

    def warning(self, message, timeout=3000):
        """显示警告"""
        self.show_alert(message, "warning", timeout)

    def error(self, message, timeout=5000):
        """显示错误"""
        self.show_alert(message, "error", timeout)

    def clear_alerts(self):
        """清除所有警告"""
        for alert in self.alerts.copy():
            self.remove_alert(alert)
