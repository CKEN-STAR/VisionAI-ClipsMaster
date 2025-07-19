#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 关键帧对齐器

此模块提供专门用于处理视频关键帧对齐的高级功能:
1. 场景切换点智能对齐
2. 关键帧距离优化
3. 多轨道关键帧同步
4. 视频流关键帧提取与映射
5. 基于内容的关键帧匹配

主要用于确保在视频编辑过程中关键帧的精确定位和匹配，
提高视频导出质量和播放流畅度。
"""

import math
import logging
import bisect
from typing import Union, Dict, List, Tuple, Optional, Any, Callable
import copy

from src.utils.log_handler import get_logger
from src.export.fps_converter import time_to_frames, frames_to_time
from src.export.precision_compensator import align_keyframes_to_grid, compensate_accumulated_error

# 配置日志
logger = get_logger("keyframe_aligner")


def align_to_keyframes(frame: float, keyframes: List[float], threshold: float = 3.0) -> float:
    """将指定帧对齐到最近的关键帧
    
    查找距离给定帧最近的关键帧，如果距离在阈值内则对齐到该关键帧。
    
    Args:
        frame: 需要对齐的帧号
        keyframes: 可用的关键帧列表
        threshold: 最大对齐距离阈值，超过此阈值不进行对齐
        
    Returns:
        float: 对齐后的帧号
        
    Examples:
        >>> align_to_keyframes(102, [100, 110, 120])  # 距离100最近，差值2帧，在阈值内
        100.0
        >>> align_to_keyframes(106, [100, 110, 120])  # 距离两边都是4帧，在阈值内，取较小的那个
        110.0
        >>> align_to_keyframes(95, [100, 110, 120], threshold=2)  # 差值5帧，超过阈值，保持原值
        95.0
    """
    if not keyframes:
        return frame
    
    # 如果帧值恰好是关键帧，直接返回
    if frame in keyframes:
        return frame
    
    # 找到最近的关键帧
    nearest = min(keyframes, key=lambda x: abs(x - frame))
    
    # 计算距离
    distance = abs(nearest - frame)
    
    # 如果距离在阈值内，进行对齐
    if distance <= threshold:
        logger.debug(f"帧 {frame} 对齐到关键帧 {nearest}，距离: {distance}")
        return nearest
    
    # 否则保持原值
    return frame


def find_optimal_keyframe(
    target_frame: float, 
    keyframes: List[float], 
    preference: str = 'nearest'
) -> float:
    """找到最优的关键帧进行对齐
    
    根据不同的优化策略找到最适合的关键帧。
    
    Args:
        target_frame: 目标帧
        keyframes: 可用的关键帧列表
        preference: 优先策略，可选值:
                   'nearest' - 最近的关键帧
                   'previous' - 前一个关键帧(用于剪切点)
                   'next' - 后一个关键帧(用于转场起点)
                   'content' - 基于内容重要性(需要关键帧带有权重)
        
    Returns:
        float: 最优的关键帧位置
    """
    if not keyframes:
        return target_frame
    
    # 确保关键帧列表有序
    sorted_keyframes = sorted(keyframes)
    
    if preference == 'nearest':
        # 找到最近的关键帧
        return min(sorted_keyframes, key=lambda x: abs(x - target_frame))
    
    elif preference == 'previous':
        # 找到前一个关键帧
        idx = bisect.bisect_left(sorted_keyframes, target_frame)
        if idx > 0:
            return sorted_keyframes[idx - 1]
        return sorted_keyframes[0]  # 如果没有前一个，返回第一个
    
    elif preference == 'next':
        # 找到后一个关键帧
        idx = bisect.bisect_right(sorted_keyframes, target_frame)
        if idx < len(sorted_keyframes):
            return sorted_keyframes[idx]
        return sorted_keyframes[-1]  # 如果没有后一个，返回最后一个
    
    elif preference == 'content':
        # 如果是带权重的关键帧列表(元组形式: (帧号, 权重))
        if isinstance(keyframes[0], tuple) and len(keyframes[0]) == 2:
            # 计算距离和权重的综合得分
            weighted_keyframes = [(frame, weight) for frame, weight in keyframes]
            
            # 找到得分最高的关键帧
            best_score = float('-inf')
            best_frame = target_frame
            
            for frame, weight in weighted_keyframes:
                # 距离分数(越近越高)与内容重要性分数的加权和
                distance_factor = 1.0 / (1.0 + abs(frame - target_frame))
                score = (distance_factor * 0.7) + (weight * 0.3)  # 可调整权重
                
                if score > best_score:
                    best_score = score
                    best_frame = frame
            
            return best_frame
        else:
            # 如果关键帧没有权重信息，退回到最近策略
            return min(sorted_keyframes, key=lambda x: abs(x - target_frame))
    
    # 默认返回最近的关键帧
    return min(sorted_keyframes, key=lambda x: abs(x - target_frame))


def optimize_cut_points(
    cut_points: List[float], 
    keyframes: List[float], 
    min_segment_duration: float = 1.0
) -> List[float]:
    """优化剪切点，确保它们对齐到关键帧并保持最小段落时长
    
    Args:
        cut_points: 原始剪切点列表
        keyframes: 可用的关键帧列表
        min_segment_duration: 最小段落时长(秒)
        
    Returns:
        List[float]: 优化后的剪切点
    """
    if not cut_points or not keyframes:
        return cut_points
    
    # 确保列表有序
    sorted_cuts = sorted(cut_points)
    sorted_keyframes = sorted(keyframes)
    
    optimized_cuts = []
    previous_cut = 0  # 假设时间轴从0开始
    
    for cut in sorted_cuts:
        # 找到最近的关键帧
        aligned_cut = find_optimal_keyframe(cut, sorted_keyframes, preference='previous')
        
        # 确保与前一个剪切点的距离不小于最小段落时长
        if aligned_cut - previous_cut < min_segment_duration:
            # 尝试使用下一个关键帧
            next_candidate = find_optimal_keyframe(cut, sorted_keyframes, preference='next')
            if next_candidate - previous_cut >= min_segment_duration:
                aligned_cut = next_candidate
            else:
                # 如果下一个关键帧也不满足，则强制设置为最小距离
                aligned_cut = previous_cut + min_segment_duration
        
        optimized_cuts.append(aligned_cut)
        previous_cut = aligned_cut
    
    return optimized_cuts


def extract_keyframes_from_timeline(
    timeline_data: Dict[str, Any], 
    min_distance: float = 0.5
) -> List[float]:
    """从时间轴数据中提取潜在的关键帧位置
    
    分析时间轴上的片段起止点、转场和标记点，提取可能的关键帧位置。
    
    Args:
        timeline_data: 时间轴数据字典
        min_distance: 关键帧之间的最小距离(秒)
        
    Returns:
        List[float]: 提取的关键帧时间列表
    """
    keyframes = set()
    fps = timeline_data.get('fps', 30.0)
    
    # 提取片段边界作为潜在关键帧
    if 'clips' in timeline_data and isinstance(timeline_data['clips'], list):
        for clip in timeline_data['clips']:
            if 'start_frame' in clip:
                keyframes.add(frames_to_time(clip['start_frame'], fps))
            if 'end_frame' in clip:
                keyframes.add(frames_to_time(clip['end_frame'], fps))
    
    # 提取轨道项目边界
    if 'tracks' in timeline_data and isinstance(timeline_data['tracks'], list):
        for track in timeline_data['tracks']:
            if 'items' in track and isinstance(track['items'], list):
                for item in track['items']:
                    if 'start_frame' in item:
                        keyframes.add(frames_to_time(item['start_frame'], fps))
                    if 'end_frame' in item:
                        keyframes.add(frames_to_time(item['end_frame'], fps))
    
    # 转换为列表并排序
    keyframe_list = sorted(list(keyframes))
    
    # 删除太近的关键帧
    if min_distance > 0:
        filtered_keyframes = []
        last_kf = -float('inf')
        
        for kf in keyframe_list:
            if kf - last_kf >= min_distance:
                filtered_keyframes.append(kf)
                last_kf = kf
        
        return filtered_keyframes
    
    return keyframe_list


def synchronize_keyframes_across_tracks(
    timeline_data: Dict[str, Any],
    max_offset: float = 0.1
) -> Dict[str, Any]:
    """同步不同轨道上的关键帧
    
    确保不同轨道上的相近关键帧保持对齐，避免轻微的时间差异。
    
    Args:
        timeline_data: 时间轴数据字典
        max_offset: 允许的最大偏移量(秒)
        
    Returns:
        Dict[str, Any]: 同步后的时间轴数据
    """
    if 'tracks' not in timeline_data or not isinstance(timeline_data['tracks'], list):
        return timeline_data
    
    # 创建深拷贝避免修改原始数据
    result = copy.deepcopy(timeline_data)
    fps = result.get('fps', 30.0)
    
    # 首先收集所有轨道上的关键时间点
    all_key_times = []
    track_key_times = []
    
    for track in result['tracks']:
        if 'items' in track and isinstance(track['items'], list):
            track_times = []
            for item in track['items']:
                if 'start_frame' in item:
                    time = frames_to_time(item['start_frame'], fps)
                    track_times.append((time, 'start_frame', item))
                    all_key_times.append(time)
                
                if 'end_frame' in item:
                    time = frames_to_time(item['end_frame'], fps)
                    track_times.append((time, 'end_frame', item))
                    all_key_times.append(time)
            
            track_key_times.append(track_times)
    
    # 对所有时间点进行聚类，找出需要对齐的组
    if not all_key_times:
        return result
    
    # 排序所有时间点
    all_key_times.sort()
    
    # 基于时间接近度对时间点进行聚类
    clusters = []
    current_cluster = [all_key_times[0]]
    
    for i in range(1, len(all_key_times)):
        if all_key_times[i] - all_key_times[i-1] <= max_offset:
            current_cluster.append(all_key_times[i])
        else:
            if len(current_cluster) > 1:  # 只对有多个点的簇进行处理
                clusters.append(current_cluster)
            current_cluster = [all_key_times[i]]
    
    # 加入最后一个簇
    if len(current_cluster) > 1:
        clusters.append(current_cluster)
    
    # 对每个簇，计算平均时间作为对齐标准
    for cluster in clusters:
        avg_time = sum(cluster) / len(cluster)
        
        # 更新所有在这个簇中的时间点
        for track_times in track_key_times:
            for time_data in track_times:
                time, key, item = time_data
                if time in cluster:
                    # 计算帧号
                    aligned_frame = time_to_frames(avg_time, fps)
                    item[key] = aligned_frame
    
    return result


class KeyframeAligner:
    """关键帧对齐器类
    
    提供全面的关键帧分析、提取和对齐功能的综合类。
    """
    
    def __init__(self, default_fps: float = 30.0):
        """初始化关键帧对齐器
        
        Args:
            default_fps: 默认帧率，用于未指定帧率的情况
        """
        self.default_fps = default_fps
        self.logger = get_logger("keyframe_aligner")
    
    def extract_keyframes(
        self, 
        video_info: Dict[str, Any], 
        source: str = 'auto'
    ) -> List[float]:
        """从视频中提取关键帧
        
        Args:
            video_info: 视频信息字典，包含帧率、时长等
            source: 关键帧来源，可选值:
                   'auto' - 自动检测
                   'timeline' - 从时间轴数据提取
                   'metadata' - 从视频元数据提取
                   'content' - 基于内容分析提取
            
        Returns:
            List[float]: 提取的关键帧列表(时间点，秒)
        """
        fps = video_info.get('fps', self.default_fps)
        keyframes = []
        
        if source == 'timeline' or source == 'auto':
            # 如果有时间轴数据，从中提取
            if 'timeline' in video_info:
                timeline_keyframes = extract_keyframes_from_timeline(video_info['timeline'])
                keyframes.extend(timeline_keyframes)
        
        if (source == 'metadata' or source == 'auto') and not keyframes:
            # 从视频元数据中提取
            if 'keyframes' in video_info:
                keyframes.extend(video_info['keyframes'])
        
        if (source == 'content' or source == 'auto') and not keyframes:
            # 基于内容计算关键帧（此处仅为示例，实际应根据视频内容分析）
            # 在实际应用中，这可能需要调用视频分析工具来识别场景切换点
            duration = video_info.get('duration', 0)
            if duration > 0:
                # 简单示例：每5秒放置一个关键帧
                keyframes = [i * 5 for i in range(int(duration / 5) + 1)]
        
        # 确保关键帧列表有序
        return sorted(keyframes)
    
    def optimize_timeline_keyframes(
        self, 
        timeline_data: Dict[str, Any], 
        video_info: Optional[Dict[str, Any]] = None,
        strictness: str = 'medium'
    ) -> Dict[str, Any]:
        """优化时间轴上的关键帧
        
        对时间轴数据进行全面分析和优化，确保关键帧对齐和一致性。
        
        Args:
            timeline_data: 时间轴数据字典
            video_info: 视频信息字典，包含真实关键帧数据
            strictness: 优化严格程度，可选值: 'low', 'medium', 'high'
            
        Returns:
            Dict[str, Any]: 优化后的时间轴数据
        """
        # 创建深拷贝避免修改原始数据
        result = copy.deepcopy(timeline_data)
        fps = result.get('fps', self.default_fps)
        
        # 根据严格程度设置参数
        if strictness == 'low':
            threshold = 5.0  # 帧
            min_segment = 0.5  # 秒
        elif strictness == 'medium':
            threshold = 3.0
            min_segment = 1.0
        else:  # high
            threshold = 1.0
            min_segment = 2.0
        
        # 获取参考关键帧
        reference_keyframes = []
        
        if video_info and 'keyframes' in video_info:
            # 优先使用视频实际关键帧
            reference_keyframes = video_info['keyframes']
        else:
            # 否则从时间轴数据中提取
            reference_keyframes = extract_keyframes_from_timeline(result)
        
        if not reference_keyframes:
            self.logger.warning("没有找到关键帧数据，无法进行优化")
            return result
        
        # 转换为帧号
        keyframes_frames = [time_to_frames(t, fps) for t in reference_keyframes]
        
        # 优化片段边界
        if 'clips' in result and isinstance(result['clips'], list):
            for clip in result['clips']:
                if 'start_frame' in clip:
                    clip['start_frame'] = align_to_keyframes(
                        clip['start_frame'], keyframes_frames, threshold
                    )
                if 'end_frame' in clip:
                    clip['end_frame'] = align_to_keyframes(
                        clip['end_frame'], keyframes_frames, threshold
                    )
        
        # 优化轨道项目
        if 'tracks' in result and isinstance(result['tracks'], list):
            for track in result['tracks']:
                if 'items' in track and isinstance(track['items'], list):
                    # 收集所有剪切点
                    cut_points = []
                    for item in track['items']:
                        if 'start_frame' in item:
                            cut_points.append(item['start_frame'])
                        if 'end_frame' in item:
                            cut_points.append(item['end_frame'])
                    
                    # 优化剪切点
                    optimized_cuts = optimize_cut_points(
                        cut_points, keyframes_frames, min_segment * fps
                    )
                    
                    # 创建映射关系
                    cut_map = {old: new for old, new in zip(sorted(cut_points), optimized_cuts)}
                    
                    # 更新项目
                    for item in track['items']:
                        if 'start_frame' in item:
                            item['start_frame'] = cut_map.get(item['start_frame'], item['start_frame'])
                        if 'end_frame' in item:
                            item['end_frame'] = cut_map.get(item['end_frame'], item['end_frame'])
        
        # 同步轨道间的关键帧
        result = synchronize_keyframes_across_tracks(result, max_offset=1.0/fps)
        
        return result
    
    def analyze_keyframe_alignment(
        self, 
        timeline_data: Dict[str, Any],
        reference_keyframes: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """分析时间轴的关键帧对齐状况
        
        检查时间轴上的关键时间点与参考关键帧的对齐情况。
        
        Args:
            timeline_data: 时间轴数据字典
            reference_keyframes: 参考关键帧列表，如果为None则从时间轴数据中提取
            
        Returns:
            Dict[str, Any]: 分析报告
        """
        fps = timeline_data.get('fps', self.default_fps)
        
        # 如果没有提供参考关键帧，则从时间轴数据中提取
        if reference_keyframes is None:
            reference_keyframes = extract_keyframes_from_timeline(timeline_data)
        
        # 获取时间轴上的所有剪切点
        cut_points = []
        
        # 从片段中提取
        if 'clips' in timeline_data and isinstance(timeline_data['clips'], list):
            for clip in timeline_data['clips']:
                if 'start_frame' in clip:
                    cut_points.append(frames_to_time(clip['start_frame'], fps))
                if 'end_frame' in clip:
                    cut_points.append(frames_to_time(clip['end_frame'], fps))
        
        # 从轨道项目中提取
        if 'tracks' in timeline_data and isinstance(timeline_data['tracks'], list):
            for track in timeline_data['tracks']:
                if 'items' in track and isinstance(track['items'], list):
                    for item in track['items']:
                        if 'start_frame' in item:
                            cut_points.append(frames_to_time(item['start_frame'], fps))
                        if 'end_frame' in item:
                            cut_points.append(frames_to_time(item['end_frame'], fps))
        
        # 删除重复值并排序
        cut_points = sorted(set(cut_points))
        
        # 统计对齐和非对齐的剪切点
        aligned = 0
        non_aligned = 0
        misalignment_stats = []
        
        # 对齐阈值
        threshold_time = 0.1  # 100毫秒
        
        for cut in cut_points:
            # 查找最近的参考关键帧
            if reference_keyframes:
                nearest = min(reference_keyframes, key=lambda x: abs(x - cut))
                distance = abs(nearest - cut)
                
                if distance <= threshold_time:
                    aligned += 1
                else:
                    non_aligned += 1
                    misalignment_stats.append({
                        'cut_point': cut,
                        'nearest_keyframe': nearest,
                        'distance': distance
                    })
        
        # 生成报告
        total_cuts = len(cut_points)
        alignment_rate = aligned / total_cuts if total_cuts > 0 else 0
        
        report = {
            'total_cut_points': total_cuts,
            'aligned_cuts': aligned,
            'non_aligned_cuts': non_aligned,
            'alignment_rate': alignment_rate,
            'avg_misalignment': (
                sum(item['distance'] for item in misalignment_stats) / 
                len(misalignment_stats) if misalignment_stats else 0
            ),
            'misaligned_cuts': sorted(
                misalignment_stats, 
                key=lambda x: x['distance'], 
                reverse=True
            )[:10]  # 显示最严重的10个不对齐点
        }
        
        return report


# 如果直接运行此模块，执行简单测试
if __name__ == "__main__":
    # 测试关键帧对齐
    print("1. 测试关键帧对齐:")
    keyframes = [100, 110, 120, 130, 140]
    test_frames = [101, 108, 119, 125, 150]
    
    for frame in test_frames:
        aligned = align_to_keyframes(frame, keyframes)
        print(f"  原始帧: {frame}, 对齐到: {aligned}")
    
    # 测试最优关键帧查找
    print("\n2. 测试最优关键帧查找:")
    for frame in [105, 115, 135]:
        previous = find_optimal_keyframe(frame, keyframes, 'previous')
        next_kf = find_optimal_keyframe(frame, keyframes, 'next')
        nearest = find_optimal_keyframe(frame, keyframes, 'nearest')
        
        print(f"  帧 {frame}:")
        print(f"    前一个关键帧: {previous}")
        print(f"    后一个关键帧: {next_kf}")
        print(f"    最近的关键帧: {nearest}")
    
    # 测试剪切点优化
    print("\n3. 测试剪切点优化:")
    cut_points = [103, 112, 116, 142]
    optimized = optimize_cut_points(cut_points, keyframes)
    
    print("  原始剪切点:", cut_points)
    print("  优化后剪切点:", optimized) 