#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立的语言检测测试脚本
避开循环导入问题
"""

import os
import sys
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("lang_test")

# 测试文件路径
ZH_TEST_SRT = "tests/golden_samples/zh/1_20250317_203031.srt"
EN_TEST_SRT = "tests/golden_samples/en/complex_1m.srt"


def is_chinese(text):
    """检测文本是否含有中文字符"""
    # 中文字符的Unicode范围
    chinese_pattern = re.compile(r'[\\\14e00-\\\19fff]')
    return bool(chinese_pattern.search(text))


def is_english(text):
    """检测文本是否主要是英文字符"""
    # 英文字符的比例
    english_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    total_chars = len(text.strip())
    return total_chars > 0 and english_chars / total_chars > 0.5


def detect_language(srt_path):
    """简单的语言检测器"""
    try:
        # 读取SRT文件
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取所有文本内容（去除时间码和序号）
        text_only = re.sub(r'\\\1+\\\1*\n\\\1{2}:\\\1{2}:\\\1{2},\\\1{3}\\\1+-->\\\1+\\\1{2}:\\\1{2}:\\\1{2},\\\1{3}\\\1*\n', '', content)
        text_only = re.sub(r'^\\\1+\\\1*$', '', text_only, flags=re.MULTILINE)
        
        # 检测语言
        if is_chinese(text_only):
            return "zh"
        elif is_english(text_only):
            return "en"
        else:
            # 进行更详细的分析
            chinese_count = len(re.findall(r'[\\\14e00-\\\19fff]', text_only))
            english_count = len(re.findall(r'[a-zA-Z]', text_only))
            
            return "zh" if chinese_count > english_count else "en"
    
    except Exception as e:
        logger.error(f"语言检测出错: {str(e)}")
        return "unknown"


def get_model_for_language(language):
    """根据语言选择模型"""
    if language == "zh":
        return "qwen2.5-7b-zh"
    elif language == "en":
        return "mistral-7b-en"
    else:
        return "qwen2.5-7b-zh"  # 默认使用中文模型


def main():
    """主函数"""
    logger.info("开始独立语言检测测试")
    
    # 测试中文字幕
    logger.info(f"检测中文字幕: {ZH_TEST_SRT}")
    zh_lang = detect_language(ZH_TEST_SRT)
    logger.info(f"检测结果: {zh_lang}")
    
    # 测试英文字幕
    logger.info(f"检测英文字幕: {EN_TEST_SRT}")
    en_lang = detect_language(EN_TEST_SRT)
    logger.info(f"检测结果: {en_lang}")
    
    # 获取对应模型
    zh_model = get_model_for_language(zh_lang)
    en_model = get_model_for_language(en_lang)
    
    logger.info(f"中文使用模型: {zh_model}")
    logger.info(f"英文使用模型: {en_model}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 