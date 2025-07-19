#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生理信号模拟器模块

基于场景的情感信息，预测和模拟观众可能产生的生理反应，
如心率变化、皮肤电反应和面部肌肉活动等。
这些信号可用于评估内容的情感影响力和沉浸感。
"""

import logging
import random
import math
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    from ..config.constants import EMOTION_TYPES
except ImportError:
    # 备用常量，以防无法导入
    EMOTION_TYPES = {
        "en": ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"],
        "zh": ["喜悦", "悲伤", "愤怒", "恐惧", "厌恶", "惊讶", "中性"]
    }

try:
    from ..utils.exceptions import ClipMasterError, ErrorCode
except ImportError:
    # 定义备用异常类，以防无法导入
    class ClipMasterError(Exception):
        def __init__(self, message="", code=None, details=None):
            self.code = code
            self.details = details or {}
            super().__init__(message)
    
    class ErrorCode:
        VALIDATION_ERROR = 1005

logger = logging.getLogger(__name__)

# 生理信号参考范围
BIOSIGNAL_REFERENCE = {
    # 心率参考值 (bpm)
    "heart_rate": {
        "base": 60,      # 基础心率
        "min": 40,       # 最小值
        "max": 120,      # 最大值
        "emotion_factors": {
            "喜悦": 1.2,   # 喜悦情绪下心率增加因子
            "悲伤": 0.9,   # 悲伤情绪下心率降低因子
            "愤怒": 1.4,   # 愤怒情绪下心率增加因子
            "恐惧": 1.5,   # 恐惧情绪下心率增加因子
            "厌恶": 1.1,   # 厌恶情绪下心率增加因子
            "惊讶": 1.3,   # 惊讶情绪下心率增加因子
            "中性": 1.0    # 中性情绪下心率保持基础水平
        }
    },
    
    # 皮肤电反应参考值 (微西门子)
    "galvanic": {
        "base": 2,       # 基础皮肤电水平
        "min": 0.5,      # 最小值
        "max": 20,       # 最大值
        "emotion_factors": {
            "喜悦": 1.3,   # 喜悦情绪下皮肤电增加因子
            "悲伤": 1.1,   # 悲伤情绪下皮肤电变化因子
            "愤怒": 1.8,   # 愤怒情绪下皮肤电增加因子
            "恐惧": 2.0,   # 恐惧情绪下皮肤电增加因子
            "厌恶": 1.5,   # 厌恶情绪下皮肤电增加因子
            "惊讶": 1.7,   # 惊讶情绪下皮肤电增加因子
            "中性": 1.0    # 中性情绪下皮肤电保持基础水平
        }
    },
    
    # 面部肌肉活动参考值 (相对单位)
    "facial_muscle": {
        "base": 0.2,     # 基础面部肌肉活动水平
        "min": 0.1,      # 最小值
        "max": 1.0,      # 最大值
        "emotion_factors": {
            "喜悦": 0.8,   # 喜悦情绪下面部肌肉活动增加因子
            "悲伤": 0.6,   # 悲伤情绪下面部肌肉活动变化因子
            "愤怒": 0.9,   # 愤怒情绪下面部肌肉活动增加因子
            "恐惧": 0.7,   # 恐惧情绪下面部肌肉活动变化因子
            "厌恶": 0.65,  # 厌恶情绪下面部肌肉活动变化因子
            "惊讶": 0.85,  # 惊讶情绪下面部肌肉活动增加因子
            "中性": 0.3    # 中性情绪下面部肌肉活动保持低水平
        }
    },
    
    # 呼吸频率参考值 (每分钟呼吸次数)
    "respiration": {
        "base": 12,      # 基础呼吸频率
        "min": 8,        # 最小值
        "max": 25,       # 最大值
        "emotion_factors": {
            "喜悦": 1.2,   # 喜悦情绪下呼吸频率变化因子
            "悲伤": 0.8,   # 悲伤情绪下呼吸频率降低因子
            "愤怒": 1.5,   # 愤怒情绪下呼吸频率增加因子
            "恐惧": 1.6,   # 恐惧情绪下呼吸频率增加因子
            "厌恶": 1.1,   # 厌恶情绪下呼吸频率变化因子
            "惊讶": 1.4,   # 惊讶情绪下呼吸频率增加因子
            "中性": 1.0    # 中性情绪下呼吸频率保持基础水平
        }
    },
    
    # 瞳孔直径变化参考值 (毫米)
    "pupil_diameter": {
        "base": 3,       # 基础瞳孔直径
        "min": 2,        # 最小值
        "max": 8,        # 最大值
        "emotion_factors": {
            "喜悦": 1.1,   # 喜悦情绪下瞳孔扩张因子
            "悲伤": 0.9,   # 悲伤情绪下瞳孔变化因子
            "愤怒": 1.2,   # 愤怒情绪下瞳孔扩张因子
            "恐惧": 1.4,   # 恐惧情绪下瞳孔扩张因子
            "厌恶": 1.0,   # 厌恶情绪下瞳孔变化因子
            "惊讶": 1.3,   # 惊讶情绪下瞳孔扩张因子
            "中性": 1.0    # 中性情绪下瞳孔保持基础大小
        }
    }
}

class BiosignalError(ClipMasterError):
    """生理信号模拟异常类"""
    
    def __init__(self, msg: str = "生理信号模拟失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(msg, code=ErrorCode.VALIDATION_ERROR, details=details)

class BiosignalGenerator:
    """生理信号生成器
    
    基于场景的情感状态，生成相应的生理反应信号，
    包括心率、皮肤电导率、面部肌肉活动等。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化生理信号生成器
        
        Args:
            config: 配置参数，用于自定义生成规则
        """
        try:
            self.config = config or self._default_config()
            self.reference = self.config.get("reference", BIOSIGNAL_REFERENCE)
            self.language = self.config.get("language", "zh")
            self.noise_level = self.config.get("noise_level", 0.1)  # 随机噪声水平，用于模拟自然变化
            self.continuity_factor = self.config.get("continuity_factor", 0.3)  # 连续性因子，用于平滑变化
            self.prev_signals = None  # 用于存储前一个场景的信号，实现平滑过渡
            
            logger.info("生理信号生成器初始化完成")
        except Exception as e:
            logger.error(f"生理信号生成器初始化失败: {str(e)}")
            raise BiosignalError(f"生理信号生成器初始化失败: {str(e)}")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "language": "zh",  # 默认语言
            "reference": BIOSIGNAL_REFERENCE,  # 生理信号参考数据
            "noise_level": 0.1,  # 随机噪声水平 (0-1)
            "continuity_factor": 0.3,  # 连续性因子，平滑场景间变化 (0-1)
            "use_narrative_position": True,  # 是否考虑叙事位置的影响
            "use_scene_intensity": True,  # 是否考虑场景整体强度的影响
            "signal_types": [  # 要生成的信号类型
                "heart_rate",
                "galvanic",
                "facial_muscle",
                "respiration",
                "pupil_diameter"
            ]
        }
    
    def process_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理场景列表，为每个场景添加生理信号预测
        
        Args:
            scenes: 场景列表
            
        Returns:
            添加了生理信号的场景列表
            
        Raises:
            BiosignalError: 处理过程中发生错误
        """
        try:
            # 重置前一个信号，确保每次处理序列时从头开始
            self.prev_signals = None
            
            processed_scenes = []
            for scene in scenes:
                processed_scene = scene.copy()  # 创建副本，避免修改原始数据
                
                # 生成生理信号
                biosignals = self.predict_reactions(scene)
                
                # 添加到场景中
                processed_scene["biosignals"] = biosignals
                
                processed_scenes.append(processed_scene)
            
            return processed_scenes
        except Exception as e:
            logger.error(f"处理场景生理信号失败: {str(e)}")
            raise BiosignalError(f"处理场景生理信号失败: {str(e)}")
    
    def predict_reactions(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """预测观众对场景的生理反应
        
        基于场景的情感信息，预测可能的生理反应信号。
        
        Args:
            scene: 场景数据
            
        Returns:
            生理信号数据字典
            
        Raises:
            BiosignalError: 无法预测生理信号时抛出
        """
        try:
            # 提取情感信息
            emotion = scene.get("emotion", {})
            emotion_type = self._normalize_emotion_type(emotion.get("type", "中性"))
            emotion_score = self._get_emotion_score(emotion)
            emotion_intensity = emotion.get("intensity", emotion_score)
            
            # 提取叙事位置信息
            narrative_position = scene.get("narrative_position", "unknown")
            valence = scene.get("valence", self._estimate_valence(emotion_type))
            
            # 准备生成的信号字典
            signals = {}
            
            # 生成各类生理信号
            for signal_type in self.config.get("signal_types", []):
                if signal_type in self.reference:
                    signals[signal_type] = self._generate_signal(
                        signal_type, 
                        emotion_type, 
                        emotion_score,
                        valence,
                        narrative_position
                    )
            
            # 应用随机噪声和连续性平滑
            signals = self._apply_noise_and_continuity(signals)
            
            # 记录当前信号作为下一个场景的参考
            self.prev_signals = signals
            
            return signals
        except Exception as e:
            logger.error(f"预测生理反应失败: {str(e)}")
            # 返回默认值而不是抛出异常，确保处理流程不会中断
            return self._default_signals()
    
    def _normalize_emotion_type(self, emotion_type: str) -> str:
        """标准化情感类型
        
        将英文情感类型转换为中文（如果需要）
        
        Args:
            emotion_type: 原始情感类型
            
        Returns:
            标准化后的情感类型
        """
        # 如果已经是中文情感类型，直接返回
        if emotion_type in EMOTION_TYPES.get("zh", []):
            return emotion_type
        
        # 尝试将英文转换为中文
        if emotion_type in EMOTION_TYPES.get("en", []):
            try:
                index = EMOTION_TYPES.get("en", []).index(emotion_type)
                return EMOTION_TYPES.get("zh", [])[index]
            except (ValueError, IndexError):
                pass
        
        # 如果无法识别，返回中性
        return "中性"
    
    def _get_emotion_score(self, emotion: Dict[str, Any]) -> float:
        """获取情感强度分数
        
        Args:
            emotion: 情感数据
            
        Returns:
            情感强度分数 (0-1)
        """
        # 尝试获取调整后的分数和原始分数
        adjusted_score = emotion.get("adjusted_score")
        if adjusted_score is not None:
            return adjusted_score
        
        # 尝试获取score字段
        score = emotion.get("score")
        if score is not None:
            return score
        
        # 回退到intensity字段
        intensity = emotion.get("intensity", 0.5)
        return intensity
    
    def _estimate_valence(self, emotion_type: str) -> float:
        """估计情感类型的效价值
        
        Args:
            emotion_type: 情感类型
            
        Returns:
            情感效价值 (-1 to 1)，正值表示积极情感，负值表示消极情感
        """
        # 情感效价映射
        valence_map = {
            "喜悦": 0.8,    # 积极情感
            "悲伤": -0.7,   # 消极情感 
            "愤怒": -0.8,   # 消极情感
            "恐惧": -0.9,   # 消极情感
            "厌恶": -0.6,   # 消极情感
            "惊讶": 0.2,    # 轻微积极
            "中性": 0.0     # 中性情感
        }
        
        return valence_map.get(emotion_type, 0.0)
    
    def _generate_signal(self, 
                        signal_type: str, 
                        emotion_type: str, 
                        emotion_score: float,
                        valence: float,
                        narrative_position: str) -> float:
        """生成特定类型的生理信号
        
        Args:
            signal_type: 信号类型
            emotion_type: 情感类型
            emotion_score: 情感强度
            valence: 情感效价
            narrative_position: 叙事位置
            
        Returns:
            生成的信号值
        """
        # 获取该信号类型的参考数据
        signal_ref = self.reference[signal_type]
        base_value = signal_ref["base"]
        
        # 获取情感类型对应的影响因子
        emotion_factor = signal_ref["emotion_factors"].get(emotion_type, 1.0)
        
        # 计算情感强度影响
        intensity_effect = 1.0 + (emotion_score - 0.5) * 2  # 将0.5归一化为基准
        
        # 计算叙事位置影响
        narrative_effect = 1.0
        if self.config.get("use_narrative_position", True):
            if narrative_position == "climax":
                narrative_effect = 1.3  # 高潮部分增强生理反应
            elif narrative_position == "resolution":
                narrative_effect = 0.8  # 解决部分减弱生理反应
        
        # 计算基础信号值
        base_signal = base_value * emotion_factor * intensity_effect * narrative_effect
        
        # 确保信号值在合理范围内
        min_val = signal_ref["min"]
        max_val = signal_ref["max"]
        signal_value = max(min_val, min(max_val, base_signal))
        
        return signal_value
    
    def _apply_noise_and_continuity(self, signals: Dict[str, float]) -> Dict[str, float]:
        """应用随机噪声和连续性平滑
        
        Args:
            signals: 原始信号值字典
            
        Returns:
            处理后的信号值字典
        """
        result = {}
        
        # 如果没有前一个信号，就不应用连续性
        if self.prev_signals is None:
            # 只应用随机噪声
            for key, value in signals.items():
                noise = random.uniform(-self.noise_level, self.noise_level) * value
                result[key] = max(0, value + noise)  # 确保不会出现负值
            return result
        
        # 应用连续性和噪声
        for key, value in signals.items():
            if key in self.prev_signals:
                # 计算与前一个信号的平滑过渡
                prev_value = self.prev_signals[key]
                smooth_value = (1 - self.continuity_factor) * value + self.continuity_factor * prev_value
                
                # 添加随机噪声
                noise = random.uniform(-self.noise_level, self.noise_level) * smooth_value
                result[key] = max(0, smooth_value + noise)  # 确保不会出现负值
            else:
                # 如果前一个信号中没有这个键，只应用噪声
                noise = random.uniform(-self.noise_level, self.noise_level) * value
                result[key] = max(0, value + noise)
        
        return result
    
    def _default_signals(self) -> Dict[str, float]:
        """获取默认的生理信号值
        
        当无法正常预测时，提供默认的生理信号值。
        
        Returns:
            默认信号字典
        """
        default_signals = {}
        
        for signal_type in self.config.get("signal_types", []):
            if signal_type in self.reference:
                default_signals[signal_type] = self.reference[signal_type]["base"]
        
        return default_signals
    
    def calculate_immersion_index(self, biosignals: Dict[str, float]) -> float:
        """计算沉浸度指数
        
        基于生理信号计算预估的观众沉浸度。
        
        Args:
            biosignals: 生理信号数据
            
        Returns:
            沉浸度指数 (0-1)
        """
        if not biosignals:
            return 0.0
        
        # 各信号对沉浸度的权重
        weights = {
            "heart_rate": 0.3,
            "galvanic": 0.25,
            "facial_muscle": 0.2,
            "respiration": 0.15,
            "pupil_diameter": 0.1
        }
        
        # 计算归一化的信号变化量
        normalized_values = {}
        total_weight = 0
        
        for signal_type, value in biosignals.items():
            if signal_type in self.reference and signal_type in weights:
                ref = self.reference[signal_type]
                base = ref["base"]
                max_val = ref["max"]
                min_val = ref["min"]
                
                # 计算信号变化量相对于可能范围的比例
                range_size = max_val - min_val
                change_ratio = abs(value - base) / range_size if range_size > 0 else 0
                
                # 归一化到0-1，且考虑非线性关系
                normalized_values[signal_type] = min(1.0, change_ratio * 1.5)
                total_weight += weights[signal_type]
        
        if total_weight == 0 or not normalized_values:
            return 0.0
        
        # 计算加权平均
        immersion_index = 0.0
        for signal_type, norm_value in normalized_values.items():
            if signal_type in weights:
                immersion_index += norm_value * weights[signal_type] / total_weight
        
        return min(1.0, immersion_index)

# 便利函数
def predict_biosignals(scene: Dict[str, Any]) -> Dict[str, float]:
    """预测单个场景的生理信号
    
    Args:
        scene: 场景数据
        
    Returns:
        生理信号数据
    """
    generator = BiosignalGenerator()
    return generator.predict_reactions(scene)

def process_scenes_with_biosignals(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """为场景序列添加生理信号预测
    
    Args:
        scenes: 场景列表
        
    Returns:
        添加了生理信号的场景列表
    """
    generator = BiosignalGenerator()
    return generator.process_scenes(scenes)

def calculate_immersion_score(scenes: List[Dict[str, Any]]) -> float:
    """计算场景序列的整体沉浸度评分
    
    Args:
        scenes: 已添加生理信号的场景列表
        
    Returns:
        整体沉浸度评分 (0-100)
    """
    if not scenes:
        return 0.0
    
    generator = BiosignalGenerator()
    
    # 计算每个场景的沉浸度
    immersion_scores = []
    for scene in scenes:
        biosignals = scene.get("biosignals", {})
        if biosignals:
            immersion_scores.append(generator.calculate_immersion_index(biosignals))
    
    # 如果没有有效分数，返回0
    if not immersion_scores:
        return 0.0
    
    # 考虑峰值和平均值的组合
    avg_immersion = sum(immersion_scores) / len(immersion_scores)
    max_immersion = max(immersion_scores)
    
    # 综合评分，转换到0-100范围
    combined_score = (avg_immersion * 0.7 + max_immersion * 0.3) * 100
    
    return combined_score 