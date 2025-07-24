#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪辑生成器模块 - 负责根据生成的字幕自动剪辑视频
对原视频进行切割、拼接，生成最终的混剪视频
支持低配置设备下的高效视频处理
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
from src.utils.memory_guard import track_memory

# 配置日志
logger = get_logger("clip_generator")

# 配置目录路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs")
CLIP_CONFIG_PATH = os.path.join(CONFIG_DIR, "clip_settings.json")

class ClipGenerator:
    """
    剪辑生成器 - 根据字幕时间码自动切割原视频并拼接
    用于生成最终的混剪视频成品，支持低配置设备下的高效视频处理
    """

    def __init__(self):
        """初始化剪辑生成器"""
        # 加载配置
        self.config = self._load_config()

        # 创建临时目录
        self.temp_dir = os.path.join(tempfile.gettempdir(), "visionai_clips")
        os.makedirs(self.temp_dir, exist_ok=True)

        # 记录处理的历史
        self.processing_history = []

        # 检查FFmpeg可用性
        self._check_ffmpeg()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载剪辑相关配置"""
        try:
            if os.path.exists(CLIP_CONFIG_PATH):
                with open(CLIP_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 默认配置
            return {
                'video_settings': {
                    'codec': 'libx264',
                    'crf': 23,
                    'preset': 'medium',
                    'resolution': None,  # 保持原分辨率
                },
                'audio_settings': {
                    'codec': 'aac',
                    'bitrate': '128k',
                },
                'performance': {
                    'threads': 0,  # 0表示自动
                    'max_memory': '1024M',
                    'segment_limit': 50,  # 每次处理的最大片段数
                },
                'output': {
                    'format': 'mp4',
                    'keep_temp_files': False,
                }
            }
            
        except Exception as e:
            logger.error(f"加载剪辑配置失败: {str(e)}")
            # 返回默认配置
            return {
                'video_settings': {'codec': 'libx264', 'crf': 23, 'preset': 'medium'},
                'audio_settings': {'codec': 'aac', 'bitrate': '128k'},
                'performance': {'threads': 0, 'max_memory': '1024M', 'segment_limit': 50},
                'output': {'format': 'mp4', 'keep_temp_files': False}
            }
    
    def _check_ffmpeg(self) -> None:
        """检查FFmpeg是否可用"""
        try:
            # 首先检查项目内置的FFmpeg
            project_root = Path(__file__).resolve().parent.parent.parent
            ffmpeg_paths = [
                project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",  # Windows
                project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg",      # Linux/Mac
                "ffmpeg"  # 系统PATH中的FFmpeg
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
            self.ffmpeg_path = "ffmpeg"  # 返回默认值，让后续调用时报错
            
        except Exception as e:
            logger.error(f"检测FFmpeg失败: {str(e)}")
            logger.warning("FFmpeg可能未安装，视频处理功能将无法使用")
            self.ffmpeg_path = "ffmpeg"
    
    # @track_memory("video_processing")  # 暂时注释装饰器
    def generate_clips(self, video_path: str, subtitle_segments: List[Dict[str, Any]],
                       output_path: str, quality_check: bool = True) -> Dict[str, Any]:
        """
        生成混剪视频
        
        参数:
            video_path: 原视频文件路径
            subtitle_segments: 字幕片段列表(包含时间码)
            output_path: 输出视频路径
            quality_check: 是否启用质量检查
            
        返回:
            处理结果信息
        """
        start_time = time.time()
        process_id = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_dir = os.path.join(self.temp_dir, process_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 记录处理开始
            logger.info(f"开始处理视频 ID: {process_id}, 视频: {video_path}, 片段数: {len(subtitle_segments)}")
            
            # 处理视频片段
            result = self._process_segments(video_path, subtitle_segments, output_path, temp_dir, {})
            
            processing_time = time.time() - start_time
            
            # 记录处理历史
            self.processing_history.append({
                'process_id': process_id,
                'timestamp': datetime.now().isoformat(),
                'video': os.path.basename(video_path),
                'segments_count': len(subtitle_segments),
                'output': os.path.basename(output_path),
                'processing_time': processing_time
            })
            
            # 清理临时文件
            if not self.config['output'].get('keep_temp_files', False):
                self._clean_temp_files(temp_dir)
            
            result = {
                'status': 'success',
                'process_id': process_id,
                'output_path': output_path,
                'segments_count': len(subtitle_segments),
                'processing_time': processing_time
            }
            
            return result
            
        except Exception as e:
            logger.error(f"处理视频时出错: {str(e)}")
            return {
                'status': 'error',
                'process_id': process_id,
                'error': str(e)
            }
            
        finally:
            # 确保临时目录被清理
            if not self.config['output'].get('keep_temp_files', False):
                self._clean_temp_files(temp_dir)
    
    def _process_segments(self, video_path: str, segments: List[Dict[str, Any]], 
                         output_path: str, temp_dir: str, 
                         video_info: Dict[str, Any]) -> Dict[str, Any]:
        """处理视频片段，切割并拼接"""
        segment_files = []
        
        try:
            # 切割视频片段
            for i, segment in enumerate(segments):
                start_time = segment.get('start', '00:00:00,000')
                end_time = segment.get('end', '00:00:02,000')
                
                # 转换时间格式
                start_seconds = self._time_to_seconds(start_time)
                end_seconds = self._time_to_seconds(end_time)
                duration = end_seconds - start_seconds
                
                if duration <= 0:
                    logger.warning(f"片段 {i} 持续时间无效: {duration}秒")
                    continue
                
                # 生成输出文件名
                segment_file = os.path.join(temp_dir, f"segment_{i:03d}.mp4")
                
                # 切割片段
                if self._cut_segment(video_path, segment_file, start_seconds, duration):
                    segment_files.append(segment_file)
                    logger.debug(f"成功切割片段 {i}: {segment_file}")
                else:
                    logger.error(f"切割片段 {i} 失败")
            
            # 如果没有有效片段，返回错误
            if not segment_files:
                return {
                    'status': 'error',
                    'error': "没有有效的视频片段可处理"
                }
            
            # 拼接视频
            success = self._concat_videos(segment_files, output_path)
            
            if success:
                return {
                    'status': 'success',
                    'segments_processed': len(segment_files)
                }
            else:
                return {
                    'status': 'error',
                    'error': "拼接视频失败"
                }
                
        except Exception as e:
            logger.error(f"处理视频片段时发生错误: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _time_to_seconds(self, time_str: str) -> float:
        """将时间字符串转换为秒数"""
        try:
            # 支持格式: "00:00:10,500" 或 "00:00:10.500"
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
                '-c', 'copy',  # 使用复制模式，避免重新编码
                '-avoid_negative_ts', 'make_zero',
                '-y',  # 覆盖输出文件
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
            # 创建文件列表
            list_file_path = os.path.join(self.temp_dir, "filelist.txt")

            with open(list_file_path, 'w', encoding='utf-8') as f:
                for file_path in input_files:
                    # FFmpeg concat需要转义路径
                    escaped_path = file_path.replace("\\", "/").replace("'", "\\'")
                    f.write(f"file '{escaped_path}'\n")

            # 拼接视频
            return self._concat_videos_from_list(list_file_path, output_path)

        except Exception as e:
            logger.error(f"拼接视频时发生错误: {str(e)}")
            return False

        finally:
            # 清理临时文件列表
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
                '-c', 'copy',  # 使用复制模式，避免重新编码
                '-y',  # 覆盖输出文件
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
                # 删除目录中的所有文件
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {file_path}, 错误: {str(e)}")

                # 删除目录
                os.rmdir(temp_dir)

                logger.debug(f"清理临时目录: {temp_dir}")

        except Exception as e:
            logger.warning(f"清理临时文件夹失败: {str(e)}")

    def generate_from_srt(self, video_path: str, srt_path: str, output_path: str) -> Dict[str, Any]:
        """
        根据SRT字幕文件生成混剪视频

        参数:
            video_path: 原视频文件路径
            srt_path: SRT字幕文件路径
            output_path: 输出视频路径

        返回:
            处理结果信息
        """
        try:
            # 导入SRT
            subtitle_segments = import_srt(srt_path)

            if not subtitle_segments:
                return {
                    'status': 'error',
                    'error': f"SRT文件导入失败或为空: {srt_path}"
                }

            # 生成视频
            return self.generate_clips(video_path, subtitle_segments, output_path)

        except Exception as e:
            logger.error(f"通过SRT生成视频失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def extract_segments(self, video_path: str, segments: List[Dict[str, Any]]) -> List[str]:
        """
        从视频中提取指定片段

        参数:
            video_path: 原视频文件路径
            segments: 片段列表，每个片段包含start和end时间

        返回:
            提取的片段文件路径列表
        """
        try:
            extracted_files = []

            for i, segment in enumerate(segments):
                start_time = segment.get("start", "00:00:00,000")
                end_time = segment.get("end", "00:00:02,000")

                # 转换时间格式
                start_seconds = self._time_to_seconds(start_time)
                end_seconds = self._time_to_seconds(end_time)
                duration = end_seconds - start_seconds

                if duration <= 0:
                    logger.warning(f"片段 {i} 持续时间无效: {duration}秒")
                    continue

                # 生成输出文件名
                output_file = os.path.join(self.temp_dir, f"segment_{i:03d}.mp4")

                # 使用FFmpeg提取片段
                if self._cut_segment(video_path, output_file, start_seconds, duration):
                    extracted_files.append(output_file)
                    logger.debug(f"成功提取片段 {i}: {output_file}")
                else:
                    logger.error(f"提取片段 {i} 失败")

            logger.info(f"成功提取 {len(extracted_files)} 个片段")
            return extracted_files

        except Exception as e:
            logger.error(f"提取片段失败: {e}")
            return []

    def concatenate_segments(self, segments: List[Dict[str, Any]], output_path: str) -> bool:
        """
        拼接视频片段

        参数:
            segments: 片段列表，每个片段包含source文件路径
            output_path: 输出视频文件路径

        返回:
            是否成功拼接
        """
        try:
            if not segments:
                logger.error("没有片段可供拼接")
                return False

            # 创建输出目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 如果只有一个片段，直接复制
            if len(segments) == 1:
                source_file = segments[0].get("source", segments[0].get("file"))
                if source_file and os.path.exists(source_file):
                    shutil.copy2(source_file, output_path)
                    logger.info(f"单片段复制完成: {output_path}")
                    return True
                else:
                    logger.error(f"源文件不存在: {source_file}")
                    return False

            # 多个片段需要拼接
            # 创建文件列表
            filelist_path = os.path.join(self.temp_dir, "filelist.txt")

            with open(filelist_path, 'w', encoding='utf-8') as f:
                for segment in segments:
                    source_file = segment.get("source", segment.get("file"))
                    if source_file and os.path.exists(source_file):
                        # FFmpeg concat需要转义路径
                        escaped_path = source_file.replace("\\", "/").replace("'", "\\'")
                        f.write(f"file '{escaped_path}'\n")
                    else:
                        logger.warning(f"跳过不存在的文件: {source_file}")

            # 使用FFmpeg concat协议拼接
            success = self._concat_videos_from_list(filelist_path, output_path)

            # 清理临时文件
            if os.path.exists(filelist_path):
                os.remove(filelist_path)

            if success:
                logger.info(f"视频拼接成功: {output_path}")
                return True
            else:
                logger.error("视频拼接失败")
                return False

        except Exception as e:
            logger.error(f"拼接片段失败: {e}")
            return False

    def export_jianying_project(self, segments: List[Dict[str, Any]], video_path: str,
                                output_path: str) -> bool:
        """
        导出剪映工程文件

        参数:
            segments: 字幕片段列表
            video_path: 原视频文件路径
            output_path: 输出工程文件路径

        返回:
            是否成功导出
        """
        # 此功能需要单独实现，将在另一个模块中完成
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


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    # 示例：从SRT文件生成视频
    test_video = "../data/input/videos/test.mp4"
    test_srt = "../data/input/subtitles/test.srt"

    if os.path.exists(test_video) and os.path.exists(test_srt):
        output_path = "../data/output/final_videos/test_output.mp4"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        result = generate_from_srt(test_video, test_srt, output_path)

        if result['status'] == 'success':
            print(f"混剪视频生成成功: {output_path}")
            print(f"时长: {result.get('duration', 0):.2f}秒, 处理时间: {result['processing_time']:.2f}秒")
