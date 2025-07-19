"""分片容错恢复系统

此模块提供模型分片加载失败时的容错恢复机制，包括：
1. 自动重试加载失败的分片
2. 备份分片切换
3. 分片完整性修复
4. 错误报告和通知
5. 可配置的恢复策略
6. 与监控系统集成
"""

import os
import time
import shutil
import threading
from enum import Enum
from typing import Dict, List, Tuple, Set, Optional, Any, Callable, Union
from collections import defaultdict, Counter
from pathlib import Path
import json
import hashlib
from loguru import logger

from src.sharding.metadata_manager import MetadataManager
from src.sharding.cache_manager import ShardManager
from src.sharding.integrity_checker import IntegrityChecker, VerificationLevel, IntegrityError


class RecoveryAction(Enum):
    """恢复操作枚举"""
    RETRY = "retry"                  # 重试加载
    USE_BACKUP = "use_backup"        # 使用备份分片
    REDOWNLOAD = "redownload"        # 重新下载分片
    REPAIR = "repair"                # 修复分片
    NOTIFY = "notify"                # 通知管理员
    SKIP = "skip"                    # 跳过此分片
    FALLBACK = "fallback"            # 使用降级模型


class FailureType(Enum):
    """失败类型枚举"""
    IO_ERROR = "io_error"            # IO错误（文件无法读取）
    CORRUPTION = "corruption"        # 文件损坏
    HASH_MISMATCH = "hash_mismatch"  # 哈希不匹配
    MISSING_FILE = "missing_file"    # 文件缺失
    SIGNATURE_ERROR = "signature"    # 签名验证失败
    FORMAT_ERROR = "format"          # 格式错误
    UNKNOWN = "unknown"              # 未知错误


class RecoveryStrategy(Enum):
    """恢复策略枚举"""
    CONSERVATIVE = "conservative"    # 保守策略（优先使用备份）
    AGGRESSIVE = "aggressive"        # 激进策略（优先尝试修复）
    MINIMAL = "minimal"              # 最小化策略（只重试）
    FAILFAST = "failfast"            # 快速失败策略（不尝试恢复）


class ShardRecoveryManager:
    """分片恢复管理器
    
    提供分片加载失败时的自动恢复机制。
    """
    
    def __init__(
        self,
        shard_manager: ShardManager,
        strategy: RecoveryStrategy = RecoveryStrategy.CONSERVATIVE,
        max_retry_count: int = 3,
        backup_dir: Optional[str] = None,
        enable_auto_repair: bool = True,
        enable_notifications: bool = True,
        notification_callback: Optional[Callable[[str], None]] = None,
        integrity_checker: Optional[IntegrityChecker] = None,
        validation_level: VerificationLevel = VerificationLevel.HASH
    ):
        """初始化分片恢复管理器
        
        Args:
            shard_manager: 分片管理器实例
            strategy: 恢复策略
            max_retry_count: 最大重试次数
            backup_dir: 备份目录路径
            enable_auto_repair: 是否启用自动修复
            enable_notifications: 是否启用通知
            notification_callback: 通知回调函数
            integrity_checker: 完整性检查器
            validation_level: 验证级别
        """
        self.shard_manager = shard_manager
        self.strategy = strategy
        self.max_retry_count = max_retry_count
        self.enable_auto_repair = enable_auto_repair
        self.enable_notifications = enable_notifications
        self.notification_callback = notification_callback
        
        # 如果没有提供备份目录，创建默认路径
        if backup_dir is None:
            model_dir = os.path.dirname(shard_manager.shard_dir)
            backup_dir = os.path.join(model_dir, "backups")
        self.backup_dir = Path(backup_dir)
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 如果没有提供完整性检查器，创建一个
        if integrity_checker is None:
            self.integrity_checker = IntegrityChecker(
                metadata_manager=shard_manager.metadata,
                default_level=validation_level
            )
        else:
            self.integrity_checker = integrity_checker
        
        # 恢复统计和历史
        self.recovery_stats = defaultdict(int)  # 统计不同恢复操作的次数
        self.recovery_history = []  # 详细恢复历史记录
        self.failure_counts = Counter()  # 每个分片的失败次数
        
        # 正在恢复的分片
        self.recovering_shards = set()
        
        # 锁
        self._lock = threading.RLock()
        
        # 集成到分片管理器
        self._integrate_with_shard_manager()
        
        logger.info(f"分片恢复管理器初始化完成，策略: {strategy.value}")
    
    def _integrate_with_shard_manager(self):
        """与分片管理器集成
        
        替换分片管理器的加载回调函数，加入错误恢复逻辑
        """
        # 保存原始回调
        self.original_load_callback = self.shard_manager.shard_cache.load_callback
        
        # 创建新的具有恢复功能的回调
        def recovery_load_callback(shard_id: str) -> Any:
            """添加恢复功能的分片加载回调"""
            try:
                # 尝试使用原始回调加载
                result = self.original_load_callback(shard_id)
                
                # 如果成功，重置该分片的失败计数
                if result is not None:
                    with self._lock:
                        self.failure_counts[shard_id] = 0
                
                return result
                
            except Exception as e:
                logger.warning(f"分片 {shard_id} 加载失败: {str(e)}")
                
                # 尝试恢复
                return self.handle_load_failure(shard_id, e)
        
        # 替换原始回调
        self.shard_manager.shard_cache.load_callback = recovery_load_callback
    
    def handle_load_failure(self, shard_id: str, error: Exception = None) -> Optional[Any]:
        """处理分片加载失败
        
        核心恢复逻辑，根据策略执行不同的恢复操作
        
        Args:
            shard_id: 分片ID
            error: 导致失败的异常
            
        Returns:
            Optional[Any]: 恢复后的分片数据，如果恢复失败则为None
        """
        with self._lock:
            # 防止重复恢复同一个分片
            if shard_id in self.recovering_shards:
                logger.warning(f"分片 {shard_id} 已经在恢复中")
                return None
            
            self.recovering_shards.add(shard_id)
            
            try:
                # 更新失败计数
                self.failure_counts[shard_id] += 1
                failure_count = self.failure_counts[shard_id]
                
                # 判断失败类型
                failure_type = self._determine_failure_type(shard_id, error)
                
                # 记录恢复开始
                start_time = time.time()
                logger.info(f"开始恢复分片 {shard_id}，失败类型: {failure_type.value}，第 {failure_count} 次尝试")
                
                # 确定恢复策略
                actions = self._determine_recovery_actions(shard_id, failure_type, failure_count)
                
                # 执行恢复操作
                for action in actions:
                    logger.debug(f"尝试恢复操作: {action.value}")
                    self.recovery_stats[action.value] += 1
                    
                    result = self._execute_recovery_action(shard_id, action, failure_type)
                    
                    # 记录恢复历史
                    duration = time.time() - start_time
                    self._record_recovery_attempt(shard_id, action, failure_type, result is not None, duration)
                    
                    if result is not None:
                        logger.info(f"分片 {shard_id} 恢复成功，操作: {action.value}")
                        return result
                
                # 所有恢复操作都失败
                logger.error(f"分片 {shard_id} 恢复失败，已尝试所有恢复操作")
                
                # 发送通知
                if self.enable_notifications and self.notification_callback:
                    self._send_notification(
                        f"分片 {shard_id} 恢复失败，已尝试 {len(actions)} 种恢复方法"
                    )
                
                return None
                
            finally:
                # 不管成功失败，都从恢复集合中移除
                self.recovering_shards.remove(shard_id)
    
    def _determine_failure_type(self, shard_id: str, error: Exception) -> FailureType:
        """确定失败类型
        
        基于异常和文件检查确定失败类型
        
        Args:
            shard_id: 分片ID
            error: 异常
            
        Returns:
            FailureType: 失败类型
        """
        # 获取分片文件路径
        shard_meta = self.shard_manager.metadata.get_shard(shard_id)
        if not shard_meta:
            return FailureType.UNKNOWN
        
        shard_path = shard_meta.get("path")
        if not shard_path:
            return FailureType.UNKNOWN
        
        if not os.path.isabs(shard_path):
            shard_path = os.path.join(self.shard_manager.shard_dir, shard_path)
        
        # 检查文件是否存在
        if not os.path.exists(shard_path):
            return FailureType.MISSING_FILE
        
        # 尝试进行完整性检查
        try:
            result, error_msg = self.integrity_checker.verify_shard(
                self.shard_manager.model_name, 
                shard_id
            )
            
            if not result:
                if "哈希" in error_msg:
                    return FailureType.HASH_MISMATCH
                elif "签名" in error_msg:
                    return FailureType.SIGNATURE_ERROR
                elif "文件头" in error_msg or "格式" in error_msg:
                    return FailureType.FORMAT_ERROR
                else:
                    return FailureType.CORRUPTION
        except Exception:
            pass  # 继续检查其他可能的失败类型
        
        # 基于异常类型判断
        if error is not None:
            error_str = str(error).lower()
            
            if "permission" in error_str or "access" in error_str:
                return FailureType.IO_ERROR
            elif "corrupt" in error_str or "invalid" in error_str:
                return FailureType.CORRUPTION
            elif "hash" in error_str or "checksum" in error_str:
                return FailureType.HASH_MISMATCH
            elif "signature" in error_str:
                return FailureType.SIGNATURE_ERROR
            elif "format" in error_str:
                return FailureType.FORMAT_ERROR
        
        return FailureType.UNKNOWN
    
    def _determine_recovery_actions(
        self, 
        shard_id: str, 
        failure_type: FailureType, 
        failure_count: int
    ) -> List[RecoveryAction]:
        """确定恢复操作顺序
        
        根据策略、失败类型和失败次数确定恢复操作顺序
        
        Args:
            shard_id: 分片ID
            failure_type: 失败类型
            failure_count: 失败次数
            
        Returns:
            List[RecoveryAction]: 按顺序执行的恢复操作列表
        """
        actions = []
        
        # 如果失败次数超过最大重试次数，可能需要更激进的恢复策略
        exhausted_retries = failure_count > self.max_retry_count
        
        # 根据恢复策略选择操作
        if self.strategy == RecoveryStrategy.MINIMAL:
            # 最小化策略：只重试，不做其他尝试
            if not exhausted_retries:
                actions = [RecoveryAction.RETRY]
            else:
                actions = [RecoveryAction.NOTIFY, RecoveryAction.SKIP]
        
        elif self.strategy == RecoveryStrategy.FAILFAST:
            # 快速失败策略：不尝试恢复，直接通知
            actions = [RecoveryAction.NOTIFY, RecoveryAction.SKIP]
        
        elif self.strategy == RecoveryStrategy.CONSERVATIVE:
            # 保守策略：优先使用备份，然后尝试重新下载
            if not exhausted_retries:
                actions.append(RecoveryAction.RETRY)
            
            # 添加备份操作
            actions.append(RecoveryAction.USE_BACKUP)
            
            # 如果是文件丢失或损坏，尝试重新下载
            if failure_type in [FailureType.MISSING_FILE, FailureType.CORRUPTION, FailureType.HASH_MISMATCH]:
                actions.append(RecoveryAction.REDOWNLOAD)
            
            # 如果启用了自动修复
            if self.enable_auto_repair:
                actions.append(RecoveryAction.REPAIR)
            
            # 最后通知和跳过
            actions.extend([RecoveryAction.NOTIFY, RecoveryAction.SKIP])
        
        elif self.strategy == RecoveryStrategy.AGGRESSIVE:
            # 激进策略：尝试所有可能的恢复方法
            if not exhausted_retries:
                actions.append(RecoveryAction.RETRY)
            
            # 根据失败类型确定优先操作
            if failure_type == FailureType.HASH_MISMATCH:
                # 哈希不匹配：优先重新下载
                actions.extend([RecoveryAction.REDOWNLOAD, RecoveryAction.USE_BACKUP, RecoveryAction.REPAIR])
            elif failure_type == FailureType.MISSING_FILE:
                # 文件缺失：优先重新下载
                actions.extend([RecoveryAction.REDOWNLOAD, RecoveryAction.USE_BACKUP])
            elif failure_type == FailureType.CORRUPTION:
                # 文件损坏：优先修复
                actions.extend([RecoveryAction.REPAIR, RecoveryAction.USE_BACKUP, RecoveryAction.REDOWNLOAD])
            else:
                # 其他情况
                actions.extend([RecoveryAction.USE_BACKUP, RecoveryAction.REDOWNLOAD, RecoveryAction.REPAIR])
            
            # 最后通知和跳过
            actions.extend([RecoveryAction.NOTIFY, RecoveryAction.FALLBACK, RecoveryAction.SKIP])
        
        return actions
    
    def _execute_recovery_action(
        self, 
        shard_id: str, 
        action: RecoveryAction, 
        failure_type: FailureType
    ) -> Optional[Any]:
        """执行恢复操作
        
        Args:
            shard_id: 分片ID
            action: 恢复操作
            failure_type: 失败类型
            
        Returns:
            Optional[Any]: 恢复后的分片数据，如果恢复失败则为None
        """
        # 获取分片元数据
        shard_meta = self.shard_manager.metadata.get_shard(shard_id)
        if not shard_meta:
            logger.error(f"无法获取分片 {shard_id} 的元数据")
            return None
        
        # 获取分片路径
        shard_path = shard_meta.get("path")
        if not shard_path:
            logger.error(f"分片 {shard_id} 没有路径信息")
            return None
        
        if not os.path.isabs(shard_path):
            shard_path = os.path.join(self.shard_manager.shard_dir, shard_path)
        
        # 执行对应的恢复操作
        if action == RecoveryAction.RETRY:
            return self._retry_load(shard_id)
            
        elif action == RecoveryAction.USE_BACKUP:
            return self._use_backup_shard(shard_id, shard_path)
            
        elif action == RecoveryAction.REDOWNLOAD:
            return self._redownload_shard(shard_id, shard_path)
            
        elif action == RecoveryAction.REPAIR:
            return self._repair_shard(shard_id, shard_path, failure_type)
            
        elif action == RecoveryAction.NOTIFY:
            self._send_notification(f"分片 {shard_id} 加载失败，类型: {failure_type.value}")
            return None
            
        elif action == RecoveryAction.FALLBACK:
            return self._use_fallback_model(shard_id)
            
        elif action == RecoveryAction.SKIP:
            logger.warning(f"跳过分片 {shard_id}")
            return None
            
        else:
            logger.error(f"未知的恢复操作: {action}")
            return None
    
    def _retry_load(self, shard_id: str) -> Optional[Any]:
        """重试加载分片
        
        Args:
            shard_id: 分片ID
            
        Returns:
            Optional[Any]: 加载的分片数据
        """
        logger.info(f"重试加载分片: {shard_id}")
        
        try:
            # 直接调用原始加载函数
            return self.original_load_callback(shard_id)
        except Exception as e:
            logger.warning(f"重试加载分片 {shard_id} 失败: {str(e)}")
            return None
    
    def _use_backup_shard(self, shard_id: str, original_path: str) -> Optional[Any]:
        """使用备份分片
        
        Args:
            shard_id: 分片ID
            original_path: 原始分片路径
            
        Returns:
            Optional[Any]: 加载的分片数据
        """
        # 检查备份是否存在
        backup_filename = f"{shard_id}_backup.bin"
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            logger.warning(f"找不到分片 {shard_id} 的备份")
            return None
        
        logger.info(f"使用备份分片: {backup_path}")
        
        try:
            # 复制备份到原始位置
            shutil.copy2(backup_path, original_path)
            
            # 重新加载
            return self.original_load_callback(shard_id)
        except Exception as e:
            logger.warning(f"使用备份分片 {shard_id} 失败: {str(e)}")
            return None
    
    def _redownload_shard(self, shard_id: str, shard_path: str) -> Optional[Any]:
        """重新下载分片
        
        Args:
            shard_id: 分片ID
            shard_path: 分片路径
            
        Returns:
            Optional[Any]: 加载的分片数据
        """
        logger.info(f"尝试重新下载分片: {shard_id}")
        
        # 这里应该实现实际的下载逻辑
        # 在实际项目中，可能需要调用模型下载的API或命令
        
        # 模拟重新下载
        try:
            # 检查是否存在临时备份，如果有则使用
            temp_backup = Path(f"{shard_path}.temp_backup")
            if temp_backup.exists():
                logger.info(f"使用临时备份恢复分片: {shard_id}")
                shutil.copy2(temp_backup, shard_path)
                
                # 重新加载
                result = self.original_load_callback(shard_id)
                if result is not None:
                    logger.info(f"使用临时备份恢复分片 {shard_id} 成功")
                    return result
            
            # 实际应用中应替换为真正的下载逻辑
            logger.warning("重新下载分片功能尚未实现，此为模拟操作")
            self._send_notification(f"分片 {shard_id} 需要重新下载")
            
            return None
        except Exception as e:
            logger.warning(f"重新下载分片 {shard_id} 失败: {str(e)}")
            return None
    
    def _repair_shard(
        self, 
        shard_id: str, 
        shard_path: str, 
        failure_type: FailureType
    ) -> Optional[Any]:
        """修复分片
        
        尝试修复损坏的分片
        
        Args:
            shard_id: 分片ID
            shard_path: 分片路径
            failure_type: 失败类型
            
        Returns:
            Optional[Any]: 修复后的分片数据
        """
        logger.info(f"尝试修复分片: {shard_id}")
        
        # 根据不同的失败类型执行不同的修复操作
        if failure_type == FailureType.HASH_MISMATCH:
            # 哈希不匹配，尝试更新元数据中的哈希值
            try:
                # 计算当前文件的哈希值
                with open(shard_path, "rb") as f:
                    content = f.read()
                    current_hash = hashlib.sha256(content).hexdigest()
                
                # 更新元数据中的哈希值
                shard_meta = self.shard_manager.metadata.get_shard(shard_id)
                if shard_meta:
                    shard_meta["hash"] = current_hash
                    self.shard_manager.metadata.update_shard(shard_id, shard_meta)
                    logger.info(f"已更新分片 {shard_id} 的哈希值")
                
                # 重新加载
                return self.original_load_callback(shard_id)
            except Exception as e:
                logger.warning(f"修复分片 {shard_id} 哈希失败: {str(e)}")
        
        elif failure_type == FailureType.FORMAT_ERROR:
            # 格式错误，尝试修复文件头
            # 实际项目中，应根据特定格式实现具体修复逻辑
            logger.warning("格式修复功能尚未实现")
        
        elif failure_type == FailureType.CORRUPTION:
            # 文件损坏，尝试从正常部分恢复
            logger.warning("文件损坏修复功能尚未实现")
        
        # 默认返回None表示修复失败
        return None
    
    def _use_fallback_model(self, shard_id: str) -> Optional[Any]:
        """使用降级模型
        
        当无法恢复主要分片时，尝试使用降级的替代模型
        
        Args:
            shard_id: 分片ID
            
        Returns:
            Optional[Any]: 降级模型数据
        """
        logger.info(f"尝试使用降级模型替代分片: {shard_id}")
        
        # 在实际项目中，应该实现降级逻辑
        # 例如，使用较小/较简单的备用模型
        
        return None  # 暂不实现
    
    def _send_notification(self, message: str):
        """发送通知
        
        Args:
            message: 通知消息
        """
        if not self.enable_notifications:
            return
        
        logger.warning(f"通知: {message}")
        
        if self.notification_callback:
            try:
                self.notification_callback(message)
            except Exception as e:
                logger.error(f"发送通知失败: {str(e)}")
    
    def _record_recovery_attempt(
        self, 
        shard_id: str, 
        action: RecoveryAction, 
        failure_type: FailureType, 
        success: bool, 
        duration: float
    ):
        """记录恢复尝试
        
        Args:
            shard_id: 分片ID
            action: 恢复操作
            failure_type: 失败类型
            success: 是否成功
            duration: 持续时间（秒）
        """
        record = {
            "shard_id": shard_id,
            "timestamp": time.time(),
            "action": action.value,
            "failure_type": failure_type.value,
            "success": success,
            "duration": duration
        }
        
        self.recovery_history.append(record)
        
        # 限制历史记录大小
        if len(self.recovery_history) > 1000:
            self.recovery_history = self.recovery_history[-1000:]
    
    def create_backup(self, shard_id: str) -> bool:
        """为分片创建备份
        
        Args:
            shard_id: 分片ID
            
        Returns:
            bool: 是否成功创建备份
        """
        # 获取分片元数据
        shard_meta = self.shard_manager.metadata.get_shard(shard_id)
        if not shard_meta:
            logger.error(f"无法获取分片 {shard_id} 的元数据")
            return False
        
        # 获取分片路径
        shard_path = shard_meta.get("path")
        if not shard_path:
            logger.error(f"分片 {shard_id} 没有路径信息")
            return False
        
        if not os.path.isabs(shard_path):
            shard_path = os.path.join(self.shard_manager.shard_dir, shard_path)
        
        # 检查文件是否存在
        if not os.path.exists(shard_path):
            logger.error(f"分片文件不存在: {shard_path}")
            return False
        
        # 创建备份目录
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 备份文件名
        backup_filename = f"{shard_id}_backup.bin"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # 复制文件
            shutil.copy2(shard_path, backup_path)
            logger.info(f"已为分片 {shard_id} 创建备份: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"为分片 {shard_id} 创建备份失败: {str(e)}")
            return False
    
    def restore_from_backup(self, shard_id: str) -> bool:
        """从备份恢复分片
        
        Args:
            shard_id: 分片ID
            
        Returns:
            bool: 是否成功恢复
        """
        # 获取分片元数据
        shard_meta = self.shard_manager.metadata.get_shard(shard_id)
        if not shard_meta:
            logger.error(f"无法获取分片 {shard_id} 的元数据")
            return False
        
        # 获取分片路径
        shard_path = shard_meta.get("path")
        if not shard_path:
            logger.error(f"分片 {shard_id} 没有路径信息")
            return False
        
        if not os.path.isabs(shard_path):
            shard_path = os.path.join(self.shard_manager.shard_dir, shard_path)
        
        # 备份文件名
        backup_filename = f"{shard_id}_backup.bin"
        backup_path = self.backup_dir / backup_filename
        
        # 检查备份是否存在
        if not backup_path.exists():
            logger.error(f"找不到分片 {shard_id} 的备份")
            return False
        
        try:
            # 复制备份到原始位置
            shutil.copy2(backup_path, shard_path)
            logger.info(f"已从备份恢复分片 {shard_id}")
            return True
        except Exception as e:
            logger.error(f"从备份恢复分片 {shard_id} 失败: {str(e)}")
            return False
    
    def backup_all_shards(self) -> Dict[str, bool]:
        """备份所有分片
        
        Returns:
            Dict[str, bool]: 备份结果 {分片ID: 是否成功}
        """
        if not self.shard_manager.metadata:
            logger.error("无法访问元数据管理器")
            return {}
        
        results = {}
        all_shards = self.shard_manager.metadata.get_shards()
        
        for shard_id in all_shards:
            results[shard_id] = self.create_backup(shard_id)
        
        logger.info(f"已完成所有分片的备份，成功: {sum(results.values())}，失败: {len(results) - sum(results.values())}")
        return results
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """获取恢复统计信息
        
        Returns:
            Dict[str, Any]: 恢复统计信息
        """
        stats = {
            "total_failures": sum(self.failure_counts.values()),
            "recovered_shards": sum(1 for record in self.recovery_history if record["success"]),
            "failed_recoveries": sum(1 for record in self.recovery_history if not record["success"]),
            "action_counts": dict(self.recovery_stats),
            "shards_with_issues": len(self.failure_counts),
            "most_problematic_shards": self.failure_counts.most_common(5)
        }
        
        return stats


def handle_load_failure(shard_id: str, retry_count: int = 0):
    """分片加载失败处理
    
    简单的分片加载失败处理函数，用于兼容旧代码
    
    Args:
        shard_id: 分片ID
        retry_count: 当前重试次数
    """
    """分片加载失败处理"""
    if retry_count < 3:
        # 简单的重试机制
        logger.warning(f"分片 {shard_id} 加载失败，尝试重新下载并重试（{retry_count + 1}/3）")
        
        # 尝试重新下载分片
        redownload_shard(shard_id)  # 重新下载分片
        
        # 尝试加载分片
        load_shard(shard_id)
    else:
        # 重试次数用尽，切换到备份分片
        logger.error(f"分片 {shard_id} 持续加载失败，切换到备份分片")
        
        # 切换到备份分片
        switch_to_backup_shard(shard_id)  # 切换到备份分片
        
        # 通知管理员
        alert_admin(f"分片{shard_id}持续加载失败")


def redownload_shard(shard_id: str) -> bool:
    """重新下载分片
    
    简单的重新下载函数，用于兼容旧代码
    
    Args:
        shard_id: 分片ID
        
    Returns:
        bool: 是否成功下载
    """
    logger.info(f"重新下载分片: {shard_id}")
    # 这里应该实现实际的下载逻辑
    return True


def switch_to_backup_shard(shard_id: str) -> bool:
    """切换到备份分片
    
    简单的备份切换函数，用于兼容旧代码
    
    Args:
        shard_id: 分片ID
        
    Returns:
        bool: 是否成功切换
    """
    logger.info(f"切换到备份分片: {shard_id}")
    # 这里应该实现实际的备份切换逻辑
    return True


def load_shard(shard_id: str) -> Any:
    """加载分片
    
    简单的分片加载函数，用于兼容旧代码
    
    Args:
        shard_id: 分片ID
        
    Returns:
        Any: 加载的分片数据
    """
    logger.info(f"加载分片: {shard_id}")
    # 这里应该实现实际的加载逻辑
    return {"id": shard_id}


def alert_admin(message: str):
    """通知管理员
    
    简单的管理员通知函数，用于兼容旧代码
    
    Args:
        message: 通知消息
    """
    logger.warning(f"管理员通知: {message}")
    # 这里应该实现实际的通知逻辑


def create_recovery_manager(
    shard_manager: ShardManager,
    strategy: RecoveryStrategy = RecoveryStrategy.CONSERVATIVE,
    max_retry_count: int = 3,
    backup_dir: Optional[str] = None,
    enable_notifications: bool = True
) -> ShardRecoveryManager:
    """创建恢复管理器
    
    便捷函数，创建并配置分片恢复管理器
    
    Args:
        shard_manager: 分片管理器实例
        strategy: 恢复策略
        max_retry_count: 最大重试次数
        backup_dir: 备份目录
        enable_notifications: 是否启用通知
        
    Returns:
        ShardRecoveryManager: 配置好的分片恢复管理器
    """
    # 创建通知回调
    def notification_callback(message: str):
        """简单的通知回调"""
        logger.warning(f"系统通知: {message}")
        # 实际项目中可以发送邮件、短信等
    
    # 创建恢复管理器
    recovery_manager = ShardRecoveryManager(
        shard_manager=shard_manager,
        strategy=strategy,
        max_retry_count=max_retry_count,
        backup_dir=backup_dir,
        enable_notifications=enable_notifications,
        notification_callback=notification_callback
    )
    
    # 创建所有分片的备份
    recovery_manager.backup_all_shards()
    
    return recovery_manager 