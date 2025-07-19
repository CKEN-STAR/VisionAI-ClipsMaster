#!/usr/bin/env python
"""
模型下载脚本
用于下载和设置模型文件
"""

import os
import sys
import argparse
import requests
import time
from pathlib import Path
from tqdm import tqdm
from loguru import logger

# 模型配置
MODEL_CONFIGS = {
    'mistral-7b-en': {
        'url': 'https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF/resolve/main/mistral-7b-v0.1.Q4_K_M.gguf',
        'path': 'models/mistral/quantized/Q4_K_M.gguf',
        'size': 4_000_000_000  # 约4GB
    },
    'qwen2.5-7b-zh': {
        'url': 'https://huggingface.co/Qwen/Qwen1.5-7B-Chat-GGUF/resolve/main/qwen1_5-7b-chat-q4_k_m.gguf',
        'path': 'models/qwen/quantized/Q4_K_M.gguf',
        'size': 4_000_000_000  # 约4GB
    }
}

def download_file(url: str, dest_path: str, expected_size: int):
    """
    下载文件并显示进度条
    """
    max_retries = 3
    retry_delay = 5  # 秒
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                logger.error(f"无法获取文件大小: {url}")
                return False
                
            if total_size != expected_size:
                logger.warning(f"文件大小不匹配: 预期 {expected_size}, 实际 {total_size}")
                
            dest_path = Path(dest_path)
            if not dest_path.parent.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
            block_size = 1024  # 1KB
            progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
            
            try:
                with open(dest_path, 'wb') as f:
                    for data in response.iter_content(block_size):
                        progress_bar.update(len(data))
                        f.write(data)
                progress_bar.close()
                
                if total_size != 0 and progress_bar.n != total_size:
                    logger.error("下载不完整")
                    return False
                    
                return True
            except Exception as e:
                logger.error(f"下载失败: {str(e)}")
                return False
                
        except (requests.exceptions.RequestException, TimeoutError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"下载尝试 {attempt + 1} 失败，{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                logger.error(f"下载失败，已达到最大重试次数: {str(e)}")
                return False
                
    return False

def main():
    parser = argparse.ArgumentParser(description='下载模型文件')
    parser.add_argument('--model', type=str, required=True, choices=MODEL_CONFIGS.keys(),
                      help='要下载的模型名称')
    parser.add_argument('--skip-download', action='store_true',
                      help='跳过下载，只创建必要的目录结构')
    args = parser.parse_args()
    
    if args.model not in MODEL_CONFIGS:
        logger.error(f"未知的模型: {args.model}")
        sys.exit(1)
        
    config = MODEL_CONFIGS[args.model]
    logger.info(f"开始处理模型: {args.model}")
    
    # 创建必要的目录结构
    dest_path = Path(config['path'])
    if not dest_path.parent.exists():
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"已创建目录: {dest_path.parent}")
    
    if args.skip_download:
        logger.info("跳过模型下载，只创建目录结构")
        return
        
    success = download_file(config['url'], config['path'], config['size'])
    
    if success:
        logger.info(f"模型下载完成: {config['path']}")
    else:
        logger.error("模型下载失败")
        sys.exit(1)

if __name__ == '__main__':
    main() 