#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时间轴检查器演示脚本

演示时间轴检查器(timeline_checker.py)的主要功能和实际应用场景
"""

import os
import sys
import json
import argparse
from pathlib import Path
import pprint

# 添加项目根目录到系统路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.export.timeline_checker import (
    detect_overlap,
    detect_gaps,
    validate_timeline,
    fix_timeline_conflicts,
    check_frame_rate_compatibility,
    analyze_timeline
)


def demo_overlap_detection():
    """演示片段重叠检测和修复"""
    print("\n===== 1. 片段重叠检测和修复 =====")
    
    # 创建包含重叠的测试片段
    test_segments = [
        {'id': 'clip1', 'name': '开场镜头', 'start': 0, 'end': 10},
        {'id': 'clip2', 'name': '对话场景', 'start': 8, 'end': 15},  # 与前一个重叠
        {'id': 'clip3', 'name': '转场特效', 'start': 14, 'end': 20},  # 与前一个重叠
        {'id': 'clip4', 'name': '结束镜头', 'start': 25, 'end': 35}   # 无重叠
    ]
    
    # 显示原始片段
    print("原始片段序列:")
    for seg in test_segments:
        print(f"  {seg['id']} ({seg['name']}): {seg['start']} - {seg['end']}")
    
    # 检测并修复重叠
    fixed_segments = detect_overlap(test_segments)
    
    # 显示修复后的片段
    print("\n修复重叠后的片段序列:")
    for i, seg in enumerate(fixed_segments):
        # 检查是否修改了开始时间
        if seg['start'] != test_segments[i]['start']:
            print(f"  {seg['id']} ({seg['name']}): {seg['start']} - {seg['end']} "
                  f"(原始开始时间: {test_segments[i]['start']})")
        else:
            print(f"  {seg['id']} ({seg['name']}): {seg['start']} - {seg['end']}")


def demo_gap_detection():
    """演示片段间隙检测"""
    print("\n===== 2. 片段间隙检测 =====")
    
    # 创建包含间隙的测试片段
    test_segments = [
        {'id': 'clip1', 'name': '标题镜头', 'start': 0, 'end': 5},
        {'id': 'clip2', 'name': '主角介绍', 'start': 10, 'end': 20},  # 5秒间隙
        {'id': 'clip3', 'name': '情节发展', 'start': 25, 'end': 40},  # 5秒间隙
        {'id': 'clip4', 'name': '结局镜头', 'start': 45, 'end': 55}   # 5秒间隙
    ]
    
    # 显示片段
    print("片段序列:")
    for seg in test_segments:
        print(f"  {seg['id']} ({seg['name']}): {seg['start']} - {seg['end']}")
    
    # 检测所有间隙
    gaps = detect_gaps(test_segments)
    
    # 显示检测到的间隙
    print("\n检测到的所有间隙:")
    for i, gap in enumerate(gaps):
        print(f"  间隙 {i+1}: {gap['start']} - {gap['end']} (持续: {gap['duration']}秒)")
        print(f"    位于 {gap['prev_segment_id']} 和 {gap['next_segment_id']} 之间")
    
    # 使用最大允许间隙参数
    max_gap = 4
    filtered_gaps = detect_gaps(test_segments, max_gap=max_gap)
    
    print(f"\n超过 {max_gap} 秒的间隙:")
    for i, gap in enumerate(filtered_gaps):
        print(f"  间隙 {i+1}: {gap['start']} - {gap['end']} (持续: {gap['duration']}秒)")
        print(f"    位于 {gap['prev_segment_id']} 和 {gap['next_segment_id']} 之间")


def demo_timeline_validation():
    """演示时间轴验证"""
    print("\n===== 3. 时间轴验证 =====")
    
    # 创建有效的时间轴
    valid_timeline = {
        'name': '示例项目',
        'fps': 30.0,
        'clips': [
            {'id': 'clip1', 'start_frame': 0, 'end_frame': 30, 'name': '开场白'},
            {'id': 'clip2', 'start_frame': 30, 'end_frame': 60, 'name': '主要内容'}
        ],
        'tracks': [
            {
                'id': 'video_track',
                'name': '视频轨道',
                'frame_rate': 30.0,
                'items': [
                    {'id': 'item1', 'clip_id': 'clip1', 'start_frame': 0, 'end_frame': 30},
                    {'id': 'item2', 'clip_id': 'clip2', 'start_frame': 30, 'end_frame': 60}
                ]
            }
        ]
    }
    
    # 验证有效时间轴
    valid, issues = validate_timeline(valid_timeline)
    print("有效时间轴验证结果:")
    print(f"  有效: {valid}")
    if issues:
        print("  问题:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  没有发现问题")
    
    # 创建包含问题的时间轴
    invalid_timeline = {
        'name': '问题项目',
        'fps': 30.0,
        'clips': [
            {'id': 'clip1', 'start_frame': 0, 'end_frame': 30, 'name': '开场白'},
            {'id': 'clip2', 'start_frame': 20, 'end_frame': 10, 'name': '无效片段'},  # 结束时间小于开始时间
            {'id': 'clip3', 'start_frame': 40, 'end_frame': 60, 'name': '结束部分'}
        ],
        'tracks': [
            {
                'id': 'video_track',
                'name': '视频轨道',
                'frame_rate': 24.0,  # 与全局帧率不匹配
                'items': [
                    {'id': 'item1', 'clip_id': 'clip1', 'start_frame': 0, 'end_frame': 30},
                    {'id': 'item2', 'clip_id': 'clip2', 'start_frame': 20, 'end_frame': 35},  # 重叠
                    {'id': 'item3', 'clip_id': 'clip3', 'start_frame': 40, 'end_frame': 60}
                ]
            }
        ]
    }
    
    # 验证无效时间轴
    valid, issues = validate_timeline(invalid_timeline)
    print("\n无效时间轴验证结果:")
    print(f"  有效: {valid}")
    if issues:
        print("  问题:")
        for issue in issues:
            print(f"    - {issue}")


def demo_fix_timeline_conflicts():
    """演示修复时间轴冲突"""
    print("\n===== 4. 修复时间轴冲突 =====")
    
    # 创建包含冲突的时间轴
    timeline_with_conflicts = {
        'name': '冲突项目',
        'fps': 30.0,
        'clips': [
            {'id': 'clip1', 'start_frame': 0, 'end_frame': 30, 'name': '片段1'},
            {'id': 'clip2', 'start_frame': 20, 'end_frame': 50, 'name': '片段2'},  # 与前一个重叠
            {'id': 'clip3', 'start_frame': 45, 'end_frame': 75, 'name': '片段3'}   # 与前一个重叠
        ],
        'tracks': [
            {
                'id': 'video_track',
                'name': '视频轨道',
                'frame_rate': 30.0,
                'items': [
                    {'id': 'item1', 'clip_id': 'clip1', 'start_frame': 0, 'end_frame': 30},
                    {'id': 'item2', 'clip_id': 'clip2', 'start_frame': 25, 'end_frame': 55},  # 与前一个重叠
                    {'id': 'item3', 'clip_id': 'clip3', 'start_frame': 50, 'end_frame': 80}   # 与前一个重叠
                ]
            }
        ]
    }
    
    # 显示原始片段信息
    print("原始时间轴片段:")
    for clip in timeline_with_conflicts['clips']:
        print(f"  {clip['id']} ({clip['name']}): {clip['start_frame']} - {clip['end_frame']}")
    
    print("\n原始轨道项目:")
    for item in timeline_with_conflicts['tracks'][0]['items']:
        print(f"  {item['id']} (clip: {item['clip_id']}): {item['start_frame']} - {item['end_frame']}")
    
    # 修复冲突
    fixed_timeline = fix_timeline_conflicts(timeline_with_conflicts)
    
    # 显示修复后的片段信息
    print("\n修复后的时间轴片段:")
    for i, clip in enumerate(fixed_timeline['clips']):
        original = timeline_with_conflicts['clips'][i]
        if clip['start_frame'] != original['start_frame']:
            print(f"  {clip['id']} ({clip['name']}): {clip['start_frame']} - {clip['end_frame']} "
                  f"(原始开始: {original['start_frame']})")
        else:
            print(f"  {clip['id']} ({clip['name']}): {clip['start_frame']} - {clip['end_frame']}")
    
    print("\n修复后的轨道项目:")
    for i, item in enumerate(fixed_timeline['tracks'][0]['items']):
        original = timeline_with_conflicts['tracks'][0]['items'][i]
        if item['start_frame'] != original['start_frame']:
            print(f"  {item['id']} (clip: {item['clip_id']}): {item['start_frame']} - {item['end_frame']} "
                  f"(原始开始: {original['start_frame']})")
        else:
            print(f"  {item['id']} (clip: {item['clip_id']}): {item['start_frame']} - {item['end_frame']}")


def demo_framerate_compatibility():
    """演示帧率兼容性检查"""
    print("\n===== 5. 帧率兼容性检查 =====")
    
    # 创建帧率不一致的时间轴
    timeline = {
        'name': '混合帧率项目',
        'fps': 30.0,
        'clips': [
            {'id': 'clip1', 'start_frame': 0, 'end_frame': 30, 'name': '30fps片段'},
            {'id': 'clip2', 'start_frame': 30, 'end_frame': 60, 'name': '24fps片段', 'fps': 24.0},
            {'id': 'clip3', 'start_frame': 60, 'end_frame': 90, 'name': '25fps片段', 'fps': 25.0}
        ],
        'tracks': [
            {
                'id': 'video_track1',
                'name': '30fps轨道',
                'frame_rate': 30.0,
                'items': [
                    {'id': 'item1', 'clip_id': 'clip1', 'start_frame': 0, 'end_frame': 30}
                ]
            },
            {
                'id': 'video_track2',
                'name': '24fps轨道',
                'frame_rate': 24.0,  # 与全局帧率不匹配
                'items': [
                    {'id': 'item2', 'clip_id': 'clip2', 'start_frame': 30, 'end_frame': 60}
                ]
            }
        ]
    }
    
    # 检查帧率兼容性
    compatible, issues = check_frame_rate_compatibility(timeline)
    
    print("帧率兼容性检查结果:")
    print(f"  兼容: {compatible}")
    if issues:
        print("  问题:")
        for issue in issues:
            print(f"    - {issue}")


def demo_complete_analysis():
    """演示完整的时间轴分析"""
    print("\n===== 6. 完整时间轴分析 =====")
    
    # 创建综合时间轴（包含多种问题）
    complex_timeline = {
        'name': '综合测试项目',
        'fps': 30.0,
        'clips': [
            {'id': 'clip1', 'start_frame': 0, 'end_frame': 30, 'name': '开场'},
            {'id': 'clip2', 'start_frame': 20, 'end_frame': 50, 'name': '场景1'},  # 重叠
            {'id': 'clip3', 'start_frame': 60, 'end_frame': 90, 'name': '场景2'},  # 间隙
            {'id': 'clip4', 'start_frame': 95, 'end_frame': 90, 'name': '场景3'},  # 无效时间
            {'id': 'clip5', 'start_frame': 120, 'end_frame': 150, 'name': '结尾', 'fps': 24.0}  # 帧率不匹配
        ],
        'tracks': [
            {
                'id': 'video_track1',
                'name': '主视频轨',
                'frame_rate': 25.0,  # 与全局帧率不匹配
                'items': [
                    {'id': 'item1', 'clip_id': 'clip1', 'start_frame': 0, 'end_frame': 30},
                    {'id': 'item2', 'clip_id': 'clip2', 'start_frame': 25, 'end_frame': 55},  # 重叠
                    {'id': 'item3', 'clip_id': 'clip3', 'start_frame': 65, 'end_frame': 95}   # 间隙
                ]
            },
            {
                'id': 'audio_track1',
                'name': '音频轨',
                'frame_rate': 30.0,
                'items': [
                    {'id': 'audio1', 'start_frame': 0, 'end_frame': 40},
                    {'id': 'audio2', 'start_frame': 50, 'end_frame': 100}  # 间隙
                ]
            }
        ]
    }
    
    # 执行完整分析
    report = analyze_timeline(complex_timeline, max_gap=3)
    
    # 显示分析报告摘要
    print("时间轴分析报告摘要:")
    print(f"  有效: {report['valid']}")
    print(f"  帧率兼容: {report['frame_rate_compatible']}")
    print(f"  存在冲突: {report['has_conflicts']}")
    print(f"  轨道数量: {report['statistics']['track_count']}")
    print(f"  片段数量: {report['statistics']['clip_count']}")
    print(f"  总时长: {report['statistics']['total_duration']:.2f}秒")
    
    # 显示检测到的问题
    if report['issues']:
        print("\n检测到的问题:")
        for issue in report['issues']:
            print(f"  - {issue}")
    
    # 显示检测到的间隙
    if report['gaps']:
        print("\n检测到的间隙:")
        for i, gap in enumerate(report['gaps']):
            print(f"  间隙 {i+1}: 轨道 {gap['track_id']}, {gap['start']} - {gap['end']} "
                 f"(持续: {gap['duration']}帧)")
    
    # 修复时间轴
    fixed_timeline = fix_timeline_conflicts(complex_timeline)
    
    # 再次分析
    fixed_report = analyze_timeline(fixed_timeline, max_gap=3)
    
    print("\n修复后的时间轴分析:")
    print(f"  有效: {fixed_report['valid']}")
    print(f"  帧率兼容: {fixed_report['frame_rate_compatible']}")
    print(f"  存在冲突: {fixed_report['has_conflicts']}")
    
    # 显示修复后仍存在的问题
    if fixed_report['issues']:
        print("\n修复后仍存在的问题:")
        for issue in fixed_report['issues']:
            print(f"  - {issue}")


def demo_real_world_scenario():
    """演示真实应用场景"""
    print("\n===== 7. 真实应用场景 =====")
    
    print("场景: 准备导出前的时间轴检查")
    print("  1. 加载项目时间轴数据")
    print("  2. 分析时间轴，检查问题")
    print("  3. 自动修复简单问题")
    print("  4. 向用户报告无法自动修复的问题")
    print("  5. 确认时间轴有效后导出")
    
    # 模拟一个真实项目的时间轴（简化版）
    project_timeline = {
        'name': '混剪项目',
        'fps': 30.0,
        'duration': 180.0,  # 3分钟
        'clips': [
            {'id': 'clip1', 'start_frame': 0, 'end_frame': 150, 'name': '开场镜头'},
            {'id': 'clip2', 'start_frame': 140, 'end_frame': 300, 'name': '人物介绍'},   # 重叠
            {'id': 'clip3', 'start_frame': 320, 'end_frame': 500, 'name': '高潮部分'},   # 间隙
            {'id': 'clip4', 'start_frame': 500, 'end_frame': 600, 'name': '转场'},
            {'id': 'clip5', 'start_frame': 600, 'end_frame': 800, 'name': '结尾'}
        ],
        'tracks': [
            {
                'id': 'video_main',
                'name': '主视频轨',
                'frame_rate': 30.0,
                'items': [
                    {'id': 'v1', 'clip_id': 'clip1', 'start_frame': 0, 'end_frame': 150},
                    {'id': 'v2', 'clip_id': 'clip2', 'start_frame': 140, 'end_frame': 300},   # 重叠
                    {'id': 'v3', 'clip_id': 'clip3', 'start_frame': 320, 'end_frame': 500},   # 间隙
                    {'id': 'v4', 'clip_id': 'clip4', 'start_frame': 500, 'end_frame': 600},
                    {'id': 'v5', 'clip_id': 'clip5', 'start_frame': 600, 'end_frame': 800}
                ]
            },
            {
                'id': 'audio_main',
                'name': '音频轨',
                'frame_rate': 30.0,
                'items': [
                    {'id': 'a1', 'start_frame': 0, 'end_frame': 200},
                    {'id': 'a2', 'start_frame': 200, 'end_frame': 500},
                    {'id': 'a3', 'start_frame': 500, 'end_frame': 800}
                ]
            }
        ]
    }
    
    print("\n第1步: 分析时间轴")
    report = analyze_timeline(project_timeline, max_gap=5)
    
    print(f"  分析结果: {'有效' if report['valid'] else '无效'}")
    print(f"  发现 {len(report['issues'])} 个问题")
    print(f"  发现 {len(report['gaps'])} 个间隙")
    
    if report['issues']:
        print("\n  问题列表:")
        for issue in report['issues']:
            print(f"    - {issue}")
    
    if report['gaps']:
        print("\n  间隙列表:")
        for gap in report['gaps']:
            seconds = gap['duration'] / project_timeline['fps']
            print(f"    - 轨道 {gap['track_id']} 上的 {gap['duration']}帧 ({seconds:.2f}秒) 间隙，"
                  f"在 {gap['prev_segment_id']} 和 {gap['next_segment_id']} 之间")
    
    print("\n第2步: 修复时间轴")
    fixed_timeline = fix_timeline_conflicts(project_timeline)
    
    print("  修复片段重叠:")
    for i, (orig, fixed) in enumerate(zip(project_timeline['clips'], fixed_timeline['clips'])):
        if orig['start_frame'] != fixed['start_frame']:
            print(f"    - {orig['name']}: {orig['start_frame']} → {fixed['start_frame']}")
    
    print("\n第3步: 再次分析修复后的时间轴")
    fixed_report = analyze_timeline(fixed_timeline, max_gap=5)
    
    print(f"  分析结果: {'有效' if fixed_report['valid'] else '无效'}")
    print(f"  剩余问题: {len(fixed_report['issues'])}")
    print(f"  剩余间隙: {len(fixed_report['gaps'])}")
    
    if not fixed_report['issues'] and not fixed_report['gaps']:
        print("\n第4步: 时间轴验证通过，可以安全导出")
    else:
        print("\n第4步: 时间轴仍有问题，需要手动修复")
        if fixed_report['issues']:
            print("  问题列表:")
            for issue in fixed_report['issues']:
                print(f"    - {issue}")
        
        if fixed_report['gaps']:
            print("  间隙列表(可能需要填充):")
            for gap in fixed_report['gaps']:
                seconds = gap['duration'] / fixed_timeline['fps']
                print(f"    - {gap['duration']}帧 ({seconds:.2f}秒) 间隙")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="时间轴检查器演示")
    parser.add_argument("--all", action="store_true", help="运行所有演示")
    parser.add_argument("--overlap", action="store_true", help="演示片段重叠检测和修复")
    parser.add_argument("--gap", action="store_true", help="演示片段间隙检测")
    parser.add_argument("--validate", action="store_true", help="演示时间轴验证")
    parser.add_argument("--fix", action="store_true", help="演示修复时间轴冲突")
    parser.add_argument("--framerate", action="store_true", help="演示帧率兼容性检查")
    parser.add_argument("--analyze", action="store_true", help="演示完整的时间轴分析")
    parser.add_argument("--scenario", action="store_true", help="演示真实应用场景")
    
    args = parser.parse_args()
    
    # 默认运行所有演示
    if not any(vars(args).values()):
        args.all = True
    
    # 打印标题
    print("==================================================")
    print("          时间轴检查器(Timeline Checker)演示")
    print("==================================================")
    
    # 运行所选的演示
    if args.all or args.overlap:
        demo_overlap_detection()
    
    if args.all or args.gap:
        demo_gap_detection()
    
    if args.all or args.validate:
        demo_timeline_validation()
    
    if args.all or args.fix:
        demo_fix_timeline_conflicts()
    
    if args.all or args.framerate:
        demo_framerate_compatibility()
    
    if args.all or args.analyze:
        demo_complete_analysis()
    
    if args.all or args.scenario:
        demo_real_world_scenario()


if __name__ == "__main__":
    main() 