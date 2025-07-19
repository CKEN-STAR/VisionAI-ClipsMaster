#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置绑定插件

提供一个简单的插件类，用于将配置绑定器集成到现有应用程序中。
它作为应用程序和配置绑定器之间的桥梁，简化了配置管理。
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

# 导入配置系统
try:
    from src.ui.ui_config_panel import ConfigBinder, Validators, Transformers
    from src.config import config_manager
    from src.utils.log_handler import get_logger
except ImportError as e:
    # 如果无法导入，使用标准日志
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    # 模拟配置管理器
    class MockConfigManager:
        def __init__(self):
            self.configs = {
                "user": {},
                "system": {},
                "version": {},
                "export": {},
                "app": {}
            }
        
        def get_config(self, config_type, key=None):
            if key is None:
                return self.configs.get(config_type, {})
            
            if "." in key:
                parts = key.split(".")
                value = self.configs.get(config_type, {})
                for part in parts:
                    if part not in value:
                        return None
                    value = value[part]
                return value
            
            return self.configs.get(config_type, {}).get(key)
        
        def set_config(self, config_type, key, value):
            if "." in key:
                parts = key.split(".")
                config = self.configs.setdefault(config_type, {})
                for part in parts[:-1]:
                    config = config.setdefault(part, {})
                config[parts[-1]] = value
            else:
                self.configs.setdefault(config_type, {})[key] = value
    
    config_manager = MockConfigManager()
    
    # 模拟其他类
    class ConfigBinder:
        def __init__(self, *args, **kwargs):
            pass
    
    class Validators:
        pass
    
    class Transformers:
        pass

# 设置日志记录器
logger = get_logger("ui_config_plugin")

class ConfigBinderPlugin:
    """配置绑定插件，用于将配置绑定器集成到应用程序中"""
    
    def __init__(self, app=None):
        """
        初始化配置绑定插件
        
        Args:
            app: 应用程序实例，用于访问UI元素和配置
        """
        self.app = app
        self.binders = {}  # 配置绑定器字典
        self.ui_elements = {}  # UI元素字典
        self.config_mappings = {}  # 配置映射字典
        self.initialized = False
    
    def setup(self, app):
        """
        设置插件，关联应用程序
        
        Args:
            app: 应用程序实例
        """
        self.app = app
        return self
    
    def collect_ui_elements(self):
        """
        收集应用程序中的UI元素
        这个方法需要根据实际应用程序的UI结构进行调整
        """
        if not self.app:
            logger.warning("没有关联应用程序实例，无法收集UI元素")
            return
        
        # 创建UI元素字典
        ui_elements = {}
        
        # 示例: 从应用程序中收集UI元素
        # 这部分需要根据实际应用程序的UI结构进行定制
        try:
            # 导出设置
            ui_elements["resolution_dropdown"] = self.app.resolution_combo
            ui_elements["output_path"] = self.app.output_path
            
            # 语言设置
            ui_elements["language_combo"] = self.app.language_combo
            
            # GPU设置
            ui_elements["use_gpu_checkbox"] = self.app.use_gpu_checkbox
            
            # 其他设置...
            # ...
            
            self.ui_elements = ui_elements
            logger.info(f"成功收集 {len(ui_elements)} 个UI元素")
        except AttributeError as e:
            logger.warning(f"收集UI元素失败: {str(e)}")
    
    def setup_bindings(self, config_type: str, mappings: Dict[str, str], defaults: Dict[str, Any] = None):
        """
        设置配置绑定
        
        Args:
            config_type: 配置类型
            mappings: 配置键到UI元素ID的映射
            defaults: 默认值字典
        """
        if not self.ui_elements:
            logger.warning("没有收集UI元素，请先调用collect_ui_elements()")
            return False
        
        if config_type in self.binders:
            logger.warning(f"配置类型 {config_type} 已经有绑定器，将被覆盖")
        
        # 过滤掉不存在的UI元素ID
        valid_mappings = {}
        for config_key, ui_id in mappings.items():
            if ui_id in self.ui_elements:
                valid_mappings[config_key] = ui_id
            else:
                logger.warning(f"UI元素ID {ui_id} 不存在，忽略配置绑定 {config_key}")
        
        if not valid_mappings:
            logger.warning(f"没有有效的映射，不创建 {config_type} 的绑定器")
            return False
        
        # 创建配置绑定器
        binder = ConfigBinder(self.ui_elements, config_type)
        
        # 绑定配置
        for config_key, ui_id in valid_mappings.items():
            default_value = defaults.get(config_key) if defaults else None
            binder.bind(config_key, ui_id, default_value)
        
        # 保存绑定器和映射
        self.binders[config_type] = binder
        self.config_mappings[config_type] = valid_mappings
        
        logger.info(f"为 {config_type} 创建了绑定器，绑定了 {len(valid_mappings)} 个配置项")
        return True
    
    def load_configs(self):
        """将配置加载到UI界面"""
        for binder in self.binders.values():
            binder.config_to_ui()
        
        logger.info("已将配置加载到UI界面")
    
    def save_configs(self):
        """将UI界面的值保存到配置"""
        for binder in self.binders.values():
            binder.ui_to_config()
        
        logger.info("已将UI界面的值保存到配置")
    
    def register_config_change_callback(self, callback):
        """
        注册配置变更回调函数
        
        Args:
            callback: 回调函数，接收三个参数 (config_type, key, value)
        """
        for binder in self.binders.values():
            binder.config_changed.connect(callback)
    
    def register_ui_update_callback(self, callback):
        """
        注册UI更新回调函数
        
        Args:
            callback: 回调函数，接收两个参数 (ui_id, value)
        """
        for binder in self.binders.values():
            binder.ui_updated.connect(callback)
    
    def initialize_app_settings(self):
        """初始化应用程序设置，通常在应用启动时调用"""
        # 收集UI元素
        self.collect_ui_elements()
        
        # 设置导出配置绑定
        export_mappings = {
            "video.resolution": "resolution_dropdown",
            "output.path": "output_path"
        }
        export_defaults = {
            "video.resolution": "1920x1080",
            "output.path": os.path.join(os.path.expanduser("~"), "Videos")
        }
        self.setup_bindings("export", export_mappings, export_defaults)
        
        # 设置用户配置绑定
        user_mappings = {
            "interface.language": "language_combo"
        }
        user_defaults = {
            "interface.language": "中文"
        }
        self.setup_bindings("user", user_mappings, user_defaults)
        
        # 设置系统配置绑定
        system_mappings = {
            "performance.use_gpu": "use_gpu_checkbox"
        }
        system_defaults = {
            "performance.use_gpu": True
        }
        self.setup_bindings("system", system_mappings, system_defaults)
        
        # 加载配置到UI
        self.load_configs()
        
        self.initialized = True
        logger.info("应用程序设置已初始化")
    
    def register_shutdown_handler(self):
        """注册应用程序关闭时的处理函数，保存配置"""
        if not self.app:
            logger.warning("没有关联应用程序实例，无法注册关闭处理函数")
            return False
        
        # 这里需要根据应用程序框架调整
        try:
            # 对于Qt应用程序
            from PyQt6.QtCore import QCoreApplication
            QCoreApplication.instance().aboutToQuit.connect(self.save_configs)
            logger.info("已注册应用程序关闭时的配置保存函数")
            return True
        except ImportError:
            logger.warning("无法导入Qt库，无法注册关闭处理函数")
            return False
    
    def get_config_value(self, config_type: str, key: str, default=None):
        """
        获取配置值
        
        Args:
            config_type: 配置类型
            key: 配置键
            default: 默认值
            
        Returns:
            配置值，如果不存在则返回默认值
        """
        value = config_manager.get_config(config_type, key)
        return value if value is not None else default
    
    def set_config_value(self, config_type: str, key: str, value):
        """
        设置配置值
        
        Args:
            config_type: 配置类型
            key: 配置键
            value: 配置值
        """
        config_manager.set_config(config_type, key, value)
        
        # 如果这个配置项绑定了UI元素，也更新UI
        if config_type in self.binders:
            binder = self.binders[config_type]
            full_key = f"{config_type}.{key}"
            if full_key in binder.mapping:
                ui_element = binder.mapping[full_key]
                binder._update_ui_element(ui_element, value)
    
    def apply_preset(self, preset_name: str):
        """
        应用预设配置
        
        Args:
            preset_name: 预设名称
        """
        # 这里需要根据实际情况实现预设配置
        if preset_name == "high_quality":
            # 高质量导出预设
            self.set_config_value("export", "video.resolution", "1920x1080")
            self.set_config_value("export", "video.bitrate", "15 Mbps")
            self.set_config_value("export", "audio.bitrate", "320 kbps")
            logger.info("应用高质量导出预设")
        
        elif preset_name == "medium_quality":
            # 中等质量导出预设
            self.set_config_value("export", "video.resolution", "1280x720")
            self.set_config_value("export", "video.bitrate", "8 Mbps")
            self.set_config_value("export", "audio.bitrate", "192 kbps")
            logger.info("应用中等质量导出预设")
        
        elif preset_name == "low_quality":
            # 低质量导出预设
            self.set_config_value("export", "video.resolution", "854x480")
            self.set_config_value("export", "video.bitrate", "3 Mbps")
            self.set_config_value("export", "audio.bitrate", "128 kbps")
            logger.info("应用低质量导出预设")
        
        elif preset_name == "mobile":
            # 移动设备预设
            self.set_config_value("export", "video.resolution", "640x360")
            self.set_config_value("export", "video.bitrate", "1.5 Mbps")
            self.set_config_value("export", "audio.bitrate", "96 kbps")
            logger.info("应用移动设备预设")
        
        # 加载配置到UI
        self.load_configs()

# 工厂函数，方便创建配置绑定插件
def create_config_plugin(app=None):
    """
    创建配置绑定插件
    
    Args:
        app: 应用程序实例
        
    Returns:
        ConfigBinderPlugin: 配置绑定插件实例
    """
    return ConfigBinderPlugin(app)

# 使用示例
if __name__ == "__main__":
    # 模拟应用程序
    class MockApp:
        def __init__(self):
            from PyQt6.QtWidgets import QComboBox, QLineEdit, QCheckBox
            self.resolution_combo = QComboBox()
            self.resolution_combo.addItems(["1920x1080", "1280x720", "854x480", "640x360"])
            
            self.output_path = QLineEdit()
            self.output_path.setText(os.path.expanduser("~/Videos"))
            
            self.language_combo = QComboBox()
            self.language_combo.addItems(["中文", "英文", "自动检测"])
            
            self.use_gpu_checkbox = QCheckBox("使用GPU")
            self.use_gpu_checkbox.setChecked(True)
    
    # 创建模拟应用
    mock_app = MockApp()
    
    # 创建并初始化配置插件
    plugin = create_config_plugin(mock_app)
    plugin.initialize_app_settings()
    
    # 测试获取和设置配置
    print(f"当前分辨率: {plugin.get_config_value('export', 'video.resolution', '默认分辨率')}")
    plugin.set_config_value("export", "video.resolution", "1280x720")
    print(f"新的分辨率: {plugin.get_config_value('export', 'video.resolution')}")
    
    # 应用预设
    plugin.apply_preset("low_quality")
    print(f"预设后的分辨率: {plugin.get_config_value('export', 'video.resolution')}")
    
    # 保存配置
    plugin.save_configs()
    print("配置已保存") 