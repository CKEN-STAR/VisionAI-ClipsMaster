#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键帧提取模块 - 提取视频中的关键帧，用于与文本内容对齐
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
import tempfile

# 导入日志模块
from src.utils.log_handler import get_logger

# 导入异常处理
from src.utils.exceptions import MediaProcessingError

# 配置日志
logger = get_logger("keyframe_extractor")

def extract_keyframes(
    video_path: str, 
    method: str = 'uniform', 
    num_frames: int = 10, 
    threshold: float = 30.0,
    save_frames: bool = False,
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    从视频中提取关键帧
    
    参数:
        video_path: 视频文件路径
        method: 提取方法，可选 'uniform'(均匀提取), 'difference'(差异提取), 'scene'(场景变化)
        num_frames: 提取的帧数（用于均匀提取）
        threshold: 差异阈值（用于差异提取和场景变化）
        save_frames: 是否保存关键帧图像
        output_dir: 保存图像的目录，如果为None则使用临时目录
        
    返回:
        关键帧信息列表，每帧包含timestamp(时间戳)和frame(图像数据)
    
    异常:
        MediaProcessingError: 视频处理失败
    """
    if not os.path.exists(video_path):
        raise MediaProcessingError(f"视频文件不存在: {video_path}")
    
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise MediaProcessingError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"视频信息: {total_frames}帧, {fps}fps, 时长{duration:.2f}秒")
        
        # 选择提取方法
        if method == 'uniform':
            keyframes = _extract_uniform_keyframes(cap, num_frames, total_frames)
        elif method == 'difference':
            keyframes = _extract_difference_keyframes(cap, threshold, total_frames)
        elif method == 'scene':
            keyframes = _extract_scene_keyframes(cap, threshold, total_frames)
        else:
            raise ValueError(f"不支持的提取方法: {method}")
        
        # 为每个关键帧添加时间戳
        for kf in keyframes:
            frame_idx = kf['frame_idx']
            kf['timestamp'] = frame_idx / fps if fps > 0 else 0
        
        # 保存关键帧图像
        if save_frames:
            _save_keyframes(keyframes, video_path, output_dir)
        
        cap.release()
        return keyframes
        
    except Exception as e:
        logger.error(f"关键帧提取失败: {str(e)}")
        raise MediaProcessingError(f"关键帧提取失败: {str(e)}")
    finally:
        # 确保视频捕获对象被释放
        if 'cap' in locals() and cap.isOpened():
            cap.release()

def _extract_uniform_keyframes(
    cap: cv2.VideoCapture, 
    num_frames: int, 
    total_frames: int
) -> List[Dict[str, Any]]:
    """均匀提取关键帧"""
    keyframes = []
    
    if total_frames <= 0 or num_frames <= 0:
        return keyframes
    
    # 计算帧间隔
    interval = max(1, total_frames // num_frames)
    
    for i in range(0, total_frames, interval):
        # 设置当前帧位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        
        if ret:
            keyframes.append({
                'frame_idx': i,
                'frame': frame,
                'method': 'uniform'
            })
        
        # 如果已经提取足够数量的帧，则停止
        if len(keyframes) >= num_frames:
            break
    
    return keyframes

def _extract_difference_keyframes(
    cap: cv2.VideoCapture, 
    threshold: float, 
    total_frames: int,
    max_frames: int = 30
) -> List[Dict[str, Any]]:
    """基于帧差异提取关键帧"""
    keyframes = []
    prev_frame = None
    
    # 读取第一帧
    ret, frame = cap.read()
    if ret:
        keyframes.append({
            'frame_idx': 0,
            'frame': frame,
            'method': 'difference',
            'diff_score': 0.0
        })
        prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    frame_idx = 1
    while frame_idx < total_frames:
        # 读取下一帧
        ret, frame = cap.read()
        if not ret:
            break
        
        # 计算与前一帧的差异
        curr_frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is not None:
            # 计算帧间差异
            diff = cv2.absdiff(curr_frame_gray, prev_frame)
            diff_score = np.mean(diff)
            
            # 如果差异超过阈值，则认为是关键帧
            if diff_score > threshold:
                keyframes.append({
                    'frame_idx': frame_idx,
                    'frame': frame,
                    'method': 'difference',
                    'diff_score': float(diff_score)
                })
        
        prev_frame = curr_frame_gray
        frame_idx += 1
        
        # 限制关键帧数量
        if len(keyframes) >= max_frames:
            break
    
    return keyframes

def _extract_scene_keyframes(
    cap: cv2.VideoCapture, 
    threshold: float, 
    total_frames: int,
    max_frames: int = 30
) -> List[Dict[str, Any]]:
    """基于场景变化提取关键帧"""
    keyframes = []
    
    # 创建BackgroundSubtractorMOG2对象
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(
        history=500, 
        varThreshold=16, 
        detectShadows=False
    )
    
    # 读取第一帧
    ret, frame = cap.read()
    if ret:
        keyframes.append({
            'frame_idx': 0,
            'frame': frame,
            'method': 'scene',
            'motion_score': 0.0
        })
    
    frame_idx = 1
    while frame_idx < total_frames:
        # 读取下一帧
        ret, frame = cap.read()
        if not ret:
            break
        
        # 应用背景减除
        fg_mask = bg_subtractor.apply(frame)
        
        # 计算运动得分
        motion_score = np.mean(fg_mask) / 255.0
        
        # 如果运动得分超过阈值，则认为是场景变化
        if motion_score > threshold / 100.0:  # 将阈值调整到0-1范围
            keyframes.append({
                'frame_idx': frame_idx,
                'frame': frame,
                'method': 'scene',
                'motion_score': float(motion_score)
            })
        
        frame_idx += 1
        
        # 限制关键帧数量
        if len(keyframes) >= max_frames:
            break
    
    return keyframes

def _save_keyframes(
    keyframes: List[Dict[str, Any]], 
    video_path: str, 
    output_dir: Optional[str] = None
) -> None:
    """保存关键帧图像到文件"""
    # 确定输出目录
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="keyframes_")
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    # 从视频路径获取文件名（不含扩展名）
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # 保存每一帧
    for i, kf in enumerate(keyframes):
        if 'frame' in kf:
            frame = kf['frame']
            timestamp = kf.get('timestamp', 0)
            method = kf.get('method', 'unknown')
            
            # 构建文件名
            filename = f"{video_name}_frame{i:03d}_{method}_{timestamp:.2f}s.jpg"
            filepath = os.path.join(output_dir, filename)
            
            # 保存图像
            cv2.imwrite(filepath, frame)
            
            # 更新关键帧信息
            kf['file_path'] = filepath
            
            # 删除frame属性，减少内存占用
            del kf['frame']
    
    logger.info(f"已保存{len(keyframes)}个关键帧到: {output_dir}")

# 为外部调用提供简单接口
def get_video_keyframes(video_path: str, num_frames: int = 10) -> List[Dict[str, Any]]:
    """
    从视频中提取关键帧的简化接口
    
    参数:
        video_path: 视频文件路径
        num_frames: 提取的帧数
        
    返回:
        关键帧信息列表
    """
    return extract_keyframes(
        video_path=video_path,
        method='uniform',
        num_frames=num_frames,
        save_frames=False
    )

# 测试代码
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <视频文件路径> [提取方法] [关键帧数/阈值]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'uniform'
    
    if method == 'uniform':
        num_frames = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        threshold = 30.0
    else:
        threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
        num_frames = 20
    
    try:
        keyframes = extract_keyframes(
            video_path=video_path,
            method=method,
            num_frames=num_frames,
            threshold=threshold,
            save_frames=True
        )
        
        print(f"提取了 {len(keyframes)} 个关键帧:")
        for i, kf in enumerate(keyframes):
            print(f"  帧 {i+1}: 时间戳 {kf['timestamp']:.2f}s, 帧索引 {kf['frame_idx']}")
            if 'file_path' in kf:
                print(f"    保存路径: {kf['file_path']}")
    
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1) 