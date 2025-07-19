#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恢复管理器 - 提供异常恢复和断点续传功能
"""

import os
import json
import time
import logging
import hashlib
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import pickle

logger = logging.getLogger(__name__)

@dataclass
class RecoveryPoint:
    """恢复点数据类"""
    id: str                          # 恢复点ID
    timestamp: float                 # 创建时间戳
    operation_type: str              # 操作类型
    progress: float                  # 进度百分比 (0.0-1.0)
    state_data: Dict[str, Any]       # 状态数据
    file_checksums: Dict[str, str]   # 文件校验和
    metadata: Dict[str, Any]         # 元数据

@dataclass
class RecoverySession:
    """恢复会话数据类"""
    session_id: str                  # 会话ID
    start_time: float               # 开始时间
    operation_type: str             # 操作类型
    total_steps: int                # 总步数
    completed_steps: int            # 已完成步数
    recovery_points: List[str]      # 恢复点ID列表
    is_active: bool                 # 是否活跃

class RecoveryManager:
    """恢复管理器"""
    
    def __init__(self, recovery_dir: str = "recovery"):
        """
        初始化恢复管理器
        
        Args:
            recovery_dir: 恢复数据存储目录
        """
        self.recovery_dir = Path(recovery_dir)
        self.recovery_dir.mkdir(exist_ok=True)
        
        # 子目录
        self.checkpoints_dir = self.recovery_dir / "checkpoints"
        self.sessions_dir = self.recovery_dir / "sessions"
        self.temp_dir = self.recovery_dir / "temp"
        
        for dir_path in [self.checkpoints_dir, self.sessions_dir, self.temp_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.current_session: Optional[RecoverySession] = None
        self.recovery_points: Dict[str, RecoveryPoint] = {}
        self.auto_save_interval = 30  # 自动保存间隔（秒）
        self.max_recovery_points = 100  # 最大恢复点数量
        
        # 线程锁
        self._lock = threading.Lock()
        self._auto_save_thread = None
        self._stop_auto_save = False
        
        logger.info(f"恢复管理器初始化完成，恢复目录: {self.recovery_dir}")
        
        # 加载现有的恢复数据
        self._load_existing_data()

    def start_session(self, operation_type: str, total_steps: int = 100) -> str:
        """
        开始新的恢复会话
        
        Args:
            operation_type: 操作类型（如 'video_processing', 'model_training'）
            total_steps: 总步数
            
        Returns:
            会话ID
        """
        with self._lock:
            session_id = f"{operation_type}_{int(time.time() * 1000)}"
            
            self.current_session = RecoverySession(
                session_id=session_id,
                start_time=time.time(),
                operation_type=operation_type,
                total_steps=total_steps,
                completed_steps=0,
                recovery_points=[],
                is_active=True
            )
            
            # 保存会话
            self._save_session(self.current_session)
            
            # 启动自动保存
            self._start_auto_save()
            
            logger.info(f"开始恢复会话: {session_id}, 操作类型: {operation_type}")
            return session_id

    def create_checkpoint(self, step_name: str, state_data: Dict[str, Any], 
                         file_paths: List[str] = None) -> str:
        """
        创建恢复点
        
        Args:
            step_name: 步骤名称
            state_data: 状态数据
            file_paths: 相关文件路径列表
            
        Returns:
            恢复点ID
        """
        if not self.current_session:
            raise RuntimeError("没有活跃的恢复会话")
        
        with self._lock:
            checkpoint_id = f"{self.current_session.session_id}_{step_name}_{int(time.time() * 1000)}"
            
            # 计算文件校验和
            file_checksums = {}
            if file_paths:
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        file_checksums[file_path] = self._calculate_file_checksum(file_path)
            
            # 计算进度
            self.current_session.completed_steps += 1
            progress = self.current_session.completed_steps / self.current_session.total_steps
            
            recovery_point = RecoveryPoint(
                id=checkpoint_id,
                timestamp=time.time(),
                operation_type=self.current_session.operation_type,
                progress=progress,
                state_data=state_data.copy(),
                file_checksums=file_checksums,
                metadata={
                    "step_name": step_name,
                    "session_id": self.current_session.session_id,
                    "step_number": self.current_session.completed_steps
                }
            )
            
            # 保存恢复点
            self.recovery_points[checkpoint_id] = recovery_point
            self.current_session.recovery_points.append(checkpoint_id)
            
            # 持久化
            self._save_checkpoint(recovery_point)
            self._save_session(self.current_session)
            
            # 清理旧的恢复点
            self._cleanup_old_checkpoints()
            
            logger.info(f"创建恢复点: {checkpoint_id}, 进度: {progress:.1%}")
            return checkpoint_id

    def get_latest_checkpoint(self, operation_type: str = None) -> Optional[RecoveryPoint]:
        """
        获取最新的恢复点
        
        Args:
            operation_type: 操作类型过滤
            
        Returns:
            最新的恢复点，如果没有则返回None
        """
        with self._lock:
            filtered_points = []
            
            for point in self.recovery_points.values():
                if operation_type is None or point.operation_type == operation_type:
                    filtered_points.append(point)
            
            if not filtered_points:
                return None
            
            # 按时间戳排序，返回最新的
            latest_point = max(filtered_points, key=lambda p: p.timestamp)
            logger.info(f"获取最新恢复点: {latest_point.id}")
            return latest_point

    def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        从恢复点恢复
        
        Args:
            checkpoint_id: 恢复点ID
            
        Returns:
            恢复的状态数据，如果失败则返回None
        """
        try:
            # 从文件加载恢复点
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
            if not checkpoint_file.exists():
                logger.error(f"恢复点文件不存在: {checkpoint_file}")
                return None
            
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            recovery_point = RecoveryPoint(**checkpoint_data)
            
            # 验证文件完整性
            if not self._verify_file_integrity(recovery_point):
                logger.warning(f"恢复点文件完整性验证失败: {checkpoint_id}")
                # 继续恢复，但记录警告
            
            logger.info(f"从恢复点恢复: {checkpoint_id}, 进度: {recovery_point.progress:.1%}")
            return recovery_point.state_data
            
        except Exception as e:
            logger.error(f"从恢复点恢复失败: {checkpoint_id} - {e}")
            return None

    def end_session(self, success: bool = True):
        """
        结束当前会话
        
        Args:
            success: 是否成功完成
        """
        if not self.current_session:
            return
        
        with self._lock:
            self.current_session.is_active = False
            
            # 保存最终状态
            self._save_session(self.current_session)
            
            # 停止自动保存
            self._stop_auto_save_thread()
            
            session_id = self.current_session.session_id
            logger.info(f"结束恢复会话: {session_id}, 成功: {success}")
            
            self.current_session = None

    def cleanup_old_data(self, days: int = 7):
        """
        清理旧的恢复数据
        
        Args:
            days: 保留天数
        """
        cutoff_time = time.time() - (days * 24 * 3600)
        
        with self._lock:
            # 清理旧的恢复点
            to_remove = []
            for checkpoint_id, point in self.recovery_points.items():
                if point.timestamp < cutoff_time:
                    to_remove.append(checkpoint_id)
            
            for checkpoint_id in to_remove:
                del self.recovery_points[checkpoint_id]
                checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
            
            # 清理旧的会话文件
            for session_file in self.sessions_dir.glob("*.json"):
                if session_file.stat().st_mtime < cutoff_time:
                    session_file.unlink()
            
            logger.info(f"清理了 {len(to_remove)} 个旧恢复点和相关会话数据")

    def get_recovery_status(self) -> Dict[str, Any]:
        """
        获取恢复状态信息
        
        Returns:
            状态信息字典
        """
        with self._lock:
            status = {
                "current_session": asdict(self.current_session) if self.current_session else None,
                "total_checkpoints": len(self.recovery_points),
                "recovery_dir": str(self.recovery_dir),
                "auto_save_active": self._auto_save_thread is not None and self._auto_save_thread.is_alive()
            }
            
            if self.current_session:
                status["session_progress"] = self.current_session.completed_steps / self.current_session.total_steps
            
            return status

    def _calculate_file_checksum(self, file_path: str) -> str:
        """计算文件MD5校验和"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"计算文件校验和失败: {file_path} - {e}")
            return ""

    def _verify_file_integrity(self, recovery_point: RecoveryPoint) -> bool:
        """验证文件完整性"""
        try:
            for file_path, expected_checksum in recovery_point.file_checksums.items():
                if not os.path.exists(file_path):
                    logger.warning(f"文件不存在: {file_path}")
                    return False

                current_checksum = self._calculate_file_checksum(file_path)
                if current_checksum != expected_checksum:
                    logger.warning(f"文件校验和不匹配: {file_path}")
                    return False

            return True
        except Exception as e:
            logger.error(f"文件完整性验证失败: {e}")
            return False

    def _save_checkpoint(self, recovery_point: RecoveryPoint):
        """保存恢复点到文件"""
        try:
            checkpoint_file = self.checkpoints_dir / f"{recovery_point.id}.json"
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(recovery_point), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存恢复点失败: {recovery_point.id} - {e}")

    def _save_session(self, session: RecoverySession):
        """保存会话到文件"""
        try:
            session_file = self.sessions_dir / f"{session.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(session), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存会话失败: {session.session_id} - {e}")

    def _load_existing_data(self):
        """加载现有的恢复数据"""
        try:
            # 加载恢复点
            for checkpoint_file in self.checkpoints_dir.glob("*.json"):
                try:
                    with open(checkpoint_file, 'r', encoding='utf-8') as f:
                        checkpoint_data = json.load(f)

                    recovery_point = RecoveryPoint(**checkpoint_data)
                    self.recovery_points[recovery_point.id] = recovery_point
                except Exception as e:
                    logger.warning(f"加载恢复点失败: {checkpoint_file} - {e}")

            logger.info(f"加载了 {len(self.recovery_points)} 个现有恢复点")

        except Exception as e:
            logger.error(f"加载现有恢复数据失败: {e}")

    def _cleanup_old_checkpoints(self):
        """清理旧的恢复点"""
        if len(self.recovery_points) <= self.max_recovery_points:
            return

        # 按时间戳排序，删除最旧的
        sorted_points = sorted(self.recovery_points.items(), key=lambda x: x[1].timestamp)
        to_remove = sorted_points[:-self.max_recovery_points]

        for checkpoint_id, _ in to_remove:
            del self.recovery_points[checkpoint_id]
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                checkpoint_file.unlink()

    def _start_auto_save(self):
        """启动自动保存线程"""
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            return

        self._stop_auto_save = False
        self._auto_save_thread = threading.Thread(target=self._auto_save_worker, daemon=True)
        self._auto_save_thread.start()

    def _stop_auto_save_thread(self):
        """停止自动保存线程"""
        self._stop_auto_save = True
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            self._auto_save_thread.join(timeout=5)

    def _auto_save_worker(self):
        """自动保存工作线程"""
        while not self._stop_auto_save:
            try:
                time.sleep(self.auto_save_interval)

                if self.current_session and self.current_session.is_active:
                    with self._lock:
                        self._save_session(self.current_session)
                        logger.debug("自动保存会话状态")

            except Exception as e:
                logger.error(f"自动保存失败: {e}")


# 全局恢复管理器实例
_recovery_manager = None

def get_recovery_manager() -> RecoveryManager:
    """获取全局恢复管理器实例"""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager

def create_checkpoint(step_name: str, state_data: Dict[str, Any],
                     file_paths: List[str] = None) -> str:
    """便捷函数：创建恢复点"""
    return get_recovery_manager().create_checkpoint(step_name, state_data, file_paths)

def restore_from_latest(operation_type: str = None) -> Optional[Dict[str, Any]]:
    """便捷函数：从最新恢复点恢复"""
    manager = get_recovery_manager()
    latest_point = manager.get_latest_checkpoint(operation_type)
    if latest_point:
        return manager.restore_from_checkpoint(latest_point.id)
    return None
