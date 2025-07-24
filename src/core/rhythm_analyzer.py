#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
节奏分析器
分析和优化视频剪辑的节奏和时长
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from ..utils.log_handler import get_logger

logger = get_logger(__name__)

class RhythmAnalyzer:
    """节奏分析器"""

    def __init__(self):
        """初始化节奏分析器"""
        self.optimal_segment_length = 3.0  # 最佳片段长度（秒）
        self.min_segment_length = 1.0      # 最小片段长度（秒）
        self.max_segment_length = 8.0      # 最大片段长度（秒）

        logger.info("[MUSIC] 节奏分析器初始化完成")

    def analyze_optimal_length(self, subtitles: List[Dict]) -> Dict[str, Any]:
        """
        分析最佳长度

        Args:
            subtitles: 字幕列表

        Returns:
            Dict: 分析结果
        """
        try:
            total_duration = sum(self._get_duration(sub) for sub in subtitles)
            segment_count = len(subtitles)
            avg_segment_length = total_duration / segment_count if segment_count > 0 else 0

            # 计算节奏评分
            rhythm_score = self._calculate_rhythm_score(subtitles)

            # 建议的目标长度
            suggested_length = self._suggest_target_length(total_duration, segment_count)

            result = {
                "total_duration": total_duration,
                "segment_count": segment_count,
                "avg_segment_length": avg_segment_length,
                "rhythm_score": rhythm_score,
                "suggested_length": suggested_length,
                "compression_ratio": suggested_length / total_duration if total_duration > 0 else 0
            }

            logger.info(f"[MUSIC] 节奏分析完成，建议长度: {suggested_length:.2f}秒")
            return result

        except Exception as e:
            logger.error(f"❌ 节奏分析失败: {e}")
            return {"error": str(e)}

    def optimize_for_length(self, subtitles: List[Dict], min_length: int, max_length: int) -> List[Dict]:
        """
        根据目标长度优化字幕

        Args:
            subtitles: 原始字幕列表
            min_length: 最小长度（秒）
            max_length: 最大长度（秒）

        Returns:
            List[Dict]: 优化后的字幕列表
        """
        try:
            logger.info(f"[MUSIC] 开始长度优化，目标范围: {min_length}-{max_length}秒")

            current_duration = sum(self._get_duration(sub) for sub in subtitles)
            target_duration = (min_length + max_length) / 2

            if current_duration <= max_length and current_duration >= min_length:
                logger.info("✅ 当前长度已在目标范围内")
                return subtitles

            # 计算压缩比
            compression_ratio = target_duration / current_duration

            if compression_ratio < 1.0:
                # 需要压缩
                optimized = self._compress_subtitles(subtitles, compression_ratio)
            else:
                # 需要扩展（通常不需要）
                optimized = subtitles

            final_duration = sum(self._get_duration(sub) for sub in optimized)
            logger.info(f"[MUSIC] 长度优化完成: {current_duration:.2f}s → {final_duration:.2f}s")

            return optimized

        except Exception as e:
            logger.error(f"❌ 长度优化失败: {e}")
            return subtitles

    def _get_duration(self, subtitle: Dict) -> float:
        """获取字幕时长"""
        try:
            if "duration" in subtitle:
                return float(subtitle["duration"])

            # 从start和end时间计算
            start = subtitle.get("start", "00:00:00,000")
            end = subtitle.get("end", "00:00:00,000")
            return self._time_to_seconds(end) - self._time_to_seconds(start)
        except:
            return 3.0  # 默认3秒

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

    def _calculate_rhythm_score(self, subtitles: List[Dict]) -> float:
        """计算节奏评分"""
        try:
            durations = [self._get_duration(sub) for sub in subtitles]

            if not durations:
                return 0.0

            # 计算时长变化的标准差
            avg_duration = sum(durations) / len(durations)
            variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
            std_dev = math.sqrt(variance)

            # 节奏评分：标准差越小，节奏越稳定
            rhythm_score = max(0, 1.0 - (std_dev / avg_duration))

            return rhythm_score

        except Exception as e:
            logger.error(f"节奏评分计算失败: {e}")
            return 0.5

    def _suggest_target_length(self, total_duration: float, segment_count: int) -> float:
        """建议目标长度"""
        try:
            # 基于总时长和片段数量的启发式算法
            if total_duration <= 60:  # 1分钟以内
                return total_duration * 0.8
            elif total_duration <= 300:  # 5分钟以内
                return total_duration * 0.6
            elif total_duration <= 900:  # 15分钟以内
                return total_duration * 0.4
            else:  # 超过15分钟
                return total_duration * 0.3

        except:
            return 60.0  # 默认1分钟

    def _compress_subtitles(self, subtitles: List[Dict], compression_ratio: float) -> List[Dict]:
        """压缩字幕"""
        try:
            # 计算需要保留的片段数量
            target_count = int(len(subtitles) * compression_ratio)
            target_count = max(1, target_count)  # 至少保留1个片段

            # 按重要性排序（这里简化为按文本长度）
            scored_subtitles = []
            for i, sub in enumerate(subtitles):
                score = len(sub.get("text", ""))  # 简单的重要性评分
                scored_subtitles.append((score, i, sub))

            # 按评分排序，保留前N个
            scored_subtitles.sort(key=lambda x: x[0], reverse=True)
            selected = scored_subtitles[:target_count]

            # 按原始顺序重新排列
            selected.sort(key=lambda x: x[1])

            return [item[2] for item in selected]

        except Exception as e:
            logger.error(f"字幕压缩失败: {e}")
            return subtitles[:len(subtitles)//2]  # 简单的一半压缩