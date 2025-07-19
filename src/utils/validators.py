"""
验证函数工具集

提供各种数据验证的辅助函数
"""

import os
import re
import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import datetime


def validate_float_range(value: float, min_val: Optional[float] = None, 
                        max_val: Optional[float] = None) -> float:
    """
    验证浮点数是否在指定范围内
    
    Args:
        value: 待验证的值
        min_val: 最小值（如果为None则不验证下限）
        max_val: 最大值（如果为None则不验证上限）
        
    Returns:
        验证后的值（如果超出范围则裁剪到范围内）
    
    Raises:
        TypeError: 如果输入不是数字类型
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"值必须是数字类型，而不是 {type(value)}")
    
    result = float(value)
    
    if min_val is not None:
        result = max(min_val, result)
    
    if max_val is not None:
        result = min(max_val, result)
    
    return result


def validate_time_format(time_str: str) -> float:
    """
    验证时间格式字符串并转换为秒数
    支持的格式：SS, MM:SS, HH:MM:SS
    
    Args:
        time_str: 时间字符串
        
    Returns:
        秒数
        
    Raises:
        ValueError: 如果时间格式无效
    """
    # 处理浮点数表示的秒
    if isinstance(time_str, (int, float)):
        return float(time_str)
    
    # 处理时:分:秒格式
    if isinstance(time_str, str):
        if re.match(r'^\d+(\.\d+)?$', time_str):
            # 纯数字，直接转换为秒
            return float(time_str)
        
        # 尝试解析时间格式
        time_formats = [
            # HH:MM:SS.mmm
            (r'^(\d+):(\d+):(\d+(\.\d+)?)$', 
             lambda m: int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))),
            # MM:SS.mmm
            (r'^(\d+):(\d+(\.\d+)?)$', 
             lambda m: int(m.group(1)) * 60 + float(m.group(2)))
        ]
        
        for pattern, parser in time_formats:
            match = re.match(pattern, time_str)
            if match:
                return parser(match)
    
    # 处理时间戳对象
    if isinstance(time_str, datetime.timedelta):
        return time_str.total_seconds()
    
    raise ValueError(f"无效的时间格式: {time_str}")


def validate_language_code(language: str) -> str:
    """
    验证语言代码
    
    Args:
        language: 语言代码（如zh, en, fr等）
        
    Returns:
        标准化的语言代码
        
    Raises:
        ValueError: 如果语言代码无效
    """
    # 标准化为小写
    lang = language.lower().strip()
    
    # 支持的语言代码
    valid_codes = {
        "zh", "zh-cn", "zh-tw", "en", "ja", "ko", "fr", "de", 
        "es", "it", "ru", "pt", "nl", "ar", "hi", "auto"
    }
    
    # 常见别名映射
    aliases = {
        "chinese": "zh",
        "english": "en",
        "japanese": "ja",
        "korean": "ko",
        "french": "fr",
        "german": "de",
        "spanish": "es",
        "italian": "it",
        "russian": "ru",
        "portuguese": "pt",
        "dutch": "nl",
        "arabic": "ar",
        "hindi": "hi",
        "cn": "zh-cn",
        "tw": "zh-tw",
        "hk": "zh-tw",
        "simplified": "zh-cn",
        "traditional": "zh-tw",
        "中文": "zh",
        "英文": "en",
        "日文": "ja",
        "韩文": "ko",
        "法文": "fr",
        "德文": "de",
        "西班牙文": "es",
        "自动": "auto"
    }
    
    # 如果是别名，转换为标准代码
    if lang in aliases:
        lang = aliases[lang]
    
    # 验证是否是有效的语言代码
    if lang not in valid_codes:
        # 如果不是有效代码但以'-'分隔，取主要部分
        main_lang = lang.split('-')[0]
        if main_lang in valid_codes:
            return main_lang
        # 失败时返回auto
        return "auto"
    
    return lang


def validate_json_data(data: Any) -> Dict:
    """
    验证并规范化JSON数据
    
    Args:
        data: 要验证的数据
        
    Returns:
        规范化的JSON数据
        
    Raises:
        ValueError: 如果数据无法转换为有效的JSON
    """
    if isinstance(data, str):
        try:
            # 如果是字符串，尝试解析为JSON
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"无效的JSON字符串: {e}")
    
    if isinstance(data, dict):
        # 如果已经是字典，确保可以序列化为JSON
        try:
            json.dumps(data)
            return data
        except TypeError as e:
            raise ValueError(f"字典包含无法序列化为JSON的数据: {e}")
    
    raise ValueError(f"数据类型无法转换为JSON: {type(data)}")


def validate_file_path(path: Union[str, Path], must_exist: bool = False, 
                      create_dir: bool = False) -> Path:
    """
    验证文件路径
    
    Args:
        path: 文件路径
        must_exist: 文件是否必须存在
        create_dir: 是否创建目录
        
    Returns:
        规范化的Path对象
        
    Raises:
        ValueError: 如果路径无效
        FileNotFoundError: 如果must_exist为True但文件不存在
    """
    if not path:
        raise ValueError("文件路径不能为空")
    
    # 转换为Path对象
    file_path = Path(path)
    
    # 创建目录
    if create_dir:
        os.makedirs(file_path.parent, exist_ok=True)
    
    # 验证是否存在
    if must_exist and not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    return file_path 