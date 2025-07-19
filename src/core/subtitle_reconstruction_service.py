#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字幕重构服务
整合真实AI引擎与现有系统，提供完整的字幕重构功能
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 导入核心组件
try:
    from .real_ai_engine import RealAIEngine
    from .language_detector import LanguageDetector
    from .srt_parser import SRTParser
    from ..utils.memory_manager import MemoryManager
    HAS_CORE_COMPONENTS = True
except ImportError as e:
    HAS_CORE_COMPONENTS = False
    logging.warning(f"核心组件导入失败: {e}")

logger = logging.getLogger(__name__)

class SubtitleReconstructionService:
    """字幕重构服务"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化字幕重构服务
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.ai_engine = None
        self.language_detector = None
        self.srt_parser = None
        self.memory_manager = None
        
        # 服务状态
        self.is_initialized = False
        self.current_task = None
        
        # 初始化服务
        self._initialize_service()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "ai_engine": {
                "config_path": "configs/ai_engine_config.json"
            },
            "memory_management": {
                "max_memory_mb": 3500,
                "enable_monitoring": True,
                "cleanup_threshold": 0.9
            },
            "reconstruction": {
                "preserve_timeline": True,
                "target_compression_ratio": 0.6,
                "viral_intensity": 0.8,
                "quality_threshold": 0.7
            },
            "output": {
                "format": "srt",
                "encoding": "utf-8",
                "include_metadata": True
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
    
    def _initialize_service(self):
        """初始化服务组件"""
        try:
            logger.info("开始初始化字幕重构服务")
            
            # 初始化内存管理器
            if HAS_CORE_COMPONENTS:
                self.memory_manager = MemoryManager(
                    max_memory_mb=self.config["memory_management"]["max_memory_mb"]
                )
            
            # 初始化语言检测器
            if HAS_CORE_COMPONENTS:
                self.language_detector = LanguageDetector()
            
            # 初始化SRT解析器
            if HAS_CORE_COMPONENTS:
                self.srt_parser = SRTParser()
            
            # 初始化AI引擎
            ai_config_path = self.config["ai_engine"].get("config_path")
            if HAS_CORE_COMPONENTS:
                self.ai_engine = RealAIEngine(ai_config_path)
            
            self.is_initialized = True
            logger.info("字幕重构服务初始化完成")
            
        except Exception as e:
            logger.error(f"初始化字幕重构服务失败: {str(e)}")
            self.is_initialized = False
    
    def reconstruct_subtitles(self, input_file: str, output_file: str,
                            language: str = "auto", 
                            style: str = "viral") -> Dict[str, Any]:
        """
        重构字幕文件
        
        Args:
            input_file: 输入字幕文件路径
            output_file: 输出字幕文件路径
            language: 语言代码，auto为自动检测
            style: 重构风格
            
        Returns:
            Dict[str, Any]: 重构结果
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "服务未初始化",
                "details": {}
            }
        
        try:
            logger.info(f"开始重构字幕: {input_file} -> {output_file}")
            start_time = time.time()
            
            # 第一步：解析输入字幕
            original_subtitles = self._parse_input_file(input_file)
            if not original_subtitles:
                return {
                    "success": False,
                    "error": "无法解析输入字幕文件",
                    "details": {"input_file": input_file}
                }
            
            # 第二步：语言检测
            if language == "auto":
                detected_language = self._detect_subtitle_language(original_subtitles)
            else:
                detected_language = language
            
            # 第三步：内存检查
            if self.memory_manager:
                memory_status = self.memory_manager.check_memory_status()
                if memory_status["usage_percent"] > 0.8:
                    logger.warning("内存使用率较高，执行清理")
                    self.memory_manager.cleanup()
            
            # 第四步：AI重构
            viral_subtitles = self._ai_reconstruct(original_subtitles, detected_language, style)
            
            # 第五步：质量验证
            quality_score = self._validate_quality(original_subtitles, viral_subtitles)
            
            # 第六步：保存结果
            save_success = self._save_output_file(viral_subtitles, output_file)
            
            elapsed_time = time.time() - start_time
            
            result = {
                "success": save_success,
                "details": {
                    "input_file": input_file,
                    "output_file": output_file,
                    "language": detected_language,
                    "style": style,
                    "original_count": len(original_subtitles),
                    "viral_count": len(viral_subtitles),
                    "quality_score": quality_score,
                    "processing_time": elapsed_time
                }
            }
            
            if not save_success:
                result["error"] = "保存输出文件失败"
            
            logger.info(f"字幕重构完成，耗时 {elapsed_time:.2f} 秒")
            return result
            
        except Exception as e:
            logger.error(f"字幕重构失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "details": {}
            }
    
    def _parse_input_file(self, input_file: str) -> List[Dict[str, Any]]:
        """解析输入字幕文件"""
        try:
            if not os.path.exists(input_file):
                logger.error(f"输入文件不存在: {input_file}")
                return []
            
            if self.srt_parser:
                return self.srt_parser.parse_file(input_file)
            else:
                # 简单的SRT解析备用方案
                return self._simple_srt_parse(input_file)
                
        except Exception as e:
            logger.error(f"解析输入文件失败: {str(e)}")
            return []
    
    def _simple_srt_parse(self, file_path: str) -> List[Dict[str, Any]]:
        """简单的SRT解析备用方案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
            logger.error(f"简单SRT解析失败: {str(e)}")
            return []
    
    def _detect_subtitle_language(self, subtitles: List[Dict[str, Any]]) -> str:
        """检测字幕语言"""
        try:
            if self.language_detector:
                # 提取文本内容
                text_content = " ".join([sub.get("text", "") for sub in subtitles])
                return self.language_detector.detect_from_text(text_content)
            else:
                # 简单的语言检测备用方案
                text_content = " ".join([sub.get("text", "") for sub in subtitles])
                chinese_chars = len([c for c in text_content if '\u4e00' <= c <= '\u9fff'])
                english_words = len(text_content.split())
                
                return "zh" if chinese_chars > english_words * 0.3 else "en"
                
        except Exception as e:
            logger.warning(f"语言检测失败: {e}")
            return "zh"  # 默认中文
    
    def _ai_reconstruct(self, subtitles: List[Dict[str, Any]], 
                       language: str, style: str) -> List[Dict[str, Any]]:
        """AI重构字幕"""
        try:
            if self.ai_engine:
                return self.ai_engine.generate_viral_subtitle(subtitles, language)
            else:
                # 备用方案：简单的模板替换
                logger.warning("AI引擎不可用，使用备用重构方案")
                return self._fallback_reconstruct(subtitles, style)
                
        except Exception as e:
            logger.error(f"AI重构失败: {str(e)}")
            return self._fallback_reconstruct(subtitles, style)
    
    def _fallback_reconstruct(self, subtitles: List[Dict[str, Any]], 
                            style: str) -> List[Dict[str, Any]]:
        """备用重构方案"""
        # 简单的模板替换逻辑
        viral_templates = [
            "太震惊了！{text}",
            "你绝对想不到：{text}",
            "这个细节太重要了：{text}",
            "注意看：{text}"
        ]
        
        viral_subtitles = []
        for i, sub in enumerate(subtitles):
            new_sub = sub.copy()
            if i % 4 == 0:  # 每4条字幕添加一个模板
                template = viral_templates[i % len(viral_templates)]
                new_sub["text"] = template.format(text=sub.get("text", ""))
            viral_subtitles.append(new_sub)
        
        return viral_subtitles
    
    def _validate_quality(self, original: List[Dict[str, Any]], 
                         viral: List[Dict[str, Any]]) -> float:
        """验证重构质量"""
        try:
            # 简单的质量评分
            if len(viral) == 0:
                return 0.0
            
            # 检查字幕数量保持度
            count_ratio = min(len(viral) / len(original), 1.0) if original else 0.0
            
            # 检查文本长度合理性
            avg_original_length = sum(len(sub.get("text", "")) for sub in original) / len(original)
            avg_viral_length = sum(len(sub.get("text", "")) for sub in viral) / len(viral)
            length_ratio = min(avg_viral_length / avg_original_length, 2.0) if avg_original_length > 0 else 0.0
            
            # 综合评分
            quality_score = (count_ratio * 0.5 + min(length_ratio, 1.0) * 0.5)
            return quality_score
            
        except Exception as e:
            logger.warning(f"质量验证失败: {e}")
            return 0.5  # 默认评分
    
    def _save_output_file(self, subtitles: List[Dict[str, Any]], 
                         output_file: str) -> bool:
        """保存输出文件"""
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 生成SRT格式内容
            srt_content = ""
            for i, sub in enumerate(subtitles, 1):
                srt_content += f"{i}\n"
                srt_content += f"{sub.get('start_time', '00:00:00,000')} --> {sub.get('end_time', '00:00:01,000')}\n"
                srt_content += f"{sub.get('text', '')}\n\n"
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"输出文件保存成功: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存输出文件失败: {str(e)}")
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.ai_engine:
                self.ai_engine.cleanup()
            
            if self.memory_manager:
                self.memory_manager.cleanup()
            
            logger.info("字幕重构服务资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()
