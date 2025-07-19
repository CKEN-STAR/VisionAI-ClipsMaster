#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
熔断事件溯源系统 (Fuse Event Tracer)
--------------------------------------
记录和分析熔断系统的各类事件，实现事件追踪和性能分析功能。

主要功能:
1. 事件记录 - 记录熔断操作、内存变化、资源状态等事件
2. 事件存储 - 支持多种存储后端(文件、内存、数据库、ElasticSearch等)
3. 事件分析 - 提供事件查询和数据分析功能
4. 性能监控 - 跟踪熔断操作的执行效率和内存恢复效果
5. 可视化支持 - 为熔断事件提供可视化数据

该系统与安全熔断执行器(safe_executor.py)、熔断状态恢复系统(recovery_manager.py)和
熔断效果验证系统(effect_validator.py)协同工作，完整记录熔断生命周期。
"""

import os
import time
import json
import logging
import threading
import datetime
import uuid
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
import traceback

# 配置日志
logger = logging.getLogger("event_tracer")

# 事件类型枚举
class EventType(Enum):
    """熔断事件类型枚举"""
    FUSE_TRIGGERED = "fuse_triggered"           # 熔断触发
    FUSE_COMPLETED = "fuse_completed"           # 熔断完成
    RESOURCE_RELEASED = "resource_released"     # 资源释放
    RECOVERY_STARTED = "recovery_started"       # 恢复开始
    RECOVERY_COMPLETED = "recovery_completed"   # 恢复完成
    VALIDATION_RESULT = "validation_result"     # 验证结果
    MEMORY_SNAPSHOT = "memory_snapshot"         # 内存快照
    GC_PERFORMED = "gc_performed"               # 执行GC
    ERROR_OCCURRED = "error_occurred"           # 发生错误
    SYSTEM_STATE_CHANGE = "system_state_change" # 系统状态变化
    CUSTOM_EVENT = "custom_event"               # 自定义事件


@dataclass
class FuseEvent:
    """熔断事件数据类"""
    event_id: str                               # 事件ID
    event_type: str                             # 事件类型
    timestamp: float                            # 时间戳
    memory_usage: Dict[str, Any]                # 内存使用情况
    details: Dict[str, Any]                     # 详细信息
    related_ids: List[str] = None               # 相关事件ID
    
    def __post_init__(self):
        """初始化后处理"""
        if self.related_ids is None:
            self.related_ids = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "datetime": datetime.datetime.fromtimestamp(self.timestamp).isoformat(),
            "memory_usage": self.memory_usage,
            "details": self.details,
            "related_ids": self.related_ids or []
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'FuseEvent':
        """从字典创建事件对象"""
        return FuseEvent(
            event_id=data.get("event_id", ""),
            event_type=data.get("event_type", ""),
            timestamp=data.get("timestamp", 0.0),
            memory_usage=data.get("memory_usage", {}),
            details=data.get("details", {}),
            related_ids=data.get("related_ids", [])
        )


class EventStorage:
    """事件存储接口基类"""
    
    def store_event(self, event: FuseEvent) -> bool:
        """存储事件，需要子类实现"""
        raise NotImplementedError
    
    def get_event(self, event_id: str) -> Optional[FuseEvent]:
        """获取指定ID的事件，需要子类实现"""
        raise NotImplementedError
    
    def query_events(self, filters: Dict[str, Any] = None, 
                    time_range: tuple = None, 
                    limit: int = 100) -> List[FuseEvent]:
        """
        查询事件
        
        Args:
            filters: 过滤条件
            time_range: 时间范围 (开始, 结束)
            limit: 最大返回数量
            
        Returns:
            List[FuseEvent]: 事件列表
        """
        raise NotImplementedError
    
    def close(self) -> None:
        """关闭存储连接"""
        pass


class MemoryEventStorage(EventStorage):

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存中的事件存储实现"""
    
    def __init__(self, max_events: int = 1000):
        """初始化内存存储"""
        self.events: Dict[str, FuseEvent] = {}
        self.events_by_type: Dict[str, List[str]] = {}
        self.max_events = max_events
        self.store_lock = threading.RLock()
    
    def store_event(self, event: FuseEvent) -> bool:
        """
        存储事件到内存
        
        Args:
            event: 要存储的事件
            
        Returns:
            bool: 是否成功存储
        """
        with self.store_lock:
            # 检查是否超过最大事件数量
            if len(self.events) >= self.max_events:
                # 删除最旧的事件
                oldest_id = min(
                    self.events.keys(), 
                    key=lambda k: self.events[k].timestamp
                )
                oldest_event = self.events.pop(oldest_id)
                
                # 从类型索引中移除
                event_type = oldest_event.event_type
                if event_type in self.events_by_type and oldest_id in self.events_by_type[event_type]:
                    self.events_by_type[event_type].remove(oldest_id)
            
            # 存储新事件
            self.events[event.event_id] = event
            
            # 更新类型索引
            event_type = event.event_type
            if event_type not in self.events_by_type:
                self.events_by_type[event_type] = []
            self.events_by_type[event_type].append(event.event_id)
            
            return True
    
    def get_event(self, event_id: str) -> Optional[FuseEvent]:
        """
        获取指定ID的事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            Optional[FuseEvent]: 找到的事件或None
        """
        return self.events.get(event_id)
    
    def query_events(self, filters: Dict[str, Any] = None, 
                    time_range: tuple = None, 
                    limit: int = 100) -> List[FuseEvent]:
        """
        查询事件
        
        Args:
            filters: 过滤条件
            time_range: 时间范围 (开始, 结束)
            limit: 最大返回数量
            
        Returns:
            List[FuseEvent]: 事件列表
        """
        with self.store_lock:
            # 根据类型筛选
            candidates = []
            
            if filters and 'event_type' in filters:
                event_type = filters['event_type']
                if event_type in self.events_by_type:
                    # 从类型索引获取ID
                    event_ids = self.events_by_type[event_type]
                    candidates = [self.events[eid] for eid in event_ids if eid in self.events]
            else:
                # 使用所有事件
                candidates = list(self.events.values())
            
            # 根据时间范围筛选
            if time_range:
                start_time, end_time = time_range
                candidates = [
                    e for e in candidates
                    if (start_time is None or e.timestamp >= start_time) and
                       (end_time is None or e.timestamp <= end_time)
                ]
            
            # 应用其他过滤条件
            if filters:
                for key, value in filters.items():
                    if key == 'event_type':
                        continue  # 已经处理过
                        
                    if key == 'details':
                        # 过滤详情字段中的值
                        if isinstance(value, dict):
                            for detail_key, detail_value in value.items():
                                candidates = [
                                    e for e in candidates
                                    if detail_key in e.details and e.details[detail_key] == detail_value
                                ]
                    else:
                        # 直接过滤其他字段
                        candidates = [
                            e for e in candidates
                            if hasattr(e, key) and getattr(e, key) == value
                        ]
            
            # 按时间戳排序并限制数量
            candidates.sort(key=lambda e: e.timestamp, reverse=True)
            return candidates[:limit]


class FileEventStorage(EventStorage):
    """基于文件的事件存储实现"""
    
    def __init__(self, file_path: str = "fuse_events.jsonl"):
        """
        初始化文件存储
        
        Args:
            file_path: 事件文件路径
        """
        self.file_path = file_path
        self.write_lock = threading.RLock()
        
        # 创建索引
        self.event_index: Dict[str, Dict[str, Any]] = {}
        self.type_index: Dict[str, List[str]] = {}
        self.time_index: List[tuple] = []  # [(timestamp, event_id), ...]
        
        # 加载现有事件
        self._load_existing_events()
    
    def _load_existing_events(self) -> None:
        """加载已有事件文件"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            event_data = json.loads(line)
                            event = FuseEvent.from_dict(event_data)
                            
                            # 更新索引
                            self._update_indexes(event)
                            
                        except Exception as e:
                            logger.error(f"解析事件行失败: {e}")
        except Exception as e:
            logger.error(f"加载现有事件文件失败: {e}")
    
    def _update_indexes(self, event: FuseEvent) -> None:
        """
        更新事件索引
        
        Args:
            event: 要索引的事件
        """
        # 事件ID索引
        self.event_index[event.event_id] = event.to_dict()
        
        # 类型索引
        if event.event_type not in self.type_index:
            self.type_index[event.event_type] = []
        self.type_index[event.event_type].append(event.event_id)
        
        # 时间索引
        self.time_index.append((event.timestamp, event.event_id))
        
        # 保持时间索引有序
        self.time_index.sort()
    
    def store_event(self, event: FuseEvent) -> bool:
        """
        存储事件到文件
        
        Args:
            event: 要存储的事件
            
        Returns:
            bool: 是否成功存储
        """
        with self.write_lock:
            try:
                # 转换为字典
                event_dict = event.to_dict()
                
                # 追加到文件
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event_dict) + "\n")
                
                # 更新索引
                self._update_indexes(event)
                
                return True
                
            except Exception as e:
                logger.error(f"存储事件到文件失败: {str(e)}")
                return False
    
    def get_event(self, event_id: str) -> Optional[FuseEvent]:
        """
        获取指定ID的事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            Optional[FuseEvent]: 找到的事件或None
        """
        event_data = self.event_index.get(event_id)
        if event_data:
            return FuseEvent.from_dict(event_data)
        return None
    
    def query_events(self, filters: Dict[str, Any] = None, 
                    time_range: tuple = None, 
                    limit: int = 100) -> List[FuseEvent]:
        """
        查询事件
        
        Args:
            filters: 过滤条件
            time_range: 时间范围 (开始, 结束)
            limit: 最大返回数量
            
        Returns:
            List[FuseEvent]: 事件列表
        """
        # 获取候选事件ID
        candidate_ids = set()
        
        # 如果指定了事件类型，使用类型索引
        if filters and 'event_type' in filters:
            event_type = filters['event_type']
            if event_type in self.type_index:
                candidate_ids.update(self.type_index[event_type])
        else:
            # 否则使用所有事件ID
            candidate_ids.update(self.event_index.keys())
        
        # 应用时间范围过滤
        if time_range:
            start_time, end_time = time_range
            
            # 过滤时间索引
            filtered_time_events = []
            for ts, event_id in self.time_index:
                if (start_time is None or ts >= start_time) and \
                   (end_time is None or ts <= end_time):
                    filtered_time_events.append(event_id)
            
            # 取交集
            if filtered_time_events:
                candidate_ids = candidate_ids.intersection(filtered_time_events)
        
        # 收集事件数据
        events = []
        for event_id in candidate_ids:
            event_data = self.event_index.get(event_id)
            if event_data:
                # 检查其他过滤条件
                include = True
                if filters:
                    for key, value in filters.items():
                        if key == 'event_type':
                            continue  # 已经处理过
                        
                        if key == 'details':
                            # 检查详情字段
                            if isinstance(value, dict):
                                for detail_key, detail_value in value.items():
                                    if 'details' not in event_data or \
                                       detail_key not in event_data['details'] or \
                                       event_data['details'][detail_key] != detail_value:
                                        include = False
                                        break
                        elif key in event_data:
                            # 直接检查其他字段
                            if event_data[key] != value:
                                include = False
                
                if include:
                    events.append(FuseEvent.from_dict(event_data))
        
        # 按时间排序
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # 返回限制数量
        return events[:limit]
    
    def close(self) -> None:
        """关闭存储"""
        pass  # 文件存储不需要特殊关闭


class FuseAudit:
    """熔断审计系统，记录和分析熔断事件"""
    
    def __init__(self, storage: Optional[EventStorage] = None):
        """
        初始化审计系统
        
        Args:
            storage: 事件存储后端，默认使用内存存储
        """
        # 如果未提供存储，使用内存存储
        self.storage = storage or MemoryEventStorage()
        
        # 事件关联映射，用于跟踪相关事件
        self.related_events: Dict[str, List[str]] = {}
        
        # 当前活动的事件跟踪
        self.active_events: Dict[str, str] = {}
        
        # 上下文锁
        self.context_lock = threading.RLock()
        
        # 初始化内存信息获取
        try:
            import psutil
            self._psutil_available = True
        except ImportError:
            self._psutil_available = False
            logger.warning("psutil未安装，内存信息将不可用")
        
        logger.info("熔断审计系统初始化完成")
    
    def log_fuse_event(self, event_type: Union[str, EventType], details: Dict[str, Any],
                      related_event_id: str = None) -> str:
        """
        记录熔断事件
        
        Args:
            event_type: 事件类型
            details: 事件详情
            related_event_id: 相关事件ID
            
        Returns:
            str: 事件ID
        """
        try:
            # 统一事件类型格式
            if isinstance(event_type, EventType):
                event_type = event_type.value
            
            # 生成事件ID
            event_id = str(uuid.uuid4())
            
            # 收集内存使用情况
            memory_usage = self._get_memory_usage()
            
            # 创建事件对象
            event = FuseEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=time.time(),
                memory_usage=memory_usage,
                details=details,
                related_ids=[related_event_id] if related_event_id else []
            )
            
            # 存储事件
            self.storage.store_event(event)
            
            # 更新关联关系
            if related_event_id:
                with self.context_lock:
                    if related_event_id not in self.related_events:
                        self.related_events[related_event_id] = []
                    self.related_events[related_event_id].append(event_id)
            
            # 日志记录
            logger.debug(f"记录熔断事件: {event_type}, ID: {event_id}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"记录熔断事件失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return ""
    
    def start_event_trace(self, trace_type: str, details: Dict[str, Any] = None) -> str:
        """
        开始事件追踪
        
        Args:
            trace_type: 追踪类型
            details: 详情
            
        Returns:
            str: 追踪ID
        """
        with self.context_lock:
            # 生成跟踪ID
            trace_id = str(uuid.uuid4())
            
            # 记录开始事件
            start_details = details or {}
            start_details.update({
                "trace_start": True,
                "trace_type": trace_type
            })
            
            # 记录事件
            event_id = self.log_fuse_event(
                f"{trace_type}_started",
                start_details
            )
            
            # 保存活动事件
            self.active_events[trace_type] = event_id
            
            return trace_id
    
    def end_event_trace(self, trace_type: str, details: Dict[str, Any] = None) -> str:
        """
        结束事件追踪
        
        Args:
            trace_type: 追踪类型
            details: 详情
            
        Returns:
            str: 结束事件ID
        """
        with self.context_lock:
            # 获取活动事件ID
            start_event_id = self.active_events.get(trace_type)
            
            # 记录结束事件
            end_details = details or {}
            end_details.update({
                "trace_end": True,
                "trace_type": trace_type
            })
            
            # 记录事件
            event_id = self.log_fuse_event(
                f"{trace_type}_completed",
                end_details,
                related_event_id=start_event_id
            )
            
            # 从活动事件中移除
            if trace_type in self.active_events:
                del self.active_events[trace_type]
            
            return event_id
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        获取事件详情
        
        Args:
            event_id: 事件ID
            
        Returns:
            Optional[Dict]: 事件详情或None
        """
        event = self.storage.get_event(event_id)
        if event:
            return event.to_dict()
        return None
    
    def query_events(self, event_type: str = None, time_range: tuple = None,
                    limit: int = 100, **filters) -> List[Dict[str, Any]]:
        """
        查询事件
        
        Args:
            event_type: 事件类型
            time_range: 时间范围 (开始, 结束)
            limit: 最大返回数量
            **filters: 其他过滤条件
            
        Returns:
            List[Dict]: 事件详情列表
        """
        # 构建查询过滤条件
        query_filters = {}
        if event_type:
            query_filters['event_type'] = event_type
        
        # 添加其他过滤条件
        query_filters.update(filters)
        
        # 执行查询
        events = self.storage.query_events(
            filters=query_filters,
            time_range=time_range,
            limit=limit
        )
        
        # 转换为字典
        return [event.to_dict() for event in events]
    
    def get_related_events(self, event_id: str) -> List[Dict[str, Any]]:
        """
        获取相关事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            List[Dict]: 相关事件列表
        """
        with self.context_lock:
            related_ids = self.related_events.get(event_id, [])
            
            # 获取所有相关事件
            events = []
            for rid in related_ids:
                event = self.storage.get_event(rid)
                if event:
                    events.append(event.to_dict())
            
            return events
    
    def send_to_elasticsearch(self, data: Dict[str, Any]) -> bool:
        """
        发送数据到Elasticsearch
        
        Args:
            data: 要发送的数据
            
        Returns:
            bool: 是否成功
        """
        try:
            # 这里添加实际的Elasticsearch发送逻辑
            # 简化示例，仅记录日志
            logger.info(f"将数据发送到Elasticsearch: {json.dumps(data, default=str)}")
            return True
        except Exception as e:
            logger.error(f"发送数据到Elasticsearch失败: {str(e)}")
            return False
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """
        获取内存使用情况
        
        Returns:
            Dict: 内存使用信息
        """
        memory_info = {}
        
        try:
            if self._psutil_available:
                import psutil
                
                # 获取进程信息
                process = psutil.Process(os.getpid())
                proc_info = process.memory_info()
                
                # 获取系统信息
                system_info = psutil.virtual_memory()
                
                # 组装内存信息
                memory_info = {
                    "process": {
                        "rss": proc_info.rss / (1024 * 1024),  # MB
                        "vms": proc_info.vms / (1024 * 1024),  # MB
                    },
                    "system": {
                        "total": system_info.total / (1024 * 1024),  # MB
                        "available": system_info.available / (1024 * 1024),  # MB
                        "used": system_info.used / (1024 * 1024),  # MB
                        "percent": system_info.percent
                    }
                }
            else:
                # 基本内存信息（通过Python的内置工具获取）
                import gc
                gc.collect()  # 执行GC以获得更准确的数据
                
                # 当前进程内存使用
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                memory_info = {
                    "process": {
                        "max_rss": usage.ru_maxrss / 1024  # MB
                    }
                }
                
        except Exception as e:
            logger.warning(f"获取内存使用信息失败: {str(e)}")
            memory_info = {"error": "无法获取内存信息"}
        
        return memory_info


# 单例模式
_audit_instance = None

def get_audit() -> FuseAudit:
    """获取审计系统单例"""
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = FuseAudit()
    return _audit_instance


def log_event(event_type: Union[str, EventType], details: Dict[str, Any] = None,
             related_event_id: str = None) -> str:
    """
    记录熔断事件（便捷函数）
    
    Args:
        event_type: 事件类型
        details: 事件详情
        related_event_id: 相关事件ID
        
    Returns:
        str: 事件ID
    """
    audit = get_audit()
    return audit.log_fuse_event(event_type, details or {}, related_event_id)


def start_trace(trace_type: str, details: Dict[str, Any] = None) -> str:
    """
    开始事件追踪（便捷函数）
    
    Args:
        trace_type: 追踪类型
        details: 详情
        
    Returns:
        str: 追踪ID
    """
    audit = get_audit()
    return audit.start_event_trace(trace_type, details)


def end_trace(trace_type: str, details: Dict[str, Any] = None) -> str:
    """
    结束事件追踪（便捷函数）
    
    Args:
        trace_type: 追踪类型
        details: 详情
        
    Returns:
        str: 结束事件ID
    """
    audit = get_audit()
    return audit.end_event_trace(trace_type, details)


# 事件分析器类
class FuseEventAnalyzer:
    """熔断事件分析器，用于分析熔断事件数据"""
    
    def __init__(self, audit: FuseAudit):
        """
        初始化分析器
        
        Args:
            audit: 审计系统实例
        """
        self.audit = audit
    
    def get_memory_trend(self, time_range: tuple = None, 
                        interval: int = 60) -> List[Dict[str, Any]]:
        """
        获取内存使用趋势
        
        Args:
            time_range: 时间范围 (开始, 结束)
            interval: 时间间隔(秒)
            
        Returns:
            List[Dict]: 内存使用趋势数据
        """
        # 查询内存快照事件
        memory_events = self.audit.query_events(
            event_type=EventType.MEMORY_SNAPSHOT.value,
            time_range=time_range
        )
        
        # 如果事件太少，查询所有事件并提取内存信息
        if len(memory_events) < 5:
            all_events = self.audit.query_events(time_range=time_range)
            
            # 按间隔分组
            now = time.time()
            if not time_range:
                # 默认查询最近24小时
                earliest_time = now - 86400
            else:
                earliest_time = time_range[0] if time_range[0] else now - 86400
            
            # 创建时间桶
            buckets = {}
            for event in all_events:
                ts = event['timestamp']
                bucket_key = int((ts - earliest_time) / interval) * interval + earliest_time
                
                if bucket_key not in buckets:
                    buckets[bucket_key] = []
                
                buckets[bucket_key].append(event)
            
            # 提取每个桶的内存信息
            trend_data = []
            for bucket_time, events in sorted(buckets.items()):
                if not events:
                    continue
                
                # 使用桶中第一个事件的内存信息
                mem_info = events[0].get('memory_usage', {})
                if mem_info:
                    trend_data.append({
                        'timestamp': bucket_time,
                        'datetime': datetime.datetime.fromtimestamp(bucket_time).isoformat(),
                        'memory': mem_info
                    })
            
            return trend_data
            
        else:
            # 直接使用内存快照事件
            trend_data = []
            for event in memory_events:
                trend_data.append({
                    'timestamp': event['timestamp'],
                    'datetime': event['datetime'],
                    'memory': event['memory_usage']
                })
            
            return sorted(trend_data, key=lambda x: x['timestamp'])
    
    def get_action_timing(self, action_type: str = None, 
                         time_range: tuple = None) -> List[Dict[str, Any]]:
        """
        获取操作执行时间统计
        
        Args:
            action_type: 操作类型
            time_range: 时间范围
            
        Returns:
            List[Dict]: 操作时间统计
        """
        # 查询操作开始和完成事件
        filters = {}
        if action_type:
            filters['details'] = {'action_type': action_type}
        
        # 获取所有操作事件
        started_events = self.audit.query_events(
            event_type=f"{action_type}_started" if action_type else None,
            time_range=time_range,
            **filters
        )
        
        completed_events = self.audit.query_events(
            event_type=f"{action_type}_completed" if action_type else None,
            time_range=time_range,
            **filters
        )
        
        # 匹配开始和完成事件
        timing_data = []
        for start_event in started_events:
            start_id = start_event['event_id']
            
            # 查找对应的完成事件
            for end_event in completed_events:
                if start_id in end_event.get('related_ids', []):
                    # 匹配成功，计算执行时间
                    execution_time = end_event['timestamp'] - start_event['timestamp']
                    
                    # 提取操作类型
                    action = action_type
                    if not action:
                        action = start_event['details'].get('action_type')
                        if not action:
                            action = start_event['event_type'].replace('_started', '')
                    
                    # 添加到结果
                    timing_data.append({
                        'action': action,
                        'start_time': start_event['timestamp'],
                        'end_time': end_event['timestamp'],
                        'execution_time': execution_time,
                        'start_event_id': start_id,
                        'end_event_id': end_event['event_id'],
                        'details': start_event['details']
                    })
                    
                    break
        
        return sorted(timing_data, key=lambda x: x['start_time'])
    
    def get_recovery_status(self, time_range: tuple = None) -> List[Dict[str, Any]]:
        """
        获取恢复状态统计
        
        Args:
            time_range: 时间范围
            
        Returns:
            List[Dict]: 恢复状态统计
        """
        # 查询恢复事件
        recovery_started = self.audit.query_events(
            event_type=EventType.RECOVERY_STARTED.value,
            time_range=time_range
        )
        
        recovery_completed = self.audit.query_events(
            event_type=EventType.RECOVERY_COMPLETED.value,
            time_range=time_range
        )
        
        # 匹配开始和完成事件
        recovery_data = []
        for start_event in recovery_started:
            start_id = start_event['event_id']
            
            # 尝试查找对应的完成事件
            completed = False
            recovery_time = None
            end_event = None
            
            for complete in recovery_completed:
                if start_id in complete.get('related_ids', []):
                    completed = True
                    recovery_time = complete['timestamp'] - start_event['timestamp']
                    end_event = complete
                    break
            
            # 统计恢复结果
            result = {
                'recovery_id': start_id,
                'start_time': start_event['timestamp'],
                'datetime': start_event['datetime'],
                'completed': completed,
                'details': start_event['details']
            }
            
            if completed and end_event:
                result.update({
                    'end_time': end_event['timestamp'],
                    'recovery_time': recovery_time,
                    'success': end_event['details'].get('success', False),
                    'memory_before': start_event['memory_usage'],
                    'memory_after': end_event['memory_usage']
                })
            
            recovery_data.append(result)
        
        return sorted(recovery_data, key=lambda x: x['start_time'], reverse=True)
    
    def get_fuse_efficiency(self, time_range: tuple = None) -> Dict[str, Any]:
        """
        获取熔断效率统计
        
        Args:
            time_range: 时间范围
            
        Returns:
            Dict: 熔断效率统计
        """
        # 查询熔断触发和完成事件
        triggered = self.audit.query_events(
            event_type=EventType.FUSE_TRIGGERED.value,
            time_range=time_range
        )
        
        completed = self.audit.query_events(
            event_type=EventType.FUSE_COMPLETED.value,
            time_range=time_range
        )
        
        # 统计数据
        fuse_count = len(triggered)
        complete_count = len(completed)
        
        # 匹配成功的熔断操作
        successful_fuses = []
        avg_response_time = 0
        
        for trigger in triggered:
            trigger_id = trigger['event_id']
            
            # 查找对应的完成事件
            for complete in completed:
                if trigger_id in complete.get('related_ids', []):
                    response_time = complete['timestamp'] - trigger['timestamp']
                    
                    successful_fuses.append({
                        'fuse_id': trigger_id,
                        'trigger_time': trigger['timestamp'],
                        'complete_time': complete['timestamp'],
                        'response_time': response_time,
                        'memory_before': trigger['memory_usage'],
                        'memory_after': complete['memory_usage'],
                        'memory_freed': self._calculate_memory_freed(
                            trigger['memory_usage'], 
                            complete['memory_usage']
                        ),
                        'actions': complete['details'].get('actions_taken', [])
                    })
                    
                    break
        
        # 计算平均响应时间
        if successful_fuses:
            avg_response_time = sum(f['response_time'] for f in successful_fuses) / len(successful_fuses)
        
        # 计算平均内存释放量
        avg_memory_freed = 0
        if successful_fuses:
            total_freed = sum(f['memory_freed'] for f in successful_fuses if f['memory_freed'] is not None)
            avg_memory_freed = total_freed / len(successful_fuses)
        
        # 统计结果
        return {
            'total_fuses': fuse_count,
            'completed_fuses': complete_count,
            'success_rate': (complete_count / fuse_count * 100) if fuse_count > 0 else 0,
            'avg_response_time': avg_response_time,
            'avg_memory_freed': avg_memory_freed,
            'successful_fuses': successful_fuses
        }
    
    def _calculate_memory_freed(self, before: Dict[str, Any], after: Dict[str, Any]) -> Optional[float]:
        """
        计算释放的内存量
        
        Args:
            before: 操作前内存状态
            after: 操作后内存状态
            
        Returns:
            Optional[float]: 释放的内存量(MB)或None
        """
        try:
            # 尝试计算进程RSS减少量
            if 'process' in before and 'process' in after:
                before_rss = before['process'].get('rss', 0)
                after_rss = after['process'].get('rss', 0)
                
                if before_rss > 0 and after_rss > 0:
                    return before_rss - after_rss
            
            # 如果进程数据不可用，尝试使用系统可用内存增加量
            if 'system' in before and 'system' in after:
                before_avail = before['system'].get('available', 0)
                after_avail = after['system'].get('available', 0)
                
                if before_avail > 0 and after_avail > 0:
                    return after_avail - before_avail
            
            return None
            
        except Exception:
            return None


# 获取分析器单例
_analyzer_instance = None

def get_analyzer() -> FuseEventAnalyzer:
    """获取事件分析器单例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = FuseEventAnalyzer(get_audit())
    return _analyzer_instance


# 主要事件类型的快捷函数
def log_fuse_triggered(details: Dict[str, Any]) -> str:
    """记录熔断触发事件"""
    return log_event(EventType.FUSE_TRIGGERED, details)

def log_fuse_completed(details: Dict[str, Any], trigger_id: str = None) -> str:
    """记录熔断完成事件"""
    return log_event(EventType.FUSE_COMPLETED, details, trigger_id)

def log_resource_released(resource_id: str, size_mb: float, details: Dict[str, Any] = None) -> str:
    """记录资源释放事件"""
    event_details = details or {}
    event_details.update({
        "resource_id": resource_id,
        "size_mb": size_mb
    })
    return log_event(EventType.RESOURCE_RELEASED, event_details)

def log_memory_snapshot(tag: str = None) -> str:
    """记录内存快照事件"""
    details = {"tag": tag} if tag else {}
    return log_event(EventType.MEMORY_SNAPSHOT, details)

def log_error(error_type: str, message: str, details: Dict[str, Any] = None) -> str:
    """记录错误事件"""
    error_details = details or {}
    error_details.update({
        "error_type": error_type,
        "message": message
    })
    return log_event(EventType.ERROR_OCCURRED, error_details)

def log_gc_performed(collected: int, duration: float) -> str:
    """记录GC执行事件"""
    return log_event(EventType.GC_PERFORMED, {
        "collected": collected,
        "duration": duration
    })

def log_system_state_change(old_state: str, new_state: str, details: Dict[str, Any] = None) -> str:
    """记录系统状态变更事件"""
    state_details = details or {}
    state_details.update({
        "old_state": old_state,
        "new_state": new_state
    })
    return log_event(EventType.SYSTEM_STATE_CHANGE, state_details)


# 用于集成的功能代码
def integrate_with_safe_executor():
    """集成到安全熔断执行器"""
    try:
        from .safe_executor import get_executor
        
        executor = get_executor()
        
        # 注册熔断操作回调
        def fuse_action_callback(action, args, result, success, duration):
            """熔断操作执行回调"""
            log_event("action_executed", {
                "action": action,
                "args": str(args),
                "success": success,
                "duration": duration,
                "result_type": str(type(result))
            })
        
        # 注册资源释放回调
        def resource_release_callback(resource_id, success, estimated_size_mb):
            """资源释放回调"""
            log_resource_released(
                resource_id=resource_id,
                size_mb=estimated_size_mb,
                details={"success": success}
            )
        
        # 注册回调函数
        if hasattr(executor, 'register_action_callback'):
            executor.register_action_callback(fuse_action_callback)
        
        if hasattr(executor, 'register_release_callback'):
            executor.register_release_callback(resource_release_callback)
            
        logger.info("已集成到安全熔断执行器")
        
    except ImportError:
        logger.warning("安全熔断执行器未导入，无法集成")

def integrate_with_recovery_manager():
    """集成到熔断状态恢复系统"""
    try:
        from .recovery_manager import get_recovery_manager
        
        recovery = get_recovery_manager()
        
        # 注册恢复开始回调
        def recovery_start_callback(state_id):
            """恢复开始回调"""
            return start_trace("recovery", {
                "state_id": state_id
            })
        
        # 注册恢复完成回调
        def recovery_complete_callback(state_id, success, resources):
            """恢复完成回调"""
            return end_trace("recovery", {
                "state_id": state_id,
                "success": success,
                "resource_count": len(resources) if resources else 0
            })
        
        # 注册资源恢复回调
        def resource_restore_callback(resource_id, resource_type, success):
            """资源恢复回调"""
            log_event("resource_restored", {
                "resource_id": resource_id,
                "resource_type": resource_type,
                "success": success
            })
        
        # 注册回调函数
        if hasattr(recovery, 'register_start_callback'):
            recovery.register_start_callback(recovery_start_callback)
        
        if hasattr(recovery, 'register_complete_callback'):
            recovery.register_complete_callback(recovery_complete_callback)
        
        if hasattr(recovery, 'register_resource_callback'):
            recovery.register_resource_callback(resource_restore_callback)
            
        logger.info("已集成到熔断状态恢复系统")
        
    except ImportError:
        logger.warning("熔断状态恢复系统未导入，无法集成")

def integrate_with_effect_validator():
    """集成到熔断效果验证系统"""
    try:
        from .effect_validator import get_validator
        
        validator = get_validator()
        
        # 注册验证结果回调
        def validation_result_callback(result):
            """验证结果回调"""
            log_event(EventType.VALIDATION_RESULT, {
                "action": result.action,
                "success": result.success,
                "memory_before": result.memory_before,
                "memory_after": result.memory_after,
                "reduction": result.reduction,
                "expected_reduction": result.expected_reduction,
                "execution_time": result.execution_time,
                "effectiveness": result.effectiveness
            })
        
        # 注册回调函数
        validator.register_result_callback(validation_result_callback)
            
        logger.info("已集成到熔断效果验证系统")
        
    except ImportError:
        logger.warning("熔断效果验证系统未导入，无法集成")


# 初始化事件追踪系统
def init_event_tracer():
    """初始化事件追踪系统并集成到其他组件"""
    try:
        # 创建事件追踪系统
        audit = get_audit()
        
        # 集成到其他组件
        integrate_with_safe_executor()
        integrate_with_recovery_manager()
        integrate_with_effect_validator()
        
        # 记录初始化事件
        log_event("system_initialized", {
            "component": "event_tracer",
            "version": "1.0.0"
        })
        
        logger.info("事件追踪系统已初始化")
        
        return audit
        
    except Exception as e:
        logger.error(f"初始化事件追踪系统失败: {str(e)}")
        logger.debug(traceback.format_exc())
        return None


# 如果直接运行此模块，执行示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化事件追踪系统
    audit = init_event_tracer()
    
    # 测试记录事件
    print("记录测试事件...")
    
    # 记录熔断触发
    trigger_id = log_fuse_triggered({
        "reason": "memory_pressure",
        "threshold": 90.0,
        "current": 92.5
    })
    
    # 记录资源释放
    log_resource_released("model_cache", 120.5, {
        "model_name": "text_generator",
        "release_type": "full"
    })
    
    # 记录GC执行
    log_gc_performed(1250, 0.35)
    
    # 记录熔断完成
    log_fuse_completed({
        "success": True,
        "actions_taken": ["clear_cache", "force_gc", "release_resources"],
        "total_freed_mb": 250.5
    }, trigger_id)
    
    # 获取事件
    print("\n获取熔断触发事件:")
    event = audit.get_event(trigger_id)
    print(json.dumps(event, indent=2))
    
    # 获取相关事件
    print("\n获取相关事件:")
    related = audit.get_related_events(trigger_id)
    print(f"找到 {len(related)} 个相关事件")
    
    # 测试事件分析
    analyzer = get_analyzer()
    
    # 获取熔断效率
    print("\n熔断效率统计:")
    efficiency = analyzer.get_fuse_efficiency()
    print(f"总熔断次数: {efficiency['total_fuses']}")
    print(f"成功率: {efficiency['success_rate']:.1f}%")
    print(f"平均响应时间: {efficiency['avg_response_time']:.3f}秒")
    print(f"平均内存释放: {efficiency['avg_memory_freed']:.1f}MB") 