#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
存储管理验证模块

提供用于验证临时文件管理的工具，确保处理过程中不会留下残留的临时文件。
实现了以下功能：
1. 临时文件追踪：记录并监控应用程序创建的所有临时文件
2. 资源泄漏检测：检测未正确清理的文件和目录
3. 清理验证：确认清理操作是否完全执行
4. 临时文件报告：提供详细的临时文件使用报告
"""

import os
import sys
import time
import glob
import shutil
import logging
import tempfile
import threading
import atexit
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union, Callable

# 配置日志
logger = logging.getLogger("storage_validator")

class TempFileRecord:
    """临时文件记录类"""
    
    def __init__(self, file_path: str, creator: str = "", creation_time: float = None):
        """初始化临时文件记录
        
        Args:
            file_path: 文件路径
            creator: 创建者信息（模块/函数名）
            creation_time: 创建时间戳，如果为None则使用当前时间
        """
        self.file_path = file_path
        self.creator = creator
        self.creation_time = creation_time or time.time()
        self.size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        self.cleanup_attempted = False
        self.cleanup_success = False
        self.cleanup_time = None
    
    def mark_cleanup_attempt(self, success: bool = True):
        """标记清理尝试
        
        Args:
            success: 清理是否成功
        """
        self.cleanup_attempted = True
        self.cleanup_success = success
        self.cleanup_time = time.time()
    
    def get_age(self) -> float:
        """获取文件年龄（秒）
        
        Returns:
            文件存在的秒数
        """
        return time.time() - self.creation_time
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            文件记录的字符串表示
        """
        status = "已清理" if self.cleanup_success else "未清理"
        return f"{self.file_path} ({self.creator}) - {status}, 大小: {self.size/1024:.2f}KB, 年龄: {self.get_age():.1f}秒"


class StorageValidator:
    """存储验证器
    
    用于监控和验证临时文件的创建和清理。
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StorageValidator, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, auto_cleanup: bool = True, temp_dirs: List[str] = None, 
                 allowed_extensions: List[str] = None, max_age_hours: float = 2.0):
        """初始化存储验证器
        
        Args:
            auto_cleanup: 是否在程序退出时自动清理
            temp_dirs: 要监控的临时目录列表，如果为None则使用默认目录
            allowed_extensions: 允许的文件扩展名列表
            max_age_hours: 临时文件最大允许存在时间（小时）
        """
        # 避免重复初始化
        if getattr(self, "_initialized", False):
            return
            
        # 配置
        self.auto_cleanup = auto_cleanup
        self.max_age_hours = max_age_hours
        self.max_age_seconds = max_age_hours * 3600
        
        # 设置临时目录
        self.temp_dirs = temp_dirs or []
        if not self.temp_dirs:
            sys_temp = tempfile.gettempdir()
            # 添加项目特定的临时目录
            project_temp_dirs = [
                os.path.join(sys_temp, "visionai_clips_temp"),
                os.path.join(sys_temp, "ffmpeg_zerocopy"),
                os.path.join(sys_temp, "clip_export_temp")
            ]
            self.temp_dirs = project_temp_dirs
            
            # 确保目录存在
            for temp_dir in self.temp_dirs:
                os.makedirs(temp_dir, exist_ok=True)
        
        # 设置允许的文件扩展名
        self.allowed_extensions = allowed_extensions or [
            ".tmp", ".temp", ".bak", ".bin", ".raw", ".mp4.part", ".buffer", 
            ".processing", ".incomplete", ".partial"
        ]
        
        # 初始化跟踪记录
        self.temp_files: Dict[str, TempFileRecord] = {}  # 路径 -> 记录对象
        self.added_count = 0
        self.cleaned_count = 0
        self.failed_cleanup_count = 0
        
        # 初始化线程锁
        self.lock = threading.Lock()
        
        # 如果启用自动清理，注册退出处理
        if self.auto_cleanup:
            atexit.register(self.verify_and_cleanup)
            
        # 标记为已初始化
        self._initialized = True
        logger.info("存储验证器已初始化")
    
    def register_temp_file(self, file_path: str, creator: str = "") -> bool:
        """注册临时文件
        
        Args:
            file_path: 文件路径
            creator: 创建者信息
            
        Returns:
            bool: 是否成功注册
        """
        with self.lock:
            if not os.path.exists(file_path):
                logger.warning(f"无法注册不存在的文件: {file_path}")
                return False
                
            # 如果文件已被跟踪，更新创建者信息
            if file_path in self.temp_files:
                if creator and not self.temp_files[file_path].creator:
                    self.temp_files[file_path].creator = creator
                return True
                
            # 添加新文件记录
            self.temp_files[file_path] = TempFileRecord(file_path, creator)
            self.added_count += 1
            logger.debug(f"已注册临时文件: {file_path}")
            return True
    
    def register_temp_directory(self, dir_path: str, creator: str = "") -> int:
        """注册目录中的所有临时文件
        
        Args:
            dir_path: 目录路径
            creator: 创建者信息
            
        Returns:
            注册的文件数量
        """
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            logger.warning(f"无法注册不存在的目录: {dir_path}")
            return 0
            
        count = 0
        for ext in self.allowed_extensions:
            pattern = os.path.join(dir_path, f"*{ext}")
            for file_path in glob.glob(pattern):
                if self.register_temp_file(file_path, creator):
                    count += 1
                    
        logger.debug(f"已从目录 {dir_path} 注册 {count} 个临时文件")
        return count
    
    def mark_file_cleaned(self, file_path: str, success: bool = True) -> bool:
        """标记文件已清理
        
        Args:
            file_path: 文件路径
            success: 清理是否成功
            
        Returns:
            bool: 是否成功标记
        """
        with self.lock:
            if file_path not in self.temp_files:
                logger.warning(f"尝试标记未跟踪的文件为已清理: {file_path}")
                return False
                
            record = self.temp_files[file_path]
            record.mark_cleanup_attempt(success)
            
            if success:
                self.cleaned_count += 1
            else:
                self.failed_cleanup_count += 1
                
            return True
    
    def cleanup_file(self, file_path: str) -> bool:
        """清理文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否成功清理
        """
        try:
            if not os.path.exists(file_path):
                # 文件已不存在，视为已清理
                self.mark_file_cleaned(file_path, True)
                return True
                
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)
                
            success = not os.path.exists(file_path)
            self.mark_file_cleaned(file_path, success)
            return success
        except Exception as e:
            logger.error(f"清理文件失败 {file_path}: {str(e)}")
            self.mark_file_cleaned(file_path, False)
            return False
    
    def scan_temp_directories(self) -> int:
        """扫描所有临时目录，注册发现的临时文件
        
        Returns:
            注册的文件数量
        """
        total_count = 0
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                count = self.register_temp_directory(temp_dir, "自动扫描")
                total_count += count
                
        logger.info(f"已扫描临时目录，发现并注册 {total_count} 个临时文件")
        return total_count
    
    def verify_cleanup(self) -> Tuple[bool, List[str]]:
        """验证所有注册的临时文件是否已清理
        
        Returns:
            (bool, List[str]): 是否全部已清理，未清理文件列表
        """
        uncleaned_files = []
        
        with self.lock:
            for file_path, record in self.temp_files.items():
                if not record.cleanup_success and os.path.exists(file_path):
                    uncleaned_files.append(file_path)
                    
        all_cleaned = len(uncleaned_files) == 0
        return all_cleaned, uncleaned_files
    
    def verify_and_cleanup(self) -> bool:
        """验证并清理所有未清理的临时文件
        
        Returns:
            bool: 是否全部成功清理
        """
        # 先执行一次扫描
        self.scan_temp_directories()
        
        all_cleaned, uncleaned_files = self.verify_cleanup()
        if all_cleaned:
            logger.info("所有临时文件已正确清理")
            return True
            
        # 尝试清理未清理的文件
        cleanup_success = True
        for file_path in uncleaned_files:
            success = self.cleanup_file(file_path)
            if not success:
                cleanup_success = False
                
        if cleanup_success:
            logger.info(f"已成功清理所有 {len(uncleaned_files)} 个残留临时文件")
        else:
            logger.warning(f"清理临时文件完成，但仍有文件未能清理")
            
        return cleanup_success
    
    def generate_report(self) -> Dict[str, Any]:
        """生成临时文件使用报告
        
        Returns:
            报告内容
        """
        with self.lock:
            total_files = len(self.temp_files)
            cleaned_files = sum(1 for record in self.temp_files.values() if record.cleanup_success)
            uncleaned_files = total_files - cleaned_files
            
            # 计算总大小
            total_size = sum(record.size for record in self.temp_files.values())
            uncleaned_size = sum(record.size for record in self.temp_files.values() 
                                if not record.cleanup_success and os.path.exists(record.file_path))
            
            # 按创建者分组
            creators = {}
            for record in self.temp_files.values():
                creator = record.creator or "未知"
                if creator not in creators:
                    creators[creator] = {
                        "count": 0,
                        "cleaned": 0,
                        "size": 0
                    }
                creators[creator]["count"] += 1
                if record.cleanup_success:
                    creators[creator]["cleaned"] += 1
                creators[creator]["size"] += record.size
            
            # 生成报告
            report = {
                "total_files": total_files,
                "cleaned_files": cleaned_files,
                "uncleaned_files": uncleaned_files,
                "total_size_kb": total_size / 1024,
                "uncleaned_size_kb": uncleaned_size / 1024,
                "cleanup_rate": (cleaned_files / total_files) * 100 if total_files > 0 else 100,
                "creators": creators,
                "timestamp": time.time()
            }
            
            return report

# 创建全局实例
storage_validator = StorageValidator()

def register_temp_file(file_path: str, creator: str = "") -> bool:
    """注册临时文件
    
    Args:
        file_path: 文件路径
        creator: 创建者信息
        
    Returns:
        bool: 是否成功注册
    """
    return storage_validator.register_temp_file(file_path, creator)

def cleanup_temp_file(file_path: str) -> bool:
    """清理临时文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否成功清理
    """
    return storage_validator.cleanup_file(file_path)

def scan_temp_directories() -> int:
    """扫描临时目录
    
    Returns:
        注册的文件数量
    """
    return storage_validator.scan_temp_directories()

def verify_cleanup() -> Tuple[bool, List[str]]:
    """验证清理状态
    
    Returns:
        (bool, List[str]): 是否全部已清理，未清理文件列表
    """
    return storage_validator.verify_cleanup()

def verify_and_cleanup() -> bool:
    """验证并执行清理
    
    Returns:
        bool: 是否全部成功清理
    """
    return storage_validator.verify_and_cleanup()

def get_storage_report() -> Dict[str, Any]:
    """获取存储报告
    
    Returns:
        存储报告
    """
    return storage_validator.generate_report()

class TempFileManager:
    """临时文件管理器，使用上下文管理接口"""
    
    def __init__(self, temp_dir: Optional[str] = None, prefix: str = "visionai_", suffix: str = ".tmp", 
                 creator: str = "", auto_cleanup: bool = True):
        """初始化临时文件管理器
        
        Args:
            temp_dir: 临时目录，如果为None则使用系统临时目录
            prefix: 文件名前缀
            suffix: 文件名后缀
            creator: 创建者信息
            auto_cleanup: 是否自动清理
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.prefix = prefix
        self.suffix = suffix
        self.creator = creator
        self.auto_cleanup = auto_cleanup
        self.temp_files = []
        
        # 确保临时目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def create_temp_file(self) -> str:
        """创建临时文件
        
        Returns:
            临时文件路径
        """
        temp_fd, temp_path = tempfile.mkstemp(suffix=self.suffix, prefix=self.prefix, dir=self.temp_dir)
        os.close(temp_fd)  # 关闭文件描述符，避免资源泄漏
        
        # 注册到验证器
        register_temp_file(temp_path, self.creator)
        self.temp_files.append(temp_path)
        
        return temp_path
    
    def cleanup(self) -> bool:
        """清理所有创建的临时文件
        
        Returns:
            bool: 是否全部成功清理
        """
        all_success = True
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                success = cleanup_temp_file(file_path)
                if not success:
                    all_success = False
        
        # 清空列表
        self.temp_files = []
        return all_success
    
    def __enter__(self):
        """进入上下文"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.auto_cleanup:
            self.cleanup() 