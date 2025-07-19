#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统集成器
整合所有核心组件，提供统一的系统接口
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
    from .real_ai_engine import RealAIEngine
    from .enhanced_video_processor import EnhancedVideoProcessor
    from .video_workflow_manager import VideoWorkflowManager
    from ..training.training_data_pipeline import TrainingDataPipeline
    from ..training.model_fine_tuner import ModelFineTuner
    from ..training.data_export_manager import DataExportManager
    from ..utils.performance_optimizer import PerformanceOptimizer
    from ..deployment.deployment_manager import DeploymentManager
    HAS_CORE_COMPONENTS = True
except ImportError as e:
    HAS_CORE_COMPONENTS = False
    logging.warning(f"核心组件导入失败: {e}")

logger = logging.getLogger(__name__)

class SystemIntegrator:
    """系统集成器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化系统集成器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        
        # 核心组件
        self.ai_engine = None
        self.video_processor = None
        self.workflow_manager = None
        self.training_pipeline = None
        self.model_fine_tuner = None
        self.data_export_manager = None
        self.performance_optimizer = None
        self.deployment_manager = None
        
        # 系统状态
        self.is_initialized = False
        self.system_status = {
            "ai_engine": "not_loaded",
            "video_processor": "not_loaded",
            "training_system": "not_loaded",
            "performance_monitor": "not_loaded"
        }
        
        # 回调函数
        self.status_callback = None
        self.progress_callback = None
        self.log_callback = None
        
        # 初始化系统
        self._initialize_system()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "system": {
                "auto_start_monitoring": True,
                "auto_optimize": True,
                "log_level": "INFO"
            },
            "components": {
                "ai_engine": {
                    "enabled": True,
                    "config_path": "configs/ai_engine_config.json"
                },
                "video_processor": {
                    "enabled": True,
                    "config_path": "configs/video_processor_config.json"
                },
                "training_system": {
                    "enabled": True,
                    "config_path": "configs/training_config.json"
                },
                "performance_optimizer": {
                    "enabled": True,
                    "config_path": "configs/performance_config.json"
                },
                "deployment_manager": {
                    "enabled": True,
                    "config_path": "configs/deployment_config.json"
                }
            },
            "data": {
                "base_dir": "data",
                "training_db": "data/training/training_data.db"
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
    
    def set_callbacks(self,
                     status_callback: Optional[Callable[[Dict[str, str]], None]] = None,
                     progress_callback: Optional[Callable[[str, float], None]] = None,
                     log_callback: Optional[Callable[[str], None]] = None):
        """设置回调函数"""
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.log_callback = log_callback
    
    def _log(self, message: str):
        """记录日志"""
        logger.info(message)
        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception as e:
                logger.warning(f"日志回调失败: {e}")
    
    def _update_status(self, component: str, status: str):
        """更新组件状态"""
        self.system_status[component] = status
        if self.status_callback:
            try:
                self.status_callback(self.system_status.copy())
            except Exception as e:
                logger.warning(f"状态回调失败: {e}")
    
    def _update_progress(self, stage: str, progress: float):
        """更新进度"""
        if self.progress_callback:
            try:
                self.progress_callback(stage, progress)
            except Exception as e:
                logger.warning(f"进度回调失败: {e}")
    
    def _initialize_system(self):
        """初始化系统"""
        try:
            self._log("开始初始化VisionAI-ClipsMaster系统")
            
            if not HAS_CORE_COMPONENTS:
                self._log("警告：部分核心组件不可用，系统将以降级模式运行")
            
            # 初始化AI引擎
            if self.config["components"]["ai_engine"]["enabled"]:
                self._initialize_ai_engine()
            
            # 初始化视频处理器
            if self.config["components"]["video_processor"]["enabled"]:
                self._initialize_video_processor()
            
            # 初始化工作流管理器
            self._initialize_workflow_manager()
            
            # 初始化训练系统
            if self.config["components"]["training_system"]["enabled"]:
                self._initialize_training_system()
            
            # 初始化性能优化器
            if self.config["components"]["performance_optimizer"]["enabled"]:
                self._initialize_performance_optimizer()
            
            # 初始化部署管理器
            if self.config["components"]["deployment_manager"]["enabled"]:
                self._initialize_deployment_manager()
            
            self.is_initialized = True
            self._log("VisionAI-ClipsMaster系统初始化完成")
            
        except Exception as e:
            self._log(f"系统初始化失败: {str(e)}")
            logger.error(f"系统初始化失败: {str(e)}")
    
    def _initialize_ai_engine(self):
        """初始化AI引擎"""
        try:
            self._log("初始化AI引擎")
            self._update_status("ai_engine", "initializing")
            
            if HAS_CORE_COMPONENTS:
                config_path = self.config["components"]["ai_engine"].get("config_path")
                self.ai_engine = RealAIEngine(config_path)
                self._update_status("ai_engine", "ready")
                self._log("AI引擎初始化完成")
            else:
                self._update_status("ai_engine", "unavailable")
                self._log("AI引擎不可用")
                
        except Exception as e:
            self._update_status("ai_engine", "error")
            self._log(f"AI引擎初始化失败: {str(e)}")
    
    def _initialize_video_processor(self):
        """初始化视频处理器"""
        try:
            self._log("初始化视频处理器")
            self._update_status("video_processor", "initializing")
            
            if HAS_CORE_COMPONENTS:
                config_path = self.config["components"]["video_processor"].get("config_path")
                self.video_processor = EnhancedVideoProcessor(config_path)
                self._update_status("video_processor", "ready")
                self._log("视频处理器初始化完成")
            else:
                self._update_status("video_processor", "unavailable")
                self._log("视频处理器不可用")
                
        except Exception as e:
            self._update_status("video_processor", "error")
            self._log(f"视频处理器初始化失败: {str(e)}")
    
    def _initialize_workflow_manager(self):
        """初始化工作流管理器"""
        try:
            self._log("初始化工作流管理器")
            
            if HAS_CORE_COMPONENTS:
                self.workflow_manager = VideoWorkflowManager()
                self.workflow_manager.set_progress_callback(self._update_progress)
                self._log("工作流管理器初始化完成")
            else:
                self._log("工作流管理器不可用")
                
        except Exception as e:
            self._log(f"工作流管理器初始化失败: {str(e)}")
    
    def _initialize_training_system(self):
        """初始化训练系统"""
        try:
            self._log("初始化训练系统")
            self._update_status("training_system", "initializing")
            
            if HAS_CORE_COMPONENTS:
                # 初始化训练数据管道
                self.training_pipeline = TrainingDataPipeline()
                
                # 初始化模型微调器
                config_path = self.config["components"]["training_system"].get("config_path")
                self.model_fine_tuner = ModelFineTuner(config_path)
                self.model_fine_tuner.set_callbacks(
                    progress_callback=self._update_progress,
                    log_callback=self._log
                )
                
                # 初始化数据导出管理器
                db_path = self.config["data"]["training_db"]
                self.data_export_manager = DataExportManager(db_path)
                
                self._update_status("training_system", "ready")
                self._log("训练系统初始化完成")
            else:
                self._update_status("training_system", "unavailable")
                self._log("训练系统不可用")
                
        except Exception as e:
            self._update_status("training_system", "error")
            self._log(f"训练系统初始化失败: {str(e)}")
    
    def _initialize_performance_optimizer(self):
        """初始化性能优化器"""
        try:
            self._log("初始化性能优化器")
            self._update_status("performance_monitor", "initializing")
            
            if HAS_CORE_COMPONENTS:
                config_path = self.config["components"]["performance_optimizer"].get("config_path")
                self.performance_optimizer = PerformanceOptimizer(config_path)
                
                # 设置警报回调
                self.performance_optimizer.set_alert_callback(self._handle_performance_alert)
                
                # 自动启动监控
                if self.config["system"]["auto_start_monitoring"]:
                    self.performance_optimizer.start_monitoring()
                
                self._update_status("performance_monitor", "running")
                self._log("性能优化器初始化完成")
            else:
                self._update_status("performance_monitor", "unavailable")
                self._log("性能优化器不可用")
                
        except Exception as e:
            self._update_status("performance_monitor", "error")
            self._log(f"性能优化器初始化失败: {str(e)}")
    
    def _initialize_deployment_manager(self):
        """初始化部署管理器"""
        try:
            self._log("初始化部署管理器")
            
            if HAS_CORE_COMPONENTS:
                config_path = self.config["components"]["deployment_manager"].get("config_path")
                self.deployment_manager = DeploymentManager(config_path)
                self._log("部署管理器初始化完成")
            else:
                self._log("部署管理器不可用")
                
        except Exception as e:
            self._log(f"部署管理器初始化失败: {str(e)}")
    
    def _handle_performance_alert(self, alert_type: str, data: Dict[str, Any]):
        """处理性能警报"""
        try:
            self._log(f"性能警报: {alert_type} - {data}")
            
            # 根据警报类型执行相应操作
            if alert_type == "memory_emergency" and self.config["system"]["auto_optimize"]:
                self._log("执行紧急内存优化")
                if self.performance_optimizer:
                    self.performance_optimizer.optimize_memory_usage()
            
        except Exception as e:
            logger.error(f"处理性能警报失败: {str(e)}")
    
    def process_video_complete(self, 
                             video_path: str,
                             subtitle_path: str,
                             output_path: str,
                             language: str = "auto",
                             style: str = "viral") -> Dict[str, Any]:
        """
        完整的视频处理流程
        
        Args:
            video_path: 原视频路径
            subtitle_path: 原字幕路径
            output_path: 输出视频路径
            language: 语言代码
            style: 重构风格
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        if not self.is_initialized:
            return {"success": False, "error": "系统未初始化"}
        
        if not self.workflow_manager:
            return {"success": False, "error": "工作流管理器不可用"}
        
        try:
            return self.workflow_manager.process_video_complete_workflow(
                video_path, subtitle_path, output_path, language, style
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def train_model(self,
                   language: str,
                   training_data_path: str,
                   validation_data_path: Optional[str] = None) -> Dict[str, Any]:
        """
        训练模型
        
        Args:
            language: 语言代码
            training_data_path: 训练数据路径
            validation_data_path: 验证数据路径
            
        Returns:
            Dict[str, Any]: 训练结果
        """
        if not self.model_fine_tuner:
            return {"success": False, "error": "模型微调器不可用"}
        
        try:
            return self.model_fine_tuner.fine_tune_model(
                language, training_data_path, validation_data_path
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "initialized": self.is_initialized,
            "components": self.system_status.copy(),
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加性能信息
        if self.performance_optimizer:
            try:
                perf_data = self.performance_optimizer.get_system_performance()
                status["performance"] = perf_data
            except Exception as e:
                status["performance"] = {"error": str(e)}
        
        return status
    
    def create_deployment_package(self, **kwargs) -> Dict[str, Any]:
        """创建部署包"""
        if not self.deployment_manager:
            return {"success": False, "error": "部署管理器不可用"}
        
        try:
            return self.deployment_manager.create_deployment_package(**kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cleanup(self):
        """清理系统资源"""
        try:
            self._log("开始清理系统资源")
            
            # 清理各个组件
            if self.ai_engine:
                self.ai_engine.cleanup()
            
            if self.video_processor:
                self.video_processor.cleanup_temp_files()
            
            if self.workflow_manager:
                self.workflow_manager.cleanup()
            
            if self.model_fine_tuner:
                self.model_fine_tuner.cleanup()
            
            if self.performance_optimizer:
                self.performance_optimizer.cleanup()
            
            self._log("系统资源清理完成")
            
        except Exception as e:
            logger.error(f"清理系统资源失败: {str(e)}")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()
