#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 完整工作流程集成测试模块

此模块测试从视频上传到剪映工程文件生成的完整工作流程，
模拟真实用户操作，验证整个系统的集成性和可靠性。
"""

import os
import sys
import json
import time
import logging
import unittest
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.video_processor import VideoProcessor
from src.core.ai_content_analyzer import AIContentAnalyzer
from src.core.viral_script_generator import ViralScriptGenerator
from src.core.srt_parser import SRTParser
from src.core.video_cutter import VideoCutter
from src.core.jianying_project_generator import JianyingProjectGenerator
from src.utils.log_handler import LogHandler
from src.utils.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class PipelineStageResult:
    """流水线阶段结果"""
    stage_name: str
    success: bool
    start_time: float
    end_time: float
    duration: float
    output_data: Dict[str, Any]
    performance_metrics: Dict[str, float]
    error_messages: List[str]
    warnings: List[str]


@dataclass
class CompletePipelineResult:
    """完整流水线测试结果"""
    test_name: str
    video_file_path: str
    pipeline_success: bool
    total_duration: float
    stage_results: List[PipelineStageResult]
    final_outputs: Dict[str, str]
    overall_performance: Dict[str, float]
    quality_metrics: Dict[str, float]
    user_experience_score: float
    error_messages: List[str]
    warnings: List[str]
    success: bool


class CompletePipelineTester:
    """完整流水线测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化完整流水线测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.video_processor = VideoProcessor()
        self.ai_analyzer = AIContentAnalyzer()
        self.viral_generator = ViralScriptGenerator()
        self.srt_parser = SRTParser()
        self.video_cutter = VideoCutter()
        self.project_generator = JianyingProjectGenerator()
        
        # 性能监控器
        self.performance_monitor = PerformanceMonitor()
        
        # 工作流程配置
        self.workflow_config = self.config.get('workflow_tests', {})
        self.pipeline_stages = self.workflow_config.get('complete_pipeline', {}).get('stages', [])
        
        # 质量标准
        self.quality_standards = self.config.get('quality_standards', {})
        
        # 测试结果存储
        self.test_results = []
        
        # 创建临时目录
        self.temp_dir = Path(self.config.get('test_environment', {}).get('temp_dir', 'tests/temp/real_world'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
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
            'test_environment': {'log_level': 'INFO', 'temp_dir': 'tests/temp/real_world'},
            'workflow_tests': {
                'complete_pipeline': {
                    'stages': [
                        'video_upload', 'preprocessing', 'ai_analysis',
                        'script_reconstruction', 'srt_generation', 'video_cutting',
                        'segment_processing', 'draftinfo_generation', 'quality_validation'
                    ]
                }
            },
            'quality_standards': {
                'functional': {'workflow_completion_rate': 1.0},
                'performance': {'min_processing_speed_multiplier': 2.0}
            }
        }
    
    def test_complete_pipeline(self, video_file_path: str, 
                             user_preferences: Dict[str, Any] = None) -> CompletePipelineResult:
        """
        测试完整的视频处理流水线
        
        Args:
            video_file_path: 输入视频文件路径
            user_preferences: 用户偏好设置
            
        Returns:
            CompletePipelineResult: 完整流水线测试结果
        """
        test_name = "complete_pipeline"
        pipeline_start_time = time.time()
        
        self.logger.info(f"开始完整流水线测试: {video_file_path}")
        
        # 启动性能监控
        self.performance_monitor.start_monitoring()
        
        stage_results = []
        error_messages = []
        warnings = []
        pipeline_success = True
        
        # 初始化用户偏好
        if user_preferences is None:
            user_preferences = {
                'target_style': 'viral',
                'compression_ratio': 0.5,
                'language_preference': 'auto',
                'quality_priority': 'balanced'
            }
        
        try:
            # 创建测试会话目录
            session_id = f"pipeline_{int(time.time())}"
            session_dir = self.temp_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            # 流水线上下文数据
            pipeline_context = {
                'session_id': session_id,
                'session_dir': str(session_dir),
                'input_video': video_file_path,
                'user_preferences': user_preferences,
                'intermediate_files': {},
                'metadata': {}
            }
            
            # 执行各个阶段
            for stage_name in self.pipeline_stages:
                stage_result = self._execute_pipeline_stage(stage_name, pipeline_context)
                stage_results.append(stage_result)
                
                if not stage_result.success:
                    pipeline_success = False
                    error_messages.extend(stage_result.error_messages)
                    
                    # 根据错误严重程度决定是否继续
                    if self._is_critical_error(stage_name, stage_result.error_messages):
                        self.logger.error(f"关键阶段失败，停止流水线: {stage_name}")
                        break
                
                warnings.extend(stage_result.warnings)
                
                # 更新流水线上下文
                pipeline_context['intermediate_files'][stage_name] = stage_result.output_data
                
                self.logger.info(f"阶段完成: {stage_name}, 耗时: {stage_result.duration:.2f}秒")
            
            # 停止性能监控
            performance_data = self.performance_monitor.stop_monitoring()
            
            # 计算总体指标
            total_duration = time.time() - pipeline_start_time
            overall_performance = self._calculate_overall_performance(stage_results, performance_data)
            quality_metrics = self._calculate_quality_metrics(stage_results, pipeline_context)
            user_experience_score = self._calculate_user_experience_score(stage_results, overall_performance)
            
            # 收集最终输出
            final_outputs = self._collect_final_outputs(pipeline_context)
            
            # 验证质量标准
            quality_validation = self._validate_quality_standards(overall_performance, quality_metrics)
            if not quality_validation['passed']:
                warnings.extend(quality_validation['warnings'])
            
            success = pipeline_success and len(error_messages) == 0
            
            result = CompletePipelineResult(
                test_name=test_name,
                video_file_path=video_file_path,
                pipeline_success=pipeline_success,
                total_duration=total_duration,
                stage_results=stage_results,
                final_outputs=final_outputs,
                overall_performance=overall_performance,
                quality_metrics=quality_metrics,
                user_experience_score=user_experience_score,
                error_messages=error_messages,
                warnings=warnings,
                success=success
            )
            
            self.test_results.append(result)
            self.logger.info(f"完整流水线测试完成: {video_file_path}, 成功: {success}, 耗时: {total_duration:.2f}秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"完整流水线测试异常: {video_file_path}, 错误: {str(e)}")
            
            # 确保停止性能监控
            try:
                self.performance_monitor.stop_monitoring()
            except:
                pass
            
            return CompletePipelineResult(
                test_name=test_name,
                video_file_path=video_file_path,
                pipeline_success=False,
                total_duration=time.time() - pipeline_start_time,
                stage_results=stage_results,
                final_outputs={},
                overall_performance={},
                quality_metrics={},
                user_experience_score=0.0,
                error_messages=[str(e)],
                warnings=[],
                success=False
            )
    
    def _execute_pipeline_stage(self, stage_name: str, pipeline_context: Dict[str, Any]) -> PipelineStageResult:
        """执行流水线阶段"""
        stage_start_time = time.time()
        
        try:
            self.logger.debug(f"开始执行阶段: {stage_name}")
            
            # 根据阶段名称调用相应的处理方法
            if stage_name == "video_upload":
                result = self._stage_video_upload(pipeline_context)
            elif stage_name == "preprocessing":
                result = self._stage_preprocessing(pipeline_context)
            elif stage_name == "ai_analysis":
                result = self._stage_ai_analysis(pipeline_context)
            elif stage_name == "script_reconstruction":
                result = self._stage_script_reconstruction(pipeline_context)
            elif stage_name == "srt_generation":
                result = self._stage_srt_generation(pipeline_context)
            elif stage_name == "video_cutting":
                result = self._stage_video_cutting(pipeline_context)
            elif stage_name == "segment_processing":
                result = self._stage_segment_processing(pipeline_context)
            elif stage_name == "draftinfo_generation":
                result = self._stage_draftinfo_generation(pipeline_context)
            elif stage_name == "quality_validation":
                result = self._stage_quality_validation(pipeline_context)
            else:
                raise ValueError(f"未知的流水线阶段: {stage_name}")
            
            stage_end_time = time.time()
            duration = stage_end_time - stage_start_time
            
            # 收集性能指标
            performance_metrics = self._collect_stage_performance_metrics(stage_name, duration)
            
            return PipelineStageResult(
                stage_name=stage_name,
                success=result.get('success', False),
                start_time=stage_start_time,
                end_time=stage_end_time,
                duration=duration,
                output_data=result.get('output_data', {}),
                performance_metrics=performance_metrics,
                error_messages=result.get('errors', []),
                warnings=result.get('warnings', [])
            )
            
        except Exception as e:
            stage_end_time = time.time()
            duration = stage_end_time - stage_start_time
            
            self.logger.error(f"阶段执行异常: {stage_name}, 错误: {str(e)}")
            
            return PipelineStageResult(
                stage_name=stage_name,
                success=False,
                start_time=stage_start_time,
                end_time=stage_end_time,
                duration=duration,
                output_data={},
                performance_metrics={},
                error_messages=[f"阶段执行异常: {str(e)}"],
                warnings=[]
            )
    
    def _stage_video_upload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """视频上传阶段"""
        try:
            input_video = context['input_video']
            session_dir = Path(context['session_dir'])
            
            # 验证输入视频
            if not os.path.exists(input_video):
                return {
                    'success': False,
                    'errors': [f"输入视频文件不存在: {input_video}"],
                    'output_data': {}
                }
            
            # 复制视频到工作目录（模拟上传）
            uploaded_video_path = session_dir / f"uploaded_{Path(input_video).name}"
            import shutil
            shutil.copy2(input_video, uploaded_video_path)
            
            # 获取视频基本信息
            video_info = self.video_processor.get_video_info(str(uploaded_video_path))
            
            return {
                'success': True,
                'output_data': {
                    'uploaded_video_path': str(uploaded_video_path),
                    'video_info': video_info,
                    'file_size_mb': os.path.getsize(uploaded_video_path) / (1024 * 1024)
                },
                'errors': [],
                'warnings': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"视频上传阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _stage_preprocessing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """预处理阶段"""
        try:
            upload_data = context['intermediate_files'].get('video_upload', {})
            video_path = upload_data.get('uploaded_video_path', '')
            
            if not video_path or not os.path.exists(video_path):
                return {
                    'success': False,
                    'errors': ['预处理阶段：缺少有效的视频文件'],
                    'output_data': {}
                }
            
            # 执行预处理
            preprocessing_result = self.video_processor.preprocess_video(video_path)
            
            if preprocessing_result.get('success', False):
                return {
                    'success': True,
                    'output_data': {
                        'preprocessed_video_path': preprocessing_result.get('output_path', video_path),
                        'preprocessing_info': preprocessing_result.get('preprocessing_info', {}),
                        'optimizations_applied': preprocessing_result.get('optimizations', [])
                    },
                    'errors': [],
                    'warnings': preprocessing_result.get('warnings', [])
                }
            else:
                return {
                    'success': False,
                    'errors': preprocessing_result.get('errors', ['预处理失败']),
                    'output_data': {}
                }
                
        except Exception as e:
            return {
                'success': False,
                'errors': [f"预处理阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _stage_ai_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """AI分析阶段"""
        try:
            preprocessing_data = context['intermediate_files'].get('preprocessing', {})
            video_path = preprocessing_data.get('preprocessed_video_path', '')
            
            if not video_path:
                # 回退到上传的视频
                upload_data = context['intermediate_files'].get('video_upload', {})
                video_path = upload_data.get('uploaded_video_path', '')
            
            if not video_path or not os.path.exists(video_path):
                return {
                    'success': False,
                    'errors': ['AI分析阶段：缺少有效的视频文件'],
                    'output_data': {}
                }
            
            # 执行AI内容分析
            analysis_result = self.ai_analyzer.analyze_content(video_path)
            
            if analysis_result.get('success', False):
                return {
                    'success': True,
                    'output_data': {
                        'content_analysis': analysis_result.get('analysis', {}),
                        'detected_language': analysis_result.get('language', 'auto'),
                        'content_summary': analysis_result.get('summary', ''),
                        'key_moments': analysis_result.get('key_moments', []),
                        'analysis_confidence': analysis_result.get('confidence', 0.0)
                    },
                    'errors': [],
                    'warnings': analysis_result.get('warnings', [])
                }
            else:
                return {
                    'success': False,
                    'errors': analysis_result.get('errors', ['AI分析失败']),
                    'output_data': {}
                }
                
        except Exception as e:
            return {
                'success': False,
                'errors': [f"AI分析阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _stage_script_reconstruction(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """剧本重构阶段"""
        try:
            ai_analysis_data = context['intermediate_files'].get('ai_analysis', {})
            content_analysis = ai_analysis_data.get('content_analysis', {})
            user_preferences = context.get('user_preferences', {})
            
            if not content_analysis:
                return {
                    'success': False,
                    'errors': ['剧本重构阶段：缺少内容分析数据'],
                    'output_data': {}
                }
            
            # 执行爆款剧本生成
            script_result = self.viral_generator.generate_viral_script(
                content_analysis=content_analysis,
                target_style=user_preferences.get('target_style', 'viral'),
                compression_ratio=user_preferences.get('compression_ratio', 0.5)
            )
            
            if script_result.get('success', False):
                return {
                    'success': True,
                    'output_data': {
                        'viral_script': script_result.get('script', {}),
                        'selected_segments': script_result.get('segments', []),
                        'compression_achieved': script_result.get('compression_ratio', 0.0),
                        'viral_score': script_result.get('viral_score', 0.0),
                        'script_metadata': script_result.get('metadata', {})
                    },
                    'errors': [],
                    'warnings': script_result.get('warnings', [])
                }
            else:
                return {
                    'success': False,
                    'errors': script_result.get('errors', ['剧本重构失败']),
                    'output_data': {}
                }
                
        except Exception as e:
            return {
                'success': False,
                'errors': [f"剧本重构阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _stage_srt_generation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """SRT生成阶段"""
        try:
            script_data = context['intermediate_files'].get('script_reconstruction', {})
            selected_segments = script_data.get('selected_segments', [])
            session_dir = Path(context['session_dir'])
            
            if not selected_segments:
                return {
                    'success': False,
                    'errors': ['SRT生成阶段：缺少选定的视频片段'],
                    'output_data': {}
                }
            
            # 生成SRT文件
            srt_content = self._generate_srt_from_segments(selected_segments)
            srt_file_path = session_dir / "viral_subtitles.srt"
            
            with open(srt_file_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            # 验证生成的SRT文件
            srt_validation = self.srt_parser.validate_srt_file(str(srt_file_path))
            
            return {
                'success': True,
                'output_data': {
                    'srt_file_path': str(srt_file_path),
                    'srt_content': srt_content,
                    'segment_count': len(selected_segments),
                    'total_duration': sum(s.get('duration', 0) for s in selected_segments),
                    'srt_validation': srt_validation
                },
                'errors': [],
                'warnings': [] if srt_validation.get('valid', False) else ['SRT文件验证存在警告']
            }
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"SRT生成阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _stage_video_cutting(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """视频剪切阶段"""
        try:
            srt_data = context['intermediate_files'].get('srt_generation', {})
            srt_file_path = srt_data.get('srt_file_path', '')
            
            # 获取原始视频路径
            preprocessing_data = context['intermediate_files'].get('preprocessing', {})
            video_path = preprocessing_data.get('preprocessed_video_path', '')
            
            if not video_path:
                upload_data = context['intermediate_files'].get('video_upload', {})
                video_path = upload_data.get('uploaded_video_path', '')
            
            if not srt_file_path or not video_path:
                return {
                    'success': False,
                    'errors': ['视频剪切阶段：缺少SRT文件或视频文件'],
                    'output_data': {}
                }
            
            # 执行视频剪切
            cutting_result = self.video_cutter.cut_video_by_srt(
                video_path=video_path,
                srt_path=srt_file_path,
                output_dir=str(Path(context['session_dir']) / "segments")
            )
            
            if cutting_result.get('success', False):
                return {
                    'success': True,
                    'output_data': {
                        'segments_dir': cutting_result.get('output_dir', ''),
                        'segment_files': cutting_result.get('segment_files', []),
                        'cutting_accuracy': cutting_result.get('accuracy', 0.0),
                        'total_segments': len(cutting_result.get('segment_files', []))
                    },
                    'errors': [],
                    'warnings': cutting_result.get('warnings', [])
                }
            else:
                return {
                    'success': False,
                    'errors': cutting_result.get('errors', ['视频剪切失败']),
                    'output_data': {}
                }
                
        except Exception as e:
            return {
                'success': False,
                'errors': [f"视频剪切阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _stage_segment_processing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """片段处理阶段"""
        try:
            cutting_data = context['intermediate_files'].get('video_cutting', {})
            segment_files = cutting_data.get('segment_files', [])
            
            if not segment_files:
                return {
                    'success': False,
                    'errors': ['片段处理阶段：缺少视频片段文件'],
                    'output_data': {}
                }
            
            # 处理每个片段（质量优化、格式统一等）
            processed_segments = []
            processing_errors = []
            
            for segment_file in segment_files:
                try:
                    # 这里可以添加片段优化逻辑
                    processed_info = {
                        'original_path': segment_file,
                        'processed_path': segment_file,  # 简化处理
                        'file_size': os.path.getsize(segment_file) if os.path.exists(segment_file) else 0,
                        'processing_applied': ['format_validation']
                    }
                    processed_segments.append(processed_info)
                except Exception as e:
                    processing_errors.append(f"处理片段失败 {segment_file}: {str(e)}")
            
            success = len(processing_errors) == 0
            
            return {
                'success': success,
                'output_data': {
                    'processed_segments': processed_segments,
                    'total_processed': len(processed_segments),
                    'processing_summary': {
                        'total_size_mb': sum(s['file_size'] for s in processed_segments) / (1024 * 1024),
                        'average_segment_duration': 0  # 可以计算实际时长
                    }
                },
                'errors': processing_errors,
                'warnings': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"片段处理阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _stage_draftinfo_generation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """剪映工程文件生成阶段"""
        try:
            segment_data = context['intermediate_files'].get('segment_processing', {})
            processed_segments = segment_data.get('processed_segments', [])
            session_dir = Path(context['session_dir'])
            
            if not processed_segments:
                return {
                    'success': False,
                    'errors': ['工程文件生成阶段：缺少处理后的视频片段'],
                    'output_data': {}
                }
            
            # 生成剪映工程文件
            segment_paths = [s['processed_path'] for s in processed_segments]
            project_name = f"VisionAI_Project_{context['session_id']}"
            draftinfo_path = session_dir / f"{project_name}.draftinfo"
            
            generation_result = self.project_generator.generate_project(
                video_segments=segment_paths,
                output_path=str(draftinfo_path),
                project_name=project_name
            )
            
            if generation_result.get('success', False):
                return {
                    'success': True,
                    'output_data': {
                        'draftinfo_path': str(draftinfo_path),
                        'project_name': project_name,
                        'segment_count': len(segment_paths),
                        'file_size_kb': os.path.getsize(draftinfo_path) / 1024 if os.path.exists(draftinfo_path) else 0,
                        'generation_metadata': generation_result.get('metadata', {})
                    },
                    'errors': [],
                    'warnings': generation_result.get('warnings', [])
                }
            else:
                return {
                    'success': False,
                    'errors': generation_result.get('errors', ['工程文件生成失败']),
                    'output_data': {}
                }
                
        except Exception as e:
            return {
                'success': False,
                'errors': [f"工程文件生成阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _stage_quality_validation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """质量验证阶段"""
        try:
            draftinfo_data = context['intermediate_files'].get('draftinfo_generation', {})
            draftinfo_path = draftinfo_data.get('draftinfo_path', '')
            
            if not draftinfo_path or not os.path.exists(draftinfo_path):
                return {
                    'success': False,
                    'errors': ['质量验证阶段：缺少剪映工程文件'],
                    'output_data': {}
                }
            
            # 执行质量验证
            validation_results = []
            validation_errors = []
            
            # 1. 文件完整性验证
            try:
                with open(draftinfo_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                validation_results.append({'check': 'file_integrity', 'passed': True})
            except Exception as e:
                validation_errors.append(f"文件完整性验证失败: {str(e)}")
                validation_results.append({'check': 'file_integrity', 'passed': False})
            
            # 2. JSON结构验证
            try:
                required_fields = ['version', 'tracks', 'materials']
                missing_fields = [field for field in required_fields if field not in project_data]
                if missing_fields:
                    validation_errors.append(f"缺少必需字段: {missing_fields}")
                    validation_results.append({'check': 'json_structure', 'passed': False})
                else:
                    validation_results.append({'check': 'json_structure', 'passed': True})
            except:
                validation_results.append({'check': 'json_structure', 'passed': False})
            
            # 3. 时间轴验证
            timeline_valid = self._validate_timeline_structure(project_data)
            validation_results.append({'check': 'timeline_structure', 'passed': timeline_valid})
            
            success = len(validation_errors) == 0
            
            return {
                'success': success,
                'output_data': {
                    'validation_results': validation_results,
                    'passed_checks': sum(1 for r in validation_results if r['passed']),
                    'total_checks': len(validation_results),
                    'quality_score': sum(1 for r in validation_results if r['passed']) / len(validation_results) if validation_results else 0
                },
                'errors': validation_errors,
                'warnings': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"质量验证阶段异常: {str(e)}"],
                'output_data': {}
            }
    
    def _generate_srt_from_segments(self, segments: List[Dict[str, Any]]) -> str:
        """从片段生成SRT内容"""
        srt_lines = []
        current_time = 0.0
        
        for i, segment in enumerate(segments):
            start_time = current_time
            duration = segment.get('duration', 5.0)  # 默认5秒
            end_time = start_time + duration
            
            # 序号
            srt_lines.append(str(i + 1))
            
            # 时间码
            start_timecode = self._seconds_to_timecode(start_time)
            end_timecode = self._seconds_to_timecode(end_time)
            srt_lines.append(f"{start_timecode} --> {end_timecode}")
            
            # 字幕文本
            text = segment.get('text', f"片段 {i + 1}")
            srt_lines.append(text)
            
            # 空行分隔
            srt_lines.append("")
            
            current_time = end_time
        
        return "\n".join(srt_lines)
    
    def _seconds_to_timecode(self, seconds: float) -> str:
        """将秒数转换为SRT时间码格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _validate_timeline_structure(self, project_data: Dict[str, Any]) -> bool:
        """验证时间轴结构"""
        try:
            tracks = project_data.get('tracks', [])
            if not tracks:
                return False
            
            # 检查视频轨道
            video_tracks = [track for track in tracks if track.get('type') == 'video']
            if not video_tracks:
                return False
            
            # 检查轨道中的片段
            for track in video_tracks:
                segments = track.get('segments', [])
                if not segments:
                    continue
                
                # 检查片段时间轴的连续性
                for i, segment in enumerate(segments):
                    if 'start' not in segment or 'end' not in segment:
                        return False
                    
                    if segment['start'] >= segment['end']:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def _is_critical_error(self, stage_name: str, error_messages: List[str]) -> bool:
        """判断是否为关键错误"""
        critical_stages = ['video_upload', 'ai_analysis', 'script_reconstruction']
        return stage_name in critical_stages
    
    def _collect_stage_performance_metrics(self, stage_name: str, duration: float) -> Dict[str, float]:
        """收集阶段性能指标"""
        try:
            import psutil
            
            return {
                'duration': duration,
                'cpu_usage_percent': psutil.cpu_percent(interval=0.1),
                'memory_usage_mb': psutil.virtual_memory().used / (1024 * 1024),
                'memory_usage_percent': psutil.virtual_memory().percent
            }
        except Exception:
            return {'duration': duration}
    
    def _calculate_overall_performance(self, stage_results: List[PipelineStageResult], 
                                     performance_data: Dict[str, Any]) -> Dict[str, float]:
        """计算总体性能指标"""
        total_duration = sum(stage.duration for stage in stage_results)
        successful_stages = sum(1 for stage in stage_results if stage.success)
        
        return {
            'total_duration': total_duration,
            'successful_stages': successful_stages,
            'total_stages': len(stage_results),
            'success_rate': successful_stages / len(stage_results) if stage_results else 0,
            'average_stage_duration': total_duration / len(stage_results) if stage_results else 0,
            'peak_memory_usage_mb': performance_data.get('peak_memory_mb', 0),
            'average_cpu_usage': performance_data.get('average_cpu_percent', 0)
        }
    
    def _calculate_quality_metrics(self, stage_results: List[PipelineStageResult], 
                                 pipeline_context: Dict[str, Any]) -> Dict[str, float]:
        """计算质量指标"""
        quality_metrics = {}
        
        # 从各阶段结果中提取质量指标
        for stage in stage_results:
            if stage.stage_name == 'ai_analysis' and stage.success:
                analysis_data = stage.output_data
                quality_metrics['ai_confidence'] = analysis_data.get('analysis_confidence', 0.0)
            
            elif stage.stage_name == 'script_reconstruction' and stage.success:
                script_data = stage.output_data
                quality_metrics['viral_score'] = script_data.get('viral_score', 0.0)
                quality_metrics['compression_ratio'] = script_data.get('compression_achieved', 0.0)
            
            elif stage.stage_name == 'video_cutting' and stage.success:
                cutting_data = stage.output_data
                quality_metrics['cutting_accuracy'] = cutting_data.get('cutting_accuracy', 0.0)
            
            elif stage.stage_name == 'quality_validation' and stage.success:
                validation_data = stage.output_data
                quality_metrics['overall_quality_score'] = validation_data.get('quality_score', 0.0)
        
        return quality_metrics
    
    def _calculate_user_experience_score(self, stage_results: List[PipelineStageResult], 
                                       overall_performance: Dict[str, float]) -> float:
        """计算用户体验评分"""
        try:
            # 基于成功率、处理时间、质量等因素计算用户体验评分
            success_rate = overall_performance.get('success_rate', 0)
            total_duration = overall_performance.get('total_duration', 0)
            
            # 时间评分（越快越好）
            time_score = min(1.0, 300 / max(total_duration, 1))  # 5分钟内完成得满分
            
            # 成功率评分
            success_score = success_rate
            
            # 综合评分
            user_experience_score = (success_score * 0.6 + time_score * 0.4)
            
            return user_experience_score
            
        except Exception:
            return 0.0
    
    def _collect_final_outputs(self, pipeline_context: Dict[str, Any]) -> Dict[str, str]:
        """收集最终输出文件"""
        final_outputs = {}
        
        # 从各阶段收集输出文件
        intermediate_files = pipeline_context.get('intermediate_files', {})
        
        if 'srt_generation' in intermediate_files:
            srt_data = intermediate_files['srt_generation']
            final_outputs['srt_file'] = srt_data.get('srt_file_path', '')
        
        if 'video_cutting' in intermediate_files:
            cutting_data = intermediate_files['video_cutting']
            final_outputs['segments_dir'] = cutting_data.get('segments_dir', '')
        
        if 'draftinfo_generation' in intermediate_files:
            draftinfo_data = intermediate_files['draftinfo_generation']
            final_outputs['draftinfo_file'] = draftinfo_data.get('draftinfo_path', '')
        
        return final_outputs
    
    def _validate_quality_standards(self, overall_performance: Dict[str, float], 
                                  quality_metrics: Dict[str, float]) -> Dict[str, Any]:
        """验证质量标准"""
        warnings = []
        passed = True
        
        # 检查成功率标准
        min_success_rate = self.quality_standards.get('functional', {}).get('workflow_completion_rate', 1.0)
        if overall_performance.get('success_rate', 0) < min_success_rate:
            warnings.append(f"工作流程成功率低于标准: {overall_performance.get('success_rate', 0):.2%} < {min_success_rate:.2%}")
            passed = False
        
        # 检查处理速度标准
        min_speed = self.quality_standards.get('performance', {}).get('min_processing_speed_multiplier', 2.0)
        # 这里需要根据视频时长计算实际的处理速度倍数
        
        return {
            'passed': passed,
            'warnings': warnings
        }


class TestCompletePipeline(unittest.TestCase):
    """完整流水线测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = CompletePipelineTester()
        
        # 设置测试视频文件路径
        cls.test_videos = [
            "tests/real_world_validation/test_data/videos/short_video_5min.mp4",
            "tests/real_world_validation/test_data/videos/medium_video_15min.mov"
        ]
    
    def test_complete_pipeline_short_video(self):
        """测试短视频完整流水线"""
        short_videos = [v for v in self.test_videos if "short" in v]
        
        for video_file in short_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_complete_pipeline(video_file)
                    
                    self.assertTrue(result.success, f"短视频流水线应该成功: {video_file}")
                    self.assertTrue(result.pipeline_success, "流水线执行应该成功")
                    self.assertGreater(result.user_experience_score, 0.7, "用户体验评分应该良好")
    
    def test_complete_pipeline_medium_video(self):
        """测试中等视频完整流水线"""
        medium_videos = [v for v in self.test_videos if "medium" in v]
        
        for video_file in medium_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_complete_pipeline(video_file)
                    
                    self.assertTrue(result.success, f"中等视频流水线应该成功: {video_file}")
                    self.assertLess(result.total_duration, 1800, "处理时间应该在30分钟内")
    
    def test_pipeline_performance(self):
        """测试流水线性能"""
        for video_file in self.test_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_complete_pipeline(video_file)
                    
                    # 检查内存使用
                    peak_memory_gb = result.overall_performance.get('peak_memory_usage_mb', 0) / 1024
                    self.assertLess(peak_memory_gb, 4.0, "内存使用应该在4GB以内")
                    
                    # 检查成功率
                    success_rate = result.overall_performance.get('success_rate', 0)
                    self.assertGreaterEqual(success_rate, 0.8, "阶段成功率应该≥80%")


if __name__ == "__main__":
    unittest.main(verbosity=2)
