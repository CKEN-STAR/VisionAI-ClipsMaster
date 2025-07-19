#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 精度补偿器

此模块提供了一系列用于处理时间轴编辑、帧率转换和时间码转换中精度问题的功能:
1. 舍入误差补偿
2. 累积误差检测与修正
3. 时间码精度优化
4. 时间轴对齐修正

主要用于确保在视频编辑和导出过程中时间精度的一致性，
防止由于舍入、累积误差导致的时间轴不准确问题。
"""

import math
import logging
from typing import Union, Dict, List, Tuple, Optional, Any, Callable
from enum import Enum
import copy

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("precision_compensator")


def compensate_rounding_error(original: float, converted: float, fps: float) -> float:
    """补偿舍入误差
    
    在帧率转换过程中，修正由于舍入导致的误差，特别是对于关键时间点。
    当误差超过半帧时，对结果进行补偿调整。
    
    Args:
        original: 原始值（通常是时间或帧号）
        converted: 转换后的值
        fps: 帧率
        
    Returns:
        float: 修正后的值
        
    Examples:
        >>> compensate_rounding_error(10.0, 9.9, 30.0)  # 误差为0.1，小于半帧(0.5/30)
        9.9
        >>> compensate_rounding_error(10.0, 9.98, 60.0)  # 误差大于半帧(0.5/60)
        10.0
    """
    # 计算误差绝对值
    error = abs(original - (converted / fps))
    
    # 如果误差超过半帧，进行补偿
    if error > 0.5 / fps:
        # 根据原始值和转换值的大小关系决定补偿方向
        direction = 1 if original > converted/fps else -1
        return converted + direction
    
    return converted


def compensate_accumulated_error(
    times: List[float], 
    fps: float, 
    threshold: float = 0.5
) -> List[float]:
    """补偿累积误差
    
    检测并修正一系列时间点中可能累积的误差，确保整体时间线的准确性。
    
    Args:
        times: 时间点列表
        fps: 帧率
        threshold: 触发补偿的误差阈值（帧的比例，默认0.5即半帧）
        
    Returns:
        List[float]: 修正后的时间点列表
    """
    if not times:
        return []
    
    # 创建副本避免修改原始数据
    corrected = copy.deepcopy(times)
    
    # 跟踪累积误差
    accumulated_error = 0.0
    frame_duration = 1.0 / fps
    
    # 对每个时间点计算并修正累积误差
    for i in range(1, len(corrected)):
        # 计算相邻时间点的间隔
        interval = corrected[i] - corrected[i-1]
        
        # 计算理想的帧数（四舍五入到最接近的整数）
        ideal_frames = round(interval * fps)
        
        # 理想情况下的间隔时间
        ideal_interval = ideal_frames * frame_duration
        
        # 当前间隔与理想间隔的误差
        current_error = interval - ideal_interval
        
        # 累积误差
        accumulated_error += current_error
        
        # 如果累积误差超过阈值，进行修正
        if abs(accumulated_error) > threshold * frame_duration:
            # 计算需要修正的帧数
            frames_to_adjust = round(accumulated_error * fps)
            
            # 修正当前时间点
            corrected[i] = corrected[i] - (frames_to_adjust * frame_duration)
            
            # 重置累积误差（可能会保留一些小误差）
            accumulated_error -= (frames_to_adjust * frame_duration)
            
            logger.info(
                f"在时间点{i}处修正了{frames_to_adjust}帧的累积误差，"
                f"原值: {times[i]:.6f}，修正为: {corrected[i]:.6f}"
            )
    
    return corrected


def optimize_timecode_precision(
    timecode: str, 
    fps: float,
    reference_fps: Optional[float] = None
) -> str:
    """优化时间码精度
    
    确保时间码在给定帧率下的精确表示，避免舍入误差导致的不准确。
    
    Args:
        timecode: 时间码字符串 (格式: "HH:MM:SS.mmm" or "HH:MM:SS:FF")
        fps: 当前时间码的帧率
        reference_fps: 参考帧率，用于跨帧率转换的精度优化
        
    Returns:
        str: 优化后的时间码
    """
    from src.export.fps_converter import timecode_to_frames, frames_to_timecode
    
    # 先转换为帧
    frames = timecode_to_frames(timecode, fps)
    
    # 如果有参考帧率，使用它来优化精度
    if reference_fps and reference_fps != fps:
        # 计算在参考帧率下的等效帧数
        equivalent_frames = round(frames * (reference_fps / fps))
        # 然后转回原始帧率
        frames = round(equivalent_frames * (fps / reference_fps))
    
    # 使用帧数重新生成时间码(使用与输入相同的格式)
    use_frames_format = ":" in timecode.split(":")[-1]  # 检查是否使用帧格式
    optimized = frames_to_timecode(frames, fps, use_frames=use_frames_format)
    
    return optimized


def align_keyframes_to_grid(
    keyframes: List[float], 
    fps: float, 
    strict: bool = False
) -> List[float]:
    """将关键帧对齐到帧网格
    
    确保关键帧时间点严格对齐到帧网格，避免亚帧位置导致的问题。
    
    Args:
        keyframes: 关键帧时间点列表(秒)
        fps: 帧率
        strict: 是否严格对齐(True=精确到帧边界，False=允许亚帧插值)
        
    Returns:
        List[float]: 对齐后的关键帧时间点
    """
    if not keyframes:
        return []
    
    # 创建副本避免修改原始数据
    aligned = []
    frame_duration = 1.0 / fps
    
    for time in keyframes:
        # 计算对应的帧数
        frame = time * fps
        
        if strict:
            # 严格对齐到最近的帧
            aligned_frame = round(frame)
            aligned_time = aligned_frame * frame_duration
        else:
            # 允许亚帧位置，但避免极小偏差
            frame_fraction = frame - math.floor(frame)
            if frame_fraction < 0.02:  # 如果非常接近帧边界
                aligned_time = math.floor(frame) * frame_duration
            elif frame_fraction > 0.98:  # 如果非常接近下一帧
                aligned_time = math.ceil(frame) * frame_duration
            else:
                aligned_time = time  # 保持原值
        
        aligned.append(aligned_time)
    
    return aligned


def correct_timeline_precision(
    timeline_data: Dict[str, Any], 
    fps: float
) -> Dict[str, Any]:
    """修正时间轴精度
    
    扫描时间轴数据，并应用各种精度补偿策略，确保时间轴准确性。
    
    Args:
        timeline_data: 时间轴数据字典
        fps: 时间轴帧率
        
    Returns:
        Dict[str, Any]: 精度修正后的时间轴数据
    """
    # 创建深拷贝避免修改原始数据
    result = copy.deepcopy(timeline_data)
    
    # 修正片段时间数据
    if 'clips' in result and isinstance(result['clips'], list):
        for clip in result['clips']:
            # 修正基于帧的时间属性
            for key in ['start_frame', 'end_frame', 'in_frame', 'out_frame']:
                if key in clip and isinstance(clip[key], (int, float)):
                    # 关键时间点应该是整数帧
                    clip[key] = round(clip[key])
            
            # 修正基于秒的时间属性
            for key in ['start_time', 'end_time', 'duration']:
                if key in clip and isinstance(clip[key], (int, float)):
                    # 确保时间精度与帧率一致
                    frame = round(clip[key] * fps)
                    clip[key] = frame / fps
    
    # 修正轨道时间数据
    if 'tracks' in result and isinstance(result['tracks'], list):
        for track in result['tracks']:
            if 'items' in track and isinstance(track['items'], list):
                for item in track['items']:
                    # 修正轨道项目的时间属性
                    for key in ['start_frame', 'end_frame']:
                        if key in item and isinstance(item[key], (int, float)):
                            # 关键时间点应该是整数帧
                            item[key] = round(item[key])
    
    # 修正关键点时间数据
    if 'keypoints' in result and isinstance(result['keypoints'], list):
        times = [kp.get('time', 0) for kp in result['keypoints'] if 'time' in kp]
        
        # 对关键点时间进行累积误差修正
        if times:
            corrected_times = compensate_accumulated_error(times, fps)
            
            # 更新关键点时间
            for i, kp in enumerate(result['keypoints']):
                if 'time' in kp:
                    kp['time'] = corrected_times[i]
    
    return result


def analyze_precision_issues(
    timeline_data: Dict[str, Any], 
    fps: float
) -> List[Dict[str, Any]]:
    """分析时间轴精度问题
    
    扫描时间轴数据并识别潜在的精度问题，生成报告。
    
    Args:
        timeline_data: 时间轴数据字典
        fps: 时间轴帧率
        
    Returns:
        List[Dict[str, Any]]: 精度问题报告列表
    """
    issues = []
    frame_duration = 1.0 / fps
    
    # 检查片段时间精度
    if 'clips' in timeline_data and isinstance(timeline_data['clips'], list):
        for i, clip in enumerate(timeline_data['clips']):
            # 检查非整数帧
            for key in ['start_frame', 'end_frame', 'in_frame', 'out_frame']:
                if key in clip and isinstance(clip[key], (int, float)):
                    if clip[key] != round(clip[key]):
                        issues.append({
                            'type': 'non_integer_frame',
                            'severity': 'warning',
                            'item_type': 'clip',
                            'item_id': clip.get('id', f'clip_{i}'),
                            'property': key,
                            'value': clip[key],
                            'expected': round(clip[key]),
                            'description': f"片段{clip.get('id', i)}的{key}不是整数帧: {clip[key]}"
                        })
            
            # 检查时间与帧的一致性
            if 'start_frame' in clip and 'start_time' in clip:
                expected_time = clip['start_frame'] * frame_duration
                if abs(clip['start_time'] - expected_time) > frame_duration * 0.1:
                    issues.append({
                        'type': 'time_frame_mismatch',
                        'severity': 'error',
                        'item_type': 'clip',
                        'item_id': clip.get('id', f'clip_{i}'),
                        'properties': ['start_frame', 'start_time'],
                        'values': [clip['start_frame'], clip['start_time']],
                        'expected': expected_time,
                        'description': (
                            f"片段{clip.get('id', i)}的start_frame({clip['start_frame']})与"
                            f"start_time({clip['start_time']})不一致，期望值: {expected_time:.6f}"
                        )
                    })
    
    # 检查轨道项目时间精度
    if 'tracks' in timeline_data and isinstance(timeline_data['tracks'], list):
        for t, track in enumerate(timeline_data['tracks']):
            if 'items' in track and isinstance(track['items'], list):
                for i, item in enumerate(track['items']):
                    # 检查非整数帧
                    for key in ['start_frame', 'end_frame']:
                        if key in item and isinstance(item[key], (int, float)):
                            if item[key] != round(item[key]):
                                issues.append({
                                    'type': 'non_integer_frame',
                                    'severity': 'warning',
                                    'item_type': 'track_item',
                                    'track_id': track.get('id', f'track_{t}'),
                                    'item_id': item.get('id', f'item_{i}'),
                                    'property': key,
                                    'value': item[key],
                                    'expected': round(item[key]),
                                    'description': (
                                        f"轨道{track.get('id', t)}中项目{item.get('id', i)}的"
                                        f"{key}不是整数帧: {item[key]}"
                                    )
                                })
    
    return issues


class PrecisionCompensator:
    """精度补偿器类
    
    提供全面的精度补偿和分析功能的综合类。
    """
    
    def __init__(self, default_fps: float = 30.0):
        """初始化精度补偿器
        
        Args:
            default_fps: 默认帧率，用于未指定帧率的情况
        """
        self.default_fps = default_fps
        self.logger = get_logger("precision_compensator")
    
    def compensate_timeline(
        self, 
        timeline_data: Dict[str, Any], 
        fps: Optional[float] = None,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """补偿整个时间轴的精度问题
        
        Args:
            timeline_data: 时间轴数据字典
            fps: 帧率，如果未指定则使用时间轴中的fps或默认值
            strict_mode: 是否使用严格模式(更强的精度要求)
            
        Returns:
            Dict[str, Any]: 补偿后的时间轴数据
        """
        # 确定使用的帧率
        timeline_fps = fps or timeline_data.get('fps', self.default_fps)
        
        # 分析当前精度问题
        issues = analyze_precision_issues(timeline_data, timeline_fps)
        if issues:
            self.logger.info(f"检测到{len(issues)}个精度问题，开始修正...")
            for issue in issues:
                if issue['severity'] == 'error':
                    self.logger.warning(
                        f"严重精度问题: {issue['description']}"
                    )
                else:
                    self.logger.info(
                        f"精度警告: {issue['description']}"
                    )
        
        # 应用精度修正
        corrected = correct_timeline_precision(timeline_data, timeline_fps)
        
        # 如果使用严格模式，还要对关键帧进行额外处理
        if strict_mode and 'keypoints' in corrected:
            if isinstance(corrected['keypoints'], list):
                times = [kp.get('time', 0) for kp in corrected['keypoints'] if 'time' in kp]
                if times:
                    aligned_times = align_keyframes_to_grid(times, timeline_fps, strict=True)
                    for i, kp in enumerate(corrected['keypoints']):
                        if 'time' in kp:
                            kp['time'] = aligned_times[i]
        
        return corrected
    
    def analyze_and_report(
        self, 
        timeline_data: Dict[str, Any], 
        fps: Optional[float] = None
    ) -> Dict[str, Any]:
        """分析并报告时间轴精度问题
        
        Args:
            timeline_data: 时间轴数据字典
            fps: 帧率，如果未指定则使用时间轴中的fps或默认值
            
        Returns:
            Dict[str, Any]: 精度分析报告
        """
        # 确定使用的帧率
        timeline_fps = fps or timeline_data.get('fps', self.default_fps)
        
        # 进行精度问题分析
        issues = analyze_precision_issues(timeline_data, timeline_fps)
        
        # 统计问题按类型和严重性
        stats = {
            'total_issues': len(issues),
            'by_severity': {},
            'by_type': {},
            'by_item_type': {}
        }
        
        for issue in issues:
            # 按严重性统计
            severity = issue.get('severity', 'unknown')
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # 按类型统计
            issue_type = issue.get('type', 'unknown')
            stats['by_type'][issue_type] = stats['by_type'].get(issue_type, 0) + 1
            
            # 按项目类型统计
            item_type = issue.get('item_type', 'unknown')
            stats['by_item_type'][item_type] = stats['by_item_type'].get(item_type, 0) + 1
        
        # 生成综合报告
        report = {
            'timeline_fps': timeline_fps,
            'issues': issues,
            'statistics': stats,
            'has_critical_issues': any(issue['severity'] == 'error' for issue in issues)
        }
        
        return report


# 如果直接运行此模块，执行简单测试
if __name__ == "__main__":
    # 测试舍入误差补偿
    print("1. 测试舍入误差补偿:")
    test_cases = [
        (10.0, 10, 30.0),  # 无误差
        (10.0, 9, 30.0),   # 大误差，需要补偿 
        (10.0, 10.01, 60.0)  # 小误差，无需补偿
    ]
    
    for original, converted, fps in test_cases:
        result = compensate_rounding_error(original, converted, fps)
        error = abs(original - (converted / fps))
        print(f"  原始: {original}, 转换后: {converted}, 帧率: {fps}")
        print(f"  误差: {error:.6f}, 补偿后: {result}")
    
    # 测试累积误差补偿
    print("\n2. 测试累积误差补偿:")
    test_times = [0.0, 1.01, 2.03, 3.02, 4.06]
    fps = 30.0
    corrected = compensate_accumulated_error(test_times, fps)
    
    print("  原始时间点:")
    for i, t in enumerate(test_times):
        print(f"    {i}: {t:.6f}")
    
    print("  修正后时间点:")
    for i, t in enumerate(corrected):
        print(f"    {i}: {t:.6f}")
    
    # 测试关键帧对齐
    print("\n3. 测试关键帧对齐:")
    test_keyframes = [1.003, 2.996, 3.5, 4.001]
    fps = 30.0
    
    aligned = align_keyframes_to_grid(test_keyframes, fps)
    strict_aligned = align_keyframes_to_grid(test_keyframes, fps, strict=True)
    
    print("  原始关键帧:")
    for i, k in enumerate(test_keyframes):
        frames = k * fps
        print(f"    {i}: {k:.6f} ({frames:.3f}帧)")
    
    print("  常规对齐后:")
    for i, k in enumerate(aligned):
        frames = k * fps
        print(f"    {i}: {k:.6f} ({frames:.3f}帧)")
    
    print("  严格对齐后:")
    for i, k in enumerate(strict_aligned):
        frames = k * fps
        print(f"    {i}: {k:.6f} ({frames:.0f}帧)") 