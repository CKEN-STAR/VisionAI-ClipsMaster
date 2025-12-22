#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端AI推理引擎
支持调用云端大模型API进行字幕重构

支持的平台：
1. 硅基流动 (SiliconFlow) - https://siliconflow.cn
2. 魔搭社区 (ModelScope) - https://modelscope.cn

支持的模型：
1. Qwen3 (通义千问3) - 最大参数规模
2. DeepSeek-V3.2 - 最新版
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
    MODELSCOPE = "modelscope"    # 魔搭社区 (ModelScope)


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
            CloudModel.QWEN3: "Qwen/Qwen3-235B-A22B",  # 硅基流动上的Qwen3-235B模型
            CloudModel.DEEPSEEK_V3_2: "deepseek-ai/DeepSeek-V3.2",  # 硅基流动上的DeepSeek-V3.2模型
        },
        "headers_template": {
            "Content-Type": "application/json",
            "Authorization": "Bearer {api_key}"
        }
    },
    CloudPlatform.MODELSCOPE: {
        "name": "魔搭社区",
        "base_url": "https://api-inference.modelscope.cn/v1",
        "models": {
            CloudModel.QWEN3: "Qwen/Qwen3-235B-A22B-FP8",  # 魔搭社区上的Qwen3模型
            CloudModel.DEEPSEEK_V3_2: "deepseek-ai/DeepSeek-V3-0324",  # 魔搭社区上的DeepSeek-V3模型
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


class ModelScopeProvider(BaseCloudProvider):
    """魔搭社区 (ModelScope) API提供者"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, CloudPlatform.MODELSCOPE)
        
    def chat_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict[str, Any]:
        """发送聊天完成请求到魔搭社区"""
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
            
            # 检查特定错误
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("errors", {}).get("message", "")
                    if "bind" in error_msg.lower() and "alibaba" in error_msg.lower():
                        raise Exception(
                            "魔搭社区API需要绑定阿里云账号！\n"
                            "请访问 https://modelscope.cn/my/myaccesstoken 绑定阿里云账号后重试。\n"
                            "或者使用硅基流动平台，无需绑定即可使用。"
                        )
                except (json.JSONDecodeError, KeyError):
                    pass
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"魔搭社区API请求失败: {e}")
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
        elif self.platform == CloudPlatform.MODELSCOPE:
            self.provider = ModelScopeProvider(self.api_key)
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
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """将秒数转换为SRT时间格式 (HH:MM:SS,mmm)"""
        if seconds < 0:
            seconds = 0
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
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
        批量生成爆款字幕（多集混剪）- 与本地模式保持一致的工作流程
        
        策略：
        步骤1：AI理解整个故事，生成故事摘要
        步骤2：AI根据故事摘要，逐集提取关键对话（保留原始时间轴）
        步骤3：合并所有关键对话，重新生成时间轴
        
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
        logger.info(f"策略：分步骤处理 - 步骤1：理解整个故事，步骤2：逐集提取关键对话，步骤3：合并生成混剪SRT")
        
        self._update_progress(5, f"准备处理{total_episodes}集字幕...")
        
        # ========== 步骤1：AI理解整个故事，生成故事摘要 ==========
        logger.info("=" * 60)
        logger.info("步骤1：AI理解整个故事，生成故事摘要")
        logger.info("=" * 60)
        self._update_progress(10, "AI正在理解整个故事...")
        
        # 构建故事理解提示词（包含所有字幕的摘要）
        story_texts = []
        for ep_idx, episode_subs in enumerate(all_subtitles):
            ep_texts = [f"[第{ep_idx+1}集-{i+1}] {sub.get('text', '')}" 
                       for i, sub in enumerate(episode_subs[:30])]  # 每集取前30条
            story_texts.extend(ep_texts)
        
        story_content = "\n".join(story_texts[:200])  # 限制总量
        
        story_prompt = f"""你是一个专业的短剧分析师。请仔细阅读以下{total_episodes}集短剧的字幕内容，
理解整个故事的剧情脉络，然后生成一个详细的故事摘要。

字幕内容：
{story_content}

请分析并输出：
1. 故事主线：主要讲述什么故事？
2. 主要角色：有哪些重要角色？他们的关系是什么？
3. 情感高潮：哪些场景是情感高潮点？
4. 冲突转折：有哪些重要的冲突和转折？
5. 精彩片段：哪些对话最精彩、最吸引人？

请用300-500字概括整个故事。"""

        try:
            story_summary = self.generate(story_prompt, language, max_tokens=2048)
            logger.info(f"故事摘要生成完成，长度: {len(story_summary)} 字符")
        except Exception as e:
            logger.error(f"故事摘要生成失败: {e}")
            story_summary = "故事摘要生成失败，将使用简化流程"
        
        self._update_progress(25, "故事摘要生成完成")
        
        # ========== 步骤2：逐集提取关键对话（保留原始时间轴） ==========
        logger.info("=" * 60)
        logger.info("步骤2：AI根据故事摘要，逐集提取关键对话")
        logger.info("=" * 60)
        self._update_progress(30, "开始提取关键对话...")
        
        all_key_dialogues = []
        
        for ep_idx, episode_subs in enumerate(all_subtitles):
            # 更新进度
            episode_progress = 30 + int((ep_idx / total_episodes) * 40)  # 30-70%
            self._update_progress(episode_progress, f"正在处理第{ep_idx + 1}/{total_episodes}集...")
            logger.info(f"正在处理第{ep_idx + 1}集，共{len(episode_subs)}条字幕...")
            
            # 构建当前集的字幕列表（包含时间轴）
            episode_texts = []
            for i, sub in enumerate(episode_subs):
                start_time = sub.get("start_time", sub.get("start", 0))
                end_time = sub.get("end_time", sub.get("end", 0))
                text = sub.get("text", "")
                episode_texts.append(f"{i+1}. [{start_time:.2f}s-{end_time:.2f}s] {text}")
            
            episode_content = "\n".join(episode_texts)
            
            # 构建关键对话提取提示词
            extract_prompt = f"""基于以下故事摘要，从第{ep_idx + 1}集的字幕中提取最关键、最精彩的对话。

故事摘要：
{story_summary[:500]}

第{ep_idx + 1}集字幕（共{len(episode_subs)}条）：
{episode_content}

请选择这一集中最重要的对话（约占总数的30%-50%），这些对话应该：
1. 推动剧情发展
2. 展现角色性格
3. 包含情感高潮或冲突
4. 有吸引力的台词

请以JSON数组格式输出你选择的对话序号，例如：[1, 3, 5, 8, 12, 15]
只输出JSON数组，不要其他内容。"""

            try:
                response = self.generate(extract_prompt, language, max_tokens=1024)
                
                # 解析选中的序号
                json_match = re.search(r'\[[\d,\s]+\]', response)
                if json_match:
                    selected_indices = json.loads(json_match.group())
                    
                    # 根据序号提取对应的字幕（保留原始时间轴）
                    for idx in selected_indices:
                        if 1 <= idx <= len(episode_subs):
                            original_sub = episode_subs[idx - 1]
                            key_dialogue = {
                                "index": len(all_key_dialogues) + 1,
                                "text": original_sub.get("text", ""),
                                "start_time": float(original_sub.get("start_time", original_sub.get("start", 0))),
                                "end_time": float(original_sub.get("end_time", original_sub.get("end", 0))),
                                "original_episode": ep_idx + 1,
                                "original_index": idx
                            }
                            key_dialogue["duration"] = key_dialogue["end_time"] - key_dialogue["start_time"]
                            all_key_dialogues.append(key_dialogue)
                    
                    logger.info(f"第{ep_idx + 1}集：提取到 {len(selected_indices)} 条关键对话")
                else:
                    # 如果解析失败，使用简单策略：取前30%的字幕
                    logger.warning(f"第{ep_idx + 1}集：JSON解析失败，使用简化策略")
                    num_to_select = max(5, len(episode_subs) // 3)
                    for i in range(min(num_to_select, len(episode_subs))):
                        original_sub = episode_subs[i]
                        key_dialogue = {
                            "index": len(all_key_dialogues) + 1,
                            "text": original_sub.get("text", ""),
                            "start_time": float(original_sub.get("start_time", original_sub.get("start", 0))),
                            "end_time": float(original_sub.get("end_time", original_sub.get("end", 0))),
                            "original_episode": ep_idx + 1,
                            "original_index": i + 1
                        }
                        key_dialogue["duration"] = key_dialogue["end_time"] - key_dialogue["start_time"]
                        all_key_dialogues.append(key_dialogue)
                        
            except Exception as e:
                logger.error(f"第{ep_idx + 1}集处理失败: {e}")
                # 降级处理：取前30%的字幕
                num_to_select = max(5, len(episode_subs) // 3)
                for i in range(min(num_to_select, len(episode_subs))):
                    original_sub = episode_subs[i]
                    key_dialogue = {
                        "index": len(all_key_dialogues) + 1,
                        "text": original_sub.get("text", ""),
                        "start_time": float(original_sub.get("start_time", original_sub.get("start", 0))),
                        "end_time": float(original_sub.get("end_time", original_sub.get("end", 0))),
                        "original_episode": ep_idx + 1,
                        "original_index": i + 1
                    }
                    key_dialogue["duration"] = key_dialogue["end_time"] - key_dialogue["start_time"]
                    all_key_dialogues.append(key_dialogue)
        
        logger.info(f"总共提取到 {len(all_key_dialogues)} 条关键对话")
        
        # ========== 步骤3：重新生成时间轴 ==========
        logger.info("=" * 60)
        logger.info("步骤3：重新生成时间轴")
        logger.info("=" * 60)
        self._update_progress(75, "正在重新生成时间轴...")
        
        # 按原始时间顺序排序（先按集数，再按原始索引）
        all_key_dialogues.sort(key=lambda x: (x.get("original_episode", 1), x.get("original_index", 0)))
        
        # 重新生成连续的时间轴
        viral_subtitles = []
        current_time = 0.0
        
        for i, dialogue in enumerate(all_key_dialogues):
            # 使用原始时长，但重新计算开始和结束时间
            duration = dialogue.get("duration", 2.0)
            if duration <= 0:
                duration = 2.0  # 默认2秒
            
            # 🔧 关键修复：保留原始视频的时间码，用于剪映工程提取正确的视频片段
            original_start = dialogue.get("start_time", 0)  # 原视频中的开始时间
            original_end = dialogue.get("end_time", duration)  # 原视频中的结束时间
            
            viral_subtitle = {
                "index": i + 1,
                "start_time": current_time,  # 新时间轴的开始时间
                "end_time": current_time + duration,  # 新时间轴的结束时间
                "text": dialogue.get("text", ""),
                "duration": duration,
                # 🔧 修复：使用统一的字段名 original_episode（与_subtitles_to_srt方法一致）
                "original_episode": dialogue.get("original_episode", 1),
                "original_index": dialogue.get("original_index", 0),
                # 🔧 新增：保存原始视频的时间码（SRT格式），用于剪映工程
                "original_start": self._seconds_to_srt_time(original_start),
                "original_end": self._seconds_to_srt_time(original_end)
            }
            
            viral_subtitles.append(viral_subtitle)
            current_time += duration + 0.1  # 添加0.1秒间隔
        
        self._update_progress(90, "时间轴生成完成")
        
        # 计算总时长
        total_duration = viral_subtitles[-1]["end_time"] if viral_subtitles else 0
        logger.info(f"混剪字幕生成完成，共 {len(viral_subtitles)} 条，总时长 {total_duration:.2f} 秒")
        
        self._update_progress(100, "批量混剪完成")
        
        return viral_subtitles


# 便捷函数
def get_supported_platforms() -> List[Dict[str, str]]:
    """获取支持的云平台列表"""
    return [
        {"id": CloudPlatform.SILICONFLOW, "name": "硅基流动", "url": "https://siliconflow.cn"},
        {"id": CloudPlatform.MODELSCOPE, "name": "魔搭社区", "url": "https://modelscope.cn"}
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
