#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
释放事件监听器

监听系统中的资源释放事件，计算释放性能指标，
并将这些信息传递给UI组件进行可视化。
"""

import time
import logging
import threading
import copy
from typing import Dict, List, Any, Optional, Callable, Tuple
from collections import deque
import weakref

# 导入相关模块
from src.memory.resource_tracker import get_resource_tracker
import src.memory.post_release_check as post_check

# 配置日志
logger = logging.getLogger("ReleaseEventListener")

class ResourceSnapshot:
    """资源状态快照，用于回滚操作"""
    
    def __init__(self, res_id: str, res_type: str, metadata: Dict[str, Any] = None):
        """
        初始化资源快照
        
        Args:
            res_id: 资源ID
            res_type: 资源类型
            metadata: 资源元数据
        """
        self.res_id = res_id
        self.res_type = res_type
        self.metadata = metadata or {}
        self.snapshot_time = time.time()
        self.resource_data = None  # 可能的资源数据备份
        
    def __str__(self) -> str:
        """字符串表示"""
        return f"ResourceSnapshot(id={self.res_id}, type={self.res_type}, time={self.snapshot_time})"

class ReleaseEvent:
    """资源释放事件记录"""
    
    def __init__(self, 
                 res_id: str, 
                 res_type: str, 
                 size_mb: float, 
                 start_time: float,
                 end_time: float):
        """
        初始化释放事件记录
        
        Args:
            res_id: 资源ID
            res_type: 资源类型
            size_mb: 资源大小(MB)
            start_time: 释放开始时间戳
            end_time: 释放结束时间戳
        """
        self.res_id = res_id
        self.res_type = res_type
        self.size_mb = size_mb
        self.start_time = start_time
        self.end_time = end_time
        self.time_cost_ms = (end_time - start_time) * 1000  # 转换为毫秒
        
        # 计算效率 (MB/ms)
        self.efficiency = size_mb / max(self.time_cost_ms, 0.1)  # 避免除零
        
        # 验证状态
        self.validated = False
        self.validation_result = None
        
        # 快照和回滚状态
        self.snapshot = None
        self.rolled_back = False
        
    def validate(self) -> bool:
        """验证资源是否正确释放"""
        try:
            self.validation_result = post_check.validate_release(self.res_id)
            self.validated = True
            return self.validation_result
        except Exception as e:
            logger.error(f"验证资源释放失败: {self.res_id} - {str(e)}")
            self.validated = True
            self.validation_result = False
            return False
            
    def __str__(self) -> str:
        """字符串表示"""
        return (f"ReleaseEvent(id={self.res_id}, type={self.res_type}, "
                f"size={self.size_mb:.1f}MB, time={self.time_cost_ms:.1f}ms, "
                f"efficiency={self.efficiency:.3f}MB/ms)")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "res_id": self.res_id,
            "res_type": self.res_type,
            "size_mb": self.size_mb,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "time_cost_ms": self.time_cost_ms,
            "efficiency": self.efficiency,
            "validated": self.validated,
            "validation_result": self.validation_result,
            "rolled_back": self.rolled_back
        }


class ReleaseEventListener:
    """释放事件监听器"""
    
    def __init__(self, max_history: int = 200):
        """
        初始化监听器
        
        Args:
            max_history: 最大历史记录数量
        """
        self.events = deque(maxlen=max_history)  # 事件历史
        self.release_callbacks = []  # UI回调函数列表
        self.resource_tracker = get_resource_tracker()  # 资源跟踪器
        
        # 统计数据
        self.stats = {
            "total_released_mb": 0.0,       # 总释放内存(MB)
            "total_release_count": 0,       # 总释放次数
            "max_efficiency": 0.0,          # 最大释放效率(MB/ms)
            "avg_efficiency": 0.0,          # 平均释放效率(MB/ms)
            "total_time_cost_ms": 0.0,      # 总耗时(ms)
            "type_stats": {},               # 按类型统计 {type: {count, size_mb}}
            "validation_success_rate": 1.0,  # 验证成功率
            "rollback_count": 0,            # 回滚次数
            "rollback_success_rate": 1.0    # 回滚成功率
        }
        
        # 监听标志
        self.is_listening = False
        self.listen_thread = None
        
        # 最后处理的释放操作ID
        self.last_release_id = 0
        
        # 资源快照字典
        self.resource_snapshots = {}
        
        # 回滚操作锁
        self.rollback_lock = threading.RLock()
        
        # 注册默认释放监听器
        # 钩子资源跟踪器的释放方法
        self._hook_resource_tracker()
    
    def _hook_resource_tracker(self):
        """钩子资源跟踪器的释放方法"""
        try:
            # 保存原始的release方法
            original_release = self.resource_tracker.release
            
            # 定义新的release方法
            def hooked_release(resource_id, force=False):
                # 获取资源信息
                resource_info = self.resource_tracker.get_resource_info(resource_id)
                if resource_info:
                    res_type = resource_info.get("res_type", "unknown")
                    size_mb = resource_info.get("size_estimate", 0)
                    
                    # 创建资源快照（在释放前）
                    self._create_resource_snapshot(resource_id, res_type, resource_info)
                    
                    # 记录开始时间
                    start_time = time.time()
                    
                    # 调用原始的release方法
                    result = original_release(resource_id, force)
                    
                    # 如果释放成功，创建事件并通知
                    if result:
                        end_time = time.time()
                        self.handle_release_event(
                            resource_id, 
                            res_type, 
                            size_mb, 
                            start_time, 
                            end_time
                        )
                        
                    return result
                else:
                    # 没有资源信息，直接调用原始方法
                    return original_release(resource_id, force)
            
            # 替换方法
            self.resource_tracker.release = hooked_release
            logger.info("已挂钩资源跟踪器的释放方法")
            
        except Exception as e:
            logger.error(f"挂钩资源跟踪器失败: {str(e)}")
    
    def _create_resource_snapshot(self, res_id: str, res_type: str, resource_info: Dict[str, Any]):
        """创建资源快照
        
        Args:
            res_id: 资源ID
            res_type: 资源类型
            resource_info: 资源信息
        """
        try:
            # 复制资源信息以创建快照
            metadata = copy.deepcopy(resource_info)
            
            # 创建快照对象
            snapshot = ResourceSnapshot(res_id, res_type, metadata)
            
            # 尝试获取资源对象本身（如果可能）
            if "obj_ref" in resource_info and resource_info["obj_ref"] is not None:
                obj = resource_info["obj_ref"]()
                if obj is not None:
                    # 对于某些类型的资源，尝试保存数据的浅拷贝
                    # 注意：这可能会消耗大量内存，因此需要谨慎使用
                    if res_type in ["temp_buffers", "file_cache"]:
                        try:
                            import numpy as np
                            if isinstance(obj, np.ndarray):
                                # 对于numpy数组，保存形状和数据类型
                                snapshot.resource_data = {
                                    "shape": obj.shape,
                                    "dtype": str(obj.dtype)
                                }
                            elif hasattr(obj, "__dict__"):
                                # 对于其他对象，保存属性字典
                                snapshot.resource_data = {
                                    "attributes": list(obj.__dict__.keys())
                                }
                        except Exception as e:
                            logger.debug(f"创建资源数据快照失败: {e}")
            
            # 保存快照
            self.resource_snapshots[res_id] = snapshot
            logger.debug(f"已创建资源快照: {res_id}")
            
        except Exception as e:
            logger.warning(f"创建资源快照失败: {res_id} - {e}")
    
    def handle_release_event(self, 
                            res_id: str, 
                            res_type: str, 
                            size_mb: float, 
                            start_time: float, 
                            end_time: float):
        """
        处理释放事件
        
        Args:
            res_id: 资源ID
            res_type: 资源类型
            size_mb: 资源大小(MB)
            start_time: 释放开始时间戳
            end_time: 释放结束时间戳
        """
        try:
            # 创建事件
            event = ReleaseEvent(res_id, res_type, size_mb, start_time, end_time)
            
            # 关联快照（如果存在）
            if res_id in self.resource_snapshots:
                event.snapshot = self.resource_snapshots[res_id]
            
            # 添加到历史记录
            self.events.append(event)
            
            # 更新统计数据
            self._update_stats(event)
            
            # 通知回调
            self._notify_callbacks(event)
            
            # 异步验证
            if threading.current_thread() is threading.main_thread():
                # 如果在主线程，创建新线程验证
                t = threading.Thread(target=self._validate_event, args=(event,))
                t.daemon = True
                t.start()
            else:
                # 如果已经在子线程，直接验证
                self._validate_event(event)
        
        except Exception as e:
            logger.error(f"处理释放事件出错: {str(e)}")
    
    def _validate_event(self, event: ReleaseEvent):
        """异步验证释放事件
        
        Args:
            event: 释放事件
        """
        try:
            # 稍微延迟，确保释放完成
            time.sleep(0.05)
            
            # 验证释放
            validation_result = event.validate()
            
            if not validation_result:
                logger.warning(f"资源释放验证失败: {event.res_id}")
                
                # 当验证失败时，尝试回滚操作
                if event.snapshot is not None:
                    self._rollback_release(event)
            
            # 更新验证统计
            self._update_validation_stats()
        
        except Exception as e:
            logger.error(f"验证释放事件出错: {str(e)}")
    
    def _rollback_release(self, event: ReleaseEvent):
        """回滚释放操作
        
        Args:
            event: 释放事件
        """
        with self.rollback_lock:
            try:
                logger.info(f"尝试回滚资源释放: {event.res_id}")
                
                # 获取资源快照
                snapshot = event.snapshot
                if not snapshot:
                    logger.warning(f"无法回滚: 找不到资源快照 - {event.res_id}")
                    return False
                
                # 尝试从快照恢复资源
                rollback_success = False
                
                try:
                    # 对于不同类型的资源，可能有不同的恢复策略
                    if event.res_type == "model_weights_cache":
                        # 对于模型权重缓存，通知模型加载器重新加载
                        from src.utils.model_cleanup import model_cleanup
                        if hasattr(model_cleanup, "_restore_model_weights"):
                            rollback_success = model_cleanup._restore_model_weights(
                                snapshot.metadata.get("model_name", "unknown")
                            )
                    
                    elif event.res_type == "temp_buffers":
                        # 对于临时缓冲区，尝试重新创建
                        # 这可能需要特定的工厂函数
                        pass
                    
                    elif event.res_type == "file_cache":
                        # 对于文件缓存，尝试从备份恢复
                        pass
                    
                    # 通用恢复策略
                    if not rollback_success:
                        # 尝试通过资源跟踪器重新注册
                        if hasattr(self.resource_tracker, "register_from_snapshot"):
                            rollback_success = self.resource_tracker.register_from_snapshot(snapshot)
                        else:
                            # 使用普通注册
                            res_id = self.resource_tracker.register(
                                event.res_type,
                                snapshot.res_id.split(":", 1)[1] if ":" in snapshot.res_id else "recovered",
                                metadata=snapshot.metadata
                            )
                            rollback_success = res_id is not None
                
                except Exception as e:
                    logger.error(f"执行资源回滚失败: {e}")
                    rollback_success = False
                
                # 更新事件状态
                event.rolled_back = rollback_success
                
                # 更新统计信息
                self.stats["rollback_count"] += 1
                if rollback_success:
                    logger.info(f"成功回滚资源: {event.res_id}")
                else:
                    logger.warning(f"回滚资源失败: {event.res_id}")
                
                # 计算成功率
                self._update_rollback_stats()
                
                # 通知UI
                if rollback_success:
                    self._notify_rollback(event)
                
                return rollback_success
                
            except Exception as e:
                logger.error(f"回滚资源时发生错误: {event.res_id} - {e}")
                return False
    
    def _update_rollback_stats(self):
        """更新回滚统计数据"""
        # 统计回滚过的事件
        rollback_events = [e for e in self.events if hasattr(e, "rolled_back") and e.rolled_back is not None]
        
        if rollback_events:
            # 计算回滚成功的比例
            success_count = sum(1 for e in rollback_events if e.rolled_back)
            if len(rollback_events) > 0:
                self.stats["rollback_success_rate"] = success_count / len(rollback_events)
    
    def _notify_rollback(self, event: ReleaseEvent):
        """通知UI回滚事件
        
        Args:
            event: 释放事件
        """
        # 向回调函数通知回滚事件
        for callback_ref in self.release_callbacks[:]:
            callback = callback_ref()
            if callback is not None and hasattr(callback, "notify_rollback"):
                try:
                    callback.notify_rollback(event.res_id, event.size_mb)
                except Exception as e:
                    logger.error(f"调用回滚通知回调出错: {str(e)}")
    
    def _update_stats(self, event: ReleaseEvent):
        """更新统计数据
        
        Args:
            event: 释放事件
        """
        # 更新总释放内存
        self.stats["total_released_mb"] += event.size_mb
        
        # 更新总释放次数
        self.stats["total_release_count"] += 1
        
        # 更新最大效率
        self.stats["max_efficiency"] = max(self.stats["max_efficiency"], event.efficiency)
        
        # 更新总耗时
        self.stats["total_time_cost_ms"] += event.time_cost_ms
        
        # 更新平均效率
        if self.stats["total_time_cost_ms"] > 0:
            self.stats["avg_efficiency"] = self.stats["total_released_mb"] / self.stats["total_time_cost_ms"]
        
        # 更新类型统计
        if event.res_type not in self.stats["type_stats"]:
            self.stats["type_stats"][event.res_type] = {"count": 0, "size_mb": 0.0}
            
        self.stats["type_stats"][event.res_type]["count"] += 1
        self.stats["type_stats"][event.res_type]["size_mb"] += event.size_mb
    
    def _update_validation_stats(self):
        """更新验证统计数据"""
        # 统计验证过的事件
        validated_events = [e for e in self.events if e.validated]
        
        if validated_events:
            # 计算验证成功的比例
            success_count = sum(1 for e in validated_events if e.validation_result)
            self.stats["validation_success_rate"] = success_count / len(validated_events)
    
    def _notify_callbacks(self, event: ReleaseEvent):
        """通知所有回调
        
        Args:
            event: 释放事件
        """
        # 如果有UI回调，通知它们
        for callback_ref in self.release_callbacks[:]:
            callback = callback_ref()
            if callback is not None:
                try:
                    callback(
                        event.res_id,
                        event.size_mb,
                        event.time_cost_ms
                    )
                except Exception as e:
                    logger.error(f"调用UI回调出错: {str(e)}")
            else:
                # 移除已失效的弱引用
                self.release_callbacks.remove(callback_ref)
    
    def register_callback(self, callback: Callable[[str, float, float], None]) -> None:
        """注册UI回调
        
        Args:
            callback: 回调函数，接收资源ID，释放的内存大小(MB)和释放耗时(ms)
        """
        # 使用弱引用，避免阻止UI组件垃圾回收
        self.release_callbacks.append(weakref.ref(callback))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据
        
        Returns:
            Dict: 统计数据字典
        """
        return self.stats.copy()
    
    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的释放事件
        
        Args:
            limit: 最大返回数量
            
        Returns:
            List[Dict]: 事件字典列表
        """
        events = list(self.events)[-limit:]
        return [e.to_dict() for e in events]
    
    def get_type_distribution(self) -> Dict[str, int]:
        """获取资源类型分布
        
        Returns:
            Dict: {资源类型: 数量} 字典
        """
        result = {}
        for res_type, data in self.stats["type_stats"].items():
            result[res_type] = data["count"]
        return result
    
    def start_polling(self, interval: float = 0.5):
        """启动轮询监听
        
        Args:
            interval: 轮询间隔(秒)
        """
        if self.is_listening:
            return
            
        self.is_listening = True
        
        def polling_thread():
            while self.is_listening:
                try:
                    # 获取资源跟踪器统计
                    tracker_stats = self.resource_tracker.get_stats()
                    
                    # 检查是否有新的释放操作
                    current_released = tracker_stats.get("released", 0)
                    
                    if current_released > self.last_release_id:
                        # 有新的释放操作，但我们没有收到事件
                        # 这可能是因为释放过程没有经过我们钩子的release方法
                        
                        # 估算释放的资源数量
                        released_count = current_released - self.last_release_id
                        
                        # 更新ID
                        self.last_release_id = current_released
                        
                        # 创建一个综合事件
                        # 假设平均每个资源50MB
                        size_mb = released_count * 50
                        
                        # 创建一个特殊的事件
                        self.handle_release_event(
                            "bulk:auto_detected",
                            "unknown",
                            size_mb,
                            time.time() - 0.1,  # 假设耗时100ms
                            time.time()
                        )
                    
                    # 间隔
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"轮询线程出错: {str(e)}")
                    time.sleep(interval)
        
        # 启动线程
        self.listen_thread = threading.Thread(target=polling_thread, daemon=True)
        self.listen_thread.start()
        
        logger.info("释放事件监听器已启动")
    
    def stop_polling(self):
        """停止轮询监听"""
        self.is_listening = False
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)
            
        logger.info("释放事件监听器已停止")
    
    def reset_stats(self):
        """重置统计数据"""
        self.events.clear()
        self.stats = {
            "total_released_mb": 0.0,
            "total_release_count": 0,
            "max_efficiency": 0.0,
            "avg_efficiency": 0.0,
            "total_time_cost_ms": 0.0,
            "type_stats": {},
            "validation_success_rate": 1.0,
            "rollback_count": 0,
            "rollback_success_rate": 1.0
        }
        
        # 清除资源快照
        self.resource_snapshots.clear()
        
        # 重置最后处理的ID
        self.last_release_id = self.resource_tracker.get_stats().get("released", 0)
        
        logger.info("释放统计数据已重置")


# 单例模式
_release_listener = None

def get_release_listener() -> ReleaseEventListener:
    """获取释放事件监听器单例
    
    Returns:
        ReleaseEventListener: 监听器实例
    """
    global _release_listener
    if _release_listener is None:
        _release_listener = ReleaseEventListener()
        # 自动启动轮询
        _release_listener.start_polling()
    return _release_listener


# 用于测试
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取监听器
    listener = get_release_listener()
    
    # 注册测试回调
    def test_callback(res_id, size_mb, time_cost):
        print(f"释放事件: {res_id}, 大小: {size_mb:.1f}MB, 耗时: {time_cost:.1f}ms")
    
    listener.register_callback(test_callback)
    
    # 获取资源跟踪器
    tracker = get_resource_tracker()
    
    # 创建一些测试资源
    print("创建测试资源...")
    import numpy as np
    
    for i in range(5):
        data = np.ones((100, 100, 100), dtype=np.float32)  # 约4MB
        tracker.register(
            "test_buffer", 
            f"test_{i}", 
            resource=data,
            metadata={"size_mb": 4}
        )
    
    # 等待一秒
    time.sleep(1)
    
    # 释放资源
    print("释放资源...")
    for i in range(5):
        tracker.release(f"test_buffer:test_{i}")
        time.sleep(0.2)
    
    # 打印统计
    print("\n统计数据:")
    stats = listener.get_stats()
    for key, value in stats.items():
        if key != "type_stats":
            print(f"  {key}: {value}")
    
    print("\n类型分布:")
    for res_type, data in stats["type_stats"].items():
        print(f"  {res_type}: {data['count']}次, {data['size_mb']:.1f}MB")
    
    # 停止监听
    listener.stop_polling() 