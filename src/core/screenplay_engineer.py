#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剧本工程师模块 - 简化版（UI演示用）

提供剧本重构、优化和转换功能，支持将原始素材整合为高质量剧本。
该模块是核心处理引擎，负责协调各种分析工具和生成策略。
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

# 获取日志记录器
logger = logging.getLogger(__name__)

class ScreenplayEngineer:
    """
    剧本工程师 - 简化版（UI演示用）
    """
    
    def __init__(self):
        """初始化剧本工程师"""
        # 记录处理的历史
        self.processing_history = []
        
    def generate_screenplay(self, original_subtitles: List[Dict[str, Any]], 
                           language: str = "auto",
                           preset_name: Optional[str] = None,
                           custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成新的混剪剧本 - 简化版（UI演示用）
        
        参数:
            original_subtitles: 原始字幕列表
            language: 语言代码或"auto"自动检测
            preset_name: 预设参数名称（如"快节奏"、"情感化"）
            custom_params: 自定义参数
            
        返回:
            包含新剧本和元数据的字典
        """
        start_time = time.time()
        process_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        try:
            # 简化版: 直接使用原始字幕，添加情感标签
            screenplay = []
            
            for i, segment in enumerate(original_subtitles):
                # 原始字幕已经有情感标签则保留，否则添加模拟情感标签
                if not segment.get("sentiment"):
                    # 模拟情感标签 (交替添加不同的情感)
                    if i % 3 == 0:
                        sentiment = {"label": "NEUTRAL", "intensity": 0.5}
                    elif i % 3 == 1:
                        sentiment = {"label": "POSITIVE", "intensity": 0.7}
                    else:
                        sentiment = {"label": "NEGATIVE", "intensity": 0.6}
                    
                    segment = segment.copy()
                    segment["sentiment"] = sentiment
                
                screenplay.append(segment)
            
            # 计算处理时间
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 返回结果
            result = {
                "process_id": process_id,
                "preset": preset_name or "默认",
                "language": language,
                "total_segments": len(screenplay),
                "processing_time": processing_time,
                "screenplay": screenplay
            }
            
            # 记录处理历史
            self.processing_history.append({
                "id": process_id,
                "timestamp": datetime.now().isoformat(),
                "preset": preset_name,
                "segments_count": len(screenplay)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"生成剧本时出错: {str(e)}")
            # 返回空结果
            return {
                "process_id": process_id,
                "error": str(e),
                "screenplay": original_subtitles
            }
    
    def export_srt(self, segments: List[Dict[str, Any]], output_path: str) -> bool:
        """导出SRT字幕文件 - 简化版（UI演示用）"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments):
                    start_time = segment.get("start_time", 0)
                    end_time = segment.get("end_time", 0)
                    text = segment.get("text", "")
                    
                    # 转换时间格式
                    start_formatted = self._seconds_to_srt_time(start_time)
                    end_formatted = self._seconds_to_srt_time(end_time)
                    
                    # 写入SRT格式
                    f.write(f"{i+1}\n")
                    f.write(f"{start_formatted} --> {end_formatted}\n")
                    f.write(f"{text}\n\n")
                    
            return True
            
        except Exception as e:
            logger.error(f"导出SRT文件失败: {str(e)}")
            return False
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """将秒转换为SRT时间格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        seconds %= 3600
        minutes = int(seconds // 60)
        seconds %= 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"
    
    def import_srt(self, srt_path: str) -> List[Dict[str, Any]]:
        """导入SRT字幕文件 - 简化版（UI演示用）"""
        subtitles = []
        
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析SRT格式
            # 示例：1\n00:00:01,000 --> 00:00:04,000\n这是第一条字幕\n\n2\n...
            pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.+\n)+)(?:\n|$)')
            matches = pattern.findall(content)
            
            for match in matches:
                index, start_time, end_time, text = match
                
                # 转换时间格式
                start_seconds = self._srt_time_to_seconds(start_time)
                end_seconds = self._srt_time_to_seconds(end_time)
                
                # 清理文本
                text = text.strip()
                
                # 添加字幕
                subtitles.append({
                    "id": int(index),
                    "start_time": start_seconds,
                    "end_time": end_seconds,
                    "text": text
                })
            
            return subtitles
            
        except Exception as e:
            logger.error(f"导入SRT文件失败: {str(e)}")
            return []
    
    def _srt_time_to_seconds(self, srt_time: str) -> float:
        """将SRT时间格式 (HH:MM:SS,mmm) 转换为秒"""
        hours, minutes, seconds = srt_time.replace(',', '.').split(':')
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    def process_subtitles(self, subtitles: List[Dict[str, Any]], 
                           language: str = "auto", 
                           params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理字幕生成新剧本 - 支持参数管理器
        
        Args:
            subtitles: 字幕列表
            language: 语言代码或"auto"自动检测
            params: 处理参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 使用参数或默认参数
        if params is None:
            # 尝试导入参数管理器
            try:
                from src.versioning.param_manager import prepare_params
                params = prepare_params(language=language)
            except ImportError:
                # 使用内部默认值
                params = {}
        
        # 使用适当的风格参数
        style = params.get("style", "viral")
        
        # 调用现有的generate_screenplay方法
        return self.generate_screenplay(
            subtitles, 
            language=language,
            preset_name=style,
            custom_params=params
        )

# 便捷函数
def generate_screenplay(subtitles: List[Dict[str, Any]], language: str = 'auto', params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """便捷函数：生成剧本
    
    Args:
        subtitles: 字幕列表
        language: 语言代码或"auto"自动检测
        params: 处理参数
        
    Returns:
        Dict[str, Any]: 处理结果
    """
    engineer = ScreenplayEngineer()
    return engineer.process_subtitles(subtitles, language, params=params)

def export_srt(segments: List[Dict[str, Any]], output_path: str) -> bool:
    """便捷函数：导出SRT"""
    return ScreenplayEngineer().export_srt(segments, output_path)

def import_srt(srt_path: str) -> List[Dict[str, Any]]:
    """便捷函数：导入SRT"""
    return ScreenplayEngineer().import_srt(srt_path)


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    # 示例：从SRT文件导入
    test_srt = "../data/input/subtitles/test.srt"
    if os.path.exists(test_srt):
        subtitles = import_srt(test_srt)
        
        if subtitles:
            # 生成新剧本
            result = generate_screenplay(subtitles, "zh")
            
            # 导出新SRT
            if result['status'] == 'success':
                output_path = "../data/output/generated_srt/test_output.srt"
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                export_srt(result['segments'], output_path)
                
                print(f"生成完成: {len(result['segments'])} 个片段, "
                     f"总时长: {result['total_duration']:.2f}秒")
