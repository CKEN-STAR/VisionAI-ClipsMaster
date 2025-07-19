#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志指纹生成模块

为日志文件生成指纹，用于日志完整性验证和防篡改。
每行日志添加基于SHA256的哈希值，形成哈希链，任何篡改都会破坏链条。
支持验证、摘要生成和日志会话唯一标识。
"""

import os
import hashlib
import json
import base64
import time
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Generator, Tuple, Any

from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_log_file_path

# 模块日志记录器
logger = get_module_logger("log_fingerprint")

def generate_log_fingerprint(log_path: Union[str, Path]) -> Generator[str, None, None]:
    """为日志文件生成哈希指纹链
    
    对每一行生成依赖于前一行的哈希值，形成防篡改的哈希链。
    
    Args:
        log_path: 日志文件路径
        
    Yields:
        带有哈希指纹的日志行
    """
    # 确保路径是Path对象
    log_path = Path(log_path)
    
    # 初始哈希值（种子值）
    prev_hash = "0"*64
    
    try:
        with open(log_path) as f:
            for line in f:
                # 生成当前行的哈希（依赖于前一行的哈希）
                current_hash = hashlib.sha256(f"{prev_hash}{line}".encode()).hexdigest()
                
                # 在行末添加哈希指纹
                line = line.strip() + f" <!-- hash:{current_hash} -->\n"
                
                # 更新哈希链
                prev_hash = current_hash
                
                yield line
    except Exception as e:
        logger.error(f"生成日志指纹时出错: {str(e)}")
        yield f"ERROR: 无法处理日志文件 {log_path}: {str(e)}\n"

def fingerprint_log_file(input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Optional[str]:
    """为整个日志文件生成指纹版本
    
    处理整个日志文件，生成带有指纹的新版本
    
    Args:
        input_path: 输入日志文件路径
        output_path: 输出文件路径，如果为None则自动生成
        
    Returns:
        输出文件路径，失败时返回None
    """
    # 确保路径是Path对象
    input_path = Path(input_path)
    
    # 如果未指定输出路径，自动生成
    if output_path is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = input_path.parent / f"{input_path.stem}_fingerprinted_{timestamp}{input_path.suffix}"
    else:
        output_path = Path(output_path)
        
    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成指纹版本
        with open(output_path, 'w', encoding='utf-8') as out_file:
            # 写入文件头
            header = f"# 日志指纹版本, 原始文件: {input_path.name}, 生成时间: {datetime.datetime.now().isoformat()}\n"
            out_file.write(header)
            
            # 写入带指纹的内容
            for line in generate_log_fingerprint(input_path):
                out_file.write(line)
                
        logger.info(f"已为日志文件生成指纹版本: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"创建指纹日志文件失败: {str(e)}")
        return None

def verify_fingerprinted_log(log_path: Union[str, Path]) -> Tuple[bool, List[Dict[str, Any]]]:
    """验证带指纹的日志文件完整性
    
    检查日志文件中的哈希链是否完整，验证是否被篡改
    
    Args:
        log_path: 带指纹的日志文件路径
    
    Returns:
        (是否完整, 错误列表)
    """
    log_path = Path(log_path)
    errors = []
    is_valid = True
    line_num = 0
    prev_hash = "0"*64  # 初始哈希种子值
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # 跳过注释行和空行
                if line.startswith('#') or not line:
                    continue
                
                # 提取哈希值
                import re
                hash_match = re.search(r'<!--\s*hash:([a-f0-9]{64})\s*-->', line)
                
                if not hash_match:
                    errors.append({
                        "line": line_num,
                        "error": "缺少哈希指纹",
                        "content": line[:100] + "..." if len(line) > 100 else line
                    })
                    is_valid = False
                    continue
                
                stored_hash = hash_match.group(1)
                
                # 移除哈希部分以计算实际哈希
                clean_line = re.sub(r'\s*<!--\s*hash:[a-f0-9]{64}\s*-->', '', line)
                
                # 计算当前行预期哈希
                expected_hash = hashlib.sha256(f"{prev_hash}{clean_line}".encode()).hexdigest()
                
                # 验证哈希
                if expected_hash != stored_hash:
                    errors.append({
                        "line": line_num,
                        "error": "哈希不匹配，可能被篡改",
                        "expected": expected_hash,
                        "found": stored_hash,
                        "content": clean_line[:100] + "..." if len(clean_line) > 100 else clean_line
                    })
                    is_valid = False
                
                # 更新哈希链
                prev_hash = stored_hash
                
        return is_valid, errors
        
    except Exception as e:
        errors.append({
            "line": line_num if line_num else 0,
            "error": f"验证过程中发生错误: {str(e)}",
            "content": ""
        })
        return False, errors

def generate_log_summary(log_path: Union[str, Path]) -> Dict[str, Any]:
    """生成日志摘要信息
    
    为日志文件生成摘要统计信息，包括大小、行数、时间范围等
    
    Args:
        log_path: 日志文件路径
        
    Returns:
        摘要信息字典
    """
    log_path = Path(log_path)
    
    if not log_path.exists():
        return {"error": f"日志文件不存在: {log_path}"}
    
    try:
        # 基本文件信息
        stats = log_path.stat()
        file_size = stats.st_size
        creation_time = datetime.datetime.fromtimestamp(stats.st_ctime)
        modification_time = datetime.datetime.fromtimestamp(stats.st_mtime)
        
        # 内容分析
        line_count = 0
        error_count = 0
        warning_count = 0
        first_timestamp = None
        last_timestamp = None
        
        # 常见时间戳模式
        import re
        timestamp_patterns = [
            # ISO格式: 2023-04-12T15:30:45.123
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?)',
            # 常见日志格式: 2023-04-12 15:30:45
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
            # 简单日期: 2023/04/12
            r'(\d{4}/\d{2}/\d{2})'
        ]
        
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line_count += 1
                
                # 统计错误和警告
                if "ERROR" in line or "Error" in line or "error" in line:
                    error_count += 1
                elif "WARNING" in line or "Warning" in line or "warning" in line:
                    warning_count += 1
                
                # 尝试提取时间戳
                for pattern in timestamp_patterns:
                    matches = re.search(pattern, line)
                    if matches:
                        timestamp_str = matches.group(1)
                        try:
                            # 尝试解析时间戳
                            if 'T' in timestamp_str:
                                timestamp = datetime.datetime.fromisoformat(timestamp_str)
                            elif ' ' in timestamp_str:
                                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            elif '/' in timestamp_str:
                                timestamp = datetime.datetime.strptime(timestamp_str, '%Y/%m/%d')
                                
                            if first_timestamp is None or timestamp < first_timestamp:
                                first_timestamp = timestamp
                            if last_timestamp is None or timestamp > last_timestamp:
                                last_timestamp = timestamp
                            break
                        except:
                            continue
        
        # 计算整体指纹 (文件内容的SHA256哈希)
        file_hash = hashlib.sha256()
        with open(log_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                file_hash.update(chunk)
        
        # 构建摘要
        summary = {
            "file_path": str(log_path),
            "file_name": log_path.name,
            "file_size": file_size,
            "file_size_human": _format_size(file_size),
            "creation_time": creation_time.isoformat(),
            "modification_time": modification_time.isoformat(),
            "line_count": line_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "file_hash": file_hash.hexdigest(),
            "analysis_time": datetime.datetime.now().isoformat()
        }
        
        # 添加时间范围（如果有）
        if first_timestamp and last_timestamp:
            summary["first_timestamp"] = first_timestamp.isoformat()
            summary["last_timestamp"] = last_timestamp.isoformat()
            summary["time_span_seconds"] = (last_timestamp - first_timestamp).total_seconds()
            
        return summary
        
    except Exception as e:
        logger.error(f"生成日志摘要时出错: {str(e)}")
        return {"error": str(e)}

def _format_size(size_bytes: int) -> str:
    """格式化文件大小为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def process_active_logs(output_dir: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """处理当前活动的日志文件
    
    为当前活动的日志文件生成指纹版本
    
    Args:
        output_dir: 输出目录
        
    Returns:
        处理结果字典 {原始文件: 指纹文件}
    """
    # 获取日志目录
    log_dir = get_log_directory()
    
    # 设置输出目录
    if output_dir is None:
        output_dir = log_dir / "fingerprinted"
    else:
        output_dir = Path(output_dir)
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 处理所有.log文件
    for log_file in log_dir.glob("**/*.log"):
        if log_file.is_file():
            # 跳过已指纹处理的文件
            if "fingerprinted" in log_file.name:
                continue
                
            output_file = output_dir / f"{log_file.stem}_fingerprinted_{timestamp}{log_file.suffix}"
            
            try:
                fingerprint_log_file(log_file, output_file)
                results[str(log_file)] = str(output_file)
                logger.info(f"已为 {log_file.name} 生成指纹版本")
            except Exception as e:
                logger.error(f"处理 {log_file.name} 时出错: {str(e)}")
                results[str(log_file)] = f"ERROR: {str(e)}"
    
    return results

if __name__ == "__main__":
    # 如果直接运行此模块，处理活动日志
    results = process_active_logs()
    print(f"已处理 {len(results)} 个日志文件")
    for src, dest in results.items():
        print(f"{Path(src).name} -> {Path(dest).name}") 