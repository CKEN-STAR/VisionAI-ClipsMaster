#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实AI推理引擎
集成Mistral-7B和Qwen2.5-7B模型，实现真正的字幕重构功能
"""

import os
import json
import time
import logging
import gc
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 尝试导入transformers和相关库
try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, 
        BitsAndBytesConfig, pipeline
    )
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# 尝试导入llama-cpp-python（用于GGUF模型）
try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False

logger = logging.getLogger(__name__)

class RealAIEngine:
    """真实AI推理引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化AI引擎
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.models = {}  # 存储加载的模型
        self.tokenizers = {}  # 存储tokenizer
        self.current_model = None
        self.current_language = None
        
        # 设备配置
        self.device = "cpu"  # 4GB设备默认使用CPU
        if torch.cuda.is_available() and self.config.get("use_gpu", False):
            self.device = "cuda"
            
        logger.info(f"AI引擎初始化完成，使用设备: {self.device}")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "models": {
                "zh": {
                    "name": "Qwen/Qwen2.5-7B-Instruct",
                    "type": "huggingface",  # 或 "gguf"
                    "path": "models/qwen/quantized/Q4_K_M.gguf",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                "en": {
                    "name": "mistralai/Mistral-7B-Instruct-v0.1",
                    "type": "huggingface",
                    "path": "models/mistral/quantized/Q4_K_M.gguf", 
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            },
            "quantization": {
                "enabled": True,
                "bits": 4,
                "use_bnb": True  # 使用BitsAndBytes量化
            },
            "memory_optimization": {
                "max_memory_mb": 3500,  # 4GB设备的内存限制
                "offload_to_cpu": True,
                "use_gradient_checkpointing": True
            },
            "use_gpu": False,  # 4GB设备默认不使用GPU
            "batch_size": 1,
            "max_length": 2048
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        
        return default_config
    
    def load_model(self, language: str) -> bool:
        """
        加载指定语言的模型
        
        Args:
            language: 语言代码 (zh/en)
            
        Returns:
            bool: 是否加载成功
        """
        if language in self.models:
            logger.info(f"模型 {language} 已加载")
            return True
            
        model_config = self.config["models"].get(language)
        if not model_config:
            logger.error(f"未找到语言 {language} 的模型配置")
            return False
            
        try:
            logger.info(f"开始加载 {language} 模型: {model_config['name']}")
            start_time = time.time()
            
            if model_config["type"] == "gguf" and HAS_LLAMA_CPP:
                # 使用llama-cpp-python加载GGUF模型
                model = self._load_gguf_model(model_config)
            elif model_config["type"] == "huggingface" and HAS_TRANSFORMERS:
                # 使用transformers加载HuggingFace模型
                model, tokenizer = self._load_hf_model(model_config)
                self.tokenizers[language] = tokenizer
            else:
                logger.error(f"不支持的模型类型或缺少依赖: {model_config['type']}")
                return False
                
            if model is None:
                return False
                
            self.models[language] = model
            elapsed = time.time() - start_time
            logger.info(f"模型 {language} 加载完成，耗时 {elapsed:.2f} 秒")
            return True
            
        except Exception as e:
            logger.error(f"加载模型 {language} 失败: {str(e)}")
            return False
    
    def _load_gguf_model(self, model_config: Dict[str, Any]) -> Optional[Any]:
        """加载GGUF格式模型"""
        try:
            model_path = model_config["path"]
            if not os.path.exists(model_path):
                logger.error(f"模型文件不存在: {model_path}")
                return None
                
            # 配置llama-cpp参数
            llama_config = {
                "model_path": model_path,
                "n_ctx": model_config.get("max_tokens", 2048),
                "n_threads": os.cpu_count() or 4,
                "verbose": False
            }
            
            # 内存优化配置
            memory_config = self.config.get("memory_optimization", {})
            if memory_config.get("max_memory_mb"):
                # 根据内存限制调整参数
                max_memory_mb = memory_config["max_memory_mb"]
                llama_config["n_batch"] = min(512, max_memory_mb // 10)
                
            model = Llama(**llama_config)
            logger.info("GGUF模型加载成功")
            return model
            
        except Exception as e:
            logger.error(f"加载GGUF模型失败: {str(e)}")
            return None
    
    def _load_hf_model(self, model_config: Dict[str, Any]) -> Tuple[Optional[Any], Optional[Any]]:
        """加载HuggingFace模型"""
        try:
            model_name = model_config["name"]
            
            # 配置量化
            quantization_config = None
            if self.config["quantization"]["enabled"]:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            
            # 加载tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                padding_side="left"
            )
            
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # 加载模型
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="auto" if self.device == "cuda" else None,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            if self.device == "cpu":
                model = model.to("cpu")
            
            logger.info("HuggingFace模型加载成功")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"加载HuggingFace模型失败: {str(e)}")
            return None, None
    
    def switch_model(self, language: str) -> bool:
        """
        切换到指定语言的模型
        
        Args:
            language: 目标语言
            
        Returns:
            bool: 是否切换成功
        """
        if self.current_language == language and language in self.models:
            return True
            
        # 卸载当前模型以释放内存
        if self.current_model is not None:
            self._unload_current_model()
        
        # 加载新模型
        if not self.load_model(language):
            return False
            
        self.current_model = self.models[language]
        self.current_language = language
        logger.info(f"已切换到 {language} 模型")
        return True
    
    def _unload_current_model(self):
        """卸载当前模型以释放内存"""
        if self.current_model is not None:
            del self.current_model
            self.current_model = None
            
        if self.current_language and self.current_language in self.models:
            del self.models[self.current_language]
            
        if self.current_language and self.current_language in self.tokenizers:
            del self.tokenizers[self.current_language]
            
        # 强制垃圾回收
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        logger.info("已卸载当前模型")

    def generate_viral_subtitle(self, original_subtitles: List[Dict[str, Any]],
                               language: str = "auto") -> List[Dict[str, Any]]:
        """
        生成爆款风格字幕

        Args:
            original_subtitles: 原始字幕列表
            language: 语言代码，auto为自动检测

        Returns:
            List[Dict[str, Any]]: 生成的爆款字幕
        """
        try:
            # 自动检测语言
            if language == "auto":
                language = self._detect_language(original_subtitles)

            # 切换到对应模型
            if not self.switch_model(language):
                logger.error(f"无法切换到 {language} 模型")
                return original_subtitles

            # 构建提示词
            prompt = self._build_viral_prompt(original_subtitles, language)

            # 生成回答
            response = self._generate_response(prompt, language)

            # 解析生成的字幕
            viral_subtitles = self._parse_generated_subtitles(response, original_subtitles)

            logger.info(f"成功生成 {len(viral_subtitles)} 条爆款字幕")
            return viral_subtitles

        except Exception as e:
            logger.error(f"生成爆款字幕失败: {str(e)}")
            return original_subtitles

    def _detect_language(self, subtitles: List[Dict[str, Any]]) -> str:
        """检测字幕语言"""
        try:
            # 提取所有文本内容
            text_content = " ".join([sub.get("text", "") for sub in subtitles])

            # 简单的中英文检测
            chinese_chars = len([c for c in text_content if '\u4e00' <= c <= '\u9fff'])
            english_words = len(text_content.split())

            if chinese_chars > english_words * 0.3:
                return "zh"
            else:
                return "en"

        except Exception as e:
            logger.warning(f"语言检测失败: {e}")
            return "zh"  # 默认中文

    def _build_viral_prompt(self, subtitles: List[Dict[str, Any]], language: str) -> str:
        """构建爆款转换提示词"""
        # 提取原始字幕文本
        original_text = "\n".join([
            f"{i+1}. {sub.get('text', '')}"
            for i, sub in enumerate(subtitles)
        ])

        if language == "zh":
            prompt = f"""你是一个专业的短视频编辑师，擅长将普通的剧情字幕改写成具有爆款潜力的吸引人字幕。

原始字幕内容：
{original_text}

请将上述字幕改写成更有吸引力的爆款风格，要求：
1. 保持原有的剧情逻辑和时间顺序
2. 增加悬疑、情感冲突等吸引人的元素
3. 使用更生动、更有冲击力的表达方式
4. 适当添加观众互动元素（如"你们觉得呢？"）
5. 保持字幕数量基本一致

改写后的爆款字幕："""
        else:
            prompt = f"""You are a professional short video editor who specializes in rewriting ordinary drama subtitles into viral, engaging content.

Original subtitles:
{original_text}

Please rewrite the above subtitles into more attractive viral style, requirements:
1. Maintain the original plot logic and timeline
2. Add suspense, emotional conflicts and other engaging elements
3. Use more vivid and impactful expressions
4. Appropriately add audience interaction elements
5. Keep the number of subtitles roughly the same

Rewritten viral subtitles:"""

        return prompt

    def _generate_response(self, prompt: str, language: str) -> str:
        """生成AI回答"""
        try:
            model_config = self.config["models"][language]

            if model_config["type"] == "gguf":
                # 使用llama-cpp生成
                response = self.current_model(
                    prompt,
                    max_tokens=model_config.get("max_tokens", 2048),
                    temperature=model_config.get("temperature", 0.7),
                    top_p=model_config.get("top_p", 0.9),
                    stop=["用户:", "User:", "\n\n\n"]
                )
                return response["choices"][0]["text"]

            else:
                # 使用transformers生成
                tokenizer = self.tokenizers[language]

                # 编码输入
                inputs = tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.config.get("max_length", 2048)
                ).to(self.device)

                # 生成回答
                with torch.no_grad():
                    outputs = self.current_model.generate(
                        **inputs,
                        max_new_tokens=model_config.get("max_tokens", 1024),
                        temperature=model_config.get("temperature", 0.7),
                        top_p=model_config.get("top_p", 0.9),
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )

                # 解码回答
                response = tokenizer.decode(
                    outputs[0][inputs["input_ids"].shape[1]:],
                    skip_special_tokens=True
                )

                return response.strip()

        except Exception as e:
            logger.error(f"生成回答失败: {str(e)}")
            return ""

    def _parse_generated_subtitles(self, response: str,
                                 original_subtitles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析生成的字幕"""
        try:
            # 按行分割回答
            lines = [line.strip() for line in response.split('\n') if line.strip()]

            # 提取编号的字幕行
            subtitle_lines = []
            for line in lines:
                # 匹配 "1. 文本" 格式
                if re.match(r'^\d+\.\s+', line):
                    text = re.sub(r'^\d+\.\s+', '', line)
                    subtitle_lines.append(text)

            # 如果没有找到编号格式，直接使用所有行
            if not subtitle_lines:
                subtitle_lines = lines

            # 构建新的字幕列表
            viral_subtitles = []
            for i, original_sub in enumerate(original_subtitles):
                new_sub = original_sub.copy()

                # 使用生成的文本，如果超出范围则使用原文本
                if i < len(subtitle_lines):
                    new_sub["text"] = subtitle_lines[i]
                else:
                    new_sub["text"] = original_sub.get("text", "")

                viral_subtitles.append(new_sub)

            return viral_subtitles

        except Exception as e:
            logger.error(f"解析生成字幕失败: {str(e)}")
            return original_subtitles

    def cleanup(self):
        """清理资源"""
        try:
            # 卸载所有模型
            for language in list(self.models.keys()):
                if language in self.models:
                    del self.models[language]
                if language in self.tokenizers:
                    del self.tokenizers[language]

            self.models.clear()
            self.tokenizers.clear()
            self.current_model = None
            self.current_language = None

            # 强制垃圾回收
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("AI引擎资源清理完成")

        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()
