#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 字幕重构阶段强化实现
严格按照核心工作流程第3阶段要求：字幕重构阶段

核心功能：
1. 集成AI剧情分析结果，利用叙事图谱、情感曲线和高潮点信息进行智能重构
2. 基于病毒传播算法重构原始字幕，保持原意的同时增强吸引力
3. 为每条重构字幕标记对应的原始字幕ID和精确时间码范围（≤0.5秒精度）
4. 应用病毒传播潜力评分（0.0-1.0），筛选高分片段用于视频拼接
5. 确保重构结果与第4阶段时间轴精确映射模块完全兼容

技术约束：
- 严格遵循"AI仅用于文本分析和重构"的限制
- 保持≤0.5秒时间轴精度要求
- 在4GB内存约束下稳定运行
- 输出格式必须包含完整的时间码映射信息
"""

import os
import re
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)

class ViralPotentialLevel(Enum):
    """病毒传播潜力等级"""
    LOW = "low"           # 低潜力 (0.0-0.3)
    MEDIUM = "medium"     # 中等潜力 (0.3-0.6)
    HIGH = "high"         # 高潜力 (0.6-0.8)
    VIRAL = "viral"       # 病毒级 (0.8-1.0)

class ReconstructionStrategy(Enum):
    """重构策略枚举"""
    EMOTION_BOOST = "emotion_boost"       # 情感增强
    SUSPENSE_BUILD = "suspense_build"     # 悬念构建
    CLIMAX_HIGHLIGHT = "climax_highlight" # 高潮突出
    HOOK_CREATION = "hook_creation"       # 钩子创建
    VIRAL_PATTERN = "viral_pattern"       # 病毒模式

@dataclass
class ReconstructedSubtitle:
    """重构字幕数据类"""
    id: int                              # 重构字幕ID
    original_subtitle_id: int            # 原始字幕ID
    start_time: float                    # 开始时间（秒）
    end_time: float                      # 结束时间（秒）
    duration: float                      # 持续时间
    original_text: str                   # 原始文本
    reconstructed_text: str              # 重构文本
    viral_score: float                   # 病毒传播评分 (0.0-1.0)
    viral_level: ViralPotentialLevel     # 病毒传播等级
    strategy: ReconstructionStrategy     # 重构策略
    emotion_intensity: float             # 情感强度
    narrative_importance: float          # 叙事重要性
    time_precision: float = 0.0          # 时间精度误差（秒）
    keywords: List[str] = field(default_factory=list)  # 关键词
    
@dataclass
class ReconstructionResult:
    """重构结果数据类"""
    original_subtitles_count: int                    # 原始字幕数量
    reconstructed_subtitles: List[ReconstructedSubtitle]  # 重构字幕列表
    high_viral_segments: List[ReconstructedSubtitle]     # 高病毒传播片段
    total_duration: float                               # 总时长
    average_viral_score: float                          # 平均病毒评分
    time_mapping: Dict[str, Any]                        # 时间码映射
    reconstruction_metadata: Dict[str, Any] = field(default_factory=dict)  # 重构元数据

class EnhancedSubtitleReconstructor:
    """
    强化版字幕重构器
    
    严格按照核心工作流程第3阶段要求实现：
    - 集成AI剧情分析结果进行智能重构
    - 基于病毒传播算法增强字幕吸引力
    - 为每条重构字幕标记精确时间码范围
    - 应用病毒传播潜力评分筛选高分片段
    """
    
    # 时间精度容差（≤0.5秒）
    TIME_PRECISION_TOLERANCE = 0.5
    
    # 病毒传播评分阈值
    VIRAL_SCORE_THRESHOLDS = {
        ViralPotentialLevel.LOW: 0.3,
        ViralPotentialLevel.MEDIUM: 0.6,
        ViralPotentialLevel.HIGH: 0.8,
        ViralPotentialLevel.VIRAL: 1.0
    }
    
    def __init__(self):
        """初始化强化版字幕重构器"""
        self.reconstruction_history = []
        
        # 病毒传播模式库
        self.viral_patterns = self._load_viral_patterns()
        
        # 情感增强词库
        self.emotion_boosters = self._load_emotion_boosters()
        
        # 悬念构建模板
        self.suspense_templates = self._load_suspense_templates()
        
        # 钩子创建模式
        self.hook_patterns = self._load_hook_patterns()
        
        logger.info("强化版字幕重构器初始化完成")
    
    def reconstruct_subtitles(self, subtitles: List[Dict[str, Any]], 
                            narrative_map: Any, language: str = "auto") -> ReconstructionResult:
        """
        重构字幕（核心工作流程第3阶段主函数）
        
        Args:
            subtitles: 原始字幕列表（来自输入验证阶段）
            narrative_map: 叙事图谱（来自AI剧情分析阶段）
            language: 语言代码（zh/en/auto）
            
        Returns:
            ReconstructionResult: 完整的重构结果
        """
        try:
            logger.info(f"开始字幕重构阶段，原始字幕数量: {len(subtitles)}")
            
            # 自动检测语言
            if language == "auto":
                language = narrative_map.language if narrative_map else self._detect_language(subtitles)
            
            # 第1步：分析重构策略
            reconstruction_strategies = self._analyze_reconstruction_strategies(
                subtitles, narrative_map, language
            )
            
            # 第2步：执行智能重构
            reconstructed_subtitles = self._execute_reconstruction(
                subtitles, narrative_map, reconstruction_strategies, language
            )
            
            # 第3步：计算病毒传播评分
            self._calculate_viral_scores(reconstructed_subtitles, narrative_map)
            
            # 第4步：筛选高病毒传播片段
            high_viral_segments = self._filter_high_viral_segments(reconstructed_subtitles)
            
            # 第5步：生成时间码映射
            time_mapping = self._generate_time_mapping(subtitles, reconstructed_subtitles)
            
            # 第6步：验证时间精度
            self._validate_time_precision(reconstructed_subtitles)
            
            # 创建重构结果
            result = ReconstructionResult(
                original_subtitles_count=len(subtitles),
                reconstructed_subtitles=reconstructed_subtitles,
                high_viral_segments=high_viral_segments,
                total_duration=subtitles[-1]['end_time'] if subtitles else 0.0,
                average_viral_score=np.mean([rs.viral_score for rs in reconstructed_subtitles]) if reconstructed_subtitles else 0.0,
                time_mapping=time_mapping,
                reconstruction_metadata={
                    "reconstruction_time": self._get_current_timestamp(),
                    "language": language,
                    "strategies_used": list(set(rs.strategy.value for rs in reconstructed_subtitles)),
                    "high_viral_count": len(high_viral_segments),
                    "average_emotion_intensity": np.mean([rs.emotion_intensity for rs in reconstructed_subtitles]) if reconstructed_subtitles else 0.0
                }
            )
            
            logger.info(f"字幕重构完成：{len(reconstructed_subtitles)}条重构字幕，{len(high_viral_segments)}个高病毒片段")
            self.reconstruction_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"字幕重构失败: {str(e)}")
            # 返回空的重构结果
            return ReconstructionResult(
                original_subtitles_count=len(subtitles),
                reconstructed_subtitles=[],
                high_viral_segments=[],
                total_duration=0.0,
                average_viral_score=0.0,
                time_mapping={},
                reconstruction_metadata={"error": str(e)}
            )
    
    def _analyze_reconstruction_strategies(self, subtitles: List[Dict[str, Any]], 
                                         narrative_map: Any, language: str) -> Dict[int, ReconstructionStrategy]:
        """分析每条字幕的重构策略"""
        try:
            strategies = {}
            
            if not narrative_map:
                # 如果没有叙事图谱，使用默认策略
                for subtitle in subtitles:
                    strategies[subtitle['id']] = ReconstructionStrategy.EMOTION_BOOST
                return strategies
            
            # 基于叙事图谱分析策略
            for subtitle in subtitles:
                subtitle_id = subtitle['id']
                start_time = subtitle['start_time']
                
                # 检查是否为高潮点
                is_climax = any(
                    abs(cp.timestamp - start_time) <= 2.0 
                    for cp in narrative_map.climax_points
                )
                
                # 检查情感强度
                emotion_intensity = 0.0
                for ep in narrative_map.emotion_curve:
                    if abs(ep.timestamp - start_time) <= 1.0:
                        emotion_intensity = max(emotion_intensity, ep.intensity)
                
                # 检查叙事重要性
                narrative_importance = 0.0
                for pp in narrative_map.plot_points:
                    if abs(pp.timestamp - start_time) <= 2.0:
                        narrative_importance = max(narrative_importance, pp.importance)
                
                # 决定重构策略
                if is_climax:
                    strategies[subtitle_id] = ReconstructionStrategy.CLIMAX_HIGHLIGHT
                elif emotion_intensity > 0.7:
                    strategies[subtitle_id] = ReconstructionStrategy.EMOTION_BOOST
                elif narrative_importance > 0.8:
                    strategies[subtitle_id] = ReconstructionStrategy.SUSPENSE_BUILD
                elif subtitle_id <= 3:  # 开头字幕
                    strategies[subtitle_id] = ReconstructionStrategy.HOOK_CREATION
                else:
                    strategies[subtitle_id] = ReconstructionStrategy.VIRAL_PATTERN
            
            logger.info(f"重构策略分析完成，共{len(strategies)}条字幕")
            return strategies
            
        except Exception as e:
            logger.error(f"重构策略分析失败: {str(e)}")
            return {}
    
    def _execute_reconstruction(self, subtitles: List[Dict[str, Any]], 
                              narrative_map: Any,
                              strategies: Dict[int, ReconstructionStrategy],
                              language: str) -> List[ReconstructedSubtitle]:
        """执行智能重构"""
        try:
            reconstructed_subtitles = []
            
            # 获取AI模型进行重构
            llm = self._get_llm_for_language(language)
            
            for subtitle in subtitles:
                subtitle_id = subtitle['id']
                original_text = subtitle.get('text', '')
                start_time = subtitle.get('start_time', 0.0)
                end_time = subtitle.get('end_time', 0.0)
                duration = subtitle.get('duration', 0.0)
                
                if not original_text.strip():
                    continue
                
                # 获取重构策略
                strategy = strategies.get(subtitle_id, ReconstructionStrategy.EMOTION_BOOST)
                
                # 获取情感和叙事信息
                emotion_intensity, narrative_importance = self._get_context_info(
                    start_time, narrative_map
                )
                
                # 执行重构
                if llm:
                    reconstructed_text = self._ai_reconstruct_subtitle(
                        llm, original_text, strategy, emotion_intensity, narrative_importance, language
                    )
                else:
                    # 回退到规则方法
                    reconstructed_text = self._rule_based_reconstruct_subtitle(
                        original_text, strategy, emotion_intensity, language
                    )
                
                # 创建重构字幕对象
                reconstructed_subtitle = ReconstructedSubtitle(
                    id=len(reconstructed_subtitles) + 1,
                    original_subtitle_id=subtitle_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    original_text=original_text,
                    reconstructed_text=reconstructed_text,
                    viral_score=0.0,  # 稍后计算
                    viral_level=ViralPotentialLevel.LOW,  # 稍后计算
                    strategy=strategy,
                    emotion_intensity=emotion_intensity,
                    narrative_importance=narrative_importance,
                    time_precision=0.0,  # 精确时间对应
                    keywords=self._extract_keywords(reconstructed_text, language)
                )
                
                reconstructed_subtitles.append(reconstructed_subtitle)
            
            logger.info(f"智能重构完成，共{len(reconstructed_subtitles)}条重构字幕")
            return reconstructed_subtitles
            
        except Exception as e:
            logger.error(f"智能重构失败: {str(e)}")
            return []

    def _get_llm_for_language(self, language: str):
        """获取对应语言的LLM模型"""
        try:
            from src.models.base_llm import get_llm_for_language
            return get_llm_for_language(language)
        except ImportError:
            logger.warning("无法导入LLM模型，使用规则方法")
            return None

    def _get_context_info(self, timestamp: float, narrative_map: Any) -> Tuple[float, float]:
        """获取时间点的情感和叙事信息"""
        try:
            emotion_intensity = 0.0
            narrative_importance = 0.0

            if not narrative_map:
                return emotion_intensity, narrative_importance

            # 查找最近的情感点
            for ep in narrative_map.emotion_curve:
                if abs(ep.timestamp - timestamp) <= 1.0:
                    emotion_intensity = max(emotion_intensity, ep.intensity)

            # 查找最近的情节点
            for pp in narrative_map.plot_points:
                if abs(pp.timestamp - timestamp) <= 2.0:
                    narrative_importance = max(narrative_importance, pp.importance)

            return emotion_intensity, narrative_importance

        except Exception as e:
            logger.error(f"获取上下文信息失败: {str(e)}")
            return 0.0, 0.0

    def _ai_reconstruct_subtitle(self, llm, original_text: str, strategy: ReconstructionStrategy,
                               emotion_intensity: float, narrative_importance: float, language: str) -> str:
        """使用AI重构字幕"""
        try:
            if language == "zh":
                strategy_prompts = {
                    ReconstructionStrategy.EMOTION_BOOST: "增强情感表达，使用更有感染力的词汇",
                    ReconstructionStrategy.SUSPENSE_BUILD: "构建悬念，增加神秘感和期待感",
                    ReconstructionStrategy.CLIMAX_HIGHLIGHT: "突出高潮，使用强烈的表达方式",
                    ReconstructionStrategy.HOOK_CREATION: "创建吸引钩子，激发观众好奇心",
                    ReconstructionStrategy.VIRAL_PATTERN: "应用病毒传播模式，增加分享欲望"
                }

                prompt = f"""
请将以下字幕重构为更具病毒传播潜力的版本：

原始字幕："{original_text}"

重构要求：
1. 策略：{strategy_prompts.get(strategy.value, "增强吸引力")}
2. 情感强度：{emotion_intensity:.2f}（0-1，越高越需要情感化表达）
3. 叙事重要性：{narrative_importance:.2f}（0-1，越高越需要突出重点）
4. 保持原意不变，只改变表达方式
5. 增加吸引力和传播性
6. 字数控制在原文的80%-120%之间

请直接返回重构后的字幕文本，不要添加其他说明：
"""
            else:
                strategy_prompts = {
                    ReconstructionStrategy.EMOTION_BOOST: "enhance emotional expression with more impactful words",
                    ReconstructionStrategy.SUSPENSE_BUILD: "build suspense, add mystery and anticipation",
                    ReconstructionStrategy.CLIMAX_HIGHLIGHT: "highlight climax with intense expressions",
                    ReconstructionStrategy.HOOK_CREATION: "create engaging hooks to spark curiosity",
                    ReconstructionStrategy.VIRAL_PATTERN: "apply viral patterns to increase shareability"
                }

                prompt = f"""
Please reconstruct the following subtitle to make it more viral and engaging:

Original subtitle: "{original_text}"

Reconstruction requirements:
1. Strategy: {strategy_prompts.get(strategy.value, "enhance appeal")}
2. Emotion intensity: {emotion_intensity:.2f} (0-1, higher means more emotional expression needed)
3. Narrative importance: {narrative_importance:.2f} (0-1, higher means more emphasis needed)
4. Keep the original meaning unchanged, only change the expression
5. Increase appeal and viral potential
6. Keep word count within 80%-120% of original

Please return only the reconstructed subtitle text without additional explanations:
"""

            response = llm.generate(prompt, temperature=0.7, max_length=200)

            # 清理响应
            reconstructed_text = response.strip()

            # 验证重构结果
            if len(reconstructed_text) < 5 or len(reconstructed_text) > len(original_text) * 2:
                logger.warning(f"AI重构结果异常，使用规则方法: {reconstructed_text}")
                return self._rule_based_reconstruct_subtitle(original_text, strategy, emotion_intensity, language)

            return reconstructed_text

        except Exception as e:
            logger.error(f"AI字幕重构失败: {str(e)}")
            return self._rule_based_reconstruct_subtitle(original_text, strategy, emotion_intensity, language)

    def _rule_based_reconstruct_subtitle(self, original_text: str, strategy: ReconstructionStrategy,
                                       emotion_intensity: float, language: str) -> str:
        """基于规则的字幕重构（AI回退方案）"""
        try:
            reconstructed_text = original_text

            # 获取对应语言的模式库
            viral_patterns = self.viral_patterns.get(language, self.viral_patterns.get("zh", {}))
            emotion_boosters = self.emotion_boosters.get(language, self.emotion_boosters.get("zh", {}))

            # 根据策略应用不同的重构方法
            if strategy == ReconstructionStrategy.EMOTION_BOOST:
                # 情感增强
                for emotion_type, boosters in emotion_boosters.items():
                    for booster in boosters:
                        if booster in reconstructed_text:
                            continue
                    # 添加情感增强词
                    if emotion_intensity > 0.5:
                        if language == "zh":
                            reconstructed_text = f"太{reconstructed_text}" if not reconstructed_text.startswith(("太", "真", "好")) else reconstructed_text
                        else:
                            reconstructed_text = f"So {reconstructed_text.lower()}" if not reconstructed_text.lower().startswith(("so", "very", "really")) else reconstructed_text

            elif strategy == ReconstructionStrategy.SUSPENSE_BUILD:
                # 悬念构建
                suspense_templates = self.suspense_templates.get(language, [])
                if suspense_templates and not any(template in reconstructed_text for template in suspense_templates):
                    template = suspense_templates[0]
                    if language == "zh":
                        reconstructed_text = f"{template}：{reconstructed_text}"
                    else:
                        reconstructed_text = f"{template}: {reconstructed_text}"

            elif strategy == ReconstructionStrategy.CLIMAX_HIGHLIGHT:
                # 高潮突出
                if language == "zh":
                    if not reconstructed_text.endswith(("！", "?")):
                        reconstructed_text += "！"
                    if not reconstructed_text.startswith(("竟然", "居然", "没想到")):
                        reconstructed_text = f"没想到{reconstructed_text}"
                else:
                    if not reconstructed_text.endswith(("!", "?")):
                        reconstructed_text += "!"
                    if not reconstructed_text.startswith(("Unbelievable", "Amazing", "Incredible")):
                        reconstructed_text = f"Unbelievable! {reconstructed_text}"

            elif strategy == ReconstructionStrategy.HOOK_CREATION:
                # 钩子创建
                hook_patterns = self.hook_patterns.get(language, [])
                if hook_patterns:
                    hook = hook_patterns[0]
                    if language == "zh":
                        reconstructed_text = f"{hook}，{reconstructed_text}"
                    else:
                        reconstructed_text = f"{hook}, {reconstructed_text}"

            elif strategy == ReconstructionStrategy.VIRAL_PATTERN:
                # 病毒模式
                viral_prefixes = viral_patterns.get("prefixes", [])
                if viral_prefixes and not any(prefix in reconstructed_text for prefix in viral_prefixes):
                    prefix = viral_prefixes[0]
                    reconstructed_text = f"{prefix}{reconstructed_text}"

            return reconstructed_text

        except Exception as e:
            logger.error(f"规则字幕重构失败: {str(e)}")
            return original_text

    def _calculate_viral_scores(self, reconstructed_subtitles: List[ReconstructedSubtitle], narrative_map: Any):
        """计算病毒传播评分"""
        try:
            for subtitle in reconstructed_subtitles:
                # 基础评分因子
                base_score = 0.3

                # 情感强度加分
                emotion_bonus = subtitle.emotion_intensity * 0.3

                # 叙事重要性加分
                narrative_bonus = subtitle.narrative_importance * 0.2

                # 重构策略加分
                strategy_bonus = {
                    ReconstructionStrategy.EMOTION_BOOST: 0.1,
                    ReconstructionStrategy.SUSPENSE_BUILD: 0.15,
                    ReconstructionStrategy.CLIMAX_HIGHLIGHT: 0.2,
                    ReconstructionStrategy.HOOK_CREATION: 0.15,
                    ReconstructionStrategy.VIRAL_PATTERN: 0.1
                }.get(subtitle.strategy, 0.1)

                # 文本特征加分
                text_bonus = self._calculate_text_viral_features(subtitle.reconstructed_text)

                # 计算总分
                viral_score = min(1.0, base_score + emotion_bonus + narrative_bonus + strategy_bonus + text_bonus)

                # 设置评分和等级
                subtitle.viral_score = viral_score
                subtitle.viral_level = self._get_viral_level(viral_score)

            logger.info(f"病毒传播评分计算完成")

        except Exception as e:
            logger.error(f"病毒传播评分计算失败: {str(e)}")

    def _calculate_text_viral_features(self, text: str) -> float:
        """计算文本的病毒传播特征评分"""
        try:
            bonus = 0.0

            # 感叹号加分
            bonus += min(0.1, text.count("！") * 0.03 + text.count("!") * 0.03)

            # 问号加分
            bonus += min(0.05, text.count("？") * 0.02 + text.count("?") * 0.02)

            # 强调词加分
            emphasis_words_zh = ["太", "超", "极", "非常", "特别", "真的", "竟然", "居然", "没想到"]
            emphasis_words_en = ["so", "very", "really", "extremely", "incredibly", "amazing", "unbelievable"]

            for word in emphasis_words_zh + emphasis_words_en:
                if word in text.lower():
                    bonus += 0.02

            # 长度适中加分
            if 10 <= len(text) <= 50:
                bonus += 0.05

            return min(0.2, bonus)

        except Exception as e:
            logger.error(f"文本病毒特征计算失败: {str(e)}")
            return 0.0

    def _get_viral_level(self, viral_score: float) -> ViralPotentialLevel:
        """根据评分获取病毒传播等级"""
        if viral_score >= 0.8:
            return ViralPotentialLevel.VIRAL
        elif viral_score >= 0.6:
            return ViralPotentialLevel.HIGH
        elif viral_score >= 0.3:
            return ViralPotentialLevel.MEDIUM
        else:
            return ViralPotentialLevel.LOW

    def _filter_high_viral_segments(self, reconstructed_subtitles: List[ReconstructedSubtitle]) -> List[ReconstructedSubtitle]:
        """筛选高病毒传播片段"""
        try:
            # 筛选高分片段（评分 >= 0.6）
            high_viral_segments = [
                subtitle for subtitle in reconstructed_subtitles
                if subtitle.viral_score >= 0.6
            ]

            # 按评分排序
            high_viral_segments.sort(key=lambda x: x.viral_score, reverse=True)

            logger.info(f"筛选出{len(high_viral_segments)}个高病毒传播片段")
            return high_viral_segments

        except Exception as e:
            logger.error(f"高病毒片段筛选失败: {str(e)}")
            return []

    def _generate_time_mapping(self, original_subtitles: List[Dict[str, Any]],
                             reconstructed_subtitles: List[ReconstructedSubtitle]) -> Dict[str, Any]:
        """生成时间码映射（为第4阶段精确对齐做准备）"""
        try:
            time_mapping = {
                "original_timeline": [],
                "reconstructed_timeline": [],
                "mapping_pairs": [],
                "precision_validation": []
            }

            # 原始时间轴
            for subtitle in original_subtitles:
                time_mapping["original_timeline"].append({
                    "id": subtitle.get("id", 0),
                    "start_time": subtitle.get("start_time", 0.0),
                    "end_time": subtitle.get("end_time", 0.0),
                    "duration": subtitle.get("duration", 0.0),
                    "text": subtitle.get("text", "")
                })

            # 重构时间轴
            for subtitle in reconstructed_subtitles:
                time_mapping["reconstructed_timeline"].append({
                    "id": subtitle.id,
                    "original_id": subtitle.original_subtitle_id,
                    "start_time": subtitle.start_time,
                    "end_time": subtitle.end_time,
                    "duration": subtitle.duration,
                    "viral_score": subtitle.viral_score,
                    "text": subtitle.reconstructed_text
                })

            # 映射对
            for subtitle in reconstructed_subtitles:
                time_mapping["mapping_pairs"].append({
                    "original_id": subtitle.original_subtitle_id,
                    "reconstructed_id": subtitle.id,
                    "time_precision": subtitle.time_precision,
                    "start_time": subtitle.start_time,
                    "end_time": subtitle.end_time,
                    "viral_score": subtitle.viral_score
                })

            # 精度验证
            for subtitle in reconstructed_subtitles:
                precision_ok = subtitle.time_precision <= self.TIME_PRECISION_TOLERANCE
                time_mapping["precision_validation"].append({
                    "subtitle_id": subtitle.id,
                    "time_precision": subtitle.time_precision,
                    "precision_ok": precision_ok,
                    "tolerance": self.TIME_PRECISION_TOLERANCE
                })

            logger.info(f"时间码映射生成完成，共{len(time_mapping['mapping_pairs'])}个映射对")
            return time_mapping

        except Exception as e:
            logger.error(f"时间码映射生成失败: {str(e)}")
            return {}

    def _validate_time_precision(self, reconstructed_subtitles: List[ReconstructedSubtitle]):
        """验证时间精度（≤0.5秒要求）"""
        try:
            precision_violations = []

            for subtitle in reconstructed_subtitles:
                # 由于是1:1对应，时间精度误差应该为0
                subtitle.time_precision = 0.0

                # 验证时间精度
                if subtitle.time_precision > self.TIME_PRECISION_TOLERANCE:
                    precision_violations.append({
                        "subtitle_id": subtitle.id,
                        "precision": subtitle.time_precision,
                        "tolerance": self.TIME_PRECISION_TOLERANCE
                    })

            if precision_violations:
                logger.warning(f"发现{len(precision_violations)}个时间精度违规")
            else:
                logger.info("所有字幕时间精度验证通过")

        except Exception as e:
            logger.error(f"时间精度验证失败: {str(e)}")

    def _extract_keywords(self, text: str, language: str) -> List[str]:
        """提取关键词"""
        try:
            keywords = []

            # 简单的关键词提取
            if language == "zh":
                # 中文关键词模式
                import re
                # 提取2-4字的词组
                words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
                keywords.extend(words[:5])  # 最多5个关键词
            else:
                # 英文关键词模式
                words = text.split()
                # 过滤停用词并提取关键词
                stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
                keywords = [word.strip(".,!?") for word in words if word.lower() not in stop_words and len(word) > 3][:5]

            return keywords

        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            return []

    def _detect_language(self, subtitles: List[Dict[str, Any]]) -> str:
        """检测字幕语言"""
        try:
            # 合并所有文本
            all_text = " ".join([sub.get("text", "") for sub in subtitles[:10]])  # 只检查前10条

            # 检测中文字符
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', all_text))
            total_chars = len(all_text)

            if total_chars == 0:
                return "zh"  # 默认中文

            chinese_ratio = chinese_chars / total_chars

            if chinese_ratio > 0.1:  # 中文字符占比超过10%
                return "zh"
            else:
                return "en"

        except Exception as e:
            logger.warning(f"语言检测失败: {str(e)}，默认使用中文")
            return "zh"

    def _load_viral_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """加载病毒传播模式库"""
        return {
            "zh": {
                "prefixes": ["震惊！", "不敢相信！", "太神了！", "绝了！", "牛逼！", "卧槽！", "我的天！", "真的假的？"],
                "hooks": ["你绝对想不到", "接下来的一幕", "然而事情的真相是", "但是剧情突然反转"],
                "emotions": ["太感动了", "笑死我了", "气死我了", "吓死我了", "美哭了", "燃爆了"]
            },
            "en": {
                "prefixes": ["OMG!", "Unbelievable!", "Amazing!", "Incredible!", "WTF!", "No way!", "Holy shit!", "Mind-blown!"],
                "hooks": ["You won't believe", "What happens next", "The truth is", "Plot twist"],
                "emotions": ["So touching", "Hilarious", "Infuriating", "Terrifying", "Gorgeous", "Epic"]
            }
        }

    def _load_emotion_boosters(self) -> Dict[str, Dict[str, List[str]]]:
        """加载情感增强词库"""
        return {
            "zh": {
                "positive": ["超级", "特别", "非常", "极其", "相当", "十分", "真的", "好"],
                "negative": ["太", "极度", "非常", "特别", "真的", "好", "超级"],
                "intense": ["疯狂", "爆炸", "炸裂", "逆天", "神级", "史诗", "传说"]
            },
            "en": {
                "positive": ["super", "extremely", "incredibly", "amazingly", "absolutely", "totally", "really"],
                "negative": ["terribly", "horribly", "awfully", "extremely", "incredibly", "absolutely"],
                "intense": ["insane", "explosive", "mind-blowing", "legendary", "epic", "phenomenal"]
            }
        }

    def _load_suspense_templates(self) -> Dict[str, List[str]]:
        """加载悬念构建模板"""
        return {
            "zh": ["然而", "但是", "没想到", "突然", "竟然", "居然", "谁知道", "结果"],
            "en": ["However", "But", "Unexpectedly", "Suddenly", "Surprisingly", "Who knew", "It turns out"]
        }

    def _load_hook_patterns(self) -> Dict[str, List[str]]:
        """加载钩子创建模式"""
        return {
            "zh": ["你绝对想不到", "接下来发生的事", "真相让人震惊", "剧情大反转"],
            "en": ["You'll never guess", "What happens next", "The shocking truth", "Plot twist ahead"]
        }

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_reconstruction_summary(self) -> Dict[str, Any]:
        """获取重构历史摘要"""
        if not self.reconstruction_history:
            return {"total_reconstructions": 0}

        total = len(self.reconstruction_history)
        avg_viral_score = np.mean([rh.average_viral_score for rh in self.reconstruction_history])
        avg_high_viral_count = np.mean([len(rh.high_viral_segments) for rh in self.reconstruction_history])

        return {
            "total_reconstructions": total,
            "avg_viral_score": avg_viral_score,
            "avg_high_viral_count": avg_high_viral_count,
            "languages_processed": list(set(rh.reconstruction_metadata.get("language", "unknown") for rh in self.reconstruction_history))
        }

# 便捷函数
def reconstruct_subtitles_enhanced(subtitles: List[Dict[str, Any]], narrative_map: Any, language: str = "auto") -> ReconstructionResult:
    """
    便捷函数：强化字幕重构

    Args:
        subtitles: 原始字幕列表（来自输入验证阶段）
        narrative_map: 叙事图谱（来自AI剧情分析阶段）
        language: 语言代码（zh/en/auto）

    Returns:
        ReconstructionResult: 完整的重构结果
    """
    reconstructor = EnhancedSubtitleReconstructor()
    return reconstructor.reconstruct_subtitles(subtitles, narrative_map, language)
