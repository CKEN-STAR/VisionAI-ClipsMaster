#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 硬件配置与兼容性标签页

为UI提供硬件检测、兼容性测试和优化建议功能。
"""

import os
import sys
import time
import threading
from typing import Dict, List, Any, Callable
from pathlib import Path

# 确保项目根目录在系统路径中
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# 导入PyQt5组件
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QProgressBar, QTabWidget, 
                           QTextEdit, QComboBox, QCheckBox, QGroupBox,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QSpacerItem, QSizePolicy, QFrame, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap

# 导入设备管理器
try:
    from src.utils.device_manager import device_manager
except ImportError:
    # 如果设备管理器导入失败，显示占位组件
    device_manager = None

class ResourceMonitorWidget(QWidget):
    """资源监控小部件，显示CPU、内存和GPU使用情况"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitoring = False
        self.timer = None
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("系统资源监控")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 创建CPU资源监控
        cpu_group = QGroupBox("CPU使用率")
        cpu_layout = QVBoxLayout(cpu_group)
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setValue(0)
        self.cpu_bar.setFormat("%p%")
        self.cpu_bar.setAlignment(Qt.AlignCenter)
        cpu_layout.addWidget(self.cpu_bar)
        layout.addWidget(cpu_group)
        
        # 创建内存监控
        memory_group = QGroupBox("内存使用率")
        memory_layout = QVBoxLayout(memory_group)
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setValue(0)
        self.memory_bar.setFormat("%p%")
        self.memory_bar.setAlignment(Qt.AlignCenter)
        memory_layout.addWidget(self.memory_bar)
        layout.addWidget(memory_group)
        
        # 创建GPU监控（如果可用）
        self.gpu_group = QGroupBox("GPU使用率")
        gpu_layout = QVBoxLayout(self.gpu_group)
        self.gpu_bar = QProgressBar()
        self.gpu_bar.setRange(0, 100)
        self.gpu_bar.setValue(0)
        self.gpu_bar.setFormat("%p%")
        self.gpu_bar.setAlignment(Qt.AlignCenter)
        gpu_layout.addWidget(self.gpu_bar)
        
        # 默认隐藏GPU监控，只有在检测到GPU时才显示
        layout.addWidget(self.gpu_group)
        self.gpu_group.setVisible(False)
        
        # 创建控制按钮
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("开始监控")
        self.stop_button = QPushButton("停止监控")
        self.stop_button.setEnabled(False)
        
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        layout.addLayout(control_layout)
        
        # 设置小部件尺寸策略
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
    
    def start_monitoring(self):
        """开始监控系统资源"""
        if not device_manager:
            return
            
        # 启动设备管理器的监控
        device_manager.start_monitoring(interval=1.0)
        
        # 更新UI状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 创建定时器，每秒更新一次UI
        self.monitoring = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_monitors)
        self.timer.start(1000)  # 1000毫秒 = 1秒
        
        # 检查是否有GPU
        self.check_for_gpu()
    
    def stop_monitoring(self):
        """停止监控系统资源"""
        if not device_manager:
            return
            
        # 停止设备管理器的监控
        device_manager.stop_monitoring()
        
        # 更新UI状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # 停止定时器
        self.monitoring = False
        if self.timer:
            self.timer.stop()
    
    def update_monitors(self):
        """更新监控数据"""
        if not device_manager or not self.monitoring:
            return
            
        # 获取当前资源使用情况
        usage = device_manager.get_current_usage()
        
        # 更新CPU使用率
        self.cpu_bar.setValue(int(usage["cpu"]))
        if usage["cpu"] > 90:
            self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #FF5252; }")
        elif usage["cpu"] > 70:
            self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
        else:
            self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
            
        # 更新内存使用率
        self.memory_bar.setValue(int(usage["memory"]))
        if usage["memory"] > 90:
            self.memory_bar.setStyleSheet("QProgressBar::chunk { background-color: #FF5252; }")
        elif usage["memory"] > 70:
            self.memory_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
        else:
            self.memory_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
            
        # 更新GPU使用率（如果可用）
        if self.gpu_group.isVisible():
            self.gpu_bar.setValue(int(usage["gpu"]))
            if usage["gpu"] > 90:
                self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #FF5252; }")
            elif usage["gpu"] > 70:
                self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
            else:
                self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
    
    def check_for_gpu(self):
        """检查是否有GPU可用"""
        if not device_manager:
            return
            
        # 检查设备管理器中是否有GPU
        if device_manager.is_gpu_available and device_manager.use_gpu:
            self.gpu_group.setVisible(True)
        else:
            self.gpu_group.setVisible(False)

class GPUTestThread(QThread):
    """执行GPU测试的后台线程"""
    
    # 信号定义
    test_progress = pyqtSignal(str, int)  # 测试进度信息
    test_completed = pyqtSignal(dict)     # 测试完成，返回结果
    test_error = pyqtSignal(str)          # 测试错误信息
    
    def __init__(self, full_test=False):
        super().__init__()
        self.full_test = full_test
    
    def run(self):
        """执行测试"""
        try:
            if not device_manager:
                self.test_error.emit("设备管理器未初始化")
                return
                
            # 发送进度信号
            self.test_progress.emit("正在检测设备硬件...", 10)
            time.sleep(0.5)
            
            # 初始化设备管理器（如果尚未初始化）
            if not device_manager.is_initialized:
                self.test_progress.emit("初始化设备管理器...", 20)
                device_manager.initialize()
            
            # 发送进度信号
            self.test_progress.emit("检测GPU设备...", 30)
            time.sleep(0.5)
            
            # 如果是完整测试，执行压力测试
            if self.full_test:
                self.test_progress.emit("准备GPU压力测试...", 50)
                time.sleep(0.5)
                
                self.test_progress.emit("执行GPU压力测试...", 60)
                # 实际执行测试
                result = device_manager.run_compatibility_test(full_test=True)
                
                self.test_progress.emit("分析测试结果...", 90)
                time.sleep(0.5)
            else:
                # 简单测试
                self.test_progress.emit("检测GPU兼容性...", 60)
                result = device_manager.run_compatibility_test(full_test=False)
            
            # 测试完成
            self.test_progress.emit("测试完成", 100)
            time.sleep(0.5)
            
            # 发送结果
            self.test_completed.emit(result)
        
        except Exception as e:
            self.test_error.emit(f"测试过程中出错: {str(e)}")

class HardwareTabWidget(QWidget):
    """硬件标签页，显示系统硬件信息和提供兼容性测试"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化界面
        self.init_ui()
        
        # 初始化设备管理器
        self.init_device_manager()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板 - 硬件信息
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 硬件信息标题
        title_label = QLabel("硬件信息")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)
        
        # 创建硬件信息表格
        self.hw_table = QTableWidget()
        self.hw_table.setColumnCount(2)
        self.hw_table.setHorizontalHeaderLabels(["组件", "信息"])
        self.hw_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.hw_table.verticalHeader().setVisible(False)
        left_layout.addWidget(self.hw_table)
        
        # 创建测试按钮
        test_buttons_layout = QHBoxLayout()
        self.detect_button = QPushButton("检测系统硬件")
        self.full_test_button = QPushButton("执行完整硬件测试")
        
        self.detect_button.clicked.connect(self.run_basic_detection)
        self.full_test_button.clicked.connect(self.run_full_test)
        
        test_buttons_layout.addWidget(self.detect_button)
        test_buttons_layout.addWidget(self.full_test_button)
        left_layout.addLayout(test_buttons_layout)
        
        # 添加测试进度条
        self.progress_group = QGroupBox("测试进度")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        left_layout.addWidget(self.progress_group)
        
        # 右侧面板 - 资源监控和优化建议
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 创建资源监控组件
        self.resource_monitor = ResourceMonitorWidget()
        right_layout.addWidget(self.resource_monitor)
        
        # 优化建议组
        optimization_group = QGroupBox("优化建议")
        optimization_layout = QVBoxLayout(optimization_group)
        
        self.optimization_text = QTextEdit()
        self.optimization_text.setReadOnly(True)
        self.optimization_text.setMinimumHeight(150)
        optimization_layout.addWidget(self.optimization_text)
        
        right_layout.addWidget(optimization_group)
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置初始分割比例
        splitter.setSizes([500, 300])
        
        # 创建测试线程
        self.test_thread = None
    
    def init_device_manager(self):
        """初始化设备管理器并加载初始硬件信息"""
        if not device_manager:
            self.show_error("无法初始化设备管理器，硬件信息不可用")
            return
            
        try:
            # 初始化设备管理器
            info = device_manager.initialize()
            
            # 显示初始硬件信息
            self.display_hardware_info(info)
            
            # 显示初始优化建议
            self.display_optimization_advice(info)
            
        except Exception as e:
            self.show_error(f"初始化设备管理器失败: {str(e)}")
    
    def display_hardware_info(self, info: Dict[str, Any]):
        """显示硬件信息"""
        self.hw_table.setRowCount(0)  # 清空现有行
        
        # 添加CPU信息
        cpu_info = info.get("cpu", {})
        self.add_table_row("CPU型号", cpu_info.get("model", "未知"))
        self.add_table_row("CPU核心数", str(cpu_info.get("cores", 0)))
        
        if "threads" in cpu_info:
            self.add_table_row("CPU线程数", str(cpu_info.get("threads", 0)))
        
        # 添加内存信息
        memory_info = info.get("memory", {})
        self.add_table_row("内存总量", f"{memory_info.get('total_gb', 0):.2f} GB")
        self.add_table_row("可用内存", f"{memory_info.get('available_gb', 0):.2f} GB")
        
        # 添加GPU信息
        if info.get("is_gpu_available", False):
            # 获取GPU摘要
            gpu_info = info.get("gpu", {})
            summary = gpu_info.get("summary", {})
            
            self.add_table_row("GPU可用", "是")
            self.add_table_row("最佳GPU API", summary.get("best_api", "未知"))
            
            # 添加各种类型GPU的详细信息
            for gpu_type in ["nvidia", "amd", "intel", "apple", "external"]:
                if gpu_type in gpu_info:
                    type_info = gpu_info[gpu_type]
                    if type_info.get("available", False):
                        count = type_info.get("count", 0)
                        
                        # 显示GPU名称
                        if "names" in type_info and type_info["names"]:
                            for i, name in enumerate(type_info["names"]):
                                if i == 0:
                                    # 第一个GPU显示类型
                                    self.add_table_row(f"{gpu_type.upper()} GPU", name)
                                else:
                                    # 其他GPU只显示名称
                                    self.add_table_row("", name)
                                
                                # 显示显存（如果有）
                                if "memory" in type_info and i < len(type_info["memory"]):
                                    memory = type_info["memory"][i]
                                    self.add_table_row("显存", f"{memory:.2f} GB")
        else:
            self.add_table_row("GPU可用", "否")
            self.add_table_row("运行模式", "CPU模式")
    
    def add_table_row(self, key: str, value: str):
        """添加一行到表格"""
        row_position = self.hw_table.rowCount()
        self.hw_table.insertRow(row_position)
        
        # 添加键和值
        key_item = QTableWidgetItem(key)
        value_item = QTableWidgetItem(value)
        
        # 设置为不可编辑
        key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
        value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
        
        # 添加到表格
        self.hw_table.setItem(row_position, 0, key_item)
        self.hw_table.setItem(row_position, 1, value_item)
    
    def display_optimization_advice(self, info: Dict[str, Any]):
        """显示优化建议"""
        if not info:
            return
            
        advice_text = ""
        
        # 基于GPU可用性的建议
        if info.get("is_gpu_available", False):
            advice_text += "## GPU加速已启用\n\n"
            
            # 获取GPU信息
            gpu_info = info.get("gpu", {})
            summary = gpu_info.get("summary", {})
            
            # 检查推荐的训练和推理能力
            if summary.get("recommended_for_training", False):
                advice_text += "✓ 您的设备适合训练和推理任务\n\n"
            else:
                advice_text += "✓ 您的设备适合推理任务\n"
                advice_text += "⚠ 但可能不适合大规模训练，建议仅进行少量微调\n\n"
                
            # 根据兼容性给出模型建议
            compatibility = info.get("compatibility", {})
            model_compatibility = compatibility.get("model_compatibility", {})
            
            # 中文模型建议
            if "qwen" in model_compatibility:
                qwen_compat = model_compatibility["qwen"]
                advice_text += f"### 中文模型 (Qwen2.5-7B):\n"
                advice_text += f"- 推荐量化: {qwen_compat.get('recommended_quantization', 'Q4_K_M')}\n"
                for note in qwen_compat.get("notes", []):
                    advice_text += f"- {note}\n"
                advice_text += "\n"
                
            # 英文模型建议
            if "mistral" in model_compatibility:
                mistral_compat = model_compatibility["mistral"]
                advice_text += f"### 英文模型 (Mistral-7B):\n"
                advice_text += f"- 推荐量化: {mistral_compat.get('recommended_quantization', 'Q4_K_M')}\n"
                for note in mistral_compat.get("notes", []):
                    advice_text += f"- {note}\n"
                advice_text += "\n"
        else:
            advice_text += "## CPU模式运行\n\n"
            advice_text += "⚠ 未检测到可用的GPU设备，系统将使用CPU模式运行\n\n"
            advice_text += "### 优化建议:\n"
            advice_text += "- 使用高度量化的模型 (Q2_K) 减少内存占用\n"
            advice_text += "- 减小批处理大小和上下文长度\n"
            advice_text += "- 处理较低分辨率的视频\n"
            advice_text += "- 避免同时运行多个资源密集型任务\n\n"
        
        # 内存建议
        memory_info = info.get("memory", {})
        available_gb = memory_info.get("available_gb", 0)
        total_gb = memory_info.get("total_gb", 0)
        
        advice_text += "### 内存建议:\n"
        if available_gb < 4.0:
            advice_text += f"⚠ 可用内存较低 ({available_gb:.2f}GB), 建议:\n"
            advice_text += "- 关闭其他内存占用较大的应用\n"
            advice_text += "- 使用高度量化的模型\n"
            advice_text += "- 处理较小的视频文件\n"
        else:
            advice_text += f"✓ 可用内存充足 ({available_gb:.2f}GB/{total_gb:.2f}GB)\n"
        
        # 设置文本
        self.optimization_text.setMarkdown(advice_text)
    
    def run_basic_detection(self):
        """运行基本硬件检测"""
        if self.test_thread and self.test_thread.isRunning():
            return
            
        # 创建并启动测试线程
        self.test_thread = GPUTestThread(full_test=False)
        self.connect_test_signals()
        self.test_thread.start()
    
    def run_full_test(self):
        """运行完整硬件测试（包括GPU压力测试）"""
        if self.test_thread and self.test_thread.isRunning():
            return
            
        # 创建并启动测试线程
        self.test_thread = GPUTestThread(full_test=True)
        self.connect_test_signals()
        self.test_thread.start()
    
    def connect_test_signals(self):
        """连接测试线程的信号"""
        if not self.test_thread:
            return
            
        # 连接进度信号
        self.test_thread.test_progress.connect(self.update_test_progress)
        
        # 连接完成和错误信号
        self.test_thread.test_completed.connect(self.handle_test_complete)
        self.test_thread.test_error.connect(self.show_error)
    
    @pyqtSlot(str, int)
    def update_test_progress(self, message: str, progress: int):
        """更新测试进度"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
    
    @pyqtSlot(dict)
    def handle_test_complete(self, result: Dict[str, Any]):
        """处理测试完成"""
        if not result.get("success", False):
            self.show_error(result.get("message", "测试失败，未知错误"))
            return
            
        # 更新硬件信息显示
        is_gpu_available = result.get("is_gpu_available", False)
        gpu_info = result.get("gpu_info", {})
        
        # 构建完整的信息对象
        info = {
            "is_gpu_available": is_gpu_available,
            "gpu": gpu_info,
            "compatibility": result.get("compatibility", {})
        }
        
        # 如果设备管理器有效，添加CPU和内存信息
        if device_manager and device_manager.is_initialized:
            info["cpu"] = device_manager.cpu_info
            info["memory"] = device_manager.memory_info
        
        # 更新显示
        self.display_hardware_info(info)
        self.display_optimization_advice(info)
        
        # 如果有压力测试结果，显示详细信息
        if "stress_test" in result:
            stress_result = result["stress_test"]
            if stress_result.get("success", False):
                # 构建压力测试结果文本
                stress_text = "## GPU压力测试结果\n\n"
                stress_text += f"- API: {stress_result.get('api', 'Unknown')}\n"
                stress_text += f"- 迭代次数: {stress_result.get('total_iterations', 0)}\n"
                stress_text += f"- 每秒迭代: {stress_result.get('iterations_per_second', 0):.2f}\n"
                stress_text += f"- 平均计算时间: {stress_result.get('avg_computation_time', 0)*1000:.2f}ms\n"
                
                if "max_memory_used_gb" in stress_result and stress_result["max_memory_used_gb"] > 0:
                    stress_text += f"- 最大显存使用: {stress_result['max_memory_used_gb']:.2f} GB\n"
                    
                # 添加到优化建议文本
                current_text = self.optimization_text.toMarkdown()
                self.optimization_text.setMarkdown(current_text + "\n\n" + stress_text)
    
    def show_error(self, message: str):
        """显示错误信息"""
        self.progress_label.setText(f"错误: {message}")
        self.progress_bar.setValue(0)
        
        # 设置错误样式
        self.progress_label.setStyleSheet("color: red;")
        
        # 3秒后重置样式
        QTimer.singleShot(3000, self.reset_error_style)
    
    def reset_error_style(self):
        """重置错误样式"""
        self.progress_label.setStyleSheet("")
        self.progress_label.setText("准备就绪")

# 独立运行此模块进行测试
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = HardwareTabWidget()
    window.setWindowTitle("硬件兼容性测试")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_()) 