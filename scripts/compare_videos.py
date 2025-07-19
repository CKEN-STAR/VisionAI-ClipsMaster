#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频相似度对比工具

此脚本用于比较两个视频的内容相似度，基于视频指纹提取引擎。
可用于检测重复视频、确认不同编码的相同内容视频，以及查找相似内容。
"""

import os
import sys
import argparse
import time
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

# 添加项目根目录到系统路径
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# 导入视频指纹模块
try:
    from tests.golden_samples.video_fingerprint import VideoFingerprint, compare_videos
except ImportError:
    print("错误: 无法导入视频指纹模块，请确保项目结构正确")
    sys.exit(1)

def format_time(seconds: float) -> str:
    """将秒数格式化为时分秒格式"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"

def print_result(similarity: float, video1: str, video2: str, elapsed_time: float):
    """打印对比结果"""
    print("\n" + "="*70)
    print(f"视频相似度比较结果:")
    print("="*70)
    print(f"视频1: {os.path.basename(video1)}")
    print(f"视频2: {os.path.basename(video2)}")
    print(f"处理时间: {format_time(elapsed_time)}")
    print("-"*70)
    print(f"相似度得分: {similarity:.4f} ({similarity*100:.1f}%)")
    
    # 相似度解释
    if similarity > 0.99:
        print("判定: 相同视频的不同版本 ✓")
        print("说明: 这两个视频极有可能是相同内容的不同编码或分辨率版本")
    elif similarity > 0.95:
        print("判定: 极高相似度 ✓")
        print("说明: 这两个视频内容极为相似，可能有轻微剪辑或调整")
    elif similarity > 0.85:
        print("判定: 高度相似 !")
        print("说明: 这两个视频内容高度相似，但可能有明显不同部分")
    elif similarity > 0.70:
        print("判定: 部分相似 !")
        print("说明: 这两个视频有相似内容，但也有明显不同")
    else:
        print("判定: 不同视频 ✗")
        print("说明: 这两个视频内容差异显著")
    
    print("="*70 + "\n")

def batch_compare(target_video: str, video_dir: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
    """批量比较目标视频与目录中所有视频的相似度"""
    fingerprinter = VideoFingerprint()
    
    # 获取目录中所有视频文件
    video_files = []
    for ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']:
        video_files.extend(Path(video_dir).glob(f"**/*{ext}"))
    
    if not video_files:
        print(f"错误: 目录 '{video_dir}' 中未找到视频文件")
        return []
    
    # 提取目标视频指纹
    print(f"提取目标视频指纹: {target_video}")
    try:
        target_sig = fingerprinter.extract_signature(target_video)
    except Exception as e:
        print(f"错误: 无法提取目标视频指纹: {str(e)}")
        return []
    
    # 比较所有视频
    results = []
    total = len(video_files)
    for i, video_path in enumerate(video_files, 1):
        video_path_str = str(video_path)
        
        # 跳过自身比对
        if os.path.abspath(video_path_str) == os.path.abspath(target_video):
            continue
        
        print(f"比较 [{i}/{total}]: {video_path.name}")
        
        try:
            # 提取并比对
            sig = fingerprinter.extract_signature(video_path_str)
            similarity = fingerprinter.compare_signatures(target_sig, sig)
            
            # 如果相似度高于阈值，加入结果
            if similarity >= threshold:
                results.append((video_path_str, similarity))
        except Exception as e:
            print(f"  处理视频 {video_path.name} 时出错: {str(e)}")
    
    # 按相似度降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视频相似度比较工具")
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 比较两个视频的命令
    compare_parser = subparsers.add_parser('compare', help='比较两个视频的相似度')
    compare_parser.add_argument('video1', help='第一个视频文件路径')
    compare_parser.add_argument('video2', help='第二个视频文件路径')
    
    # 批量比较的命令
    batch_parser = subparsers.add_parser('batch', help='批量比较视频相似度')
    batch_parser.add_argument('target', help='目标视频文件路径')
    batch_parser.add_argument('directory', help='要比较的视频目录')
    batch_parser.add_argument('--threshold', '-t', type=float, default=0.7,
                             help='相似度阈值 (0-1 之间，默认 0.7)')
    batch_parser.add_argument('--limit', '-l', type=int, default=10,
                             help='显示结果的最大数量 (默认 10)')
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return
    
    # 比较两个视频
    if args.command == 'compare':
        video1 = args.video1
        video2 = args.video2
        
        # 检查文件是否存在
        if not os.path.exists(video1):
            print(f"错误: 视频文件不存在: {video1}")
            return
        if not os.path.exists(video2):
            print(f"错误: 视频文件不存在: {video2}")
            return
        
        print(f"正在比较视频相似度:")
        print(f"视频1: {video1}")
        print(f"视频2: {video2}")
        
        # 执行比较
        start_time = time.time()
        try:
            similarity = compare_videos(video1, video2)
            elapsed_time = time.time() - start_time
            
            # 打印结果
            print_result(similarity, video1, video2, elapsed_time)
        except Exception as e:
            print(f"错误: 比较过程中出错: {str(e)}")
    
    # 批量比较视频
    elif args.command == 'batch':
        target = args.target
        directory = args.directory
        threshold = args.threshold
        limit = args.limit
        
        # 检查文件和目录是否存在
        if not os.path.exists(target):
            print(f"错误: 目标视频文件不存在: {target}")
            return
        if not os.path.exists(directory) or not os.path.isdir(directory):
            print(f"错误: 视频目录不存在: {directory}")
            return
        
        print(f"正在批量比较视频相似度:")
        print(f"目标视频: {target}")
        print(f"视频目录: {directory}")
        print(f"相似度阈值: {threshold}")
        
        # 执行批量比较
        start_time = time.time()
        try:
            results = batch_compare(target, directory, threshold)
            elapsed_time = time.time() - start_time
            
            # 打印结果
            print("\n" + "="*70)
            print(f"批量视频相似度比较结果:")
            print("="*70)
            print(f"目标视频: {os.path.basename(target)}")
            print(f"处理时间: {format_time(elapsed_time)}")
            print(f"找到 {len(results)} 个相似视频 (相似度 >= {threshold})")
            print("-"*70)
            
            for i, (video_path, similarity) in enumerate(results[:limit], 1):
                print(f"{i}. 相似度: {similarity:.4f} ({similarity*100:.1f}%): {os.path.basename(video_path)}")
            
            # 如果结果被截断
            if len(results) > limit:
                print(f"...(还有 {len(results) - limit} 个结果未显示)")
            
            print("="*70 + "\n")
        except Exception as e:
            print(f"错误: 批量比较过程中出错: {str(e)}")

if __name__ == "__main__":
    main() 