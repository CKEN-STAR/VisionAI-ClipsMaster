#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频播放器模块

提供跨平台的视频播放功能，支持基础播放控制和高级媒体操作。
与时间轴编辑和素材管理集成，提供一体化的视频预览体验。
"""

import os
import cv2
import numpy as np
import time
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from threading import Thread, Event

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("video_player")

class VideoPlayer:
    """视频播放器类
    
    跨平台视频播放器实现，支持基本播放控制和帧操作。
    集成时间轴和素材指纹功能，用于视频素材预览和剪辑点选择。
    """
    
    def __init__(self, video_path: str = None):
        """初始化视频播放器
        
        Args:
            video_path: 视频文件路径，可选
        """
        self.video_path = video_path
        self.cap = None
        self.is_playing = False
        self.play_thread = None
        self.stop_event = Event()
        
        # 视频属性
        self.total_frames = 0
        self.fps = 0
        self.width = 0
        self.height = 0
        self.duration = 0
        
        # 回调函数
        self.frame_callback = None
        self.position_callback = None
        
        # 剪辑点
        self.in_point = None
        self.out_point = None
        
        # 初始加载视频（如果提供了路径）
        if video_path:
            self.load_video(video_path)
    
    def load_video(self, video_path: str) -> bool:
        """加载视频文件
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            bool: 加载是否成功
        """
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        # 关闭现有视频
        self.close()
        
        # 打开新视频
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return False
        
        # 获取视频属性
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        # 重置播放状态
        self.is_playing = False
        self.stop_event.clear()
        self.current_frame_position = 0
        
        # 重置剪辑点
        self.in_point = None
        self.out_point = None
        
        logger.info(f"已加载视频: {os.path.basename(video_path)} | {self.width}x{self.height} | {self.fps}fps | {self.format_duration(self.duration)}")
        return True
    
    def close(self) -> None:
        """关闭视频并释放资源"""
        self.stop_playback()
        
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def play(self) -> None:
        """开始播放视频"""
        if self.cap is None or self.is_playing:
            return
        
        self.is_playing = True
        self.stop_event.clear()
        
        # 使用线程播放视频
        self.play_thread = Thread(target=self._play_thread)
        self.play_thread.daemon = True
        self.play_thread.start()
    
    def _play_thread(self) -> None:
        """播放线程函数"""
        if self.cap is None:
            return
        
        # 获取当前位置
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        # 如果已经到达视频结尾，重新开始
        if current_pos >= self.total_frames - 1:
            self.seek_to_frame(0)
        
        # 计算帧间隔时间（秒）
        frame_time = 1.0 / self.fps if self.fps > 0 else 0.033
        
        while self.is_playing and not self.stop_event.is_set():
            # 获取下一帧
            start_time = time.time()
            ret, frame = self.cap.read()
            
            # 检查是否到达视频结尾
            if not ret:
                self.current_frame_position = 0
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # 更新当前帧位置
            self.current_frame_position = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            
            # 调用帧回调函数
            if self.frame_callback:
                self.frame_callback(frame)
            
            # 调用位置回调函数
            if self.position_callback:
                current_time = self.current_frame_position / self.fps if self.fps > 0 else 0
                self.position_callback(self.current_frame_position, current_time)
            
            # 如果设置了出点并达到出点，暂停播放
            if self.out_point is not None and self.current_frame_position >= self.out_point:
                self.pause()
                break
            
            # 控制播放速度
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            time.sleep(sleep_time)
    
    def pause(self) -> None:
        """暂停视频播放"""
        self.is_playing = False
    
    def stop_playback(self) -> None:
        """停止视频播放并重置位置"""
        if self.is_playing:
            self.is_playing = False
            self.stop_event.set()
            
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join(timeout=1.0)
        
        # 重置到开始位置
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_position = 0
    
    def toggle_play_pause(self) -> bool:
        """切换播放/暂停状态
        
        Returns:
            bool: 切换后是否为播放状态
        """
        if self.is_playing:
            self.pause()
        else:
            self.play()
        return self.is_playing
    
    def seek_to_frame(self, frame_number: int) -> bool:
        """定位到指定帧
        
        Args:
            frame_number: 帧索引
            
        Returns:
            bool: 定位是否成功
        """
        if self.cap is None:
            return False
        
        # 确保帧索引在有效范围内
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        
        # 设置位置
        ret = self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        if ret:
            self.current_frame_position = frame_number
            
            # 获取并显示当前帧
            ret, frame = self.cap.read()
            if ret and self.frame_callback:
                self.frame_callback(frame)
                # 回退一帧，确保下次get会得到相同的帧
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # 更新位置回调
            if self.position_callback:
                current_time = frame_number / self.fps if self.fps > 0 else 0
                self.position_callback(frame_number, current_time)
            
            return True
        
        return False
    
    def seek_to_time(self, time_seconds: float) -> bool:
        """定位到指定时间点
        
        Args:
            time_seconds: 时间点（秒）
            
        Returns:
            bool: 定位是否成功
        """
        if self.fps <= 0:
            return False
        
        frame_number = int(time_seconds * self.fps)
        return self.seek_to_frame(frame_number)
    
    def next_frame(self) -> Optional[np.ndarray]:
        """移动到下一帧
        
        Returns:
            Optional[np.ndarray]: 帧图像，如果无法获取则为None
        """
        if self.cap is None:
            return None
        
        # 暂停播放
        was_playing = self.is_playing
        if was_playing:
            self.pause()
        
        # 获取当前帧索引
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        # 检查是否已经到达视频末尾
        if current_pos >= self.total_frames - 1:
            return None
        
        # 读取下一帧
        ret, frame = self.cap.read()
        
        if ret:
            self.current_frame_position = current_pos
            
            # 调用回调函数
            if self.frame_callback:
                self.frame_callback(frame)
            
            # 调用位置回调函数
            if self.position_callback:
                current_time = self.current_frame_position / self.fps if self.fps > 0 else 0
                self.position_callback(self.current_frame_position, current_time)
            
            return frame
        
        return None
    
    def previous_frame(self) -> Optional[np.ndarray]:
        """移动到上一帧
        
        Returns:
            Optional[np.ndarray]: 帧图像，如果无法获取则为None
        """
        if self.cap is None:
            return None
        
        # 暂停播放
        was_playing = self.is_playing
        if was_playing:
            self.pause()
        
        # 获取当前帧索引
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        # 检查是否已经在视频开头
        if current_pos <= 1:
            self.seek_to_frame(0)
            ret, frame = self.cap.read()
            if ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return frame
            return None
        
        # 向前移动两帧
        new_pos = max(0, current_pos - 2)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
        
        # 读取帧
        ret, frame = self.cap.read()
        
        if ret:
            self.current_frame_position = new_pos
            
            # 调用回调函数
            if self.frame_callback:
                self.frame_callback(frame)
            
            # 调用位置回调函数
            if self.position_callback:
                current_time = self.current_frame_position / self.fps if self.fps > 0 else 0
                self.position_callback(self.current_frame_position, current_time)
            
            return frame
        
        return None
    
    def format_duration(self, seconds: float) -> str:
        """将秒数格式化为时间字符串
        
        Args:
            seconds: 时间（秒）
            
        Returns:
            str: 格式化的时间字符串，格式为HH:MM:SS
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def format_timecode(self, seconds: float) -> str:
        """将秒数格式化为时间码
        
        Args:
            seconds: 时间（秒）
            
        Returns:
            str: 格式化的时间码，格式为HH:MM:SS:FF
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds - int(seconds)) * self.fps)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """设置帧回调函数
        
        Args:
            callback: 回调函数，接收帧图像作为参数
        """
        self.frame_callback = callback
    
    def set_position_callback(self, callback: Callable[[int, float], None]) -> None:
        """设置位置回调函数
        
        Args:
            callback: 回调函数，接收帧索引和时间作为参数
        """
        self.position_callback = callback
    
    def set_in_point(self, frame_number: Optional[int] = None) -> int:
        """设置入点
        
        Args:
            frame_number: 帧索引，默认使用当前位置
            
        Returns:
            int: 设置的入点帧索引
        """
        if frame_number is None and self.cap is not None:
            frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        if frame_number is not None:
            self.in_point = max(0, min(frame_number, self.total_frames - 1))
            logger.info(f"已设置入点: 第 {self.in_point} 帧 ({self.format_timecode(self.in_point/self.fps if self.fps > 0 else 0)})")
            
            # 如果出点在入点之前，清除出点
            if self.out_point is not None and self.out_point < self.in_point:
                self.out_point = None
        
        return self.in_point
    
    def set_out_point(self, frame_number: Optional[int] = None) -> int:
        """设置出点
        
        Args:
            frame_number: 帧索引，默认使用当前位置
            
        Returns:
            int: 设置的出点帧索引
        """
        if frame_number is None and self.cap is not None:
            frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        if frame_number is not None:
            self.out_point = max(0, min(frame_number, self.total_frames - 1))
            logger.info(f"已设置出点: 第 {self.out_point} 帧 ({self.format_timecode(self.out_point/self.fps if self.fps > 0 else 0)})")
            
            # 如果入点在出点之后，清除入点
            if self.in_point is not None and self.in_point > self.out_point:
                self.in_point = None
        
        return self.out_point
    
    def clear_in_point(self) -> None:
        """清除入点"""
        self.in_point = None
        logger.info("已清除入点")
    
    def clear_out_point(self) -> None:
        """清除出点"""
        self.out_point = None
        logger.info("已清除出点")
    
    def get_selected_clip_info(self) -> Dict[str, Any]:
        """获取当前选择的剪辑信息
        
        Returns:
            Dict[str, Any]: 剪辑信息，包括入点、出点、持续时间等
        """
        in_frame = self.in_point if self.in_point is not None else 0
        out_frame = self.out_point if self.out_point is not None else self.total_frames - 1
        
        in_time = in_frame / self.fps if self.fps > 0 else 0
        out_time = out_frame / self.fps if self.fps > 0 else 0
        duration = out_time - in_time
        
        return {
            "in_frame": in_frame,
            "out_frame": out_frame,
            "in_time": in_time,
            "out_time": out_time,
            "duration": duration,
            "in_timecode": self.format_timecode(in_time),
            "out_timecode": self.format_timecode(out_time),
            "duration_timecode": self.format_timecode(duration)
        }
    
    def extract_clip_frames(self, output_dir: Optional[str] = None, 
                           frame_interval: int = 1) -> List[str]:
        """提取选定区域的帧图像
        
        Args:
            output_dir: 输出目录，默认为临时目录
            frame_interval: 帧间隔，每隔多少帧提取一帧
            
        Returns:
            List[str]: 提取的帧图像文件路径列表
        """
        if self.cap is None:
            logger.error("没有加载视频")
            return []
        
        # 设置默认输出目录
        if output_dir is None:
            import tempfile
            output_dir = os.path.join(tempfile.gettempdir(), "visionai_clips")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取入点和出点
        in_frame = self.in_point if self.in_point is not None else 0
        out_frame = self.out_point if self.out_point is not None else self.total_frames - 1
        
        # 保存当前位置
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        # 跳转到入点
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, in_frame)
        
        output_files = []
        frame_count = 0
        
        # 提取帧图像
        while True:
            # 读取帧
            ret, frame = self.cap.read()
            
            if not ret or frame_count > (out_frame - in_frame):
                break
            
            # 每隔指定帧数保存一帧
            if frame_count % frame_interval == 0:
                filename = os.path.join(output_dir, f"frame_{in_frame + frame_count:06d}.jpg")
                cv2.imwrite(filename, frame)
                output_files.append(filename)
            
            frame_count += 1
        
        # 恢复原位置
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
        
        logger.info(f"已提取 {len(output_files)} 帧图像，保存至 {output_dir}")
        return output_files
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """获取当前帧图像
        
        Returns:
            Optional[np.ndarray]: 当前帧图像，如果无法获取则为None
        """
        if self.cap is None:
            return None
        
        # 保存当前位置
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        # 向前回退一帧
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos - 1)
        
        # 读取帧
        ret, frame = self.cap.read()
        
        return frame if ret else None

def test_video_player(video_path: str) -> None:
    """测试视频播放器功能
    
    Args:
        video_path: 视频文件路径
    """
    import cv2
    
    def on_frame(frame):
        # 显示帧
        cv2.imshow("Video Player", frame)
        key = cv2.waitKey(1)
        
        # 按ESC退出
        if key == 27:
            player.close()
            cv2.destroyAllWindows()
    
    def on_position(frame_index, time_seconds):
        # 打印位置信息
        print(f"\rFrame: {frame_index}/{player.total_frames} | Time: {player.format_timecode(time_seconds)}", end="")
    
    # 创建播放器
    player = VideoPlayer(video_path)
    
    # 设置回调
    player.set_frame_callback(on_frame)
    player.set_position_callback(on_position)
    
    # 创建窗口
    cv2.namedWindow("Video Player", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Video Player", 800, 600)
    
    # 开始播放
    player.play()
    
    print("\n按空格键暂停/播放，方向键前进/后退帧，I键设置入点，O键设置出点，ESC退出")
    
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
    
    player.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        test_video_player(video_path)
    else:
        print("请提供视频文件路径作为参数") 