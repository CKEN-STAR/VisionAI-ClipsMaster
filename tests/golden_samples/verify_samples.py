#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
黄金样本验证脚本

此脚本用于验证黄金样本的完整性，包括检查文件存在性、哈希值一致性等。
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# 添加项目根目录到系统路径
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# 黄金样本库目录
GOLDEN_SAMPLES_DIR = project_root / "tests" / "golden_samples"
METADATA_PATH = GOLDEN_SAMPLES_DIR / "metadata.json"

def verify_samples(verbose: bool = False) -> bool:
    """
    验证黄金样本的完整性
    
    Args:
        verbose: 是否输出详细信息
        
    Returns:
        bool: 验证通过返回True，否则返回False
    """
    print("开始验证黄金样本库...")
    
    if not METADATA_PATH.exists():
        print(f"错误: 元数据文件不存在: {METADATA_PATH}")
        return False
    
    # 加载元数据
    try:
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"错误: 无法加载元数据文件: {str(e)}")
        return False
    
    # 验证版本
    version = metadata.get("version", "unknown")
    print(f"黄金样本库版本: {version}")
    
    # 获取样本列表
    samples = metadata.get("samples", [])
    print(f"样本总数: {len(samples)}")
    
    verification_failed = False
    
    # 验证每个样本
    for sample in samples:
        name = sample.get("name", "unknown")
        lang = sample.get("lang", "unknown")
        
        print(f"\n验证样本: {name} ({lang})")
        
        # 验证视频文件
        if "video_path" in sample:
            video_path = project_root / sample["video_path"]
            video_hash = sample.get("video_hash", "")
            
            # 检查文件存在
            if not video_path.exists():
                print(f"  错误: 视频文件不存在: {video_path}")
                verification_failed = True
                continue
            
            # 验证哈希值
            current_hash = calculate_hash(str(video_path))
            if current_hash != video_hash:
                print(f"  错误: 视频哈希不匹配:")
                print(f"    期望: {video_hash}")
                print(f"    实际: {current_hash}")
                verification_failed = True
            else:
                if verbose:
                    print(f"  视频哈希验证通过: {video_path}")
        else:
            print(f"  警告: 无视频文件路径信息")
        
        # 验证字幕文件
        if "srt_path" in sample:
            srt_path = project_root / sample["srt_path"]
            srt_hash = sample.get("srt_hash", "")
            
            # 检查文件存在
            if not srt_path.exists():
                print(f"  错误: 字幕文件不存在: {srt_path}")
                verification_failed = True
                continue
            
            # 验证哈希值
            current_hash = calculate_hash(str(srt_path))
            if current_hash != srt_hash:
                print(f"  错误: 字幕哈希不匹配:")
                print(f"    期望: {srt_hash}")
                print(f"    实际: {current_hash}")
                verification_failed = True
            else:
                if verbose:
                    print(f"  字幕哈希验证通过: {srt_path}")
        else:
            print(f"  警告: 无字幕文件路径信息")
    
    # 整体验证结果
    if verification_failed:
        print("\n验证失败: 黄金样本库存在问题")
        return False
    else:
        print("\n验证通过: 黄金样本库完整")
        return True

def calculate_hash(file_path: str) -> str:
    """
    计算文件的SHA-256哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 哈希值字符串
    """
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # 分块读取文件以处理大文件
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"  计算哈希值失败: {str(e)}")
        return "hash_calculation_failed"

def build_if_missing() -> bool:
    """
    如果黄金样本库不存在，则构建它
    
    Returns:
        bool: 构建成功返回True，否则返回False
    """
    if not METADATA_PATH.exists():
        print("未找到黄金样本库，正在构建...")
        
        # 导入黄金样本生成模块
        from generate_samples import create_golden_samples
        
        # 生成样本
        create_golden_samples()
        
        # 验证是否成功构建
        return METADATA_PATH.exists()
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="黄金样本验证工具")
    parser.add_argument("--verbose", "-v", action="store_true", help="输出详细验证信息")
    parser.add_argument("--build-if-missing", "-b", action="store_true", help="如果样本不存在则构建")
    args = parser.parse_args()
    
    # 如果需要，构建缺失的样本
    if args.build_if_missing and not METADATA_PATH.exists():
        print("样本库不存在，尝试构建...")
        if not build_if_missing():
            print("构建黄金样本库失败")
            sys.exit(1)
    
    # 执行验证
    success = verify_samples(args.verbose)
    
    # 设置退出码
    sys.exit(0 if success else 1) 