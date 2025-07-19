#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Initialization Script for VisionAI-ClipsMaster
Downloads and prepares models for first use
"""

import os
import yaml
import logging
import shutil
from pathlib import Path
from huggingface_hub import snapshot_download
from .converters.model_converter import ModelConverter

# Set up proxy if needed
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelInitializer:
    def __init__(self):
        self.config_dir = Path("configs/models/available_models")
        self.models_dir = Path("models")
        self.converter = ModelConverter()
        
    def initialize_models(self):
        """Initialize all configured models"""
        # 读取所有模型配置
        for config_file in self.config_dir.glob("*.yaml"):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if config['name'] == 'mistral-7b-en':
                logger.info("Skipping English model initialization as requested")
                continue
                
            self._initialize_single_model(config)
                
    def _initialize_single_model(self, config):
        """Initialize a single model based on its configuration"""
        model_name = config['name']
        logger.info(f"Initializing model: {model_name}")
        
        # 确定模型路径
        base_path = Path(config['path'].replace('\\', '/'))
        base_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 检查本地模型文件
        if not (base_path / "config.json").exists():
            logger.info(f"Model files not found at {base_path}, checking local files...")
            local_model_path = Path("models/qwen/base/qwen/Qwen-7B-Chat")
            if local_model_path.exists():
                logger.info(f"Found local model at {local_model_path}, copying...")
                shutil.copytree(str(local_model_path), str(base_path), dirs_exist_ok=True)
            else:
                logger.error(f"Local model files not found at {local_model_path}")
                return
            
        # 创建量化目录
        quant_dir = base_path.parent / "quantized"
        quant_dir.mkdir(exist_ok=True)
        
        # 执行量化
        default_quant = config['quantization']['default']
        output_path = quant_dir / f"{model_name}_{default_quant}.gguf"
        
        if not output_path.exists():
            logger.info(f"Converting model to GGUF with {default_quant} quantization...")
            try:
                self.converter.convert_format(
                    str(base_path),
                    "gguf",
                    str(output_path),
                    default_quant
                )
            except Exception as e:
                logger.error(f"Model conversion failed: {e}")
                return
            
        # 验证转换结果
        if not self.converter.verify_conversion(str(base_path), str(output_path)):
            logger.error(f"Model conversion verification failed for {model_name}")
            return
            
        logger.info(f"Successfully initialized {model_name}")
        
    def _get_model_id(self, model_name):
        """Get Hugging Face model ID based on model name"""
        model_ids = {
            'qwen2.5-7b-zh': 'Qwen/Qwen1.5-7B',
            'mistral-7b-en': 'mistralai/Mistral-7B-v0.1'
        }
        return model_ids.get(model_name)

if __name__ == "__main__":
    initializer = ModelInitializer()
    initializer.initialize_models() 