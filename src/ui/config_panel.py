#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置面板

提供一个UI界面，用于编辑和管理配置项，集成了配置绑定器实现配置与UI的双向同步。
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QScrollArea, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QFileDialog, QSlider,
    QGroupBox, QFormLayout, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QIcon

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

# 导入配置绑定器
try:
    from src.ui.ui_config_panel import ConfigBinder, Validators, Transformers, ResolutionTransformer
    from src.config import config_manager
    from src.utils.log_handler import get_logger
except ImportError as e:
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    # 创建空的模拟对象
    class MockObject:
        def __init__(self):
            pass
    
    ConfigBinder = MockObject
    Validators = MockObject
    Transformers = MockObject
    ResolutionTransformer = MockObject
    config_manager = MockObject()

# 设置日志记录器
logger = get_logger("config_panel")

class ConfigPanel(QWidget):
    """配置面板，用于编辑和管理配置项"""
    
    # 定义信号
    config_saved = pyqtSignal(dict)  # 配置保存信号
    config_changed = pyqtSignal(str, str, object)  # 配置变更信号 (配置类型, 键, 值)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_elements = {}  # UI元素字典
        self.config_binders = {}  # 配置绑定器字典
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("配置面板")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标签和按钮布局
        header_layout = QHBoxLayout()
        title_label = QLabel("配置管理")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # 添加保存和重置按钮
        self.save_button = QPushButton("保存配置")
        self.save_button.clicked.connect(self.save_all_configs)
        self.reset_button = QPushButton("重置选项")
        self.reset_button.clicked.connect(self.reset_configs)
        
        header_layout.addWidget(self.save_button)
        header_layout.addWidget(self.reset_button)
        
        main_layout.addLayout(header_layout)
        
        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        
        # 创建各个配置选项卡
        self.create_user_settings_tab()
        self.create_export_settings_tab()
        self.create_system_settings_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # 创建配置绑定器
        self.setup_config_binders()
        
        # 加载配置到UI
        self.load_configs()
    
    def create_user_settings_tab(self):
        """创建用户设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # ===== 常规设置组 =====
        general_group = QGroupBox("常规设置")
        general_form = QFormLayout(general_group)
        
        # 语言模式
        self.lang_mode_combo = QComboBox()
        self.lang_mode_combo.addItems(["中文", "英文", "自动检测"])
        self.ui_elements["lang_mode_combo"] = self.lang_mode_combo
        general_form.addRow("语言模式:", self.lang_mode_combo)
        
        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "系统默认"])
        self.ui_elements["theme_combo"] = self.theme_combo
        general_form.addRow("界面主题:", self.theme_combo)
        
        # 自动保存
        self.auto_save_check = QCheckBox("启用")
        self.ui_elements["auto_save_check"] = self.auto_save_check
        general_form.addRow("自动保存:", self.auto_save_check)
        
        # 自动保存间隔
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setSuffix(" 分钟")
        self.ui_elements["auto_save_interval"] = self.auto_save_interval
        general_form.addRow("保存间隔:", self.auto_save_interval)
        
        # ===== 剪辑设置组 =====
        clip_group = QGroupBox("剪辑设置")
        clip_form = QFormLayout(clip_group)
        
        # 默认转场
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["淡入淡出", "擦除", "溶解", "无"])
        self.ui_elements["transition_combo"] = self.transition_combo
        clip_form.addRow("默认转场:", self.transition_combo)
        
        # 默认转场时长
        self.transition_duration = QDoubleSpinBox()
        self.transition_duration.setRange(0.1, 5.0)
        self.transition_duration.setSingleStep(0.1)
        self.transition_duration.setSuffix(" 秒")
        self.ui_elements["transition_duration"] = self.transition_duration
        clip_form.addRow("转场时长:", self.transition_duration)
        
        # 启用音频淡入淡出
        self.audio_fade_check = QCheckBox("启用")
        self.ui_elements["audio_fade_check"] = self.audio_fade_check
        clip_form.addRow("音频淡变:", self.audio_fade_check)
        
        # 音频淡变时长
        self.audio_fade_duration = QDoubleSpinBox()
        self.audio_fade_duration.setRange(0.0, 3.0)
        self.audio_fade_duration.setSingleStep(0.1)
        self.audio_fade_duration.setSuffix(" 秒")
        self.ui_elements["audio_fade_duration"] = self.audio_fade_duration
        clip_form.addRow("淡变时长:", self.audio_fade_duration)
        
        # 添加组到布局
        scroll_layout.addWidget(general_group)
        scroll_layout.addWidget(clip_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(tab, "用户设置")
    
    def create_export_settings_tab(self):
        """创建导出设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # ===== 视频导出设置组 =====
        video_group = QGroupBox("视频导出设置")
        video_form = QFormLayout(video_group)
        
        # 分辨率
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "854x480", "640x360", "原始分辨率"])
        self.ui_elements["resolution_combo"] = self.resolution_combo
        video_form.addRow("导出分辨率:", self.resolution_combo)
        
        # 帧率
        self.framerate_combo = QComboBox()
        self.framerate_combo.addItems(["60fps", "30fps", "25fps", "24fps", "原始帧率"])
        self.ui_elements["framerate_combo"] = self.framerate_combo
        video_form.addRow("帧率:", self.framerate_combo)
        
        # 视频编码
        self.video_codec_combo = QComboBox()
        self.video_codec_combo.addItems(["H.264", "H.265", "ProRes", "VP9"])
        self.ui_elements["video_codec_combo"] = self.video_codec_combo
        video_form.addRow("视频编码:", self.video_codec_combo)
        
        # 视频比特率
        self.video_bitrate = QComboBox()
        self.video_bitrate.addItems(["15 Mbps", "10 Mbps", "8 Mbps", "5 Mbps", "3 Mbps"])
        self.ui_elements["video_bitrate"] = self.video_bitrate
        video_form.addRow("视频比特率:", self.video_bitrate)
        
        # ===== 音频导出设置组 =====
        audio_group = QGroupBox("音频导出设置")
        audio_form = QFormLayout(audio_group)
        
        # 音频编码
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(["AAC", "MP3", "PCM", "FLAC"])
        self.ui_elements["audio_codec_combo"] = self.audio_codec_combo
        audio_form.addRow("音频编码:", self.audio_codec_combo)
        
        # 音频比特率
        self.audio_bitrate = QComboBox()
        self.audio_bitrate.addItems(["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps"])
        self.ui_elements["audio_bitrate"] = self.audio_bitrate
        audio_form.addRow("音频比特率:", self.audio_bitrate)
        
        # 采样率
        self.sample_rate = QComboBox()
        self.sample_rate.addItems(["48 kHz", "44.1 kHz", "32 kHz", "原始采样率"])
        self.ui_elements["sample_rate"] = self.sample_rate
        audio_form.addRow("采样率:", self.sample_rate)
        
        # ===== 输出路径设置组 =====
        output_group = QGroupBox("输出设置")
        output_form = QFormLayout(output_group)
        
        # 输出路径
        self.output_path_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("默认输出路径")
        self.ui_elements["output_path"] = self.output_path
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_output_path)
        
        self.output_path_layout.addWidget(self.output_path)
        self.output_path_layout.addWidget(self.browse_button)
        
        output_form.addRow("输出路径:", self.output_path_layout)
        
        # 文件名格式
        self.filename_format = QLineEdit()
        self.filename_format.setPlaceholderText("例如: {project}_{date}_{time}")
        self.ui_elements["filename_format"] = self.filename_format
        output_form.addRow("文件名格式:", self.filename_format)
        
        # 添加组到布局
        scroll_layout.addWidget(video_group)
        scroll_layout.addWidget(audio_group)
        scroll_layout.addWidget(output_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(tab, "导出设置")
    
    def create_system_settings_tab(self):
        """创建系统设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # ===== 性能设置组 =====
        performance_group = QGroupBox("性能设置")
        performance_form = QFormLayout(performance_group)
        
        # 线程数
        self.threads_spinbox = QSpinBox()
        self.threads_spinbox.setRange(1, 16)
        self.ui_elements["threads_spinbox"] = self.threads_spinbox
        performance_form.addRow("处理线程数:", self.threads_spinbox)
        
        # 内存限制
        self.memory_limit = QSpinBox()
        self.memory_limit.setRange(512, 16384)
        self.memory_limit.setSingleStep(512)
        self.memory_limit.setSuffix(" MB")
        self.ui_elements["memory_limit"] = self.memory_limit
        performance_form.addRow("内存限制:", self.memory_limit)
        
        # 使用GPU加速
        self.use_gpu_check = QCheckBox("启用 (如可用)")
        self.ui_elements["use_gpu_check"] = self.use_gpu_check
        performance_form.addRow("GPU加速:", self.use_gpu_check)
        
        # ===== 缓存设置组 =====
        cache_group = QGroupBox("缓存设置")
        cache_form = QFormLayout(cache_group)
        
        # 启用缓存
        self.use_cache_check = QCheckBox("启用")
        self.ui_elements["use_cache_check"] = self.use_cache_check
        cache_form.addRow("视频缓存:", self.use_cache_check)
        
        # 缓存路径
        self.cache_path_layout = QHBoxLayout()
        self.cache_path = QLineEdit()
        self.ui_elements["cache_path"] = self.cache_path
        
        self.cache_browse_button = QPushButton("浏览...")
        self.cache_browse_button.clicked.connect(self.browse_cache_path)
        
        self.cache_path_layout.addWidget(self.cache_path)
        self.cache_path_layout.addWidget(self.cache_browse_button)
        
        cache_form.addRow("缓存路径:", self.cache_path_layout)
        
        # 缓存大小限制
        self.cache_size_limit = QSpinBox()
        self.cache_size_limit.setRange(1, 100)
        self.cache_size_limit.setSuffix(" GB")
        self.ui_elements["cache_size_limit"] = self.cache_size_limit
        cache_form.addRow("缓存大小:", self.cache_size_limit)
        
        # 自动清理缓存
        self.auto_clean_cache = QCheckBox("启用")
        self.ui_elements["auto_clean_cache"] = self.auto_clean_cache
        cache_form.addRow("自动清理:", self.auto_clean_cache)
        
        # 添加组到布局
        scroll_layout.addWidget(performance_group)
        scroll_layout.addWidget(cache_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(tab, "系统设置")
    
    def setup_config_binders(self):
        """设置配置绑定器"""
        # 用户设置绑定器
        user_binder = ConfigBinder(self.ui_elements, "user")
        user_binder.config_changed.connect(lambda ctype, key, val: self.config_changed.emit(ctype, key, val))
        
        # 绑定用户设置
        user_binder.bind("interface.language_mode", "lang_mode_combo", "中文")
        user_binder.bind("interface.theme", "theme_combo", "系统默认")
        user_binder.bind("editing.auto_save", "auto_save_check", True)
        user_binder.bind("editing.auto_save_interval", "auto_save_interval", 5, 
                        validator=Validators.range(1, 60))
        user_binder.bind("editing.default_transition", "transition_combo", "淡入淡出")
        user_binder.bind("editing.transition_duration", "transition_duration", 0.5, 
                        validator=Validators.range(0.1, 5.0))
        user_binder.bind("editing.audio_fade", "audio_fade_check", True)
        user_binder.bind("editing.audio_fade_duration", "audio_fade_duration", 0.3, 
                        validator=Validators.range(0.0, 3.0))
        
        # 导出设置绑定器
        export_binder = ConfigBinder(self.ui_elements, "export")
        export_binder.config_changed.connect(lambda ctype, key, val: self.config_changed.emit(ctype, key, val))
        
        # 绑定导出设置
        export_binder.bind("video.resolution", "resolution_combo", "1920x1080")
        export_binder.bind("video.framerate", "framerate_combo", "30fps")
        export_binder.bind("video.codec", "video_codec_combo", "H.264")
        export_binder.bind("video.bitrate", "video_bitrate", "10 Mbps")
        export_binder.bind("audio.codec", "audio_codec_combo", "AAC")
        export_binder.bind("audio.bitrate", "audio_bitrate", "192 kbps")
        export_binder.bind("audio.sample_rate", "sample_rate", "48 kHz")
        
        # 使用转换器处理路径
        export_binder.bind("output.path", "output_path", str(Path.home() / "Videos"),
                          transformer=Transformers.path_to_string())
        export_binder.bind("output.filename_format", "filename_format", "{project}_{date}")
        
        # 系统设置绑定器
        system_binder = ConfigBinder(self.ui_elements, "system")
        system_binder.config_changed.connect(lambda ctype, key, val: self.config_changed.emit(ctype, key, val))
        
        # 绑定系统设置
        import multiprocessing
        cpu_count = max(1, multiprocessing.cpu_count() - 1)
        system_binder.bind("performance.threads", "threads_spinbox", cpu_count, 
                          validator=Validators.range(1, 16))
        system_binder.bind("performance.memory_limit", "memory_limit", 2048, 
                          validator=Validators.range(512, 16384))
        system_binder.bind("performance.use_gpu", "use_gpu_check", True)
        system_binder.bind("cache.enabled", "use_cache_check", True)
        
        # 缓存路径
        default_cache_path = str(Path.home() / "AppData" / "Local" / "VisionAI-ClipsMaster" / "cache")
        system_binder.bind("cache.path", "cache_path", default_cache_path,
                          transformer=Transformers.path_to_string())
        system_binder.bind("cache.size_limit", "cache_size_limit", 10, 
                          validator=Validators.range(1, 100))
        system_binder.bind("cache.auto_clean", "auto_clean_cache", True)
        
        # 存储配置绑定器
        self.config_binders["user"] = user_binder
        self.config_binders["export"] = export_binder
        self.config_binders["system"] = system_binder
    
    def load_configs(self):
        """加载配置到UI"""
        for binder in self.config_binders.values():
            binder.config_to_ui()
    
    def save_all_configs(self):
        """保存所有配置"""
        for config_type, binder in self.config_binders.items():
            binder.ui_to_config()
        
        # 发出保存信号
        combined_config = {}
        for config_type in self.config_binders.keys():
            combined_config[config_type] = config_manager.get_config(config_type)
        
        self.config_saved.emit(combined_config)
        
        QMessageBox.information(self, "配置已保存", "所有配置已成功保存。")
    
    def reset_configs(self):
        """重置配置到默认值"""
        result = QMessageBox.question(
            self, 
            "重置配置", 
            "确定要将所有配置重置为默认值吗？这将丢失您的所有自定义设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # 重新加载默认值
            for binder in self.config_binders.values():
                binder.config_to_ui()
    
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
    
    def browse_cache_path(self):
        """浏览并选择缓存路径"""
        current_path = self.cache_path.text()
        if not current_path:
            current_path = str(Path.home())
        
        directory = QFileDialog.getExistingDirectory(
            self, "选择缓存目录", current_path
        )
        
        if directory:
            self.cache_path.setText(directory)

# 使用示例
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    config_panel = ConfigPanel()
    config_panel.resize(600, 500)
    config_panel.show()
    
    sys.exit(app.exec()) 