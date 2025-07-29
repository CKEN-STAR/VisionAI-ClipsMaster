#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能下载源管理器 - VisionAI-ClipsMaster
实现下载源的智能选择、连通性检测、故障转移等功能
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class DownloadSourceType(Enum):
    """下载源类型"""
    MODELSCOPE = "modelscope"
    HUGGINGFACE = "huggingface"
    MIRROR = "mirror"
    CUSTOM = "custom"

@dataclass
class DownloadSource:
    """下载源配置"""
    name: str
    base_url: str
    source_type: DownloadSourceType
    priority: int = 0  # 优先级，数字越小优先级越高
    timeout: int = 30
    max_retries: int = 3
    available: bool = True
    last_check: float = 0
    response_time: float = 0
    error_count: int = 0

@dataclass
class ModelDownloadConfig:
    """模型下载配置"""
    model_name: str
    model_type: str  # mistral, qwen, etc.
    quantization: str  # Q4_K_M, Q5_K_M, etc.
    sources: Dict[DownloadSourceType, str]  # 各源的具体URL
    file_size: int = 0
    checksum: Optional[str] = None

class IntelligentDownloadManager:
    """智能下载源管理器"""
    
    def __init__(self):
        self.sources: Dict[str, DownloadSource] = {}
        self.model_configs: Dict[str, ModelDownloadConfig] = {}
        self.connectivity_cache: Dict[str, Tuple[bool, float]] = {}
        self.cache_duration = 300  # 5分钟缓存
        self.session: Optional[aiohttp.ClientSession] = None
        
        self._initialize_sources()
        self._initialize_model_configs()
    
    def _initialize_sources(self):
        """初始化下载源配置"""
        self.sources = {
            "modelscope_cn": DownloadSource(
                name="ModelScope (中国)",
                base_url="https://modelscope.cn",
                source_type=DownloadSourceType.MODELSCOPE,
                priority=1,
                timeout=30
            ),
            "huggingface_co": DownloadSource(
                name="HuggingFace (官方)",
                base_url="https://huggingface.co",
                source_type=DownloadSourceType.HUGGINGFACE,
                priority=3,
                timeout=30
            ),
            "hf_mirror": DownloadSource(
                name="HuggingFace (镜像)",
                base_url="https://hf-mirror.com",
                source_type=DownloadSourceType.MIRROR,
                priority=2,
                timeout=25
            ),
            "modelscope_us": DownloadSource(
                name="ModelScope (国际)",
                base_url="https://www.modelscope.cn",
                source_type=DownloadSourceType.MODELSCOPE,
                priority=2,
                timeout=35
            )
        }
    
    def _initialize_model_configs(self):
        """初始化模型配置"""
        self.model_configs = {
            "mistral-7b-en": ModelDownloadConfig(
                model_name="mistral-7b-en",
                model_type="mistral",
                quantization="Q4_K_M",
                sources={
                    DownloadSourceType.MODELSCOPE: "https://modelscope.cn/models/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
                    DownloadSourceType.HUGGINGFACE: "https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
                    DownloadSourceType.MIRROR: "https://hf-mirror.com/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf"
                },
                file_size=4_000_000_000
            ),
            "qwen2.5-7b-zh": ModelDownloadConfig(
                model_name="qwen2.5-7b-zh",
                model_type="qwen",
                quantization="Q4_K_M",
                sources={
                    DownloadSourceType.MODELSCOPE: "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
                    DownloadSourceType.HUGGINGFACE: "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
                    DownloadSourceType.MIRROR: "https://hf-mirror.com/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
                },
                file_size=4_000_000_000
            )
        }
    
    async def check_source_connectivity(self, source: DownloadSource) -> Tuple[bool, float]:
        """检查下载源连通性"""
        cache_key = f"{source.name}_{source.base_url}"
        current_time = time.time()
        
        # 检查缓存
        if cache_key in self.connectivity_cache:
            cached_result, cached_time = self.connectivity_cache[cache_key]
            if current_time - cached_time < self.cache_duration:
                return cached_result, cached_time
        
        try:
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=source.timeout)
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            start_time = time.time()
            
            # 使用HEAD请求检查连通性
            async with self.session.head(source.base_url) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 毫秒
                
                is_available = response.status < 400
                source.available = is_available
                source.response_time = response_time
                source.last_check = current_time
                
                if not is_available:
                    source.error_count += 1
                else:
                    source.error_count = 0
                
                # 更新缓存
                self.connectivity_cache[cache_key] = (is_available, current_time)
                
                logger.info(f"源 {source.name} 连通性检查: {'可用' if is_available else '不可用'} ({response_time:.1f}ms)")
                return is_available, response_time
                
        except asyncio.TimeoutError:
            logger.warning(f"源 {source.name} 连接超时")
            source.available = False
            source.error_count += 1
            self.connectivity_cache[cache_key] = (False, current_time)
            return False, source.timeout * 1000
            
        except Exception as e:
            logger.error(f"源 {source.name} 连通性检查失败: {e}")
            source.available = False
            source.error_count += 1
            self.connectivity_cache[cache_key] = (False, current_time)
            return False, 0
    
    async def check_all_sources(self) -> Dict[str, Tuple[bool, float]]:
        """检查所有下载源的连通性"""
        logger.info("开始检查所有下载源连通性...")
        
        tasks = []
        for source_id, source in self.sources.items():
            task = asyncio.create_task(self.check_source_connectivity(source))
            tasks.append((source_id, task))
        
        results = {}
        for source_id, task in tasks:
            try:
                is_available, response_time = await task
                results[source_id] = (is_available, response_time)
            except Exception as e:
                logger.error(f"检查源 {source_id} 时发生错误: {e}")
                results[source_id] = (False, 0)
        
        return results
    
    def get_best_source_for_model(self, model_name: str) -> Optional[Tuple[DownloadSource, str]]:
        """为指定模型获取最佳下载源"""
        if model_name not in self.model_configs:
            logger.error(f"未找到模型 {model_name} 的配置")
            return None
        
        model_config = self.model_configs[model_name]
        available_sources = []
        
        # 收集可用的源
        for source_type, url in model_config.sources.items():
            for source_id, source in self.sources.items():
                if source.source_type == source_type and source.available:
                    available_sources.append((source, url))
        
        if not available_sources:
            logger.warning(f"模型 {model_name} 没有可用的下载源")
            return None
        
        # 按优先级和响应时间排序
        available_sources.sort(key=lambda x: (x[0].priority, x[0].response_time))
        
        best_source, best_url = available_sources[0]
        logger.info(f"为模型 {model_name} 选择最佳源: {best_source.name} ({best_source.response_time:.1f}ms)")
        
        return best_source, best_url
    
    async def get_intelligent_download_url(self, model_name: str) -> Optional[str]:
        """智能获取下载URL"""
        # 首先检查所有源的连通性
        await self.check_all_sources()
        
        # 获取最佳源
        result = self.get_best_source_for_model(model_name)
        if result:
            source, url = result
            return url
        
        return None
    
    def get_fallback_urls(self, model_name: str) -> List[str]:
        """获取备用下载URL列表"""
        if model_name not in self.model_configs:
            return []
        
        model_config = self.model_configs[model_name]
        fallback_urls = []
        
        # 按优先级排序所有可能的URL
        source_priority = []
        for source_type, url in model_config.sources.items():
            for source_id, source in self.sources.items():
                if source.source_type == source_type:
                    source_priority.append((source.priority, url))
        
        source_priority.sort(key=lambda x: x[0])
        fallback_urls = [url for _, url in source_priority]
        
        return fallback_urls
    
    def get_network_diagnostics(self) -> Dict[str, Any]:
        """获取网络诊断信息"""
        diagnostics = {
            "timestamp": time.time(),
            "sources": {},
            "recommendations": []
        }
        
        available_count = 0
        total_response_time = 0
        
        for source_id, source in self.sources.items():
            source_info = {
                "name": source.name,
                "type": source.source_type.value,
                "available": source.available,
                "response_time": source.response_time,
                "error_count": source.error_count,
                "last_check": source.last_check
            }
            diagnostics["sources"][source_id] = source_info
            
            if source.available:
                available_count += 1
                total_response_time += source.response_time
        
        # 生成建议
        if available_count == 0:
            diagnostics["recommendations"].append("所有下载源均不可用，请检查网络连接")
        elif available_count < len(self.sources) / 2:
            diagnostics["recommendations"].append("部分下载源不可用，建议检查网络设置")
        else:
            avg_response_time = total_response_time / available_count if available_count > 0 else 0
            if avg_response_time > 2000:  # 2秒
                diagnostics["recommendations"].append("网络响应较慢，建议优化网络环境")
            else:
                diagnostics["recommendations"].append("网络状态良好")
        
        return diagnostics
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None
