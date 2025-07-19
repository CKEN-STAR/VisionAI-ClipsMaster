#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多线叙事协调器

此模块提供用于验证和协调多条并行叙事线的工具。主要功能包括：
1. 多线程叙事验证 - 确保多条故事线之间的时空逻辑一致性
2. 叙事线交叉点管理 - 处理多条叙事线之间的交叉和影响
3. 叙事辅助功能 - 生成多线叙事结构建议和可视化
4. 故事线冲突检测 - 识别多条叙事线之间的内容或逻辑冲突
5. 叙事完整性评估 - 评估多线叙事的整体连贯性和完整性

这些工具可帮助创作者构建复杂而连贯的多线故事，确保叙事在逻辑上的完整和协调。
"""

from typing import Dict, List, Set, Tuple, Any, Optional, Union, DefaultDict
from enum import Enum, auto
from collections import defaultdict, Counter
import logging
import json
import math
from dataclasses import dataclass, field
import networkx as nx
from datetime import datetime, timedelta
import re

# 尝试导入项目内部模块
try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
    from src.logic.spatiotemporal_checker import parse_time_ms, format_time_ms
except ImportError:
    logging.warning("无法导入完整的异常处理模块，将使用基础异常类")
    
    class ErrorCode:
        NARRATIVE_ERROR = 1600
    
    class ClipMasterError(Exception):
        def __init__(self, message, code=None, details=None):
            self.message = message
            self.code = code
            self.details = details or {}
            super().__init__(message)

    def parse_time_ms(time_str: str) -> int:
        """解析时间字符串为毫秒"""
        if isinstance(time_str, (int, float)):
            return int(time_str)
        
        # 处理格式如 "00:01:30.500" 的时间字符串
        pattern = r"(\d+):(\d+):(\d+)(?:\.(\d+))?"
        match = re.match(pattern, time_str)
        if match:
            hours, minutes, seconds, millis = match.groups()
            total_ms = int(hours) * 3600000 + int(minutes) * 60000 + int(seconds) * 1000
            if millis:
                total_ms += int(millis.ljust(3, '0')[:3])
            return total_ms
        
        return 0
    
    def format_time_ms(ms: int) -> str:
        """将毫秒转换为时间字符串"""
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        ms %= 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"

# 配置日志
logger = logging.getLogger(__name__)


class NarrativeRelationType(Enum):
    """叙事关系类型"""
    PARALLEL = auto()     # 并行关系：两个故事线同时发生
    SEQUENTIAL = auto()   # 顺序关系：一个故事线在另一个之后
    INTERLEAVED = auto()  # 交错关系：两个故事线交错发生
    EMBEDDED = auto()     # 嵌入关系：一个故事线嵌入另一个故事线内
    CONVERGENT = auto()   # 收敛关系：多个故事线汇聚到一个点
    DIVERGENT = auto()    # 发散关系：从一个点分出多个故事线


class ThreadRelationship(Enum):
    """故事线关系"""
    INDEPENDENT = auto()  # 独立关系：故事线之间没有直接关系
    CAUSAL = auto()       # 因果关系：一个故事线影响另一个故事线
    THEMATIC = auto()     # 主题关系：故事线共享主题元素
    ANTAGONISTIC = auto() # 对抗关系：故事线之间存在冲突
    SUPPORTIVE = auto()   # 支持关系：故事线相互支持或补充
    REFLECTIVE = auto()   # 反射关系：故事线相互映射或对比


class EventSyncType(Enum):
    """事件同步类型"""
    TIME_SYNC = auto()    # 时间同步：事件在时间上同步
    SPACE_SYNC = auto()   # 空间同步：事件在空间上同步
    CAUSAL_SYNC = auto()  # 因果同步：事件之间有因果关系
    THEME_SYNC = auto()   # 主题同步：事件在主题上同步
    CHARACTER_SYNC = auto() # 角色同步：事件共享角色
    NO_SYNC = auto()      # 无同步：事件之间没有同步关系


class ThreadConsistencyProblem(Enum):
    """线程一致性问题类型"""
    TIME_PARADOX = auto()        # 时间悖论：角色在同一时间出现在不同地点
    CHARACTER_INCONSISTENCY = auto() # 角色不一致：角色行为或状态矛盾
    PLOT_CONTRADICTION = auto()  # 情节矛盾：情节之间存在逻辑矛盾
    UNRESOLVED_CROSSOVER = auto() # 未解决的交叉：故事线交叉点没有适当处理
    THREAD_IMBALANCE = auto()    # 线程不平衡：故事线发展不均衡
    CONVERGENCE_FAILURE = auto() # 汇聚失败：故事线应该汇聚但未汇聚
    THREAD_ABANDONMENT = auto()  # 线程放弃：故事线开始但未完成


class NarrativeThreadError(ClipMasterError):
    """多线叙事错误异常
    
    当多线叙事中存在逻辑问题或结构问题时抛出。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化多线叙事错误异常
        
        Args:
            message: 错误信息
            details: 详细信息，包含错误的具体描述
        """
        super().__init__(
            message,
            code=ErrorCode.NARRATIVE_ERROR,
            details=details or {}
        )


@dataclass
class NarrativeEvent:
    """叙事事件
    
    表示叙事中的单个事件，可以属于一个或多个故事线。
    """
    id: str                                     # 事件ID
    thread_ids: Set[str] = field(default_factory=set)  # 所属故事线ID集合
    timestamp: int = 0                          # 事件时间戳（毫秒）
    duration: int = 0                           # 事件持续时间（毫秒）
    location: Optional[str] = None              # 事件发生位置
    characters: Set[str] = field(default_factory=set)  # 涉及角色集合
    description: str = ""                       # 事件描述
    type: str = "event"                         # 事件类型
    properties: Dict[str, Any] = field(default_factory=dict)  # 事件属性
    
    def overlaps_with(self, other: 'NarrativeEvent') -> bool:
        """检查两个事件在时间上是否重叠"""
        if self.timestamp == 0 or other.timestamp == 0:
            return False
        
        self_end = self.timestamp + self.duration
        other_end = other.timestamp + other.duration
        
        return (self.timestamp <= other.timestamp < self_end or
                other.timestamp <= self.timestamp < other_end)
    
    def has_character(self, character_id: str) -> bool:
        """检查事件是否涉及特定角色"""
        return character_id in self.characters
    
    def has_common_characters(self, other: 'NarrativeEvent') -> bool:
        """检查两个事件是否有共同角色"""
        return bool(self.characters.intersection(other.characters))
    
    def get_end_time(self) -> int:
        """获取事件结束时间"""
        return self.timestamp + self.duration
    
    def is_crossover_with(self, thread_id: str) -> bool:
        """检查事件是否是与指定故事线的交叉点"""
        return thread_id in self.thread_ids and len(self.thread_ids) > 1
    
    def __str__(self) -> str:
        """返回事件的字符串表示"""
        time_str = format_time_ms(self.timestamp)
        return f"Event({self.id}: {self.description} @ {time_str}, threads={len(self.thread_ids)})"


class NarrativeThread:
    """叙事线
    
    表示单一的故事情节线，包含一系列按时间顺序排列的事件。
    """
    
    def __init__(self, thread_id: str, name: str = "", description: str = ""):
        """初始化叙事线
        
        Args:
            thread_id: 故事线ID
            name: 故事线名称
            description: 故事线描述
        """
        self.id = thread_id
        self.name = name
        self.description = description
        self.events: List[str] = []  # 事件ID列表，按时间顺序
        self.characters: Set[str] = set()  # 涉及的角色集合
        self.properties: Dict[str, Any] = {}  # 故事线属性
        self.relations: Dict[str, ThreadRelationship] = {}  # 与其他故事线的关系
        self.metadata: Dict[str, Any] = {}  # 元数据
    
    def add_event(self, event_id: str) -> None:
        """添加事件到故事线
        
        Args:
            event_id: 事件ID
        """
        if event_id not in self.events:
            self.events.append(event_id)
    
    def add_character(self, character_id: str) -> None:
        """添加角色到故事线
        
        Args:
            character_id: 角色ID
        """
        self.characters.add(character_id)
    
    def set_relation(self, target_thread_id: str, relationship: ThreadRelationship) -> None:
        """设置与其他故事线的关系
        
        Args:
            target_thread_id: 目标故事线ID
            relationship: 关系类型
        """
        self.relations[target_thread_id] = relationship
    
    def get_relation(self, target_thread_id: str) -> ThreadRelationship:
        """获取与其他故事线的关系
        
        Args:
            target_thread_id: 目标故事线ID
            
        Returns:
            关系类型，默认为INDEPENDENT
        """
        return self.relations.get(target_thread_id, ThreadRelationship.INDEPENDENT)
    
    def get_event_count(self) -> int:
        """获取故事线包含的事件数量"""
        return len(self.events)
    
    def has_character(self, character_id: str) -> bool:
        """检查故事线是否包含特定角色"""
        return character_id in self.characters
    
    def has_common_characters(self, other: 'NarrativeThread') -> bool:
        """检查两个故事线是否有共同角色"""
        return bool(self.characters.intersection(other.characters))
    
    def __str__(self) -> str:
        """返回故事线的字符串表示"""
        return f"Thread({self.id}: {self.name}, events={len(self.events)})"


class NarrativeThreadIntegrator:
    """多线叙事协调器
    
    用于管理和协调多条叙事线，确保它们之间的时空逻辑一致性。
    """
    
    def __init__(self):
        """初始化多线叙事协调器"""
        self.threads: Dict[str, NarrativeThread] = {}  # 故事线 {thread_id: Thread}
        self.events: Dict[str, NarrativeEvent] = {}    # 事件 {event_id: Event}
        self.thread_relations: Dict[Tuple[str, str], NarrativeRelationType] = {}  # 故事线关系
        self.problems: List[Dict[str, Any]] = []       # 检测到的问题列表
        self.character_timeline: Dict[str, List[str]] = defaultdict(list)  # 角色时间线 {character_id: [event_id]}
        self.timeline: Dict[int, List[str]] = defaultdict(list)  # 全局时间线 {timestamp: [event_id]}
        self.crossover_points: List[str] = []          # 故事线交叉点事件ID列表
        
    def reset(self) -> None:
        """重置协调器状态"""
        self.threads.clear()
        self.events.clear()
        self.thread_relations.clear()
        self.problems.clear()
        self.character_timeline.clear()
        self.timeline.clear()
        self.crossover_points.clear()
        
    def add_thread(self, thread_id: str, name: str = "", description: str = "") -> NarrativeThread:
        """添加新的故事线
        
        Args:
            thread_id: 故事线ID
            name: 故事线名称
            description: 故事线描述
            
        Returns:
            创建的故事线对象
        """
        thread = NarrativeThread(thread_id, name, description)
        self.threads[thread_id] = thread
        return thread
    
    def add_event(self, event_data: Dict[str, Any]) -> NarrativeEvent:
        """添加事件
        
        Args:
            event_data: 事件数据
            
        Returns:
            创建的事件对象
            
        Raises:
            ValueError: 如果事件数据缺少必要字段
        """
        if "id" not in event_data:
            raise ValueError("事件数据缺少ID字段")
        
        event_id = event_data["id"]
        
        # 创建事件对象
        event = NarrativeEvent(
            id=event_id,
            thread_ids=set(event_data.get("thread_ids", [])),
            timestamp=parse_time_ms(event_data.get("timestamp", 0)),
            duration=parse_time_ms(event_data.get("duration", 0)),
            location=event_data.get("location"),
            characters=set(event_data.get("characters", [])),
            description=event_data.get("description", ""),
            type=event_data.get("type", "event"),
            properties=event_data.get("properties", {})
        )
        
        self.events[event_id] = event
        
        # 更新故事线
        for thread_id in event.thread_ids:
            if thread_id in self.threads:
                self.threads[thread_id].add_event(event_id)
                
                # 更新故事线的角色集合
                for character_id in event.characters:
                    self.threads[thread_id].add_character(character_id)
        
        # 更新角色时间线
        for character_id in event.characters:
            self.character_timeline[character_id].append(event_id)
            
        # 更新全局时间线
        if event.timestamp > 0:
            self.timeline[event.timestamp].append(event_id)
            
        # 检查是否为交叉点
        if len(event.thread_ids) > 1:
            self.crossover_points.append(event_id)
            
        return event
    
    def add_thread_relation(self, thread_id1: str, thread_id2: str, 
                          relation_type: NarrativeRelationType) -> bool:
        """添加故事线关系
        
        Args:
            thread_id1: 第一个故事线ID
            thread_id2: 第二个故事线ID
            relation_type: 关系类型
            
        Returns:
            是否成功添加关系
        """
        if thread_id1 not in self.threads or thread_id2 not in self.threads:
            return False
            
        # 确保关系键的一致性（总是将较小的ID放在前面）
        if thread_id1 > thread_id2:
            thread_id1, thread_id2 = thread_id2, thread_id1
            
        self.thread_relations[(thread_id1, thread_id2)] = relation_type
        return True
    
    def load_narrative_data(self, data: Dict[str, Any]) -> None:
        """从数据字典加载叙事数据
        
        Args:
            data: 包含线程和事件数据的字典
        """
        self.reset()
        
        # 加载故事线
        for thread_data in data.get("threads", []):
            thread_id = thread_data.get("id")
            if thread_id:
                self.add_thread(
                    thread_id,
                    thread_data.get("name", ""),
                    thread_data.get("description", "")
                )
                
                # 加载故事线属性
                if "properties" in thread_data and isinstance(thread_data["properties"], dict):
                    self.threads[thread_id].properties.update(thread_data["properties"])
                    
                # 加载故事线元数据
                if "metadata" in thread_data and isinstance(thread_data["metadata"], dict):
                    self.threads[thread_id].metadata.update(thread_data["metadata"])
        
        # 加载事件
        for event_data in data.get("events", []):
            if "id" in event_data:
                self.add_event(event_data)
                
        # 加载故事线关系
        for relation_data in data.get("relations", []):
            thread_id1 = relation_data.get("thread_id1")
            thread_id2 = relation_data.get("thread_id2")
            relation_type_str = relation_data.get("type", "PARALLEL")
            
            if thread_id1 and thread_id2:
                try:
                    relation_type = getattr(NarrativeRelationType, relation_type_str)
                    self.add_thread_relation(thread_id1, thread_id2, relation_type)
                except (AttributeError, TypeError):
                    logger.warning(f"无效的故事线关系类型: {relation_type_str}")
    
    def get_thread_relation(self, thread_id1: str, thread_id2: str) -> Optional[NarrativeRelationType]:
        """获取两个故事线之间的关系
        
        Args:
            thread_id1: 第一个故事线ID
            thread_id2: 第二个故事线ID
            
        Returns:
            关系类型，如果不存在则返回None
        """
        # 确保关系键的一致性
        if thread_id1 > thread_id2:
            thread_id1, thread_id2 = thread_id2, thread_id1
            
        return self.thread_relations.get((thread_id1, thread_id2))
    
    def check_thread_consistency(self, threads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证多线叙事的一致性
        
        检查当前所有故事线中的事件是否存在时空逻辑冲突。
        
        Args:
            threads: 故事线数据列表，每个故事线包含线程ID、名称和事件列表
            
        Returns:
            检测到的问题列表，每个问题包含类型、描述、相关故事线等信息
        """
        # 重置问题列表
        self.problems = []
        
        # 加载数据
        self.load_narrative_data({"threads": threads})
        
        # 检查时间悖论
        self._check_temporal_paradoxes()
        
        # 检查角色一致性
        self._check_character_consistency()
        
        # 检查情节矛盾
        self._check_plot_contradictions()
        
        # 检查未解决的交叉点
        self._check_unresolved_crossovers()
        
        # 检查故事线平衡性
        self._check_thread_balance()
        
        # 检查故事线放弃问题
        self._check_thread_abandonment()
        
        return self.problems
        
    def _check_temporal_paradoxes(self) -> None:
        """检查时间悖论
        
        识别同一角色在同一时间出现在不同地点的情况。
        """
        # 遍历每个角色
        for character_id, event_ids in self.character_timeline.items():
            # 按时间戳排序事件
            sorted_events = sorted(
                [self.events[event_id] for event_id in event_ids if event_id in self.events], 
                key=lambda e: e.timestamp
            )
            
            # 检查角色在同一时间点的位置冲突
            for i in range(len(sorted_events)):
                for j in range(i + 1, len(sorted_events)):
                    event1 = sorted_events[i]
                    event2 = sorted_events[j]
                    
                    # 检查事件是否时间重叠
                    if event1.overlaps_with(event2):
                        # 检查位置是否不同
                        if (event1.location and event2.location and 
                            event1.location != event2.location):
                            
                            # 记录问题
                            self._add_problem(
                                ThreadConsistencyProblem.TIME_PARADOX,
                                f"角色 {character_id} 同时出现在不同位置: {event1.location} 和 {event2.location}",
                                {
                                    "character_id": character_id,
                                    "event1_id": event1.id,
                                    "event2_id": event2.id,
                                    "time": format_time_ms(event1.timestamp),
                                    "location1": event1.location,
                                    "location2": event2.location,
                                    "thread_ids1": list(event1.thread_ids),
                                    "thread_ids2": list(event2.thread_ids)
                                }
                            )
    
    def _check_character_consistency(self) -> None:
        """检查角色行为和状态的一致性
        
        识别角色在不同故事线中的行为或状态矛盾。
        """
        # 遍历每个角色
        for character_id, event_ids in self.character_timeline.items():
            # 按时间戳排序事件
            sorted_events = sorted(
                [self.events[event_id] for event_id in event_ids if event_id in self.events], 
                key=lambda e: e.timestamp
            )
            
            # 跟踪角色状态
            character_state = {}
            
            for event in sorted_events:
                # 检查事件中的角色状态
                if "character_states" in event.properties:
                    char_states = event.properties["character_states"]
                    if isinstance(char_states, dict) and character_id in char_states:
                        new_state = char_states[character_id]
                        
                        # 检查状态变化是否合理
                        for state_key, state_value in new_state.items():
                            if state_key in character_state:
                                old_value = character_state[state_key]
                                
                                # 检查状态是否矛盾（例如，从"活着"变为"死亡"后又变回"活着"）
                                if self._is_state_contradiction(state_key, old_value, state_value):
                                    self._add_problem(
                                        ThreadConsistencyProblem.CHARACTER_INCONSISTENCY,
                                        f"角色 {character_id} 状态矛盾: {state_key} 从 {old_value} 变为 {state_value}",
                                        {
                                            "character_id": character_id,
                                            "event_id": event.id,
                                            "state_key": state_key,
                                            "old_value": old_value,
                                            "new_value": state_value,
                                            "thread_ids": list(event.thread_ids)
                                        }
                                    )
                            
                            # 更新状态
                            character_state[state_key] = state_value
    
    def _is_state_contradiction(self, state_key: str, old_value: Any, new_value: Any) -> bool:
        """检查状态变化是否矛盾
        
        Args:
            state_key: 状态键
            old_value: 旧状态值
            new_value: 新状态值
            
        Returns:
            是否矛盾
        """
        # 检查常见的矛盾状态
        if state_key == "alive" or state_key == "dead" or state_key == "存活":
            # 从死亡到活着是矛盾的（除非有复活情节）
            if (old_value is False and new_value is True) or (old_value == "dead" and new_value == "alive"):
                return True
                
        # 检查位置状态
        if state_key == "location" or state_key == "位置":
            # 忽略空值
            if old_value and new_value:
                # 检查位置变化是否不合理（应该由专门的时空检查来处理）
                pass
        
        # 其他状态矛盾检查可以根据具体需求添加
        return False
    
    def _check_plot_contradictions(self) -> None:
        """检查情节矛盾
        
        识别不同故事线之间的情节逻辑矛盾。
        """
        # 构建故事线事件分组
        thread_events = {}
        for thread_id, thread in self.threads.items():
            thread_events[thread_id] = [self.events[event_id] for event_id in thread.events if event_id in self.events]
        
        # 检查每对故事线之间的事件关系
        thread_ids = list(self.threads.keys())
        for i in range(len(thread_ids)):
            for j in range(i + 1, len(thread_ids)):
                thread_id1 = thread_ids[i]
                thread_id2 = thread_ids[j]
                
                # 获取故事线关系
                relation = self.get_thread_relation(thread_id1, thread_id2)
                
                # 如果是因果关系，检查是否有与因果链矛盾的事件
                if relation == NarrativeRelationType.CAUSAL:
                    events1 = thread_events[thread_id1]
                    events2 = thread_events[thread_id2]
                    
                    # 找到连接两个故事线的交叉点事件
                    crossover_events = []
                    for event in self.events.values():
                        if thread_id1 in event.thread_ids and thread_id2 in event.thread_ids:
                            crossover_events.append(event)
                    
                    if crossover_events:
                        # 检查因果逻辑是否正确
                        causal_errors = self._check_causal_logic(
                            events1, events2, crossover_events, thread_id1, thread_id2
                        )
                        
                        for error in causal_errors:
                            self._add_problem(
                                ThreadConsistencyProblem.PLOT_CONTRADICTION,
                                error["message"],
                                error["details"]
                            )
    
    def _check_causal_logic(self, events1: List[NarrativeEvent], events2: List[NarrativeEvent],
                          crossover_events: List[NarrativeEvent], thread_id1: str, thread_id2: str) -> List[Dict[str, Any]]:
        """检查两个故事线之间的因果逻辑
        
        Args:
            events1: 第一个故事线的事件列表
            events2: 第二个故事线的事件列表
            crossover_events: 交叉点事件列表
            thread_id1: 第一个故事线ID
            thread_id2: 第二个故事线ID
            
        Returns:
            错误列表
        """
        errors = []
        
        # 按时间排序事件
        events1.sort(key=lambda e: e.timestamp)
        events2.sort(key=lambda e: e.timestamp)
        crossover_events.sort(key=lambda e: e.timestamp)
        
        for crossover in crossover_events:
            # 检查交叉点事件的前后事件是否满足因果关系
            if "cause_event_id" in crossover.properties:
                cause_id = crossover.properties["cause_event_id"]
                if cause_id in self.events:
                    cause_event = self.events[cause_id]
                    
                    # 检查因果事件的时间顺序
                    if cause_event.timestamp > crossover.timestamp:
                        errors.append({
                            "message": f"因果逻辑错误: 结果事件 {crossover.id} 发生在原因事件 {cause_id} 之前",
                            "details": {
                                "cause_event_id": cause_id,
                                "effect_event_id": crossover.id,
                                "cause_time": format_time_ms(cause_event.timestamp),
                                "effect_time": format_time_ms(crossover.timestamp),
                                "thread_ids": [thread_id1, thread_id2]
                            }
                        })
        
        return errors
    
    def _check_unresolved_crossovers(self) -> None:
        """检查未解决的交叉点
        
        识别故事线交叉点未得到适当处理的情况。
        """
        for event_id in self.crossover_points:
            event = self.events[event_id]
            
            # 检查交叉点是否有明确的解决方案
            if "resolution" not in event.properties:
                involved_threads = list(event.thread_ids)
                
                # 检查是否是情节冲突事件
                is_conflict = event.properties.get("is_conflict", False)
                
                if is_conflict:
                    self._add_problem(
                        ThreadConsistencyProblem.UNRESOLVED_CROSSOVER,
                        f"未解决的故事线冲突交叉点: {event.description}",
                        {
                            "event_id": event.id,
                            "thread_ids": involved_threads,
                            "time": format_time_ms(event.timestamp),
                            "location": event.location,
                            "characters": list(event.characters)
                        }
                    )
    
    def _check_thread_balance(self) -> None:
        """检查故事线平衡性
        
        识别故事线发展不均衡的情况。
        """
        # 计算每个故事线的事件数量和时长
        thread_stats = {}
        for thread_id, thread in self.threads.items():
            if thread.events:
                events = [self.events[event_id] for event_id in thread.events]
                
                # 计算故事线时长
                events_with_time = [e for e in events if e.timestamp > 0]
                if events_with_time:
                    start_time = min(e.timestamp for e in events_with_time)
                    end_time = max(e.get_end_time() for e in events_with_time)
                    duration = end_time - start_time
                else:
                    duration = 0
                
                thread_stats[thread_id] = {
                    "event_count": len(thread.events),
                    "duration": duration,
                    "name": thread.name
                }
        
        # 计算平均事件数量和时长
        if thread_stats:
            avg_event_count = sum(stats["event_count"] for stats in thread_stats.values()) / len(thread_stats)
            durations = [stats["duration"] for stats in thread_stats.values() if stats["duration"] > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # 检查明显不平衡的故事线
            for thread_id, stats in thread_stats.items():
                # 事件数量过少
                if stats["event_count"] < avg_event_count * 0.5 and stats["event_count"] < 3:
                    self._add_problem(
                        ThreadConsistencyProblem.THREAD_IMBALANCE,
                        f"故事线 '{stats['name']}' 事件数量不足 (只有 {stats['event_count']} 个，平均为 {avg_event_count:.1f})",
                        {
                            "thread_id": thread_id,
                            "event_count": stats["event_count"],
                            "avg_event_count": avg_event_count,
                            "type": "event_count"
                        }
                    )
                
                # 时长过短
                if durations and stats["duration"] > 0 and stats["duration"] < avg_duration * 0.3:
                    self._add_problem(
                        ThreadConsistencyProblem.THREAD_IMBALANCE,
                        f"故事线 '{stats['name']}' 时长过短 (只有 {format_time_ms(stats['duration'])}，平均为 {format_time_ms(avg_duration)})",
                        {
                            "thread_id": thread_id,
                            "duration": stats["duration"],
                            "avg_duration": avg_duration,
                            "type": "duration"
                        }
                    )
    
    def _check_thread_abandonment(self) -> None:
        """检查故事线放弃问题
        
        识别开始但未完成的故事线。
        """
        for thread_id, thread in self.threads.items():
            if thread.events:
                events = [self.events[event_id] for event_id in thread.events]
                events.sort(key=lambda e: e.timestamp)
                
                # 获取故事线最后一个事件
                last_event = events[-1]
                
                # 检查故事线是否有明确的结束
                has_conclusion = False
                
                # 检查最后一个事件是否是结论类型
                if last_event.type in ["conclusion", "resolution", "ending", "结局", "结束"]:
                    has_conclusion = True
                
                # 检查故事线元数据中是否标记为已完成
                if thread.metadata.get("completed", False) or thread.metadata.get("concluded", False):
                    has_conclusion = True
                
                # 检查故事线属性中是否有结束标记
                if thread.properties.get("has_conclusion", False) or thread.properties.get("is_completed", False):
                    has_conclusion = True
                
                if not has_conclusion:
                    # 检查是否与其他故事线有收敛关系
                    is_converged = False
                    for (t1, t2), relation in self.thread_relations.items():
                        if relation == NarrativeRelationType.CONVERGENT:
                            if thread_id == t1 or thread_id == t2:
                                is_converged = True
                                break
                    
                    if not is_converged:
                        self._add_problem(
                            ThreadConsistencyProblem.THREAD_ABANDONMENT,
                            f"故事线 '{thread.name}' 可能未完成，缺少明确的结论",
                            {
                                "thread_id": thread_id,
                                "last_event_id": last_event.id,
                                "last_event_description": last_event.description,
                                "event_count": len(thread.events)
                            }
                        )
    
    def _add_problem(self, problem_type: ThreadConsistencyProblem, message: str, details: Dict[str, Any]) -> None:
        """添加问题到问题列表
        
        Args:
            problem_type: 问题类型
            message: 问题描述
            details: 问题详细信息
        """
        self.problems.append({
            "type": problem_type.name,
            "message": message,
            "details": details
        })
    
    def analyze_thread_structure(self) -> Dict[str, Any]:
        """分析故事线结构
        
        分析当前故事线的结构，包括故事线关系、交叉点等。
        
        Returns:
            分析结果，包含故事线结构图、关键交叉点、故事线特征等
        """
        # 创建图结构
        graph = nx.Graph()
        
        # 添加节点（故事线）
        for thread_id, thread in self.threads.items():
            graph.add_node(thread_id, name=thread.name, 
                        event_count=len(thread.events),
                        character_count=len(thread.characters))
            
        # 添加边（故事线关系）
        for (t1, t2), relation in self.thread_relations.items():
            graph.add_edge(t1, t2, relation=relation.name)
        
        # 分析故事线特征
        thread_features = {}
        for thread_id, thread in self.threads.items():
            events = [self.events[event_id] for event_id in thread.events if event_id in self.events]
            
            # 计算故事线时长
            events_with_time = [e for e in events if e.timestamp > 0]
            if events_with_time:
                start_time = min(e.timestamp for e in events_with_time)
                end_time = max(e.get_end_time() for e in events_with_time)
                duration = end_time - start_time
            else:
                duration = 0
                
            # 计算事件密度
            event_density = len(events) / (duration/60000) if duration > 0 else 0  # 每分钟事件数
            
            # 收集主要角色
            character_count = Counter()
            for event in events:
                for char in event.characters:
                    character_count[char] += 1
                    
            main_characters = [char for char, count in character_count.most_common(3)]
            
            # 收集故事线特征
            thread_features[thread_id] = {
                "name": thread.name,
                "event_count": len(events),
                "duration": duration,
                "event_density": event_density,
                "main_characters": main_characters,
                "crossover_count": sum(1 for e in events if len(e.thread_ids) > 1)
            }
        
        # 分析交叉点
        crossover_analysis = []
        for event_id in self.crossover_points:
            if event_id in self.events:
                event = self.events[event_id]
                involved_threads = list(event.thread_ids)
                
                # 检查交叉点类型
                crossover_type = "unknown"
                if event.type in ["convergence", "divergence", "meeting", "split"]:
                    crossover_type = event.type
                elif "crossover_type" in event.properties:
                    crossover_type = event.properties["crossover_type"]
                elif len(involved_threads) > 2:
                    crossover_type = "multi_thread"
                else:
                    crossover_type = "simple"
                
                crossover_analysis.append({
                    "event_id": event.id,
                    "description": event.description,
                    "involved_threads": involved_threads,
                    "type": crossover_type,
                    "timestamp": event.timestamp,
                    "characters": list(event.characters)
                })
        
        # 计算故事线中心性
        try:
            centrality = nx.betweenness_centrality(graph)
            central_threads = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            main_thread_id = central_threads[0][0] if central_threads else None
        except:
            centrality = {}
            central_threads = []
            main_thread_id = next(iter(self.threads.keys())) if self.threads else None
        
        return {
            "thread_count": len(self.threads),
            "event_count": len(self.events),
            "crossover_count": len(self.crossover_points),
            "thread_features": thread_features,
            "crossover_analysis": crossover_analysis,
            "main_thread": main_thread_id,
            "central_threads": central_threads,
            "thread_relations": [(t1, t2, rel.name) for (t1, t2), rel in self.thread_relations.items()]
        }
    
    def generate_thread_suggestions(self) -> Dict[str, List[str]]:
        """生成故事线改进建议
        
        基于当前故事线分析，生成改进建议。
        
        Returns:
            各类建议列表
        """
        suggestions = {
            "balancing": [],    # 平衡性建议
            "crossover": [],    # 交叉点建议
            "continuity": [],   # 连续性建议
            "structure": []     # 结构建议
        }
        
        # 获取问题和分析结果
        problems = self.problems
        analysis = self.analyze_thread_structure()
        
        # 根据问题生成建议
        for problem in problems:
            problem_type = problem.get("type")
            
            if problem_type == ThreadConsistencyProblem.THREAD_IMBALANCE.name:
                details = problem.get("details", {})
                thread_id = details.get("thread_id")
                
                if thread_id and thread_id in self.threads:
                    if details.get("type") == "event_count":
                        suggestions["balancing"].append(
                            f"为故事线 '{self.threads[thread_id].name}' 添加更多事件以平衡叙事"
                        )
                    elif details.get("type") == "duration":
                        suggestions["balancing"].append(
                            f"延长故事线 '{self.threads[thread_id].name}' 的时间跨度以平衡叙事"
                        )
            
            elif problem_type == ThreadConsistencyProblem.UNRESOLVED_CROSSOVER.name:
                details = problem.get("details", {})
                event_id = details.get("event_id")
                if event_id and event_id in self.events:
                    event = self.events[event_id]
                    suggestions["crossover"].append(
                        f"为交叉点 '{event.description}' 添加明确的解决方案"
                    )
            
            elif problem_type == ThreadConsistencyProblem.CHARACTER_INCONSISTENCY.name:
                details = problem.get("details", {})
                character_id = details.get("character_id")
                if character_id:
                    suggestions["continuity"].append(
                        f"解决角色 '{character_id}' 的状态一致性问题"
                    )
            
            elif problem_type == ThreadConsistencyProblem.THREAD_ABANDONMENT.name:
                details = problem.get("details", {})
                thread_id = details.get("thread_id")
                if thread_id and thread_id in self.threads:
                    suggestions["structure"].append(
                        f"为故事线 '{self.threads[thread_id].name}' 添加明确的结论"
                    )
        
        # 添加结构建议
        thread_features = analysis.get("thread_features", {})
        if thread_features:
            # 检查是否没有交叉点
            crossover_count = analysis.get("crossover_count", 0)
            if crossover_count == 0 and len(self.threads) > 1:
                suggestions["structure"].append(
                    "添加故事线之间的交叉点以增强叙事的连贯性"
                )
            
            # 检查是否过多交叉点
            elif crossover_count > len(self.threads) * 3:
                suggestions["structure"].append(
                    "减少故事线交叉点数量，保持故事线的独立性"
                )
            
            # 检查是否有无角色的故事线
            for thread_id, features in thread_features.items():
                if thread_id in self.threads and not self.threads[thread_id].characters:
                    suggestions["continuity"].append(
                        f"为故事线 '{self.threads[thread_id].name}' 添加角色"
                    )
        
        return suggestions
                    
    def generate_crossover_suggestions(self, thread_id1: str, thread_id2: str) -> List[Dict[str, Any]]:
        """生成两个故事线的交叉点建议
        
        基于两个故事线的特征，生成可能的交叉点建议。
        
        Args:
            thread_id1: 第一个故事线ID
            thread_id2: 第二个故事线ID
            
        Returns:
            交叉点建议列表
        """
        if (thread_id1 not in self.threads or 
            thread_id2 not in self.threads):
            return []
        
        suggestions = []
        thread1 = self.threads[thread_id1]
        thread2 = self.threads[thread_id2]
        
        # 检查是否有共同角色
        common_characters = thread1.characters.intersection(thread2.characters)
        
        if common_characters:
            # 基于共同角色的交叉点建议
            for char in common_characters:
                suggestions.append({
                    "type": "character_based",
                    "description": f"通过角色 '{char}' 创建故事线交叉",
                    "location": "共享位置",
                    "crossover_type": "meeting",
                    "characters": [char]
                })
        
        # 检查时间线重叠
        events1 = [self.events[event_id] for event_id in thread1.events if event_id in self.events]
        events2 = [self.events[event_id] for event_id in thread2.events if event_id in self.events]
        
        events_with_time1 = [e for e in events1 if e.timestamp > 0]
        events_with_time2 = [e for e in events2 if e.timestamp > 0]
        
        if events_with_time1 and events_with_time2:
            start_time1 = min(e.timestamp for e in events_with_time1)
            end_time1 = max(e.get_end_time() for e in events_with_time1)
            
            start_time2 = min(e.timestamp for e in events_with_time2)
            end_time2 = max(e.get_end_time() for e in events_with_time2)
            
            # 检查时间重叠
            if (start_time1 <= end_time2 and start_time2 <= end_time1):
                # 计算重叠的中点
                overlap_start = max(start_time1, start_time2)
                overlap_end = min(end_time1, end_time2)
                overlap_mid = (overlap_start + overlap_end) // 2
                
                suggestions.append({
                    "type": "time_based",
                    "description": "基于时间重叠创建故事线交叉",
                    "timestamp": overlap_mid,
                    "time_formatted": format_time_ms(overlap_mid),
                    "crossover_type": "temporal_convergence"
                })
        
        # 基于情节的建议
        suggestions.append({
            "type": "plot_based",
            "description": f"创建连接 '{thread1.name}' 和 '{thread2.name}' 的关键情节点",
            "crossover_type": "plot_connection",
            "relation_suggestion": "CAUSAL"
        })
        
        # 基于位置的建议
        locations1 = set(e.location for e in events1 if e.location)
        locations2 = set(e.location for e in events2 if e.location)
        common_locations = locations1.intersection(locations2)
        
        if common_locations:
            for location in common_locations:
                suggestions.append({
                    "type": "location_based",
                    "description": f"在共享位置 '{location}' 创建故事线交叉",
                    "location": location,
                    "crossover_type": "spatial_convergence"
                })
        
        return suggestions
    
    def check_thread_consistency_wrapper(self, threads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """故事线一致性检查封装函数
        
        Args:
            threads: 故事线数据列表
            
        Returns:
            包含问题、建议和分析的结果字典
        """
        # 检查故事线一致性
        problems = self.check_thread_consistency(threads)
        
        # 分析故事线结构
        analysis = self.analyze_thread_structure()
        
        # 生成改进建议
        suggestions = self.generate_thread_suggestions()
        
        return {
            "valid": len(problems) == 0,
            "problems": problems,
            "suggestions": suggestions,
            "analysis": analysis
        }

def validate_narrative_thread_consistency(threads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """验证多线叙事的一致性
    
    检查多个叙事线之间的逻辑一致性，识别潜在的时空悖论、角色状态矛盾等问题。
    
    Args:
        threads: 故事线数据列表
        
    Returns:
        验证结果，包含问题、建议和分析
        
    Raises:
        NarrativeThreadError: 如果验证失败且raise_exception为True
    """
    integrator = NarrativeThreadIntegrator()
    return integrator.check_thread_consistency_wrapper(threads) 