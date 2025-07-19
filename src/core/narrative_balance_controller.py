#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能长度平衡控制系统

该模块实现VisionAI-ClipsMaster的核心长度控制逻辑，确保生成的视频：
1. 避免过短导致剧情不连贯
2. 避免过长与原片相差不大
3. 保持最佳的病毒式传播长度
4. 维护剧情的完整性和吸引力

主要功能：
- 剧情连贯性评分算法
- 视频时长优化器
- 节奏分析器集成
- 智能片段选择
- 质量检查机制
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class VideoLengthCategory(Enum):
    """视频长度分类"""
    TOO_SHORT = "too_short"      # <30秒，剧情不连贯
    OPTIMAL_SHORT = "optimal_short"  # 30-90秒，最佳短视频长度
    MEDIUM = "medium"            # 90-180秒，中等长度
    LONG = "long"               # 180-300秒，较长视频
    TOO_LONG = "too_long"       # >300秒，与原片差异不大

@dataclass
class NarrativeSegment:
    """叙事片段数据结构"""
    start_time: float
    end_time: float
    text: str
    importance_score: float
    emotion_intensity: float
    plot_relevance: float
    viral_potential: float

@dataclass
class BalanceMetrics:
    """平衡控制指标"""
    coherence_score: float      # 连贯性评分 (0-1)
    length_ratio: float         # 与原片长度比例
    viral_score: float          # 病毒式传播潜力 (0-1)
    rhythm_score: float         # 节奏评分 (0-1)
    quality_score: float        # 综合质量评分 (0-1)

class NarrativeBalanceController:
    """智能长度平衡控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.min_duration = 30.0    # 最小时长（秒）
        self.max_duration = 300.0   # 最大时长（秒）
        self.optimal_range = (60.0, 120.0)  # 最佳时长范围
        self.min_coherence_score = 0.6  # 最小连贯性要求
        self.target_length_ratio = (0.3, 0.7)  # 目标长度比例范围
        
        logger.info("智能长度平衡控制器初始化完成")

    def analyze_and_optimize(self, original_segments: List[Dict[str, Any]], 
                           reconstructed_segments: List[Dict[str, Any]],
                           language: str = "zh") -> Dict[str, Any]:
        """
        分析并优化视频长度平衡
        
        Args:
            original_segments: 原始视频片段
            reconstructed_segments: 重构后的片段
            language: 语言代码
            
        Returns:
            Dict: 优化结果和建议
        """
        try:
            logger.info("开始智能长度平衡分析...")
            
            # 第一步：计算基础指标
            original_duration = self._calculate_total_duration(original_segments)
            reconstructed_duration = self._calculate_total_duration(reconstructed_segments)
            
            logger.debug(f"原片时长: {original_duration:.2f}秒, 重构后时长: {reconstructed_duration:.2f}秒")
            
            # 第二步：剧情连贯性评分
            coherence_score = self._calculate_coherence_score(reconstructed_segments, language)
            
            # 第三步：长度分类和评估
            length_category = self._classify_video_length(reconstructed_duration)
            length_ratio = reconstructed_duration / original_duration if original_duration > 0 else 1.0
            
            # 第四步：病毒式传播潜力评估
            viral_score = self._assess_viral_potential(reconstructed_segments, reconstructed_duration, language)
            
            # 第五步：节奏分析
            rhythm_score = self._analyze_rhythm_quality(reconstructed_segments, language)
            
            # 第六步：综合质量评分
            quality_score = self._calculate_overall_quality(
                coherence_score, length_ratio, viral_score, rhythm_score
            )
            
            # 第七步：生成优化建议
            optimization_suggestions = self._generate_optimization_suggestions(
                length_category, coherence_score, length_ratio, viral_score, rhythm_score
            )
            
            # 第八步：如果需要，执行自动优化
            optimized_segments = self._auto_optimize_if_needed(
                reconstructed_segments, length_category, coherence_score, language
            )
            
            # 构建结果
            balance_metrics = BalanceMetrics(
                coherence_score=coherence_score,
                length_ratio=length_ratio,
                viral_score=viral_score,
                rhythm_score=rhythm_score,
                quality_score=quality_score
            )
            
            result = {
                "original_duration": original_duration,
                "reconstructed_duration": reconstructed_duration,
                "optimized_duration": self._calculate_total_duration(optimized_segments),
                "length_category": length_category.value,
                "balance_metrics": balance_metrics.__dict__,
                "optimization_suggestions": optimization_suggestions,
                "optimized_segments": optimized_segments,
                "quality_assessment": self._generate_quality_assessment(balance_metrics),
                "recommendations": self._generate_recommendations(balance_metrics, length_category)
            }
            
            logger.info(f"长度平衡分析完成，质量评分: {quality_score:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"长度平衡分析失败: {e}")
            return {
                "error": str(e),
                "original_segments": original_segments,
                "reconstructed_segments": reconstructed_segments
            }

    def _calculate_total_duration(self, segments: List[Dict[str, Any]]) -> float:
        """计算总时长"""
        try:
            if not segments:
                return 0.0
            
            total_duration = 0.0
            for segment in segments:
                start_time = segment.get("start_time", 0)
                end_time = segment.get("end_time", 0)
                duration = end_time - start_time
                if duration > 0:
                    total_duration += duration
            
            return total_duration
            
        except Exception as e:
            logger.error(f"计算总时长失败: {e}")
            return 0.0

    def _calculate_coherence_score(self, segments: List[Dict[str, Any]], language: str) -> float:
        """
        计算剧情连贯性评分
        
        基于语义相似度和逻辑连接强度评估剧情连贯性
        """
        try:
            if len(segments) < 2:
                return 1.0  # 单个片段默认连贯
            
            coherence_scores = []
            
            for i in range(len(segments) - 1):
                current_text = segments[i].get("text", "")
                next_text = segments[i + 1].get("text", "")
                
                # 计算语义连接强度
                semantic_connection = self._calculate_semantic_connection(
                    current_text, next_text, language
                )
                
                # 计算时间连续性
                time_continuity = self._calculate_time_continuity(
                    segments[i], segments[i + 1]
                )
                
                # 综合连贯性评分
                segment_coherence = (semantic_connection * 0.7 + time_continuity * 0.3)
                coherence_scores.append(segment_coherence)
            
            # 计算平均连贯性
            avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
            
            # 应用长度惩罚（过短的视频连贯性天然较低）
            total_duration = self._calculate_total_duration(segments)
            length_penalty = min(total_duration / 60.0, 1.0)  # 60秒以下有惩罚
            
            final_coherence = avg_coherence * length_penalty
            
            logger.debug(f"连贯性评分: {final_coherence:.3f} (平均: {avg_coherence:.3f}, 长度惩罚: {length_penalty:.3f})")
            return final_coherence
            
        except Exception as e:
            logger.error(f"计算连贯性评分失败: {e}")
            return 0.0

    def _classify_video_length(self, duration: float) -> VideoLengthCategory:
        """分类视频长度"""
        if duration < 30:
            return VideoLengthCategory.TOO_SHORT
        elif duration <= 90:
            return VideoLengthCategory.OPTIMAL_SHORT
        elif duration <= 180:
            return VideoLengthCategory.MEDIUM
        elif duration <= 300:
            return VideoLengthCategory.LONG
        else:
            return VideoLengthCategory.TOO_LONG

    def _assess_viral_potential(self, segments: List[Dict[str, Any]], 
                              duration: float, language: str) -> float:
        """评估病毒式传播潜力"""
        try:
            # 时长因子（60-120秒最佳）
            if 60 <= duration <= 120:
                duration_factor = 1.0
            elif 30 <= duration < 60 or 120 < duration <= 180:
                duration_factor = 0.8
            elif duration < 30:
                duration_factor = 0.4
            else:
                duration_factor = 0.6
            
            # 内容吸引力因子
            attraction_keywords = {
                "zh": ["震撼", "不敢相信", "惊人", "意外", "反转", "真相", "秘密"],
                "en": ["shocking", "unbelievable", "amazing", "unexpected", "twist", "truth", "secret"]
            }
            
            keywords = attraction_keywords.get(language, attraction_keywords["zh"])
            
            content_factor = 0.0
            total_text = " ".join([seg.get("text", "") for seg in segments])
            
            for keyword in keywords:
                if keyword in total_text.lower():
                    content_factor += 0.15
            
            content_factor = min(content_factor, 1.0)
            
            # 节奏因子
            rhythm_factor = self._calculate_rhythm_factor(segments)
            
            # 综合病毒潜力
            viral_potential = (duration_factor * 0.4 + content_factor * 0.4 + rhythm_factor * 0.2)
            
            logger.debug(f"病毒潜力: {viral_potential:.3f} (时长: {duration_factor:.3f}, 内容: {content_factor:.3f}, 节奏: {rhythm_factor:.3f})")
            return viral_potential
            
        except Exception as e:
            logger.error(f"评估病毒潜力失败: {e}")
            return 0.0

    def _analyze_rhythm_quality(self, segments: List[Dict[str, Any]], language: str) -> float:
        """分析节奏质量"""
        try:
            if not segments:
                return 0.0
            
            # 计算片段时长分布
            durations = []
            for segment in segments:
                duration = segment.get("end_time", 0) - segment.get("start_time", 0)
                if duration > 0:
                    durations.append(duration)
            
            if not durations:
                return 0.0
            
            # 计算节奏变化
            avg_duration = sum(durations) / len(durations)
            rhythm_variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
            rhythm_std = math.sqrt(rhythm_variance)
            
            # 理想的节奏应该有适度的变化
            ideal_std = avg_duration * 0.3  # 30%的标准差被认为是理想的
            rhythm_score = 1.0 - abs(rhythm_std - ideal_std) / max(ideal_std, 0.1)
            rhythm_score = max(0.0, min(1.0, rhythm_score))
            
            logger.debug(f"节奏评分: {rhythm_score:.3f} (平均时长: {avg_duration:.2f}s, 标准差: {rhythm_std:.2f}s)")
            return rhythm_score

        except Exception as e:
            logger.error(f"分析节奏质量失败: {e}")
            return 0.0

    def _calculate_overall_quality(self, coherence: float, length_ratio: float,
                                 viral: float, rhythm: float) -> float:
        """计算综合质量评分"""
        try:
            # 长度比例评分
            if 0.3 <= length_ratio <= 0.7:
                length_score = 1.0
            elif 0.2 <= length_ratio < 0.3 or 0.7 < length_ratio <= 0.8:
                length_score = 0.8
            elif length_ratio < 0.2:
                length_score = 0.4  # 过短惩罚
            else:
                length_score = 0.6  # 过长惩罚

            # 加权综合评分
            weights = {
                "coherence": 0.35,    # 连贯性最重要
                "length": 0.25,      # 长度控制重要
                "viral": 0.25,       # 病毒潜力重要
                "rhythm": 0.15       # 节奏相对次要
            }

            quality_score = (
                coherence * weights["coherence"] +
                length_score * weights["length"] +
                viral * weights["viral"] +
                rhythm * weights["rhythm"]
            )

            return min(1.0, max(0.0, quality_score))

        except Exception:
            return 0.5

    def _generate_optimization_suggestions(self, length_category: VideoLengthCategory,
                                         coherence: float, length_ratio: float,
                                         viral: float, rhythm: float) -> List[str]:
        """生成优化建议"""
        suggestions = []

        try:
            # 长度相关建议
            if length_category == VideoLengthCategory.TOO_SHORT:
                suggestions.append("视频过短，建议增加关键剧情片段以提升连贯性")
                suggestions.append("考虑添加背景信息或角色介绍片段")
            elif length_category == VideoLengthCategory.TOO_LONG:
                suggestions.append("视频过长，建议删除次要片段以突出核心剧情")
                suggestions.append("考虑提高剪辑节奏，减少冗余内容")

            # 连贯性建议
            if coherence < 0.6:
                suggestions.append("剧情连贯性较低，建议添加过渡片段")
                suggestions.append("检查片段间的逻辑连接，确保故事流畅")

            # 病毒潜力建议
            if viral < 0.5:
                suggestions.append("病毒传播潜力较低，建议增强开头的吸引力")
                suggestions.append("考虑添加更多悬念或反转元素")

            # 节奏建议
            if rhythm < 0.5:
                suggestions.append("视频节奏需要优化，建议调整片段时长分布")
                suggestions.append("考虑在高潮部分使用更短的片段增强紧张感")

            # 长度比例建议
            if length_ratio < 0.3:
                suggestions.append("与原片相比过短，可能丢失重要剧情信息")
            elif length_ratio > 0.7:
                suggestions.append("与原片相比过长，建议进一步精简内容")

            return suggestions

        except Exception as e:
            logger.error(f"生成优化建议失败: {e}")
            return ["建议重新分析视频结构"]

    def _auto_optimize_if_needed(self, segments: List[Dict[str, Any]],
                               length_category: VideoLengthCategory,
                               coherence: float, language: str) -> List[Dict[str, Any]]:
        """如果需要，执行自动优化"""
        try:
            # 如果质量已经足够好，不需要优化
            if (length_category in [VideoLengthCategory.OPTIMAL_SHORT, VideoLengthCategory.MEDIUM]
                and coherence >= 0.6):
                return segments

            optimized_segments = segments.copy()

            # 处理过短的情况
            if length_category == VideoLengthCategory.TOO_SHORT:
                optimized_segments = self._extend_segments(optimized_segments, language)

            # 处理过长的情况
            elif length_category == VideoLengthCategory.TOO_LONG:
                optimized_segments = self._compress_segments(optimized_segments, language)

            # 处理连贯性问题
            if coherence < 0.6:
                optimized_segments = self._improve_coherence(optimized_segments, language)

            return optimized_segments

        except Exception as e:
            logger.error(f"自动优化失败: {e}")
            return segments

    def _calculate_semantic_connection(self, text1: str, text2: str, language: str) -> float:
        """计算语义连接强度"""
        try:
            # 简化的语义连接计算
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            if not words1 or not words2:
                return 0.0

            # 计算词汇重叠度
            overlap = len(words1 & words2)
            total_unique = len(words1 | words2)

            overlap_score = overlap / total_unique if total_unique > 0 else 0.0

            # 检查连接词
            connectors = {
                "zh": ["然后", "接着", "于是", "因此", "但是", "然而", "最后"],
                "en": ["then", "next", "therefore", "but", "however", "finally"]
            }

            connector_list = connectors.get(language, connectors["zh"])
            has_connector = any(conn in text2.lower() for conn in connector_list)

            connector_bonus = 0.3 if has_connector else 0.0

            return min(1.0, overlap_score + connector_bonus)

        except Exception:
            return 0.0

    def _calculate_time_continuity(self, segment1: Dict[str, Any], segment2: Dict[str, Any]) -> float:
        """计算时间连续性"""
        try:
            end_time1 = segment1.get("end_time", 0)
            start_time2 = segment2.get("start_time", 0)

            # 计算时间间隔
            time_gap = abs(start_time2 - end_time1)

            # 时间间隔越小，连续性越好
            if time_gap <= 1.0:  # 1秒内认为是连续的
                return 1.0
            elif time_gap <= 5.0:  # 5秒内认为是较好的
                return 0.8
            elif time_gap <= 10.0:  # 10秒内认为是可接受的
                return 0.6
            else:
                return 0.3  # 超过10秒认为连续性较差

        except Exception:
            return 0.0

    def _calculate_rhythm_factor(self, segments: List[Dict[str, Any]]) -> float:
        """计算节奏因子"""
        try:
            if len(segments) < 3:
                return 0.5  # 片段太少无法评估节奏

            durations = []
            for segment in segments:
                duration = segment.get("end_time", 0) - segment.get("start_time", 0)
                if duration > 0:
                    durations.append(duration)

            if len(durations) < 3:
                return 0.5

            # 计算节奏变化模式
            rhythm_changes = []
            for i in range(len(durations) - 1):
                change = durations[i + 1] - durations[i]
                rhythm_changes.append(change)

            # 理想的节奏应该有变化但不过于剧烈
            avg_change = sum(abs(change) for change in rhythm_changes) / len(rhythm_changes)
            avg_duration = sum(durations) / len(durations)

            # 变化幅度在平均时长的20%-50%之间被认为是理想的
            ideal_change_range = (avg_duration * 0.2, avg_duration * 0.5)

            if ideal_change_range[0] <= avg_change <= ideal_change_range[1]:
                return 1.0
            elif avg_change < ideal_change_range[0]:
                return 0.7  # 节奏过于平缓
            else:
                return 0.6  # 节奏过于剧烈

        except Exception:
            return 0.5

    def _extend_segments(self, segments: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """扩展片段以增加时长"""
        try:
            extended_segments = []

            for segment in segments:
                extended_segment = segment.copy()

                # 适度延长片段时长
                duration = segment.get("end_time", 0) - segment.get("start_time", 0)
                if duration > 0:
                    extension = min(duration * 0.2, 2.0)  # 最多延长20%或2秒
                    extended_segment["end_time"] = segment.get("end_time", 0) + extension

                extended_segments.append(extended_segment)

            return extended_segments

        except Exception as e:
            logger.error(f"扩展片段失败: {e}")
            return segments

    def _compress_segments(self, segments: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """压缩片段以减少时长"""
        try:
            # 计算重要性评分
            scored_segments = []
            for i, segment in enumerate(segments):
                importance = self._calculate_segment_importance(segment, i, len(segments), language)
                scored_segments.append((importance, segment))

            # 按重要性排序
            scored_segments.sort(key=lambda x: x[0], reverse=True)

            # 保留最重要的70%片段
            keep_count = max(1, int(len(scored_segments) * 0.7))
            compressed_segments = [seg for _, seg in scored_segments[:keep_count]]

            # 按原始顺序重新排列
            compressed_segments.sort(key=lambda x: x.get("start_time", 0))

            return compressed_segments

        except Exception as e:
            logger.error(f"压缩片段失败: {e}")
            return segments

    def _improve_coherence(self, segments: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """改善连贯性"""
        try:
            if len(segments) < 2:
                return segments

            improved_segments = []

            for i, segment in enumerate(segments):
                improved_segment = segment.copy()

                # 为非第一个片段添加连接词
                if i > 0:
                    text = segment.get("text", "")
                    if text and not self._has_connector(text, language):
                        connectors = {
                            "zh": ["然后", "接着", "于是"],
                            "en": ["then", "next", "so"]
                        }
                        connector_list = connectors.get(language, connectors["zh"])
                        connector = connector_list[i % len(connector_list)]
                        improved_segment["text"] = f"{connector}，{text}"

                improved_segments.append(improved_segment)

            return improved_segments

        except Exception as e:
            logger.error(f"改善连贯性失败: {e}")
            return segments

    def _calculate_segment_importance(self, segment: Dict[str, Any], index: int,
                                    total_count: int, language: str) -> float:
        """计算片段重要性"""
        try:
            text = segment.get("text", "")

            # 位置重要性（开头和结尾更重要）
            if index == 0 or index == total_count - 1:
                position_score = 1.0
            elif index < total_count * 0.3 or index > total_count * 0.7:
                position_score = 0.8
            else:
                position_score = 0.6

            # 内容重要性
            important_keywords = {
                "zh": ["重要", "关键", "核心", "主要", "突然", "意外", "结果", "最后"],
                "en": ["important", "key", "main", "suddenly", "unexpected", "result", "finally"]
            }

            keywords = important_keywords.get(language, important_keywords["zh"])
            content_score = sum(0.1 for keyword in keywords if keyword in text.lower())
            content_score = min(1.0, content_score)

            # 长度重要性（适中长度更重要）
            duration = segment.get("end_time", 0) - segment.get("start_time", 0)
            if 2.0 <= duration <= 8.0:
                length_score = 1.0
            elif duration < 1.0 or duration > 15.0:
                length_score = 0.3
            else:
                length_score = 0.7

            # 综合重要性
            importance = (position_score * 0.4 + content_score * 0.4 + length_score * 0.2)
            return importance

        except Exception:
            return 0.5

    def _has_connector(self, text: str, language: str) -> bool:
        """检查文本是否包含连接词"""
        connectors = {
            "zh": ["然后", "接着", "于是", "因此", "但是", "然而", "最后", "首先"],
            "en": ["then", "next", "so", "therefore", "but", "however", "finally", "first"]
        }

        connector_list = connectors.get(language, connectors["zh"])
        return any(conn in text.lower() for conn in connector_list)

    def _generate_quality_assessment(self, metrics: BalanceMetrics) -> Dict[str, str]:
        """生成质量评估"""
        assessment = {}

        # 连贯性评估
        if metrics.coherence_score >= 0.8:
            assessment["coherence"] = "优秀"
        elif metrics.coherence_score >= 0.6:
            assessment["coherence"] = "良好"
        elif metrics.coherence_score >= 0.4:
            assessment["coherence"] = "一般"
        else:
            assessment["coherence"] = "需要改进"

        # 长度比例评估
        if 0.3 <= metrics.length_ratio <= 0.7:
            assessment["length"] = "理想"
        elif 0.2 <= metrics.length_ratio < 0.3 or 0.7 < metrics.length_ratio <= 0.8:
            assessment["length"] = "可接受"
        else:
            assessment["length"] = "需要调整"

        # 病毒潜力评估
        if metrics.viral_score >= 0.7:
            assessment["viral_potential"] = "高"
        elif metrics.viral_score >= 0.5:
            assessment["viral_potential"] = "中等"
        else:
            assessment["viral_potential"] = "较低"

        # 综合评估
        if metrics.quality_score >= 0.8:
            assessment["overall"] = "优秀，可以发布"
        elif metrics.quality_score >= 0.6:
            assessment["overall"] = "良好，建议微调"
        elif metrics.quality_score >= 0.4:
            assessment["overall"] = "一般，需要优化"
        else:
            assessment["overall"] = "较差，建议重新制作"

        return assessment

    def _generate_recommendations(self, metrics: BalanceMetrics,
                                length_category: VideoLengthCategory) -> List[str]:
        """生成具体建议"""
        recommendations = []

        # 基于质量评分的建议
        if metrics.quality_score >= 0.8:
            recommendations.append("视频质量优秀，可以直接发布")
        elif metrics.quality_score >= 0.6:
            recommendations.append("视频质量良好，建议进行微调后发布")
        else:
            recommendations.append("视频质量需要改进，建议重新优化")

        # 基于长度分类的建议
        if length_category == VideoLengthCategory.TOO_SHORT:
            recommendations.append("建议增加2-3个关键片段以提升完整性")
        elif length_category == VideoLengthCategory.TOO_LONG:
            recommendations.append("建议删除次要片段，保留核心剧情")
        elif length_category == VideoLengthCategory.OPTIMAL_SHORT:
            recommendations.append("时长控制理想，适合短视频平台传播")

        # 基于具体指标的建议
        if metrics.coherence_score < 0.6:
            recommendations.append("增加过渡片段或连接词以提升连贯性")

        if metrics.viral_score < 0.5:
            recommendations.append("增强开头吸引力，添加悬念或反转元素")

        if metrics.rhythm_score < 0.5:
            recommendations.append("优化剪辑节奏，调整片段时长分布")

        return recommendations


# 便捷函数
def analyze_video_balance(original_segments: List[Dict[str, Any]],
                         reconstructed_segments: List[Dict[str, Any]],
                         language: str = "zh") -> Dict[str, Any]:
    """
    便捷函数：分析视频长度平衡

    Args:
        original_segments: 原始片段
        reconstructed_segments: 重构片段
        language: 语言代码

    Returns:
        Dict: 分析结果
    """
    controller = NarrativeBalanceController()
    return controller.analyze_and_optimize(original_segments, reconstructed_segments, language)


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)

    # 模拟测试数据
    original_segments = [
        {"start_time": 0, "end_time": 30, "text": "这是一个关于爱情的故事"},
        {"start_time": 30, "end_time": 60, "text": "男主角遇到了女主角"},
        {"start_time": 60, "end_time": 90, "text": "他们经历了很多困难"},
        {"start_time": 90, "end_time": 120, "text": "最终他们在一起了"}
    ]

    reconstructed_segments = [
        {"start_time": 0, "end_time": 20, "text": "震撼！这是一个关于爱情的故事"},
        {"start_time": 20, "end_time": 40, "text": "然后男主角遇到了女主角"},
        {"start_time": 40, "end_time": 60, "text": "最终他们在一起了，结局太意外了！"}
    ]

    result = analyze_video_balance(original_segments, reconstructed_segments, "zh")

    print("=== 智能长度平衡分析结果 ===")
    print(f"原片时长: {result['original_duration']:.1f}秒")
    print(f"重构时长: {result['reconstructed_duration']:.1f}秒")
    print(f"长度分类: {result['length_category']}")
    print(f"质量评分: {result['balance_metrics']['quality_score']:.3f}")
    print("\n优化建议:")
    for suggestion in result['optimization_suggestions']:
        print(f"- {suggestion}")
    print("\n质量评估:")
    for aspect, assessment in result['quality_assessment'].items():
        print(f"- {aspect}: {assessment}")
