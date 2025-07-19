#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 训练监控面板
实现实时Loss曲线显示和资源监控功能
"""

import sys
import os
import time
import json
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime

# 获取日志记录器
logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTextEdit, QProgressBar, QGroupBox,
                               QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
                               QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
    from PyQt6.QtGui import QFont, QPalette, QColor
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    # 创建模拟的pyqtSignal和QObject用于类定义
    class MockSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, *args):
            pass
    pyqtSignal = MockSignal
    QObject = object

class TrainingMonitorWorker(QObject):
    """训练监控工作线程"""

    # 信号定义
    loss_updated = pyqtSignal(float, float)  # train_loss, val_loss
    resource_updated = pyqtSignal(dict)      # resource_info
    training_status_changed = pyqtSignal(str)  # status
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.training_data = {
            "train_losses": [],
            "val_losses": [],
            "epochs": [],
            "learning_rates": [],
            "resource_usage": []
        }
    
    def start_monitoring(self):
        """开始监控"""
        self.is_running = True
        self.training_status_changed.emit("MONITORING")
        
        # 模拟训练数据更新
        timer = QTimer()
        timer.timeout.connect(self._update_training_data)
        timer.start(1000)  # 每秒更新一次
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        self.training_status_changed.emit("STOPPED")
    
    def _update_training_data(self):
        """更新训练数据"""
        if not self.is_running:
            return
            
        # 模拟Loss数据
        import random
        train_loss = random.uniform(0.1, 2.0)
        val_loss = random.uniform(0.1, 2.0)
        
        self.loss_updated.emit(train_loss, val_loss)
        
        # 模拟资源使用情况
        resource_info = {
            "cpu_usage": random.uniform(20, 80),
            "memory_usage": random.uniform(30, 90),
            "gpu_usage": random.uniform(0, 100),
            "gpu_memory": random.uniform(10, 95),
            "temperature": random.uniform(45, 75)
        }
        
        self.resource_updated.emit(resource_info)

class TrainingPanel(QWidget if QT_AVAILABLE else object):
    """训练监控面板主类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor_worker = None
        self.monitor_thread = None
        self.training_data = {
            "train_losses": [],
            "val_losses": [],
            "timestamps": []
        }

        # 日志显示组件
        self.log_display = None
        self.log_handler = None

        logger.info("训练监控面板初始化开始")
        
        # 多语言支持
        self.language = "zh_CN"  # 默认中文
        self.translations = {
            "zh_CN": {
                "title": "训练监控面板",
                "loss_curves": "Loss曲线",
                "resource_monitor": "资源监控",
                "training_status": "训练状态",
                "start_monitoring": "开始监控",
                "stop_monitoring": "停止监控",
                "train_loss": "训练Loss",
                "val_loss": "验证Loss",
                "cpu_usage": "CPU使用率",
                "memory_usage": "内存使用率",
                "gpu_usage": "GPU使用率",
                "gpu_memory": "GPU内存",
                "temperature": "温度"
            },
            "en_US": {
                "title": "Training Monitor Panel",
                "loss_curves": "Loss Curves",
                "resource_monitor": "Resource Monitor",
                "training_status": "Training Status",
                "start_monitoring": "Start Monitoring",
                "stop_monitoring": "Stop Monitoring",
                "train_loss": "Train Loss",
                "val_loss": "Validation Loss",
                "cpu_usage": "CPU Usage",
                "memory_usage": "Memory Usage",
                "gpu_usage": "GPU Usage",
                "gpu_memory": "GPU Memory",
                "temperature": "Temperature"
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
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：Loss曲线面板
        loss_panel = self.create_loss_panel()
        splitter.addWidget(loss_panel)
        
        # 右侧：资源监控面板
        resource_panel = self.create_resource_panel()
        splitter.addWidget(resource_panel)
        
        # 底部：控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        # 日志显示面板
        log_panel = self.create_log_panel()
        layout.addWidget(log_panel)

        # 设置分割器比例
        splitter.setSizes([400, 300])

        logger.info("训练监控面板UI初始化完成")
    
    def create_loss_panel(self) -> QGroupBox:
        """创建Loss曲线面板"""
        group = QGroupBox(self.tr("loss_curves"))
        layout = QVBoxLayout(group)
        
        # Loss显示区域
        self.loss_display = QTextEdit()
        self.loss_display.setMaximumHeight(200)
        self.loss_display.setReadOnly(True)
        layout.addWidget(self.loss_display)
        
        # Loss统计表格
        self.loss_table = QTableWidget(0, 3)
        self.loss_table.setHorizontalHeaderLabels([
            self.tr("train_loss"), 
            self.tr("val_loss"), 
            "Epoch"
        ])
        layout.addWidget(self.loss_table)
        
        return group
    
    def create_resource_panel(self) -> QGroupBox:
        """创建资源监控面板"""
        group = QGroupBox(self.tr("resource_monitor"))
        layout = QVBoxLayout(group)
        
        # 资源使用率显示
        self.resource_labels = {}
        resource_items = ["cpu_usage", "memory_usage", "gpu_usage", "gpu_memory", "temperature"]
        
        for item in resource_items:
            item_layout = QHBoxLayout()
            
            label = QLabel(f"{self.tr(item)}:")
            item_layout.addWidget(label)
            
            progress = QProgressBar()
            progress.setRange(0, 100)
            item_layout.addWidget(progress)
            
            value_label = QLabel("0%")
            item_layout.addWidget(value_label)
            
            layout.addLayout(item_layout)
            
            self.resource_labels[item] = {
                "progress": progress,
                "label": value_label
            }
        
        return group
    
    def create_control_panel(self) -> QGroupBox:
        """创建控制面板"""
        group = QGroupBox(self.tr("training_status"))
        layout = QHBoxLayout(group)
        
        # 状态标签
        self.status_label = QLabel("STOPPED")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 控制按钮
        self.start_btn = QPushButton(self.tr("start_monitoring"))
        self.start_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton(self.tr("stop_monitoring"))
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        return group
    
    def setup_monitoring(self):
        """设置监控"""
        if not QT_AVAILABLE:
            return
            
        self.monitor_worker = TrainingMonitorWorker()
        self.monitor_thread = QThread()
        
        # 连接信号
        self.monitor_worker.loss_updated.connect(self.update_loss_display)
        self.monitor_worker.resource_updated.connect(self.update_resource_display)
        self.monitor_worker.training_status_changed.connect(self.update_status)
        
        # 移动到线程
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.start()
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitor_worker:
            self.monitor_worker.start_monitoring()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
    
    def stop_monitoring(self):
        """停止监控"""
        if self.monitor_worker:
            self.monitor_worker.stop_monitoring()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def update_loss_display(self, train_loss: float, val_loss: float):
        """更新Loss显示"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 添加到数据列表
        self.training_data["train_losses"].append(train_loss)
        self.training_data["val_losses"].append(val_loss)
        self.training_data["timestamps"].append(timestamp)
        
        # 更新文本显示
        loss_text = f"[{timestamp}] Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}\n"
        self.loss_display.append(loss_text)
        
        # 更新表格
        row = self.loss_table.rowCount()
        self.loss_table.insertRow(row)
        self.loss_table.setItem(row, 0, QTableWidgetItem(f"{train_loss:.4f}"))
        self.loss_table.setItem(row, 1, QTableWidgetItem(f"{val_loss:.4f}"))
        self.loss_table.setItem(row, 2, QTableWidgetItem(str(row + 1)))
        
        # 滚动到底部
        self.loss_table.scrollToBottom()
    
    def update_resource_display(self, resource_info: Dict[str, float]):
        """更新资源显示"""
        for key, value in resource_info.items():
            if key in self.resource_labels:
                progress = self.resource_labels[key]["progress"]
                label = self.resource_labels[key]["label"]
                
                progress.setValue(int(value))
                
                if key == "temperature":
                    label.setText(f"{value:.1f}°C")
                else:
                    label.setText(f"{value:.1f}%")
                
                # 根据使用率设置颜色
                if value > 80:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: red; }")
                elif value > 60:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
                else:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: green; }")
    
    def update_status(self, status: str):
        """更新状态显示"""
        self.status_label.setText(status)
        
        if status == "MONITORING":
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def create_log_panel(self) -> QGroupBox:
        """创建日志显示面板"""
        group = QGroupBox("训练日志")
        layout = QVBoxLayout(group)

        # 日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(150)
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.log_display)

        # 日志控制按钮
        log_controls = QHBoxLayout()

        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_logs)
        log_controls.addWidget(clear_log_btn)

        auto_scroll_checkbox = QCheckBox("自动滚动")
        auto_scroll_checkbox.setChecked(True)
        auto_scroll_checkbox.stateChanged.connect(self.toggle_auto_scroll)
        log_controls.addWidget(auto_scroll_checkbox)

        log_controls.addStretch()
        layout.addLayout(log_controls)

        # 设置日志回调
        self.setup_log_callback()

        return group

    def setup_log_callback(self):
        """设置日志回调"""
        try:
            # 优先使用PyQt6信号机制
            from src.visionai_clipsmaster.ui.main_window import log_signal_emitter
            log_signal_emitter.log_message.connect(self.on_log_message)
            logger.info("训练面板日志信号已连接")
        except Exception as e:
            logger.warning(f"无法连接日志信号: {e}")

            # 备用：传统回调方式
            try:
                from src.visionai_clipsmaster.ui.main_window import log_handler
                if hasattr(log_handler, 'register_ui_callback'):
                    log_handler.register_ui_callback(self.on_log_message)
                    logger.info("训练面板日志回调已注册（备用方式）")
            except Exception as e2:
                logger.warning(f"无法注册日志回调: {e2}")

    def on_log_message(self, message: str, level: str):
        """处理日志消息"""
        if not self.log_display:
            return

        # 根据日志级别设置颜色
        color_map = {
            'DEBUG': '#888888',
            'INFO': '#ffffff',
            'WARNING': '#ffaa00',
            'ERROR': '#ff4444',
            'CRITICAL': '#ff0000'
        }

        color = color_map.get(level.upper(), '#ffffff')
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 格式化消息
        formatted_message = f'<span style="color: {color}">[{timestamp}] {message}</span>'

        # 添加到显示区域
        self.log_display.append(formatted_message)

        # 自动滚动到底部
        if hasattr(self, 'auto_scroll') and self.auto_scroll:
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self):
        """清空日志"""
        if self.log_display:
            self.log_display.clear()
            logger.info("训练面板日志已清空")

    def toggle_auto_scroll(self, state):
        """切换自动滚动"""
        self.auto_scroll = state == 2  # Qt.CheckState.Checked

    def tr(self, key: str) -> str:
        """翻译函数"""
        return self.translations.get(self.language, {}).get(key, key)
    
    def set_language(self, language: str):
        """设置语言"""
        if language in self.translations:
            self.language = language
            # 重新初始化UI以应用新语言
            # 这里可以添加动态更新UI文本的逻辑
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.monitor_worker:
            self.monitor_worker.stop_monitoring()
        if self.monitor_thread:
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        event.accept()
