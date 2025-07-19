#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频播放器集成演示

展示如何将视频播放器与时间轴映射和素材指纹功能集成使用。
"""

import os
import sys
import cv2
import json
import tempfile
import numpy as np
from typing import Dict, List, Any

from src.export.video_player import VideoPlayer
from src.export.timeline_mapper import map_segments_to_timeline, time_to_frame, frame_to_time
from src.export.asset_fingerprint import generate_asset_id, get_asset_metadata, save_asset_fingerprint

# 全局变量
segments = []
current_segment = None
timeline_data = None

def create_segment_from_selection(player: VideoPlayer, text: str = "") -> Dict[str, Any]:
    """从播放器选择点创建片段
    
    Args:
        player: 视频播放器实例
        text: 片段文本
        
    Returns:
        Dict[str, Any]: 创建的片段数据
    """
    clip_info = player.get_selected_clip_info()
    
    # 生成素材ID
    asset_id = generate_asset_id(player.video_path)
    
    # 创建片段
    segment = {
        "asset_id": asset_id,
        "start_time": clip_info["in_time"],
        "duration": clip_info["duration"],
        "text": text or f"片段 {len(segments) + 1}",
        "in_frame": clip_info["in_frame"],
        "out_frame": clip_info["out_frame"],
        "in_timecode": clip_info["in_timecode"],
        "out_timecode": clip_info["out_timecode"]
    }
    
    return segment

def draw_timeline(frame: np.ndarray, player: VideoPlayer, segments: List[Dict[str, Any]]) -> np.ndarray:
    """在帧上绘制时间轴信息
    
    Args:
        frame: 原始帧图像
        player: 视频播放器实例
        segments: 片段列表
        
    Returns:
        np.ndarray: 添加了时间轴的帧图像
    """
    height, width = frame.shape[:2]
    
    # 创建时间轴区域
    timeline_height = 50
    timeline_y = height - timeline_height
    timeline_frame = frame.copy()
    
    # 绘制时间轴背景
    cv2.rectangle(timeline_frame, (0, timeline_y), (width, height), (40, 40, 40), -1)
    
    # 计算比例
    scale = width / player.total_frames
    
    # 绘制片段
    for i, seg in enumerate(segments):
        start_frame = seg.get("in_frame", 0)
        end_frame = seg.get("out_frame", 0)
        
        # 计算位置
        x1 = int(start_frame * scale)
        x2 = int(end_frame * scale)
        
        # 为每个片段使用不同颜色
        colors = [(0, 200, 0), (0, 0, 200), (200, 0, 0), (200, 200, 0), (0, 200, 200), (200, 0, 200)]
        color = colors[i % len(colors)]
        
        # 绘制片段区域
        cv2.rectangle(timeline_frame, (x1, timeline_y + 5), (x2, height - 5), color, -1)
        
        # 添加片段索引
        cv2.putText(timeline_frame, str(i+1), (x1 + 5, timeline_y + 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # 绘制播放头
    playhead_pos = int(player.current_frame_position * scale)
    cv2.line(timeline_frame, (playhead_pos, timeline_y), (playhead_pos, height), (255, 255, 255), 2)
    
    # 绘制入点和出点标记
    if player.in_point is not None:
        in_pos = int(player.in_point * scale)
        cv2.line(timeline_frame, (in_pos, timeline_y), (in_pos, height), (0, 255, 0), 2)
        cv2.putText(timeline_frame, "I", (in_pos - 5, timeline_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    if player.out_point is not None:
        out_pos = int(player.out_point * scale)
        cv2.line(timeline_frame, (out_pos, timeline_y), (out_pos, height), (0, 0, 255), 2)
        cv2.putText(timeline_frame, "O", (out_pos - 5, timeline_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # 显示当前位置时间码
    current_time = player.current_frame_position / player.fps if player.fps > 0 else 0
    time_text = f"当前: {player.format_timecode(current_time)}"
    cv2.putText(timeline_frame, time_text, (10, timeline_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return timeline_frame

def on_frame(frame):
    """帧回调函数
    
    Args:
        frame: 视频帧
    """
    global segments, player
    
    # 添加时间轴信息
    display_frame = draw_timeline(frame, player, segments)
    
    # 显示帧
    cv2.imshow("VisionAI ClipsMaster", display_frame)
    key = cv2.waitKey(1)
    
    # 按ESC退出
    if key == 27:
        player.close()
        cv2.destroyAllWindows()

def main(video_path: str):
    """主函数
    
    Args:
        video_path: 视频文件路径
    """
    global segments, player, timeline_data
    
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return
    
    # 创建播放器
    player = VideoPlayer(video_path)
    
    # 设置回调
    player.set_frame_callback(on_frame)
    
    # 创建窗口
    cv2.namedWindow("VisionAI ClipsMaster", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("VisionAI ClipsMaster", 1280, 720)
    
    print("\n==== VisionAI ClipsMaster 演示 ====")
    print("视频信息:")
    print(f"  - 分辨率: {player.width}x{player.height}")
    print(f"  - 帧率: {player.fps}fps")
    print(f"  - 时长: {player.format_duration(player.duration)}")
    print(f"  - 总帧数: {player.total_frames}")
    
    print("\n控制键:")
    print("  - 空格: 播放/暂停")
    print("  - 左/右箭头: 前一帧/后一帧")
    print("  - I: 设置入点")
    print("  - O: 设置出点")
    print("  - A: 添加当前选区为片段")
    print("  - T: 生成时间轴数据并保存")
    print("  - S: 保存素材指纹")
    print("  - ESC: 退出")
    
    # 开始播放
    player.play()
    
    while True:
        key = cv2.waitKey(100)
        
        if key == 27:  # ESC
            break
        elif key == 32:  # 空格
            player.toggle_play_pause()
        elif key == 81 or key == 2424832:  # 左箭头
            player.previous_frame()
        elif key == 83 or key == 2555904:  # 右箭头
            player.next_frame()
        elif key == 105 or key == 73:  # I键
            player.set_in_point()
        elif key == 111 or key == 79:  # O键
            player.set_out_point()
        elif key == 97 or key == 65:  # A键 - 添加片段
            if player.in_point is not None and player.out_point is not None:
                segment = create_segment_from_selection(player)
                segments.append(segment)
                print(f"\n已添加片段 {len(segments)}: {segment['in_timecode']} - {segment['out_timecode']} ({segment['duration']:.2f}秒)")
                
                # 清除入点和出点
                player.clear_in_point()
                player.clear_out_point()
        elif key == 116 or key == 84:  # T键 - 生成时间轴
            if segments:
                timeline_data = map_segments_to_timeline(segments, player.fps)
                
                # 保存到临时文件
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, "visionai_timeline.json")
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(timeline_data, f, ensure_ascii=False, indent=2)
                
                print(f"\n已生成时间轴数据并保存至: {output_path}")
                print(f"总时长: {timeline_data['duration']:.2f}秒")
                print(f"视频轨道片段数: {len(timeline_data['tracks']['video'][0]['clips'])}")
                print(f"音频轨道片段数: {len(timeline_data['tracks']['audio'][0]['clips'])}")
            else:
                print("\n错误: 没有添加任何片段")
        elif key == 115 or key == 83:  # S键 - 保存素材指纹
            fingerprint_path = save_asset_fingerprint(video_path)
            print(f"\n已保存素材指纹: {fingerprint_path}")
            
            # 获取详细元数据
            metadata = get_asset_metadata(video_path)
            print(f"素材ID: {metadata['asset_id']}")
            print(f"文件大小: {metadata['size_human']}")
            print(f"MIME类型: {metadata['mime_type']}")
    
    # 关闭资源
    player.close()
    cv2.destroyAllWindows()
    
    print("\n会话结束，已添加 {} 个片段".format(len(segments)))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        main(video_path)
    else:
        print("请提供视频文件路径作为参数")
        print("用法: python demo_video_player.py <视频文件路径>") 