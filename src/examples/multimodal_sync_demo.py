#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多模态对齐模块演示脚本
展示如何使用视频-文本对齐功能
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

# 导入多模态对齐模块
from src.alignment.multimodal_sync import AudioVisualAligner
from src.alignment.keyframe_extractor import extract_keyframes
from src.alignment.scene_analyzer import analyze_video_scenes
from src.core.srt_parser import parse_subtitle

# 设置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("multimodal_sync_demo")


def demonstrate_keyframe_extraction(video_path: str, output_dir: Optional[str] = None) -> None:
    """
    演示关键帧提取功能
    
    参数:
        video_path: 视频文件路径
        output_dir: 可选的输出目录
    """
    print("\n===== 关键帧提取演示 =====")
    
    # 使用均匀提取方法
    print("\n1. 均匀提取关键帧:")
    keyframes_uniform = extract_keyframes(
        video_path=video_path,
        method='uniform',
        num_frames=10,
        save_frames=True,
        output_dir=output_dir
    )
    
    print(f"  提取了 {len(keyframes_uniform)} 个关键帧")
    for i, kf in enumerate(keyframes_uniform[:3]):  # 只显示前3个
        print(f"  帧 {i+1}: 时间戳 {kf['timestamp']:.2f}秒")
        if 'file_path' in kf:
            print(f"    保存路径: {kf['file_path']}")
    
    if len(keyframes_uniform) > 3:
        print(f"  ... 更多关键帧省略 ...")
    
    # 使用差异提取方法
    print("\n2. 基于差异提取关键帧:")
    keyframes_diff = extract_keyframes(
        video_path=video_path,
        method='difference',
        threshold=25.0,
        save_frames=True,
        output_dir=output_dir
    )
    
    print(f"  提取了 {len(keyframes_diff)} 个关键帧")
    for i, kf in enumerate(keyframes_diff[:3]):  # 只显示前3个
        print(f"  帧 {i+1}: 时间戳 {kf['timestamp']:.2f}秒, 差异分数: {kf.get('diff_score', 0):.2f}")
        if 'file_path' in kf:
            print(f"    保存路径: {kf['file_path']}")
    
    if len(keyframes_diff) > 3:
        print(f"  ... 更多关键帧省略 ...")
    
    # 使用场景提取方法
    print("\n3. 基于场景变化提取关键帧:")
    keyframes_scene = extract_keyframes(
        video_path=video_path,
        method='scene',
        threshold=30.0,
        save_frames=True,
        output_dir=output_dir
    )
    
    print(f"  提取了 {len(keyframes_scene)} 个关键帧")
    for i, kf in enumerate(keyframes_scene[:3]):  # 只显示前3个
        print(f"  帧 {i+1}: 时间戳 {kf['timestamp']:.2f}秒, 运动分数: {kf.get('motion_score', 0):.2f}")
        if 'file_path' in kf:
            print(f"    保存路径: {kf['file_path']}")
    
    if len(keyframes_scene) > 3:
        print(f"  ... 更多关键帧省略 ...")


def demonstrate_scene_analysis(video_path: str, subtitle_path: Optional[str] = None) -> None:
    """
    演示场景分析功能
    
    参数:
        video_path: 视频文件路径
        subtitle_path: 可选的字幕文件路径
    """
    print("\n===== 场景分析演示 =====")
    
    # 如果提供了字幕，解析字幕
    subtitle_data = None
    if subtitle_path and os.path.exists(subtitle_path):
        try:
            subtitle_data = parse_subtitle(subtitle_path)
            print(f"已加载 {len(subtitle_data)} 条字幕")
        except Exception as e:
            print(f"字幕解析错误: {str(e)}")
    
    # 分析视频场景
    start_time = time.time()
    print("正在分析视频场景...")
    scenes = analyze_video_scenes(video_path, subtitle_data)
    elapsed = time.time() - start_time
    
    print(f"场景分析完成，耗时: {elapsed:.2f}秒")
    print(f"识别出 {len(scenes)} 个场景:")
    
    # 显示场景信息
    for i, scene in enumerate(scenes[:3]):  # 只显示前3个场景
        print(f"\n场景 {i+1}: {scene.start_time:.2f}s - {scene.end_time:.2f}s (持续: {scene.end_time - scene.start_time:.2f}s)")
        print(f"  类型: {scene.scene_type or '未知'}, 位置: {scene.location or '未知'}")
        if scene.text:
            text_preview = scene.text[:100] + ('...' if len(scene.text) > 100 else '')
            print(f"  文本: {text_preview}")
        print(f"  关键帧数: {len(scene.keyframes)}")
        if scene.metadata:
            print(f"  亮度: {scene.metadata.get('brightness', 'N/A'):.2f}")
    
    if len(scenes) > 3:
        print(f"\n... 更多场景省略 ...")
    
    # 分析场景过渡
    if len(scenes) > 1:
        print("\n场景过渡分析:")
        from src.alignment.scene_analyzer import SceneAnalyzer
        analyzer = SceneAnalyzer()
        transitions = analyzer.analyze_scene_transitions(scenes)
        
        print(f"  总场景数: {transitions['total_scenes']}")
        print(f"  平均场景持续时间: {transitions['avg_scene_duration']:.2f}秒")
        print(f"  场景类型分布: {transitions['scene_types']}")
        
        if transitions['transitions']:
            print("\n  场景切换样例:")
            for i, trans in enumerate(transitions['transitions'][:2]):  # 只显示前2个过渡
                print(f"    过渡 {i+1}: 场景{trans['from_scene_idx']}({trans['from_type'] or '未知'}) -> 场景{trans['to_scene_idx']}({trans['to_type'] or '未知'})")
                print(f"      过渡时间: {trans['transition_time']:.2f}秒")
                print(f"      是否为硬切换: {'是' if trans['is_cut'] else '否'}")


def demonstrate_content_alignment(video_path: str, subtitle_path: str, output_path: Optional[str] = None) -> None:
    """
    演示内容对齐功能
    
    参数:
        video_path: 视频文件路径
        subtitle_path: 字幕文件路径
        output_path: 可选的输出文件路径
    """
    print("\n===== 内容对齐演示 =====")
    
    # 解析字幕
    try:
        subtitle_data = parse_subtitle(subtitle_path)
        print(f"已加载 {len(subtitle_data)} 条字幕")
    except Exception as e:
        print(f"字幕解析错误: {str(e)}")
        return
    
    # 创建对齐器
    aligner = AudioVisualAligner(
        time_tolerance=1.0,
        visual_context_extraction=True
    )
    
    # 执行对齐
    print("正在进行对齐...")
    start_time = time.time()
    alignments = aligner.align_with_video(subtitle_data, video_path)
    elapsed = time.time() - start_time
    
    print(f"对齐完成，耗时: {elapsed:.2f}秒")
    
    # 生成报告
    report = aligner.get_alignment_report(alignments)
    
    print(f"\n对齐报告:")
    print(f"  总对齐数: {report['total_alignments']}")
    print(f"  平均置信度: {report['average_confidence']:.2f}")
    print(f"  警告数量: {report['warnings_count']} ({report['warnings_percentage']:.1f}%)")
    print(f"  场景覆盖率: {report['scene_coverage']:.1f}%")
    
    # 打印示例对齐结果
    print("\n对齐结果样例:")
    for i, alignment in enumerate(alignments[:3]):  # 只显示前3个对齐
        print(f"\n  对齐项 {i+1}: 时间 {alignment.start_time:.2f}s - {alignment.end_time:.2f}s")
        print(f"    文本: {alignment.text}")
        print(f"    视觉上下文: {alignment.visual_context or '无'}")
        print(f"    置信度: {alignment.confidence:.2f}")
        if alignment.warnings:
            print(f"    警告: {', '.join(alignment.warnings)}")
    
    if len(alignments) > 3:
        print(f"\n... 更多对齐结果省略 ...")
    
    # 增强字幕数据
    enhanced_data = aligner.enhance_subtitle_data(subtitle_data, alignments)
    
    # 保存结果
    if output_path is None:
        output_path = os.path.splitext(subtitle_path)[0] + "_enhanced.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n增强后的字幕数据已保存到: {output_path}")
    
    # 显示如何使用增强数据
    print("\n如何使用增强后的字幕数据:")
    print("  1. 导入增强数据:")
    print("     with open('enhanced_subtitles.json', 'r') as f:")
    print("         enhanced_subs = json.load(f)")
    print("\n  2. 使用增强字幕的上下文信息:")
    print("     for sub in enhanced_subs:")
    print("         print(f\"时间: {sub['start_time']}-{sub['end_time']}\")")
    print("         print(f\"文本: {sub['text']}\")")
    print("         print(f\"视觉上下文: {sub.get('visual_context', '无')}\")")
    print("         print(f\"场景类型: {sub.get('scene_type', '未知')}\")")
    print("         print(f\"位置: {sub.get('location', '未知')}\")")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多模态对齐演示")
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument("--subtitle", "-s", help="字幕文件路径")
    parser.add_argument("--output", "-o", help="输出目录或文件路径")
    parser.add_argument("--demo", "-d", choices=["all", "keyframes", "scenes", "alignment"], 
                      default="all", help="演示类型")
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.video_path):
        print(f"错误: 视频文件不存在: {args.video_path}")
        return 1
    
    if args.subtitle and not os.path.exists(args.subtitle):
        print(f"错误: 字幕文件不存在: {args.subtitle}")
        return 1
    
    # 根据演示类型执行不同的功能
    if args.demo in ["all", "keyframes"]:
        demonstrate_keyframe_extraction(args.video_path, args.output)
    
    if args.demo in ["all", "scenes"]:
        demonstrate_scene_analysis(args.video_path, args.subtitle)
    
    if args.demo in ["all", "alignment"]:
        if args.subtitle:
            demonstrate_content_alignment(args.video_path, args.subtitle, args.output)
        else:
            print("错误: 内容对齐演示需要提供字幕文件")
            if args.demo == "alignment":
                return 1
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n演示被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 