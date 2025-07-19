#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应配置控制面板
提供用户界面来控制和监控自适应模型配置系统
"""

import sys
import time
import logging
from typing import Dict, Any, Optional

# 安全导入PyQt6
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QComboBox, QPushButton, QProgressBar,
        QGroupBox, QSlider, QSpinBox, QCheckBox,
        QTextEdit, QTabWidget, QFrame, QSplitter
    )
    from PyQt6.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot, Qt
    from PyQt6.QtGui import QFont, QPalette, QColor
    PYQT6_AVAILABLE = True
except ImportError as e:
    print(f"PyQt6导入失败: {e}")
    PYQT6_AVAILABLE = False
    # 创建模拟类以避免导入错误
    class QWidget: pass
    class QTimer: pass
    pyqtSignal = lambda *args: None

# 安全导入pyqtgraph
try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

# 导入自适应配置模块
try:
    from src.core.adaptive_model_config import AdaptiveModelConfigManager, ModelMode
    from src.core.resource_monitor import ResourceMonitor, AlertLevel
    from src.core.hardware_detector import PerformanceLevel
    ADAPTIVE_CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"导入自适应配置模块失败: {e}")
    ADAPTIVE_CONFIG_AVAILABLE = False


class ResourceMonitorWidget(QWidget):
    """资源监控显示组件"""

    def __init__(self):
        if not PYQT6_AVAILABLE:
            print("PyQt6不可用，ResourceMonitorWidget将不会正常工作")
            return
        super().__init__()
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 内存使用显示
        memory_group = QGroupBox("内存使用")
        memory_layout = QGridLayout()
        
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_label = QLabel("0.0GB / 0.0GB (0%)")
        
        memory_layout.addWidget(QLabel("内存:"), 0, 0)
        memory_layout.addWidget(self.memory_progress, 0, 1)
        memory_layout.addWidget(self.memory_label, 0, 2)
        memory_group.setLayout(memory_layout)
        
        # CPU使用显示
        cpu_group = QGroupBox("CPU使用")
        cpu_layout = QGridLayout()
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("0%")
        
        cpu_layout.addWidget(QLabel("CPU:"), 0, 0)
        cpu_layout.addWidget(self.cpu_progress, 0, 1)
        cpu_layout.addWidget(self.cpu_label, 0, 2)
        cpu_group.setLayout(cpu_layout)
        
        # GPU使用显示
        gpu_group = QGroupBox("GPU使用")
        gpu_layout = QGridLayout()
        
        self.gpu_progress = QProgressBar()
        self.gpu_progress.setRange(0, 100)
        self.gpu_label = QLabel("0% / 0.0GB")
        
        gpu_layout.addWidget(QLabel("GPU:"), 0, 0)
        gpu_layout.addWidget(self.gpu_progress, 0, 1)
        gpu_layout.addWidget(self.gpu_label, 0, 2)
        gpu_group.setLayout(gpu_layout)
        
        # 警告状态显示
        self.alert_label = QLabel("状态: 正常")
        self.alert_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        
        layout.addWidget(memory_group)
        layout.addWidget(cpu_group)
        layout.addWidget(gpu_group)
        layout.addWidget(self.alert_label)
        
        self.setLayout(layout)
    
    def setup_timer(self):
        """设置更新定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_resource_info)
        self.update_timer.start(5000)  # 每5秒更新一次
    
    def update_resource_info(self):
        """更新资源信息"""
        try:
            # 这里应该从资源监控器获取实际数据
            # 为演示目的，使用模拟数据
            import psutil
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used / (1024**3)
            memory_total = memory.total / (1024**3)
            
            self.memory_progress.setValue(int(memory_percent))
            self.memory_label.setText(f"{memory_used:.1f}GB / {memory_total:.1f}GB ({memory_percent:.1f}%)")
            
            # 设置内存进度条颜色
            if memory_percent > 85:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }")
                self.alert_label.setText("状态: 紧急 - 内存使用过高")
                self.alert_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            elif memory_percent > 70:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
                self.alert_label.setText("状态: 警告 - 内存使用较高")
                self.alert_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
            else:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: green; }")
                self.alert_label.setText("状态: 正常")
                self.alert_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            
            # GPU信息（模拟）
            self.gpu_progress.setValue(0)
            self.gpu_label.setText("无GPU或未检测到")
            
        except Exception as e:
            print(f"更新资源信息失败: {e}")


class PerformanceModeSelector(QWidget):
    """性能模式选择器"""
    
    mode_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 模式选择
        mode_group = QGroupBox("性能模式")
        mode_layout = QGridLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "自动模式 - 根据硬件自动优化",
            "性能优先 - 最佳生成质量",
            "内存优先 - 最小内存使用",
            "自定义模式 - 手动配置"
        ])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        
        mode_layout.addWidget(QLabel("运行模式:"), 0, 0)
        mode_layout.addWidget(self.mode_combo, 0, 1)
        mode_group.setLayout(mode_layout)
        
        # 当前配置显示
        config_group = QGroupBox("当前配置")
        config_layout = QGridLayout()
        
        self.quantization_label = QLabel("量化等级: Q4_K_M")
        self.memory_limit_label = QLabel("内存限制: 2.8GB")
        self.concurrent_label = QLabel("并发模型: 否")
        self.bleu_score_label = QLabel("预期BLEU: 0.75")
        
        config_layout.addWidget(self.quantization_label, 0, 0)
        config_layout.addWidget(self.memory_limit_label, 0, 1)
        config_layout.addWidget(self.concurrent_label, 1, 0)
        config_layout.addWidget(self.bleu_score_label, 1, 1)
        config_group.setLayout(config_layout)
        
        # 应用按钮
        self.apply_button = QPushButton("应用配置")
        self.apply_button.clicked.connect(self.apply_configuration)
        
        layout.addWidget(mode_group)
        layout.addWidget(config_group)
        layout.addWidget(self.apply_button)
        
        self.setLayout(layout)
    
    def on_mode_changed(self, text: str):
        """模式改变处理"""
        mode = text.split(" - ")[0]
        self.mode_changed.emit(mode)
        
        # 更新配置显示（模拟）
        if "自动模式" in text:
            self.quantization_label.setText("量化等级: 自动选择")
            self.memory_limit_label.setText("内存限制: 自动调整")
            self.concurrent_label.setText("并发模型: 自动决定")
            self.bleu_score_label.setText("预期BLEU: 0.70-0.78")
        elif "性能优先" in text:
            self.quantization_label.setText("量化等级: Q5_K")
            self.memory_limit_label.setText("内存限制: 4.0GB")
            self.concurrent_label.setText("并发模型: 是")
            self.bleu_score_label.setText("预期BLEU: 0.78")
        elif "内存优先" in text:
            self.quantization_label.setText("量化等级: Q2_K")
            self.memory_limit_label.setText("内存限制: 1.5GB")
            self.concurrent_label.setText("并发模型: 否")
            self.bleu_score_label.setText("预期BLEU: 0.68")
    
    def apply_configuration(self):
        """应用配置"""
        try:
            # 这里应该调用配置管理器应用新配置
            print("应用新配置...")
            self.apply_button.setText("配置已应用")
            QTimer.singleShot(2000, lambda: self.apply_button.setText("应用配置"))
        except Exception as e:
            print(f"应用配置失败: {e}")


class AdvancedSettingsWidget(QWidget):
    """高级设置组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 量化设置
        quant_group = QGroupBox("量化设置")
        quant_layout = QGridLayout()
        
        self.quant_combo = QComboBox()
        self.quant_combo.addItems(["Q2_K", "Q4_K_M", "Q5_K", "FP16", "FP32"])
        
        quant_layout.addWidget(QLabel("量化等级:"), 0, 0)
        quant_layout.addWidget(self.quant_combo, 0, 1)
        quant_group.setLayout(quant_layout)
        
        # 内存设置
        memory_group = QGroupBox("内存设置")
        memory_layout = QGridLayout()
        
        self.memory_slider = QSlider()
        self.memory_slider.setOrientation(1)  # 水平
        self.memory_slider.setRange(1, 8)
        self.memory_slider.setValue(3)
        self.memory_slider.valueChanged.connect(self.update_memory_label)
        
        self.memory_value_label = QLabel("3.0GB")
        
        memory_layout.addWidget(QLabel("最大内存:"), 0, 0)
        memory_layout.addWidget(self.memory_slider, 0, 1)
        memory_layout.addWidget(self.memory_value_label, 0, 2)
        memory_group.setLayout(memory_layout)
        
        # 线程设置
        thread_group = QGroupBox("线程设置")
        thread_layout = QGridLayout()
        
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setRange(1, 16)
        self.thread_spinbox.setValue(4)
        
        thread_layout.addWidget(QLabel("线程数:"), 0, 0)
        thread_layout.addWidget(self.thread_spinbox, 0, 1)
        thread_group.setLayout(thread_layout)
        
        # GPU设置
        gpu_group = QGroupBox("GPU设置")
        gpu_layout = QGridLayout()
        
        self.use_gpu_checkbox = QCheckBox("启用GPU加速")
        self.gpu_layers_spinbox = QSpinBox()
        self.gpu_layers_spinbox.setRange(0, 40)
        self.gpu_layers_spinbox.setValue(20)
        
        gpu_layout.addWidget(self.use_gpu_checkbox, 0, 0)
        gpu_layout.addWidget(QLabel("GPU层数:"), 1, 0)
        gpu_layout.addWidget(self.gpu_layers_spinbox, 1, 1)
        gpu_group.setLayout(gpu_layout)
        
        layout.addWidget(quant_group)
        layout.addWidget(memory_group)
        layout.addWidget(thread_group)
        layout.addWidget(gpu_group)
        
        self.setLayout(layout)
    
    def update_memory_label(self, value):
        """更新内存标签"""
        self.memory_value_label.setText(f"{value}.0GB")


class AdaptiveConfigPanel(QWidget):
    """自适应配置主面板"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.resource_monitor = None
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 资源监控标签页
        self.resource_tab = ResourceMonitorWidget()
        self.tab_widget.addTab(self.resource_tab, "资源监控")
        
        # 性能模式标签页
        self.mode_tab = PerformanceModeSelector()
        self.tab_widget.addTab(self.mode_tab, "性能模式")
        
        # 高级设置标签页
        self.advanced_tab = AdvancedSettingsWidget()
        self.tab_widget.addTab(self.advanced_tab, "高级设置")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
        # 设置窗口属性
        self.setWindowTitle("自适应配置控制面板")
        self.resize(600, 400)
    
    def setup_connections(self):
        """设置信号连接"""
        try:
            # 初始化配置管理器
            self.config_manager = AdaptiveModelConfigManager()
            
            # 初始化资源监控器
            self.resource_monitor = ResourceMonitor()
            
            # 连接信号
            self.mode_tab.mode_changed.connect(self.on_mode_changed)
            
        except Exception as e:
            print(f"设置连接失败: {e}")
    
    def on_mode_changed(self, mode: str):
        """处理模式改变"""
        try:
            if self.config_manager:
                # 这里应该调用配置管理器切换模式
                print(f"切换到模式: {mode}")
        except Exception as e:
            print(f"模式切换失败: {e}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    panel = AdaptiveConfigPanel()
    panel.show()
    sys.exit(app.exec())
