#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多线叙事协调器独立测试脚本

提供多线叙事协调器的独立测试功能，无需依赖完整项目。
"""

import sys
import os
import logging
from pathlib import Path
import json
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Any, Optional, Union
from collections import defaultdict, Counter
import math
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===========================================
# 简化的模型代码，独立运行
# ===========================================

# 尝试导入networkx
try:
    import networkx as nx
except ImportError:
    logger.warning("未安装networkx，某些功能将不可用")
    # 定义一个简化的图结构
    class SimpleGraph:
        def __init__(self):
            self.nodes = {}
            self.edges = {}
        
        def add_node(self, node, **attrs):
            self.nodes[node] = attrs
        
        def add_edge(self, u, v, **attrs):
            if (u, v) not in self.edges:
                self.edges[(u, v)] = attrs
    
    class nx:
        @staticmethod
        def Graph():
            return SimpleGraph()
        
        @staticmethod
        def betweenness_centrality(G):
            return {node: 1.0/len(G.nodes) for node in G.nodes}


# 基本异常类
class ErrorCode:
    NARRATIVE_ERROR = 1600

class ClipMasterError(Exception):
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


# 解析时间工具函数
def parse_time_ms(time_str: str) -> int:
    """解析时间字符串为毫秒"""
    if isinstance(time_str, (int, float)):
        return int(time_str)
    
    # 处理格式如 "00:01:30.500" 的时间字符串
    pattern = r"(\\\\\\1+):(\\\\\\1+):(\\\\\\1+)(?:\\\\\\1(\\\\\\1+))?"
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


# 枚举类型
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
    UNRESOLVED_CROSSOVER = auto() # 未解决的交叉点：故事线交叉点没有适当处理
    THREAD_IMBALANCE = auto()    # 线程不平衡：故事线发展不均衡
    CONVERGENCE_FAILURE = auto() # 汇聚失败：故事线应该汇聚但未汇聚
    THREAD_ABANDONMENT = auto()  # 线程放弃：故事线开始但未完成


class NarrativeThreadError(ClipMasterError):
    """多线叙事错误异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=ErrorCode.NARRATIVE_ERROR, details=details or {})


@dataclass
class NarrativeEvent:
    """叙事事件"""
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
        
        # 打印时间信息进行调试
        print(f"      事件 {self.id}: {format_time_ms(self.timestamp)} - {format_time_ms(self_end)}")
        print(f"      事件 {other.id}: {format_time_ms(other.timestamp)} - {format_time_ms(other_end)}")
        
        # 检查一个事件是否在另一个事件的时间范围内开始或结束
        # A在B开始之前结束，或B在A开始之前结束，则不重叠
        no_overlap = (self_end <= other.timestamp or other_end <= self.timestamp)
        return not no_overlap
    
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
    """叙事线"""
    def __init__(self, thread_id: str, name: str = "", description: str = ""):
        self.id = thread_id
        self.name = name
        self.description = description
        self.events: List[str] = []  # 事件ID列表，按时间顺序
        self.characters: Set[str] = set()  # 涉及的角色集合
        self.properties: Dict[str, Any] = {}  # 故事线属性
        self.relations: Dict[str, ThreadRelationship] = {}  # 与其他故事线的关系
        self.metadata: Dict[str, Any] = {}  # 元数据
    
    def add_event(self, event_id: str) -> None:
        """添加事件到故事线"""
        if event_id not in self.events:
            self.events.append(event_id)
    
    def add_character(self, character_id: str) -> None:
        """添加角色到故事线"""
        self.characters.add(character_id)
    
    def set_relation(self, target_thread_id: str, relationship: ThreadRelationship) -> None:
        """设置与其他故事线的关系"""
        self.relations[target_thread_id] = relationship
    
    def get_relation(self, target_thread_id: str) -> ThreadRelationship:
        """获取与其他故事线的关系"""
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
    """多线叙事协调器"""
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
        """添加新的故事线"""
        thread = NarrativeThread(thread_id, name, description)
        self.threads[thread_id] = thread
        return thread
    
    def add_event(self, event_data: Dict[str, Any]) -> NarrativeEvent:
        """添加事件"""
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
    
    def load_narrative_data(self, data: Dict[str, Any]) -> None:
        """从数据字典加载叙事数据"""
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
    
    def _check_temporal_paradoxes(self) -> None:
        """检查时间悖论"""
        print("开始检查时间悖论...")
        
        # 遍历每个角色
        for character_id, event_ids in self.character_timeline.items():
            print(f"检查角色 {character_id} 的事件...")
            
            # 按时间戳排序事件
            sorted_events = sorted(
                [self.events[event_id] for event_id in event_ids if event_id in self.events], 
                key=lambda e: e.timestamp
            )
            
            print(f"  角色 {character_id} 有 {len(sorted_events)} 个事件")
            
            # 检查角色在同一时间点的位置冲突
            for i in range(len(sorted_events)):
                for j in range(i + 1, len(sorted_events)):
                    event1 = sorted_events[i]
                    event2 = sorted_events[j]
                    
                    print(f"  比较事件 {event1.id} ({event1.location} @ {format_time_ms(event1.timestamp)}) 与 {event2.id} ({event2.location} @ {format_time_ms(event2.timestamp)})")
                    
                    # 检查事件是否时间重叠
                    overlaps = event1.overlaps_with(event2)
                    print(f"    时间重叠: {overlaps}")
                    
                    if overlaps:
                        # 检查位置是否不同
                        locations_different = (event1.location and event2.location and 
                                           event1.location != event2.location)
                        print(f"    位置不同: {locations_different}")
                        
                        if locations_different:
                            print(f"    检测到时间悖论: {character_id} 同时在 {event1.location} 和 {event2.location}")
                            
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
    
    def _add_problem(self, problem_type: ThreadConsistencyProblem, message: str, details: Dict[str, Any]) -> None:
        """添加问题到问题列表"""
        self.problems.append({
            "type": problem_type.name,
            "message": message,
            "details": details
        })
    
    def check_thread_consistency(self, threads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证多线叙事的一致性"""
        # 重置问题列表
        self.problems = []
        
        # 加载数据
        data = {"threads": threads}
        # 如果我们已经有事件，不要重新加载
        if hasattr(self, 'character_timeline') and self.character_timeline:
            print("使用现有的事件数据进行验证...")
        else:
            print("从头加载数据进行验证...")
            self.load_narrative_data(data)
        
        # 检查时间悖论
        self._check_temporal_paradoxes()
        
        # 在实际项目中这里会有更多检查:
        # self._check_character_consistency()
        # self._check_plot_contradictions()
        # self._check_unresolved_crossovers()
        # self._check_thread_balance()
        # self._check_thread_abandonment()
        
        return self.problems


def validate_narrative_thread_consistency(data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
    """验证多线叙事的一致性"""
    integrator = NarrativeThreadIntegrator()
    
    # 处理不同的输入格式
    if isinstance(data, list):
        # 如果是故事线列表，构造完整数据结构
        threads_data = {"threads": data}
        integrator.load_narrative_data(threads_data)
    else:
        # 如果是完整数据结构，直接加载
        integrator.load_narrative_data(data)
    
    problems = integrator.check_thread_consistency(integrator.threads.keys())
    
    return {
        "valid": len(problems) == 0,
        "problems": problems
    }


# ===========================================
# 测试数据和测试函数
# ===========================================

def create_test_data():
    """创建测试数据"""
    # 创建简单的测试故事线和事件
    threads = [
        {
            "id": "main",
            "name": "主线剧情",
            "description": "主要故事情节"
        },
        {
            "id": "side",
            "name": "支线剧情",
            "description": "次要故事情节"
        }
    ]
    
    events = [
        # 主线剧情事件
        {
            "id": "main_start",
            "thread_ids": ["main"],
            "timestamp": "00:01:00.000",
            "duration": "00:01:00.000",
            "location": "家",
            "characters": ["小明"],
            "description": "小明开始一天的生活",
            "type": "start"
        },
        {
            "id": "main_middle",
            "thread_ids": ["main"],
            "timestamp": "00:03:00.000",
            "duration": "00:02:00.000",
            "location": "办公室",
            "characters": ["小明"],
            "description": "小明在办公室工作",
            "type": "event"
        },
        
        # 支线剧情事件
        {
            "id": "side_start",
            "thread_ids": ["side"],
            "timestamp": "00:02:00.000",
            "duration": "00:01:00.000",
            "location": "学校",
            "characters": ["小红"],
            "description": "小红在学校上课",
            "type": "start"
        },
        
        # 故事线交叉点
        {
            "id": "crossover",
            "thread_ids": ["main", "side"],
            "timestamp": "00:06:00.000",
            "duration": "00:01:00.000",
            "location": "咖啡厅",
            "characters": ["小明", "小红"],
            "description": "小明和小红在咖啡厅相遇",
            "type": "crossover",
            "properties": {
                "is_conflict": False,
                "resolution": "友好交流"
            }
        },
        
        # 主线剧情结束
        {
            "id": "main_end",
            "thread_ids": ["main"],
            "timestamp": "00:08:00.000",
            "duration": "00:01:00.000",
            "location": "家",
            "characters": ["小明"],
            "description": "小明回到家",
            "type": "conclusion"
        }
    ]
    
    # 创建有问题的事件 - 时间悖论
    problem_events = events + [
        {
            "id": "paradox",
            "thread_ids": ["main"],
            "timestamp": "00:06:30.000",  # 与crossover事件时间重叠
            "duration": "00:00:30.000",
            "location": "公园",  # 与crossover事件位置不同
            "characters": ["小明"],  # 同一角色在同一时间出现在不同地点
            "description": "小明在公园散步",
            "type": "event"
        }
    ]
    
    return {
        "valid_data": {
            "threads": threads,
            "events": events
        },
        "problem_data": {
            "threads": threads,
            "events": problem_events
        }
    }


def test_thread_consistency():
    """测试故事线一致性"""
    print("\n===== 测试故事线一致性 =====")
    
    # 获取测试数据
    test_data = create_test_data()
    valid_data = test_data["valid_data"]
    problem_data = test_data["problem_data"]
    
    # 打印测试数据
    print("\n测试数据详情:")
    print(f"有效数据: {len(valid_data['threads'])} 个故事线, {len(valid_data['events'])} 个事件")
    print(f"问题数据: {len(problem_data['threads'])} 个故事线, {len(problem_data['events'])} 个事件")
    
    # 打印问题数据中的关键事件
    print("\n问题数据事件详情:")
    for event in problem_data["events"]:
        print(f"事件ID: {event['id']}")
        print(f"  时间: {event['timestamp']} - 持续: {event['duration']}")
        print(f"  位置: {event['location']}")
        print(f"  角色: {event['characters']}")
        print(f"  故事线: {event['thread_ids']}")
    
    # 测试有效数据
    integrator = NarrativeThreadIntegrator()
    integrator.load_narrative_data(valid_data)
    problems = integrator.check_thread_consistency(valid_data["threads"])
    
    print(f"\n有效数据检测到问题数量: {len(problems)}")
    if not problems:
        print("  ✓ 有效数据无问题")
    
    # 测试问题数据
    integrator.reset()
    print("\n加载问题数据...")
    integrator.load_narrative_data(problem_data)
    
    # 打印角色时间线
    print("\n角色时间线:")
    for character_id, event_ids in integrator.character_timeline.items():
        print(f"角色 {character_id}: {event_ids}")
    
    problems = integrator.check_thread_consistency(problem_data["threads"])
    
    print(f"\n问题数据检测到问题数量: {len(problems)}")
    if problems:
        print("  ✓ 成功检测到问题")
        for i, problem in enumerate(problems, 1):
            print(f"  问题 {i}: {problem['message']}")
            print(f"  类型: {problem['type']}")
            print(f"  详情: {json.dumps(problem['details'], ensure_ascii=False)}")
    
    # 测试便捷函数
    result = validate_narrative_thread_consistency(valid_data)
    print(f"\n便捷函数 - 有效数据: {'有效' if result['valid'] else '无效'}")
    
    result = validate_narrative_thread_consistency(problem_data)
    print(f"便捷函数 - 问题数据: {'有效' if result['valid'] else '无效'}")


def main():
    """主函数"""
    print("===== 多线叙事协调器独立测试 =====")
    
    try:
        # 测试故事线一致性
        test_thread_consistency()
        
        print("\n所有测试完成!")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 