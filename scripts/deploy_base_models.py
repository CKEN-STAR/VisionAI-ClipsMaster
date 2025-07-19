#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基础预训练模型部署脚本
用于下载和设置基础预训练模型
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from tqdm import tqdm
from loguru import logger
from huggingface_hub import snapshot_download
import shutil
import yaml

# 模型配置
MODEL_CONFIGS = {
    'qwen2.5-7b-zh': {
        'repo_id': 'Qwen/Qwen1.5-7B-Chat',
        'local_dir': 'models/qwen/base',
        'config_file': 'configs/models/available_models/qwen2.5-7b-zh.yaml'
    },
    'mistral-7b-en': {
        'repo_id': 'mistralai/Mistral-7B-v0.1',
        'local_dir': 'models/mistral/base',
        'config_file': 'configs/models/available_models/mistral-7b-en.yaml'
    }
}

def setup_logging():
    """配置日志系统"""
    logger.remove()
    logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

def create_model_config(model_name: str, model_path: str):
    """创建或更新模型配置文件"""
    config = {
        'name': model_name,
        'path': model_path,
        'type': 'pretrained',
        'language': 'zh' if 'qwen' in model_name else 'en',
        'parameters': {
            'max_length': 2048,
            'temperature': 0.7,
            'top_p': 0.9,
            'repetition_penalty': 1.1
        }
    }
    
    config_path = MODEL_CONFIGS[model_name]['config_file']
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    
    logger.info(f"已创建/更新模型配置文件: {config_path}")

def deploy_model(model_name: str, skip_download: bool = False):
    """部署指定的模型"""
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"未知的模型: {model_name}")
    
    config = MODEL_CONFIGS[model_name]
    local_dir = Path(config['local_dir'])
    
    # 创建必要的目录
    os.makedirs(local_dir, exist_ok=True)
    
    # 创建或更新模型配置
    create_model_config(model_name, str(local_dir))
    
    if skip_download:
        logger.info(f"跳过模型下载，仅创建配置: {model_name}")
        return
    
    try:
        logger.info(f"开始下载模型 {model_name} 到 {local_dir}")
        snapshot_download(
            repo_id=config['repo_id'],
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        logger.info(f"模型 {model_name} 下载完成")
        
    except Exception as e:
        logger.error(f"模型下载失败: {str(e)}")
        raise

def verify_deployment(model_name: str):
    """验证模型部署状态"""
    config = MODEL_CONFIGS[model_name]
    local_dir = Path(config['local_dir'])
    config_file = Path(config['config_file'])
    
    # 检查目录和配置文件
    checks = {
        '模型目录': local_dir.exists(),
        '配置文件': config_file.exists()
    }
    
    if not checks['模型目录']:
        logger.error(f"模型目录不存在: {local_dir}")
    if not checks['配置文件']:
        logger.error(f"配置文件不存在: {config_file}")
    
    return all(checks.values())

def main():
    parser = argparse.ArgumentParser(description='部署基础预训练模型')
    parser.add_argument('--model', type=str, required=True, choices=MODEL_CONFIGS.keys(),
                      help='要部署的模型名称')
    parser.add_argument('--skip-download', action='store_true',
                      help='跳过下载，只创建配置')
    parser.add_argument('--verify', action='store_true',
                      help='验证部署状态')
    
    args = parser.parse_args()
    setup_logging()
    
    try:
        if args.verify:
            success = verify_deployment(args.model)
            sys.exit(0 if success else 1)
        
        deploy_model(args.model, args.skip_download)
        
        # 验证部署
        if verify_deployment(args.model):
            logger.info(f"模型 {args.model} 部署成功")
        else:
            logger.error(f"模型 {args.model} 部署验证失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"部署失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 