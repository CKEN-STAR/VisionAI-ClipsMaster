#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪辑生成器模块 - 负责根据生成的字幕自动剪辑视频
对原视频进行切割、拼接，生成最终的混剪视频
支持低配置设备下的高效视频处理
"""

import os
import json
import yaml
import logging
import time
import tempfile
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import glob

# 导入相关模块
from src.core.screenplay_engineer import import_srt
from src.utils.log_handler import get_logger
from src.utils.memory_guard import track_memory
from src.quality.quality_controller import QualityController
from src.core.exceptions import QualityCheckError

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
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                logger.info("FFmpeg可用")
                # 提取版本信息
                version_line = result.stdout.split('\n')[0]
                logger.debug(f"FFmpeg版本: {version_line}")
            else:
                logger.warning("FFmpeg命令返回非零状态，可能无法正常使用")
        except Exception as e:
            logger.error(f"检测FFmpeg失败: {str(e)}")
            logger.warning("FFmpeg可能未安装，视频处理功能将无法使用")
    
    @track_memory("video_processing")
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
            
            # 初始化质量控制器（如果启用质量检查）
            quality_controller = None
            if quality_check:
                try:
                    quality_controller = QualityController()
                    logger.info("质量检查已启用")
                except Exception as e:
                    logger.warning(f"初始化质量控制器失败: {str(e)}")
                    logger.warning("质量检查将被禁用")
                    quality_check = False

            # 检查视频是否存在
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
                
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 获取视频信息
            video_info = self._get_video_info(video_path)
            logger.info(f"视频信息: 时长={video_info.get('duration', 0)}秒, "
                       f"分辨率={video_info.get('width', 0)}x{video_info.get('height', 0)}")
            
            # 如果片段过多，分批处理
            segment_limit = self.config['performance'].get('segment_limit', 50)
            if len(subtitle_segments) > segment_limit:
                logger.info(f"片段数量({len(subtitle_segments)})超过限制({segment_limit})，将分批处理")
                batch_results = []
                
                # 分批处理
                for i in range(0, len(subtitle_segments), segment_limit):
                    batch = subtitle_segments[i:i+segment_limit]
                    batch_output = os.path.join(temp_dir, f"batch_{i//segment_limit}.mp4")
                    
                    batch_result = self._process_segments(
                        video_path, batch, batch_output, temp_dir, video_info
                    )
                    
                    if batch_result.get('status') == 'success':
                        batch_results.append(batch_output)
                    else:
                        raise Exception(f"处理批次 {i//segment_limit} 失败: {batch_result.get('error')}")
                
                # 合并批次结果
                self._concat_videos(batch_results, output_path)
                
            else:
                # 直接处理所有片段
                result = self._process_segments(
                    video_path, subtitle_segments, output_path, temp_dir, video_info
                )
                
                if result.get('status') != 'success':
                    raise Exception(f"处理视频片段失败: {result.get('error')}")
            
            # 添加字幕（如果需要）
            # 此处可以添加为视频嵌入字幕的代码
            
            # 处理完成
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
            
            # 执行质量检查（如果启用）
            if quality_check and quality_controller:
                logger.info("开始视频质量评估")
                quality_result = quality_controller.process_video(
                    output_path, 
                    subtitle_segments,
                    generate_report=True
                )
                
                if quality_result.get('success', False):
                    # 添加质量信息到结果
                    result['quality'] = quality_result.get('quality', {})
                    result['quality_reports'] = quality_result.get('reports', {})
                    
                    # 添加质量建议
                    recommendations = quality_result.get('recommendations', [])
                    if recommendations:
                        result['recommendations'] = recommendations
                        logger.info(f"质量建议: {', '.join(recommendations)}")
                else:
                    logger.warning(f"质量检查失败: {quality_result.get('error', '未知错误')}")
            
            return result
            
        except QualityCheckError as qce:
            # 质量检查错误单独处理
            logger.error(f"质量检查错误: {str(qce)}")
            return {
                'status': 'quality_error',
                'process_id': process_id,
                'error': str(qce),
                'details': qce.details if hasattr(qce, 'details') else {},
                'output_path': output_path
            }
        except Exception as e:
            # 其他错误继续使用原有错误处理
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
            # 检查每个片段
            valid_segments = []
            for segment in segments:
                # 获取时间信息（优先使用original_time）
                if 'original_time' in segment:
                    start_time = segment['original_time'].get('start', 0)
                    end_time = segment['original_time'].get('end', 0)
                else:
                    start_time = segment.get('time', {}).get('start', 0)
                    end_time = segment.get('time', {}).get('end', 0)
                
                # 确保时间有效
                if start_time >= end_time or start_time < 0:
                    logger.warning(f"忽略无效时间的片段: {start_time}-{end_time}")
                    continue
                    
                # 确保不超过视频总时长
                video_duration = video_info.get('duration', 0)
                if start_time >= video_duration:
                    logger.warning(f"忽略超出视频时长的片段: {start_time}-{end_time}, 视频时长: {video_duration}")
                    continue
                    
                # 如果结束时间超出视频，截断到视频结束
                if end_time > video_duration:
                    logger.warning(f"片段结束时间超出视频时长，将截断: {end_time} -> {video_duration}")
                    end_time = video_duration
                
                valid_segments.append({
                    'segment': segment,
                    'start': start_time,
                    'end': end_time
                })
            
            # 切割每个有效片段
            for i, item in enumerate(valid_segments):
                segment = item['segment']
                start_time = item['start']
                end_time = item['end']
                
                # 计算时长
                duration = end_time - start_time
                
                # 切割片段
                segment_file = os.path.join(temp_dir, f"segment_{i:04d}.mp4")
                success = self._cut_segment(video_path, segment_file, start_time, duration)
                
                if success:
                    segment_files.append(segment_file)
                else:
                    logger.warning(f"切割片段失败: {start_time}-{end_time}")
            
            # 如果没有有效片段，返回错误
            if not segment_files:
                return {
                    'status': 'error',
                    'error': "没有有效的视频片段可处理"
                }
            
            # 生成片段列表文件
            list_file_path = os.path.join(temp_dir, "segments.txt")
            with open(list_file_path, 'w', encoding='utf-8') as f:
                for file in segment_files:
                    f.write(f"file '{file}'\n")
            
            # 拼接片段
            success = self._concat_videos_from_list(list_file_path, output_path)
            
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
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频的基本信息"""
        try:
            # 调用FFprobe获取视频信息
            result = subprocess.run([
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration : stream=width,height,codec_type',
                '-of', 'json',
                video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFprobe返回错误: {result.stderr}")
            
            info = json.loads(result.stdout)
            
            # 提取视频信息
            duration = float(info.get('format', {}).get('duration', 0))
            
            width = None
            height = None
            
            # 查找视频流
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width = stream.get('width')
                    height = stream.get('height')
                    break
            
            return {
                'duration': duration,
                'width': width,
                'height': height
            }
            
        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return {
                'duration': 0,
                'width': 0,
                'height': 0
            }
    
    def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        try:
            # 调用FFprobe获取视频时长
            result = subprocess.run([
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFprobe返回错误: {result.stderr}")
            
            return float(result.stdout.strip())
            
        except Exception as e:
            logger.error(f"获取视频时长失败: {str(e)}")
            return 0.0
    
    def _cut_segment(self, input_path: str, output_path: str, 
                    start_time: float, duration: float) -> bool:
        """切割视频片段"""
        try:
            # 构建FFmpeg命令
            video_settings = self.config['video_settings']
            audio_settings = self.config['audio_settings']
            performance = self.config['performance']
            
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'warning',
                
                # 设置线程数
                '-threads', str(performance.get('threads', 0)),
                
                # 输入时间偏移
                '-ss', str(start_time),
                
                # 输入文件
                '-i', input_path,
                
                # 时长
                '-t', str(duration),
                
                # 视频设置
                '-c:v', video_settings.get('codec', 'libx264'),
                '-crf', str(video_settings.get('crf', 23)),
                '-preset', video_settings.get('preset', 'medium'),
                
                # 音频设置
                '-c:a', audio_settings.get('codec', 'aac'),
                '-b:a', audio_settings.get('bitrate', '128k'),
                
                # 快速切割，不重新编码（如果可能）
                '-avoid_negative_ts', '1',
                
                # 输出文件
                '-y', output_path
            ]
            
            # 如果设置了分辨率
            resolution = video_settings.get('resolution')
            if resolution:
                cmd.extend(['-s', resolution])
            
            # 执行命令
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                logger.error(f"切割片段失败: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"切割视频片段时发生错误: {str(e)}")
            return False
    
    def _concat_videos_from_list(self, list_file_path: str, output_path: str) -> bool:
        """通过列表文件拼接视频"""
        try:
            # 构建FFmpeg命令
            video_settings = self.config['video_settings']
            audio_settings = self.config['audio_settings']
            
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'warning',
                
                # 使用concat分离器
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file_path,
                
                # 视频设置
                '-c:v', video_settings.get('codec', 'libx264'),
                '-crf', str(video_settings.get('crf', 23)),
                '-preset', video_settings.get('preset', 'medium'),
                
                # 音频设置
                '-c:a', audio_settings.get('codec', 'aac'),
                '-b:a', audio_settings.get('bitrate', '128k'),
                
                # 输出文件
                '-y', output_path
            ]
            
            # 执行命令
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                logger.error(f"拼接视频失败: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"拼接视频时发生错误: {str(e)}")
            return False
    
    def _concat_videos(self, input_files: List[str], output_path: str) -> bool:
        """拼接多个视频文件"""
        # 创建临时列表文件
        list_file_path = os.path.join(self.temp_dir, f"concat_{int(time.time())}.txt")
        
        try:
            # 创建文件列表
            with open(list_file_path, 'w', encoding='utf-8') as f:
                for file in input_files:
                    f.write(f"file '{file}'\n")
            
            # 拼接视频
            return self._concat_videos_from_list(list_file_path, output_path)
            
        except Exception as e:
            logger.error(f"拼接视频时发生错误: {str(e)}")
            return False
            
        finally:
            # 清理临时文件
            if os.path.exists(list_file_path):
                os.remove(list_file_path)
    
    def _clean_temp_files(self, temp_dir: str) -> None:
        """清理临时文件"""
        try:
            if os.path.exists(temp_dir):
                # 删除目录中的所有文件
                for file in glob.glob(os.path.join(temp_dir, "*")):
                    try:
                        os.remove(file)
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {file}, 错误: {str(e)}")
                
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
            print(f"时长: {result['duration']:.2f}秒, 处理时间: {result['processing_time']:.2f}秒")
