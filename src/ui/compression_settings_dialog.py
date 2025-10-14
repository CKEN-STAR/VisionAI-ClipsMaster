#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压缩设置对话框
显示SmartCompressor的状态和统计信息
"""

import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QCheckBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QTabWidget,
    QWidget, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

class CompressionSettingsDialog(QDialog):
    """压缩设置对话框"""
    
    def __init__(self, smart_compressor=None, parent=None):
        """
        初始化对话框
        
        Args:
            smart_compressor: SmartCompressor实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.smart_compressor = smart_compressor
        self.setWindowTitle("智能压缩设置")
        self.setMinimumSize(700, 500)
        
        self.setup_ui()
        self.setup_timer()
        
        # 初始化显示
        if self.smart_compressor:
            self.update_display()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("智能自适应压缩器")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 标签页1: 状态监控
        self.create_status_tab()
        
        # 标签页2: 统计信息
        self.create_stats_tab()
        
        # 标签页3: 设置
        self.create_settings_tab()
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.update_display)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def create_status_tab(self):
        """创建状态监控标签页"""
        status_widget = QWidget()
        layout = QVBoxLayout(status_widget)
        
        # 当前状态
        status_group = QGroupBox("当前状态")
        status_layout = QVBoxLayout(status_group)
        
        self.memory_label = QLabel("内存使用率: --")
        self.pressure_label = QLabel("内存压力级别: --")
        self.algo_label = QLabel("当前压缩算法: --")
        self.level_label = QLabel("当前压缩级别: --")
        self.hardware_label = QLabel("硬件加速: --")
        
        # 设置字体大小
        font = QFont()
        font.setPointSize(11)
        for label in [self.memory_label, self.pressure_label, self.algo_label, 
                     self.level_label, self.hardware_label]:
            label.setFont(font)
        
        status_layout.addWidget(self.memory_label)
        status_layout.addWidget(self.pressure_label)
        status_layout.addWidget(self.algo_label)
        status_layout.addWidget(self.level_label)
        status_layout.addWidget(self.hardware_label)
        
        layout.addWidget(status_group)
        
        # 内存历史
        history_group = QGroupBox("内存使用历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(150)
        history_layout.addWidget(self.history_text)
        
        layout.addWidget(history_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(status_widget, "状态监控")
    
    def create_stats_tab(self):
        """创建统计信息标签页"""
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        
        # 统计表格
        stats_group = QGroupBox("压缩统计")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["统计项", "数值"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setRowCount(9)
        
        # 设置统计项名称
        stats_items = [
            "压缩级别调整次数",
            "压缩算法切换次数",
            "压缩操作次数",
            "解压操作次数",
            "处理的总字节数",
            "输出的总字节数",
            "平均压缩率",
            "总耗时(秒)",
            "上次更新时间"
        ]
        
        for i, item in enumerate(stats_items):
            name_item = QTableWidgetItem(item)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.stats_table.setItem(i, 0, name_item)
            
            value_item = QTableWidgetItem("--")
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.stats_table.setItem(i, 1, value_item)
        
        stats_layout.addWidget(self.stats_table)
        layout.addWidget(stats_group)
        
        self.tab_widget.addTab(stats_widget, "统计信息")
    
    def create_settings_tab(self):
        """创建设置标签页"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # 基本设置
        basic_group = QGroupBox("基本设置")
        basic_layout = QVBoxLayout(basic_group)
        
        # 启用/禁用
        self.enable_checkbox = QCheckBox("启用智能压缩")
        self.enable_checkbox.setChecked(True)
        basic_layout.addWidget(self.enable_checkbox)
        
        # 硬件加速
        self.hardware_checkbox = QCheckBox("启用硬件加速(GPU)")
        self.hardware_checkbox.setChecked(True)
        basic_layout.addWidget(self.hardware_checkbox)
        
        layout.addWidget(basic_group)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # 监控间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("监控间隔(秒):"))
        self.interval_spinbox = QDoubleSpinBox()
        self.interval_spinbox.setRange(1.0, 60.0)
        self.interval_spinbox.setValue(10.0)
        self.interval_spinbox.setSingleStep(1.0)
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        advanced_layout.addLayout(interval_layout)
        
        # 变化阈值
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("内存变化阈值(%):"))
        self.threshold_spinbox = QDoubleSpinBox()
        self.threshold_spinbox.setRange(1.0, 20.0)
        self.threshold_spinbox.setValue(5.0)
        self.threshold_spinbox.setSingleStep(1.0)
        threshold_layout.addWidget(self.threshold_spinbox)
        threshold_layout.addStretch()
        advanced_layout.addLayout(threshold_layout)
        
        # 默认算法
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("默认压缩算法:"))
        self.algo_combobox = QComboBox()
        self.algo_combobox.addItems(["lz4", "zstd", "bzip2", "lzma"])
        self.algo_combobox.setCurrentText("zstd")
        algo_layout.addWidget(self.algo_combobox)
        algo_layout.addStretch()
        advanced_layout.addLayout(algo_layout)
        
        # 默认级别
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("默认压缩级别:"))
        self.level_spinbox = QSpinBox()
        self.level_spinbox.setRange(1, 9)
        self.level_spinbox.setValue(3)
        level_layout.addWidget(self.level_spinbox)
        level_layout.addStretch()
        advanced_layout.addLayout(level_layout)
        
        layout.addWidget(advanced_group)
        
        # 应用按钮
        apply_layout = QHBoxLayout()
        apply_layout.addStretch()
        self.apply_btn = QPushButton("应用设置")
        self.apply_btn.clicked.connect(self.apply_settings)
        apply_layout.addWidget(self.apply_btn)
        layout.addLayout(apply_layout)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "设置")
    
    def setup_timer(self):
        """设置定时器,自动刷新显示"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(2000)  # 每2秒刷新一次
    
    def update_display(self):
        """更新显示"""
        if not self.smart_compressor:
            return
        
        try:
            # 更新状态
            import psutil
            memory_percent = psutil.virtual_memory().percent
            self.memory_label.setText(f"内存使用率: {memory_percent:.1f}%")
            
            # 设置颜色
            if memory_percent < 50:
                color = QColor(0, 150, 0)  # 绿色
            elif memory_percent < 70:
                color = QColor(200, 150, 0)  # 橙色
            elif memory_percent < 85:
                color = QColor(200, 100, 0)  # 深橙色
            else:
                color = QColor(200, 0, 0)  # 红色
            
            palette = self.memory_label.palette()
            palette.setColor(palette.ColorRole.WindowText, color)
            self.memory_label.setPalette(palette)
            
            # 压力级别
            pressure_level = self.smart_compressor.current_pressure_level
            pressure_text = {
                0: "低压力 ✅",
                1: "中等压力 ⚠️",
                2: "高压力 ⚠️⚠️",
                3: "临界压力 ❌"
            }.get(pressure_level.value if hasattr(pressure_level, 'value') else pressure_level, "未知")
            self.pressure_label.setText(f"内存压力级别: {pressure_text}")
            
            # 压缩算法和级别
            if self.smart_compressor.compressor:
                algo = getattr(self.smart_compressor.compressor, 'name', self.smart_compressor.default_algo)
                self.algo_label.setText(f"当前压缩算法: {algo.upper()}")
                self.level_label.setText(f"当前压缩级别: {self.smart_compressor.default_level}")
            
            # 硬件加速
            hardware_status = "已启用 ✅" if self.smart_compressor.hardware_compressor else "未启用 ❌"
            self.hardware_label.setText(f"硬件加速: {hardware_status}")
            
            # 更新统计信息
            stats = self.smart_compressor.stats

            # 确保所有值都是正确的类型
            average_ratio = stats.get('average_ratio', 0)
            if isinstance(average_ratio, dict):
                average_ratio = 0

            last_update = stats.get("last_update", "--")
            if isinstance(last_update, (int, float)):
                import datetime
                last_update = datetime.datetime.fromtimestamp(last_update).strftime("%H:%M:%S")

            stats_values = [
                str(stats.get("level_adjustments", 0)),
                str(stats.get("algo_switches", 0)),
                str(stats.get("compression_count", 0)),
                str(stats.get("decompression_count", 0)),
                f"{stats.get('bytes_processed', 0) / 1024 / 1024:.2f} MB",
                f"{stats.get('bytes_output', 0) / 1024 / 1024:.2f} MB",
                f"{average_ratio:.2%}",
                f"{stats.get('time_spent', 0):.2f}",
                str(last_update)
            ]
            
            for i, value in enumerate(stats_values):
                self.stats_table.item(i, 1).setText(value)
            
            # 更新内存历史
            memory_samples = stats.get("memory_samples", [])
            if memory_samples:
                history_text = "最近10次内存采样:\n"
                for sample in memory_samples[-10:]:
                    # sample可能是dict或float
                    if isinstance(sample, dict):
                        memory_percent = sample.get("memory_percent", 0)
                        history_text += f"  {memory_percent:.1f}%\n"
                    else:
                        history_text += f"  {sample:.1f}%\n"
                self.history_text.setPlainText(history_text)
        
        except Exception as e:
            print(f"[ERROR] 更新压缩设置显示失败: {e}")
    
    def apply_settings(self):
        """应用设置"""
        if not self.smart_compressor:
            return
        
        try:
            # 应用设置
            self.smart_compressor.monitoring_interval = self.interval_spinbox.value()
            self.smart_compressor.change_threshold = self.threshold_spinbox.value() / 100.0
            self.smart_compressor.default_algo = self.algo_combobox.currentText()
            self.smart_compressor.default_level = self.level_spinbox.value()
            self.smart_compressor.use_hardware_accel = self.hardware_checkbox.isChecked()
            
            # 重新初始化压缩器
            self.smart_compressor._init_compressor()
            
            print("[OK] 压缩设置已应用")
            self.update_display()
        
        except Exception as e:
            print(f"[ERROR] 应用压缩设置失败: {e}")

def show_compression_settings(smart_compressor=None, parent=None):
    """显示压缩设置对话框"""
    dialog = CompressionSettingsDialog(smart_compressor, parent)
    return dialog.exec()

