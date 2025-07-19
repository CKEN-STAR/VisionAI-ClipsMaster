#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建样本视频脚本

生成用于测试内存映射引擎的样本视频文件。
"""

import os
import cv2
import numpy as np
import argparse
from pathlib import Path

def create_sample_video(output_path, duration=5, fps=30, width=640, height=480):
    """创建样本视频
    
    Args:
        output_path: 输出文件路径
        duration: 视频时长（秒）
        fps: 帧率
        width: 视频宽度
        height: 视频高度
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 视频编解码器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # 创建视频写入器
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # 确定总帧数
    total_frames = int(duration * fps)
    
    print(f"生成 {total_frames} 帧样本视频，分辨率 {width}x{height}...")
    
    # 生成并写入帧
    for i in range(total_frames):
        # 创建彩色渐变背景
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 颜色随时间变化
        r = int(128 + 127 * np.sin(i * 0.05))
        g = int(128 + 127 * np.sin(i * 0.05 + 2))
        b = int(128 + 127 * np.sin(i * 0.05 + 4))
        
        # 填充背景色
        frame[:, :] = (b, g, r)
        
        # 添加圆形物体
        cv2.circle(
            frame,
            center=(int(width/2 + width/4 * np.sin(i * 0.1)),
                   int(height/2 + height/4 * np.cos(i * 0.1))),
            radius=50,
            color=(0, 0, 255),
            thickness=-1
        )
        
        # 添加文本
        cv2.putText(
            frame,
            f'Frame {i} / {total_frames}',
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
        # 添加时间码
        time_str = f'{i//fps:02d}:{i%fps:02d}'
        cv2.putText(
            frame,
            time_str,
            (width - 150, height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
        # 写入帧
        out.write(frame)
        
        # 显示进度
        if i % 30 == 0:
            print(f"已处理: {i}/{total_frames} 帧 ({i/total_frames*100:.1f}%)")
    
    # 释放资源
    out.release()
    
    print(f"样本视频已生成: {output_path}")
    print(f"时长: {duration}秒, 帧率: {fps}, 分辨率: {width}x{height}")

def main():
    parser = argparse.ArgumentParser(description='创建样本视频文件')
    parser.add_argument('--output', type=str, default='outputs/sample_video.mp4',
                        help='输出视频文件路径')
    parser.add_argument('--duration', type=int, default=5,
                        help='视频时长（秒）')
    parser.add_argument('--fps', type=int, default=30,
                        help='帧率')
    parser.add_argument('--width', type=int, default=640,
                        help='视频宽度')
    parser.add_argument('--height', type=int, default=480,
                        help='视频高度')
    
    args = parser.parse_args()
    
    create_sample_video(
        args.output,
        args.duration,
        args.fps,
        args.width,
        args.height
    )

if __name__ == '__main__':
    main() 