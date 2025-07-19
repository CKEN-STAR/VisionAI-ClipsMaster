#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
删除大模型文件，释放14.4GB空间
保留目录结构和配置文件
"""

import os
import sys
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def safe_remove_file(file_path):
    """安全删除文件"""
    try:
        if file_path.exists():
            size = file_path.stat().st_size
            file_path.unlink()
            logger.info(f"删除模型文件: {file_path.name} ({format_size(size)})")
            return size
    except (PermissionError, OSError) as e:
        logger.error(f"无法删除文件 {file_path}: {e}")
    return 0

def remove_model_files():
    """删除大模型文件"""
    logger.info("🗑️ 开始删除大模型文件...")
    
    total_removed = 0
    
    # 1. 删除Qwen模型文件
    qwen_base_dir = Path("models/models/qwen/base")
    if qwen_base_dir.exists():
        logger.info(f"📁 处理Qwen模型目录: {qwen_base_dir}")
        
        # 删除所有safetensors文件
        safetensor_files = list(qwen_base_dir.glob("*.safetensors"))
        logger.info(f"发现 {len(safetensor_files)} 个safetensors文件")
        
        for file_path in safetensor_files:
            total_removed += safe_remove_file(file_path)
        
        # 保留配置文件
        config_files = ["config.json", "generation_config.json", "tokenizer_config.json", "tokenizer.json"]
        preserved_files = []
        for config_file in config_files:
            config_path = qwen_base_dir / config_file
            if config_path.exists():
                preserved_files.append(config_file)
        
        if preserved_files:
            logger.info(f"保留配置文件: {', '.join(preserved_files)}")
    else:
        logger.warning("Qwen模型目录不存在")
    
    # 2. 删除Mistral模型文件
    mistral_base_dir = Path("models/mistral/base")
    if mistral_base_dir.exists():
        logger.info(f"📁 处理Mistral模型目录: {mistral_base_dir}")
        
        # 删除大模型文件
        model_patterns = ["*.safetensors", "*.bin", "*.pt", "*.pth"]
        for pattern in model_patterns:
            for file_path in mistral_base_dir.glob(pattern):
                if file_path.stat().st_size > 100 * 1024 * 1024:  # >100MB
                    total_removed += safe_remove_file(file_path)
    else:
        logger.info("Mistral模型目录不存在")
    
    # 3. 检查其他可能的大模型文件
    logger.info("🔍 检查其他大模型文件...")
    
    model_patterns = ["*.safetensors", "*.bin", "*.pt", "*.pth"]
    for pattern in model_patterns:
        for file_path in Path("models").rglob(pattern):
            if file_path.stat().st_size > 500 * 1024 * 1024:  # >500MB
                total_removed += safe_remove_file(file_path)
    
    logger.info("=" * 50)
    logger.info(f"🎉 模型文件删除完成!")
    logger.info(f"📊 总释放空间: {format_size(total_removed)}")
    logger.info("=" * 50)
    
    return total_removed

def verify_directory_structure():
    """验证目录结构保持完整"""
    logger.info("🔍 验证目录结构...")
    
    important_dirs = [
        "models/models/qwen/base",
        "models/models/qwen/quantized", 
        "models/mistral/base",
        "models/mistral/quantized",
        "configs/models"
    ]
    
    for dir_path in important_dirs:
        path = Path(dir_path)
        if path.exists():
            logger.info(f"✅ 目录存在: {dir_path}")
        else:
            logger.warning(f"⚠️ 目录不存在: {dir_path}")
    
    # 检查配置文件
    config_files = [
        "models/models/qwen/base/config.json",
        "configs/model_config.yaml"
    ]
    
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            logger.info(f"✅ 配置文件存在: {config_file}")
        else:
            logger.warning(f"⚠️ 配置文件不存在: {config_file}")

def main():
    """主函数"""
    logger.info("🚀 开始删除大模型文件操作...")
    
    # 确认操作
    print("⚠️ 警告：此操作将删除所有大模型文件（约14.4GB）")
    print("📋 将删除的文件类型：")
    print("  - models/models/qwen/base/*.safetensors")
    print("  - models/mistral/base/ 中的大文件")
    print("  - 其他>500MB的模型文件")
    print()
    print("✅ 将保留的内容：")
    print("  - 所有目录结构")
    print("  - 配置文件 (config.json, tokenizer.json等)")
    print("  - 小于100MB的文件")
    print()
    
    confirm = input("确认删除大模型文件? (y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 执行删除
    total_removed = remove_model_files()
    
    # 验证结构
    verify_directory_structure()
    
    print(f"\n✅ 操作完成！释放空间: {format_size(total_removed)}")

if __name__ == "__main__":
    main()
