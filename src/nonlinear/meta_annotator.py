#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
元叙事注释器

为场景添加丰富的元叙事注释，帮助理解场景在整体叙事中的结构角色和关联关系。
通过深入分析场景内容、情感变化、角色互动等信息，构建更完整的叙事理解。
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from enum import Enum
import numpy as np

# 导入相关模块
from src.narrative.anchor_types import AnchorType, AnchorInfo
from src.narrative.structure_selector import select_narrative_structure, get_structure_patterns
from src.utils.text_analyzer import extract_keywords, calc_text_similarity

# 创建日志记录器
logger = logging.getLogger("meta_annotator")


class StructuralRole(Enum):
    """场景在叙事结构中的角色枚举"""
    HOOK = "hook"                # 开场钩子，吸引观众注意
    SETUP = "setup"              # 设定，介绍背景和角色
    INCITING = "inciting"        # 引发事件，故事正式开始的触发点
    RISING = "rising"            # 情节发展，冲突升级
    MIDPOINT = "midpoint"        # 中点转折，故事转向的关键点
    COMPLICATION = "complication" # 复杂化，新的障碍出现
    CRISIS = "crisis"            # 危机，紧张局势达到高峰前
    CLIMAX = "climax"            # 高潮，情节最激烈处
    RESOLUTION = "resolution"    # 解决，冲突的解决
    FALLOUT = "fallout"          # 余波，高潮后的收尾
    EPILOGUE = "epilogue"        # 尾声，故事结束的额外场景


class LogicChainType(Enum):
    """逻辑链类型枚举"""
    CAUSALITY = "causality"      # 因果关系
    CHARACTER_ARC = "character_arc" # 角色弧
    THEME_DEVELOPMENT = "theme_development" # 主题发展
    FORESHADOWING = "foreshadowing" # 前兆暗示
    PARALLEL = "parallel"        # 平行情节
    CONTRAST = "contrast"        # 对比情节


class MetaAnnotator:
    """
    元叙事注释器，分析场景并添加丰富的元叙事注释
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化元叙事注释器
        
        Args:
            config_path: 配置文件路径，可选
        """
        # 初始化关键词提取器
        self.key_phrases = {
            StructuralRole.HOOK: ["开场", "引入", "介绍", "首先", "一开始"],
            StructuralRole.SETUP: ["背景", "设定", "介绍", "认识", "初遇"],
            StructuralRole.INCITING: ["突然", "意外", "转折", "开始", "决定"],
            StructuralRole.RISING: ["逐渐", "越来越", "发展", "深入", "进展"],
            StructuralRole.MIDPOINT: ["转折", "关键点", "意识到", "发现", "醒悟"],
            StructuralRole.COMPLICATION: ["问题", "困难", "障碍", "挑战", "阻碍"],
            StructuralRole.CRISIS: ["危机", "紧张", "冲突", "对抗", "绝境"],
            StructuralRole.CLIMAX: ["高潮", "巅峰", "极限", "关键", "决战"],
            StructuralRole.RESOLUTION: ["解决", "处理", "缓解", "方案", "办法"],
            StructuralRole.FALLOUT: ["结果", "后果", "影响", "余波", "反应"],
            StructuralRole.EPILOGUE: ["结局", "尾声", "最后", "结束", "告别"]
        }
        
        # 结构角色分布模板（在整个故事中的相对位置）
        self.role_position_template = {
            StructuralRole.HOOK: 0.0,
            StructuralRole.SETUP: 0.08,
            StructuralRole.INCITING: 0.15,
            StructuralRole.RISING: 0.3,
            StructuralRole.MIDPOINT: 0.5,
            StructuralRole.COMPLICATION: 0.65,
            StructuralRole.CRISIS: 0.75,
            StructuralRole.CLIMAX: 0.85,
            StructuralRole.RESOLUTION: 0.92,
            StructuralRole.FALLOUT: 0.95,
            StructuralRole.EPILOGUE: 0.98
        }
        
        # 位置容差（允许的位置偏移范围）
        self.position_tolerance = 0.1
        
        # 导入叙事结构库
        self.narrative_patterns = get_structure_patterns()
        
        logger.info("元叙事注释器初始化完成")
    
    def annotate_scenes(self, scenes: List[Dict[str, Any]], 
                      anchors: Optional[List[AnchorInfo]] = None) -> List[Dict[str, Any]]:
        """
        为场景添加元叙事注释
        
        Args:
            scenes: 场景列表
            anchors: 情节锚点列表，可选
            
        Returns:
            添加了元注释的场景列表
        """
        if not scenes:
            return []
        
        # 创建场景副本，避免修改原始数据
        annotated_scenes = [scene.copy() for scene in scenes]
        
        # 预处理：提取基本信息
        total_scenes = len(scenes)
        scene_texts = [self._extract_scene_text(scene) for scene in scenes]
        scene_keywords = [extract_keywords(text, 5) for text in scene_texts]
        
        # 1. 标识每个场景的结构角色
        for i, scene in enumerate(annotated_scenes):
            # 计算场景在整体中的相对位置
            position = i / total_scenes
            
            # 确定场景结构角色
            role = self._get_structural_role(scene, position, i, total_scenes, anchors)
            
            # 确保meta字段存在
            if "meta" not in scene:
                scene["meta"] = {}
                
            # 添加结构角色标签
            scene["meta"]["structural_role"] = role.value
            
            # 为角色添加中文描述
            scene["meta"]["role_description"] = self._get_role_description(role)
        
        # 2. 找出场景之间的关联
        # 为每个场景找出相关的其他场景
        for i, scene in enumerate(annotated_scenes):
            related_scenes = self._find_related_scenes(scene, annotated_scenes, i, scene_texts, scene_keywords)
            scene["meta"]["connect_to"] = related_scenes
        
        # 3. 构建场景之间的逻辑链
        self._build_logic_chains(annotated_scenes, anchors)
        
        return annotated_scenes
    
    def _extract_scene_text(self, scene: Dict[str, Any]) -> str:
        """提取场景的文本内容"""
        # 尝试从不同字段获取文本
        text = scene.get("text", "")
        if not text:
            text = scene.get("content", "")
        if not text:
            text = scene.get("subtitle", "")
        if not text:
            dialogue = scene.get("dialogue", "")
            if dialogue:
                if isinstance(dialogue, list):
                    text = " ".join(dialogue)
                else:
                    text = dialogue
        
        return text
    
    def _get_structural_role(self, scene: Dict[str, Any], position: float, 
                           index: int, total: int,
                           anchors: Optional[List[AnchorInfo]] = None) -> StructuralRole:
        """
        确定场景的结构角色
        
        Args:
            scene: 场景字典
            position: 场景在整体中的相对位置(0-1)
            index: 场景索引
            total: 场景总数
            anchors: 情节锚点列表，可选
            
        Returns:
            场景的结构角色
        """
        # 1. 首先查看是否有明确标签
        if "tags" in scene:
            tags = scene["tags"]
            if isinstance(tags, str):
                tags = [tags]
                
            # 检查直接映射的标签
            tag_role_map = {
                "开场": StructuralRole.HOOK,
                "引入": StructuralRole.SETUP,
                "设定": StructuralRole.SETUP,
                "触发": StructuralRole.INCITING,
                "发展": StructuralRole.RISING,
                "转折": StructuralRole.MIDPOINT,
                "复杂化": StructuralRole.COMPLICATION,
                "困境": StructuralRole.CRISIS,
                "危机": StructuralRole.CRISIS,
                "高潮": StructuralRole.CLIMAX,
                "解决": StructuralRole.RESOLUTION,
                "结局": StructuralRole.EPILOGUE
            }
            
            for tag in tags:
                if tag in tag_role_map:
                    return tag_role_map[tag]
        
        # 2. 检查锚点信息
        if anchors:
            for anchor in anchors:
                anchor_position = anchor.position
                if abs(position - anchor_position) < 0.05:  # 如果场景位置与锚点位置接近
                    # 锚点类型到结构角色的映射
                    anchor_role_map = {
                        AnchorType.EMOTION: StructuralRole.MIDPOINT,
                        AnchorType.CHARACTER: StructuralRole.SETUP,
                        AnchorType.SUSPENSE: StructuralRole.COMPLICATION,
                        AnchorType.CONFLICT: StructuralRole.CRISIS,
                        AnchorType.REVELATION: StructuralRole.MIDPOINT,
                        AnchorType.TRANSITION: StructuralRole.RISING,
                        AnchorType.CLIMAX: StructuralRole.CLIMAX,
                        AnchorType.RESOLUTION: StructuralRole.RESOLUTION
                    }
                    
                    if anchor.type in anchor_role_map:
                        return anchor_role_map[anchor.type]
        
        # 3. 根据内容分析
        text = self._extract_scene_text(scene)
        
        # 检查是否包含特定关键词
        for role, phrases in self.key_phrases.items():
            if any(phrase in text for phrase in phrases):
                return role
        
        # 4. 根据位置推断
        # 为每个可能的角色计算位置匹配度，选择最接近的
        best_match = None
        min_distance = float('inf')
        
        for role, ideal_position in self.role_position_template.items():
            distance = abs(position - ideal_position)
            if distance < min_distance:
                min_distance = distance
                best_match = role
        
        # 特殊处理：强制第一个场景为HOOK或SETUP，最后一个场景为RESOLUTION或EPILOGUE
        if index == 0:
            if min_distance > 0.1:  # 如果不是很接近理想位置
                return StructuralRole.HOOK
        elif index == total - 1:
            if min_distance > 0.1:  # 如果不是很接近理想位置
                return StructuralRole.EPILOGUE
        
        return best_match if best_match else StructuralRole.RISING
    
    def _get_role_description(self, role: StructuralRole) -> str:
        """获取结构角色的中文描述"""
        descriptions = {
            StructuralRole.HOOK: "悬念铺垫",
            StructuralRole.SETUP: "背景设定",
            StructuralRole.INCITING: "触发事件",
            StructuralRole.RISING: "情节发展",
            StructuralRole.MIDPOINT: "中点转折",
            StructuralRole.COMPLICATION: "情节复杂化",
            StructuralRole.CRISIS: "危机紧张",
            StructuralRole.CLIMAX: "情节高潮",
            StructuralRole.RESOLUTION: "问题解决",
            StructuralRole.FALLOUT: "事件余波",
            StructuralRole.EPILOGUE: "故事尾声"
        }
        
        return descriptions.get(role, "情节发展")
    
    def _find_related_scenes(self, scene: Dict[str, Any], 
                           all_scenes: List[Dict[str, Any]],
                           current_index: int,
                           scene_texts: List[str],
                           scene_keywords: List[List[str]]) -> List[str]:
        """
        查找与当前场景相关的其他场景
        
        Args:
            scene: 当前场景
            all_scenes: 所有场景
            current_index: 当前场景索引
            scene_texts: 所有场景的文本内容
            scene_keywords: 所有场景的关键词列表
            
        Returns:
            相关场景的ID或描述列表
        """
        current_text = scene_texts[current_index]
        current_keywords = set(scene_keywords[current_index])
        
        # 存储相关场景及其相关性分数
        related_with_score = []
        
        # 对场景当前角色进行跟踪
        current_role = StructuralRole(scene["meta"]["structural_role"])
        current_characters = self._extract_characters(scene)
        
        for i, other_scene in enumerate(all_scenes):
            if i == current_index:
                continue  # 跳过自己
                
            # 相关性分数
            relevance_score = 0.0
            other_text = scene_texts[i]
            
            # 1. 检查角色连续性
            other_characters = self._extract_characters(other_scene)
            character_overlap = len(current_characters.intersection(other_characters))
            if character_overlap > 0:
                relevance_score += 0.3 * (character_overlap / max(len(current_characters), 1))
            
            # 2. 检查情节连贯性
            other_role = StructuralRole(other_scene["meta"]["structural_role"])
            
            # 特定结构角色之间的天然联系
            natural_connections = {
                StructuralRole.HOOK: [StructuralRole.SETUP, StructuralRole.INCITING],
                StructuralRole.SETUP: [StructuralRole.INCITING, StructuralRole.HOOK],
                StructuralRole.INCITING: [StructuralRole.RISING, StructuralRole.SETUP],
                StructuralRole.RISING: [StructuralRole.MIDPOINT, StructuralRole.COMPLICATION],
                StructuralRole.MIDPOINT: [StructuralRole.COMPLICATION, StructuralRole.RISING],
                StructuralRole.COMPLICATION: [StructuralRole.CRISIS, StructuralRole.CLIMAX],
                StructuralRole.CRISIS: [StructuralRole.CLIMAX, StructuralRole.COMPLICATION],
                StructuralRole.CLIMAX: [StructuralRole.RESOLUTION, StructuralRole.FALLOUT],
                StructuralRole.RESOLUTION: [StructuralRole.FALLOUT, StructuralRole.EPILOGUE],
                StructuralRole.FALLOUT: [StructuralRole.EPILOGUE, StructuralRole.RESOLUTION],
                StructuralRole.EPILOGUE: [StructuralRole.FALLOUT, StructuralRole.RESOLUTION]
            }
            
            if other_role in natural_connections.get(current_role, []):
                relevance_score += 0.25
            
            # 3. 关键词重叠
            other_keywords = set(scene_keywords[i])
            keyword_overlap = len(current_keywords.intersection(other_keywords))
            if keyword_overlap > 0:
                relevance_score += 0.2 * (keyword_overlap / max(len(current_keywords), 1))
            
            # 4. 内容相似度（简化版）
            # 如果文本太长，只考虑前100个字符
            short_current = current_text[:min(len(current_text), 100)]
            short_other = other_text[:min(len(other_text), 100)]
            
            if short_current and short_other:
                similarity = calc_text_similarity(short_current, short_other)
                relevance_score += 0.15 * similarity
            
            # 5. 时间接近性（按索引）
            distance = abs(current_index - i)
            max_distance = len(all_scenes) - 1
            proximity = 1 - (distance / max_distance) if max_distance > 0 else 0
            relevance_score += 0.1 * proximity
            
            # 加入列表
            if relevance_score > 0.3:  # 只保留相关性达到阈值的场景
                scene_id = other_scene.get("scene_id", f"场景{i+1}")
                related_with_score.append((scene_id, relevance_score))
        
        # 按相关性排序，取前3个
        related_with_score.sort(key=lambda x: x[1], reverse=True)
        related_scenes = [scene_id for scene_id, _ in related_with_score[:3]]
        
        return related_scenes
    
    def _extract_characters(self, scene: Dict[str, Any]) -> Set[str]:
        """从场景中提取角色"""
        characters = set()
        
        # 检查是否已经有角色信息
        if "character" in scene:
            char = scene["character"]
            if char:
                if isinstance(char, list):
                    characters.update(char)
                else:
                    characters.add(char)
        
        if "characters" in scene:
            chars = scene["characters"]
            if chars:
                if isinstance(chars, list):
                    characters.update(chars)
                elif isinstance(chars, str):
                    characters.add(chars)
        
        # 也可以从内容中尝试提取角色，但这需要更复杂的NLP
        
        return characters
    
    def _build_logic_chains(self, scenes: List[Dict[str, Any]], 
                          anchors: Optional[List[AnchorInfo]] = None) -> None:
        """
        构建场景之间的逻辑链
        
        Args:
            scenes: 场景列表
            anchors: 情节锚点列表，可选
        """
        if len(scenes) <= 1:
            return
        
        # 获取角色信息
        all_characters = set()
        for scene in scenes:
            all_characters.update(self._extract_characters(scene))
        
        # 追踪每个角色的场景序列
        character_scenes = {char: [] for char in all_characters if char}
        
        for i, scene in enumerate(scenes):
            scene_chars = self._extract_characters(scene)
            for char in scene_chars:
                if char:  # 确保角色名不为空
                    character_scenes[char].append(i)
        
        # 分析角色弧
        for char, scene_indices in character_scenes.items():
            if len(scene_indices) > 1:  # 只处理出现在多个场景的角色
                for i in range(1, len(scene_indices)):
                    prev_idx = scene_indices[i-1]
                    curr_idx = scene_indices[i]
                    
                    if "meta" not in scenes[curr_idx]:
                        scenes[curr_idx]["meta"] = {}
                    
                    # 添加逻辑链
                    if "logic_chain" not in scenes[curr_idx]["meta"]:
                        scenes[curr_idx]["meta"]["logic_chain"] = f"伏笔A → 呼应B"
                    
                    # 可以在这里为不同类型的逻辑链添加更复杂的规则
        
        # 分析因果关系
        # 这需要更高级的NLP理解，这里仅做简单处理
        for i in range(1, len(scenes)):
            role = StructuralRole(scenes[i]["meta"]["structural_role"])
            prev_role = StructuralRole(scenes[i-1]["meta"]["structural_role"])
            
            # 特定角色组合暗示因果关系
            if (prev_role == StructuralRole.INCITING and role == StructuralRole.RISING) or \
               (prev_role == StructuralRole.COMPLICATION and role == StructuralRole.CRISIS) or \
               (prev_role == StructuralRole.CRISIS and role == StructuralRole.CLIMAX):
                
                if "meta" not in scenes[i]:
                    scenes[i]["meta"] = {}
                
                if "logic_chain" not in scenes[i]["meta"]:
                    scenes[i]["meta"]["logic_chain"] = f"因A → 果B"


def add_meta_comments(scenes: List[Dict[str, Any]], 
                     anchors: Optional[List[AnchorInfo]] = None) -> List[Dict[str, Any]]:
    """
    添加重构编辑的元注释的便捷函数
    
    Args:
        scenes: 场景列表
        anchors: 情节锚点列表，可选
        
    Returns:
        添加了元注释的场景列表
    """
    annotator = MetaAnnotator()
    return annotator.annotate_scenes(scenes, anchors)


def get_scene_structural_role(scene: Dict[str, Any]) -> str:
    """
    获取场景的结构角色的便捷函数
    
    Args:
        scene: 场景字典
        
    Returns:
        场景的结构角色字符串
    """
    if "meta" in scene and "structural_role" in scene["meta"]:
        return scene["meta"]["structural_role"]
    return ""


def get_scene_connections(scene: Dict[str, Any]) -> List[str]:
    """
    获取场景的关联场景列表的便捷函数
    
    Args:
        scene: 场景字典
        
    Returns:
        关联场景ID或描述列表
    """
    if "meta" in scene and "connect_to" in scene["meta"]:
        return scene["meta"]["connect_to"]
    return []


def get_scene_logic_chain(scene: Dict[str, Any]) -> str:
    """
    获取场景的逻辑链的便捷函数
    
    Args:
        scene: 场景字典
        
    Returns:
        逻辑链描述字符串
    """
    if "meta" in scene and "logic_chain" in scene["meta"]:
        return scene["meta"]["logic_chain"]
    return ""


if __name__ == "__main__":
    # 简单示例
    import json
    
    # 创建测试场景
    test_scenes = [
        {
            "scene_id": "scene_001",
            "text": "主角小明走在街上，偶然发现一个神秘的信封。",
            "duration": 5.0,
            "character": "小明"
        },
        {
            "scene_id": "scene_002",
            "text": "小明打开信封，里面是一张神秘地图。",
            "duration": 4.0,
            "character": "小明"
        },
        {
            "scene_id": "scene_003",
            "text": "小明决定按照地图去寻找宝藏。途中他遇到了小红。",
            "duration": 6.0,
            "characters": ["小明", "小红"]
        },
        {
            "scene_id": "scene_004",
            "text": "小明和小红一起冒险，遇到了许多障碍。",
            "duration": 8.0,
            "characters": ["小明", "小红"]
        },
        {
            "scene_id": "scene_005",
            "text": "他们终于找到了宝藏，但发现宝藏被怪兽守护着。",
            "duration": 7.0,
            "characters": ["小明", "小红"],
            "tags": ["高潮"]
        },
        {
            "scene_id": "scene_006",
            "text": "经过一番激战，他们打败了怪兽，获得了宝藏。",
            "duration": 9.0,
            "characters": ["小明", "小红"]
        },
        {
            "scene_id": "scene_007",
            "text": "他们回到城市，分享了宝藏，成为了好朋友。",
            "duration": 5.0,
            "characters": ["小明", "小红"],
            "tags": ["结局"]
        }
    ]
    
    # 添加元注释
    annotated = add_meta_comments(test_scenes)
    
    # 打印结果
    for scene in annotated:
        print(f"场景ID: {scene['scene_id']}")
        print(f"结构角色: {scene['meta']['structural_role']}")
        print(f"相关场景: {', '.join(scene['meta'].get('connect_to', []))}")
        if "logic_chain" in scene['meta']:
            print(f"逻辑链: {scene['meta']['logic_chain']}")
        print("-" * 40) 