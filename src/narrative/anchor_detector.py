#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
锚点检测器

检测剧本中的情节锚点，包括情感锚点、悬念锚点、角色锚点等。
锚点是指剧情中的重要转折点或关键点，它们在叙事结构中起着承上启下的作用。
"""

import logging
from typing import Dict, List, Any, Optional, Set
import re

# 导入锚点类型
from src.narrative.anchor_types import AnchorType, AnchorInfo

# 获取日志记录器
logger = logging.getLogger(__name__)

class AnchorDetector:
    """锚点检测器，用于检测剧本中的情节锚点"""
    
    def __init__(self):
        """初始化锚点检测器"""
        # 锚点关键词
        self.anchor_keywords = {
            AnchorType.EMOTION: [
                "感动", "激动", "心情", "情绪", "愤怒", "喜悦", "悲伤", "惊讶", "恐惧", 
                "开心", "悲伤", "紧张", "满足", "失望", "感伤", "兴奋"
            ],
            AnchorType.CHARACTER: [
                "登场", "出场", "初次", "亮相", "介绍", "主角", "配角", "人物", "角色"
            ],
            AnchorType.SUSPENSE: [
                "疑问", "谜团", "秘密", "线索", "暗示", "疑惑", "猜测", "好奇", "谜题",
                "悬念", "悬疑", "谜底", "揭示", "谜团", "真相"
            ],
            AnchorType.CONFLICT: [
                "对抗", "冲突", "矛盾", "争执", "吵架", "争吵", "战斗", "较量", "竞争",
                "挑战", "拒绝", "抗拒", "对立", "对峙", "反对"
            ],
            AnchorType.REVELATION: [
                "发现", "揭露", "真相", "真实", "秘密", "揭开", "曝光", "真实面目", "真实身份",
                "隐藏", "真实情况", "明白", "理解", "顿悟", "领悟"
            ],
            AnchorType.TRANSITION: [
                "转折", "转变", "变化", "改变", "突然", "却", "不料", "没想到", "出乎意料",
                "意想不到", "然而", "但是", "突然", "转而", "开始"
            ],
            AnchorType.CLIMAX: [
                "高潮", "巅峰", "最后", "最终", "决战", "决定性", "关键", "顶点", "制高点",
                "最重要", "最关键", "最终", "最后", "决赛", "决胜"
            ],
            AnchorType.RESOLUTION: [
                "解决", "和解", "完结", "结束", "解开", "释然", "释怀", "宽恕", "原谅",
                "理解", "接受", "达成", "共识", "一致", "明白"
            ]
        }
        
        # 场景标签映射
        self.tag_mapping = {
            "开场": AnchorType.CHARACTER,
            "引入": AnchorType.CHARACTER,
            "转折": AnchorType.TRANSITION,
            "高潮": AnchorType.CLIMAX,
            "结局": AnchorType.RESOLUTION,
            "冲突": AnchorType.CONFLICT,
            "发现": AnchorType.REVELATION,
            "悬念": AnchorType.SUSPENSE,
            "情感": AnchorType.EMOTION,
            "危机": AnchorType.CONFLICT,
            "解决": AnchorType.RESOLUTION
        }
        
        logger.info("锚点检测器初始化完成")
    
    def detect_anchors(self, script: List[Dict[str, Any]]) -> List[AnchorInfo]:
        """
        检测剧本中的锚点
        
        Args:
            script: 剧本场景列表
            
        Returns:
            锚点信息列表
        """
        anchors = []
        
        # 分析每个场景
        for i, scene in enumerate(script):
            text = scene.get('text', '')
            relative_position = i / len(script)
            
            # 从标签中检测锚点
            scene_anchors = self._detect_from_tags(scene, i, relative_position)
            anchors.extend(scene_anchors)
            
            # 从文本中检测锚点
            text_anchors = self._detect_from_text(text, i, relative_position)
            anchors.extend(text_anchors)
            
            # 从情感变化中检测锚点
            if i > 0:
                emotion_anchors = self._detect_from_sentiment(script[i-1], scene, i, relative_position)
                anchors.extend(emotion_anchors)
        
        # 处理锚点之间的关系
        anchors = self._process_anchor_relationships(anchors, script)
        
        logger.info(f"在{len(script)}个场景中检测到{len(anchors)}个锚点")
        return anchors
    
    def _detect_from_tags(self, scene: Dict[str, Any], scene_idx: int, position: float) -> List[AnchorInfo]:
        """从场景标签中检测锚点"""
        anchors = []
        
        # 获取标签
        tags = scene.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
            
        for tag in tags:
            anchor_type = self.tag_mapping.get(tag)
            if anchor_type:
                # 计算置信度（标签直接匹配，给高置信度）
                confidence = 0.85
                
                # 创建锚点信息
                anchor = AnchorInfo(
                    anchor_type=anchor_type,
                    start_idx=scene_idx,
                    position=position,
                    description=f"通过标签'{tag}'识别的{anchor_type.value}锚点",
                    confidence=confidence
                )
                
                anchors.append(anchor)
        
        return anchors
    
    def _detect_from_text(self, text: str, scene_idx: int, position: float) -> List[AnchorInfo]:
        """从场景文本中检测锚点"""
        anchors = []
        
        for anchor_type, keywords in self.anchor_keywords.items():
            # 计算文本中包含的锚点关键词数量
            match_count = 0
            matching_words = []
            
            for keyword in keywords:
                matches = re.findall(keyword, text)
                match_count += len(matches)
                if matches:
                    matching_words.append(keyword)
            
            # 如果匹配到足够的关键词，创建锚点
            if match_count >= 2 or (match_count == 1 and len(text) < 50):
                # 置信度基于匹配数量
                confidence = min(0.75, 0.5 + 0.1 * match_count)
                
                # 创建锚点信息
                anchor = AnchorInfo(
                    anchor_type=anchor_type,
                    start_idx=scene_idx,
                    position=position,
                    description=f"通过关键词{', '.join(matching_words)}识别的{anchor_type.value}锚点",
                    confidence=confidence
                )
                
                anchors.append(anchor)
        
        return anchors
    
    def _detect_from_sentiment(self, prev_scene: Dict[str, Any], 
                             curr_scene: Dict[str, Any], 
                             scene_idx: int, 
                             position: float) -> List[AnchorInfo]:
        """从场景情感变化中检测锚点"""
        anchors = []
        
        # 获取情感数据
        prev_sentiment = prev_scene.get('sentiment', {})
        curr_sentiment = curr_scene.get('sentiment', {})
        
        prev_label = prev_sentiment.get('label', 'NEUTRAL')
        curr_label = curr_sentiment.get('label', 'NEUTRAL')
        
        prev_intensity = prev_sentiment.get('intensity', 0.5)
        curr_intensity = curr_sentiment.get('intensity', 0.5)
        
        # 检测情感标签变化
        if prev_label != curr_label:
            # 情感极性发生变化，可能是情感锚点或转折
            
            anchor_type = AnchorType.EMOTION
            confidence = 0.6  # 基础置信度
            
            # 如果从积极到消极，可能是冲突锚点
            if prev_label == 'POSITIVE' and curr_label == 'NEGATIVE':
                anchor_type = AnchorType.CONFLICT
                confidence = 0.65
            
            # 如果从消极到积极，可能是解决锚点
            elif prev_label == 'NEGATIVE' and curr_label == 'POSITIVE':
                anchor_type = AnchorType.RESOLUTION
                confidence = 0.65
            
            # 如果是惊讶情感，可能是悬念或转折锚点
            elif curr_label == 'SURPRISE':
                anchor_type = AnchorType.TRANSITION
                confidence = 0.7
            
            # 创建锚点信息
            anchor = AnchorInfo(
                anchor_type=anchor_type,
                start_idx=scene_idx,
                position=position,
                description=f"通过情感变化从{prev_label}到{curr_label}识别的{anchor_type.value}锚点",
                confidence=confidence
            )
            
            anchors.append(anchor)
        
        # 检测情感强度显著变化
        elif abs(curr_intensity - prev_intensity) > 0.3:
            # 情感强度变化显著，可能是情感或转折锚点
            
            if curr_intensity > prev_intensity:
                # 情感增强，可能是高潮或冲突
                anchor_type = AnchorType.CLIMAX if curr_intensity > 0.7 else AnchorType.EMOTION
            else:
                # 情感减弱，可能是解决或情感
                anchor_type = AnchorType.RESOLUTION if prev_intensity > 0.7 else AnchorType.EMOTION
            
            # 置信度基于变化程度
            confidence = 0.5 + min(0.2, abs(curr_intensity - prev_intensity))
            
            # 创建锚点信息
            anchor = AnchorInfo(
                anchor_type=anchor_type,
                start_idx=scene_idx,
                position=position,
                description=f"通过情感强度变化从{prev_intensity:.2f}到{curr_intensity:.2f}识别的{anchor_type.value}锚点",
                confidence=confidence
            )
            
            anchors.append(anchor)
        
        return anchors
    
    def _process_anchor_relationships(self, anchors: List[AnchorInfo], 
                                    script: List[Dict[str, Any]]) -> List[AnchorInfo]:
        """处理锚点之间的关系"""
        # 按场景位置排序
        anchors.sort(key=lambda x: x.start_idx)
        
        # 找出悬念锚点及其解答
        suspense_anchors = [a for a in anchors if a.anchor_type == AnchorType.SUSPENSE]
        resolution_anchors = [a for a in anchors if a.anchor_type == AnchorType.RESOLUTION]
        revelation_anchors = [a for a in anchors if a.anchor_type == AnchorType.REVELATION]
        
        # 标记已解决的悬念锚点
        for suspense in suspense_anchors:
            # 找出在这个悬念锚点之后的解决或揭示锚点
            potential_resolutions = [a for a in resolution_anchors + revelation_anchors 
                                    if a.start_idx > suspense.start_idx]
            
            if potential_resolutions:
                # 取最近的解决或揭示锚点
                nearest_resolution = min(potential_resolutions, key=lambda a: a.start_idx)
                
                # 设置悬念锚点的解决状态
                suspense.is_resolved = True
                suspense.resolution_idx = nearest_resolution.start_idx
                
                # 在两个锚点之间的场景可能包含悬念的解决过程
                suspense.related_scenes = list(range(suspense.start_idx + 1, nearest_resolution.start_idx + 1))
            else:
                # 没有找到解决锚点，悬念未解决
                suspense.is_resolved = False
        
        return anchors


# 创建全局检测器实例
_detector = None

def get_detector() -> AnchorDetector:
    """获取或创建锚点检测器实例"""
    global _detector
    if _detector is None:
        _detector = AnchorDetector()
    return _detector

def detect_anchors(script: List[Dict[str, Any]]) -> List[AnchorInfo]:
    """
    检测剧本中的锚点
    
    Args:
        script: 剧本场景列表
        
    Returns:
        锚点信息列表
    """
    detector = get_detector()
    return detector.detect_anchors(script)


if __name__ == "__main__":
    # 测试锚点检测
    from src.utils.sample_data import get_sample_script
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取示例脚本
    script = get_sample_script()
    
    # 检测锚点
    anchors = detect_anchors(script)
    
    # 输出锚点信息
    print(f"检测到 {len(anchors)} 个锚点:")
    
    for i, anchor in enumerate(anchors):
        print(f"\n锚点 {i+1}:")
        print(f"  类型: {anchor.anchor_type.value}")
        print(f"  场景: {anchor.start_idx}")
        print(f"  位置: {anchor.position:.2f}")
        print(f"  描述: {anchor.description}")
        print(f"  置信度: {anchor.confidence:.2f}")
        
        if anchor.anchor_type == AnchorType.SUSPENSE:
            if anchor.is_resolved:
                print(f"  已解决: 是 (在场景 {anchor.resolution_idx})")
            else:
                print(f"  已解决: 否")