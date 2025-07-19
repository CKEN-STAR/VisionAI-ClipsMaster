#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 时间轴检查器

此模块提供了一系列用于检测和修复时间轴数据中常见问题的功能:
1. 检测片段重叠冲突
2. 修复片段重叠
3. 检测空隙和不连续性
4. 验证时间轴完整性
5. 检测帧率兼容性

主要用于在导出和渲染前确保时间轴数据的有效性，
防止渲染错误和不一致的视频输出。
"""

import logging
from typing import List, Dict, Any, Tuple, Optional, Union
import copy

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("timeline_checker")


def detect_overlap(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """检测片段重叠并自动修复
    
    通过检查排序后的片段序列，识别重叠的时间段并调整起始位置，
    确保所有片段按顺序排列且不重叠。
    
    Args:
        segments: 片段列表，每个片段必须包含'start'和'end'键
        
    Returns:
        修复重叠后的片段列表
        
    Examples:
        >>> segments = [
        ...     {'id': 1, 'start': 0, 'end': 10},
        ...     {'id': 2, 'start': 8, 'end': 15},  # 与前一个片段重叠
        ...     {'id': 3, 'start': 20, 'end': 30}
        ... ]
        >>> result = detect_overlap(segments)
        >>> result[1]['start']  # 已调整为10
        10
    """
    if not segments:
        return []
    
    # 创建副本避免修改原始数据
    segments_copy = copy.deepcopy(segments)
    
    # 按开始时间排序
    sorted_segs = sorted(segments_copy, key=lambda x: x['start'])
    
    # 检查并修复重叠
    for i in range(1, len(sorted_segs)):
        if sorted_segs[i]['start'] < sorted_segs[i-1]['end']:
            # 记录原始值用于日志
            original_start = sorted_segs[i]['start']
            
            # 修复：将当前片段的开始时间设为前一个片段的结束时间
            sorted_segs[i]['start'] = sorted_segs[i-1]['end']
            
            # 检查修复后是否有效（开始时间必须小于结束时间）
            if sorted_segs[i]['start'] >= sorted_segs[i]['end']:
                logger.warning(
                    f"片段 {sorted_segs[i].get('id', i)} 在修复重叠后无效: "
                    f"start={sorted_segs[i]['start']} >= end={sorted_segs[i]['end']}"
                )
                # 将结束时间也相应调整
                sorted_segs[i]['end'] = sorted_segs[i]['start'] + 1
            
            logger.info(
                f"修复了片段 {sorted_segs[i].get('id', i)} 与 {sorted_segs[i-1].get('id', i-1)} 之间的重叠: "
                f"start 从 {original_start} 调整到 {sorted_segs[i]['start']}"
            )
    
    return sorted_segs


def detect_gaps(segments: List[Dict[str, Any]], max_gap: float = 0.0) -> List[Dict[str, Any]]:
    """检测片段之间的间隙
    
    识别时间轴上相邻片段之间超过允许阈值的间隙，通常用于检查时间轴完整性。
    
    Args:
        segments: 片段列表，每个片段必须包含'start'和'end'键
        max_gap: 允许的最大间隙（单位：与片段时间单位相同，通常是秒或帧）
        
    Returns:
        检测到的间隙列表，每个间隙是一个字典，包含'start'、'end'和'duration'键
        
    Examples:
        >>> segments = [
        ...     {'id': 1, 'start': 0, 'end': 10},
        ...     {'id': 2, 'start': 15, 'end': 20},  # 有5单位的间隙
        ...     {'id': 3, 'start': 20, 'end': 30}
        ... ]
        >>> gaps = detect_gaps(segments, max_gap=2)
        >>> len(gaps)  # 发现1个超过阈值的间隙
        1
        >>> gaps[0]['duration']  # 间隙长度为5
        5
    """
    if not segments or len(segments) < 2:
        return []
    
    # 按开始时间排序
    sorted_segs = sorted(segments, key=lambda x: x['start'])
    
    gaps = []
    for i in range(1, len(sorted_segs)):
        current_start = sorted_segs[i]['start']
        previous_end = sorted_segs[i-1]['end']
        
        # 计算间隙大小
        gap_size = current_start - previous_end
        
        # 如果间隙大于允许的最大值，记录它
        if gap_size > max_gap:
            gaps.append({
                'start': previous_end,
                'end': current_start,
                'duration': gap_size,
                'prev_segment_id': sorted_segs[i-1].get('id', f'segment_{i-1}'),
                'next_segment_id': sorted_segs[i].get('id', f'segment_{i}')
            })
    
    return gaps


def validate_timeline(timeline_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """验证时间轴数据的有效性和完整性
    
    全面检查时间轴数据，包括结构完整性、片段有效性、时间冲突等问题。
    
    Args:
        timeline_data: 完整的时间轴数据字典
        
    Returns:
        验证结果元组：(是否有效, 问题列表)
    """
    valid = True
    issues = []
    
    # 基本结构检查
    required_keys = ['clips', 'tracks']
    for key in required_keys:
        if key not in timeline_data:
            valid = False
            issues.append(f"缺少必要的键: '{key}'")
    
    # 帧率检查
    if 'fps' not in timeline_data:
        issues.append("警告: 未指定全局帧率")
    
    # 检查轨道
    if 'tracks' in timeline_data and isinstance(timeline_data['tracks'], list):
        for i, track in enumerate(timeline_data['tracks']):
            if 'items' not in track:
                issues.append(f"轨道 {i} 缺少 'items' 列表")
                continue
                
            # 检查轨道内的片段是否重叠
            if 'items' in track and isinstance(track['items'], list):
                if len(track['items']) > 1:
                    # 检查前后是否有重叠
                    sorted_items = sorted(track['items'], key=lambda x: x.get('start_frame', x.get('start', 0)))
                    for j in range(1, len(sorted_items)):
                        current_item = sorted_items[j]
                        previous_item = sorted_items[j-1]
                        
                        # 确定要比较的键（有些用start_frame，有些用start）
                        start_key = 'start_frame' if 'start_frame' in current_item else 'start'
                        end_key = 'end_frame' if 'end_frame' in previous_item else 'end'
                        
                        if current_item.get(start_key, 0) < previous_item.get(end_key, 0):
                            valid = False
                            issues.append(
                                f"轨道 {i} 中有重叠片段: 片段 {j-1} 和 片段 {j} 在时间轴上重叠"
                            )
    
    # 检查片段定义
    if 'clips' in timeline_data and isinstance(timeline_data['clips'], list):
        for i, clip in enumerate(timeline_data['clips']):
            # 检查必要字段
            for field in ['start_frame', 'end_frame']:
                if field not in clip:
                    issues.append(f"片段 {i} (ID:{clip.get('id', '未知')}) 缺少字段: {field}")
            
            # 检查时间值有效性
            if ('start_frame' in clip and 'end_frame' in clip and 
                clip['start_frame'] >= clip['end_frame']):
                valid = False
                issues.append(
                    f"片段 {i} (ID:{clip.get('id', '未知')}) 的时间无效: "
                    f"start_frame={clip['start_frame']} >= end_frame={clip['end_frame']}"
                )
    
    return valid, issues


def fix_timeline_conflicts(timeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """修复时间轴中的所有冲突和问题
    
    综合应用各种检测和修复功能，处理时间轴中的重叠、间隙和其他问题。
    
    Args:
        timeline_data: 时间轴数据字典
        
    Returns:
        修复后的时间轴数据字典
    """
    # 创建深拷贝以避免修改原始数据
    result = copy.deepcopy(timeline_data)
    
    # 修复轨道中的片段重叠
    if 'tracks' in result and isinstance(result['tracks'], list):
        for i, track in enumerate(result['tracks']):
            if 'items' in track and isinstance(track['items'], list):
                # 确定使用的键名（不同系统可能使用不同命名）
                sample_item = track['items'][0] if track['items'] else {}
                start_key = 'start_frame' if 'start_frame' in sample_item else 'start'
                end_key = 'end_frame' if 'end_frame' in sample_item else 'end'
                
                # 标准化键名以便修复
                normalized_items = []
                for item in track['items']:
                    normalized_item = copy.deepcopy(item)
                    if start_key != 'start':
                        normalized_item['start'] = item[start_key]
                    if end_key != 'end':
                        normalized_item['end'] = item[end_key]
                    normalized_items.append(normalized_item)
                
                # 修复重叠
                fixed_items = detect_overlap(normalized_items)
                
                # 将修复后的值更新回原始键名
                for j, fixed_item in enumerate(fixed_items):
                    track['items'][j][start_key] = fixed_item['start']
                    track['items'][j][end_key] = fixed_item['end']
    
    # 处理片段上的冲突
    if 'clips' in result and isinstance(result['clips'], list):
        clips_with_std_keys = []
        for clip in result['clips']:
            std_clip = copy.deepcopy(clip)
            if 'start_frame' in clip:
                std_clip['start'] = clip['start_frame']
            if 'end_frame' in clip:
                std_clip['end'] = clip['end_frame']
            clips_with_std_keys.append(std_clip)
        
        # 修复片段重叠
        fixed_clips = detect_overlap(clips_with_std_keys)
        
        # 更新回原数据
        for i, fixed_clip in enumerate(fixed_clips):
            if 'start_frame' in result['clips'][i]:
                result['clips'][i]['start_frame'] = fixed_clip['start']
            if 'end_frame' in result['clips'][i]:
                result['clips'][i]['end_frame'] = fixed_clip['end']
    
    return result


def check_frame_rate_compatibility(timeline_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """检查时间轴中的帧率兼容性
    
    确保时间轴中的所有轨道和片段使用兼容的帧率。
    
    Args:
        timeline_data: 时间轴数据字典
        
    Returns:
        兼容性检查结果元组: (是否兼容, 问题列表)
    """
    compatible = True
    issues = []
    
    # 获取全局帧率
    global_fps = timeline_data.get('fps')
    if not global_fps:
        issues.append("警告: 未指定全局帧率")
        return compatible, issues
    
    # 检查轨道帧率
    if 'tracks' in timeline_data and isinstance(timeline_data['tracks'], list):
        for i, track in enumerate(timeline_data['tracks']):
            track_fps = track.get('frame_rate')
            if track_fps and track_fps != global_fps:
                compatible = False
                issues.append(
                    f"轨道 {i} (ID:{track.get('id', '未知')}) 帧率不匹配: "
                    f"track_fps={track_fps}, global_fps={global_fps}"
                )
    
    # 检查片段帧率
    if 'clips' in timeline_data and isinstance(timeline_data['clips'], list):
        for i, clip in enumerate(timeline_data['clips']):
            clip_fps = clip.get('fps', clip.get('frame_rate'))
            if clip_fps and clip_fps != global_fps:
                # 这可能不是严重问题，但应该警告
                issues.append(
                    f"警告: 片段 {i} (ID:{clip.get('id', '未知')}) 帧率不匹配: "
                    f"clip_fps={clip_fps}, global_fps={global_fps}"
                )
    
    return compatible, issues


def analyze_timeline(timeline_data: Dict[str, Any], max_gap: float = 0.0) -> Dict[str, Any]:
    """全面分析时间轴，生成报告
    
    执行完整的时间轴分析，包括有效性、冲突、间隙等多方面检查，生成详细报告。
    
    Args:
        timeline_data: 时间轴数据字典
        max_gap: 允许的最大间隙
        
    Returns:
        分析报告字典，包含各项检查结果
    """
    # 创建分析报告
    report = {
        'valid': True,
        'issues': [],
        'gaps': [],
        'frame_rate_compatible': True,
        'has_conflicts': False,
        'statistics': {
            'track_count': 0,
            'clip_count': 0,
            'total_duration': 0
        }
    }
    
    # 检查时间轴有效性
    valid, issues = validate_timeline(timeline_data)
    report['valid'] = valid
    report['issues'].extend(issues)
    
    # 检查帧率兼容性
    compatible, compat_issues = check_frame_rate_compatibility(timeline_data)
    report['frame_rate_compatible'] = compatible
    report['issues'].extend(compat_issues)
    
    # 收集统计信息
    if 'tracks' in timeline_data and isinstance(timeline_data['tracks'], list):
        report['statistics']['track_count'] = len(timeline_data['tracks'])
        
        # 检查每个轨道上的间隙
        for i, track in enumerate(timeline_data['tracks']):
            if 'items' in track and isinstance(track['items'], list):
                # 确定使用的键名
                sample_item = track['items'][0] if track['items'] else {}
                start_key = 'start_frame' if 'start_frame' in sample_item else 'start'
                end_key = 'end_frame' if 'end_frame' in sample_item else 'end'
                
                # 标准化键名以便分析
                normalized_items = []
                for item in track['items']:
                    normalized_item = {
                        'id': item.get('id', f'item_{len(normalized_items)}'),
                        'track_id': track.get('id', f'track_{i}'),
                        'start': item.get(start_key, 0),
                        'end': item.get(end_key, 0),
                    }
                    normalized_items.append(normalized_item)
                
                # 检测间隙
                track_gaps = detect_gaps(normalized_items, max_gap)
                if track_gaps:
                    for gap in track_gaps:
                        gap['track_id'] = track.get('id', f'track_{i}')
                    report['gaps'].extend(track_gaps)
    
    # 计算片段统计
    if 'clips' in timeline_data and isinstance(timeline_data['clips'], list):
        clips = timeline_data['clips']
        report['statistics']['clip_count'] = len(clips)
        
        # 计算总时长
        if clips:
            # 查找最大结束时间
            max_end = 0
            for clip in clips:
                end = clip.get('end_frame', clip.get('end', 0))
                if end > max_end:
                    max_end = end
            
            # 若有帧率，转换为时间
            if 'fps' in timeline_data and timeline_data['fps'] > 0:
                report['statistics']['total_duration'] = max_end / timeline_data['fps']
            else:
                report['statistics']['total_duration'] = max_end
    
    # 设置是否有冲突的标志
    report['has_conflicts'] = not valid or not compatible or report['gaps']
    
    return report


# 如果直接运行此模块，执行简单测试
if __name__ == "__main__":
    # 测试数据
    test_segments = [
        {'id': 'clip1', 'start': 0, 'end': 10},
        {'id': 'clip2', 'start': 8, 'end': 15},  # 重叠
        {'id': 'clip3', 'start': 20, 'end': 30}  # 间隙
    ]
    
    # 测试重叠检测和修复
    print("测试重叠检测和修复:")
    fixed_segments = detect_overlap(test_segments)
    for seg in fixed_segments:
        print(f"  片段 {seg['id']}: {seg['start']} - {seg['end']}")
    
    # 测试间隙检测
    print("\n测试间隙检测:")
    gaps = detect_gaps(fixed_segments, max_gap=1)
    for gap in gaps:
        print(f"  间隙: {gap['start']} - {gap['end']} (持续: {gap['duration']})")
        print(f"  位于片段 {gap['prev_segment_id']} 和 {gap['next_segment_id']} 之间") 