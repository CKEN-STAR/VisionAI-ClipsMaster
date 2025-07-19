#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 容错修复机制

此模块提供用于检测和修复导出内容中常见错误的功能。
包括对时间段、元数据和内容的自动修复，确保导出结果的正确性。

主要功能：
1. 修复无效的片段（起止时间错误）
2. 修复元数据不一致
3. 修复时间线冲突
4. 处理空内容和引用错误
5. 智能内容验证和修复
"""

import os
import re
import json
import logging
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

from src.utils.log_handler import get_logger
from src.utils.exceptions import ClipMasterError, ValidationError
from src.export.timeline_checker import detect_overlap, detect_gaps

# 配置日志
logger = get_logger("error_fixer")


def fix_invalid_segment(seg: Dict[str, Any]) -> Dict[str, Any]:
    """修复无效片段（开始>结束）
    
    Args:
        seg: 包含start和end键的片段字典
        
    Returns:
        修复后的片段
    """
    # 复制片段以避免修改原始数据
    fixed_seg = seg.copy()
    
    if 'start' in fixed_seg and 'end' in fixed_seg:
        # 检查并修复开始时间大于结束时间的情况
        if fixed_seg['start'] >= fixed_seg['end']:
            logger.warning(f"修复异常时间段 (开始>结束): {fixed_seg['id'] if 'id' in fixed_seg else ''}")
            fixed_seg['end'] = fixed_seg['start'] + 1  # 最小限度1秒
    
    return fixed_seg


def fix_negative_duration(seg: Dict[str, Any]) -> Dict[str, Any]:
    """修复负持续时间
    
    Args:
        seg: 包含duration键的片段字典
        
    Returns:
        修复后的片段
    """
    fixed_seg = seg.copy()
    
    # 检查持续时间是否为负值
    if 'duration' in fixed_seg and fixed_seg['duration'] < 0:
        logger.warning(f"修复负持续时间: {fixed_seg['id'] if 'id' in fixed_seg else ''}")
        fixed_seg['duration'] = abs(fixed_seg['duration'])
        
        # 如果有开始和结束时间，确保它们一致
        if 'start' in fixed_seg and 'end' in fixed_seg:
            fixed_seg['end'] = fixed_seg['start'] + fixed_seg['duration']
    
    return fixed_seg


def fix_metadata_consistency(seg: Dict[str, Any]) -> Dict[str, Any]:
    """修复元数据不一致问题
    
    确保片段的start, end和duration值相互一致
    
    Args:
        seg: 片段字典
        
    Returns:
        修复后的片段
    """
    fixed_seg = seg.copy()
    
    # 检查start、end和duration是否存在并一致
    has_start = 'start' in fixed_seg
    has_end = 'end' in fixed_seg
    has_duration = 'duration' in fixed_seg
    
    if has_start and has_end and has_duration:
        # 所有三个值都存在，检查一致性
        calculated_duration = fixed_seg['end'] - fixed_seg['start']
        if abs(calculated_duration - fixed_seg['duration']) > 0.001:  # 允许小误差
            logger.warning(f"修复元数据不一致: {fixed_seg['id'] if 'id' in fixed_seg else ''}")
            fixed_seg['duration'] = calculated_duration
    elif has_start and has_end and not has_duration:
        # 计算缺失的duration
        fixed_seg['duration'] = fixed_seg['end'] - fixed_seg['start']
    elif has_start and has_duration and not has_end:
        # 计算缺失的end
        fixed_seg['end'] = fixed_seg['start'] + fixed_seg['duration']
    elif has_end and has_duration and not has_start:
        # 计算缺失的start
        fixed_seg['start'] = fixed_seg['end'] - fixed_seg['duration']
    
    return fixed_seg


def fix_empty_content(seg: Dict[str, Any]) -> Dict[str, Any]:
    """修复空内容问题
    
    Args:
        seg: 片段字典
        
    Returns:
        修复后的片段
    """
    fixed_seg = seg.copy()
    
    # 检查内容是否为空
    if 'content' in fixed_seg and (fixed_seg['content'] is None or fixed_seg['content'] == ''):
        logger.warning(f"修复空内容: {fixed_seg['id'] if 'id' in fixed_seg else ''}")
        
        # 使用默认内容或ID作为内容
        if 'id' in fixed_seg:
            fixed_seg['content'] = f"Segment {fixed_seg['id']}"
        else:
            fixed_seg['content'] = "Unnamed Segment"
    
    # 检查标题是否为空
    if 'title' in fixed_seg and (fixed_seg['title'] is None or fixed_seg['title'] == ''):
        logger.warning(f"修复空标题: {fixed_seg['id'] if 'id' in fixed_seg else ''}")
        
        # 使用内容前几个字符或ID作为标题
        if 'content' in fixed_seg and fixed_seg['content']:
            # 取内容的前20个字符作为标题
            fixed_seg['title'] = fixed_seg['content'][:20] + ('...' if len(fixed_seg['content']) > 20 else '')
        elif 'id' in fixed_seg:
            fixed_seg['title'] = f"Segment {fixed_seg['id']}"
        else:
            fixed_seg['title'] = "Unnamed Segment"
    
    return fixed_seg


def fix_invalid_references(seg: Dict[str, Any], valid_assets: List[str] = None) -> Dict[str, Any]:
    """修复无效的资源引用
    
    Args:
        seg: 片段字典
        valid_assets: 有效资源ID列表
        
    Returns:
        修复后的片段
    """
    fixed_seg = seg.copy()
    
    # 如果没有提供有效资源列表，则跳过验证
    if not valid_assets:
        return fixed_seg
    
    # 检查asset_id是否有效
    if 'asset_id' in fixed_seg and fixed_seg['asset_id'] not in valid_assets:
        logger.warning(f"修复无效资源引用: {fixed_seg['id'] if 'id' in fixed_seg else ''} 引用无效资源 {fixed_seg['asset_id']}")
        
        # 尝试找到一个有效的资源ID
        if valid_assets:
            fixed_seg['asset_id'] = valid_assets[0]
            logger.info(f"已将资源ID更改为 {fixed_seg['asset_id']}")
        else:
            # 如果没有有效资源，则删除引用
            del fixed_seg['asset_id']
            logger.info("已移除无效的资源引用")
    
    return fixed_seg


def fix_overlapping_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """修复重叠片段
    
    Args:
        segments: 片段列表
        
    Returns:
        修复后的片段列表
    """
    # 检查列表是否为空
    if not segments:
        return []
    
    # 复制列表以避免修改原始数据
    fixed_segments = [seg.copy() for seg in segments]
    
    # 按开始时间排序
    fixed_segments.sort(key=lambda x: x.get('start', 0))
    
    # 检查并修复重叠
    for i in range(len(fixed_segments) - 1):
        curr_seg = fixed_segments[i]
        next_seg = fixed_segments[i + 1]
        
        if 'end' in curr_seg and 'start' in next_seg:
            # 如果当前片段结束时间大于下一个片段开始时间，则调整
            if curr_seg['end'] > next_seg['start']:
                logger.warning(f"修复重叠片段: {curr_seg['id'] if 'id' in curr_seg else ''} 和 {next_seg['id'] if 'id' in next_seg else ''}")
                
                # 计算重叠量
                overlap = curr_seg['end'] - next_seg['start']
                
                # 平均分配重叠
                curr_seg['end'] -= overlap / 2
                next_seg['start'] += overlap / 2
                
                # 更新持续时间
                if 'duration' in curr_seg:
                    curr_seg['duration'] = curr_seg['end'] - curr_seg.get('start', 0)
                if 'duration' in next_seg:
                    next_seg['duration'] = next_seg.get('end', 0) - next_seg['start']
    
    return fixed_segments


def fix_timeline_gaps(segments: List[Dict[str, Any]], allow_gaps: bool = True, 
                     max_gap: float = 5.0) -> List[Dict[str, Any]]:
    """修复时间线中的间隙
    
    Args:
        segments: 片段列表
        allow_gaps: 是否允许间隙存在
        max_gap: 最大允许的间隙大小（秒）
        
    Returns:
        修复后的片段列表
    """
    # 检查是否需要修复间隙
    if allow_gaps:
        return segments
    
    # 复制列表以避免修改原始数据
    fixed_segments = [seg.copy() for seg in segments]
    
    # 按开始时间排序
    fixed_segments.sort(key=lambda x: x.get('start', 0))
    
    # 检查并修复间隙
    for i in range(len(fixed_segments) - 1):
        curr_seg = fixed_segments[i]
        next_seg = fixed_segments[i + 1]
        
        if 'end' in curr_seg and 'start' in next_seg:
            # 计算间隙大小
            gap = next_seg['start'] - curr_seg['end']
            
            # 如果存在间隙并且大于允许的最大值
            if gap > 0 and gap > max_gap:
                logger.warning(f"修复时间线间隙: {curr_seg['id'] if 'id' in curr_seg else ''} 和 {next_seg['id'] if 'id' in next_seg else ''} 之间有 {gap} 秒间隙")
                
                # 扩展当前片段结束时间以填补间隙
                curr_seg['end'] = next_seg['start']
                
                # 更新持续时间
                if 'duration' in curr_seg:
                    curr_seg['duration'] = curr_seg['end'] - curr_seg.get('start', 0)
    
    return fixed_segments


def fix_corrupt_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """修复损坏的数据结构
    
    Args:
        data: 数据字典
        
    Returns:
        修复后的数据
    """
    fixed_data = {}
    
    try:
        # 尝试深度复制数据
        import copy
        fixed_data = copy.deepcopy(data)
    except:
        # 如果深度复制失败，则可能是数据结构损坏
        logger.warning("数据结构可能已损坏，尝试基本复制")
        
        # 尝试基本复制
        for key, value in data.items():
            try:
                # 尝试转换为JSON然后再转回来，以清理无效的对象
                json_value = json.dumps(value)
                fixed_data[key] = json.loads(json_value)
            except:
                logger.warning(f"跳过损坏的键: {key}")
                continue
    
    return fixed_data


def fix_invalid_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """修复无效值（NaN, Infinite等）
    
    Args:
        data: 数据字典
        
    Returns:
        修复后的数据
    """
    fixed_data = {}
    
    for key, value in data.items():
        if isinstance(value, dict):
            # 递归处理嵌套字典
            fixed_data[key] = fix_invalid_values(value)
        elif isinstance(value, list):
            # 处理列表
            fixed_data[key] = []
            for item in value:
                if isinstance(item, dict):
                    fixed_data[key].append(fix_invalid_values(item))
                else:
                    # 处理特殊值
                    fixed_value = _fix_special_value(item)
                    fixed_data[key].append(fixed_value)
        else:
            # 处理特殊值
            fixed_data[key] = _fix_special_value(value)
    
    return fixed_data


def _fix_special_value(value: Any) -> Any:
    """修复特殊值
    
    Args:
        value: 要检查的值
        
    Returns:
        修复后的值
    """
    # 处理float特殊值
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return 0.0
        elif math.isinf(value) and value > 0:
            return float(1e9)  # 使用一个大但有限的值
        elif math.isinf(value) and value < 0:
            return float(-1e9)  # 使用一个小但有限的值
    
    # 处理None值
    if value is None:
        return ""
    
    return value


class ErrorFixer:
    """错误修复器类"""
    
    def __init__(self):
        """初始化错误修复器"""
        self.logger = logger
        self.fix_count = 0
        self.warning_count = 0
        self.error_count = 0
    
    def fix_timeline(self, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """修复时间线数据
        
        Args:
            timeline_data: 时间线数据
            
        Returns:
            修复后的时间线数据
        """
        # 重置计数器
        self.fix_count = 0
        self.warning_count = 0
        self.error_count = 0
        
        try:
            # 检查数据是否为空
            if not timeline_data:
                self.warning_count += 1
                return {}
            
            # 修复可能的损坏数据
            fixed_data = fix_corrupt_data(timeline_data)
            
            # 修复无效值
            fixed_data = fix_invalid_values(fixed_data)
            
            # 如果有clips键，修复片段
            if 'clips' in fixed_data and isinstance(fixed_data['clips'], list):
                # 提取有效资源列表（如果有）
                valid_assets = []
                if 'assets' in fixed_data and isinstance(fixed_data['assets'], list):
                    valid_assets = [asset.get('id') for asset in fixed_data['assets'] if 'id' in asset]
                
                # 修复每个片段
                fixed_clips = []
                for clip in fixed_data['clips']:
                    fixed_clip = self._fix_segment(clip, valid_assets)
                    fixed_clips.append(fixed_clip)
                
                # 修复片段间关系
                fixed_clips = fix_overlapping_segments(fixed_clips)
                fixed_clips = fix_timeline_gaps(fixed_clips)
                
                fixed_data['clips'] = fixed_clips
            
            # 如果有tracks键，修复轨道中的项目
            if 'tracks' in fixed_data and isinstance(fixed_data['tracks'], list):
                for track_idx, track in enumerate(fixed_data['tracks']):
                    if 'items' in track and isinstance(track['items'], list):
                        # 修复每个轨道项
                        fixed_items = []
                        for item in track['items']:
                            fixed_item = self._fix_segment(item)
                            fixed_items.append(fixed_item)
                        
                        # 修复项目间关系
                        fixed_items = fix_overlapping_segments(fixed_items)
                        
                        fixed_data['tracks'][track_idx]['items'] = fixed_items
            
            # 返回修复后的数据
            if self.fix_count > 0:
                self.logger.info(f"已修复 {self.fix_count} 个问题")
            
            return fixed_data
        
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"修复时间线数据时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            return timeline_data  # 返回原始数据
    
    def _fix_segment(self, segment: Dict[str, Any], valid_assets: List[str] = None) -> Dict[str, Any]:
        """修复单个片段
        
        Args:
            segment: 片段数据
            valid_assets: 有效资源ID列表
            
        Returns:
            修复后的片段
        """
        # 应用所有修复函数
        fixed = segment
        orig_fixed = json.dumps(fixed)  # 保存原始状态
        
        # 应用修复
        fixed = fix_invalid_segment(fixed)
        fixed = fix_negative_duration(fixed)
        fixed = fix_metadata_consistency(fixed)
        fixed = fix_empty_content(fixed)
        
        if valid_assets:
            fixed = fix_invalid_references(fixed, valid_assets)
        
        # 检查是否有修复
        if json.dumps(fixed) != orig_fixed:
            self.fix_count += 1
        
        return fixed
    
    def get_stats(self) -> Dict[str, int]:
        """获取修复统计信息
        
        Returns:
            包含统计信息的字典
        """
        return {
            "fixed": self.fix_count,
            "warnings": self.warning_count,
            "errors": self.error_count,
            "total_fixes": self.fix_count  # 添加total_fixes字段用于测试
        }


# 创建全局实例
_error_fixer = None

def get_error_fixer() -> ErrorFixer:
    """获取错误修复器实例
    
    Returns:
        ErrorFixer: 错误修复器实例
    """
    global _error_fixer
    if _error_fixer is None:
        _error_fixer = ErrorFixer()
    return _error_fixer


def fix_errors(data: Dict[str, Any]) -> Dict[str, Any]:
    """修复数据中的错误（便捷函数）
    
    Args:
        data: 包含可能错误的数据
        
    Returns:
        修复后的数据
    """
    fixer = get_error_fixer()
    return fixer.fix_timeline(data)


if __name__ == "__main__":
    # 简单测试
    test_timeline = {
        "clips": [
            {"id": "clip1", "start": 5.0, "end": 2.0, "content": "测试片段1"},
            {"id": "clip2", "start": 7.0, "end": 10.0, "duration": 5.0},
            {"id": "clip3", "start": 12.0, "end": 15.0, "content": ""},
            {"id": "clip4", "start": 15.0, "end": 20.0, "asset_id": "invalid_asset"}
        ],
        "assets": [
            {"id": "asset1", "path": "/path/to/asset1"},
            {"id": "asset2", "path": "/path/to/asset2"}
        ]
    }
    
    # 修复错误
    fixed_timeline = fix_errors(test_timeline)
    
    # 打印结果
    print("原始时间线:")
    print(json.dumps(test_timeline, indent=2))
    
    print("\n修复后的时间线:")
    print(json.dumps(fixed_timeline, indent=2))
    
    fixer = get_error_fixer()
    print(f"\n统计信息: {fixer.get_stats()}") 