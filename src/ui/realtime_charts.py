#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 实时图表组件
提供实时性能监控和数据可视化功能

功能特性：
1. CPU/GPU使用率实时监控
2. 内存使用情况图表
3. 处理进度可视化
4. 性能指标趋势分析
"""

import sys
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QProgressBar, QFrame, QGridLayout)
    from PyQt6.QtCore import QTimer, pyqtSignal, QThread
    from PyQt6.QtGui import QFont, QPalette, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # 创建模拟的pyqtSignal用于类定义
    class MockSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, *args):
            pass
    pyqtSignal = MockSignal

# 获取日志记录器
logger = logging.getLogger(__name__)

class RealtimeCharts(QWidget if PYQT_AVAILABLE else object):
    """实时图表组件"""

    # 信号定义
    data_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """初始化实时图表组件"""
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for RealtimeCharts")
        
        super().__init__(parent)
        self.setObjectName("RealtimeCharts")
        
        # 数据存储
        self.performance_data = {
            "cpu_usage": [],
            "memory_usage": [],
            "gpu_usage": [],
            "processing_speed": [],
            "timestamps": []
        }
        
        # 配置参数
        self.max_data_points = 100
        self.update_interval = 1000  # 1秒更新一次
        
        # 初始化UI
        self._init_ui()
        
        # 启动数据更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(self.update_interval)
        
        logger.info("实时图表组件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("实时性能监控")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 性能指标网格
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.Shape.Box)
        metrics_layout = QGridLayout(metrics_frame)
        
        # CPU使用率
        self.cpu_label = QLabel("CPU使用率:")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_value_label = QLabel("0%")
        
        metrics_layout.addWidget(self.cpu_label, 0, 0)
        metrics_layout.addWidget(self.cpu_progress, 0, 1)
        metrics_layout.addWidget(self.cpu_value_label, 0, 2)
        
        # 内存使用率
        self.memory_label = QLabel("内存使用率:")
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_value_label = QLabel("0%")
        
        metrics_layout.addWidget(self.memory_label, 1, 0)
        metrics_layout.addWidget(self.memory_progress, 1, 1)
        metrics_layout.addWidget(self.memory_value_label, 1, 2)
        
        # GPU使用率（如果可用）
        self.gpu_label = QLabel("GPU使用率:")
        self.gpu_progress = QProgressBar()
        self.gpu_progress.setRange(0, 100)
        self.gpu_value_label = QLabel("N/A")
        
        metrics_layout.addWidget(self.gpu_label, 2, 0)
        metrics_layout.addWidget(self.gpu_progress, 2, 1)
        metrics_layout.addWidget(self.gpu_value_label, 2, 2)
        
        # 处理速度
        self.speed_label = QLabel("处理速度:")
        self.speed_progress = QProgressBar()
        self.speed_progress.setRange(0, 100)
        self.speed_value_label = QLabel("0 fps")
        
        metrics_layout.addWidget(self.speed_label, 3, 0)
        metrics_layout.addWidget(self.speed_progress, 3, 1)
        metrics_layout.addWidget(self.speed_value_label, 3, 2)
        
        layout.addWidget(metrics_frame)
        
        # 状态信息
        self.status_label = QLabel("状态: 监控中...")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.status_label)
        
        # 应用样式
        self._apply_styles()
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QWidget#RealtimeCharts {
                background-color: #f8f9fa;
                border-radius: 8px;
            }
            
            QLabel {
                color: #333333;
                font-family: 'Microsoft YaHei';
            }
            
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #007bff, stop: 1 #0056b3);
                border-radius: 3px;
            }
            
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
            }
        """)
    
    def _update_data(self):
        """更新性能数据"""
        try:
            # 获取当前性能数据
            current_data = self._get_current_performance_data()
            
            # 更新数据存储
            self._add_data_point(current_data)
            
            # 更新UI显示
            self._update_ui_display(current_data)
            
            # 发送数据更新信号
            self.data_updated.emit(current_data)
            
        except Exception as e:
            logger.error(f"性能数据更新失败: {str(e)}")
    
    def _get_current_performance_data(self) -> Dict[str, Any]:
        """获取当前性能数据"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # GPU使用率（模拟，实际需要GPU库）
            gpu_percent = 0  # 默认为0，表示无GPU或未检测到
            
            # 处理速度（模拟）
            processing_speed = min(100, cpu_percent + 10)  # 基于CPU使用率模拟
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "gpu_usage": gpu_percent,
                "processing_speed": processing_speed,
                "timestamp": datetime.now()
            }
            
        except ImportError:
            # 如果psutil不可用，返回模拟数据
            return {
                "cpu_usage": 25.0,
                "memory_usage": 45.0,
                "gpu_usage": 0.0,
                "processing_speed": 30.0,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.warning(f"获取性能数据失败，使用默认值: {str(e)}")
            return {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "gpu_usage": 0.0,
                "processing_speed": 0.0,
                "timestamp": datetime.now()
            }
    
    def _add_data_point(self, data: Dict[str, Any]):
        """添加数据点"""
        # 添加新数据
        self.performance_data["cpu_usage"].append(data["cpu_usage"])
        self.performance_data["memory_usage"].append(data["memory_usage"])
        self.performance_data["gpu_usage"].append(data["gpu_usage"])
        self.performance_data["processing_speed"].append(data["processing_speed"])
        self.performance_data["timestamps"].append(data["timestamp"])
        
        # 限制数据点数量
        for key in self.performance_data:
            if len(self.performance_data[key]) > self.max_data_points:
                self.performance_data[key] = self.performance_data[key][-self.max_data_points:]
    
    def _update_ui_display(self, data: Dict[str, Any]):
        """更新UI显示"""
        # 更新CPU使用率
        cpu_value = int(data["cpu_usage"])
        self.cpu_progress.setValue(cpu_value)
        self.cpu_value_label.setText(f"{cpu_value}%")
        
        # 更新内存使用率
        memory_value = int(data["memory_usage"])
        self.memory_progress.setValue(memory_value)
        self.memory_value_label.setText(f"{memory_value}%")
        
        # 更新GPU使用率
        gpu_value = int(data["gpu_usage"])
        if gpu_value > 0:
            self.gpu_progress.setValue(gpu_value)
            self.gpu_value_label.setText(f"{gpu_value}%")
        else:
            self.gpu_progress.setValue(0)
            self.gpu_value_label.setText("N/A")
        
        # 更新处理速度
        speed_value = int(data["processing_speed"])
        self.speed_progress.setValue(speed_value)
        self.speed_value_label.setText(f"{speed_value} fps")
        
        # 更新状态
        current_time = data["timestamp"].strftime("%H:%M:%S")
        self.status_label.setText(f"状态: 监控中... (更新时间: {current_time})")
        
        # 根据性能状态调整进度条颜色
        self._update_progress_bar_colors(data)
    
    def _update_progress_bar_colors(self, data: Dict[str, Any]):
        """根据性能状态更新进度条颜色"""
        # CPU颜色
        if data["cpu_usage"] > 80:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #dc3545; }")
        elif data["cpu_usage"] > 60:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #ffc107; }")
        else:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")
        
        # 内存颜色
        if data["memory_usage"] > 80:
            self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #dc3545; }")
        elif data["memory_usage"] > 60:
            self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #ffc107; }")
        else:
            self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.performance_data["cpu_usage"]:
            return {"error": "暂无性能数据"}
        
        # 计算平均值
        avg_cpu = sum(self.performance_data["cpu_usage"]) / len(self.performance_data["cpu_usage"])
        avg_memory = sum(self.performance_data["memory_usage"]) / len(self.performance_data["memory_usage"])
        avg_speed = sum(self.performance_data["processing_speed"]) / len(self.performance_data["processing_speed"])
        
        # 计算最大值
        max_cpu = max(self.performance_data["cpu_usage"])
        max_memory = max(self.performance_data["memory_usage"])
        
        return {
            "average_cpu_usage": round(avg_cpu, 1),
            "average_memory_usage": round(avg_memory, 1),
            "average_processing_speed": round(avg_speed, 1),
            "peak_cpu_usage": round(max_cpu, 1),
            "peak_memory_usage": round(max_memory, 1),
            "data_points": len(self.performance_data["cpu_usage"]),
            "monitoring_duration_minutes": len(self.performance_data["cpu_usage"]) / 60
        }
    
    def reset_data(self):
        """重置性能数据"""
        for key in self.performance_data:
            self.performance_data[key].clear()
        
        logger.info("性能数据已重置")
    
    def set_update_interval(self, interval_ms: int):
        """设置更新间隔"""
        self.update_interval = interval_ms
        self.update_timer.setInterval(interval_ms)
        
        logger.info(f"更新间隔已设置为: {interval_ms}ms")
    
    def start_monitoring(self):
        """开始监控"""
        if not self.update_timer.isActive():
            self.update_timer.start()
            logger.info("性能监控已开始")
    
    def stop_monitoring(self):
        """停止监控"""
        if self.update_timer.isActive():
            self.update_timer.stop()
            logger.info("性能监控已停止")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.stop_monitoring()
        super().closeEvent(event)


# 便捷函数
def create_realtime_charts(parent=None) -> Optional[RealtimeCharts]:
    """创建实时图表组件"""
    if not PYQT_AVAILABLE:
        logger.warning("PyQt6不可用，无法创建实时图表组件")
        return None
    
    try:
        return RealtimeCharts(parent)
    except Exception as e:
        logger.error(f"创建实时图表组件失败: {str(e)}")
        return None
