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

# 统一日志记录器，确保写入 logs/visionai.log
logger = get_logger(__name__)

from src.utils.memory_guard import track_memory
from src.quality.quality_controller import QualityController
from src.core.exceptions import QualityCheckError

# 🆕 导入GPU视频处理组件
try:
    from src.core.gpu_video_components import GPUVideoEncoder, CPUVideoEncoder
    GPU_COMPONENTS_AVAILABLE = True
except ImportError:
    GPU_COMPONENTS_AVAILABLE = False
    logger.warning("GPU视频处理组件不可用，将使用基础CPU处理")

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
    from src.utils.memory_config import get_memory_config
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

    def __init__(self, use_gpu: bool = True, progress_callback=None):
        """
        初始化剪辑生成器

        Args:
            use_gpu: 是否尝试使用GPU加速（默认True）
            progress_callback: 进度回调函数，签名为 callback(progress: int, message: str)
        """
        # 加载配置
        self.config = self._load_config()

        # 🆕 保存进度回调
        self.external_progress_callback = progress_callback

        # 创建临时目录
        self.temp_dir = os.path.join(tempfile.gettempdir(), "visionai_clips")
        os.makedirs(self.temp_dir, exist_ok=True)

        # 记录处理的历史
        self.processing_history = []

        # 解析并选择FFmpeg/FFprobe可执行路径（优先使用环境配置）
        self.ffmpeg_cmd = 'ffmpeg'
        self.ffprobe_cmd = 'ffprobe'
        try:
            from ui.config.environment import FFMPEG_PATH, HAS_FFMPEG
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            candidates = [
                os.path.join(base_dir, "tools", "ffmpeg", "bin", "ffmpeg.exe"),
                os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg.exe"),
                os.path.join(base_dir, "ffmpeg", "ffmpeg.exe"),
                os.path.join(base_dir, "bin", "ffmpeg.exe"),
            ] if os.name == 'nt' else [
                os.path.join(base_dir, "tools", "ffmpeg", "bin", "ffmpeg"),
                os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg"),
                os.path.join(base_dir, "ffmpeg", "ffmpeg"),
                os.path.join(base_dir, "bin", "ffmpeg"),
            ]

            resolved = None
            if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
                resolved = FFMPEG_PATH
            elif HAS_FFMPEG and shutil.which('ffmpeg'):
                resolved = shutil.which('ffmpeg')
            else:
                for p in candidates:
                    if os.path.exists(p):
                        resolved = p
                        break

            if resolved:
                self.ffmpeg_cmd = resolved
                logger.info(f"FFmpeg路径已解析: {self.ffmpeg_cmd}")
                # 推断同目录下的 ffprobe 可执行文件
                ffmpeg_dir = os.path.dirname(self.ffmpeg_cmd)
                probe_candidate = os.path.join(ffmpeg_dir, 'ffprobe.exe' if os.name == 'nt' else 'ffprobe')
                if os.path.exists(probe_candidate):
                    self.ffprobe_cmd = probe_candidate
            # 兜底：如果未能从环境推断，尝试系统 PATH
            if shutil.which('ffprobe') and self.ffprobe_cmd == 'ffprobe':
                self.ffprobe_cmd = shutil.which('ffprobe')
        except Exception:
            pass

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
                    'ffmpeg_timeout_sec': 600,
                },
                'processing': {
                    # 片段处理策略：避免碎片化
                    'min_segment_duration': float(os.environ.get('VACL_MIN_SEG_DUR', 3.0)),
                    'gap_merge_threshold': float(os.environ.get('VACL_GAP_MERGE', 0.8)),
                    'max_merged_duration': float(os.environ.get('VACL_MAX_MERGE_DUR', 12.0)),
                    'enforce_time_order': True,
                    'merge_short_segments': True,
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
                'performance': {'threads': 0, 'max_memory': '1024M', 'segment_limit': 50, 'ffmpeg_timeout_sec': 600},
                'processing': {
                    'min_segment_duration': float(os.environ.get('VACL_MIN_SEG_DUR', 3.0)),
                    'gap_merge_threshold': float(os.environ.get('VACL_GAP_MERGE', 0.8)),
                    'max_merged_duration': float(os.environ.get('VACL_MAX_MERGE_DUR', 12.0)),
                    'enforce_time_order': True,
                    'merge_short_segments': True,
                },
                'output': {'format': 'mp4', 'keep_temp_files': False}
            }

    def _check_ffmpeg(self) -> None:
        """检查FFmpeg是否可用"""
        try:
            cmd = [self.ffmpeg_cmd, '-version']
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                # 提取版本信息
                version_line = result.stdout.split('\n')[0]
                logger.info(f"FFmpeg可用: {self.ffmpeg_cmd}")
                logger.debug(f"FFmpeg版本: {version_line}")
            else:
                logger.warning(f"FFmpeg命令返回非零状态，可能无法正常使用: {self.ffmpeg_cmd}")
        except Exception as e:
            logger.error(f"检测FFmpeg失败({self.ffmpeg_cmd}): {str(e)}")
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
                [self.ffmpeg_cmd, '-hide_banner', '-encoders'],
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
                    callback=lambda data: self.optimize_memory(
                        aggressive=(data.get("memory_usage", 0.0) >= get_memory_config().get("aggressive_threshold", 0.85))
                    )
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


    def generate_mixed_video(self, video_path: str, subtitles: List[Dict[str, Any]], output_dir: str) -> str:
        """
        兼容 WorkflowManager：根据字幕片段生成混剪视频，返回输出视频路径
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            pass
        base = os.path.splitext(os.path.basename(video_path))[0]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"{base}_mixed_{stamp}.mp4")
        result = self.generate_clips(video_path, subtitles, output_path)
        if isinstance(result, dict) and result.get("status") == "success":
            return result.get("output_path", output_path)
        if isinstance(result, dict) and "output_path" in result:
            return result["output_path"]
        return output_path

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
                elif 'start_time' in segment and 'end_time' in segment:
                    # 兼容ScreenplayEngineer.import_srt()的键名
                    start_time = float(segment.get('start_time', 0) or 0)
                    end_time = float(segment.get('end_time', 0) or 0)
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


            # 🆕 去碎片化：按时间排序 + 合并过短片段
            proc = self.config.get('processing', {}) or {}
            min_dur = float(proc.get('min_segment_duration', 3.0))
            gap_thres = float(proc.get('gap_merge_threshold', 0.8))
            max_merged = float(proc.get('max_merged_duration', 12.0))
            enforce_order = bool(proc.get('enforce_time_order', True))
            merge_short = bool(proc.get('merge_short_segments', True))
            tail_pad = float(proc.get('tail_safety_pad', 0.0))
            punct_merge_factor = float(proc.get('punctuation_merge_factor', 1.0))
            # 新增：下一段开始前的最小防重叠保护（可配置）
            next_guard = float(proc.get('next_transition_guard', 0.04))

            if enforce_order:
                valid_segments = sorted(valid_segments, key=lambda x: (x['start'], x['end']))
            before_cnt = len(valid_segments)
            # 记录当前处理配置（便于诊断配置是否生效）
            try:
                head_min_gap = float(proc.get('head_transition_min_gap', 0.08))
                logger.info(f"[ProcCfg] min_dur={min_dur}, gap_merge={gap_thres}, max_merge={max_merged}, tail_pad={tail_pad}, no_punct_extra={proc.get('no_punct_tail_extra', 0.10)}, head_min_gap={head_min_gap}, next_guard={next_guard}")
            except Exception:
                pass
            if merge_short and len(valid_segments) > 1:
                nonpunct_gap_min = float(proc.get('min_non_punct_gap_merge', 0.0))
                semantic_soft = float(proc.get('semantic_merge_soft_allowance', 0.0))
                valid_segments = self._merge_and_filter_segments(
                    valid_segments, min_dur, gap_thres, max_merged,
                    enforce_order=enforce_order,
                    punctuation_merge_factor=punct_merge_factor,
                    min_non_punct_gap_merge=nonpunct_gap_min,
                    semantic_merge_soft_allowance=semantic_soft
                )
                try:
                    logger.info(f"[Merge] before={before_cnt}, after={len(valid_segments)}, gap={gap_thres}, max={max_merged}, min={min_dur}, tail_pad={tail_pad}, punct_factor={punct_merge_factor}, nonpunct_min={nonpunct_gap_min}, soft_allow={semantic_soft}")
                except Exception:
                    pass

            # 切割每个有效片段
            prev_final_end = None
            for i, item in enumerate(valid_segments):
                segment = item['segment']
                start_time = item['start']
                end_time = item['end']

                # 头部最小过渡间隙：避免上一段刚结束下一段立刻起（人耳感知为硬切）
                try:
                    head_min_gap = float(proc.get('head_transition_min_gap', 0.08))
                    if prev_final_end is not None and (start_time < prev_final_end + head_min_gap):
                        orig_start = start_time
                        start_time = min(max(prev_final_end + head_min_gap, start_time), max(end_time - 0.05, start_time))
                        try:
                            logger.info(f"[CutPlan] seg#{i:03d} START-ADJ {orig_start:.3f} -> {start_time:.3f} (prev_end={prev_final_end:.3f}, min_gap={head_min_gap:.2f})")
                        except Exception:
                            pass
                except Exception:
                    pass

                # 末尾安全缓冲：统一为所有片段追加最小尾部缓冲；若无句末标点则再追加少量额外缓冲，避免“话未完即切”
                try:
                    # 基础缓冲（对所有片段生效）与“无句末标点”额外缓冲
                    univ_pad = max(0.0, float(proc.get('tail_safety_pad', 0.0)))
                    extra_no_punct = max(0.0, float(proc.get('no_punct_tail_extra', 0.10)))
                    # 新增：允许当前段尾部超过下一段原始起点的最大宽容（秒），由下一段起点自动后移保障自然过渡
                    allow_beyond_next = max(0.0, float(proc.get('allow_end_beyond_next_max', 0.20)))

                    txt = str((segment or {}).get('text', '')).strip()
                    ends_with_punct = False
                    if txt:
                        last = txt[-1]
                        ends_with_punct = last in ('。', '！', '？', '.', '!', '?', '」', '』', '”', '’', '》', '】', ')', '）', ']', '］')
                        # 若引号未闭合或以省略符结尾，视为未完句
                        try:
                            if (txt.count('“') > txt.count('”')) or (txt.count('‘') > txt.count('’')):
                                ends_with_punct = False
                            if txt.endswith('…') or txt.endswith('...'):
                                ends_with_punct = False
                        except Exception:
                            pass

                    nxt_start = valid_segments[i+1]['start'] if (i + 1) < len(valid_segments) else video_info.get('duration', end_time)

                    # 原始结束时间提示（若存在）
                    try:
                        orig_end_hint = None
                        seg_meta = segment or {}
                        if 'original_end' in seg_meta:
                            orig_end_hint = self._parse_srt_time(seg_meta.get('original_end'))
                        elif 'original_time' in seg_meta:
                            orig_end_hint = float(seg_meta.get('original_time', {}).get('end'))
                    except Exception:
                        orig_end_hint = None

                    orig_end = end_time
                    # 基础目标端点：统一追加基础尾部缓冲
                    target_end = end_time + univ_pad
                    # 若无句末标点，额外放宽一点点缓冲
                    if not ends_with_punct:
                        target_end += extra_no_punct
                    # 若存在原始结束时间提示，优先不短于其+少量缓冲
                    if isinstance(orig_end_hint, (int, float)) and orig_end_hint:
                        target_end = max(target_end, orig_end_hint + 0.15)

                    # 修复：不再让当前片段的结束时间受下一片段开始时间的影响。
                    # 片段间的重叠问题由后续处理下一片段的 start_time 的逻辑来解决，
                    # 从而确保当前片段的尾部安全缓冲（tail_safety_pad）始终生效。
                    # 同时确保不超过视频总时长。
                    video_dur = float(video_info.get('duration', end_time) or end_time)
                    end_time = min(target_end, video_dur)

                    # 记录剪辑计划日志，便于定位边界
                    try:
                        final_duration = max(0.0, end_time - start_time)
                        extra_tag = f"+{extra_no_punct:.2f}" if not ends_with_punct else ""
                        logger.info(f"[CutPlan] seg#{i:03d} {start_time:.3f}->{orig_end:.3f} -> {end_time:.3f} dur={final_duration:.3f} pad={univ_pad:.2f}{extra_tag} next={nxt_start:.3f} allow_beyond={allow_beyond_next:.2f} punct={ends_with_punct}")
                    except Exception:
                        pass
                except Exception:
                    pass

                # 记录上一段的最终结束时间，供下一段起点平滑调整
                try:
                    prev_final_end = end_time
                except Exception:
                    prev_final_end = end_time

                # 计算时长
                duration = end_time - start_time

                # 严格过滤过短片段，避免碎片化
                if duration < min_dur:
                    logger.debug(f"skip short segment: {duration:.2f}s @ {start_time:.2f}-{end_time:.2f}")
                    continue

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
                self.ffprobe_cmd,
                '-v', 'error',
                '-show_entries', 'format=duration : stream=width,height,codec_type',
                '-of', 'json',
                video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)

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
                self.ffprobe_cmd,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)

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

        修复说明：
        1. 启用精准切割模式（precise_cut）避免关键帧对齐导致的台词截断
        2. 添加头部安全缓冲（head_safety_pad）确保台词开头不被截断
        3. 使用 -ss 在 -i 之后的模式，确保精确到帧的切割

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
            proc = self.config.get('processing', {}) or {}

            # 🔧 修复：默认启用精准切割，避免关键帧对齐问题
            precise_cut = bool(proc.get('precise_cut', True))  # 默认改为True

            # 🔧 修复：添加头部安全缓冲，确保台词开头不被截断
            head_safety_pad = float(proc.get('head_safety_pad', 0.15))  # 默认150ms

            # 应用头部缓冲：向前延伸起点，确保不会截断台词开头
            adjusted_start = max(0.0, start_time - head_safety_pad)
            adjusted_duration = duration + (start_time - adjusted_start)

            end_ts = adjusted_start + adjusted_duration

            # 记录调整信息
            if head_safety_pad > 0 and start_time > 0:
                logger.debug(f"[CutAdj] 原始: {start_time:.3f}s, 调整后: {adjusted_start:.3f}s, "
                           f"头部缓冲: {head_safety_pad:.3f}s, 时长: {duration:.3f}s -> {adjusted_duration:.3f}s")

            #[object Object]根据GPU可用性选择编码器
            if self.gpu_available:
                if not precise_cut:
                    # 快速模式（不推荐，可能截断台词）
                    cmd = [
                        self.ffmpeg_cmd,
                        '-hide_banner',
                        '-loglevel', 'warning',
                        '-hwaccel', 'cuda',
                        '-hwaccel_output_format', 'cuda',
                        '-ss', str(adjusted_start),  # 🔧 使用调整后的起点
                        '-i', input_path,
                        '-t', str(adjusted_duration),  # 🔧 使用调整后的时长
                        '-c:v', 'h264_nvenc',
                        '-preset', 'fast',
                        '-crf', str(video_settings.get('crf', 23)),
                        '-c:a', audio_settings.get('codec', 'aac'),
                        '-b:a', audio_settings.get('bitrate', '128k'),
                        '-avoid_negative_ts', '1',
                        '-y', output_path
                    ]
                else:
                    # 🔧 精准切割模式（推荐）：先输入，再精确定位
                    # 这种模式确保精确到帧的切割，避免关键帧对齐问题
                    cmd = [
                        self.ffmpeg_cmd,
                        '-hide_banner',
                        '-loglevel', 'warning',
                        '-hwaccel', 'cuda',
                        '-hwaccel_output_format', 'cuda',
                        '-i', input_path,
                        '-ss', str(adjusted_start),  # 🔧 使用调整后的起点
                        '-to', str(end_ts),  # 使用绝对结束时间
                        '-c:v', 'h264_nvenc',
                        '-preset', 'fast',
                        '-crf', str(video_settings.get('crf', 23)),
                        '-c:a', audio_settings.get('codec', 'aac'),
                        '-b:a', audio_settings.get('bitrate', '128k'),
                        '-avoid_negative_ts', '1',
                        '-copyts',  # 🔧 保持原始时间戳，提高精度
                        '-y', output_path
                    ]
            else:
                # CPU模式
                if not precise_cut:
                    # 快速模式（不推荐，可能截断台词）
                    cmd = [
                        self.ffmpeg_cmd,
                        '-hide_banner',
                        '-loglevel', 'warning',
                        '-threads', str(performance.get('threads', 0)),
                        '-ss', str(adjusted_start),  # 🔧 使用调整后的起点
                        '-i', input_path,
                        '-t', str(adjusted_duration),  # 🔧 使用调整后的时长
                        '-c:v', video_settings.get('codec', 'libx264'),
                        '-crf', str(video_settings.get('crf', 23)),
                        '-preset', video_settings.get('preset', 'medium'),
                        '-c:a', audio_settings.get('codec', 'aac'),
                        '-b:a', audio_settings.get('bitrate', '128k'),
                        '-avoid_negative_ts', '1',
                        '-y', output_path
                    ]
                else:
                    # 🔧 精准切割模式（推荐）
                    cmd = [
                        self.ffmpeg_cmd,
                        '-hide_banner',
                        '-loglevel', 'warning',
                        '-threads', str(performance.get('threads', 0)),
                        '-i', input_path,
                        '-ss', str(adjusted_start),  # 🔧 使用调整后的起点
                        '-to', str(end_ts),  # 使用绝对结束时间
                        '-c:v', video_settings.get('codec', 'libx264'),
                        '-crf', str(video_settings.get('crf', 23)),
                        '-preset', video_settings.get('preset', 'medium'),
                        '-c:a', audio_settings.get('codec', 'aac'),
                        '-b:a', audio_settings.get('bitrate', '128k'),
                        '-avoid_negative_ts', '1',
                        '-copyts',  # 🔧 保持原始时间戳，提高精度
                        '-y', output_path
                    ]

            # 如果设置了分辨率

                # 可选：片段级音频淡入淡出，降低硬切的突兀感
                audio_proc = self.config.get('audio_processing', {}) or {}
                enable_fade = bool(audio_proc.get('enable_audio_fade', False))
                if enable_fade:
                    try:
                        fi_ms = int(audio_proc.get('fade_in_ms', 0) or 0)
                        fo_ms = int(audio_proc.get('fade_out_ms', 0) or 0)
                        fi = max(0.0, fi_ms / 1000.0)
                        fo = max(0.0, fo_ms / 1000.0)
                        if duration > (fi + fo + 0.10):
                            # 将 -af 插入到输出参数之前
                            insert_at = len(cmd) - 2  # 在 '-y', output_path 之前
                            st_out = max(fi, 0.05)
                            st_in = 0.0
                            filt = f"afade=t=in:st={st_in:.2f}:d={fi:.2f},afade=t=out:st={duration-fo:.2f}:d={fo:.2f}"
                            cmd[insert_at:insert_at] = ['-af', filt]
                    except Exception:
                        pass

            resolution = video_settings.get('resolution')
            if resolution:
                cmd.extend(['-s', resolution])

            # 记录命令关键信息便于诊断
            try:
                ss_idx = cmd.index('-ss') + 1 if '-ss' in cmd else None
                t_idx = cmd.index('-t') + 1 if '-t' in cmd else None
                to_idx = cmd.index('-to') + 1 if '-to' in cmd else None
                ss_val = cmd[ss_idx] if ss_idx else 'N/A'
                t_val = cmd[t_idx] if t_idx else 'N/A'
                to_val = cmd[to_idx] if to_idx else 'N/A'
                logger.info(f"[FFMPEG] ss={ss_val} t={t_val} to={to_val} gpu={self.gpu_available}")
            except Exception:
                pass

            # 执行命令
            timeout_sec = int(self.config['performance'].get('ffmpeg_timeout_sec', 600))
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                logger.error(f"切割片段超时({timeout_sec}s): start={start_time}, duration={duration}")
                if self.gpu_available:
                    logger.warning("GPU切割超时，回退到CPU模式重试一次")
                    self.gpu_available = False
                    return self._cut_segment(input_path, output_path, start_time, duration)
                return False

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
                    self.ffmpeg_cmd,
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
                    self.ffmpeg_cmd,
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
            timeout_sec = int(self.config['performance'].get('ffmpeg_timeout_sec', 600))
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                logger.error(f"拼接视频超时({timeout_sec}s): 列表={list_file_path}")
                if self.gpu_available:
                    logger.warning("GPU拼接超时，回退到CPU模式重试一次")
                    self.gpu_available = False
                    return self._concat_videos_from_list(list_file_path, output_path)
                return False

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


    def _merge_and_filter_segments(self,
                                   items: List[Dict[str, Any]],
                                   min_dur: float,
                                   gap_thres: float,
                                   max_merged: float,
                                   enforce_order: bool = True,
                                   punctuation_merge_factor: float = 1.0,
                                   min_non_punct_gap_merge: float = 0.0,
                                   semantic_merge_soft_allowance: float = 0.0) -> List[Dict[str, Any]]:
        """
        Normalize, merge and filter short/adjacent segments to reduce fragmentation.
        items: [{'segment': dict, 'start': float, 'end': float}, ...]
        Returns the same shape, sorted if enforce_order.
        """
        if not items:
            return []

        # Defensive copy
        segs = [dict(segment=it.get('segment'), start=float(it.get('start', 0.0)), end=float(it.get('end', 0.0))) for it in items]

        # Ensure sane ordering and non-negative durations
        for it in segs:
            s, e = float(it.get('start', 0.0)), float(it.get('end', 0.0))
            if e < s:
                s, e = e, s
            it['start'], it['end'] = s, e

        if enforce_order:
            segs.sort(key=lambda x: (x['start'], x['end']))

        merged: List[Dict[str, Any]] = []
        for cur in segs:
            s, e = cur['start'], cur['end']
            if not merged:
                merged.append(cur)
                continue

            prev = merged[-1]
            gap = max(0.0, s - float(prev['end']))
            cur_dur = max(0.0, e - s)
            prev_dur = max(0.0, float(prev['end']) - float(prev['start']))

            # Merge when: close enough OR any side is too short; and the merged duration would not exceed max_merged
            would_merged_len = max(float(prev['end']), e) - float(prev['start'])
            can_merge = (gap <= gap_thres) and (would_merged_len <= max_merged)

            # 语义友好：若上一段结尾无句末标点，则放宽合并距离
            if not can_merge:
                try:
                    pseg = prev.get('segment') or {}
                    cseg = cur.get('segment') or {}
                    t1 = str(pseg.get('text', '')).strip()
                    # 是否同集（如有该字段才判断）
                    ep_ok = True
                    try:
                        pe = pseg.get('episode'); ce = cseg.get('episode')
                        if pe is not None and ce is not None:
                            ep_ok = (str(pe) == str(ce))
                    except Exception:
                        ep_ok = True
                    ends_with_punct = False
                    if t1:
                        last = t1[-1]
                        ends_with_punct = last in ('。','！','？','.','!','?','』','」','”','’','》','】',')','）',']','］')
                        # 若引号未闭合，视为未完句，允许更积极合并
                        try:
                            if (t1.count('“') > t1.count('”')) or (t1.count('‘') > t1.count('’')):
                                ends_with_punct = False
                        except Exception:
                            pass
                    if not ends_with_punct and ep_ok:
                        allow_gap = gap_thres * max(1.0, float(punctuation_merge_factor or 1.0))
                        allow_gap = max(allow_gap, float(min_non_punct_gap_merge or 0.0))
                        soft_limit = max_merged + float(semantic_merge_soft_allowance or 0.0)
                        if (gap <= allow_gap) and (would_merged_len <= soft_limit):
                            can_merge = True
                except Exception:
                    pass

            if can_merge or prev_dur < min_dur or cur_dur < min_dur:
                # Merge metadata best-effort
                prev['start'] = min(float(prev['start']), s)
                prev['end'] = max(float(prev['end']), e)

                pseg = prev.get('segment') or {}
                cseg = cur.get('segment') or {}
                if isinstance(pseg, dict) and isinstance(cseg, dict):
                    try:
                        if ('start_time' in cseg) or ('start_time' in pseg):
                            pseg['start_time'] = float(cseg.get('start_time', pseg.get('start_time', prev['start'])))
                        if ('end_time' in cseg) or ('end_time' in pseg):
                            pseg['end_time'] = float(cseg.get('end_time', pseg.get('end_time', prev['end'])))
                        if ('original_start' in cseg) or ('original_start' in pseg):
                            pseg['original_start'] = float(cseg.get('original_start', pseg.get('original_start', prev['start'])))
                        if ('original_end' in cseg) or ('original_end' in pseg):
                            pseg['original_end'] = float(cseg.get('original_end', pseg.get('original_end', prev['end'])))
                    except Exception:
                        pass

                    # merge text
                    try:
                        t1 = str(pseg.get('text', '')).strip()
                        t2 = str(cseg.get('text', '')).strip()
                        if t1 and t2:
                            pseg['text'] = f"{t1} {t2}"
                        elif t2:
                            pseg['text'] = t2
                        else:
                            pseg['text'] = t1
                    except Exception:
                        pass

                    # keep minimal sequence_index if present
                    try:
                        si1 = int(pseg.get('sequence_index', 10**9))
                        si2 = int(cseg.get('sequence_index', 10**9))
                        pseg['sequence_index'] = min(si1, si2)
                    except Exception:
                        pass

                    prev['segment'] = pseg

                merged[-1] = prev
            else:
                merged.append(cur)

        # Final filter by min duration and optional sorting
        cleaned = [m for m in merged if max(0.0, float(m['end']) - float(m['start'])) >= min_dur]
        if enforce_order:
            cleaned.sort(key=lambda x: (x['start'], x['end']))
        return cleaned

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


    async def generate_async(
        self,
        video_path: str,
        srt_path: str,
        quant_level: Optional[str] = None,
        lang: str = "auto",
        max_duration: Optional[float] = None,
        narrative_focus: Optional[str] = None,
        temperature: Optional[float] = None,
        preserve_segments: Optional[bool] = None,
        export_format: Optional[str] = None,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """异步包装：在后台线程中调用同步生成逻辑。
        兼容 API 层对 ClipGenerator.generate_async(...) 的调用。
        """
        # 进度回调工具
        def _notify(p: float):
            try:
                if callable(progress_callback):
                    progress_callback(float(max(0.0, min(1.0, p))))
                if callable(self.external_progress_callback):
                    self.external_progress_callback(float(max(0.0, min(1.0, p))), "processing")
            except Exception:
                pass

        _notify(0.05)

        # 规划输出目录与文件名
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            output_dir = os.path.join(base_dir, "outputs")
            os.makedirs(output_dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(video_path))[0] or "output"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"{base}_mixed_{stamp}.mp4")
        except Exception:
            # 兜底：使用临时目录
            output_path = os.path.join(self.temp_dir, f"output_{int(time.time())}.mp4")
        _notify(0.1)

        # 在后台线程中执行同步逻辑
        import asyncio as _asyncio
        try:
            to_thread = getattr(_asyncio, "to_thread", None)
            if to_thread:
                result = await to_thread(self.generate_from_srt, video_path, srt_path, output_path)
            else:
                loop = _asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: self.generate_from_srt(video_path, srt_path, output_path))
        except Exception as e:
            # 执行失败
            _notify(0.0)
            raise e

        _notify(0.9)

        if not isinstance(result, dict) or result.get("status") != "success":
            err = result.get("error") if isinstance(result, dict) else str(result)
            raise RuntimeError(err or "生成失败")

        # 构造API需要的结果字段
        resp: Dict[str, Any] = {
            "video_path": result.get("output_path", output_path),
        }
        metrics = {}
        if "processing_time" in result:
            metrics["processing_time"] = result["processing_time"]
        if "segments_count" in result:
            metrics["segments_count"] = result["segments_count"]
        if metrics:
            resp["metrics"] = metrics

        # 项目工程导出（如有需要，后续可扩展 export_format == "project" / "both"）
        resp.setdefault("project_path", None)

        _notify(1.0)
        return resp


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

        # 🆕 调用外部进度回调（如果有）
        if self.external_progress_callback:
            try:
                self.external_progress_callback(progress_percent, message)
            except Exception as e:
                logger.warning(f"外部进度回调失败: {e}")

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
                freed_mb = max(before - after, 0.0)
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


# 创建全局单例（惰性初始化，避免导入期触发重依赖）
_clipgen_singleton = None

def get_clip_generator() -> "ClipGenerator":
    global _clipgen_singleton
    if _clipgen_singleton is None:
        try:
            _clipgen_singleton = ClipGenerator(use_gpu=False)
        except Exception as e:
            logger.warning(f"初始化 ClipGenerator 降级: {e}")
            _clipgen_singleton = ClipGenerator(use_gpu=False)
    return _clipgen_singleton

def generate_clips(video_path: str, subtitle_segments: List[Dict[str, Any]],
                  output_path: str) -> Dict[str, Any]:
    """便捷函数，生成混剪视频"""
    return get_clip_generator().generate_clips(video_path, subtitle_segments, output_path)

def generate_from_srt(video_path: str, srt_path: str, output_path: str) -> Dict[str, Any]:
    """便捷函数，根据SRT字幕文件生成混剪视频"""
    return get_clip_generator().generate_from_srt(video_path, srt_path, output_path)

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
