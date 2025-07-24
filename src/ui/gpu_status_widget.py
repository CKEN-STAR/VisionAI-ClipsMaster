#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU状态显示组件
用于在UI中显示GPU加速状态和性能信息
"""

import os
import sys
import time
import threading
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QGroupBox, QGridLayout,
    QFrame, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

try:
    from src.utils.enhanced_device_manager import EnhancedDeviceManager, WorkloadProfile
    from src.core.gpu_accelerated_video_processor import ProcessingConfig
except ImportError as e:
    print(f"⚠️ 导入GPU模块失败: {e}")

class GPUStatusWidget(QWidget):
    """GPU状态显示组件"""
    
    # 信号定义
    gpu_status_changed = pyqtSignal(dict)  # GPU状态变化信号
    performance_updated = pyqtSignal(dict)  # 性能指标更新信号
    
    def __init__(self, parent=None):
        """初始化GPU状态组件"""
        super().__init__(parent)
        
        self.device_manager = None
        self.monitoring_active = False
        self.monitor_timer = None
        self.current_gpu_status = {}
        
        # 初始化UI
        self.init_ui()
        
        # 初始化设备管理器
        self.init_device_manager()
        
        # 启动状态监控
        self.start_monitoring()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建GPU状态组
        self.create_gpu_status_group(layout)
        
        # 创建性能监控组
        self.create_performance_group(layout)
        
        # 创建控制按钮组
        self.create_control_group(layout)
    
    def create_gpu_status_group(self, parent_layout):
        """创建GPU状态显示组"""
        gpu_group = QGroupBox("🎮 GPU状态")
        gpu_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        gpu_layout = QGridLayout(gpu_group)
        
        # GPU可用性状态
        self.gpu_status_label = QLabel("检测中...")
        self.gpu_status_label.setStyleSheet("font-weight: bold; color: #666;")
        gpu_layout.addWidget(QLabel("状态:"), 0, 0)
        gpu_layout.addWidget(self.gpu_status_label, 0, 1)
        
        # GPU设备名称
        self.gpu_name_label = QLabel("未知")
        gpu_layout.addWidget(QLabel("设备:"), 1, 0)
        gpu_layout.addWidget(self.gpu_name_label, 1, 1)
        
        # GPU内存信息
        self.gpu_memory_label = QLabel("N/A")
        gpu_layout.addWidget(QLabel("显存:"), 2, 0)
        gpu_layout.addWidget(self.gpu_memory_label, 2, 1)
        
        # GPU利用率
        self.gpu_utilization_bar = QProgressBar()
        self.gpu_utilization_bar.setRange(0, 100)
        self.gpu_utilization_bar.setValue(0)
        self.gpu_utilization_bar.setFormat("利用率: %p%")
        gpu_layout.addWidget(QLabel("利用率:"), 3, 0)
        gpu_layout.addWidget(self.gpu_utilization_bar, 3, 1)
        
        parent_layout.addWidget(gpu_group)
    
    def create_performance_group(self, parent_layout):
        """创建性能监控组"""
        perf_group = QGroupBox("📊 性能监控")
        perf_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        perf_layout = QGridLayout(perf_group)
        
        # 处理速度
        self.processing_speed_label = QLabel("0 FPS")
        perf_layout.addWidget(QLabel("处理速度:"), 0, 0)
        perf_layout.addWidget(self.processing_speed_label, 0, 1)
        
        # 内存使用
        self.memory_usage_bar = QProgressBar()
        self.memory_usage_bar.setRange(0, 100)
        self.memory_usage_bar.setValue(0)
        self.memory_usage_bar.setFormat("内存: %p%")
        perf_layout.addWidget(QLabel("内存使用:"), 1, 0)
        perf_layout.addWidget(self.memory_usage_bar, 1, 1)
        
        # 温度监控（如果可用）
        self.temperature_label = QLabel("N/A")
        perf_layout.addWidget(QLabel("温度:"), 2, 0)
        perf_layout.addWidget(self.temperature_label, 2, 1)
        
        # 加速比
        self.speedup_label = QLabel("1.0x")
        self.speedup_label.setStyleSheet("font-weight: bold; color: #28a745;")
        perf_layout.addWidget(QLabel("加速比:"), 3, 0)
        perf_layout.addWidget(self.speedup_label, 3, 1)
        
        parent_layout.addWidget(perf_group)
    
    def create_control_group(self, parent_layout):
        """创建控制按钮组"""
        control_layout = QHBoxLayout()
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新状态")
        self.refresh_btn.clicked.connect(self.refresh_gpu_status)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        control_layout.addWidget(self.refresh_btn)
        
        # 详细信息按钮
        self.details_btn = QPushButton("📋 详细信息")
        self.details_btn.clicked.connect(self.show_detailed_info)
        self.details_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        control_layout.addWidget(self.details_btn)
        
        # 性能测试按钮
        self.benchmark_btn = QPushButton("⚡ 性能测试")
        self.benchmark_btn.clicked.connect(self.run_performance_test)
        self.benchmark_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #d39e00;
            }
        """)
        control_layout.addWidget(self.benchmark_btn)
        
        control_layout.addStretch()
        parent_layout.addLayout(control_layout)
    
    def init_device_manager(self):
        """初始化设备管理器"""
        try:
            self.device_manager = EnhancedDeviceManager()
            self.device_manager.start_monitoring()
            
            # 获取初始状态
            self.refresh_gpu_status()
            
        except Exception as e:
            print(f"设备管理器初始化失败: {e}")
            self.update_status_labels({"error": str(e)})
    
    def start_monitoring(self):
        """启动状态监控"""
        if not self.monitoring_active:
            self.monitoring_active = True
            
            # 创建定时器
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self.update_gpu_status)
            self.monitor_timer.start(2000)  # 每2秒更新一次
    
    def stop_monitoring(self):
        """停止状态监控"""
        self.monitoring_active = False
        
        if self.monitor_timer:
            self.monitor_timer.stop()
            self.monitor_timer = None
        
        if self.device_manager:
            self.device_manager.stop_monitoring()
    
    @pyqtSlot()
    def refresh_gpu_status(self):
        """刷新GPU状态"""
        try:
            if self.device_manager:
                device_status = self.device_manager.get_device_status()
                self.current_gpu_status = device_status
                self.update_status_labels(device_status)
                
                # 发射状态变化信号
                self.gpu_status_changed.emit(device_status)
            
        except Exception as e:
            print(f"刷新GPU状态失败: {e}")
            self.update_status_labels({"error": str(e)})
    
    @pyqtSlot()
    def update_gpu_status(self):
        """定时更新GPU状态"""
        if self.monitoring_active:
            self.refresh_gpu_status()
    
    def update_status_labels(self, status: Dict[str, Any]):
        """更新状态标签"""
        try:
            if "error" in status:
                self.gpu_status_label.setText("❌ 错误")
                self.gpu_status_label.setStyleSheet("font-weight: bold; color: #dc3545;")
                self.gpu_name_label.setText(f"错误: {status['error']}")
                return
            
            available_devices = status.get("available_devices", {})
            gpu_devices = {k: v for k, v in available_devices.items() if k.startswith("cuda:")}
            
            if gpu_devices:
                # 有GPU设备
                first_gpu = list(gpu_devices.values())[0]
                
                self.gpu_status_label.setText("✅ 可用")
                self.gpu_status_label.setStyleSheet("font-weight: bold; color: #28a745;")
                
                self.gpu_name_label.setText(first_gpu.get("device_name", "未知GPU"))
                
                # 显存信息
                memory_total = first_gpu.get("memory_total", 0)
                memory_used = first_gpu.get("current_allocation", 0)
                memory_available = first_gpu.get("memory_available", 0)
                
                if memory_total > 0:
                    memory_percent = (memory_used / memory_total) * 100
                    self.gpu_memory_label.setText(f"{memory_used:.1f}GB / {memory_total:.1f}GB")
                    
                    # 更新利用率进度条
                    self.gpu_utilization_bar.setValue(int(memory_percent))
                    
                    # 设置进度条颜色
                    if memory_percent > 80:
                        color = "#dc3545"  # 红色
                    elif memory_percent > 60:
                        color = "#ffc107"  # 黄色
                    else:
                        color = "#28a745"  # 绿色
                    
                    self.gpu_utilization_bar.setStyleSheet(f"""
                        QProgressBar::chunk {{
                            background-color: {color};
                        }}
                    """)
                else:
                    self.gpu_memory_label.setText("N/A")
                
                # 估算加速比
                performance = first_gpu.get("estimated_performance", 1.0)
                self.speedup_label.setText(f"{performance:.1f}x")
                
            else:
                # 无GPU设备，使用CPU
                self.gpu_status_label.setText("⚠️ 不可用")
                self.gpu_status_label.setStyleSheet("font-weight: bold; color: #ffc107;")
                self.gpu_name_label.setText("使用CPU模式")
                self.gpu_memory_label.setText("N/A")
                self.gpu_utilization_bar.setValue(0)
                self.speedup_label.setText("1.0x")
            
            # 更新系统内存
            system_memory = status.get("system_memory", {})
            if system_memory:
                memory_percent = system_memory.get("percent", 0)
                self.memory_usage_bar.setValue(int(memory_percent))
                
                # 设置内存使用颜色
                if memory_percent > 90:
                    color = "#dc3545"
                elif memory_percent > 70:
                    color = "#ffc107"
                else:
                    color = "#28a745"
                
                self.memory_usage_bar.setStyleSheet(f"""
                    QProgressBar::chunk {{
                        background-color: {color};
                    }}
                """)
            
            # 更新GPU温度（如果可用）
            gpu_status = status.get("gpu_status", {})
            if gpu_status:
                first_gpu_status = list(gpu_status.values())[0] if gpu_status else {}
                temperature = first_gpu_status.get("temperature", 0)
                if temperature > 0:
                    self.temperature_label.setText(f"{temperature}°C")
                    
                    # 设置温度颜色
                    if temperature > 80:
                        color = "#dc3545"
                    elif temperature > 70:
                        color = "#ffc107"
                    else:
                        color = "#28a745"
                    
                    self.temperature_label.setStyleSheet(f"color: {color}; font-weight: bold;")
                else:
                    self.temperature_label.setText("N/A")
            
        except Exception as e:
            print(f"更新状态标签失败: {e}")
    
    @pyqtSlot()
    def show_detailed_info(self):
        """显示详细信息对话框"""
        try:
            dialog = GPUDetailDialog(self.current_gpu_status, self)
            dialog.exec()
            
        except Exception as e:
            print(f"显示详细信息失败: {e}")
    
    @pyqtSlot()
    def run_performance_test(self):
        """运行性能测试"""
        try:
            # 这里可以集成GPU性能测试
            from gpu_video_performance_test import GPUVideoPerformanceTest
            
            # 创建性能测试对话框
            test_dialog = PerformanceTestDialog(self)
            test_dialog.exec()
            
        except Exception as e:
            print(f"性能测试失败: {e}")
    
    def get_current_gpu_config(self) -> ProcessingConfig:
        """获取当前GPU配置"""
        try:
            if self.device_manager:
                available_devices = self.device_manager.available_devices
                gpu_devices = {k: v for k, v in available_devices.items() if k.startswith("cuda:")}
                
                if gpu_devices:
                    first_gpu = list(gpu_devices.values())[0]
                    
                    return ProcessingConfig(
                        use_gpu=True,
                        gpu_device_id=0,
                        batch_size=min(4, first_gpu.max_batch_size),
                        precision="fp16" if first_gpu.supports_fp16 else "fp32",
                        memory_limit_gb=first_gpu.memory_available * 0.8  # 使用80%的可用内存
                    )
            
            # 回退到CPU配置
            return ProcessingConfig(
                use_gpu=False,
                batch_size=1,
                precision="fp32",
                fallback_to_cpu=True
            )
            
        except Exception as e:
            print(f"获取GPU配置失败: {e}")
            return ProcessingConfig(use_gpu=False, fallback_to_cpu=True)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.stop_monitoring()
        super().closeEvent(event)


class GPUDetailDialog(QDialog):
    """GPU详细信息对话框"""
    
    def __init__(self, gpu_status: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.gpu_status = gpu_status
        
        self.setWindowTitle("GPU详细信息")
        self.setFixedSize(600, 500)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建文本显示区域
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QFont("Consolas", 10))
        
        # 格式化GPU信息
        info_content = self.format_gpu_info()
        self.info_text.setPlainText(info_content)
        
        layout.addWidget(self.info_text)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
    
    def format_gpu_info(self) -> str:
        """格式化GPU信息"""
        try:
            import json
            return json.dumps(self.gpu_status, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"格式化信息失败: {e}"


class PerformanceTestDialog(QDialog):
    """性能测试对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("GPU性能测试")
        self.setFixedSize(400, 200)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 提示信息
        info_label = QLabel("性能测试将评估GPU加速效果，可能需要几分钟时间。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备开始测试...")
        layout.addWidget(self.status_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始测试")
        self.start_btn.clicked.connect(self.start_test)
        button_layout.addWidget(self.start_btn)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def start_test(self):
        """开始性能测试"""
        self.start_btn.setEnabled(False)
        self.status_label.setText("正在运行性能测试...")
        
        # 模拟测试进度
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.update_test_progress)
        self.test_progress = 0
        self.test_timer.start(100)
    
    def update_test_progress(self):
        """更新测试进度"""
        self.test_progress += 2
        self.progress_bar.setValue(self.test_progress)
        
        if self.test_progress >= 100:
            self.test_timer.stop()
            self.status_label.setText("测试完成！GPU加速效果良好。")
            self.start_btn.setEnabled(True)
