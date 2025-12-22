#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪辑生成器模块 - 负责根据生成的字幕自动剪辑视频
对原视频进行切割、拼接，生成最终的混剪视频
支持低配置设备下的高效视频处理
集成GPU加速视频处理组件和质量评估功能
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

# 🆕 导入GPU视频处理组件
try:
    from src.core.gpu_video_components import GPUVideoEncoder, CPUVideoEncoder
    GPU_COMPONENTS_AVAILABLE = True
except ImportError:
    GPU_COMPONENTS_AVAILABLE = False
    logger = logging.getLogger("clip_generator")
    logger.warning("GPU视频处理组件不可用，将使用基础GPU支持")

# 🆕 导入视频质量评估器
try:
    from src.core.video_quality import VideoQualityEvaluator
    QUALITY_EVALUATOR_AVAILABLE = True
except ImportError:
    QUALITY_EVALUATOR_AVAILABLE = False

# 🆕 导入增强工作流管理器
try:
    from src.core.enhanced_workflow_manager import EnhancedWorkflowManager
    ENHANCED_WORKFLOW_AVAILABLE = True
except ImportError:
    ENHANCED_WORKFLOW_AVAILABLE = False

# 🆕 导入场景分析器
try:
    from src.alignment.scene_analyzer import SceneAnalyzer
    SCENE_ANALYZER_AVAILABLE = True
except ImportError:
    SCENE_ANALYZER_AVAILABLE = False

# 🆕 导入关键帧提取器
try:
    from src.alignment.keyframe_extractor import extract_keyframes
    KEYFRAME_EXTRACTOR_AVAILABLE = True
except ImportError:
    KEYFRAME_EXTRACTOR_AVAILABLE = False

# 🆕 导入内存管理模块
try:
    from src.utils.memory_integration import MemoryManager
    from src.utils.memory_probes import MemoryProbe, MemoryProbeManager
    MEMORY_MANAGEMENT_AVAILABLE = True
except ImportError:
    MEMORY_MANAGEMENT_AVAILABLE = False

# 🆕 导入错误处理模块
try:
    from src.core.error_handler import get_error_handler
    from src.core.auto_recovery import auto_heal
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    if 'logger' not in locals():
        logger = logging.getLogger("clip_generator")
    logger.warning("视频质量评估器不可用")

# 配置日志
if 'logger' not in locals():
    logger = get_logger("clip_generator")

# 配置目录路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs")
CLIP_CONFIG_PATH = os.path.join(CONFIG_DIR, "clip_settings.json")

class ClipGenerator:
    """
    剪辑生成器 - 根据字幕时间码自动切割原视频并拼接
    用于生成最终的混剪视频成品，支持低配置设备下的高效视频处理
    """
    
    def __init__(self, use_gpu: bool = True):
        """
        初始化剪辑生成器

        Args:
            use_gpu: 是否尝试使用GPU加速（默认True）
        """
        # 加载配置
        self.config = self._load_config()

        # 创建临时目录
        self.temp_dir = os.path.join(tempfile.gettempdir(), "visionai_clips")
        os.makedirs(self.temp_dir, exist_ok=True)

        # 记录处理的历史
        self.processing_history = []

        # 检查FFmpeg可用性
        self._check_ffmpeg()

        # 🆕 检查并初始化GPU加速
        self.use_gpu = use_gpu
        self.gpu_available = False
        self.gpu_encoder = None

        if use_gpu:
            self.gpu_available = self._check_gpu_acceleration()
            if self.gpu_available:
                logger.info("✅ GPU加速已启用")
                # 🆕 初始化GPU视频编码器（如果可用）
                if GPU_COMPONENTS_AVAILABLE:
                    try:
                        import torch
                        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                        self.gpu_encoder = GPUVideoEncoder(device, self.config)
                        logger.info("🎮 GPU视频编码器已初始化")
                    except Exception as e:
                        logger.warning(f"GPU视频编码器初始化失败: {e}")
                        self.gpu_encoder = None
            else:
                logger.info("ℹ️ GPU加速不可用，将使用CPU模式")

        # 🆕 初始化视频质量评估器（如果可用）
        self.quality_evaluator = None
        if QUALITY_EVALUATOR_AVAILABLE:
            try:
                self.quality_evaluator = VideoQualityEvaluator(use_gpu=self.gpu_available)
                logger.info("📊 视频质量评估器已初始化")
            except Exception as e:
                logger.warning(f"视频质量评估器初始化失败: {e}")

        # 🆕 初始化增强工作流管理器（如果可用）
        self.enhanced_workflow = None
        if ENHANCED_WORKFLOW_AVAILABLE:
            try:
                self.enhanced_workflow = EnhancedWorkflowManager(
                    progress_callback=self._workflow_progress_callback
                )
                logger.info("🔄 增强工作流管理器已初始化")
            except Exception as e:
                logger.warning(f"增强工作流管理器初始化失败: {e}")

        # 🆕 初始化场景分析器（如果可用）
        self.scene_analyzer = None
        if SCENE_ANALYZER_AVAILABLE:
            try:
                self.scene_analyzer = SceneAnalyzer(
                    min_scene_duration=1.0,
                    scene_threshold=30.0,
                    use_external_models=False
                )
                logger.info("🎬 场景分析器已初始化")
            except Exception as e:
                logger.warning(f"场景分析器初始化失败: {e}")

        # 🆕 关键帧提取功能标记
        self.keyframe_extraction_enabled = KEYFRAME_EXTRACTOR_AVAILABLE
        if self.keyframe_extraction_enabled:
            logger.info("🎞️ 关键帧提取功能已启用")

        # 🆕 初始化内存管理器（如果可用）
        self.memory_manager = None
        self.memory_probe_manager = None
        if MEMORY_MANAGEMENT_AVAILABLE:
            try:
                self.memory_manager = MemoryManager()
                self.memory_probe_manager = MemoryProbeManager()
                logger.info("💾 内存管理器已初始化")
            except Exception as e:
                logger.warning(f"内存管理器初始化失败: {e}")

        # 🆕 初始化错误处理器（如果可用）
        self.error_handler = None
        if ERROR_HANDLING_AVAILABLE:
            try:
                self.error_handler = get_error_handler()
                logger.info("🛡️ 错误处理器已初始化")
            except Exception as e:
                logger.warning(f"错误处理器初始化失败: {e}")

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

    def _check_gpu_acceleration(self) -> bool:
        """
        检查GPU硬件加速支持

        Returns:
            bool: GPU加速是否可用
        """
        try:
            # 检查NVIDIA GPU编码器
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                output = result.stdout.lower()
                has_nvenc = 'h264_nvenc' in output or 'hevc_nvenc' in output

                if has_nvenc:
                    logger.info("🎮 检测到NVIDIA GPU编码器支持 (NVENC)")
                    return True
                else:
                    logger.debug("未检测到NVIDIA GPU编码器")
                    return False

            return False

        except Exception as e:
            logger.debug(f"GPU加速检查失败: {e}")
            return False
    
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
        
        # 🆕 创建内存探针（如果可用）
        memory_probe = None
        if self.memory_probe_manager:
            try:
                memory_probe = MemoryProbe(
                    name="generate_clips",
                    level="high",
                    callback=lambda: self.optimize_memory(aggressive=False)
                )
                memory_probe.check()
            except Exception as e:
                logger.warning(f"内存探针创建失败: {e}")

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
                    logger.warning("质量检查失败")

            # 🆕 使用VideoQualityEvaluator进行额外的质量评估（如果可用）
            if self.quality_evaluator and os.path.exists(output_path):
                try:
                    logger.info("📊 开始视频质量评估（PSNR/SSIM）")

                    # 评估视频质量
                    quality_metrics = self.quality_evaluator.evaluate_video_quality(
                        video_path=output_path,
                        reference_video=video_path  # 使用原视频作为参考
                    )

                    if quality_metrics:
                        # 添加质量指标到结果
                        if 'quality' not in result:
                            result['quality'] = {}
                        result['quality']['psnr'] = quality_metrics.get('avg_psnr', 0)
                        result['quality']['min_psnr'] = quality_metrics.get('min_psnr', 0)
                        result['quality']['error_rate'] = quality_metrics.get('error_rate', 0)
                        result['quality']['meets_standard'] = quality_metrics.get('meets_standard', False)

                        logger.info(f"📊 质量评估完成: PSNR={quality_metrics.get('avg_psnr', 0):.2f}, "
                                  f"误差率={quality_metrics.get('error_rate', 0):.4%}")

                        # 如果质量不达标，添加警告
                        if not quality_metrics.get('meets_standard', False):
                            logger.warning("⚠️ 视频质量未达到标准（PSNR<28或误差率>0.1%）")
                            if 'recommendations' not in result:
                                result['recommendations'] = []
                            result['recommendations'].append("视频质量未达标，建议调整编码参数或使用更高质量的源视频")
                except Exception as e:
                    logger.warning(f"视频质量评估失败: {e}")

            # 返回结果
            if not quality_check or not quality_controller:
                # 如果没有启用质量检查，直接返回
                return result

            # 检查质量检查结果
            if quality_result.get('success', False):
                return result
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
            # 🆕 尝试使用错误处理器进行恢复
            error_context = {
                "module": "clip_generator",
                "component": "video_processing",
                "video_path": video_path,
                "process_id": process_id,
                "segments_count": len(subtitle_segments)
            }

            if self.error_handler:
                logger.info("🛡️ 尝试使用错误处理器恢复...")
                handled = self.handle_error_with_recovery(e, context=error_context)

                if handled:
                    logger.info("✅ 错误已恢复，重试处理...")
                    # 重试一次
                    try:
                        return self.generate_clips(video_path, subtitle_segments, output_path, quality_check=False)
                    except Exception as retry_error:
                        logger.error(f"重试失败: {retry_error}")

            # 如果无法恢复，记录错误并返回
            logger.error(f"处理视频时出错: {str(e)}")
            return {
                'status': 'error',
                'process_id': process_id,
                'error': str(e)
            }

        finally:
            # 🆕 检查内存探针
            if memory_probe:
                try:
                    memory_probe.check()
                except Exception as e:
                    logger.warning(f"内存探针检查失败: {e}")

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
                # 获取时间信息（优先使用original_start/original_end，然后是original_time，最后是time）
                if 'original_start' in segment and 'original_end' in segment:
                    # 使用原始字幕的时间码（SRT格式：HH:MM:SS,mmm）
                    start_time = self._parse_srt_time(segment['original_start'])
                    end_time = self._parse_srt_time(segment['original_end'])
                    logger.debug(f"使用原始时间码: {segment['original_start']} -> {segment['original_end']}")
                elif 'original_time' in segment:
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
        """
        切割视频片段（支持GPU加速）

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            start_time: 开始时间（秒）
            duration: 持续时间（秒）

        Returns:
            bool: 是否成功
        """
        try:
            # 构建FFmpeg命令
            video_settings = self.config['video_settings']
            audio_settings = self.config['audio_settings']
            performance = self.config['performance']

            # 🆕 根据GPU可用性选择编码器
            if self.gpu_available:
                cmd = [
                    'ffmpeg',
                    '-hide_banner',
                    '-loglevel', 'warning',

                    # 🎮 GPU硬件加速
                    '-hwaccel', 'cuda',
                    '-hwaccel_output_format', 'cuda',

                    # 输入时间偏移
                    '-ss', str(start_time),

                    # 输入文件
                    '-i', input_path,

                    # 时长
                    '-t', str(duration),

                    # 🎮 GPU编码器
                    '-c:v', 'h264_nvenc',
                    '-preset', 'fast',
                    '-crf', str(video_settings.get('crf', 23)),

                    # 音频设置
                    '-c:a', audio_settings.get('codec', 'aac'),
                    '-b:a', audio_settings.get('bitrate', '128k'),

                    # 快速切割
                    '-avoid_negative_ts', '1',

                    # 输出文件
                    '-y', output_path
                ]
            else:
                # CPU模式
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

                    # 快速切割
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
                # 🆕 如果GPU失败，尝试回退到CPU
                if self.gpu_available:
                    logger.warning(f"GPU切割失败，回退到CPU模式: {result.stderr}")
                    self.gpu_available = False  # 临时禁用GPU
                    return self._cut_segment(input_path, output_path, start_time, duration)
                else:
                    logger.error(f"切割片段失败: {result.stderr}")
                    return False

            return True

        except Exception as e:
            logger.error(f"切割视频片段时发生错误: {str(e)}")
            return False
    
    def _concat_videos_from_list(self, list_file_path: str, output_path: str) -> bool:
        """
        通过列表文件拼接视频（支持GPU加速）

        Args:
            list_file_path: 视频列表文件路径
            output_path: 输出视频路径

        Returns:
            bool: 是否成功
        """
        try:
            # 🆕 优先使用GPU视频编码器组件（如果可用）
            if self.gpu_encoder is not None:
                try:
                    # 读取视频列表
                    segment_files = []
                    with open(list_file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('file '):
                                file_path = line.strip()[6:-1]  # 移除 "file '" 和 "'"
                                segment_files.append(file_path)

                    # 使用GPU编码器拼接
                    logger.info(f"🎮 使用GPU视频编码器拼接 {len(segment_files)} 个片段")
                    self.gpu_encoder.concatenate_segments(segment_files, output_path)
                    logger.info(f"✅ GPU拼接成功: {output_path}")
                    return True
                except Exception as e:
                    logger.warning(f"GPU编码器拼接失败，回退到FFmpeg: {e}")
                    # 继续使用下面的FFmpeg方法

            # 构建FFmpeg命令
            video_settings = self.config['video_settings']
            audio_settings = self.config['audio_settings']

            # 🆕 根据GPU可用性选择编码器
            if self.gpu_available:
                cmd = [
                    'ffmpeg',
                    '-hide_banner',
                    '-loglevel', 'warning',

                    # 🎮 GPU硬件加速
                    '-hwaccel', 'cuda',

                    # 使用concat分离器
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', list_file_path,

                    # 🎮 GPU编码器
                    '-c:v', 'h264_nvenc',
                    '-preset', 'fast',
                    '-crf', str(video_settings.get('crf', 23)),

                    # 音频设置
                    '-c:a', audio_settings.get('codec', 'aac'),
                    '-b:a', audio_settings.get('bitrate', '128k'),

                    # 输出文件
                    '-y', output_path
                ]
            else:
                # CPU模式
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
                # 🆕 如果GPU失败，尝试回退到CPU
                if self.gpu_available:
                    logger.warning(f"GPU拼接失败，回退到CPU模式: {result.stderr}")
                    self.gpu_available = False  # 临时禁用GPU
                    return self._concat_videos_from_list(list_file_path, output_path)
                else:
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
    
    def _parse_srt_time(self, srt_time: str) -> float:
        """
        解析SRT时间格式为秒数

        参数:
            srt_time: SRT时间格式字符串 (HH:MM:SS,mmm)

        返回:
            秒数（浮点数）
        """
        try:
            # SRT格式: HH:MM:SS,mmm
            if not srt_time or not isinstance(srt_time, str):
                return 0.0

            # 分割时间和毫秒
            time_part, ms_part = srt_time.split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)

            # 转换为总秒数
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0

            return total_seconds
        except Exception as e:
            logger.warning(f"解析SRT时间失败: {srt_time}, 错误: {e}")
            return 0.0

    def analyze_scenes(self, video_path: str, subtitle_data: List[Dict] = None) -> List:
        """
        分析视频场景

        Args:
            video_path: 视频文件路径
            subtitle_data: 字幕数据（可选）

        Returns:
            场景列表
        """
        if not self.scene_analyzer:
            logger.warning("场景分析器不可用")
            return []

        try:
            logger.info(f"🎬 开始分析视频场景: {video_path}")
            scenes = self.scene_analyzer.analyze_video(
                video_path=video_path,
                subtitle_data=subtitle_data,
                use_cache=True
            )
            logger.info(f"✅ 场景分析完成: {len(scenes)}个场景")
            return scenes
        except Exception as e:
            logger.error(f"场景分析失败: {e}")
            return []

    def extract_keyframes(self, video_path: str, method: str = 'scene',
                         num_frames: int = 10, threshold: float = 30.0) -> List[Dict]:
        """
        提取视频关键帧

        Args:
            video_path: 视频文件路径
            method: 提取方法 ('uniform', 'difference', 'scene')
            num_frames: 提取帧数（uniform方法）
            threshold: 阈值（difference/scene方法）

        Returns:
            关键帧列表
        """
        if not self.keyframe_extraction_enabled:
            logger.warning("关键帧提取功能不可用")
            return []

        try:
            logger.info(f"🎞️ 开始提取关键帧: 方法={method}")
            keyframes = extract_keyframes(
                video_path=video_path,
                method=method,
                num_frames=num_frames,
                threshold=threshold,
                save_frames=False
            )
            logger.info(f"✅ 关键帧提取完成: {len(keyframes)}帧")
            return keyframes
        except Exception as e:
            logger.error(f"关键帧提取失败: {e}")
            return []

    def _workflow_progress_callback(self, current_step: int, total_steps: int, message: str):
        """
        增强工作流进度回调

        Args:
            current_step: 当前步骤
            total_steps: 总步骤数
            message: 进度消息
        """
        progress_percent = int((current_step / total_steps) * 100)
        logger.info(f"🔄 工作流进度 [{current_step}/{total_steps}] ({progress_percent}%): {message}")

    def process_with_enhanced_workflow(self, video_path: str, srt_path: str,
                                      output_path: str, language: str = None) -> Dict[str, Any]:
        """
        使用增强工作流处理完整流程

        Args:
            video_path: 原视频文件路径
            srt_path: SRT字幕文件路径
            output_path: 输出文件路径
            language: 指定语言（可选）

        Returns:
            处理结果字典
        """
        if not self.enhanced_workflow:
            logger.warning("增强工作流管理器不可用，回退到标准流程")
            return self.generate_from_srt(video_path, srt_path, output_path)

        try:
            logger.info("🚀 使用增强工作流处理完整流程")
            result = self.enhanced_workflow.process_complete_workflow(
                video_path=video_path,
                srt_path=srt_path,
                output_path=output_path,
                language=language
            )

            if result.get("success"):
                logger.info(f"✅ 增强工作流处理成功，耗时: {result.get('duration', 0):.2f}秒")
            else:
                logger.error(f"❌ 增强工作流处理失败: {result.get('error', '未知错误')}")

            return result

        except Exception as e:
            logger.error(f"增强工作流处理异常: {e}")
            logger.warning("回退到标准流程")
            return self.generate_from_srt(video_path, srt_path, output_path)

    def check_memory_usage(self) -> Dict[str, Any]:
        """
        检查内存使用情况

        Returns:
            内存使用信息字典
        """
        if not self.memory_manager:
            # 回退到基本的内存检查
            try:
                import psutil
                memory = psutil.virtual_memory()
                return {
                    "memory_percent": memory.percent,
                    "memory_used_mb": memory.used / 1024 / 1024,
                    "memory_available_mb": memory.available / 1024 / 1024,
                    "status": "ok" if memory.percent < 80 else "warning"
                }
            except Exception as e:
                logger.warning(f"检查内存使用失败: {e}")
                return {}

        try:
            # 使用内存管理器获取详细信息
            memory_info = self.memory_manager.get_current_memory_usage()
            return {
                "memory_used_mb": memory_info / (1024 * 1024),
                "status": "ok"
            }
        except Exception as e:
            logger.warning(f"检查内存使用失败: {e}")
            return {}

    def optimize_memory(self, aggressive: bool = False):
        """
        优化内存使用

        Args:
            aggressive: 是否使用激进的内存优化
        """
        try:
            logger.info(f"🧹 开始{'激进' if aggressive else '常规'}内存优化...")

            if self.memory_manager:
                # 使用内存管理器进行优化
                before, after = self.memory_manager.optimize_memory(aggressive=aggressive)
                freed_mb = before - after
                logger.info(f"✅ 内存优化完成，释放了 {freed_mb:.2f}MB 内存")
            else:
                # 回退到基本的垃圾回收
                import gc
                gc.collect()
                logger.info("✅ 基本内存优化完成（垃圾回收）")

        except Exception as e:
            logger.warning(f"内存优化失败: {e}")

    def handle_error_with_recovery(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """
        使用错误处理器处理错误并尝试恢复

        Args:
            error: 捕获的异常
            context: 错误上下文

        Returns:
            是否成功处理/恢复
        """
        if not self.error_handler:
            logger.error(f"错误处理器不可用，无法处理错误: {error}")
            return False

        try:
            logger.info(f"🛡️ 使用错误处理器处理错误: {type(error).__name__}")
            handled = self.error_handler.handle_error(error, context=context)

            if handled:
                logger.info("✅ 错误已成功处理/恢复")
            else:
                logger.warning("⚠️ 错误无法自动恢复")

            return handled
        except Exception as handler_error:
            logger.error(f"错误处理器本身发生异常: {handler_error}")
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
            print(f"时长: {result['duration']:.2f}秒, 处理时间: {result['processing_time']:.2f}秒")
