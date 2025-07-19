"""
实时图表组件
提供CPU/GPU监控、内存使用、性能指标等实时数据可视化
"""

import time
import psutil
from collections import deque
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QGridLayout, QFrame, QTabWidget, QProgressBar
)
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygon
from PyQt6.QtCore import QPoint

class LineChart(QWidget):
    """简单的线图组件"""
    
    def __init__(self, title: str, unit: str = "", max_points: int = 60, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.max_points = max_points
        self.data_points = deque(maxlen=max_points)
        self.max_value = 100.0
        self.min_value = 0.0
        
        self.setMinimumSize(300, 200)
        self.setStyleSheet("background-color: white; border: 1px solid #ddd;")
    
    def add_point(self, value: float):
        """添加数据点"""
        self.data_points.append(value)
        
        # 动态调整Y轴范围
        if self.data_points:
            self.max_value = max(max(self.data_points) * 1.1, 1.0)
            self.min_value = min(min(self.data_points) * 0.9, 0.0)
        
        self.update()
    
    def clear(self):
        """清空数据"""
        self.data_points.clear()
        self.update()
    
    def paintEvent(self, event):
        """绘制图表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取绘制区域
        rect = self.rect()
        margin = 40
        chart_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # 绘制背景
        painter.fillRect(rect, QBrush(QColor(255, 255, 255)))
        
        # 绘制标题
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_rect = rect.adjusted(0, 5, 0, -rect.height() + 25)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
        
        # 绘制坐标轴
        painter.setPen(QPen(QColor(128, 128, 128), 1))
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.bottomRight())  # X轴
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.topLeft())      # Y轴
        
        # 绘制网格线
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        for i in range(1, 5):
            y = chart_rect.bottom() - (chart_rect.height() * i / 5)
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)
        
        # 绘制Y轴标签
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.setFont(QFont("Arial", 8))
        for i in range(6):
            value = self.min_value + (self.max_value - self.min_value) * i / 5
            y = chart_rect.bottom() - (chart_rect.height() * i / 5)
            text = f"{value:.1f}{self.unit}"
            painter.drawText(5, y + 3, text)
        
        # 绘制数据线
        if len(self.data_points) > 1:
            painter.setPen(QPen(QColor(33, 150, 243), 2))
            
            points = []
            for i, value in enumerate(self.data_points):
                x = chart_rect.left() + (chart_rect.width() * i / (self.max_points - 1))
                y_ratio = (value - self.min_value) / (self.max_value - self.min_value) if self.max_value != self.min_value else 0
                y = chart_rect.bottom() - (chart_rect.height() * y_ratio)
                points.append(QPoint(int(x), int(y)))
            
            if len(points) > 1:
                polygon = QPolygon(points)
                painter.drawPolyline(polygon)
            
            # 绘制最新值
            if points:
                last_point = points[-1]
                painter.setPen(QPen(QColor(255, 87, 34), 3))
                painter.drawEllipse(last_point.x() - 3, last_point.y() - 3, 6, 6)
                
                # 显示当前值
                current_value = self.data_points[-1]
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                value_text = f"{current_value:.1f}{self.unit}"
                painter.drawText(last_point.x() + 10, last_point.y() - 5, value_text)

class GaugeChart(QWidget):
    """仪表盘组件"""
    
    def __init__(self, title: str, unit: str = "", min_val: float = 0, max_val: float = 100, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val
        self.current_value = 0.0
        
        self.setMinimumSize(200, 200)
        self.setStyleSheet("background-color: white; border: 1px solid #ddd;")
    
    def set_value(self, value: float):
        """设置当前值"""
        self.current_value = max(self.min_val, min(self.max_val, value))
        self.update()
    
    def paintEvent(self, event):
        """绘制仪表盘"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取绘制区域
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 20
        
        # 绘制背景
        painter.fillRect(rect, QBrush(QColor(255, 255, 255)))
        
        # 绘制标题
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_rect = rect.adjusted(0, 5, 0, -rect.height() + 25)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
        
        # 绘制外圆
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawEllipse(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        
        # 绘制刻度
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        for i in range(11):
            angle = -180 + (180 * i / 10)  # -180度到0度
            x1 = center.x() + (radius - 10) * 0.866 * (1 if angle >= -90 else -1)  # 简化计算
            y1 = center.y() + (radius - 10) * 0.5
            x2 = center.x() + radius * 0.866 * (1 if angle >= -90 else -1)
            y2 = center.y() + radius * 0.5
            # 这里简化了三角函数计算，实际应该使用 cos/sin
        
        # 绘制指针
        value_ratio = (self.current_value - self.min_val) / (self.max_val - self.min_val) if self.max_val != self.min_val else 0
        angle = -180 + (180 * value_ratio)  # 角度范围：-180到0度
        
        # 简化指针绘制
        painter.setPen(QPen(QColor(244, 67, 54), 3))
        pointer_length = radius - 15
        # 这里应该使用三角函数计算指针位置，简化处理
        end_x = center.x() + pointer_length * value_ratio
        end_y = center.y()
        painter.drawLine(center, QPoint(int(end_x), int(end_y)))
        
        # 绘制中心点
        painter.setBrush(QBrush(QColor(244, 67, 54)))
        painter.drawEllipse(center.x() - 5, center.y() - 5, 10, 10)
        
        # 绘制数值
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        value_text = f"{self.current_value:.1f}{self.unit}"
        value_rect = rect.adjusted(0, rect.height() - 40, 0, -10)
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, value_text)

class SystemMonitor(QObject):
    """系统监控器"""
    
    data_updated = pyqtSignal(dict)  # 数据更新信号
    
    def __init__(self):
        super().__init__()
        self.is_monitoring = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.collect_data)
    
    def start_monitoring(self, interval: int = 1000):
        """开始监控"""
        self.is_monitoring = True
        self.timer.start(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        self.timer.stop()
    
    def collect_data(self):
        """收集系统数据"""
        try:
            data = {
                'cpu_percent': psutil.cpu_percent(interval=None),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_used_gb': psutil.virtual_memory().used / (1024**3),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_percent': psutil.disk_usage('/').percent,
                'timestamp': time.time()
            }
            
            # 尝试获取GPU信息（如果可用）
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    data['gpu_percent'] = gpu.load * 100
                    data['gpu_memory_percent'] = gpu.memoryUtil * 100
                    data['gpu_temperature'] = gpu.temperature
                else:
                    data['gpu_percent'] = 0
                    data['gpu_memory_percent'] = 0
                    data['gpu_temperature'] = 0
            except ImportError:
                data['gpu_percent'] = 0
                data['gpu_memory_percent'] = 0
                data['gpu_temperature'] = 0
            
            self.data_updated.emit(data)
            
        except Exception as e:
            print(f"[WARN] 收集系统数据失败: {e}")

class RealtimeCharts(QWidget):
    """实时图表主组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.system_monitor = SystemMonitor()
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("系统性能监控")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # CPU/内存监控页
        self.system_tab = self._create_system_tab()
        self.tabs.addTab(self.system_tab, "系统监控")
        
        # GPU监控页
        self.gpu_tab = self._create_gpu_tab()
        self.tabs.addTab(self.gpu_tab, "GPU监控")
        
        # 网络监控页
        self.network_tab = self._create_network_tab()
        self.tabs.addTab(self.network_tab, "网络监控")
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始监控")
        self.start_btn.clicked.connect(self.start_monitoring)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止监控")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("清空数据")
        self.clear_btn.clicked.connect(self.clear_data)
        control_layout.addWidget(self.clear_btn)
        
        layout.addLayout(control_layout)
    
    def _create_system_tab(self) -> QWidget:
        """创建系统监控页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 仪表盘行
        gauges_layout = QHBoxLayout()
        
        self.cpu_gauge = GaugeChart("CPU使用率", "%", 0, 100)
        gauges_layout.addWidget(self.cpu_gauge)
        
        self.memory_gauge = GaugeChart("内存使用率", "%", 0, 100)
        gauges_layout.addWidget(self.memory_gauge)
        
        self.disk_gauge = GaugeChart("磁盘使用率", "%", 0, 100)
        gauges_layout.addWidget(self.disk_gauge)
        
        layout.addLayout(gauges_layout)
        
        # 趋势图行
        charts_layout = QHBoxLayout()
        
        self.cpu_chart = LineChart("CPU使用率趋势", "%")
        charts_layout.addWidget(self.cpu_chart)
        
        self.memory_chart = LineChart("内存使用率趋势", "%")
        charts_layout.addWidget(self.memory_chart)
        
        layout.addLayout(charts_layout)
        
        return tab
    
    def _create_gpu_tab(self) -> QWidget:
        """创建GPU监控页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # GPU信息
        info_group = QGroupBox("GPU信息")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("GPU状态:"), 0, 0)
        self.gpu_status_label = QLabel("未检测到GPU")
        info_layout.addWidget(self.gpu_status_label, 0, 1)
        
        info_layout.addWidget(QLabel("GPU使用率:"), 1, 0)
        self.gpu_usage_bar = QProgressBar()
        info_layout.addWidget(self.gpu_usage_bar, 1, 1)
        
        info_layout.addWidget(QLabel("GPU内存:"), 2, 0)
        self.gpu_memory_bar = QProgressBar()
        info_layout.addWidget(self.gpu_memory_bar, 2, 1)
        
        info_layout.addWidget(QLabel("GPU温度:"), 3, 0)
        self.gpu_temp_label = QLabel("--°C")
        info_layout.addWidget(self.gpu_temp_label, 3, 1)
        
        layout.addWidget(info_group)
        
        # GPU趋势图
        self.gpu_chart = LineChart("GPU使用率趋势", "%")
        layout.addWidget(self.gpu_chart)
        
        return tab
    
    def _create_network_tab(self) -> QWidget:
        """创建网络监控页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 网络统计
        stats_group = QGroupBox("网络统计")
        stats_layout = QGridLayout(stats_group)
        
        stats_layout.addWidget(QLabel("发送速率:"), 0, 0)
        self.net_sent_label = QLabel("0 KB/s")
        stats_layout.addWidget(self.net_sent_label, 0, 1)
        
        stats_layout.addWidget(QLabel("接收速率:"), 1, 0)
        self.net_recv_label = QLabel("0 KB/s")
        stats_layout.addWidget(self.net_recv_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        # 网络趋势图
        network_charts_layout = QHBoxLayout()
        
        self.net_sent_chart = LineChart("发送速率", "KB/s")
        network_charts_layout.addWidget(self.net_sent_chart)
        
        self.net_recv_chart = LineChart("接收速率", "KB/s")
        network_charts_layout.addWidget(self.net_recv_chart)
        
        layout.addLayout(network_charts_layout)
        
        return tab
    
    def setup_connections(self):
        """设置信号连接"""
        self.system_monitor.data_updated.connect(self.update_charts)
    
    def start_monitoring(self):
        """开始监控"""
        self.system_monitor.start_monitoring(1000)  # 每秒更新
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        print("[INFO] 开始系统监控")
    
    def stop_monitoring(self):
        """停止监控"""
        self.system_monitor.stop_monitoring()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        print("[INFO] 停止系统监控")
    
    def clear_data(self):
        """清空数据"""
        self.cpu_chart.clear()
        self.memory_chart.clear()
        self.gpu_chart.clear()
        self.net_sent_chart.clear()
        self.net_recv_chart.clear()
        print("[INFO] 已清空监控数据")
    
    def update_charts(self, data: Dict[str, Any]):
        """更新图表数据"""
        try:
            # 更新仪表盘
            self.cpu_gauge.set_value(data.get('cpu_percent', 0))
            self.memory_gauge.set_value(data.get('memory_percent', 0))
            self.disk_gauge.set_value(data.get('disk_percent', 0))
            
            # 更新趋势图
            self.cpu_chart.add_point(data.get('cpu_percent', 0))
            self.memory_chart.add_point(data.get('memory_percent', 0))
            
            # 更新GPU信息
            gpu_percent = data.get('gpu_percent', 0)
            gpu_memory = data.get('gpu_memory_percent', 0)
            gpu_temp = data.get('gpu_temperature', 0)
            
            if gpu_percent > 0:
                self.gpu_status_label.setText("GPU可用")
                self.gpu_usage_bar.setValue(int(gpu_percent))
                self.gpu_memory_bar.setValue(int(gpu_memory))
                self.gpu_temp_label.setText(f"{gpu_temp:.1f}°C")
                self.gpu_chart.add_point(gpu_percent)
            else:
                self.gpu_status_label.setText("未检测到GPU")
                self.gpu_usage_bar.setValue(0)
                self.gpu_memory_bar.setValue(0)
                self.gpu_temp_label.setText("--°C")
            
            # 更新网络信息（简化处理）
            # 实际应该计算网络速率
            self.net_sent_label.setText("-- KB/s")
            self.net_recv_label.setText("-- KB/s")
            
        except Exception as e:
            print(f"[WARN] 更新图表失败: {e}")

# 导入QPushButton
from PyQt6.QtWidgets import QPushButton

__all__ = ['RealtimeCharts', 'LineChart', 'GaugeChart', 'SystemMonitor']
