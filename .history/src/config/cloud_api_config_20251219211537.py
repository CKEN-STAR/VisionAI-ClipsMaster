#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端API配置管理模块

管理云端大模型API的配置信息，包括平台、模型、API密钥等
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent.parent / "configs"
CLOUD_API_CONFIG_FILE = CONFIG_DIR / "cloud_api_config.json"


class CloudAPIConfig:
    """云端API配置管理器"""
    
    def __init__(self):
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "mode": "local",  # local 或 cloud
            "cloud": {
                "platform": "siliconflow",  # siliconflow 或 dashscope
                "model": "qwen3",  # qwen3 或 deepseek-v3.2
                "api_key": "",
                "last_used": None
            },
            "local": {
                "language_mode": "auto",  # auto, zh, en
                "model_path": ""
            }
        }
        
        try:
            if CLOUD_API_CONFIG_FILE.exists():
                with open(CLOUD_API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 合并配置
                    for key in default_config:
                        if key in saved_config:
                            if isinstance(default_config[key], dict):
                                default_config[key].update(saved_config[key])
                            else:
                                default_config[key] = saved_config[key]
                    logger.info("已加载云端API配置")
        except Exception as e:
            logger.warning(f"加载云端API配置失败: {e}")
            
        return default_config
    
    def save_config(self):
        """保存配置"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CLOUD_API_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("云端API配置已保存")
        except Exception as e:
            logger.error(f"保存云端API配置失败: {e}")
    
    @property
    def mode(self) -> str:
        """获取当前模式"""
        return self.config.get("mode", "local")
    
    @mode.setter
    def mode(self, value: str):
        """设置模式"""
        if value in ["local", "cloud"]:
            self.config["mode"] = value
            self.save_config()
    
    @property
    def is_cloud_mode(self) -> bool:
        """是否为云端模式"""
        return self.mode == "cloud"
    
    @property
    def platform(self) -> str:
        """获取云平台"""
        return self.config.get("cloud", {}).get("platform", "siliconflow")
    
    @platform.setter
    def platform(self, value: str):
        """设置云平台"""
        if "cloud" not in self.config:
            self.config["cloud"] = {}
        self.config["cloud"]["platform"] = value
        self.save_config()
    
    @property
    def model(self) -> str:
        """获取云端模型"""
        return self.config.get("cloud", {}).get("model", "qwen3-max")
    
    @model.setter
    def model(self, value: str):
        """设置云端模型"""
        if "cloud" not in self.config:
            self.config["cloud"] = {}
        self.config["cloud"]["model"] = value
        self.save_config()
    
    @property
    def api_key(self) -> str:
        """获取API密钥"""
        return self.config.get("cloud", {}).get("api_key", "")
    
    @api_key.setter
    def api_key(self, value: str):
        """设置API密钥"""
        if "cloud" not in self.config:
            self.config["cloud"] = {}
        self.config["cloud"]["api_key"] = value
        self.save_config()
    
    @property
    def language_mode(self) -> str:
        """获取本地模式的语言设置"""
        return self.config.get("local", {}).get("language_mode", "auto")
    
    @language_mode.setter
    def language_mode(self, value: str):
        """设置本地模式的语言"""
        if "local" not in self.config:
            self.config["local"] = {}
        self.config["local"]["language_mode"] = value
        self.save_config()
    
    def get_cloud_config(self) -> Dict[str, Any]:
        """获取完整的云端配置"""
        return self.config.get("cloud", {}).copy()
    
    def set_cloud_config(self, platform: str, model: str, api_key: str):
        """设置云端配置"""
        self.config["cloud"] = {
            "platform": platform,
            "model": model,
            "api_key": api_key,
            "last_used": None
        }
        self.save_config()
    
    def validate_cloud_config(self) -> tuple:
        """
        验证云端配置是否完整
        
        Returns:
            (is_valid, error_message)
        """
        cloud_config = self.config.get("cloud", {})
        
        if not cloud_config.get("platform"):
            return False, "未选择云平台"
        
        if not cloud_config.get("model"):
            return False, "未选择模型"
        
        if not cloud_config.get("api_key"):
            return False, "未填写API密钥"
        
        return True, ""
    
    def get_display_info(self) -> Dict[str, str]:
        """获取用于显示的配置信息"""
        if self.is_cloud_mode:
            platform_names = {
                "siliconflow": "硅基流动",
                "dashscope": "阿里魔搭社区"
            }
            model_names = {
                "qwen3": "Qwen3",
                "deepseek-v3.2": "DeepSeek-V3.2"
            }
            return {
                "mode": "云端模式",
                "platform": platform_names.get(self.platform, self.platform),
                "model": model_names.get(self.model, self.model),
                "api_key_status": "已配置" if self.api_key else "未配置"
            }
        else:
            lang_names = {
                "auto": "自动检测",
                "zh": "中文模式",
                "en": "英文模式"
            }
            return {
                "mode": "本地模式",
                "language": lang_names.get(self.language_mode, self.language_mode)
            }


# 单例实例
_cloud_api_config = None


def get_cloud_api_config() -> CloudAPIConfig:
    """获取云端API配置实例（单例）"""
    global _cloud_api_config
    if _cloud_api_config is None:
        _cloud_api_config = CloudAPIConfig()
    return _cloud_api_config
