#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
对话逻辑校验器

此模块提供用于验证角色对话逻辑一致性的工具。主要功能包括：
1. 历史知识一致性 - 检测对话内容是否与已知历史信息相符
2. 角色背景一致性 - 验证对话是否符合角色的教育水平、职业背景等
3. 时代准确性 - 检查对话内容是否符合特定历史时期的用语和知识
4. 人物关系校验 - 确保对话中提及的人物关系一致
5. 对话情感连贯性 - 分析对话情感变化是否自然合理

使用这些工具可以避免混剪过程中造成的对话逻辑混乱，提高视频的叙事连贯性。
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import os
from pathlib import Path

# 尝试导入知识图谱构建模块
try:
    from src.knowledge.graph_builder import KnowledgeGraph
except ImportError:
    from knowledge.graph_builder import KnowledgeGraph

# 配置日志
logger = logging.getLogger(__name__)

class DialogueConsistencyError(Exception):
    """对话一致性错误基类"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class HistoricalInconsistencyError(DialogueConsistencyError):
    """历史知识不一致错误"""
    pass


class CharacterBackgroundError(DialogueConsistencyError):
    """角色背景不一致错误"""
    pass


class TimelineInconsistencyError(DialogueConsistencyError):
    """时间线不一致错误"""
    pass


class KnowledgeGraph:
    """基础知识图谱类，用于当导入失败时的备用实现"""
    
    def __init__(self):
        """初始化知识图谱"""
        self.entities = {}
        self.relations = []
        
    def add_entity(self, name: str, entity_type: str, attributes: Dict[str, Any] = None):
        """添加实体"""
        if attributes is None:
            attributes = {}
        self.entities[name] = {"type": entity_type, "attributes": attributes}
        
    def add_relation(self, source: str, relation_type: str, target: str, attributes: Dict[str, Any] = None):
        """添加关系"""
        if attributes is None:
            attributes = {}
        self.relations.append((source, relation_type, target, attributes))


class DialogueValidator:
    """
    对话一致性验证器
    
    用于检查对话内容的逻辑一致性，包括历史准确性、角色背景一致性等。
    """
    
    def __init__(self):
        """初始化对话验证器"""
        self.knowledge_graph = KnowledgeGraph()
        self.historical_facts = {}  # 存储历史事实的字典
        self.character_profiles = {}  # 存储角色档案的字典
        self.time_periods = {
            "ancient": (-3000, 476),  # 古代（公元前3000年至公元476年）
            "medieval": (476, 1453),  # 中世纪（476年至1453年）
            "renaissance": (1453, 1600),  # 文艺复兴（1453年至1600年）
            "early_modern": (1600, 1800),  # 早期现代（1600年至1800年）
            "industrial": (1800, 1914),  # 工业时代（1800年至1914年）
            "modern": (1914, 2000),  # 现代（1914年至2000年）
            "contemporary": (2000, 2100),  # 当代（2000年至今）
        }
        
        # 初始化历史背景知识库
        self._init_historical_knowledge()
        
        # 初始化特定时代的关键词和术语
        self.era_keywords = self._load_era_keywords()
        
        # 初始化教育水平对应的语言复杂度指标
        self.education_level_metrics = {
            "小学": {"avg_sentence_length": 8, "max_word_length": 2, "complex_word_ratio": 0.1},
            "初中": {"avg_sentence_length": 12, "max_word_length": 3, "complex_word_ratio": 0.2},
            "高中": {"avg_sentence_length": 16, "max_word_length": 4, "complex_word_ratio": 0.3},
            "大学": {"avg_sentence_length": 20, "max_word_length": 5, "complex_word_ratio": 0.4},
            "研究生": {"avg_sentence_length": 25, "max_word_length": 6, "complex_word_ratio": 0.5},
        }
    
    def _init_historical_knowledge(self):
        """初始化历史知识库"""
        # 基本历史事实（这里只是示例，实际应用中可能需要从数据库或文件加载）
        self.historical_facts = {
            "二战": {"start_year": 1939, "end_year": 1945},
            "冷战": {"start_year": 1947, "end_year": 1991},
            "互联网": {"invention_year": 1983},
            "智能手机": {"invention_year": 2007},
            "清朝": {"start_year": 1644, "end_year": 1912},
            "明朝": {"start_year": 1368, "end_year": 1644},
        }
    
    def _load_era_keywords(self) -> Dict[str, Set[str]]:
        """加载不同时代的关键词和术语"""
        # 这里是一个简化的实现，实际应用中可能需要从数据文件加载
        return {
            "ancient": {"帝国", "奴隶", "神话", "君主", "王朝"},
            "medieval": {"封建", "骑士", "城堡", "十字军", "瘟疫"},
            "renaissance": {"人文主义", "文艺复兴", "改革", "新大陆", "航海"},
            "industrial": {"蒸汽机", "工厂", "铁路", "殖民地", "资本主义"},
            "modern": {"电话", "电影", "广播", "电视", "原子能"},
            "contemporary": {"互联网", "手机", "社交媒体", "人工智能", "气候变化"}
        }
    
    def validate_dialogue(self, scene: Dict[str, Any]) -> Optional[str]:
        """
        验证对话内容的一致性
        
        Args:
            scene: 场景信息，包含对话内容、角色和背景
            
        Returns:
            如果发现问题，返回错误消息；否则返回None
        """
        # 如果场景没有对话，则直接返回
        if "dialogues" not in scene or not scene["dialogues"]:
            return None
        
        # 验证历史知识准确性
        history_issue = self._validate_historical_accuracy(scene)
        if history_issue:
            return history_issue
        
        # 验证角色背景一致性
        character_issue = self._validate_character_background(scene)
        if character_issue:
            return character_issue
        
        # 验证时代准确性
        timeline_issue = self._validate_timeline_accuracy(scene)
        if timeline_issue:
            return timeline_issue
        
        # 验证人物关系
        relationship_issue = self._validate_relationships(scene)
        if relationship_issue:
            return relationship_issue
        
        # 验证对话情感连贯性
        emotion_issue = self._validate_emotional_coherence(scene)
        if emotion_issue:
            return emotion_issue
        
        # 所有验证通过
        return None
    
    def _validate_historical_accuracy(self, scene: Dict[str, Any]) -> Optional[str]:
        """验证对话中的历史知识准确性"""
        if "year" not in scene:
            return None  # 如果没有指定年份，则跳过该验证
        
        year = scene["year"]
        
        for dialogue in scene["dialogues"]:
            text = dialogue.get("text", "")
            
            # 检查对二战的引用
            if "二战" in text and year < 1939:
                return f"时间线矛盾：二战相关对话出现在1939年前"
            
            # 检查对现代技术的引用
            if "互联网" in text and year < 1983:
                return f"时间线矛盾：互联网相关对话出现在1983年前"
            
            if "智能手机" in text and year < 2007:
                return f"时间线矛盾：智能手机相关对话出现在2007年前"
            
            # 检查朝代矛盾
            if "清朝" in text and "当前" in text and (year < 1644 or year > 1912):
                return f"时间线矛盾：清朝作为'当前'朝代在不合适的年份({year})被提及"
        
        return None
    
    def _validate_character_background(self, scene: Dict[str, Any]) -> Optional[str]:
        """验证对话是否符合角色的教育背景和知识水平"""
        for dialogue in scene["dialogues"]:
            if "character" not in dialogue:
                continue
            
            character = dialogue["character"]
            text = dialogue.get("text", "")
            
            # 检查教育水平与语言复杂度的匹配
            education_level = character.get("education_level", "")
            
            if education_level == "小学" and "量子物理" in text:
                return f"教育背景与对话内容不符：小学教育水平的角色讨论量子物理"
            
            if education_level == "小学" and "量子物理" in text:
                return f"教育背景与对话内容不符：小学教育水平的角色讨论量子物理"
                
            # 更复杂的语言复杂度分析可以在这里实现
        
        return None
    
    def _validate_timeline_accuracy(self, scene: Dict[str, Any]) -> Optional[str]:
        """验证对话内容是否符合特定历史时期"""
        if "year" not in scene:
            return None
        
        year = scene["year"]
        era = self._determine_era(year)
        
        for dialogue in scene["dialogues"]:
            text = dialogue.get("text", "")
            
            # 检查是否使用了不符合时代的术语或概念
            for other_era, keywords in self.era_keywords.items():
                if other_era != era:
                    for keyword in keywords:
                        if keyword in text:
                            # 检查关键词是否真的与时代不符（避免误报）
                            # 例如，"封建"一词可以在现代讨论历史时使用
                            if self._is_anachronistic(keyword, era, text):
                                return f"时代用语不符：'{keyword}'是{other_era}时期的术语，不应出现在{era}时期的对话中"
        
        return None
    
    def _determine_era(self, year: int) -> str:
        """根据年份确定时代"""
        for era, (start, end) in self.time_periods.items():
            if start <= year <= end:
                return era
        return "unknown"
    
    def _is_anachronistic(self, keyword: str, current_era: str, context: str) -> bool:
        """
        判断关键词在当前时代的使用是否不合时宜
        
        这里可以实现更复杂的逻辑，例如考虑上下文和讨论的方式
        """
        # 简化实现：如果是在讨论历史，则允许使用其他时代的词汇
        history_indicators = ["历史", "古代", "过去", "传说"]
        for indicator in history_indicators:
            if indicator in context:
                return False
        
        # 否则认为是不合时宜的
        return True
    
    def _validate_relationships(self, scene: Dict[str, Any]) -> Optional[str]:
        """验证对话中提及的人物关系是否一致"""
        # 从对话中提取人物关系
        mentioned_relationships = []
        
        for dialogue in scene["dialogues"]:
            text = dialogue.get("text", "")
            
            # 简单的关系提取（实际应用中应使用更复杂的NLP技术）
            relationship_patterns = [
                (r"我(?:的)?\s*([父母兄弟姐妹叔叔阿姨])", "family"),
                (r"(?:我|他|她)(?:的)?\s*([丈夫妻子老婆老公])", "spouse"),
                (r"(?:我|他|她)(?:的)?\s*([朋友伙伴同事])", "friend"),
                (r"(?:我|他|她)(?:的)?\s*([上司下属老板员工])", "work"),
            ]
            
            for pattern, rel_type in relationship_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    speaker = dialogue.get("character", {}).get("name", "")
                    mentioned_relationships.append((speaker, rel_type, matches[0]))
        
        # 检查关系一致性
        # 这里可以实现更复杂的逻辑，例如检查A说B是其朋友，但B说不认识A的情况
        
        return None
    
    def _validate_emotional_coherence(self, scene: Dict[str, Any]) -> Optional[str]:
        """验证对话的情感连贯性"""
        # 跟踪对话中的情感变化
        if len(scene["dialogues"]) < 2:
            return None  # 单条对话无需检查连贯性
        
        last_emotion = None
        last_character = None
        
        for dialogue in scene["dialogues"]:
            text = dialogue.get("text", "")
            character = dialogue.get("character", {}).get("name", "")
            
            # 简单的情感分析（实际应用中应使用更复杂的NLP技术）
            current_emotion = self._analyze_emotion(text)
            
            # 检查情感突变
            if last_emotion and last_character == character:
                if self._is_emotion_jump(last_emotion, current_emotion):
                    return f"情感连贯性问题：角色'{character}'的情感从'{last_emotion}'突然跳到'{current_emotion}'，缺乏过渡"
            
            last_emotion = current_emotion
            last_character = character
        
        return None
    
    def _analyze_emotion(self, text: str) -> str:
        """从文本中分析情感（简化版）"""
        # 这里使用简单的关键词匹配，实际应用中应使用情感分析模型
        if any(word in text for word in ["高兴", "开心", "快乐", "兴奋", "欣喜"]):
            return "happy"
        elif any(word in text for word in ["悲伤", "难过", "伤心", "痛苦", "绝望"]):
            return "sad"
        elif any(word in text for word in ["愤怒", "生气", "恼火", "暴躁", "憎恨"]):
            return "angry"
        elif any(word in text for word in ["害怕", "恐惧", "担忧", "焦虑", "紧张"]):
            return "fearful"
        else:
            return "neutral"
    
    def _is_emotion_jump(self, emotion1: str, emotion2: str) -> bool:
        """判断两种情感之间是否存在跳跃"""
        # 定义情感对立关系
        opposite_emotions = {
            "happy": ["sad", "angry"],
            "sad": ["happy", "angry"],
            "angry": ["happy", "fearful"],
            "fearful": ["angry", "happy"]
        }
        
        return emotion1 in opposite_emotions.get(emotion2, [])
    
    def expand_knowledge_graph(self, scene: Dict[str, Any]) -> None:
        """从场景对话中扩展知识图谱"""
        for dialogue in scene.get("dialogues", []):
            text = dialogue.get("text", "")
            character = dialogue.get("character", {})
            character_name = character.get("name", "")
            
            if not character_name:
                continue
            
            # 添加角色实体
            if character_name not in self.knowledge_graph.entities:
                attributes = {k: v for k, v in character.items() if k != "name"}
                self.knowledge_graph.add_entity(character_name, "character", attributes)
            
            # 从对话中提取实体和关系
            self._extract_entities_and_relations(character_name, text)
    
    def _extract_entities_and_relations(self, speaker: str, text: str) -> None:
        """从对话文本中提取实体和关系（简化版）"""
        # 提取人名
        name_pattern = r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*|[\u4e00-\u9fa5]{2,3})"
        names = re.findall(name_pattern, text)
        
        # 提取位置
        location_pattern = r"在([A-Z][a-z]+(?:\s[A-Z][a-z]+)*|[\u4e00-\u9fa5]{2,4})"
        locations = re.findall(location_pattern, text)
        
        # 添加实体和关系
        for name in names:
            if name != speaker and name not in self.knowledge_graph.entities:
                self.knowledge_graph.add_entity(name, "person")
                # 添加关系：说话者提到了这个人
                self.knowledge_graph.add_relation(speaker, "mentions", name)
        
        for location in locations:
            if location not in self.knowledge_graph.entities:
                self.knowledge_graph.add_entity(location, "location")
                # 添加关系：说话者提到了这个地点
                self.knowledge_graph.add_relation(speaker, "mentions", location)
    
    def explain_validation_result(self, issue: Optional[str]) -> Dict[str, Any]:
        """
        解释验证结果
        
        Args:
            issue: 验证发现的问题
            
        Returns:
            包含问题解释和建议的字典
        """
        if not issue:
            return {"valid": True, "explanation": "对话逻辑验证通过，未发现问题。"}
        
        explanation = {"valid": False, "issue": issue}
        
        # 根据问题类型提供修复建议
        if "时间线矛盾" in issue:
            explanation["suggestion"] = "调整对话内容，确保符合设定的历史时期，或调整场景的时间设置。"
        elif "教育背景" in issue:
            explanation["suggestion"] = "修改对话内容，使其符合角色的教育背景和知识水平，或调整角色的教育背景设定。"
        elif "时代用语不符" in issue:
            explanation["suggestion"] = "修改对话，使用符合特定历史时期的用语和概念，避免时代错位。"
        elif "情感连贯性问题" in issue:
            explanation["suggestion"] = "在情感变化明显的对话之间添加过渡性内容，使情感变化更自然。"
        else:
            explanation["suggestion"] = "检查对话内容，确保与剧情背景和角色设定保持一致。"
        
        return explanation


def validate_dialogue_consistency(scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    便捷函数：验证对话一致性
    
    Args:
        scene: 场景信息，包含对话内容、角色和背景
        
    Returns:
        验证结果和建议
    """
    validator = DialogueValidator()
    issue = validator.validate_dialogue(scene)
    return validator.explain_validation_result(issue) 