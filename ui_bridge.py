#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI功能桥接模块
连接UI界面与后端核心功能
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

class UIBridge:
    """UI功能桥接器"""
    
    def __init__(self):
        self.clip_generator = None
        self.screenplay_engineer = None
        self.trainer = None
        self._init_modules()
    
    def _init_modules(self):
        """初始化后端模块"""
        try:
            from src.core.clip_generator import ClipGenerator
            self.clip_generator = ClipGenerator()
            logger.info("ClipGenerator 初始化成功")
        except Exception as e:
            logger.warning(f"ClipGenerator 初始化失败: {e}")
        
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            self.screenplay_engineer = ScreenplayEngineer()
            logger.info("ScreenplayEngineer 初始化成功")
        except Exception as e:
            logger.warning(f"ScreenplayEngineer 初始化失败: {e}")
    
    def generate_viral_srt(self, srt_file_path: str, language_mode: str = "auto") -> Optional[str]:
        """生成爆款SRT文件"""
        if not self.screenplay_engineer:
            logger.error("ScreenplayEngineer 不可用")
            return None

        try:
            # 严格验证输入文件
            if not os.path.exists(srt_file_path):
                logger.error(f"SRT文件不存在: {srt_file_path}")
                return None
            
            # 验证文件大小
            file_size = os.path.getsize(srt_file_path)
            if file_size == 0:
                logger.error(f"SRT文件为空: {srt_file_path}")
                return None
            
            # 验证文件扩展名
            if not srt_file_path.lower().endswith('.srt'):
                logger.error(f"文件不是SRT格式: {srt_file_path}")
                return None
            
            # 先加载原始字幕文件（使用正确的方法名）
            subtitles = self.screenplay_engineer.load_subtitles(srt_file_path)
            if not subtitles or len(subtitles) == 0:
                logger.error("加载原始字幕失败或文件无有效内容")
                return None
            
            # 验证字幕内容质量
            valid_subtitles = [s for s in subtitles if s.get("text", "").strip()]
            if len(valid_subtitles) == 0:
                logger.error("SRT文件中没有有效的文本内容")
                return None

            # 调用剧本工程师生成爆款字幕（使用正确的方法名）
            result = self.screenplay_engineer.generate_viral_screenplay(language_mode)
            return result
        except Exception as e:
            logger.error(f"生成爆款SRT失败: {e}")
            return None
    
    def process_video(self, video_path: str, srt_path: str, output_path: str) -> bool:
        """处理视频生成混剪"""
        if not self.clip_generator:
            logger.error("ClipGenerator 不可用")
            return False
        
        try:
            # 调用剪辑生成器处理视频
            result = self.clip_generator.generate_clips(
                video_path, srt_path, output_path
            )
            return result
        except Exception as e:
            logger.error(f"视频处理失败: {e}")
            return False
    
    def train_model(self, original_srt_paths: List[str], viral_srt_path: str, 
                   language_mode: str = "zh") -> bool:
        """训练模型"""
        try:
            if language_mode == "zh":
                from src.training.zh_trainer import ZhTrainer
                trainer = ZhTrainer()
            else:
                from src.training.en_trainer import EnTrainer
                trainer = EnTrainer()
            
            # 执行训练
            result = trainer.train(original_srt_paths, viral_srt_path)
            return result
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return False

# 全局桥接器实例
ui_bridge = UIBridge()
