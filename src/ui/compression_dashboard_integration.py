#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩监控系统集成模块

将压缩性能监控仪表盘集成到主应用程序中，提供UI入口和后台数据收集机制。
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List, Tuple

from PyQt6.QtWidgets import QPushButton, QMenu
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from src.ui.compression_dashboard import CompressionDashboardWindow, run_dashboard
from src.compression.adaptive_compression import get_smart_compressor, get_compression_stats
from src.compression.core import compress, decompress

# 设置日志
logger = logging.getLogger("compression_integration")


class CompressionMonitor(QObject):

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """压缩性能监控器
    
    监控压缩系统性能指标，收集统计数据并在需要时提醒用户
    """
    
    # 压缩率下降信号
    ratio_alert_signal = pyqtSignal(float, float)  # 当前值, 历史平均值
    
    def __init__(self, parent=None):
        """初始化压缩监控器"""
        super().__init__(parent)
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 历史数据
        self.history = {
            "ratios": [],
            "speeds": [],
            "memory_levels": [],
            "timestamps": []
        }
        
        # 统计数据
        self.stats = {
            "avg_ratio": 0.0,
            "avg_speed": 0.0,
            "total_bytes": 0,
            "total_compressed_bytes": 0,
            "last_update": time.time()
        }
        
        # 上次发出警报的时间
        self.last_alert_time = 0
        
        # 警报阈值
        self.ratio_alert_threshold = 0.2  # 压缩率下降20%触发警报
    
    def start_monitoring(self, check_interval: int = 10):
        """启动压缩性能监控
        
        Args:
            check_interval: 检查间隔（秒）
        """
        if self.is_monitoring:
            logger.warning("压缩监控器已在运行")
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"压缩监控器已启动，检查间隔: {check_interval}秒")
    
    def stop_monitoring(self):
        """停止压缩性能监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            logger.info("压缩监控器已停止")
    
    def _monitoring_loop(self, interval: int):
        """监控循环
        
        Args:
            interval: 检查间隔（秒）
        """
        while self.is_monitoring:
            try:
                # 获取当前压缩统计信息
                current_stats = get_compression_stats()
                
                if current_stats:
                    # 压缩率（较小值表示更好的压缩）
                    if "average_ratio" in current_stats:
                        ratio = current_stats["average_ratio"]
                        self.history["ratios"].append(ratio)
                        
                        # 检查压缩率是否下降
                        self._check_ratio_alert(ratio)
                    
                    # 压缩速度
                    if "bytes_processed" in current_stats and "time_spent" in current_stats and current_stats["time_spent"] > 0:
                        speed = current_stats["bytes_processed"] / (1024 * 1024) / current_stats["time_spent"]
                        self.history["speeds"].append(speed)
                    
                    # 内存压力级别
                    compressor = get_smart_compressor()
                    self.history["memory_levels"].append(compressor.current_pressure_level.value)
                    
                    # 时间戳
                    self.history["timestamps"].append(time.time())
                    
                    # 保持历史记录在合理范围内
                    max_history = 1000
                    if len(self.history["ratios"]) > max_history:
                        for key in self.history:
                            self.history[key] = self.history[key][-max_history:]
                    
                    # 更新统计信息
                    self._update_stats()
            
            except Exception as e:
                logger.error(f"压缩监控出错: {e}")
            
            # 等待下一次检查
            time.sleep(interval)
    
    def _check_ratio_alert(self, current_ratio: float):
        """检查压缩率是否需要发出警报
        
        Args:
            current_ratio: 当前压缩率
        """
        # 计算历史平均压缩率（最近20个样本）
        recent_ratios = self.history["ratios"][-20:]
        if len(recent_ratios) < 5:  # 至少需要5个样本
            return
            
        avg_ratio = sum(recent_ratios) / len(recent_ratios)
        
        # 如果当前压缩率比平均值高（更差）超过阈值，发出警报
        # 但限制警报频率（至少间隔10分钟）
        current_time = time.time()
        if (current_ratio > avg_ratio * (1 + self.ratio_alert_threshold) and
            current_time - self.last_alert_time > 600):
            
            self.ratio_alert_signal.emit(current_ratio, avg_ratio)
            self.last_alert_time = current_time
    
    def _update_stats(self):
        """更新统计信息"""
        if self.history["ratios"]:
            self.stats["avg_ratio"] = sum(self.history["ratios"]) / len(self.history["ratios"])
        
        if self.history["speeds"]:
            self.stats["avg_speed"] = sum(self.history["speeds"]) / len(self.history["speeds"])
        
        self.stats["last_update"] = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取压缩监控统计信息
        
        Returns:
            Dict: 统计信息
        """
        return dict(self.stats)
    
    def get_history(self) -> Dict[str, List]:
        """获取历史数据
        
        Returns:
            Dict: 历史数据
        """
        return dict(self.history)


class CompressionDashboardLauncher(QObject):
    """压缩仪表盘启动器
    
    提供在主程序中启动压缩仪表盘的功能
    """
    
    def __init__(self, parent=None):
        """初始化启动器"""
        super().__init__(parent)
        
        # 仪表盘实例
        self.dashboard = None
        
        logger.info("压缩仪表盘启动器初始化完成")
    
    def create_toolbar_button(self, toolbar):
        """为工具栏创建按钮
        
        Args:
            toolbar: 工具栏对象
            
        Returns:
            创建的按钮
        """
        button = QPushButton("压缩监控")
        button.setToolTip("打开压缩性能监控仪表盘")
        button.clicked.connect(self.launch_dashboard)
        toolbar.addWidget(button)
        return button
    
    def create_menu_action(self, menu):
        """为菜单创建动作
        
        Args:
            menu: 菜单对象
            
        Returns:
            创建的动作
        """
        action = QAction("压缩性能监控", menu)
        action.setStatusTip("打开压缩性能监控仪表盘")
        action.triggered.connect(self.launch_dashboard)
        menu.addAction(action)
        return action
    
    def launch_dashboard(self):
        """启动压缩仪表盘"""
        logger.info("启动压缩性能监控仪表盘")
        
        # 避免重复启动
        if self.dashboard is not None and hasattr(self.dashboard, "isVisible") and self.dashboard.isVisible():
            # 如果已存在且可见，则前置显示
            self.dashboard.activateWindow()
            self.dashboard.raise_()
            return
        
        # 启动仪表盘窗口
        self.dashboard = CompressionDashboardWindow()
        self.dashboard.show()


# 全局实例
_compression_monitor: Optional[CompressionMonitor] = None
_dashboard_launcher: Optional[CompressionDashboardLauncher] = None


def get_compression_monitor() -> CompressionMonitor:
    """获取压缩监控器实例
    
    Returns:
        压缩监控器实例
    """
    global _compression_monitor
    if _compression_monitor is None:
        _compression_monitor = CompressionMonitor()
    return _compression_monitor


def get_compression_dashboard_launcher() -> CompressionDashboardLauncher:
    """获取压缩仪表盘启动器实例
    
    Returns:
        压缩仪表盘启动器实例
    """
    global _dashboard_launcher
    if _dashboard_launcher is None:
        _dashboard_launcher = CompressionDashboardLauncher()
    return _dashboard_launcher


def initialize_compression_monitoring(auto_start: bool = True):
    """初始化压缩监控功能
    
    Args:
        auto_start: 是否自动启动监控
    """
    monitor = get_compression_monitor()
    if auto_start:
        monitor.start_monitoring()
    
    # 确保启动器已初始化
    get_compression_dashboard_launcher()
    
    logger.info("压缩监控系统初始化完成")


def run_standalone_dashboard():
    """运行独立的压缩仪表盘"""
    run_dashboard() 