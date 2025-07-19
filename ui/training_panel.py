
# 安全导入包装 - 自动生成
import sys
import os

# 确保PyQt6可用
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    print(f"[WARN] PyQt6不可用，TrainingPanel将使用fallback模式")

# 线程安全检查
def ensure_main_thread():
    """确保在主线程中执行"""
    if QT_AVAILABLE and QApplication.instance():
        current_thread = QThread.currentThread()
        main_thread = QApplication.instance().thread()
        if current_thread != main_thread:
            print(f"[WARN] TrainingPanel不在主线程中，可能导致问题")
            return False
    return True

"""
训练面板组件
提供模型训练的可视化界面和实时监控功能
"""

import time
import threading
from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QGroupBox, QGridLayout, QComboBox,
    QSpinBox, QCheckBox, QFileDialog, QListWidget, QSplitter,
    QTabWidget, QFrame
)
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

try:
    from ui.components.alert_manager import AlertManager, AlertLevel
    from ui.progress.tracker import ProgressTracker
    HAS_ALERT_MANAGER = True
except ImportError:
    HAS_ALERT_MANAGER = False
    print("[WARN] Alert manager not available, using fallback")

class TrainingWorker(QObject):
    """训练工作线程"""
    
    progress_updated = pyqtSignal(int)  # 进度更新
    status_updated = pyqtSignal(str)    # 状态更新
    loss_updated = pyqtSignal(float)    # Loss值更新
    training_completed = pyqtSignal(dict)  # 训练完成
    training_failed = pyqtSignal(str)   # 训练失败
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.is_running = False
        self.should_stop = False
    
    def start_training(self):
        """开始训练"""
        self.is_running = True
        self.should_stop = False
        
        try:
            # 模拟训练过程
            total_epochs = self.config.get('epochs', 10)
            
            for epoch in range(total_epochs):
                if self.should_stop:
                    break
                
                # 更新状态
                self.status_updated.emit(f"训练第 {epoch + 1}/{total_epochs} 轮")
                
                # 模拟训练步骤
                for step in range(100):
                    if self.should_stop:
                        break
                    
                    # 计算进度
                    progress = int(((epoch * 100 + step) / (total_epochs * 100)) * 100)
                    self.progress_updated.emit(progress)
                    
                    # 模拟Loss值变化
                    loss = 2.0 * (1 - progress / 100) + 0.1
                    self.loss_updated.emit(loss)
                    
                    # 模拟训练时间
                    time.sleep(0.05)
            
            if not self.should_stop:
                # 训练完成
                result = {
                    'status': 'completed',
                    'final_loss': 0.1,
                    'epochs': total_epochs,
                    'language': self.config.get('language', 'zh')
                }
                self.training_completed.emit(result)
            
        except Exception as e:
            self.training_failed.emit(str(e))
        finally:
            self.is_running = False
    
    def stop_training(self):
        """停止训练"""
        self.should_stop = True

class TrainingPanel(QWidget):
    """训练面板主组件"""
    
    # 信号定义
    training_started = pyqtSignal()
    training_stopped = pyqtSignal()
    training_completed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.training_worker = None
        self.training_thread = None
        self.loss_history = []
        self.start_time = None
        
        # 初始化Alert Manager
        if HAS_ALERT_MANAGER:
            self.alert_manager = AlertManager(self)
        else:
            self.alert_manager = None
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 训练配置页
        self.config_tab = self._create_config_tab()
        self.tabs.addTab(self.config_tab, "训练配置")
        
        # 训练监控页
        self.monitor_tab = self._create_monitor_tab()
        self.tabs.addTab(self.monitor_tab, "训练监控")
        
        # 训练历史页
        self.history_tab = self._create_history_tab()
        self.tabs.addTab(self.history_tab, "训练历史")
    
    def _create_config_tab(self) -> QWidget:
        """创建训练配置页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 数据配置组
        data_group = QGroupBox("训练数据配置")
        data_layout = QGridLayout(data_group)
        
        # 语言选择
        data_layout.addWidget(QLabel("语言模式:"), 0, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文 (Qwen2.5-7B)", "英文 (Mistral-7B)"])
        data_layout.addWidget(self.language_combo, 0, 1)
        
        # 训练轮数
        data_layout.addWidget(QLabel("训练轮数:"), 1, 0)
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 100)
        self.epochs_spin.setValue(10)
        data_layout.addWidget(self.epochs_spin, 1, 1)
        
        # 批次大小
        data_layout.addWidget(QLabel("批次大小:"), 2, 0)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        self.batch_size_spin.setValue(4)
        data_layout.addWidget(self.batch_size_spin, 2, 1)
        
        # GPU使用
        self.use_gpu_check = QCheckBox("使用GPU加速")
        data_layout.addWidget(self.use_gpu_check, 3, 0, 1, 2)
        
        layout.addWidget(data_group)
        
        # 数据文件选择
        files_group = QGroupBox("训练文件")
        files_layout = QVBoxLayout(files_group)
        
        # 原片字幕文件列表
        files_layout.addWidget(QLabel("原片字幕文件:"))
        self.original_files_list = QListWidget()
        files_layout.addWidget(self.original_files_list)
        
        # 添加文件按钮
        add_files_btn = QPushButton("添加原片字幕文件")
        add_files_btn.clicked.connect(self.add_original_files)
        files_layout.addWidget(add_files_btn)
        
        # 爆款字幕文件
        files_layout.addWidget(QLabel("爆款字幕文件:"))
        self.viral_file_label = QLabel("未选择文件")
        files_layout.addWidget(self.viral_file_label)
        
        select_viral_btn = QPushButton("选择爆款字幕文件")
        select_viral_btn.clicked.connect(self.select_viral_file)
        files_layout.addWidget(select_viral_btn)
        
        layout.addWidget(files_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始训练")
        self.start_btn.clicked.connect(self.start_training)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止训练")
        self.stop_btn.clicked.connect(self.stop_training)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        return tab
    
    def _create_monitor_tab(self) -> QWidget:
        """创建训练监控页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 状态信息
        status_group = QGroupBox("训练状态")
        status_layout = QGridLayout(status_group)
        
        # 当前状态
        status_layout.addWidget(QLabel("状态:"), 0, 0)
        self.status_label = QLabel("未开始")
        status_layout.addWidget(self.status_label, 0, 1)
        
        # 进度条
        status_layout.addWidget(QLabel("进度:"), 1, 0)
        self.progress_bar = QProgressBar()
        status_layout.addWidget(self.progress_bar, 1, 1)
        
        # 当前Loss
        status_layout.addWidget(QLabel("当前Loss:"), 2, 0)
        self.loss_label = QLabel("0.000")
        status_layout.addWidget(self.loss_label, 2, 1)
        
        # 训练时间
        status_layout.addWidget(QLabel("训练时间:"), 3, 0)
        self.time_label = QLabel("00:00:00")
        status_layout.addWidget(self.time_label, 3, 1)
        
        layout.addWidget(status_group)
        
        # 训练日志
        log_group = QGroupBox("训练日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        return tab
    
    def _create_history_tab(self) -> QWidget:
        """创建训练历史页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 历史记录列表
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)
        
        # 清除历史按钮
        clear_btn = QPushButton("清除历史记录")
        clear_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_btn)
        
        return tab
    
    def setup_connections(self):
        """设置信号连接"""
        # 定时器用于更新训练时间
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_training_time)
    
    def add_original_files(self):
        """添加原片字幕文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择原片字幕文件", "", "SRT文件 (*.srt);;所有文件 (*)"
        )
        
        for file in files:
            self.original_files_list.addItem(file)
        
        if files and self.alert_manager:
            self.alert_manager.show_info(f"已添加 {len(files)} 个字幕文件")
    
    def select_viral_file(self):
        """选择爆款字幕文件"""
        file, _ = QFileDialog.getOpenFileName(
            self, "选择爆款字幕文件", "", "SRT文件 (*.srt);;所有文件 (*)"
        )
        
        if file:
            self.viral_file_label.setText(file)
            if self.alert_manager:
                self.alert_manager.show_info("爆款字幕文件已选择")
    
    def start_training(self):
        """开始训练"""
        # 验证配置
        if self.original_files_list.count() == 0:
            if self.alert_manager:
                self.alert_manager.show_error("请先添加原片字幕文件")
            return
        
        if self.viral_file_label.text() == "未选择文件":
            if self.alert_manager:
                self.alert_manager.show_error("请选择爆款字幕文件")
            return
        
        # 准备训练配置
        config = {
            'language': 'zh' if '中文' in self.language_combo.currentText() else 'en',
            'epochs': self.epochs_spin.value(),
            'batch_size': self.batch_size_spin.value(),
            'use_gpu': self.use_gpu_check.isChecked(),
            'original_files': [self.original_files_list.item(i).text() 
                             for i in range(self.original_files_list.count())],
            'viral_file': self.viral_file_label.text()
        }
        
        # 创建训练工作线程
        self.training_worker = TrainingWorker(config)
        self.training_thread = QThread()
        self.training_worker.moveToThread(self.training_thread)
        
        # 连接信号
        self.training_thread.started.connect(self.training_worker.start_training)
        self.training_worker.progress_updated.connect(self.update_progress)
        self.training_worker.status_updated.connect(self.update_status)
        self.training_worker.loss_updated.connect(self.update_loss)
        self.training_worker.training_completed.connect(self.on_training_completed)
        self.training_worker.training_failed.connect(self.on_training_failed)
        
        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.start_time = time.time()
        self.timer.start(1000)  # 每秒更新一次时间
        
        # 开始训练
        self.training_thread.start()
        self.training_started.emit()
        
        self.log_message("训练开始...")
        if self.alert_manager:
            self.alert_manager.show_info("训练已开始")
    
    def stop_training(self):
        """停止训练"""
        if self.training_worker:
            self.training_worker.stop_training()
        
        self.reset_ui_state()
        self.log_message("训练已停止")
        if self.alert_manager:
            self.alert_manager.show_warning("训练已被用户停止")
    
    def update_progress(self, progress: int):
        """更新进度"""
        self.progress_bar.setValue(progress)
    
    def update_status(self, status: str):
        """更新状态"""
        self.status_label.setText(status)
        self.log_message(status)
    
    def update_loss(self, loss: float):
        """更新Loss值"""
        self.loss_label.setText(f"{loss:.3f}")
        self.loss_history.append(loss)
    
    def update_training_time(self):
        """更新训练时间"""
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def on_training_completed(self, result: Dict[str, Any]):
        """训练完成处理"""
        self.reset_ui_state()
        self.log_message(f"训练完成！最终Loss: {result.get('final_loss', 0):.3f}")
        
        # 添加到历史记录
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        history_item = f"{timestamp} - {result.get('language', 'zh')} - Loss: {result.get('final_loss', 0):.3f}"
        self.history_list.addItem(history_item)
        
        self.training_completed.emit(result)
        
        if self.alert_manager:
            self.alert_manager.show_success("训练成功完成！")
    
    def on_training_failed(self, error: str):
        """训练失败处理"""
        self.reset_ui_state()
        self.log_message(f"训练失败: {error}")
        
        if self.alert_manager:
            self.alert_manager.show_error(f"训练失败: {error}")
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.timer.stop()
        self.training_stopped.emit()
        
        if self.training_thread and self.training_thread.isRunning():
            self.training_thread.quit()
            self.training_thread.wait()
    
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_history(self):
        """清除历史记录"""
        self.history_list.clear()
        if self.alert_manager:
            self.alert_manager.show_info("历史记录已清除")

# 全局实例
_training_panel = None

def get_training_panel():
    """获取训练面板实例"""
    global _training_panel
    if _training_panel is None:
        _training_panel = TrainingPanel()
    return _training_panel

__all__ = ['TrainingPanel', 'TrainingWorker', 'get_training_panel']
