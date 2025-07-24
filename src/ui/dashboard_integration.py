#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
内存监控看板集成模块

将内存监控仪表盘集成到主应用程序中，提供UI入口和后台数据共享机制。
"""

import logging
import threading
import time
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import QPushButton, QMenu
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from src.ui.memory_dashboard import MemoryDashboard, run_dashboard
from src.monitoring import get_metrics_collector, get_alert_manager, AlertLevel

# 设置日志
logger = logging.getLogger("dashboard_integration")


class DashboardLauncher(QObject):
    """仪表盘启动器
    
    提供在主程序中启动内存仪表盘的功能，可作为独立窗口或嵌入式组件使用。
    """
    
    # 预警信号
    alert_signal = pyqtSignal(str, str)  # 级别, 消息
    
    def __init__(self, parent=None):
        """初始化启动器
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        
        # 仪表盘实例
        self.dashboard: Optional[MemoryDashboard] = None
        
        # 预警监听器
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self._check_alerts)
        self.alert_timer.start(5000)  # 每5秒检查一次预警
        
        # 最后一次看到的预警ID
        self.last_seen_alert_id = ""
        
        logger.info("内存仪表盘启动器初始化完成")
    
    def create_toolbar_button(self, toolbar):
        """为工具栏创建按钮
        
        Args:
            toolbar: 工具栏对象
            
        Returns:
            创建的按钮
        """
        button = QPushButton("内存监控")
        button.setToolTip("打开内存监控仪表盘")
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
        action = QAction("内存监控仪表盘", menu)
        action.setStatusTip("打开内存监控仪表盘")
        action.triggered.connect(self.launch_dashboard)
        menu.addAction(action)
        return action
    
    def launch_dashboard(self):
        """启动内存仪表盘"""
        logger.info("启动内存监控仪表盘")
        
        # 避免重复启动
        if self.dashboard is not None and hasattr(self.dashboard, "isVisible") and self.dashboard.isVisible():
            # 如果已存在且可见，则前置显示
            self.dashboard.activateWindow()
            self.dashboard.raise_()
            return
        
        # 启动仪表盘窗口
        threading.Thread(target=run_dashboard, daemon=True).start()
    
    def _check_alerts(self):
        """检查是否有新预警需要通知"""
        try:
            # 获取最新的高级别预警
            alert_manager = get_alert_manager()
            recent_alerts = alert_manager.get_history(limit=1, level=AlertLevel.ERROR)
            
            if not recent_alerts:
                # 尝试获取警告级别的预警
                recent_alerts = alert_manager.get_history(limit=1, level=AlertLevel.WARNING)
            
            if recent_alerts:
                latest_alert = recent_alerts[0]
                alert_id = f"{latest_alert['timestamp']}_{latest_alert['category']}_{latest_alert['resource']}"
                
                # 只有新预警才通知
                if alert_id != self.last_seen_alert_id:
                    self.last_seen_alert_id = alert_id
                    
                    # 构建消息
                    level = latest_alert["level"]
                    message = f"{latest_alert['category']}/{latest_alert['resource']}: {latest_alert['value']}"
                    if "message" in latest_alert.get("details", {}):
                        message += f"\n{latest_alert['details']['message']}"
                    
                    # 发出信号
                    self.alert_signal.emit(level, message)
        
        except Exception as e:
            logger.error(f"检查预警出错: {e}")


class MemoryMonitor:
    """内存监控器
    
    在后台监控内存使用情况，并在达到阈值时提醒用户。
    """
    
    def __init__(self):
        """初始化内存监控器"""
        self.metrics_collector = get_metrics_collector()
        self.alert_manager = get_alert_manager()
        
        # 启动监控线程
        self.running = False
        self.monitor_thread = None
    
    def start_monitoring(self, check_interval: int = 5):
        """启动后台监控
        
        Args:
            check_interval: 检查间隔（秒）
        """
        if self.running and self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("内存监控器已在运行")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"内存监控器已启动，检查间隔: {check_interval}秒")
    
    def stop_monitoring(self):
        """停止后台监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            logger.info("内存监控器已停止")
    
    def _monitoring_loop(self, interval: int):
        """监控循环
        
        Args:
            interval: 检查间隔（秒）
        """
        while self.running:
            try:
                # 检查系统内存使用率
                system_memory = self.metrics_collector.collect_on_demand("system_metrics.total_memory")
                process_memory = self.metrics_collector.collect_on_demand("system_metrics.process_rss")
                
                if system_memory is not None:
                    logger.debug(f"系统内存使用率: {system_memory:.1f}%, 进程内存: {process_memory:.1f}MB")
                
            except Exception as e:
                logger.error(f"内存监控出错: {e}")
            
            # 暂停指定时间
            time.sleep(interval)


# 创建全局实例
_memory_monitor: Optional[MemoryMonitor] = None
_dashboard_launcher: Optional[DashboardLauncher] = None


def get_memory_monitor() -> MemoryMonitor:
    """获取内存监控器实例
    
    Returns:
        内存监控器实例
    """
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor


def get_dashboard_launcher() -> DashboardLauncher:
    """获取仪表盘启动器实例
    
    Returns:
        仪表盘启动器实例
    """
    global _dashboard_launcher
    if _dashboard_launcher is None:
        _dashboard_launcher = DashboardLauncher()
    return _dashboard_launcher


def initialize_memory_monitoring(auto_start: bool = True):
    """初始化内存监控功能
    
    Args:
        auto_start: 是否自动启动监控
    """
    monitor = get_memory_monitor()
    if auto_start:
        monitor.start_monitoring()
    
    # 确保启动器已初始化
    get_dashboard_launcher()
    
    logger.info("内存监控系统初始化完成") 