#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认知负荷优化器模块

优化内容的认知负荷，确保用户能够舒适地接收和处理信息，
提高用户体验和内容有效性。根据用户认知能力动态调整内容复杂度。
"""

import os
import json
import copy
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import re
from collections import defaultdict

from loguru import logger
from src.utils.log_handler import get_logger

# 配置日志
cognitive_logger = get_logger("cognitive_optimizer")

class CognitiveLoadBalancer:
    """
    认知负荷优化器
    
    根据内容复杂度和用户认知能力，优化内容的认知负荷，
    确保用户能够舒适地接收和处理信息，提高用户体验和内容有效性。
    """
    
    # 认知负荷阈值
    MAX_LOAD = 0.7  # 认知负荷阈值
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化认知负荷优化器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化简化策略
        self._initialize_simplification_strategies()
        
        cognitive_logger.info("认知负荷优化器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        default_config = {
            "thresholds": {
                "max_cognitive_load": 0.7,
                "min_cognitive_load": 0.3,
                "optimal_load": 0.5
            },
            "user_factors": {
                "attention_span_weight": 0.4,
                "processing_speed_weight": 0.3,
                "domain_knowledge_weight": 0.3
            },
            "content_factors": {
                "complexity_weight": 0.35,
                "density_weight": 0.25,
                "pacing_weight": 0.25,
                "novelty_weight": 0.15
            },
            "simplification_strategies": {
                "reduce_information_density": True,
                "slow_down_pacing": True,
                "chunk_complex_information": True,
                "reduce_transitions": True,
                "prioritize_essential_content": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config
            except Exception as e:
                cognitive_logger.error(f"加载配置文件失败: {str(e)}")
                
        return default_config
    
    def _initialize_simplification_strategies(self):
        """
        初始化内容简化策略
        """
        self.simplification_strategies = {
            "reduce_information_density": self._reduce_information_density,
            "slow_down_pacing": self._slow_down_pacing,
            "chunk_complex_information": self._chunk_complex_information,
            "reduce_transitions": self._reduce_transitions,
            "prioritize_essential_content": self._prioritize_essential_content
        }
    
    def optimize(self, content: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        优化内容认知负荷
        
        根据用户认知能力和内容复杂度，动态调整内容，
        确保用户能够舒适地接收和处理信息。
        
        Args:
            content: 需要优化的内容
            user_profile: 用户画像，包含认知能力指标
            
        Returns:
            优化后的内容
        """
        cognitive_logger.info("开始认知负荷优化")
        
        # 创建内容副本
        optimized_content = copy.deepcopy(content)
        
        # 计算当前认知负荷
        current_load = self._calculate_load(optimized_content, user_profile)
        cognitive_logger.debug(f"初始认知负荷: {current_load:.2f}")
        
        # 迭代优化，直到认知负荷在可接受范围内或无法进一步优化
        max_iterations = 5
        iteration = 0
        
        while current_load > self.config["thresholds"]["max_cognitive_load"] and iteration < max_iterations:
            # 应用简化策略
            optimized_content = self._simplify_content(optimized_content, current_load)
            
            # 重新计算认知负荷
            new_load = self._calculate_load(optimized_content, user_profile)
            
            # 检查是否有改善
            if abs(new_load - current_load) < 0.01:
                # 几乎没有改善，中断循环
                cognitive_logger.debug("认知负荷优化达到极限")
                break
            
            current_load = new_load
            iteration += 1
            cognitive_logger.debug(f"优化迭代 {iteration}, 当前认知负荷: {current_load:.2f}")
        
        cognitive_logger.info(f"认知负荷优化完成，最终负荷: {current_load:.2f}")
        return optimized_content
    
    def _calculate_load(self, content: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None) -> float:
        """
        计算内容的认知负荷
        
        基于内容复杂度、信息密度、节奏等因素，以及用户的认知能力，
        计算内容的认知负荷分数。
        
        Args:
            content: 内容数据
            user_profile: 用户画像，包含认知能力指标
            
        Returns:
            认知负荷分数，范围在0-1之间
        """
        # 提取内容特征
        content_features = self._extract_content_features(content)
        
        # 计算内容因素得分
        content_score = self._calculate_content_score(content_features)
        
        # 如果有用户画像，考虑用户认知能力
        if user_profile:
            user_factors = self._extract_user_factors(user_profile)
            # 基于用户能力调整认知负荷
            load = content_score * (1.0 - self._calculate_user_capability(user_factors))
        else:
            # 没有用户画像，使用标准负荷
            load = content_score
        
        return min(1.0, max(0.0, load))
    
    def _extract_content_features(self, content: Dict[str, Any]) -> Dict[str, float]:
        """
        提取内容认知负荷相关特征
        
        Args:
            content: 内容数据
            
        Returns:
            内容特征字典
        """
        features = {
            "complexity": 0.0,
            "density": 0.0,
            "pacing": 0.0,
            "novelty": 0.0
        }
        
        # 计算复杂度（基于场景转换、特效使用等）
        if "scenes" in content and isinstance(content["scenes"], list):
            # 场景数量和复杂度
            scenes = content["scenes"]
            num_scenes = len(scenes)
            
            if num_scenes > 0:
                # 场景复杂度
                scene_complexities = []
                total_transitions = 0
                total_effects = 0
                total_elements = 0
                
                for scene in scenes:
                    transitions = scene.get("transitions", [])
                    effects = scene.get("effects", [])
                    elements = len(scene.get("elements", []))
                    
                    total_transitions += len(transitions)
                    total_effects += len(effects)
                    total_elements += elements
                    
                    # 计算单个场景复杂度
                    scene_complexity = (
                        0.4 * len(transitions) / max(1, 3) +  # 标准化到3个转场
                        0.3 * len(effects) / max(1, 5) +     # 标准化到5个特效
                        0.3 * elements / max(1, 10)          # 标准化到10个元素
                    )
                    scene_complexities.append(scene_complexity)
                
                # 整体复杂度
                features["complexity"] = min(1.0, 0.5 * (
                    # 场景平均复杂度
                    sum(scene_complexities) / num_scenes +
                    # 整体场景数量复杂度
                    num_scenes / 20  # 标准化到20个场景
                ))
                
                # 信息密度（元素/场景数量比例）
                features["density"] = min(1.0, total_elements / (num_scenes * 10))
                
                # 节奏/速度
                if "duration" in content and content["duration"] > 0:
                    # 场景切换速度
                    scene_rate = num_scenes / content["duration"]  # 场景数/秒
                    features["pacing"] = min(1.0, scene_rate * 10)  # 标准化，假设1秒1个场景为0.1分
        
        # 新奇度（基于内容标签的独特性）
        if "tags" in content and isinstance(content["tags"], list):
            # 内容标签的独特程度（这里简化处理，实际应该比较用户已知标签）
            unique_factor = 0.5  # 默认中等新奇度
            features["novelty"] = unique_factor
        
        # 文本复杂度
        if "dialogues" in content and isinstance(content["dialogues"], list):
            dialogues = content["dialogues"]
            if dialogues:
                # 平均句子长度
                total_words = sum(len(dialogue.get("text", "").split()) for dialogue in dialogues)
                avg_sentence_length = total_words / len(dialogues)
                
                # 文本复杂度影响总复杂度
                text_complexity = min(1.0, avg_sentence_length / 20)  # 标准化到20词/句
                features["complexity"] = (features["complexity"] + text_complexity) / 2
        
        return features
    
    def _extract_user_factors(self, user_profile: Dict[str, Any]) -> Dict[str, float]:
        """
        从用户画像中提取认知能力因素
        
        Args:
            user_profile: 用户画像
            
        Returns:
            用户认知因素字典
        """
        factors = {
            "attention_span": 0.5,  # 默认注意力水平
            "processing_speed": 0.5,  # 默认处理速度
            "domain_knowledge": 0.5   # 默认领域知识
        }
        
        # 从用户画像中提取认知能力指标
        cognitive = user_profile.get("cognitive_abilities", {})
        
        if isinstance(cognitive, dict):
            # 注意力水平
            if "attention_span" in cognitive:
                factors["attention_span"] = min(1.0, max(0.0, cognitive["attention_span"]))
            
            # 处理速度
            if "processing_speed" in cognitive:
                factors["processing_speed"] = min(1.0, max(0.0, cognitive["processing_speed"]))
            
            # 领域知识
            if "domain_knowledge" in cognitive:
                factors["domain_knowledge"] = min(1.0, max(0.0, cognitive["domain_knowledge"]))
        
        return factors
    
    def _calculate_content_score(self, content_features: Dict[str, float]) -> float:
        """
        计算内容因素得分
        
        Args:
            content_features: 内容特征
            
        Returns:
            内容得分
        """
        weights = self.config["content_factors"]
        
        # 加权计算各因素得分
        score = (
            weights["complexity_weight"] * content_features["complexity"] +
            weights["density_weight"] * content_features["density"] +
            weights["pacing_weight"] * content_features["pacing"] +
            weights["novelty_weight"] * content_features["novelty"]
        )
        
        return min(1.0, max(0.0, score))
    
    def _calculate_user_capability(self, user_factors: Dict[str, float]) -> float:
        """
        计算用户认知能力分数
        
        Args:
            user_factors: 用户认知因素
            
        Returns:
            用户能力分数
        """
        weights = self.config["user_factors"]
        
        # 加权计算用户能力
        capability = (
            weights["attention_span_weight"] * user_factors["attention_span"] +
            weights["processing_speed_weight"] * user_factors["processing_speed"] +
            weights["domain_knowledge_weight"] * user_factors["domain_knowledge"]
        )
        
        return min(1.0, max(0.0, capability))
    
    def _simplify_content(self, content: Dict[str, Any], current_load: float) -> Dict[str, Any]:
        """
        简化内容以降低认知负荷
        
        根据当前负荷水平，应用不同的简化策略
        
        Args:
            content: 内容数据
            current_load: 当前认知负荷
            
        Returns:
            简化后的内容
        """
        # 创建内容副本
        simplified = copy.deepcopy(content)
        
        # 决定简化强度（基于当前负荷与目标负荷的差距）
        target_load = self.config["thresholds"]["optimal_load"]
        simplification_intensity = min(1.0, (current_load - target_load) / 0.5)
        
        # 应用启用的简化策略
        for strategy_name, enabled in self.config["simplification_strategies"].items():
            if enabled and strategy_name in self.simplification_strategies:
                strategy_func = self.simplification_strategies[strategy_name]
                simplified = strategy_func(simplified, simplification_intensity)
        
        return simplified
    
    def _reduce_information_density(self, content: Dict[str, Any], intensity: float) -> Dict[str, Any]:
        """
        降低信息密度
        
        减少次要信息和细节，保留核心内容
        
        Args:
            content: 内容数据
            intensity: 简化强度
            
        Returns:
            简化后的内容
        """
        result = copy.deepcopy(content)
        
        # 计算需要保留的信息比例
        retention_ratio = max(0.5, 1.0 - intensity * 0.5)
        
        # 处理场景元素
        if "scenes" in result and isinstance(result["scenes"], list):
            for scene in result["scenes"]:
                # 简化次要元素
                if "elements" in scene and isinstance(scene["elements"], list):
                    # 为元素计算重要性分数
                    elements_with_importance = []
                    for element in scene["elements"]:
                        importance = element.get("importance", 0.5)
                        elements_with_importance.append((element, importance))
                    
                    # 按重要性排序
                    elements_with_importance.sort(key=lambda x: x[1], reverse=True)
                    
                    # 保留重要元素
                    elements_to_keep = max(1, int(len(elements_with_importance) * retention_ratio))
                    scene["elements"] = [e[0] for e in elements_with_importance[:elements_to_keep]]
        
        # 简化对话/文本
        if "dialogues" in result and isinstance(result["dialogues"], list):
            dialogues = result["dialogues"]
            if len(dialogues) > 3:  # 至少保留最少数量的对话
                # 按重要性排序
                dialogues_with_importance = []
                for dialogue in dialogues:
                    importance = dialogue.get("importance", 0.5)
                    dialogues_with_importance.append((dialogue, importance))
                
                dialogues_with_importance.sort(key=lambda x: x[1], reverse=True)
                
                # 保留重要对话
                dialogues_to_keep = max(3, int(len(dialogues) * retention_ratio))
                result["dialogues"] = [d[0] for d in dialogues_with_importance[:dialogues_to_keep]]
        
        return result
    
    def _slow_down_pacing(self, content: Dict[str, Any], intensity: float) -> Dict[str, Any]:
        """
        降低节奏/速度
        
        延长场景持续时间，降低切换频率
        
        Args:
            content: 内容数据
            intensity: 简化强度
            
        Returns:
            简化后的内容
        """
        result = copy.deepcopy(content)
        
        if "scenes" in result and isinstance(result["scenes"], list):
            scenes = result["scenes"]
            
            # 如果场景数量较多，合并一些相似场景
            if len(scenes) > 5:
                # 计算需要合并的场景数量
                merge_target = max(5, int(len(scenes) * (1.0 - intensity * 0.3)))
                
                # 尝试找出最相似的场景进行合并
                while len(scenes) > merge_target:
                    # 简化：删除重要性最低的场景
                    # 实际应用中应该使用更复杂的相似度计算和合并逻辑
                    min_importance = 1.0
                    min_idx = 0
                    
                    for i, scene in enumerate(scenes):
                        importance = scene.get("importance", 0.5)
                        if importance < min_importance:
                            min_importance = importance
                            min_idx = i
                    
                    # 删除重要性最低的场景
                    if min_importance < 0.7:  # 不删除重要场景
                        scenes.pop(min_idx)
                    else:
                        break  # 没有不重要的场景可删除
            
            # 调整场景持续时间
            for scene in scenes:
                if "duration" in scene:
                    # 延长持续时间，最多增加30%
                    scene["duration"] *= (1.0 + intensity * 0.3)
        
        return result
    
    def _chunk_complex_information(self, content: Dict[str, Any], intensity: float) -> Dict[str, Any]:
        """
        将复杂信息分块
        
        将复杂概念分解为更容易理解的部分
        
        Args:
            content: 内容数据
            intensity: 简化强度
            
        Returns:
            简化后的内容
        """
        result = copy.deepcopy(content)
        
        # 处理复杂场景
        if "scenes" in result and isinstance(result["scenes"], list):
            new_scenes = []
            
            for scene in result["scenes"]:
                # 检查场景复杂度
                complexity = self._calculate_scene_complexity(scene)
                
                if complexity > 0.7 and intensity > 0.3:
                    # 将复杂场景分解为两个
                    scene1, scene2 = self._split_scene(scene)
                    new_scenes.append(scene1)
                    new_scenes.append(scene2)
                else:
                    new_scenes.append(scene)
            
            result["scenes"] = new_scenes
        
        return result
    
    def _calculate_scene_complexity(self, scene: Dict[str, Any]) -> float:
        """
        计算场景复杂度
        
        Args:
            scene: 场景数据
            
        Returns:
            复杂度得分
        """
        # 元素数量
        elements_count = len(scene.get("elements", []))
        
        # 特效数量
        effects_count = len(scene.get("effects", []))
        
        # 转场数量
        transitions_count = len(scene.get("transitions", []))
        
        # 计算复杂度得分
        complexity = (
            0.4 * min(1.0, elements_count / 10) +
            0.3 * min(1.0, effects_count / 5) +
            0.3 * min(1.0, transitions_count / 3)
        )
        
        return complexity
    
    def _split_scene(self, scene: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        将复杂场景分解为两个场景
        
        Args:
            scene: 原始场景
            
        Returns:
            分解后的两个场景
        """
        # 创建两个新场景
        scene1 = copy.deepcopy(scene)
        scene2 = copy.deepcopy(scene)
        
        # 分配元素
        if "elements" in scene and isinstance(scene["elements"], list):
            elements = scene["elements"]
            mid = len(elements) // 2
            
            scene1["elements"] = elements[:mid]
            scene2["elements"] = elements[mid:]
        
        # 分配特效
        if "effects" in scene and isinstance(scene["effects"], list):
            effects = scene["effects"]
            mid = len(effects) // 2
            
            scene1["effects"] = effects[:mid]
            scene2["effects"] = effects[mid:]
        
        # 调整持续时间
        if "duration" in scene:
            duration = scene["duration"]
            scene1["duration"] = duration / 2
            scene2["duration"] = duration / 2
        
        # 设置描述
        if "description" in scene:
            desc = scene["description"]
            scene1["description"] = f"{desc} (第一部分)"
            scene2["description"] = f"{desc} (第二部分)"
        
        return scene1, scene2
    
    def _reduce_transitions(self, content: Dict[str, Any], intensity: float) -> Dict[str, Any]:
        """
        减少转场和特效
        
        减少不必要的视觉干扰
        
        Args:
            content: 内容数据
            intensity: 简化强度
            
        Returns:
            简化后的内容
        """
        result = copy.deepcopy(content)
        
        # 设置保留比例
        retention_ratio = max(0.3, 1.0 - intensity * 0.7)
        
        # 处理场景转场和特效
        if "scenes" in result and isinstance(result["scenes"], list):
            for scene in result["scenes"]:
                # 简化转场
                if "transitions" in scene and isinstance(scene["transitions"], list):
                    transitions = scene["transitions"]
                    transitions_to_keep = max(1, int(len(transitions) * retention_ratio))
                    
                    # 按重要性排序
                    transitions_with_importance = []
                    for transition in transitions:
                        importance = transition.get("importance", 0.5)
                        transitions_with_importance.append((transition, importance))
                    
                    transitions_with_importance.sort(key=lambda x: x[1], reverse=True)
                    scene["transitions"] = [t[0] for t in transitions_with_importance[:transitions_to_keep]]
                
                # 简化特效
                if "effects" in scene and isinstance(scene["effects"], list):
                    effects = scene["effects"]
                    effects_to_keep = max(1, int(len(effects) * retention_ratio))
                    
                    # 按重要性排序
                    effects_with_importance = []
                    for effect in effects:
                        importance = effect.get("importance", 0.5)
                        effects_with_importance.append((effect, importance))
                    
                    effects_with_importance.sort(key=lambda x: x[1], reverse=True)
                    scene["effects"] = [e[0] for e in effects_with_importance[:effects_to_keep]]
        
        return result
    
    def _prioritize_essential_content(self, content: Dict[str, Any], intensity: float) -> Dict[str, Any]:
        """
        优先保留核心内容
        
        移除次要内容，突出关键信息
        
        Args:
            content: 内容数据
            intensity: 简化强度
            
        Returns:
            简化后的内容
        """
        result = copy.deepcopy(content)
        
        # 根据重要性对场景排序
        if "scenes" in result and isinstance(result["scenes"], list):
            scenes = result["scenes"]
            
            # 计算每个场景的重要性
            scenes_with_importance = []
            for scene in scenes:
                # 默认重要性
                importance = scene.get("importance", 0.5)
                
                # 如果有关键信息标记，提高重要性
                if scene.get("has_key_information", False):
                    importance = max(0.8, importance)
                
                # 如果有情感高潮，提高重要性
                if scene.get("emotional_peak", False):
                    importance = max(0.7, importance)
                
                scenes_with_importance.append((scene, importance))
            
            # 按重要性排序
            scenes_with_importance.sort(key=lambda x: x[1], reverse=True)
            
            # 计算保留场景数量
            min_scenes = max(3, int(len(scenes) * 0.5))  # 至少保留50%或3个场景
            scenes_to_keep = max(min_scenes, int(len(scenes) * (1.0 - intensity * 0.5)))
            
            # 保留重要场景
            result["scenes"] = [s[0] for s in scenes_with_importance[:scenes_to_keep]]
        
        return result


# 创建单例对象
_cognitive_optimizer = None

def get_cognitive_optimizer() -> CognitiveLoadBalancer:
    """
    获取认知负荷优化器实例
    
    Returns:
        CognitiveLoadBalancer: 认知负荷优化器实例
    """
    global _cognitive_optimizer
    if _cognitive_optimizer is None:
        _cognitive_optimizer = CognitiveLoadBalancer()
    return _cognitive_optimizer

def optimize_content(content: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    优化内容认知负荷的便捷函数
    
    Args:
        content: 需要优化的内容
        user_profile: 用户画像
        
    Returns:
        优化后的内容
    """
    optimizer = get_cognitive_optimizer()
    return optimizer.optimize(content, user_profile)

def calculate_cognitive_load(content: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None) -> float:
    """
    计算内容认知负荷分数的便捷函数
    
    Args:
        content: 内容数据
        user_profile: 用户画像
        
    Returns:
        认知负荷分数
    """
    optimizer = get_cognitive_optimizer()
    return optimizer._calculate_load(content, user_profile) 