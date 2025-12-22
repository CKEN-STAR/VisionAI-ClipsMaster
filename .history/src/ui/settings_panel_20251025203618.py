#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 设置面板
提供系统配置和用户偏好设置功能

功能特性：
1. 主题切换（浅色/深色/高对比度）
2. 语言切换（中文/英文）
3. 性能设置
4. ML优化配置
5. 导出设置
"""

import sys
import json
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QComboBox, QCheckBox, QSpinBox,
                                QGroupBox, QGridLayout, QSlider, QLineEdit,
                                QTabWidget, QFrame, QScrollArea, QTableWidget,
                                QTableWidgetItem, QHeaderView, QFileDialog,
                                QMessageBox)
    from PyQt6.QtCore import Qt, pyqtSignal, QSettings
    from PyQt6.QtGui import QFont, QPalette, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # 创建模拟的pyqtSignal和QSettings用于类定义
    class MockSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, *args):
            pass
    pyqtSignal = MockSignal

    class MockSettings:
        def __init__(self, *args):
            pass
        def setValue(self, key, value):
            pass
        def value(self, key, default=None):
            return default
        def sync(self):
            pass
    QSettings = MockSettings

# 获取日志记录器
logger = logging.getLogger(__name__)

class SettingsPanel(QWidget if PYQT_AVAILABLE else object):
    """设置面板"""

    # 信号定义
    theme_changed = pyqtSignal(str)
    language_changed = pyqtSignal(str)
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """初始化设置面板"""
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for SettingsPanel")
        
        super().__init__(parent)
        self.setObjectName("SettingsPanel")
        
        # 设置存储
        self.settings = QSettings("VisionAI", "ClipsMaster")
        self.current_settings = self._load_default_settings()
        
        # 初始化UI
        self._init_ui()
        
        # 加载保存的设置
        self._load_settings()
        
        logger.info("设置面板初始化完成")
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """加载默认设置"""
        return {
            "theme": "light",  # light, dark, high_contrast
            "language": "zh_CN",  # zh_CN, en_US
            "ml_optimization_enabled": True,
            "auto_save": True,
            "max_memory_usage_gb": 3.8,
            "processing_threads": 4,
            "export_quality": "high",  # low, medium, high
            "export_format": "mp4",
            "subtitle_font_size": 24,
            "subtitle_position": "bottom_center",
            "auto_backup": True,
            "backup_interval_minutes": 10,
            "show_performance_monitor": True,
            "enable_gpu_acceleration": False,
            "log_level": "INFO"
        }
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("系统设置")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 添加设置选项卡
        self._add_appearance_tab()
        self._add_performance_tab()
        self._add_model_management_tab()  # 新增：模型管理选项卡
        self._add_export_tab()
        self._add_advanced_tab()
        
        # 控制按钮
        buttons_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        buttons_layout.addWidget(self.reset_btn)
        
        self.apply_btn = QPushButton("应用")
        self.apply_btn.clicked.connect(self._apply_settings)
        buttons_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_settings)
        buttons_layout.addWidget(self.save_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # 应用样式
        self._apply_styles()
    
    def _add_appearance_tab(self):
        """添加外观设置选项卡"""
        appearance_widget = QWidget()
        layout = QVBoxLayout(appearance_widget)
        
        # 主题设置组
        theme_group = QGroupBox("主题设置")
        theme_layout = QGridLayout(theme_group)
        
        # 主题选择
        theme_layout.addWidget(QLabel("主题:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题", "高对比度"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        # 语言设置
        theme_layout.addWidget(QLabel("语言:"), 1, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        theme_layout.addWidget(self.language_combo, 1, 1)
        
        layout.addWidget(theme_group)
        
        # 字幕设置组
        subtitle_group = QGroupBox("字幕设置")
        subtitle_layout = QGridLayout(subtitle_group)
        
        # 字幕字体大小
        subtitle_layout.addWidget(QLabel("字体大小:"), 0, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 48)
        self.font_size_spin.setValue(24)
        subtitle_layout.addWidget(self.font_size_spin, 0, 1)
        
        # 字幕位置
        subtitle_layout.addWidget(QLabel("位置:"), 1, 0)
        self.position_combo = QComboBox()
        self.position_combo.addItems(["底部居中", "顶部居中", "左下角", "右下角"])
        subtitle_layout.addWidget(self.position_combo, 1, 1)
        
        layout.addWidget(subtitle_group)
        layout.addStretch()
        
        self.tab_widget.addTab(appearance_widget, "外观")
    
    def _add_performance_tab(self):
        """添加性能设置选项卡"""
        performance_widget = QWidget()
        layout = QVBoxLayout(performance_widget)
        
        # ML优化设置组
        ml_group = QGroupBox("机器学习优化")
        ml_layout = QGridLayout(ml_group)
        
        # ML优化开关
        self.ml_enabled_check = QCheckBox("启用ML权重优化")
        self.ml_enabled_check.setChecked(True)
        ml_layout.addWidget(self.ml_enabled_check, 0, 0, 1, 2)
        
        # 处理线程数
        ml_layout.addWidget(QLabel("处理线程数:"), 1, 0)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        self.threads_spin.setValue(4)
        ml_layout.addWidget(self.threads_spin, 1, 1)
        
        layout.addWidget(ml_group)
        
        # 内存设置组
        memory_group = QGroupBox("内存管理")
        memory_layout = QGridLayout(memory_group)
        
        # 最大内存使用
        memory_layout.addWidget(QLabel("最大内存使用 (GB):"), 0, 0)
        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(1, 16)
        self.memory_spin.setValue(4)
        memory_layout.addWidget(self.memory_spin, 0, 1)
        
        # GPU加速
        self.gpu_check = QCheckBox("启用GPU加速（如果可用）")
        memory_layout.addWidget(self.gpu_check, 1, 0, 1, 2)
        
        layout.addWidget(memory_group)
        
        # 监控设置组
        monitor_group = QGroupBox("性能监控")
        monitor_layout = QGridLayout(monitor_group)
        
        # 显示性能监控
        self.monitor_check = QCheckBox("显示实时性能监控")
        self.monitor_check.setChecked(True)
        monitor_layout.addWidget(self.monitor_check, 0, 0, 1, 2)
        
        layout.addWidget(monitor_group)
        layout.addStretch()

        self.tab_widget.addTab(performance_widget, "性能")

    def _add_model_management_tab(self):
        """添加模型管理选项卡"""
        model_widget = QWidget()
        layout = QVBoxLayout(model_widget)

        # 已安装模型列表组
        installed_group = QGroupBox("已安装模型")
        installed_layout = QVBoxLayout(installed_group)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(self._refresh_model_list)
        toolbar_layout.addWidget(refresh_btn)

        # 模型统计标签
        self.model_count_label = QLabel("正在扫描...")
        self.model_count_label.setStyleSheet("color: #666; font-size: 12px;")
        toolbar_layout.addWidget(self.model_count_label)

        toolbar_layout.addStretch()
        installed_layout.addLayout(toolbar_layout)

        # 模型列表表格
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(6)
        self.model_table.setHorizontalHeaderLabels([
            "模型名称", "类型", "格式", "大小", "路径", "最后修改"
        ])

        # 设置表格属性
        self.model_table.setAlternatingRowColors(True)
        self.model_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.model_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 设置列宽
        header = self.model_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 模型名称
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 类型
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 格式
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 大小
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # 路径
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 最后修改

        installed_layout.addWidget(self.model_table)

        # 操作按钮
        button_layout = QHBoxLayout()

        view_details_btn = QPushButton("📋 查看详情")
        view_details_btn.clicked.connect(self._view_model_details)
        button_layout.addWidget(view_details_btn)

        open_folder_btn = QPushButton("📂 打开文件夹")
        open_folder_btn.clicked.connect(self._open_model_folder)
        button_layout.addWidget(open_folder_btn)

        button_layout.addStretch()

        delete_btn = QPushButton("🗑️ 删除模型")
        delete_btn.setStyleSheet("color: #dc3545;")
        delete_btn.clicked.connect(self._delete_model)
        button_layout.addWidget(delete_btn)

        installed_layout.addLayout(button_layout)

        layout.addWidget(installed_group)

        # 模型转换组
        convert_group = QGroupBox("模型格式转换")
        convert_layout = QGridLayout(convert_group)

        # 说明文字
        info_label = QLabel(
            "训练后的模型默认保存为HuggingFace格式。\n"
            "如需用于推理，可手动转换为GGUF格式以提升性能。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        convert_layout.addWidget(info_label, 0, 0, 1, 2)

        # 源模型路径
        convert_layout.addWidget(QLabel("源模型路径:"), 1, 0)
        self.source_model_path = QLineEdit()
        self.source_model_path.setPlaceholderText("例如: ./results_zh 或 models/qwen/base")
        convert_layout.addWidget(self.source_model_path, 1, 1)

        # 浏览按钮
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_source_model)
        convert_layout.addWidget(browse_btn, 1, 2)

        # 输出路径
        convert_layout.addWidget(QLabel("输出路径:"), 2, 0)
        self.output_gguf_path = QLineEdit()
        self.output_gguf_path.setPlaceholderText("例如: models/qwen/quantized/trained_Q4_K_M.gguf")
        convert_layout.addWidget(self.output_gguf_path, 2, 1)

        # 浏览输出按钮
        browse_output_btn = QPushButton("浏览...")
        browse_output_btn.clicked.connect(self._browse_output_path)
        convert_layout.addWidget(browse_output_btn, 2, 2)

        # 量化级别
        convert_layout.addWidget(QLabel("量化级别:"), 3, 0)
        self.quant_type_combo = QComboBox()
        self.quant_type_combo.addItems([
            "Q4_K_M (推荐，平衡性能和质量)",
            "Q5_K (更高质量)",
            "Q2_K (最小体积)",
            "Q8_0 (最高质量)"
        ])
        convert_layout.addWidget(self.quant_type_combo, 3, 1, 1, 2)

        # 转换按钮（两个按钮并排）
        button_layout = QHBoxLayout()

        # 智能转换按钮（新增）
        self.smart_convert_btn = QPushButton("🤖 智能转换（推荐）")
        self.smart_convert_btn.setMinimumHeight(40)
        self.smart_convert_btn.clicked.connect(self._smart_conversion)
        self.smart_convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.smart_convert_btn)

        # 手动转换按钮
        self.convert_btn = QPushButton("🔄 手动转换")
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.clicked.connect(self._start_conversion)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.convert_btn)

        convert_layout.addLayout(button_layout, 4, 0, 1, 3)

        # 转换状态
        self.convert_status_label = QLabel("")
        self.convert_status_label.setWordWrap(True)
        self.convert_status_label.setStyleSheet("color: #007bff; font-size: 12px; padding: 5px;")
        convert_layout.addWidget(self.convert_status_label, 5, 0, 1, 3)

        layout.addWidget(convert_group)

        self.tab_widget.addTab(model_widget, "模型管理")

        # 初始化时刷新模型列表
        self._refresh_model_list()

    def _browse_source_model(self):
        """浏览源模型路径"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            path = QFileDialog.getExistingDirectory(
                self,
                "选择源模型目录",
                "",
                QFileDialog.Option.ShowDirsOnly
            )
            if path:
                self.source_model_path.setText(path)
                # 自动生成输出路径建议
                from pathlib import Path
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                suggested_output = f"models/qwen/quantized/trained_{timestamp}_Q4_K_M.gguf"
                self.output_gguf_path.setText(suggested_output)
        except Exception as e:
            logger.error(f"浏览源模型路径失败: {e}")

    def _browse_output_path(self):
        """浏览输出路径"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(
                self,
                "选择输出文件",
                "",
                "GGUF文件 (*.gguf)"
            )
            if path:
                self.output_gguf_path.setText(path)
        except Exception as e:
            logger.error(f"浏览输出路径失败: {e}")

    def _start_conversion(self):
        """开始模型转换"""
        source_path = self.source_model_path.text().strip()
        output_path = self.output_gguf_path.text().strip()

        if not source_path or not output_path:
            self.convert_status_label.setText("❌ 请填写源模型路径和输出路径")
            self.convert_status_label.setStyleSheet("color: #dc3545; font-size: 12px; padding: 5px;")
            return

        # 获取量化类型
        quant_text = self.quant_type_combo.currentText()
        quant_type = quant_text.split()[0]  # 提取 Q4_K_M 等

        try:
            self.convert_btn.setEnabled(False)
            self.convert_status_label.setText("🔄 正在转换，请稍候...")
            self.convert_status_label.setStyleSheet("color: #007bff; font-size: 12px; padding: 5px;")

            # 导入模型转换器
            from models.converters.model_converter import ModelConverter

            converter = ModelConverter()
            result_path = converter.convert_format(
                model_path=source_path,
                output_format='gguf',
                output_path=output_path,
                quant_type=quant_type
            )

            self.convert_status_label.setText(f"✅ 转换成功！\n输出文件: {result_path}")
            self.convert_status_label.setStyleSheet("color: #28a745; font-size: 12px; padding: 5px;")

        except Exception as e:
            self.convert_status_label.setText(f"❌ 转换失败: {str(e)}")
            self.convert_status_label.setStyleSheet("color: #dc3545; font-size: 12px; padding: 5px;")
            logger.error(f"模型转换失败: {e}")
        finally:
            self.convert_btn.setEnabled(True)

    def _add_export_tab(self):
        """添加导出设置选项卡"""
        export_widget = QWidget()
        layout = QVBoxLayout(export_widget)
        
        # 导出质量设置组
        quality_group = QGroupBox("导出质量")
        quality_layout = QGridLayout(quality_group)
        
        # 导出质量
        quality_layout.addWidget(QLabel("视频质量:"), 0, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["低质量", "中等质量", "高质量"])
        self.quality_combo.setCurrentText("高质量")
        quality_layout.addWidget(self.quality_combo, 0, 1)
        
        # 导出格式
        quality_layout.addWidget(QLabel("导出格式:"), 1, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MOV"])
        quality_layout.addWidget(self.format_combo, 1, 1)
        
        layout.addWidget(quality_group)
        
        # 剪映设置组
        jianying_group = QGroupBox("剪映导出")
        jianying_layout = QGridLayout(jianying_group)
        
        # 自动打开剪映
        self.auto_open_check = QCheckBox("导出后自动打开剪映")
        jianying_layout.addWidget(self.auto_open_check, 0, 0, 1, 2)
        
        # 保留原始文件
        self.keep_original_check = QCheckBox("保留原始视频文件")
        self.keep_original_check.setChecked(True)
        jianying_layout.addWidget(self.keep_original_check, 1, 0, 1, 2)
        
        layout.addWidget(jianying_group)
        layout.addStretch()
        
        self.tab_widget.addTab(export_widget, "导出")
    
    def _add_advanced_tab(self):
        """添加高级设置选项卡"""
        advanced_widget = QWidget()
        layout = QVBoxLayout(advanced_widget)
        
        # 自动保存设置组
        autosave_group = QGroupBox("自动保存")
        autosave_layout = QGridLayout(autosave_group)
        
        # 启用自动保存
        self.autosave_check = QCheckBox("启用自动保存")
        self.autosave_check.setChecked(True)
        autosave_layout.addWidget(self.autosave_check, 0, 0, 1, 2)
        
        # 自动备份
        self.backup_check = QCheckBox("启用自动备份")
        self.backup_check.setChecked(True)
        autosave_layout.addWidget(self.backup_check, 1, 0, 1, 2)
        
        # 备份间隔
        autosave_layout.addWidget(QLabel("备份间隔 (分钟):"), 2, 0)
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 60)
        self.backup_interval_spin.setValue(10)
        autosave_layout.addWidget(self.backup_interval_spin, 2, 1)
        
        layout.addWidget(autosave_group)
        
        # 日志设置组
        log_group = QGroupBox("日志设置")
        log_layout = QGridLayout(log_group)
        
        # 日志级别
        log_layout.addWidget(QLabel("日志级别:"), 0, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        log_layout.addWidget(self.log_level_combo, 0, 1)
        
        layout.addWidget(log_group)
        layout.addStretch()
        
        self.tab_widget.addTab(advanced_widget, "高级")
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QWidget#SettingsPanel {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #007bff;
                font-family: 'Microsoft YaHei';
            }
            
            QLabel {
                color: #333333;
                font-family: 'Microsoft YaHei';
            }
            
            QComboBox, QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
                font-family: 'Microsoft YaHei';
            }
            
            QComboBox:focus, QSpinBox:focus {
                border-color: #007bff;
            }
            
            QCheckBox {
                font-family: 'Microsoft YaHei';
                color: #333333;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #ced4da;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
    
    def _on_theme_changed(self, theme_text: str):
        """主题改变处理"""
        theme_map = {
            "浅色主题": "light",
            "深色主题": "dark", 
            "高对比度": "high_contrast"
        }
        
        theme = theme_map.get(theme_text, "light")
        self.current_settings["theme"] = theme
        self.theme_changed.emit(theme)
        
        logger.info(f"主题已切换到: {theme}")
    
    def _on_language_changed(self, language_text: str):
        """语言改变处理"""
        language_map = {
            "中文": "zh_CN",
            "English": "en_US"
        }
        
        language = language_map.get(language_text, "zh_CN")
        self.current_settings["language"] = language
        self.language_changed.emit(language)
        
        logger.info(f"语言已切换到: {language}")
    
    def _collect_current_settings(self) -> Dict[str, Any]:
        """收集当前设置"""
        settings = self.current_settings.copy()
        
        # 更新设置值
        settings["ml_optimization_enabled"] = self.ml_enabled_check.isChecked()
        settings["processing_threads"] = self.threads_spin.value()
        settings["max_memory_usage_gb"] = self.memory_spin.value()
        settings["enable_gpu_acceleration"] = self.gpu_check.isChecked()
        settings["show_performance_monitor"] = self.monitor_check.isChecked()
        settings["subtitle_font_size"] = self.font_size_spin.value()
        settings["auto_save"] = self.autosave_check.isChecked()
        settings["auto_backup"] = self.backup_check.isChecked()
        settings["backup_interval_minutes"] = self.backup_interval_spin.value()
        
        # 质量和格式映射
        quality_map = {"低质量": "low", "中等质量": "medium", "高质量": "high"}
        settings["export_quality"] = quality_map.get(self.quality_combo.currentText(), "high")
        
        format_map = {"MP4": "mp4", "AVI": "avi", "MOV": "mov"}
        settings["export_format"] = format_map.get(self.format_combo.currentText(), "mp4")
        
        position_map = {"底部居中": "bottom_center", "顶部居中": "top_center", 
                       "左下角": "bottom_left", "右下角": "bottom_right"}
        settings["subtitle_position"] = position_map.get(self.position_combo.currentText(), "bottom_center")
        
        settings["log_level"] = self.log_level_combo.currentText()
        
        return settings
    
    def _apply_settings(self):
        """应用设置"""
        try:
            self.current_settings = self._collect_current_settings()
            self.settings_changed.emit(self.current_settings)
            
            logger.info("设置已应用")
            
        except Exception as e:
            logger.error(f"应用设置失败: {str(e)}")
    
    def _save_settings(self):
        """保存设置"""
        try:
            self.current_settings = self._collect_current_settings()
            
            # 保存到QSettings
            for key, value in self.current_settings.items():
                self.settings.setValue(key, value)
            
            self.settings.sync()
            
            # 发送信号
            self.settings_changed.emit(self.current_settings)
            
            logger.info("设置已保存")
            
        except Exception as e:
            logger.error(f"保存设置失败: {str(e)}")
    
    def _load_settings(self):
        """加载设置"""
        try:
            # 从QSettings加载
            for key, default_value in self.current_settings.items():
                value = self.settings.value(key, default_value)
                self.current_settings[key] = value
            
            # 更新UI控件
            self._update_ui_from_settings()
            
            logger.info("设置已加载")
            
        except Exception as e:
            logger.error(f"加载设置失败: {str(e)}")

    def _refresh_model_list(self):
        """刷新模型列表"""
        try:
            self.model_count_label.setText("正在扫描...")
            self.model_table.setRowCount(0)

            # 扫描models目录
            models_dir = Path("models")
            if not models_dir.exists():
                self.model_count_label.setText("未找到models目录")
                return

            detected_models = []

            # 定义需要扫描的目录模式
            scan_patterns = [
                ("qwen2.5-1.5b/fp16", "Qwen2.5-1.5B", "中文基础模型"),
                ("qwen2.5-1.5b/quantized", "Qwen2.5-1.5B", "中文量化模型"),
                ("qwen/base", "Qwen", "中文基础模型"),
                ("qwen/finetuned", "Qwen", "中文微调模型"),
                ("qwen/trained", "Qwen", "中文训练模型"),
                ("qwen/quantized", "Qwen", "中文量化模型"),
                ("mistral/base", "Mistral", "英文基础模型"),
                ("mistral/trained", "Mistral", "英文训练模型"),
                ("mistral/quantized", "Mistral", "英文量化模型"),
            ]

            for pattern, model_type, description in scan_patterns:
                model_path = models_dir / pattern
                if model_path.exists():
                    # 检查是否包含模型文件
                    has_config = (model_path / "config.json").exists()
                    has_safetensors = list(model_path.glob("*.safetensors"))
                    has_gguf = list(model_path.glob("*.gguf"))
                    has_adapter = (model_path / "adapter_config.json").exists()

                    if has_config or has_safetensors or has_gguf or has_adapter:
                        # 确定格式
                        if has_adapter:
                            format_type = "LoRA"
                        elif has_safetensors:
                            format_type = "SafeTensors"
                        elif has_gguf:
                            format_type = "GGUF"
                        else:
                            format_type = "HuggingFace"

                        # 计算大小
                        total_size = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file())
                        size_str = self._format_size(total_size)

                        # 获取最后修改时间
                        try:
                            mtime = max(f.stat().st_mtime for f in model_path.rglob("*") if f.is_file())
                            last_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                        except:
                            last_modified = "未知"

                        detected_models.append({
                            "name": f"{model_type} - {description}",
                            "type": model_type,
                            "format": format_type,
                            "size": size_str,
                            "path": str(model_path),
                            "last_modified": last_modified
                        })

            # 填充表格
            self.model_table.setRowCount(len(detected_models))
            for row, model in enumerate(detected_models):
                self.model_table.setItem(row, 0, QTableWidgetItem(model["name"]))
                self.model_table.setItem(row, 1, QTableWidgetItem(model["type"]))
                self.model_table.setItem(row, 2, QTableWidgetItem(model["format"]))
                self.model_table.setItem(row, 3, QTableWidgetItem(model["size"]))
                self.model_table.setItem(row, 4, QTableWidgetItem(model["path"]))
                self.model_table.setItem(row, 5, QTableWidgetItem(model["last_modified"]))

            # 更新统计信息
            self.model_count_label.setText(f"共检测到 {len(detected_models)} 个模型")
            logger.info(f"模型列表刷新完成，检测到 {len(detected_models)} 个模型")

        except Exception as e:
            logger.error(f"刷新模型列表失败: {str(e)}")
            self.model_count_label.setText(f"扫描失败: {str(e)}")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _view_model_details(self):
        """查看模型详情"""
        try:
            selected_rows = self.model_table.selectedItems()
            if not selected_rows:
                QMessageBox.information(self, "提示", "请先选择一个模型")
                return

            row = self.model_table.currentRow()
            model_name = self.model_table.item(row, 0).text()
            model_type = self.model_table.item(row, 1).text()
            model_format = self.model_table.item(row, 2).text()
            model_size = self.model_table.item(row, 3).text()
            model_path = self.model_table.item(row, 4).text()
            last_modified = self.model_table.item(row, 5).text()

            # 读取配置文件或GGUF元数据
            config_info = ""

            if model_format == "GGUF":
                # GGUF格式：读取GGUF文件元数据
                gguf_files = list(Path(model_path).glob("*.gguf"))
                if gguf_files:
                    try:
                        import gguf
                        reader = gguf.GGUFReader(str(gguf_files[0]))

                        # 提取元数据
                        metadata = {}
                        if hasattr(reader, 'fields'):
                            # 提取关键字段
                            key_fields = [
                                'general.name',
                                'general.architecture',
                                'general.file_type',
                                'general.quantization_version',
                                'llama.context_length',
                                'llama.embedding_length',
                                'llama.block_count',
                                'llama.attention.head_count',
                                'llama.attention.head_count_kv'
                            ]
                            for key in key_fields:
                                if key in reader.fields:
                                    parts = reader.fields[key].parts
                                    if parts:
                                        metadata[key] = parts[0]

                        if metadata:
                            config_info = "\n\nGGUF元数据:\n"
                            for key, value in metadata.items():
                                config_info += f"  {key}: {value}\n"

                        # 添加张量信息
                        if hasattr(reader, 'tensors'):
                            config_info += f"\n张量数量: {len(reader.tensors)}\n"

                        # 添加文件列表
                        config_info += f"\nGGUF文件:\n"
                        for gguf_file in gguf_files:
                            file_size = gguf_file.stat().st_size / 1024 / 1024
                            config_info += f"  - {gguf_file.name} ({file_size:.2f} MB)\n"

                    except Exception as e:
                        config_info = f"\n\nGGUF元数据读取失败: {str(e)}"
                        logger.warning(f"GGUF元数据读取失败: {e}")
            else:
                # 其他格式：读取config.json
                config_path = Path(model_path) / "config.json"
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        config_info = f"\n\n配置信息:\n{json.dumps(config, indent=2, ensure_ascii=False)}"
                    except:
                        config_info = "\n\n配置文件读取失败"

            # 显示详情
            details = f"""模型详细信息

名称: {model_name}
类型: {model_type}
格式: {model_format}
大小: {model_size}
路径: {model_path}
最后修改: {last_modified}{config_info}"""

            QMessageBox.information(self, "模型详情", details)

        except Exception as e:
            logger.error(f"查看模型详情失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"查看详情失败: {str(e)}")

    def _open_model_folder(self):
        """打开模型文件夹"""
        try:
            selected_rows = self.model_table.selectedItems()
            if not selected_rows:
                QMessageBox.information(self, "提示", "请先选择一个模型")
                return

            row = self.model_table.currentRow()
            model_path = self.model_table.item(row, 4).text()

            # 在文件管理器中打开
            if sys.platform == "win32":
                os.startfile(model_path)
            elif sys.platform == "darwin":
                os.system(f'open "{model_path}"')
            else:
                os.system(f'xdg-open "{model_path}"')

        except Exception as e:
            logger.error(f"打开文件夹失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"打开文件夹失败: {str(e)}")

    def _delete_model(self):
        """删除模型"""
        try:
            selected_rows = self.model_table.selectedItems()
            if not selected_rows:
                QMessageBox.information(self, "提示", "请先选择一个模型")
                return

            row = self.model_table.currentRow()
            model_name = self.model_table.item(row, 0).text()
            model_path = self.model_table.item(row, 4).text()

            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除模型吗？\n\n{model_name}\n{model_path}\n\n此操作不可恢复！",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                import shutil
                shutil.rmtree(model_path)
                QMessageBox.information(self, "成功", "模型已删除")
                self._refresh_model_list()

        except Exception as e:
            logger.error(f"删除模型失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"删除模型失败: {str(e)}")

    def _update_ui_from_settings(self):
        """根据设置更新UI"""
        try:
            # 主题
            theme_map = {"light": "浅色主题", "dark": "深色主题", "high_contrast": "高对比度"}
            theme_text = theme_map.get(self.current_settings["theme"], "浅色主题")
            self.theme_combo.setCurrentText(theme_text)
            
            # 语言
            language_map = {"zh_CN": "中文", "en_US": "English"}
            language_text = language_map.get(self.current_settings["language"], "中文")
            self.language_combo.setCurrentText(language_text)
            
            # 其他设置
            self.ml_enabled_check.setChecked(self.current_settings["ml_optimization_enabled"])
            self.threads_spin.setValue(self.current_settings["processing_threads"])
            self.memory_spin.setValue(int(self.current_settings["max_memory_usage_gb"]))
            self.gpu_check.setChecked(self.current_settings["enable_gpu_acceleration"])
            self.monitor_check.setChecked(self.current_settings["show_performance_monitor"])
            self.font_size_spin.setValue(self.current_settings["subtitle_font_size"])
            self.autosave_check.setChecked(self.current_settings["auto_save"])
            self.backup_check.setChecked(self.current_settings["auto_backup"])
            self.backup_interval_spin.setValue(self.current_settings["backup_interval_minutes"])
            
        except Exception as e:
            logger.error(f"更新UI失败: {str(e)}")
    
    def _reset_to_defaults(self):
        """恢复默认设置"""
        try:
            self.current_settings = self._load_default_settings()
            self._update_ui_from_settings()
            
            logger.info("设置已恢复为默认值")
            
        except Exception as e:
            logger.error(f"恢复默认设置失败: {str(e)}")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        return self.current_settings.copy()


# 便捷函数
def create_settings_panel(parent=None) -> Optional[SettingsPanel]:
    """创建设置面板"""
    if not PYQT_AVAILABLE:
        logger.warning("PyQt6不可用，无法创建设置面板")
        return None
    
    try:
        return SettingsPanel(parent)
    except Exception as e:
        logger.error(f"创建设置面板失败: {str(e)}")
        return None
