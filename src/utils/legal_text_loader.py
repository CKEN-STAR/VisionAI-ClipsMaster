#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 法律文本加载器

此模块提供加载和管理法律文本模板的功能，
包括版权声明、免责声明和使用条款等。

主要功能：
1. 加载法律文本模板配置
2. 根据语言获取相应的法律文本
3. 支持不同场景和格式的法律声明
4. 提供文本插值功能，支持动态替换变量
"""

import os
import copy
from typing import Dict, Any, Optional
from pathlib import Path

import yaml

from src.utils.log_handler import get_logger
from src.utils.config_utils import load_yaml_config

# 配置日志
logger = get_logger("legal_text_loader")


class LegalTextLoader:
    """法律文本加载器，负责加载和管理法律文本模板"""

    _instance = None
    _templates = {}
    _format_templates = {}
    _special_cases = {}
    
    def __new__(cls):
        """单例模式实现，确保只有一个LegalTextLoader实例"""
        if cls._instance is None:
            cls._instance = super(LegalTextLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化法律文本加载器，加载相关配置"""
        if self._initialized:
            return
            
        self._initialized = True
        self._load_templates()
        
    def _load_templates(self) -> None:
        """加载法律文本模板配置"""
        try:
            # 使用简化版配置加载函数
            config = load_yaml_config("legal_templates")
            
            # 提取模板配置
            self._templates = config.get("templates", {})
            self._format_templates = config.get("format_templates", {})
            self._special_cases = config.get("special_cases", {})
            
            logger.info(f"已加载法律文本模板配置: {len(self._templates)} 种语言, "
                       f"{len(self._format_templates)} 种格式, "
                       f"{len(self._special_cases)} 种特殊场景")
        except Exception as e:
            logger.error(f"加载法律文本模板配置失败: {str(e)}")
            # 设置默认模板，确保系统不会因为缺少配置而崩溃
            self._set_default_templates()
    
    def _set_default_templates(self) -> None:
        """设置默认法律文本模板（当配置加载失败时使用）"""
        self._templates = {
            "zh": {
                "copyright": "本视频由AI生成，版权归原作者所有",
                "disclaimer": "本内容仅用于技术演示，禁止商用"
            },
            "en": {
                "copyright": "AI Generated Content, All Rights Reserved",
                "disclaimer": "For technical demonstration only"
            }
        }
        self._format_templates = {
            "video": {"watermark_position": "bottom-right"},
            "document": {"header_position": "top"},
            "audio": {"credits_position": "end"}
        }
        self._special_cases = {}
        logger.warning("使用默认法律文本模板")
    
    def get_legal_text(self, 
                      text_type: str, 
                      lang: str = "zh", 
                      case: Optional[str] = None, 
                      variables: Optional[Dict[str, str]] = None) -> str:
        """获取指定类型和语言的法律文本
        
        Args:
            text_type: 文本类型，如'copyright', 'disclaimer'等
            lang: 语言代码，如'zh', 'en'
            case: 特殊场景，如'commercial', 'educational'等
            variables: 用于替换文本中变量的字典
            
        Returns:
            格式化后的法律文本
        """
        # 检查语言是否存在，不存在则使用默认语言
        if lang not in self._templates:
            available_langs = list(self._templates.keys())
            logger.warning(f"请求的语言'{lang}'不存在，使用默认语言'{available_langs[0] if available_langs else 'zh'}'")
            lang = available_langs[0] if available_langs else "zh"
        
        # 如果指定了特殊场景，优先使用特殊场景的模板
        if case and case in self._special_cases and lang in self._special_cases[case]:
            if text_type in self._special_cases[case][lang]:
                text = self._special_cases[case][lang][text_type]
            else:
                text = self._templates[lang].get(text_type, "")
        else:
            text = self._templates[lang].get(text_type, "")
        
        # 如果没有找到指定类型的文本，返回空字符串
        if not text:
            logger.warning(f"找不到类型为'{text_type}'的法律文本")
            return ""
        
        # 替换变量
        if variables:
            try:
                # 初始化变量字典
                default_vars = self._get_default_variables()
                merged_vars = {**default_vars, **(variables or {})}
                
                # 处理括号中的变量
                import re
                
                # 先检查文本中是否包含变量占位符
                if "{" in text and "}" in text:
                    # 找出所有变量占位符
                    placeholders = re.findall(r'\{([^{}]+)\}', text)
                    
                    # 替换变量
                    for placeholder in placeholders:
                        if placeholder in merged_vars:
                            text = text.replace(f"{{{placeholder}}}", str(merged_vars[placeholder]))
                        else:
                            logger.warning(f"变量 '{placeholder}' 未在变量字典中提供，保留原始占位符")
                
            except Exception as e:
                logger.error(f"替换法律文本中的变量时出错: {str(e)}")
                # 如果替换失败，仍然继续，返回部分替换的文本
        else:
            # 如果没有提供变量，使用默认变量
            default_vars = self._get_default_variables()
            
            # 处理括号中的变量
            import re
            
            # 先检查文本中是否包含变量占位符
            if "{" in text and "}" in text:
                # 找出所有变量占位符
                placeholders = re.findall(r'\{([^{}]+)\}', text)
                
                # 替换变量
                for placeholder in placeholders:
                    if placeholder in default_vars:
                        text = text.replace(f"{{{placeholder}}}", str(default_vars[placeholder]))
        
        return text
    
    def _get_default_variables(self) -> Dict[str, str]:
        """获取默认变量，用于文本插值"""
        import datetime
        
        return {
            "current_year": str(datetime.datetime.now().year),
            "app_name": "VisionAI-ClipsMaster",
            "app_version": "1.0",
            "version": "1.0"  # 可从项目配置中获取
        }
    
    def get_format_settings(self, format_type: str) -> Dict[str, Any]:
        """获取指定格式的模板设置
        
        Args:
            format_type: 格式类型，如'video', 'document', 'audio'
            
        Returns:
            格式设置字典
        """
        if format_type in self._format_templates:
            return copy.deepcopy(self._format_templates[format_type])
        else:
            logger.warning(f"找不到类型为'{format_type}'的格式模板")
            return {}
    
    def reload_templates(self) -> bool:
        """重新加载法律文本模板配置
        
        Returns:
            bool: 是否成功重新加载
        """
        try:
            self._load_templates()
            return True
        except Exception as e:
            logger.error(f"重新加载法律文本模板配置失败: {str(e)}")
            return False


# 简化调用的辅助函数
def load_legal_text(text_type: str, lang: str = "zh", case: Optional[str] = None, 
                  variables: Optional[Dict[str, str]] = None) -> str:
    """加载指定类型和语言的法律文本（简化调用）
    
    Args:
        text_type: 文本类型，如'copyright', 'disclaimer'等
        lang: 语言代码，如'zh', 'en'
        case: 特殊场景，如'commercial', 'educational'等
        variables: 用于替换文本中变量的字典
        
    Returns:
        格式化后的法律文本
    """
    loader = LegalTextLoader()
    return loader.get_legal_text(text_type, lang, case, variables)


# 测试代码
if __name__ == "__main__":
    # 测试加载
    loader = LegalTextLoader()
    
    # 获取中文版权声明
    print("中文版权声明:", loader.get_legal_text("copyright", "zh"))
    
    # 获取英文免责声明
    print("英文免责声明:", loader.get_legal_text("disclaimer", "en"))
    
    # 获取特殊场景声明
    print("商业场景声明:", loader.get_legal_text("disclaimer", "zh", "commercial"))
    
    # 测试变量替换
    vars = {"app_name": "ClipsMaster Pro"}
    print("变量替换测试:", load_legal_text("attribution", "zh", variables=vars))
    
    # 获取格式设置
    print("视频格式设置:", loader.get_format_settings("video")) 