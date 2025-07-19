#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志轮换管理模块

管理日志文件的生命周期，包括大小控制、文件轮换、备份和压缩归档。
自动监控日志文件大小，并在达到指定大小时进行轮换处理。
"""

import os
import sys
import shutil
import zipfile
import gzip
import time
import glob
import datetime
import threading
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Callable

from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_log_file_path, get_temp_log_directory

# 模块日志记录器
logger = get_module_logger("log_rotator")

class LogRotator:
    """
    日志轮换管理器
    
    监控和管理日志文件大小，自动进行文件轮换、备份和压缩处理。
    支持按大小、时间或两者结合的轮换策略。
    """
    
    # 默认轮换策略
    ROTATION_POLICY = {
        "size": "100MB",        # 单个日志文件最大大小
        "backup_count": 10,     # 保留10个历史文件
        "compress": True,       # 启用ZIP压缩
        "check_interval": 60,   # 检查间隔（秒）
        "rotate_on_startup": False,  # 启动时是否轮换
        "time_rotation": None,  # None, "daily", "hourly"
    }
    
    # 大小单位转换
    SIZE_UNITS = {
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024
    }
    
    def __init__(self, log_file: Union[str, Path] = None, 
                 policy: Optional[Dict] = None,
                 monitor: bool = True):
        """
        初始化日志轮换管理器
        
        Args:
            log_file: 要监控的日志文件路径
            policy: 轮换策略，覆盖默认配置
            monitor: 是否启动监控线程
        """
        # 确定日志文件路径
        if log_file is None:
            self.log_file = get_log_file_path("app.log")
        else:
            self.log_file = Path(log_file)
            
        # 确保日志文件所在目录存在
        self.log_dir = self.log_file.parent
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份目录
        self.backup_dir = self.log_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 应用策略
        self.policy = self.ROTATION_POLICY.copy()
        if policy:
            self.policy.update(policy)
            
        # 计算大小限制（字节）
        self.size_limit = self._parse_size(self.policy["size"])
        
        # 上次检查时间
        self.last_check_time = time.time()
        self.last_rotation_date = datetime.datetime.now().date()
        
        # 安装监控线程
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # 如果策略要求，启动时自动轮换
        if self.policy["rotate_on_startup"] and self.log_file.exists():
            self.rotate()
            
        # 启动监控线程
        if monitor:
            self.start_monitoring()
        
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节数"""
        # 移除所有空格
        size_str = size_str.strip().upper()
        
        # 检查是否有单位
        unit = "B"
        for u in self.SIZE_UNITS:
            if size_str.endswith(u):
                unit = u
                size_str = size_str[:-len(u)]
                break
                
        try:
            size = float(size_str)
            if unit in self.SIZE_UNITS:
                size *= self.SIZE_UNITS[unit]
            return int(size)
        except ValueError:
            logger.error(f"无法解析大小: {size_str}, 使用默认值: 100MB")
            return 100 * 1024 * 1024
        
    def should_rotate(self) -> bool:
        """检查是否需要轮换日志文件"""
        # 如果文件不存在，不需要轮换
        if not self.log_file.exists():
            return False
            
        # 检查文件大小
        size_check = os.path.getsize(self.log_file) > self.size_limit
        
        # 检查时间轮换
        time_check = False
        if self.policy["time_rotation"] == "daily":
            today = datetime.datetime.now().date()
            time_check = today > self.last_rotation_date
        elif self.policy["time_rotation"] == "hourly":
            now = datetime.datetime.now()
            last_rotation = datetime.datetime.fromtimestamp(self.last_check_time)
            time_check = now.hour > last_rotation.hour or now.date() > last_rotation.date()
            
        return size_check or time_check
    
    def rotate(self) -> bool:
        """执行日志轮换"""
        if not self.log_file.exists():
            return False
            
        try:
            # 获取当前时间戳
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 创建备份文件名
            backup_name = f"{self.log_file.stem}_{timestamp}{self.log_file.suffix}"
            backup_path = self.backup_dir / backup_name
            
            # 记录轮换操作
            logger.info(f"轮换日志文件: {self.log_file} -> {backup_path}")
            
            # 移动当前日志到备份目录
            shutil.move(str(self.log_file), str(backup_path))
            
            # 压缩备份
            if self.policy["compress"]:
                self._compress_log(backup_path)
                
            # 清理过期备份
            self._cleanup_old_backups()
            
            # 更新最后轮换时间
            self.last_rotation_date = datetime.datetime.now().date()
            self.last_check_time = time.time()
            
            return True
        except Exception as e:
            logger.error(f"日志轮换失败: {str(e)}")
            return False
            
    def _compress_log(self, log_path: Path) -> Optional[Path]:
        """压缩日志文件"""
        try:
            # 创建zip文件名
            zip_path = log_path.with_suffix('.zip')
            
            # 创建ZIP归档
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(log_path, arcname=log_path.name)
                
            # 删除原始日志文件
            log_path.unlink()
            
            logger.info(f"日志压缩完成: {zip_path}")
            return zip_path
        except Exception as e:
            logger.error(f"压缩日志文件失败: {str(e)}")
            return None
            
    def _cleanup_old_backups(self) -> int:
        """清理过期的备份文件"""
        backup_count = self.policy["backup_count"]
        if backup_count <= 0:
            return 0
            
        try:
            # 获取所有备份文件
            backups = []
            
            # 查找所有相关备份（未压缩和压缩的）
            pattern = f"{self.log_file.stem}_*{self.log_file.suffix}"
            backups.extend(self.backup_dir.glob(pattern))
            
            pattern = f"{self.log_file.stem}_*.zip"
            backups.extend(self.backup_dir.glob(pattern))
            
            # 如果备份数量未超过限制，不需要清理
            if len(backups) <= backup_count:
                return 0
                
            # 按修改时间排序
            backups.sort(key=lambda p: p.stat().st_mtime)
            
            # 删除最旧的备份
            to_delete = backups[:-backup_count]
            deleted_count = 0
            
            for backup in to_delete:
                try:
                    backup.unlink()
                    deleted_count += 1
                    logger.info(f"删除过期备份: {backup}")
                except Exception as e:
                    logger.error(f"删除备份失败: {backup}, 错误: {str(e)}")
                    
            return deleted_count
        except Exception as e:
            logger.error(f"清理备份失败: {str(e)}")
            return 0
            
    def start_monitoring(self) -> None:
        """启动日志监控线程"""
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            return
            
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="LogRotatorMonitor"
        )
        self.monitor_thread.start()
        logger.info(f"已启动日志轮换监控: {self.log_file}")
        
    def stop_monitoring(self) -> None:
        """停止日志监控线程"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            return
            
        self.stop_event.set()
        self.monitor_thread.join(timeout=5.0)
        logger.info("日志轮换监控已停止")
        
    def _monitor_loop(self) -> None:
        """监控线程主循环"""
        while not self.stop_event.is_set():
            try:
                # 检查是否需要轮换
                if self.should_rotate():
                    self.rotate()
                    
                # 等待下一次检查
                check_interval = self.policy["check_interval"]
                for _ in range(int(check_interval / 0.1)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"日志监控线程发生错误: {str(e)}")
                time.sleep(1.0)  # 避免错误情况下CPU占用过高
                
    def __del__(self):
        """析构函数"""
        self.stop_monitoring()


class LogRotationManager:
    """
    日志轮换管理器
    
    统一管理多个日志文件的轮换。
    """
    
    def __init__(self, default_policy: Optional[Dict] = None):
        """
        初始化日志轮换管理器
        
        Args:
            default_policy: 默认轮换策略
        """
        self.rotators = {}
        self.default_policy = default_policy or LogRotator.ROTATION_POLICY.copy()
        
    def add_log(self, log_path: Union[str, Path], policy: Optional[Dict] = None) -> LogRotator:
        """
        添加日志文件到管理器
        
        Args:
            log_path: 日志文件路径
            policy: 轮换策略，覆盖默认策略
            
        Returns:
            该日志的轮换器实例
        """
        log_path = Path(log_path)
        
        # 如果已存在，返回现有旋转器
        if str(log_path) in self.rotators:
            return self.rotators[str(log_path)]
            
        # 创建新的策略，合并默认策略和自定义策略
        effective_policy = self.default_policy.copy()
        if policy:
            effective_policy.update(policy)
            
        # 创建轮换器
        rotator = LogRotator(log_path, effective_policy)
        self.rotators[str(log_path)] = rotator
        
        return rotator
        
    def remove_log(self, log_path: Union[str, Path]) -> None:
        """
        从管理器中移除日志文件
        
        Args:
            log_path: 日志文件路径
        """
        log_path = str(Path(log_path))
        if log_path in self.rotators:
            # 停止监控
            self.rotators[log_path].stop_monitoring()
            # 从字典中移除
            del self.rotators[log_path]
            
    def rotate_all(self) -> Dict[str, bool]:
        """
        轮换所有管理的日志文件
        
        Returns:
            每个日志文件的轮换结果
        """
        results = {}
        for path, rotator in self.rotators.items():
            results[path] = rotator.rotate()
        return results
        
    def shutdown(self) -> None:
        """关闭所有轮换器"""
        for rotator in self.rotators.values():
            rotator.stop_monitoring()
        self.rotators.clear()
        
    def get_status(self) -> Dict[str, Dict]:
        """
        获取所有日志轮换状态
        
        Returns:
            包含每个日志文件状态的字典
        """
        status = {}
        for path, rotator in self.rotators.items():
            status[path] = {
                "size": os.path.getsize(rotator.log_file) if rotator.log_file.exists() else 0,
                "size_limit": rotator.size_limit,
                "rotation_needed": rotator.should_rotate(),
                "backup_count": len(list(rotator.backup_dir.glob(f"{rotator.log_file.stem}_*")))
            }
        return status


# 全局日志轮换管理器
_rotation_manager = None

def get_log_rotation_manager() -> LogRotationManager:
    """
    获取全局日志轮换管理器
    
    Returns:
        日志轮换管理器实例
    """
    global _rotation_manager
    if _rotation_manager is None:
        _rotation_manager = LogRotationManager()
    return _rotation_manager

def setup_standard_log_rotation():
    """
    配置标准日志轮换
    
    配置应用程序的主要日志文件的轮换
    """
    manager = get_log_rotation_manager()
    
    # 主应用日志
    manager.add_log(get_log_file_path("app.log"))
    
    # 错误日志（较少轮换，保留更多备份）
    manager.add_log(
        get_log_file_path("error.log"),
        {
            "size": "200MB",
            "backup_count": 20
        }
    )
    
    # 实时日志目录
    realtime_dir = get_log_directory() / "realtime"
    if realtime_dir.exists():
        for log_file in realtime_dir.glob("*.jsonl"):
            manager.add_log(
                log_file,
                {
                    "size": "500MB",
                    "time_rotation": "daily"
                }
            )
    
    # 结构化日志目录
    structured_dir = get_log_directory() / "structured"
    if structured_dir.exists():
        for log_file in structured_dir.glob("*.jsonl"):
            manager.add_log(log_file)


if __name__ == "__main__":
    # 测试代码
    import tempfile
    import random
    
    # 创建测试日志目录
    test_dir = Path(tempfile.mkdtemp()) / "logs"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_log = test_dir / "test.log"
    
    print(f"测试日志目录: {test_dir}")
    print(f"测试日志文件: {test_log}")
    
    # 创建轮换器（小文件限制，便于测试）
    rotator = LogRotator(
        test_log,
        {
            "size": "10KB",
            "backup_count": 3,
            "check_interval": 1
        }
    )
    
    # 写入测试数据
    for i in range(5):
        print(f"写入数据块 {i+1}...")
        with open(test_log, "a") as f:
            # 写入约3KB数据
            for j in range(100):
                data = f"测试日志数据 {i}-{j}: " + "X" * random.randint(10, 50) + "\n"
                f.write(data)
                
        # 暂停，让轮换器有时间检查
        time.sleep(1.5)
        
        # 显示状态
        if test_log.exists():
            size = os.path.getsize(test_log)
            print(f"当前日志大小: {size / 1024:.2f}KB")
        else:
            print("日志文件已轮换")
            
        # 显示备份文件
        backups = list(rotator.backup_dir.glob("*"))
        print(f"备份文件数量: {len(backups)}")
        for backup in backups:
            print(f"  {backup.name} - {backup.stat().st_size / 1024:.2f}KB")
            
    # 停止监控
    rotator.stop_monitoring()
    print("测试完成") 