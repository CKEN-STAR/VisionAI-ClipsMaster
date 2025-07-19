#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 独立的训练数据许可证验证器

这是一个独立的脚本，用于验证训练数据的许可证合规性，
不依赖于项目中其他可能存在问题的模块。
"""

import os
import sys
import json
import time
import shutil
import logging
import hashlib
import datetime
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("license_validator")

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent

# 合法许可证列表
ALLOWED_LICENSES = [
    "CC-BY-4.0",      # 知识共享署名 4.0
    "CC-BY-SA-4.0",   # 知识共享署名-相同方式共享 4.0
    "CC-BY-NC-4.0",   # 知识共享署名-非商业性使用 4.0
    "Apache-2.0",     # Apache 许可证 2.0
    "MIT",            # MIT 许可证
    "BSD-3-Clause",   # BSD 3-Clause 许可证
    "GPL-3.0",        # GNU 通用公共许可证 3.0
    "LGPL-3.0",       # GNU 宽通用公共许可证 3.0
    "Proprietary-Licensed"  # 专有许可（已获授权）
]

# 隔离区目录
QUARANTINE_DIR = os.path.join(PROJECT_ROOT, "data", "training", "quarantine")

# 确保隔离区目录存在
os.makedirs(QUARANTINE_DIR, exist_ok=True)
for lang in ["zh", "en"]:
    os.makedirs(os.path.join(QUARANTINE_DIR, lang), exist_ok=True)

def get_license_from_file(file_path: str) -> Optional[str]:
    """
    从文件中提取许可证信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        str or None: 许可证标识符，如果未找到则返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 搜索文件头部的许可证信息
            # 通常许可证信息在文件的前20行
            lines = content.split('\n')[:20]
            
            # 检查常见的许可证标记
            license_markers = [
                ("License:", r"License:\\\\\\1*([\\\\\\1.-]+)"),
                ("许可证:", r"许可证:\\\\\\1*([\\\\\\1.-]+)"),
                ("版权声明:", r"版权声明:.*?[【\\\\\\1]([\\\\\\1.-]+)[】\\\\\\1]"),
                ("Copyright:", r"Copyright:.*?[(\\\\\\1]([\\\\\\1.-]+)[\\\\\\1)]")
            ]
            
            for prefix, pattern in license_markers:
                for line in lines:
                    if prefix in line:
                        match = re.search(pattern, line)
                        if match:
                            return match.group(1)
            
            # 检查JSON元数据
            if file_path.endswith('.json'):
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        # 检查常见的许可证字段
                        for field in ['license', 'LICENSE', 'License', '许可证']:
                            if field in data:
                                return data[field]
                except:
                    pass
                    
            # 检查文件名中的许可证标记
            filename = os.path.basename(file_path)
            for license_id in ALLOWED_LICENSES:
                if license_id.lower() in filename.lower():
                    return license_id
            
            # 默认返回None表示未找到许可证信息
            return None
            
    except Exception as e:
        logger.error(f"读取文件 {file_path} 时出错: {str(e)}")
        return None

def check_file_license(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    检查文件的许可证是否合法
    
    Args:
        file_path: 文件路径
        
    Returns:
        Tuple: (是否合法, 许可证标识符)
    """
    license_id = get_license_from_file(file_path)
    
    # 如果没有找到许可证信息，尝试检查metadata.json
    if not license_id:
        dir_path = os.path.dirname(file_path)
        metadata_path = os.path.join(dir_path, "metadata.json")
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    if "license" in metadata:
                        license_id = metadata["license"]
            except:
                pass
    
    # 检查许可证是否在允许列表中
    if license_id and license_id in ALLOWED_LICENSES:
        return True, license_id
    
    return False, license_id

def quarantine_data(file_path: str) -> bool:
    """
    将不合规数据移动到隔离区
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 隔离操作是否成功
    """
    try:
        # 确定文件的语言类型
        lang = "zh" if "/zh/" in file_path else "en" if "/en/" in file_path else "unknown"
        
        # 创建目标路径
        filename = os.path.basename(file_path)
        quarantine_path = os.path.join(QUARANTINE_DIR, lang, filename)
        
        # 如果已存在同名文件，添加哈希值以避免冲突
        if os.path.exists(quarantine_path):
            file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()[:8]
            base, ext = os.path.splitext(filename)
            quarantine_path = os.path.join(QUARANTINE_DIR, lang, f"{base}_{file_hash}{ext}")
        
        # 移动文件到隔离区
        shutil.move(file_path, quarantine_path)
        logger.warning(f"不合规数据已隔离: {file_path} -> {quarantine_path}")
        
        # 创建隔离记录
        record_path = f"{quarantine_path}.record.json"
        record = {
            "original_path": file_path,
            "quarantine_time": datetime.datetime.now().isoformat(),
            "reason": "未授权许可证或许可证缺失",
            "action": "隔离"
        }
        
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"隔离数据 {file_path} 时出错: {str(e)}")
        return False

def log_legal_risk(message: str, file_path: str, level: str = "warning") -> None:
    """
    记录法律风险
    
    Args:
        message: 风险消息
        file_path: 相关文件路径
        level: 风险级别，可选值: "info", "warning", "error"
    """
    log_funcs = {
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error
    }
    
    log_func = log_funcs.get(level.lower(), logger.warning)
    log_func(f"[法律风险] {message}: {file_path}")
    
    # 记录到法律风险日志文件
    risk_log_dir = os.path.join(PROJECT_ROOT, "logs", "legal")
    os.makedirs(risk_log_dir, exist_ok=True)
    
    risk_log_path = os.path.join(risk_log_dir, "legal_risks.log")
    with open(risk_log_path, 'a', encoding='utf-8') as f:
        timestamp = datetime.datetime.now().isoformat()
        f.write(f"[{timestamp}] [{level.upper()}] {message}: {file_path}\n")

def validate_training_dataset(dataset_dir: str) -> Dict[str, Any]:
    """
    验证整个训练数据集
    
    Args:
        dataset_dir: 数据集目录
        
    Returns:
        Dict: 验证结果统计
    """
    logger.info(f"开始验证训练数据合法性: {dataset_dir}")
    
    valid_files = []
    invalid_files = []
    
    # 计数器
    valid_count = 0
    quarantined_count = 0
    
    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            # 跳过隐藏文件和非数据文件
            if file.startswith('.') or file.endswith(('.pyc', '.log', '.md')):
                continue
                
            # 跳过metadata.json文件
            if file == "metadata.json":
                continue
            
            file_path = os.path.join(root, file)
            
            # 检查许可证
            is_valid, license_id = check_file_license(file_path)
            
            if is_valid:
                valid_count += 1
                valid_files.append({
                    "path": file_path,
                    "license": license_id
                })
            else:
                quarantined_count += 1
                invalid_files.append({
                    "path": file_path,
                    "license": license_id
                })
                
                # 记录风险
                log_legal_risk(
                    "未授权训练数据发现" if license_id else "训练数据缺少许可证信息", 
                    file_path, 
                    "warning"
                )
                
                # 隔离数据
                quarantine_data(file_path)
    
    # 准备结果报告
    total_count = valid_count + quarantined_count
    result = {
        "dataset_dir": dataset_dir,
        "valid_count": valid_count,
        "invalid_count": quarantined_count,
        "total_count": total_count,
        "valid_percent": 100.0 * valid_count / total_count if total_count > 0 else 0,
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # 保存验证报告
    report_dir = os.path.join(PROJECT_ROOT, "data", "validation_reports")
    os.makedirs(report_dir, exist_ok=True)
    
    report_path = os.path.join(report_dir, f"license_validation_{int(time.time())}.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"训练数据合法性验证完成: 有效 {valid_count}, 隔离 {quarantined_count}")
    logger.info(f"验证报告已保存: {report_path}")
    
    return result

def check_training_data_license():
    """验证训练数据版权许可"""
    logger.info("验证训练数据版权许可")
    
    # 获取训练数据目录
    training_data_dir = os.path.join(PROJECT_ROOT, "data", "training")
    
    # 确保训练数据目录存在
    if not os.path.exists(training_data_dir):
        logger.error(f"训练数据目录不存在: {training_data_dir}")
        return False
    
    # 验证中文训练数据
    zh_dir = os.path.join(training_data_dir, "zh")
    if os.path.exists(zh_dir):
        logger.info("验证中文训练数据...")
        zh_result = validate_training_dataset(zh_dir)
        
        print(f"\n中文训练数据验证结果:")
        print(f"总文件数: {zh_result['total_count']}")
        print(f"有效文件: {zh_result['valid_count']} ({zh_result['valid_percent']:.1f}%)")
        print(f"隔离文件: {zh_result['invalid_count']}")
        
        # 打印有效文件信息
        if zh_result['valid_files']:
            print("\n有效文件:")
            for file in zh_result['valid_files']:
                print(f"  - {os.path.basename(file['path'])}: {file['license']}")
                
        # 打印无效文件信息
        if zh_result['invalid_files']:
            print("\n无效文件:")
            for file in zh_result['invalid_files']:
                print(f"  - {os.path.basename(file['path'])}: {file['license'] if file['license'] else '无许可证'}")
    
    # 验证英文训练数据
    en_dir = os.path.join(training_data_dir, "en")
    if os.path.exists(en_dir):
        logger.info("验证英文训练数据...")
        en_result = validate_training_dataset(en_dir)
        
        print(f"\n英文训练数据验证结果:")
        print(f"总文件数: {en_result['total_count']}")
        print(f"有效文件: {en_result['valid_count']} ({en_result['valid_percent']:.1f}%)")
        print(f"隔离文件: {en_result['invalid_count']}")
        
        # 打印有效文件信息
        if en_result['valid_files']:
            print("\n有效文件:")
            for file in en_result['valid_files']:
                print(f"  - {os.path.basename(file['path'])}: {file['license']}")
                
        # 打印无效文件信息
        if en_result['invalid_files']:
            print("\n无效文件:")
            for file in en_result['invalid_files']:
                print(f"  - {os.path.basename(file['path'])}: {file['license'] if file['license'] else '无许可证'}")
    
    # 检查隔离区
    if os.path.exists(QUARANTINE_DIR):
        print("\n检查隔离区...")
        for lang in ["zh", "en"]:
            lang_dir = os.path.join(QUARANTINE_DIR, lang)
            if os.path.exists(lang_dir):
                files = [f for f in os.listdir(lang_dir) if not f.endswith('.record.json')]
                if files:
                    print(f"\n{lang}语言隔离数据:")
                    for file in files:
                        print(f"  - {file}")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("VisionAI-ClipsMaster 训练数据合法性验证器")
    print("=" * 50)
    
    # 运行验证
    check_training_data_license()
    
    print("\n训练数据合法性验证完成!") 