#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能默认值更新器

根据用户使用模式和系统变化，定期更新推荐配置。
"""

import os
import sys
import time
import json
import logging
import threading
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timedelta

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
    from src.config.defaults import smart_defaults
    from src.config.config_manager import config_manager
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    # 占位引用
    smart_defaults = None
    config_manager = None

# 设置日志记录器
logger = get_logger("smart_updater")

class SmartUpdater:
    """智能默认值更新器，根据使用模式和系统变化更新推荐配置"""
    
    def __init__(self, config_manager=None, smart_defaults=None):
        """初始化智能更新器"""
        self.config_manager = config_manager
        self.smart_defaults = smart_defaults
        
        # 使用统计
        self.usage_stats = {
            "export": {
                "resolutions": {},
                "codecs": {},
                "formats": {}
            },
            "interface": {
                "timeline_zoom": {},
                "theme": {}
            },
            "performance": {
                "render_times": [],
                "memory_usage": []
            },
            "first_run": True,
            "last_update": None,
            "update_count": 0,
            "settings_overridden": set()
        }
        
        # 上次更新时间
        self.last_check = datetime.now()
        
        # 更新间隔（默认每天检查一次）
        self.check_interval = timedelta(days=1)
        
        # 加载使用统计
        self._load_usage_stats()
    
    def _load_usage_stats(self) -> bool:
        """从文件加载使用统计"""
        stats_path = os.path.join(root_dir, "configs", "usage_stats.json")
        
        try:
            if os.path.exists(stats_path):
                with open(stats_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 更新统计数据
                    for key, value in data.items():
                        if key in self.usage_stats and isinstance(value, type(self.usage_stats[key])):
                            self.usage_stats[key] = value
                    
                    # 转换集合
                    if "settings_overridden" in data:
                        self.usage_stats["settings_overridden"] = set(data["settings_overridden"])
                    
                    logger.debug("成功加载使用统计数据")
                    return True
            return False
        except Exception as e:
            logger.error(f"加载使用统计数据失败: {str(e)}")
            return False
    
    def _save_usage_stats(self) -> bool:
        """保存使用统计到文件"""
        stats_path = os.path.join(root_dir, "configs", "usage_stats.json")
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(stats_path), exist_ok=True)
            
            # 转换集合为列表以便JSON序列化
            data = {**self.usage_stats}
            data["settings_overridden"] = list(self.usage_stats["settings_overridden"])
            
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("成功保存使用统计数据")
            return True
        except Exception as e:
            logger.error(f"保存使用统计数据失败: {str(e)}")
            return False
    
    def update_export_stats(self, resolution: str, codec: str, format: str) -> None:
        """更新导出统计信息"""
        try:
            # 更新分辨率统计
            if resolution in self.usage_stats["export"]["resolutions"]:
                self.usage_stats["export"]["resolutions"][resolution] += 1
            else:
                self.usage_stats["export"]["resolutions"][resolution] = 1
            
            # 更新编解码器统计
            if codec in self.usage_stats["export"]["codecs"]:
                self.usage_stats["export"]["codecs"][codec] += 1
            else:
                self.usage_stats["export"]["codecs"][codec] = 1
            
            # 更新格式统计
            if format in self.usage_stats["export"]["formats"]:
                self.usage_stats["export"]["formats"][format] += 1
            else:
                self.usage_stats["export"]["formats"][format] = 1
            
            # 保存更新
            self._save_usage_stats()
        except Exception as e:
            logger.error(f"更新导出统计失败: {str(e)}")
    
    def update_interface_stats(self, timeline_zoom: int, theme: str) -> None:
        """更新界面使用统计"""
        try:
            # 更新时间线缩放统计
            zoom_key = str(timeline_zoom)
            if zoom_key in self.usage_stats["interface"]["timeline_zoom"]:
                self.usage_stats["interface"]["timeline_zoom"][zoom_key] += 1
            else:
                self.usage_stats["interface"]["timeline_zoom"][zoom_key] = 1
            
            # 更新主题统计
            if theme in self.usage_stats["interface"]["theme"]:
                self.usage_stats["interface"]["theme"][theme] += 1
            else:
                self.usage_stats["interface"]["theme"][theme] = 1
            
            # 保存更新
            self._save_usage_stats()
        except Exception as e:
            logger.error(f"更新界面统计失败: {str(e)}")
    
    def update_performance_stats(self, render_time: float, memory_usage: float) -> None:
        """更新性能统计信息"""
        try:
            # 添加渲染时间记录（保留最近50条）
            self.usage_stats["performance"]["render_times"].append(render_time)
            self.usage_stats["performance"]["render_times"] = self.usage_stats["performance"]["render_times"][-50:]
            
            # 添加内存使用记录（保留最近50条）
            self.usage_stats["performance"]["memory_usage"].append(memory_usage)
            self.usage_stats["performance"]["memory_usage"] = self.usage_stats["performance"]["memory_usage"][-50:]
            
            # 保存更新
            self._save_usage_stats()
        except Exception as e:
            logger.error(f"更新性能统计失败: {str(e)}")
    
    def record_setting_override(self, setting_path: str) -> None:
        """记录用户手动覆盖的设置"""
        try:
            self.usage_stats["settings_overridden"].add(setting_path)
            self._save_usage_stats()
        except Exception as e:
            logger.error(f"记录设置覆盖失败: {str(e)}")
    
    def get_most_used_setting(self, category: str, setting: str) -> Optional[Any]:
        """获取使用最多的设置值"""
        try:
            if category in self.usage_stats and setting in self.usage_stats[category]:
                stats = self.usage_stats[category][setting]
                if stats:
                    return max(stats.items(), key=lambda x: x[1])[0]
            return None
        except Exception as e:
            logger.error(f"获取使用最多的设置失败: {str(e)}")
            return None
    
    def check_and_update(self, force=False) -> bool:
        """
        检查并更新智能默认值
        
        Args:
            force: 是否强制更新，忽略时间间隔
            
        Returns:
            bool: 是否进行了更新
        """
        now = datetime.now()
        
        # 检查是否需要更新
        if not force and (now - self.last_check) < self.check_interval:
            return False
        
        try:
            if self.config_manager is None or self.smart_defaults is None:
                logger.error("配置管理器或智能默认值引擎未初始化")
                return False
            
            # 更新检查时间
            self.last_check = now
            
            # 是否首次运行
            is_first_run = self.usage_stats["first_run"]
            
            # 获取智能推荐设置
            smart_settings = self.smart_defaults.get_all_smart_defaults()
            
            # 需要更新的设置
            updates = []
            
            # 检查硬件相关设置
            hw_settings = {
                "resolution": ("user", "export.resolution"),
                "frame_rate": ("user", "export.frame_rate"),
                "gpu_memory": ("system", "gpu.memory_limit"),
                "cpu_threads": ("system", "cpu.threads"),
                "cache_size": ("system", "cache.size_limit")
            }
            
            for setting, (config_type, config_key) in hw_settings.items():
                # 跳过用户手动覆盖的设置
                if f"{config_type}.{config_key}" in self.usage_stats["settings_overridden"]:
                    continue
                
                smart_value = smart_settings["hardware"].get(setting)
                if smart_value is not None:
                    try:
                        current_value = self.config_manager.get_config(config_type, config_key)
                        
                        # 首次运行或硬件推荐值变化，更新设置
                        if is_first_run or current_value != smart_value:
                            updates.append((config_type, config_key, smart_value, current_value))
                    except:
                        # 设置不存在，添加
                        updates.append((config_type, config_key, smart_value, None))
            
            # 根据使用统计更新软件设置
            if not is_first_run:
                # 检查导出设置
                most_used_resolution = self.get_most_used_setting("export", "resolutions")
                if most_used_resolution and "user.export.resolution" not in self.usage_stats["settings_overridden"]:
                    current = self.config_manager.get_config("user", "export.resolution")
                    if current != most_used_resolution:
                        updates.append(("user", "export.resolution", most_used_resolution, current))
                
                most_used_codec = self.get_most_used_setting("export", "codecs")
                if most_used_codec and "user.export.codec" not in self.usage_stats["settings_overridden"]:
                    current = self.config_manager.get_config("user", "export.codec")
                    if current != most_used_codec:
                        updates.append(("user", "export.codec", most_used_codec, current))
                
                most_used_format = self.get_most_used_setting("export", "formats")
                if most_used_format and "user.export.format" not in self.usage_stats["settings_overridden"]:
                    current = self.config_manager.get_config("user", "export.format")
                    if current != most_used_format:
                        updates.append(("user", "export.format", most_used_format, current))
                
                # 检查界面设置
                most_used_zoom = self.get_most_used_setting("interface", "timeline_zoom")
                if most_used_zoom and "user.interface.timeline_zoom" not in self.usage_stats["settings_overridden"]:
                    current = self.config_manager.get_config("user", "interface.timeline_zoom")
                    if str(current) != most_used_zoom:
                        updates.append(("user", "interface.timeline_zoom", int(most_used_zoom), current))
                
                most_used_theme = self.get_most_used_setting("interface", "theme")
                if most_used_theme and "app.theme" not in self.usage_stats["settings_overridden"]:
                    current = self.config_manager.get_config("app", "theme")
                    if current != most_used_theme:
                        updates.append(("app", "theme", most_used_theme, current))
            
            # 应用更新
            for config_type, config_key, new_value, old_value in updates:
                try:
                    self.config_manager.set_config(config_type, config_key, new_value)
                    logger.info(f"已更新智能设置 {config_type}.{config_key}: {old_value} -> {new_value}")
                except Exception as e:
                    logger.error(f"更新设置 {config_type}.{config_key} 失败: {str(e)}")
            
            # 更新统计信息
            self.usage_stats["first_run"] = False
            self.usage_stats["last_update"] = now.isoformat()
            self.usage_stats["update_count"] += 1
            self._save_usage_stats()
            
            return len(updates) > 0
            
        except Exception as e:
            logger.error(f"检查和更新智能默认值失败: {str(e)}")
            return False
    
    def start_auto_update(self, interval_days=1) -> None:
        """
        启动自动更新线程
        
        Args:
            interval_days: 检查间隔天数
        """
        self.check_interval = timedelta(days=interval_days)
        
        def update_thread():
            while True:
                try:
                    self.check_and_update()
                    # 睡眠1小时检查一次
                    time.sleep(3600)
                except Exception as e:
                    logger.error(f"自动更新线程错误: {str(e)}")
                    # 发生错误，睡眠更长时间
                    time.sleep(7200)
        
        # 启动后台线程
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()
        logger.info(f"已启动智能设置自动更新线程，检查间隔: {interval_days}天")


# 创建全局智能更新器实例
try:
    smart_updater = SmartUpdater(config_manager, smart_defaults)
except:
    smart_updater = None

def initialize_updater():
    """初始化智能更新器"""
    global smart_updater
    
    try:
        if smart_updater is None:
            from src.config.defaults import smart_defaults
            from src.config.config_manager import config_manager
            smart_updater = SmartUpdater(config_manager, smart_defaults)
        return smart_updater
    except Exception as e:
        logger.error(f"初始化智能更新器失败: {str(e)}")
        return None

if __name__ == "__main__":
    # 简单测试
    updater = initialize_updater()
    if updater:
        result = updater.check_and_update(force=True)
        print(f"智能设置检查结果: {'已更新' if result else '无需更新'}")
    else:
        print("智能更新器初始化失败") 