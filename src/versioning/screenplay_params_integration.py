"""
剧本参数集成模块

该模块负责将参数矩阵系统与剧本重构引擎连接，确保参数正确应用到剧本生成过程。
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from .param_manager import get_param_manager
from src.core.language_detector import LanguageDetector

class ScreenplayParamsIntegrator:
    """剧本参数集成器"""
    
    def __init__(self):
        """初始化集成器"""
        self.param_manager = get_param_manager()
        self.language_detector = LanguageDetector()
        
    def prepare_params(self, 
                      subtitles: List[Dict[str, Any]], 
                      preset_name: Optional[str] = None, 
                      language: Optional[str] = None,
                      custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备剧本重构参数
        
        Args:
            subtitles: 字幕列表
            preset_name: 预设名称，如不指定则自动推荐
            language: 语言代码，如不指定则自动检测
            custom_params: 自定义参数
            
        Returns:
            Dict[str, Any]: 参数字典
        """
        # 内容分析
        content_analysis = self.param_manager.analyze_content(subtitles)
        
        # 如果未指定预设，根据内容推荐
        if preset_name is None:
            preset_name = self.param_manager.suggest_preset(content_analysis)
        
        # 如果未指定语言，自动检测
        if language is None:
            language = self._detect_language(subtitles)
        
        # 获取参数
        params = self.param_manager.get_screenplay_params(
            preset_name=preset_name,
            language=language,
            content_analysis=content_analysis,
            **(custom_params or {})
        )
        
        # 添加全局设置
        global_settings = {
            'min_segment_duration': self.param_manager.get_global_setting('min_segment_duration', 1.5),
            'max_total_duration': self.param_manager.get_global_setting('max_total_duration', 120),
            'min_total_duration': self.param_manager.get_global_setting('min_total_duration', 20),
            'target_duration': self.param_manager.get_global_setting('target_duration', 60),
            'max_segments': self.param_manager.get_global_setting('max_segments', 15)
        }
        
        # 合并全局设置
        final_params = {**params, **global_settings}
        
        # 记录日志
        logger.info(f"已准备剧本参数 - 预设: {preset_name}, 语言: {language}")
        
        return final_params
    
    def _detect_language(self, subtitles: List[Dict[str, Any]]) -> str:
        """检测字幕主要语言
        
        Args:
            subtitles: 字幕列表
            
        Returns:
            str: 语言代码 ('zh'或'en')
        """
        if not subtitles:
            return 'zh'  # 默认中文
            
        # 合并所有字幕文本
        all_text = ' '.join([item.get('text', '') for item in subtitles if 'text' in item])
        
        # 检测语言比例
        lang_ratios = self.language_detector.detect_hybrid(all_text)
        
        # 根据比例判断主要语言
        zh_ratio = lang_ratios.get('zh_ratio', 0)
        en_ratio = lang_ratios.get('en_ratio', 0)
        
        # 主要语言判定（阈值可调整）
        if zh_ratio > en_ratio:
            return 'zh'
        else:
            return 'en'
            
    def get_generation_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取生成配置
        
        Args:
            params: 参数字典
            
        Returns:
            Dict[str, Any]: 生成配置
        """
        # 转换参数为生成配置
        config = {
            # 情感设置
            'emotion': {
                'intensity': params.get('emotion_intensity', 0.7),
                'variation': True if params.get('emotion_intensity', 0.7) > 0.5 else False
            },
            
            # 剧情结构
            'structure': {
                'subplots': params.get('subplot', 3),
                'linearity': params.get('linearity', 0.7),
                'preserve_context': params.get('context_preservation', 0.5)
            },
            
            # 角色设置
            'characters': {
                'focus_count': params.get('character_focus', 2),
                'preserve_names': True
            },
            
            # 节奏设置
            'pacing': {
                'pace_factor': params.get('pace', 1.0),
                'min_duration': params.get('min_segment_duration', 1.5),
                'target_duration': params.get('target_duration', 60)
            },
            
            # 悬念设置
            'suspense': {
                'frequency': params.get('cliffhanger_freq', 0.4),
                'resolution_delay': params.get('resolution_delay', 0.5)
            },
            
            # 冲突设置
            'conflict': {
                'intensity': params.get('conflict_intensity', 0.6),
                'highlight': True if params.get('conflict_intensity', 0.6) > 0.7 else False
            },
            
            # 金句设置
            'quotes': {
                'preserve_ratio': params.get('punchline_ratio', 0.15),
                'highlight': True if params.get('punchline_ratio', 0.15) > 0.2 else False
            },
            
            # 长度控制
            'length': {
                'min_total': params.get('min_total_duration', 20),
                'max_total': params.get('max_total_duration', 120),
                'target': params.get('target_duration', 60),
                'max_segments': params.get('max_segments', 15)
            }
        }
        
        return config
    
    def log_params(self, params: Dict[str, Any], level: str = 'info') -> None:
        """记录参数信息
        
        Args:
            params: 参数字典
            level: 日志级别
        """
        # 参数分组
        param_groups = {
            '节奏控制': ['pace', 'min_segment_duration', 'max_total_duration', 'min_total_duration', 'target_duration'],
            '情感设置': ['emotion_intensity', 'conflict_intensity'],
            '剧情结构': ['subplot', 'linearity', 'context_preservation', 'character_focus'],
            '悬念配置': ['cliffhanger_freq', 'resolution_delay'],
            '语言风格': ['punchline_ratio']
        }
        
        # 构建日志消息
        messages = ["剧本重构参数配置:"]
        
        for group_name, param_names in param_groups.items():
            group_params = [f"{name}={params.get(name, 'N/A')}" for name in param_names if name in params]
            if group_params:
                messages.append(f"  {group_name}: {', '.join(group_params)}")
        
        # 记录日志
        log_message = '\n'.join(messages)
        
        if level == 'debug':
            logger.debug(log_message)
        elif level == 'info':
            logger.info(log_message)
        elif level == 'warning':
            logger.warning(log_message)
        else:
            logger.info(log_message)


# 创建单例实例
_integrator_instance = None

def get_screenplay_params_integrator() -> ScreenplayParamsIntegrator:
    """获取剧本参数集成器单例实例
    
    Returns:
        ScreenplayParamsIntegrator: 集成器实例
    """
    global _integrator_instance
    if _integrator_instance is None:
        _integrator_instance = ScreenplayParamsIntegrator()
    return _integrator_instance


def prepare_screenplay_params(subtitles: List[Dict[str, Any]], 
                             preset_name: Optional[str] = None,
                             language: Optional[str] = None,
                             custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """快捷函数：准备剧本重构参数
    
    Args:
        subtitles: 字幕列表
        preset_name: 预设名称，如不指定则自动推荐
        language: 语言代码，如不指定则自动检测
        custom_params: 自定义参数
        
    Returns:
        Dict[str, Any]: 参数字典
    """
    integrator = get_screenplay_params_integrator()
    return integrator.prepare_params(subtitles, preset_name, language, custom_params) 