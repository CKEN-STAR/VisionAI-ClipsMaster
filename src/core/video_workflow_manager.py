#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频工作流管理器
整合字幕重构和视频处理的完整工作流
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

# 导入核心组件
try:
    from .subtitle_reconstruction_service import SubtitleReconstructionService
    from .enhanced_video_processor import EnhancedVideoProcessor
    from ..utils.memory_manager import MemoryManager
    HAS_CORE_COMPONENTS = True
except ImportError as e:
    HAS_CORE_COMPONENTS = False
    logging.warning(f"核心组件导入失败: {e}")

logger = logging.getLogger(__name__)

class VideoWorkflowManager:
    """视频工作流管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化工作流管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.subtitle_service = None
        self.video_processor = None
        self.memory_manager = None
        
        # 工作流状态
        self.current_workflow = None
        self.workflow_history = []
        
        # 进度回调
        self.progress_callback = None
        
        # 初始化服务
        self._initialize_services()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "workflow": {
                "auto_cleanup": True,
                "save_intermediate": False,
                "max_concurrent_tasks": 1
            },
            "output": {
                "base_dir": "output",
                "naming_pattern": "{timestamp}_{original_name}",
                "formats": ["mp4"],
                "quality": "high"
            },
            "memory_management": {
                "max_memory_mb": 3500,
                "cleanup_threshold": 0.8
            },
            "subtitle_service": {
                "config_path": None
            },
            "video_processor": {
                "config_path": None
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
    
    def _initialize_services(self):
        """初始化服务组件"""
        try:
            logger.info("初始化视频工作流服务")
            
            # 初始化内存管理器
            if HAS_CORE_COMPONENTS:
                self.memory_manager = MemoryManager(
                    max_memory_mb=self.config["memory_management"]["max_memory_mb"]
                )
            
            # 初始化字幕重构服务
            if HAS_CORE_COMPONENTS:
                subtitle_config = self.config["subtitle_service"].get("config_path")
                self.subtitle_service = SubtitleReconstructionService(subtitle_config)
            
            # 初始化视频处理器
            if HAS_CORE_COMPONENTS:
                video_config = self.config["video_processor"].get("config_path")
                self.video_processor = EnhancedVideoProcessor(video_config)
            
            logger.info("视频工作流服务初始化完成")
            
        except Exception as e:
            logger.error(f"初始化服务失败: {str(e)}")
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def _update_progress(self, stage: str, progress: float):
        """更新进度"""
        if self.progress_callback:
            try:
                self.progress_callback(stage, progress)
            except Exception as e:
                logger.warning(f"进度回调失败: {e}")
    
    def process_video_complete_workflow(self, 
                                      video_path: str,
                                      subtitle_path: str,
                                      output_path: str,
                                      language: str = "auto",
                                      style: str = "viral") -> Dict[str, Any]:
        """
        完整的视频处理工作流
        
        Args:
            video_path: 原视频路径
            subtitle_path: 原字幕路径
            output_path: 输出视频路径
            language: 语言代码
            style: 重构风格
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        workflow_id = f"workflow_{int(time.time())}"
        
        try:
            logger.info(f"开始完整视频处理工作流: {workflow_id}")
            start_time = time.time()
            
            self.current_workflow = {
                "id": workflow_id,
                "start_time": start_time,
                "stage": "initializing",
                "progress": 0.0
            }
            
            # 第一步：验证输入文件
            self._update_progress("验证输入文件", 5.0)
            validation_result = self._validate_inputs(video_path, subtitle_path)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "workflow_id": workflow_id
                }
            
            # 第二步：内存检查
            self._update_progress("内存检查", 10.0)
            if self.memory_manager:
                memory_status = self.memory_manager.check_memory_status()
                if memory_status["usage_percent"] > self.config["memory_management"]["cleanup_threshold"]:
                    logger.info("执行内存清理")
                    self.memory_manager.cleanup()
            
            # 第三步：字幕重构
            self._update_progress("AI字幕重构", 20.0)
            
            # 生成临时字幕文件路径
            temp_subtitle_path = self._generate_temp_path(subtitle_path, "viral_subtitles.srt")
            
            subtitle_result = self.subtitle_service.reconstruct_subtitles(
                subtitle_path, temp_subtitle_path, language, style
            ) if self.subtitle_service else self._fallback_subtitle_processing(subtitle_path, temp_subtitle_path)
            
            if not subtitle_result["success"]:
                return {
                    "success": False,
                    "error": f"字幕重构失败: {subtitle_result.get('error', '未知错误')}",
                    "workflow_id": workflow_id
                }
            
            self._update_progress("字幕重构完成", 50.0)
            
            # 第四步：解析重构后的字幕
            viral_subtitles = self._parse_subtitle_file(temp_subtitle_path)
            if not viral_subtitles:
                return {
                    "success": False,
                    "error": "无法解析重构后的字幕文件",
                    "workflow_id": workflow_id
                }
            
            # 第五步：视频处理
            self._update_progress("视频处理", 60.0)
            
            video_result = self.video_processor.process_video_with_subtitles(
                video_path, viral_subtitles, output_path
            ) if self.video_processor else self._fallback_video_processing(video_path, viral_subtitles, output_path)
            
            if not video_result["success"]:
                return {
                    "success": False,
                    "error": f"视频处理失败: {video_result.get('error', '未知错误')}",
                    "workflow_id": workflow_id
                }
            
            self._update_progress("视频处理完成", 90.0)
            
            # 第六步：清理临时文件
            if self.config["workflow"]["auto_cleanup"]:
                self._update_progress("清理临时文件", 95.0)
                self._cleanup_temp_files([temp_subtitle_path])
            
            # 完成工作流
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "workflow_id": workflow_id,
                "output_path": output_path,
                "processing_time": processing_time,
                "subtitle_result": subtitle_result,
                "video_result": video_result
            }
            
            # 记录工作流历史
            self.workflow_history.append({
                "id": workflow_id,
                "timestamp": datetime.now().isoformat(),
                "input_video": video_path,
                "input_subtitle": subtitle_path,
                "output_video": output_path,
                "language": language,
                "style": style,
                "processing_time": processing_time,
                "success": True
            })
            
            self._update_progress("工作流完成", 100.0)
            self.current_workflow = None
            
            logger.info(f"工作流 {workflow_id} 完成，耗时 {processing_time:.2f} 秒")
            return result
            
        except Exception as e:
            logger.error(f"工作流 {workflow_id} 失败: {str(e)}")
            
            # 记录失败的工作流
            self.workflow_history.append({
                "id": workflow_id,
                "timestamp": datetime.now().isoformat(),
                "input_video": video_path,
                "input_subtitle": subtitle_path,
                "error": str(e),
                "success": False
            })
            
            self.current_workflow = None
            
            return {
                "success": False,
                "error": str(e),
                "workflow_id": workflow_id
            }
    
    def _validate_inputs(self, video_path: str, subtitle_path: str) -> Dict[str, Any]:
        """验证输入文件"""
        try:
            # 检查视频文件
            if not os.path.exists(video_path):
                return {"valid": False, "error": f"视频文件不存在: {video_path}"}
            
            # 检查字幕文件
            if not os.path.exists(subtitle_path):
                return {"valid": False, "error": f"字幕文件不存在: {subtitle_path}"}
            
            # 检查文件大小
            video_size = os.path.getsize(video_path)
            if video_size == 0:
                return {"valid": False, "error": "视频文件为空"}
            
            subtitle_size = os.path.getsize(subtitle_path)
            if subtitle_size == 0:
                return {"valid": False, "error": "字幕文件为空"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"验证输入文件失败: {str(e)}"}
    
    def _generate_temp_path(self, original_path: str, suffix: str) -> str:
        """生成临时文件路径"""
        temp_dir = self.config.get("temp_dir", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"{timestamp}_{suffix}"
        return os.path.join(temp_dir, filename)
    
    def _parse_subtitle_file(self, subtitle_path: str) -> List[Dict[str, Any]]:
        """解析字幕文件"""
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的SRT解析
            import re
            pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\s*\n|\Z)'
            matches = re.findall(pattern, content, re.DOTALL)
            
            subtitles = []
            for match in matches:
                subtitles.append({
                    "index": int(match[0]),
                    "start_time": match[1],
                    "end_time": match[2],
                    "text": match[3].strip().replace('\n', ' ')
                })
            
            return subtitles
            
        except Exception as e:
            logger.error(f"解析字幕文件失败: {str(e)}")
            return []
    
    def _fallback_subtitle_processing(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """备用字幕处理"""
        try:
            # 简单复制文件作为备用方案
            import shutil
            shutil.copy2(input_path, output_path)
            
            return {
                "success": True,
                "details": {
                    "method": "fallback_copy",
                    "message": "使用备用字幕处理方案"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _fallback_video_processing(self, video_path: str, subtitles: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """备用视频处理"""
        try:
            # 简单复制视频作为备用方案
            import shutil
            shutil.copy2(video_path, output_path)
            
            return {
                "success": True,
                "details": {
                    "method": "fallback_copy",
                    "message": "使用备用视频处理方案"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _cleanup_temp_files(self, file_paths: List[str]):
        """清理临时文件"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"删除临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除临时文件失败: {file_path}, {e}")
    
    def get_workflow_status(self) -> Optional[Dict[str, Any]]:
        """获取当前工作流状态"""
        return self.current_workflow.copy() if self.current_workflow else None
    
    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """获取工作流历史"""
        return self.workflow_history.copy()
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.subtitle_service:
                self.subtitle_service.cleanup()
            
            if self.video_processor:
                self.video_processor.cleanup_temp_files()
            
            if self.memory_manager:
                self.memory_manager.cleanup()
            
            logger.info("视频工作流管理器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()
