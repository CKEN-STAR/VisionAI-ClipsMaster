#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 动态节奏调整器

此模块提供根据不同视频节奏类型调整片段长度和过渡效果的功能。
它能够使混剪视频具有更好的节奏感和视觉流畅性，增强观看体验。

主要功能：
1. 基于节奏类型调整片段时长
2. 智能处理过长/过短片段
3. 维持叙事连贯性的同时优化节奏
4. 支持多种预设节奏模式（快节奏、慢镜头等）
5. 可定制节奏规则的灵活架构
"""

import os
import re
import json
import logging
import math
import statistics
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# 相对导入变更为适应模块化运行
try:
    from src.utils.log_handler import get_logger
    from src.utils.exceptions import ClipMasterError, RhythmError
except ImportError:
    # 当作为独立模块运行时的后备导入路径
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    try:
        from src.utils.log_handler import get_logger
        from src.utils.exceptions import ClipMasterError, RhythmError
    except ImportError:
        # 如果还是无法导入，使用基本日志
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        def get_logger(name):
            return logging.getLogger(name)
        
        # 定义基本异常类
        class ClipMasterError(Exception):
            pass
        
        class RhythmError(ClipMasterError):
            pass

# 配置日志
logger = get_logger("rhythm_adjuster")


# 预定义节奏类型
RHYTHM_TYPES = {
    "fast_pace": "快节奏",         # 快速切换，适合动作场景
    "slow_motion": "慢镜头",       # 舒缓节奏，强调情感
    "dramatic": "戏剧性",         # 戏剧性节奏，强调冲突
    "montage": "蒙太奇",          # 快速组接多个镜头
    "dialogue": "对话节奏",       # 保持对话流畅
    "emotional": "情感节奏",      # 强调情感变化
    "suspense": "悬疑节奏",       # 缓慢构建悬疑氛围
    "action": "动作节奏",         # 适合动作场景
    "comedy": "喜剧节奏",         # 适合喜剧效果
    "dynamic_contrast": "动态对比" # 快慢交替
}


def apply_rhythm_rules(segments: List[Dict[str, Any]], rhythm_type: str) -> List[Dict[str, Any]]:
    """根据指定节奏类型调整片段时长
    
    Args:
        segments: 视频片段列表
        rhythm_type: 节奏类型
        
    Returns:
        调整后的片段列表
    """
    # 定义不同节奏类型的规则
    rules = {
        # 快节奏：限制最大时长，保持节奏紧凑
        'fast_pace': lambda x: min(max(x, 1.5), 5.0),  # 限制在1.5-5秒
        
        # 慢镜头：延长片段时长
        'slow_motion': lambda x: max(x * 1.5, 3.0),    # 至少3秒，原时长的1.5倍
        
        # 戏剧性：基于内容重要性动态调整
        'dramatic': lambda x: x * 1.2 if x > 3 else x * 0.8,  # 长镜头延长，短镜头缩短
        
        # 蒙太奇：极短片段快速组接
        'montage': lambda x: min(x, 2.5),              # 最长2.5秒
        
        # 对话节奏：保持适中，确保台词完整
        'dialogue': lambda x: max(min(x, 8.0), 2.0),   # 限制在2-8秒
        
        # 情感节奏：变长，让观众有时间感受
        'emotional': lambda x: max(x * 1.3, 4.0),      # 至少4秒，原时长的1.3倍
        
        # 悬疑节奏：逐渐加速
        'suspense': lambda x, idx=0, total=1: x * (0.8 + 0.4 * (idx / max(total, 1))),  # 随序列位置递增
        
        # 动作节奏：快速切换
        'action': lambda x: min(x * 0.7, 3.0),         # 最长3秒，原时长的0.7倍
        
        # 喜剧节奏：强调节奏感
        'comedy': lambda x: x * 0.8 if x > 3 else x * 1.1,  # 长镜头缩短，短镜头延长
        
        # 动态对比：交替快慢
        'dynamic_contrast': lambda x, idx=0: x * 0.7 if idx % 2 == 0 else x * 1.3  # 奇偶交替
    }
    
    # 如果提供的节奏类型不存在，使用默认规则
    if rhythm_type not in rules:
        logger.warning(f"未知节奏类型: {rhythm_type}，使用默认规则")
        rhythm_type = 'dialogue'  # 默认使用对话节奏
    
    # 应用规则
    adjusted_segments = []
    total_segments = len(segments)
    
    for idx, segment in enumerate(segments):
        adjusted = segment.copy()
        
        # 处理特殊规则（需要索引或总数信息）
        if rhythm_type in ['suspense', 'dynamic_contrast']:
            if rhythm_type == 'suspense':
                if 'duration' in segment:
                    adjusted['duration'] = rules[rhythm_type](segment['duration'], idx, total_segments)
                    # 更新结束时间
                    if 'start' in segment:
                        adjusted['end'] = segment['start'] + adjusted['duration']
            elif rhythm_type == 'dynamic_contrast':
                if 'duration' in segment:
                    adjusted['duration'] = rules[rhythm_type](segment['duration'], idx)
                    # 更新结束时间
                    if 'start' in segment:
                        adjusted['end'] = segment['start'] + adjusted['duration']
        else:
            # 处理标准规则
            if 'duration' in segment:
                adjusted['duration'] = rules[rhythm_type](segment['duration'])
                # 更新结束时间
                if 'start' in segment:
                    adjusted['end'] = segment['start'] + adjusted['duration']
        
        adjusted_segments.append(adjusted)
    
    # 修复时间线（确保片段不重叠）
    fix_timeline_continuity(adjusted_segments)
    
    return adjusted_segments


def fix_timeline_continuity(segments: List[Dict[str, Any]]) -> None:
    """修复时间线连续性，避免片段重叠
    
    Args:
        segments: 视频片段列表
    """
    # 按开始时间排序
    segments.sort(key=lambda x: x.get('start', 0))
    
    # 修复重叠
    for i in range(1, len(segments)):
        prev_seg = segments[i-1]
        curr_seg = segments[i]
        
        if 'end' in prev_seg and 'start' in curr_seg:
            # 如果前一个片段结束时间超过当前片段开始时间
            if prev_seg['end'] > curr_seg['start']:
                # 调整当前片段的开始时间
                curr_seg['start'] = prev_seg['end']
                
                # 更新当前片段的持续时间
                if 'end' in curr_seg:
                    curr_seg['duration'] = curr_seg['end'] - curr_seg['start']
                elif 'duration' in curr_seg:
                    curr_seg['end'] = curr_seg['start'] + curr_seg['duration']


def analyze_rhythm_pattern(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析片段列表的节奏模式
    
    Args:
        segments: 视频片段列表
        
    Returns:
        节奏分析结果
    """
    if not segments:
        return {"pattern": "empty", "avg_duration": 0, "recommendation": "无可分析片段"}
    
    # 提取持续时间
    durations = []
    for seg in segments:
        if 'duration' in seg:
            durations.append(seg['duration'])
        elif 'start' in seg and 'end' in seg:
            durations.append(seg['end'] - seg['start'])
    
    if not durations:
        return {"pattern": "unknown", "avg_duration": 0, "recommendation": "无法确定片段持续时间"}
    
    # 计算基本统计量
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    try:
        std_dev = statistics.stdev(durations) if len(durations) > 1 else 0
    except:
        std_dev = 0
    
    # 确定节奏模式
    pattern = "balanced"  # 默认
    recommendation = None
    
    if avg_duration < 2.5:
        pattern = "fast"
        if std_dev < 0.5:
            recommendation = "fast_pace"  # 推荐快节奏
        else:
            recommendation = "action"  # 推荐动作节奏
    elif avg_duration > 6:
        pattern = "slow"
        if std_dev < 1.0:
            recommendation = "slow_motion"  # 推荐慢镜头
        else:
            recommendation = "emotional"  # 推荐情感节奏
    else:
        # 中等节奏
        if std_dev > 2.0:
            pattern = "varied"
            recommendation = "dynamic_contrast"  # 推荐动态对比
        else:
            pattern = "balanced"
            recommendation = "dialogue"  # 推荐对话节奏
    
    # 检查是否有长短交替模式
    alternating = True
    for i in range(2, len(durations)):
        # 检查是否遵循短-长-短或长-短-长模式
        if (durations[i-2] > durations[i-1] and durations[i] > durations[i-1]) or \
           (durations[i-2] < durations[i-1] and durations[i] < durations[i-1]):
            continue
        else:
            alternating = False
            break
    
    if alternating and len(durations) > 3:
        pattern = "alternating"
        recommendation = "dynamic_contrast"  # 推荐动态对比
    
    return {
        "pattern": pattern,
        "avg_duration": avg_duration,
        "min_duration": min_duration,
        "max_duration": max_duration,
        "std_deviation": std_dev,
        "recommendation": recommendation,
        "segment_count": len(segments)
    }


def suggest_rhythm_type(segments: List[Dict[str, Any]], content_tags: List[str] = None) -> str:
    """基于片段特征和内容标签推荐最适合的节奏类型
    
    Args:
        segments: 视频片段列表
        content_tags: 内容相关标签（如"动作"、"对话"、"情感"等）
        
    Returns:
        推荐的节奏类型
    """
    # 分析当前节奏模式
    analysis = analyze_rhythm_pattern(segments)
    recommended_type = analysis.get("recommendation", "dialogue")
    
    # 如果有内容标签，根据标签调整推荐
    if content_tags:
        # 标签映射到节奏类型
        tag_mapping = {
            "动作": "action",
            "action": "action",
            "fight": "action",
            "打斗": "action",
            
            "对话": "dialogue",
            "talk": "dialogue",
            "conversation": "dialogue",
            "交流": "dialogue",
            
            "情感": "emotional",
            "emotional": "emotional",
            "感人": "emotional",
            "touching": "emotional",
            
            "悬疑": "suspense",
            "suspense": "suspense",
            "mystery": "suspense",
            "紧张": "suspense",
            
            "喜剧": "comedy",
            "comedy": "comedy",
            "funny": "comedy",
            "搞笑": "comedy",
            
            "蒙太奇": "montage",
            "montage": "montage",
            "快闪": "montage",
            "快速": "montage",
            
            "慢镜头": "slow_motion",
            "slow": "slow_motion",
            "舒缓": "slow_motion",
            "缓慢": "slow_motion"
        }
        
        # 根据标签调整推荐
        for tag in content_tags:
            tag = tag.lower()
            if tag in tag_mapping:
                return tag_mapping[tag]
    
    return recommended_type


def optimize_emotional_flow(segments: List[Dict[str, Any]], emotion_map: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """优化情感流动，根据情感强度调整节奏
    
    Args:
        segments: 视频片段列表
        emotion_map: 情感强度映射（字幕ID到情感强度值的映射）
        
    Returns:
        调整后的片段列表
    """
    if not emotion_map:
        return segments
    
    adjusted = []
    
    for segment in segments:
        adjusted_segment = segment.copy()
        
        # 获取片段ID或字幕ID
        segment_id = segment.get('id', None) or segment.get('subtitle_id', None)
        
        if segment_id and segment_id in emotion_map:
            # 获取情感强度
            emotion_intensity = emotion_map[segment_id]
            
            # 基于情感强度调整持续时间
            if 'duration' in segment:
                # 高情感 -> 更长时间；低情感 -> 更短时间
                adjusted_segment['duration'] = segment['duration'] * (0.8 + 0.4 * emotion_intensity)
                
                # 更新结束时间
                if 'start' in segment:
                    adjusted_segment['end'] = segment['start'] + adjusted_segment['duration']
        
        adjusted.append(adjusted_segment)
    
    # 修复时间线
    fix_timeline_continuity(adjusted)
    
    return adjusted


class RhythmAdjuster:
    """节奏调整器类"""
    
    def __init__(self):
        """初始化节奏调整器"""
        self.logger = logger
        self.custom_rules = {}
    
    def register_custom_rule(self, name: str, rule_func: Callable) -> None:
        """注册自定义节奏规则
        
        Args:
            name: 规则名称
            rule_func: 规则函数（接受duration参数并返回调整后的duration）
        """
        self.custom_rules[name] = rule_func
        self.logger.info(f"已注册自定义节奏规则: {name}")
    
    def adjust(self, segments: List[Dict[str, Any]], rhythm_type: str = None, 
              content_tags: List[str] = None, emotion_map: Dict[str, float] = None) -> Dict[str, Any]:
        """调整片段的节奏
        
        Args:
            segments: 视频片段列表
            rhythm_type: 指定节奏类型（如不指定则自动推荐）
            content_tags: 内容标签（用于智能推荐节奏类型）
            emotion_map: 情感强度映射
            
        Returns:
            调整结果
        """
        try:
            # 分析当前节奏
            analysis = analyze_rhythm_pattern(segments)
            
            # 如果未指定节奏类型，则推荐一个
            if not rhythm_type:
                rhythm_type = suggest_rhythm_type(segments, content_tags)
            
            # 检查是否使用自定义规则
            if rhythm_type in self.custom_rules:
                # 使用自定义规则
                adjusted_segments = []
                for segment in segments:
                    adjusted = segment.copy()
                    if 'duration' in segment:
                        adjusted['duration'] = self.custom_rules[rhythm_type](segment['duration'])
                        if 'start' in segment:
                            adjusted['end'] = segment['start'] + adjusted['duration']
                    adjusted_segments.append(adjusted)
                fix_timeline_continuity(adjusted_segments)
            else:
                # 使用预定义规则
                adjusted_segments = apply_rhythm_rules(segments, rhythm_type)
            
            # 如果提供了情感映射，进一步优化情感流动
            if emotion_map:
                adjusted_segments = optimize_emotional_flow(adjusted_segments, emotion_map)
            
            # 分析调整后的节奏
            adjusted_analysis = analyze_rhythm_pattern(adjusted_segments)
            
            return {
                "original_segments": segments,
                "adjusted_segments": adjusted_segments,
                "rhythm_type": rhythm_type,
                "original_analysis": analysis,
                "adjusted_analysis": adjusted_analysis,
                "segment_count": len(segments)
            }
        
        except Exception as e:
            self.logger.error(f"调整节奏时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise RhythmError(f"节奏调整失败: {str(e)}")


# 创建全局实例
_adjuster = None

def get_rhythm_adjuster() -> RhythmAdjuster:
    """获取节奏调整器实例
    
    Returns:
        RhythmAdjuster: 节奏调整器实例
    """
    global _adjuster
    if _adjuster is None:
        _adjuster = RhythmAdjuster()
    return _adjuster


def adjust_rhythm(segments: List[Dict[str, Any]], rhythm_type: str = None,
                 content_tags: List[str] = None) -> List[Dict[str, Any]]:
    """调整视频片段的节奏（便捷函数）
    
    Args:
        segments: 视频片段列表
        rhythm_type: 节奏类型
        content_tags: 内容标签
        
    Returns:
        调整后的片段列表
    """
    adjuster = get_rhythm_adjuster()
    result = adjuster.adjust(segments, rhythm_type, content_tags)
    return result["adjusted_segments"]


if __name__ == "__main__":
    # 简单测试
    test_segments = [
        {"id": "seg1", "start": 0.0, "end": 3.0, "duration": 3.0, "content": "测试片段1"},
        {"id": "seg2", "start": 3.0, "end": 5.0, "duration": 2.0, "content": "测试片段2"},
        {"id": "seg3", "start": 5.0, "end": 10.0, "duration": 5.0, "content": "测试片段3"},
        {"id": "seg4", "start": 10.0, "end": 12.0, "duration": 2.0, "content": "测试片段4"}
    ]
    
    # 分析当前节奏
    analysis = analyze_rhythm_pattern(test_segments)
    print("原始节奏分析:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    # 测试不同节奏类型
    for rhythm_type in ["fast_pace", "slow_motion", "dialogue", "dynamic_contrast"]:
        print(f"\n应用{RHYTHM_TYPES.get(rhythm_type, rhythm_type)}节奏:")
        adjusted = adjust_rhythm(test_segments, rhythm_type)
        
        for i, seg in enumerate(adjusted):
            print(f"  片段 {i+1}: {seg['start']:.1f}s - {seg['end']:.1f}s (时长: {seg['duration']:.1f}s)")
        
        # 分析调整后的节奏
        adjusted_analysis = analyze_rhythm_pattern(adjusted)
        print(f"  平均时长: {adjusted_analysis['avg_duration']:.2f}秒 (原始: {analysis['avg_duration']:.2f}秒)")
    
    # 测试基于内容的推荐
    content_tags = ["对话", "情感"]
    recommended_type = suggest_rhythm_type(test_segments, content_tags)
    print(f"\n基于标签{content_tags}的推荐节奏类型: {recommended_type} ({RHYTHM_TYPES.get(recommended_type, '')})")
    
    # 测试情感流动优化
    emotion_map = {
        "seg1": 0.3,  # 低情感
        "seg2": 0.7,  # 中情感
        "seg3": 0.9,  # 高情感
        "seg4": 0.5   # 中情感
    }
    
    print("\n情感流动优化:")
    emotion_adjusted = optimize_emotional_flow(test_segments, emotion_map)
    for i, seg in enumerate(emotion_adjusted):
        print(f"  片段 {i+1}: {seg['start']:.1f}s - {seg['end']:.1f}s (时长: {seg['duration']:.1f}s, 情感强度: {emotion_map[seg['id']]:.1f})") 