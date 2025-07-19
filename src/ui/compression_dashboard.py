#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩性能监控仪表盘

可视化显示压缩系统性能指标，包括压缩率、吞吐量和资源使用情况。
提供实时监控和历史趋势分析功能。
"""

import os
import sys
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Union
from collections import deque
import datetime

from PyQt6.QtWidgets import (
    QWidget, QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QLabel, QTabWidget, QGroupBox, QSplitter, QPushButton, 
    QComboBox, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QProgressBar, QFrame, QSizePolicy, QStackedWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QAction, QColor, QFont, QPainter, QPen, QBrush, QIcon

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

# 导入压缩相关模块
from src.compression.adaptive_compression import (
    get_smart_compressor, get_compression_stats,
    MemoryPressureLevel, ResourcePriority
)
from src.compression.hardware_accel import get_best_hardware, benchmark_hardware
from src.compression.core import benchmark as benchmark_algorithms
from src.compression.compressors import get_available_compressors

# 导入UI组件
from src.ui.components.memory_visualization import MemoryWidget

# 配置日志
logger = logging.getLogger("compression_dashboard")


class GaugeChart(QWidget):
    """仪表盘组件，显示单个度量值"""
    
    def __init__(self, title="压缩率", unit="%", min_value=0, max_value=100, parent=None):
        """
        初始化仪表盘组件
        
        Args:
            title: 标题
            unit: 单位
            min_value: 最小值
            max_value: 最大值
            parent: 父窗口
        """
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = min_value
        
        self.color_low = QColor(76, 175, 80)     # 绿色
        self.color_med = QColor(255, 193, 7)     # 黄色
        self.color_high = QColor(255, 87, 34)    # 橙色
        
        # 设置最小尺寸
        self.setMinimumSize(150, 150)
        
        # 设置外观
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
        """)
    
    def set(self, value):
        """设置当前值"""
        self.current_value = max(self.min_value, min(self.max_value, value))
        self.update()  # 触发重绘
    
    def paintEvent(self, event):
        """绘制仪表盘"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor("#f5f5f5"))
        
        # 绘制标题
        painter.setPen(QColor("#333333"))
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(0, 10, width, 20, Qt.AlignmentFlag.AlignCenter, self.title)
        
        # 计算仪表盘位置
        center_x = width // 2
        center_y = height // 2 + 10
        radius = min(width, height) // 2 - 20
        
        # 绘制外圈
        painter.setPen(QPen(QColor("#cccccc"), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # 绘制刻度
        painter.setPen(QPen(QColor("#999999"), 1))
        for i in range(11):  # 绘制0-10的刻度
            angle = 225 + i * 27  # 从225度（左下）到45度（右下）
            rad_angle = angle * 3.14159 / 180
            
            inner_x = center_x + int((radius - 10) * -1 * 0.8 * 1.414 / 2 * 1 * (angle == 225) + (radius - 10) * 0.8 * 1.414 / 2 * 1 * (angle == 45) + (radius - 10) * cos(rad_angle) * (angle != 225 and angle != 45))
            inner_y = center_y + int((radius - 10) * 0.8 * 1.414 / 2 * 1 * (angle == 225) + (radius - 10) * 0.8 * 1.414 / 2 * 1 * (angle == 45) + (radius - 10) * sin(rad_angle) * (angle != 225 and angle != 45))
            
            outer_x = center_x + int((radius) * -1 * 0.8 * 1.414 / 2 * 1 * (angle == 225) + (radius) * 0.8 * 1.414 / 2 * 1 * (angle == 45) + (radius) * cos(rad_angle) * (angle != 225 and angle != 45))
            outer_y = center_y + int((radius) * 0.8 * 1.414 / 2 * 1 * (angle == 225) + (radius) * 0.8 * 1.414 / 2 * 1 * (angle == 45) + (radius) * sin(rad_angle) * (angle != 225 and angle != 45))
            
            painter.drawLine(inner_x, inner_y, outer_x, outer_y)
            
            # 绘制刻度值
            value = self.min_value + (self.max_value - self.min_value) * i / 10
            text_x = center_x + int((radius + 15) * cos(rad_angle))
            text_y = center_y + int((radius + 15) * sin(rad_angle))
            
            value_text = f"{value:.0f}" if value == int(value) else f"{value:.1f}"
            painter.drawText(text_x - 15, text_y - 5, 30, 10, 
                          Qt.AlignmentFlag.AlignCenter, value_text)
        
        # 绘制当前值文本
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        painter.setFont(value_font)
        
        # 根据值选择颜色
        normalized_value = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        if normalized_value < 0.3:
            color = self.color_low
        elif normalized_value < 0.7:
            color = self.color_med
        else:
            color = self.color_high
            
        painter.setPen(color)
        
        value_text = f"{self.current_value:.1f}{self.unit}"
        painter.drawText(center_x - 60, center_y - 10, 120, 40, 
                      Qt.AlignmentFlag.AlignCenter, value_text)
        
        # 绘制指针
        angle = 225 + (self.current_value - self.min_value) / (self.max_value - self.min_value) * 270
        rad_angle = angle * 3.14159 / 180
        
        pointer_length = radius - 20
        pointer_end_x = center_x + int(pointer_length * cos(rad_angle))
        pointer_end_y = center_y + int(pointer_length * sin(rad_angle))
        
        painter.setPen(QPen(color, 3))
        painter.drawLine(center_x, center_y, pointer_end_x, pointer_end_y)
        
        # 绘制中心圆
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)


class LineChart(QWidget):
    """折线图组件，显示时间序列数据"""
    
    def __init__(self, title="吞吐量", unit="MB/s", max_points=100, parent=None):
        """
        初始化折线图组件
        
        Args:
            title: 标题
            unit: 单位
            max_points: 最大点数
            parent: 父窗口
        """
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.max_points = max_points
        
        self.data = deque(maxlen=max_points)
        self.time_labels = deque(maxlen=max_points)
        
        # 设置最小尺寸
        self.setMinimumSize(300, 200)
        
        # 设置外观
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
        """)
    
    def add_point(self, value, timestamp=None):
        """添加数据点"""
        if timestamp is None:
            timestamp = time.time()
            
        self.data.append(value)
        t = datetime.datetime.fromtimestamp(timestamp)
        self.time_labels.append(t.strftime("%H:%M:%S"))
        
        self.update()  # 触发重绘
    
    def paintEvent(self, event):
        """绘制折线图"""
        if not self.data:  # 没有数据则不绘制
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor("#f5f5f5"))
        
        # 绘制标题
        painter.setPen(QColor("#333333"))
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(0, 10, width, 20, Qt.AlignmentFlag.AlignCenter, self.title)
        
        # 计算图表区域
        chart_x = 50
        chart_y = 40
        chart_width = width - 70
        chart_height = height - 60
        
        # 绘制边框
        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.drawRect(chart_x, chart_y, chart_width, chart_height)
        
        # 计算Y轴范围
        if self.data:
            max_value = max(self.data) * 1.1  # 最大值增加10%留出上边距
            min_value = min(min(self.data) * 0.9, 0)  # 最小值，确保至少包含0
        else:
            max_value = 100
            min_value = 0
            
        # 绘制Y轴刻度
        painter.setPen(QColor("#999999"))
        y_step = max(1, int(max_value / 5))  # 至少1个单位
        
        for i in range(0, int(max_value) + y_step, y_step):
            if i > max_value:  # 防止超出范围
                break
                
            y = chart_y + chart_height - (i - min_value) / (max_value - min_value) * chart_height
            painter.drawLine(chart_x - 5, y, chart_x, y)
            painter.drawText(5, y - 10, chart_x - 10, 20, 
                          Qt.AlignmentFlag.AlignRight, f"{i}{self.unit}")
        
        # 绘制X轴
        if len(self.data) > 1:
            # 绘制X轴刻度
            x_steps = min(len(self.data), 5)  # 最多显示5个时间刻度
            x_step = max(1, len(self.data) // x_steps)
            
            for i in range(0, len(self.data), x_step):
                x = chart_x + i * chart_width / (len(self.data) - 1)
                painter.drawLine(x, chart_y + chart_height, x, chart_y + chart_height + 5)
                painter.drawText(x - 30, chart_y + chart_height + 5, 60, 20, 
                              Qt.AlignmentFlag.AlignCenter, self.time_labels[i])
            
            # 绘制折线
            painter.setPen(QPen(QColor(33, 150, 243), 2))  # 蓝色线
            
            for i in range(len(self.data) - 1):
                x1 = chart_x + i * chart_width / (len(self.data) - 1)
                y1 = chart_y + chart_height - (self.data[i] - min_value) / (max_value - min_value) * chart_height
                
                x2 = chart_x + (i + 1) * chart_width / (len(self.data) - 1)
                y2 = chart_y + chart_height - (self.data[i + 1] - min_value) / (max_value - min_value) * chart_height
                
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # 绘制数据点
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(33, 150, 243)))
            
            for i in range(len(self.data)):
                x = chart_x + i * chart_width / (len(self.data) - 1)
                y = chart_y + chart_height - (self.data[i] - min_value) / (max_value - min_value) * chart_height
                painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)


# 必要的数学函数
def cos(x):
    import math
    return math.cos(x)

def sin(x):
    import math
    return math.sin(x)


class AlgorithmComparisonChart(QWidget):
    """算法比较图表，显示不同算法的性能对比"""
    
    def __init__(self, parent=None):
        """初始化算法比较图表"""
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("各算法资源消耗对比")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.layout.addWidget(title_label)
        
        # 算法数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["算法", "压缩率", "压缩速度", "解压速度", "内存使用"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.layout.addWidget(self.table)
        
        # 设置最小尺寸
        self.setMinimumSize(400, 300)
    
    def update_data(self, algorithms_data):
        """更新算法数据
        
        Args:
            algorithms_data: 算法数据字典
                {
                    "zstd": {
                        "ratio": 0.4,
                        "compression_speed": 120,
                        "decompression_speed": 300,
                        "memory_usage": 20
                    },
                    ...
                }
        """
        self.table.setRowCount(len(algorithms_data))
        
        for i, (algo, data) in enumerate(algorithms_data.items()):
            # 算法名称
            self.table.setItem(i, 0, QTableWidgetItem(algo))
            
            # 压缩率
            ratio_item = QTableWidgetItem(f"{data['ratio']:.3f}")
            self.table.setItem(i, 1, ratio_item)
            
            # 压缩速度
            comp_speed_item = QTableWidgetItem(f"{data['compression_speed']:.1f} MB/s")
            self.table.setItem(i, 2, comp_speed_item)
            
            # 解压速度
            decomp_speed_item = QTableWidgetItem(f"{data['decompression_speed']:.1f} MB/s")
            self.table.setItem(i, 3, decomp_speed_item)
            
            # 内存使用
            memory_item = QTableWidgetItem(f"{data['memory_usage']:.1f} MB")
            self.table.setItem(i, 4, memory_item)
        
        self.table.resizeColumnsToContents()


class CompressionDashboardWindow(QMainWindow):
    """压缩监控仪表盘窗口"""
    
    def __init__(self):
        """初始化仪表盘窗口"""
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("压缩性能监控仪表盘")
        self.resize(900, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项栏
        options_layout = QHBoxLayout()
        
        # 更新频率选择
        update_label = QLabel("更新频率:")
        options_layout.addWidget(update_label)
        
        self.update_combo = QComboBox()
        self.update_combo.addItems(["1秒", "2秒", "5秒", "10秒"])
        self.update_combo.setCurrentIndex(1)  # 默认2秒
        self.update_combo.currentIndexChanged.connect(self._update_refresh_rate)
        options_layout.addWidget(self.update_combo)
        
        options_layout.addStretch()
        
        # 运行基准测试按钮
        self.benchmark_button = QPushButton("运行基准测试")
        self.benchmark_button.clicked.connect(self._run_benchmark)
        options_layout.addWidget(self.benchmark_button)
        
        main_layout.addLayout(options_layout)
        
        # 创建标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 创建实时监控页
        realtime_tab = QWidget()
        self.tabs.addTab(realtime_tab, "实时监控")
        
        # 实时监控布局
        realtime_layout = QVBoxLayout(realtime_tab)
        
        # 上半部分：仪表盘和图表
        top_layout = QHBoxLayout()
        
        # 压缩率仪表盘
        self.ratio_gauge = GaugeChart("压缩率", "%", 0, 100)
        top_layout.addWidget(self.ratio_gauge)
        
        # 吞吐量图表
        self.throughput_chart = LineChart("吞吐量", "MB/s")
        top_layout.addWidget(self.throughput_chart)
        
        realtime_layout.addLayout(top_layout)
        
        # 下半部分：算法对比和内存监控
        bottom_layout = QHBoxLayout()
        
        # 算法对比
        self.algo_chart = AlgorithmComparisonChart()
        bottom_layout.addWidget(self.algo_chart)
        
        # 内存监控
        self.memory_widget = MemoryWidget()
        bottom_layout.addWidget(self.memory_widget)
        
        realtime_layout.addLayout(bottom_layout)
        
        # 创建历史趋势页
        history_tab = QWidget()
        self.tabs.addTab(history_tab, "历史趋势")
        
        # 历史趋势布局
        history_layout = QVBoxLayout(history_tab)
        
        # 历史压缩率图表
        self.history_ratio_chart = LineChart("历史压缩率", "%", 1000)
        history_layout.addWidget(self.history_ratio_chart)
        
        # 历史吞吐量图表
        self.history_throughput_chart = LineChart("历史吞吐量", "MB/s", 1000)
        history_layout.addWidget(self.history_throughput_chart)
        
        # 创建详细信息页
        details_tab = QWidget()
        self.tabs.addTab(details_tab, "详细信息")
        
        # 详细信息布局
        details_layout = QVBoxLayout(details_tab)
        
        # 压缩统计信息表格
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["指标", "值"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        details_layout.addWidget(self.stats_table)
        
        # 初始化数据
        self._initialize_data()
        
        # 设置更新计时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(2000)  # 默认2秒更新一次
        
        # 启动内存监控
        self.memory_widget.start_monitoring()
    
    def _initialize_data(self):
        """初始化数据"""
        # 初始化算法对比数据
        # 此处使用示例数据，实际应从压缩系统获取
        algorithms_data = {
            "zstd": {
                "ratio": 0.4,
                "compression_speed": 120,
                "decompression_speed": 300,
                "memory_usage": 20
            },
            "lz4": {
                "ratio": 0.6,
                "compression_speed": 350,
                "decompression_speed": 700,
                "memory_usage": 15
            },
            "bzip2": {
                "ratio": 0.35,
                "compression_speed": 30,
                "decompression_speed": 60,
                "memory_usage": 25
            }
        }
        self.algo_chart.update_data(algorithms_data)
        
        # 初始化统计表格
        self._update_stats_table()
    
    def _update_refresh_rate(self):
        """更新刷新频率"""
        refresh_rates = [1000, 2000, 5000, 10000]  # 毫秒
        rate = refresh_rates[self.update_combo.currentIndex()]
        
        self.update_timer.stop()
        self.update_timer.start(rate)
        
        self.memory_widget.set_update_interval(rate)
    
    def _update_data(self):
        """更新显示数据"""
        try:
            # 获取压缩统计信息
            stats = get_compression_stats()
            
            if stats:
                # 更新压缩率
                if "average_ratio" in stats:
                    ratio = (1 - stats["average_ratio"]) * 100  # 转换为节省的百分比
                    self.ratio_gauge.set(ratio)
                    self.history_ratio_chart.add_point(ratio)
                
                # 更新吞吐量
                if "bytes_processed" in stats and "time_spent" in stats and stats["time_spent"] > 0:
                    throughput = stats["bytes_processed"] / (1024 * 1024) / stats["time_spent"]
                    self.throughput_chart.add_point(throughput)
                    self.history_throughput_chart.add_point(throughput)
                
                # 更新详细统计信息
                self._update_stats_table(stats)
        
        except Exception as e:
            logger.error(f"更新仪表盘数据出错: {e}")
    
    def _update_stats_table(self, stats=None):
        """更新统计信息表格"""
        if stats is None:
            # 初始化表格
            self.stats_table.setRowCount(10)
            self.stats_table.setItem(0, 0, QTableWidgetItem("压缩操作次数"))
            self.stats_table.setItem(1, 0, QTableWidgetItem("解压操作次数"))
            self.stats_table.setItem(2, 0, QTableWidgetItem("处理的总字节数"))
            self.stats_table.setItem(3, 0, QTableWidgetItem("输出的总字节数"))
            self.stats_table.setItem(4, 0, QTableWidgetItem("平均压缩率"))
            self.stats_table.setItem(5, 0, QTableWidgetItem("总耗时(秒)"))
            self.stats_table.setItem(6, 0, QTableWidgetItem("平均吞吐量"))
            self.stats_table.setItem(7, 0, QTableWidgetItem("算法切换次数"))
            self.stats_table.setItem(8, 0, QTableWidgetItem("当前内存压力级别"))
            self.stats_table.setItem(9, 0, QTableWidgetItem("压缩级别调整次数"))
            
            for i in range(10):
                self.stats_table.setItem(i, 1, QTableWidgetItem("0"))
        else:
            # 更新表格数据
            self.stats_table.setItem(0, 1, QTableWidgetItem(str(stats.get("compression_count", 0))))
            self.stats_table.setItem(1, 1, QTableWidgetItem(str(stats.get("decompression_count", 0))))
            
            bytes_processed = stats.get("bytes_processed", 0)
            self.stats_table.setItem(2, 1, QTableWidgetItem(f"{bytes_processed / (1024*1024):.2f} MB"))
            
            bytes_output = stats.get("bytes_output", 0)
            self.stats_table.setItem(3, 1, QTableWidgetItem(f"{bytes_output / (1024*1024):.2f} MB"))
            
            avg_ratio = stats.get("average_ratio", 1.0)
            self.stats_table.setItem(4, 1, QTableWidgetItem(f"{avg_ratio:.3f} ({(1-avg_ratio)*100:.1f}%)"))
            
            time_spent = stats.get("time_spent", 0)
            self.stats_table.setItem(5, 1, QTableWidgetItem(f"{time_spent:.2f}"))
            
            if time_spent > 0:
                throughput = bytes_processed / (1024 * 1024) / time_spent
                self.stats_table.setItem(6, 1, QTableWidgetItem(f"{throughput:.2f} MB/s"))
            
            self.stats_table.setItem(7, 1, QTableWidgetItem(str(stats.get("algo_switches", 0))))
            
            # 获取当前内存压力级别
            compressor = get_smart_compressor()
            pressure_level = compressor.current_pressure_level.name
            self.stats_table.setItem(8, 1, QTableWidgetItem(pressure_level))
            
            self.stats_table.setItem(9, 1, QTableWidgetItem(str(stats.get("level_adjustments", 0))))
            
            self.stats_table.resizeColumnsToContents()
    
    def _run_benchmark(self):
        """运行基准测试"""
        # 禁用按钮防止重复点击
        self.benchmark_button.setEnabled(False)
        self.benchmark_button.setText("测试中...")
        
        # 创建并启动测试线程
        self.benchmark_thread = BenchmarkThread()
        self.benchmark_thread.finished.connect(self._benchmark_completed)
        self.benchmark_thread.results_ready.connect(self._update_benchmark_results)
        self.benchmark_thread.start()
    
    def _benchmark_completed(self):
        """基准测试完成处理"""
        self.benchmark_button.setEnabled(True)
        self.benchmark_button.setText("运行基准测试")
    
    def _update_benchmark_results(self, results):
        """更新基准测试结果
        
        Args:
            results: 测试结果字典
        """
        self.algo_chart.update_data(results)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止所有计时器和监控
        self.update_timer.stop()
        self.memory_widget.stop_monitoring()
        
        # 如果正在运行基准测试，等待它完成
        if hasattr(self, 'benchmark_thread') and self.benchmark_thread.isRunning():
            self.benchmark_thread.wait()
        
        event.accept()


class BenchmarkThread(QThread):
    """基准测试线程"""
    
    # 结果就绪信号
    results_ready = pyqtSignal(dict)
    
    def run(self):
        """运行基准测试"""
        try:
            # 设置较小的数据大小以便快速测试
            data_size = 50 * 1024 * 1024  # 50MB
            
            # 获取可用算法
            algorithms = get_available_compressors()
            
            # 创建测试数据
            test_data = b"Test data" * (data_size // 9)
            
            results = {}
            
            # 测试每个算法
            for algo in algorithms:
                # 跳过一些极慢的算法
                if algo in ["lzma", "xz"]:
                    continue
                    
                try:
                    # 运行单个算法基准测试
                    result = self._benchmark_algorithm(algo, test_data)
                    results[algo] = result
                except Exception as e:
                    logger.error(f"测试算法 {algo} 出错: {e}")
            
            # 发送结果
            self.results_ready.emit(results)
            
        except Exception as e:
            logger.error(f"基准测试出错: {e}")
    
    def _benchmark_algorithm(self, algo, test_data):
        """测试单个算法性能
        
        Args:
            algo: 算法名称
            test_data: 测试数据
        
        Returns:
            dict: 测试结果
        """
        # 导入压缩函数
        from src.compression.core import compress, decompress
        import time
        import psutil
        
        start_mem = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        
        # 测试压缩速度
        start_time = time.time()
        compressed, metadata = compress(test_data, algo=algo, level=3)
        compress_time = time.time() - start_time
        
        # 测试解压速度
        start_time = time.time()
        decompressed = decompress(compressed, metadata=metadata)
        decompress_time = time.time() - start_time
        
        end_mem = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        
        # 计算指标
        compression_ratio = len(compressed) / len(test_data)
        compression_speed = len(test_data) / (1024 * 1024) / compress_time  # MB/s
        decompression_speed = len(test_data) / (1024 * 1024) / decompress_time  # MB/s
        memory_usage = max(0.1, end_mem - start_mem)  # 至少0.1MB避免除零
        
        return {
            "ratio": compression_ratio,
            "compression_speed": compression_speed,
            "decompression_speed": decompression_speed,
            "memory_usage": memory_usage
        }


class CompressionDashboardLauncher:
    """压缩仪表盘启动器"""
    
    def __init__(self):
        """初始化启动器"""
        self.dashboard = None
    
    def create_toolbar_button(self, toolbar):
        """为工具栏创建按钮"""
        button = QPushButton("压缩监控")
        button.setToolTip("打开压缩性能监控仪表盘")
        button.clicked.connect(self.launch_dashboard)
        toolbar.addWidget(button)
        return button
    
    def create_menu_action(self, menu):
        """为菜单创建动作"""
        action = QAction("压缩性能监控", menu)
        action.setStatusTip("打开压缩性能监控仪表盘")
        action.triggered.connect(self.launch_dashboard)
        menu.addAction(action)
        return action
    
    def launch_dashboard(self):
        """启动仪表盘"""
        if self.dashboard is None or not self.dashboard.isVisible():
            self.dashboard = CompressionDashboardWindow()
            self.dashboard.show()
        else:
            self.dashboard.activateWindow()
            self.dashboard.raise_()


# 全局实例
_dashboard_launcher = None

def get_compression_dashboard_launcher():
    """获取压缩仪表盘启动器实例"""
    global _dashboard_launcher
    if _dashboard_launcher is None:
        _dashboard_launcher = CompressionDashboardLauncher()
    return _dashboard_launcher


def run_dashboard():
    """作为独立应用运行仪表盘"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = CompressionDashboardWindow()
    window.show()
    
    if app is not None:
        app.exec()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行仪表盘
    run_dashboard() 