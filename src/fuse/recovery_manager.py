"""
熔断状态恢复系统 (Fuse State Recovery System)
-------------------------------------------
负责在系统发生熔断（资源紧急释放）后进行状态恢复，确保系统可以安全地
重新加载资源并继续运行。主要功能包括：

1. 记录熔断前状态 - 保存关键资源状态，用于后续恢复
2. 按序恢复资源 - 以与熔断相反的顺序恢复资源
3. 渐进式恢复 - 添加适当间隔，避免恢复过程中再次触发熔断
4. 恢复监控 - 在恢复过程中持续监控资源状态，必要时暂停恢复
5. 健康检查 - 确保恢复后系统处于稳定状态

此系统与安全熔断执行器(safe_executor.py)配合使用，为低资源环境提供可靠性保障。
"""

import os
import time
import json
import threading
import logging
import traceback
from typing import Dict, List, Any, Optional, Callable, Union, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
import psutil

from .safe_executor import get_executor, force_gc, release_resource

# 配置日志
logger = logging.getLogger("fuse_recovery")

@dataclass
class ResourceState:
    """资源状态记录，用于恢复时重建资源"""
    resource_id: str
    resource_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    creation_timestamp: float = field(default_factory=time.time)


class FuseRecovery:
    """
    熔断状态恢复管理器
    负责在系统熔断后有序地恢复资源和状态
    """
    
    def __init__(self):
        """初始化熔断恢复管理器"""
        self.pre_fuse_state = {}         # 保存熔断前的状态
        self.recovery_sequence = []      # 恢复序列
        self.recovery_ongoing = False    # 是否正在进行恢复
        self.recovery_lock = threading.RLock()  # 恢复过程锁
        self.recovery_monitor_thread = None     # 恢复监控线程
        self.recovery_pause_event = threading.Event()  # 恢复暂停事件
        self.recovery_interval = 0.1     # 恢复操作间隔，默认100ms
        self.memory_threshold = 80       # 内存阈值，超过此值暂停恢复
        
        # 资源恢复处理器注册表
        self.resource_handlers = {}
        
        # 恢复状态回调
        self.recovery_callbacks = []
        
        # 恢复日志目录
        self.recovery_log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "recovery")
        os.makedirs(self.recovery_log_dir, exist_ok=True)
    
    def register_pre_fuse_state(self, resource_id: str, resource_state: ResourceState) -> None:
        """
        注册一个资源的熔断前状态
        
        Args:
            resource_id: 资源标识符
            resource_state: 资源状态对象
        """
        with self.recovery_lock:
            self.pre_fuse_state[resource_id] = resource_state
            if resource_id not in self.recovery_sequence:
                self.recovery_sequence.append(resource_id)
            logger.debug(f"已注册资源 {resource_id} 的熔断前状态")
    
    def register_resource_handler(self, resource_type: str, handler: Callable) -> None:
        """
        注册资源类型的恢复处理函数
        
        Args:
            resource_type: 资源类型标识
            handler: 恢复处理函数，接收ResourceState返回恢复后的资源
        """
        self.resource_handlers[resource_type] = handler
        logger.debug(f"已注册资源类型 {resource_type} 的恢复处理器")
    
    def register_recovery_callback(self, callback: Callable[[str, bool], None]) -> None:
        """
        注册恢复状态回调函数
        
        Args:
            callback: 回调函数，接收资源ID和成功标志
        """
        self.recovery_callbacks.append(callback)
    
    def snapshot_current_state(self) -> Dict[str, ResourceState]:
        """
        获取当前系统资源状态的快照
        用于在熔断前保存状态
        
        Returns:
            资源状态字典
        """
        # 从执行器获取已注册的资源信息
        executor = get_executor()
        current_state = {}
        
        with executor.action_lock:
            for resource_id, resource_data in executor.registered_resources.items():
                # 根据资源类型提取元数据
                metadata = self._extract_resource_metadata(resource_id, resource_data["resource"])
                
                # 创建资源状态对象
                resource_state = ResourceState(
                    resource_id=resource_id,
                    resource_type=self._detect_resource_type(resource_id, resource_data["resource"]),
                    metadata=metadata,
                    dependencies=self._detect_dependencies(resource_id, resource_data["resource"]),
                    creation_timestamp=time.time()
                )
                
                current_state[resource_id] = resource_state
        
        return current_state
    
    def _extract_resource_metadata(self, resource_id: str, resource: Any) -> Dict[str, Any]:
        """从资源对象提取恢复所需的元数据"""
        metadata = {}
        
        # 根据资源ID的前缀确定资源类型并提取相关元数据
        if resource_id.startswith("model_"):
            # 模型资源
            metadata["model_type"] = getattr(resource, "model_type", "unknown")
            metadata["model_path"] = getattr(resource, "model_path", "")
            metadata["quantization"] = getattr(resource, "quantization", "default")
            metadata["language"] = "zh" if "zh" in resource_id else "en"
            
        elif resource_id.startswith("video_"):
            # 视频资源
            metadata["file_path"] = getattr(resource, "file_path", "")
            metadata["duration"] = getattr(resource, "duration", 0)
            
        elif resource_id.startswith("subtitle_"):
            # 字幕资源
            metadata["file_path"] = getattr(resource, "file_path", "")
            metadata["language"] = getattr(resource, "language", "auto")
            
        elif resource_id.startswith("temp_"):
            # 临时资源
            metadata["cleanup_required"] = True
        
        return metadata
    
    def _detect_resource_type(self, resource_id: str, resource: Any) -> str:
        """检测资源类型"""
        if resource_id.startswith("model_"):
            return "model"
        elif resource_id.startswith("video_"):
            return "video"
        elif resource_id.startswith("subtitle_"):
            return "subtitle"
        elif resource_id.startswith("temp_"):
            return "temporary"
        else:
            # 尝试通过类名推断
            return resource.__class__.__name__.lower()
    
    def _detect_dependencies(self, resource_id: str, resource: Any) -> List[str]:
        """检测资源依赖关系"""
        # 模拟资源依赖逻辑
        dependencies = []
        
        # 视频处理可能依赖模型
        if resource_id.startswith("video_processed_"):
            # 假设处理后的视频依赖于原始视频和模型
            original_video_id = resource_id.replace("processed_", "")
            dependencies.append(original_video_id)
            
            # 添加可能的模型依赖
            for model_prefix in ["model_zh_", "model_en_"]:
                for suffix in ["main", "subtitle", "scene"]:
                    potential_dep = f"{model_prefix}{suffix}"
                    if hasattr(resource, "used_models") and potential_dep in resource.used_models:
                        dependencies.append(potential_dep)
        
        return dependencies
    
    def save_state_snapshot(self) -> None:
        """保存当前系统状态快照"""
        current_state = self.snapshot_current_state()
        
        with self.recovery_lock:
            self.pre_fuse_state = current_state
            self.recovery_sequence = list(current_state.keys())
            
        # 将状态保存到磁盘(仅用于灾难恢复)
        self._save_state_to_disk()
        
        logger.info(f"已保存系统状态快照，包含 {len(current_state)} 个资源")
    
    def _save_state_to_disk(self) -> None:
        """将状态保存到磁盘，用于在崩溃后恢复"""
        try:
            # 创建一个不包含实际资源对象的状态副本
            serializable_state = {}
            for res_id, res_state in self.pre_fuse_state.items():
                serializable_state[res_id] = asdict(res_state)
            
            # 保存到日志目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            state_file = os.path.join(self.recovery_log_dir, f"state_{timestamp}.json")
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, ensure_ascii=False, indent=2)
                
            # 保留最新状态的软链接
            latest_file = os.path.join(self.recovery_log_dir, "state_latest.json")
            if os.path.exists(latest_file):
                os.remove(latest_file)
                
            # 创建软链接(仅UNIX)或复制(Windows)
            try:
                os.symlink(state_file, latest_file)
            except (OSError, AttributeError):
                # Windows不支持软链接，使用复制
                import shutil

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

                shutil.copy2(state_file, latest_file)
                
        except Exception as e:
            logger.error(f"保存状态到磁盘失败: {e}")
    
    def clear_state(self) -> None:
        """清除保存的状态"""
        with self.recovery_lock:
            self.pre_fuse_state = {}
            self.recovery_sequence = []
        logger.debug("已清除熔断恢复状态")
    
    def rollback(self) -> bool:
        """
        执行资源回滚，恢复熔断前的系统状态
        
        Returns:
            恢复是否成功
        """
        if not self.pre_fuse_state:
            logger.warning("没有可用的熔断前状态，无法执行回滚")
            return False
        
        with self.recovery_lock:
            if self.recovery_ongoing:
                logger.warning("恢复已在进行中，请勿重复调用")
                return False
            
            self.recovery_ongoing = True
            self.recovery_pause_event.clear()  # 确保恢复开始时没有暂停
        
        # 启动恢复监控线程
        self.recovery_monitor_thread = threading.Thread(
            target=self.monitor_recovery,
            daemon=True,
            name="FuseRecoveryMonitor"
        )
        self.recovery_monitor_thread.start()
        
        try:
            logger.info("开始执行熔断状态恢复...")
            
            # 首先执行一次垃圾回收，确保有足够内存
            force_gc()
            
            # 按照与注册相反的顺序恢复资源
            success_count = 0
            failed_resources = []
            
            for res_id in reversed(self.recovery_sequence):
                # 检查恢复是否被暂停
                if self.recovery_pause_event.is_set():
                    logger.info("恢复过程已暂停，等待恢复...")
                    self.recovery_pause_event.wait()  # 等待恢复继续
                
                if res_id in self.pre_fuse_state:
                    resource_state = self.pre_fuse_state[res_id]
                    
                    try:
                        # 尝试恢复资源
                        success = self._restore_resource(res_id, resource_state)
                        
                        # 通知回调
                        for callback in self.recovery_callbacks:
                            try:
                                callback(res_id, success)
                            except Exception as cb_err:
                                logger.error(f"资源恢复回调错误: {cb_err}")
                        
                        if success:
                            success_count += 1
                            logger.info(f"成功恢复资源: {res_id}")
                        else:
                            failed_resources.append(res_id)
                            logger.warning(f"无法恢复资源: {res_id}")
                        
                        # 防止恢复过载，每次恢复后休眠
                        time.sleep(self.recovery_interval)
                        
                    except Exception as e:
                        logger.error(f"恢复资源 {res_id} 时发生错误: {e}\n{traceback.format_exc()}")
                        failed_resources.append(res_id)
            
            # 恢复结束
            with self.recovery_lock:
                self.recovery_ongoing = False
            
            # 记录恢复结果
            success_rate = success_count / len(self.recovery_sequence) if self.recovery_sequence else 0
            logger.info(f"熔断状态恢复完成。成功: {success_count}, "
                       f"失败: {len(failed_resources)}, 成功率: {success_rate:.1%}")
            
            # 清理恢复完成的状态(可选，取决于是否需要重试失败的恢复)
            if not failed_resources:
                self.clear_state()
            else:
                # 仅保留失败的资源状态，以便后续重试
                with self.recovery_lock:
                    new_state = {}
                    for failed_id in failed_resources:
                        if failed_id in self.pre_fuse_state:
                            new_state[failed_id] = self.pre_fuse_state[failed_id]
                    self.pre_fuse_state = new_state
                    self.recovery_sequence = failed_resources
            
            return success_rate > 0.8  # 如果80%以上资源恢复成功，视为成功
            
        except Exception as e:
            logger.error(f"执行熔断恢复过程时发生错误: {e}\n{traceback.format_exc()}")
            with self.recovery_lock:
                self.recovery_ongoing = False
            return False
        finally:
            # 结束监控线程
            if self.recovery_monitor_thread and self.recovery_monitor_thread.is_alive():
                with self.recovery_lock:
                    self.recovery_ongoing = False
                self.recovery_monitor_thread.join(timeout=1.0)
    
    def _restore_resource(self, resource_id: str, resource_state: ResourceState) -> bool:
        """
        恢复单个资源
        
        Args:
            resource_id: 资源ID
            resource_state: 资源状态对象
            
        Returns:
            恢复是否成功
        """
        resource_type = resource_state.resource_type
        
        # 检查是否有注册的处理器
        if resource_type in self.resource_handlers:
            try:
                # 调用对应的恢复处理器
                handler = self.resource_handlers[resource_type]
                resource = handler(resource_state)
                
                # 获取执行器并重新注册资源
                executor = get_executor()
                
                # 为恢复的资源注册默认的释放函数
                def default_release(res):
                    logger.debug(f"释放资源 {resource_id}")
                    if hasattr(res, 'close'):
                        res.close()
                    elif hasattr(res, 'release'):
                        res.release()
                    elif hasattr(res, 'cleanup'):
                        res.cleanup()
                    # 对于纯Python对象，依赖GC回收
                
                # 重新注册到执行器
                executor.register_resource(resource_id, resource, default_release)
                return True
                
            except Exception as e:
                logger.error(f"恢复资源 {resource_id} 失败: {e}")
                return False
        else:
            logger.warning(f"未找到资源类型 {resource_type} 的恢复处理器")
            return False
    
    def monitor_recovery(self) -> None:
        """恢复过程监控，检查系统健康状态"""
        logger.debug("启动恢复监控线程")
        
        while self.recovery_ongoing:
            try:
                # 检查内存使用情况
                memory_usage = psutil.virtual_memory().percent
                
                if memory_usage > self.memory_threshold:
                    logger.warning(f"内存使用率过高 ({memory_usage}%)，暂停恢复过程")
                    self.recovery_pause_event.set()  # 暂停恢复
                    
                    # 尝试释放内存
                    force_gc()
                    
                    # 等待内存降至安全水平
                    while psutil.virtual_memory().percent > self.memory_threshold - 5:
                        time.sleep(1.0)
                    
                    logger.info(f"内存使用率已降至安全水平 ({psutil.virtual_memory().percent}%)，继续恢复")
                    self.recovery_pause_event.clear()  # 继续恢复
                
                # 检查间隔
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"监控恢复过程时发生错误: {e}")
                time.sleep(5.0)  # 出错后等待较长时间再继续
    
    def set_recovery_interval(self, interval_seconds: float) -> None:
        """设置资源恢复间隔"""
        self.recovery_interval = max(0.01, min(interval_seconds, 2.0))  # 限制在10ms-2s范围内
    
    def set_memory_threshold(self, percent: int) -> None:
        """设置内存阈值百分比"""
        self.memory_threshold = max(50, min(percent, 95))  # 限制在50%-95%范围内
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """获取恢复统计信息"""
        with self.recovery_lock:
            return {
                "total_resources": len(self.pre_fuse_state),
                "recovery_sequence": self.recovery_sequence.copy(),
                "recovery_ongoing": self.recovery_ongoing,
                "recovery_paused": self.recovery_pause_event.is_set(),
                "memory_threshold": self.memory_threshold,
                "recovery_interval": self.recovery_interval,
            }
    
    def reset(self) -> None:
        """完全重置恢复系统状态"""
        with self.recovery_lock:
            self.pre_fuse_state = {}
            self.recovery_sequence = []
            self.recovery_ongoing = False
            self.recovery_pause_event.clear()
            
        logger.info("熔断恢复系统已重置")


# 单例模式
_recovery_instance = None

def get_recovery_manager() -> FuseRecovery:
    """获取熔断恢复管理器单例"""
    global _recovery_instance
    if _recovery_instance is None:
        _recovery_instance = FuseRecovery()
    return _recovery_instance


# 便捷函数
def save_system_state() -> None:
    """保存当前系统状态，用于后续可能的恢复"""
    get_recovery_manager().save_state_snapshot()

def restore_system_state() -> bool:
    """从保存的状态恢复系统"""
    return get_recovery_manager().rollback()

def register_resource_state(resource_id: str, resource_type: str, metadata: Dict[str, Any] = None) -> None:
    """注册资源状态，用于可能的恢复"""
    if metadata is None:
        metadata = {}
    
    state = ResourceState(
        resource_id=resource_id,
        resource_type=resource_type,
        metadata=metadata
    )
    
    get_recovery_manager().register_pre_fuse_state(resource_id, state)

def register_recovery_handler(resource_type: str, handler_func: Callable) -> None:
    """注册资源类型的恢复处理函数"""
    get_recovery_manager().register_resource_handler(resource_type, handler_func) 