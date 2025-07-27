#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
片段建议器
提供智能的视频片段选择和优化建议
"""

from typing import List, Dict, Any, Tuple, Optional
from ..utils.log_handler import get_logger

logger = get_logger(__name__)

class SegmentAdvisor:
    """片段建议器"""

    def __init__(self):
        """初始化片段建议器"""
        self.importance_weights = {
            "text_length": 0.3,      # 文本长度权重
            "emotional_intensity": 0.4,  # 情感强度权重
            "position_bonus": 0.2,   # 位置奖励权重
            "duration_penalty": 0.1  # 时长惩罚权重
        }

        logger.info("🎯 片段建议器初始化完成")

    def suggest_segment_merging(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        建议片段合并策略

        Args:
            segments: 片段列表

        Returns:
            合并建议结果
        """
        try:
            if not segments:
                return {
                    "status": "empty",
                    "suggestions": [],
                    "total_segments": 0
                }

            suggestions = []

            # 分析相邻片段的合并可能性
            for i in range(len(segments) - 1):
                current_seg = segments[i]
                next_seg = segments[i + 1]

                # 计算时间间隔
                current_end = current_seg.get("end_time", 0.0)
                next_start = next_seg.get("start_time", 0.0)
                gap = next_start - current_end

                # 如果间隔很小，建议合并
                if gap < 1.0:  # 小于1秒
                    suggestion = {
                        "type": "merge",
                        "segments": [i, i + 1],
                        "reason": f"时间间隔很小 ({gap:.2f}秒)",
                        "confidence": 0.8 if gap < 0.5 else 0.6
                    }
                    suggestions.append(suggestion)

                # 如果内容相关，建议合并
                current_text = current_seg.get("text", "")
                next_text = next_seg.get("text", "")

                if self._are_texts_related(current_text, next_text):
                    suggestion = {
                        "type": "merge",
                        "segments": [i, i + 1],
                        "reason": "内容相关性高",
                        "confidence": 0.7
                    }
                    suggestions.append(suggestion)

            # 分析过短片段
            for i, segment in enumerate(segments):
                duration = segment.get("duration", 0.0)
                if duration < 2.0:  # 小于2秒
                    suggestion = {
                        "type": "extend",
                        "segments": [i],
                        "reason": f"片段过短 ({duration:.2f}秒)",
                        "confidence": 0.9
                    }
                    suggestions.append(suggestion)

            return {
                "status": "success",
                "suggestions": suggestions,
                "total_segments": len(segments),
                "merge_candidates": len([s for s in suggestions if s["type"] == "merge"]),
                "extend_candidates": len([s for s in suggestions if s["type"] == "extend"])
            }

        except Exception as e:
            logger.error(f"片段合并建议失败: {e}")
            return {
                "status": "failed",
                "suggestions": [],
                "total_segments": len(segments),
                "error": str(e)
            }

    def _are_texts_related(self, text1: str, text2: str) -> bool:
        """判断两个文本是否相关"""
        try:
            # 简单的相关性判断
            words1 = set(text1.split())
            words2 = set(text2.split())

            if not words1 or not words2:
                return False

            # 计算词汇重叠率
            overlap = len(words1.intersection(words2))
            total_unique = len(words1.union(words2))

            overlap_rate = overlap / total_unique if total_unique > 0 else 0

            return overlap_rate > 0.3  # 30%以上重叠认为相关

        except Exception:
            return False

    def suggest_optimal_segments(self, subtitles: List[Dict],
                               target_length: Tuple[int, int]) -> List[Dict]:
        """
        建议最佳片段组合

        Args:
            subtitles: 字幕列表
            target_length: 目标长度范围(最小秒数, 最大秒数)

        Returns:
            List[Dict]: 优化后的片段列表
        """
        try:
            min_length, max_length = target_length
            logger.info(f"🎯 开始片段优化，目标长度: {min_length}-{max_length}秒")

            # 计算每个片段的重要性评分
            scored_segments = self._score_segments(subtitles)

            # 选择最佳片段组合
            optimal_segments = self._select_optimal_combination(
                scored_segments, min_length, max_length
            )

            # 按时间顺序重新排列
            optimal_segments.sort(key=lambda x: self._get_start_time(x))

            total_duration = sum(self._get_duration(seg) for seg in optimal_segments)
            logger.info(f"🎯 片段优化完成: {len(optimal_segments)}个片段，总时长: {total_duration:.2f}秒")

            return optimal_segments

        except Exception as e:
            logger.error(f"❌ 片段优化失败: {e}")
            return subtitles

    def _score_segments(self, subtitles: List[Dict]) -> List[Tuple[float, Dict]]:
        """为片段评分"""
        try:
            scored_segments = []
            total_segments = len(subtitles)

            for i, segment in enumerate(subtitles):
                score = 0.0

                # 文本长度评分
                text_length = len(segment.get("text", ""))
                text_score = min(text_length / 50, 1.0)  # 归一化到0-1
                score += text_score * self.importance_weights["text_length"]

                # 情感强度评分
                emotional_score = self._calculate_emotional_intensity(segment.get("text", ""))
                score += emotional_score * self.importance_weights["emotional_intensity"]

                # 位置奖励（开头和结尾更重要）
                position_ratio = i / total_segments if total_segments > 1 else 0
                if position_ratio <= 0.2 or position_ratio >= 0.8:  # 前20%或后20%
                    position_bonus = 1.0
                else:
                    position_bonus = 0.5
                score += position_bonus * self.importance_weights["position_bonus"]

                # 时长惩罚（过长或过短的片段扣分）
                duration = self._get_duration(segment)
                if 2.0 <= duration <= 6.0:  # 理想时长范围
                    duration_score = 1.0
                else:
                    duration_score = 0.5
                score += duration_score * self.importance_weights["duration_penalty"]

                scored_segments.append((score, segment))

            # 按评分排序
            scored_segments.sort(key=lambda x: x[0], reverse=True)

            return scored_segments

        except Exception as e:
            logger.error(f"片段评分失败: {e}")
            return [(0.5, seg) for seg in subtitles]

    def _calculate_emotional_intensity(self, text: str) -> float:
        """计算情感强度"""
        try:
            # 情感关键词
            high_intensity_words = [
                "震撼", "惊呆", "不敢相信", "史上最", "必看", "爆款",
                "SHOCKING", "AMAZING", "UNBELIEVABLE", "INCREDIBLE", "MUST WATCH", "VIRAL"
            ]

            medium_intensity_words = [
                "惊讶", "意外", "精彩", "厉害", "牛逼", "绝了",
                "surprising", "amazing", "awesome", "incredible", "fantastic", "wonderful"
            ]

            text_lower = text.lower()
            score = 0.0

            # 高强度词汇
            for word in high_intensity_words:
                if word.lower() in text_lower:
                    score += 1.0

            # 中等强度词汇
            for word in medium_intensity_words:
                if word.lower() in text_lower:
                    score += 0.6

            # 标点符号强度
            if "!" in text:
                score += 0.3 * text.count("!")
            if "？" in text or "?" in text:
                score += 0.2

            # 归一化到0-1范围
            return min(score / 3.0, 1.0)

        except Exception as e:
            logger.error(f"情感强度计算失败: {e}")
            return 0.5

    def _select_optimal_combination(self, scored_segments: List[Tuple[float, Dict]],
                                  min_length: int, max_length: int) -> List[Dict]:
        """选择最佳片段组合"""
        try:
            selected_segments = []
            current_duration = 0.0
            target_duration = (min_length + max_length) / 2

            # 贪心算法选择片段
            for score, segment in scored_segments:
                segment_duration = self._get_duration(segment)

                # 检查是否可以添加这个片段
                if current_duration + segment_duration <= max_length:
                    selected_segments.append(segment)
                    current_duration += segment_duration

                    # 如果达到目标长度，停止添加
                    if current_duration >= min_length:
                        break

            # 如果选择的片段太少，添加更多片段
            if current_duration < min_length and len(selected_segments) < len(scored_segments):
                remaining_segments = [seg for score, seg in scored_segments
                                    if seg not in selected_segments]

                for segment in remaining_segments:
                    segment_duration = self._get_duration(segment)
                    if current_duration + segment_duration <= max_length:
                        selected_segments.append(segment)
                        current_duration += segment_duration

                        if current_duration >= min_length:
                            break

            return selected_segments

        except Exception as e:
            logger.error(f"片段组合选择失败: {e}")
            return [seg for score, seg in scored_segments[:5]]  # 返回前5个高分片段

    def _get_duration(self, segment: Dict) -> float:
        """获取片段时长"""
        try:
            if "duration" in segment:
                return float(segment["duration"])

            # 从start和end时间计算
            start = segment.get("start", "00:00:00,000")
            end = segment.get("end", "00:00:00,000")
            return self._time_to_seconds(end) - self._time_to_seconds(start)
        except:
            return 3.0  # 默认3秒

    def _get_start_time(self, segment: Dict) -> float:
        """获取片段开始时间"""
        try:
            start = segment.get("start", "00:00:00,000")
            return self._time_to_seconds(start)
        except:
            return 0.0

    def _time_to_seconds(self, time_str: str) -> float:
        """时间字符串转秒数"""
        try:
            parts = time_str.replace(',', '.').split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0.0