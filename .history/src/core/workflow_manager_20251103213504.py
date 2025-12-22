#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工作流程管理器
实现完整的"原片+字幕 → 剧本重构 → 混剪视频"工作流程
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .language_detector import LanguageDetector
from .srt_parser import SRTParser
from .narrative_analyzer import IntegratedNarrativeAnalyzer
from .screenplay_engineer import ScreenplayEngineer
from .rhythm_analyzer import RhythmAnalyzer
from .segment_advisor import SegmentAdvisor
from .clip_generator import ClipGenerator
from .input_validator import InputValidator
from ..exporters.jianying_pro_exporter import JianYingProExporter
from ..utils.exceptions import WorkflowError, ValidationError
from ..utils.log_handler import get_logger

logger = get_logger(__name__)

class WorkflowManager:
    """工作流程管理器"""

    def __init__(self, progress_callback=None):
        """初始化工作流程管理器

        Args:
            progress_callback: 进度回调函数，接收参数(current_step, total_steps, description)
        """
        self.progress_callback = progress_callback
        self.language_detector = LanguageDetector()
        self.srt_parser = SRTParser()
        self.narrative_analyzer = IntegratedNarrativeAnalyzer()
        self.screenplay_engineer = ScreenplayEngineer()
        self.rhythm_analyzer = RhythmAnalyzer()
        self.segment_advisor = SegmentAdvisor()
        self.clip_generator = ClipGenerator()
        self.input_validator = InputValidator()
        self.jianying_exporter = JianYingProExporter()

        # 初始化场景分析器
        try:
            from src.alignment.scene_analyzer import SceneAnalyzer
            self.scene_analyzer = SceneAnalyzer(
                min_scene_duration=1.0,
                scene_threshold=30.0,
                use_external_models=False
            )
            logger.info("场景分析器已启用")
        except ImportError as e:
            logger.warning(f"场景分析器导入失败: {e}")
            self.scene_analyzer = None

        self.workflow_state = {
            "current_step": 0,
            "total_steps": 9,  # 从8步增加到9步(添加关键帧提取)
            "status": "ready",
            "start_time": None,
            "end_time": None,
            "results": {}
        }

        logger.info("🎬 工作流程管理器初始化完成")
    
    def execute_full_workflow(self, video_path: str, subtitle_path: str, 
                            output_dir: str = "output", 
                            target_length: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        执行完整工作流程
        
        Args:
            video_path: 原片视频路径
            subtitle_path: 字幕文件路径
            output_dir: 输出目录
            target_length: 目标长度范围(最小秒数, 最大秒数)
            
        Returns:
            Dict: 工作流程结果
        """
        try:
            self.workflow_state["status"] = "running"
            self.workflow_state["start_time"] = datetime.now()
            
            logger.info(f"🚀 开始执行完整工作流程")
            logger.info(f"📹 原片: {video_path}")
            logger.info(f"📝 字幕: {subtitle_path}")
            
            # 步骤1: 输入验证
            self._update_step(1, "输入验证")
            validation_result = self._validate_inputs(video_path, subtitle_path)
            
            # 步骤2: 语言检测
            self._update_step(2, "语言检测")
            language_result = self._detect_language(subtitle_path)
            
            # 步骤3: 字幕解析
            self._update_step(3, "字幕解析")
            parsing_result = self._parse_subtitles(subtitle_path)

            # 步骤4: 关键帧提取
            self._update_step(4, "关键帧提取")
            keyframe_result = self._extract_keyframes(video_path, parsing_result["total_duration"])

            # 步骤5: 场景分析
            self._update_step(5, "场景分析")
            scene_result = self._analyze_scenes(
                video_path,
                parsing_result["subtitles"],
                keyframe_result.get("keyframes", [])
            )

            # 步骤6: 剧情分析
            self._update_step(6, "剧情分析")
            analysis_result = self._analyze_narrative(
                parsing_result["subtitles"],
                scene_result.get("scenes", [])
            )

            # 步骤7: 剧本重构
            self._update_step(7, "剧本重构")
            reconstruction_result = self._reconstruct_screenplay(
                parsing_result["subtitles"],
                analysis_result,
                language_result["language"],
                target_length
            )

            # 步骤8: 视频生成
            self._update_step(8, "视频生成")
            generation_result = self._generate_clips(
                video_path,
                reconstruction_result["new_subtitles"],
                output_dir
            )

            # 步骤9: 导出工程
            self._update_step(9, "导出工程")
            export_result = self._export_project(
                generation_result["output_video"],
                reconstruction_result["new_subtitles"],
                output_dir
            )
            
            # 汇总结果
            final_result = {
                "status": "success",
                "workflow_id": f"workflow_{int(time.time())}",
                "input": {
                    "video_path": video_path,
                    "subtitle_path": subtitle_path,
                    "detected_language": language_result["language"]
                },
                "output": {
                    "mixed_video": generation_result["output_video"],
                    "new_subtitles": reconstruction_result["new_subtitles"],
                    "jianying_project": export_result["project_file"],
                    "output_directory": output_dir
                },
                "statistics": {
                    "original_duration": parsing_result["total_duration"],
                    "final_duration": generation_result["final_duration"],
                    "compression_ratio": generation_result["final_duration"] / parsing_result["total_duration"],
                    "subtitle_count": len(reconstruction_result["new_subtitles"]),
                    "processing_time": (datetime.now() - self.workflow_state["start_time"]).total_seconds()
                },
                "quality_metrics": {
                    "narrative_coherence": analysis_result.get("coherence_score", 0.8),
                    "emotional_impact": analysis_result.get("emotional_score", 0.7),
                    "length_control": self._check_length_control(
                        generation_result["final_duration"], 
                        parsing_result["total_duration"],
                        target_length
                    )
                }
            }
            
            self.workflow_state["status"] = "completed"
            self.workflow_state["end_time"] = datetime.now()
            self.workflow_state["results"] = final_result
            
            logger.info(f"✅ 工作流程执行完成")
            logger.info(f"⏱️ 总耗时: {final_result['statistics']['processing_time']:.2f}秒")
            logger.info(f"🎯 压缩比: {final_result['statistics']['compression_ratio']:.2f}")
            
            return final_result
            
        except Exception as e:
            self.workflow_state["status"] = "failed"
            self.workflow_state["end_time"] = datetime.now()
            logger.error(f"❌ 工作流程执行失败: {e}")
            raise WorkflowError(f"工作流程执行失败: {e}")
    
    def _update_step(self, step: int, description: str):
        """更新当前步骤"""
        self.workflow_state["current_step"] = step
        logger.info(f"📋 步骤 {step}/{self.workflow_state['total_steps']}: {description}")

        # 调用进度回调函数
        if self.progress_callback:
            try:
                self.progress_callback(step, self.workflow_state['total_steps'], description)
            except Exception as e:
                logger.warning(f"进度回调函数执行失败: {e}")
    
    def _validate_inputs(self, video_path: str, subtitle_path: str) -> Dict[str, Any]:
        """验证输入文件"""
        video_valid = self.input_validator.validate_video_file(video_path)
        subtitle_valid = self.input_validator.validate_srt_file(subtitle_path)
        
        if not video_valid:
            raise ValidationError(f"视频文件验证失败: {video_path}")
        if not subtitle_valid:
            raise ValidationError(f"字幕文件验证失败: {subtitle_path}")
        
        return {"video_valid": video_valid, "subtitle_valid": subtitle_valid}
    
    def _detect_language(self, subtitle_path: str) -> Dict[str, Any]:
        """检测语言"""
        language = self.language_detector.detect_from_file(subtitle_path)
        logger.info(f"🌍 检测到语言: {language}")
        return {"language": language}
    
    def _parse_subtitles(self, subtitle_path: str) -> Dict[str, Any]:
        """解析字幕"""
        subtitles = self.srt_parser.parse(subtitle_path)
        total_duration = self.srt_parser.get_total_duration(subtitles)
        logger.info(f"📝 解析字幕: {len(subtitles)}条，总时长: {total_duration:.2f}秒")
        return {"subtitles": subtitles, "total_duration": total_duration}

    def _extract_keyframes(self, video_path: str, video_duration: float) -> Dict[str, Any]:
        """提取关键帧(智能自动化)"""
        try:
            # 延迟导入,避免cv2循环导入
            from src.alignment import extract_keyframes

            # 智能选择提取方法和参数
            method, num_frames, threshold = self._select_keyframe_params(video_duration)

            logger.info(f"🎞️ 开始提取关键帧: 方法={method}, 参数={num_frames if method=='uniform' else threshold}")

            # 提取关键帧(不保存图像,仅用于分析)
            keyframes = extract_keyframes(
                video_path=video_path,
                method=method,
                num_frames=num_frames,
                threshold=threshold,
                save_frames=False
            )

            logger.info(f"✅ 关键帧提取完成: {len(keyframes)}帧")

            return {
                "keyframes": keyframes,
                "keyframe_count": len(keyframes),
                "method": method,
                "video_duration": video_duration
            }

        except Exception as e:
            logger.warning(f"关键帧提取失败: {e}, 继续执行后续步骤")
            return {
                "keyframes": [],
                "keyframe_count": 0,
                "method": "none",
                "video_duration": video_duration
            }

    def _select_keyframe_params(self, video_duration: float) -> tuple:
        """智能选择关键帧提取参数

        根据视频时长自动选择最优的提取方法和参数:
        - 短视频(<5分钟): 均匀提取, 10帧
        - 中等视频(5-30分钟): 差异提取, 阈值35.0
        - 长视频(>30分钟): 场景变化提取, 阈值30.0
        """
        if video_duration < 300:  # 5分钟
            return ('uniform', 10, 30.0)
        elif video_duration < 1800:  # 30分钟
            return ('difference', 20, 35.0)
        else:
            return ('scene', 30, 30.0)

    def _analyze_scenes(self, video_path: str, subtitles: List[Dict], keyframes: List[Dict] = None) -> Dict[str, Any]:
        """分析场景"""
        if self.scene_analyzer is None:
            logger.warning("场景分析器未启用，跳过场景分析")
            return {"scenes": [], "scene_count": 0}

        try:
            # 分析视频场景(自动使用缓存)
            scenes = self.scene_analyzer.analyze_video(
                video_path=video_path,
                subtitle_data=subtitles,
                use_cache=True
            )

            logger.info(f"🎬 场景分析完成: {len(scenes)}个场景")

            # 统计场景类型
            scene_types = {}
            for scene in scenes:
                scene_type = getattr(scene, 'scene_type', 'unknown')
                scene_types[scene_type] = scene_types.get(scene_type, 0) + 1

            return {
                "scenes": scenes,
                "scene_count": len(scenes),
                "scene_types": scene_types
            }

        except Exception as e:
            logger.error(f"场景分析失败: {e}")
            return {"scenes": [], "scene_count": 0, "error": str(e)}

    def _analyze_narrative(self, subtitles: List[Dict], scenes: List = None) -> Dict[str, Any]:
        """分析剧情"""
        analysis = self.narrative_analyzer.analyze_narrative_structure(subtitles)

        # 如果有场景数据,添加到分析结果中
        if scenes:
            analysis["scenes"] = scenes
            analysis["scene_count"] = len(scenes)

        logger.info(f"🎭 剧情分析完成，连贯性评分: {analysis.get('coherence_score', 0.8):.2f}")
        return analysis
    
    def _reconstruct_screenplay(self, subtitles: List[Dict], analysis: Dict, 
                              language: str, target_length: Optional[Tuple[int, int]]) -> Dict[str, Any]:
        """重构剧本"""
        # 使用剧本工程师重构
        new_subtitles = self.screenplay_engineer.reconstruct_screenplay(
            subtitles, analysis, language
        )
        
        # 长度控制
        if target_length:
            new_subtitles = self._apply_length_control(new_subtitles, target_length)
        
        logger.info(f"✂️ 剧本重构完成，生成 {len(new_subtitles)} 个片段")
        return {"new_subtitles": new_subtitles}
    
    def _apply_length_control(self, subtitles: List[Dict], 
                            target_length: Tuple[int, int]) -> List[Dict]:
        """应用长度控制"""
        min_length, max_length = target_length
        
        # 使用节奏分析器优化长度
        optimized_subtitles = self.rhythm_analyzer.optimize_for_length(
            subtitles, min_length, max_length
        )
        
        # 使用片段建议器进一步优化
        final_subtitles = self.segment_advisor.suggest_optimal_segments(
            optimized_subtitles, target_length
        )
        
        return final_subtitles
    
    def _generate_clips(self, video_path: str, subtitles: List[Dict], 
                       output_dir: str) -> Dict[str, Any]:
        """生成视频片段"""
        output_video = self.clip_generator.generate_mixed_video(
            video_path, subtitles, output_dir
        )
        
        final_duration = self.clip_generator.get_video_duration(output_video)
        logger.info(f"🎬 视频生成完成: {output_video}，时长: {final_duration:.2f}秒")
        
        return {"output_video": output_video, "final_duration": final_duration}
    
    def _export_project(self, video_path: str, subtitles: List[Dict], 
                       output_dir: str) -> Dict[str, Any]:
        """导出剪映工程"""
        project_file = self.jianying_exporter.export_project(
            video_path, subtitles, output_dir
        )
        
        logger.info(f"📁 剪映工程导出完成: {project_file}")
        return {"project_file": project_file}
    
    def _check_length_control(self, final_duration: float, original_duration: float,
                            target_length: Optional[Tuple[int, int]]) -> Dict[str, Any]:
        """检查长度控制效果"""
        compression_ratio = final_duration / original_duration
        
        result = {
            "compression_ratio": compression_ratio,
            "is_too_short": compression_ratio < 0.1,  # 压缩比小于10%可能过短
            "is_too_long": compression_ratio > 0.8,   # 压缩比大于80%可能过长
            "meets_target": True
        }
        
        if target_length:
            min_length, max_length = target_length
            result["meets_target"] = min_length <= final_duration <= max_length
        
        return result
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流程状态"""
        return self.workflow_state.copy()
    
    def reset_workflow(self):
        """重置工作流程状态"""
        self.workflow_state = {
            "current_step": 0,
            "total_steps": 9,  # 更新为9步(添加关键帧提取)
            "status": "ready",
            "start_time": None,
            "end_time": None,
            "results": {}
        }
        logger.info("🔄 工作流程状态已重置")
