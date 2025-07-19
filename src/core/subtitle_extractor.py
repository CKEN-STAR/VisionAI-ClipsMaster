#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕提取模块

提供从视频文件中提取嵌入字幕和解析SRT文件的功能。
支持多语言字幕识别和处理。
"""

import os
import re
import subprocess
import chardet
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

# 项目内部导入
from src.utils.log_handler import get_logger
from src.utils.config_manager import get_config

# 配置日志
subtitle_logger = get_logger("subtitle_extractor")

def extract_subtitles(
    video_path: str, 
    output_path: str,
    overwrite: bool = True
) -> Dict[str, Any]:
    """从视频中提取字幕
    
    使用FFmpeg提取嵌入式字幕或OCR识别硬字幕。
    
    Args:
        video_path: 视频文件路径
        output_path: 字幕输出路径
        overwrite: 是否覆盖已存在的字幕文件
        
    Returns:
        Dict[str, Any]: 提取结果信息
    """
    subtitle_logger.info(f"正在从视频提取字幕: {video_path}")
    
    # 如果输出文件已存在且不覆盖，直接返回成功
    if os.path.exists(output_path) and not overwrite:
        subtitle_logger.info(f"字幕文件已存在: {output_path}")
        return {
            "success": True,
            "path": output_path,
            "method": "existing",
            "message": "字幕文件已存在"
        }
    
    # 加载配置
    config = get_config("core").get("subtitle_extractor", {})
    ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
    
    # 尝试提取嵌入式字幕
    try:
        # 先检查视频是否包含字幕流
        subtitle_streams = _get_subtitle_streams(video_path, ffmpeg_path)
        
        if subtitle_streams:
            # 存在嵌入式字幕，提取第一个字幕流
            subtitle_stream = subtitle_streams[0]
            stream_index = subtitle_stream["index"]
            
            cmd = [
                ffmpeg_path,
                "-i", video_path,
                "-map", f"0:{stream_index}",
                "-f", "srt",
                output_path,
                "-y"
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            if os.path.exists(output_path):
                subtitle_logger.info(f"成功提取嵌入式字幕: {output_path}")
                return {
                    "success": True,
                    "path": output_path,
                    "method": "embedded",
                    "stream_info": subtitle_stream,
                    "message": "成功提取嵌入式字幕"
                }
        
        # 如果没有嵌入式字幕，尝试硬字幕OCR识别
        if config.get("enable_ocr", False):
            try:
                # 使用OCR提取硬字幕
                ocr_result = _extract_hardcoded_subtitles(video_path, output_path, ffmpeg_path)
                
                if ocr_result["success"]:
                    subtitle_logger.info(f"成功OCR识别硬字幕: {output_path}")
                    return {
                        "success": True,
                        "path": output_path,
                        "method": "ocr",
                        "message": "成功OCR识别硬字幕"
                    }
                else:
                    subtitle_logger.warning(f"OCR识别硬字幕失败: {ocr_result['error']}")
                    return ocr_result
            except Exception as ocr_e:
                subtitle_logger.error(f"OCR识别过程发生错误: {str(ocr_e)}")
                return {
                    "success": False,
                    "error": f"OCR识别失败: {str(ocr_e)}",
                    "message": "OCR识别失败"
                }
        
        # 如果没有嵌入式字幕且OCR未启用或失败，返回失败结果
        subtitle_logger.warning(f"无法从视频中提取字幕: {video_path}")
        return {
            "success": False,
            "error": "视频不包含嵌入式字幕，且OCR提取未启用或失败",
            "message": "无法提取字幕"
        }
            
    except Exception as e:
        subtitle_logger.error(f"字幕提取失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "字幕提取过程发生错误"
        }

def _get_subtitle_streams(video_path: str, ffmpeg_path: str) -> List[Dict[str, Any]]:
    """获取视频中的字幕流信息
    
    Args:
        video_path: 视频文件路径
        ffmpeg_path: FFmpeg路径
        
    Returns:
        List[Dict[str, Any]]: 字幕流信息
    """
    cmd = [
        ffmpeg_path.replace("ffmpeg", "ffprobe"),
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "s",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            import json
            probe_result = json.loads(result.stdout)
            return probe_result.get("streams", [])
        return []
    except Exception as e:
        subtitle_logger.error(f"获取字幕流信息失败: {str(e)}")
        return []

def _extract_hardcoded_subtitles(
    video_path: str, 
    output_path: str, 
    ffmpeg_path: str
) -> Dict[str, Any]:
    """使用OCR提取硬字幕
    
    注意：此功能需要安装额外的OCR工具
    
    Args:
        video_path: 视频文件路径
        output_path: 字幕输出路径
        ffmpeg_path: FFmpeg路径
        
    Returns:
        Dict[str, Any]: OCR提取结果
    """
    subtitle_logger.warning("OCR提取硬字幕功能尚未完全实现")
    return {
        "success": False,
        "error": "OCR提取功能尚未完全实现",
        "message": "OCR功能未实现"
    }
    
    # 此处应实现OCR识别流程
    # 可以使用FFmpeg+Tesseract/PaddleOCR等组合实现
    # 1. 使用FFmpeg定时截取帧图像
    # 2. 对帧图像进行OCR识别
    # 3. 将识别结果组合成SRT格式字幕
    # 由于这是一个复杂功能，暂未实现

def parse_srt(subtitle_path: str) -> List[Dict[str, Any]]:
    """解析SRT字幕文件
    
    Args:
        subtitle_path: SRT文件路径
        
    Returns:
        List[Dict[str, Any]]: 解析后的字幕列表
    """
    subtitle_logger.debug(f"解析SRT文件: {subtitle_path}")
    
    if not os.path.exists(subtitle_path):
        subtitle_logger.error(f"字幕文件不存在: {subtitle_path}")
        return []
    
    try:
        # 先检测文件编码
        with open(subtitle_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
        
        # 读取文件内容
        with open(subtitle_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        # 正则表达式匹配SRT格式
        # 格式: 序号 + 时间码 (00:00:00,000 --> 00:00:00,000) + 文本
        pattern = r'(\d+)\s*\n\s*(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n([\s\S]*?)(?=\n\s*\d+\s*\n|\Z)'
        matches = re.findall(pattern, content)
        
        subtitles = []
        for match in matches:
            index = int(match[0])
            start_time = _time_to_seconds(match[1])
            end_time = _time_to_seconds(match[2])
            text = match[3].strip()
            
            subtitles.append({
                "index": index,
                "start": start_time,
                "end": end_time,
                "duration": end_time - start_time,
                "text": text
            })
        
        subtitle_logger.debug(f"成功解析 {len(subtitles)} 条字幕")
        return subtitles
        
    except Exception as e:
        subtitle_logger.error(f"解析SRT文件失败: {str(e)}")
        return []

def _time_to_seconds(time_str: str) -> float:
    """将SRT时间格式转换为秒
    
    Args:
        time_str: 时间字符串，格式 hh:mm:ss,ms
        
    Returns:
        float: 时间，单位秒
    """
    try:
        # 处理不同格式的分隔符
        if ',' in time_str:
            parts = time_str.replace(',', ':').split(':')
        else:
            parts = time_str.replace('.', ':').split(':')
        
        # 确保有足够的部分
        if len(parts) < 4:
            return 0.0
            
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        milliseconds = int(parts[3])
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        return total_seconds
        
    except Exception as e:
        subtitle_logger.error(f"时间转换错误 {time_str}: {str(e)}")
        return 0.0

def write_srt(subtitles: List[Dict[str, Any]], output_path: str) -> bool:
    """将字幕数据写入SRT文件
    
    Args:
        subtitles: 字幕数据列表
        output_path: 输出文件路径
        
    Returns:
        bool: 是否成功写入
    """
    subtitle_logger.debug(f"写入SRT文件: {output_path}")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(subtitles, 1):
                start_time_str = _seconds_to_time(subtitle["start"])
                end_time_str = _seconds_to_time(subtitle["end"])
                text = subtitle["text"]
                
                f.write(f"{i}\n")
                f.write(f"{start_time_str} --> {end_time_str}\n")
                f.write(f"{text}\n\n")
        
        subtitle_logger.info(f"成功写入 {len(subtitles)} 条字幕到文件: {output_path}")
        return True
        
    except Exception as e:
        subtitle_logger.error(f"写入SRT文件失败: {str(e)}")
        return False

def _seconds_to_time(seconds: float) -> str:
    """将秒转换为SRT时间格式
    
    Args:
        seconds: 时间，单位秒
        
    Returns:
        str: 时间字符串，格式 hh:mm:ss,ms
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_part = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d},{milliseconds:03d}"

def merge_subtitles(
    subtitles: List[Dict[str, Any]], 
    max_gap: float = 1.0
) -> List[Dict[str, Any]]:
    """合并相近的字幕条目
    
    Args:
        subtitles: 字幕列表
        max_gap: 最大时间间隔，单位秒
        
    Returns:
        List[Dict[str, Any]]: 合并后的字幕列表
    """
    if not subtitles:
        return []
    
    # 按开始时间排序
    sorted_subtitles = sorted(subtitles, key=lambda x: x["start"])
    
    merged = []
    current = sorted_subtitles[0].copy()
    
    for next_sub in sorted_subtitles[1:]:
        # 如果两个字幕时间间隔小于阈值，合并
        if next_sub["start"] - current["end"] <= max_gap:
            # 更新结束时间
            current["end"] = next_sub["end"]
            # 合并文本
            current["text"] += " " + next_sub["text"]
            # 更新持续时间
            current["duration"] = current["end"] - current["start"]
        else:
            # 添加当前字幕到结果中
            merged.append(current)
            # 开始新的字幕
            current = next_sub.copy()
    
    # 添加最后一个字幕
    merged.append(current)
    
    return merged 