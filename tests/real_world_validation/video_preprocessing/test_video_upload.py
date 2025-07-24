#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 真实视频上传测试模块

此模块测试系统对真实视频文件的上传、验证和预处理能力。
验证多种格式支持、文件完整性检查、分辨率处理等关键功能。
"""

import os
import sys
import json
import time
import logging
import hashlib
import unittest
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.video_uploader import VideoUploader
from src.core.video_processor import VideoProcessor
from src.core.format_validator import FormatValidator
from src.utils.log_handler import LogHandler
from src.utils.file_checker import FileChecker

logger = logging.getLogger(__name__)


@dataclass
class VideoUploadResult:
    """视频上传测试结果数据类"""
    test_name: str
    video_file_path: str
    upload_success: bool
    upload_time: float
    file_size_mb: float
    format_validation: Dict[str, Any]
    integrity_check: Dict[str, Any]
    preprocessing_result: Dict[str, Any]
    performance_metrics: Dict[str, float]
    error_messages: List[str]
    warnings: List[str]
    success: bool


class RealWorldVideoUploadTester:
    """真实世界视频上传测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化视频上传测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.video_uploader = VideoUploader()
        self.video_processor = VideoProcessor()
        self.format_validator = FormatValidator()
        self.file_checker = FileChecker()
        
        # 测试配置
        self.supported_formats = self.config.get('test_data', {}).get('supported_formats', [])
        self.supported_resolutions = self.config.get('test_data', {}).get('supported_resolutions', [])
        
        # 性能标准
        self.performance_standards = self.config.get('quality_standards', {}).get('performance', {})
        
        # 测试结果存储
        self.test_results = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/real_world_validation/real_world_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_environment': {'log_level': 'INFO'},
            'test_data': {
                'supported_formats': ['mp4', 'mov', 'avi', 'mkv'],
                'supported_resolutions': ['1920x1080', '1280x720', '854x480']
            },
            'quality_standards': {
                'performance': {
                    'max_response_time_seconds': 2,
                    'max_memory_usage_gb': 4.0
                }
            }
        }
    
    def test_real_video_upload(self, video_file_path: str) -> VideoUploadResult:
        """
        测试真实视频文件上传
        
        Args:
            video_file_path: 真实视频文件路径
            
        Returns:
            VideoUploadResult: 上传测试结果
        """
        test_name = "real_video_upload"
        start_time = time.time()
        
        self.logger.info(f"开始测试真实视频上传: {video_file_path}")
        
        error_messages = []
        warnings = []
        
        try:
            # 验证文件存在
            if not os.path.exists(video_file_path):
                raise FileNotFoundError(f"视频文件不存在: {video_file_path}")
            
            # 获取文件基本信息
            file_size_bytes = os.path.getsize(video_file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # 1. 格式验证
            format_validation = self._validate_video_format(video_file_path)
            if not format_validation['valid']:
                error_messages.extend(format_validation['errors'])
            
            # 2. 文件完整性检查
            integrity_check = self._check_file_integrity(video_file_path)
            if not integrity_check['valid']:
                error_messages.extend(integrity_check['errors'])
            
            # 3. 执行上传
            upload_result = self._perform_upload(video_file_path)
            upload_success = upload_result['success']
            
            if not upload_success:
                error_messages.extend(upload_result.get('errors', []))
            
            # 4. 预处理测试
            preprocessing_result = self._test_preprocessing(video_file_path)
            if not preprocessing_result['success']:
                error_messages.extend(preprocessing_result.get('errors', []))
            
            # 5. 性能指标收集
            performance_metrics = self._collect_performance_metrics(start_time)
            
            # 检查性能标准
            if performance_metrics.get('upload_time', 0) > self.performance_standards.get('max_response_time_seconds', 2):
                warnings.append(f"上传时间超过标准: {performance_metrics['upload_time']:.2f}秒")
            
            upload_time = time.time() - start_time
            success = upload_success and len(error_messages) == 0
            
            result = VideoUploadResult(
                test_name=test_name,
                video_file_path=video_file_path,
                upload_success=upload_success,
                upload_time=upload_time,
                file_size_mb=file_size_mb,
                format_validation=format_validation,
                integrity_check=integrity_check,
                preprocessing_result=preprocessing_result,
                performance_metrics=performance_metrics,
                error_messages=error_messages,
                warnings=warnings,
                success=success
            )
            
            self.test_results.append(result)
            self.logger.info(f"视频上传测试完成: {video_file_path}, 成功: {success}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"视频上传测试异常: {video_file_path}, 错误: {str(e)}")
            
            return VideoUploadResult(
                test_name=test_name,
                video_file_path=video_file_path,
                upload_success=False,
                upload_time=time.time() - start_time,
                file_size_mb=0.0,
                format_validation={'valid': False, 'errors': [str(e)]},
                integrity_check={'valid': False, 'errors': [str(e)]},
                preprocessing_result={'success': False, 'errors': [str(e)]},
                performance_metrics={},
                error_messages=[str(e)],
                warnings=[],
                success=False
            )
    
    def _validate_video_format(self, video_file_path: str) -> Dict[str, Any]:
        """验证视频格式"""
        try:
            # 获取文件扩展名
            file_extension = Path(video_file_path).suffix.lower().lstrip('.')
            
            errors = []
            
            # 检查格式支持
            if file_extension not in self.supported_formats:
                errors.append(f"不支持的视频格式: {file_extension}")
            
            # 使用格式验证器进行详细验证
            validation_result = self.format_validator.validate_video_file(video_file_path)
            
            if not validation_result.get('valid', False):
                errors.extend(validation_result.get('errors', []))
            
            # 获取视频信息
            video_info = self.video_processor.get_video_info(video_file_path)
            
            # 验证分辨率
            resolution = f"{video_info.get('width', 0)}x{video_info.get('height', 0)}"
            if resolution not in self.supported_resolutions and video_info.get('width', 0) > 0:
                # 检查是否为支持的分辨率的变体
                supported = False
                for supported_res in self.supported_resolutions:
                    if self._is_resolution_compatible(resolution, supported_res):
                        supported = True
                        break
                
                if not supported:
                    errors.append(f"不支持的分辨率: {resolution}")
            
            # 验证编码格式
            video_codec = video_info.get('video_codec', '')
            audio_codec = video_info.get('audio_codec', '')
            
            supported_video_codecs = ['h264', 'h265', 'vp9', 'av1']
            supported_audio_codecs = ['aac', 'mp3', 'wav', 'opus']
            
            if video_codec.lower() not in supported_video_codecs:
                errors.append(f"不支持的视频编码: {video_codec}")
            
            if audio_codec and audio_codec.lower() not in supported_audio_codecs:
                errors.append(f"不支持的音频编码: {audio_codec}")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'video_info': video_info,
                'format': file_extension,
                'resolution': resolution,
                'video_codec': video_codec,
                'audio_codec': audio_codec
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"格式验证异常: {str(e)}"],
                'video_info': {},
                'format': '',
                'resolution': '',
                'video_codec': '',
                'audio_codec': ''
            }
    
    def _check_file_integrity(self, video_file_path: str) -> Dict[str, Any]:
        """检查文件完整性"""
        try:
            errors = []
            
            # 1. 文件大小检查
            file_size = os.path.getsize(video_file_path)
            if file_size == 0:
                errors.append("文件大小为0")
            elif file_size < 1024:  # 小于1KB
                errors.append("文件大小异常小")
            
            # 2. 文件头检查
            header_check = self._check_file_header(video_file_path)
            if not header_check['valid']:
                errors.extend(header_check['errors'])
            
            # 3. 文件完整性验证
            integrity_check = self.file_checker.check_file_integrity(video_file_path)
            if not integrity_check:
                errors.append("文件完整性验证失败")
            
            # 4. 视频流完整性检查
            stream_check = self._check_video_streams(video_file_path)
            if not stream_check['valid']:
                errors.extend(stream_check['errors'])
            
            # 5. 计算文件校验和
            checksum = self._calculate_file_checksum(video_file_path)
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'file_size': file_size,
                'header_check': header_check,
                'stream_check': stream_check,
                'checksum': checksum
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"完整性检查异常: {str(e)}"],
                'file_size': 0,
                'header_check': {'valid': False},
                'stream_check': {'valid': False},
                'checksum': ''
            }
    
    def _check_file_header(self, video_file_path: str) -> Dict[str, Any]:
        """检查文件头"""
        try:
            with open(video_file_path, 'rb') as f:
                header = f.read(16)  # 读取前16字节
            
            errors = []
            
            # 检查常见视频格式的文件头
            if video_file_path.lower().endswith('.mp4'):
                # MP4文件应该包含ftyp box
                if b'ftyp' not in header:
                    errors.append("MP4文件头格式不正确")
            
            elif video_file_path.lower().endswith('.avi'):
                # AVI文件应该以RIFF开头
                if not header.startswith(b'RIFF'):
                    errors.append("AVI文件头格式不正确")
            
            elif video_file_path.lower().endswith('.mov'):
                # MOV文件通常包含特定的原子结构
                if len(header) < 8:
                    errors.append("MOV文件头长度不足")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'header_bytes': header.hex()
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"文件头检查异常: {str(e)}"],
                'header_bytes': ''
            }
    
    def _check_video_streams(self, video_file_path: str) -> Dict[str, Any]:
        """检查视频流"""
        try:
            video_info = self.video_processor.get_video_info(video_file_path)
            
            errors = []
            
            # 检查是否有视频流
            if not video_info.get('has_video', False):
                errors.append("文件中没有视频流")
            
            # 检查视频时长
            duration = video_info.get('duration', 0)
            if duration <= 0:
                errors.append("视频时长无效")
            elif duration < 1:  # 少于1秒
                errors.append("视频时长过短")
            
            # 检查帧率
            frame_rate = video_info.get('frame_rate', 0)
            if frame_rate <= 0:
                errors.append("帧率无效")
            elif frame_rate < 1 or frame_rate > 120:
                errors.append(f"帧率异常: {frame_rate}")
            
            # 检查分辨率
            width = video_info.get('width', 0)
            height = video_info.get('height', 0)
            if width <= 0 or height <= 0:
                errors.append("分辨率无效")
            elif width < 160 or height < 120:  # 最小分辨率检查
                errors.append(f"分辨率过小: {width}x{height}")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'video_info': video_info
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"视频流检查异常: {str(e)}"],
                'video_info': {}
            }
    
    def _calculate_file_checksum(self, video_file_path: str) -> str:
        """计算文件校验和"""
        try:
            hash_md5 = hashlib.md5()
            with open(video_file_path, 'rb') as f:
                # 分块读取以处理大文件
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _perform_upload(self, video_file_path: str) -> Dict[str, Any]:
        """执行视频上传"""
        try:
            upload_start = time.time()
            
            # 使用视频上传器进行上传
            upload_result = self.video_uploader.upload_video(video_file_path)
            
            upload_time = time.time() - upload_start
            
            if upload_result.get('success', False):
                return {
                    'success': True,
                    'upload_time': upload_time,
                    'upload_id': upload_result.get('upload_id', ''),
                    'uploaded_path': upload_result.get('uploaded_path', ''),
                    'errors': []
                }
            else:
                return {
                    'success': False,
                    'upload_time': upload_time,
                    'upload_id': '',
                    'uploaded_path': '',
                    'errors': upload_result.get('errors', ['上传失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'upload_time': 0,
                'upload_id': '',
                'uploaded_path': '',
                'errors': [f"上传异常: {str(e)}"]
            }
    
    def _test_preprocessing(self, video_file_path: str) -> Dict[str, Any]:
        """测试预处理"""
        try:
            preprocessing_start = time.time()
            
            # 执行预处理
            preprocessing_result = self.video_processor.preprocess_video(video_file_path)
            
            preprocessing_time = time.time() - preprocessing_start
            
            if preprocessing_result.get('success', False):
                return {
                    'success': True,
                    'preprocessing_time': preprocessing_time,
                    'processed_info': preprocessing_result.get('processed_info', {}),
                    'optimizations': preprocessing_result.get('optimizations', []),
                    'errors': []
                }
            else:
                return {
                    'success': False,
                    'preprocessing_time': preprocessing_time,
                    'processed_info': {},
                    'optimizations': [],
                    'errors': preprocessing_result.get('errors', ['预处理失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'preprocessing_time': 0,
                'processed_info': {},
                'optimizations': [],
                'errors': [f"预处理异常: {str(e)}"]
            }
    
    def _collect_performance_metrics(self, start_time: float) -> Dict[str, float]:
        """收集性能指标"""
        try:
            import psutil
            
            current_time = time.time()
            
            # 获取系统资源使用情况
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            
            return {
                'total_time': current_time - start_time,
                'upload_time': current_time - start_time,  # 简化处理
                'cpu_usage_percent': cpu_percent,
                'memory_usage_mb': memory_info.used / (1024 * 1024),
                'memory_usage_percent': memory_info.percent,
                'disk_read_mb': disk_io.read_bytes / (1024 * 1024) if disk_io else 0,
                'disk_write_mb': disk_io.write_bytes / (1024 * 1024) if disk_io else 0
            }
            
        except Exception:
            return {
                'total_time': time.time() - start_time,
                'upload_time': 0,
                'cpu_usage_percent': 0,
                'memory_usage_mb': 0,
                'memory_usage_percent': 0,
                'disk_read_mb': 0,
                'disk_write_mb': 0
            }
    
    def _is_resolution_compatible(self, resolution: str, supported_resolution: str) -> bool:
        """检查分辨率兼容性"""
        try:
            # 解析分辨率
            width, height = map(int, resolution.split('x'))
            sup_width, sup_height = map(int, supported_resolution.split('x'))
            
            # 检查宽高比是否相近
            aspect_ratio = width / height
            sup_aspect_ratio = sup_width / sup_height
            
            # 允许5%的宽高比差异
            return abs(aspect_ratio - sup_aspect_ratio) / sup_aspect_ratio <= 0.05
            
        except Exception:
            return False
    
    def test_multiple_video_formats(self, video_files: List[str]) -> List[VideoUploadResult]:
        """测试多种视频格式"""
        results = []
        
        for video_file in video_files:
            try:
                result = self.test_real_video_upload(video_file)
                results.append(result)
            except Exception as e:
                self.logger.error(f"测试视频文件失败: {video_file}, 错误: {str(e)}")
        
        return results


class TestRealWorldVideoUpload(unittest.TestCase):
    """真实世界视频上传测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = RealWorldVideoUploadTester()
        
        # 这里应该设置真实的测试视频文件路径
        cls.test_videos = [
            "tests/real_world_validation/test_data/videos/short_video_5min.mp4",
            "tests/real_world_validation/test_data/videos/medium_video_15min.mov",
            "tests/real_world_validation/test_data/videos/long_video_30min.avi"
        ]
    
    def test_mp4_video_upload(self):
        """测试MP4视频上传"""
        mp4_videos = [v for v in self.test_videos if v.endswith('.mp4')]
        
        for video_file in mp4_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_real_video_upload(video_file)
                    self.assertTrue(result.success, f"MP4视频上传应该成功: {video_file}")
                    self.assertTrue(result.upload_success, "上传操作应该成功")
                    self.assertTrue(result.format_validation['valid'], "格式验证应该通过")
    
    def test_mov_video_upload(self):
        """测试MOV视频上传"""
        mov_videos = [v for v in self.test_videos if v.endswith('.mov')]
        
        for video_file in mov_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_real_video_upload(video_file)
                    self.assertTrue(result.success, f"MOV视频上传应该成功: {video_file}")
    
    def test_avi_video_upload(self):
        """测试AVI视频上传"""
        avi_videos = [v for v in self.test_videos if v.endswith('.avi')]
        
        for video_file in avi_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_real_video_upload(video_file)
                    self.assertTrue(result.success, f"AVI视频上传应该成功: {video_file}")
    
    def test_upload_performance(self):
        """测试上传性能"""
        for video_file in self.test_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_real_video_upload(video_file)
                    
                    # 检查上传时间
                    max_upload_time = 30  # 最大30秒
                    self.assertLess(result.upload_time, max_upload_time, 
                                  f"上传时间应该少于{max_upload_time}秒")
                    
                    # 检查内存使用
                    memory_usage_gb = result.performance_metrics.get('memory_usage_mb', 0) / 1024
                    self.assertLess(memory_usage_gb, 4.0, "内存使用应该少于4GB")


if __name__ == "__main__":
    unittest.main(verbosity=2)
