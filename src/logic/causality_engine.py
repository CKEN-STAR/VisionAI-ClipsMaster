#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
因果链验证引擎

此模块提供用于分析和验证视频剧情因果关系的工具。主要功能包括：
1. 因果链追踪 - 跟踪事件之间的因果关系
2. 悬念点检测 - 识别剧情中引入但未解决的问题或线索
3. 因果矛盾检测 - 发现剧情中的逻辑矛盾
4. 因果链补全建议 - 提供完善因果链的建议

使用这些工具可以避免混剪过程中造成的剧情逻辑混乱，提高视频的叙事连贯性。
"""

from typing import Dict, List, Set, Tuple, Any, Optional
import logging
from collections import defaultdict
from enum import Enum, auto

# 配置日志
logger = logging.getLogger(__name__)

# 定义因果关系类型
class CausalityType(Enum):
    """因果关系类型枚举"""
    DIRECT = auto()       # 直接因果：A直接导致B
    INDIRECT = auto()     # 间接因果：A通过中间事件导致B
    ENABLING = auto()     # 使能因果：A使B成为可能
    PREVENTIVE = auto()   # 阻止因果：A阻止B发生
    MOTIVATIONAL = auto() # 动机因果：A成为B的动机
    TEMPORAL = auto()     # 时序因果：A在时间上先于B


class EventNode:
    """
    事件节点
    
    表示因果网络中的一个事件节点，包含事件信息及其与其他事件的关系。
    """
    
    def __init__(self, event_id: str, event_data: Dict[str, Any]):
        """
        初始化事件节点
        
        Args:
            event_id: 事件ID
            event_data: 事件数据，包含事件类型、描述等信息
        """
        self.id = event_id
        self.data = event_data
        self.causes: Dict[str, CausalityType] = {}  # 指向原因事件的映射 {event_id: relation_type}
        self.effects: Dict[str, CausalityType] = {} # 指向结果事件的映射 {event_id: relation_type}
        self.resolved = False  # 标记事件是否已解决
        self.scene_index = event_data.get("scene_index", -1)  # 事件所在场景索引
        
    def add_cause(self, cause_id: str, relation_type: CausalityType = CausalityType.DIRECT) -> None:
        """添加一个原因事件"""
        self.causes[cause_id] = relation_type
    
    def add_effect(self, effect_id: str, relation_type: CausalityType = CausalityType.DIRECT) -> None:
        """添加一个结果事件"""
        self.effects[effect_id] = relation_type
    
    def has_causes(self) -> bool:
        """检查是否有原因事件"""
        return len(self.causes) > 0
    
    def has_effects(self) -> bool:
        """检查是否有结果事件"""
        return len(self.effects) > 0
    
    def is_problem(self) -> bool:
        """检查是否是问题事件（需要解决的）"""
        return self.data.get("type") == "problem"
    
    def is_clue(self) -> bool:
        """检查是否是线索事件（需要有后续）"""
        return self.data.get("type") == "clue"
    
    def is_resolution(self) -> bool:
        """检查是否是解决事件（用于解决问题）"""
        return self.data.get("type") == "resolution"
    
    def get_characters(self) -> List[str]:
        """获取与事件相关的角色"""
        return self.data.get("characters", [])
    
    def get_importance(self) -> float:
        """获取事件的重要性"""
        return float(self.data.get("importance", 0.5))
    
    def __str__(self) -> str:
        """返回事件节点的字符串表示"""
        return f"EventNode({self.id}: {self.data.get('description', '无描述')})"


class CausalityValidator:
    """
    因果一致性验证器
    
    分析和验证事件之间的因果关系，检测剧情中的逻辑问题。
    """
    
    def __init__(self):
        """初始化因果一致性验证器"""
        self.events: Dict[str, EventNode] = {}  # 所有事件节点 {event_id: EventNode}
        self.unresolved_problems: List[str] = []  # 未解决的问题事件ID列表
        self.dangling_clues: List[str] = []  # 悬而未决的线索事件ID列表
        self.causality_breaks: List[Dict[str, Any]] = []  # 因果断裂问题列表
        self.event_order: List[str] = []  # 事件的顺序列表
    
    def reset(self) -> None:
        """重置验证器状态"""
        self.events.clear()
        self.unresolved_problems.clear()
        self.dangling_clues.clear()
        self.causality_breaks.clear()
        self.event_order.clear()
    
    def add_event(self, event_id: str, event_data: Dict[str, Any]) -> EventNode:
        """
        添加事件
        
        Args:
            event_id: 事件ID
            event_data: 事件数据
            
        Returns:
            创建的事件节点
        """
        node = EventNode(event_id, event_data)
        self.events[event_id] = node
        self.event_order.append(event_id)
        return node
    
    def add_causal_link(self, cause_id: str, effect_id: str, 
                      relation_type: CausalityType = CausalityType.DIRECT) -> bool:
        """
        添加因果关系链接
        
        Args:
            cause_id: 原因事件ID
            effect_id: 结果事件ID
            relation_type: 关系类型
            
        Returns:
            添加是否成功
        """
        if cause_id not in self.events or effect_id not in self.events:
            return False
        
        # 更新原因事件
        self.events[cause_id].add_effect(effect_id, relation_type)
        
        # 更新结果事件
        self.events[effect_id].add_cause(cause_id, relation_type)
        
        return True
    
    def check_causal_links(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证事件集合中的因果关系
        
        分析事件列表，构建因果网络，并检测可能的因果问题。
        
        Args:
            events: 事件列表，每个事件包含ID、类型、描述等信息
            
        Returns:
            问题列表，包含未解决的问题、悬而未决的线索等
        """
        # 重置状态
        self.reset()
        
        # 第一步：创建所有事件节点
        for i, event in enumerate(events):
            event_id = event.get("id", f"event_{i}")
            # 添加场景索引以便追踪事件发生顺序
            event["scene_index"] = i
            self.add_event(event_id, event)
        
        # 第二步：建立因果关系
        for event in events:
            event_id = event.get("id")
            
            # 检查原因关系
            if "causes" in event:
                for cause_info in event["causes"]:
                    cause_id = cause_info.get("id")
                    relation_type_str = cause_info.get("relation", "DIRECT")
                    relation_type = getattr(CausalityType, relation_type_str, CausalityType.DIRECT)
                    self.add_causal_link(cause_id, event_id, relation_type)
            
            # 检查结果关系
            if "effects" in event:
                for effect_info in event["effects"]:
                    effect_id = effect_info.get("id")
                    relation_type_str = effect_info.get("relation", "DIRECT")
                    relation_type = getattr(CausalityType, relation_type_str, CausalityType.DIRECT)
                    self.add_causal_link(event_id, effect_id, relation_type)
        
        # 第三步：检测问题和线索是否已解决
        for event_id, node in self.events.items():
            # 检查问题是否有解决方案
            if node.is_problem() and "resolution" not in node.data:
                # 问题没有直接标记为已解决，检查是否有解决事件链接
                resolution_found = False
                for effect_id in node.effects:
                    if self.events[effect_id].is_resolution():
                        resolution_found = True
                        break
                
                if not resolution_found:
                    self.unresolved_problems.append(event_id)
            
            # 检查线索是否有后续发展
            if node.is_clue() and not node.has_effects():
                self.dangling_clues.append(event_id)
            
            # 检查事件前后顺序的逻辑性
            if node.has_causes():
                for cause_id in node.causes:
                    cause_node = self.events[cause_id]
                    # 如果原因事件的场景索引大于结果事件，则可能存在时序问题
                    if cause_node.scene_index > node.scene_index:
                        self.causality_breaks.append({
                            "type": "temporal_paradox",
                            "cause_id": cause_id,
                            "effect_id": event_id,
                            "message": f"时序悖论: 结果事件 '{node.data.get('description')}' 出现在原因事件 '{cause_node.data.get('description')}' 之前"
                        })
        
        # 第四步：整理问题清单
        issues = []
        
        # 处理未解决的问题
        for problem_id in self.unresolved_problems:
            problem_node = self.events[problem_id]
            issues.append({
                "type": "unresolved_problem",
                "event_id": problem_id,
                "description": problem_node.data.get("description", "无描述"),
                "scene_index": problem_node.scene_index,
                "message": f"未解决的问题: '{problem_node.data.get('description')}'"
            })
        
        # 处理悬而未决的线索
        for clue_id in self.dangling_clues:
            clue_node = self.events[clue_id]
            issues.append({
                "type": "dangling_clue",
                "event_id": clue_id,
                "description": clue_node.data.get("description", "无描述"),
                "scene_index": clue_node.scene_index,
                "message": f"悬而未决的线索: '{clue_node.data.get('description')}'"
            })
        
        # 处理因果断裂
        for break_info in self.causality_breaks:
            issues.append(break_info)
        
        # 检查孤立事件（既没有原因也没有结果的重要事件）
        for event_id, node in self.events.items():
            if not node.is_clue() and not node.is_problem() and not node.is_resolution():
                if not node.has_causes() and not node.has_effects() and node.get_importance() > 0.7:
                    issues.append({
                        "type": "isolated_event",
                        "event_id": event_id,
                        "description": node.data.get("description", "无描述"),
                        "scene_index": node.scene_index,
                        "message": f"孤立事件: 重要事件 '{node.data.get('description')}' 没有与其他事件的因果联系"
                    })
        
        return issues
    
    def suggest_causal_fixes(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        为因果问题提供修复建议
        
        Args:
            issues: 问题列表
            
        Returns:
            按问题类型分组的修复建议
        """
        suggestions = defaultdict(list)
        
        for issue in issues:
            issue_type = issue["type"]
            event_id = issue.get("event_id")
            
            if issue_type == "unresolved_problem":
                # 为未解决的问题提供建议
                problem_node = self.events[event_id]
                
                # 寻找可能的解决方案
                potential_resolutions = []
                for other_id, other_node in self.events.items():
                    if other_id != event_id and other_node.is_resolution():
                        # 检查是否有角色重叠
                        problem_chars = set(problem_node.get_characters())
                        resolution_chars = set(other_node.get_characters())
                        if problem_chars.intersection(resolution_chars):
                            potential_resolutions.append(other_id)
                
                if potential_resolutions:
                    for res_id in potential_resolutions:
                        suggestions["unresolved_problem"].append({
                            "issue_id": event_id,
                            "suggestion_type": "link_to_resolution",
                            "target_id": res_id,
                            "message": f"建议将问题 '{problem_node.data.get('description')}' 与解决事件 '{self.events[res_id].data.get('description')}' 链接"
                        })
                else:
                    suggestions["unresolved_problem"].append({
                        "issue_id": event_id,
                        "suggestion_type": "add_resolution",
                        "message": f"建议为问题 '{problem_node.data.get('description')}' 添加解决事件"
                    })
            
            elif issue_type == "dangling_clue":
                # 为悬而未决的线索提供建议
                clue_node = self.events[event_id]
                
                # 寻找可能的后续发展
                potential_followups = []
                for other_id, other_node in self.events.items():
                    if other_id != event_id and other_node.scene_index > clue_node.scene_index:
                        # 检查是否有角色或主题重叠
                        clue_chars = set(clue_node.get_characters())
                        other_chars = set(other_node.get_characters())
                        if clue_chars.intersection(other_chars) or self._has_theme_overlap(clue_node, other_node):
                            potential_followups.append(other_id)
                
                if potential_followups:
                    for followup_id in potential_followups[:3]:  # 最多提供3个建议
                        suggestions["dangling_clue"].append({
                            "issue_id": event_id,
                            "suggestion_type": "link_to_event",
                            "target_id": followup_id,
                            "message": f"建议将线索 '{clue_node.data.get('description')}' 与后续事件 '{self.events[followup_id].data.get('description')}' 链接"
                        })
                else:
                    suggestions["dangling_clue"].append({
                        "issue_id": event_id,
                        "suggestion_type": "add_followup",
                        "message": f"建议为线索 '{clue_node.data.get('description')}' 添加后续发展"
                    })
            
            elif issue_type == "temporal_paradox":
                # 为时序悖论提供建议
                cause_id = issue["cause_id"]
                effect_id = issue["effect_id"]
                cause_node = self.events[cause_id]
                effect_node = self.events[effect_id]
                
                suggestions["temporal_paradox"].append({
                    "issue_id": f"{cause_id}->{effect_id}",
                    "suggestion_type": "reorder_scenes",
                    "message": f"建议调整场景顺序，将原因事件 '{cause_node.data.get('description')}' 放在结果事件 '{effect_node.data.get('description')}' 之前"
                })
            
            elif issue_type == "isolated_event":
                # 为孤立事件提供建议
                isolated_node = self.events[event_id]
                
                # 寻找可能的因果关联
                potential_causes = []
                potential_effects = []
                
                for other_id, other_node in self.events.items():
                    if other_id != event_id:
                        if other_node.scene_index < isolated_node.scene_index:
                            potential_causes.append(other_id)
                        elif other_node.scene_index > isolated_node.scene_index:
                            potential_effects.append(other_id)
                
                if potential_causes:
                    cause_id = potential_causes[0]  # 选择最接近的一个
                    suggestions["isolated_event"].append({
                        "issue_id": event_id,
                        "suggestion_type": "link_as_effect",
                        "target_id": cause_id,
                        "message": f"建议将事件 '{isolated_node.data.get('description')}' 作为事件 '{self.events[cause_id].data.get('description')}' 的结果"
                    })
                
                if potential_effects:
                    effect_id = potential_effects[0]  # 选择最接近的一个
                    suggestions["isolated_event"].append({
                        "issue_id": event_id,
                        "suggestion_type": "link_as_cause",
                        "target_id": effect_id,
                        "message": f"建议将事件 '{isolated_node.data.get('description')}' 作为事件 '{self.events[effect_id].data.get('description')}' 的原因"
                    })
        
        return dict(suggestions)
    
    def _has_theme_overlap(self, node1: EventNode, node2: EventNode) -> bool:
        """检查两个事件节点是否有主题重叠"""
        # 从事件描述中提取关键词
        keywords1 = set(self._extract_keywords(node1.data.get("description", "")))
        keywords2 = set(self._extract_keywords(node2.data.get("description", "")))
        
        # 检查是否有关键词重叠
        return len(keywords1.intersection(keywords2)) > 0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词（简化版）"""
        # 这是一个简化的实现，实际应用中可能需要更复杂的NLP方法
        # 移除常见标点符号并分词
        words = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text).split()
        
        # 过滤掉常见停用词和短词
        stopwords = {"的", "了", "和", "是", "在", "有", "就", "不", "人", "我", "他", "你", "她", "们", "这", "那", "其", "与"}
        keywords = [word for word in words if len(word) > 1 and word not in stopwords]
        
        return keywords
    
    def get_event_chains(self) -> List[List[str]]:
        """
        获取事件因果链
        
        将事件组织成连续的因果链。
        
        Returns:
            事件链列表，每个链是一系列有因果关联的事件ID
        """
        # 找出所有起始事件（没有原因的事件）
        root_events = [event_id for event_id, node in self.events.items() if not node.has_causes()]
        
        chains = []
        visited = set()
        
        # 从每个起始事件开始，沿着结果链构建事件链
        for root_id in root_events:
            if root_id in visited:
                continue
                
            chain = []
            self._build_chain(root_id, chain, visited)
            
            if chain:
                chains.append(chain)
        
        # 处理环形因果链
        remaining_events = set(self.events.keys()) - visited
        while remaining_events:
            # 选择一个未访问的事件作为起点
            event_id = next(iter(remaining_events))
            chain = []
            cycle_visited = set()
            self._build_chain(event_id, chain, cycle_visited)
            
            if chain:
                chains.append(chain)
            
            visited.update(cycle_visited)
            remaining_events -= cycle_visited
        
        return chains
    
    def _build_chain(self, event_id: str, chain: List[str], visited: Set[str]) -> None:
        """递归构建事件链"""
        if event_id in visited:
            return
            
        visited.add(event_id)
        chain.append(event_id)
        
        # 找出所有直接结果事件
        node = self.events[event_id]
        direct_effects = [effect_id for effect_id, relation in node.effects.items() 
                         if relation == CausalityType.DIRECT]
        
        # 按场景顺序排序结果事件
        sorted_effects = sorted(direct_effects, 
                               key=lambda eid: self.events[eid].scene_index)
        
        # 递归处理每个结果事件
        for effect_id in sorted_effects:
            self._build_chain(effect_id, chain, visited)
    
    def analyze_causal_structure(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析事件的因果结构
        
        Args:
            events: 事件列表
            
        Returns:
            因果结构分析结果
        """
        # 首先检查因果问题
        issues = self.check_causal_links(events)
        
        # 获取事件链
        chains = self.get_event_chains()
        
        # 生成修复建议
        suggestions = self.suggest_causal_fixes(issues)
        
        # 计算因果完整性指标
        completeness_score = self._calculate_completeness()
        
        # 识别主要因果线
        main_chain_index, main_chain = self._identify_main_chain(chains)
        
        return {
            "issues": issues,
            "chains": chains,
            "main_chain_index": main_chain_index,
            "suggestions": suggestions,
            "completeness": completeness_score,
            "num_events": len(self.events),
            "num_problems": len([e for e in self.events.values() if e.is_problem()]),
            "num_clues": len([e for e in self.events.values() if e.is_clue()]),
            "num_resolutions": len([e for e in self.events.values() if e.is_resolution()]),
            "num_unresolved": len(self.unresolved_problems),
            "num_dangling": len(self.dangling_clues)
        }
    
    def _calculate_completeness(self) -> float:
        """计算因果完整性指标"""
        # 计算问题解决率和线索发展率
        total_problems = len([e for e in self.events.values() if e.is_problem()])
        total_clues = len([e for e in self.events.values() if e.is_clue()])
        
        if total_problems == 0 and total_clues == 0:
            return 1.0  # 没有问题和线索，视为完整
        
        resolved_problems = total_problems - len(self.unresolved_problems)
        developed_clues = total_clues - len(self.dangling_clues)
        
        problem_score = resolved_problems / total_problems if total_problems > 0 else 1.0
        clue_score = developed_clues / total_clues if total_clues > 0 else 1.0
        
        # 综合指标，问题解决率权重较高
        return 0.7 * problem_score + 0.3 * clue_score
    
    def _identify_main_chain(self, chains: List[List[str]]) -> Tuple[int, List[str]]:
        """识别主要因果链"""
        if not chains:
            return -1, []
        
        # 计算每条链的重要性得分
        chain_scores = []
        for i, chain in enumerate(chains):
            # 计算链中事件的平均重要性
            importance_sum = sum(self.events[event_id].get_importance() for event_id in chain)
            avg_importance = importance_sum / len(chain) if chain else 0
            
            # 计算链的长度得分
            length_score = min(1.0, len(chain) / 10)  # 最多考虑10个事件
            
            # 计算问题-解决得分
            problems_in_chain = sum(1 for event_id in chain if self.events[event_id].is_problem())
            resolutions_in_chain = sum(1 for event_id in chain if self.events[event_id].is_resolution())
            problem_resolution_score = min(problems_in_chain, resolutions_in_chain) / max(1, max(problems_in_chain, resolutions_in_chain))
            
            # 综合得分
            score = (0.4 * avg_importance + 0.3 * length_score + 0.3 * problem_resolution_score)
            chain_scores.append(score)
        
        # 找出得分最高的链
        if chain_scores:
            main_chain_index = chain_scores.index(max(chain_scores))
            return main_chain_index, chains[main_chain_index]
        
        return 0, chains[0] if chains else []  # 默认返回第一条链


def validate_causality(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    便捷函数：验证事件的因果一致性
    
    Args:
        events: 事件列表
        
    Returns:
        因果验证结果
    """
    validator = CausalityValidator()
    return validator.analyze_causal_structure(events) 