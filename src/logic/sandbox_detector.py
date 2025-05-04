#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
逻辑漏洞沙盒检测模块

提供用于检测脚本中逻辑漏洞和不一致性的工具，通过模拟插入缺陷并检测其影响来评估脚本逻辑的稳健性。
"""

import logging
import random
import json
import os
import copy
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
except ImportError:
    logging.warning("无法导入完整的异常处理模块，将使用基础异常类")
    
    class ErrorCode:
        LOGIC_SANDBOX_ERROR = 1800
    
    class ClipMasterError(Exception):
        def __init__(self, message, code=None, details=None):
            self.message = message
            self.code = code
            self.details = details or {}
            super().__init__(message)

# 配置日志
logger = logging.getLogger(__name__)


class LogicDefectType(Enum):
    """逻辑缺陷类型"""
    TIME_JUMP = auto()          # 时间跳跃：场景时间线异常跳跃
    PROP_TELEPORT = auto()      # 道具传送：道具无故出现或消失
    CHARACTER_CLONE = auto()    # 角色分身：角色同时出现在不同场景
    CHARACTER_SWAP = auto()     # 角色互换：角色特征/性格突然互换
    CAUSALITY_BREAK = auto()    # 因果断裂：事件因果关系断裂
    DIALOGUE_MISMATCH = auto()  # 对话错位：人物对话与角色设定不符
    EMOTION_FLIP = auto()       # 情感翻转：情感突然不合理转变
    KNOWLEDGE_ERROR = auto()    # 知识错误：常识性错误或专业知识错误
    CONSTRAINT_BREAK = auto()   # 约束违反：违反物理或世界观规则
    MOTIVATION_LOSS = auto()    # 动机丢失：角色行为失去合理动机


class LogicSandboxError(ClipMasterError):
    """逻辑沙盒错误异常
    
    当检测到逻辑沙盒错误时抛出。
    """
    
    def __init__(self, message: str, defect_type: LogicDefectType, 
                 details: Optional[Dict[str, Any]] = None):
        """初始化逻辑沙盒错误异常
        
        Args:
            message: 错误信息
            defect_type: 缺陷类型
            details: 详细信息，包含错误的具体描述
        """
        super().__init__(
            message,
            code=ErrorCode.LOGIC_SANDBOX_ERROR,
            details=details or {"defect_type": defect_type.name}
        )
        self.defect_type = defect_type


@dataclass
class LogicDefect:
    """逻辑缺陷
    
    表示脚本中可能的逻辑缺陷。
    """
    defect_type: LogicDefectType          # 缺陷类型
    description: str                      # 缺陷描述
    scene_index: int = -1                 # 缺陷所在场景索引（-1表示全局缺陷）
    confidence: float = 1.0               # 缺陷检测置信度
    severity: str = "medium"              # 缺陷严重程度 (low, medium, high, critical)
    suggested_fix: Optional[str] = None   # 建议修复方法


class LogicSandbox:
    """逻辑沙盒
    
    用于检测脚本中的逻辑漏洞，通过向脚本中注入缺陷测试检测能力。
    """
    
    def __init__(self):
        """初始化逻辑沙盒"""
        # 注册内置缺陷注入器
        self.defect_injectors = {
            LogicDefectType.TIME_JUMP: self._inject_time_jump,
            LogicDefectType.PROP_TELEPORT: self._inject_prop_teleport,
            LogicDefectType.CHARACTER_CLONE: self._inject_character_clone,
            LogicDefectType.CAUSALITY_BREAK: self._inject_causality_break,
            LogicDefectType.DIALOGUE_MISMATCH: self._inject_dialogue_mismatch,
            LogicDefectType.EMOTION_FLIP: self._inject_emotion_flip
        }
        
        # 注册内置缺陷检测器
        self.defect_detectors = {
            LogicDefectType.TIME_JUMP: self._detect_time_jump,
            LogicDefectType.PROP_TELEPORT: self._detect_prop_teleport,
            LogicDefectType.CHARACTER_CLONE: self._detect_character_clone,
            LogicDefectType.CAUSALITY_BREAK: self._detect_causality_break,
            LogicDefectType.DIALOGUE_MISMATCH: self._detect_dialogue_mismatch,
            LogicDefectType.EMOTION_FLIP: self._detect_emotion_flip
        }
        
        # 初始化配置参数
        self.config = {
            "detection_threshold": 0.7,  # 缺陷检测阈值
            "severity_weights": {        # 不同严重程度的权重
                "low": 0.5,
                "medium": 1.0,
                "high": 1.5,
                "critical": 2.0
            }
        }
    
    def stress_test(self, script: Dict[str, Any]) -> float:
        """注入50种典型逻辑错问题进行压力测试
        
        Args:
            script: 待测试的脚本
            
        Returns:
            漏洞检出率，越高越好
        """
        test_cases = [
            {"type": "TIME_JUMP", "value": -300},      # 时间倒流
            {"type": "PROP_TELEPORT", "item": "宝剑"},  # 道具瞬移
            {"type": "CHARACTER_CLONE"}                # 角色分身
        ]
        
        detection_rate = 0
        for case in test_cases:
            corrupted_script = self.inject_defect(script, case)
            if self.detect_defects(corrupted_script):
                detection_rate += 1
                
        return detection_rate / len(test_cases)  # 返回漏洞检出率
    
    def inject_defect(self, script: Dict[str, Any], defect_config: Dict[str, Any]) -> Dict[str, Any]:
        """向脚本中注入缺陷
        
        Args:
            script: 原始脚本
            defect_config: 缺陷配置，包含类型和相关参数
            
        Returns:
            注入缺陷后的脚本副本
        """
        # 创建脚本副本，避免修改原始脚本
        script_copy = copy.deepcopy(script)
        
        # 解析缺陷类型
        defect_type_str = defect_config.get("type", "").upper()
        try:
            # 尝试将字符串映射到枚举
            defect_type = next(t for t in LogicDefectType 
                              if t.name == defect_type_str)
        except StopIteration:
            # 找不到对应的缺陷类型
            logger.warning(f"未知的缺陷类型: {defect_type_str}")
            return script_copy
        
        # 调用对应的缺陷注入器
        if defect_type in self.defect_injectors:
            try:
                result = self.defect_injectors[defect_type](script_copy, defect_config)
                logger.info(f"已注入缺陷: {defect_type.name}")
                return result
            except Exception as e:
                logger.error(f"注入缺陷失败: {e}")
                return script_copy
        else:
            logger.warning(f"没有找到缺陷类型 {defect_type.name} 的注入器")
            return script_copy
    
    def detect_defects(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测脚本中的逻辑缺陷
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的缺陷列表
        """
        defects = []
        
        # 运行所有注册的缺陷检测器
        for defect_type, detector in self.defect_detectors.items():
            try:
                defect_results = detector(script)
                if defect_results:
                    # 过滤低于检测阈值的缺陷
                    filtered_defects = [d for d in defect_results 
                                       if d.confidence >= self.config["detection_threshold"]]
                    defects.extend(filtered_defects)
            except Exception as e:
                logger.error(f"运行缺陷检测器 {defect_type.name} 时出错: {e}")
        
        return defects
    
    # ===== 缺陷注入方法 =====
    
    def _inject_time_jump(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入时间跳跃缺陷
        
        在时间线上创建不合理的跳跃，如时间倒流或大幅度跳跃
        
        Args:
            script: 原始脚本
            config: 缺陷配置参数
            
        Returns:
            注入缺陷后的脚本
        """
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return script
        
        # 获取跳跃值，正值为向前跳跃，负值为时间倒流
        jump_value = config.get("value", 1000)  # 默认跳跃1000ms
        
        # 随机选择一个场景进行修改
        scene_idx = random.randint(1, len(scenes) - 1)
        
        # 如果场景有时间戳，修改其值造成跳跃
        if "timestamp" in scenes[scene_idx]:
            # 计算新时间戳，确保不为负数
            original_time = scenes[scene_idx]["timestamp"]
            new_time = max(0, original_time + jump_value)
            scenes[scene_idx]["timestamp"] = new_time
            
            # 记录注入的缺陷
            if "_injected_defects" not in script:
                script["_injected_defects"] = []
                
            script["_injected_defects"].append({
                "type": LogicDefectType.TIME_JUMP.name,
                "scene_index": scene_idx,
                "original_value": original_time,
                "new_value": new_time,
                "description": f"在场景 {scene_idx} 中注入时间跳跃，从 {original_time} 到 {new_time}"
            })
        
        return script
    
    def _inject_prop_teleport(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入道具传送缺陷
        
        使道具无缘由地出现或消失
        
        Args:
            script: 原始脚本
            config: 缺陷配置参数
            
        Returns:
            注入缺陷后的脚本
        """
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return script
        
        # 获取要操作的道具名称
        item_name = config.get("item", "")
        if not item_name:
            # 如果未指定道具，尝试从脚本中提取一个
            for scene in scenes:
                props = scene.get("props", [])
                if props:
                    if isinstance(props[0], str):
                        item_name = props[0]
                    elif isinstance(props[0], dict) and "name" in props[0]:
                        item_name = props[0]["name"]
                    break
        
        if not item_name:
            logger.warning("无法注入道具传送缺陷：找不到合适的道具")
            return script
            
        # 随机选择一个场景
        scene_idx = random.randint(0, len(scenes) - 1)
        
        # 根据场景当前状态决定是添加还是移除道具
        props = scenes[scene_idx].get("props", [])
        prop_exists = False
        
        # 检查道具是否已存在
        for i, prop in enumerate(props):
            if (isinstance(prop, str) and prop == item_name) or \
               (isinstance(prop, dict) and prop.get("name") == item_name):
                prop_exists = True
                # 移除道具
                props.pop(i)
                action = "removed"
                break
        
        # 如果道具不存在，添加它
        if not prop_exists:
            if not props:
                scenes[scene_idx]["props"] = []
                props = scenes[scene_idx]["props"]
            
            if all(isinstance(p, str) for p in props):
                props.append(item_name)
            else:
                props.append({"name": item_name, "state": "appeared"})
            action = "added"
        
        # 记录注入的缺陷
        if "_injected_defects" not in script:
            script["_injected_defects"] = []
            
        script["_injected_defects"].append({
            "type": LogicDefectType.PROP_TELEPORT.name,
            "scene_index": scene_idx,
            "item": item_name,
            "action": action,
            "description": f"在场景 {scene_idx} 中{action}道具 '{item_name}'"
        })
        
        return script
    
    def _inject_character_clone(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入角色分身缺陷
        
        让一个角色同时出现在两个连续的场景中，而这在物理上是不可能的
        
        Args:
            script: 原始脚本
            config: 缺陷配置参数
            
        Returns:
            注入缺陷后的脚本
        """
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 3:
            return script
        
        # 尝试找到一个适合克隆的角色
        character_name = config.get("character", "")
        if not character_name:
            # 如果未指定角色，尝试从脚本中提取一个
            for scene in scenes:
                characters = scene.get("characters", [])
                if characters:
                    if isinstance(characters[0], str):
                        character_name = characters[0]
                    elif isinstance(characters[0], dict) and "name" in characters[0]:
                        character_name = characters[0]["name"]
                    break
        
        if not character_name:
            logger.warning("无法注入角色分身缺陷：找不到合适的角色")
            return script
            
        # 找到两个远距离场景，让角色同时出现
        # 先找一个角色出现的场景
        character_scenes = []
        for i, scene in enumerate(scenes):
            characters = scene.get("characters", [])
            character_exists = False
            
            for char in characters:
                if (isinstance(char, str) and char == character_name) or \
                   (isinstance(char, dict) and char.get("name") == character_name):
                    character_exists = True
                    character_scenes.append(i)
                    break
        
        if not character_scenes:
            logger.warning(f"找不到角色 '{character_name}' 出现的场景")
            return script
            
        # 选择一个角色出现的场景，和一个远距离场景
        source_scene_idx = random.choice(character_scenes)
        
        # 找一个远距离场景（至少间隔2个场景）
        possible_targets = [i for i in range(len(scenes)) 
                           if i not in character_scenes and abs(i - source_scene_idx) >= 2]
        
        if not possible_targets:
            logger.warning("找不到合适的远距离场景进行角色分身")
            return script
            
        target_scene_idx = random.choice(possible_targets)
        
        # 在目标场景中添加角色
        target_scene = scenes[target_scene_idx]
        if "characters" not in target_scene:
            target_scene["characters"] = []
            
        characters = target_scene["characters"]
        
        if all(isinstance(c, str) for c in characters):
            characters.append(character_name)
        else:
            characters.append({"name": character_name})
            
        # 确保两个场景的时间戳相近（如果有时间戳）
        if "timestamp" in scenes[source_scene_idx] and "timestamp" in target_scene:
            # 将目标场景时间设置为接近源场景
            target_scene["timestamp"] = scenes[source_scene_idx]["timestamp"] + random.randint(5, 30)
        
        # 记录注入的缺陷
        if "_injected_defects" not in script:
            script["_injected_defects"] = []
            
        script["_injected_defects"].append({
            "type": LogicDefectType.CHARACTER_CLONE.name,
            "character": character_name,
            "source_scene": source_scene_idx,
            "target_scene": target_scene_idx,
            "description": f"角色 '{character_name}' 同时出现在场景 {source_scene_idx} 和 {target_scene_idx}"
        })
        
        return script
    
    def _inject_causality_break(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入因果断裂缺陷
        
        打破事件之间的因果关系，如结果出现在原因之前
        
        Args:
            script: 原始脚本
            config: 缺陷配置参数
            
        Returns:
            注入缺陷后的脚本
        """
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 3:
            return script
        
        # 尝试找到一对因果关系场景
        cause_scene_idx = -1
        effect_scene_idx = -1
        
        # 检查场景中的因果关系标记
        for i, scene in enumerate(scenes):
            if i < len(scenes) - 1:  # 跳过最后一个场景
                # 检查当前场景是否被标记为原因
                if scene.get("is_cause") or "cause_for" in scene:
                    # 找到对应的结果场景
                    effect_id = scene.get("cause_for")
                    if effect_id:
                        for j, effect_scene in enumerate(scenes):
                            if effect_scene.get("id") == effect_id:
                                cause_scene_idx = i
                                effect_scene_idx = j
                                break
                
                # 如果没找到标记的因果关系，尝试推断
                if cause_scene_idx == -1 and i + 1 < len(scenes):
                    # 简单假设相邻场景可能有因果关系
                    if random.random() < 0.7:  # 70% 的概率选择
                        cause_scene_idx = i
                        effect_scene_idx = i + 1
        
        # 如果找不到因果关系，随机选择两个场景
        if cause_scene_idx == -1:
            indices = list(range(len(scenes)))
            if len(indices) >= 2:
                random.shuffle(indices)
                cause_scene_idx, effect_scene_idx = indices[:2]
        
        # 交换因果场景的位置
        if 0 <= cause_scene_idx < len(scenes) and 0 <= effect_scene_idx < len(scenes):
            if cause_scene_idx < effect_scene_idx:  # 只有原因在前，结果在后才需要交换
                scenes[cause_scene_idx], scenes[effect_scene_idx] = scenes[effect_scene_idx], scenes[cause_scene_idx]
                
                # 记录注入的缺陷
                if "_injected_defects" not in script:
                    script["_injected_defects"] = []
                    
                script["_injected_defects"].append({
                    "type": LogicDefectType.CAUSALITY_BREAK.name,
                    "original_cause_idx": cause_scene_idx,
                    "original_effect_idx": effect_scene_idx,
                    "new_cause_idx": effect_scene_idx,
                    "new_effect_idx": cause_scene_idx,
                    "description": f"交换了因果场景的位置，原场景 {cause_scene_idx} (原因) 和场景 {effect_scene_idx} (结果)"
                })
        
        return script
    
    def _inject_dialogue_mismatch(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入对话错位缺陷
        
        使角色的对话与其性格/身份不符
        
        Args:
            script: 原始脚本
            config: 缺陷配置参数
            
        Returns:
            注入缺陷后的脚本
        """
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes:
            return script
        
        # 尝试找到包含对话的场景
        dialogue_scenes = []
        for i, scene in enumerate(scenes):
            if "dialogue" in scene or "dialogues" in scene:
                dialogue_scenes.append(i)
        
        if not dialogue_scenes:
            logger.warning("找不到包含对话的场景")
            return script
            
        # 随机选择一个有对话的场景
        scene_idx = random.choice(dialogue_scenes)
        scene = scenes[scene_idx]
        
        # 获取场景中的对话
        dialogues = scene.get("dialogues", [])
        if not dialogues:
            dialogues = scene.get("dialogue", [])
            if isinstance(dialogues, str):
                logger.warning("对话格式不是列表，无法注入对话错位缺陷")
                return script
        
        if not dialogues:
            logger.warning("选中的场景没有对话内容")
            return script
            
        # 如果对话是字典列表，找出角色和对话内容
        if isinstance(dialogues[0], dict):
            character_dialogues = {}
            for d in dialogues:
                if "character" in d and "text" in d:
                    character = d["character"]
                    if character not in character_dialogues:
                        character_dialogues[character] = []
                    character_dialogues[character].append(d)
            
            # 至少需要两个角色才能交换对话
            if len(character_dialogues) < 2:
                logger.warning("场景中角色不足，无法注入对话错位缺陷")
                return script
                
            # 选择两个角色交换一句对话
            characters = list(character_dialogues.keys())
            char1, char2 = random.sample(characters, 2)
            
            if character_dialogues[char1] and character_dialogues[char2]:
                # 随机选择一句对话进行交换
                dialog1 = random.choice(character_dialogues[char1])
                dialog2 = random.choice(character_dialogues[char2])
                
                # 交换对话文本
                dialog1_text = dialog1["text"]
                dialog1["text"] = dialog2["text"]
                dialog2["text"] = dialog1_text
                
                # 记录注入的缺陷
                if "_injected_defects" not in script:
                    script["_injected_defects"] = []
                    
                script["_injected_defects"].append({
                    "type": LogicDefectType.DIALOGUE_MISMATCH.name,
                    "scene_index": scene_idx,
                    "character1": char1,
                    "character2": char2,
                    "description": f"在场景 {scene_idx} 中交换了角色 '{char1}' 和 '{char2}' 的对话"
                })
        
        return script
    
    def _inject_emotion_flip(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入情感翻转缺陷
        
        使角色的情感状态突然不合理地转变
        
        Args:
            script: 原始脚本
            config: 缺陷配置参数
            
        Returns:
            注入缺陷后的脚本
        """
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return script
        
        # 获取要操作的角色名称
        character_name = config.get("character", "")
        if not character_name:
            # 如果未指定角色，尝试从脚本中提取一个
            for scene in scenes:
                characters = scene.get("characters", [])
                if characters:
                    if isinstance(characters[0], str):
                        character_name = characters[0]
                    elif isinstance(characters[0], dict) and "name" in characters[0]:
                        character_name = characters[0]["name"]
                    break
        
        if not character_name:
            logger.warning("无法注入情感翻转缺陷：找不到合适的角色")
            return script
            
        # 尝试找到角色出现的连续场景
        character_scenes = []
        for i, scene in enumerate(scenes):
            characters = scene.get("characters", [])
            character_exists = False
            
            for char in characters:
                if (isinstance(char, str) and char == character_name) or \
                   (isinstance(char, dict) and char.get("name") == character_name):
                    character_exists = True
                    character_scenes.append(i)
                    break
        
        # 需要至少两个连续的场景
        consecutive_scenes = []
        for i in range(len(character_scenes) - 1):
            if character_scenes[i+1] - character_scenes[i] == 1:
                consecutive_scenes.append((character_scenes[i], character_scenes[i+1]))
        
        if not consecutive_scenes:
            logger.warning(f"找不到角色 '{character_name}' 出现的连续场景")
            return script
            
        # 随机选择一对连续场景
        scene1_idx, scene2_idx = random.choice(consecutive_scenes)
        
        # 获取场景中的情感信息
        scene1 = scenes[scene1_idx]
        scene2 = scenes[scene2_idx]
        
        # 如果场景有情感数据，进行极端反转
        if "emotion" in scene1 or "sentiment" in scene1:
            emotion_key = "emotion" if "emotion" in scene1 else "sentiment"
            
            # 获取原始情感
            original_emotion = scene1.get(emotion_key)
            
            # 为第二个场景设置极端相反的情感
            if isinstance(original_emotion, (int, float)):
                # 数值型情感，取反并增强
                scene2[emotion_key] = -original_emotion * 1.5
            elif isinstance(original_emotion, str):
                # 字符串型情感，设置为相反情感
                emotion_pairs = {
                    "happy": "sad", "sad": "happy",
                    "angry": "calm", "calm": "angry",
                    "fear": "confidence", "confidence": "fear",
                    "positive": "negative", "negative": "positive"
                }
                scene2[emotion_key] = emotion_pairs.get(original_emotion.lower(), "extreme_opposite")
            
            # 记录注入的缺陷
            if "_injected_defects" not in script:
                script["_injected_defects"] = []
                
            script["_injected_defects"].append({
                "type": LogicDefectType.EMOTION_FLIP.name,
                "character": character_name,
                "scene1_idx": scene1_idx,
                "scene2_idx": scene2_idx,
                "original_emotion": original_emotion,
                "new_emotion": scene2.get(emotion_key),
                "description": f"角色 '{character_name}' 在场景 {scene1_idx} 和 {scene2_idx} 之间情感突然翻转"
            })
        
        return script
    
    def _detect_time_jump(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测时间跳跃缺陷
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的缺陷列表
        """
        defects = []
        
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return defects
            
        # 检查时间戳序列
        prev_timestamp = None
        for i, scene in enumerate(scenes):
            if "timestamp" in scene:
                current_timestamp = scene["timestamp"]
                
                if prev_timestamp is not None:
                    # 检查是否有时间倒流
                    if current_timestamp < prev_timestamp:
                        defects.append(LogicDefect(
                            defect_type=LogicDefectType.TIME_JUMP,
                            description=f"场景 {i} 的时间戳 ({current_timestamp}) 早于前一个场景 ({prev_timestamp})，可能存在时间倒流",
                            scene_index=i,
                            confidence=0.9,
                            severity="high",
                            suggested_fix=f"调整场景 {i} 的时间戳，确保不早于前一个场景"
                        ))
                    # 检查是否有不合理的大跳跃
                    elif current_timestamp - prev_timestamp > 10000:  # 假设超过10秒的跳跃是可疑的
                        defects.append(LogicDefect(
                            defect_type=LogicDefectType.TIME_JUMP,
                            description=f"场景 {i} 与前一个场景间存在较大时间跳跃 ({current_timestamp - prev_timestamp}ms)",
                            scene_index=i,
                            confidence=0.7,  # 较低的置信度，因为大跳跃可能是有意的
                            severity="medium",
                            suggested_fix="考虑在两个场景之间添加过渡场景解释时间跳跃"
                        ))
                
                prev_timestamp = current_timestamp
        
        return defects
    
    def _detect_prop_teleport(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测道具传送缺陷
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的缺陷列表
        """
        defects = []
        
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return defects
            
        # 跟踪每个道具的出现和消失
        props_tracker = {}  # {prop_name: [scene_indices]}
        
        # 构建道具跟踪数据
        for i, scene in enumerate(scenes):
            props = scene.get("props", [])
            
            # 提取道具名称
            current_props = set()
            for prop in props:
                if isinstance(prop, str):
                    current_props.add(prop)
                elif isinstance(prop, dict) and "name" in prop:
                    current_props.add(prop["name"])
            
            # 更新道具跟踪器
            for prop_name in current_props:
                if prop_name not in props_tracker:
                    props_tracker[prop_name] = []
                props_tracker[prop_name].append(i)
        
        # 检查每个道具的出现模式
        for prop_name, occurrences in props_tracker.items():
            if len(occurrences) >= 2:
                # 检查道具是否消失后又重新出现
                for j in range(1, len(occurrences)):
                    gap = occurrences[j] - occurrences[j-1]
                    if gap > 1:  # 如果不是连续场景
                        # 检查是否有交代道具去向的场景
                        explanation_found = False
                        
                        # 这里可以添加更复杂的逻辑检查道具去向是否有交代
                        # 简化版本：检查道具状态是否标记为"lost"或"given"等
                        for scene_idx in range(occurrences[j-1], occurrences[j]):
                            scene = scenes[scene_idx]
                            props = scene.get("props", [])
                            for prop in props:
                                if isinstance(prop, dict) and prop.get("name") == prop_name:
                                    state = prop.get("state", "")
                                    if state in ["lost", "given", "hidden", "destroyed"]:
                                        explanation_found = True
                                        break
                        
                        if not explanation_found:
                            defects.append(LogicDefect(
                                defect_type=LogicDefectType.PROP_TELEPORT,
                                description=f"道具 '{prop_name}' 在场景 {occurrences[j-1]} 后消失，又在场景 {occurrences[j]} 重新出现，中间没有交代",
                                scene_index=occurrences[j],
                                confidence=0.85,
                                severity="medium",
                                suggested_fix=f"在场景之间添加对道具 '{prop_name}' 去向的交代"
                            ))
        
        return defects
    
    def _detect_character_clone(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测角色分身缺陷
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的缺陷列表
        """
        defects = []
        
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return defects
            
        # 跟踪角色在每个场景的出现情况
        character_tracker = {}  # {character_name: [scene_indices]}
        
        # 构建角色跟踪数据
        for i, scene in enumerate(scenes):
            characters = scene.get("characters", [])
            
            # 提取角色名称
            current_characters = set()
            for character in characters:
                if isinstance(character, str):
                    current_characters.add(character)
                elif isinstance(character, dict) and "name" in character:
                    current_characters.add(character["name"])
            
            # 更新角色跟踪器
            for char_name in current_characters:
                if char_name not in character_tracker:
                    character_tracker[char_name] = []
                character_tracker[char_name].append({
                    "scene_idx": i,
                    "timestamp": scene.get("timestamp", i * 1000)  # 使用时间戳或默认值
                })
        
        # 检查每个角色是否出现分身情况
        for char_name, appearances in character_tracker.items():
            if len(appearances) >= 2:
                # 按时间戳排序
                sorted_appearances = sorted(appearances, key=lambda x: x["timestamp"])
                
                for j in range(1, len(sorted_appearances)):
                    current = sorted_appearances[j]
                    previous = sorted_appearances[j-1]
                    
                    # 检查时间戳是否过近（角色无法在短时间内出现在不同场景）
                    time_diff = current["timestamp"] - previous["timestamp"]
                    scene_diff = abs(current["scene_idx"] - previous["scene_idx"])
                    
                    # 场景序号相差大但时间相近，可能是分身
                    if scene_diff > 1 and time_diff < 100:  # 100ms内出现在不同场景
                        defects.append(LogicDefect(
                            defect_type=LogicDefectType.CHARACTER_CLONE,
                            description=f"角色 '{char_name}' 在场景 {previous['scene_idx']} 和 {current['scene_idx']} 同时出现，时间差仅 {time_diff}ms",
                            scene_index=current["scene_idx"],
                            confidence=0.9,
                            severity="high",
                            suggested_fix=f"调整角色 '{char_name}' 的出场安排，或延长场景之间的时间间隔"
                        ))
        
        return defects
    
    def _detect_causality_break(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测因果断裂缺陷
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的缺陷列表
        """
        defects = []
        
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return defects
            
        # 查找有明确因果关联的场景对
        causal_pairs = []
        
        for i, scene in enumerate(scenes):
            # 检查是否有明确的因果标记
            if "cause_for" in scene:
                effect_id = scene["cause_for"]
                for j, effect_scene in enumerate(scenes):
                    if effect_scene.get("id") == effect_id:
                        causal_pairs.append({
                            "cause_idx": i,
                            "effect_idx": j,
                            "explicit": True
                        })
            
            # 检查场景中是否有事件标记
            events = scene.get("events", [])
            for event in events:
                if isinstance(event, dict):
                    # 检查事件是否有因果关系标记
                    if "causes" in event:
                        effect_event = event["causes"]
                        # 寻找包含这个事件的场景
                        for j, effect_scene in enumerate(scenes):
                            effect_events = effect_scene.get("events", [])
                            for e_event in effect_events:
                                if isinstance(e_event, dict) and e_event.get("id") == effect_event:
                                    causal_pairs.append({
                                        "cause_idx": i,
                                        "effect_idx": j,
                                        "explicit": True
                                    })
        
        # 检查因果关系的时序
        for pair in causal_pairs:
            cause_idx = pair["cause_idx"]
            effect_idx = pair["effect_idx"]
            
            # 因在后，果在前，明显违反因果关系
            if cause_idx > effect_idx:
                defects.append(LogicDefect(
                    defect_type=LogicDefectType.CAUSALITY_BREAK,
                    description=f"因果关系倒置：场景 {effect_idx} (结果) 出现在场景 {cause_idx} (原因) 之前",
                    scene_index=effect_idx,
                    confidence=0.95,
                    severity="critical",
                    suggested_fix=f"调整场景顺序，确保场景 {cause_idx} (原因) 出现在场景 {effect_idx} (结果) 之前"
                ))
            
            # 如果有时间戳，检查时间戳的合理性
            cause_scene = scenes[cause_idx]
            effect_scene = scenes[effect_idx]
            
            if "timestamp" in cause_scene and "timestamp" in effect_scene:
                cause_time = cause_scene["timestamp"]
                effect_time = effect_scene["timestamp"]
                
                if effect_time <= cause_time:
                    defects.append(LogicDefect(
                        defect_type=LogicDefectType.CAUSALITY_BREAK,
                        description=f"时间上的因果矛盾：场景 {effect_idx} 的时间戳不晚于场景 {cause_idx}",
                        scene_index=effect_idx,
                        confidence=0.9,
                        severity="high",
                        suggested_fix=f"调整场景 {effect_idx} 的时间戳，确保晚于场景 {cause_idx}"
                    ))
        
        return defects
    
    def _detect_dialogue_mismatch(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测对话错位缺陷
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的缺陷列表
        """
        defects = []
        
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes:
            return defects
            
        # 首先构建角色特征/性格模型
        character_profiles = {}  # {character_name: {traits, style, keywords}}
        
        # 提取角色信息
        for scene in scenes:
            characters = scene.get("characters", [])
            for character in characters:
                if isinstance(character, dict) and "name" in character:
                    char_name = character["name"]
                    
                    # 如果角色未记录，初始化
                    if char_name not in character_profiles:
                        character_profiles[char_name] = {
                            "traits": character.get("traits", []),
                            "style": character.get("speech_style", ""),
                            "keywords": set(),
                            "emotions": []
                        }
                    
                    # 更新角色特征
                    if "traits" in character and character_profiles[char_name]["traits"] == []:
                        character_profiles[char_name]["traits"] = character["traits"]
                    
                    if "speech_style" in character and character_profiles[char_name]["style"] == "":
                        character_profiles[char_name]["style"] = character["speech_style"]
        
        # 分析每个场景的对话，更新角色特征
        for scene in scenes:
            dialogues = scene.get("dialogues", [])
            if not dialogues:
                dialogues = scene.get("dialogue", [])
                if isinstance(dialogues, str):
                    continue  # 不处理单一字符串对话
            
            # 分析对话内容
            for dialogue in dialogues:
                if isinstance(dialogue, dict) and "character" in dialogue and "text" in dialogue:
                    char_name = dialogue["character"]
                    text = dialogue["text"]
                    
                    if char_name in character_profiles:
                        # 提取关键词
                        words = text.lower().split()
                        character_profiles[char_name]["keywords"].update(words)
                        
                        # 提取情感
                        emotion = dialogue.get("emotion", "")
                        if emotion:
                            character_profiles[char_name]["emotions"].append(emotion)
        
        # 检查对话是否与角色特征/风格一致
        for i, scene in enumerate(scenes):
            dialogues = scene.get("dialogues", [])
            if not dialogues:
                dialogues = scene.get("dialogue", [])
                if isinstance(dialogues, str):
                    continue
            
            for dialogue in dialogues:
                if isinstance(dialogue, dict) and "character" in dialogue and "text" in dialogue:
                    char_name = dialogue["character"]
                    text = dialogue["text"]
                    
                    if char_name in character_profiles:
                        profile = character_profiles[char_name]
                        
                        # 检查对话风格是否匹配
                        style_mismatch = False
                        if profile["style"]:
                            # 简单检查，实际应用中可能需要更复杂的NLP分析
                            style = profile["style"].lower()
                            if style == "formal" and ("ain't" in text.lower() or "gonna" in text.lower()):
                                style_mismatch = True
                            elif style == "casual" and all(w not in text.lower() for w in ["hey", "cool", "ok", "yeah"]):
                                style_mismatch = True
                        
                        if style_mismatch:
                            defects.append(LogicDefect(
                                defect_type=LogicDefectType.DIALOGUE_MISMATCH,
                                description=f"场景 {i} 中角色 '{char_name}' 的对话风格与其设定不符",
                                scene_index=i,
                                confidence=0.7,
                                severity="medium",
                                suggested_fix=f"调整角色 '{char_name}' 的对话，使其符合 '{profile['style']}' 的说话风格"
                            ))
        
        return defects
    
    def _detect_emotion_flip(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测情感翻转缺陷
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的缺陷列表
        """
        defects = []
        
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return defects
            
        # 跟踪角色的情感变化
        character_emotions = {}  # {character_name: [{scene_idx, emotion}]}
        
        # 提取场景中的情感信息
        for i, scene in enumerate(scenes):
            # 获取场景的整体情感基调
            scene_emotion = scene.get("emotion", scene.get("sentiment", None))
            
            # 提取角色及其情感
            characters = scene.get("characters", [])
            for character in characters:
                char_name = character if isinstance(character, str) else character.get("name", "")
                if not char_name:
                    continue
                
                # 获取角色的情感
                char_emotion = None
                if isinstance(character, dict) and "emotion" in character:
                    char_emotion = character["emotion"]
                elif "dialogues" in scene:
                    # 从对话中提取情感
                    for dialogue in scene["dialogues"]:
                        if isinstance(dialogue, dict) and dialogue.get("character") == char_name and "emotion" in dialogue:
                            char_emotion = dialogue["emotion"]
                            break
                
                # 如果没有角色特定情感，使用场景情感
                if char_emotion is None:
                    char_emotion = scene_emotion
                
                if char_emotion is not None:
                    if char_name not in character_emotions:
                        character_emotions[char_name] = []
                    
                    character_emotions[char_name].append({
                        "scene_idx": i,
                        "emotion": char_emotion
                    })
        
        # 检查情感变化是否合理
        for char_name, emotions in character_emotions.items():
            if len(emotions) < 2:
                continue
                
            for j in range(1, len(emotions)):
                prev = emotions[j-1]
                curr = emotions[j]
                
                # 检查是否有剧烈情感变化
                emotion_flip = False
                
                # 检查数值型情感
                if isinstance(prev["emotion"], (int, float)) and isinstance(curr["emotion"], (int, float)):
                    # 情感值反转且变化幅度大
                    if prev["emotion"] * curr["emotion"] < 0 and abs(curr["emotion"] - prev["emotion"]) > 1.5:
                        emotion_flip = True
                
                # 检查字符串型情感
                elif isinstance(prev["emotion"], str) and isinstance(curr["emotion"], str):
                    opposite_pairs = [
                        {"happy", "sad"}, {"angry", "calm"}, 
                        {"fear", "confidence"}, {"positive", "negative"}
                    ]
                    
                    prev_emotion = prev["emotion"].lower()
                    curr_emotion = curr["emotion"].lower()
                    
                    for pair in opposite_pairs:
                        if prev_emotion in pair and curr_emotion in pair and prev_emotion != curr_emotion:
                            emotion_flip = True
                            break
                
                if emotion_flip:
                    # 检查场景是否连续
                    scene_gap = curr["scene_idx"] - prev["scene_idx"]
                    
                    if scene_gap <= 1:  # 场景连续或只相差一个场景
                        defects.append(LogicDefect(
                            defect_type=LogicDefectType.EMOTION_FLIP,
                            description=f"角色 '{char_name}' 在场景 {prev['scene_idx']} 到 {curr['scene_idx']} 之间情感突然剧烈转变",
                            scene_index=curr["scene_idx"],
                            confidence=0.85,
                            severity="high",
                            suggested_fix=f"添加过渡场景或情感发展过程，解释角色 '{char_name}' 的情感变化"
                        ))
        
        return defects


# 便捷函数
def validate_logic_sandbox(script: Dict[str, Any], stress_test: bool = False) -> Dict[str, Any]:
    """
    使用逻辑沙盒验证脚本
    
    Args:
        script: 待验证的脚本
        stress_test: 是否进行压力测试
        
    Returns:
        验证结果，包含检测到的缺陷和评分
    """
    sandbox = LogicSandbox()
    defects = sandbox.detect_defects(script)
    
    result = {
        "defects": [defect.__dict__ for defect in defects],
        "defect_count": len(defects),
        "timestamp": "N/A"  # 可以添加时间戳
    }
    
    # 计算综合评分
    if defects:
        severity_weights = sandbox.config["severity_weights"]
        weighted_score = sum(severity_weights.get(d.severity, 1.0) * d.confidence for d in defects)
        avg_score = weighted_score / len(defects)
        result["score"] = max(0, 1 - avg_score / 3)  # 转换为0-1分数，越高越好
    else:
        result["score"] = 1.0
        
    # 如果需要进行压力测试
    if stress_test:
        detection_rate = sandbox.stress_test(script)
        result["stress_test"] = {
            "detection_rate": detection_rate,
            "description": f"在模拟注入的缺陷中检测出了 {detection_rate:.2%}"
        }
    
    return result 