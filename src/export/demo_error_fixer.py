#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 错误修复模块演示

此脚本展示如何使用错误修复模块来检测和修复导出内容中的各种错误。
包括示例数据和各种修复功能的应用。
"""

import os
import sys
import json
import math
from pprint import pprint

# 确保可以导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.export.error_fixer import (
    fix_invalid_segment,
    fix_negative_duration,
    fix_metadata_consistency,
    fix_empty_content,
    fix_invalid_references,
    fix_overlapping_segments,
    fix_timeline_gaps,
    fix_corrupt_data,
    fix_invalid_values,
    ErrorFixer,
    get_error_fixer,
    fix_errors
)
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("demo_error_fixer")


def demo_individual_fixes():
    """演示单独的修复功能"""
    print("\n=== 演示单独的修复功能 ===\n")
    
    # 示例1: 修复无效片段（开始>结束）
    invalid_segment = {'id': 'invalid1', 'start': 5.0, 'end': 3.0, 'title': '无效片段'}
    fixed_segment = fix_invalid_segment(invalid_segment)
    print("1. 修复无效片段（开始>结束）:")
    print("   修复前:", invalid_segment)
    print("   修复后:", fixed_segment)
    
    # 示例2: 修复负持续时间
    negative_duration = {'id': 'negative1', 'start': 1.0, 'end': 3.0, 'duration': -2.0, 'title': '负持续时间'}
    fixed_duration = fix_negative_duration(negative_duration)
    print("\n2. 修复负持续时间:")
    print("   修复前:", negative_duration)
    print("   修复后:", fixed_duration)
    
    # 示例3: 修复元数据不一致
    inconsistent = {'id': 'inconsistent1', 'start': 1.0, 'end': 4.0, 'duration': 2.0, 'title': '元数据不一致'}
    fixed_metadata = fix_metadata_consistency(inconsistent)
    print("\n3. 修复元数据不一致:")
    print("   修复前:", inconsistent)
    print("   修复后:", fixed_metadata)
    
    # 示例4: 修复空内容
    empty_content = {'id': 'empty1', 'start': 1.0, 'end': 3.0, 'content': '', 'title': ''}
    fixed_content = fix_empty_content(empty_content)
    print("\n4. 修复空内容:")
    print("   修复前:", empty_content)
    print("   修复后:", fixed_content)
    
    # 示例5: 修复无效引用
    invalid_ref = {'id': 'ref1', 'start': 1.0, 'end': 3.0, 'asset_id': 'non_existent', 'title': '无效引用'}
    valid_assets = ['asset1', 'asset2']
    fixed_ref = fix_invalid_references(invalid_ref, valid_assets)
    print("\n5. 修复无效引用:")
    print("   有效资源:", valid_assets)
    print("   修复前:", invalid_ref)
    print("   修复后:", fixed_ref)


def demo_timeline_fixes():
    """演示时间线修复功能"""
    print("\n=== 演示时间线修复功能 ===\n")
    
    # 示例1: 修复重叠片段
    overlapping = [
        {'id': 'clip1', 'start': 1.0, 'end': 4.0, 'title': '片段1'},
        {'id': 'clip2', 'start': 3.0, 'end': 6.0, 'title': '片段2'},
        {'id': 'clip3', 'start': 5.0, 'end': 8.0, 'title': '片段3'}
    ]
    fixed_overlapping = fix_overlapping_segments(overlapping)
    print("1. 修复重叠片段:")
    print("   修复前:")
    for clip in overlapping:
        print(f"   - {clip['id']}: {clip['start']} -> {clip['end']}")
    print("   修复后:")
    for clip in fixed_overlapping:
        print(f"   - {clip['id']}: {clip['start']} -> {clip['end']}")
    
    # 示例2: 修复时间线间隙
    gaps = [
        {'id': 'clip1', 'start': 1.0, 'end': 3.0, 'title': '片段1'},
        {'id': 'clip2', 'start': 4.0, 'end': 6.0, 'title': '片段2'},
        {'id': 'clip3', 'start': 8.0, 'end': 10.0, 'title': '片段3'}
    ]
    fixed_gaps = fix_timeline_gaps(gaps, allow_gaps=False)
    print("\n2. 修复时间线间隙:")
    print("   修复前:")
    for clip in gaps:
        print(f"   - {clip['id']}: {clip['start']} -> {clip['end']}")
    print("   修复后:")
    for clip in fixed_gaps:
        print(f"   - {clip['id']}: {clip['start']} -> {clip['end']}")
    
    # 示例3: 修复无效值
    invalid_values = {
        'fps': float('inf'),
        'duration': float('nan'),
        'clips': [
            {'id': 'clip1', 'start': float('nan'), 'end': 3.0, 'title': '无效值片段'}
        ]
    }
    fixed_values = fix_invalid_values(invalid_values)
    print("\n3. 修复无效值 (NaN, Infinity):")
    print("   修复前:", invalid_values)
    print("   修复后:", fixed_values)


def demo_error_fixer_class():
    """演示ErrorFixer类的使用"""
    print("\n=== 演示ErrorFixer类 ===\n")
    
    # 创建包含多种错误的时间轴
    problem_timeline = {
        'fps': float('inf'),
        'duration': -1.0,
        'clips': [
            {'id': 'clip1', 'start': 5.0, 'end': 3.0, 'duration': -2.0, 'content': '', 'title': '问题片段1'},
            {'id': 'clip2', 'start': 3.0, 'end': 6.0, 'title': '问题片段2'},
            {'id': 'clip3', 'start': 5.0, 'end': 8.0, 'title': '问题片段3'}  # 与clip2重叠
        ],
        'assets': [{'id': 'asset1', 'path': '/path/to/asset1.mp4'}]
    }
    
    print("包含错误的时间轴:")
    pprint(problem_timeline)
    
    # 使用ErrorFixer修复
    fixer = ErrorFixer()
    fixed = fixer.fix_timeline(problem_timeline)
    
    print("\n修复后的时间轴:")
    pprint(fixed)
    
    # 获取修复统计
    stats = fixer.get_stats()
    print("\n修复统计:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")


def demo_fix_errors_function():
    """演示fix_errors函数的使用"""
    print("\n=== 演示fix_errors函数 ===\n")
    
    # 创建包含错误的完整时间线数据
    complex_timeline = {
        'fps': float('inf'),
        'duration': -5.0,
        'clips': [
            {'id': 'clip1', 'start': 5.0, 'end': 3.0, 'duration': -2.0, 'content': None, 'title': ''},
            {'id': 'clip2', 'start': 3.0, 'end': 6.0, 'asset_id': 'non_existent'},
            {'id': 'clip3', 'start': 5.0, 'end': 8.0}  # 与clip2重叠
        ],
        'assets': [
            {'id': 'asset1', 'path': '/path/to/asset1.mp4'},
            {'id': 'asset2', 'path': '/path/to/asset2.mp4'}
        ],
        'metadata': {
            'created_at': 'invalid_date',
            'version': 'v1.0'
        }
    }
    
    print("复杂的问题时间轴:")
    pprint(complex_timeline)
    
    # 使用fix_errors函数一键修复所有问题
    fixed = fix_errors(complex_timeline)
    
    print("\n一键修复后的时间轴:")
    pprint(fixed)
    
    # 显示修复前后的主要变化
    print("\n主要修复内容:")
    print(f"1. fps: {complex_timeline['fps']} -> {fixed['fps']}")
    print(f"2. duration: {complex_timeline['duration']} -> {fixed['duration']}")
    print(f"3. 第一个片段开始/结束时间: {complex_timeline['clips'][0]['start']}/{complex_timeline['clips'][0]['end']} -> "
          f"{fixed['clips'][0]['start']}/{fixed['clips'][0]['end']}")
    print("4. 内容空值已修复")
    print("5. 无效资源引用已修复")
    print("6. 片段重叠已修复")


def main():
    """主函数"""
    print("=== VisionAI-ClipsMaster 错误修复模块演示 ===")
    
    # 演示各种修复功能
    demo_individual_fixes()
    demo_timeline_fixes()
    demo_error_fixer_class()
    demo_fix_errors_function()
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main() 