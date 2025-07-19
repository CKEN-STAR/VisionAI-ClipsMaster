#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
内存可视化组件

提供可嵌入其他UI界面的轻量级内存监控组件，可以在各种窗口中展示内存使用情况。
"""

import logging
from typing import Dict, Optional, List, Any, Tuple
import time
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame, QSizePolicy,
    QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

from src.monitoring import (
    get_metrics_collector, get_alert_manager, 
    AlertLevel, check_memory_usage
)

# 设置日志
logger = logging.getLogger("memory_visualization")


class MemoryBar(QWidget):

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存使用进度条组件"""
    
    # 内存预警信号
    alert_signal = pyqtSignal(str, float)  # 级别, 值
    
    def __init__(self, title: str = "内存使用", parent=None):
        """初始化内存进度条
        
        Args:
            title: 标题
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题标签
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.title_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% (%v MB)")
        layout.addWidget(self.progress_bar)
        
        # 使用布局
        self.setLayout(layout)
        
        # 预警阈值
        self.warning_threshold = 80
        self.error_threshold = 90
        self.critical_threshold = 95
        
        # 更新计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_memory)
        
        # 初始化数据
        self.memory_percent = 0
        self.memory_mb = 0
        self.is_system_memory = True  # 是否显示系统内存（而非进程内存）
    
    def start_monitoring(self, interval: int = 2000):
        """开始监控
        
        Args:
            interval: 更新间隔（毫秒）
        """
        self.timer.start(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.timer.stop()
    
    def set_memory(self, percent: float, memory_mb: float = 0):
        """设置内存使用值
        
        Args:
            percent: 使用百分比
            memory_mb: 使用量（MB）
        """
        self.memory_percent = percent
        self.memory_mb = memory_mb
        
        # 更新进度条
        self.progress_bar.setValue(int(percent))
        
        # 根据使用率设置颜色
        if percent >= self.critical_threshold:
            color = "rgba(244, 67, 54, 200)"  # 红色
            level = AlertLevel.CRITICAL.value
        elif percent >= self.error_threshold:
            color = "rgba(255, 152, 0, 200)"  # 橙色
            level = AlertLevel.ERROR.value
        elif percent >= self.warning_threshold:
            color = "rgba(255, 193, 7, 200)"  # 黄色
            level = AlertLevel.WARNING.value
        else:
            color = "rgba(76, 175, 80, 200)"  # 绿色
            level = AlertLevel.INFO.value
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ccc;
                border-radius: 2px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
        
        # 发出预警信号
        if percent >= self.warning_threshold:
            self.alert_signal.emit(level, percent)
    
    def set_thresholds(self, warning: float, error: float, critical: float):
        """设置预警阈值
        
        Args:
            warning: 警告阈值
            error: 错误阈值
            critical: 严重阈值
        """
        self.warning_threshold = warning
        self.error_threshold = error
        self.critical_threshold = critical
    
    def set_is_system_memory(self, is_system: bool):
        """设置是否显示系统内存
        
        Args:
            is_system: 是否是系统内存
        """
        self.is_system_memory = is_system
    
    def _update_memory(self):
        """更新内存使用情况"""
        try:
            metrics_collector = get_metrics_collector()
            
            if self.is_system_memory:
                # 系统内存
                memory_percent = metrics_collector.collect_on_demand("system_metrics.total_memory")
                if memory_percent is not None:
                    # 获取系统总内存
                    import psutil
                    total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
                    used_memory = total_memory * memory_percent / 100
                    self.set_memory(memory_percent, used_memory)
            else:
                # 进程内存
                memory_mb = metrics_collector.collect_on_demand("system_metrics.process_rss")
                if memory_mb is not None:
                    # 计算百分比
                    import psutil
                    total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
                    memory_percent = (memory_mb / total_memory) * 100
                    self.set_memory(memory_percent, memory_mb)
        
        except Exception as e:
            logger.error(f"更新内存使用出错: {e}")


class MemoryMiniTrend(QWidget):
    """简易内存趋势图"""
    
    def __init__(self, parent=None):
        """初始化内存趋势图
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 设置最小大小
        self.setMinimumSize(100, 50)
        
        # 初始化数据
        self.values = deque(maxlen=100)  # 最多保存100个点
        self.max_value = 100
        
        # 设置绘图颜色
        self.line_color = QColor(76, 114, 176)  # 蓝色
        self.fill_color = QColor(76, 114, 176, 100)  # 半透明蓝色
        
        # 更新计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_trend)
        
        # 是否显示系统内存
        self.is_system_memory = True
    
    def start_monitoring(self, interval: int = 2000):
        """开始监控
        
        Args:
            interval: 更新间隔（毫秒）
        """
        self.timer.start(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.timer.stop()
    
    def add_value(self, value: float):
        """添加数据点
        
        Args:
            value: 数据值
        """
        self.values.append(value)
        if value > self.max_value:
            self.max_value = value
        self.update()  # 触发重绘
    
    def set_is_system_memory(self, is_system: bool):
        """设置是否显示系统内存
        
        Args:
            is_system: 是否是系统内存
        """
        self.is_system_memory = is_system
    
    def paintEvent(self, event):
        """绘制趋势图"""
        if not self.values:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算绘图区域
        width = self.width()
        height = self.height()
        
        # 计算点间距
        step = width / (len(self.values) - 1) if len(self.values) > 1 else width
        
        # 绘制填充区域
        path = QPainterPath()
        path.moveTo(0, height)
        
        # 添加数据点
        for i, value in enumerate(self.values):
            x = i * step
            y = height - (value / self.max_value) * height
            path.lineTo(x, y)
        
        # 闭合路径
        path.lineTo((len(self.values) - 1) * step, height)
        path.lineTo(0, height)
        
        # 填充区域
        painter.setBrush(QBrush(self.fill_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        
        # 绘制曲线
        painter.setPen(QPen(self.line_color, 2))
        
        for i in range(len(self.values) - 1):
            x1 = i * step
            y1 = height - (self.values[i] / self.max_value) * height
            x2 = (i + 1) * step
            y2 = height - (self.values[i + 1] / self.max_value) * height
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _update_trend(self):
        """更新趋势数据"""
        try:
            metrics_collector = get_metrics_collector()
            
            if self.is_system_memory:
                # 系统内存
                memory_percent = metrics_collector.collect_on_demand("system_metrics.total_memory")
                if memory_percent is not None:
                    self.add_value(memory_percent)
            else:
                # 进程内存
                memory_mb = metrics_collector.collect_on_demand("system_metrics.process_rss")
                if memory_mb is not None:
                    # 计算百分比
                    import psutil
                    total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
                    memory_percent = (memory_mb / total_memory) * 100
                    self.add_value(memory_percent)
        
        except Exception as e:
            logger.error(f"更新内存趋势出错: {e}")


class MemoryWidget(QWidget):
    """内存监控小组件
    
    可嵌入到UI的轻量级内存监控组件
    """
    
    def __init__(self, parent=None):
        """初始化内存监控组件
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 系统内存进度条
        self.system_memory_bar = MemoryBar("系统内存")
        self.system_memory_bar.set_is_system_memory(True)
        layout.addWidget(self.system_memory_bar)
        
        # 进程内存进度条
        self.process_memory_bar = MemoryBar("进程内存")
        self.process_memory_bar.set_is_system_memory(False)
        layout.addWidget(self.process_memory_bar)
        
        # 趋势图
        trend_group = QGroupBox("内存趋势")
        trend_layout = QVBoxLayout(trend_group)
        
        if HAS_PYQTGRAPH:
            # 使用PyQtGraph绘制趋势图
            self.trend_graph = pg.PlotWidget()
            self.trend_graph.setBackground('w')
            self.trend_graph.showGrid(x=True, y=True, alpha=0.3)
            self.trend_graph.setLabel('left', '使用率', units='%')
            self.trend_graph.setYRange(0, 100)
            
            # 创建曲线
            self.system_curve = self.trend_graph.plot(pen=pg.mkPen(color=(76, 114, 176), width=2), name="系统内存")
            self.process_curve = self.trend_graph.plot(pen=pg.mkPen(color=(214, 39, 40), width=2), name="进程内存")
            
            trend_layout.addWidget(self.trend_graph)
            
            # 初始化数据
            self.timestamps = []
            self.system_values = []
            self.process_values = []
            self.start_time = time.time()
            
        else:
            # 使用简易趋势图
            self.system_trend = MemoryMiniTrend()
            self.system_trend.set_is_system_memory(True)
            trend_layout.addWidget(self.system_trend)
            
            self.process_trend = MemoryMiniTrend()
            self.process_trend.set_is_system_memory(False)
            trend_layout.addWidget(self.process_trend)
        
        layout.addWidget(trend_group)
        
        # 使用布局
        self.setLayout(layout)
        
        # 更新计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_data)
        
        # 设置首选大小
        self.setMinimumWidth(200)
        self.setMinimumHeight(300)
    
    def start_monitoring(self, interval: int = 2000):
        """开始监控
        
        Args:
            interval: 更新间隔（毫秒）
        """
        self.timer.start(interval)
        
        # 启动进度条监控
        self.system_memory_bar.start_monitoring(interval)
        self.process_memory_bar.start_monitoring(interval)
        
        if not HAS_PYQTGRAPH:
            # 启动简易趋势图监控
            self.system_trend.start_monitoring(interval)
            self.process_trend.start_monitoring(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.timer.stop()
        
        # 停止进度条监控
        self.system_memory_bar.stop_monitoring()
        self.process_memory_bar.stop_monitoring()
        
        if not HAS_PYQTGRAPH:
            # 停止简易趋势图监控
            self.system_trend.stop_monitoring()
            self.process_trend.stop_monitoring()
    
    def set_update_interval(self, interval: int):
        """设置更新间隔
        
        Args:
            interval: 更新间隔（毫秒）
        """
        self.timer.setInterval(interval)
        
        # 更新进度条监控间隔
        self.system_memory_bar.timer.setInterval(interval)
        self.process_memory_bar.timer.setInterval(interval)
        
        if not HAS_PYQTGRAPH:
            # 更新简易趋势图监控间隔
            self.system_trend.timer.setInterval(interval)
            self.process_trend.timer.setInterval(interval)
    
    def _update_data(self):
        """更新数据"""
        if not HAS_PYQTGRAPH:
            # 简易趋势图由其自身更新
            return
            
        try:
            metrics_collector = get_metrics_collector()
            
            # 获取内存使用情况
            system_memory = metrics_collector.collect_on_demand("system_metrics.total_memory")
            process_memory_mb = metrics_collector.collect_on_demand("system_metrics.process_rss")
            
            if system_memory is not None and process_memory_mb is not None:
                # 计算进程内存百分比
                import psutil
                total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
                process_memory = (process_memory_mb / total_memory) * 100
                
                # 添加数据点
                current_time = time.time()
                if not self.timestamps:
                    self.start_time = current_time
                    
                self.timestamps.append(current_time - self.start_time)
                self.system_values.append(system_memory)
                self.process_values.append(process_memory)
                
                # 限制数据点数量（5分钟，每2秒一个点，最多150个点）
                max_points = 150
                if len(self.timestamps) > max_points:
                    self.timestamps = self.timestamps[-max_points:]
                    self.system_values = self.system_values[-max_points:]
                    self.process_values = self.process_values[-max_points:]
                
                # 更新曲线
                self.system_curve.setData(self.timestamps, self.system_values)
                self.process_curve.setData(self.timestamps, self.process_values)
        
        except Exception as e:
            logger.error(f"更新内存数据出错: {e}")


class MemoryStatusIndicator(QWidget):
    """内存状态指示器
    
    极简的内存状态指示器，可以放在状态栏或工具栏中
    """
    
    # 点击信号
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化内存状态指示器
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 设置大小
        self.setFixedSize(16, 16)
        
        # 状态颜色
        self.normal_color = QColor(76, 175, 80)  # 绿色
        self.warning_color = QColor(255, 193, 7)  # 黄色
        self.error_color = QColor(255, 152, 0)    # 橙色
        self.critical_color = QColor(244, 67, 54) # 红色
        
        # 当前状态
        self.status = "normal"  # normal, warning, error, critical
        
        # 当前值
        self.value = 0
        
        # 更新计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_status)
        
        # 设置工具提示
        self.setToolTip("内存使用正常")
        
        # 启用鼠标追踪
        self.setMouseTracking(True)
    
    def start_monitoring(self, interval: int = 5000):
        """开始监控
        
        Args:
            interval: 更新间隔（毫秒）
        """
        self.timer.start(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.timer.stop()
    
    def set_status(self, status: str, value: float = 0):
        """设置状态
        
        Args:
            status: 状态（normal, warning, error, critical）
            value: 相关数值
        """
        if status not in ["normal", "warning", "error", "critical"]:
            return
            
        self.status = status
        self.value = value
        
        # 更新工具提示
        if status == "normal":
            self.setToolTip(f"内存使用正常: {value:.1f}%")
        elif status == "warning":
            self.setToolTip(f"内存使用警告: {value:.1f}%")
        elif status == "error":
            self.setToolTip(f"内存使用错误: {value:.1f}%")
        elif status == "critical":
            self.setToolTip(f"内存使用严重: {value:.1f}%")
        
        # 触发重绘
        self.update()
    
    def paintEvent(self, event):
        """绘制指示器"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 确定颜色
        if self.status == "critical":
            color = self.critical_color
        elif self.status == "error":
            color = self.error_color
        elif self.status == "warning":
            color = self.warning_color
        else:
            color = self.normal_color
        
        # 绘制圆形
        painter.setPen(QPen(Qt.GlobalColor.gray, 1))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(2, 2, 12, 12)
    
    def _update_status(self):
        """更新状态"""
        try:
            metrics_collector = get_metrics_collector()
            system_memory = metrics_collector.collect_on_demand("system_metrics.total_memory")
            
            if system_memory is not None:
                # 根据内存使用率设置状态
                if system_memory >= 95:
                    self.set_status("critical", system_memory)
                elif system_memory >= 90:
                    self.set_status("error", system_memory)
                elif system_memory >= 80:
                    self.set_status("warning", system_memory)
                else:
                    self.set_status("normal", system_memory)
        
        except Exception as e:
            logger.error(f"更新内存状态出错: {e}")
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        # 发射点击信号
        self.clicked.emit()
        super().mousePressEvent(event)


# 创建辅助函数
def create_embedded_memory_widget(parent=None) -> MemoryWidget:
    """创建可嵌入的内存监控组件
    
    Args:
        parent: 父窗口
        
    Returns:
        内存监控组件
    """
    widget = MemoryWidget(parent)
    widget.start_monitoring()
    return widget


def create_status_indicator(parent=None) -> MemoryStatusIndicator:
    """创建状态栏内存指示器
    
    Args:
        parent: 父窗口
        
    Returns:
        内存状态指示器
    """
    indicator = MemoryStatusIndicator(parent)
    indicator.start_monitoring()
    return indicator 