#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强视频处理器
实现基于新字幕的视频片段自动拼接功能，确保时间轴精确对齐
"""

import os
import json
import time
import logging
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

# 尝试导入视频处理库
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import ffmpeg
    HAS_FFMPEG_PYTHON = True
except ImportError:
    HAS_FFMPEG_PYTHON = False

logger = logging.getLogger(__name__)

class EnhancedVideoProcessor:
    """增强视频处理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化视频处理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.temp_dir = self.config.get("temp_dir", "temp")
        self.ffmpeg_path = self._find_ffmpeg()
        
        # 确保临时目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 处理历史
        self.processing_history = []
        
        logger.info("增强视频处理器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "temp_dir": "temp",
            "video_settings": {
                "codec": "libx264",
                "crf": 23,
                "preset": "medium",
                "resolution": None,
                "fps": None
            },
            "audio_settings": {
                "codec": "aac",
                "bitrate": "128k",
                "sample_rate": 44100
            },
            "processing": {
                "max_segments": 100,
                "segment_overlap": 0.1,  # 片段重叠时间（秒）
                "precision_mode": True,  # 精确模式
                "threads": 0  # 0表示自动
            },
            "alignment": {
                "tolerance": 0.05,  # 时间轴对齐容差（秒）
                "auto_adjust": True,  # 自动调整时间轴
                "smooth_transitions": True  # 平滑过渡
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        
        return default_config
    
    def _find_ffmpeg(self) -> str:
        """查找FFmpeg可执行文件"""
        # 常见的FFmpeg路径
        possible_paths = [
            "ffmpeg",
            "ffmpeg.exe",
            "./ffmpeg/bin/ffmpeg.exe",
            "./ffmpeg/ffmpeg.exe",
            "C:/ffmpeg/bin/ffmpeg.exe"
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"找到FFmpeg: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        logger.warning("未找到FFmpeg，视频处理功能可能受限")
        return "ffmpeg"
    
    def process_video_with_subtitles(self, video_path: str, 
                                   viral_subtitles: List[Dict[str, Any]],
                                   output_path: str) -> Dict[str, Any]:
        """
        根据爆款字幕处理视频
        
        Args:
            video_path: 原视频路径
            viral_subtitles: 爆款字幕列表
            output_path: 输出视频路径
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            logger.info(f"开始处理视频: {video_path}")
            start_time = time.time()
            
            # 第一步：验证输入
            if not os.path.exists(video_path):
                return {"success": False, "error": f"视频文件不存在: {video_path}"}
            
            if not viral_subtitles:
                return {"success": False, "error": "字幕列表为空"}
            
            # 第二步：获取视频信息
            video_info = self._get_video_info(video_path)
            if not video_info:
                return {"success": False, "error": "无法获取视频信息"}
            
            # 第三步：时间轴对齐优化
            aligned_subtitles = self._align_timeline(viral_subtitles, video_info)
            
            # 第四步：生成视频片段
            segments = self._extract_video_segments(video_path, aligned_subtitles)
            if not segments:
                return {"success": False, "error": "无法提取视频片段"}
            
            # 第五步：拼接视频
            success = self._concatenate_segments(segments, output_path)
            
            processing_time = time.time() - start_time
            
            if success:
                # 记录处理历史
                self.processing_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "input_video": video_path,
                    "output_video": output_path,
                    "segments_count": len(segments),
                    "processing_time": processing_time
                })
                
                return {
                    "success": True,
                    "output_path": output_path,
                    "segments_count": len(segments),
                    "processing_time": processing_time,
                    "video_info": video_info
                }
            else:
                return {"success": False, "error": "视频拼接失败"}
                
        except Exception as e:
            logger.error(f"处理视频失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """获取视频信息"""
        try:
            if HAS_FFMPEG_PYTHON:
                # 使用ffmpeg-python获取信息
                probe = ffmpeg.probe(video_path)
                video_stream = next(
                    (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                    None
                )
                audio_stream = next(
                    (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
                    None
                )
                
                if video_stream:
                    duration = float(video_stream.get('duration', 0))
                    fps = eval(video_stream.get('r_frame_rate', '25/1'))
                    width = int(video_stream.get('width', 0))
                    height = int(video_stream.get('height', 0))
                    
                    return {
                        "duration": duration,
                        "fps": fps,
                        "width": width,
                        "height": height,
                        "has_audio": audio_stream is not None,
                        "codec": video_stream.get('codec_name', 'unknown')
                    }
            
            # 备用方案：使用FFmpeg命令行
            cmd = [
                self.ffmpeg_path, "-i", video_path,
                "-f", "null", "-"
            ]
            
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 解析FFmpeg输出
            output = result.stderr
            duration = self._parse_duration_from_ffmpeg(output)
            fps = self._parse_fps_from_ffmpeg(output)
            resolution = self._parse_resolution_from_ffmpeg(output)
            
            return {
                "duration": duration,
                "fps": fps,
                "width": resolution[0] if resolution else 0,
                "height": resolution[1] if resolution else 0,
                "has_audio": "Audio:" in output,
                "codec": "unknown"
            }
            
        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return None
    
    def _parse_duration_from_ffmpeg(self, output: str) -> float:
        """从FFmpeg输出解析时长"""
        import re
        match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', output)
        if match:
            hours, minutes, seconds, centiseconds = map(int, match.groups())
            return hours * 3600 + minutes * 60 + seconds + centiseconds / 100
        return 0.0
    
    def _parse_fps_from_ffmpeg(self, output: str) -> float:
        """从FFmpeg输出解析帧率"""
        import re
        match = re.search(r'(\d+\.?\d*) fps', output)
        if match:
            return float(match.group(1))
        return 25.0  # 默认帧率
    
    def _parse_resolution_from_ffmpeg(self, output: str) -> Optional[Tuple[int, int]]:
        """从FFmpeg输出解析分辨率"""
        import re
        match = re.search(r'(\d+)x(\d+)', output)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None
    
    def _align_timeline(self, subtitles: List[Dict[str, Any]], 
                       video_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """时间轴对齐优化"""
        try:
            aligned_subtitles = []
            video_duration = video_info.get("duration", 0)
            tolerance = self.config["alignment"]["tolerance"]
            
            for i, subtitle in enumerate(subtitles):
                aligned_sub = subtitle.copy()
                
                # 解析时间
                start_time = self._parse_time(subtitle.get("start_time", "00:00:00,000"))
                end_time = self._parse_time(subtitle.get("end_time", "00:00:01,000"))
                
                # 确保时间在视频范围内
                start_time = max(0, min(start_time, video_duration - 0.1))
                end_time = max(start_time + 0.1, min(end_time, video_duration))
                
                # 避免片段重叠
                if i > 0 and aligned_subtitles:
                    prev_end = self._parse_time(aligned_subtitles[-1]["end_time"])
                    if start_time < prev_end + tolerance:
                        start_time = prev_end + tolerance
                        end_time = max(start_time + 0.1, end_time)
                
                # 更新时间
                aligned_sub["start_time"] = self._format_time(start_time)
                aligned_sub["end_time"] = self._format_time(end_time)
                aligned_sub["duration"] = end_time - start_time
                
                aligned_subtitles.append(aligned_sub)
            
            logger.info(f"时间轴对齐完成，处理了 {len(aligned_subtitles)} 个片段")
            return aligned_subtitles
            
        except Exception as e:
            logger.error(f"时间轴对齐失败: {str(e)}")
            return subtitles
    
    def _parse_time(self, time_str: str) -> float:
        """解析时间字符串为秒数"""
        try:
            # 支持格式：HH:MM:SS,mmm 或 HH:MM:SS.mmm
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
            logger.warning(f"解析时间失败: {time_str}, {e}")
            return 0.0
    
    def _format_time(self, seconds: float) -> str:
        """格式化秒数为时间字符串"""
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            milliseconds = int((secs % 1) * 1000)
            secs = int(secs)
            
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
            
        except Exception as e:
            logger.warning(f"格式化时间失败: {seconds}, {e}")
            return "00:00:00,000"

    def _extract_video_segments(self, video_path: str,
                               subtitles: List[Dict[str, Any]]) -> List[str]:
        """提取视频片段"""
        try:
            segment_files = []
            video_settings = self.config["video_settings"]
            audio_settings = self.config["audio_settings"]

            for i, subtitle in enumerate(subtitles):
                start_time = self._parse_time(subtitle.get("start_time", "00:00:00,000"))
                end_time = self._parse_time(subtitle.get("end_time", "00:00:01,000"))
                duration = end_time - start_time

                if duration <= 0:
                    logger.warning(f"跳过无效片段 {i}: 时长 {duration}")
                    continue

                # 生成片段文件名
                segment_file = os.path.join(
                    self.temp_dir,
                    f"segment_{i:04d}_{int(start_time*1000):06d}.mp4"
                )

                # 构建FFmpeg命令
                cmd = [
                    self.ffmpeg_path,
                    "-hide_banner", "-loglevel", "warning",
                    "-ss", str(start_time),
                    "-i", video_path,
                    "-t", str(duration),
                    "-c:v", video_settings.get("codec", "libx264"),
                    "-crf", str(video_settings.get("crf", 23)),
                    "-preset", video_settings.get("preset", "medium"),
                    "-c:a", audio_settings.get("codec", "aac"),
                    "-b:a", audio_settings.get("bitrate", "128k"),
                    "-avoid_negative_ts", "1",
                    "-y", segment_file
                ]

                # 添加分辨率设置
                if video_settings.get("resolution"):
                    cmd.extend(["-s", video_settings["resolution"]])

                # 执行命令
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0 and os.path.exists(segment_file):
                    segment_files.append(segment_file)
                    logger.debug(f"提取片段 {i} 成功: {segment_file}")
                else:
                    logger.error(f"提取片段 {i} 失败: {result.stderr}")

            logger.info(f"成功提取 {len(segment_files)} 个视频片段")
            return segment_files

        except Exception as e:
            logger.error(f"提取视频片段失败: {str(e)}")
            return []

    def _concatenate_segments(self, segment_files: List[str],
                            output_path: str) -> bool:
        """拼接视频片段"""
        try:
            if not segment_files:
                logger.error("没有可拼接的片段")
                return False

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # 创建片段列表文件
            list_file = os.path.join(self.temp_dir, f"concat_list_{int(time.time())}.txt")

            try:
                with open(list_file, 'w', encoding='utf-8') as f:
                    for segment_file in segment_files:
                        # 使用绝对路径并转义
                        abs_path = os.path.abspath(segment_file).replace('\\', '/')
                        f.write(f"file '{abs_path}'\n")

                # 构建拼接命令
                video_settings = self.config["video_settings"]
                audio_settings = self.config["audio_settings"]

                cmd = [
                    self.ffmpeg_path,
                    "-hide_banner", "-loglevel", "warning",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    "-c:v", video_settings.get("codec", "libx264"),
                    "-crf", str(video_settings.get("crf", 23)),
                    "-preset", video_settings.get("preset", "medium"),
                    "-c:a", audio_settings.get("codec", "aac"),
                    "-b:a", audio_settings.get("bitrate", "128k"),
                    "-y", output_path
                ]

                # 执行拼接
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0 and os.path.exists(output_path):
                    logger.info(f"视频拼接成功: {output_path}")
                    return True
                else:
                    logger.error(f"视频拼接失败: {result.stderr}")
                    return False

            finally:
                # 清理列表文件
                if os.path.exists(list_file):
                    os.remove(list_file)

        except Exception as e:
            logger.error(f"拼接视频失败: {str(e)}")
            return False

    def create_smooth_transitions(self, segment_files: List[str],
                                output_path: str) -> bool:
        """创建平滑过渡效果"""
        try:
            if not self.config["alignment"]["smooth_transitions"]:
                return self._concatenate_segments(segment_files, output_path)

            if len(segment_files) < 2:
                return self._concatenate_segments(segment_files, output_path)

            # 使用FFmpeg的xfade滤镜创建过渡效果
            filter_complex = []
            inputs = []

            for i, segment in enumerate(segment_files):
                inputs.extend(["-i", segment])

            # 构建过渡滤镜链
            current_output = "0:v"
            for i in range(1, len(segment_files)):
                transition_duration = 0.5  # 过渡时长
                filter_complex.append(
                    f"[{current_output}][{i}:v]xfade=transition=fade:duration={transition_duration}:offset=0[v{i}]"
                )
                current_output = f"v{i}"

            # 音频混合
            audio_inputs = [f"{i}:a" for i in range(len(segment_files))]
            filter_complex.append(f"[{''.join(audio_inputs)}]amix=inputs={len(segment_files)}[a]")

            cmd = [
                self.ffmpeg_path,
                "-hide_banner", "-loglevel", "warning"
            ] + inputs + [
                "-filter_complex", ";".join(filter_complex),
                "-map", f"[{current_output}]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-crf", "23",
                "-preset", "medium",
                "-c:a", "aac",
                "-y", output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("平滑过渡视频创建成功")
                return True
            else:
                logger.warning(f"平滑过渡失败，使用普通拼接: {result.stderr}")
                return self._concatenate_segments(segment_files, output_path)

        except Exception as e:
            logger.error(f"创建平滑过渡失败: {str(e)}")
            return self._concatenate_segments(segment_files, output_path)

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    if file.startswith("segment_") or file.startswith("concat_"):
                        file_path = os.path.join(self.temp_dir, file)
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logger.warning(f"删除临时文件失败: {file_path}, {e}")

            logger.info("临时文件清理完成")

        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")

    def get_processing_history(self) -> List[Dict[str, Any]]:
        """获取处理历史"""
        return self.processing_history.copy()

    def __del__(self):
        """析构函数"""
        self.cleanup_temp_files()
