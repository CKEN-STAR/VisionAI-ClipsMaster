"""
恢复管理器模块

负责处理系统中断、崩溃和错误后的恢复操作，具备：
1. 断点续传能力 - 支持从中断的剪辑任务恢复
2. 进度持久化 - 保存处理中间状态
3. 状态恢复机制 - 在崩溃后重建工作环境
4. 资源清理 - 确保临时文件和资源被正确释放
"""

import os
import json
import time
import pickle
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Set

from loguru import logger
from src.utils.exceptions import ClipMasterError, FileOperationError, ErrorCode
from src.utils.file_checker import calculate_file_hash
from src.core.auto_recovery import auto_heal


class RecoveryPoint:
    """表示处理过程中的恢复点"""
    
    def __init__(self, 
                 task_id: str,
                 stage: str,
                 processed_segments: List[Dict[str, Any]] = None,
                 source_files: Dict[str, str] = None,
                 metadata: Dict[str, Any] = None):
        """
        初始化恢复点
        
        Args:
            task_id: 任务唯一标识符
            stage: 处理阶段标识
            processed_segments: 已处理的片段信息
            source_files: 源文件路径及其哈希值
            metadata: 额外元数据
        """
        self.task_id = task_id
        self.stage = stage
        self.processed_segments = processed_segments or []
        self.source_files = source_files or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "task_id": self.task_id,
            "stage": self.stage,
            "processed_segments": self.processed_segments,
            "source_files": self.source_files,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecoveryPoint':
        """从字典创建实例"""
        recovery_point = cls(
            task_id=data["task_id"],
            stage=data["stage"],
            processed_segments=data.get("processed_segments", []),
            source_files=data.get("source_files", {}),
            metadata=data.get("metadata", {})
        )
        recovery_point.timestamp = data.get("timestamp", datetime.now().isoformat())
        return recovery_point


class RecoveryManager:
    """系统恢复管理器"""
    
    RECOVERY_DIR = "recovery"
    
    def __init__(self, workspace_dir: str = None):
        """
        初始化恢复管理器
        
        Args:
            workspace_dir: 工作目录，默认为当前目录
        """
        self.workspace_dir = workspace_dir or os.getcwd()
        self.recovery_dir = os.path.join(self.workspace_dir, self.RECOVERY_DIR)
        self._ensure_recovery_dir()
        self.current_task_id = None
        self.current_recovery_file = None
        logger.info(f"恢复管理器初始化，恢复目录: {self.recovery_dir}")
    
    def _ensure_recovery_dir(self) -> None:
        """确保恢复目录存在"""
        os.makedirs(self.recovery_dir, exist_ok=True)
    
    def _get_recovery_file_path(self, task_id: str) -> str:
        """获取恢复文件路径"""
        return os.path.join(self.recovery_dir, f"{task_id}.recovery")
    
    def start_task(self, task_id: str, source_files: Dict[str, str]) -> str:
        """
        开始一个新任务，计算源文件哈希并创建初始恢复点
        
        Args:
            task_id: 任务ID
            source_files: 源文件路径映射 {文件类型: 文件路径}
            
        Returns:
            任务ID
        """
        self.current_task_id = task_id
        self.current_recovery_file = self._get_recovery_file_path(task_id)
        
        # 计算源文件哈希值
        file_hashes = {}
        for file_type, file_path in source_files.items():
            try:
                file_hash = calculate_file_hash(file_path)
                file_hashes[file_path] = file_hash
                logger.debug(f"已计算文件哈希: {file_path} -> {file_hash[:8]}...")
            except Exception as e:
                logger.warning(f"无法计算文件哈希: {file_path}, 错误: {e}")
        
        # 创建初始恢复点
        recovery_point = RecoveryPoint(
            task_id=task_id,
            stage="initialized",
            source_files=file_hashes,
            metadata={"started_at": datetime.now().isoformat()}
        )
        
        # 保存恢复点
        self.save_recovery_point(recovery_point)
        logger.info(f"任务 {task_id} 已启动，创建了初始恢复点")
        
        return task_id

    def save_checkpoint(self, progress_data: Dict[str, Any], task_id: str = None) -> bool:
        """
        保存检查点 - 测试API兼容方法

        Args:
            progress_data: 进度数据
            task_id: 任务ID，如果为None则使用当前任务ID

        Returns:
            bool: 是否保存成功
        """
        try:
            # 使用当前任务ID或提供的任务ID
            current_task_id = task_id or self.current_task_id
            if not current_task_id:
                # 如果没有任务ID，生成一个
                current_task_id = f"checkpoint_{int(time.time())}"
                self.current_task_id = current_task_id

            # 创建恢复点
            recovery_point = RecoveryPoint(
                task_id=current_task_id,
                stage="checkpoint",
                processed_segments=progress_data.get("processed_segments", []),
                metadata={
                    "current_position": progress_data.get("current_position", ""),
                    "total_segments": progress_data.get("total_segments", 0),
                    "checkpoint_time": datetime.now().isoformat(),
                    "progress_data": progress_data
                }
            )

            # 保存恢复点
            success = self.save_recovery_point(recovery_point)

            if success:
                logger.info(f"检查点保存成功: 任务{current_task_id}, 位置{progress_data.get('current_position', 'unknown')}")
            else:
                logger.error(f"检查点保存失败: 任务{current_task_id}")

            return success

        except Exception as e:
            logger.error(f"保存检查点时发生错误: {e}")
            return False

    def load_checkpoint(self, task_id: str = None) -> Optional[Dict[str, Any]]:
        """
        加载检查点 - 测试API兼容方法

        Args:
            task_id: 任务ID，如果为None则使用当前任务ID

        Returns:
            Optional[Dict[str, Any]]: 检查点数据，如果不存在则返回None
        """
        try:
            # 使用当前任务ID或提供的任务ID
            current_task_id = task_id or self.current_task_id
            if not current_task_id:
                logger.warning("没有指定任务ID，无法加载检查点")
                return None

            # 尝试加载恢复点
            recovery_point = self.load_recovery_point(current_task_id)
            if not recovery_point:
                logger.info(f"没有找到任务{current_task_id}的检查点")
                return None

            # 提取进度数据
            metadata = recovery_point.metadata
            progress_data = metadata.get("progress_data", {})

            # 如果没有progress_data，从其他字段构建
            if not progress_data:
                progress_data = {
                    "processed_segments": recovery_point.processed_segments,
                    "current_position": metadata.get("current_position", ""),
                    "total_segments": metadata.get("total_segments", 0),
                    "task_id": recovery_point.task_id,
                    "stage": recovery_point.stage,
                    "timestamp": recovery_point.timestamp
                }

            logger.info(f"检查点加载成功: 任务{current_task_id}, 阶段{recovery_point.stage}")
            return progress_data

        except Exception as e:
            logger.error(f"加载检查点时发生错误: {e}")
            return None

    def load_recovery_point(self, task_id: str) -> Optional[RecoveryPoint]:
        """
        加载恢复点

        Args:
            task_id: 任务ID

        Returns:
            Optional[RecoveryPoint]: 恢复点对象，如果不存在则返回None
        """
        try:
            recovery_file = self._get_recovery_file_path(task_id)

            if not os.path.exists(recovery_file):
                logger.debug(f"恢复文件不存在: {recovery_file}")
                return None

            with open(recovery_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            recovery_point = RecoveryPoint.from_dict(data)
            logger.debug(f"恢复点加载成功: {task_id}")
            return recovery_point

        except Exception as e:
            logger.error(f"加载恢复点失败: {task_id}, 错误: {e}")
            return None
    
    def save_recovery_point(self, recovery_point: RecoveryPoint) -> bool:
        """
        保存恢复点
        
        Args:
            recovery_point: 恢复点对象
            
        Returns:
            保存是否成功
        """
        if not self.current_recovery_file:
            self.current_recovery_file = self._get_recovery_file_path(recovery_point.task_id)
        
        try:
            # 先写入临时文件，再重命名，确保原子操作
            temp_file = f"{self.current_recovery_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(recovery_point.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 原子替换原文件
            shutil.move(temp_file, self.current_recovery_file)
            logger.debug(f"已保存恢复点: {recovery_point.stage} (任务 {recovery_point.task_id})")
            return True
        except Exception as e:
            logger.error(f"保存恢复点失败: {e}")
            return False
    
    def update_progress(self, 
                       stage: str, 
                       processed_segment: Dict[str, Any] = None,
                       metadata: Dict[str, Any] = None) -> bool:
        """
        更新任务进度
        
        Args:
            stage: 当前处理阶段
            processed_segment: 新处理的片段(可选)
            metadata: 要更新的元数据(可选)
            
        Returns:
            更新是否成功
        """
        if not self.current_task_id:
            logger.warning("尝试更新进度但没有活动任务")
            return False
        
        # 读取当前恢复点
        recovery_point = self.load_recovery_point(self.current_task_id)
        if not recovery_point:
            logger.warning(f"无法加载当前任务 {self.current_task_id} 的恢复点")
            return False
        
        # 更新恢复点信息
        recovery_point.stage = stage
        
        # 添加新处理的片段
        if processed_segment:
            recovery_point.processed_segments.append(processed_segment)
        
        # 更新元数据
        if metadata:
            recovery_point.metadata.update(metadata)
        
        # 更新时间戳
        recovery_point.timestamp = datetime.now().isoformat()
        
        # 保存更新后的恢复点
        return self.save_recovery_point(recovery_point)
    
    def load_recovery_point(self, task_id: str) -> Optional[RecoveryPoint]:
        """
        加载恢复点
        
        Args:
            task_id: 任务ID
            
        Returns:
            恢复点对象，如果不存在则返回None
        """
        recovery_file = self._get_recovery_file_path(task_id)
        
        if not os.path.exists(recovery_file):
            logger.debug(f"恢复文件不存在: {recovery_file}")
            return None
        
        try:
            with open(recovery_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return RecoveryPoint.from_dict(data)
        except Exception as e:
            logger.error(f"加载恢复点失败: {e}")
            return None
    
    def can_resume(self, task_id: str, source_files: Dict[str, str]) -> bool:
        """
        检查任务是否可以恢复
        
        Args:
            task_id: 任务ID
            source_files: 源文件路径映射
            
        Returns:
            是否可以恢复
        """
        recovery_point = self.load_recovery_point(task_id)
        if not recovery_point:
            return False
        
        # 验证源文件是否发生变化
        for file_path in source_files.values():
            try:
                current_hash = calculate_file_hash(file_path)
                original_hash = recovery_point.source_files.get(file_path)
                
                if not original_hash or current_hash != original_hash:
                    logger.warning(f"源文件已更改，无法恢复: {file_path}")
                    return False
            except Exception as e:
                logger.warning(f"无法验证文件哈希: {file_path}, 错误: {e}")
                return False
        
        logger.info(f"任务 {task_id} 可以恢复到阶段: {recovery_point.stage}")
        return True
    
    def resume_task(self, task_id: str) -> Optional[RecoveryPoint]:
        """
        恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            恢复点对象，如果无法恢复则返回None
        """
        recovery_point = self.load_recovery_point(task_id)
        if not recovery_point:
            return None
        
        self.current_task_id = task_id
        self.current_recovery_file = self._get_recovery_file_path(task_id)
        
        logger.info(f"已恢复任务 {task_id} 到阶段: {recovery_point.stage}, 处理了 {len(recovery_point.processed_segments)} 个片段")
        return recovery_point
    
    def cleanup_task(self, task_id: str = None) -> bool:
        """
        清理任务的恢复数据
        
        Args:
            task_id: 任务ID，默认为当前任务
            
        Returns:
            清理是否成功
        """
        task_id = task_id or self.current_task_id
        if not task_id:
            logger.warning("尝试清理任务但没有指定任务ID")
            return False
        
        recovery_file = self._get_recovery_file_path(task_id)
        
        if os.path.exists(recovery_file):
            try:
                os.remove(recovery_file)
                logger.info(f"已清理任务 {task_id} 的恢复数据")
                
                if task_id == self.current_task_id:
                    self.current_task_id = None
                    self.current_recovery_file = None
                
                return True
            except Exception as e:
                logger.error(f"清理恢复数据失败: {e}")
                return False
        else:
            logger.debug(f"恢复文件不存在，无需清理: {recovery_file}")
            return True
    
    def list_recoverable_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有可恢复的任务
        
        Returns:
            可恢复任务的列表，每个任务为一个字典
        """
        tasks = []
        
        if not os.path.exists(self.recovery_dir):
            return tasks
        
        for file_name in os.listdir(self.recovery_dir):
            if file_name.endswith('.recovery'):
                task_id = file_name[:-9]  # 去除 .recovery 后缀
                recovery_point = self.load_recovery_point(task_id)
                
                if recovery_point:
                    try:
                        # 获取恢复文件的修改时间
                        file_path = self._get_recovery_file_path(task_id)
                        mtime = os.path.getmtime(file_path)
                        mtime_str = datetime.fromtimestamp(mtime).isoformat()
                        
                        tasks.append({
                            "task_id": task_id,
                            "stage": recovery_point.stage,
                            "timestamp": recovery_point.timestamp,
                            "modified": mtime_str,
                            "segments_count": len(recovery_point.processed_segments),
                            "metadata": recovery_point.metadata
                        })
                    except Exception as e:
                        logger.warning(f"获取任务信息失败: {task_id}, 错误: {e}")
        
        # 按修改时间降序排序
        tasks.sort(key=lambda x: x["modified"], reverse=True)
        return tasks
    
    def cleanup_old_recovery_files(self, max_age_days: int = 30) -> int:
        """
        清理老旧的恢复文件
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的文件数量
        """
        if not os.path.exists(self.recovery_dir):
            return 0
        
        count = 0
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        for file_name in os.listdir(self.recovery_dir):
            if file_name.endswith('.recovery'):
                file_path = os.path.join(self.recovery_dir, file_name)
                
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime < cutoff_time:
                        os.remove(file_path)
                        count += 1
                        logger.debug(f"已清理老旧恢复文件: {file_name}")
                except Exception as e:
                    logger.warning(f"清理恢复文件失败: {file_name}, 错误: {e}")
        
        if count > 0:
            logger.info(f"已清理 {count} 个老旧恢复文件")
        
        return count


# 全局恢复管理器实例
_recovery_manager = None

def get_recovery_manager() -> RecoveryManager:
    """获取全局恢复管理器实例"""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager 