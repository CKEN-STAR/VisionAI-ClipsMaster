#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源回收模块

为VisionAI-ClipsMaster项目提供资源回收和清理功能：
1. 紧急资源回收，用于处理异常情况
2. 常规资源回收，用于正常操作结束时清理
3. 定时资源回收，用于长时间运行的操作
4. 智能资源监控，根据系统负载进行优化
"""

import os
import sys
import gc
import time
import threading
import traceback
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union, Set, Callable
from pathlib import Path
from contextlib import contextmanager
from enum import Enum, auto

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from src.utils.log_handler import get_logger
from src.utils.memory_manager import MemoryManager
try:
    from src.utils.buffer_manager import get_buffer_manager, BufferType
    BUFFER_MANAGER_AVAILABLE = True
except ImportError:
    BUFFER_MANAGER_AVAILABLE = False

try:
    from src.utils.vram_detector import VRAMDetector
    VRAM_DETECTOR_AVAILABLE = True
except ImportError:
    VRAM_DETECTOR_AVAILABLE = False

try:
    from src.data.storage_manager import get_storage_manager
    STORAGE_MANAGER_AVAILABLE = True
except ImportError:
    STORAGE_MANAGER_AVAILABLE = False

# 配置日志
logger = get_logger("resource_cleaner")


class CleanupPriority(Enum):
    """清理优先级枚举"""
    LOW = auto()      # 低优先级，只清理不重要的资源
    MEDIUM = auto()   # 中优先级，清理大部分资源
    HIGH = auto()     # 高优先级，清理所有可能的资源
    CRITICAL = auto() # 紧急优先级，强制清理所有资源


class ResourceCleaner:
    """资源清理器
    
    负责管理和回收系统资源，确保资源不会泄露，系统能够高效运行。
    提供多种清理级别和策略，适应不同场景需求。
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ResourceCleaner, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """初始化资源清理器"""
        # 避免重复初始化
        if getattr(self, '_initialized', False):
            return
            
        # 初始化成员变量
        self.temp_dirs = set()  # 临时目录集合
        self.open_files = {}    # 打开的文件句柄 {file_id: file_handle}
        self.gpu_buffers = {}   # GPU缓冲区 {buffer_id: buffer_info}
        self.db_connections = {}  # 数据库连接 {conn_id: conn_obj}
        
        # 自定义清理器
        self.custom_cleaners = {
            CleanupPriority.LOW: [],
            CleanupPriority.MEDIUM: [],
            CleanupPriority.HIGH: [],
            CleanupPriority.CRITICAL: []
        }
        
        # 初始化内存管理器
        self.memory_manager = MemoryManager()
        
        # 初始化VRAM检测器
        if VRAM_DETECTOR_AVAILABLE:
            self.vram_detector = VRAMDetector()
        else:
            self.vram_detector = None
            
        # 初始化完成标记
        self._initialized = True
        
        # 注册基本清理器
        self._register_basic_cleaners()
        
        logger.info("资源清理器初始化完成")
    
    def _register_basic_cleaners(self):
        """注册基本清理器"""
        # 低优先级清理器
        self.register_cleaner(self._clean_temp_files, CleanupPriority.LOW)
        
        # 中优先级清理器
        if BUFFER_MANAGER_AVAILABLE:
            self.register_cleaner(self._clean_temporary_buffers, CleanupPriority.MEDIUM)
        
        # 高优先级清理器
        self.register_cleaner(self._clean_memory, CleanupPriority.HIGH)
        if VRAM_DETECTOR_AVAILABLE:
            self.register_cleaner(self._clean_gpu_memory, CleanupPriority.HIGH)
        
        # 紧急优先级清理器
        self.register_cleaner(self._clean_all, CleanupPriority.CRITICAL)
    
    def register_cleaner(self, 
                       cleaner_function: Callable, 
                       priority: CleanupPriority = CleanupPriority.MEDIUM) -> None:
        """注册自定义清理器
        
        Args:
            cleaner_function: 清理函数，接收context参数
            priority: 清理优先级
        """
        self.custom_cleaners[priority].append(cleaner_function)
        logger.debug(f"注册了优先级为{priority.name}的清理器: {cleaner_function.__name__}")
    
    def register_temp_dir(self, directory: Union[str, Path]) -> None:
        """注册临时目录，以便后续清理
        
        Args:
            directory: 临时目录路径
        """
        if isinstance(directory, Path):
            directory = str(directory)
        
        if os.path.isdir(directory):
            self.temp_dirs.add(directory)
            logger.debug(f"注册临时目录: {directory}")
    
    def register_file_handle(self, file_id: str, file_handle: Any) -> None:
        """注册文件句柄，以便后续关闭
        
        Args:
            file_id: 文件标识符
            file_handle: 文件句柄对象
        """
        if hasattr(file_handle, 'close'):
            self.open_files[file_id] = file_handle
            logger.debug(f"注册文件句柄: {file_id}")
    
    def register_gpu_buffer(self, buffer_id: str, buffer_info: Dict[str, Any]) -> None:
        """注册GPU缓冲区，以便后续释放
        
        Args:
            buffer_id: 缓冲区标识符
            buffer_info: 缓冲区信息
        """
        self.gpu_buffers[buffer_id] = buffer_info
        logger.debug(f"注册GPU缓冲区: {buffer_id}")
    
    def register_db_connection(self, conn_id: str, conn_obj: Any) -> None:
        """注册数据库连接，以便后续关闭
        
        Args:
            conn_id: 连接标识符
            conn_obj: 连接对象
        """
        if hasattr(conn_obj, 'close') or hasattr(conn_obj, 'commit'):
            self.db_connections[conn_id] = conn_obj
            logger.debug(f"注册数据库连接: {conn_id}")
    
    def clean(self, priority: CleanupPriority = CleanupPriority.MEDIUM, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行资源清理
        
        Args:
            priority: 清理优先级
            context: 清理上下文，包含附加信息
            
        Returns:
            Dict[str, Any]: 清理结果统计
        """
        start_time = time.time()
        context = context or {}
        results = {
            "status": "success",
            "cleaned_items": 0,
            "errors": 0,
            "details": {}
        }
        
        logger.info(f"开始执行{priority.name}优先级的资源清理")
        
        # 根据优先级选择要执行的清理器
        cleaners_to_run = []
        priority_values = [p.value for p in CleanupPriority]
        target_value = priority.value
        
        # 添加所有优先级小于等于目标优先级的清理器
        for p in CleanupPriority:
            if p.value <= target_value:
                cleaners_to_run.extend(self.custom_cleaners[p])
        
        # 执行所有选定的清理器
        for cleaner in cleaners_to_run:
            try:
                # 获取清理器名称，处理 MagicMock 对象
                try:
                    cleaner_name = cleaner.__name__
                except (AttributeError, TypeError):
                    cleaner_name = str(cleaner)
                
                cleaner_start = time.time()
                
                # 执行清理
                cleaner_result = cleaner(context)
                
                # 记录结果
                duration = time.time() - cleaner_start
                results["details"][cleaner_name] = {
                    "status": "success",
                    "duration": duration,
                    "result": cleaner_result
                }
                
                # 更新统计
                results["cleaned_items"] += cleaner_result.get("cleaned_items", 0) if isinstance(cleaner_result, dict) else 0
                
                logger.debug(f"清理器 {cleaner_name} 成功执行，耗时: {duration:.3f}秒")
            except Exception as e:
                # 获取清理器名称，处理 MagicMock 对象
                try:
                    cleaner_name = cleaner.__name__
                except (AttributeError, TypeError):
                    cleaner_name = str(cleaner)
                
                error_details = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                results["details"][cleaner_name] = error_details
                results["errors"] += 1
                logger.error(f"清理器 {cleaner_name} 执行失败: {str(e)}")
        
        # 计算总耗时
        results["duration"] = time.time() - start_time
        
        # 更新状态
        if results["errors"] > 0:
            results["status"] = "partial" if results["cleaned_items"] > 0 else "failed"
        
        logger.info(f"资源清理完成，状态: {results['status']}，清理项目: {results['cleaned_items']}，错误: {results['errors']}，耗时: {results['duration']:.3f}秒")
        
        return results
    
    def _clean_temp_files(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """清理临时文件
        
        Args:
            context: 清理上下文
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        result = {
            "cleaned_items": 0,
            "failed_items": 0,
            "skipped_items": 0
        }
        
        # 清理注册的临时目录
        temp_dirs_to_remove = set(self.temp_dirs)
        for temp_dir in temp_dirs_to_remove:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    result["cleaned_items"] += 1
                    logger.debug(f"已清理临时目录: {temp_dir}")
                    self.temp_dirs.remove(temp_dir)
                else:
                    result["skipped_items"] += 1
                    logger.debug(f"临时目录不存在，跳过: {temp_dir}")
                    self.temp_dirs.remove(temp_dir)
            except Exception as e:
                result["failed_items"] += 1
                logger.error(f"清理临时目录失败 {temp_dir}: {str(e)}")
        
        # 根据上下文清理额外的临时目录
        if "temp_dir" in context:
            temp_dir = context["temp_dir"]
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    result["cleaned_items"] += 1
                    logger.debug(f"已清理上下文临时目录: {temp_dir}")
            except Exception as e:
                result["failed_items"] += 1
                logger.error(f"清理上下文临时目录失败 {temp_dir}: {str(e)}")
        
        return result
    
    def _clean_file_handles(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """关闭文件句柄
        
        Args:
            context: 清理上下文
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        result = {
            "cleaned_items": 0,
            "failed_items": 0
        }
        
        file_handles_to_close = dict(self.open_files)
        for file_id, file_handle in file_handles_to_close.items():
            try:
                if hasattr(file_handle, 'close'):
                    file_handle.close()
                    result["cleaned_items"] += 1
                    logger.debug(f"已关闭文件句柄: {file_id}")
                    del self.open_files[file_id]
            except Exception as e:
                result["failed_items"] += 1
                logger.error(f"关闭文件句柄失败 {file_id}: {str(e)}")
        
        # 关闭上下文中的文件句柄
        if "open_files" in context and isinstance(context["open_files"], dict):
            for file_id, file_handle in context["open_files"].items():
                try:
                    if hasattr(file_handle, 'close'):
                        file_handle.close()
                        result["cleaned_items"] += 1
                        logger.debug(f"已关闭上下文文件句柄: {file_id}")
                except Exception as e:
                    result["failed_items"] += 1
                    logger.error(f"关闭上下文文件句柄失败 {file_id}: {str(e)}")
        
        return result
    
    def _clean_temporary_buffers(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """清理临时缓冲区
        
        Args:
            context: 清理上下文
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        result = {
            "cleaned_items": 0,
            "failed_items": 0
        }
        
        if not BUFFER_MANAGER_AVAILABLE:
            logger.warning("缓冲区管理器不可用，跳过缓冲区清理")
            return result
        
        try:
            buffer_manager = get_buffer_manager()
            
            # 清理临时缓冲区
            buffer_manager.clear(BufferType.TEMPORARY)
            result["cleaned_items"] += 1
            logger.debug("已清理临时缓冲区")
            
            # 如果上下文指定了要清理的缓冲区键
            if "buffer_keys" in context and isinstance(context["buffer_keys"], list):
                for key in context["buffer_keys"]:
                    try:
                        if buffer_manager.release(key):
                            result["cleaned_items"] += 1
                            logger.debug(f"已释放缓冲区: {key}")
                        else:
                            logger.debug(f"缓冲区不存在，跳过: {key}")
                    except Exception as e:
                        result["failed_items"] += 1
                        logger.error(f"释放缓冲区失败 {key}: {str(e)}")
        except Exception as e:
            result["failed_items"] += 1
            logger.error(f"清理缓冲区失败: {str(e)}")
        
        return result
    
    def _clean_gpu_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """清理GPU内存
        
        Args:
            context: 清理上下文
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        result = {
            "cleaned_items": 0,
            "failed_items": 0
        }
        
        # 清理GPU缓冲区
        gpu_buffers_to_clean = dict(self.gpu_buffers)
        for buffer_id, buffer_info in gpu_buffers_to_clean.items():
            try:
                if "tensor" in buffer_info and hasattr(buffer_info["tensor"], "to"):
                    # 将张量移到CPU
                    buffer_info["tensor"] = buffer_info["tensor"].to("cpu")
                    result["cleaned_items"] += 1
                    logger.debug(f"已将GPU张量移至CPU: {buffer_id}")
                
                # 从字典中删除
                del self.gpu_buffers[buffer_id]
            except Exception as e:
                result["failed_items"] += 1
                logger.error(f"清理GPU缓冲区失败 {buffer_id}: {str(e)}")
        
        # 尝试清理CUDA缓存
        try:
            import torch
            if torch.cuda.is_available():
                # 释放所有未使用的缓存
                torch.cuda.empty_cache()
                result["cleaned_items"] += 1
                logger.debug("已清空CUDA缓存")
        except (ImportError, Exception) as e:
            logger.debug(f"清空CUDA缓存失败: {str(e)}")
        
        return result
    
    def _clean_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """清理内存
        
        Args:
            context: 清理上下文
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        result = {
            "cleaned_items": 0,
            "memory_before": 0,
            "memory_after": 0
        }
        
        # 记录清理前的内存使用情况
        memory_before = self.memory_manager.get_current_memory_usage()
        result["memory_before"] = memory_before / (1024 * 1024)  # 转换为MB
        
        # 执行内存优化
        before, after = self.memory_manager.optimize_memory(
            aggressive=context.get("aggressive", False)
        )
        
        # 记录清理后的内存使用情况
        result["memory_after"] = after
        result["memory_saved"] = before - after
        result["cleaned_items"] += 1
        
        # 执行垃圾回收
        gc.collect()
        
        logger.debug(f"已清理内存: 优化前{before:.2f}MB, 优化后{after:.2f}MB, 节省{before-after:.2f}MB")
        
        return result
    
    def _clean_db_connections(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """清理数据库连接
        
        Args:
            context: 清理上下文
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        result = {
            "cleaned_items": 0,
            "failed_items": 0
        }
        
        db_connections_to_close = dict(self.db_connections)
        for conn_id, conn_obj in db_connections_to_close.items():
            try:
                # 如果是当前任务上下文，可能需要回滚而不是提交
                should_rollback = context.get("rollback_db", False)
                
                # 先尝试提交或回滚
                if hasattr(conn_obj, 'rollback') and should_rollback:
                    conn_obj.rollback()
                    logger.debug(f"已回滚数据库连接: {conn_id}")
                elif hasattr(conn_obj, 'commit') and not should_rollback:
                    conn_obj.commit()
                    logger.debug(f"已提交数据库连接: {conn_id}")
                
                # 然后关闭连接
                if hasattr(conn_obj, 'close'):
                    conn_obj.close()
                    result["cleaned_items"] += 1
                    logger.debug(f"已关闭数据库连接: {conn_id}")
                    del self.db_connections[conn_id]
            except Exception as e:
                result["failed_items"] += 1
                logger.error(f"清理数据库连接失败 {conn_id}: {str(e)}")
        
        # 处理上下文中的数据库连接
        if "db_conn" in context:
            db_conn = context["db_conn"]
            try:
                should_rollback = context.get("rollback_db", False)
                
                if hasattr(db_conn, 'rollback') and should_rollback:
                    db_conn.rollback()
                    logger.debug("已回滚上下文数据库连接")
                elif hasattr(db_conn, 'commit') and not should_rollback:
                    db_conn.commit()
                    logger.debug("已提交上下文数据库连接")
                
                if hasattr(db_conn, 'close'):
                    db_conn.close()
                    result["cleaned_items"] += 1
                    logger.debug("已关闭上下文数据库连接")
            except Exception as e:
                result["failed_items"] += 1
                logger.error(f"清理上下文数据库连接失败: {str(e)}")
        
        return result
    
    def _clean_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """清理所有资源（紧急模式）
        
        Args:
            context: 清理上下文
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        result = {
            "cleaned_items": 0,
            "failed_items": 0,
            "components": {}
        }
        
        # 执行所有清理操作
        components = [
            ("temp_files", self._clean_temp_files),
            ("file_handles", self._clean_file_handles),
            ("temporary_buffers", self._clean_temporary_buffers),
            ("gpu_memory", self._clean_gpu_memory),
            ("memory", self._clean_memory),
            ("db_connections", self._clean_db_connections)
        ]
        
        for name, cleaner in components:
            try:
                component_result = cleaner(context)
                result["components"][name] = component_result
                result["cleaned_items"] += component_result.get("cleaned_items", 0)
                result["failed_items"] += component_result.get("failed_items", 0)
            except Exception as e:
                result["failed_items"] += 1
                result["components"][name] = {"status": "error", "error": str(e)}
                logger.error(f"紧急清理组件 {name} 失败: {str(e)}")
        
        # 强制执行垃圾回收
        gc.collect()
        gc.collect()  # 连续执行两次，确保最大限度回收
        
        return result
    
    @contextmanager
    def cleanup_context(self, name: str = "default", auto_cleanup: bool = True, priority: CleanupPriority = CleanupPriority.MEDIUM):
        """创建自动清理的上下文管理器
        
        Args:
            name: 上下文名称
            auto_cleanup: 是否在退出上下文时自动清理
            priority: 清理优先级
            
        Yields:
            Dict[str, Any]: 上下文字典，可用于收集需要清理的资源
        """
        context = {
            "name": name,
            "start_time": time.time(),
            "temp_dir": None,
            "open_files": {},
            "buffer_keys": [],
            "db_conn": None,
            "rollback_db": False
        }
        
        logger.debug(f"进入资源清理上下文: {name}")
        
        try:
            yield context
        except Exception as e:
            logger.error(f"上下文 {name} 中发生异常: {str(e)}")
            # 如果发生异常，设置回滚标志
            context["rollback_db"] = True
            
            # 执行紧急清理
            if auto_cleanup:
                self.clean(CleanupPriority.HIGH, context=context)
                
            # 重新抛出异常
            raise
        else:
            # 正常退出，执行标准清理
            if auto_cleanup:
                self.clean(priority, context=context)
                
        finally:
            # 记录耗时
            duration = time.time() - context["start_time"]
            logger.debug(f"退出资源清理上下文: {name}，耗时: {duration:.3f}秒")


def get_resource_cleaner() -> ResourceCleaner:
    """获取资源清理器单例
    
    Returns:
        ResourceCleaner: 资源清理器实例
    """
    return ResourceCleaner()


def emergency_cleanup(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """紧急资源回收
    
    Args:
        context: 清理上下文
        
    Returns:
        Dict[str, Any]: 清理结果
    """
    logger.warning("执行紧急资源回收")
    context = context or {}
    
    # 获取资源清理器并执行紧急清理
    cleaner = get_resource_cleaner()
    return cleaner.clean(CleanupPriority.CRITICAL, context)


def close_file_handles(context: Dict[str, Any]) -> None:
    """关闭文件句柄
    
    Args:
        context: 包含文件句柄的上下文
    """
    # 关闭上下文中的文件句柄
    for handle in context.get('open_files', {}).values():
        try:
            if hasattr(handle, 'close'):
                handle.close()
        except Exception as e:
            logger.error(f"资源回收失败: {str(e)}")


def release_gpu_memory(context: Dict[str, Any]) -> None:
    """释放GPU内存
    
    Args:
        context: 包含GPU缓冲区的上下文
    """
    try:
        import torch
        if torch.cuda.is_available():
            # 释放所有未使用的缓存
            torch.cuda.empty_cache()
            logger.debug("已清空CUDA缓存")
    except (ImportError, Exception) as e:
        logger.debug(f"清空CUDA缓存失败: {str(e)}")


def delete_temp_files(context: Dict[str, Any]) -> None:
    """删除临时文件
    
    Args:
        context: 包含临时目录的上下文
    """
    if "temp_dir" in context and context["temp_dir"]:
        try:
            temp_dir = context["temp_dir"]
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"已删除临时目录: {temp_dir}")
        except Exception as e:
            logger.error(f"删除临时目录失败: {str(e)}")


def rollback_database(context: Dict[str, Any]) -> None:
    """回滚数据库事务
    
    Args:
        context: 包含数据库连接的上下文
    """
    if "db_conn" in context and context["db_conn"]:
        try:
            db_conn = context["db_conn"]
            
            # 如果连接支持回滚，执行回滚
            if hasattr(db_conn, 'rollback'):
                db_conn.rollback()
                logger.debug("已回滚数据库事务")
                
            # 如果连接支持关闭，关闭连接
            if hasattr(db_conn, 'close'):
                db_conn.close()
                logger.debug("已关闭数据库连接")
        except Exception as e:
            logger.error(f"数据库回滚失败: {str(e)}")


@contextmanager
def resource_cleanup_context(name: str = "default"):
    """资源清理上下文管理器
    
    Args:
        name: 上下文名称
        
    Yields:
        Dict[str, Any]: 上下文字典
    """
    cleaner = get_resource_cleaner()
    with cleaner.cleanup_context(name=name) as context:
        yield context 