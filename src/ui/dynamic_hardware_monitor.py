#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态硬件监控组件 - VisionAI-ClipsMaster
实现设备配置实时检测与显示，支持硬件变化时的自动更新
"""

import sys
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QProgressBar, QFrame, QGridLayout, QSizePolicy,
    QTextEdit, QScrollArea, QSpacerItem, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject, QMutex
from PyQt6.QtGui import QFont, QPalette, QColor

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

@dataclass
class HardwareSnapshot:
    """硬件快照数据类"""
    gpu_type: str
    gpu_memory_gb: float
    gpu_count: int
    gpu_names: List[str]
    system_ram_gb: float
    available_ram_gb: float
    cpu_cores: int
    cpu_freq_mhz: float
    performance_level: str
    recommended_quantization: str
    gpu_acceleration: bool
    has_gpu: bool
    detection_timestamp: float
    
    def __eq__(self, other):
        """比较两个硬件快照是否相同（忽略时间戳）"""
        if not isinstance(other, HardwareSnapshot):
            return False
        
        return (
            self.gpu_type == other.gpu_type and
            abs(self.gpu_memory_gb - other.gpu_memory_gb) < 0.1 and
            self.gpu_count == other.gpu_count and
            self.gpu_names == other.gpu_names and
            abs(self.system_ram_gb - other.system_ram_gb) < 0.1 and
            self.cpu_cores == other.cpu_cores and
            self.performance_level == other.performance_level and
            self.recommended_quantization == other.recommended_quantization and
            self.gpu_acceleration == other.gpu_acceleration and
            self.has_gpu == other.has_gpu
        )

class HardwareMonitorWorker(QObject):
    """硬件监控工作线程"""
    
    hardware_detected = pyqtSignal(object)  # 硬件检测信号
    hardware_changed = pyqtSignal(object, object)  # 硬件变化信号 (old, new)
    detection_error = pyqtSignal(str)  # 检测错误信号
    
    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.last_snapshot = None
        self.detection_interval = 5.0  # 5秒检测一次
        self.mutex = QMutex()
        
    def start_monitoring(self):
        """开始监控"""
        self.mutex.lock()
        try:
            if not self.monitoring:
                self.monitoring = True
                # 使用QTimer来避免阻塞线程
                self.timer = QTimer()
                self.timer.timeout.connect(self._detect_once)
                self.timer.start(int(self.detection_interval * 1000))  # 转换为毫秒
        finally:
            self.mutex.unlock()

    def stop_monitoring(self):
        """停止监控"""
        self.mutex.lock()
        try:
            self.monitoring = False
            if hasattr(self, 'timer'):
                self.timer.stop()
                self.timer.deleteLater()
        finally:
            self.mutex.unlock()

    def _detect_once(self):
        """执行一次检测"""
        try:
            if not self.monitoring:
                return

            # 检测硬件
            snapshot = self._detect_hardware()

            if snapshot:
                # 发送检测信号
                self.hardware_detected.emit(snapshot)

                # 检查是否有变化
                if self.last_snapshot and self.last_snapshot != snapshot:
                    self.hardware_changed.emit(self.last_snapshot, snapshot)
                    logger.info("检测到硬件配置变化")

                self.last_snapshot = snapshot

        except Exception as e:
            logger.error(f"硬件检测错误: {e}")
            self.detection_error.emit(str(e))
    
    def _detect_hardware(self) -> Optional[HardwareSnapshot]:
        """检测硬件配置"""
        try:
            from src.utils.hardware_detector import HardwareDetector
            
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            
            # 转换为快照对象
            snapshot = HardwareSnapshot(
                gpu_type=str(getattr(hardware_info, 'gpu_type', 'unknown')),
                gpu_memory_gb=getattr(hardware_info, 'gpu_memory_gb', 0),
                gpu_count=getattr(hardware_info, 'gpu_count', 0),
                gpu_names=getattr(hardware_info, 'gpu_names', []),
                system_ram_gb=getattr(hardware_info, 'total_memory_gb', 0),
                available_ram_gb=getattr(hardware_info, 'available_memory_gb', 0),
                cpu_cores=getattr(hardware_info, 'cpu_cores', 0),
                cpu_freq_mhz=getattr(hardware_info, 'cpu_freq_mhz', 0),
                performance_level=str(getattr(hardware_info, 'performance_level', 'unknown')),
                recommended_quantization=getattr(hardware_info, 'recommended_quantization', 'unknown'),
                gpu_acceleration=getattr(hardware_info, 'gpu_acceleration', False),
                has_gpu=getattr(hardware_info, 'gpu_memory_gb', 0) > 0,
                detection_timestamp=time.time()
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"硬件检测失败: {e}")
            return None
    
    def force_detection(self):
        """强制执行一次检测"""
        try:
            snapshot = self._detect_hardware()
            if snapshot:
                self.hardware_detected.emit(snapshot)
                
                if self.last_snapshot and self.last_snapshot != snapshot:
                    self.hardware_changed.emit(self.last_snapshot, snapshot)
                
                self.last_snapshot = snapshot
                
        except Exception as e:
            logger.error(f"强制检测失败: {e}")
            self.detection_error.emit(str(e))

class RealTimeHardwareInfoWidget(QWidget):
    """实时硬件信息显示组件"""

    hardware_detected = pyqtSignal(object)  # 硬件检测完成信号（包括初始检测）
    hardware_changed = pyqtSignal(object)  # 硬件变化信号
    refresh_requested = pyqtSignal()  # 刷新请求信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_snapshot = None
        self.monitor_worker = None
        self.monitor_thread = None
        
        self.init_ui()
        self.start_monitoring()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🔧 实时硬件信息")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 刷新按钮
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 手动刷新")
        self.refresh_btn.clicked.connect(self.force_refresh)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # 硬件信息显示区域
        self.info_group = QGroupBox("硬件配置")
        self.info_layout = QGridLayout(self.info_group)
        layout.addWidget(self.info_group)
        
        # 状态标签
        self.status_label = QLabel("🔍 正在检测硬件配置...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def start_monitoring(self):
        """开始硬件监控"""
        try:
            # 创建监控工作线程
            self.monitor_thread = QThread()
            self.monitor_worker = HardwareMonitorWorker()
            self.monitor_worker.moveToThread(self.monitor_thread)

            # 连接信号
            self.monitor_worker.hardware_detected.connect(self.update_hardware_info)
            self.monitor_worker.hardware_changed.connect(self.on_hardware_changed)
            self.monitor_worker.detection_error.connect(self.on_detection_error)

            # 连接线程完成信号
            self.monitor_thread.finished.connect(self.monitor_worker.deleteLater)
            self.monitor_thread.finished.connect(self.monitor_thread.deleteLater)

            # 启动线程
            self.monitor_thread.started.connect(self.monitor_worker.start_monitoring)
            self.monitor_thread.start()

            logger.info("硬件监控已启动")

        except Exception as e:
            logger.error(f"启动硬件监控失败: {e}")
            self.status_label.setText(f"❌ 监控启动失败: {e}")
    
    def stop_monitoring(self):
        """停止硬件监控"""
        try:
            if self.monitor_worker:
                self.monitor_worker.stop_monitoring()

            if self.monitor_thread and self.monitor_thread.isRunning():
                self.monitor_thread.quit()
                if not self.monitor_thread.wait(3000):  # 等待3秒
                    logger.warning("线程未能在3秒内正常退出，强制终止")
                    self.monitor_thread.terminate()
                    self.monitor_thread.wait(1000)  # 再等待1秒

            # 清理引用
            self.monitor_worker = None
            self.monitor_thread = None

            logger.info("硬件监控已停止")

        except Exception as e:
            logger.error(f"停止硬件监控失败: {e}")

    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self.stop_monitoring()
        except:
            pass  # 析构函数中忽略异常

    def force_refresh(self):
        """强制刷新硬件信息"""
        try:
            if self.monitor_worker:
                self.monitor_worker.force_detection()
                self.status_label.setText("🔄 正在强制刷新...")
                self.refresh_requested.emit()
                
        except Exception as e:
            logger.error(f"强制刷新失败: {e}")
            self.status_label.setText(f"❌ 刷新失败: {e}")
    
    def update_hardware_info(self, snapshot: HardwareSnapshot):
        """更新硬件信息显示"""
        try:
            self.current_snapshot = snapshot

            # 🔧 修复：确保UI更新在主线程中执行,避免闪退
            # 清除现有信息时使用deleteLater()而不是直接删除
            for i in reversed(range(self.info_layout.count())):
                widget = self.info_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()  # 延迟删除,避免崩溃

            # 添加硬件信息
            row = 0

            # GPU信息显示已移除 - 恢复UI界面到原始状态
            # 保留硬件检测后端功能，仅移除UI显示

            # 内存信息
            self._add_info_row("🧠 系统内存", f"{snapshot.system_ram_gb:.1f} GB", row)
            row += 1
            self._add_info_row("💿 可用内存", f"{snapshot.available_ram_gb:.1f} GB", row)
            row += 1

            # CPU信息
            self._add_info_row("⚡ CPU核心", f"{snapshot.cpu_cores} 核", row)
            row += 1
            if snapshot.cpu_freq_mhz > 0:
                self._add_info_row("🔄 CPU频率", f"{snapshot.cpu_freq_mhz:.0f} MHz", row)
                row += 1

            # 性能等级
            self._add_info_row("📊 性能等级", snapshot.performance_level, row)
            row += 1
            self._add_info_row("🎯 推荐量化", snapshot.recommended_quantization, row)

            # 更新状态
            timestamp = datetime.fromtimestamp(snapshot.detection_timestamp)
            self.status_label.setText(f"✅ 最后更新: {timestamp.strftime('%H:%M:%S')}")

            # 🔧 关键修复：发射hardware_detected信号
            # 这样初始检测时也能触发推荐更新
            logger.info("📤 发射 hardware_detected 信号")
            self.hardware_detected.emit(snapshot)

        except Exception as e:
            logger.error(f"更新硬件信息失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            try:
                self.status_label.setText(f"❌ 更新失败: {e}")
            except:
                pass  # 忽略setText可能的异常
    
    def _add_info_row(self, label: str, value: str, row: int):
        """添加信息行"""
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Microsoft YaHei", 9, QFont.Weight.Bold))
        
        value_widget = QLabel(value)
        value_widget.setFont(QFont("Microsoft YaHei", 9))
        value_widget.setStyleSheet("color: #333;")
        
        self.info_layout.addWidget(label_widget, row, 0)
        self.info_layout.addWidget(value_widget, row, 1)
    
    def on_hardware_changed(self, old_snapshot: HardwareSnapshot, new_snapshot: HardwareSnapshot):
        """硬件配置变化处理"""
        try:
            logger.info("检测到硬件配置变化，正在更新显示")
            self.hardware_changed.emit(new_snapshot)
            
            # 显示变化通知
            self.status_label.setText("🔄 检测到硬件变化，正在更新...")
            
        except Exception as e:
            logger.error(f"处理硬件变化失败: {e}")
    
    def on_detection_error(self, error_msg: str):
        """检测错误处理"""
        logger.error(f"硬件检测错误: {error_msg}")
        self.status_label.setText(f"❌ 检测错误: {error_msg}")
    
    def get_hardware_info(self) -> Optional[Dict]:
        """获取当前硬件信息"""
        if self.current_snapshot:
            return {
                'gpu_type': self.current_snapshot.gpu_type,
                'gpu_memory_gb': self.current_snapshot.gpu_memory_gb,
                'gpu_count': self.current_snapshot.gpu_count,
                'gpu_names': self.current_snapshot.gpu_names,
                'system_ram_gb': self.current_snapshot.system_ram_gb,
                'available_ram_gb': self.current_snapshot.available_ram_gb,
                'cpu_cores': self.current_snapshot.cpu_cores,
                'cpu_freq_mhz': self.current_snapshot.cpu_freq_mhz,
                'performance_level': self.current_snapshot.performance_level,
                'recommended_quantization': self.current_snapshot.recommended_quantization,
                'gpu_acceleration': self.current_snapshot.gpu_acceleration,
                'has_gpu': self.current_snapshot.has_gpu,
                'detection_timestamp': self.current_snapshot.detection_timestamp
            }
        return None
    
    def closeEvent(self, event):
        """关闭事件"""
        self.stop_monitoring()
        super().closeEvent(event)
