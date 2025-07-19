#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
素材指纹生成模块

提供对视频、音频等媒体素材的指纹生成功能，用于高效识别和追踪素材。
素材指纹可用于：
1. 检测重复素材
2. 追踪素材版本变化
3. 快速定位素材
4. 素材去重
"""

import os
import hashlib
import logging
import json
from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path
import mimetypes
import time
import base64
from concurrent.futures import ThreadPoolExecutor

from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("asset_fingerprint")

def generate_asset_id(video_path: str) -> str:
    """通过文件内容哈希生成唯一素材ID
    
    为视频文件生成一个基于SHA256哈希的唯一标识符，截取前8位作为ID。
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        str: 生成的素材ID，格式为"asset_{hash[:8]}"
    
    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 无权限读取文件
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"文件不存在: {video_path}")
    
    try:
        file_hash = hashlib.sha256(open(video_path, 'rb').read()).hexdigest()
        return f"asset_{file_hash[:8]}"
    except PermissionError:
        logger.error(f"无权限读取文件: {video_path}")
        raise
    except Exception as e:
        logger.error(f"生成素材ID失败: {str(e)}")
        raise

def get_asset_metadata(video_path: str) -> Dict[str, Any]:
    """获取素材元数据
    
    获取视频文件的详细元数据，包括文件大小、修改时间、哈希等。
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        Dict[str, Any]: 素材元数据
    """
    if not os.path.exists(video_path):
        return {"error": "文件不存在"}
    
    try:
        file_stats = os.stat(video_path)
        file_hash = hashlib.sha256(open(video_path, 'rb').read()).hexdigest()
        
        # 猜测MIME类型
        mime_type, _ = mimetypes.guess_type(video_path)
        
        return {
            "path": os.path.abspath(video_path),
            "filename": os.path.basename(video_path),
            "size_bytes": file_stats.st_size,
            "size_human": format_file_size(file_stats.st_size),
            "modified_time": time.ctime(file_stats.st_mtime),
            "created_time": time.ctime(file_stats.st_ctime),
            "mime_type": mime_type or "未知",
            "extension": os.path.splitext(video_path)[1].lower(),
            "hash": {
                "sha256": file_hash,
                "sha256_short": file_hash[:8]
            },
            "asset_id": f"asset_{file_hash[:8]}"
        }
    except Exception as e:
        logger.error(f"获取素材元数据失败: {str(e)}")
        return {"error": str(e)}

def format_file_size(size_bytes: int) -> str:
    """将字节大小转换为人类可读格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化的文件大小
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def is_same_asset(path1: str, path2: str) -> bool:
    """检查两个文件是否为同一素材
    
    通过对比文件哈希来确定两个文件是否为同一素材
    
    Args:
        path1: 第一个文件路径
        path2: 第二个文件路径
        
    Returns:
        bool: 是否为同一素材
    """
    if not (os.path.exists(path1) and os.path.exists(path2)):
        return False
    
    try:
        hash1 = hashlib.sha256(open(path1, 'rb').read()).hexdigest()
        hash2 = hashlib.sha256(open(path2, 'rb').read()).hexdigest()
        return hash1 == hash2
    except Exception as e:
        logger.error(f"对比素材失败: {str(e)}")
        return False

def generate_chunk_fingerprint(file_path: str, chunk_size: int = 1024*1024) -> List[str]:
    """生成文件分块指纹
    
    针对大文件，通过分块哈希生成指纹列表，可用于部分匹配
    
    Args:
        file_path: 文件路径
        chunk_size: 分块大小（字节），默认1MB
        
    Returns:
        List[str]: 分块指纹列表
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    fingerprints = []
    
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_hash = hashlib.sha256(chunk).hexdigest()
                fingerprints.append(chunk_hash)
    except Exception as e:
        logger.error(f"生成分块指纹失败: {str(e)}")
        raise
    
    return fingerprints

def save_asset_fingerprint(file_path: str, output_dir: Optional[str] = None) -> str:
    """保存素材指纹到文件
    
    将素材的指纹和元数据保存到JSON文件，方便后续查询
    
    Args:
        file_path: 素材文件路径
        output_dir: 输出目录，默认为"data/fingerprints"
        
    Returns:
        str: 保存的指纹文件路径
    """
    if output_dir is None:
        output_dir = os.path.join("data", "fingerprints")
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        metadata = get_asset_metadata(file_path)
        asset_id = metadata.get("asset_id", f"asset_{int(time.time())}")
        
        # 添加简单的分块指纹（前10MB）
        try:
            chunk_fingerprints = generate_chunk_fingerprint(file_path, chunk_size=1024*1024)
            metadata["chunk_fingerprints"] = chunk_fingerprints[:10]  # 只保存前10个块
        except Exception as e:
            logger.warning(f"生成分块指纹失败: {str(e)}")
        
        # 保存到文件
        output_path = os.path.join(output_dir, f"{asset_id}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存素材指纹: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"保存素材指纹失败: {str(e)}")
        raise

def bulk_generate_fingerprints(directory: str, file_extensions: List[str] = None, recursive: bool = True) -> Dict[str, str]:
    """批量生成目录下所有素材的指纹
    
    Args:
        directory: 目录路径
        file_extensions: 文件扩展名列表，如['.mp4', '.mov']，为None则处理所有文件
        recursive: 是否递归处理子目录
        
    Returns:
        Dict[str, str]: 文件路径到素材ID的映射
    """
    if file_extensions is None:
        file_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v']
    
    file_paths = []
    results = {}
    
    # 收集所有匹配的文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in file_extensions):
                file_paths.append(os.path.join(root, file))
        
        if not recursive:
            break
    
    logger.info(f"找到 {len(file_paths)} 个媒体文件进行指纹生成")
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=min(10, os.cpu_count() or 4)) as executor:
        def process_file(file_path):
            try:
                asset_id = generate_asset_id(file_path)
                return file_path, asset_id
            except Exception as e:
                logger.error(f"处理文件 {file_path} 失败: {str(e)}")
                return file_path, None
        
        for file_path, asset_id in executor.map(process_file, file_paths):
            if asset_id:
                results[file_path] = asset_id
    
    logger.info(f"成功生成 {len(results)} 个素材指纹")
    return results

def find_duplicate_assets(directory: str, file_extensions: List[str] = None) -> Dict[str, List[str]]:
    """查找重复素材
    
    在指定目录下查找内容相同的重复素材文件
    
    Args:
        directory: 目录路径
        file_extensions: 文件扩展名列表，如['.mp4', '.mov']，为None则处理所有文件
        
    Returns:
        Dict[str, List[str]]: 指纹到文件路径列表的映射，每组表示相同内容的文件
    """
    if file_extensions is None:
        file_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v']
    
    # 收集文件路径
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in file_extensions):
                file_paths.append(os.path.join(root, file))
    
    # 生成指纹
    hash_map = {}
    for file_path in file_paths:
        try:
            file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
            if file_hash in hash_map:
                hash_map[file_hash].append(file_path)
            else:
                hash_map[file_hash] = [file_path]
        except Exception as e:
            logger.error(f"处理文件 {file_path} 失败: {str(e)}")
    
    # 过滤出有重复的
    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    return duplicates

# 为便于测试和示例，提供简单测试函数
def test_asset_fingerprint(video_path: str):
    """测试素材指纹功能
    
    Args:
        video_path: 视频文件路径
    """
    print(f"测试文件: {video_path}")
    
    try:
        # 生成素材ID
        asset_id = generate_asset_id(video_path)
        print(f"素材ID: {asset_id}")
        
        # 获取完整元数据
        metadata = get_asset_metadata(video_path)
        print(f"素材元数据: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
        
        # 保存指纹
        fingerprint_file = save_asset_fingerprint(video_path)
        print(f"指纹已保存至: {fingerprint_file}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    # 如果直接运行此脚本，测试当前目录下的第一个视频文件
    import sys
    
    if len(sys.argv) > 1:
        test_video = sys.argv[1]
    else:
        # 尝试在当前目录找一个视频文件
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        test_video = None
        
        for file in os.listdir('.'):
            if any(file.lower().endswith(ext) for ext in video_extensions):
                test_video = file
                break
        
        if not test_video:
            print("未找到视频文件，请指定视频文件路径作为参数")
            sys.exit(1)
    
    test_asset_fingerprint(test_video) 