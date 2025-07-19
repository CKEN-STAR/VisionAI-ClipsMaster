"""
叙事结构选择器

根据剧本元数据和内容特征选择最适合的叙事结构模式，
提供对非线性叙事重构的结构化支持。
"""

import os
import yaml
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

from src.narrative.anchor_types import AnchorType, AnchorInfo
from src.utils.validators import validate_float_range
from src.utils.file_utils import safe_read_yaml, ensure_directory

# 创建日志记录器
logger = logging.getLogger("structure_selector")

class StructureSelector:
    """叙事结构选择器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化叙事结构选择器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化叙事模式库
        self.patterns = {
            "倒叙风暴": {
                "steps": ["高潮前置", "回忆插叙", "悬念回收"],
                "suitability": ["悬疑", "推理"],
                "description": "从故事高潮开始，然后通过回忆或倒叙解释前因后果",
                "min_anchors": 3,
                "anchor_types": [AnchorType.EMOTION, AnchorType.SUSPENSE]
            },
            "多线织网": {
                "steps": ["视角切换", "平行叙事", "线索汇聚"],
                "suitability": ["群像", "史诗"],
                "description": "多条故事线并行发展，最终汇聚成完整叙事",
                "min_anchors": 4,
                "anchor_types": [AnchorType.CHARACTER, AnchorType.REVELATION]
            },
            "高潮迭起": {
                "steps": ["铺垫", "多重高潮", "余波"],
                "suitability": ["动作", "冒险"],
                "description": "多个情感和剧情高潮点连续出现，形成强烈节奏感",
                "min_anchors": 4,
                "anchor_types": [AnchorType.EMOTION, AnchorType.CLIMAX]
            },
            "环形结构": {
                "steps": ["首尾呼应", "循环暗示", "意义升华"],
                "suitability": ["文艺", "寓言"],
                "description": "故事结尾回到开始，但主角或情境已有深刻变化",
                "min_anchors": 3,
                "anchor_types": [AnchorType.TRANSITION, AnchorType.RESOLUTION]
            },
            "悬念递进": {
                "steps": ["谜题设置", "线索播撒", "悬念解决"],
                "suitability": ["悬疑", "犯罪"],
                "description": "不断设置和解决悬念，推动故事向前发展",
                "min_anchors": 3,
                "anchor_types": [AnchorType.SUSPENSE, AnchorType.REVELATION]
            }
        }
        
        # 扩展模式库
        self._extend_patterns_from_config()
        
        logger.info("叙事结构选择器初始化完成")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            
        Returns:
            配置字典
        """
        # 默认配置路径
        if not config_path:
            # 尝试读取专用配置
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "configs" / "narrative" / "structure_selector.yaml"
            
            # 如果专用配置不存在，使用通用叙事配置
            if not config_path.exists():
                config_path = base_dir / "configs" / "narrative_types.yaml"
            
            # 如果通用配置也不存在，使用基本叙事配置
            if not config_path.exists():
                config_path = base_dir / "configs" / "narrative_config.yaml"
        
        try:
            # 读取配置文件
            config = safe_read_yaml(config_path)
            if config:
                logger.info(f"从 {config_path} 加载叙事结构选择器配置")
                return config
            else:
                logger.warning(f"配置文件 {config_path} 为空或无法读取，使用默认配置")
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
        
        # 返回基本默认配置
        return {
            "narrative_patterns": {},
            "structure_selection": {
                "match_threshold": 0.6,
                "anchor_weight": 0.7,
                "genre_weight": 0.8,
                "emotion_weight": 0.5
            },
            "language": {
                "default": "zh",
                "auto_detect": True
            }
        }
    
    def _extend_patterns_from_config(self) -> None:
        """从配置文件扩展叙事模式库"""
        # 从配置中获取叙事模式
        config_patterns = self.config.get("narrative_patterns", {})
        
        # 处理标准叙事模式
        if "standard_narrative" in self.config:
            std_narrative = self.config["standard_narrative"]
            config_patterns["经典结构"] = {
                "steps": ["铺垫", "发展", "高潮", "结局"],
                "suitability": ["通用", "剧情"],
                "description": std_narrative.get("description", "经典的开端-发展-高潮-结局结构"),
                "beat_distribution": std_narrative.get("beat_distribution", {})
            }
        
        # 处理快节奏紧张型
        if "tension_driven" in self.config:
            tension = self.config["tension_driven"]
            config_patterns["紧张型"] = {
                "steps": ["快速开场", "冲突升级", "紧张高潮", "迅速结局"],
                "suitability": ["动作", "惊悚"],
                "description": tension.get("description", "快节奏冲突驱动，强调戏剧冲突和悬疑"),
                "beat_distribution": tension.get("beat_distribution", {})
            }
        
        # 处理情感主导型
        if "emotional_focus" in self.config:
            emotional = self.config["emotional_focus"]
            config_patterns["情感型"] = {
                "steps": ["情感铺垫", "情感变化", "情感高潮", "情感解决"],
                "suitability": ["爱情", "亲情", "友情"],
                "description": emotional.get("description", "强调人物情感变化，关注情感起伏和内心世界"),
                "beat_distribution": emotional.get("beat_distribution", {})
            }
            
        # 合并到现有模式中
        for pattern_name, pattern_data in config_patterns.items():
            if pattern_name not in self.patterns:
                self.patterns[pattern_name] = pattern_data
            else:
                # 更新现有模式的额外属性
                for key, value in pattern_data.items():
                    if key not in self.patterns[pattern_name]:
                        self.patterns[pattern_name][key] = value
    
    def select_best_fit(self, script_metadata: Dict[str, Any], anchors: Optional[List[AnchorInfo]] = None) -> Dict[str, Any]:
        """
        根据剧本特征选择最适合的叙事结构
        
        Args:
            script_metadata: 剧本元数据，包含类型、情感特征等
            anchors: 检测到的情节锚点列表，可选
            
        Returns:
            最适合的叙事结构信息
        """
        # 如果没有元数据，返回默认结构
        if not script_metadata:
            return {
                "pattern_name": "经典结构",
                "pattern_data": self.patterns.get("经典结构", self.patterns["倒叙风暴"]),
                "confidence": 0.5,
                "reason": "缺少剧本元数据，使用默认叙事结构"
            }
        
        # 提取剧本类型
        genre = script_metadata.get("genre", "")
        if isinstance(genre, list):
            genre = ",".join(genre)
        
        # 提取情感特征
        emotion_tone = script_metadata.get("emotion_tone", "")
        pace = script_metadata.get("pace", "medium")
        
        # 计算每个模式的匹配分数
        pattern_scores = {}
        reasons = {}
        
        for pattern_name, pattern_data in self.patterns.items():
            # 基础分数
            score = 0.0
            reason_parts = []
            
            # 1. 类型匹配度评分
            suitability = pattern_data.get("suitability", [])
            genre_score = self._calculate_genre_similarity(genre, suitability)
            score += genre_score * self.config.get("structure_selection", {}).get("genre_weight", 0.8)
            
            if genre_score > 0.7:
                reason_parts.append(f"类型匹配度高")
            
            # 2. 锚点匹配评分
            if anchors:
                anchor_score = self._calculate_anchor_compatibility(anchors, pattern_data)
                score += anchor_score * self.config.get("structure_selection", {}).get("anchor_weight", 0.7)
                
                if anchor_score > 0.6:
                    reason_parts.append(f"情节锚点匹配良好")
            
            # 3. 情感和节奏匹配
            emotion_score = self._calculate_emotion_fit(emotion_tone, pace, pattern_data)
            score += emotion_score * self.config.get("structure_selection", {}).get("emotion_weight", 0.5)
            
            if emotion_score > 0.7:
                reason_parts.append(f"情感节奏匹配优秀")
            
            # 添加最终分数和原因
            pattern_scores[pattern_name] = score
            reasons[pattern_name] = "，".join(reason_parts) if reason_parts else "综合评分结果"
        
        # 选择得分最高的结构
        if not pattern_scores:
            best_pattern = "经典结构"
            confidence = 0.5
            reason = "未能计算匹配分数，使用默认结构"
        else:
            best_pattern = max(pattern_scores, key=pattern_scores.get)
            confidence = pattern_scores[best_pattern]
            reason = reasons[best_pattern]
        
        return {
            "pattern_name": best_pattern,
            "pattern_data": self.patterns[best_pattern],
            "confidence": confidence,
            "reason": reason,
            "all_scores": pattern_scores
        }
    
    def _calculate_genre_similarity(self, genre: str, suitability: List[str]) -> float:
        """
        计算类型匹配度
        
        Args:
            genre: 剧本类型
            suitability: 适合的类型列表
            
        Returns:
            匹配度分数 (0-1)
        """
        if not genre or not suitability:
            return 0.3  # 默认基础分数
        
        # 将类型拆分为关键词
        genre_keywords = [kw.strip().lower() for kw in genre.split(',')]
        suit_keywords = [kw.strip().lower() for kw in suitability]
        
        # 计算匹配的关键词数量
        matches = sum(1 for kw in genre_keywords if any(suit_kw in kw or kw in suit_kw for suit_kw in suit_keywords))
        
        # 计算匹配分数
        if not genre_keywords:
            return 0.3
        
        match_ratio = matches / len(genre_keywords)
        return min(1.0, 0.3 + match_ratio * 0.7)  # 确保至少有0.3的基础分
    
    def _calculate_anchor_compatibility(self, anchors: List[AnchorInfo], pattern_data: Dict[str, Any]) -> float:
        """
        计算锚点与结构的兼容性
        
        Args:
            anchors: 锚点列表
            pattern_data: 结构模式数据
            
        Returns:
            兼容性分数 (0-1)
        """
        if not anchors:
            return 0.5  # 无锚点时默认中等匹配度
        
        # 获取结构需要的锚点类型
        required_types = pattern_data.get("anchor_types", [])
        if not required_types:
            required_types = [AnchorType.EMOTION, AnchorType.CHARACTER]  # 默认类型
        
        # 获取最小锚点数量要求
        min_anchors = pattern_data.get("min_anchors", 3)
        
        # 计算匹配的锚点类型数量
        matching_anchors = [a for a in anchors if a.type in required_types]
        
        # 计算分数
        if len(anchors) < min_anchors:
            # 锚点数量不足
            type_ratio = len(matching_anchors) / len(anchors) if anchors else 0
            count_penalty = 0.3 * (len(anchors) / min_anchors)
            return min(0.7, type_ratio * 0.5 + count_penalty)
        else:
            # 锚点数量充足
            type_ratio = len(matching_anchors) / len(anchors) if anchors else 0
            important_anchors = [a for a in matching_anchors if a.importance > 0.7]
            
            # 重要锚点额外加分
            importance_bonus = min(0.3, len(important_anchors) / min_anchors * 0.3)
            
            return min(1.0, type_ratio * 0.7 + importance_bonus)
    
    def _calculate_emotion_fit(self, emotion_tone: str, pace: str, pattern_data: Dict[str, Any]) -> float:
        """
        计算情感和节奏匹配度
        
        Args:
            emotion_tone: 情感基调
            pace: 节奏 (slow/medium/fast)
            pattern_data: 结构模式数据
            
        Returns:
            匹配度分数 (0-1)
        """
        # 默认匹配度
        if not emotion_tone:
            return 0.5
        
        # 结构描述
        description = pattern_data.get("description", "").lower()
        
        # 情感关键词映射
        emotion_keywords = {
            "喜剧": ["喜剧", "幽默", "欢乐", "搞笑", "轻松"],
            "悲剧": ["悲剧", "悲伤", "遗憾", "痛苦", "悲壮"],
            "温情": ["温情", "温暖", "感人", "治愈", "亲情"],
            "紧张": ["紧张", "惊悚", "悬疑", "刺激", "冲突"],
            "史诗": ["史诗", "宏大", "震撼", "壮观", "恢弘"]
        }
        
        # 节奏关键词映射
        pace_keywords = {
            "slow": ["慢节奏", "缓慢", "从容", "深度", "细腻"],
            "medium": ["中等节奏", "平衡", "稳定"],
            "fast": ["快节奏", "紧凑", "迅速", "高速", "激烈"]
        }
        
        # 计算情感匹配度
        emotion_match = 0.0
        for emotion, keywords in emotion_keywords.items():
            if any(kw in emotion_tone.lower() for kw in keywords):
                if any(kw in description for kw in keywords):
                    emotion_match = 0.8
                    break
                else:
                    emotion_match = 0.4
        
        # 计算节奏匹配度
        pace_match = 0.0
        if pace and pace in pace_keywords:
            if any(kw in description for kw in pace_keywords[pace]):
                pace_match = 0.7
            else:
                # 检查结构是否明确反对这种节奏
                opposite_paces = {"slow": "fast", "fast": "slow", "medium": ""}
                if opposite_paces[pace] and any(kw in description for kw in pace_keywords[opposite_paces[pace]]):
                    pace_match = 0.3
                else:
                    pace_match = 0.5
        
        # 综合分数
        return (emotion_match * 0.6 + pace_match * 0.4)
    
    def get_structure_steps(self, pattern_name: str) -> List[str]:
        """
        获取指定叙事结构的步骤
        
        Args:
            pattern_name: 结构模式名称
            
        Returns:
            结构步骤列表
        """
        if pattern_name in self.patterns:
            return self.patterns[pattern_name].get("steps", [])
        else:
            # 如果找不到指定模式，返回默认步骤
            return ["铺垫", "发展", "高潮", "结局"]
    
    def get_all_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有可用的叙事结构模式
        
        Returns:
            所有叙事结构模式字典
        """
        return self.patterns
    
    def map_anchors_to_structure(self, anchors: List[AnchorInfo], structure_name: str) -> Dict[str, List[AnchorInfo]]:
        """
        将锚点映射到叙事结构的各个步骤
        
        Args:
            anchors: 锚点列表
            structure_name: 结构名称
            
        Returns:
            按结构步骤分组的锚点字典
        """
        if not anchors:
            return {}
        
        # 获取结构步骤
        steps = self.get_structure_steps(structure_name)
        if not steps:
            return {}
        
        # 按位置排序锚点
        sorted_anchors = sorted(anchors, key=lambda a: a.position)
        
        # 计算每个步骤的位置范围
        step_count = len(steps)
        step_ranges = []
        for i in range(step_count):
            start = i / step_count
            end = (i + 1) / step_count
            step_ranges.append((start, end))
        
        # 将锚点映射到步骤
        step_anchors = {step: [] for step in steps}
        
        for anchor in sorted_anchors:
            # 确定锚点属于哪个步骤
            for i, (start, end) in enumerate(step_ranges):
                if start <= anchor.position < end or (i == step_count - 1 and anchor.position == end):
                    step_anchors[steps[i]].append(anchor)
                    break
        
        return step_anchors


# 便捷函数

def select_narrative_structure(script_metadata: Dict[str, Any], 
                               anchors: Optional[List[AnchorInfo]] = None) -> Dict[str, Any]:
    """
    选择最适合的叙事结构（便捷函数）
    
    Args:
        script_metadata: 剧本元数据
        anchors: 情节锚点列表，可选
        
    Returns:
        最佳匹配的叙事结构信息
    """
    selector = StructureSelector()
    return selector.select_best_fit(script_metadata, anchors)


def get_structure_patterns() -> Dict[str, Dict[str, Any]]:
    """
    获取所有可用的叙事结构模式（便捷函数）
    
    Returns:
        所有叙事结构模式字典
    """
    selector = StructureSelector()
    return selector.get_all_patterns()


def organize_anchors_by_structure(anchors: List[AnchorInfo], 
                                 structure_name: str) -> Dict[str, List[AnchorInfo]]:
    """
    按照叙事结构组织锚点（便捷函数）
    
    Args:
        anchors: 锚点列表
        structure_name: 结构名称
        
    Returns:
        按结构步骤分组的锚点字典
    """
    selector = StructureSelector()
    return selector.map_anchors_to_structure(anchors, structure_name)


if __name__ == "__main__":
    # 简单测试
    selector = StructureSelector()
    
    # 测试数据
    test_metadata = {
        "genre": "悬疑,犯罪",
        "emotion_tone": "紧张",
        "pace": "fast"
    }
    
    # 选择结构
    result = selector.select_best_fit(test_metadata)
    
    print(f"最佳匹配结构: {result['pattern_name']}")
    print(f"匹配原因: {result['reason']}")
    print(f"匹配度: {result['confidence']:.2f}")
    print(f"结构步骤: {result['pattern_data']['steps']}") 