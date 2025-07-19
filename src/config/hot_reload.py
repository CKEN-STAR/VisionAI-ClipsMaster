#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置热重载监听器

监控配置文件的变更，并在文件被修改时自动重新加载，
使配置更改无需重启应用即可生效。支持JSON和YAML格式。
"""

import os
import sys
import time
import json
import yaml
import logging
import threading
from typing import Dict, List, Any, Callable, Optional, Set, Union
from pathlib import Path
import datetime

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    from src.utils.log_handler import get_logger
    from src.config.path_resolver import resolve_special_path, normalize_path
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    print("警告: watchdog库未安装，配置热重载功能将无法使用")
    print("请安装必要的依赖: pip install watchdog")

# 设置日志记录器
logger = get_logger("config_hot_reload")

# 配置文件默认目录
DEFAULT_CONFIG_DIR = os.path.join(root_dir, "configs")

class ConfigFileHandler(FileSystemEventHandler):
    """配置文件事件处理器，响应文件系统事件"""
    
    def __init__(self, watcher):
        """
        初始化处理器
        
        Args:
            watcher: 配置观察器实例
        """
        self.watcher = watcher
        super().__init__()
    
    def on_modified(self, event):
        """
        处理文件修改事件
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            filepath = event.src_path
            if self.watcher.is_watched_file(filepath):
                logger.info(f"检测到配置文件变更: {filepath}")
                self.watcher.process_file_change(filepath)
    
    def on_created(self, event):
        """
        处理文件创建事件
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            filepath = event.src_path
            if self.watcher.should_watch_file(filepath):
                logger.info(f"检测到新配置文件: {filepath}")
                self.watcher.add_watch_file(filepath)
                self.watcher.process_file_change(filepath)


class ConfigWatcher:
    """配置文件观察器，监控配置文件变更并触发重新加载"""
    
    def __init__(self, config_dir: Optional[str] = None, patterns: List[str] = None):
        """
        初始化配置观察器
        
        Args:
            config_dir: 配置文件目录，默认为项目的configs目录
            patterns: 要监控的文件模式列表，如["*.json", "*.yaml"]
        """
        self.config_dir = resolve_special_path(config_dir or DEFAULT_CONFIG_DIR)
        self.patterns = patterns or ["*.json", "*.yaml", "*.yml"]
        self.watched_files = set()
        self.file_timestamps = {}
        self.callbacks = {}
        self.observer = None
        self.handler = None
        self.lock = threading.RLock()
        self.initialized = False
        self.running = False
        
        # 存储已加载的配置
        self.configs = {}
        
        logger.info(f"初始化配置热重载监听器, 监控目录: {self.config_dir}")
    
    def start(self):
        """启动配置文件监控"""
        if self.running:
            logger.warning("配置监控器已经在运行")
            return
        
        with self.lock:
            try:
                self.handler = ConfigFileHandler(self)
                self.observer = Observer()
                self.observer.schedule(self.handler, self.config_dir, recursive=True)
                self.observer.start()
                self.running = True
                self.scan_config_files()
                logger.info("配置热重载监控器已启动")
            except Exception as e:
                logger.error(f"启动配置监控器失败: {str(e)}")
                self.running = False
                if self.observer:
                    self.observer.stop()
                    self.observer = None
    
    def stop(self):
        """停止配置文件监控"""
        if not self.running:
            logger.warning("配置监控器未在运行")
            return
        
        with self.lock:
            try:
                if self.observer:
                    self.observer.stop()
                    self.observer.join()
                    self.observer = None
                self.running = False
                logger.info("配置热重载监控器已停止")
            except Exception as e:
                logger.error(f"停止配置监控器失败: {str(e)}")
    
    def scan_config_files(self):
        """扫描配置目录，初始加载所有匹配的配置文件"""
        config_files = []
        
        # 扫描所有匹配的文件
        for pattern in self.patterns:
            import glob
            pattern_path = os.path.join(self.config_dir, pattern)
            matched_files = glob.glob(pattern_path)
            config_files.extend(matched_files)
        
        # 添加到监控列表
        for filepath in config_files:
            self.add_watch_file(filepath)
        
        logger.info(f"已扫描配置文件: 找到 {len(config_files)} 个匹配文件")
    
    def add_watch_file(self, filepath: str):
        """
        添加文件到监控列表
        
        Args:
            filepath: 文件路径
        """
        with self.lock:
            normalized_path = normalize_path(filepath)
            if normalized_path not in self.watched_files:
                self.watched_files.add(normalized_path)
                self.file_timestamps[normalized_path] = os.path.getmtime(normalized_path)
                logger.debug(f"添加监控文件: {normalized_path}")
    
    def remove_watch_file(self, filepath: str):
        """
        从监控列表移除文件
        
        Args:
            filepath: 文件路径
        """
        with self.lock:
            normalized_path = normalize_path(filepath)
            if normalized_path in self.watched_files:
                self.watched_files.remove(normalized_path)
                if normalized_path in self.file_timestamps:
                    del self.file_timestamps[normalized_path]
                logger.debug(f"移除监控文件: {normalized_path}")
    
    def is_watched_file(self, filepath: str) -> bool:
        """
        检查文件是否在监控列表中
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 如果文件在监控列表中返回True
        """
        normalized_path = normalize_path(filepath)
        return normalized_path in self.watched_files
    
    def should_watch_file(self, filepath: str) -> bool:
        """
        检查文件是否应该被监控（匹配模式）
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 如果文件应该被监控返回True
        """
        # 检查文件是否在配置目录下
        normalized_path = normalize_path(filepath)
        config_dir = normalize_path(self.config_dir)
        
        if not normalized_path.startswith(config_dir):
            return False
        
        # 检查文件扩展名是否匹配
        from fnmatch import fnmatch
        filename = os.path.basename(normalized_path)
        
        for pattern in self.patterns:
            if fnmatch(filename, pattern):
                return True
        
        return False
    
    def register_callback(self, filepath: str, callback: Callable[[Dict[str, Any]], None]):
        """
        为指定文件注册配置变更回调函数
        
        Args:
            filepath: 配置文件路径
            callback: 回调函数，接收加载的配置作为参数
        """
        with self.lock:
            normalized_path = normalize_path(filepath)
            
            if normalized_path not in self.callbacks:
                self.callbacks[normalized_path] = []
            
            if callback not in self.callbacks[normalized_path]:
                self.callbacks[normalized_path].append(callback)
                logger.debug(f"为文件 {normalized_path} 注册回调函数")
    
    def unregister_callback(self, filepath: str, callback: Callable[[Dict[str, Any]], None]):
        """
        为指定文件取消注册配置变更回调函数
        
        Args:
            filepath: 配置文件路径
            callback: 回调函数
        """
        with self.lock:
            normalized_path = normalize_path(filepath)
            
            if normalized_path in self.callbacks:
                if callback in self.callbacks[normalized_path]:
                    self.callbacks[normalized_path].remove(callback)
                    logger.debug(f"为文件 {normalized_path} 取消注册回调函数")
    
    def process_file_change(self, filepath: str):
        """
        处理文件变更
        
        Args:
            filepath: 变更的文件路径
        """
        with self.lock:
            normalized_path = normalize_path(filepath)
            
            # 获取当前文件修改时间
            try:
                current_mtime = os.path.getmtime(normalized_path)
            except (FileNotFoundError, PermissionError) as e:
                logger.error(f"无法获取文件修改时间: {normalized_path}, 错误: {str(e)}")
                return
            
            # 检查文件是否真的变更了（避免重复触发）
            last_mtime = self.file_timestamps.get(normalized_path, 0)
            
            # 文件修改时间相同，跳过处理
            if current_mtime <= last_mtime:
                logger.debug(f"文件未变更或重复事件: {normalized_path}")
                return
            
            # 更新时间戳
            self.file_timestamps[normalized_path] = current_mtime
            
            # 加载配置文件
            try:
                config = self.load_config_file(normalized_path)
                if config is not None:
                    # 存储配置
                    self.configs[normalized_path] = config
                    
                    # 调用回调函数
                    if normalized_path in self.callbacks:
                        for callback in self.callbacks[normalized_path]:
                            try:
                                callback(config)
                            except Exception as e:
                                logger.error(f"执行回调函数失败: {str(e)}")
                    
                    logger.info(f"成功重新加载配置文件: {normalized_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {normalized_path}, 错误: {str(e)}")
    
    def load_config_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        加载配置文件
        
        Args:
            filepath: 配置文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 加载的配置数据，如果加载失败则返回None
        """
        if not os.path.exists(filepath):
            logger.error(f"配置文件不存在: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                ext = os.path.splitext(filepath)[1].lower()
                
                if ext in ['.json']:
                    return json.load(f)
                elif ext in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    logger.error(f"不支持的配置文件格式: {filepath}")
                    return None
        except Exception as e:
            logger.error(f"读取配置文件失败: {filepath}, 错误: {str(e)}")
            return None
    
    def get_config(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        获取配置数据
        
        Args:
            filepath: 配置文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 已加载的配置数据
        """
        normalized_path = normalize_path(filepath)
        
        # 如果配置未加载，尝试加载
        if normalized_path not in self.configs:
            if os.path.exists(normalized_path):
                config = self.load_config_file(normalized_path)
                if config is not None:
                    self.configs[normalized_path] = config
                    self.add_watch_file(normalized_path)
        
        return self.configs.get(normalized_path)
    
    def reload_all(self):
        """强制重新加载所有监控的配置文件"""
        with self.lock:
            for filepath in list(self.watched_files):
                try:
                    self.process_file_change(filepath)
                except Exception as e:
                    logger.error(f"重新加载配置文件失败: {filepath}, 错误: {str(e)}")
    
    def __del__(self):
        """析构函数，确保停止观察器"""
        self.stop()


# 创建全局单例实例
_instance = None

def get_config_watcher() -> ConfigWatcher:
    """
    获取ConfigWatcher全局单例实例
    
    Returns:
        ConfigWatcher: 配置观察器实例
    """
    global _instance
    if _instance is None:
        _instance = ConfigWatcher()
    return _instance


# 便捷函数
def watch_config(filepath: str, callback: Callable[[Dict[str, Any]], None]):
    """
    监控配置文件并注册回调
    
    Args:
        filepath: 配置文件路径
        callback: 当配置变更时的回调函数
    """
    watcher = get_config_watcher()
    
    # 确保观察器已启动
    if not watcher.running:
        watcher.start()
    
    # 加载当前配置并调用回调
    config = watcher.get_config(filepath)
    if config is not None:
        try:
            callback(config)
        except Exception as e:
            logger.error(f"执行回调函数失败: {str(e)}")
    
    # 注册回调以接收后续更新
    watcher.register_callback(filepath, callback)


def get_config(filepath: str) -> Optional[Dict[str, Any]]:
    """
    获取指定配置文件的数据
    
    Args:
        filepath: 配置文件路径
        
    Returns:
        Optional[Dict[str, Any]]: 配置数据
    """
    watcher = get_config_watcher()
    
    # 确保观察器已启动
    if not watcher.running:
        watcher.start()
    
    return watcher.get_config(filepath)


# 示例使用
if __name__ == "__main__":
    # 设置日志级别
    logger.setLevel(logging.DEBUG)
    
    # 测试回调函数
    def config_changed(config):
        print(f"配置已更改: {config}")
    
    # 启动监控
    watcher = get_config_watcher()
    watcher.start()
    
    # 监控特定文件
    test_config_path = os.path.join(DEFAULT_CONFIG_DIR, "test_config.json")
    
    # 创建测试配置
    if not os.path.exists(test_config_path):
        with open(test_config_path, 'w', encoding='utf-8') as f:
            json.dump({"test": "value", "timestamp": str(datetime.datetime.now())}, f, indent=2)
    
    # 注册回调
    watch_config(test_config_path, config_changed)
    
    print(f"监控配置文件: {test_config_path}")
    print("修改文件内容以查看热重载效果...")
    print("按 Ctrl+C 停止")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("停止监控")
    finally:
        watcher.stop() 