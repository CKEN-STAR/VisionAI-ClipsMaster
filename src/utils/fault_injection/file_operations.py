#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件操作故障注入模块 - 提供文件操作相关的故障模拟
用于测试系统在文件访问/存储问题时的稳定性
"""

import os
import io
import random
import tempfile
import shutil
import threading
import time
import stat
from typing import Any, Callable, Dict, List, Optional, Union, BinaryIO, TextIO
from pathlib import Path
from unittest.mock import patch

import logging
logger = logging.getLogger(__name__)

from .core import FaultInjector


class FileNotFoundInjector(FaultInjector):
    """文件不存在故障注入器"""
    
    def __init__(self, 
                 target_patterns: List[str] = None,
                 exclude_patterns: List[str] = None,
                 probability: float = 0.1, 
                 enabled: bool = True):
        """
        初始化文件不存在故障注入器
        
        Args:
            target_patterns: 目标文件模式列表，如[".srt", "config."]
            exclude_patterns: 排除文件模式列表
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.target_patterns = target_patterns or [".srt", ".mp4", ".json", "config"]
        self.exclude_patterns = exclude_patterns or ["temp", "backup"]
        
    def should_affect_file(self, filepath: str) -> bool:
        """
        判断是否应该影响指定文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 是否应该影响
        """
        # 首先检查排除模式
        if any(pattern in filepath for pattern in self.exclude_patterns):
            return False
        
        # 然后检查目标模式
        return any(pattern in filepath for pattern in self.target_patterns)
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入文件不存在故障
        
        Args:
            context: 上下文信息，必须包含filepath键
            
        Raises:
            ValueError: 如果上下文中没有filepath键
            FileNotFoundError: 模拟文件不存在
        """
        if not context or "filepath" not in context:
            raise ValueError("上下文必须包含filepath键")
        
        filepath = context["filepath"]
        if not self.should_affect_file(filepath):
            return
            
        logger.debug(f"注入文件不存在故障: {filepath}")
        raise FileNotFoundError(f"模拟的文件不存在: {filepath}")


class FileCorruptionInjector(FaultInjector):
    """文件损坏注入器"""
    
    def __init__(self, 
                 corruption_modes: List[str] = None,
                 target_extensions: List[str] = None,
                 probability: float = 0.1, 
                 enabled: bool = True):
        """
        初始化文件损坏注入器
        
        Args:
            corruption_modes: 损坏模式列表，可选["truncate", "random_bytes", "header_damage", "all"]
            target_extensions: 目标文件扩展名列表，如[".json", ".srt"]
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.corruption_modes = corruption_modes or ["truncate", "random_bytes", "header_damage", "all"]
        self.target_extensions = target_extensions or [".json", ".srt", ".txt", ".yaml", ".csv"]
        
    def should_affect_file(self, filepath: str) -> bool:
        """
        判断是否应该影响指定文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 是否应该影响
        """
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.target_extensions
    
    def corrupt_file_content(self, content: bytes, mode: str = None) -> bytes:
        """
        损坏文件内容
        
        Args:
            content: 原始文件内容
            mode: 损坏模式，如果为None则随机选择
            
        Returns:
            bytes: 损坏后的内容
        """
        if not content:
            return content
            
        if mode is None:
            mode = random.choice(self.corruption_modes)
        
        content_length = len(content)
        if content_length < 10:
            # 文件太小，简单替换几个字节
            return self._inject_random_bytes(content, max(1, content_length // 2))
        
        # 执行特定的损坏模式
        if mode == "truncate" or mode == "all":
            # 截断文件
            truncate_pos = random.randint(content_length // 10, content_length - 10)
            return content[:truncate_pos]
            
        elif mode == "random_bytes" or mode == "all":
            # 注入随机字节
            num_bytes = random.randint(1, min(100, content_length // 10))
            return self._inject_random_bytes(content, num_bytes)
            
        elif mode == "header_damage" or mode == "all":
            # 损坏文件头部
            header_size = min(50, content_length // 5)
            pos = random.randint(0, header_size)
            num_bytes = random.randint(1, 10)
            corrupted = bytearray(content)
            for i in range(num_bytes):
                if pos + i < content_length:
                    corrupted[pos + i] = random.randint(0, 255)
            return bytes(corrupted)
        
        # 默认情况，返回原始内容
        return content
    
    def _inject_random_bytes(self, content: bytes, num_bytes: int) -> bytes:
        """
        在内容中注入随机字节
        
        Args:
            content: 原始内容
            num_bytes: 要注入的字节数
            
        Returns:
            bytes: 注入后的内容
        """
        content_length = len(content)
        corrupted = bytearray(content)
        
        for _ in range(num_bytes):
            pos = random.randint(0, content_length - 1)
            corrupted[pos] = random.randint(0, 255)
            
        return bytes(corrupted)
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入文件损坏故障
        
        Args:
            context: 上下文信息，必须包含filepath和content键
            
        Raises:
            ValueError: 如果上下文中缺少必要的键
        """
        if not context or "filepath" not in context:
            raise ValueError("上下文必须包含filepath键")
        
        filepath = context["filepath"]
        if not self.should_affect_file(filepath):
            return
        
        # 如果上下文中有content，直接修改它
        if "content" in context and isinstance(context["content"], (bytes, bytearray)):
            mode = random.choice(self.corruption_modes)
            logger.debug(f"注入文件内容损坏: {mode} - {filepath}")
            context["content"] = self.corrupt_file_content(context["content"], mode)
            context["corrupted"] = True
            return
            
        # 否则，修改实际文件
        if os.path.exists(filepath) and os.access(filepath, os.R_OK | os.W_OK):
            try:
                mode = random.choice(self.corruption_modes)
                logger.debug(f"注入文件损坏: {mode} - {filepath}")
                
                # 备份原始文件
                backup_file = f"{filepath}.bak"
                shutil.copy2(filepath, backup_file)
                
                # 读取文件内容
                with open(filepath, 'rb') as f:
                    content = f.read()
                
                # 损坏内容
                corrupted = self.corrupt_file_content(content, mode)
                
                # 写回文件
                with open(filepath, 'wb') as f:
                    f.write(corrupted)
                
                # 记录信息以供恢复
                context["backup_file"] = backup_file
                context["original_file"] = filepath
                context["corrupted"] = True
                
            except Exception as e:
                logger.error(f"注入文件损坏失败: {e}")
    
    def restore_file(self, context: Dict[str, Any]) -> bool:
        """
        恢复被损坏的文件
        
        Args:
            context: 上下文信息，必须包含backup_file和original_file键
            
        Returns:
            bool: 是否成功恢复
        """
        if not context or "backup_file" not in context or "original_file" not in context:
            return False
            
        backup = context["backup_file"]
        original = context["original_file"]
        
        if os.path.exists(backup):
            try:
                shutil.copy2(backup, original)
                os.remove(backup)
                logger.debug(f"已恢复文件: {original}")
                return True
            except Exception as e:
                logger.error(f"恢复文件失败: {e}")
                
        return False


class PermissionDeniedInjector(FaultInjector):
    """权限拒绝注入器"""
    
    def __init__(self, 
                 target_operations: List[str] = None,
                 exclude_paths: List[str] = None,
                 probability: float = 0.1, 
                 enabled: bool = True):
        """
        初始化权限拒绝注入器
        
        Args:
            target_operations: 目标操作列表，可选["read", "write", "execute", "all"]
            exclude_paths: 排除路径列表
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.target_operations = target_operations or ["read", "write", "execute", "all"]
        self.exclude_paths = exclude_paths or ["/tmp", "/var/tmp", "C:\\Windows\\Temp"]
        self._permission_lock = threading.RLock()
        self._restricted_files = {}  # filepath -> original_mode
    
    def should_affect_path(self, filepath: str) -> bool:
        """
        判断是否应该影响指定路径
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 是否应该影响
        """
        # 检查排除路径
        return not any(excl in filepath for excl in self.exclude_paths)
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入权限拒绝故障
        
        Args:
            context: 上下文信息，必须包含filepath键，可选operation键
            
        Raises:
            ValueError: 如果上下文中没有filepath键
            PermissionError: 模拟权限拒绝
        """
        if not context or "filepath" not in context:
            raise ValueError("上下文必须包含filepath键")
        
        filepath = context["filepath"]
        if not self.should_affect_path(filepath):
            return
            
        operation = context.get("operation", random.choice(self.target_operations))
        
        # 如果文件存在，修改文件权限
        if os.path.exists(filepath):
            try:
                self._restrict_file_permissions(filepath, operation)
                logger.debug(f"注入权限拒绝: {operation} - {filepath}")
            except Exception as e:
                logger.error(f"修改文件权限失败: {e}")
                
        # 始终抛出权限错误，即使文件不存在
        error_msg = f"模拟的权限拒绝: {operation} - {filepath}"
        raise PermissionError(error_msg)
    
    def _restrict_file_permissions(self, filepath: str, operation: str) -> None:
        """
        限制文件权限
        
        Args:
            filepath: 文件路径
            operation: 操作类型
        """
        with self._permission_lock:
            # 如果已经限制了该文件，不再重复操作
            if filepath in self._restricted_files:
                return
                
            try:
                # 保存原始文件权限
                original_mode = os.stat(filepath).st_mode
                self._restricted_files[filepath] = original_mode
                
                # 设置新权限
                if operation == "read" or operation == "all":
                    # 移除读权限
                    new_mode = original_mode & ~(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                    os.chmod(filepath, new_mode)
                    
                elif operation == "write" or operation == "all":
                    # 移除写权限
                    new_mode = original_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                    os.chmod(filepath, new_mode)
                    
                elif operation == "execute" or operation == "all":
                    # 移除执行权限
                    new_mode = original_mode & ~(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    os.chmod(filepath, new_mode)
                    
                # 设置恢复定时器
                self._schedule_permission_restore(filepath, 30)  # 30秒后恢复
                
            except Exception as e:
                logger.error(f"限制文件权限失败: {e}")
                if filepath in self._restricted_files:
                    del self._restricted_files[filepath]
    
    def _schedule_permission_restore(self, filepath: str, delay: float) -> None:
        """
        计划恢复文件权限
        
        Args:
            filepath: 文件路径
            delay: 延迟时间(秒)
        """
        def restore_permissions():
            with self._permission_lock:
                if filepath in self._restricted_files:
                    try:
                        os.chmod(filepath, self._restricted_files[filepath])
                        del self._restricted_files[filepath]
                        logger.debug(f"已恢复文件权限: {filepath}")
                    except Exception as e:
                        logger.error(f"恢复文件权限失败: {e}")
        
        timer = threading.Timer(delay, restore_permissions)
        timer.daemon = True
        timer.start()


class DiskSpaceInjector(FaultInjector):
    """磁盘空间不足注入器"""
    
    def __init__(self,
                 free_space_mb: float = 0,
                 simulation_mode: str = "exception",
                 duration: float = 60.0,
                 probability: float = 0.05, 
                 enabled: bool = True):
        """
        初始化磁盘空间不足注入器
        
        Args:
            free_space_mb: 模拟的可用空间(MB)
            simulation_mode: 模拟模式，可选["exception", "slow", "intermittent"]
            duration: 模拟持续时间(秒)
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.free_space_mb = free_space_mb
        self.simulation_mode = simulation_mode
        self.duration = duration
        self._simulate_until = 0
        self._lock = threading.RLock()
        
    def is_simulating(self) -> bool:
        """
        检查当前是否正在模拟磁盘空间不足
        
        Returns:
            bool: 是否正在模拟
        """
        with self._lock:
            return time.time() < self._simulate_until
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入磁盘空间不足故障
        
        Args:
            context: 上下文信息
            
        Raises:
            OSError: 磁盘空间不足异常
        """
        with self._lock:
            self._simulate_until = time.time() + self.duration
            
        logger.debug(f"注入磁盘空间不足: 模式={self.simulation_mode}, 持续{self.duration}秒 - {context}")
        
        if self.simulation_mode == "exception":
            raise OSError(28, f"模拟的磁盘空间不足错误 (剩余 {self.free_space_mb} MB)")
            
        elif self.simulation_mode == "slow":
            # 添加延迟，模拟慢速磁盘
            delay = random.uniform(0.5, 2.0)
            time.sleep(delay)
            
        elif self.simulation_mode == "intermittent":
            # 间歇性失败
            if random.random() < 0.5:
                raise OSError(28, f"模拟的间歇性磁盘空间不足错误 (剩余 {self.free_space_mb} MB)")
    
    @classmethod
    def patch_os_statvfs(cls, free_space_mb=10, duration=60.0):
        """
        替换os.statvfs以模拟磁盘空间不足
        
        Args:
            free_space_mb: 模拟的可用空间(MB)
            duration: 持续时间(秒)
        """
        injector = cls(free_space_mb=free_space_mb, duration=duration, probability=1.0)
        
        # 在Windows系统上没有statvfs，使用模拟的方式
        if hasattr(os, 'statvfs'):
            original_statvfs = os.statvfs
            
            def patched_statvfs(path):
                result = original_statvfs(path)
                
                if injector.is_simulating():
                    # 创建一个模拟的结果，设置极低的可用空间
                    patched_result = list(result)
                    
                    # f_bavail: 非超级用户可获取的空闲块数
                    # f_frsize: 文件系统块大小
                    block_size = result.f_frsize
                    free_blocks = int(injector.free_space_mb * 1024 * 1024 / block_size)
                    
                    # 修改可用块数
                    patched_result[statvfs_bavail_index] = free_blocks
                    
                    # 转换回原始类型
                    return type(result)(patched_result)
                
                return result
            
            # 获取f_bavail的索引
            statvfs_result = os.statvfs('/')
            statvfs_fields = dir(statvfs_result)
            statvfs_bavail_index = statvfs_fields.index('f_bavail')
            
            # 应用补丁
            os.statvfs = patched_statvfs
            
            # 设置恢复定时器
            def restore():
                os.statvfs = original_statvfs
                logger.debug("已恢复原始statvfs方法")
                
            timer = threading.Timer(duration * 1.1, restore)
            timer.daemon = True
            timer.start()
            
            logger.debug(f"已应用磁盘空间不足补丁，持续{duration}秒")


class FileLockedInjector(FaultInjector):
    """文件锁定注入器"""
    
    def __init__(self, 
                 lock_duration: float = 30.0,
                 target_extensions: List[str] = None,
                 probability: float = 0.1, 
                 enabled: bool = True):
        """
        初始化文件锁定注入器
        
        Args:
            lock_duration: 锁定持续时间(秒)
            target_extensions: 目标文件扩展名列表
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.lock_duration = lock_duration
        self.target_extensions = target_extensions or [".json", ".srt", ".txt", ".csv", ".xml"]
        self._locked_files = {}  # filepath -> lock_handle
        self._lock = threading.RLock()
        
    def should_affect_file(self, filepath: str) -> bool:
        """
        判断是否应该影响指定文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 是否应该影响
        """
        if not os.path.exists(filepath):
            return False
            
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.target_extensions
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入文件锁定故障
        
        Args:
            context: 上下文信息，必须包含filepath键
            
        Raises:
            ValueError: 如果上下文中没有filepath键
            IOError: 模拟文件锁定错误
        """
        if not context or "filepath" not in context:
            raise ValueError("上下文必须包含filepath键")
        
        filepath = context["filepath"]
        if not self.should_affect_file(filepath):
            return
        
        try:
            # 锁定文件
            self._lock_file(filepath)
            logger.debug(f"注入文件锁定: {filepath}, 持续{self.lock_duration}秒")
        except Exception as e:
            logger.error(f"锁定文件失败: {e}")
            
        # 无论是否成功锁定文件，都抛出异常
        raise IOError(f"模拟的文件锁定错误: {filepath}")
    
    def _lock_file(self, filepath: str) -> None:
        """
        锁定文件
        
        Args:
            filepath: 文件路径
        """
        with self._lock:
            # 如果文件已经被锁定，不再重复操作
            if filepath in self._locked_files and self._locked_files[filepath] is not None:
                return
                
            try:
                # 打开文件并保持打开状态
                lock_handle = open(filepath, 'rb')
                self._locked_files[filepath] = lock_handle
                
                # 设置解锁定时器
                self._schedule_file_unlock(filepath, self.lock_duration)
                
            except Exception as e:
                logger.error(f"锁定文件失败: {e}")
                if filepath in self._locked_files:
                    del self._locked_files[filepath]
    
    def _schedule_file_unlock(self, filepath: str, delay: float) -> None:
        """
        计划解锁文件
        
        Args:
            filepath: 文件路径
            delay: 延迟时间(秒)
        """
        def unlock_file():
            with self._lock:
                if filepath in self._locked_files and self._locked_files[filepath] is not None:
                    try:
                        self._locked_files[filepath].close()
                        self._locked_files[filepath] = None
                        logger.debug(f"已解锁文件: {filepath}")
                    except Exception as e:
                        logger.error(f"解锁文件失败: {e}")
        
        timer = threading.Timer(delay, unlock_file)
        timer.daemon = True
        timer.start()


class FileSystemSimulator:
    """文件系统故障模拟器，组合多种文件操作故障注入器"""
    
    def __init__(self):
        """初始化文件系统故障模拟器"""
        self.injectors = {}
        
        # 默认创建所有注入器但禁用
        self.injectors["not_found"] = FileNotFoundInjector(enabled=False)
        self.injectors["corruption"] = FileCorruptionInjector(enabled=False)
        self.injectors["permission"] = PermissionDeniedInjector(enabled=False)
        self.injectors["disk_space"] = DiskSpaceInjector(enabled=False)
        self.injectors["locked"] = FileLockedInjector(enabled=False)
    
    def configure(self, injector_name: str, **kwargs) -> None:
        """
        配置特定的注入器
        
        Args:
            injector_name: 注入器名称
            **kwargs: 配置参数
        
        Raises:
            ValueError: 如果注入器名称无效
        """
        if injector_name not in self.injectors:
            raise ValueError(f"无效的注入器名称: {injector_name}")
        
        # 创建新的注入器实例
        if injector_name == "not_found":
            self.injectors[injector_name] = FileNotFoundInjector(**kwargs)
        elif injector_name == "corruption":
            self.injectors[injector_name] = FileCorruptionInjector(**kwargs)
        elif injector_name == "permission":
            self.injectors[injector_name] = PermissionDeniedInjector(**kwargs)
        elif injector_name == "disk_space":
            self.injectors[injector_name] = DiskSpaceInjector(**kwargs)
        elif injector_name == "locked":
            self.injectors[injector_name] = FileLockedInjector(**kwargs)
    
    def enable(self, injector_name: str) -> None:
        """
        启用特定的注入器
        
        Args:
            injector_name: 注入器名称
        
        Raises:
            ValueError: 如果注入器名称无效
        """
        if injector_name not in self.injectors:
            raise ValueError(f"无效的注入器名称: {injector_name}")
        
        self.injectors[injector_name].enabled = True
    
    def disable(self, injector_name: str) -> None:
        """
        禁用特定的注入器
        
        Args:
            injector_name: 注入器名称
        
        Raises:
            ValueError: 如果注入器名称无效
        """
        if injector_name not in self.injectors:
            raise ValueError(f"无效的注入器名称: {injector_name}")
        
        self.injectors[injector_name].enabled = False
    
    def enable_all(self) -> None:
        """启用所有注入器"""
        for name in self.injectors:
            self.injectors[name].enabled = True
    
    def disable_all(self) -> None:
        """禁用所有注入器"""
        for name in self.injectors:
            self.injectors[name].enabled = False
    
    def try_inject(self, context: Dict[str, Any]) -> bool:
        """
        尝试注入文件系统故障
        
        Args:
            context: 上下文信息
            
        Returns:
            bool: 是否注入了故障
        """
        injected = False
        for injector in self.injectors.values():
            if injector.enabled and injector.try_inject(context.copy()):
                injected = True
                break
        
        return injected


# 全局文件系统模拟器实例
filesystem_simulator = FileSystemSimulator()


def configure_corrupted_files():
    """配置文件损坏模拟环境"""
    filesystem_simulator.configure("corruption", 
                                  corruption_modes=["random_bytes", "header_damage"],
                                  target_extensions=[".json", ".srt", ".txt", ".yaml"],
                                  probability=0.3,
                                  enabled=True)
    logger.info("已配置文件损坏模拟环境")


def configure_permission_issues():
    """配置权限问题模拟环境"""
    filesystem_simulator.configure("permission", 
                                  target_operations=["read", "write"],
                                  probability=0.2,
                                  enabled=True)
    logger.info("已配置权限问题模拟环境")


def configure_disk_space_issues():
    """配置磁盘空间不足模拟环境"""
    filesystem_simulator.configure("disk_space", 
                                  free_space_mb=5,
                                  simulation_mode="intermittent",
                                  duration=120.0,
                                  probability=0.1,
                                  enabled=True)
    
    # 应用全局补丁
    DiskSpaceInjector.patch_os_statvfs(free_space_mb=5, duration=120.0)
    logger.info("已配置磁盘空间不足模拟环境") 