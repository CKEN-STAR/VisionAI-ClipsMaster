#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
from tqdm import tqdm
import torch
from modelscope import snapshot_download, AutoTokenizer, AutoModelForCausalLM
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS = {
    "qwen": {
        "name": "QWen/QWen-7B-Chat",
        "path": "models/qwen/base",
        "model_id": "qwen/Qwen-7B-Chat"
    }
}

def download_model(model_type):
    """Download and save the specified model"""
    if model_type not in MODELS:
        raise ValueError(f"Unknown model type: {model_type}")
        
    model_info = MODELS[model_type]
    logger.info(f"Downloading {model_type} model from ModelScope...")
    
    try:
        # 使用ModelScope下载模型
        model_dir = snapshot_download(model_info["model_id"], cache_dir=model_info["path"])
        logger.info(f"Successfully downloaded {model_type} model to {model_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading {model_type} model: {str(e)}")
        return False

def main():
    """Main function to download all models"""
    success = True
    for model_type in MODELS:
        if not download_model(model_type):
            success = False
            
    if success:
        logger.info("All models downloaded successfully!")
    else:
        logger.error("Some models failed to download. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main() 