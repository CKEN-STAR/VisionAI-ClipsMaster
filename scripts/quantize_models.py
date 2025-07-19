#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型量化转换脚本
用于将基础模型转换为量化版本，支持多种量化策略
"""

import os
import sys
import argparse
from pathlib import Path
import subprocess
import shutil
from loguru import logger
import yaml
from typing import Dict, Optional

# 量化配置
QUANT_CONFIGS = {
    'qwen2.5-7b-zh': {
        'base_dir': 'models/qwen/base/qwen/Qwen-7B-Chat',
        'quant_dir': 'models/qwen/quantized',
        'quant_type': 'Q4_K_M',  # 默认量化类型
        'model_files': ['model-00001-of-00008.safetensors',
                       'model-00002-of-00008.safetensors',
                       'model-00003-of-00008.safetensors',
                       'model-00004-of-00008.safetensors',
                       'model-00005-of-00008.safetensors',
                       'model-00006-of-00008.safetensors',
                       'model-00007-of-00008.safetensors',
                       'model-00008-of-00008.safetensors'],
        'config_file': 'configs/models/available_models/qwen2.5-7b-zh.yaml'
    },
    'mistral-7b-en': {
        'base_dir': 'models/mistral/base',
        'quant_dir': 'models/mistral/quantized',
        'quant_type': 'Q4_K_M',
        'model_files': ['model.safetensors'],  # 预留配置
        'config_file': 'configs/models/available_models/mistral-7b-en.yaml'
    }
}

# 支持的量化类型
QUANT_TYPES = ['Q4_K_M', 'Q5_K_M', 'Q6_K', 'Q8_0']

def setup_logging():
    """配置日志系统"""
    logger.remove()
    logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

def check_dependencies():
    """检查量化工具依赖"""
    try:
        import torch
        import transformers
        return True
    except ImportError as e:
        logger.error(f"缺少必要依赖: {str(e)}")
        logger.info("请执行: pip install torch transformers")
        return False

def update_model_config(model_name: str, quant_type: str):
    """更新模型配置文件，添加量化信息"""
    config_path = QUANT_CONFIGS[model_name]['config_file']
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在: {config_path}")
        return False
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # 更新量化配置
        config['quantization'] = {
            'type': quant_type,
            'bits': int(quant_type[1]),  # 从量化类型名称提取位数
            'path': str(Path(QUANT_CONFIGS[model_name]['quant_dir']) / f"{quant_type}.gguf")
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            
        logger.info(f"已更新模型配置: {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}")
        return False

def quantize_model(model_name: str, quant_type: str, skip_convert: bool = False):
    """执行模型量化转换"""
    if model_name not in QUANT_CONFIGS:
        raise ValueError(f"未知的模型: {model_name}")
        
    if quant_type not in QUANT_TYPES:
        raise ValueError(f"不支持的量化类型: {quant_type}")
        
    config = QUANT_CONFIGS[model_name]
    base_dir = Path(config['base_dir'])
    quant_dir = Path(config['quant_dir'])
    
    # 创建量化输出目录
    os.makedirs(quant_dir, exist_ok=True)
    
    if skip_convert:
        logger.info(f"跳过转换，仅更新配置: {model_name}")
        return update_model_config(model_name, quant_type)
    
    try:
        # 执行量化转换
        output_path = quant_dir / f"{quant_type}.gguf"
        logger.info(f"开始量化转换: {model_name} -> {quant_type}")
        
        # 使用llama.cpp进行量化
        llama_cpp_path = "tools/llama.cpp"
        if not os.path.exists(llama_cpp_path):
            logger.info("克隆llama.cpp...")
            subprocess.run(["git", "clone", "https://github.com/ggerganov/llama.cpp.git", llama_cpp_path], check=True)
            
            logger.info("编译llama.cpp...")
            subprocess.run(["make"], cwd=llama_cpp_path, check=True)
        
        # 转换模型为GGUF格式
        logger.info("转换模型为GGUF格式...")
        convert_cmd = [
            "python",
            f"{llama_cpp_path}/convert.py",
            str(base_dir),
            "--outfile", str(output_path),
            "--outtype", "f16"
        ]
        subprocess.run(convert_cmd, check=True)
        
        # 执行量化
        logger.info("执行量化...")
        quantize_cmd = [
            f"{llama_cpp_path}/quantize",
            str(output_path),
            str(output_path.with_suffix(f'.{quant_type}.gguf')),
            quant_type.lower()
        ]
        subprocess.run(quantize_cmd, check=True)
        
        # 更新配置文件
        if not update_model_config(model_name, quant_type):
            return False
            
        logger.info(f"量化转换完成: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"量化转换失败: {str(e)}")
        return False

def verify_quantization(model_name: str, quant_type: str) -> bool:
    """验证量化结果"""
    config = QUANT_CONFIGS[model_name]
    quant_dir = Path(config['quant_dir'])
    quant_file = quant_dir / f"{quant_type}.gguf"
    
    checks = {
        '量化模型文件': quant_file.exists(),
        '配置文件更新': Path(config['config_file']).exists()
    }
    
    # 检查文件大小（应该比原始模型小30-50%）
    if checks['量化模型文件']:
        original_size = sum(os.path.getsize(p) for p in Path(config['base_dir']).glob('*.safetensors'))
        quant_size = os.path.getsize(quant_file)
        size_reduction = (original_size - quant_size) / original_size * 100
        
        if not (30 <= size_reduction <= 50):
            logger.warning(f"量化后的大小减少比例 ({size_reduction:.1f}%) 不在预期范围内(30-50%)")
    
    return all(checks.values())

def main():
    parser = argparse.ArgumentParser(description='模型量化转换工具')
    parser.add_argument('--model', type=str, required=True, choices=QUANT_CONFIGS.keys(),
                      help='要量化的模型名称')
    parser.add_argument('--type', type=str, choices=QUANT_TYPES, default='Q4_K_M',
                      help='量化类型')
    parser.add_argument('--skip-convert', action='store_true',
                      help='跳过转换，只更新配置')
    parser.add_argument('--verify', action='store_true',
                      help='验证量化结果')
    
    args = parser.parse_args()
    setup_logging()
    
    if not check_dependencies():
        sys.exit(1)
    
    try:
        if args.verify:
            success = verify_quantization(args.model, args.type)
            sys.exit(0 if success else 1)
        
        success = quantize_model(args.model, args.type, args.skip_convert)
        if not success:
            sys.exit(1)
        
        # 验证量化结果
        if verify_quantization(args.model, args.type):
            logger.info(f"模型 {args.model} 量化成功")
        else:
            logger.error(f"模型 {args.model} 量化验证失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"量化失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 