#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频时长分析示例

此示例脚本展示了如何使用VisionAI-ClipsMaster的时长分析模块
来准确计算视频的时长，并对比不同的分析方法。
"""

import os
import sys
import logging
import argparse
from typing import Dict, List, Any

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from src.timecode import BaseAnalyzer, analyze_source_duration
except ImportError:
    print("错误: 无法导入VisionAI-ClipsMaster模块。请确认项目目录结构正确。")
    sys.exit(1)


def print_separator(title: str = None):
    """打印分隔符"""
    width = 70
    if title:
        print(f"\n{'-' * 10} {title} {'-' * (width - 12 - len(title))}")
    else:
        print(f"\n{'-' * width}")


def analyze_videos(video_paths: List[str], verbose: bool = False):
    """分析多个视频的时长
    
    Args:
        video_paths: 视频文件路径列表
        verbose: 是否显示详细信息
    """
    if not video_paths:
        print("请提供至少一个视频文件路径")
        return
    
    print_separator("视频时长分析示例")
    print(f"共有 {len(video_paths)} 个视频文件待分析")
    
    analyzer = BaseAnalyzer()
    
    for i, video_path in enumerate(video_paths):
        print_separator(f"视频 {i+1}: {os.path.basename(video_path)}")
        
        if not os.path.exists(video_path):
            print(f"错误: 文件不存在 '{video_path}'")
            continue
        
        try:
            # 使用便利函数进行简单的时长分析
            duration = analyze_source_duration(video_path)
            print(f"时长: {duration:.3f} 秒 ({format_time(duration)})")
            
            if verbose:
                # 获取详细的视频元数据
                metadata = analyzer.get_video_metadata(video_path)
                
                print("\n视频元数据:")
                print(f"  • 分辨率: {metadata.get('width', 'N/A')}x{metadata.get('height', 'N/A')}")
                print(f"  • 帧率: {metadata.get('fps', 'N/A'):.3f} fps")
                
                if 'format_name' in metadata:
                    print(f"  • 格式: {metadata.get('format_name', 'N/A')}")
                
                if 'codec' in metadata:
                    print(f"  • 编解码器: {metadata.get('codec', 'N/A')}")
                
                if 'bit_rate' in metadata:
                    print(f"  • 比特率: {int(metadata.get('bit_rate', 0)/1000):.0f} kbps")
                
                # 如果同时有OpenCV和FFprobe的数据，显示对比信息
                if 'cv2' in metadata and 'duration' in metadata['cv2'] and 'duration' in metadata:
                    cv_duration = metadata['cv2']['duration']
                    ff_duration = metadata['duration']
                    diff = abs(cv_duration - ff_duration)
                    
                    print("\n时长分析对比:")
                    print(f"  • OpenCV: {cv_duration:.3f} 秒")
                    print(f"  • FFprobe: {ff_duration:.3f} 秒")
                    print(f"  • 差异: {diff:.3f} 秒 ({diff*1000:.1f} 毫秒)")
                    
                    # 评估精度
                    if diff <= 0.001:  # 1毫秒内
                        print("  • 精度评估: 极高 ✓✓✓")
                    elif diff <= 0.01:  # 10毫秒内
                        print("  • 精度评估: 很好 ✓✓")
                    elif diff <= 0.1:  # 100毫秒内
                        print("  • 精度评估: 良好 ✓")
                    else:
                        print("  • 精度评估: 存在较大差异 ⚠")
        
        except Exception as e:
            print(f"分析出错: {str(e)}")


def format_time(seconds: float) -> str:
    """将秒数格式化为时:分:秒.毫秒格式
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视频时长分析示例")
    parser.add_argument("video_paths", nargs="+", help="视频文件路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    
    args = parser.parse_args()
    analyze_videos(args.video_paths, args.verbose)


if __name__ == "__main__":
    main() 