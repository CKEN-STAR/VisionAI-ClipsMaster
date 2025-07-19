#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据隔离验证脚本
用于验证中英文训练数据的隔离性，确保数据不受污染
可以集成到CI/CD流程以自动验证数据质量
"""

import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime

# 配置参数
CONFIG = {
    "languages": {
        "zh": {
            "name": "中文",
            "data_dir": "data/training/zh",
            "max_other_lang_ratio": 0.05,  # 最大允许的其他语言比例
            "other_lang": "en"
        },
        "en": {
            "name": "英文",
            "data_dir": "data/training/en",  # 修正英文数据目录路径
            "max_other_lang_ratio": 0.05,  # 最大允许的其他语言比例
            "other_lang": "zh"
        }
    },
    "report_file": "data/validation_reports/isolation_report.json",
    "ignore_files": ["contaminated_sample.txt"]  # 忽略的文件列表（用于测试）
}

def get_language_ratio(text):
    """
    计算文本中不同语言的比例
    
    Args:
        text: 输入文本
        
    Returns:
        dict: 包含语言比例的字典 {'zh': 中文比例, 'en': 英文比例, 'other': 其他字符比例}
    """
    if not text:
        return {'zh': 0, 'en': 0, 'other': 1}
    
    # 清理空白字符
    clean_text = text.strip()
    if not clean_text:
        return {'zh': 0, 'en': 0, 'other': 1}
    
    total_chars = len(clean_text)
    
    # 计算中文字符
    chinese_chars = 0
    for char in clean_text:
        if '\\\14e00' <= char <= '\\\19fff':
            chinese_chars += 1
    
    # 计算英文字符（a-z和A-Z）
    english_chars = 0
    for char in clean_text:
        if ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
            english_chars += 1
    
    # 其他字符
    other_chars = total_chars - chinese_chars - english_chars
    
    return {
        'zh': chinese_chars / total_chars,
        'en': english_chars / total_chars,
        'other': other_chars / total_chars
    }

def load_samples(directory):
    """
    加载指定目录下的文本样本
    
    Args:
        directory: 样本目录
        
    Returns:
        list: 文本样本列表，每个元素为(文件名, 内容)的元组
    """
    samples = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"警告: 目录不存在 {directory}")
        return samples
    
    for file_path in directory_path.glob("*.txt"):
        try:
            if file_path.name in CONFIG["ignore_files"]:
                print(f"跳过忽略的文件: {file_path.name}")
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # 忽略空文件
                    samples.append((file_path.name, content))
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
    
    return samples

def validate_language_isolation():
    """
    验证语言数据隔离性
    
    Returns:
        tuple: (是否通过验证, 验证报告)
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "passed": True,
        "languages": {},
        "contaminated_files": []
    }
    
    # 检查每种语言的样本
    for lang_code, lang_config in CONFIG["languages"].items():
        lang_name = lang_config["name"]
        data_dir = lang_config["data_dir"]
        max_ratio = lang_config["max_other_lang_ratio"]
        other_lang = lang_config["other_lang"]
        
        print(f"验证{lang_name}训练数据...")
        samples = load_samples(data_dir)
        
        # 初始化语言报告
        report["languages"][lang_code] = {
            "total_files": len(samples),
            "contaminated_files": 0,
            "average_contamination": 0.0
        }
        
        # 没有样本文件
        if not samples:
            print(f"警告: 未找到{lang_name}样本文件")
            continue
        
        # 检查每个样本
        contamination_total = 0.0
        for filename, content in samples:
            ratios = get_language_ratio(content)
            contamination_ratio = ratios[other_lang]
            contamination_total += contamination_ratio
            
            # 检查是否超过污染阈值
            if contamination_ratio >= max_ratio:
                report["languages"][lang_code]["contaminated_files"] += 1
                report["contaminated_files"].append({
                    "language": lang_code,
                    "filename": filename,
                    "contamination_ratio": contamination_ratio,
                    "other_lang": other_lang
                })
                print(f"警告: {lang_name}文件 {filename} 被{CONFIG['languages'][other_lang]['name']}污染: {contamination_ratio:.2%}")
                report["passed"] = False
        
        # 计算平均污染比例
        if samples:
            report["languages"][lang_code]["average_contamination"] = contamination_total / len(samples)
    
    # 保存报告
    try:
        report_path = Path(CONFIG["report_file"])
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"验证报告已保存至: {report_path}")
    except Exception as e:
        print(f"保存报告失败: {e}")
    
    return report["passed"], report

if __name__ == "__main__":
    print("=" * 50)
    print("数据隔离验证")
    print("=" * 50)
    
    passed, report = validate_language_isolation()
    
    print("\n" + "=" * 50)
    if passed:
        print("验证通过: 所有训练数据保持良好隔离")
    else:
        contaminated_count = len(report["contaminated_files"])
        print(f"验证失败: 发现{contaminated_count}个文件存在语言污染")
    print("=" * 50)
    
    # 返回适当的退出码
    sys.exit(0 if passed else 1) 