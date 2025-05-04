#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键场景保护机制模块

此模块实现视频关键场景的保护功能，防止重要场景在压缩和编辑过程中被不当修改：
1. 根据情感分数、叙事结构、标签等多维度识别关键场景
2. 为关键场景应用保护标记，防止压缩/截取
3. 支持自定义保护规则和阈值
4. 与编辑器和压缩器集成，确保保护策略生效
"""

import os
import json
import logging
import base64
import hashlib
import zlib
from typing import Dict, List, Set, Tuple, Optional, Any, Union, Callable
from enum import Enum, auto
from dataclasses import dataclass, field

# 配置日志
logger = logging.getLogger(__name__)

# 保护级别枚举
class ProtectionLevel(Enum):
    """场景保护级别"""
    NONE = 0        # 无保护
    LOW = 1         # 低级保护，允许轻微修改
    MEDIUM = 2      # 中级保护，允许有限修改
    HIGH = 3        # 高级保护，几乎不允许修改
    CRITICAL = 4    # 关键保护，不允许任何修改

# 保护策略枚举
class ProtectionStrategy(Enum):
    """保护策略类型"""
    LOCK = auto()           # 锁定，防止任何修改
    NO_COMPRESSION = auto() # 禁止压缩
    NO_TRIM = auto()        # 禁止裁剪
    NO_DELETION = auto()    # 禁止删除
    WATERMARK = auto()      # 添加水印
    CHECKSUM = auto()       # 校验和保护

@dataclass
class ProtectionRule:
    """保护规则定义"""
    name: str                                            # 规则名称
    criteria: Callable[[Dict[str, Any]], bool]           # 判断标准函数
    level: ProtectionLevel = ProtectionLevel.MEDIUM      # 保护级别
    strategies: List[ProtectionStrategy] = field(default_factory=list)  # 保护策略
    description: str = ""                                # 规则描述

class KeySceneGuard:
    """关键场景保护器
    
    识别并保护视频中的关键场景，防止在编辑和压缩过程中被意外修改。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化关键场景保护器
        
        Args:
            config: 配置参数
        """
        self.config = config or self._default_config()
        self.protected_scenes: List[str] = []  # 保存已保护场景的ID
        self.protection_rules: List[ProtectionRule] = []
        
        # 初始化默认规则
        self._initialize_default_rules()
        
        logger.info("关键场景保护器初始化完成")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "emotion_threshold": 0.8,          # 情感强度阈值
            "importance_threshold": 0.7,       # 重要性阈值
            "critical_tags": [                 # 关键标签列表
                "climax", "高潮", "重要", "关键", 
                "转折", "结局", "开场", "核心"
            ],
            "compression_protection": True,    # 是否启用压缩保护
            "edit_protection": True,           # 是否启用编辑保护
            "checksum_verification": True,     # 是否启用校验和验证
            "enable_watermark": False,         # 是否启用水印
            "protection_metadata_key": "_protection_info"  # 保护信息元数据键
        }
    
    def _initialize_default_rules(self) -> None:
        """初始化默认保护规则"""
        # 规则1: 高情感强度场景保护
        self.add_protection_rule(
            ProtectionRule(
                name="high_emotion_rule",
                criteria=lambda scene: self._check_emotion_score(scene, self.config["emotion_threshold"]),
                level=ProtectionLevel.HIGH,
                strategies=[ProtectionStrategy.NO_COMPRESSION, ProtectionStrategy.NO_DELETION],
                description="保护高情感强度场景"
            )
        )
        
        # 规则2: 关键情节标签保护
        self.add_protection_rule(
            ProtectionRule(
                name="critical_tag_rule",
                criteria=lambda scene: self._check_critical_tags(scene, self.config["critical_tags"]),
                level=ProtectionLevel.CRITICAL,
                strategies=[
                    ProtectionStrategy.LOCK,
                    ProtectionStrategy.NO_COMPRESSION,
                    ProtectionStrategy.CHECKSUM
                ],
                description="保护关键情节标签场景"
            )
        )
        
        # 规则3: 关键时刻保护（基于场景位置）
        self.add_protection_rule(
            ProtectionRule(
                name="narrative_position_rule",
                criteria=lambda scene: self._check_narrative_position(scene),
                level=ProtectionLevel.MEDIUM,
                strategies=[ProtectionStrategy.NO_TRIM],
                description="保护关键叙事位置场景"
            )
        )
    
    def add_protection_rule(self, rule: ProtectionRule) -> None:
        """添加保护规则
        
        Args:
            rule: 保护规则
        """
        self.protection_rules.append(rule)
        logger.debug(f"已添加保护规则: {rule.name}")
    
    def _check_emotion_score(self, scene: Dict[str, Any], threshold: float) -> bool:
        """检查场景情感分数是否超过阈值
        
        Args:
            scene: 场景数据
            threshold: 阈值
            
        Returns:
            是否超过阈值
        """
        # 检查情感分数
        emotion_score = 0.0
        
        # 尝试不同的情感分数字段
        if "emotion_score" in scene:
            emotion_score = abs(float(scene["emotion_score"]))
        elif "emotion" in scene:
            if isinstance(scene["emotion"], dict):
                if "score" in scene["emotion"]:
                    emotion_score = abs(float(scene["emotion"]["score"]))
                elif "intensity" in scene["emotion"]:
                    emotion_score = abs(float(scene["emotion"]["intensity"]))
            elif isinstance(scene["emotion"], (int, float)):
                emotion_score = abs(float(scene["emotion"]))
        
        return emotion_score >= threshold
    
    def _check_critical_tags(self, scene: Dict[str, Any], critical_tags: List[str]) -> bool:
        """检查场景是否包含关键标签
        
        Args:
            scene: 场景数据
            critical_tags: 关键标签列表
            
        Returns:
            是否包含关键标签
        """
        # 检查标签
        scene_tags = []
        
        # 支持不同的标签字段格式
        if "tags" in scene:
            if isinstance(scene["tags"], list):
                scene_tags = scene["tags"]
            elif isinstance(scene["tags"], str):
                scene_tags = [scene["tags"]]
        
        if "tag" in scene:
            if isinstance(scene["tag"], list):
                scene_tags.extend(scene["tag"])
            elif isinstance(scene["tag"], str):
                scene_tags.append(scene["tag"])
        
        # 检查标签是否包含关键词
        for tag in scene_tags:
            if isinstance(tag, str) and any(ctag in tag.lower() for ctag in critical_tags):
                return True
        
        return False
    
    def _check_narrative_position(self, scene: Dict[str, Any]) -> bool:
        """检查场景是否处于关键叙事位置
        
        Args:
            scene: 场景数据
            
        Returns:
            是否处于关键位置
        """
        # 检查叙事位置
        if "narrative_position" in scene:
            position = scene["narrative_position"]
            # 开场、高潮和结局通常是关键场景
            if position in ["introduction", "开场", "climax", "高潮", "resolution", "结局"]:
                return True
        
        return False
    
    def mark_protected(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """标记需要保护的关键场景
        
        根据规则标识不应被压缩或过度编辑的场景
        
        Args:
            scenes: 场景列表
            
        Returns:
            处理后的场景列表
        """
        if not scenes:
            logger.warning("场景列表为空，无需标记保护")
            return scenes
        
        # 清空历史保护记录
        self.protected_scenes = []
        
        # 创建场景副本以避免修改原始数据
        processed_scenes = []
        
        for scene in scenes:
            # 创建场景副本
            scene_copy = scene.copy()
            
            # 评估所有保护规则
            max_protection_level = ProtectionLevel.NONE
            applied_strategies = set()
            applied_rules = []
            
            for rule in self.protection_rules:
                if rule.criteria(scene_copy):
                    # 记录最高保护级别
                    if rule.level.value > max_protection_level.value:
                        max_protection_level = rule.level
                    
                    # 收集保护策略
                    for strategy in rule.strategies:
                        applied_strategies.add(strategy)
                    
                    # 记录应用的规则
                    applied_rules.append(rule.name)
            
            # 应用保护标记
            if max_protection_level != ProtectionLevel.NONE:
                # 设置基本保护标记
                scene_copy["compressible"] = False if ProtectionStrategy.NO_COMPRESSION in applied_strategies else True
                scene_copy["protected"] = True
                
                # 获取场景ID
                scene_id = self._get_scene_id(scene_copy)
                if scene_id:
                    self.protected_scenes.append(scene_id)
                
                # 添加保护元数据
                protection_info = {
                    "level": max_protection_level.name,
                    "strategies": [s.name for s in applied_strategies],
                    "applied_rules": applied_rules,
                }
                
                # 如果需要校验和，添加校验信息
                if ProtectionStrategy.CHECKSUM in applied_strategies:
                    protection_info["checksum"] = self._generate_checksum(scene_copy)
                
                # 存储保护信息
                metadata_key = self.config["protection_metadata_key"]
                if "metadata" not in scene_copy:
                    scene_copy["metadata"] = {}
                scene_copy["metadata"][metadata_key] = protection_info
            
            processed_scenes.append(scene_copy)
        
        logger.info(f"完成场景保护标记，共保护 {len(self.protected_scenes)} 个场景")
        return processed_scenes
    
    def _get_scene_id(self, scene: Dict[str, Any]) -> str:
        """获取场景ID
        
        Args:
            scene: 场景数据
            
        Returns:
            场景ID
        """
        # 尝试不同的ID字段
        for id_field in ["id", "scene_id", "idx", "index"]:
            if id_field in scene:
                return str(scene[id_field])
        
        # 如果没有显式ID，生成一个基于内容的唯一ID
        content_hash = hashlib.md5()
        
        # 使用场景文本和时间信息生成哈希
        if "text" in scene:
            content_hash.update(str(scene["text"]).encode('utf-8'))
        
        if "start_time" in scene and "end_time" in scene:
            content_hash.update(f"{scene['start_time']}_{scene['end_time']}".encode('utf-8'))
        elif "time" in scene and isinstance(scene["time"], dict):
            if "start" in scene["time"] and "end" in scene["time"]:
                content_hash.update(f"{scene['time']['start']}_{scene['time']['end']}".encode('utf-8'))
        
        return content_hash.hexdigest()[:16]  # 使用前16位作为ID
    
    def _generate_checksum(self, scene: Dict[str, Any]) -> str:
        """为场景生成校验和
        
        Args:
            scene: 场景数据
            
        Returns:
            校验和字符串
        """
        # 创建场景副本，移除可能变化的元数据
        scene_copy = scene.copy()
        if "metadata" in scene_copy:
            scene_copy["metadata"] = {
                k: v for k, v in scene_copy["metadata"].items() 
                if k != self.config["protection_metadata_key"]
            }
        
        # 生成场景数据的JSON字符串
        scene_json = json.dumps(scene_copy, sort_keys=True)
        
        # 计算校验和
        checksum = hashlib.sha256(scene_json.encode("utf-8")).digest()
        compressed = zlib.compress(checksum)
        
        # 返回BASE64编码的校验和
        return base64.b64encode(compressed).decode("utf-8")
    
    def verify_protected_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证受保护场景的完整性
        
        检查受保护场景是否被修改，恢复保护标记
        
        Args:
            scenes: 场景列表
            
        Returns:
            验证后的场景列表
        """
        if not scenes:
            return scenes
        
        verified_scenes = []
        modified_scenes = []
        
        for scene in scenes:
            scene_copy = scene.copy()
            metadata_key = self.config["protection_metadata_key"]
            
            # 检查是否是受保护场景
            if "metadata" in scene_copy and metadata_key in scene_copy["metadata"]:
                protection_info = scene_copy["metadata"][metadata_key]
                
                # 检查是否有校验和
                if "checksum" in protection_info:
                    # 检查校验和
                    current_checksum = self._generate_checksum(scene_copy)
                    original_checksum = protection_info["checksum"]
                    
                    if current_checksum != original_checksum:
                        logger.warning(f"检测到受保护场景被修改: {self._get_scene_id(scene_copy)}")
                        modified_scenes.append(scene_copy)
                        
                        # 强制恢复保护标记
                        if "LOCK" in protection_info.get("strategies", []):
                            scene_copy["compressible"] = False
                            scene_copy["protected"] = True
                            logger.info(f"已恢复场景的保护标记: {self._get_scene_id(scene_copy)}")
            
            verified_scenes.append(scene_copy)
        
        if modified_scenes:
            logger.warning(f"发现 {len(modified_scenes)} 个受保护场景被修改")
        
        return verified_scenes
    
    def get_protection_stats(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取场景保护统计信息
        
        Args:
            scenes: 场景列表
            
        Returns:
            保护统计信息
        """
        stats = {
            "total_scenes": len(scenes),
            "protected_scenes": 0,
            "protection_levels": {
                "LOW": 0,
                "MEDIUM": 0,
                "HIGH": 0,
                "CRITICAL": 0
            },
            "protection_strategies": {}
        }
        
        metadata_key = self.config["protection_metadata_key"]
        
        for scene in scenes:
            if "metadata" in scene and metadata_key in scene["metadata"]:
                protection_info = scene["metadata"][metadata_key]
                stats["protected_scenes"] += 1
                
                # 统计保护级别
                if "level" in protection_info:
                    level = protection_info["level"]
                    if level in stats["protection_levels"]:
                        stats["protection_levels"][level] += 1
                
                # 统计保护策略
                if "strategies" in protection_info:
                    for strategy in protection_info["strategies"]:
                        if strategy not in stats["protection_strategies"]:
                            stats["protection_strategies"][strategy] = 0
                        stats["protection_strategies"][strategy] += 1
        
        return stats


# 便利函数
def mark_protected_scenes(scenes: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """标记受保护的关键场景
    
    Args:
        scenes: 场景列表
        config: 保护配置
        
    Returns:
        处理后的场景列表
    """
    protector = KeySceneGuard(config)
    return protector.mark_protected(scenes)

def verify_scene_protection(scenes: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """验证场景保护状态
    
    Args:
        scenes: 场景列表
        config: 保护配置
        
    Returns:
        验证后的场景列表
    """
    protector = KeySceneGuard(config)
    return protector.verify_protected_scenes(scenes) 