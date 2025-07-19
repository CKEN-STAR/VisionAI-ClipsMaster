#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
操作日志溯源器

记录用户对视频进行的各种操作，以便追踪问题、恢复历史状态和分析使用模式。
支持将操作日志保存到本地文件和云存储（如S3），确保即使在系统崩溃时也能恢复操作历史。
"""

import os
import time
import json
import logging
import threading
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

# 可选依赖
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

# 配置日志记录器
logger = logging.getLogger(__name__)

class OperationLogger:
    """操作日志溯源器
    
    记录用户在编辑过程中执行的各种操作，支持本地和云端存储。
    提供操作历史查询、回溯和统计分析功能。
    """
    
    def __init__(self, 
                 base_log_dir: str = "logs/operations", 
                 enable_s3: bool = False,
                 s3_bucket: Optional[str] = None,
                 s3_prefix: str = "operations/",
                 auto_flush: bool = True,
                 flush_interval: int = 300):
        """初始化操作日志记录器
        
        Args:
            base_log_dir: 本地日志文件存储目录
            enable_s3: 是否启用S3云存储备份
            s3_bucket: S3存储桶名称
            s3_prefix: S3存储路径前缀
            auto_flush: 是否自动刷新缓存到磁盘
            flush_interval: 自动刷新间隔（秒）
        """
        # 日志存储路径
        self.base_log_dir = base_log_dir
        
        # 创建日志目录（如果不存在）
        if not os.path.exists(self.base_log_dir):
            try:
                os.makedirs(self.base_log_dir, exist_ok=True)
                logger.info(f"创建操作日志目录: {self.base_log_dir}")
            except Exception as e:
                logger.error(f"创建操作日志目录失败: {str(e)}")
        
        # S3云存储配置
        self.enable_s3 = enable_s3 and S3_AVAILABLE
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        
        # 初始化S3客户端（如果启用）
        self.s3_client = None
        if self.enable_s3:
            if not S3_AVAILABLE:
                logger.warning("未安装boto3库，S3云存储功能将被禁用")
                self.enable_s3 = False
            elif not self.s3_bucket:
                logger.warning("未指定S3存储桶，S3云存储功能将被禁用")
                self.enable_s3 = False
            else:
                try:
                    self.s3_client = boto3.client("s3")
                    logger.info(f"S3云存储备份已启用，存储桶: {self.s3_bucket}")
                except Exception as e:
                    logger.error(f"初始化S3客户端失败: {str(e)}")
                    self.enable_s3 = False
        
        # 日志缓存和锁
        self.session_logs: Dict[str, List[Dict[str, Any]]] = {}
        self.log_lock = threading.RLock()
        
        # 自动刷新
        self.auto_flush = auto_flush
        self.flush_interval = flush_interval
        self.flush_thread = None
        
        # 启动自动刷新线程
        if self.auto_flush:
            self.start_flush_thread()
    
    def log_operation(self, 
                     session_id: str, 
                     operation: str,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """记录操作
        
        Args:
            session_id: 会话ID
            operation: 操作描述
            metadata: 操作相关元数据
        """
        # 构建日志条目
        log_entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "session_id": session_id,
            "operation": operation,
            "metadata": metadata or {}
        }
        
        # 添加到会话日志
        with self.log_lock:
            if session_id not in self.session_logs:
                self.session_logs[session_id] = []
            
            self.session_logs[session_id].append(log_entry)
        
        # 同步写入到文件
        try:
            log_file_path = self._get_log_file_path(session_id)
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"{json.dumps(log_entry, ensure_ascii=False)}\n")
            
            logger.debug(f"已记录操作 [{operation}] 到会话 {session_id}")
        except Exception as e:
            logger.error(f"写入操作日志失败: {str(e)}")
    
    def _get_log_file_path(self, session_id: str) -> str:
        """获取会话日志文件路径
        
        Args:
            session_id: 会话ID
            
        Returns:
            日志文件完整路径
        """
        # 为每个会话创建单独的日志目录
        session_dir = os.path.join(self.base_log_dir, session_id)
        if not os.path.exists(session_dir):
            os.makedirs(session_dir, exist_ok=True)
        
        # 每天一个日志文件
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(session_dir, f"oplog-{date_str}.jsonl")
    
    def get_session_operations(self, 
                              session_id: str, 
                              start_time: Optional[float] = None,
                              end_time: Optional[float] = None,
                              limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取会话操作历史
        
        Args:
            session_id: 会话ID
            start_time: 起始时间戳（可选）
            end_time: 结束时间戳（可选）
            limit: 返回记录数量限制（可选）
            
        Returns:
            操作记录列表
        """
        # 首先从内存缓存加载
        operations = []
        with self.log_lock:
            if session_id in self.session_logs:
                operations = self.session_logs[session_id].copy()
        
        # 如果内存中没有，尝试从文件加载
        if not operations:
            operations = self._load_operations_from_file(session_id)
        
        # 应用筛选条件
        if start_time is not None:
            operations = [op for op in operations if op["timestamp"] >= start_time]
        
        if end_time is not None:
            operations = [op for op in operations if op["timestamp"] <= end_time]
        
        # 按时间排序
        operations.sort(key=lambda x: x["timestamp"])
        
        # 应用限制
        if limit is not None and limit > 0:
            operations = operations[:limit]
        
        return operations
    
    def _load_operations_from_file(self, session_id: str) -> List[Dict[str, Any]]:
        """从文件加载操作历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            操作记录列表
        """
        operations = []
        session_dir = os.path.join(self.base_log_dir, session_id)
        
        if not os.path.exists(session_dir):
            logger.debug(f"会话目录不存在: {session_dir}")
            return operations
        
        # 加载所有日志文件
        try:
            log_files = [f for f in os.listdir(session_dir) if f.startswith("oplog-") and f.endswith(".jsonl")]
            logger.debug(f"找到 {len(log_files)} 个日志文件")
        except Exception as e:
            logger.error(f"读取会话目录失败: {str(e)}")
            return operations
        
        for log_file in log_files:
            file_path = os.path.join(session_dir, log_file)
            try:
                if not os.path.exists(file_path):
                    logger.warning(f"日志文件不存在: {file_path}")
                    continue
                
                if os.path.getsize(file_path) == 0:
                    logger.warning(f"日志文件为空: {file_path}")
                    continue
                
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            operation = json.loads(line)
                            operations.append(operation)
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析日志条目失败 (文件: {log_file}, 行: {line_num}): {str(e)}")
            
                logger.debug(f"已从文件 {log_file} 加载 {len(operations)} 条操作记录")
            except Exception as e:
                logger.error(f"读取操作日志文件 {file_path} 失败: {str(e)}")
        
        # 按时间戳排序
        operations.sort(key=lambda x: x.get("timestamp", 0))
        
        # 更新内存缓存
        with self.log_lock:
            self.session_logs[session_id] = operations.copy()
        
        return operations
    
    def _upload_to_s3(self, local_path, s3_key):
        """上传文件到S3
        
        内部方法，封装异常处理和重试逻辑。
        
        Args:
            local_path: 本地文件路径
            s3_key: S3对象键
            
        Returns:
            上传是否成功
        """
        if not self.enable_s3 or not self.s3_client:
            return False
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.s3_client.upload_file(local_path, self.s3_bucket, s3_key)
                logger.debug(f"已上传操作日志到S3: s3://{self.s3_bucket}/{s3_key}")
                return True
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"上传操作日志到S3失败 (重试{retry_count}/{max_retries}): {str(e)}")
                    return False
                else:
                    # 指数退避
                    wait_time = 2 ** retry_count
                    logger.warning(f"上传操作日志到S3失败，{wait_time}秒后重试 ({retry_count}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
    
    def upload_to_s3(self, session_id: Optional[str] = None) -> bool:
        """将操作日志上传到S3
        
        Args:
            session_id: 特定会话ID（如不指定则上传所有会话）
            
        Returns:
            上传是否成功
        """
        if not self.enable_s3 or not self.s3_client:
            logger.warning("S3功能未启用，无法上传")
            return False
        
        # 确定要上传的会话
        sessions = [session_id] if session_id else os.listdir(self.base_log_dir)
        success = True
        
        for sess_id in sessions:
            # 跳过非目录文件
            session_dir = os.path.join(self.base_log_dir, sess_id)
            if not os.path.isdir(session_dir):
                continue
            
            log_files = [f for f in os.listdir(session_dir) if f.startswith("oplog-") and f.endswith(".jsonl")]
            
            for log_file in log_files:
                local_path = os.path.join(session_dir, log_file)
                s3_key = f"{self.s3_prefix}{sess_id}/{log_file}"
                
                success_upload = self._upload_to_s3(local_path, s3_key)
                if not success_upload:
                    success = False
        
        return success
    
    def start_flush_thread(self) -> None:
        """启动自动刷新线程"""
        if self.flush_thread and self.flush_thread.is_alive():
            return
        
        def flush_periodically():
            while self.auto_flush:
                time.sleep(self.flush_interval)
                try:
                    # 上传到S3
                    if self.enable_s3:
                        self.upload_to_s3()
                except Exception as e:
                    logger.error(f"自动刷新操作日志失败: {str(e)}")
        
        self.flush_thread = threading.Thread(target=flush_periodically, daemon=True)
        self.flush_thread.start()
    
    def stop_flush_thread(self) -> None:
        """停止自动刷新线程"""
        self.auto_flush = False
        if self.flush_thread:
            self.flush_thread.join(timeout=1.0)
    
    def __del__(self):
        """析构函数"""
        self.stop_flush_thread()


# 单例模式
_operation_logger_instance = None
_instance_lock = threading.Lock()

def get_operation_logger() -> OperationLogger:
    """获取操作日志记录器单例实例
    
    Returns:
        操作日志记录器实例
    """
    global _operation_logger_instance
    
    if _operation_logger_instance is None:
        with _instance_lock:
            if _operation_logger_instance is None:
                _operation_logger_instance = OperationLogger()
    
    return _operation_logger_instance

def initialize_operation_logger(**kwargs) -> OperationLogger:
    """初始化操作日志记录器
    
    Args:
        **kwargs: 传递给OperationLogger构造函数的参数
        
    Returns:
        操作日志记录器实例
    """
    global _operation_logger_instance
    
    with _instance_lock:
        _operation_logger_instance = OperationLogger(**kwargs)
    
    return _operation_logger_instance 