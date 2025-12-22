#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型微调训练器
实现中英文模型的微调训练功能，支持用户自定义训练数据
"""

import os
import json
import time
import logging
import torch
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import threading

# 尝试导入训练相关库
try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM,
        TrainingArguments, Trainer, DataCollatorForLanguageModeling,
        EarlyStoppingCallback, get_linear_schedule_with_warmup,
        TrainerCallback
    )
    from datasets import Dataset
    import torch.nn as nn
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
    HAS_PEFT = True
except ImportError:
    HAS_PEFT = False

# 尝试导入量化工具
try:
    from src.core.bnb_quantizer import BnBQuantizer, create_4bit_config, create_8bit_config
    HAS_BNB_QUANTIZER = True
except ImportError:
    HAS_BNB_QUANTIZER = False

# 导入版本管理器
try:
    from src.training.model_version_manager import ModelVersionManager
    HAS_VERSION_MANAGER = True
except ImportError:
    HAS_VERSION_MANAGER = False

logger = logging.getLogger(__name__)

class ModelFineTuner:
    """模型微调训练器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化微调训练器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.device = "cuda" if torch.cuda.is_available() and self.config.get("use_gpu", False) else "cpu"

        # 训练状态
        self.is_training = False
        self.current_training_info = None
        self.training_history = []

        # 回调函数
        self.progress_callback = None
        self.log_callback = None

        # 线程锁
        self._lock = threading.Lock()

        # 初始化版本管理器
        self.version_managers = {}
        if HAS_VERSION_MANAGER:
            try:
                self.version_managers["zh"] = ModelVersionManager(base_dir="models/qwen", max_versions=5)
                self.version_managers["en"] = ModelVersionManager(base_dir="models/mistral", max_versions=5)
                logger.info("版本管理器初始化成功")
            except Exception as e:
                logger.warning(f"版本管理器初始化失败: {e}")

        logger.info(f"模型微调训练器初始化完成，使用设备: {self.device}")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "models": {
                "zh": {
                    "base_model": "Qwen/Qwen2.5-1.5B-Instruct",  # 修正：使用Qwen2.5而非不存在的Qwen3
                    "model_path": "models/qwen2.5-1.5b/fp16",  # 修正：指向实际的本地模型路径
                    "output_dir": "models/qwen/finetuned"
                },
                "en": {
                    "base_model": "mistralai/Mistral-7B-Instruct-v0.3",
                    "model_path": "models/mistral/base",
                    "output_dir": "models/mistral/finetuned"
                }
            },
            "training": {
                "batch_size": 1,
                "gradient_accumulation_steps": 8,
                "learning_rate": 2e-5,
                "num_epochs": 3,
                "warmup_steps": 100,
                "max_length": 2048,
                "save_steps": 500,
                "eval_steps": 500,
                "logging_steps": 50,
                "early_stopping_patience": 3
            },
            "lora": {
                "enabled": True,
                "r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.1,
                "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"]
            },
            "quantization": {
                "enabled": False,  # 是否启用量化
                "load_in_8bit": False,  # 8bit量化
                "load_in_4bit": False,  # 4bit量化(QLoRA)
                "bnb_4bit_compute_dtype": "float16",  # 4bit计算类型
                "bnb_4bit_quant_type": "nf4",  # 量化类型
                "bnb_4bit_use_double_quant": True  # 双重量化
            },
            "memory_optimization": {
                "use_gradient_checkpointing": True,
                "dataloader_num_workers": 0,
                "fp16": False,
                "bf16": False
            },
            "use_gpu": False,
            "data_dir": "data/training/exports"
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        
        return default_config
    
    def set_callbacks(self, 
                     progress_callback: Optional[Callable[[str, float], None]] = None,
                     log_callback: Optional[Callable[[str], None]] = None):
        """设置回调函数"""
        self.progress_callback = progress_callback
        self.log_callback = log_callback
    
    def _log(self, message: str):
        """记录日志"""
        logger.info(message)
        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception as e:
                logger.warning(f"日志回调失败: {e}")
    
    def _update_progress(self, stage: str, progress: float):
        """更新进度"""
        if self.progress_callback:
            try:
                self.progress_callback(stage, progress)
            except Exception as e:
                logger.warning(f"进度回调失败: {e}")
    
    def fine_tune_model(self, 
                       language: str,
                       training_data_path: str,
                       validation_data_path: Optional[str] = None,
                       custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        微调模型
        
        Args:
            language: 语言代码 (zh/en)
            training_data_path: 训练数据路径
            validation_data_path: 验证数据路径
            custom_config: 自定义配置
            
        Returns:
            Dict[str, Any]: 训练结果
        """
        if not HAS_TRANSFORMERS:
            return {"success": False, "error": "transformers库未安装"}
        
        with self._lock:
            if self.is_training:
                return {"success": False, "error": "已有训练任务在进行中"}
            
            self.is_training = True
        
        try:
            training_id = f"training_{language}_{int(time.time())}"
            self._log(f"开始微调训练: {training_id}")
            start_time = time.time()
            
            self.current_training_info = {
                "id": training_id,
                "language": language,
                "start_time": start_time,
                "stage": "initializing",
                "progress": 0.0
            }
            
            # 合并配置
            training_config = self.config.copy()
            if custom_config:
                training_config.update(custom_config)
            
            # 第一步：加载数据
            self._update_progress("加载训练数据", 10.0)
            train_dataset, val_dataset = self._load_training_data(
                training_data_path, validation_data_path, language
            )
            
            if not train_dataset:
                return {"success": False, "error": "无法加载训练数据"}
            
            # 第二步：加载模型和tokenizer
            self._update_progress("加载模型", 20.0)
            model, tokenizer = self._load_model_and_tokenizer(language, training_config)
            
            if not model or not tokenizer:
                return {"success": False, "error": "无法加载模型"}
            
            # 第三步：配置LoRA（如果启用）
            if training_config["lora"]["enabled"] and HAS_PEFT:
                self._update_progress("配置LoRA", 25.0)
                model = self._setup_lora(model, training_config["lora"])
            
            # 第四步：准备训练参数
            self._update_progress("准备训练", 30.0)
            training_args = self._create_training_arguments(language, training_config)
            
            # 第五步：创建训练器
            trainer = self._create_trainer(
                model, tokenizer, train_dataset, val_dataset, training_args
            )
            
            # 第六步：开始训练
            self._update_progress("开始训练", 35.0)
            self._log("开始模型训练...")
            
            # 设置训练进度监控
            class ProgressCallback(TrainerCallback):
                def __init__(self, fine_tuner, total_steps):
                    super().__init__()
                    self.fine_tuner = fine_tuner
                    self.total_steps = total_steps

                def on_step_end(self, args, state, control, **kwargs):
                    progress = 35.0 + (state.global_step / self.total_steps) * 55.0
                    self.fine_tuner._update_progress("训练中", progress)
            
            # 计算总步数
            total_steps = len(train_dataset) // training_config["training"]["batch_size"] * training_config["training"]["num_epochs"]
            trainer.add_callback(ProgressCallback(self, total_steps))
            
            # 执行训练
            train_result = trainer.train()
            
            # 第七步：保存模型
            self._update_progress("保存模型", 90.0)
            output_dir = self.config["models"][language]["output_dir"]
            os.makedirs(output_dir, exist_ok=True)

            trainer.save_model(output_dir)
            tokenizer.save_pretrained(output_dir)

            # 保存训练配置
            config_path = os.path.join(output_dir, "training_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(training_config, f, ensure_ascii=False, indent=2)

            processing_time = time.time() - start_time

            # 第八步：注册模型版本
            version_id = None
            if HAS_VERSION_MANAGER and language in self.version_managers:
                try:
                    self._update_progress("注册模型版本", 95.0)
                    self._log("正在注册模型版本...")

                    # 准备训练信息
                    training_info = {
                        "training_type": "REAL_ML_TRAINING",
                        "dataset_size": len(training_data),
                        "training_args": {
                            "num_epochs": training_config["training"]["num_epochs"],
                            "batch_size": training_config["training"]["batch_size"],
                            "learning_rate": training_config["training"]["learning_rate"],
                            "max_length": training_config["training"]["max_length"]
                        },
                        "train_loss": float(train_result.training_loss) if hasattr(train_result, 'training_loss') else None,
                        "processing_time": processing_time
                    }

                    # 注册版本（使用引用模式，不复制文件）
                    version_manager = self.version_managers[language]
                    version_id = version_manager.register_new_version(
                        model_path=output_dir,
                        gguf_path=None,  # 不自动转换GGUF，用户可在UI中手动转换
                        training_info=training_info,
                        copy_files=False  # 使用引用模式，不复制文件，保持原有路径
                    )

                    if version_id:
                        self._log(f"✅ 版本注册成功: {version_id}")

                        # 显示存储使用情况
                        storage = version_manager.get_storage_usage()
                        self._log(f"   总存储: {storage['total_gb']:.2f}GB")
                        self._log(f"   版本数: {len(storage['versions'])}")
                    else:
                        self._log("⚠️ 版本注册失败")

                except Exception as e:
                    self._log(f"⚠️ 版本注册失败: {e}")
                    logger.warning(f"版本注册失败: {e}")
                    # 不影响训练成功的返回

            # 记录训练历史
            training_record = {
                "id": training_id,
                "language": language,
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "processing_time": processing_time,
                "output_dir": output_dir,
                "train_loss": train_result.training_loss,
                "version_id": version_id,
                "success": True
            }

            self.training_history.append(training_record)

            result = {
                "success": True,
                "training_id": training_id,
                "output_dir": output_dir,
                "processing_time": processing_time,
                "train_loss": train_result.training_loss,
                "version_id": version_id,
                "training_record": training_record
            }

            self._update_progress("训练完成", 100.0)
            self._log(f"微调训练完成: {training_id}，耗时 {processing_time:.2f} 秒")
            if version_id:
                self._log(f"模型版本: {version_id}")

            return result
            
        except Exception as e:
            error_msg = f"微调训练失败: {str(e)}"
            self._log(error_msg)
            logger.error(error_msg)
            
            # 记录失败的训练
            if hasattr(self, 'current_training_info') and self.current_training_info:
                training_record = {
                    "id": self.current_training_info["id"],
                    "language": language,
                    "start_time": datetime.fromtimestamp(self.current_training_info["start_time"]).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "error": str(e),
                    "success": False
                }
                self.training_history.append(training_record)
            
            return {"success": False, "error": str(e)}
            
        finally:
            with self._lock:
                self.is_training = False
                self.current_training_info = None
    
    def _load_training_data(self, 
                           training_data_path: str,
                           validation_data_path: Optional[str],
                           language: str) -> tuple:
        """加载训练数据"""
        try:
            # 加载训练数据
            if not os.path.exists(training_data_path):
                self._log(f"训练数据文件不存在: {training_data_path}")
                return None, None
            
            with open(training_data_path, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            
            # 提取数据部分
            if isinstance(train_data, dict) and "data" in train_data:
                train_data = train_data["data"]
            
            # 转换为训练格式
            train_texts = []
            for item in train_data:
                if isinstance(item, dict):
                    original = item.get("original_subtitles", "")
                    viral = item.get("viral_subtitles", "")
                    if original and viral:
                        # 构建训练文本
                        if language == "zh":
                            text = f"将以下字幕改写为爆款风格：\n{original}\n\n改写结果：\n{viral}"
                        else:
                            text = f"Rewrite the following subtitles in viral style:\n{original}\n\nRewritten result:\n{viral}"
                        train_texts.append(text)
            
            if not train_texts:
                self._log("训练数据为空")
                return None, None
            
            train_dataset = Dataset.from_dict({"text": train_texts})
            
            # 加载验证数据（如果提供）
            val_dataset = None
            if validation_data_path and os.path.exists(validation_data_path):
                try:
                    with open(validation_data_path, 'r', encoding='utf-8') as f:
                        val_data = json.load(f)
                    
                    if isinstance(val_data, dict) and "data" in val_data:
                        val_data = val_data["data"]
                    
                    val_texts = []
                    for item in val_data:
                        if isinstance(item, dict):
                            original = item.get("original_subtitles", "")
                            viral = item.get("viral_subtitles", "")
                            if original and viral:
                                if language == "zh":
                                    text = f"将以下字幕改写为爆款风格：\n{original}\n\n改写结果：\n{viral}"
                                else:
                                    text = f"Rewrite the following subtitles in viral style:\n{original}\n\nRewritten result:\n{viral}"
                                val_texts.append(text)
                    
                    if val_texts:
                        val_dataset = Dataset.from_dict({"text": val_texts})
                        
                except Exception as e:
                    self._log(f"加载验证数据失败: {e}")
            
            self._log(f"训练数据加载完成: {len(train_texts)} 条训练样本")
            if val_dataset:
                self._log(f"验证数据加载完成: {len(val_dataset)} 条验证样本")
            
            return train_dataset, val_dataset
            
        except Exception as e:
            self._log(f"加载训练数据失败: {str(e)}")
            return None, None
    
    def _load_model_and_tokenizer(self, language: str, config: Dict[str, Any]) -> tuple:
        """加载模型和tokenizer(支持量化)"""
        try:
            model_config = config["models"][language]
            # 优先使用本地路径，如果不存在则使用HuggingFace ID
            model_path = model_config.get("model_path", model_config["base_model"])
            quant_config = config.get("quantization", {})

            self._log(f"加载模型: {model_path}")

            # 检查本地模型是否存在
            import os
            if not os.path.exists(os.path.join(model_path, "config.json")):
                self._log(f"错误: 本地模型不存在: {model_path}")
                return None, None

            # 检查是否启用量化
            use_quantization = quant_config.get("enabled", False)
            load_in_8bit = quant_config.get("load_in_8bit", False)
            load_in_4bit = quant_config.get("load_in_4bit", False)

            # 加载tokenizer（从本地路径）
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                padding_side="right",
                local_files_only=True  # 只使用本地文件
            )

            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # 加载模型(支持量化)
            if use_quantization and HAS_BNB_QUANTIZER:
                self._log(f"使用量化加载: 8bit={load_in_8bit}, 4bit={load_in_4bit}")
                quantizer = BnBQuantizer()

                if load_in_4bit:
                    # 4bit量化(QLoRA)
                    model, _ = quantizer.load_model_4bit(
                        model_path,
                        device_map="auto",
                        compute_dtype=quant_config.get("bnb_4bit_compute_dtype", "float16"),
                        use_double_quant=quant_config.get("bnb_4bit_use_double_quant", True),
                        quant_type=quant_config.get("bnb_4bit_quant_type", "nf4")
                    )
                    # 准备模型用于k-bit训练
                    if HAS_PEFT:
                        model = prepare_model_for_kbit_training(model)
                        self._log("✅ 模型已准备用于4bit训练(QLoRA)")
                elif load_in_8bit:
                    # 8bit量化
                    model, _ = quantizer.load_model_8bit(
                        model_path,
                        device_map="auto"
                    )
                    # 准备模型用于k-bit训练
                    if HAS_PEFT:
                        model = prepare_model_for_kbit_training(model)
                        self._log("✅ 模型已准备用于8bit训练")
                else:
                    # 普通加载
                    model = self._load_model_normal(model_path, config)
            else:
                # 普通加载
                model = self._load_model_normal(model_path, config)

            # 启用梯度检查点（内存优化）
            if config["memory_optimization"]["use_gradient_checkpointing"]:
                model.gradient_checkpointing_enable()
            
            self._log("模型和tokenizer加载完成")
            return model, tokenizer

        except Exception as e:
            self._log(f"加载模型失败: {str(e)}")
            return None, None

    def _load_model_normal(self, model_path: str, config: Dict[str, Any]):
        """普通方式加载模型(无量化)"""
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            local_files_only=True  # 只使用本地文件
        )

        if self.device == "cpu":
            model = model.to("cpu")

        return model

    def _setup_lora(self, model, lora_config: Dict[str, Any]):
        """设置LoRA配置"""
        try:
            self._log("配置LoRA参数")

            peft_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=lora_config["r"],
                lora_alpha=lora_config["lora_alpha"],
                lora_dropout=lora_config["lora_dropout"],
                target_modules=lora_config["target_modules"]
            )

            model = get_peft_model(model, peft_config)
            model.print_trainable_parameters()

            self._log("LoRA配置完成")
            return model

        except Exception as e:
            self._log(f"LoRA配置失败: {str(e)}")
            return model

    def _create_training_arguments(self, language: str, config: Dict[str, Any]) -> 'TrainingArguments':
        """创建训练参数"""
        try:
            training_config = config["training"]
            memory_config = config["memory_optimization"]
            output_dir = config["models"][language]["output_dir"]

            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            args = TrainingArguments(
                output_dir=output_dir,
                overwrite_output_dir=True,
                num_train_epochs=training_config["num_epochs"],
                per_device_train_batch_size=training_config["batch_size"],
                per_device_eval_batch_size=training_config["batch_size"],
                gradient_accumulation_steps=training_config["gradient_accumulation_steps"],
                learning_rate=training_config["learning_rate"],
                warmup_steps=training_config["warmup_steps"],
                logging_steps=training_config["logging_steps"],
                save_steps=training_config["save_steps"],
                # 只有在有验证数据集时才启用评估
                evaluation_strategy="no",  # 禁用评估，因为没有验证数据集
                save_strategy="steps",
                # load_best_model_at_end=True,  # 禁用，因为没有评估
                # metric_for_best_model="eval_loss",  # 禁用，因为没有评估
                # greater_is_better=False,  # 禁用，因为没有评估
                dataloader_num_workers=memory_config["dataloader_num_workers"],
                fp16=memory_config["fp16"] and self.device == "cuda",
                bf16=memory_config["bf16"] and self.device == "cuda",
                gradient_checkpointing=memory_config["use_gradient_checkpointing"],
                report_to=None,  # 禁用wandb等报告
                remove_unused_columns=False,
                prediction_loss_only=True
            )

            self._log("训练参数配置完成")
            return args

        except Exception as e:
            self._log(f"创建训练参数失败: {str(e)}")
            raise

    def _create_trainer(self, model, tokenizer, train_dataset, val_dataset, training_args) -> 'Trainer':
        """创建训练器"""
        try:
            # 数据预处理函数
            def preprocess_function(examples):
                # 对文本进行tokenize
                model_inputs = tokenizer(
                    examples["text"],
                    truncation=True,
                    padding=True,
                    max_length=self.config["training"]["max_length"],
                    return_tensors="pt"
                )

                # 设置labels（用于计算loss）
                model_inputs["labels"] = model_inputs["input_ids"].clone()

                return model_inputs

            # 预处理数据集
            train_dataset = train_dataset.map(
                preprocess_function,
                batched=True,
                remove_columns=train_dataset.column_names
            )

            if val_dataset:
                val_dataset = val_dataset.map(
                    preprocess_function,
                    batched=True,
                    remove_columns=val_dataset.column_names
                )

            # 数据整理器
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False,  # 因果语言模型不使用MLM
                pad_to_multiple_of=8 if self.device == "cuda" else None
            )

            # 创建训练器
            # 只有在有验证数据集时才添加EarlyStoppingCallback
            callbacks = []
            if val_dataset is not None:
                callbacks.append(EarlyStoppingCallback(early_stopping_patience=self.config["training"]["early_stopping_patience"]))

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=data_collator,
                tokenizer=tokenizer,
                callbacks=callbacks
            )

            self._log("训练器创建完成")
            return trainer

        except Exception as e:
            self._log(f"创建训练器失败: {str(e)}")
            raise

    def get_training_status(self) -> Optional[Dict[str, Any]]:
        """获取当前训练状态"""
        with self._lock:
            return self.current_training_info.copy() if self.current_training_info else None

    def get_training_history(self) -> List[Dict[str, Any]]:
        """获取训练历史"""
        return self.training_history.copy()

    def validate_training_data(self, data_path: str) -> Dict[str, Any]:
        """验证训练数据格式"""
        try:
            if not os.path.exists(data_path):
                return {"valid": False, "error": f"数据文件不存在: {data_path}"}

            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查数据格式
            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            if not isinstance(data, list):
                return {"valid": False, "error": "数据格式错误，应为列表"}

            if len(data) == 0:
                return {"valid": False, "error": "数据为空"}

            # 检查数据项格式
            valid_count = 0
            for i, item in enumerate(data[:10]):  # 检查前10项
                if isinstance(item, dict):
                    if "original_subtitles" in item and "viral_subtitles" in item:
                        if item["original_subtitles"] and item["viral_subtitles"]:
                            valid_count += 1

            if valid_count == 0:
                return {"valid": False, "error": "没有找到有效的训练样本"}

            return {
                "valid": True,
                "total_samples": len(data),
                "valid_samples": valid_count,
                "sample_rate": valid_count / min(len(data), 10)
            }

        except Exception as e:
            return {"valid": False, "error": f"验证数据失败: {str(e)}"}

    def cleanup(self):
        """清理资源"""
        try:
            with self._lock:
                self.is_training = False
                self.current_training_info = None

            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self._log("微调训练器资源清理完成")

        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()
