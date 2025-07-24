#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪辑生成器模块 - 负责根据生成的字幕自动剪辑视频
"""

import os
import json
import logging
import time
import tempfile
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import glob
from pathlib import Path

# 导入相关模块
from src.core.screenplay_engineer import import_srt
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("clip_generator")

class ClipGenerator:
    """剪辑生成器"""
    
    def __init__(self):
        """初始化剪辑生成器"""
        self.temp_dir = os.path.join(tempfile.gettempdir(), "visionai_clips")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.processing_history = []
        self._check_ffmpeg()
        
    def _check_ffmpeg(self) -> None:
        """检查FFmpeg是否可用"""
        try:
            project_root = Path(__file__).resolve().parent.parent.parent
            ffmpeg_paths = [
                project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
                project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg",
                "ffmpeg"
            ]
            
            for ffmpeg_path in ffmpeg_paths:
                try:
                    result = subprocess.run([str(ffmpeg_path), "-version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        logger.info(f"找到FFmpeg: {ffmpeg_path}")
                        self.ffmpeg_path = str(ffmpeg_path)
                        return
                except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                    continue
            
            logger.warning("未找到FFmpeg，某些功能可能不可用")
            self.ffmpeg_path = "ffmpeg"
            
        except Exception as e:
            logger.error(f"检测FFmpeg失败: {str(e)}")
            self.ffmpeg_path = "ffmpeg"
    
    def generate_clips(self, video_path: str, subtitle_segments: List[Dict[str, Any]], 
                       output_path: str, quality_check: bool = True) -> Dict[str, Any]:
        """生成混剪视频"""
        start_time = time.time()
        process_id = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_dir = os.path.join(self.temp_dir, process_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            logger.info(f"开始处理视频 ID: {process_id}, 视频: {video_path}, 片段数: {len(subtitle_segments)}")
            
            # 处理视频片段
            result = self._process_segments(video_path, subtitle_segments, output_path, temp_dir, {})
            
            processing_time = time.time() - start_time
            
            self.processing_history.append({
                'process_id': process_id,
                'timestamp': datetime.now().isoformat(),
                'video': os.path.basename(video_path),
                'segments_count': len(subtitle_segments),
                'output': os.path.basename(output_path),
                'processing_time': processing_time
            })
            
            self._clean_temp_files(temp_dir)
            
            return {
                'status': 'success',
                'process_id': process_id,
                'output_path': output_path,
                'segments_count': len(subtitle_segments),
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"处理视频时出错: {str(e)}")
            return {
                'status': 'error',
                'process_id': process_id,
                'error': str(e)
            }
            
        finally:
            self._clean_temp_files(temp_dir)
    
    def _process_segments(self, video_path: str, segments: List[Dict[str, Any]], 
                         output_path: str, temp_dir: str, 
                         video_info: Dict[str, Any]) -> Dict[str, Any]:
        """处理视频片段，切割并拼接"""
        segment_files = []
        
        try:
            for i, segment in enumerate(segments):
                start_time = segment.get('start', '00:00:00,000')
                end_time = segment.get('end', '00:00:02,000')
                
                start_seconds = self._time_to_seconds(start_time)
                end_seconds = self._time_to_seconds(end_time)
                duration = end_seconds - start_seconds
                
                if duration <= 0:
                    logger.warning(f"片段 {i} 持续时间无效: {duration}秒")
                    continue
                
                segment_file = os.path.join(temp_dir, f"segment_{i:03d}.mp4")
                
                if self._cut_segment(video_path, segment_file, start_seconds, duration):
                    segment_files.append(segment_file)
                    logger.debug(f"成功切割片段 {i}: {segment_file}")
                else:
                    logger.error(f"切割片段 {i} 失败")
            
            if not segment_files:
                return {'status': 'error', 'error': "没有有效的视频片段可处理"}
            
            success = self._concat_videos(segment_files, output_path)
            
            if success:
                return {'status': 'success', 'segments_processed': len(segment_files)}
            else:
                return {'status': 'error', 'error': "拼接视频失败"}
                
        except Exception as e:
            logger.error(f"处理视频片段时发生错误: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _time_to_seconds(self, time_str: str) -> float:
        """将时间字符串转换为秒数"""
        try:
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(parts[0])
                
        except Exception as e:
            logger.error(f"时间转换失败: {time_str}, {e}")
            return 0.0
    
    def _cut_segment(self, input_path: str, output_path: str, 
                     start_time: float, duration: float) -> bool:
        """切割视频片段"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return True
            else:
                logger.error(f"切割片段失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"切割视频片段时发生错误: {str(e)}")
            return False
    
    def _concat_videos(self, input_files: List[str], output_path: str) -> bool:
        """拼接视频文件"""
        try:
            list_file_path = os.path.join(self.temp_dir, "filelist.txt")
            
            with open(list_file_path, 'w', encoding='utf-8') as f:
                for file_path in input_files:
                    escaped_path = file_path.replace("\\", "/").replace("'", "\\'")
                    f.write(f"file '{escaped_path}'\n")
            
            return self._concat_videos_from_list(list_file_path, output_path)
            
        except Exception as e:
            logger.error(f"拼接视频时发生错误: {str(e)}")
            return False
            
        finally:
            if os.path.exists(list_file_path):
                os.remove(list_file_path)
    
    def _concat_videos_from_list(self, list_file_path: str, output_path: str) -> bool:
        """从文件列表拼接视频"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file_path,
                '-c', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return True
            else:
                logger.error(f"拼接视频失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"拼接视频时发生错误: {str(e)}")
            return False
    
    def _clean_temp_files(self, temp_dir: str) -> None:
        """清理临时文件"""
        try:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {file_path}, 错误: {str(e)}")
                
                os.rmdir(temp_dir)
                logger.debug(f"清理临时目录: {temp_dir}")
                
        except Exception as e:
            logger.warning(f"清理临时文件夹失败: {str(e)}")
    
    def extract_segments(self, video_path: str, segments: List[Dict[str, Any]]) -> List[str]:
        """从视频中提取指定片段"""
        try:
            extracted_files = []
            for i, segment in enumerate(segments):
                start_time = segment.get("start", "00:00:00,000")
                end_time = segment.get("end", "00:00:02,000")
                start_seconds = self._time_to_seconds(start_time)
                end_seconds = self._time_to_seconds(end_time)
                duration = end_seconds - start_seconds
                if duration <= 0:
                    continue
                output_file = os.path.join(self.temp_dir, f"segment_{i:03d}.mp4")
                if self._cut_segment(video_path, output_file, start_seconds, duration):
                    extracted_files.append(output_file)
            return extracted_files
        except Exception as e:
            logger.error(f"提取片段失败: {e}")
            return []
    
    def concatenate_segments(self, segments: List[Dict[str, Any]], output_path: str) -> bool:
        """拼接视频片段"""
        try:
            if not segments:
                return False
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            if len(segments) == 1:
                source_file = segments[0].get("source", segments[0].get("file"))
                if source_file and os.path.exists(source_file):
                    shutil.copy2(source_file, output_path)
                    return True
                return False
            filelist_path = os.path.join(self.temp_dir, "filelist.txt")
            with open(filelist_path, 'w', encoding='utf-8') as f:
                for segment in segments:
                    source_file = segment.get("source", segment.get("file"))
                    if source_file and os.path.exists(source_file):
                        escaped_path = source_file.replace("\\", "/").replace("'", "\\'")
                        f.write(f"file '{escaped_path}'\n")
            success = self._concat_videos_from_list(filelist_path, output_path)
            if os.path.exists(filelist_path):
                os.remove(filelist_path)
            return success
        except Exception as e:
            logger.error(f"拼接片段失败: {e}")
            return False
    
    def generate_from_srt(self, video_path: str, srt_path: str, output_path: str) -> Dict[str, Any]:
        """根据SRT字幕文件生成混剪视频"""
        try:
            subtitle_segments = import_srt(srt_path)
            if not subtitle_segments:
                return {'status': 'error', 'error': f"SRT文件导入失败或为空: {srt_path}"}
            return self.generate_clips(video_path, subtitle_segments, output_path)
        except Exception as e:
            logger.error(f"通过SRT生成视频失败: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def export_jianying_project(self, segments: List[Dict[str, Any]], video_path: str, 
                                output_path: str) -> bool:
        """导出剪映工程文件"""
        logger.warning("剪映工程导出功能尚未实现")
        return False


# 创建全局单例
clip_generator = ClipGenerator()

def generate_clips(video_path: str, subtitle_segments: List[Dict[str, Any]], 
                  output_path: str) -> Dict[str, Any]:
    """便捷函数，生成混剪视频"""
    return clip_generator.generate_clips(video_path, subtitle_segments, output_path)

def generate_from_srt(video_path: str, srt_path: str, output_path: str) -> Dict[str, Any]:
    """便捷函数，根据SRT字幕文件生成混剪视频"""
    return clip_generator.generate_from_srt(video_path, srt_path, output_path)

def export_jianying_project(segments: List[Dict[str, Any]], video_path: str, 
                           output_path: str) -> bool:
    """便捷函数，导出剪映工程文件"""
    return clip_generator.export_jianying_project(segments, video_path, output_path)
