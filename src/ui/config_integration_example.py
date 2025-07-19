#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置绑定集成示例

展示如何在现有UI中集成配置绑定功能。
本示例创建一个简单的导出设置页面，并绑定到配置系统。
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox,
    QFileDialog, QSpinBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

# 导入配置绑定器
try:
    from src.ui.ui_config_panel import ConfigBinder, Validators, Transformers, ResolutionTransformer
    from src.ui.ui_config_plugin import ConfigBinderPlugin
    from src.config import config_manager
    from src.utils.log_handler import get_logger
except ImportError as e:
    # 如果无法导入，使用标准日志
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    # 简单的模拟对象
    class MockConfigManager:
        def __init__(self):
            self.configs = {}
        
        def get_config(self, config_type, key=None):
            config = self.configs.get(config_type, {})
            if key is None:
                return config
            return config.get(key)
        
        def set_config(self, config_type, key, value):
            if config_type not in self.configs:
                self.configs[config_type] = {}
            self.configs[config_type][key] = value
    
    config_manager = MockConfigManager()
    
    class ConfigBinder:
        def __init__(self, *args, **kwargs):
            pass
        
        def bind(self, *args, **kwargs):
            pass
        
        def config_to_ui(self):
            pass
        
        def ui_to_config(self):
            pass
    
    class ConfigBinderPlugin:
        def __init__(self, *args, **kwargs):
            pass
    
    class Validators:
        pass
    
    class Transformers:
        pass
    
    class ResolutionTransformer:
        pass

# 设置日志记录器
logger = get_logger("config_integration_example")

class ExportSettingsPage(QWidget):
    """导出设置页面，展示配置绑定的用法"""
    
    # 定义信号
    settings_saved = pyqtSignal(dict)  # 设置保存信号
    export_started = pyqtSignal(dict)  # 导出开始信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_elements = {}  # UI元素字典
        self.config_binder = None  # 配置绑定器
        self.initialized = False
        
        # 初始化UI
        self.init_ui()
        
        # 设置配置绑定
        self.setup_config_binding()
        
        # 标记为已初始化
        self.initialized = True
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        
        # 创建标题
        title_label = QLabel("导出设置")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # 创建分组框：视频设置
        video_group = QGroupBox("视频设置")
        video_layout = QFormLayout()
        
        # 分辨率下拉框
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "854x480", "640x360", "原始分辨率"])
        self.ui_elements["resolution_combo"] = self.resolution_combo
        video_layout.addRow("导出分辨率:", self.resolution_combo)
        
        # 帧率下拉框
        self.framerate_combo = QComboBox()
        self.framerate_combo.addItems(["60fps", "30fps", "25fps", "24fps", "原始帧率"])
        self.ui_elements["framerate_combo"] = self.framerate_combo
        video_layout.addRow("帧率:", self.framerate_combo)
        
        # 视频编码下拉框
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["H.264", "H.265", "AV1", "VP9"])
        self.ui_elements["codec_combo"] = self.codec_combo
        video_layout.addRow("视频编码:", self.codec_combo)
        
        # 视频质量滑块
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 10)
        self.quality_spin.setValue(8)
        self.quality_spin.setSuffix(" (1-10)")
        self.ui_elements["quality_spin"] = self.quality_spin
        video_layout.addRow("视频质量:", self.quality_spin)
        
        video_group.setLayout(video_layout)
        main_layout.addWidget(video_group)
        
        # 创建分组框：音频设置
        audio_group = QGroupBox("音频设置")
        audio_layout = QFormLayout()
        
        # 音频编码下拉框
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(["AAC", "MP3", "Opus", "FLAC"])
        self.ui_elements["audio_codec_combo"] = self.audio_codec_combo
        audio_layout.addRow("音频编码:", self.audio_codec_combo)
        
        # 音频比特率下拉框
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems(["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps"])
        self.ui_elements["audio_bitrate_combo"] = self.audio_bitrate_combo
        audio_layout.addRow("音频比特率:", self.audio_bitrate_combo)
        
        # 音频处理复选框
        self.audio_normalize_check = QCheckBox("启用")
        self.ui_elements["audio_normalize_check"] = self.audio_normalize_check
        audio_layout.addRow("音频标准化:", self.audio_normalize_check)
        
        audio_group.setLayout(audio_layout)
        main_layout.addWidget(audio_group)
        
        # 创建分组框：输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout()
        
        # 输出路径
        path_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出路径...")
        self.ui_elements["output_path"] = self.output_path
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_output_path)
        
        path_layout.addWidget(self.output_path)
        path_layout.addWidget(self.browse_button)
        
        output_layout.addRow("输出路径:", path_layout)
        
        # 文件名格式
        self.filename_format = QLineEdit()
        self.filename_format.setPlaceholderText("{project}_{date}_{time}")
        self.ui_elements["filename_format"] = self.filename_format
        output_layout.addRow("文件名格式:", self.filename_format)
        
        # 导出格式
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["MP4", "MOV", "MKV", "WebM"])
        self.ui_elements["export_format_combo"] = self.export_format_combo
        output_layout.addRow("导出格式:", self.export_format_combo)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # 创建分组框：预设
        preset_group = QGroupBox("预设")
        preset_layout = QHBoxLayout()
        
        # 预设按钮
        self.preset_high = QPushButton("高质量")
        self.preset_high.clicked.connect(lambda: self.apply_preset("high"))
        
        self.preset_medium = QPushButton("中等质量")
        self.preset_medium.clicked.connect(lambda: self.apply_preset("medium"))
        
        self.preset_low = QPushButton("低质量")
        self.preset_low.clicked.connect(lambda: self.apply_preset("low"))
        
        self.preset_mobile = QPushButton("移动设备")
        self.preset_mobile.clicked.connect(lambda: self.apply_preset("mobile"))
        
        preset_layout.addWidget(self.preset_high)
        preset_layout.addWidget(self.preset_medium)
        preset_layout.addWidget(self.preset_low)
        preset_layout.addWidget(self.preset_mobile)
        
        preset_group.setLayout(preset_layout)
        main_layout.addWidget(preset_group)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 保存按钮
        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self.save_settings)
        
        # 导出按钮
        self.export_button = QPushButton("开始导出")
        self.export_button.clicked.connect(self.start_export)
        
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
    
    def setup_config_binding(self):
        """设置配置绑定"""
        try:
            # 创建配置绑定器
            self.config_binder = ConfigBinder(self.ui_elements, "export")
            
            # 绑定配置
            resolution_transformer = ResolutionTransformer()
            
            # 视频设置
            self.config_binder.bind("video.resolution", "resolution_combo", "1920x1080")
            self.config_binder.bind("video.framerate", "framerate_combo", "30fps")
            self.config_binder.bind("video.codec", "codec_combo", "H.264")
            self.config_binder.bind("video.quality", "quality_spin", 8, 
                                   validator=Validators.range(1, 10))
            
            # 音频设置
            self.config_binder.bind("audio.codec", "audio_codec_combo", "AAC")
            self.config_binder.bind("audio.bitrate", "audio_bitrate_combo", "192 kbps")
            self.config_binder.bind("audio.normalize", "audio_normalize_check", True)
            
            # 输出设置
            output_path = str(Path.home() / "Videos")
            self.config_binder.bind("output.path", "output_path", output_path)
            self.config_binder.bind("output.filename_format", "filename_format", "{project}_{date}")
            self.config_binder.bind("output.format", "export_format_combo", "MP4")
            
            # 加载配置
            self.config_binder.config_to_ui()
            
            # 连接配置变更信号
            self.config_binder.config_changed.connect(self.on_config_changed)
            
            logger.info("配置绑定设置完成")
            
        except Exception as e:
            logger.error(f"设置配置绑定失败: {str(e)}")
    
    def browse_output_path(self):
        """浏览并选择输出路径"""
        current_path = self.output_path.text()
        if not current_path:
            current_path = str(Path.home())
        
        directory = QFileDialog.getExistingDirectory(
            self, "选择输出目录", current_path
        )
        
        if directory:
            self.output_path.setText(directory)
    
    def apply_preset(self, preset_type):
        """
        应用预设
        
        Args:
            preset_type: 预设类型，可选值: "high", "medium", "low", "mobile"
        """
        if preset_type == "high":
            # 高质量预设
            self.resolution_combo.setCurrentText("1920x1080")
            self.framerate_combo.setCurrentText("60fps")
            self.codec_combo.setCurrentText("H.264")
            self.quality_spin.setValue(10)
            self.audio_codec_combo.setCurrentText("AAC")
            self.audio_bitrate_combo.setCurrentText("320 kbps")
            self.audio_normalize_check.setChecked(True)
            self.export_format_combo.setCurrentText("MP4")
            
            QMessageBox.information(self, "应用预设", "已应用高质量导出预设。")
        
        elif preset_type == "medium":
            # 中等质量预设
            self.resolution_combo.setCurrentText("1280x720")
            self.framerate_combo.setCurrentText("30fps")
            self.codec_combo.setCurrentText("H.264")
            self.quality_spin.setValue(7)
            self.audio_codec_combo.setCurrentText("AAC")
            self.audio_bitrate_combo.setCurrentText("192 kbps")
            self.audio_normalize_check.setChecked(True)
            self.export_format_combo.setCurrentText("MP4")
            
            QMessageBox.information(self, "应用预设", "已应用中等质量导出预设。")
        
        elif preset_type == "low":
            # 低质量预设
            self.resolution_combo.setCurrentText("854x480")
            self.framerate_combo.setCurrentText("24fps")
            self.codec_combo.setCurrentText("H.264")
            self.quality_spin.setValue(5)
            self.audio_codec_combo.setCurrentText("AAC")
            self.audio_bitrate_combo.setCurrentText("128 kbps")
            self.audio_normalize_check.setChecked(False)
            self.export_format_combo.setCurrentText("MP4")
            
            QMessageBox.information(self, "应用预设", "已应用低质量导出预设。")
        
        elif preset_type == "mobile":
            # 移动设备预设
            self.resolution_combo.setCurrentText("640x360")
            self.framerate_combo.setCurrentText("30fps")
            self.codec_combo.setCurrentText("H.264")
            self.quality_spin.setValue(6)
            self.audio_codec_combo.setCurrentText("AAC")
            self.audio_bitrate_combo.setCurrentText("96 kbps")
            self.audio_normalize_check.setChecked(False)
            self.export_format_combo.setCurrentText("MP4")
            
            QMessageBox.information(self, "应用预设", "已应用移动设备导出预设。")
    
    def save_settings(self):
        """保存设置"""
        if self.config_binder:
            # 将UI的值同步到配置
            self.config_binder.ui_to_config()
            
            # 获取配置
            export_config = config_manager.get_config("export")
            
            # 发出信号
            self.settings_saved.emit(export_config)
            
            QMessageBox.information(self, "设置已保存", "导出设置已成功保存。")
            logger.info("导出设置已保存")
        else:
            QMessageBox.warning(self, "保存失败", "配置绑定器未初始化，无法保存设置。")
            logger.warning("保存设置失败：配置绑定器未初始化")
    
    def start_export(self):
        """开始导出"""
        if self.config_binder:
            # 首先保存配置
            self.config_binder.ui_to_config()
            
            # 获取导出配置
            export_config = config_manager.get_config("export")
            
            # 发出导出信号
            self.export_started.emit(export_config)
            
            # 显示导出信息对话框
            output_path = export_config.get("output", {}).get("path", "")
            resolution = export_config.get("video", {}).get("resolution", "")
            
            msg = (
                f"导出配置:\n"
                f"分辨率: {resolution}\n"
                f"输出路径: {output_path}\n\n"
                f"导出已开始，请等待完成..."
            )
            
            QMessageBox.information(self, "导出已开始", msg)
            logger.info(f"开始导出，分辨率: {resolution}, 输出路径: {output_path}")
        else:
            QMessageBox.warning(self, "导出失败", "配置绑定器未初始化，无法开始导出。")
            logger.warning("开始导出失败：配置绑定器未初始化")
    
    def on_config_changed(self, config_type, key, value):
        """
        配置变更回调
        
        Args:
            config_type: 配置类型
            key: 配置键
            value: 新值
        """
        logger.debug(f"配置已变更: {config_type}.{key} = {value}")

class IntegrationExampleApp(QMainWindow):
    """集成示例应用程序"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("配置绑定集成示例")
        self.resize(700, 600)
        
        # 创建中央部件
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建导出设置页面
        self.export_settings_page = ExportSettingsPage()
        self.export_settings_page.settings_saved.connect(self.on_settings_saved)
        self.export_settings_page.export_started.connect(self.on_export_started)
        
        # 添加页面到选项卡
        self.central_widget.addTab(self.export_settings_page, "导出设置")
        
        # 创建其他页面（仅作为示例）
        other_page = QWidget()
        other_layout = QVBoxLayout(other_page)
        other_layout.addWidget(QLabel("这是其他设置页面，用作占位符"))
        
        self.central_widget.addTab(other_page, "其他设置")
        
        # 设置状态栏
        self.statusBar().showMessage("就绪")
    
    def on_settings_saved(self, settings):
        """
        设置保存回调
        
        Args:
            settings: 保存的设置
        """
        self.statusBar().showMessage("设置已保存", 3000)
    
    def on_export_started(self, export_config):
        """
        导出开始回调
        
        Args:
            export_config: 导出配置
        """
        # 更新状态栏
        self.statusBar().showMessage("导出已开始...", 3000)
        
        # 模拟导出过程
        QApplication.processEvents()
        time.sleep(1)  # 模拟处理时间
        self.statusBar().showMessage("导出进行中 (25%)...", 1000)
        
        QApplication.processEvents()
        time.sleep(1)  # 模拟处理时间
        self.statusBar().showMessage("导出进行中 (50%)...", 1000)
        
        QApplication.processEvents()
        time.sleep(1)  # 模拟处理时间
        self.statusBar().showMessage("导出进行中 (75%)...", 1000)
        
        QApplication.processEvents()
        time.sleep(1)  # 模拟处理时间
        self.statusBar().showMessage("导出已完成", 3000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建并显示示例应用
    example_app = IntegrationExampleApp()
    example_app.show()
    
    sys.exit(app.exec()) 