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
    
    def _ensure_narrative_continuity(self, selected_indices: List[int], episode_subs: List[Dict]) -> List[int]:
        """
        确保叙事连贯性：自动补充缺失的上下文对话
        
        核心策略：
        1. 场景完整性：确保每个场景的开头和结尾都被包含
        2. 因果关系：确保"起因"和"结果"成对出现
        3. 对话完整性：确保问答、反应等对话链完整
        4. 情节单元：将连续的相关对话作为一个整体
        5. 事件-反应模式：确保事件描述和反应之间的关系完整
        6. 动作-结果模式：确保动作和结果之间的关系完整
        7. 背景-行动模式：确保行动有足够的背景铺垫
        
        Args:
            selected_indices: AI选中的对话序号列表
            episode_subs: 当前集的所有字幕
            
        Returns:
            补充后的对话序号列表
        """
        if not selected_indices or not episode_subs:
            return selected_indices
        
        # 排序并去重
        selected_set = set(selected_indices)
        sorted_indices = sorted(selected_set)
        enhanced_indices = set(sorted_indices)
        
        # ========== 词汇库定义（增强版） ==========
        # 结果/反应词汇（需要前文铺垫）- 扩展
        result_words = [
            '所以', '因此', '于是', '结果', '怪不得', '原来', '难怪', '这就是', '这才', '终于',
            '果然', '看来', '这下', '这回', '这次', '总算', '到底', '毕竟', '既然如此',
            '那就', '那么', '这样的话', '也就是说', '换句话说', '意思是'
        ]
        # 起因词汇 - 扩展
        cause_words = [
            '因为', '由于', '既然', '要是', '如果', '假如', '本来', '原本',
            '之所以', '正是因为', '就是因为', '都是因为', '全是因为', '皆因',
            '起因是', '原因是', '缘由是', '根源在于'
        ]
        # 转折词汇（需要前文对比）- 扩展
        contrast_words = [
            '但是', '可是', '然而', '不过', '却', '反而', '相反', '没想到', '谁知', '竟然',
            '岂料', '哪知', '殊不知', '万万没想到', '出乎意料', '意想不到',
            '话虽如此', '虽然', '尽管', '即便', '就算'
        ]
        # 递进词汇（需要前文基础）- 扩展
        progression_words = [
            '而且', '并且', '同时', '另外', '还有', '更', '甚至', '不仅', '除了',
            '不但', '不光', '何况', '况且', '再说', '再者', '此外', '加上',
            '更何况', '更重要的是', '更关键的是'
        ]
        # 问句词汇
        question_words = ['为什么', '怎么', '什么', '哪里', '哪个', '谁', '几', '多少', '吗', '呢', '？', '?']
        # 回应词汇（表示对前文的回应）- 扩展
        response_words = [
            '是的', '对', '没错', '好的', '知道', '明白', '当然', '不是', '不对', '不行', '可以', '行',
            '嗯', '啊', '哦', '好', '是', '对啊', '没错啊', '就是', '正是', '确实',
            '你说得对', '说的是', '有道理', '我懂了', '我明白了', '原来如此'
        ]
        # 指代词汇（需要前文明确指代对象）- 扩展
        reference_words = [
            '这', '那', '他', '她', '它', '这个', '那个', '这样', '那样', '如此', '这么', '那么',
            '这件事', '那件事', '这种', '那种', '这些', '那些', '此', '彼',
            '这人', '那人', '这位', '那位', '这边', '那边'
        ]
        # 情感反应词汇（通常是对前文事件的反应）- 扩展
        emotion_words = [
            '天哪', '什么', '不会吧', '真的吗', '怎么会', '太好了', '糟了', '完了', '救命', '不要',
            '我的天', '天啊', '啊', '哇', '呀', '哎呀', '哎', '唉', '嘿',
            '不可能', '怎么可能', '这不可能', '开什么玩笑', '你在开玩笑吧',
            '太棒了', '太厉害了', '太可怕了', '太过分了', '太离谱了'
        ]
        # 【新增】事件描述词汇（通常需要后续反应）
        event_words = [
            '发生了', '出事了', '有人', '有事', '来了', '走了', '死了', '活了',
            '成功了', '失败了', '赢了', '输了', '找到了', '丢了', '发现了',
            '告诉你', '跟你说', '你知道吗', '你听说了吗', '你猜怎么着'
        ]
        # 【新增】动作词汇（通常需要结果）
        action_words = [
            '去', '来', '做', '说', '看', '听', '想', '要', '给', '拿',
            '打', '杀', '救', '帮', '找', '追', '跑', '逃', '躲', '藏'
        ]
        # 【新增】承接词汇（表示承接前文）
        continuation_words = [
            '然后', '接着', '随后', '之后', '后来', '紧接着', '接下来',
            '于是乎', '就这样', '就在这时', '正在这时', '这时候', '那时候'
        ]
        
        # ========== 策略1：场景完整性检测 ==========
        # 识别场景边界（通过时间间隙判断）
        scene_groups = self._identify_scene_groups(sorted_indices, episode_subs)
        for group in scene_groups:
            if len(group) >= 2:
                # 确保场景组内的所有对话都被选中
                min_idx, max_idx = min(group), max(group)
                # 如果场景组内有间隙，填补
                for fill_idx in range(min_idx, max_idx + 1):
                    if fill_idx <= len(episode_subs):
                        enhanced_indices.add(fill_idx)
        
        # ========== 策略2：因果关系补充（增强版） ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            # 如果包含"结果"类词汇，向前查找"起因"
            if any(word in text for word in result_words):
                # 向前查找最多6条，找到起因或场景开头
                found_cause = False
                for prev_idx in range(idx - 1, max(0, idx - 7), -1):
                    if prev_idx >= 1 and prev_idx <= len(episode_subs):
                        prev_text = episode_subs[prev_idx - 1].get("text", "")
                        # 如果找到起因词，添加从起因到当前的所有对话
                        if any(word in prev_text for word in cause_words):
                            for fill_idx in range(prev_idx, idx):
                                enhanced_indices.add(fill_idx)
                            found_cause = True
                            break
                # 如果没找到明确的起因词，补充前2-3条作为背景
                if not found_cause:
                    for prev_idx in range(max(1, idx - 3), idx):
                        if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                            prev_text = episode_subs[prev_idx - 1].get("text", "")
                            if len(prev_text) > 3:  # 有实际内容
                                enhanced_indices.add(prev_idx)
            
            # 如果包含转折词，确保前文被选中
            if any(word in text for word in contrast_words):
                # 向前查找3-4条作为对比基础
                for prev_idx in range(max(1, idx - 4), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
            
            # 如果包含递进词，确保前文基础被选中
            if any(word in text for word in progression_words):
                # 向前查找2条
                for prev_idx in range(max(1, idx - 2), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
            
            # 【新增】如果包含承接词，确保前文被选中
            if any(word in text for word in continuation_words):
                # 向前查找2-3条
                for prev_idx in range(max(1, idx - 3), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
        
        # ========== 策略3：问答完整性 ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            # 如果是问句，确保后面有回答
            if any(word in text for word in question_words):
                # 向后查找3条，补充回答
                for next_idx in range(idx + 1, min(len(episode_subs) + 1, idx + 4)):
                    if next_idx <= len(episode_subs):
                        next_text = episode_subs[next_idx - 1].get("text", "")
                        # 如果下一条是回应或者不是问句，添加
                        if any(word in next_text for word in response_words) or not any(word in next_text for word in question_words):
                            enhanced_indices.add(next_idx)
                            break
            
            # 如果是回应词开头，确保前面的问题/陈述被选中
            if any(text.startswith(word) for word in response_words):
                # 向前查找2条
                for prev_idx in range(max(1, idx - 2), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
        
        # ========== 策略4：指代消解（增强版） ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            # 如果以指代词开头，需要前文明确指代对象
            if any(text.startswith(word) for word in reference_words):
                # 向前查找，直到找到非指代词开头的对话
                for prev_idx in range(idx - 1, max(0, idx - 5), -1):
                    if prev_idx >= 1 and prev_idx <= len(episode_subs):
                        prev_text = episode_subs[prev_idx - 1].get("text", "")
                        enhanced_indices.add(prev_idx)
                        # 如果前一条不是以指代词开头，停止
                        if not any(prev_text.startswith(word) for word in reference_words):
                            break
        
        # ========== 策略5：情感反应补充（增强版） ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            # 如果是情感反应，需要前文说明原因
            if any(word in text for word in emotion_words):
                # 向前查找2-3条作为触发事件
                for prev_idx in range(max(1, idx - 3), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
        
        # ========== 策略6：事件-反应模式检测（新增） ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            # 如果包含事件描述词，确保后续反应被选中
            if any(word in text for word in event_words):
                # 向后查找2-3条，补充反应
                for next_idx in range(idx + 1, min(len(episode_subs) + 1, idx + 4)):
                    if next_idx <= len(episode_subs):
                        next_text = episode_subs[next_idx - 1].get("text", "")
                        # 如果下一条包含情感反应或回应词，添加
                        if any(word in next_text for word in emotion_words + response_words):
                            enhanced_indices.add(next_idx)
        
        # ========== 策略7：填补小间隙（增强版） ==========
        sorted_enhanced = sorted(enhanced_indices)
        for i in range(len(sorted_enhanced) - 1):
            current_idx = sorted_enhanced[i]
            next_idx = sorted_enhanced[i + 1]
            gap = next_idx - current_idx
            
            # 如果间隙是2-5条，检查是否应该补充
            if 2 <= gap <= 5:
                # 检查间隙中的对话
                for fill_idx in range(current_idx + 1, next_idx):
                    if fill_idx <= len(episode_subs):
                        fill_text = episode_subs[fill_idx - 1].get("text", "")
                        # 如果包含任何关键词，补充
                        all_keywords = (result_words + cause_words + contrast_words + 
                                       progression_words + response_words + continuation_words)
                        if any(word in fill_text for word in all_keywords):
                            enhanced_indices.add(fill_idx)
                        # 如果间隙只有2-3条，直接补充
                        elif gap <= 3:
                            enhanced_indices.add(fill_idx)
                        # 如果对话较长（可能是重要内容），补充
                        elif len(fill_text) > 8:
                            enhanced_indices.add(fill_idx)
        
        # ========== 策略8：确保开头不是"半句话"（增强版） ==========
        final_indices = sorted(enhanced_indices)
        for idx in final_indices:
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            # 检查是否以连接词/指代词开头
            incomplete_starters = [
                '但', '可', '然', '不过', '而', '所以', '因此', '于是', 
                '这', '那', '他', '她', '它', '还', '也', '又', '再',
                '然后', '接着', '随后', '之后', '后来', '就', '便', '才'
            ]
            if text and any(text.startswith(word) for word in incomplete_starters):
                # 向前查找2条
                for prev_idx in range(max(1, idx - 2), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
        
        # ========== 策略9：语义连贯性检测（新增） ==========
        # 检测选中的对话之间是否存在语义断层
        final_sorted = sorted(enhanced_indices)
        for i in range(1, len(final_sorted)):
            curr_idx = final_sorted[i]
            prev_idx = final_sorted[i - 1]
            
            if curr_idx > len(episode_subs) or prev_idx > len(episode_subs):
                continue
                
            curr_text = episode_subs[curr_idx - 1].get("text", "")
            prev_text = episode_subs[prev_idx - 1].get("text", "")
            
            # 如果当前对话看起来是对某事的反应，但前一条不是触发事件
            # 检查是否需要补充中间的对话
            if curr_idx - prev_idx > 1:
                # 检查当前对话是否是反应性的
                is_reaction = (
                    any(word in curr_text for word in emotion_words) or
                    any(word in curr_text for word in result_words) or
                    any(curr_text.startswith(word) for word in response_words)
                )
                
                if is_reaction:
                    # 检查前一条是否是触发事件
                    is_trigger = (
                        any(word in prev_text for word in event_words) or
                        any(word in prev_text for word in question_words) or
                        any(word in prev_text for word in cause_words)
                    )
                    
                    # 如果前一条不是触发事件，补充中间的对话
                    if not is_trigger:
                        for fill_idx in range(prev_idx + 1, curr_idx):
                            if fill_idx <= len(episode_subs):
                                enhanced_indices.add(fill_idx)
        
        # ========== 策略10：避免切断原本连贯的内容（新增） ==========
        # 检测原始字幕中时间上连续的对话段落，如果选中了其中一部分，应该保持完整
        final_sorted = sorted(enhanced_indices)
        for idx in final_sorted:
            if idx > len(episode_subs):
                continue
            
            # 获取当前对话的时间信息
            curr_sub = episode_subs[idx - 1]
            curr_end = float(curr_sub.get("end_time", curr_sub.get("end", 0)))
            
            # 检查下一条对话是否与当前对话时间上连续（间隙小于1秒）
            if idx < len(episode_subs):
                next_sub = episode_subs[idx]  # idx是1-based，所以idx就是下一条的0-based索引
                next_start = float(next_sub.get("start_time", next_sub.get("start", 0)))
                time_gap = next_start - curr_end
                
                # 如果时间间隙小于1秒，说明是连贯的对话
                if 0 <= time_gap < 1.0:
                    next_idx = idx + 1
                    # 如果下一条不在选中列表中，检查是否应该添加
                    if next_idx not in enhanced_indices:
                        next_text = next_sub.get("text", "")
                        # 如果下一条以连接词开头，或者是短回应，应该添加
                        if (any(next_text.startswith(word) for word in continuation_words + response_words) or
                            len(next_text) < 10):
                            enhanced_indices.add(next_idx)
        
        result = sorted(enhanced_indices)
        
        # 记录补充情况
        added_count = len(result) - len(sorted_indices)
        if added_count > 0:
            logger.info(f"叙事连贯性优化：补充了 {added_count} 条上下文对话（原{len(sorted_indices)}条 -> 现{len(result)}条）")
        
        return result
    
    def _identify_scene_groups(self, indices: List[int], episode_subs: List[Dict]) -> List[List[int]]:
        """
        识别场景组：将时间上连续的对话分组
        
        Args:
            indices: 选中的对话序号列表
            episode_subs: 当前集的所有字幕
            
        Returns:
            场景组列表，每个组是一个序号列表
        """
        if not indices:
            return []
        
        groups = []
        current_group = [indices[0]]
        
        for i in range(1, len(indices)):
            prev_idx = indices[i - 1]
            curr_idx = indices[i]
            
            # 获取时间信息
            prev_end = 0
            curr_start = 0
            
            if prev_idx <= len(episode_subs):
                prev_sub = episode_subs[prev_idx - 1]
                prev_end = float(prev_sub.get("end_time", prev_sub.get("end", 0)))
            
            if curr_idx <= len(episode_subs):
                curr_sub = episode_subs[curr_idx - 1]
                curr_start = float(curr_sub.get("start_time", curr_sub.get("start", 0)))
            
            # 如果时间间隙小于5秒，认为是同一场景
            time_gap = curr_start - prev_end
            index_gap = curr_idx - prev_idx
            
            if time_gap < 5.0 and index_gap <= 3:
                current_group.append(curr_idx)
            else:
                if len(current_group) >= 1:
                    groups.append(current_group)
                current_group = [curr_idx]
        
        # 添加最后一组
        if current_group:
            groups.append(current_group)
        
        return groups
    
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
            
            # 🔧 优化：构建更注重叙事连贯性的提示词
            extract_prompt = f"""你是一个专业的短剧剪辑师。请从第{ep_idx + 1}集的字幕中提取关键对话片段，用于制作混剪视频。

故事背景：
{story_summary[:500]}

第{ep_idx + 1}集字幕（共{len(episode_subs)}条）：
{episode_content}

【核心原则】选择对话时，必须确保观众能够理解剧情，不会感到困惑。宁可多选几条保证连贯，也不要跳跃式选择导致观众看不懂。

【选择规则】（约选择总数的38%-55%）：

1. **因果完整性**（最重要！！！）：
   - 【必须】如果选择了"结果"，必须选择"起因"
   - 【必须】如果选择了"反应"，必须选择"触发事件"
   - 【必须】如果选择了"回答"，必须选择"问题"
   - 【禁止】不要选择孤立的结论性对话，必须包含前因
   - 例如：如果选了"原来是你干的！"，必须选择前面解释"是谁干的"的对话
   - 例如：如果选了"所以你才会这样"，必须选择前面说明"为什么"的对话
   - 例如：如果选了"什么？！"这样的惊讶反应，必须选择前面让人惊讶的内容

2. **对话链完整性**：
   - 问句必须配回答：选了问题就要选答案
   - 反应必须配触发：选了惊讶/愤怒/开心的反应，就要选前面的触发事件
   - 转折必须配前提：选了"但是..."就要选前面的内容
   - 承接必须配前文：选了"然后..."、"接着..."就要选前面的内容

3. **场景完整性**：
   - 同一个场景的对话尽量连续选择，不要跳着选
   - 不要只选场景的结尾，要包含开头和中间
   - 避免选择孤立的、没有上下文的台词
   - 如果选了某个场景的高潮，必须选择铺垫

4. **内容价值**：
   - 推动剧情发展的关键对话
   - 展现角色性格和关系的对话
   - 情感高潮或冲突点
   - 重要的转折点

【输出格式】
请以JSON数组格式输出对话序号，连续的序号表示一个完整的情节单元。
例如：[1, 2, 3, 4, 5, 10, 11, 12, 13, 20, 21, 22, 23, 24]
（1-5是一个单元，10-13是一个单元，20-24是一个单元）

【重要提醒】
- 每个情节单元至少包含3-5条连续对话
- 不要选择单独的1-2条对话，这样会导致观众看不懂
- 宁可多选几条保证连贯，也不要跳跃式选择

只输出JSON数组，不要其他内容。"""

            try:
                response = self.generate(extract_prompt, language, max_tokens=1024)
                
                # 解析选中的序号
                json_match = re.search(r'\[[\d,\s]+\]', response)
                if json_match:
                    selected_indices = json.loads(json_match.group())
                    
                    # 🔧 优化：自动补充连贯性缺失的对话
                    selected_indices = self._ensure_narrative_continuity(selected_indices, episode_subs)
                    
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
