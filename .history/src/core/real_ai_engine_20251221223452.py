#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实AI推理引擎
集成Mistral-7B和Qwen3系列模型，实现真正的字幕重构功能

工作流程说明：
1. 训练阶段（Track 1）：
   - 使用HuggingFace原始模型（FP16/BF16）
   - 使用transformers + LoRA进行微调
   - 输出：微调后的adapter权重

2. 推理阶段（Track 2）：
   - 使用GGUF量化模型（由HF模型转换而来）
   - 使用llama-cpp-python加载GGUF模型
   - 优势：内存占用小、推理速度快
   - 转换流程：HF模型 → 合并LoRA → 转GGUF → 量化
"""

import os
import json
import time
import logging
import gc
import re
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

    def __init__(self, config_path: Optional[str] = None, progress_callback=None):
        """
        初始化AI引擎

        Args:
            config_path: 配置文件路径
            progress_callback: 进度回调函数，签名为 callback(progress: int, message: str)
        """
        self.config = self._load_config(config_path)
        self.models = {}  # 存储加载的模型
        self.tokenizers = {}  # 存储tokenizer
        self.current_model = None
        self.current_language = None

        # 🆕 保存进度回调
        self.progress_callback = progress_callback

        # 🆕 GPU检测（在初始化时执行，确保每次都能看到）
        logger.info("=" * 60)
        logger.info("🔍 GPU加速检测")
        logger.info("=" * 60)

        # 先导入torch，避免UnboundLocalError
        torch_available = False
        cuda_available = False
        try:
            import torch
            torch_available = True
            logger.info(f"🔍 PyTorch版本: {torch.__version__}")
            cuda_available = torch.cuda.is_available()
            logger.info(f"🔍 CUDA是否可用: {cuda_available}")

            if cuda_available:
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
                logger.info(f"🎮 检测到 {gpu_count} 个GPU: {gpu_name}")
                logger.info("✅ GPU可用，模型加载时将启用GPU加速")
            else:
                logger.warning("⚠️ CUDA不可用，将使用CPU推理")
                logger.warning("💡 提示：安装支持CUDA的llama-cpp-python以启用GPU加速")
                logger.warning("   命令：CMAKE_ARGS=\"-DLLAMA_CUBLAS=on\" pip install llama-cpp-python --force-reinstall")
        except ImportError as e:
            logger.warning(f"⚠️ PyTorch未安装或导入失败: {e}")
            logger.warning("💡 提示：安装PyTorch CUDA版本以启用GPU检测")
        except Exception as e:
            logger.error(f"❌ GPU检测失败: {e}")
        logger.info("=" * 60)

        # 设备配置（自动启用GPU）
        self.device = "cpu"
        self.cuda_available = cuda_available
        if cuda_available:
            self.device = "cuda"
            logger.info("🚀 GPU加速已自动启用")
        else:
            logger.info("ℹ️ 使用CPU模式（GPU不可用）")

        logger.info(f"AI引擎初始化完成，使用设备: {self.device}")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "models": {
                "zh": {
                    "name": "Qwen/Qwen3-1.7B-Instruct",
                    "type": "gguf",  # 推理轨道使用GGUF格式
                    "path": "models/qwen/quantized/qwen-test-small.gguf",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                "en": {
                    "name": "mistralai/Mistral-7B-Instruct-v0.1",
                    "type": "gguf",  # 推理轨道使用GGUF格式
                    "path": "models/mistral/quantized/mistral-7b-instruct-v0.2-q4_k_m.gguf",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            },
            "quantization": {
                "enabled": True,
                "bits": 4,
                "use_bnb": True  # 使用BitsAndBytes量化（仅用于HuggingFace格式）
            },
            "memory_optimization": {
                "max_memory_mb": 3500,  # 4GB设备的内存限制
                "offload_to_cpu": True,
                "use_gradient_checkpointing": True
            },
            "use_gpu": False,  # 4GB设备默认不使用GPU
            "batch_size": 1,
            "max_length": 2048,
            "use_demo_mode": False  # 是否使用演示模式（模拟推理）
        }

        # 尝试从YAML配置文件加载
        try:
            import yaml
            zh_config_path = "configs/models/dual_model_config/zh_model.yaml"
            en_config_path = "configs/models/dual_model_config/en_model.yaml"

            if os.path.exists(zh_config_path):
                with open(zh_config_path, 'r', encoding='utf-8') as f:
                    zh_config = yaml.safe_load(f)
                    if zh_config:
                        default_config["models"]["zh"]["path"] = zh_config.get("path", default_config["models"]["zh"]["path"])
                        default_config["models"]["zh"]["temperature"] = zh_config.get("temperature", 0.7)
                        default_config["models"]["zh"]["top_p"] = zh_config.get("top_p", 0.9)
                        logger.info(f"从配置文件加载中文模型配置: {zh_config.get('path')}")

            if os.path.exists(en_config_path):
                with open(en_config_path, 'r', encoding='utf-8') as f:
                    en_config = yaml.safe_load(f)
                    if en_config:
                        default_config["models"]["en"]["path"] = en_config.get("path", default_config["models"]["en"]["path"])
                        default_config["models"]["en"]["temperature"] = en_config.get("temperature", 0.7)
                        default_config["models"]["en"]["top_p"] = en_config.get("top_p", 0.9)
                        logger.info(f"从配置文件加载英文模型配置: {en_config.get('path')}")
        except Exception as e:
            logger.warning(f"从YAML配置加载失败: {e}")

        # 如果提供了自定义配置文件，覆盖默认配置
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
        """
        加载GGUF格式模型（智能路径选择）

        重要说明：
        - GGUF模型用于推理阶段（Track 2: 推理轨道）
        - GGUF模型由HuggingFace原始模型转换而来
        - 转换流程：HF模型 → 合并LoRA → 转GGUF → 量化
        - 转换工具：models/converters/model_converter.py

        优先级：
        1. 训练后的GGUF模型（models/*/quantized/trained_*.gguf）
        2. 训练后的GGUF模型（models/*/quantized/trained/latest.gguf）
        3. 基础GGUF模型（配置文件中指定的路径）
        """
        try:
            base_model_path = model_config["path"]

            # 构建训练后模型的路径
            # 从基础路径推导训练模型路径
            import re
            from pathlib import Path
            import glob

            base_path = Path(base_model_path)
            trained_model_paths = []

            if "quantized" in base_path.parts:
                # 找到quantized目录的位置
                parts = list(base_path.parts)
                try:
                    quant_idx = parts.index("quantized")
                    quantized_dir = str(Path(*parts[:quant_idx+1]))

                    # 方法1: 查找 quantized 目录下的 trained_*.gguf 文件
                    pattern1 = os.path.join(quantized_dir, "trained_*.gguf")
                    trained_files = glob.glob(pattern1)
                    if trained_files:
                        # 按修改时间排序，选择最新的
                        trained_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                        trained_model_paths.append(trained_files[0])
                        logger.info(f"✅ 发现训练后的GGUF模型: {trained_files[0]}")

                    # 方法2: 查找 quantized/trained/latest.gguf
                    trained_parts = parts[:quant_idx+1] + ["trained", "latest.gguf"]
                    trained_model_path = str(Path(*trained_parts))
                    if os.path.exists(trained_model_path):
                        trained_model_paths.append(trained_model_path)
                        logger.info(f"✅ 发现训练后的GGUF模型: {trained_model_path}")

                except ValueError:
                    pass

            # 按优先级尝试加载模型
            model_paths_to_try = []

            # 添加训练后的模型
            for trained_path in trained_model_paths:
                model_paths_to_try.append((trained_path, "训练后的GGUF模型"))

            # 添加基础模型
            if os.path.exists(base_model_path):
                model_paths_to_try.append((base_model_path, "基础GGUF模型"))

            if not model_paths_to_try:
                logger.error(f"未找到可用的GGUF模型文件")
                logger.error(f"  尝试的路径: {', '.join(trained_model_paths) if trained_model_paths else '无'}, {base_model_path}")
                return None

            # 尝试加载第一个可用的模型
            for model_path, model_type in model_paths_to_try:
                try:
                    logger.info(f"正在加载{model_type}: {model_path}")

                    # 检查文件大小
                    file_size = os.path.getsize(model_path)
                    file_size_mb = file_size / (1024 * 1024)
                    logger.info(f"📦 模型文件大小: {file_size_mb:.2f} MB")

                    # 验证文件大小（GGUF模型至少应该有几十MB）
                    if file_size < 10 * 1024 * 1024:  # 小于10MB
                        logger.error(f"❌ 模型文件太小({file_size_mb:.2f} MB)，可能已损坏")
                        logger.error(f"💡 提示: 正常的GGUF模型文件应该至少有几百MB")
                        logger.error(f"💡 请重新下载或转换模型文件")
                        continue

                    # 配置llama-cpp参数
                    llama_config = {
                        "model_path": model_path,
                        "n_ctx": 8192,  # 增加上下文窗口到8192，支持批量处理多集字幕
                        "n_threads": os.cpu_count() or 4,
                        "verbose": False
                    }

                    # GPU加速配置（增强检测）
                    gpu_enabled = False
                    try:
                        import torch
                        logger.info(f"🔍 PyTorch版本: {torch.__version__}")
                        logger.info(f"🔍 CUDA是否可用: {torch.cuda.is_available()}")

                        if torch.cuda.is_available():
                            gpu_count = torch.cuda.device_count()
                            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
                            logger.info(f"🎮 检测到 {gpu_count} 个GPU: {gpu_name}")

                            # 使用GPU加速，将所有层卸载到GPU
                            llama_config["n_gpu_layers"] = -1  # -1表示所有层都使用GPU
                            llama_config["n_batch"] = 512  # 增加批处理大小以充分利用GPU
                            gpu_enabled = True
                            logger.info("✅ GPU加速已启用（所有层）")
                        else:
                            logger.warning("⚠️ CUDA不可用，使用CPU推理")
                            logger.warning("💡 提示：安装支持CUDA的llama-cpp-python以启用GPU加速")
                            logger.warning("   命令：CMAKE_ARGS=\"-DLLAMA_CUBLAS=on\" pip install llama-cpp-python --force-reinstall")
                    except ImportError as e:
                        logger.warning(f"⚠️ PyTorch未安装或导入失败: {e}")
                        logger.warning("💡 提示：安装PyTorch CUDA版本以启用GPU检测")
                    except Exception as e:
                        logger.error(f"❌ GPU检测失败: {e}")

                    # 记录最终配置
                    logger.info(f"📋 模型配置: n_ctx={llama_config['n_ctx']}, n_gpu_layers={llama_config.get('n_gpu_layers', 0)}, GPU={gpu_enabled}")

                    # 内存优化配置
                    memory_config = self.config.get("memory_optimization", {})
                    if memory_config.get("max_memory_mb"):
                        # 根据内存限制调整参数
                        max_memory_mb = memory_config["max_memory_mb"]
                        llama_config["n_batch"] = min(512, max_memory_mb // 10)

                    model = Llama(**llama_config)
                    logger.info(f"✅ {model_type}加载成功: {model_path}")
                    return model

                except Exception as e:
                    logger.warning(f"加载{model_type}失败: {e}")
                    continue

            logger.error("所有GGUF模型加载尝试均失败")
            return None

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
            try:
                if hasattr(self.current_model, "close"):
                    self.current_model.close()
            except Exception as _e:
                logger.debug(f"关闭模型句柄失败（忽略）：{_e}")
            del self.current_model
            self.current_model = None

        if self.current_language and self.current_language in self.models:
            try:
                _m = self.models[self.current_language]
                if hasattr(_m, "close"):
                    _m.close()
            except Exception:
                pass
            del self.models[self.current_language]

        if self.current_language and self.current_language in self.tokenizers:
            del self.tokenizers[self.current_language]

        # 强制垃圾回收
        gc.collect()
        try:
            import torch as _torch
            if hasattr(_torch, "cuda") and _torch.cuda.is_available():
                _torch.cuda.empty_cache()
        except Exception as _e:
            logger.debug(f"跳过CUDA缓存清理: {_e}")

        logger.info("已卸载当前模型")

    def generate(self, prompt: str, language: str = "zh", **kwargs) -> str:
        """
        生成文本响应（公开接口，供适配器调用）

        Args:
            prompt: 输入提示词
            language: 语言代码（zh或en）
            **kwargs: 其他生成参数（如max_tokens, temperature等）

        Returns:
            生成的文本响应
        """
        try:
            # 确保模型已加载
            if not self.current_model:
                logger.warning(f"模型未加载，尝试加载{language}模型...")
                if not self.load_model(language):
                    logger.error(f"加载{language}模型失败")
                    return ""

            # 切换到对应语言的模型（如果需要）
            if self.current_language != language:
                logger.info(f"切换语言模式: {self.current_language} -> {language}")
                if not self.switch_model(language):
                    logger.error(f"切换到{language}模型失败")
                    return ""

            # 调用内部生成方法
            response = self._generate_response(
                prompt,
                language,
                json_only=bool(kwargs.get("json_only", False))
            )

            return response

        except Exception as e:
            logger.error(f"生成响应失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ""

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

    def generate_viral_subtitle_batch(self, all_subtitles: List[List[Dict[str, Any]]],
                                      language: str = "auto",
                                      analysis_results: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        批量生成爆款风格字幕 - 分步骤混剪

        策略：
        步骤1：AI理解整个故事（第1-11集），然后逐集提取关键对话
        步骤2：AI合并所有关键对话，生成1个混剪SRT

        Args:
            all_subtitles: 所有字幕列表的列表，每个元素是一集的字幕列表
            language: 语言代码，auto为自动检测
            analysis_results: 可选的分析结果列表（叙事结构、节奏、片段建议等）

        Returns:
            List[Dict[str, Any]]: 生成的混剪爆款字幕列表（1个SRT）
        """
        try:
            # 自动检测语言
            if language == "auto":
                language = self._detect_language(all_subtitles[0] if all_subtitles else [])

            # 切换到对应模型
            if not self.switch_model(language):
                logger.error(f"无法切换到 {language} 模型")
                # 返回第一集作为降级处理
                return all_subtitles[0] if all_subtitles else []

            logger.info(f"开始生成混剪爆款字幕，共{len(all_subtitles)}集")
            logger.info(f"策略：分步骤处理 - 步骤0：理解整个故事，步骤1：逐集提取关键对话，步骤2：合并生成混剪SRT")

            # 🆕 更新进度：开始处理
            self._update_progress(0, "开始生成混剪爆款字幕...")

            # 🆕 启用七步重构算法（强制启用）
            logger.info("=" * 60)
            logger.info("🔍 初始化七步重构算法")
            logger.info("=" * 60)
            use_seven_step_algorithm = True
            screenplay_engineer = None
            try:
                logger.info("📦 正在导入ScreenplayEngineer...")
                from src.core.screenplay_engineer import ScreenplayEngineer
                logger.info("✅ ScreenplayEngineer导入成功")

                logger.info("🔧 正在初始化ScreenplayEngineer...")
                screenplay_engineer = ScreenplayEngineer()
                logger.info("✅ ScreenplayEngineer初始化成功")

                logger.info("🎯 七步重构算法已启用（深度语义分析→叙事结构解析→角色关系识别→情节转折点检测→爆款化改造→智能时间轴重新分配→质量验证）")
            except ImportError as e:
                use_seven_step_algorithm = False
                logger.error(f"❌ ScreenplayEngineer导入失败（ImportError）: {e}")
                logger.error("⚠️ 七步重构算法不可用，将使用简化版流程")
                import traceback
                logger.error(traceback.format_exc())
            except Exception as e:
                use_seven_step_algorithm = False
                logger.error(f"❌ ScreenplayEngineer初始化失败: {e}")
                logger.error("⚠️ 七步重构算法不可用，将使用简化版流程")
                import traceback
                logger.error(traceback.format_exc())
            logger.info("=" * 60)

            # ========== 步骤0：AI理解整个故事，生成故事摘要 ==========
            logger.info("=" * 60)
            logger.info("步骤0：AI理解整个故事，生成故事摘要")
            logger.info("=" * 60)
            self._update_progress(5, "AI理解整个故事...")

            # 🔧 新增：记录分析结果
            if analysis_results:
                logger.info(f"使用分析结果增强AI理解（共{len(analysis_results)}集）")

            # 构建提示词：让AI理解整个故事
            prompt = self._build_story_understanding_prompt(all_subtitles, language, analysis_results)

            # 生成回答
            response = self._generate_response(prompt, language)

            # 解析故事摘要
            story_summary = self._parse_story_summary(response, language)

            logger.info(f"故事摘要长度: {len(story_summary)} 字符")
            logger.debug(f"故事摘要: {story_summary[:500]}...")
            self._update_progress(15, "故事摘要生成完成")

            # 🆕 应用七步重构算法（如果启用）
            if use_seven_step_algorithm and screenplay_engineer and story_summary:
                logger.info("=" * 60)
                logger.info("🎯 启动七步重构算法")
                logger.info("=" * 60)
                logger.info("📝 输入故事摘要长度: {} 字符".format(len(story_summary)))
                self._update_progress(20, "🎬 步骤1/7：深度语义分析...")

                try:
                    # 调用七步重构算法
                    logger.info("🔄 调用ScreenplayEngineer.reconstruct_plot()...")
                    reconstructed_plot = screenplay_engineer.reconstruct_plot(story_summary, language)

                    # 如果重构成功，使用重构后的剧情
                    if reconstructed_plot and len(reconstructed_plot) > len(story_summary) * 0.5:
                        logger.info("=" * 60)
                        logger.info(f"✅ 七步重构算法执行成功")
                        logger.info(f"📊 原始摘要: {len(story_summary)} 字符")
                        logger.info(f"📊 重构后: {len(reconstructed_plot)} 字符")
                        logger.info(f"📊 增长率: {(len(reconstructed_plot) / len(story_summary) - 1) * 100:.1f}%")
                        logger.info("=" * 60)
                        story_summary = reconstructed_plot
                        self._update_progress(35, "✅ 七步重构完成")
                    else:
                        logger.warning("=" * 60)
                        logger.warning("⚠️ 七步重构结果不理想")
                        logger.warning(f"原因：重构后长度({len(reconstructed_plot) if reconstructed_plot else 0})小于原始长度的50%")
                        logger.warning("⚠️ 使用原始摘要")
                        logger.warning("=" * 60)
                        self._update_progress(35, "使用原始摘要")
                except Exception as e:
                    logger.error("=" * 60)
                    logger.error(f"❌ 七步重构算法执行失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    logger.error("⚠️ 回退到原始摘要")
                    logger.error("=" * 60)
                    self._update_progress(35, "回退到原始摘要")
            elif not use_seven_step_algorithm:
                logger.warning("⚠️ 七步重构算法未启用，跳过此步骤")
                self._update_progress(35, "跳过七步重构")

            # ========== 步骤1：AI根据故事摘要，逐集提取关键对话 ==========
            logger.info("=" * 60)
            logger.info("步骤1：AI根据故事摘要，逐集提取关键对话")
            logger.info("=" * 60)
            self._update_progress(40, "开始提取关键对话...")

            key_dialogues_list = []
            total_episodes = len(all_subtitles)
            for episode_idx, episode_subtitles in enumerate(all_subtitles):
                # 🆕 更新进度：逐集处理
                episode_progress = 40 + int((episode_idx / total_episodes) * 20)  # 40-60%
                self._update_progress(episode_progress, f"正在处理第{episode_idx + 1}/{total_episodes}集...")
                logger.info(f"正在处理第{episode_idx + 1}集...")

                # 🔧 方案1：获取当前集的分析结果
                current_analysis = None
                if analysis_results and episode_idx < len(analysis_results):
                    current_analysis = analysis_results[episode_idx]
                    logger.info(f"第{episode_idx + 1}集：使用分析结果增强关键对话提取")

                # 构建提示词：让AI根据故事摘要，提取当前集的关键对话
                prompt = self._build_key_dialogue_extraction_prompt(
                    story_summary, episode_subtitles, episode_idx, language, current_analysis
                )

                # 生成回答
                response = self._generate_response(prompt, language)

                # 解析关键对话
                key_dialogues = self._parse_key_dialogues(
                    response, episode_subtitles, episode_idx + 1, language
                )

                logger.info(f"第{episode_idx + 1}集：提取到 {len(key_dialogues)} 条关键对话")
                key_dialogues_list.append(key_dialogues)

            # ========== 步骤2：分批生成混剪SRT ==========
            logger.info("=" * 60)
            logger.info("步骤2：分批生成混剪SRT")
            logger.info("=" * 60)
            self._update_progress(60, "开始生成混剪SRT...")

            # 合并所有关键对话
            all_key_dialogues = []
            for episode_idx, key_dialogues in enumerate(key_dialogues_list):
                for dialogue in key_dialogues:
                    # 保留原始字幕的完整信息
                    dialogue_copy = dialogue.copy()
                    dialogue_copy['original_episode'] = episode_idx + 1  # 标记来源集数

                    # 🔧 修复：处理字段名不一致问题
                    # SRTParser返回的字段：id, start_time, end_time, text
                    # 但代码期望：index, start, end, text
                    dialogue_copy['original_index'] = dialogue.get('index', dialogue.get('id', 0))

                    # 时间码字段映射和格式转换
                    original_start = dialogue.get('start', dialogue.get('start_time', ''))
                    original_end = dialogue.get('end', dialogue.get('end_time', ''))

                    # 如果是秒数格式（float），转换为SRT格式（HH:MM:SS,mmm）
                    if isinstance(original_start, (int, float)):
                        original_start = self._format_time(int(original_start * 1000))
                    if isinstance(original_end, (int, float)):
                        original_end = self._format_time(int(original_end * 1000))

                    dialogue_copy['original_start'] = original_start
                    dialogue_copy['original_end'] = original_end

                    # 验证时间码不为空
                    if not dialogue_copy['original_start'] or not dialogue_copy['original_end']:
                        logger.warning(f"第{episode_idx + 1}集：对话时间码为空，dialogue={dialogue}")

                    all_key_dialogues.append(dialogue_copy)

            logger.info(f"总共提取到 {len(all_key_dialogues)} 条关键对话")

            # 分批处理
            batch_size = 40  # 每批40条关键对话
            batches = [all_key_dialogues[i:i + batch_size] for i in range(0, len(all_key_dialogues), batch_size)]
            logger.info(f"分成 {len(batches)} 批处理，每批约 {batch_size} 条")

            # 生成故事摘要（简化版，约200-300字）
            story_summary_short = self._extract_short_summary(story_summary, language)
            logger.info(f"故事摘要（简化版）长度: {len(story_summary_short)} 字符")

            # 逐批生成混剪SRT
            all_viral_subtitles = []
            total_batches = len(batches)
            for batch_idx, batch in enumerate(batches):
                # 🆕 更新进度：批次处理
                batch_progress = 60 + int((batch_idx / total_batches) * 30)  # 60-90%
                self._update_progress(batch_progress, f"正在处理第{batch_idx + 1}/{total_batches}批...")
                logger.info(f"正在处理第 {batch_idx + 1}/{total_batches} 批...")

                # 优先尝试JSON模式，降低解析失败概率
                prompt_json = self._build_batch_merge_prompt_json(
                    story_summary_short, batch, batch_idx, len(batches), language
                )
                response_json = self._generate_response(prompt_json, language, json_only=True)
                batch_viral_subtitles = self._parse_batch_mixed_cut_subtitles_json(
                    response_json, batch, batch_idx, language
                )
                if not batch_viral_subtitles:
                    logger.info(f"第 {batch_idx + 1} 批：JSON模式未产出，尝试索引模式")
                    # 尝试更简单的索引模式，降低结构复杂度
                    prompt_idx = self._build_batch_merge_prompt_indices(
                        story_summary_short, batch, batch_idx, len(batches), language
                    )
                    response_idx = self._generate_response(prompt_idx, language)
                    batch_viral_subtitles = self._parse_batch_indices_response(
                        response_idx, batch, batch_idx, language
                    )

                    # 索引模式最小数量保障（例如至少16条，且不超过批大小）
                    if batch_viral_subtitles:
                        try:
                            min_needed = min(16, len(batch))
                            if len(batch_viral_subtitles) < min_needed:
                                before = len(batch_viral_subtitles)
                                batch_viral_subtitles = self._ensure_minimum_index_result(
                                    batch_viral_subtitles, batch, min_needed, story_summary_short, batch_idx
                                )
                                logger.info(f"第 {batch_idx + 1} 批（索引-补齐）：从 {before} → {len(batch_viral_subtitles)} 条")
                        except Exception as _e:
                            logger.warning(f"第 {batch_idx + 1} 批（索引-补齐）失败: {_e}")

                if not batch_viral_subtitles:
                    logger.info(f"第 {batch_idx + 1} 批：索引模式未产出，回退至SRT解析")
                    # 构建提示词：让AI生成当前批次的混剪SRT
                    prompt = self._build_batch_merge_prompt(
                        story_summary_short, batch, batch_idx, len(batches), language
                    )
                    # 生成回答
                    response = self._generate_response(prompt, language)
                    # 解析混剪字幕
                    batch_viral_subtitles = self._parse_batch_mixed_cut_subtitles(
                        response, batch, batch_idx, language
                    )

                logger.info(f"第 {batch_idx + 1} 批：生成 {len(batch_viral_subtitles)} 条混剪字幕")

                # 🔧 新增：批次间连贯性验证
                if all_viral_subtitles and batch_viral_subtitles:
                    coherence_score = self._validate_batch_coherence(
                        all_viral_subtitles[-5:],  # 前一批的最后5条
                        batch_viral_subtitles[:5],  # 当前批的前5条
                        language
                    )
                    logger.info(f"批次 {batch_idx} 与前批的连贯性评分: {coherence_score:.2f}/10")

                    if coherence_score < 5.0:
                        logger.warning(f"批次 {batch_idx} 连贯性较低，可能需要调整")

                all_viral_subtitles.extend(batch_viral_subtitles)

            logger.info(f"总共生成 {len(all_viral_subtitles)} 条混剪字幕")

            # 🧩 重排/精剪阶段：优先按“原时间线快节奏精剪”，否则走“蒙太奇重排”
            try:
                # 环境开关：CHRONO_MODE 优先生效；默认开启；MONTAGE_MODE 默认关闭
                if not hasattr(self, "_chrono_mode"):
                    env_chrono = os.getenv("CHRONO_MODE", "1").lower()
                    self._chrono_mode = env_chrono in ("1", "true", "yes", "on", "y")
                if not hasattr(self, "_montage_mode"):
                    env_montage = os.getenv("MONTAGE_MODE", "0").lower()
                    self._montage_mode = env_montage in ("1", "true", "yes", "on", "y")
                logger.info(f"剪辑模式选择: CHRONO_MODE={self._chrono_mode}, MONTAGE_MODE={self._montage_mode}, CHRONO_RETAIN={os.getenv('CHRONO_RETAIN','0.7')}")

                if getattr(self, "_chrono_mode", False):
                    logger.info("启用按原时间线快节奏精剪（去冗、保时间顺序）")
                    all_viral_subtitles = self._arrange_chronological_fast(all_viral_subtitles, language=language)
                elif getattr(self, "_montage_mode", True):
                    logger.info("启用蒙太奇重排（低相似度跳切，避免ABA）")
                    all_viral_subtitles = self._arrange_for_montage(all_viral_subtitles, avoid_aba=True)
            except Exception as _e:
                logger.warning(f"重排/精剪阶段失败，继续原顺序: {_e}")


            # 句缝拼接（同集、未完句、原始间隔<=2s）
            try:
                stitched_subtitles = self._stitch_incomplete_sentences(all_viral_subtitles, language)
            except Exception:
                stitched_subtitles = all_viral_subtitles
            # 重新生成时间轴
            self._update_progress(90, "重新生成时间轴...")
            viral_subtitles = self._regenerate_timeline(stitched_subtitles, language)

            self._update_progress(100, "混剪爆款字幕生成完成！")
            logger.info(f"成功生成混剪爆款字幕，共 {len(viral_subtitles)} 条")
            return viral_subtitles

        except Exception as e:
            logger.error(f"生成混剪爆款字幕失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 返回第一集作为降级处理
            return all_subtitles[0] if all_subtitles else []

    def _validate_batch_coherence(self, prev_batch_end: List[Dict[str, Any]],
                                   curr_batch_start: List[Dict[str, Any]],
                                   language: str) -> float:
        """
        验证批次间的连贯性

        Args:
            prev_batch_end: 前一批的最后几条字幕
            curr_batch_start: 当前批的前几条字幕
            language: 语言代码

        Returns:
            float: 连贯性评分 (0-10)
        """
        try:
            if not prev_batch_end or not curr_batch_start:
                return 10.0  # 如果没有前批，默认连贯

            # 提取文本
            prev_text = " ".join([sub.get('text', '') for sub in prev_batch_end])
            curr_text = " ".join([sub.get('text', '') for sub in curr_batch_start])

            # 简单的连贯性评分：基于文本相似度和剧情连续性
            score = 7.0  # 基础分

            # 检查是否有重复内容（降低分数）
            if prev_text and curr_text:
                # 计算文本重叠度
                prev_words = set(prev_text.split())
                curr_words = set(curr_text.split())
                overlap = len(prev_words & curr_words) / max(len(prev_words), len(curr_words))

                if overlap > 0.5:
                    score -= 2.0  # 重复过多
                elif overlap < 0.1:
                    # 蒙太奇模式（且未启用按时序精剪）下：低重叠加分；时序模式则惩罚
                    if getattr(self, "_montage_mode", False) and not getattr(self, "_chrono_mode", False):
                        score += 1.0
                    else:
                        score -= 1.0  # 完全不相关

            # 检查剧情连续性（基于original_episode）
            if prev_batch_end[-1].get('original_episode') and curr_batch_start[0].get('original_episode'):
                prev_episode = prev_batch_end[-1].get('original_episode')
                curr_episode = curr_batch_start[0].get('original_episode')

                # 如果跨度太大，可能不连贯（蒙太奇模式下不惩罚）
                if getattr(self, "_chrono_mode", False) or not getattr(self, "_montage_mode", False):
                    if abs(curr_episode - prev_episode) > 3:
                        score -= 1.0

            return max(0.0, min(10.0, score))

        except Exception as e:
            logger.warning(f"连贯性验证失败: {e}")
            return 7.0  # 默认中等连贯性

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
            prompt = f"""你是一个顶级的短剧爆款内容创作专家，精通短视频平台的流量密码和用户心理。

【任务】
将普通的短剧字幕转化为具有爆款潜力的吸引人内容。

【原始字幕】
{original_text}

【爆款转换核心逻辑】
1. **理解剧情脉络**：深入理解整个故事的剧情发展、人物关系、冲突矛盾
2. **识别关键剧情点**：找出最具冲突性、最具悬念、最具情感冲击力的剧情点
3. **重新构建内容**：
   - 强化冲突：将普通对话转化为强烈的情感冲突
   - 制造悬念：在关键位置设置悬念，吸引观众继续观看
   - 情感共鸣：使用能引发观众情感共鸣的表达方式
   - 反转惊喜：适当添加反转元素，制造惊喜感
   - 观众互动：添加能引发观众评论和讨论的元素

4. **爆款表达技巧**：
   - 使用短句、感叹句、疑问句，增强节奏感
   - 使用"竟然"、"居然"、"没想到"等词汇制造惊喜
   - 使用"你们觉得呢？"、"猜猜接下来会发生什么？"等互动元素
   - 使用"太狠了"、"绝了"、"炸裂"等网络热词
   - 强化人物性格特点，使用符合人物身份的台词

5. **内容重构规则**：
   - 可以合并多条字幕，使表达更连贯
   - 可以拆分长字幕，增强节奏感
   - 可以完全重写某些场景的字幕，只要符合剧情逻辑
   - 可以调整表达顺序，先抛出悬念，再揭示答案
   - 保持字幕数量基本一致（允许±20%的浮动）

【输出格式】
请按照以下格式输出改写后的爆款字幕：

1. [第一条爆款字幕]
2. [第二条爆款字幕]
3. [第三条爆款字幕]
...

【开始转换】
改写后的爆款字幕："""
        else:
            prompt = f"""You are a top-tier viral content creator specializing in short drama, mastering the traffic secrets and user psychology of short video platforms.

【Task】
Transform ordinary short drama subtitles into viral, engaging content.

【Original Subtitles】
{original_text}

【Viral Conversion Core Logic】
1. **Understand the Plot**: Deeply understand the story development, character relationships, and conflicts
2. **Identify Key Plot Points**: Find the most conflicting, suspenseful, and emotionally impactful plot points
3. **Reconstruct Content**:
   - Intensify conflicts: Transform ordinary dialogues into strong emotional conflicts
   - Create suspense: Set up suspense at key positions to attract viewers
   - Emotional resonance: Use expressions that resonate with the audience
   - Plot twists: Add reversal elements to create surprises
   - Audience interaction: Add elements that trigger comments and discussions

4. **Viral Expression Techniques**:
   - Use short sentences, exclamations, questions to enhance rhythm
   - Use words like "surprisingly", "unexpectedly", "didn't expect" to create surprises
   - Use interactive elements like "What do you think?", "Guess what happens next?"
   - Use trending internet slang
   - Strengthen character traits with appropriate dialogues

5. **Content Reconstruction Rules**:
   - Can merge multiple subtitles for better flow
   - Can split long subtitles to enhance rhythm
   - Can completely rewrite some scene subtitles as long as it fits the plot
   - Can adjust expression order, throw out suspense first, then reveal the answer
   - Keep the number of subtitles roughly the same (±20% fluctuation allowed)

【Output Format】
Please output the rewritten viral subtitles in the following format:

1. [First viral subtitle]
2. [Second viral subtitle]
3. [Third viral subtitle]
...

【Start Conversion】
Rewritten viral subtitles:"""

        return prompt

    def _build_single_episode_viral_prompt(self, all_subtitles: List[List[Dict[str, Any]]],
                                           episode_idx: int, language: str) -> str:
        """构建单集爆款转换提示词 - AI查看所有集（精简版），但只生成当前集"""
        # 提取所有集的字幕文本（精简版：每集只取前10条，用于理解整个故事）
        all_episodes_text = []
        for ep_idx, subtitles in enumerate(all_subtitles):
            episode_text = f"=== 第{ep_idx + 1}集（前10条概览） ===\n"
            # 只取前10条字幕作为概览
            preview_subtitles = subtitles[:10]
            episode_text += "\n".join([
                f"{i+1}. {sub.get('text', '')}"
                for i, sub in enumerate(preview_subtitles)
            ])
            all_episodes_text.append(episode_text)

        combined_text = "\n\n".join(all_episodes_text)

        # 当前集的字幕
        current_episode_subtitles = all_subtitles[episode_idx]
        current_episode_text = "\n".join([
            f"{i+1}. {sub.get('text', '')}"
            for i, sub in enumerate(current_episode_subtitles)
        ])

        if language == "zh":
            prompt = f"""你是一个顶级的短剧内容剪辑专家。

【任务】
从第{episode_idx + 1}集的字幕中删除废话和冗余内容，保留关键对话。

【完整故事概览（第1-{len(all_subtitles)}集，每集前10条）】
{combined_text}

【当前需要处理的：第{episode_idx + 1}集（完整，共{len(current_episode_subtitles)}条）】
{current_episode_text}

【删减要求】
1. 理解整个故事（第1-{len(all_subtitles)}集）的完整剧情
2. 删除废话、重复、无关紧要的字幕
3. 保留关键对话、重要剧情、精彩片段
4. 保留约50%-70%的字幕（约{int(len(current_episode_subtitles) * 0.6)}条）

【输出格式】
只输出保留的字幕序号，用逗号分隔，例如：
1,2,4,5,7,10,12,15,18,20,22,25,28,30,32,35,38

**重要**：
- 只输出序号，不要输出字幕内容
- 序号用逗号分隔，不要换行
- 序号范围：1-{len(current_episode_subtitles)}

现在开始输出第{episode_idx + 1}集保留的字幕序号：

"""
        else:
            prompt = f"""You are a top-tier viral content creator.

【Task】
Transform Episode {episode_idx + 1}'s ordinary subtitles into viral, engaging content.

【Complete Story Overview (Episodes 1-{len(all_subtitles)}, first 10 lines each)】
{combined_text}

【Current Episode to Transform: Episode {episode_idx + 1} (Complete)】
{current_episode_text}

【Viral Conversion Requirements】
1. Understand the complete story (Episodes 1-{len(all_subtitles)})
2. Generate viral version for each subtitle in Episode {episode_idx + 1}
3. Must add viral elements:
   - Use exclamations, questions to enhance emotion
   - Add suspense and interactive elements
   - Use words like "OMG", "surprisingly", "didn't expect"
   - Strengthen conflicts and emotional expression
4. **Important**: Each subtitle must be different, do NOT repeat the same content!

【Output Format】
Only output viral subtitles for Episode {episode_idx + 1}, one per line:
1. [Viral subtitle 1]
2. [Viral subtitle 2]
3. [Viral subtitle 3]
...

【Examples】
Original: Where did this queen come from
Viral: OMG! Where did this queen come from?!

Original: The battlefield is not where you should be
Viral: The battlefield is NOT where you should be! Too dangerous!

**Note**: Generate {len(current_episode_subtitles)} different viral subtitles, do NOT repeat!

Start generating viral subtitles for Episode {episode_idx + 1}:

"""

        return prompt

    def _build_batch_viral_prompt(self, all_subtitles: List[List[Dict[str, Any]]], language: str) -> str:
        """构建批量爆款转换提示词 - 整体理解所有剧情"""
        # 提取所有集的字幕文本
        all_episodes_text = []
        for episode_idx, subtitles in enumerate(all_subtitles):
            episode_text = f"=== 第{episode_idx + 1}集 ===\n"
            episode_text += "\n".join([
                f"{i+1}. {sub.get('text', '')}"
                for i, sub in enumerate(subtitles)
            ])
            all_episodes_text.append(episode_text)

        combined_text = "\n\n".join(all_episodes_text)

        if language == "zh":
            prompt = f"""你是一个顶级的短剧爆款内容创作专家，精通短视频平台的流量密码和用户心理。

【任务】
将普通的短剧字幕转化为具有爆款潜力的吸引人内容。你需要先理解整个故事的完整剧情（第1-{len(all_subtitles)}集），然后为每一集生成爆款字幕。

【原始字幕（共{len(all_subtitles)}集）】
{combined_text}

【爆款转换核心逻辑】
1. **理解整个故事**：
   - 深入理解第1-{len(all_subtitles)}集的完整剧情发展
   - 识别主要人物关系、核心冲突、剧情高潮
   - 理解故事的整体节奏和情感曲线

2. **识别关键剧情点**：
   - 找出每一集中最具冲突性、最具悬念、最具情感冲击力的剧情点
   - 识别能引发观众好奇心的关键信息
   - 找出能制造反转和惊喜的剧情转折点

3. **重新构建内容**：
   - **强化冲突**：将普通对话转化为强烈的情感冲突
   - **制造悬念**：在关键位置设置悬念，吸引观众继续观看
   - **情感共鸣**：使用能引发观众情感共鸣的表达方式
   - **反转惊喜**：适当添加反转元素，制造惊喜感
   - **观众互动**：添加能引发观众评论和讨论的元素

4. **爆款表达技巧**：
   - 使用短句、感叹句、疑问句，增强节奏感
   - 使用"竟然"、"居然"、"没想到"、"天哪"等词汇制造惊喜
   - 使用"你们觉得呢？"、"猜猜接下来会发生什么？"等互动元素
   - 使用"太狠了"、"绝了"、"炸裂"、"震惊"等网络热词
   - 强化人物性格特点，使用符合人物身份的台词
   - 适当使用"..."、"！！！"等符号增强情感表达

5. **内容重构规则**：
   - 可以合并多条字幕，使表达更连贯
   - 可以拆分长字幕，增强节奏感
   - 可以完全重写某些场景的字幕，只要符合剧情逻辑
   - 可以调整表达顺序，先抛出悬念，再揭示答案
   - 保持每集字幕数量基本一致（允许±20%的浮动）
   - 可以删除不重要的场景，强化关键场景

6. **整体连贯性**：
   - 保持各集之间的连贯性和整体节奏
   - 在每集结尾设置悬念，吸引观众观看下一集
   - 在关键剧情点强化情感表达

【输出格式】
请按照以下格式输出改写后的爆款字幕，每集之间用 "=== 第X集 ===" 分隔。

**重要**：
- 必须为每一集的每一条原始字幕都生成对应的爆款字幕
- 如果原始字幕有38条，爆款字幕也必须有38条（可以合并或拆分，但总数要接近）
- 不要使用占位符，必须生成真实的爆款内容
- 每条字幕必须是完整的、有意义的内容

示例格式：
=== 第1集 ===
1. 天哪！这是什么情况？
2. 她竟然穿越到了古代战场！
3. 这位女将军的气势太强了！
...（继续生成所有字幕）

=== 第2集 ===
1. 没想到她的身份这么特殊！
2. 这个反转太震撼了！
3. 接下来会发生什么？
...（继续生成所有字幕）

【开始转换】
请先理解整个故事（第1-{len(all_subtitles)}集），然后为每一集生成爆款字幕。

**关键要求**：
1. 必须为每条原始字幕生成对应的爆款字幕
2. 不要使用占位符
3. 必须添加爆款元素：感叹号、疑问句、悬念、互动等
4. 必须重构内容，不要简单复制原文
5. 示例：
   - 原文："哪来的女王"
   - 爆款："天哪！这是哪来的女王？！"
   - 原文："战场不是你该来的地方"
   - 爆款："战场可不是你该来的地方！太危险了！"

现在开始生成：

"""
        else:
            prompt = f"""You are a top-tier viral content creator specializing in short drama, mastering the traffic secrets and user psychology of short video platforms.

【Task】
Transform ordinary short drama subtitles into viral, engaging content. You need to first understand the complete plot of the entire story (Episodes 1-{len(all_subtitles)}), then generate viral subtitles for each episode.

【Original Subtitles ({len(all_subtitles)} Episodes)】
{combined_text}

【Viral Conversion Core Logic】
1. **Understand the Entire Story**:
   - Deeply understand the complete plot development of Episodes 1-{len(all_subtitles)}
   - Identify main character relationships, core conflicts, plot climaxes
   - Understand the overall rhythm and emotional curve of the story

2. **Identify Key Plot Points**:
   - Find the most conflicting, suspenseful, and emotionally impactful plot points in each episode
   - Identify key information that can trigger audience curiosity
   - Find plot twists that can create reversals and surprises

3. **Reconstruct Content**:
   - **Intensify conflicts**: Transform ordinary dialogues into strong emotional conflicts
   - **Create suspense**: Set up suspense at key positions to attract viewers
   - **Emotional resonance**: Use expressions that resonate with the audience
   - **Plot twists**: Add reversal elements to create surprises
   - **Audience interaction**: Add elements that trigger comments and discussions

4. **Viral Expression Techniques**:
   - Use short sentences, exclamations, questions to enhance rhythm
   - Use words like "surprisingly", "unexpectedly", "didn't expect", "OMG" to create surprises
   - Use interactive elements like "What do you think?", "Guess what happens next?"
   - Use trending internet slang like "epic", "mind-blowing", "shocking"
   - Strengthen character traits with appropriate dialogues
   - Use "...", "!!!" to enhance emotional expression

5. **Content Reconstruction Rules**:
   - Can merge multiple subtitles for better flow
   - Can split long subtitles to enhance rhythm
   - Can completely rewrite some scene subtitles as long as it fits the plot
   - Can adjust expression order, throw out suspense first, then reveal the answer
   - Keep the number of subtitles roughly the same per episode (±20% fluctuation allowed)
   - Can remove unimportant scenes and strengthen key scenes

6. **Overall Coherence**:
   - Maintain coherence and overall rhythm between episodes
   - Set up suspense at the end of each episode to attract viewers to watch the next episode
   - Strengthen emotional expression at key plot points

【Output Format】
Please output the rewritten viral subtitles in the following format, separated by "=== Episode X ===" between episodes.

**Important**:
- Must generate corresponding viral subtitles for every original subtitle in each episode
- If original has 38 subtitles, viral must also have 38 (can merge or split, but total should be close)
- Do NOT use placeholders, must generate real viral content
- Each subtitle must be complete and meaningful

Example format:
=== Episode 1 ===
1. OMG! What's happening here?
2. She actually traveled to an ancient battlefield!
3. This female general's aura is so powerful!
...(continue generating all subtitles)

=== Episode 2 ===
1. Didn't expect her identity to be so special!
2. This plot twist is mind-blowing!
3. What will happen next?
...(continue generating all subtitles)

【Start Conversion】
Please first understand the entire story (Episodes 1-{len(all_subtitles)}), then generate viral subtitles for each episode.

**Key Requirements**:
1. Must generate corresponding viral subtitles for every original subtitle
2. Do NOT use placeholders
3. Must add viral elements: exclamations, questions, suspense, interaction, etc.
4. Must reconstruct content, do NOT simply copy original text
5. Examples:
   - Original: "Where did this queen come from"
   - Viral: "OMG! Where did this queen come from?!"
   - Original: "The battlefield is not where you should be"
   - Viral: "The battlefield is NOT where you should be! Too dangerous!"

Start generating now:

"""

        return prompt

    def _build_mixed_cut_viral_prompt(self, all_subtitles: List[List[Dict[str, Any]]], language: str) -> str:
        """构建混剪爆款转换提示词 - 从所有集中提取精华，混剪成一个完整视频"""
        # 提取所有集的字幕文本
        all_episodes_text = []
        for episode_idx, subtitles in enumerate(all_subtitles):
            episode_text = f"=== 第{episode_idx + 1}集 ===\n"
            episode_text += "\n".join([
                f"{i+1}. {sub.get('text', '')}"
                for i, sub in enumerate(subtitles)
            ])
            all_episodes_text.append(episode_text)

        combined_text = "\n\n".join(all_episodes_text)

        if language == "zh":
            prompt = f"""你是一个专业的短剧剪辑师，精通短视频平台的流量密码和用户心理。

【任务】
将第1-{len(all_subtitles)}集的原片字幕混剪成一个爆款视频的字幕。

【原片字幕（第1-{len(all_subtitles)}集）】
{combined_text}

【混剪要求】
1. **理解完整故事**：
   - 深入理解第1-{len(all_subtitles)}集的完整剧情发展
   - 识别主要人物关系、核心冲突、剧情高潮
   - 理解故事的整体节奏和情感曲线

2. **提取精华内容**：
   - 从所有{len(all_subtitles)}集中选择最精彩的对话
   - 删除废话、重复、过渡性对话
   - 保留关键剧情、重要对话、情感高潮

3. **重新排列组合**：
   - 按照新的故事逻辑重新排序
   - 制造悬念和反转
   - 保持故事的连贯性和节奏感

4. **生成新的时间轴**：
   - 从 00:00:00 开始
   - 每条字幕约1-3秒
   - 总时长约5-10分钟

【输出格式】
请按照SRT格式输出混剪后的爆款字幕：

1
00:00:00,000 --> 00:00:01,500
[第一条爆款字幕]

2
00:00:01,500 --> 00:00:03,000
[第二条爆款字幕]

3
00:00:03,000 --> 00:00:05,000
[第三条爆款字幕]

...（继续生成约200-300条字幕）

【重要提示】
- 不要使用占位符，必须生成真实的字幕内容
- 每条字幕必须是完整的、有意义的内容
- 时间轴必须连续递增
- 总共生成约200-300条字幕

【开始混剪】
现在开始生成混剪后的爆款字幕：

"""
        else:
            prompt = f"""You are a professional short drama editor, mastering the traffic secrets and user psychology of short video platforms.

【Task】
Mix and cut the original subtitles from Episodes 1-{len(all_subtitles)} into a single viral video subtitle.

【Original Subtitles (Episodes 1-{len(all_subtitles)})】
{combined_text}

【Mixing Requirements】
1. **Understand the Complete Story**:
   - Deeply understand the complete plot development of Episodes 1-{len(all_subtitles)}
   - Identify main character relationships, core conflicts, plot climaxes
   - Understand the overall rhythm and emotional curve of the story

2. **Extract Essence Content**:
   - Select the most exciting dialogues from all {len(all_subtitles)} episodes
   - Remove filler, repetition, transitional dialogues
   - Keep key plots, important dialogues, emotional climaxes

3. **Rearrange and Recombine**:
   - Reorder according to new story logic
   - Create suspense and plot twists
   - Maintain story coherence and rhythm

4. **Generate New Timeline**:
   - Start from 00:00:00
   - Each subtitle about 1-3 seconds
   - Total duration about 5-10 minutes

【Output Format】
Please output the mixed-cut viral subtitles in SRT format:

1
00:00:00,000 --> 00:00:01,500
[First viral subtitle]

2
00:00:01,500 --> 00:00:03,000
[Second viral subtitle]

3
00:00:03,000 --> 00:00:05,000
[Third viral subtitle]

...(continue generating about 200-300 subtitles)

【Important Notes】
- Do NOT use placeholders, must generate real subtitle content
- Each subtitle must be complete and meaningful
- Timeline must be continuously increasing
- Generate about 200-300 subtitles in total

【Start Mixing】
Now start generating the mixed-cut viral subtitles:

"""

        return prompt

    def _build_story_understanding_prompt(self, all_subtitles: List[List[Dict[str, Any]]],
                                          language: str,
                                          analysis_results: Optional[List[Dict[str, Any]]] = None) -> str:
        """构建故事理解提示词 - 让AI理解整个故事，生成故事摘要"""
        # 提取所有集的字幕文本
        all_episodes_text = []
        for episode_idx, subtitles in enumerate(all_subtitles):
            episode_text = f"=== 第{episode_idx + 1}集 ===\n"
            episode_text += "\n".join([
                f"{i+1}. {sub.get('text', '')}"
                for i, sub in enumerate(subtitles)
            ])

            # 🔧 新增：添加分析结果（如果有）
            if analysis_results and episode_idx < len(analysis_results):
                analysis = analysis_results[episode_idx]
                if analysis:
                    episode_text += "\n\n【分析结果】\n"

                    # 添加叙事结构分析
                    if 'narrative' in analysis:
                        narrative = analysis['narrative']
                        episode_text += f"叙事类型: {narrative.get('narrative_type', '未知')}\n"
                        episode_text += f"结构: {narrative.get('structure', '未知')}\n"

                    # 添加节奏分析
                    if 'rhythm' in analysis:
                        rhythm = analysis['rhythm']
                        episode_text += f"节奏: {rhythm.get('overall_pace', '未知')}\n"

                    # 添加片段建议
                    if 'segments' in analysis:
                        segments = analysis['segments']
                        if 'key_segments' in segments:
                            key_count = len(segments['key_segments'])
                            episode_text += f"关键片段数: {key_count}\n"

            all_episodes_text.append(episode_text)

        combined_text = "\n\n".join(all_episodes_text)

        if language == "zh":
            prompt = f"""你是一个专业的短剧剪辑师，精通短视频平台的流量密码和用户心理。

【任务】
理解第1-{len(all_subtitles)}集的完整故事，生成故事摘要。

【原片字幕（第1-{len(all_subtitles)}集）】
{combined_text}

【理解要求】
1. **深入理解完整故事**：
   - 识别主要人物、核心冲突、剧情高潮
   - 理解故事的整体节奏和情感曲线
   - 识别每集的关键剧情点

2. **生成故事摘要**：
   - 总结整个故事的主线剧情
   - 列出每集的关键剧情点
   - 约500-1000字

【输出格式】
**整体故事**：
[总结整个故事的主线剧情，约200-300字]

**每集关键剧情**：
第1集：[关键剧情点]
第2集：[关键剧情点]
...
第{len(all_subtitles)}集：[关键剧情点]

【开始理解】
请理解整个故事并生成摘要：

"""
        else:
            prompt = f"""You are a professional short drama editor, mastering the traffic secrets and user psychology of short video platforms.

【Task】
Understand the complete story of Episodes 1-{len(all_subtitles)} and generate a story summary.

【Original Subtitles (Episodes 1-{len(all_subtitles)})】
{combined_text}

【Understanding Requirements】
1. **Deeply Understand the Complete Story**:
   - Identify main characters, core conflicts, plot climaxes
   - Understand the overall rhythm and emotional curve of the story
   - Identify key plot points in each episode

2. **Generate Story Summary**:
   - Summarize the main plot of the entire story
   - List key plot points for each episode
   - About 500-1000 words

【Output Format】
**Overall Story**:
[Summarize the main plot of the entire story, about 200-300 words]

**Key Plot Points for Each Episode**:
Episode 1: [Key plot points]
Episode 2: [Key plot points]
...
Episode {len(all_subtitles)}: [Key plot points]

【Start Understanding】
Please understand the entire story and generate a summary:

"""

        return prompt

    def _parse_story_summary(self, response: str, language: str) -> str:
        """解析故事摘要"""
        try:
            # 检查响应是否为空
            if not response or not response.strip():
                logger.error("AI响应为空，返回空摘要")
                return ""

            # 直接返回响应作为摘要
            return response.strip()

        except Exception as e:
            logger.error(f"解析故事摘要失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return ""

    def _build_key_dialogue_extraction_prompt(self, story_summary: str,
                                              episode_subtitles: List[Dict[str, Any]],
                                              episode_idx: int, language: str,
                                              analysis_result: Optional[Dict[str, Any]] = None) -> str:
        """构建关键对话提取提示词 - 让AI根据故事摘要，提取当前集的关键对话

        Args:
            story_summary: 整个故事的摘要
            episode_subtitles: 当前集的字幕列表
            episode_idx: 当前集的索引（从0开始）
            language: 语言代码
            analysis_result: 可选的分析结果（叙事结构、节奏、片段建议等）
        """
        # 当前集的完整字幕
        current_episode_text = "\n".join([
            f"{i+1}. {sub.get('text', '')}"
            for i, sub in enumerate(episode_subtitles)
        ])

        # 计算目标数量（默认60%，可由环境变量/配置覆盖）
        total_count = len(episode_subtitles)
        # 优先读取环境变量（0.1-0.9），其次读取YAML配置：configs/narrative_config.yaml -> key_dialogue_extraction.retention_ratio
        retain_ratio = 0.6
        try:
            env_ratio = os.getenv("VACL_DIALOGUE_RETAINED_PCT")
            if env_ratio:
                retain_ratio = float(env_ratio)
        except Exception:
            pass
        try:
            from src.utils.file_utils import safe_read_yaml
            ncfg = safe_read_yaml("configs/narrative_config.yaml", {}) or {}
            kd = (ncfg.get("key_dialogue_extraction") or {})
            cfg_ratio = kd.get("retention_ratio")
            if cfg_ratio is not None:
                retain_ratio = float(cfg_ratio)
        except Exception:
            pass
        retain_ratio = max(0.3, min(0.8, retain_ratio))
        target_count = int(total_count * retain_ratio)
        min_count = int(total_count * max(0.1, retain_ratio - 0.1))
        max_count = int(total_count * min(0.9, retain_ratio + 0.1))

        if language == "zh":
            # 🔧 优化1：简化任务描述 + 明确数量要求
            # 🔧 方案1：使用分析结果提供选择提示

            # 构建分析结果提示（如果有）
            analysis_hint = ""
            if analysis_result:
                # 从叙事分析中提取关键情节点
                narrative_hints = []
                if "narrative_structure" in analysis_result:
                    narrative = analysis_result["narrative_structure"]
                    if "key_plot_points" in narrative:
                        narrative_hints = narrative["key_plot_points"]

                # 从节奏分析中提取建议片段
                rhythm_hints = []
                if "rhythm_analysis" in analysis_result:
                    rhythm = analysis_result["rhythm_analysis"]
                    if "suggested_segments" in rhythm:
                        rhythm_hints = rhythm["suggested_segments"]

                # 构建提示文本
                if narrative_hints or rhythm_hints:
                    analysis_hint = "\n【选择提示】\n"
                    if narrative_hints:
                        analysis_hint += f"关键情节点: {', '.join(narrative_hints[:5])}\n"
                    if rhythm_hints:
                        analysis_hint += f"建议片段: {', '.join([str(s) for s in rhythm_hints[:5]])}\n"

            prompt = f"""你是一个专业的短剧剪辑师。

【整个故事摘要】
{story_summary}

【任务】
从第{episode_idx + 1}集的{total_count}条字幕中，选择{target_count}条关键对话（最少{min_count}条，最多{max_count}条）。
{analysis_hint}
【第{episode_idx + 1}集完整字幕】
{current_episode_text}

【选择标准】
1. 包含重要剧情信息的对话
2. 包含情感强烈的对话
3. 包含人物关系变化的对话
4. 对话长度较长的（超过5个字）

【输出要求】
- 必须选择{target_count}条对话（最少{min_count}条，最多{max_count}条）
- 只输出序号，用逗号分隔
- 示例：1,3,4,10,15,20

【开始选择】
请选择{target_count}条关键对话的序号：
"""
        else:
            # 🔧 优化1：简化任务描述 + 明确数量要求（英文版）
            # 🔧 方案1：使用分析结果提供选择提示（英文版）

            # 构建分析结果提示（如果有）
            analysis_hint = ""
            if analysis_result:
                # 从叙事分析中提取关键情节点
                narrative_hints = []
                if "narrative_structure" in analysis_result:
                    narrative = analysis_result["narrative_structure"]
                    if "key_plot_points" in narrative:
                        narrative_hints = narrative["key_plot_points"]

                # 从节奏分析中提取建议片段
                rhythm_hints = []
                if "rhythm_analysis" in analysis_result:
                    rhythm = analysis_result["rhythm_analysis"]
                    if "suggested_segments" in rhythm:
                        rhythm_hints = rhythm["suggested_segments"]

                # 构建提示文本
                if narrative_hints or rhythm_hints:
                    analysis_hint = "\n【Selection Hints】\n"
                    if narrative_hints:
                        analysis_hint += f"Key Plot Points: {', '.join(narrative_hints[:5])}\n"
                    if rhythm_hints:
                        analysis_hint += f"Suggested Segments: {', '.join([str(s) for s in rhythm_hints[:5]])}\n"

            prompt = f"""You are a professional short drama editor.

【Story Summary】
{story_summary}

【Task】
Select {target_count} key dialogues from {total_count} subtitles in Episode {episode_idx + 1} (minimum {min_count}, maximum {max_count}).
{analysis_hint}
【Episode {episode_idx + 1} Complete Subtitles】
{current_episode_text}

【Selection Criteria】
1. Dialogues containing important plot information
2. Dialogues with strong emotions
3. Dialogues showing character relationship changes
4. Longer dialogues (more than 5 characters)

【Output Requirements】
- Must select {target_count} dialogues (minimum {min_count}, maximum {max_count})
- Output only numbers, separated by commas
- Example: 1,3,4,10,15,20

【Start Selection】
Please select {target_count} key dialogue numbers:
"""

        return prompt

    def _build_merge_prompt(self, story_summary: str, key_dialogues_list: List[List[Dict[str, Any]]], language: str) -> str:
        """构建合并提示词 - 让AI根据故事摘要和所有关键对话，生成混剪SRT"""
        # 提取所有关键对话
        all_key_dialogues = []
        for episode_idx, key_dialogues in enumerate(key_dialogues_list):
            episode_text = f"=== 第{episode_idx + 1}集关键对话 ===\n"
            episode_text += "\n".join([
                f"{i+1}. {sub.get('text', '')}"
                for i, sub in enumerate(key_dialogues)
            ])
            all_key_dialogues.append(episode_text)

        combined_text = "\n\n".join(all_key_dialogues)

        if language == "zh":
            prompt = f"""你是一个专业的短剧剪辑师，精通短视频平台的流量密码和用户心理。

【任务】
将所有关键对话合并成一个混剪爆款视频的字幕。

【整个故事摘要】
{story_summary}

【所有关键对话（第1-{len(key_dialogues_list)}集）】
{combined_text}

【合并要求】
1. **根据故事摘要重新排列组合**：
   - 按照新的故事逻辑重新排序
   - 制造悬念和反转
   - 保持故事的连贯性和节奏感

2. **生成新的时间轴**：
   - 从 00:00:00 开始
   - 每条字幕约1-3秒
   - 总时长约5-10分钟

【输出格式】
请按照SRT格式输出混剪后的爆款字幕：

1
00:00:00,000 --> 00:00:01,500
[第一条爆款字幕]

2
00:00:01,500 --> 00:00:03,000
[第二条爆款字幕]

3
00:00:03,000 --> 00:00:05,000
[第三条爆款字幕]

...（继续生成约100-200条字幕）

【重要提示】
- 不要使用占位符，必须生成真实的字幕内容
- 每条字幕必须是完整的、有意义的内容
- 时间轴必须连续递增
- 总共生成约100-200条字幕

【开始合并】
现在开始生成混剪后的爆款字幕：

"""
        else:
            prompt = f"""You are a professional short drama editor, mastering the traffic secrets and user psychology of short video platforms.

【Task】
Merge all key dialogues into a single viral video subtitle.

【Story Summary】
{story_summary}

【All Key Dialogues (Episodes 1-{len(key_dialogues_list)})】
{combined_text}

【Merging Requirements】
1. **Rearrange and Recombine Based on Story Summary**:
   - Reorder according to new story logic
   - Create suspense and plot twists
   - Maintain story coherence and rhythm

2. **Generate New Timeline**:
   - Start from 00:00:00
   - Each subtitle about 1-3 seconds
   - Total duration about 5-10 minutes

【Output Format】
Please output the mixed-cut viral subtitles in SRT format:

1
00:00:00,000 --> 00:00:01,500
[First viral subtitle]

2
00:00:01,500 --> 00:00:03,000
[Second viral subtitle]

3
00:00:03,000 --> 00:00:05,000
[Third viral subtitle]

...(continue generating about 100-200 subtitles)

【Important Notes】
- Do NOT use placeholders, must generate real subtitle content
- Each subtitle must be complete and meaningful
- Timeline must be continuously increasing
- Generate about 100-200 subtitles in total

【Start Merging】
Now start generating the mixed-cut viral subtitles:

"""

        return prompt

    def _extract_short_summary(self, story_summary: str, language: str) -> str:
        """提取故事摘要的简化版（约200-300字）"""
        try:
            # 如果摘要太长，只保留前300字
            if len(story_summary) > 300:
                # 尝试找到第一个段落结束的位置
                lines = story_summary.split('\n')
                short_summary = ""
                for line in lines:
                    if len(short_summary) + len(line) > 300:
                        break
                    short_summary += line + "\n"

                if not short_summary.strip():
                    # 如果没有找到合适的段落，直接截取前300字
                    short_summary = story_summary[:300] + "..."

                return short_summary.strip()
            else:
                return story_summary.strip()
        except Exception as e:
            logger.error(f"提取简化摘要失败: {str(e)}")
            return story_summary[:300] if len(story_summary) > 300 else story_summary

    def _build_batch_merge_prompt(self, story_summary_short: str, batch: List[Dict[str, Any]],
                                   batch_idx: int, total_batches: int, language: str) -> str:
        """构建分批合并提示词 - 让AI生成当前批次的混剪SRT"""
        # 提取当前批次的关键对话
        batch_text = "\n".join([
            f"{i+1}. [第{dialogue.get('episode', '?')}集] {dialogue.get('text', '')}"
            for i, dialogue in enumerate(batch)
        ])

        if language == "zh":
            prompt = f"""从以下对话中选择并重新排序，生成SRT格式字幕。

【对话列表】
{batch_text}

【输出要求】
1. 只输出SRT格式：序号 + 时间轴 + 文本
2. 时间轴格式必须是：HH:MM:SS,mmm --> HH:MM:SS,mmm
3. 每条字幕时长1.5秒
4. 不要输出任何其他内容

【正确示例】
1
00:00:00,000 --> 00:00:01,500
哪来的女王

2
00:00:01,500 --> 00:00:03,000
她竟是法力通天的神真女君啊

【错误示例（禁止）】
❌ 03:24 --> 56,879（时间格式错误）
❌ 02:45,987 --> 36.5s（时间格式错误）
❌ **第?集** 哪来的女王（包含额外文字）
❌ 好的，现在开始生成...（包含解释）
❌ ```srt（包含代码块标记）

立即输出SRT格式字幕（不要输出任何其他内容）：
"""
        else:
            prompt = f"""Select and reorder dialogues to generate SRT format subtitles.

【Dialogue List】
{batch_text}

【Output Requirements】
1. Only output SRT format: index + timeline + text
2. Timeline format MUST be: HH:MM:SS,mmm --> HH:MM:SS,mmm
3. Each subtitle duration is 1.5 seconds
4. Do NOT output any other content

【Correct Example】
1
00:00:00,000 --> 00:00:01,500
Where did the queen come from

2
00:00:01,500 --> 00:00:03,000
She is actually the divine goddess

【Wrong Examples (FORBIDDEN)】
❌ 03:24 --> 56,879 (wrong time format)
❌ 02:45,987 --> 36.5s (wrong time format)
❌ **Episode?** Where did the queen come from (extra text)
❌ OK, now generating... (explanation)
❌ ```srt (code block marker)

Output SRT format subtitles immediately (no other content):
"""

        return prompt


    def _build_batch_merge_prompt_json(self, story_summary_short: str, batch: List[Dict[str, Any]],
                                       batch_idx: int, total_batches: int, language: str) -> str:
        """构建分批合并提示词(JSON模式)——约束输出为JSON数组，降低解析失败概率"""
        batch_text = "\n".join([
            f"[第{d.get('episode','?')}集] {d.get('text','').strip()}" for d in batch if d.get('text')
        ])
        if language == "zh":
            prompt = f"""你是一名资深短视频剪辑师。任务：基于摘要与对话列表，选择并重排对白，输出字幕JSON数组。

【严格输出要求（务必遵守）】
- 仅返回合法 JSON 数组；不得包含任何解释、分析、理由、道歉、提示语、Markdown 代码块或其他文本
- 数组元素为对象，键必须为 "start"、"end"、"text"
- 若信息不足，也必须返回空数组 []（不要输出任何额外字符）
- 时间字符串可先近似或占位，后续会统一重排时间轴
- 每条字幕约 1–3 秒，保证语义连贯

【示例（仅作格式参考）】
[
  {{"start":"00:00:00,000","end":"00:00:01,600","text":"台词A"}},
  {{"start":"00:00:01,600","end":"00:00:03,000","text":"台词B"}}
]

【剧情摘要(精简)】
{story_summary_short}

【对话列表】
{batch_text}

现在请直接输出 JSON 数组（不要任何额外文本）："""
        else:
            prompt = f"""You are a senior short-video editor. Task: select and reorder dialogues based on the summary and list, and OUTPUT a JSON array of subtitles.

[STRICT OUTPUT RULES]
- Return ONLY a valid JSON array; DO NOT include explanations, analysis, apologies, hints, or Markdown code fences
- Each element must be an object with keys "start", "end", "text"
- If information is insufficient, you MUST return an empty array [] (and nothing else)
- Time strings can be placeholders; timeline will be rebuilt later
- Each subtitle should be about 1–3 seconds; keep narrative coherence

[Example format]
[
  {{"start":"00:00:00,000","end":"00:00:01,600","text":"Line A"}},
  {{"start":"00:00:01,600","end":"00:00:03,000","text":"Line B"}}
]

[Story Summary (short)]
{story_summary_short}

[Dialogues]
{batch_text}

Now output the JSON array only (no extra text):"""
        return prompt

    def _parse_batch_mixed_cut_subtitles_json(self, response: str, batch: List[Dict[str, Any]],
                                              batch_idx: int, language: str) -> List[Dict[str, Any]]:
        """解析JSON模式下的混剪字幕；解析失败返回空列表以触发SRT或规则兜底"""
        try:
            logger.info(f"第{batch_idx + 1}批(JSON)响应长度: {len(response)} 字符")
            if not response or not response.strip():
                logger.warning(f"第{batch_idx + 1}批(JSON)：响应为空")
                return []
            # 预清洗：去除Markdown围栏、替换花括号引号
            data = None
            clean = (response or "").strip()
            try:
                clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", clean, flags=re.I)
            except Exception:
                pass
            clean = clean.replace("“", '"').replace("”", '"').replace("‘", '"').replace("’", '"').replace("：", ":")

            def _json_salvage(txt: str):
                # 直接尝试完整解析
                try:
                    return json.loads(txt)
                except Exception:
                    pass

                def fix_json_like(s: str) -> str:
                    s2 = s
                    # 修复遗漏的键名（如 ":end" / ":start"）
                    s2 = re.sub(r'([,{]\s*):\s*end"', r'\1"end"', s2)
                    s2 = re.sub(r'([,{]\s*):\s*start"', r'\1"start"', s2)
                    # 为未加引号的键名补引号
                    s2 = re.sub(r'([\{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', s2)
                    # 去除尾随逗号
                    s2 = re.sub(r",\s*([\]\}])", r"\1", s2)
                    return s2

                # 优先在所有数组候选中选取“可解析且元素最多”的数组
                best = None
                best_len = -1
                for m in re.finditer(r"\[[\s\S]*?\]", txt):
                    cand = m.group(0)
                    for c in (cand, fix_json_like(cand)):
                        try:
                            obj = json.loads(c)
                            if isinstance(obj, list):
                                score = len(obj)
                                if score > best_len:
                                    best = obj
                                    best_len = score
                        except Exception:
                            continue
                if best is not None:
                    return best

                # 退而求其次：尝试单个对象（原样与修复后）
                m = re.search(r"\{[\s\S]*?\}", txt)
                if m:
                    cand = m.group(0)
                    for c in (cand, fix_json_like(cand)):
                        try:
                            return json.loads(c)
                        except Exception:
                            continue
                return None

            try:
                data = _json_salvage(clean)
            except Exception as e:
                data = None
            if data is None:
                logger.warning(f"第{batch_idx + 1}批(JSON)：解析JSON失败: 预处理后仍无法解析")
                return []

            # 支持 {"subtitles": [...]} 、{"items": [...]}，或直接单对象/数组
            if isinstance(data, dict):
                # 如果是单条对象且包含 text，无论是否带时间字段，均包装为数组（时间轴后续重排）
                if ("text" in data):
                    data = [data]
                else:
                    for key in ["subtitles", "items", "data", "lines", "result"]:
                        if key in data and isinstance(data[key], list):
                            data = data[key]
                            break
            if not isinstance(data, list):
                logger.warning(f"第{batch_idx + 1}批(JSON)：JSON不是数组")
                return []
            # 若为字符串数组，转换为对象数组
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                data = [{"text": str(x)} for x in data]


            out = []
            time_pat = re.compile(r"\d{2}:\d{2}:\d{2},\d{3}")

            def _to_srt_time(val: Any) -> Optional[str]:
                s = str(val).strip()
                s = s.replace("，", ",")
                # 规范SRT
                if time_pat.fullmatch(s):
                    return s
                # H?:MM:SS(.mmm) 或 MM:SS(.mmm)
                m = re.fullmatch(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})(?:[.,](\d{1,3}))?", s)
                if m:
                    h = int(m.group(1) or 0)
                    mi = int(m.group(2))
                    se = int(m.group(3))
                    ms = m.group(4)
                    ms = int((ms or "0").ljust(3, "0")[:3])
                    return f"{h:02d}:{mi:02d}:{se:02d},{ms:03d}"
                # 浮点秒
                try:
                    f = float(s)
                    if 0 <= f < 36000:
                        ms = int(round(f * 1000))
                        h = ms // 3600000
                        ms %= 3600000
                        mi = ms // 60000
                        ms %= 60000
                        se = ms // 1000
                        ms %= 1000
                        return f"{h:02d}:{mi:02d}:{se:02d},{ms:03d}"
                except Exception:
                    pass
                # 纯毫秒带后缀
                m2 = re.fullmatch(r"(\d+)\s*ms", s, re.I)
                if m2:
                    ms = int(m2.group(1))
                    h = ms // 3600000
                    ms %= 3600000
                    mi = ms // 60000
                    ms %= 60000
                    se = ms // 1000
                    ms %= 1000
                    return f"{h:02d}:{mi:02d}:{se:02d},{ms:03d}"
                return None

            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                text = str(item.get("text", "")).strip()
                if not text:
                    for k in ("content", "line", "subtitle", "sentence", "dialogue", "content_text", "value"):
                        v = str(item.get(k, "")).strip()
                        if v:
                            text = v
                            break
                if not text:
                    continue
                start_raw = item.get("start")
                if start_raw is None:
                    start_raw = item.get("from") or item.get("begin") or item.get("start_ms") or item.get("startMs")
                end_raw = item.get("end")
                if end_raw is None:
                    end_raw = item.get("to") or item.get("stop") or item.get("end_ms") or item.get("endMs")
                start = _to_srt_time(start_raw) if start_raw is not None else None
                end = _to_srt_time(end_raw) if end_raw is not None else None
                if not start:
                    start = "00:00:00,000"
                if not end:
                    end = "00:00:01,500"
                # 若end<=start，强制加1.6s
                try:
                    def _to_ms(ts: str) -> int:
                        hh, mm, ss_ms = ts.split(":")
                        ss, ms = ss_ms.split(",")
                        return int(hh) * 3600000 + int(mm) * 60000 + int(ss) * 1000 + int(ms)
                    st_ms = _to_ms(start)
                    ed_ms = _to_ms(end)
                    if ed_ms <= st_ms:
                        ed_ms = st_ms + 1600
                        h = ed_ms // 3600000
                        r = ed_ms % 3600000
                        m = r // 60000
                        r %= 60000
                        s = r // 1000
                        ms = r % 1000
                        end = f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                except Exception:
                    pass
                # 匹配原始字幕
                matched_original = None
                for original_dialogue in batch:
                    original_text = original_dialogue.get('text', '')
                    if original_text and (text in original_text or original_text in text or
                                          self._text_similarity(text, original_text) > 0.5):
                        matched_original = original_dialogue
                        break
                obj = {
                    "index": i + 1,
                    "start": start,
                    "end": end,
                    "text": text
                }
                if matched_original:
                    obj['original_episode'] = matched_original.get('original_episode', 0)
                    obj['original_index'] = matched_original.get('original_index', 0)
                    obj['original_start'] = matched_original.get('original_start', '')
                    obj['original_end'] = matched_original.get('original_end', '')
                out.append(obj)
            logger.info(f"第{batch_idx + 1}批(JSON)：成功解析 {len(out)} 条混剪字幕")
            return out
        except Exception as e:
            logger.error(f"第{batch_idx + 1}批(JSON)：解析异常: {e}")
            return []


    def _build_batch_merge_prompt_indices(self, story_summary_short: str, batch: List[Dict[str, Any]],
                                           batch_idx: int, total_batches: int, language: str) -> str:
        """构建分批合并提示词（索引模式）——仅输出选中对白的行号序列，降低结构化难度"""
        lines = []
        for i, d in enumerate(batch, 1):
            ep = d.get('original_episode', d.get('episode', '?'))
            text = str(d.get('text', '')).strip().replace('\n', ' ')
            if len(text) > 120:
                text = text[:120] + '…'
            lines.append(f"{i}) [第{ep}集] {text}")
        if language == 'zh':
            prompt = f"""
你是一名资深短视频剪辑师。任务：基于“剧情摘要(精简)”与“对话列表(编号)”选择并重排对白。

【输出要求（务必遵守）】
- 仅返回索引数组，如 [3,7,2,10]；不要任何解释、分析、道歉、提示语、Markdown或其他文本
- 索引从 1 开始，对应下方“对话列表”的行号
- 若信息不足，也必须返回空数组 []（不要输出任何额外字符）
	- 目标数量：优先选择并重排 15–30 条；若不足，尽量接近 15 条


【示例】
对话列表：
1) [第1集] 你别走
2) [第1集] 我非走不可
输出：
[2,1]

【剧情摘要(精简)】
{story_summary_short}

【对话列表(编号) | 第{batch_idx+1}/{total_batches}批，总计{len(batch)}条】
{chr(10).join(lines)}

现在请仅输出索引数组：
"""
        else:
            prompt = f"""
You are a senior short-video editor. Task: Select and reorder dialogues based on the short story summary and the numbered dialogue list.

[Output rules]
- Return ONLY an array of indices like [3,7,2,10]; no explanations/markdown/extra text
- Indices start from 1 and refer to the line numbers below
- If unsure, return [] (empty array) with no extra characters
	- Target count: Prefer selecting and reordering 15–30 items; if not enough, aim for at least 15


[Example]
Dialogues:
1) [Ep1] Don't go
2) [Ep1] I must leave
Output:
[2,1]

[Story Summary (short)]
{story_summary_short}

[Dialogues (numbered) | Batch {batch_idx+1}/{total_batches}, size={len(batch)}]
{chr(10).join(lines)}

Now output the indices array only:
"""
        return prompt

    def _parse_batch_indices_response(self, response: str, batch: List[Dict[str, Any]],
                                      batch_idx: int, language: str) -> List[Dict[str, Any]]:
        """解析索引模式响应：抽取数字序列并映射到当前批对话，失败返回空列表"""
        try:
            logger.info(f"第{batch_idx + 1}批（索引）响应长度: {len(response)} 字符")
            if not response or not response.strip():
                return []
            txt = response.strip()
            # 优先提取方括号中的数字序列；若无方括号，则全局提取数字
            m = re.search(r"\[(.*?)\]", txt, flags=re.S)
            segment = m.group(1) if m else txt
            nums = re.findall(r"\d+", segment)
            if not nums:
                return []
            n = len(batch)
            seen = set()
            order = []
            for s in nums:
                k = int(s)
                if 1 <= k <= n and k not in seen:
                    seen.add(k)
                    order.append(k)
            # 限制上限，避免过长（后续仍会重排时间轴）
            if len(order) > 200:
                order = order[:200]
            out = []
            for rank, idx1 in enumerate(order, 1):
                src = batch[idx1 - 1]
                text = str(src.get('text', '')).strip()
                if not text:
                    continue
                obj = {"index": rank, "text": text}
                # 透传原始映射信息，便于时间轴再生成时保留来源
                for key in ("original_episode", "original_index", "original_start", "original_end"):
                    if key in src:
                        obj[key] = src[key]
                out.append(obj)
            logger.info(f"第{batch_idx + 1}批（索引）：成功解析 {len(out)} 条混剪字幕")
            return out
        except Exception as e:
            logger.error(f"第{batch_idx + 1}批（索引）：解析异常: {e}")
            return []

    def _ensure_minimum_index_result(self, items: List[Dict[str, Any]], batch: List[Dict[str, Any]],
                                     min_count: int, story_summary_short: str, batch_idx: int) -> List[Dict[str, Any]]:
        """在索引模式已产出部分结果的基础上，进行最小数量保障补齐。
        优先按与剧情摘要的相似度补齐，不足再用规则引擎补齐，最后对结果重新编号。
        """
        try:
            orig_count = len(items)
            # 已使用文本集合（去重）
            used_texts = set()
            for it in items:
                t = str(it.get('text', '')).strip()
                if t:
                    used_texts.add(t)

            def _score_dialogue(d: Dict[str, Any]):
                t = str(d.get('text', '')).strip()
                sim = self._text_similarity(t, story_summary_short)
                length_bonus = min(len(t), 60) / 120.0  # 最多+0.5
                punct_bonus = 0.2 if any(ch in t for ch in ['！', '!', '？', '?', '…']) else 0.0
                return sim + length_bonus + punct_bonus, sim, len(t), t

            candidates = []
            for d in batch:
                t = str(d.get('text', '')).strip()
                if not t or t in used_texts:
                    continue
                s, sim, L, txt = _score_dialogue(d)
                candidates.append((s, sim, L, d))

            # 第一优先：相似度>=0.55 的候选
            primary = [(s, sim, L, d) for (s, sim, L, d) in candidates if sim >= 0.55]
            primary.sort(key=lambda x: x[0], reverse=True)

            selected: List[Dict[str, Any]] = []
            need = max(0, min_count - len(items))
            for s, sim, L, d in primary:
                if need <= 0:
                    break
                t = str(d.get('text', '')).strip()
                if not t or t in used_texts:
                    continue
                selected.append(d)
                used_texts.add(t)
                need -= 1

            # 第二优先：其余候选中，按长度与综合分排序填充
            if need > 0:
                rest = [(s, sim, L, d) for (s, sim, L, d) in candidates if str(d.get('text', '')).strip() not in used_texts]
                rest.sort(key=lambda x: (x[2], x[0]), reverse=True)  # 长文本略优先
                for s, sim, L, d in rest:
                    if need <= 0:
                        break
                    t = str(d.get('text', '')).strip()
                    if not t or t in used_texts:
                        continue
                    selected.append(d)
                    used_texts.add(t)
                    need -= 1

            sim_added = len(selected)
            # 将相似度补齐的对话转为字幕对象并追加
            for d in selected:
                obj = {"text": str(d.get('text', '')).strip()}
                for key in ("original_episode", "original_index", "original_start", "original_end"):
                    if key in d:
                        obj[key] = d[key]
                items.append(obj)

            # 若仍不足，使用规则引擎补齐剩余数量
            rule_added = 0
            if len(items) < min_count:
                remain = min_count - len(items)
                leftovers = [d for d in batch if str(d.get('text', '')).strip() not in used_texts][:remain]
                if leftovers:
                    gen = self._generate_srt_from_dialogues(leftovers, batch_idx) or []
                    for g in gen[:remain]:
                        t = str(g.get('text', '')).strip()
                        if not t or t in used_texts:
                            continue
                        items.append({
                            "text": t,
                            "original_episode": g.get("original_episode", 0),
                            "original_index": g.get("original_index", 0),
                            "original_start": g.get("original_start", ""),
                            "original_end": g.get("original_end", "")
                        })
                        used_texts.add(t)
                        rule_added += 1

            # 重新编号
            for i, it in enumerate(items, 1):
                it["index"] = i

            logger.info(
                f"第{batch_idx + 1}批（索引-补齐）目标≥{min_count}：索引{orig_count} + 相似度补齐{sim_added} + 规则补齐{rule_added} → 最终{len(items)}"
            )
            return items
        except Exception as e:
            logger.warning(f"第{batch_idx + 1}批（索引-补齐）异常: {e}")
            return items


    def _generate_response(self, prompt: str, language: str, json_only: bool = False) -> str:
        """生成AI回答"""
        try:
            model_config = self.config["models"][language]

            if model_config["type"] == "gguf":
                # 调试日志与提示词长度
                logger.info("开始调用GGUF模型生成响应...")
                logger.debug(f"提示词长度: {len(prompt)} 字符")
                logger.debug(f"提示词前500字符: {prompt[:500]}")

                # 1) 安全截断超长提示词（避免超过上下文窗口导致极慢或卡死）
                try:
                    max_prompt_chars = int(self.config.get("max_prompt_chars", 20000))
                except Exception:
                    max_prompt_chars = 20000
                effective_prompt = prompt
                if len(effective_prompt) > max_prompt_chars:
                    effective_prompt = effective_prompt[-max_prompt_chars:]
                    logger.warning(f"提示词过长，已截断到后{max_prompt_chars}字符以避免超出上下文窗口")
                # 在仅JSON模式下，追加更严格的输出约束（避免fenced code & 说明性文字）
                try:
                    if json_only and "json" not in effective_prompt.lower():
                        if language == "zh":
                            effective_prompt += "\n仅返回合法JSON（对象或数组），不要输出Markdown代码块、解释或任何额外文本。\n"
                        else:
                            effective_prompt += "\nReturn only valid JSON (object or array). Do not include code fences, explanations, or any extra text.\n"
                except Exception:
                    pass

                # 2) 生成超时控制与通用参数
                timeout_sec = int(self.config.get("generation_timeout_sec", 600))
                max_tokens = model_config.get("max_tokens", 8192)
                temperature = model_config.get("temperature", 0.5)
                top_p = model_config.get("top_p", 0.9)

                generated_text = ""
                start_ts = time.time()
                last_log_ts = start_ts

                try:
                    # 优先使用可流式的接口，便于实现超时控制与进度日志
                    if hasattr(self.current_model, "create_completion"):
                        for chunk in self.current_model.create_completion(
                            prompt=effective_prompt,
                            max_tokens=max_tokens,
                            temperature=(0.2 if json_only else temperature),
                            top_p=(0.8 if json_only else top_p),
                            repeat_penalty=1.8,
                            stop=["用户:", "User:", "\n\n\n"],
                            stream=True,
                        ):
                            piece = chunk.get("choices", [{}])[0].get("text", "")
                            if piece:
                                generated_text += piece

                            now = time.time()
                            if now - last_log_ts >= 5:
                                elapsed = now - start_ts
                                logger.info(f"GGUF生成中... 已输出{len(generated_text)}字符, 用时{elapsed:.1f}s")
                                last_log_ts = now

                            # 超时检查
                            if now - start_ts > timeout_sec:
                                logger.error(f"GGUF生成超时({timeout_sec}s)，返回部分结果，长度={len(generated_text)}")
                                break
                    else:
                        # 兼容旧接口（非流式，无法中途打断，但仍受max_tokens限制）
                        resp = self.current_model(
                            effective_prompt,
                            max_tokens=max_tokens,
                            temperature=(0.2 if json_only else temperature),
                            top_p=(0.8 if json_only else top_p),
                            repeat_penalty=1.8,
                            stop=["用户:", "User:", "\n\n\n"],
                        )
                        generated_text = resp["choices"][0]["text"]
                except Exception as e:
                    logger.error(f"GGUF生成失败: {e}")
                    return ""

                logger.info(f"GGUF模型响应长度: {len(generated_text)} 字符")
                # 避免日志过大：长文本仅打印部分
                if len(generated_text) <= 4000:
                    logger.info(f"GGUF模型完整响应:\n{generated_text}")
                else:
                    logger.debug(f"GGUF模型部分响应(前4000):\n{generated_text[:4000]}")

                # 针对要求JSON输出或json_only模式，尽量提取首个合法JSON片段
                try:
                    if json_only or ("json" in effective_prompt.lower()):
                        json_text = None
                        # 先尝试```json fenced```中的对象或数组
                        m = re.search(r"```json\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", generated_text, re.I)
                        if m:
                            cand = m.group(1)
                            try:
                                json.loads(cand)
                                json_text = cand
                            except Exception:
                                json_text = None
                        # 再尝试全文内首个对象
                        if not json_text:
                            m2 = re.search(r"\{[\s\S]*?\}", generated_text)
                            if m2:
                                cand2 = m2.group(0)
                                try:
                                    json.loads(cand2)
                                    json_text = cand2
                                except Exception:
                                    json_text = None
                        # 最后尝试全文内首个数组
                        if not json_text:
                            m3 = re.search(r"\[[\s\S]*?\]", generated_text)
                            if m3:
                                cand3 = m3.group(0)
                                try:
                                    json.loads(cand3)
                                    json_text = cand3
                                except Exception:
                                    json_text = None
                        if json_text:
                            logger.info(f"检测到JSON输出，已提取JSON片段: 长度={len(json_text)}")
                            return json_text
                        if json_only:
                            # 严格模式未能提取，返回空数组以触发回退逻辑（而非字典导致的非数组告警）
                            logger.warning("json_only模式下未能提取到合法JSON，返回空数组[]")
                            return "[]"
                except Exception:
                    pass

                # 全局最大返回长度裁剪，避免异常长文本导致上游卡顿
                try:
                    max_response_chars = int(self.config.get("max_response_chars", 4000))
                except Exception:
                    max_response_chars = 4000
                if len(generated_text) > max_response_chars:
                    generated_text = generated_text[:max_response_chars]

                return generated_text

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
            # 添加调试日志
            logger.info(f"AI响应长度: {len(response)} 字符")
            logger.debug(f"AI响应前500字符: {response[:500]}")

            # 检查响应是否为空
            if not response or not response.strip():
                logger.error("AI响应为空，返回原始字幕")
                return original_subtitles

            # 按行分割回答
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            logger.info(f"解析到 {len(lines)} 行非空内容")

            # 提取编号的字幕行
            subtitle_lines = []
            for line in lines:
                # 匹配 "1. 文本" 格式
                if re.match(r'^\d+\.\s+', line):
                    text = re.sub(r'^\d+\.\s+', '', line)
                    subtitle_lines.append(text)

            # 如果没有找到编号格式，直接使用所有行
            if not subtitle_lines:
                logger.warning(f"未找到编号格式，使用所有 {len(lines)} 行")
                subtitle_lines = lines

            logger.info(f"提取到 {len(subtitle_lines)} 条字幕文本")

            # 构建新的字幕列表
            viral_subtitles = []
            for i, original_sub in enumerate(original_subtitles):
                new_sub = original_sub.copy()

                # 使用生成的文本，如果超出范围则使用原文本
                if i < len(subtitle_lines):
                    new_sub["text"] = subtitle_lines[i]
                else:
                    logger.warning(f"字幕 {i+1} 超出生成范围，使用原文本")
                    new_sub["text"] = original_sub.get("text", "")

                viral_subtitles.append(new_sub)

            logger.info(f"成功构建 {len(viral_subtitles)} 条爆款字幕")
            return viral_subtitles

        except Exception as e:
            logger.error(f"解析生成字幕失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return original_subtitles

    def _parse_single_episode_generated_subtitles(self, response: str,
                                                  original_subtitles: List[Dict[str, Any]],
                                                  episode_num: int,
                                                  language: str) -> List[Dict[str, Any]]:
        """解析单集生成的字幕"""
        try:
            logger.info(f"第{episode_num}集AI响应长度: {len(response)} 字符")
            logger.debug(f"第{episode_num}集AI响应前500字符: {response[:500]}")

            # 提取编号的字幕行
            lines = response.strip().split('\n')
            subtitle_lines = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 匹配 "1. 文本" 格式
                match = re.match(r'^\d+\.\s+(.+)$', line)
                if match:
                    text = match.group(1).strip()
                    # 移除可能的占位符标记
                    if not text.startswith('[') or not text.endswith(']'):
                        subtitle_lines.append(text)
                    else:
                        logger.warning(f"第{episode_num}集：跳过占位符 '{text}'")

            logger.info(f"第{episode_num}集：提取到 {len(subtitle_lines)} 条爆款字幕文本")

            # 构建新的字幕列表
            viral_subtitles = []
            for i, original_sub in enumerate(original_subtitles):
                new_sub = original_sub.copy()

                # 使用生成的文本，如果超出范围则使用原文本
                if i < len(subtitle_lines):
                    new_sub["text"] = subtitle_lines[i]
                else:
                    logger.warning(f"第{episode_num}集：字幕 {i+1} 超出生成范围，使用原文本")
                    new_sub["text"] = original_sub.get("text", "")

                viral_subtitles.append(new_sub)

            logger.info(f"第{episode_num}集：成功构建 {len(viral_subtitles)} 条爆款字幕")
            return viral_subtitles

        except Exception as e:
            logger.error(f"第{episode_num}集：解析生成的字幕失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return original_subtitles

    def _parse_batch_generated_subtitles(self, response: str,
                                        all_original_subtitles: List[List[Dict[str, Any]]],
                                        language: str) -> List[List[Dict[str, Any]]]:
        """解析批量生成的字幕 - 按集分割"""
        try:
            # 添加调试日志
            logger.info(f"AI批量响应长度: {len(response)} 字符")
            logger.debug(f"AI批量响应前1000字符: {response[:1000]}")

            # 检查响应是否为空
            if not response or not response.strip():
                logger.error("AI批量响应为空，返回原始字幕")
                return all_original_subtitles

            # 按集分割响应
            if language == "zh":
                episode_pattern = r'===\s*第(\d+)集\s*==='
            else:
                episode_pattern = r'===\s*Episode\s+(\d+)\s*==='

            # 分割响应
            episodes = re.split(episode_pattern, response)

            # 过滤掉空字符串和集数标记
            episode_contents = []
            for i in range(1, len(episodes), 2):
                if i + 1 < len(episodes):
                    episode_num = int(episodes[i])
                    episode_content = episodes[i + 1].strip()
                    episode_contents.append((episode_num, episode_content))

            logger.info(f"解析到 {len(episode_contents)} 集内容")

            # 如果没有找到集数标记，尝试其他分割方式
            if not episode_contents:
                logger.warning("未找到集数标记，尝试按空行分割")
                # 按双换行符分割
                parts = response.split('\n\n')
                episode_contents = [(i + 1, part.strip()) for i, part in enumerate(parts) if part.strip()]
                logger.info(f"按空行分割后得到 {len(episode_contents)} 个部分")

            # 解析每一集的字幕
            viral_subtitles_list = []
            for episode_num, episode_content in episode_contents:
                if episode_num - 1 < len(all_original_subtitles):
                    original_subtitles = all_original_subtitles[episode_num - 1]

                    # 按行分割
                    lines = [line.strip() for line in episode_content.split('\n') if line.strip()]
                    logger.info(f"第{episode_num}集：解析到 {len(lines)} 行非空内容")

                    # 提取编号的字幕行
                    subtitle_lines = []
                    for line in lines:
                        # 匹配 "1. 文本" 格式
                        if re.match(r'^\d+\.\s+', line):
                            text = re.sub(r'^\d+\.\s+', '', line)
                            subtitle_lines.append(text)

                    # 如果没有找到编号格式，直接使用所有行
                    if not subtitle_lines:
                        logger.warning(f"第{episode_num}集：未找到编号格式，使用所有 {len(lines)} 行")
                        subtitle_lines = lines

                    logger.info(f"第{episode_num}集：提取到 {len(subtitle_lines)} 条字幕文本")

                    # 构建新的字幕列表
                    viral_subtitles = []
                    for i, original_sub in enumerate(original_subtitles):
                        new_sub = original_sub.copy()

                        # 使用生成的文本，如果超出范围则使用原文本
                        if i < len(subtitle_lines):
                            new_sub["text"] = subtitle_lines[i]
                        else:
                            logger.warning(f"第{episode_num}集：字幕 {i+1} 超出生成范围，使用原文本")
                            new_sub["text"] = original_sub.get("text", "")

                        viral_subtitles.append(new_sub)

                    logger.info(f"第{episode_num}集：成功构建 {len(viral_subtitles)} 条爆款字幕")
                    viral_subtitles_list.append(viral_subtitles)
                else:
                    logger.warning(f"第{episode_num}集：超出原始字幕范围，使用原始字幕")
                    viral_subtitles_list.append(all_original_subtitles[episode_num - 1])

            # 如果解析的集数不够，补充原始字幕
            while len(viral_subtitles_list) < len(all_original_subtitles):
                missing_idx = len(viral_subtitles_list)
                logger.warning(f"第{missing_idx + 1}集：未生成，使用原始字幕")
                viral_subtitles_list.append(all_original_subtitles[missing_idx])

            logger.info(f"批量解析完成，共 {len(viral_subtitles_list)} 集")
            return viral_subtitles_list

        except Exception as e:
            logger.error(f"批量解析生成字幕失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return all_original_subtitles

    def _parse_mixed_cut_generated_subtitles(self, response: str,
                                            all_original_subtitles: List[List[Dict[str, Any]]],
                                            language: str) -> List[Dict[str, Any]]:
        """解析混剪生成的字幕 - 解析SRT格式"""
        try:
            logger.info(f"AI混剪响应长度: {len(response)} 字符")
            logger.debug(f"AI混剪响应前1000字符: {response[:1000]}")

            # 检查响应是否为空
            if not response or not response.strip():
                logger.error("AI混剪响应为空，返回第一集原始字幕")
                return all_original_subtitles[0] if all_original_subtitles else []

            # 解析SRT格式
            viral_subtitles = []

            # 按空行分割SRT块
            blocks = response.strip().split('\n\n')

            for block in blocks:
                if not block.strip():
                    continue

                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue

                try:
                    # 第1行：序号
                    index = int(lines[0].strip())

                    # 第2行：时间轴
                    time_line = lines[1].strip()
                    time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
                    if not time_match:
                        logger.warning(f"无法解析时间轴: {time_line}")
                        continue

                    start_time = time_match.group(1)
                    end_time = time_match.group(2)

                    # 第3行及以后：字幕文本
                    text = '\n'.join(lines[2:]).strip()

                    # 跳过占位符
                    if text.startswith('[') and text.endswith(']'):
                        logger.warning(f"跳过占位符: {text}")
                        continue

                    # 构建字幕对象
                    subtitle = {
                        "index": index,
                        "start": start_time,
                        "end": end_time,
                        "text": text
                    }

                    viral_subtitles.append(subtitle)

                except (ValueError, IndexError) as e:
                    logger.warning(f"解析SRT块失败: {block[:100]}... 错误: {e}")
                    continue

            logger.info(f"成功解析 {len(viral_subtitles)} 条混剪爆款字幕")

            # 如果解析失败，返回第一集原始字幕
            if not viral_subtitles:
                logger.error("未能解析任何字幕，返回第一集原始字幕")
                return all_original_subtitles[0] if all_original_subtitles else []

            return viral_subtitles

        except Exception as e:
            logger.error(f"解析混剪字幕失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return all_original_subtitles[0] if all_original_subtitles else []

    def _parse_key_dialogues(self, response: str,
                            original_subtitles: List[Dict[str, Any]],
                            episode_num: int,
                            language: str) -> List[Dict[str, Any]]:
        """解析关键对话 - 提取AI选择的关键对话"""
        try:
            logger.info(f"第{episode_num}集：AI响应长度: {len(response)} 字符")
            logger.debug(f"第{episode_num}集：AI响应前500字符: {response[:500]}")

            # 检查响应是否为空
            if not response or not response.strip():
                logger.error(f"第{episode_num}集：AI响应为空，返回所有原始字幕")
                return original_subtitles

            # 按行分割
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            logger.info(f"第{episode_num}集：解析到 {len(lines)} 行非空内容")

            # 🔧 优化1：支持新的逗号分隔格式（例如"1,3,4,10,15,20"）
            key_indices = []

            # 方法1：尝试解析逗号分隔的序号
            for line in lines:
                # 检查是否包含逗号分隔的数字
                if ',' in line:
                    # 提取所有数字
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        key_indices.extend([int(n) for n in numbers])
                        logger.info(f"第{episode_num}集：从逗号分隔格式中提取到 {len(numbers)} 个序号")
                        break  # 找到逗号分隔格式后就停止

            # 方法2：如果没有找到逗号分隔格式，尝试解析 "1. 文本" 格式
            if not key_indices:
                for line in lines:
                    # 匹配 "1. 文本" 格式
                    match = re.match(r'^(\d+)\.\s+', line)
                    if match:
                        index = int(match.group(1))
                        key_indices.append(index)

            logger.info(f"第{episode_num}集：提取到 {len(key_indices)} 个关键对话序号")

            # 🔧 修复：去除重复的序号
            key_indices_unique = list(dict.fromkeys(key_indices))  # 保持顺序的去重
            if len(key_indices_unique) < len(key_indices):
                logger.warning(f"第{episode_num}集：发现 {len(key_indices) - len(key_indices_unique)} 个重复序号，已去重")
                logger.debug(f"第{episode_num}集：原始序号: {key_indices}")
                logger.debug(f"第{episode_num}集：去重后序号: {key_indices_unique}")

            # 根据序号提取原始字幕
            key_dialogues = []
            for index in key_indices_unique:
                # 序号从1开始，列表索引从0开始
                if 0 < index <= len(original_subtitles):
                    key_dialogues.append(original_subtitles[index - 1])
                else:
                    logger.warning(f"第{episode_num}集：序号 {index} 超出范围，跳过")

            logger.info(f"第{episode_num}集：成功提取 {len(key_dialogues)} 条关键对话")

            # 如果没有提取到任何关键对话，返回所有原始字幕（保持原有兜底逻辑）
            if not key_dialogues:
                logger.warning(f"第{episode_num}集：未提取到任何关键对话，返回所有原始字幕")
                return original_subtitles

            # 🔒 强化约束：当AI选择过少时，按保留比例的最小值进行补全，避免总时长过短
            try:
                total_count = len(original_subtitles)
                # 读取期望保留比例（优先ENV，其次YAML配置，最后默认值）
                retain_ratio = 0.6
                env_ratio = os.getenv("VACL_DIALOGUE_RETAINED_PCT")
                if env_ratio:
                    retain_ratio = float(env_ratio)
                try:
                    from src.utils.file_utils import safe_read_yaml
                    ncfg = safe_read_yaml("configs/narrative_config.yaml", {}) or {}
                    kd = (ncfg.get("key_dialogue_extraction") or {})
                    cfg_ratio = kd.get("retention_ratio")
                    if cfg_ratio is not None:
                        retain_ratio = float(cfg_ratio)
                except Exception:
                    pass
                # 合理边界（与提示词对齐）
                retain_ratio = max(0.3, min(0.8, retain_ratio))
                min_count = int(total_count * max(0.1, retain_ratio - 0.1))
                min_count = max(1, min(min_count, total_count))
            except Exception as _e:
                logger.warning(f"第{episode_num}集：计算最小保留数量失败，使用默认规则: {_e}")
                total_count = len(original_subtitles)
                min_count = max(1, int(total_count * 0.5))

            if len(key_dialogues) < min_count:
                need = min_count - len(key_dialogues)
                # 从未被选中的原始字幕中，按启发式打分补充（偏好文本更长/含情绪标点，过滤超短）
                try:
                    def _score(sub):
                        txt = (sub.get('text') or '').strip()
                        L = len(txt)
                        score = L
                        if any(ch in txt for ch in ['！','!','？','?','…']):
                            score += 5
                        if L <= 3:
                            score -= 100
                        return score

                    candidates = [sub for sub in original_subtitles if sub not in key_dialogues]
                    candidates_sorted = sorted(candidates, key=_score, reverse=True)
                    fill = candidates_sorted[:max(0, need)]
                    key_dialogues.extend(fill)
                    logger.warning(f"第{episode_num}集：AI仅选{len(key_dialogues)-len(fill)}条，按规则补充{len(fill)}条 → 最终{len(key_dialogues)}/{total_count}")
                except Exception as _e2:
                    logger.warning(f"第{episode_num}集：补充分段失败，回退原有选择: {_e2}")

            # 🔧 新增：应用叙事连贯性优化
            try:
                key_indices_enhanced = self._ensure_narrative_continuity(key_indices_unique, original_subtitles)
                if len(key_indices_enhanced) > len(key_indices_unique):
                    # 根据增强后的序号重新提取对话
                    key_dialogues = []
                    for index in key_indices_enhanced:
                        if 0 < index <= len(original_subtitles):
                            key_dialogues.append(original_subtitles[index - 1])
                    logger.info(f"第{episode_num}集：叙事连贯性优化后 {len(key_dialogues)} 条关键对话")
            except Exception as _e3:
                logger.warning(f"第{episode_num}集：叙事连贯性优化失败: {_e3}")

            return key_dialogues

        except Exception as e:
            logger.error(f"第{episode_num}集：解析关键对话失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return original_subtitles

    def _ensure_narrative_continuity(self, selected_indices: List[int], episode_subs: List[Dict]) -> List[int]:
        """
        确保叙事连贯性：自动补充缺失的上下文对话（与云端模式保持一致）
        
        核心策略：
        1. 场景完整性：确保每个场景的开头和结尾都被包含
        2. 因果关系：确保"起因"和"结果"成对出现
        3. 对话完整性：确保问答、反应等对话链完整
        4. 避免切断连贯内容：不在连续对话中间切断
        
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
        
        # ========== 词汇库定义 ==========
        # 结果/反应词汇（需要前文铺垫）
        result_words = [
            '所以', '因此', '于是', '结果', '怪不得', '原来', '难怪', '这就是', '这才', '终于',
            '果然', '看来', '这下', '这回', '这次', '总算', '到底', '毕竟', '既然如此',
            '那就', '那么', '这样的话', '也就是说', '换句话说', '意思是'
        ]
        # 起因词汇
        cause_words = [
            '因为', '由于', '既然', '要是', '如果', '假如', '本来', '原本',
            '之所以', '正是因为', '就是因为', '都是因为', '全是因为', '皆因',
            '起因是', '原因是', '缘由是', '根源在于'
        ]
        # 转折词汇（需要前文对比）
        contrast_words = [
            '但是', '可是', '然而', '不过', '却', '反而', '相反', '没想到', '谁知', '竟然',
            '岂料', '哪知', '殊不知', '万万没想到', '出乎意料', '意想不到',
            '话虽如此', '虽然', '尽管', '即便', '就算'
        ]
        # 递进词汇（需要前文基础）
        progression_words = [
            '而且', '并且', '同时', '另外', '还有', '更', '甚至', '不仅', '除了',
            '不但', '不光', '何况', '况且', '再说', '再者', '此外', '加上',
            '更何况', '更重要的是', '更关键的是'
        ]
        # 问句词汇
        question_words = ['为什么', '怎么', '什么', '哪里', '哪个', '谁', '几', '多少', '吗', '呢', '？', '?']
        # 回应词汇
        response_words = [
            '是的', '对', '没错', '好的', '知道', '明白', '当然', '不是', '不对', '不行', '可以', '行',
            '嗯', '啊', '哦', '好', '是', '对啊', '没错啊', '就是', '正是', '确实'
        ]
        # 指代词汇
        reference_words = [
            '这', '那', '他', '她', '它', '这个', '那个', '这样', '那样', '如此', '这么', '那么',
            '这件事', '那件事', '这种', '那种', '这些', '那些'
        ]
        # 情感反应词汇
        emotion_words = [
            '天哪', '什么', '不会吧', '真的吗', '怎么会', '太好了', '糟了', '完了', '救命', '不要',
            '我的天', '天啊', '啊', '哇', '呀', '哎呀', '不可能', '怎么可能'
        ]
        # 承接词汇
        continuation_words = [
            '然后', '接着', '随后', '之后', '后来', '紧接着', '接下来',
            '于是乎', '就这样', '就在这时', '正在这时', '这时候', '那时候'
        ]
        
        # ========== 策略1：因果关系补充 ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            # 如果包含"结果"类词汇，向前查找"起因"
            if any(word in text for word in result_words):
                for prev_idx in range(max(1, idx - 4), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
            
            # 如果包含转折词，确保前文被选中
            if any(word in text for word in contrast_words):
                for prev_idx in range(max(1, idx - 3), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
            
            # 如果包含承接词，确保前文被选中
            if any(word in text for word in continuation_words):
                for prev_idx in range(max(1, idx - 2), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
        
        # ========== 策略2：问答完整性 ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            # 如果是问句，确保后面有回答
            if any(word in text for word in question_words):
                for next_idx in range(idx + 1, min(len(episode_subs) + 1, idx + 3)):
                    if next_idx <= len(episode_subs):
                        next_text = episode_subs[next_idx - 1].get("text", "")
                        if any(word in next_text for word in response_words) or not any(word in next_text for word in question_words):
                            enhanced_indices.add(next_idx)
                            break
            
            # 如果是回应词开头，确保前面的问题被选中
            if any(text.startswith(word) for word in response_words):
                for prev_idx in range(max(1, idx - 2), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
        
        # ========== 策略3：指代消解 ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            if any(text.startswith(word) for word in reference_words):
                for prev_idx in range(idx - 1, max(0, idx - 4), -1):
                    if prev_idx >= 1 and prev_idx <= len(episode_subs):
                        prev_text = episode_subs[prev_idx - 1].get("text", "")
                        enhanced_indices.add(prev_idx)
                        if not any(prev_text.startswith(word) for word in reference_words):
                            break
        
        # ========== 策略4：情感反应补充 ==========
        for idx in list(enhanced_indices):
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            if any(word in text for word in emotion_words):
                for prev_idx in range(max(1, idx - 2), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
        
        # ========== 策略5：填补小间隙（避免切断连贯内容） ==========
        sorted_enhanced = sorted(enhanced_indices)
        for i in range(len(sorted_enhanced) - 1):
            current_idx = sorted_enhanced[i]
            next_idx = sorted_enhanced[i + 1]
            gap = next_idx - current_idx
            
            # 如果间隙是2-4条，检查是否应该补充
            if 2 <= gap <= 4:
                for fill_idx in range(current_idx + 1, next_idx):
                    if fill_idx <= len(episode_subs):
                        fill_text = episode_subs[fill_idx - 1].get("text", "")
                        all_keywords = result_words + cause_words + contrast_words + progression_words + response_words + continuation_words
                        if any(word in fill_text for word in all_keywords):
                            enhanced_indices.add(fill_idx)
                        elif gap <= 3:
                            enhanced_indices.add(fill_idx)
                        elif len(fill_text) > 8:
                            enhanced_indices.add(fill_idx)
        
        # ========== 策略6：确保开头不是"半句话" ==========
        final_indices = sorted(enhanced_indices)
        incomplete_starters = [
            '但', '可', '然', '不过', '而', '所以', '因此', '于是', 
            '这', '那', '他', '她', '它', '还', '也', '又', '再',
            '然后', '接着', '随后', '之后', '后来', '就', '便', '才'
        ]
        for idx in final_indices:
            if idx > len(episode_subs):
                continue
            text = episode_subs[idx - 1].get("text", "")
            
            if text and any(text.startswith(word) for word in incomplete_starters):
                for prev_idx in range(max(1, idx - 2), idx):
                    if prev_idx not in enhanced_indices and prev_idx <= len(episode_subs):
                        enhanced_indices.add(prev_idx)
        
        result = sorted(enhanced_indices)
        
        # 记录补充情况
        added_count = len(result) - len(sorted_indices)
        if added_count > 0:
            logger.info(f"叙事连贯性优化：补充了 {added_count} 条上下文对话（原{len(sorted_indices)}条 -> 现{len(result)}条）")
        
        return result

    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（简单的字符级相似度）"""
        try:
            if not text1 or not text2:
                return 0.0

            # 移除空格和标点符号
            import string
            text1_clean = ''.join(c for c in text1 if c not in string.punctuation and c not in ' \n\t')
            text2_clean = ''.join(c for c in text2 if c not in string.punctuation and c not in ' \n\t')

            if not text1_clean or not text2_clean:
                return 0.0

            # 计算最长公共子序列长度
            len1, len2 = len(text1_clean), len(text2_clean)
            dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

            for i in range(1, len1 + 1):
                for j in range(1, len2 + 1):
                    if text1_clean[i-1] == text2_clean[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])

            lcs_length = dp[len1][len2]
            similarity = lcs_length / max(len1, len2)

            return similarity
        except Exception as e:
            logger.warning(f"计算文本相似度失败: {e}")
            return 0.0

    def cleanup(self):
        """清理资源"""
        try:
            # 卸载所有模型
            for language, _model in list(self.models.items()):
                try:
                    if hasattr(_model, "close"):
                        _model.close()
                except Exception:
                    pass
                del self.models[language]
                if language in self.tokenizers:
                    del self.tokenizers[language]

            self.models.clear()
            self.tokenizers.clear()
            self.current_model = None
            self.current_language = None

            # 强制垃圾回收
            gc.collect()
            try:
                import torch as _torch
                if hasattr(_torch, "cuda") and _torch.cuda.is_available():
                    _torch.cuda.empty_cache()
            except Exception as _e:
                logger.debug(f"跳过CUDA缓存清理: {_e}")

            logger.info("AI引擎资源清理完成")

        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

    def _clean_ai_response(self, response: str) -> str:
        """
        智能清理AI响应，移除Python代码、markdown代码块、解释文字等
        只保留SRT格式的内容
        """
        try:
            lines = response.split('\n')
            cleaned_lines = []
            in_code_block = False
            skip_line = False

            for line in lines:
                # 检测markdown代码块
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue

                # 跳过代码块内的内容
                if in_code_block:
                    continue

                # 跳过Python代码行
                if any(keyword in line for keyword in ['def ', 'import ', 'class ', 'return ', 'if __name__', '# ', 'print(']):
                    continue

                # 跳过解释性文字（中文）
                if any(keyword in line for keyword in ['【', '】', '好的', '现在', '请', '以下是', '根据', '这是', '混剪任务']):
                    continue

                # 跳过解释性文字（英文）
                if any(keyword in line for keyword in ['【', '】', 'OK', 'Now', 'Please', 'Here is', 'According to', 'This is']):
                    continue

                # 保留SRT格式的行（序号、时间轴、文本）
                # 序号行：纯数字
                if line.strip().isdigit():
                    cleaned_lines.append(line)
                    continue

                # 时间轴行：包含 -->
                if '-->' in line:
                    cleaned_lines.append(line)
                    continue

                # 文本行：非空且不是特殊字符开头
                if line.strip() and not line.strip().startswith(('=', '-', '*', '#', '/', '\\')):
                    # 进一步过滤：不包含代码特征
                    if not any(char in line for char in ['{', '}', '(', ')', '=', ';']) or len(line.strip()) < 50:
                        cleaned_lines.append(line)

            cleaned_response = '\n'.join(cleaned_lines)
            logger.debug(f"清理前: {len(response)} 字符, 清理后: {len(cleaned_response)} 字符")

            return cleaned_response

        except Exception as e:
            logger.error(f"清理AI响应失败: {str(e)}")
            return response  # 如果清理失败，返回原始响应

    def _parse_batch_mixed_cut_subtitles(self, response: str, batch: List[Dict[str, Any]],
                                         batch_idx: int, language: str) -> List[Dict[str, Any]]:
        """解析分批混剪字幕"""
        try:
            logger.info(f"第{batch_idx + 1}批AI响应长度: {len(response)} 字符")
            logger.debug(f"第{batch_idx + 1}批AI响应前500字符: {response[:500]}")

            # 检查响应是否为空
            if not response or not response.strip():
                logger.error(f"第{batch_idx + 1}批AI响应为空，使用原始对话")
                return batch

            # 🔧 新增：智能清理响应内容（移除Python代码、markdown等）
            cleaned_response = self._clean_ai_response(response)
            if not cleaned_response:
                logger.error(f"第{batch_idx + 1}批：清理后响应为空，使用原始对话")
                return batch

            logger.info(f"第{batch_idx + 1}批清理后响应长度: {len(cleaned_response)} 字符")

            # 解析SRT格式
            viral_subtitles = []

            # 按空行分割SRT块
            blocks = cleaned_response.strip().split('\n\n')

            for block in blocks:
                if not block.strip():
                    continue

                try:
                    lines = block.strip().split('\n')
                    if len(lines) < 3:
                        continue

                    # 解析序号（容错：允许'1.'、'1、'等）
                    m_index = re.match(r'^\s*(\d+)', lines[0])
                    if not m_index:
                        logger.warning(f"第{batch_idx + 1}批：序号行无效: {lines[0]}")
                        continue
                    index = int(m_index.group(1))

                    # 解析时间轴
                    time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                    if not time_match:
                        logger.warning(f"第{batch_idx + 1}批：解析时间轴失败: {lines[1]}")
                        continue

                    start_time = time_match.group(1)
                    end_time = time_match.group(2)

                    # 解析文本
                    text = '\n'.join(lines[2:]).strip()

                    # 跳过占位符
                    if '[' in text and ']' in text:
                        logger.warning(f"第{batch_idx + 1}批：跳过占位符: {text}")
                        continue

                    # 尝试匹配原始字幕，保留原始时间码信息
                    matched_original = None
                    for original_dialogue in batch:
                        # 通过文本相似度匹配（简单的包含关系）
                        original_text = original_dialogue.get('text', '')
                        if original_text and (text in original_text or original_text in text or
                                            self._text_similarity(text, original_text) > 0.5):
                            matched_original = original_dialogue
                            break

                    # 构建字幕对象
                    subtitle_obj = {
                        'index': index,
                        'start': start_time,
                        'end': end_time,
                        'text': text
                    }

                    # 如果匹配到原始字幕，保留原始信息
                    if matched_original:
                        subtitle_obj['original_episode'] = matched_original.get('original_episode', 0)
                        subtitle_obj['original_index'] = matched_original.get('original_index', 0)
                        subtitle_obj['original_start'] = matched_original.get('original_start', '')
                        subtitle_obj['original_end'] = matched_original.get('original_end', '')

                        # 🔧 新增：验证原始时间码不为空
                        if not subtitle_obj['original_start'] or not subtitle_obj['original_end']:
                            logger.warning(f"第{batch_idx + 1}批：匹配到的原始字幕时间码为空，matched_original={matched_original}")
                        else:
                            logger.debug(f"匹配到原始字幕: 第{subtitle_obj['original_episode']}集 #{subtitle_obj['original_index']}")

                    viral_subtitles.append(subtitle_obj)

                except Exception as e:
                    logger.warning(f"第{batch_idx + 1}批：解析SRT块失败: {block[:100]}... 错误: {str(e)}")
                    continue

            logger.info(f"第{batch_idx + 1}批：成功解析 {len(viral_subtitles)} 条混剪字幕")

            # 🔧 修复：如果AI解析失败，使用规则引擎生成正确的SRT格式
            if not viral_subtitles:
                logger.warning(f"第{batch_idx + 1}批：AI解析失败，使用规则引擎生成SRT格式")
                viral_subtitles = self._generate_srt_from_dialogues(batch, batch_idx)
                logger.info(f"第{batch_idx + 1}批：规则引擎生成 {len(viral_subtitles)} 条字幕")
                return viral_subtitles

            return viral_subtitles

        except Exception as e:
            logger.error(f"第{batch_idx + 1}批：解析混剪字幕失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return batch

    def _generate_srt_from_dialogues(self, dialogues: List[Dict[str, Any]], batch_idx: int) -> List[Dict[str, Any]]:
        """
        使用规则引擎从对话列表生成正确的SRT格式字幕

        当AI解析失败时，使用此方法作为回退方案，确保100%成功率

        Args:
            dialogues: 对话列表
            batch_idx: 批次索引

        Returns:
            SRT格式的字幕列表
        """
        try:
            viral_subtitles = []

            for i, dialogue in enumerate(dialogues):
                # 提取文本
                text = dialogue.get('text', '').strip()
                if not text:
                    continue

                # 生成占位符时间轴（后续会重新生成）
                start_time = '00:00:00,000'
                end_time = '00:00:01,500'

                # 构建字幕对象
                subtitle_obj = {
                    'index': i + 1,
                    'start': start_time,
                    'end': end_time,
                    'text': text,
                    'original_episode': dialogue.get('original_episode', 0),
                    'original_index': dialogue.get('original_index', 0),
                    'original_start': dialogue.get('original_start', ''),
                    'original_end': dialogue.get('original_end', '')
                }

                # 验证原始时间码
                if not subtitle_obj['original_start'] or not subtitle_obj['original_end']:
                    logger.warning(f"第{batch_idx + 1}批：对话{i+1}缺少原始时间码")

                viral_subtitles.append(subtitle_obj)

            logger.info(f"第{batch_idx + 1}批：规则引擎成功生成 {len(viral_subtitles)} 条字幕")
            return viral_subtitles

        except Exception as e:
            logger.error(f"第{batch_idx + 1}批：规则引擎生成失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []


    def _arrange_for_montage(self, items: List[Dict[str, Any]], avoid_aba: bool = True, ngram: int = 3) -> List[Dict[str, Any]]:
        """对已产出的字幕条目做蒙太奇重排：
        - 最小化相邻文本相似度（字符n-gram Jaccard）
        - 避免 A→B→A 的回钩（可选）
        - 轻微惩罚同集连续，增加跨集对比感
        返回同结构的新顺序列表。
        """
        try:
            import math
            def _norm_text(s: str) -> str:
                if not s:
                    return ""
                # 去除 #ORIGINAL 元信息行，统一大小写，压缩空白
                s2 = re.sub(r"(?im)^\s*#ORIGINAL:.*$", "", s)
                s2 = s2.strip().lower()
                s2 = re.sub(r"\s+", " ", s2)
                return s2

            def _grams(s: str, n: int = ngram) -> set:
                s2 = _norm_text(s)
                if not s2:
                    return set()
                if len(s2) < n:
                    return {s2}
                return {s2[i:i + n] for i in range(len(s2) - n + 1)}

            def _jacc(a: set, b: set) -> float:
                if not a and not b:
                    return 0.0
                inter = len(a & b)
                uni = len(a | b)
                return (inter / uni) if uni else 0.0

            def _impact(t: str) -> int:
                t = t or ""
                return min(60, len(t)) + 2 * (t.count('!') + t.count('！') + t.count('?') + t.count('？')) + t.count('…')

            N = len(items)
            if N <= 2:
                return items

            texts = [str(it.get('text', '') or '') for it in items]
            grams = [_grams(t) for t in texts]
            episodes = [it.get('original_episode') for it in items]

            # 选择一个“冲击力”较强的种子作为起点
            seed_idx = max(range(N), key=lambda i: _impact(texts[i]))
            selected = [seed_idx]
            remaining = set(range(N))
            remaining.remove(seed_idx)

            while remaining:
                last = selected[-1]
                prev = selected[-2] if len(selected) >= 2 else None
                best_cost = None
                best_idx = None
                for i in list(remaining):
                    sim = _jacc(grams[last], grams[i])
                    same_pen = 1.0 if (episodes[i] is not None and episodes[last] is not None and episodes[i] == episodes[last]) else 0.0
                    aba_pen = 0.0
                    if avoid_aba and prev is not None:
                        pe, le, ce = episodes[prev], episodes[last], episodes[i]
                        if pe is not None and le is not None and ce is not None:
                            if pe != le and ce == pe:
                                aba_pen = 1.0
                    cost = sim + 0.8 * aba_pen + 0.2 * same_pen
                    if best_cost is None or cost < best_cost:
                        best_cost, best_idx = cost, i
                selected.append(best_idx)
                remaining.remove(best_idx)

            reordered = [items[i] for i in selected]
            return reordered
        except Exception as e:
            logger.warning(f"_arrange_for_montage 失败，返回原顺序: {e}")
            return items


    def _arrange_chronological_fast(self, items: List[Dict[str, Any]], language: str = 'zh') -> List[Dict[str, Any]]:
        """
        按原集数与时间顺序重排，并做轻量“去冗快剪”。
        - 分组：original_episode 升序；组内：original_index 升序（或 original_start 时间码）
        - 评分：爆点标点(?! )、冲突关键词、合适长度；剔除明显口水/纯感叹
        - 保留比例：每集按 CHRONO_RETAIN（默认0.55，范围0.3-0.9）截断；保持原时间顺序
        - 去重：同一集内与上一保留条目过于相似（Jaccard>0.7）则跳过
        """
        try:
            import re
            def _norm_text(s: str) -> str:
                if not s:
                    return ""
                s2 = re.sub(r"(?im)^\s*#ORIGINAL:.*$", "", s)  # 去元信息
                s2 = re.sub(r"\s+", "", s2)
                return s2

            def _grams(s: str, n: int = 3) -> set:
                s2 = _norm_text(s)
                if not s2:
                    return set()
                if len(s2) < n:
                    return {s2}
                return {s2[i:i+n] for i in range(len(s2)-n+1)}

            def _jacc(a: set, b: set) -> float:
                if not a and not b:
                    return 0.0
                inter = len(a & b)
                uni = len(a | b)
                return (inter/uni) if uni else 0.0

            filler_words = {
                '哈','哈哈','哈哈哈','呵','呵呵','啊','啊啊','哦','喔','嗯','呃','额','哎','哎呀','唉','喂','咦','嗨','嘿',
                '好的','好吧','知道了','行','好','哦哦','嗯嗯','不是吧','不会吧'
            }
            conflict_words = [
                '杀','打','骗','告','报警','抓','证据','录音','监控','曝光','道歉','公司','合同','钱','债','借','还',
                '孩子','怀孕','流产','离婚','结婚','出轨','背叛','复仇','死亡','救','医院','法庭','案件','记者','直播',
                '选举','竞选','权力','威胁','勒索','危机','真相','谎言','阴谋'
            ]

            def _is_filler(t: str) -> bool:
                s = _norm_text(t)
                if not s:
                    return True
                # 纯标点或极短
                if len(s) <= 2:
                    return True
                if re.fullmatch(r"[\W_·、，,。.!！?？…~\-：:；;（）()\[\]\s]+", s):
                    return True
                # 重复字符（如 哈哈哈、啊啊啊）
                if len(set(s)) <= 2 and any(ch in '哈呵啊哦嗯呃额' for ch in set(s)):
                    return True
                # 明显口水词
                if s in filler_words:
                    return True
                return False

            def _score(t: str) -> float:
                s = _norm_text(t)
                if _is_filler(s):
                    return -1.0
                score = 0.0
                # 标点情绪
                bang = t.count('!') + t.count('！')
                q = t.count('?') + t.count('？')
                score += min(0.8, 0.4*bang + 0.4*q)
                # 关键词
                kw = sum(1 for w in conflict_words if w in t)
                if kw >= 2:
                    score += 1.0
                elif kw == 1:
                    score += 0.5
                # 长度
                L = len(s)
                if 6 <= L <= 36:
                    score += 0.3
                elif 37 <= L <= 56:
                    score += 0.15
                elif L < 4:
                    score -= 0.5
                elif L > 70:
                    score -= 0.4
                return score

            def _parse_ms(ts: str):
                m = re.match(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$", str(ts or '').strip())
                if not m:
                    return None
                hh, mm, ss, ms = map(int, m.groups())
                return ((hh*60 + mm)*60 + ss)*1000 + ms

            # 读取保留比例
            import os
            try:
                r = float(os.getenv('CHRONO_RETAIN', '0.7'))
                retain_ratio = max(0.3, min(0.9, r))
            except Exception:
                retain_ratio = 0.55

            logger.info(f"[Chrono] 目标每集保留比例: {retain_ratio:.2f}")

            # 分组
            groups: Dict[int, List[Dict[str, Any]]] = {}
            for it in items:
                ep = it.get('original_episode') or it.get('episode') or 0
                try:
                    ep = int(ep)
                except Exception:
                    ep = 0
                groups.setdefault(ep, []).append(it)

            ordered: List[Dict[str, Any]] = []
            for ep in sorted(groups.keys()):
                g = groups[ep]
                def _key(it):
                    idx = it.get('original_index')
                    if isinstance(idx, int):
                        return (0, idx)
                    tms = _parse_ms(it.get('original_start', ''))
                    if tms is not None:
                        return (1, tms)
                    return (2, 0)
                g_sorted = sorted(g, key=_key)

                scored = [(i, _score(str(it.get('text', '') or '')), it) for i, it in enumerate(g_sorted)]
                # 先过滤明显口水
                base = [(i, sc, it) for (i, sc, it) in scored if sc >= 0]
                total = len(g_sorted)
                # 动态保留比例：以全局retain_ratio为基线，结合内容强度在[0.65,0.80]内微调
                base_ratio = retain_ratio if isinstance(retain_ratio, (float, int)) else 0.7
                texts = [str(it.get('text', '') or '') for it in g_sorted]
                valid = [t for t in texts if not _is_filler(t)]
                lens = [len(_norm_text(t)) for t in valid] or [0]
                avg_len = (sum(lens) / max(1, len(lens)))
                def _pun(x: str) -> int: return x.count('!') + x.count('！') + x.count('?') + x.count('？')
                p_int = (sum(1 for t in valid if _pun(t) > 0) / max(1, len(valid)))
                c_cnt = 0
                for _t in valid:
                    if any(w in _t for w in conflict_words):
                        c_cnt += 1
                c_int = c_cnt / max(1, len(valid))
                local_ratio = base_ratio
                if avg_len < 10: local_ratio += 0.05
                if c_int >= 0.35: local_ratio += 0.03
                if p_int >= 0.5: local_ratio += 0.02
                if avg_len > 28: local_ratio -= 0.03
                local_ratio = max(0.65, min(0.80, local_ratio))
                logger.info(f"[Chrono] Episode {ep:02d} 保留比例: {local_ratio:.2f} (total={total})")
                target = max(1, min(len(base) if base else total, int(round(local_ratio * total))))
                # 选分高的前 target 个，但按原时间顺序输出
                top = sorted(base if base else [(i, sc, it) for (i, sc, it) in scored], key=lambda x: x[1], reverse=True)[:target]
                sel_idx = set(i for i, sc, it in top)
                selected = [it for i, it in enumerate(g_sorted) if i in sel_idx]

                # 集内近重复去重（保持节奏干净）
                final_ep: List[Dict[str, Any]] = []
                last_g = None
                for it in selected:
                    g3 = _grams(str(it.get('text', '') or ''))
                    if last_g is not None and _jacc(g3, last_g) > 0.7:
                        continue
                    final_ep.append(it)
                    last_g = g3

                # 保底：至少保留40%
                min_cnt = max(1, int(0.4 * total))
                if len(final_ep) < min_cnt:
                    for it in g_sorted:
                        if it in final_ep:
                            continue
                        final_ep.append(it)
                        if len(final_ep) >= min_cnt:
                            break

                ordered.extend(final_ep)

            return ordered
        except Exception as e:
            logger.warning(f"_arrange_chronological_fast 失败，返回原顺序: {e}")
            return items




    def _stitch_incomplete_sentences(self, items: List[Dict[str, Any]], language: str = 'zh') -> List[Dict[str, Any]]:
        """
        邻接拼接：针对“上一句没说完就切”的根因，在重建时间轴之前，先按来源（同集、近邻）将未完句拼成一个完整语义单元。
        规则（保守）：
        - 同一 original_episode；
        - 当前字幕末尾不是句末标点（不把省略号 … 和 ASCII ... 当作句末）；
        - 原始时间码相邻（index 连续，或 original_start-gap ≤ 2000ms）；
        - 合并链长度 ≤ 3，合并后总字数 ≤ 140；
        合并后：
        - 文本直接相连（中文无空格，英文加空格）；
        - original_end 取链条最后一个；index 可保留起点（如有 original_index_end 可补充，但非必须）；
        """
        try:
            if not items:
                return items

            def _ends_with_sentence_punct(txt: str) -> bool:
                if not txt:
                    return False
                t = (txt or '').strip()
                if not t:
                    return False
                # 仅将真正句末标点视为“完句”
                enders = ('。', '！', '？', '.', '!', '?')
                last = t[-1]
                if last in enders:
                    return True
                # 明确排除省略与破折/顿号、逗号、中文冒号/分号
                if t.endswith('…') or t.endswith('...'):
                    return False
                if last in ('，', '、', '—', '：', '；', '」', '』'):
                    return False
                # 未闭合引号 -> 视为未完句
                if t.count('“') > t.count('”') or t.count('‘') > t.count('’'):
                    return False
                # 中文右引号作为句末，若之前无终止标点，也可视为未完句（避免误判为完句）
                return False

            import re
            def _parse_ms(ts: Optional[str]) -> Optional[int]:
                if ts is None:
                    return None
                m = re.match(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$", str(ts).strip())
                if not m:
                    return None
                hh, mm, ss, ms = map(int, m.groups())
                return ((hh * 60 + mm) * 60 + ss) * 1000 + ms

            same_lang_space = (language or 'zh').lower().startswith('en')
            gap_limit_ms = 2000
            max_chain = 3
            max_chars = 140

            res: List[Dict[str, Any]] = []
            i = 0
            merged_pairs = 0
            max_chain_len_seen = 1
            n = len(items)

            while i < n:
                cur = dict(items[i])  # 复制，避免原地修改
                chain_len = 1
                # 连续向后吸收符合条件的项
                while (i + 1) < n:
                    nxt = items[i + 1]
                    # 同集约束
                    if str(nxt.get('original_episode', '')) != str(cur.get('original_episode', '')):
                        break
                    # 仅在“当前不是完句”时才尝试拼接
                    if _ends_with_sentence_punct(str(cur.get('text', ''))):
                        break
                    # 原始时间/索引邻接性
                    ok_adjacent = False
                    try:
                        idx_cur = int(cur.get('original_index')) if cur.get('original_index') is not None else None
                        idx_nxt = int(nxt.get('original_index')) if nxt.get('original_index') is not None else None
                        if isinstance(idx_cur, int) and isinstance(idx_nxt, int) and idx_nxt == idx_cur + 1:
                            ok_adjacent = True
                    except Exception:
                        pass
                    if not ok_adjacent:
                        try:
                            e_cur = _parse_ms(cur.get('original_end'))
                            s_nxt = _parse_ms(nxt.get('original_start'))
                            if isinstance(e_cur, int) and isinstance(s_nxt, int) and (0 <= (s_nxt - e_cur) <= gap_limit_ms):
                                ok_adjacent = True
                        except Exception:
                            ok_adjacent = False
                    if not ok_adjacent:
                        break

                    # 合并上限控制
                    new_text = (str(cur.get('text', '')) or '').rstrip()
                    add_text = (str(nxt.get('text', '')) or '').lstrip()
                    combined_len = len(new_text) + len(add_text)
                    if chain_len + 1 > max_chain or combined_len > max_chars:
                        break

                    # 满足条件 → 合并
                    cur['text'] = (new_text + (' ' if same_lang_space else '') + add_text)
                    # 扩大原始时间范围
                    if nxt.get('original_end'):
                        cur['original_end'] = nxt.get('original_end')
                    # 可选：记录合并来源（便于诊断）
                    cur['stitched'] = True
                    cur['stitched_count'] = int(cur.get('stitched_count') or 1) + 1

                    # 前进，吸收 next
                    i += 1
                    chain_len += 1
                    merged_pairs += 1
                    max_chain_len_seen = max(max_chain_len_seen, chain_len)

                res.append(cur)
                i += 1

            try:
                logger.info(f"[Stitch] before={len(items)}, after={len(res)}, merged_pairs={merged_pairs}, max_chain={max_chain_len_seen}, gap_ms<={gap_limit_ms}")
            except Exception:
                pass
            return res
        except Exception as e:
            logger.warning(f"_stitch_incomplete_sentences 失败，跳过：{e}")
            return items

    def _regenerate_timeline(self, all_viral_subtitles: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """重新生成时间轴 - 从00:00:00开始，优先使用原始时间码的时长"""
        try:
            logger.info(f"开始重新生成时间轴，共 {len(all_viral_subtitles)} 条字幕")

            # 重新生成时间轴
            current_time = 0  # 毫秒
            regenerated_subtitles = []

            for i, subtitle in enumerate(all_viral_subtitles):
                text = subtitle.get('text', '')
                text_length = len(text)

                # 🔧 优先使用原始时间码的时长（精确到毫秒）
                duration = None
                try:
                    def _parse_ms_local(ts: str):
                        m = re.match(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$", str(ts or '').strip())
                        if not m:
                            return None
                        hh, mm, ss, ms = map(int, m.groups())
                        return ((hh*60 + mm)*60 + ss)*1000 + ms
                    o_start = subtitle.get('original_start')
                    o_end = subtitle.get('original_end')
                    ms_s = _parse_ms_local(o_start)
                    ms_e = _parse_ms_local(o_end)
                    if isinstance(ms_s, int) and isinstance(ms_e, int) and ms_e > ms_s:
                        # 使用原始时间码的时长，添加少量缓冲避免紧切
                        duration = ms_e - ms_s + 100  # 添加100ms缓冲
                        logger.debug(f"字幕{i+1}：使用原始时长 {duration}ms (原始: {o_start} -> {o_end})")
                except Exception as e:
                    logger.debug(f"字幕{i+1}：解析原始时间码失败: {e}")

                # 如果没有原始时间码，使用基于文本长度的估算（降级方案）
                if duration is None:
                    if text_length <= 5:
                        duration = 1800
                    elif text_length <= 10:
                        duration = 2200
                    elif text_length <= 15:
                        duration = 2700
                    else:
                        duration = 3200

                    # 语义加权：若非句末，适当延长
                    try:
                        ends_with_punct = False
                        if text:
                            last = text.strip()[-1]
                            ends_with_punct = last in ('。', '！', '？', '.', '!', '?')
                            if (text.count('“') > text.count('”')) or (text.count('‘') > text.count('’')):
                                ends_with_punct = False
                            if last in ('…', '，', '、', '—', '—'):
                                ends_with_punct = False
                        if not ends_with_punct:
                            duration += 600
                    except Exception:
                        pass
                    logger.debug(f"字幕{i+1}：使用文本长度估算时长 {duration}ms")

                # 生成时间轴
                start_time = self._format_time(current_time)
                end_time = self._format_time(current_time + duration)

                # 构建新字幕对象，保留原始时间码信息
                new_subtitle = {
                    'index': i + 1,
                    'start': start_time,
                    'end': end_time,
                    'text': text
                }

                # 保留原始字幕的映射信息（如果存在）
                if 'original_episode' in subtitle:
                    new_subtitle['original_episode'] = subtitle['original_episode']
                if 'original_index' in subtitle:
                    new_subtitle['original_index'] = subtitle['original_index']
                if 'original_start' in subtitle:
                    new_subtitle['original_start'] = subtitle['original_start']
                if 'original_end' in subtitle:
                    new_subtitle['original_end'] = subtitle['original_end']

                regenerated_subtitles.append(new_subtitle)

                current_time += duration

            logger.info(f"时间轴重新生成完成，总时长: {self._format_time(current_time)}")

            return regenerated_subtitles

        except Exception as e:
            logger.error(f"重新生成时间轴失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return all_viral_subtitles

    def _format_time(self, milliseconds: int) -> str:
        """格式化时间（毫秒 -> SRT时间格式）"""
        hours = milliseconds // 3600000
        milliseconds %= 3600000
        minutes = milliseconds // 60000
        milliseconds %= 60000
        seconds = milliseconds // 1000
        milliseconds %= 1000

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    # ==================== 病毒评分算法（从AIViralTransformer提取） ====================

    def calculate_viral_score(self, subtitle: Dict[str, Any],
                             narrative_analysis: Optional[Dict[str, Any]] = None,
                             emotion_analysis: Optional[Dict[str, Any]] = None) -> float:
        """
        计算字幕的病毒传播潜力评分

        Args:
            subtitle: 字幕片段
            narrative_analysis: 叙事分析结果（可选）
            emotion_analysis: 情感分析结果（可选）

        Returns:
            float: 病毒传播评分 (0.0-1.0)
        """
        try:
            text = subtitle.get("text", "")
            if not text.strip():
                return 0.0

            score = 0.0

            # 情感强度权重 (40%)
            emotion_score = self._calculate_emotion_intensity(text)
            score += emotion_score * 0.4

            # 关键词匹配权重 (30%)
            keyword_score = self._calculate_keyword_score(text)
            score += keyword_score * 0.3

            # 叙事位置权重 (20%)
            if narrative_analysis:
                narrative_score = self._calculate_narrative_position_score(subtitle, narrative_analysis)
                score += narrative_score * 0.2
            else:
                score += 0.5 * 0.2  # 默认中等评分

            # 长度适宜性权重 (10%)
            length_score = self._calculate_length_score(text)
            score += length_score * 0.1

            return min(1.0, max(0.0, score))

        except Exception as e:
            logger.error(f"病毒传播评分计算失败: {str(e)}")
            return 0.5  # 默认中等评分

    def _calculate_emotion_intensity(self, text: str) -> float:
        """计算文本情感强度"""
        try:
            if not text.strip():
                return 0.0

            # 检测语言
            language = "zh" if re.search(r'[\u4e00-\u9fff]', text) else "en"

            # 情感关键词库
            emotion_keywords = self._get_emotion_keywords()
            keywords = emotion_keywords.get(language, emotion_keywords.get("zh", {}))

            intensity = 0.0
            word_count = len(text.split())

            # 检查各类情感词汇
            for category, keyword_list in keywords.items():
                matches = sum(1 for keyword in keyword_list if keyword in text)
                if category == "intense":
                    intensity += matches * 0.3  # 强烈词汇权重更高
                elif category in ["positive", "negative"]:
                    intensity += matches * 0.2
                elif category == "suspense":
                    intensity += matches * 0.25

            # 检查标点符号强度
            exclamation_count = text.count("！") + text.count("!")
            question_count = text.count("？") + text.count("?")
            intensity += (exclamation_count * 0.1 + question_count * 0.05)

            # 标准化到0-1范围
            normalized_intensity = min(1.0, intensity / max(1, word_count * 0.1))

            return normalized_intensity

        except Exception as e:
            logger.error(f"情感强度计算失败: {str(e)}")
            return 0.5

    def _calculate_keyword_score(self, text: str) -> float:
        """计算关键词评分"""
        try:
            # 检测语言
            language = "zh" if re.search(r'[\u4e00-\u9fff]', text) else "en"
            emotion_keywords = self._get_emotion_keywords()
            keywords = emotion_keywords.get(language, {})

            score = 0.0
            total_words = len(text.split())

            for category, keyword_list in keywords.items():
                matches = sum(1 for keyword in keyword_list if keyword in text)
                if matches > 0:
                    if category == "intense":
                        score += matches * 0.3
                    elif category == "suspense":
                        score += matches * 0.25
                    else:
                        score += matches * 0.2

            return min(1.0, score / max(1, total_words * 0.1))

        except Exception as e:
            logger.error(f"关键词评分计算失败: {str(e)}")
            return 0.0

    def _calculate_narrative_position_score(self, subtitle: Dict[str, Any],
                                          narrative_analysis: Dict[str, Any]) -> float:
        """计算叙事位置评分"""
        try:
            # 高潮点和关键位置获得更高评分
            climax_points = narrative_analysis.get("climax_points", [])
            subtitle_time = subtitle.get("start_time", 0)

            # 检查是否接近高潮点
            for climax in climax_points:
                climax_time = climax.get("start_time", climax.get("time", 0))
                if abs(subtitle_time - climax_time) < 10:  # 10秒内
                    return 0.9

            # 基于叙事位置的基础评分
            narrative_beats = narrative_analysis.get("narrative_beats", [])
            for beat in narrative_beats:
                if beat.get("type") in ["climax", "plot_point_2", "midpoint"]:
                    return 0.7
                elif beat.get("type") in ["inciting_incident", "plot_point_1"]:
                    return 0.6

            return 0.5  # 默认评分

        except Exception as e:
            logger.error(f"叙事位置评分计算失败: {str(e)}")
            return 0.5

    def _calculate_length_score(self, text: str) -> float:
        """计算长度适宜性评分"""
        try:
            length = len(text)

            # 理想长度范围：10-50字符
            if 10 <= length <= 50:
                return 1.0
            elif 5 <= length < 10 or 50 < length <= 80:
                return 0.8
            elif length < 5 or length > 80:
                return 0.5
            else:
                return 0.3

        except Exception as e:
            logger.error(f"长度评分计算失败: {str(e)}")
            return 0.5

    def _get_emotion_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """获取情感关键词库"""
        return {
            "zh": {
                "positive": ["开心", "快乐", "兴奋", "激动", "惊喜", "满足", "幸福", "欣慰", "骄傲", "感动"],
                "negative": ["伤心", "难过", "愤怒", "失望", "绝望", "痛苦", "恐惧", "焦虑", "沮丧", "悲伤"],
                "intense": ["震撼", "惊人", "疯狂", "极致", "爆炸", "炸裂", "燃爆", "逆天", "神级", "史诗"],
                "suspense": ["悬疑", "神秘", "诡异", "离奇", "不可思议", "匪夷所思", "扑朔迷离", "悬念", "谜团", "秘密"]
            },
            "en": {
                "positive": ["happy", "joyful", "excited", "thrilled", "surprised", "satisfied", "blessed", "relieved", "proud", "moved"],
                "negative": ["sad", "upset", "angry", "disappointed", "desperate", "painful", "fearful", "anxious", "depressed", "sorrowful"],
                "intense": ["shocking", "amazing", "crazy", "extreme", "explosive", "mind-blowing", "epic", "legendary", "incredible", "phenomenal"],
                "suspense": ["mysterious", "strange", "weird", "bizarre", "unbelievable", "incomprehensible", "puzzling", "suspenseful", "enigmatic", "secretive"]
            }
        }

    def _update_progress(self, progress: int, message: str):
        """
        更新进度

        Args:
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        if self.progress_callback:
            try:
                self.progress_callback(progress, message)
            except Exception as e:
                logger.warning(f"进度回调失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()
