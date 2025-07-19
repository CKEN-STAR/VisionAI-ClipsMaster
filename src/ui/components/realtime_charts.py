#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 实时图表组件
用于CPU/GPU使用率监控和数据可视化
"""

import sys
import os
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QProgressBar, QGroupBox, 
                               QSplitter, QTabWidget, QComboBox, QCheckBox,
                               QFrame, QGridLayout)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QRect
    from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

class ChartWidget(QWidget):
    """基础图表组件"""
    
    def __init__(self, title: str = "", max_points: int = 100, parent=None):
        super().__init__(parent)
        self.title = title
        self.max_points = max_points
        self.data_series = {}  # 存储多个数据系列
        self.colors = [
            QColor(255, 0, 0),    # 红色
            QColor(0, 255, 0),    # 绿色  
            QColor(0, 0, 255),    # 蓝色
            QColor(255, 255, 0),  # 黄色
            QColor(255, 0, 255),  # 紫色
            QColor(0, 255, 255),  # 青色
        ]
        self.setMinimumSize(300, 200)
        
    def add_series(self, name: str, color: QColor = None):
        """添加数据系列"""
        if color is None:
            color = self.colors[len(self.data_series) % len(self.colors)]
        
        self.data_series[name] = {
            "data": deque(maxlen=self.max_points),
            "color": color,
            "visible": True
        }
    
    def add_data_point(self, series_name: str, value: float):
        """添加数据点"""
        if series_name in self.data_series:
            self.data_series[series_name]["data"].append(value)
            self.update()
    
    def clear_data(self):
        """清空数据"""
        for series in self.data_series.values():
            series["data"].clear()
        self.update()
    
    def set_series_visible(self, series_name: str, visible: bool):
        """设置数据系列可见性"""
        if series_name in self.data_series:
            self.data_series[series_name]["visible"] = visible
            self.update()
    
    def paintEvent(self, event):
        """绘制图表"""
        if not QT_AVAILABLE:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # 绘制边框
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        
        # 绘制标题
        if self.title:
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            title_rect = QRect(10, 5, self.width() - 20, 20)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
        
        # 计算绘图区域
        margin = 40
        chart_rect = QRect(margin, 30, self.width() - 2 * margin, self.height() - 60)
        
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return
        
        # 绘制网格
        self._draw_grid(painter, chart_rect)
        
        # 绘制数据系列
        for series_name, series_data in self.data_series.items():
            if series_data["visible"] and len(series_data["data"]) > 1:
                self._draw_series(painter, chart_rect, series_data)
        
        # 绘制图例
        self._draw_legend(painter)
    
    def _draw_grid(self, painter: QPainter, rect: QRect):
        """绘制网格"""
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        # 垂直网格线
        for i in range(1, 10):
            x = rect.left() + (rect.width() * i // 10)
            painter.drawLine(x, rect.top(), x, rect.bottom())
        
        # 水平网格线
        for i in range(1, 5):
            y = rect.top() + (rect.height() * i // 5)
            painter.drawLine(rect.left(), y, rect.right(), y)
    
    def _draw_series(self, painter: QPainter, rect: QRect, series_data: Dict):
        """绘制数据系列"""
        data = list(series_data["data"])
        if len(data) < 2:
            return
        
        painter.setPen(QPen(series_data["color"], 2))
        
        # 计算点的位置
        points = []
        for i, value in enumerate(data):
            x = rect.left() + (rect.width() * i // max(1, len(data) - 1))
            y = rect.bottom() - (rect.height() * value // 100)  # 假设值范围0-100
            points.append((x, y))
        
        # 绘制线条
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
    
    def _draw_legend(self, painter: QPainter):
        """绘制图例"""
        legend_y = self.height() - 25
        legend_x = 10
        
        painter.setFont(QFont("Arial", 9))
        
        for series_name, series_data in self.data_series.items():
            if series_data["visible"]:
                # 绘制颜色块
                painter.fillRect(legend_x, legend_y, 10, 10, series_data["color"])
                
                # 绘制文本
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(legend_x + 15, legend_y + 8, series_name)
                
                legend_x += len(series_name) * 8 + 30

class SystemMonitorWorker(QObject):
    """系统监控工作线程"""
    
    # 信号定义
    data_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        
    def start_monitoring(self):
        """开始监控"""
        self.is_running = True
        
        # 创建定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self._collect_system_data)
        self.timer.start(1000)  # 每秒更新一次
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if hasattr(self, 'timer'):
            self.timer.stop()
    
    def _collect_system_data(self):
        """收集系统数据"""
        if not self.is_running:
            return
        
        # 模拟系统数据（实际应用中可以使用psutil等库）
        import random
        
        data = {
            "cpu_usage": random.uniform(10, 90),
            "memory_usage": random.uniform(20, 80),
            "gpu_usage": random.uniform(0, 100),
            "gpu_memory": random.uniform(10, 95),
            "network_in": random.uniform(0, 100),
            "network_out": random.uniform(0, 100),
            "disk_read": random.uniform(0, 50),
            "disk_write": random.uniform(0, 50),
            "timestamp": datetime.now()
        }
        
        self.data_updated.emit(data)

class RealtimeCharts(QWidget):
    """实时图表主组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 监控工作线程
        self.monitor_worker = None
        self.monitor_thread = None
        
        # 图表组件
        self.charts = {}
        
        # 多语言支持
        self.language = "zh_CN"
        self.translations = {
            "zh_CN": {
                "title": "实时监控图表",
                "cpu_usage": "CPU使用率",
                "memory_usage": "内存使用率", 
                "gpu_monitor": "GPU监控",
                "network_monitor": "网络监控",
                "disk_monitor": "磁盘监控",
                "start_monitoring": "开始监控",
                "stop_monitoring": "停止监控",
                "clear_data": "清空数据",
                "gpu_usage": "GPU使用率",
                "gpu_memory": "GPU内存",
                "network_in": "网络接收",
                "network_out": "网络发送",
                "disk_read": "磁盘读取",
                "disk_write": "磁盘写入"
            },
            "en_US": {
                "title": "Realtime Monitoring Charts",
                "cpu_usage": "CPU Usage",
                "memory_usage": "Memory Usage",
                "gpu_monitor": "GPU Monitor", 
                "network_monitor": "Network Monitor",
                "disk_monitor": "Disk Monitor",
                "start_monitoring": "Start Monitoring",
                "stop_monitoring": "Stop Monitoring",
                "clear_data": "Clear Data",
                "gpu_usage": "GPU Usage",
                "gpu_memory": "GPU Memory",
                "network_in": "Network In",
                "network_out": "Network Out",
                "disk_read": "Disk Read",
                "disk_write": "Disk Write"
            }
        }
        
        self.init_ui()
        self.setup_monitoring()
    
    def init_ui(self):
        """初始化用户界面"""
        if not QT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(self.tr("title"))
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 图表区域
        charts_area = self.create_charts_area()
        layout.addWidget(charts_area)
    
    def create_control_panel(self) -> QFrame:
        """创建控制面板"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)
        
        # 开始监控按钮
        self.start_btn = QPushButton(self.tr("start_monitoring"))
        self.start_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_btn)
        
        # 停止监控按钮
        self.stop_btn = QPushButton(self.tr("stop_monitoring"))
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # 清空数据按钮
        clear_btn = QPushButton(self.tr("clear_data"))
        clear_btn.clicked.connect(self.clear_all_data)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        
        # 状态指示器
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        return frame
    
    def create_charts_area(self) -> QWidget:
        """创建图表区域"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # CPU和内存图表
        cpu_memory_chart = ChartWidget(self.tr("cpu_usage") + " & " + self.tr("memory_usage"))
        cpu_memory_chart.add_series(self.tr("cpu_usage"), QColor(255, 0, 0))
        cpu_memory_chart.add_series(self.tr("memory_usage"), QColor(0, 255, 0))
        self.charts["cpu_memory"] = cpu_memory_chart
        layout.addWidget(cpu_memory_chart, 0, 0)
        
        # GPU监控图表
        gpu_chart = ChartWidget(self.tr("gpu_monitor"))
        gpu_chart.add_series(self.tr("gpu_usage"), QColor(0, 0, 255))
        gpu_chart.add_series(self.tr("gpu_memory"), QColor(255, 0, 255))
        self.charts["gpu"] = gpu_chart
        layout.addWidget(gpu_chart, 0, 1)
        
        # 网络监控图表
        network_chart = ChartWidget(self.tr("network_monitor"))
        network_chart.add_series(self.tr("network_in"), QColor(0, 255, 255))
        network_chart.add_series(self.tr("network_out"), QColor(255, 255, 0))
        self.charts["network"] = network_chart
        layout.addWidget(network_chart, 1, 0)
        
        # 磁盘监控图表
        disk_chart = ChartWidget(self.tr("disk_monitor"))
        disk_chart.add_series(self.tr("disk_read"), QColor(128, 0, 128))
        disk_chart.add_series(self.tr("disk_write"), QColor(255, 128, 0))
        self.charts["disk"] = disk_chart
        layout.addWidget(disk_chart, 1, 1)
        
        return widget
    
    def setup_monitoring(self):
        """设置监控"""
        if not QT_AVAILABLE:
            return
            
        self.monitor_worker = SystemMonitorWorker()
        self.monitor_thread = QThread()
        
        # 连接信号
        self.monitor_worker.data_updated.connect(self.update_charts)
        
        # 移动到线程
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.start()
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitor_worker:
            self.monitor_worker.start_monitoring()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("监控中...")
            self.status_label.setStyleSheet("color: blue; font-weight: bold;")
    
    def stop_monitoring(self):
        """停止监控"""
        if self.monitor_worker:
            self.monitor_worker.stop_monitoring()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("已停止")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def update_charts(self, data: Dict[str, Any]):
        """更新图表数据"""
        # 更新CPU和内存图表
        self.charts["cpu_memory"].add_data_point(self.tr("cpu_usage"), data["cpu_usage"])
        self.charts["cpu_memory"].add_data_point(self.tr("memory_usage"), data["memory_usage"])
        
        # 更新GPU图表
        self.charts["gpu"].add_data_point(self.tr("gpu_usage"), data["gpu_usage"])
        self.charts["gpu"].add_data_point(self.tr("gpu_memory"), data["gpu_memory"])
        
        # 更新网络图表
        self.charts["network"].add_data_point(self.tr("network_in"), data["network_in"])
        self.charts["network"].add_data_point(self.tr("network_out"), data["network_out"])
        
        # 更新磁盘图表
        self.charts["disk"].add_data_point(self.tr("disk_read"), data["disk_read"])
        self.charts["disk"].add_data_point(self.tr("disk_write"), data["disk_write"])
    
    def clear_all_data(self):
        """清空所有图表数据"""
        for chart in self.charts.values():
            chart.clear_data()
    
    def tr(self, key: str) -> str:
        """翻译函数"""
        return self.translations.get(self.language, {}).get(key, key)
    
    def set_language(self, language: str):
        """设置语言"""
        if language in self.translations:
            self.language = language
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.monitor_worker:
            self.monitor_worker.stop_monitoring()
        if self.monitor_thread:
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        event.accept()
