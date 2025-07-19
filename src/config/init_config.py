#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置初始化脚本

用于初始化配置目录，确保所有必要的配置文件存在。
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)

# 设置日志记录器
logger = get_logger("init_config")

def create_config_dir(config_dir: str) -> bool:
    """
    创建配置目录
    
    Args:
        config_dir: 配置目录路径
        
    Returns:
        bool: 是否成功创建
    """
    try:
        os.makedirs(config_dir, exist_ok=True)
        logger.info(f"配置目录已创建: {config_dir}")
        return True
    except Exception as e:
        logger.error(f"创建配置目录失败: {str(e)}")
        return False

def copy_default_configs(config_dir: str) -> bool:
    """
    复制默认配置文件
    
    Args:
        config_dir: 配置目录路径
        
    Returns:
        bool: 是否成功复制
    """
    # 默认配置文件列表
    default_configs = [
        "config_schema.yaml",
        "user_settings.yaml",
        "system_settings.yaml",
        "version_settings.yaml",
        "export_settings.yaml"
    ]
    
    default_config_dir = os.path.join(root_dir, "configs")
    
    success = True
    for config_file in default_configs:
        src_path = os.path.join(default_config_dir, config_file)
        dst_path = os.path.join(config_dir, config_file)
        
        # 如果目标文件已存在，则跳过
        if os.path.exists(dst_path):
            logger.debug(f"配置文件已存在，跳过: {dst_path}")
            continue
        
        try:
            # 检查源文件是否存在
            if not os.path.exists(src_path):
                logger.warning(f"默认配置文件不存在: {src_path}")
                success = False
                continue
            
            # 复制文件
            shutil.copy2(src_path, dst_path)
            logger.info(f"配置文件已复制: {dst_path}")
        except Exception as e:
            logger.error(f"复制配置文件失败: {str(e)}")
            success = False
    
    return success

def init_configs(config_dir: str, force: bool = False) -> bool:
    """
    初始化配置
    
    Args:
        config_dir: 配置目录路径
        force: 是否强制初始化（覆盖现有配置）
        
    Returns:
        bool: 是否成功初始化
    """
    # 创建配置目录
    if not create_config_dir(config_dir):
        return False
    
    # 如果强制初始化，则删除现有配置
    if force:
        try:
            for file in os.listdir(config_dir):
                if file.endswith('.yaml') or file.endswith('.json'):
                    file_path = os.path.join(config_dir, file)
                    os.remove(file_path)
                    logger.info(f"已删除配置文件: {file_path}")
        except Exception as e:
            logger.error(f"删除现有配置失败: {str(e)}")
            return False
    
    # 复制默认配置
    return copy_default_configs(config_dir)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="初始化配置目录")
    parser.add_argument('--config-dir', default=os.path.join(root_dir, "configs"),
                        help="配置目录路径")
    parser.add_argument('--force', action='store_true',
                        help="强制初始化（覆盖现有配置）")
    args = parser.parse_args()
    
    success = init_configs(args.config_dir, args.force)
    
    if success:
        print(f"配置初始化成功: {args.config_dir}")
        return 0
    else:
        print("配置初始化失败，请查看日志")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 