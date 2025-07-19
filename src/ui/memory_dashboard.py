#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
内存监控可视化看板

为VisionAI-ClipsMaster提供实时内存使用趋势、资源占用展示，集成预警系统。
适用于低资源设备(4GB RAM/无GPU)环境。
"""

import sys
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict, deque
from threading import Lock, Thread
import os

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
        QPushButton, QComboBox, QSizePolicy, QGroupBox, QTableWidget,
        QTableWidgetItem, QHeaderView, QProgressBar, QTabWidget,
        QApplication, QMainWindow
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
    from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPixmap, QRadialGradient
    import pyqtgraph as pg
    HAS_QT = True
except ImportError:
    HAS_QT = False
    logging.warning("PyQt6 或 pyqtgraph 未安装，可视化看板将不可用")

# 导入监控组件
from src.monitoring import (
    get_metrics_collector, get_alert_manager, 
    DataCollector, get_collector,
    AlertLevel, AlertCategory, 
    check_memory_usage
)

# 设置日志
logger = logging.getLogger("memory_dashboard")


class GaugeChart(QWidget):
    """仪表盘组件"""
    
    def __init__(self, title: str, parent=None):
        """初始化仪表盘
        
        Args:
            title: 仪表盘标题
            parent: 父窗口
        """
        super().__init__(parent)
        self.title = title
        self.value = 0
        self.min_value = 0
        self.max_value = 100
        self.unit = "%"
        self.alert_threshold = 80
        self.critical_threshold = 95
        
        # 设置首选大小
        self.setMinimumSize(200, 200)
        
        # 状态颜色
        self.normal_color = QColor(76, 175, 80)  # 绿色
        self.warning_color = QColor(255, 152, 0)  # 橙色
        self.critical_color = QColor(244, 67, 54)  # 红色
    
    def set(self, value: float) -> None:
        """设置仪表盘值
        
        Args:
            value: 仪表盘值
        """
        self.value = max(self.min_value, min(value, self.max_value))
        self.update()
    
    def set_range(self, min_value: float, max_value: float) -> None:
        """设置仪表盘范围
        
        Args:
            min_value: 最小值
            max_value: 最大值
        """
        self.min_value = min_value
        self.max_value = max_value
    
    def set_thresholds(self, alert: float, critical: float) -> None:
        """设置告警阈值
        
        Args:
            alert: 警告阈值
            critical: 严重阈值
        """
        self.alert_threshold = alert
        self.critical_threshold = critical
    
    def set_unit(self, unit: str) -> None:
        """设置单位
        
        Args:
            unit: 单位字符串
        """
        self.unit = unit
    
    def paintEvent(self, event):
        """绘制仪表盘"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算仪表盘位置和大小
        w = self.width()
        h = self.height()
        size = min(w, h)
        
        # 计算圆心和半径
        cx = w / 2
        cy = h / 2
        radius = size / 2 * 0.8
        
        # 计算指针角度 (-30到210度，总共240度)
        angle_range = 240
        start_angle = -30
        normalized_value = (self.value - self.min_value) / (self.max_value - self.min_value)
        angle = start_angle + normalized_value * angle_range
        
        # 绘制背景圆弧
        painter.setPen(QPen(Qt.GlobalColor.gray, 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2), start_angle * 16, angle_range * 16)
        
        # 确定当前颜色
        if self.value >= self.critical_threshold:
            color = self.critical_color
        elif self.value >= self.alert_threshold:
            color = self.warning_color
        else:
            color = self.normal_color
        
        # 绘制值圆弧
        painter.setPen(QPen(color, 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2), start_angle * 16, int(normalized_value * angle_range * 16))
        
        # 绘制中心点
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)
        
        # 绘制指针
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine))
        angle_rad = angle * 3.14159 / 180
        pointer_length = radius * 0.7
        px = cx + pointer_length * -1 * (-1 * (angle_rad + 3.14159 / 2)).cos()
        py = cy + pointer_length * -1 * (-1 * (angle_rad + 3.14159 / 2)).sin()
        painter.drawLine(int(cx), int(cy), int(px), int(py))
        
        # 绘制标题
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(0, 0, w, h - radius / 2, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, self.title)
        
        # 绘制值
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.setPen(QPen(color))
        text = f"{self.value:.1f}{self.unit}"
        painter.drawText(0, h - radius / 2, w, radius / 2, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignCenter, text)


class LineChart(QWidget):
    """折线图组件"""
    
    def __init__(self, title: str, parent=None):
        """初始化折线图
        
        Args:
            title: 折线图标题
            parent: 父窗口
        """
        super().__init__(parent)
        self.title = title
        
        # 创建pyqtgraph图表
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle(title, color="k", size="12pt")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', '使用率', units='%')
        self.plot_widget.setLabel('bottom', '时间 (分:秒)')
        
        # 创建曲线
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color=(76, 114, 176), width=2))
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
        
        # 初始化数据
        self.timestamps = []
        self.values = []
        self.start_time = time.time()
        
        # 设置最大显示点数（5分钟，采样间隔1秒）
        self.max_points = 300
    
    def add_point(self, value: float) -> None:
        """添加数据点
        
        Args:
            value: Y轴值
        """
        # 添加新数据点
        current_time = time.time()
        if not self.timestamps:
            self.start_time = current_time
            
        self.timestamps.append(current_time - self.start_time)
        self.values.append(value)
        
        # 限制数据点数量
        if len(self.timestamps) > self.max_points:
            self.timestamps.pop(0)
            self.values.pop(0)
        
        # 更新图表
        self.curve.setData(self.timestamps, self.values)
        
        # 自动调整X轴范围
        self.plot_widget.setXRange(
            max(0, self.timestamps[-1] - 300),  # 显示最近5分钟
            self.timestamps[-1]
        )
        
        # 自定义X轴标签格式
        def format_time(x):
            seconds = int(x)
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        
        self.plot_widget.getAxis('bottom').setTicks([[(i, format_time(i)) for i in range(0, int(self.timestamps[-1]) + 60, 60)]])


class ComponentTable(QTableWidget):
    """组件内存占用表格"""
    
    def __init__(self, parent=None):
        """初始化表格
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 设置列
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["组件", "内存占用 (MB)"])
        
        # 调整列宽
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        # 设置排序
        self.setSortingEnabled(True)
        
        # 初始化数据
        self.components = {}
    
    def update_components(self, components: Dict[str, float]) -> None:
        """更新组件列表
        
        Args:
            components: 组件内存占用字典 {组件名: 内存占用(MB)}
        """
        self.components = components
        
        # 更新行数
        self.setRowCount(len(components))
        
        # 填充数据
        for row, (name, memory) in enumerate(sorted(components.items(), key=lambda x: x[1], reverse=True)):
            self.setItem(row, 0, QTableWidgetItem(name))
            self.setItem(row, 1, QTableWidgetItem(f"{memory:.1f}"))
            
            # 为较大的内存使用设置背景色
            if memory > 1000:
                self.item(row, 1).setBackground(QBrush(QColor(244, 67, 54, 100)))  # 红色
            elif memory > 500:
                self.item(row, 1).setBackground(QBrush(QColor(255, 152, 0, 100)))  # 橙色
            elif memory > 100:
                self.item(row, 1).setBackground(QBrush(QColor(255, 193, 7, 100)))  # 黄色


class AlertWidget(QWidget):
    """预警组件"""
    
    def __init__(self, parent=None):
        """初始化预警组件
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("最近预警")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title_label)
        
        # 预警表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["级别", "时间", "资源", "值"])
        
        # 调整列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # 初始化缓存
        self.alerts_cache = []
    
    def update_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """更新预警列表
        
        Args:
            alerts: 预警列表
        """
        self.alerts_cache = alerts
        
        # 更新行数
        self.table.setRowCount(len(alerts))
        
        # 填充数据
        for row, alert in enumerate(alerts):
            # 级别
            level_item = QTableWidgetItem(alert["level"])
            if alert["level"] == AlertLevel.CRITICAL.value:
                level_item.setBackground(QBrush(QColor(244, 67, 54, 100)))  # 红色
            elif alert["level"] == AlertLevel.ERROR.value:
                level_item.setBackground(QBrush(QColor(255, 152, 0, 100)))  # 橙色
            elif alert["level"] == AlertLevel.WARNING.value:
                level_item.setBackground(QBrush(QColor(255, 193, 7, 100)))  # 黄色
            self.table.setItem(row, 0, level_item)
            
            # 时间
            try:
                timestamp = datetime.fromisoformat(alert["timestamp"])
                time_text = timestamp.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                time_text = str(alert["timestamp"])
            self.table.setItem(row, 1, QTableWidgetItem(time_text))
            
            # 资源
            self.table.setItem(row, 2, QTableWidgetItem(f"{alert['category']}/{alert['resource']}"))
            
            # 值
            self.table.setItem(row, 3, QTableWidgetItem(str(alert["value"])))


class MemoryDashboard(QWidget):

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存监控仪表盘"""
    
    def __init__(self, parent=None):
        """初始化内存仪表盘
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 初始化数据收集器
        self.data_collector = get_collector()
        self.metrics_collector = get_metrics_collector()
        self.alert_manager = get_alert_manager()
        
        # 数据缓存
        self.memory_data = deque(maxlen=300)  # 最多保存5分钟数据
        self.component_memory = {}
        
        # 初始化UI
        self.init_ui()
        
        # 启动更新定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)  # 每秒更新一次
        
        # 刷新一次数据
        self.update_dashboard()
    
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout()
        
        # 创建标签页
        tabs = QTabWidget()
        
        # === 概览标签页 ===
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        # 仪表盘部分
        gauges_widget = QWidget()
        gauges_layout = QHBoxLayout(gauges_widget)
        
        # 系统内存仪表盘
        self.gauges = {
            'system': GaugeChart(title="系统内存"),
            'process': GaugeChart(title="进程内存")
        }
        
        # 设置进程内存单位为MB
        self.gauges['process'].set_unit("MB")
        self.gauges['process'].set_range(0, 4000)  # 假设最大4GB
        self.gauges['process'].set_thresholds(3000, 3700)  # 警告和严重阈值
        
        # 添加仪表盘
        for gauge in self.gauges.values():
            gauges_layout.addWidget(gauge)
        
        overview_layout.addWidget(gauges_widget)
        
        # 内存趋势图
        self.trend = LineChart(title="内存趋势")
        overview_layout.addWidget(self.trend)
        
        # 组件内存排行
        components_group = QGroupBox("组件内存占用排行")
        components_layout = QVBoxLayout(components_group)
        
        self.components_table = ComponentTable()
        components_layout.addWidget(self.components_table)
        
        overview_layout.addWidget(components_group)
        
        # === 预警标签页 ===
        alerts_tab = QWidget()
        alerts_layout = QVBoxLayout(alerts_tab)
        
        self.alert_widget = AlertWidget()
        alerts_layout.addWidget(self.alert_widget)
        
        # === 添加标签页 ===
        tabs.addTab(overview_tab, "概览")
        tabs.addTab(alerts_tab, "预警记录")
        
        main_layout.addWidget(tabs)
        
        # 控制按钮
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.update_dashboard)
        control_layout.addWidget(self.refresh_button)
        
        self.pause_button = QPushButton("暂停")
        self.pause_button.clicked.connect(self.toggle_update)
        control_layout.addWidget(self.pause_button)
        
        main_layout.addWidget(control_widget)
        
        self.setLayout(main_layout)
        self.resize(800, 600)
        self.setWindowTitle("内存监控仪表盘")
    
    def update_dashboard(self):
        """更新仪表盘数据"""
        try:
            # 获取系统内存使用率
            system_memory = self.metrics_collector.collect_on_demand("system_metrics.total_memory")
            if system_memory is not None:
                self.gauges['system'].set(system_memory)
            
            # 获取进程内存使用
            process_memory = self.metrics_collector.collect_on_demand("system_metrics.process_rss")
            if process_memory is not None:
                self.gauges['process'].set(process_memory)
            
            # 更新内存趋势图
            if system_memory is not None:
                self.trend.add_point(system_memory)
            
            # 更新组件内存排行
            self.update_components_table()
            
            # 更新预警列表
            self.update_alerts()
            
            # 检查内存使用预警（集成预警系统）
            if system_memory is not None:
                check_memory_usage(system_memory, {
                    "source": "memory_dashboard",
                    "details": "内存仪表盘检测",
                    "process_memory_mb": process_memory
                })
        
        except Exception as e:
            logger.error(f"更新仪表盘出错: {e}")
    
    def update_components_table(self):
        """更新组件内存表格"""
        try:
            # 获取组件内存使用
            # 这里示例数据，实际应从监控系统获取
            components = {
                "Qwen模型": 2500,
                "缓存系统": 350,
                "UI界面": 150,
                "视频处理": 200,
                "字幕解析": 50,
                "监控系统": 30,
                "其他": 70
            }
            
            # 如果Mistral模型已加载，添加到列表（未来支持）
            # if mistral_loaded:
            #    components["Mistral模型"] = 2700
            
            self.components_table.update_components(components)
        
        except Exception as e:
            logger.error(f"更新组件表格出错: {e}")
    
    def update_alerts(self):
        """更新预警列表"""
        try:
            # 获取最近20条预警
            alerts = self.alert_manager.get_history(limit=20)
            self.alert_widget.update_alerts(alerts)
        
        except Exception as e:
            logger.error(f"更新预警列表出错: {e}")
    
    def toggle_update(self):
        """切换更新状态"""
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("继续")
        else:
            self.timer.start(1000)
            self.pause_button.setText("暂停")


def run_dashboard():
    """运行内存仪表盘"""
    if not HAS_QT:
        logger.error("缺少PyQt6或pyqtgraph，无法启动仪表盘")
        return
    
    app = QApplication([])
    dashboard = MemoryDashboard()
    dashboard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行仪表盘
    run_dashboard() 