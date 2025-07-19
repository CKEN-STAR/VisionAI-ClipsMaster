#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 系统监控UI

提供系统资源监控界面
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTabWidget, QProgressBar, QGroupBox, QGridLayout, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入系统监控模块
try:
    from src.monitor.system_monitor import get_system_monitor, get_current_stats, get_system_info
    HAS_MONITOR = True
except ImportError:
    try:
        # 尝试相对导入
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from src.monitor.system_monitor import get_system_monitor, get_current_stats, get_system_info
        HAS_MONITOR = True
    except ImportError:
        logger.warning("无法导入系统监控模块，将使用模拟数据")
        HAS_MONITOR = False

# 如果无法导入系统监控模块，使用模拟数据
if not HAS_MONITOR:
    import random
    
    def get_system_info():
        """模拟系统信息"""
        return {
            "platform": "模拟平台",
            "processor": "模拟处理器",
            "python_version": "3.x",
            "cpu_count": 4,
            "total_memory": 8 * 1024 * 1024 * 1024  # 8GB
        }
    
    def get_current_stats():
        """模拟系统统计信息"""
        return {
            "timestamp": time.time(),
            "cpu": {
                "percent": random.uniform(10, 90),
                "per_cpu": [random.uniform(10, 90) for _ in range(4)]
            },
            "memory": {
                "total": 8 * 1024 * 1024 * 1024,  # 8GB
                "available": random.uniform(2, 6) * 1024 * 1024 * 1024,
                "used": random.uniform(2, 6) * 1024 * 1024 * 1024,
                "percent": random.uniform(20, 80)
            },
            "disk": {
                "total": 500 * 1024 * 1024 * 1024,  # 500GB
                "used": random.uniform(100, 400) * 1024 * 1024 * 1024,
                "free": random.uniform(100, 400) * 1024 * 1024 * 1024,
                "percent": random.uniform(20, 80)
            }
        }

class SystemMonitorWindow(QMainWindow):
    """系统监控窗口"""
    
    def __init__(self):
        """初始化系统监控窗口"""
        super().__init__()
        
        self.setWindowTitle("VisionAI-ClipsMaster 系统监控")
        self.resize(800, 600)
        
        # 初始化UI组件
        self.init_ui()
        
        # 更新定时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # 每秒更新一次
        
        # 立即更新一次
        self.update_stats()
        
        # 启动系统监控
        if HAS_MONITOR:
            monitor = get_system_monitor()
            if monitor:
                monitor.start()
        
        self.statusBar().showMessage("系统监控已启动")
        logger.info("系统监控UI已启动")
    
    def init_ui(self):
        """初始化UI组件"""
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 系统信息区域
        system_info_group = QGroupBox("系统信息")
        system_info_layout = QGridLayout(system_info_group)
        
        # 系统信息标签
        self.platform_label = QLabel("平台: 加载中...")
        self.processor_label = QLabel("处理器: 加载中...")
        self.python_version_label = QLabel("Python版本: 加载中...")
        self.cpu_count_label = QLabel("CPU核心数: 加载中...")
        self.memory_total_label = QLabel("总内存: 加载中...")
        
        # 添加系统信息标签
        system_info_layout.addWidget(self.platform_label, 0, 0)
        system_info_layout.addWidget(self.processor_label, 1, 0)
        system_info_layout.addWidget(self.python_version_label, 2, 0)
        system_info_layout.addWidget(self.cpu_count_label, 0, 1)
        system_info_layout.addWidget(self.memory_total_label, 1, 1)
        
        # 添加系统信息组
        main_layout.addWidget(system_info_group)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        
        # 资源监控选项卡
        self.monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(self.monitor_tab)
        
        # CPU使用率
        cpu_group = QGroupBox("CPU使用率")
        cpu_layout = QVBoxLayout(cpu_group)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setValue(0)
        self.cpu_label = QLabel("CPU使用率: 0%")
        
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_progress)
        
        # 内存使用率
        memory_group = QGroupBox("内存使用率")
        memory_layout = QVBoxLayout(memory_group)
        
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setValue(0)
        self.memory_label = QLabel("内存使用率: 0%")
        
        memory_layout.addWidget(self.memory_label)
        memory_layout.addWidget(self.memory_progress)
        
        # 磁盘使用率
        disk_group = QGroupBox("磁盘使用率")
        disk_layout = QVBoxLayout(disk_group)
        
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_progress.setValue(0)
        self.disk_label = QLabel("磁盘使用率: 0%")
        
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.disk_progress)
        
        # 添加组到监控布局
        monitor_layout.addWidget(cpu_group)
        monitor_layout.addWidget(memory_group)
        monitor_layout.addWidget(disk_group)
        
        # 添加选项卡
        self.tabs.addTab(self.monitor_tab, "系统监控")
        
        # 添加选项卡到主布局
        main_layout.addWidget(self.tabs)
        
        # 更新系统信息
        self.update_system_info()
    
    def update_system_info(self):
        """更新系统信息"""
        try:
            info = get_system_info()
            
            self.platform_label.setText(f"平台: {info.get('platform', '未知')}")
            self.processor_label.setText(f"处理器: {info.get('processor', '未知')}")
            self.python_version_label.setText(f"Python版本: {info.get('python_version', '未知')}")
            self.cpu_count_label.setText(f"CPU核心数: {info.get('cpu_count', '未知')}")
            
            # 格式化内存大小
            total_memory = info.get('total_memory', 0)
            if total_memory > 0:
                if total_memory >= 1024 ** 3:
                    total_memory_str = f"{total_memory / (1024 ** 3):.2f} GB"
                else:
                    total_memory_str = f"{total_memory / (1024 ** 2):.2f} MB"
            else:
                total_memory_str = "未知"
            
            self.memory_total_label.setText(f"总内存: {total_memory_str}")
            
        except Exception as e:
            logger.error(f"更新系统信息时出错: {e}")
    
    def update_stats(self):
        """更新统计信息"""
        try:
            stats = get_current_stats()
            
            # 更新CPU使用率
            if "cpu" in stats:
                cpu_percent = stats["cpu"]["percent"]
                self.cpu_progress.setValue(int(cpu_percent))
                self.cpu_label.setText(f"CPU使用率: {cpu_percent:.1f}%")
                
                # 设置进度条颜色
                self._set_progress_color(self.cpu_progress, cpu_percent)
            
            # 更新内存使用率
            if "memory" in stats:
                memory_percent = stats["memory"]["percent"]
                self.memory_progress.setValue(int(memory_percent))
                self.memory_label.setText(f"内存使用率: {memory_percent:.1f}%")
                
                # 设置进度条颜色
                self._set_progress_color(self.memory_progress, memory_percent)
                
                # 格式化内存大小
                used_memory = stats["memory"]["used"]
                total_memory = stats["memory"]["total"]
                
                if used_memory >= 1024 ** 3 and total_memory >= 1024 ** 3:
                    used_str = f"{used_memory / (1024 ** 3):.2f} GB"
                    total_str = f"{total_memory / (1024 ** 3):.2f} GB"
                else:
                    used_str = f"{used_memory / (1024 ** 2):.2f} MB"
                    total_str = f"{total_memory / (1024 ** 2):.2f} MB"
                
                self.memory_label.setText(f"内存使用率: {memory_percent:.1f}% ({used_str} / {total_str})")
            
            # 更新磁盘使用率
            if "disk" in stats:
                disk_percent = stats["disk"]["percent"]
                self.disk_progress.setValue(int(disk_percent))
                self.disk_label.setText(f"磁盘使用率: {disk_percent:.1f}%")
                
                # 设置进度条颜色
                self._set_progress_color(self.disk_progress, disk_percent)
                
                # 格式化磁盘大小
                used_disk = stats["disk"]["used"]
                total_disk = stats["disk"]["total"]
                
                if used_disk >= 1024 ** 3 and total_disk >= 1024 ** 3:
                    used_str = f"{used_disk / (1024 ** 3):.2f} GB"
                    total_str = f"{total_disk / (1024 ** 3):.2f} GB"
                else:
                    used_str = f"{used_disk / (1024 ** 2):.2f} MB"
                    total_str = f"{total_disk / (1024 ** 2):.2f} MB"
                
                self.disk_label.setText(f"磁盘使用率: {disk_percent:.1f}% ({used_str} / {total_str})")
            
        except Exception as e:
            logger.error(f"更新统计信息时出错: {e}")
    
    def _set_progress_color(self, progress_bar, value):
        """设置进度条颜色
        
        Args:
            progress_bar: 进度条
            value: 进度值
        """
        style = ""
        if value < 60:
            style = "QProgressBar::chunk { background-color: #4CAF50; }"  # 绿色
        elif value < 80:
            style = "QProgressBar::chunk { background-color: #FF9800; }"  # 橙色
        else:
            style = "QProgressBar::chunk { background-color: #F44336; }"  # 红色
        
        progress_bar.setStyleSheet(style)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止更新定时器
        if self.update_timer.isActive():
            self.update_timer.stop()
        
        # 停止系统监控
        if HAS_MONITOR:
            monitor = get_system_monitor()
            if monitor:
                monitor.stop()
        
        logger.info("系统监控UI已关闭")
        event.accept()

def show_system_monitor():
    """显示系统监控窗口"""
    try:
        # 如果已经有QApplication实例，使用它
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        window = SystemMonitorWindow()
        window.show()
        
        # 如果是独立运行，则执行事件循环
        if QApplication.instance() is app:
            return app.exec()
        
        return window
    
    except Exception as e:
        logger.error(f"显示系统监控窗口时出错: {str(e)}")
        return None

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(" VisionAI-ClipsMaster 系统监控UI测试 ")
    print("-" * 50)
    
    # 显示系统监控窗口
    sys.exit(show_system_monitor()) 