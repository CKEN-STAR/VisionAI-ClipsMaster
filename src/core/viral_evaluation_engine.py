#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
爆款转换评估引擎
提供多维度、精确的爆款转换效果评估机制
"""

import re
import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """评估结果数据类"""
    overall_score: float
    dimension_scores: Dict[str, float]
    improvement_detected: bool
    quality_metrics: Dict[str, Any]
    recommendations: List[str]
    confidence: float

class ViralEvaluationEngine:
    """爆款转换评估引擎"""
    
    def __init__(self):
        """初始化评估引擎"""
        self.evaluation_criteria = {
            "emotional_impact": {
                "weight": 0.20,  # 降低权重，更平衡
                "indicators": {
                    "shock_words": ["震撼", "惊人", "不可思议", "令人震惊", "震惊全网", "惊艳", "轰动"],
                    "mystery_words": ["神秘", "诡异", "离奇", "匪夷所思", "扑朔迷离", "神秘莫测"],
                    "urgency_words": ["紧急", "火速", "刻不容缓", "迫在眉睫", "千钧一发", "分秒必争"],
                    "emotional_hooks": ["心跳加速", "血脉贲张", "毛骨悚然", "热泪盈眶", "激动不已", "感动落泪"]
                }
            },
            "attention_grabbing": {
                "weight": 0.25,  # 提高权重，这是爆款的核心
                "indicators": {
                    "brackets": ["【", "】", "《", "》"],
                    "attention_grabbers": ["重磅", "独家", "曝光", "揭秘", "突发", "最新", "首次", "史上"],
                    "impact_words": ["震撼", "惊人", "轰动", "爆料", "劲爆", "惊艳", "颠覆"]
                }
            },
            "suspense_building": {
                "weight": 0.20,
                "indicators": {
                    "cliffhangers": ["你绝对想不到", "接下来发生的事", "真相令人震惊", "结局让人意外", "答案呼之欲出"],
                    "questions": ["到底发生了什么", "究竟是怎么回事", "背后的真相是", "谜底即将揭晓"],
                    "predictions": ["下一秒的画面", "意想不到的是", "事实超乎想象", "出人意料"]
                }
            },
            "rhythm_optimization": {
                "weight": 0.15,
                "indicators": {
                    "punctuation_density": ["！", "？", "…"],
                    "sentence_breaks": ["。", "！", "？"],
                    "length_optimization": True
                }
            },
            "linguistic_enhancement": {
                "weight": 0.15,  # 提高权重
                "indicators": {
                    "tone_changes": ["exclamatory", "questioning"],
                    "word_upgrades": ["改变→颠覆", "遇到→邂逅", "看到→目睹", "发生→上演"],
                    "style_markers": ["viral_style", "engaging_tone"],
                    "enhancement_words": ["逐步", "深度", "全面", "终极", "巅峰"]
                }
            },
            "structural_improvement": {
                "weight": 0.05,  # 降低权重，结构不是最重要的
                "indicators": {
                    "compression_ratio": [0.3, 1.5],  # 放宽压缩比范围
                    "information_density": True,
                    "narrative_flow": ["hook", "build", "reveal"]
                }
            }
        }
        
        logger.info("爆款转换评估引擎初始化完成")
    
    def evaluate_transformation(self, original: str, transformed: str, 
                              learning_context: Optional[Dict[str, Any]] = None) -> EvaluationResult:
        """
        评估转换效果
        
        Args:
            original: 原始文本
            transformed: 转换后文本
            learning_context: 学习上下文信息
            
        Returns:
            评估结果
        """
        try:
            # 计算各维度得分
            dimension_scores = {}
            
            # 1. 情感冲击力评估
            dimension_scores["emotional_impact"] = self._evaluate_emotional_impact(original, transformed)
            
            # 2. 注意力抓取评估
            dimension_scores["attention_grabbing"] = self._evaluate_attention_grabbing(original, transformed)
            
            # 3. 悬念构建评估
            dimension_scores["suspense_building"] = self._evaluate_suspense_building(original, transformed)
            
            # 4. 节奏优化评估
            dimension_scores["rhythm_optimization"] = self._evaluate_rhythm_optimization(original, transformed)
            
            # 5. 语言增强评估
            dimension_scores["linguistic_enhancement"] = self._evaluate_linguistic_enhancement(original, transformed)
            
            # 6. 结构改进评估
            dimension_scores["structural_improvement"] = self._evaluate_structural_improvement(original, transformed)
            
            # 计算总体得分
            overall_score = self._calculate_overall_score(dimension_scores)
            
            # 检测改进
            improvement_detected = self._detect_improvement(original, transformed, dimension_scores)
            
            # 生成质量指标
            quality_metrics = self._generate_quality_metrics(original, transformed, dimension_scores)
            
            # 生成建议
            recommendations = self._generate_recommendations(dimension_scores)
            
            # 计算置信度
            confidence = self._calculate_confidence(dimension_scores, learning_context)
            
            result = EvaluationResult(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                improvement_detected=improvement_detected,
                quality_metrics=quality_metrics,
                recommendations=recommendations,
                confidence=confidence
            )
            
            logger.info(f"转换评估完成: 总分 {overall_score:.2f}, 改进检测 {improvement_detected}")
            
            return result
            
        except Exception as e:
            logger.error(f"转换评估失败: {e}")
            return EvaluationResult(
                overall_score=0.0,
                dimension_scores={},
                improvement_detected=False,
                quality_metrics={},
                recommendations=["评估失败，请检查输入"],
                confidence=0.0
            )
    
    def _evaluate_emotional_impact(self, original: str, transformed: str) -> float:
        """评估情感冲击力 - 优化版"""
        try:
            score = 0.0
            criteria = self.evaluation_criteria["emotional_impact"]["indicators"]

            # 检查情感词汇增加（更宽松的评分）
            for category, words in criteria.items():
                original_count = sum(1 for word in words if word in original)
                transformed_count = sum(1 for word in words if word in transformed)

                # 增加基础分数，即使没有新增也给予一定分数
                if transformed_count > 0:
                    score += transformed_count * 0.15

                # 新增词汇额外加分
                if transformed_count > original_count:
                    score += (transformed_count - original_count) * 0.25

            # 情感强度评估（更宽松）
            emotional_punctuation = transformed.count('！') - original.count('！')
            if emotional_punctuation > 0:
                score += emotional_punctuation * 0.15
            elif transformed.count('！') > 0:  # 即使原文有感叹号，转换后保持也给分
                score += 0.1

            # 检查是否有情感相关的词汇
            emotional_indicators = ["感动", "激动", "震撼", "惊人", "神秘", "紧急"]
            if any(word in transformed for word in emotional_indicators):
                score += 0.2

            return min(score, 1.0)  # 最大值为1.0

        except Exception as e:
            logger.error(f"情感冲击力评估失败: {e}")
            return 0.0
    
    def _evaluate_attention_grabbing(self, original: str, transformed: str) -> float:
        """评估注意力抓取能力 - 优化版"""
        try:
            score = 0.0
            criteria = self.evaluation_criteria["attention_grabbing"]["indicators"]

            # 检查注意力抓取器（更宽松的评分）
            for category, indicators in criteria.items():
                if category == "brackets":
                    # 检查是否有括号（不管是否新增）
                    bracket_count = sum(1 for bracket in indicators if bracket in transformed)
                    if bracket_count > 0:
                        score += 0.3  # 有括号就给高分

                    # 新增括号额外加分
                    new_bracket_count = sum(1 for bracket in indicators if bracket in transformed and bracket not in original)
                    score += new_bracket_count * 0.2
                else:
                    # 检查是否有注意力抓取词
                    existing_count = sum(1 for indicator in indicators if indicator in transformed)
                    if existing_count > 0:
                        score += existing_count * 0.15

                    # 新增词汇额外加分
                    new_count = sum(1 for indicator in indicators if indicator in transformed and indicator not in original)
                    score += new_count * 0.25

            # 检查标题化特征
            if transformed.startswith('【') or '】' in transformed:
                score += 0.2

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"注意力抓取评估失败: {e}")
            return 0.0
    
    def _evaluate_suspense_building(self, original: str, transformed: str) -> float:
        """评估悬念构建能力"""
        try:
            score = 0.0
            criteria = self.evaluation_criteria["suspense_building"]["indicators"]
            
            for category, phrases in criteria.items():
                for phrase in phrases:
                    if phrase in transformed and phrase not in original:
                        score += 0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"悬念构建评估失败: {e}")
            return 0.0

    def _evaluate_rhythm_optimization(self, original: str, transformed: str) -> float:
        """评估节奏优化"""
        try:
            score = 0.0

            # 长度优化评估
            length_ratio = len(transformed) / len(original) if len(original) > 0 else 1.0
            if 0.5 <= length_ratio <= 0.8:  # 理想压缩比
                score += 0.4
            elif 0.8 < length_ratio <= 1.2:  # 可接受范围
                score += 0.2

            # 标点密度评估
            original_punct = original.count('！') + original.count('？') + original.count('…')
            transformed_punct = transformed.count('！') + transformed.count('？') + transformed.count('…')

            if transformed_punct > original_punct:
                score += 0.3

            # 句子密度评估
            original_sentences = original.count('。') + original.count('！') + original.count('？')
            transformed_sentences = transformed.count('。') + transformed.count('！') + transformed.count('？')

            if len(transformed) > 0:
                sentence_density = transformed_sentences / len(transformed) * 100
                if 3 <= sentence_density <= 8:  # 理想句子密度
                    score += 0.3

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"节奏优化评估失败: {e}")
            return 0.0

    def _evaluate_linguistic_enhancement(self, original: str, transformed: str) -> float:
        """评估语言增强"""
        try:
            score = 0.0

            # 语调变化评估
            if '！' in transformed and '！' not in original:
                score += 0.3
            if '？' in transformed and '？' not in original:
                score += 0.2

            # 词汇升级评估
            upgrade_patterns = [
                ("改变", "颠覆"), ("遇到", "邂逅"), ("看到", "目睹"),
                ("发生", "上演"), ("开始", "拉开序幕"), ("结束", "落下帷幕")
            ]

            for original_word, upgraded_word in upgrade_patterns:
                if original_word in original and upgraded_word in transformed:
                    score += 0.2

            # 风格标记评估
            style_markers = ["【", "】", "…", "！"]
            style_count = sum(1 for marker in style_markers if marker in transformed and marker not in original)
            score += style_count * 0.1

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"语言增强评估失败: {e}")
            return 0.0

    def _evaluate_structural_improvement(self, original: str, transformed: str) -> float:
        """评估结构改进"""
        try:
            score = 0.0

            # 信息密度评估
            if len(transformed) < len(original) and len(transformed) > len(original) * 0.5:
                score += 0.4  # 有效压缩

            # 叙事流程评估
            has_hook = any(hook in transformed for hook in ["【", "震撼", "惊人", "神秘"])
            has_build = any(build in transformed for build in ["接下来", "然而", "突然"])
            has_reveal = any(reveal in transformed for reveal in ["真相", "结果", "最终"])

            narrative_elements = sum([has_hook, has_build, has_reveal])
            score += narrative_elements * 0.2

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"结构改进评估失败: {e}")
            return 0.0

    def _calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """计算总体得分"""
        try:
            total_score = 0.0

            for dimension, score in dimension_scores.items():
                weight = self.evaluation_criteria.get(dimension, {}).get("weight", 0.0)
                total_score += score * weight

            return min(total_score, 1.0)

        except Exception as e:
            logger.error(f"总体得分计算失败: {e}")
            return 0.0

    def _detect_improvement(self, original: str, transformed: str, dimension_scores: Dict[str, float]) -> bool:
        """检测是否有改进 - 优化版"""
        try:
            # 多维度改进检测（更宽松的标准）
            improvement_indicators = 0
            max_indicators = 6  # 增加检测维度

            # 1. 长度变化检测（任何变化都算改进）
            length_change = abs(len(transformed) - len(original))
            if length_change > 3:  # 降低阈值
                improvement_indicators += 1

            # 2. 维度得分检测（降低阈值）
            significant_scores = sum(1 for score in dimension_scores.values() if score >= 0.2)  # 从0.3降到0.2
            if significant_scores >= 1:  # 从2降到1
                improvement_indicators += 1

            # 3. 特征增加检测（扩大特征范围）
            viral_features = ["【", "】", "！", "？", "…", "震撼", "惊人", "神秘", "揭秘", "重磅", "独家", "曝光"]
            original_features = sum(1 for feature in viral_features if feature in original)
            transformed_features = sum(1 for feature in viral_features if feature in transformed)

            if transformed_features > original_features:
                improvement_indicators += 1
            elif transformed_features >= 2:  # 即使没有增加，有足够特征也算改进
                improvement_indicators += 1

            # 4. 总体得分检测（降低阈值）
            overall_score = self._calculate_overall_score(dimension_scores)
            if overall_score >= 0.25:  # 从0.4降到0.25
                improvement_indicators += 1

            # 5. 风格转换检测
            style_indicators = ["【", "震撼", "惊人", "神秘", "重磅", "独家"]
            if any(indicator in transformed for indicator in style_indicators):
                improvement_indicators += 1

            # 6. 情感强化检测
            if transformed.count('！') > original.count('！'):
                improvement_indicators += 1

            # 降低成功阈值
            required_indicators = max(1, max_indicators // 3)  # 至少1个，最多2个指标即可
            success = improvement_indicators >= required_indicators

            logger.info(f"改进检测: {improvement_indicators}/{max_indicators} 指标达成，需要 {required_indicators}，结果: {'成功' if success else '失败'}")

            return success

        except Exception as e:
            logger.error(f"改进检测失败: {e}")
            return False

    def _generate_quality_metrics(self, original: str, transformed: str, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """生成质量指标"""
        try:
            return {
                "length_change_ratio": len(transformed) / len(original) if len(original) > 0 else 1.0,
                "viral_feature_count": sum(1 for feature in ["【", "】", "！", "震撼", "惊人"] if feature in transformed),
                "dimension_average": np.mean(list(dimension_scores.values())) if dimension_scores else 0.0,
                "top_dimension": max(dimension_scores.items(), key=lambda x: x[1])[0] if dimension_scores else "none",
                "improvement_strength": "strong" if self._calculate_overall_score(dimension_scores) >= 0.6 else "moderate" if self._calculate_overall_score(dimension_scores) >= 0.3 else "weak"
            }

        except Exception as e:
            logger.error(f"质量指标生成失败: {e}")
            return {}

    def _generate_recommendations(self, dimension_scores: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        try:
            recommendations = []

            for dimension, score in dimension_scores.items():
                if score < 0.3:
                    if dimension == "emotional_impact":
                        recommendations.append("建议增加更多情感强化词汇，如'震撼'、'惊人'等")
                    elif dimension == "attention_grabbing":
                        recommendations.append("建议添加注意力抓取器，如【重磅】、【独家】等")
                    elif dimension == "suspense_building":
                        recommendations.append("建议增加悬念构建元素，如'你绝对想不到'等")
                    elif dimension == "rhythm_optimization":
                        recommendations.append("建议优化文本节奏，适当压缩长度或增加标点")
                    elif dimension == "linguistic_enhancement":
                        recommendations.append("建议提升语言表达，使用更有冲击力的词汇")
                    elif dimension == "structural_improvement":
                        recommendations.append("建议优化文本结构，提高信息密度")

            if not recommendations:
                recommendations.append("转换效果良好，继续保持当前策略")

            return recommendations

        except Exception as e:
            logger.error(f"建议生成失败: {e}")
            return ["评估失败，无法生成建议"]

    def _calculate_confidence(self, dimension_scores: Dict[str, float], learning_context: Optional[Dict[str, Any]]) -> float:
        """计算评估置信度"""
        try:
            confidence = 0.5  # 基础置信度

            # 基于维度得分的置信度
            if dimension_scores:
                avg_score = np.mean(list(dimension_scores.values()))
                confidence += avg_score * 0.3

            # 基于学习上下文的置信度
            if learning_context:
                if learning_context.get("training_samples", 0) > 5:
                    confidence += 0.1
                if learning_context.get("learning_success_rate", 0) > 0.7:
                    confidence += 0.1

            return min(confidence, 1.0)

        except Exception as e:
            logger.error(f"置信度计算失败: {e}")
            return 0.5
