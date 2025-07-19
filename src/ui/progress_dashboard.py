#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 进度看板
实现任务状态更新和进度图表功能
"""

import sys
import os
import time
import json
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# 获取日志记录器
logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTextEdit, QProgressBar, QGroupBox,
                               QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
                               QListWidget, QListWidgetItem, QComboBox, QFrame)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
    from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    # 创建模拟的pyqtSignal用于类定义
    class MockSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, *args):
            pass
    pyqtSignal = MockSignal

class TaskStatus:
    """任务状态枚举"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ProgressDashboard(QWidget if QT_AVAILABLE else object):
    """进度看板主类"""

    # 信号定义
    task_added = pyqtSignal(dict)
    task_updated = pyqtSignal(str, dict)  # task_id, update_data
    task_completed = pyqtSignal(str)      # task_id
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # 任务数据
        self.tasks = {}
        self.task_history = []

        # 日志显示组件
        self.log_display = None

        logger.info("进度看板初始化开始")
        
        # 多语言支持
        self.language = "zh_CN"
        self.translations = {
            "zh_CN": {
                "title": "进度看板",
                "current_tasks": "当前任务",
                "task_history": "任务历史",
                "task_statistics": "任务统计",
                "task_name": "任务名称",
                "status": "状态",
                "progress": "进度",
                "start_time": "开始时间",
                "duration": "持续时间",
                "pending": "等待中",
                "running": "运行中",
                "completed": "已完成",
                "failed": "失败",
                "cancelled": "已取消",
                "total_tasks": "总任务数",
                "completed_tasks": "已完成",
                "failed_tasks": "失败任务",
                "success_rate": "成功率",
                "add_task": "添加任务",
                "clear_history": "清空历史"
            },
            "en_US": {
                "title": "Progress Dashboard",
                "current_tasks": "Current Tasks",
                "task_history": "Task History",
                "task_statistics": "Task Statistics",
                "task_name": "Task Name",
                "status": "Status",
                "progress": "Progress",
                "start_time": "Start Time",
                "duration": "Duration",
                "pending": "Pending",
                "running": "Running",
                "completed": "Completed",
                "failed": "Failed",
                "cancelled": "Cancelled",
                "total_tasks": "Total Tasks",
                "completed_tasks": "Completed",
                "failed_tasks": "Failed Tasks",
                "success_rate": "Success Rate",
                "add_task": "Add Task",
                "clear_history": "Clear History"
            }
        }
        
        self.init_ui()
        self.setup_demo_data()
    
    def init_ui(self):
        """初始化用户界面"""
        if not QT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(self.tr("title"))
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 创建标签页
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 当前任务标签页
        current_tasks_tab = self.create_current_tasks_tab()
        tab_widget.addTab(current_tasks_tab, self.tr("current_tasks"))
        
        # 任务历史标签页
        history_tab = self.create_history_tab()
        tab_widget.addTab(history_tab, self.tr("task_history"))
        
        # 统计信息标签页
        statistics_tab = self.create_statistics_tab()
        tab_widget.addTab(statistics_tab, self.tr("task_statistics"))

        # 日志显示标签页
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "实时日志")

        # 底部控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        logger.info("进度看板UI初始化完成")
    
    def create_current_tasks_tab(self) -> QWidget:
        """创建当前任务标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 当前任务表格
        self.current_tasks_table = QTableWidget(0, 5)
        self.current_tasks_table.setHorizontalHeaderLabels([
            self.tr("task_name"),
            self.tr("status"), 
            self.tr("progress"),
            self.tr("start_time"),
            self.tr("duration")
        ])
        
        # 设置列宽
        self.current_tasks_table.setColumnWidth(0, 200)
        self.current_tasks_table.setColumnWidth(1, 100)
        self.current_tasks_table.setColumnWidth(2, 150)
        self.current_tasks_table.setColumnWidth(3, 150)
        self.current_tasks_table.setColumnWidth(4, 100)
        
        layout.addWidget(self.current_tasks_table)
        
        return widget
    
    def create_history_tab(self) -> QWidget:
        """创建任务历史标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 历史任务列表
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)
        
        return widget
    
    def create_statistics_tab(self) -> QWidget:
        """创建统计信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计信息组
        stats_group = QGroupBox(self.tr("task_statistics"))
        stats_layout = QVBoxLayout(stats_group)
        
        # 统计标签
        self.stats_labels = {}
        stats_items = [
            ("total_tasks", "0"),
            ("completed_tasks", "0"),
            ("failed_tasks", "0"),
            ("success_rate", "0%")
        ]
        
        for key, default_value in stats_items:
            item_layout = QHBoxLayout()
            
            label = QLabel(f"{self.tr(key)}:")
            label.setMinimumWidth(120)
            item_layout.addWidget(label)
            
            value_label = QLabel(default_value)
            value_label.setStyleSheet("font-weight: bold; color: blue;")
            item_layout.addWidget(value_label)
            
            item_layout.addStretch()
            stats_layout.addLayout(item_layout)
            
            self.stats_labels[key] = value_label
        
        layout.addWidget(stats_group)
        
        # 进度图表区域（占位符）
        chart_group = QGroupBox("进度图表")
        chart_layout = QVBoxLayout(chart_group)
        
        chart_placeholder = QLabel("图表区域 (可集成matplotlib或其他图表库)")
        chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_placeholder.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")
        chart_layout.addWidget(chart_placeholder)
        
        layout.addWidget(chart_group)
        
        return widget
    
    def create_control_panel(self) -> QFrame:
        """创建控制面板"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)
        
        # 添加任务按钮
        add_task_btn = QPushButton(self.tr("add_task"))
        add_task_btn.clicked.connect(self.add_demo_task)
        layout.addWidget(add_task_btn)
        
        # 清空历史按钮
        clear_history_btn = QPushButton(self.tr("clear_history"))
        clear_history_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_history_btn)
        
        layout.addStretch()
        
        # 状态指示器
        status_label = QLabel("就绪")
        status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(status_label)
        
        return frame
    
    def add_task(self, task_name: str, task_type: str = "default") -> str:
        """添加新任务"""
        task_id = f"task_{int(time.time() * 1000)}"
        
        task_data = {
            "id": task_id,
            "name": task_name,
            "type": task_type,
            "status": TaskStatus.PENDING,
            "progress": 0,
            "start_time": datetime.now(),
            "end_time": None,
            "duration": timedelta(0),
            "error_message": None
        }
        
        self.tasks[task_id] = task_data
        self.update_current_tasks_display()
        self.update_statistics()
        
        self.task_added.emit(task_data)
        return task_id
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        if task_id not in self.tasks:
            return
            
        task = self.tasks[task_id]
        
        # 更新任务数据
        for key, value in kwargs.items():
            if key in task:
                task[key] = value
        
        # 如果任务完成，记录结束时间
        if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task["end_time"] = datetime.now()
            task["duration"] = task["end_time"] - task["start_time"]
            
            # 移动到历史记录
            self.task_history.append(task.copy())
            del self.tasks[task_id]
            
            self.task_completed.emit(task_id)
        
        self.update_current_tasks_display()
        self.update_history_display()
        self.update_statistics()
        
        self.task_updated.emit(task_id, kwargs)
    
    def update_current_tasks_display(self):
        """更新当前任务显示"""
        if not QT_AVAILABLE:
            return
            
        self.current_tasks_table.setRowCount(len(self.tasks))
        
        for row, (task_id, task) in enumerate(self.tasks.items()):
            # 任务名称
            self.current_tasks_table.setItem(row, 0, QTableWidgetItem(task["name"]))
            
            # 状态
            status_item = QTableWidgetItem(self.tr(task["status"].lower()))
            if task["status"] == TaskStatus.RUNNING:
                status_item.setBackground(QColor(255, 255, 0, 100))  # 黄色背景
            elif task["status"] == TaskStatus.PENDING:
                status_item.setBackground(QColor(200, 200, 200, 100))  # 灰色背景
            self.current_tasks_table.setItem(row, 1, status_item)
            
            # 进度
            progress_widget = QProgressBar()
            progress_widget.setRange(0, 100)
            progress_widget.setValue(task["progress"])
            self.current_tasks_table.setCellWidget(row, 2, progress_widget)
            
            # 开始时间
            start_time_str = task["start_time"].strftime("%H:%M:%S")
            self.current_tasks_table.setItem(row, 3, QTableWidgetItem(start_time_str))
            
            # 持续时间
            duration = datetime.now() - task["start_time"]
            duration_str = str(duration).split('.')[0]  # 去掉微秒
            self.current_tasks_table.setItem(row, 4, QTableWidgetItem(duration_str))
    
    def update_history_display(self):
        """更新历史显示"""
        if not QT_AVAILABLE:
            return
            
        self.history_list.clear()
        
        for task in reversed(self.task_history[-50:]):  # 只显示最近50个
            status_icon = "✓" if task["status"] == TaskStatus.COMPLETED else "✗"
            duration_str = str(task["duration"]).split('.')[0]
            
            item_text = f"{status_icon} {task['name']} - {self.tr(task['status'].lower())} ({duration_str})"
            
            item = QListWidgetItem(item_text)
            if task["status"] == TaskStatus.COMPLETED:
                item.setBackground(QColor(0, 255, 0, 50))  # 淡绿色
            elif task["status"] == TaskStatus.FAILED:
                item.setBackground(QColor(255, 0, 0, 50))  # 淡红色
            
            self.history_list.addItem(item)
    
    def update_statistics(self):
        """更新统计信息"""
        if not QT_AVAILABLE:
            return
            
        total_tasks = len(self.task_history) + len(self.tasks)
        completed_tasks = len([t for t in self.task_history if t["status"] == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.task_history if t["status"] == TaskStatus.FAILED])
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        self.stats_labels["total_tasks"].setText(str(total_tasks))
        self.stats_labels["completed_tasks"].setText(str(completed_tasks))
        self.stats_labels["failed_tasks"].setText(str(failed_tasks))
        self.stats_labels["success_rate"].setText(f"{success_rate:.1f}%")
    
    def add_demo_task(self):
        """添加演示任务"""
        task_names = [
            "视频分析任务",
            "字幕生成任务", 
            "模型训练任务",
            "数据预处理任务",
            "视频导出任务"
        ]
        
        task_name = random.choice(task_names)
        task_id = self.add_task(task_name)
        
        # 模拟任务进度
        def simulate_progress():
            progress = 0
            self.update_task(task_id, status=TaskStatus.RUNNING)
            
            def update_progress():
                nonlocal progress
                progress += random.randint(5, 20)
                if progress >= 100:
                    progress = 100
                    status = TaskStatus.COMPLETED if random.random() > 0.1 else TaskStatus.FAILED
                    self.update_task(task_id, progress=progress, status=status)
                else:
                    self.update_task(task_id, progress=progress)
                    QTimer.singleShot(1000, update_progress)
            
            QTimer.singleShot(500, update_progress)
        
        QTimer.singleShot(100, simulate_progress)
    
    def clear_history(self):
        """清空历史记录"""
        self.task_history.clear()
        self.update_history_display()
        self.update_statistics()
    
    def setup_demo_data(self):
        """设置演示数据"""
        # 添加一些历史任务
        demo_tasks = [
            ("视频分析完成", TaskStatus.COMPLETED),
            ("字幕生成完成", TaskStatus.COMPLETED),
            ("模型训练失败", TaskStatus.FAILED),
        ]
        
        for task_name, status in demo_tasks:
            task_data = {
                "id": f"demo_{len(self.task_history)}",
                "name": task_name,
                "type": "demo",
                "status": status,
                "progress": 100,
                "start_time": datetime.now() - timedelta(minutes=random.randint(5, 60)),
                "end_time": datetime.now() - timedelta(minutes=random.randint(1, 5)),
                "duration": timedelta(minutes=random.randint(1, 10)),
                "error_message": "模拟错误" if status == TaskStatus.FAILED else None
            }
            self.task_history.append(task_data)
        
        self.update_history_display()
        self.update_statistics()
    
    def create_log_tab(self) -> QWidget:
        """创建日志显示标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 日志显示区域
        self.log_display = QTextEdit()
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

        # 日志控制面板
        log_controls = QHBoxLayout()

        # 日志级别过滤
        level_combo = QComboBox()
        level_combo.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        level_combo.currentTextChanged.connect(self.filter_logs_by_level)
        log_controls.addWidget(QLabel("级别:"))
        log_controls.addWidget(level_combo)

        # 清空日志按钮
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_logs)
        log_controls.addWidget(clear_log_btn)

        # 自动滚动复选框
        auto_scroll_checkbox = QCheckBox("自动滚动")
        auto_scroll_checkbox.setChecked(True)
        auto_scroll_checkbox.stateChanged.connect(self.toggle_auto_scroll)
        log_controls.addWidget(auto_scroll_checkbox)

        log_controls.addStretch()
        layout.addLayout(log_controls)

        # 设置日志回调
        self.setup_log_callback()
        self.auto_scroll = True

        return widget

    def setup_log_callback(self):
        """设置日志回调"""
        try:
            # 优先使用PyQt6信号机制
            from src.visionai_clipsmaster.ui.main_window import log_signal_emitter
            log_signal_emitter.log_message.connect(self.on_log_message)
            logger.info("进度看板日志信号已连接")
        except Exception as e:
            logger.warning(f"无法连接日志信号: {e}")

            # 备用：传统回调方式
            try:
                from src.visionai_clipsmaster.ui.main_window import log_handler
                if hasattr(log_handler, 'register_ui_callback'):
                    log_handler.register_ui_callback(self.on_log_message)
                    logger.info("进度看板日志回调已注册（备用方式）")
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

    def filter_logs_by_level(self, level: str):
        """按级别过滤日志"""
        # 这里可以实现日志级别过滤逻辑
        logger.info(f"日志级别过滤器设置为: {level}")

    def clear_logs(self):
        """清空日志"""
        if self.log_display:
            self.log_display.clear()
            logger.info("进度看板日志已清空")

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
