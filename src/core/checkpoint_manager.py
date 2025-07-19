#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查点管理器模块

负责视频处理过程中的检查点保存和恢复，以支持在处理中断后能够从中断点继续处理。
"""

import os
import json
import time
import threading
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union

from loguru import logger

# 导入恢复管理器
from src.core.recovery_manager import get_recovery_manager

# 默认检查点间隔(秒)
DEFAULT_CHECKPOINT_INTERVAL = 60  # 默认每分钟保存一次检查点

class CheckpointManager:
    """视频处理检查点管理器，用于处理过程中定期保存处理状态"""
    
    def __init__(self, task_id: str = None, auto_save: bool = True, 
                 interval: int = DEFAULT_CHECKPOINT_INTERVAL):
        """
        初始化检查点管理器
        
        Args:
            task_id: 任务ID，如果为None则自动生成
            auto_save: 是否自动保存检查点
            interval: 自动保存间隔(秒)
        """
        self.recovery_manager = get_recovery_manager()
        self.task_id = task_id or f"task_{int(time.time())}"
        self.auto_save = auto_save
        self.interval = interval
        
        # 检查点数据
        self.checkpoint_data = {
            "task_id": self.task_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "progress": 0.0,
            "stage": "initialized",
            "segments": [],
            "completed_segments": [],
            "current_segment": None,
            "total_segments": 0,
            "metadata": {},
            "options": {},
            "source_files": {},
            "output_files": {}
        }
        
        # 检查点自动保存线程
        self.save_thread = None
        self.stop_flag = threading.Event()
        
        # 注册任务到恢复管理器
        self._register_task()
        
        # 如果启用自动保存，启动保存线程
        if self.auto_save:
            self.start_auto_save()
    
    def _register_task(self) -> bool:
        """
        向恢复管理器注册任务
        
        Returns:
            注册是否成功
        """
        try:
            self.recovery_manager.start_task(
                task_id=self.task_id,
                source_files=self.checkpoint_data["source_files"]
            )
            
            logger.debug(f"任务 {self.task_id} 已注册到恢复管理器")
            return True
        except Exception as e:
            logger.error(f"注册任务到恢复管理器失败: {e}")
            return False
    
    def update_source_files(self, source_files: Dict[str, str]) -> None:
        """
        更新源文件信息
        
        Args:
            source_files: 源文件信息，格式为 {文件类型: 文件路径}
        """
        self.checkpoint_data["source_files"] = source_files
        
        # 更新恢复管理器中的源文件信息
        self._register_task()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        更新元数据
        
        Args:
            metadata: 元数据字典
        """
        self.checkpoint_data["metadata"].update(metadata)
        self.checkpoint_data["updated_at"] = datetime.now().isoformat()
    
    def update_options(self, options: Dict[str, Any]) -> None:
        """
        更新处理选项
        
        Args:
            options: 处理选项字典
        """
        self.checkpoint_data["options"].update(options)
        self.checkpoint_data["updated_at"] = datetime.now().isoformat()
    
    def start_auto_save(self) -> None:
        """启动自动保存线程"""
        if self.save_thread is not None and self.save_thread.is_alive():
            logger.warning("自动保存线程已在运行")
            return
        
        self.stop_flag.clear()
        self.save_thread = threading.Thread(
            target=self._auto_save_worker,
            daemon=True
        )
        self.save_thread.start()
        logger.debug(f"已启动自动保存线程，间隔: {self.interval}秒")
    
    def stop_auto_save(self) -> None:
        """停止自动保存线程"""
        if self.save_thread is None or not self.save_thread.is_alive():
            return
        
        self.stop_flag.set()
        self.save_thread.join(timeout=5)
        logger.debug("已停止自动保存线程")
    
    def _auto_save_worker(self) -> None:
        """自动保存工作线程"""
        while not self.stop_flag.is_set():
            try:
                # 保存检查点
                self.save_checkpoint()
                
                # 等待下一次保存
                # 使用小间隔检查停止标志，以便能够及时响应停止请求
                for _ in range(self.interval * 2):  # 每0.5秒检查一次
                    if self.stop_flag.is_set():
                        break
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"自动保存检查点时出错: {e}")
                # 出错后等待一段时间再重试
                time.sleep(5)
    
    def update_progress(self, progress: float, stage: str = None,
                       current_segment: Dict[str, Any] = None,
                       completed_segment: Dict[str, Any] = None) -> None:
        """
        更新处理进度
        
        Args:
            progress: 处理进度(0-1.0)
            stage: 处理阶段
            current_segment: 当前处理的片段信息
            completed_segment: 已完成的片段信息
        """
        self.checkpoint_data["progress"] = progress
        
        if stage:
            self.checkpoint_data["stage"] = stage
        
        if current_segment:
            self.checkpoint_data["current_segment"] = current_segment
        
        if completed_segment:
            # 将已完成的片段添加到列表
            self.checkpoint_data["completed_segments"].append(completed_segment)
            
            # 更新已处理计数
            segments_count = len(self.checkpoint_data["completed_segments"])
            completion_percent = 0
            if self.checkpoint_data["total_segments"] > 0:
                completion_percent = segments_count / self.checkpoint_data["total_segments"]
            
            logger.debug(f"片段 {completed_segment.get('id', 'unknown')} 已完成，"
                       f"总进度: {completion_percent:.1%} ({segments_count}/{self.checkpoint_data['total_segments']})")
        
        self.checkpoint_data["updated_at"] = datetime.now().isoformat()
    
    def set_segments(self, segments: List[Dict[str, Any]]) -> None:
        """
        设置要处理的片段列表
        
        Args:
            segments: 片段信息列表
        """
        self.checkpoint_data["segments"] = segments
        self.checkpoint_data["total_segments"] = len(segments)
        self.checkpoint_data["updated_at"] = datetime.now().isoformat()
        
        logger.debug(f"已设置处理片段，总数: {len(segments)}")
    
    def set_output_files(self, output_files: Dict[str, str]) -> None:
        """
        设置输出文件
        
        Args:
            output_files: 输出文件，格式为 {文件类型: 文件路径}
        """
        self.checkpoint_data["output_files"] = output_files
        self.checkpoint_data["updated_at"] = datetime.now().isoformat()
    
    def save_checkpoint(self) -> bool:
        """
        保存检查点
        
        Returns:
            保存是否成功
        """
        try:
            # 更新时间戳
            self.checkpoint_data["updated_at"] = datetime.now().isoformat()
            
            # 保存到恢复管理器
            success = self.recovery_manager.update_progress(
                stage=self.checkpoint_data["stage"],
                processed_segment=self.checkpoint_data["current_segment"],
                metadata={
                    "progress": self.checkpoint_data["progress"],
                    "completed_segments": len(self.checkpoint_data["completed_segments"]),
                    "total_segments": self.checkpoint_data["total_segments"],
                    **self.checkpoint_data["metadata"]
                }
            )
            
            if success:
                logger.debug(f"已保存检查点，进度: {self.checkpoint_data['progress']:.1%}, "
                           f"阶段: {self.checkpoint_data['stage']}")
            else:
                logger.warning("保存检查点失败")
                
            return success
        except Exception as e:
            logger.error(f"保存检查点时出错: {e}")
            return False
    
    def load_checkpoint(self, task_id: str = None) -> Optional[Dict[str, Any]]:
        """
        加载检查点
        
        Args:
            task_id: 要加载的任务ID，如果为None则使用当前任务ID
            
        Returns:
            检查点数据或None(如果加载失败)
        """
        task_id = task_id or self.task_id
        
        try:
            # 从恢复管理器加载恢复点
            recovery_point = self.recovery_manager.load_recovery_point(task_id)
            
            if not recovery_point:
                logger.warning(f"未找到任务 {task_id} 的恢复点")
                return None
            
            # 更新检查点数据
            self.checkpoint_data["task_id"] = task_id
            self.checkpoint_data["progress"] = recovery_point.metadata.get("progress", 0.0)
            self.checkpoint_data["stage"] = recovery_point.stage
            
            # 恢复已处理片段
            if "processed_segments" in recovery_point.metadata:
                self.checkpoint_data["completed_segments"] = recovery_point.metadata["processed_segments"]
                
            # 恢复源文件信息
            self.checkpoint_data["source_files"] = recovery_point.source_files
            
            # 恢复其他元数据
            for key, value in recovery_point.metadata.items():
                if key not in ["progress", "processed_segments"]:
                    self.checkpoint_data["metadata"][key] = value
            
            logger.info(f"已加载任务 {task_id} 的检查点，进度: {self.checkpoint_data['progress']:.1%}, "
                       f"阶段: {self.checkpoint_data['stage']}")
            
            return self.checkpoint_data
        except Exception as e:
            logger.error(f"加载检查点时出错: {e}")
            return None
    
    def finalize(self) -> bool:
        """
        完成处理，保存最终状态并清理资源
        
        Returns:
            是否成功完成
        """
        try:
            # 更新状态为已完成
            self.checkpoint_data["stage"] = "completed"
            self.checkpoint_data["progress"] = 1.0
            self.checkpoint_data["updated_at"] = datetime.now().isoformat()
            self.checkpoint_data["metadata"]["completed_at"] = datetime.now().isoformat()
            
            # 保存最终状态
            success = self.save_checkpoint()
            
            # 停止自动保存
            self.stop_auto_save()
            
            # 清理资源(但保留恢复点一段时间)
            # self.recovery_manager.cleanup_task(self.task_id)
            
            logger.info(f"任务 {self.task_id} 处理已完成")
            return success
        except Exception as e:
            logger.error(f"完成处理时出错: {e}")
            return False
    
    def get_checkpoint_data(self) -> Dict[str, Any]:
        """
        获取当前检查点数据
        
        Returns:
            检查点数据副本
        """
        return self.checkpoint_data.copy()
    
    def get_remaining_segments(self) -> List[Dict[str, Any]]:
        """
        获取尚未处理的片段
        
        Returns:
            未处理片段列表
        """
        # 获取已完成片段的ID
        completed_ids = {s.get("id") for s in self.checkpoint_data["completed_segments"]}
        
        # 过滤出未处理的片段
        remaining = [s for s in self.checkpoint_data["segments"] 
                   if s.get("id") not in completed_ids]
        
        return remaining
    
    def __del__(self):
        """析构方法，确保停止自动保存线程"""
        self.stop_auto_save()


# 全局检查点管理器实例
_checkpoint_manager = None

def get_checkpoint_manager(task_id: str = None, auto_save: bool = True,
                          interval: int = DEFAULT_CHECKPOINT_INTERVAL) -> CheckpointManager:
    """
    获取检查点管理器实例
    
    Args:
        task_id: 任务ID，如果为None则使用现有任务ID或自动生成
        auto_save: 是否自动保存
        interval: 自动保存间隔(秒)
        
    Returns:
        检查点管理器实例
    """
    global _checkpoint_manager
    
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager(
            task_id=task_id,
            auto_save=auto_save,
            interval=interval
        )
    elif task_id is not None and task_id != _checkpoint_manager.task_id:
        # 如果请求了不同的任务ID，停止当前实例并创建新实例
        _checkpoint_manager.stop_auto_save()
        _checkpoint_manager = CheckpointManager(
            task_id=task_id,
            auto_save=auto_save,
            interval=interval
        )
    
    return _checkpoint_manager


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    # 创建检查点管理器
    manager = get_checkpoint_manager(auto_save=True, interval=5)
    
    # 设置源文件
    manager.update_source_files({
        "video": "/path/to/video.mp4",
        "audio": "/path/to/audio.mp3"
    })
    
    # 设置处理选项
    manager.update_options({
        "quality": "high",
        "format": "mp4",
        "resolution": "1080p"
    })
    
    # 设置片段
    segments = [
        {"id": f"segment_{i}", "start": i*10, "end": (i+1)*10} 
        for i in range(10)
    ]
    manager.set_segments(segments)
    
    # 模拟处理过程
    for i, segment in enumerate(segments):
        # 更新进度
        progress = (i + 1) / len(segments)
        manager.update_progress(
            progress=progress,
            stage="processing",
            current_segment=segment,
            completed_segment=segment if i > 0 else None
        )
        
        # 等待一会儿
        time.sleep(2)
    
    # 完成处理
    manager.finalize() 