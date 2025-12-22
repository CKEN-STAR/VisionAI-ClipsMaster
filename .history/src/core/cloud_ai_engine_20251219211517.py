#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端AI推理引擎
支持调用云端大模型API进行字幕重构

支持的平台：
1. 硅基流动 (SiliconFlow) - https://siliconflow.cn
2. 阿里魔搭社区 (DashScope) - https://dashscope.aliyuncs.com

支持的模型：
1. Qwen3 (通义千问3) - 最大参数规模
2. DeepSeek-V3 - 最大参数规模
"""

import os
import json
import time
import logging
import re
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

# 尝试导入requests
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# 尝试导入aiohttp用于异步请求
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

logger = logging.getLogger(__name__)


class CloudPlatform:
    """云平台枚举"""
    SILICONFLOW = "siliconflow"  # 硅基流动
    DASHSCOPE = "dashscope"      # 阿里魔搭社区/DashScope


class CloudModel:
    """云端模型枚举"""
    QWEN3 = "qwen3"                   # Qwen3 通义千问3
    DEEPSEEK_V3_2 = "deepseek-v3.2"   # DeepSeek-V3.2 最新版


# 平台配置
PLATFORM_CONFIG = {
    CloudPlatform.SILICONFLOW: {
        "name": "硅基流动",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": {
            CloudModel.QWEN3: "Qwen/Qwen3-235B-A22B",  # 硅基流动上的Qwen3模型
            CloudModel.DEEPSEEK_V3_2: "deepseek-ai/DeepSeek-V3",  # 硅基流动上的DeepSeek-V3模型
        },
        "headers_template": {
            "Content-Type": "application/json",
            "Authorization": "Bearer {api_key}"
        }
    },
    CloudPlatform.DASHSCOPE: {
        "name": "阿里魔搭社区",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": {
            CloudModel.QWEN3: "qwen3-235b-a22b",  # DashScope上的Qwen3模型
            CloudModel.DEEPSEEK_V3_2: "deepseek-v3",  # DashScope上的DeepSeek-V3模型
        },
        "headers_template": {
            "Content-Type": "application/json",
            "Authorization": "Bearer {api_key}"
        }
    }
}


class BaseCloudProvider(ABC):
    """云端API提供者基类"""
    
    def __init__(self, api_key: str, platform: str):
        self.api_key = api_key
        self.platform = platform
        self.config = PLATFORM_CONFIG.get(platform, {})
        self.base_url = self.config.get("base_url", "")
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {}
        template = self.config.get("headers_template", {})
        for key, value in template.items():
            headers[key] = value.format(api_key=self.api_key)
        return headers
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict[str, Any]:
        """发送聊天完成请求"""
        pass


class SiliconFlowProvider(BaseCloudProvider):
    """硅基流动API提供者"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, CloudPlatform.SILICONFLOW)
        
    def chat_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict[str, Any]:
        """发送聊天完成请求到硅基流动"""
        if not HAS_REQUESTS:
            raise ImportError("requests库未安装，请运行: pip install requests")
            
        url = f"{self.base_url}/chat/completions"
        
        # 获取实际模型名称
        model_name = self.config["models"].get(model, model)
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": False
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"硅基流动API请求失败: {e}")
            raise


class DashScopeProvider(BaseCloudProvider):
    """阿里魔搭社区/DashScope API提供者"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, CloudPlatform.DASHSCOPE)
        
    def chat_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict[str, Any]:
        """发送聊天完成请求到DashScope"""
        if not HAS_REQUESTS:
            raise ImportError("requests库未安装，请运行: pip install requests")
            
        url = f"{self.base_url}/chat/completions"
        
        # 获取实际模型名称
        model_name = self.config["models"].get(model, model)
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": False
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"DashScope API请求失败: {e}")
            raise


class CloudAIEngine:
    """云端AI推理引擎"""
    
    def __init__(self, platform: str = None, model: str = None, api_key: str = None, 
                 progress_callback=None):
        """
        初始化云端AI引擎
        
        Args:
            platform: 云平台 (siliconflow/dashscope)
            model: 模型名称 (qwen3-max/deepseek-v3)
            api_key: API密钥
            progress_callback: 进度回调函数
        """
        self.platform = platform
        self.model = model
        self.api_key = api_key
        self.progress_callback = progress_callback
        self.provider = None
        
        # 如果提供了完整配置，初始化provider
        if platform and api_key:
            self._init_provider()
            
        logger.info(f"云端AI引擎初始化完成，平台: {platform}, 模型: {model}")
    
    def _init_provider(self):
        """初始化API提供者"""
        if self.platform == CloudPlatform.SILICONFLOW:
            self.provider = SiliconFlowProvider(self.api_key)
        elif self.platform == CloudPlatform.DASHSCOPE:
            self.provider = DashScopeProvider(self.api_key)
        else:
            raise ValueError(f"不支持的平台: {self.platform}")
    
    def configure(self, platform: str, model: str, api_key: str):
        """配置云端引擎"""
        self.platform = platform
        self.model = model
        self.api_key = api_key
        self._init_provider()
        logger.info(f"云端AI引擎已配置: 平台={platform}, 模型={model}")
    
    def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        if not self.provider:
            return {"success": False, "error": "未配置API"}
            
        try:
            # 发送简单测试请求
            messages = [{"role": "user", "content": "你好，请回复'连接成功'"}]
            response = self.provider.chat_completion(messages, self.model, max_tokens=50)
            
            if "choices" in response and len(response["choices"]) > 0:
                return {
                    "success": True,
                    "message": "API连接成功",
                    "model": self.model,
                    "platform": self.platform
                }
            else:
                return {"success": False, "error": "API响应格式异常"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _update_progress(self, progress: int, message: str):
        """更新进度"""
        if self.progress_callback:
            try:
                self.progress_callback(progress, message)
            except Exception as e:
                logger.warning(f"进度回调失败: {e}")
    
    def generate(self, prompt: str, language: str = "zh", **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示词
            language: 语言代码
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        if not self.provider:
            raise ValueError("云端AI引擎未配置，请先调用configure()方法")
            
        messages = [
            {"role": "system", "content": self._get_system_prompt(language)},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.provider.chat_completion(
                messages, 
                self.model,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096)
            )
            
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                logger.error(f"API响应格式异常: {response}")
                return ""
                
        except Exception as e:
            logger.error(f"云端AI生成失败: {e}")
            raise
    
    def _get_system_prompt(self, language: str) -> str:
        """获取系统提示词"""
        if language == "zh":
            return """你是一个专业的短剧混剪AI助手。你的任务是分析原始字幕内容，理解剧情，
并重构为更具吸引力的"爆款"风格字幕。请保持剧情连贯性，突出情感高潮和转折点，
使用更具感染力的表达方式。输出格式为JSON数组。"""
        else:
            return """You are a professional short drama remix AI assistant. Your task is to analyze 
the original subtitle content, understand the plot, and reconstruct it into more attractive 
"viral" style subtitles. Please maintain plot coherence, highlight emotional climaxes and 
turning points, and use more engaging expressions. Output format is JSON array."""
    
    def generate_viral_subtitle(self, original_subtitles: List[Dict[str, Any]],
                               language: str = "zh") -> List[Dict[str, Any]]:
        """
        生成爆款风格字幕
        
        Args:
            original_subtitles: 原始字幕列表
            language: 语言代码
            
        Returns:
            生成的爆款字幕列表
        """
        if not self.provider:
            raise ValueError("云端AI引擎未配置")
            
        self._update_progress(10, "正在准备字幕数据...")
        
        # 构建提示词
        prompt = self._build_viral_prompt(original_subtitles, language)
        
        self._update_progress(30, f"正在调用{PLATFORM_CONFIG[self.platform]['name']} API...")
        
        try:
            response = self.generate(prompt, language, max_tokens=8192)
            
            self._update_progress(70, "正在解析生成结果...")
            
            # 解析生成的字幕
            viral_subtitles = self._parse_generated_subtitles(response, original_subtitles)
            
            self._update_progress(100, "爆款字幕生成完成")
            
            logger.info(f"成功生成 {len(viral_subtitles)} 条爆款字幕")
            return viral_subtitles
            
        except Exception as e:
            logger.error(f"生成爆款字幕失败: {e}")
            return original_subtitles
    
    def _build_viral_prompt(self, subtitles: List[Dict], language: str) -> str:
        """构建爆款字幕生成提示词"""
        # 提取字幕文本
        subtitle_texts = []
        for i, sub in enumerate(subtitles[:50]):  # 限制数量避免超长
            text = sub.get("text", "")
            start = sub.get("start_time", sub.get("start", 0))
            end = sub.get("end_time", sub.get("end", 0))
            subtitle_texts.append(f"{i+1}. [{start:.2f}s-{end:.2f}s] {text}")
        
        subtitles_str = "\n".join(subtitle_texts)
        
        if language == "zh":
            prompt = f"""请分析以下原始字幕内容，理解剧情后重构为更具吸引力的"爆款"风格字幕。

原始字幕：
{subtitles_str}

要求：
1. 保持原有剧情的核心内容和时间顺序
2. 突出情感高潮、冲突和转折点
3. 使用更具感染力和吸引力的表达方式
4. 适当精简冗余内容，保留精华
5. 确保字幕时间轴合理

请以JSON数组格式输出，每个元素包含：
- index: 序号
- start: 开始时间（秒）
- end: 结束时间（秒）
- text: 字幕文本
- original_index: 对应原始字幕序号（如有）

只输出JSON数组，不要其他内容。"""
        else:
            prompt = f"""Please analyze the following original subtitles, understand the plot, 
and reconstruct them into more attractive "viral" style subtitles.

Original subtitles:
{subtitles_str}

Requirements:
1. Maintain the core content and chronological order of the original plot
2. Highlight emotional climaxes, conflicts, and turning points
3. Use more engaging and attractive expressions
4. Appropriately streamline redundant content, keep the essence
5. Ensure reasonable subtitle timeline

Please output in JSON array format, each element contains:
- index: sequence number
- start: start time (seconds)
- end: end time (seconds)
- text: subtitle text
- original_index: corresponding original subtitle number (if any)

Output only the JSON array, nothing else."""
        
        return prompt
    
    def _parse_generated_subtitles(self, response: str, 
                                   original_subtitles: List[Dict]) -> List[Dict[str, Any]]:
        """解析生成的字幕"""
        try:
            # 尝试提取JSON数组
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                # 标准化字段
                result = []
                for item in parsed:
                    subtitle = {
                        "index": item.get("index", len(result) + 1),
                        "start_time": float(item.get("start", item.get("start_time", 0))),
                        "end_time": float(item.get("end", item.get("end_time", 0))),
                        "text": item.get("text", ""),
                        "duration": 0
                    }
                    subtitle["duration"] = subtitle["end_time"] - subtitle["start_time"]
                    
                    # 保留原始索引信息
                    if "original_index" in item:
                        subtitle["original_index"] = item["original_index"]
                        
                    result.append(subtitle)
                
                return result
            else:
                logger.warning("无法从响应中提取JSON数组，返回原始字幕")
                return original_subtitles
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return original_subtitles
        except Exception as e:
            logger.error(f"解析生成字幕失败: {e}")
            return original_subtitles
    
    def generate_viral_subtitle_batch(self, all_subtitles: List[List[Dict[str, Any]]],
                                      language: str = "zh",
                                      analysis_results: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """
        批量生成爆款字幕（多集混剪）
        
        Args:
            all_subtitles: 所有字幕列表的列表
            language: 语言代码
            analysis_results: 分析结果（可选）
            
        Returns:
            混剪后的爆款字幕列表
        """
        if not self.provider:
            raise ValueError("云端AI引擎未配置")
            
        total_episodes = len(all_subtitles)
        logger.info(f"开始批量生成爆款字幕，共{total_episodes}集")
        
        self._update_progress(5, f"准备处理{total_episodes}集字幕...")
        
        # 合并所有字幕用于整体理解
        all_texts = []
        for ep_idx, episode_subs in enumerate(all_subtitles):
            for sub in episode_subs[:20]:  # 每集取前20条
                text = sub.get("text", "")
                all_texts.append(f"[第{ep_idx+1}集] {text}")
        
        combined_text = "\n".join(all_texts[:100])  # 限制总量
        
        self._update_progress(20, "AI正在理解整个故事...")
        
        # 构建批量处理提示词
        if language == "zh":
            prompt = f"""你是一个专业的短剧混剪AI。请分析以下多集字幕内容，理解整个故事后，
生成一个精华混剪版本的字幕。

原始字幕（来自{total_episodes}集）：
{combined_text}

要求：
1. 从所有集数中提取最精彩、最吸引人的片段
2. 保持故事的核心脉络和逻辑连贯性
3. 突出情感高潮、冲突和转折点
4. 生成的混剪字幕总时长控制在原片的30%-50%
5. 使用更具感染力的表达方式

请以JSON数组格式输出混剪字幕，每个元素包含：
- index: 序号
- start: 开始时间（秒）
- end: 结束时间（秒）
- text: 字幕文本
- source_episode: 来源集数

只输出JSON数组。"""
        else:
            prompt = f"""You are a professional short drama remix AI. Please analyze the following 
multi-episode subtitles, understand the entire story, and generate a highlight remix version.

Original subtitles (from {total_episodes} episodes):
{combined_text}

Requirements:
1. Extract the most exciting and attractive segments from all episodes
2. Maintain the core storyline and logical coherence
3. Highlight emotional climaxes, conflicts, and turning points
4. Control the total duration of remixed subtitles to 30%-50% of the original
5. Use more engaging expressions

Please output in JSON array format, each element contains:
- index: sequence number
- start: start time (seconds)
- end: end time (seconds)
- text: subtitle text
- source_episode: source episode number

Output only the JSON array."""
        
        self._update_progress(40, f"正在调用{PLATFORM_CONFIG[self.platform]['name']} API...")
        
        try:
            response = self.generate(prompt, language, max_tokens=8192)
            
            self._update_progress(80, "正在解析混剪结果...")
            
            # 解析结果
            result = self._parse_batch_subtitles(response, all_subtitles)
            
            self._update_progress(100, "批量混剪完成")
            
            logger.info(f"批量混剪完成，生成 {len(result)} 条字幕")
            return result
            
        except Exception as e:
            logger.error(f"批量生成失败: {e}")
            # 返回第一集作为降级处理
            return all_subtitles[0] if all_subtitles else []
    
    def _parse_batch_subtitles(self, response: str, 
                               all_subtitles: List[List[Dict]]) -> List[Dict[str, Any]]:
        """解析批量生成的字幕"""
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                result = []
                current_time = 0.0
                
                for item in parsed:
                    # 计算时间轴
                    duration = float(item.get("end", 0)) - float(item.get("start", 0))
                    if duration <= 0:
                        duration = 3.0  # 默认3秒
                    
                    subtitle = {
                        "index": len(result) + 1,
                        "start_time": current_time,
                        "end_time": current_time + duration,
                        "text": item.get("text", ""),
                        "duration": duration,
                        "source_episode": item.get("source_episode", 1)
                    }
                    
                    result.append(subtitle)
                    current_time += duration + 0.1  # 添加小间隔
                
                return result
            else:
                logger.warning("无法解析批量结果")
                return all_subtitles[0] if all_subtitles else []
                
        except Exception as e:
            logger.error(f"解析批量字幕失败: {e}")
            return all_subtitles[0] if all_subtitles else []


# 便捷函数
def get_supported_platforms() -> List[Dict[str, str]]:
    """获取支持的云平台列表"""
    return [
        {"id": CloudPlatform.SILICONFLOW, "name": "硅基流动", "url": "https://siliconflow.cn"},
        {"id": CloudPlatform.DASHSCOPE, "name": "阿里魔搭社区", "url": "https://dashscope.aliyuncs.com"}
    ]


def get_supported_models() -> List[Dict[str, str]]:
    """获取支持的模型列表"""
    return [
        {"id": CloudModel.QWEN3, "name": "Qwen3", "description": "阿里通义千问3大模型"},
        {"id": CloudModel.DEEPSEEK_V3_2, "name": "DeepSeek-V3.2", "description": "深度求索V3.2大模型"}
    ]


def get_platform_models(platform: str) -> List[Dict[str, str]]:
    """获取指定平台支持的模型"""
    config = PLATFORM_CONFIG.get(platform, {})
    models = config.get("models", {})
    
    result = []
    for model_id, model_name in models.items():
        model_info = next((m for m in get_supported_models() if m["id"] == model_id), None)
        if model_info:
            result.append({
                "id": model_id,
                "name": model_info["name"],
                "api_name": model_name
            })
    
    return result


# 单例实例
_cloud_ai_engine = None


def get_cloud_ai_engine() -> CloudAIEngine:
    """获取云端AI引擎实例（单例）"""
    global _cloud_ai_engine
    if _cloud_ai_engine is None:
        _cloud_ai_engine = CloudAIEngine()
    return _cloud_ai_engine
