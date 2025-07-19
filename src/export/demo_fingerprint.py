#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
素材指纹生成模块演示
"""

import os
import hashlib
import json
import time
from datetime import datetime

def generate_asset_id(file_path):
    """生成简单的素材ID"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
        
    try:
        file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
        return f"asset_{file_hash[:8]}"
    except Exception as e:
        print(f"处理失败: {e}")
        return None

def format_file_size(size_bytes):
    """将字节大小转换为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def get_basic_metadata(file_path):
    """获取基本的文件元数据"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
        
    try:
        file_stats = os.stat(file_path)
        file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
        
        return {
            "path": os.path.abspath(file_path),
            "filename": os.path.basename(file_path),
            "size_bytes": file_stats.st_size,
            "size_human": format_file_size(file_stats.st_size),
            "modified_time": time.ctime(file_stats.st_mtime),
            "created_time": time.ctime(file_stats.st_ctime),
            "extension": os.path.splitext(file_path)[1].lower(),
            "hash": {
                "sha256": file_hash,
                "sha256_short": file_hash[:8]
            },
            "asset_id": f"asset_{file_hash[:8]}"
        }
    except Exception as e:
        print(f"处理失败: {e}")
        return None

def demo_file_fingerprint(file_path):
    """演示文件指纹生成"""
    print(f"\n素材指纹演示: {file_path}")
    print("-" * 50)
    
    # 生成资产ID
    asset_id = generate_asset_id(file_path)
    if not asset_id:
        return
        
    print(f"生成的素材ID: {asset_id}")
    
    # 获取元数据
    metadata = get_basic_metadata(file_path)
    if not metadata:
        return
        
    print(f"文件大小: {metadata['size_human']}")
    print(f"修改时间: {metadata['modified_time']}")
    print(f"SHA256哈希: {metadata['hash']['sha256'][:16]}...")
    
    # 保存指纹到文件
    output_dir = "fingerprints"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"{asset_id}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"指纹已保存至: {output_path}")

def find_demo_file():
    """查找当前目录下的一个示例文件"""
    extensions = ['.py', '.json', '.md', '.txt']
    
    for file in os.listdir('.'):
        if os.path.isfile(file) and any(file.endswith(ext) for ext in extensions):
            # 不要用自己来测试
            if file == os.path.basename(__file__):
                continue
            return file
    
    return None

if __name__ == "__main__":
    import sys
    
    # 获取测试文件
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = find_demo_file()
        if not test_file:
            print("未找到测试文件，请提供一个文件路径作为参数")
            sys.exit(1)
            
    # 运行演示
    demo_file_fingerprint(test_file)
    
    print("\n素材指纹生成演示完成!") 