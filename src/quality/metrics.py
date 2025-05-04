#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
质量评估指标计算模块

提供计算视频图像质量评估指标的功能，包括SSIM、PSNR和光流分析等。
支持视频、音频质量评估以及场景转换质量评估。
"""

import os
import logging
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入CV和视频处理库
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    logger.warning("未安装OpenCV，将使用备用视频处理方法")
    CV2_AVAILABLE = False

try:
    from skimage.metrics import structural_similarity, peak_signal_noise_ratio
    SKIMAGE_AVAILABLE = True
except ImportError:
    logger.warning("未安装scikit-image，将使用OpenCV计算SSIM和PSNR")
    SKIMAGE_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    logger.warning("未安装librosa，音频质量评估功能将不可用")
    LIBROSA_AVAILABLE = False


def _extract_frames(video_path: str, max_frames: int = 100) -> List[np.ndarray]:
    """从视频中提取帧

    Args:
        video_path: 视频文件路径
        max_frames: 最大提取帧数，默认100

    Returns:
        List[np.ndarray]: 提取的帧列表
    """
    if not CV2_AVAILABLE:
        logger.error("未安装OpenCV，无法提取视频帧")
        return []

    frames = []
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logger.error(f"无法打开视频文件: {video_path}")
        return []

    # 获取视频信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames <= 0:
        logger.error(f"视频帧数无效: {total_frames}")
        return []
    
    # 计算采样间隔
    sample_interval = max(1, total_frames // max_frames)
    
    # 提取帧
    frame_positions = list(range(0, total_frames, sample_interval))[:max_frames]
    
    for pos in frame_positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    
    cap.release()
    return frames


def calculate_ssim(video1_path: str, video2_path: str, max_frames: int = 50) -> float:
    """计算两个视频之间的结构相似性指标(SSIM)

    Args:
        video1_path: 第一个视频的路径
        video2_path: 第二个视频的路径
        max_frames: 最大比较的帧数

    Returns:
        float: SSIM值，范围[0,1]，值越大表示越相似
    """
    try:
        # 提取帧
        frames1 = _extract_frames(video1_path, max_frames)
        frames2 = _extract_frames(video2_path, max_frames)
        
        if not frames1 or not frames2:
            logger.error("无法从视频中提取帧")
            return 0.0
        
        # 取最小帧数
        min_frames = min(len(frames1), len(frames2))
        
        if min_frames == 0:
            logger.error("没有可用于比较的帧")
            return 0.0
        
        # 计算每一帧的SSIM
        ssim_values = []
        
        for i in range(min_frames):
            # 转换为灰度图
            gray1 = cv2.cvtColor(frames1[i], cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frames2[i], cv2.COLOR_BGR2GRAY)
            
            # 计算SSIM
            if SKIMAGE_AVAILABLE:
                ssim_val = structural_similarity(gray1, gray2, data_range=255)
            else:
                ssim_val, _ = cv2.compare_ssim(gray1, gray2, full=True)
            
            ssim_values.append(ssim_val)
        
        # 返回平均SSIM
        return np.mean(ssim_values)
        
    except Exception as e:
        logger.error(f"计算SSIM失败: {str(e)}")
        return 0.0


def calculate_psnr(video1_path: str, video2_path: str, max_frames: int = 50) -> float:
    """计算两个视频之间的峰值信噪比(PSNR)

    Args:
        video1_path: 第一个视频的路径
        video2_path: 第二个视频的路径
        max_frames: 最大比较的帧数

    Returns:
        float: PSNR值，单位dB，值越大表示越相似
    """
    try:
        # 提取帧
        frames1 = _extract_frames(video1_path, max_frames)
        frames2 = _extract_frames(video2_path, max_frames)
        
        if not frames1 or not frames2:
            logger.error("无法从视频中提取帧")
            return 0.0
        
        # 取最小帧数
        min_frames = min(len(frames1), len(frames2))
        
        if min_frames == 0:
            logger.error("没有可用于比较的帧")
            return 0.0
        
        # 计算每一帧的PSNR
        psnr_values = []
        
        for i in range(min_frames):
            # 确保尺寸一致
            if frames1[i].shape != frames2[i].shape:
                frames2[i] = cv2.resize(frames2[i], (frames1[i].shape[1], frames1[i].shape[0]))
            
            # 计算PSNR
            if SKIMAGE_AVAILABLE:
                psnr_val = peak_signal_noise_ratio(frames1[i], frames2[i], data_range=255)
            else:
                mse = np.mean((frames1[i].astype(np.float64) - frames2[i].astype(np.float64)) ** 2)
                if mse == 0:
                    psnr_val = 100  # 避免除以零
                else:
                    psnr_val = 10 * np.log10((255 ** 2) / mse)
            
            psnr_values.append(psnr_val)
        
        # 返回平均PSNR
        return np.mean(psnr_values)
        
    except Exception as e:
        logger.error(f"计算PSNR失败: {str(e)}")
        return 0.0


def optical_flow_analysis(video1_path: str, video2_path: str, max_frames: int = 30) -> float:
    """通过光流分析计算两个视频的运动一致性

    Args:
        video1_path: 第一个视频的路径
        video2_path: 第二个视频的路径
        max_frames: 最大分析的帧数

    Returns:
        float: 运动一致性得分，范围[0,1]，值越大表示越一致
    """
    if not CV2_AVAILABLE:
        logger.error("未安装OpenCV，无法进行光流分析")
        return 0.0
    
    try:
        # 提取帧，需要连续帧
        frames1 = _extract_frames(video1_path, max_frames * 2)
        frames2 = _extract_frames(video2_path, max_frames * 2)
        
        if len(frames1) < 2 or len(frames2) < 2:
            logger.error("帧数不足，无法进行光流分析")
            return 0.0
        
        # 计算连续帧之间的光流
        flow_consistency_scores = []
        
        # 创建光流计算器
        flow_calculator = cv2.optflow.createOptFlow_DualTVL1()
        
        # 分析连续帧之间的光流
        for i in range(min(len(frames1) - 1, len(frames2) - 1, max_frames)):
            # 准备第一个视频的帧
            prev_frame1 = cv2.cvtColor(frames1[i], cv2.COLOR_BGR2GRAY)
            curr_frame1 = cv2.cvtColor(frames1[i + 1], cv2.COLOR_BGR2GRAY)
            
            # 计算第一个视频的光流
            flow1 = flow_calculator.calc(prev_frame1, curr_frame1, None)
            
            # 准备第二个视频的帧
            prev_frame2 = cv2.cvtColor(frames2[i], cv2.COLOR_BGR2GRAY)
            curr_frame2 = cv2.cvtColor(frames2[i + 1], cv2.COLOR_BGR2GRAY)
            
            # 计算第二个视频的光流
            flow2 = flow_calculator.calc(prev_frame2, curr_frame2, None)
            
            # 计算光流相似度
            flow_diff = np.abs(flow1 - flow2)
            flow_magnitude = np.maximum(np.sqrt(flow1[..., 0]**2 + flow1[..., 1]**2), 
                                       np.sqrt(flow2[..., 0]**2 + flow2[..., 1]**2))
            flow_magnitude = np.maximum(flow_magnitude, 0.1)  # 避免除以零
            
            # 计算归一化差异
            normalized_diff = flow_diff[..., 0] / flow_magnitude + flow_diff[..., 1] / flow_magnitude
            consistency = 1.0 - np.mean(normalized_diff) / 2.0  # 范围[0,1]
            
            flow_consistency_scores.append(consistency)
        
        # 如果没有计算出任何得分
        if not flow_consistency_scores:
            return 0.0
            
        # 返回平均一致性得分
        return np.mean(flow_consistency_scores)
        
    except Exception as e:
        logger.error(f"光流分析失败: {str(e)}")
        return 0.0


def audio_quality_metrics(audio1_path: str, audio2_path: str) -> Dict[str, float]:
    """计算两个音频文件之间的质量指标

    Args:
        audio1_path: 第一个音频的路径
        audio2_path: 第二个音频的路径

    Returns:
        Dict[str, float]: 包含各项音频质量指标的字典
    """
    if not LIBROSA_AVAILABLE:
        logger.error("未安装librosa，无法进行音频质量评估")
        return {"error": "未安装librosa"}
    
    try:
        # 从视频中提取音频，如果是视频文件
        if audio1_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            if not CV2_AVAILABLE:
                logger.error("未安装OpenCV，无法从视频中提取音频")
                return {"error": "未安装OpenCV"}
            
            # 提取音频
            audio1_path = _extract_audio_from_video(audio1_path)
            audio2_path = _extract_audio_from_video(audio2_path)
        
        # 加载音频
        y1, sr1 = librosa.load(audio1_path, sr=None)
        y2, sr2 = librosa.load(audio2_path, sr=None)
        
        # 如果采样率不同，重采样
        if sr1 != sr2:
            y2 = librosa.resample(y2, orig_sr=sr2, target_sr=sr1)
        
        # 确保长度一致
        min_len = min(len(y1), len(y2))
        y1 = y1[:min_len]
        y2 = y2[:min_len]
        
        # 计算均方误差
        mse = np.mean((y1 - y2) ** 2)
        
        # 计算峰值信噪比
        if mse == 0:
            psnr = 100
        else:
            psnr = 10 * np.log10(1.0 / mse)
        
        # 计算音频特征
        # 提取MFCC特征
        mfcc1 = librosa.feature.mfcc(y=y1, sr=sr1, n_mfcc=20)
        mfcc2 = librosa.feature.mfcc(y=y2, sr=sr1, n_mfcc=20)
        
        # 计算MFCC相似度
        mfcc_similarity = 1.0 - np.mean(np.abs(mfcc1 - mfcc2)) / np.mean(np.abs(mfcc1) + np.abs(mfcc2))
        
        # 计算频谱对比度
        spec1 = np.abs(librosa.stft(y1))
        spec2 = np.abs(librosa.stft(y2))
        spec_contrast = 1.0 - np.mean(np.abs(spec1 - spec2)) / np.mean(spec1 + spec2)
        
        return {
            "audio_mse": float(mse),
            "audio_psnr": float(psnr),
            "mfcc_similarity": float(mfcc_similarity),
            "spectral_contrast": float(spec_contrast)
        }
        
    except Exception as e:
        logger.error(f"音频质量评估失败: {str(e)}")
        return {"error": str(e)}


def _extract_audio_from_video(video_path: str) -> str:
    """从视频中提取音频

    Args:
        video_path: 视频文件路径

    Returns:
        str: 临时音频文件路径
    """
    # 创建临时文件
    temp_audio_path = f"{video_path}_temp_audio.wav"
    
    try:
        import subprocess
        # 使用FFmpeg提取音频
        cmd = [
            "ffmpeg", "-i", video_path, 
            "-q:a", "0", "-map", "a", 
            "-y", temp_audio_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return temp_audio_path
    except Exception as e:
        logger.error(f"从视频提取音频失败: {str(e)}")
        return ""


def scene_transition_quality(video1_path: str, video2_path: str) -> Dict[str, float]:
    """评估场景转换质量

    分析两个视频中的场景转换点，评估转换的流畅度和一致性

    Args:
        video1_path: 第一个视频的路径
        video2_path: 第二个视频的路径

    Returns:
        Dict[str, float]: 场景转换质量指标
    """
    if not CV2_AVAILABLE:
        logger.error("未安装OpenCV，无法进行场景转换分析")
        return {"error": "未安装OpenCV"}
    
    try:
        # 检测场景变化
        scene_changes1 = _detect_scene_changes(video1_path)
        scene_changes2 = _detect_scene_changes(video2_path)
        
        if not scene_changes1 or not scene_changes2:
            logger.warning("无法检测到场景变化")
            return {
                "scene_count_similarity": 0.0,
                "transition_timing_similarity": 0.0,
                "overall_transition_quality": 0.0
            }
        
        # 计算场景数量相似度
        count_ratio = min(len(scene_changes1), len(scene_changes2)) / max(len(scene_changes1), len(scene_changes2))
        
        # 计算场景转换时机的相似度
        # 将场景变化点归一化到[0,1]区间
        duration1 = _get_video_duration(video1_path)
        duration2 = _get_video_duration(video2_path)
        
        if duration1 <= 0 or duration2 <= 0:
            logger.error("无效的视频时长")
            return {
                "scene_count_similarity": count_ratio,
                "transition_timing_similarity": 0.0,
                "overall_transition_quality": count_ratio * 0.5
            }
        
        normalized_changes1 = [t / duration1 for t in scene_changes1]
        normalized_changes2 = [t / duration2 for t in scene_changes2]
        
        # 计算最小编辑距离
        timing_similarity = 1.0 - _scene_timing_distance(normalized_changes1, normalized_changes2)
        
        # 综合评分
        overall_quality = count_ratio * 0.5 + timing_similarity * 0.5
        
        return {
            "scene_count_similarity": float(count_ratio),
            "transition_timing_similarity": float(timing_similarity),
            "overall_transition_quality": float(overall_quality)
        }
        
    except Exception as e:
        logger.error(f"场景转换质量评估失败: {str(e)}")
        return {"error": str(e)}


def _detect_scene_changes(video_path: str, threshold: float = 30.0) -> List[float]:
    """检测视频中的场景变化时间点

    Args:
        video_path: 视频文件路径
        threshold: 场景变化阈值

    Returns:
        List[float]: 场景变化的时间点列表(秒)
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logger.error(f"无法打开视频文件: {video_path}")
        return []
    
    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if fps <= 0:
        logger.error(f"无效的视频帧率: {fps}")
        return []
    
    # 读取第一帧
    ret, prev_frame = cap.read()
    if not ret:
        logger.error("无法读取视频帧")
        return []
    
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    scene_changes = []
    frame_count = 1
    
    while True:
        ret, curr_frame = cap.read()
        if not ret:
            break
        
        # 转换为灰度图
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # 计算帧差异
        frame_diff = cv2.absdiff(curr_gray, prev_gray)
        mean_diff = np.mean(frame_diff)
        
        # 如果差异超过阈值，认为是场景变化
        if mean_diff > threshold:
            time_point = frame_count / fps
            scene_changes.append(time_point)
        
        # 更新前一帧
        prev_gray = curr_gray
        frame_count += 1
    
    cap.release()
    return scene_changes


def _get_video_duration(video_path: str) -> float:
    """获取视频时长

    Args:
        video_path: 视频文件路径

    Returns:
        float: 视频时长(秒)
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logger.error(f"无法打开视频文件: {video_path}")
        return 0.0
    
    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps <= 0 or frame_count <= 0:
        logger.error(f"无效的视频参数: fps={fps}, frame_count={frame_count}")
        return 0.0
    
    duration = frame_count / fps
    cap.release()
    return duration


def _scene_timing_distance(times1: List[float], times2: List[float]) -> float:
    """计算两组场景时间点之间的归一化距离

    Args:
        times1: 第一组时间点(归一化到[0,1])
        times2: 第二组时间点(归一化到[0,1])

    Returns:
        float: 归一化距离，范围[0,1]
    """
    # 特殊情况处理
    if not times1 and not times2:
        return 0.0
    if not times1 or not times2:
        return 1.0
    
    # 计算两组时间点之间的最小匹配距离
    total_dist = 0.0
    
    # 对于第一组中的每个点，找到第二组中最近的点
    for t1 in times1:
        min_dist = min(abs(t1 - t2) for t2 in times2)
        total_dist += min_dist
    
    # 反向再算一次，确保双向距离
    for t2 in times2:
        min_dist = min(abs(t2 - t1) for t1 in times1)
        total_dist += min_dist
    
    # 归一化距离
    normalized_dist = total_dist / (len(times1) + len(times2))
    
    # 限制在[0,1]范围内
    return min(1.0, normalized_dist)


def extract_video_features(video_path: str) -> Dict[str, Any]:
    """从视频中提取质量评分所需的特征
    
    提取视频的技术特征(如分辨率、码率等)和艺术特征(如色彩、构图等)
    用于多维度质量评分模型

    Args:
        video_path: 视频文件路径
        
    Returns:
        Dict[str, Any]: 特征字典
    """
    logger.info(f"从视频中提取质量特征: {video_path}")
    
    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        return {}
    
    features = {}
    
    try:
        # 使用ffmpeg获取视频技术信息
        import subprocess
        import json
        
        # 获取视频元数据
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"获取视频元数据失败: {result.stderr}")
            return {}
            
        probe_data = json.loads(result.stdout)
        
        # 提取技术特征
        
        # 1. 找到视频流
        video_stream = None
        audio_stream = None
        
        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "video" and not video_stream:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and not audio_stream:
                audio_stream = stream
        
        if not video_stream:
            logger.error("未找到视频流")
            return {}
        
        # 2. 提取分辨率
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        features["resolution"] = [width, height]
        
        # 3. 提取帧率
        fps_str = video_stream.get("r_frame_rate", "30/1")
        try:
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                fps = num / den if den != 0 else 0
            else:
                fps = float(fps_str)
        except:
            fps = 30.0
        
        features["fps"] = fps
        
        # 4. 提取码率
        bitrate = int(probe_data.get("format", {}).get("bit_rate", 0))
        features["bitrate"] = bitrate
        
        # 5. 提取时长
        duration = float(probe_data.get("format", {}).get("duration", 0))
        features["duration"] = duration
        
        # 6. 提取音频质量相关信息
        if audio_stream:
            audio_bitrate = int(audio_stream.get("bit_rate", 0))
            audio_channels = int(audio_stream.get("channels", 0))
            audio_sample_rate = int(audio_stream.get("sample_rate", 0))
            
            # 计算音频质量分数
            audio_quality = 0.5  # 默认中等质量
            
            # 基于音频参数计算质量
            if audio_bitrate > 0:
                # 标准化码率评分，以320kbps为基准
                br_score = min(1.0, audio_bitrate / 320000)
                
                # 声道数评分
                ch_score = min(1.0, audio_channels / 2)
                
                # 采样率评分，以48kHz为基准
                sr_score = min(1.0, audio_sample_rate / 48000)
                
                # 加权计算音频质量
                audio_quality = 0.6 * br_score + 0.2 * ch_score + 0.2 * sr_score
            
            features["audio_quality"] = audio_quality
            features["audio_bitrate"] = audio_bitrate
            features["audio_channels"] = audio_channels
            features["audio_sample_rate"] = audio_sample_rate
        else:
            features["audio_quality"] = 0.0
        
        # 7. 估算VMAF值
        # 通常需要与参考视频比较，这里我们使用分辨率和码率估算
        # 实际应用中应该使用真实VMAF测试
        resolution_factor = min(1.0, (width * height) / (1920 * 1080))
        bitrate_factor = min(1.0, bitrate / 5000000)  # 5Mbps基准
        
        estimated_vmaf = 60 + 40 * (0.7 * resolution_factor + 0.3 * bitrate_factor)
        features["vmaf"] = estimated_vmaf
        
        # 8. 提取艺术特征
        # 艺术特征通常需要更高级的图像分析，这里我们简化实现
        
        # 8.1 色彩分级评分 - 使用颜色直方图分析
        frames = _extract_frames(video_path, 20)  # 取20帧样本
        
        if frames:
            # 颜色直方图分析
            color_scores = []
            
            for frame in frames:
                # 转换为HSV色彩空间
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # 计算色相和饱和度的标准差作为色彩多样性指标
                h_std = np.std(hsv[:, :, 0])
                s_std = np.std(hsv[:, :, 1])
                
                # 归一化
                h_score = min(1.0, h_std / 50)  # 色相差异
                s_score = min(1.0, s_std / 50)  # 饱和度差异
                
                # 色彩平衡性评分
                color_score = 0.5 * h_score + 0.5 * s_score
                color_scores.append(color_score)
            
            features["color_grading"] = np.mean(color_scores) if color_scores else 0.5
        else:
            features["color_grading"] = 0.5
            
        # 8.2 构图评分 - 使用规则分析和边缘检测
        framing_scores = []
        
        if frames:
            for frame in frames:
                # 转为灰度图像
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # 边缘检测
                edges = cv2.Canny(gray, 100, 200)
                edge_ratio = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
                
                # 计算构图得分
                # 1. 对比度分数
                contrast = np.std(gray) / 128
                contrast_score = min(1.0, contrast * 2)
                
                # 2. 边缘复杂度分数
                edge_score = min(1.0, edge_ratio * 10)
                
                # 3. 黄金分割点分析
                h, w = gray.shape
                golden_areas = [
                    gray[int(h*0.382):int(h*0.618), int(w*0.382):int(w*0.618)]
                ]
                
                # 计算主体是否在黄金分割区域
                golden_mean = np.mean([np.std(area) for area in golden_areas])
                whole_mean = np.std(gray)
                
                golden_ratio = golden_mean / whole_mean if whole_mean > 0 else 0.5
                golden_score = min(1.0, golden_ratio)
                
                # 综合评分
                framing_score = 0.3 * contrast_score + 0.3 * edge_score + 0.4 * golden_score
                framing_scores.append(framing_score)
            
            features["framing"] = np.mean(framing_scores) if framing_scores else 0.5
        else:
            features["framing"] = 0.5
        
        # 8.3 节奏控制评分 - 基于场景切换频率
        scene_changes = _detect_scene_changes(video_path)
        
        if scene_changes and duration > 0:
            # 场景变化频率
            change_frequency = len(scene_changes) / duration
            
            # 5-10秒一个场景为适中节奏
            if change_frequency == 0:
                pacing_score = 0.3  # 节奏过慢
            elif change_frequency < 0.05:  # 每20秒以上一个场景
                pacing_score = 0.4  # 节奏较慢
            elif change_frequency < 0.1:  # 每10-20秒一个场景
                pacing_score = 0.6  # 节奏适中偏慢
            elif change_frequency < 0.2:  # 每5-10秒一个场景
                pacing_score = 0.9  # 节奏适中
            elif change_frequency < 0.5:  # 每2-5秒一个场景
                pacing_score = 0.8  # 节奏适中偏快
            elif change_frequency < 1.0:  # 每1-2秒一个场景
                pacing_score = 0.7  # 节奏较快
            else:  # 每秒以上一个场景
                pacing_score = 0.5  # 节奏过快
                
            features["pacing"] = pacing_score
        else:
            features["pacing"] = 0.5
        
        # 8.4 场景流畅度评分
        if len(scene_changes) >= 2 and duration > 0:
            # 计算场景间隔的一致性
            intervals = []
            for i in range(1, len(scene_changes)):
                intervals.append(scene_changes[i] - scene_changes[i-1])
            
            # 间隔一致性 - 使用变异系数
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            # 变异系数，越小越一致
            cv = std_interval / mean_interval if mean_interval > 0 else 1.0
            
            # 转换为分数，变异系数越小，分数越高
            scene_flow_score = max(0, 1.0 - min(cv, 1.0))
            features["scene_flow"] = scene_flow_score
        else:
            features["scene_flow"] = 0.5
        
        logger.info(f"成功提取视频特征: {video_path}")
        return features
        
    except Exception as e:
        logger.error(f"提取视频特征失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # 返回默认值
        return {
            "resolution": [1280, 720],
            "fps": 30.0,
            "bitrate": 2000000,
            "duration": 60.0,
            "audio_quality": 0.5,
            "vmaf": 75.0,
            "color_grading": 0.5,
            "framing": 0.5,
            "pacing": 0.5,
            "scene_flow": 0.5
        } 