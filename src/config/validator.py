#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置验证器模块

负责验证用户配置的合法性，确保配置参数符合预期范围和类型。
支持不同类型配置的专项验证，如导出、存储、模型和系统配置等。
"""

import os
import sys
import logging
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Set

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
    from src.config.path_resolver import resolve_special_path, is_subpath
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)

# 设置日志记录器
logger = get_logger("config_validator")

class ConfigValidationError(Exception):
    """配置验证错误异常"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


def validate_config(user_config: Dict[str, Any]) -> List[str]:
    """
    深度验证配置合法性
    
    检查用户配置是否符合预期的范围和类型，确保所有必需参数存在
    
    Args:
        user_config: 用户配置字典
        
    Returns:
        List[str]: 错误信息列表，如果没有错误则为空列表
    """
    errors = []
    
    # 检查导出设置
    if "export" in user_config:
        export_errors = validate_export_config(user_config["export"])
        errors.extend(export_errors)
    
    # 检查存储设置
    if "storage" in user_config:
        storage_errors = validate_storage_config(user_config["storage"])
        errors.extend(storage_errors)
    
    # 检查模型设置
    if "model" in user_config:
        model_errors = validate_model_config(user_config["model"])
        errors.extend(model_errors)
    
    # 检查系统设置
    if "system" in user_config:
        system_errors = validate_system_config(user_config["system"])
        errors.extend(system_errors)
    
    # 检查UI设置
    if "ui" in user_config:
        ui_errors = validate_ui_config(user_config["ui"])
        errors.extend(ui_errors)
    
    # 检查全局设置
    if "global" in user_config:
        global_errors = validate_global_config(user_config["global"])
        errors.extend(global_errors)
    
    return errors


def validate_export_config(export_config: Dict[str, Any]) -> List[str]:
    """
    验证导出配置
    
    Args:
        export_config: 导出配置字典
        
    Returns:
        List[str]: 错误信息列表
    """
    errors = []
    
    # 验证帧率
    if "frame_rate" in export_config:
        frame_rate = export_config["frame_rate"]
        
        # 帧率必须是数字
        if not isinstance(frame_rate, (int, float)):
            errors.append(f"帧率必须是数字，当前为: {type(frame_rate).__name__}")
        
        # 帧率必须在合理范围内
        elif frame_rate > 60:
            errors.append(f"帧率超过最大值60: {frame_rate}")
        elif frame_rate < 10:
            errors.append(f"帧率低于最小值10: {frame_rate}")
    
    # 验证分辨率
    if "resolution" in export_config:
        resolution = export_config["resolution"]
        valid_resolutions = ["720p", "1080p", "2K", "4K"]
        
        if not isinstance(resolution, str):
            errors.append(f"分辨率必须是字符串，当前为: {type(resolution).__name__}")
        elif resolution not in valid_resolutions:
            errors.append(f"分辨率必须是以下值之一: {', '.join(valid_resolutions)}, 当前为: {resolution}")
    
    # 验证编解码器
    if "codec" in export_config:
        codec = export_config["codec"]
        valid_codecs = ["h264", "h265", "av1", "prores", "vp9"]
        
        if not isinstance(codec, str):
            errors.append(f"编解码器必须是字符串，当前为: {type(codec).__name__}")
        elif codec not in valid_codecs:
            errors.append(f"编解码器必须是以下值之一: {', '.join(valid_codecs)}, 当前为: {codec}")
    
    # 验证比特率
    if "bitrate" in export_config:
        bitrate = export_config["bitrate"]
        
        if not isinstance(bitrate, (int, float)):
            errors.append(f"比特率必须是数字，当前为: {type(bitrate).__name__}")
        elif bitrate < 1000:
            errors.append(f"比特率低于最小值1000: {bitrate}")
        elif bitrate > 100000:
            errors.append(f"比特率超过最大值100000: {bitrate}")
    
    # 验证格式
    if "format" in export_config:
        format_value = export_config["format"]
        valid_formats = ["mp4", "mov", "avi", "mkv"]
        
        if not isinstance(format_value, str):
            errors.append(f"导出格式必须是字符串，当前为: {type(format_value).__name__}")
        elif format_value not in valid_formats:
            errors.append(f"导出格式必须是以下值之一: {', '.join(valid_formats)}, 当前为: {format_value}")
    
    # 验证输出路径
    if "output_path" in export_config:
        output_path = export_config["output_path"]
        
        if not isinstance(output_path, str):
            errors.append(f"输出路径必须是字符串，当前为: {type(output_path).__name__}")
        else:
            try:
                # 解析路径并检查权限
                resolved_path = resolve_special_path(output_path)
                if os.path.exists(resolved_path) and not os.access(resolved_path, os.W_OK):
                    errors.append(f"输出路径不可写: {output_path}")
            except Exception as e:
                errors.append(f"输出路径错误: {str(e)}")
    
    return errors


def validate_storage_config(storage_config: Dict[str, Any]) -> List[str]:
    """
    验证存储配置
    
    Args:
        storage_config: 存储配置字典
        
    Returns:
        List[str]: 错误信息列表
    """
    errors = []
    
    # 验证输出路径
    if "output_path" in storage_config:
        output_path = storage_config["output_path"]
        
        if not isinstance(output_path, str):
            errors.append(f"输出路径必须是字符串，当前为: {type(output_path).__name__}")
        else:
            try:
                # 解析路径并检查权限
                resolved_path = resolve_special_path(output_path)
                if os.path.exists(resolved_path) and not os.access(resolved_path, os.W_OK):
                    errors.append(f"输出路径不可写: {output_path}")
            except Exception as e:
                errors.append(f"输出路径错误: {str(e)}")
    
    # 验证缓存路径
    if "cache_path" in storage_config:
        cache_path = storage_config["cache_path"]
        
        if not isinstance(cache_path, str):
            errors.append(f"缓存路径必须是字符串，当前为: {type(cache_path).__name__}")
        else:
            try:
                # 解析路径并检查权限
                resolved_path = resolve_special_path(cache_path)
                if os.path.exists(resolved_path) and not os.access(resolved_path, os.W_OK):
                    errors.append(f"缓存路径不可写: {cache_path}")
            except Exception as e:
                errors.append(f"缓存路径错误: {str(e)}")
    
    # 验证缓存大小限制
    if "cache_size_limit" in storage_config:
        cache_size_limit = storage_config["cache_size_limit"]
        
        if not isinstance(cache_size_limit, (int, float)):
            errors.append(f"缓存大小限制必须是数字，当前为: {type(cache_size_limit).__name__}")
        elif cache_size_limit < 100:
            errors.append(f"缓存大小限制低于最小值100MB: {cache_size_limit}")
        elif cache_size_limit > 50000:
            errors.append(f"缓存大小限制超过最大值50000MB: {cache_size_limit}")
    
    # 验证云存储设置
    if "cloud_storage" in storage_config and storage_config["cloud_storage"].get("enabled", False):
        cloud = storage_config["cloud_storage"]
        
        # 验证云存储类型
        if "type" in cloud:
            storage_type = cloud["type"]
            valid_types = ["s3", "oss", "gcs", "azure"]
            
            if not isinstance(storage_type, str):
                errors.append(f"云存储类型必须是字符串，当前为: {type(storage_type).__name__}")
            elif storage_type not in valid_types:
                errors.append(f"云存储类型必须是以下值之一: {', '.join(valid_types)}, 当前为: {storage_type}")
        
        # 验证必填字段
        required_fields = ["bucket", "access_key", "secret_key"]
        for field in required_fields:
            if field not in cloud or not cloud[field]:
                errors.append(f"启用云存储时，{field}为必填项")
    
    return errors


def validate_model_config(model_config: Dict[str, Any]) -> List[str]:
    """
    验证模型配置
    
    Args:
        model_config: 模型配置字典
        
    Returns:
        List[str]: 错误信息列表
    """
    errors = []
    
    # 验证语言模式
    if "language_mode" in model_config:
        language_mode = model_config["language_mode"]
        valid_modes = ["auto", "zh", "en"]
        
        if not isinstance(language_mode, str):
            errors.append(f"语言模式必须是字符串，当前为: {type(language_mode).__name__}")
        elif language_mode not in valid_modes:
            errors.append(f"语言模式必须是以下值之一: {', '.join(valid_modes)}, 当前为: {language_mode}")
    
    # 验证量化等级
    if "quantization" in model_config:
        quantization = model_config["quantization"]
        valid_levels = ["Q2_K", "Q4_K_M", "Q5_K", "Q8_0"]
        
        if not isinstance(quantization, str):
            errors.append(f"量化等级必须是字符串，当前为: {type(quantization).__name__}")
        elif quantization not in valid_levels:
            errors.append(f"量化等级必须是以下值之一: {', '.join(valid_levels)}, 当前为: {quantization}")
    
    # 验证上下文窗口大小
    if "context_length" in model_config:
        context_length = model_config["context_length"]
        
        if not isinstance(context_length, int):
            errors.append(f"上下文窗口大小必须是整数，当前为: {type(context_length).__name__}")
        elif context_length < 512:
            errors.append(f"上下文窗口大小低于最小值512: {context_length}")
        elif context_length > 8192:
            errors.append(f"上下文窗口大小超过最大值8192: {context_length}")
    
    # 验证生成参数
    if "generation_params" in model_config:
        gen_params = model_config["generation_params"]
        
        # 验证温度
        if "temperature" in gen_params:
            temp = gen_params["temperature"]
            
            if not isinstance(temp, (int, float)):
                errors.append(f"温度参数必须是数字，当前为: {type(temp).__name__}")
            elif temp < 0.1:
                errors.append(f"温度参数低于最小值0.1: {temp}")
            elif temp > 2.0:
                errors.append(f"温度参数超过最大值2.0: {temp}")
        
        # 验证top-p
        if "top_p" in gen_params:
            top_p = gen_params["top_p"]
            
            if not isinstance(top_p, (int, float)):
                errors.append(f"top_p参数必须是数字，当前为: {type(top_p).__name__}")
            elif top_p < 0.0:
                errors.append(f"top_p参数低于最小值0.0: {top_p}")
            elif top_p > 1.0:
                errors.append(f"top_p参数超过最大值1.0: {top_p}")
    
    # 验证是否禁用英文模型
    if "disable_en_model" in model_config:
        if not isinstance(model_config["disable_en_model"], bool):
            errors.append(f"disable_en_model必须是布尔值，当前为: {type(model_config['disable_en_model']).__name__}")
    
    return errors


def validate_system_config(system_config: Dict[str, Any]) -> List[str]:
    """
    验证系统配置
    
    Args:
        system_config: 系统配置字典
        
    Returns:
        List[str]: 错误信息列表
    """
    errors = []
    
    # 验证线程数
    if "num_threads" in system_config:
        threads = system_config["num_threads"]
        
        if not isinstance(threads, int):
            errors.append(f"线程数必须是整数，当前为: {type(threads).__name__}")
        elif threads < 1:
            errors.append(f"线程数低于最小值1: {threads}")
        elif threads > 32:
            errors.append(f"线程数超过最大值32: {threads}")
    
    # 验证内存限制
    if "memory_limit" in system_config:
        memory = system_config["memory_limit"]
        
        if not isinstance(memory, (int, float)):
            errors.append(f"内存限制必须是数字，当前为: {type(memory).__name__}")
        elif memory < 512:
            errors.append(f"内存限制低于最小值512MB: {memory}")
    
    # 验证GPU设置
    if "gpu" in system_config:
        gpu = system_config["gpu"]
        
        # 验证GPU使能
        if "enabled" in gpu and not isinstance(gpu["enabled"], bool):
            errors.append(f"GPU使能必须是布尔值，当前为: {type(gpu['enabled']).__name__}")
        
        # 验证GPU内存限制
        if "memory_limit" in gpu:
            gpu_mem = gpu["memory_limit"]
            
            if not isinstance(gpu_mem, (int, float)):
                errors.append(f"GPU内存限制必须是数字，当前为: {type(gpu_mem).__name__}")
            elif gpu_mem < 1024 and gpu_mem != 0:  # 0表示不限制
                errors.append(f"GPU内存限制低于最小值1024MB: {gpu_mem}")
    
    # 验证日志级别
    if "log_level" in system_config:
        log_level = system_config["log_level"]
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        
        if not isinstance(log_level, str):
            errors.append(f"日志级别必须是字符串，当前为: {type(log_level).__name__}")
        elif log_level.lower() not in valid_levels:
            errors.append(f"日志级别必须是以下值之一: {', '.join(valid_levels)}, 当前为: {log_level}")
    
    return errors


def validate_ui_config(ui_config: Dict[str, Any]) -> List[str]:
    """
    验证UI配置
    
    Args:
        ui_config: UI配置字典
        
    Returns:
        List[str]: 错误信息列表
    """
    errors = []
    
    # 验证主题
    if "theme" in ui_config:
        theme = ui_config["theme"]
        valid_themes = ["light", "dark", "system"]
        
        if not isinstance(theme, str):
            errors.append(f"主题必须是字符串，当前为: {type(theme).__name__}")
        elif theme not in valid_themes:
            errors.append(f"主题必须是以下值之一: {', '.join(valid_themes)}, 当前为: {theme}")
    
    # 验证字体大小
    if "font_size" in ui_config:
        font_size = ui_config["font_size"]
        
        if not isinstance(font_size, (int, float)):
            errors.append(f"字体大小必须是数字，当前为: {type(font_size).__name__}")
        elif font_size < 8:
            errors.append(f"字体大小低于最小值8: {font_size}")
        elif font_size > 24:
            errors.append(f"字体大小超过最大值24: {font_size}")
    
    # 验证语言
    if "language" in ui_config:
        language = ui_config["language"]
        valid_languages = ["zh-CN", "en-US", "auto"]
        
        if not isinstance(language, str):
            errors.append(f"界面语言必须是字符串，当前为: {type(language).__name__}")
        elif language not in valid_languages:
            errors.append(f"界面语言必须是以下值之一: {', '.join(valid_languages)}, 当前为: {language}")
    
    return errors


def validate_global_config(global_config: Dict[str, Any]) -> List[str]:
    """
    验证全局配置
    
    Args:
        global_config: 全局配置字典
        
    Returns:
        List[str]: 错误信息列表
    """
    errors = []
    
    # 验证默认语言模式
    if "default_language_mode" in global_config:
        lang_mode = global_config["default_language_mode"]
        valid_modes = ["auto", "zh", "en"]
        
        if not isinstance(lang_mode, str):
            errors.append(f"默认语言模式必须是字符串，当前为: {type(lang_mode).__name__}")
        elif lang_mode not in valid_modes:
            errors.append(f"默认语言模式必须是以下值之一: {', '.join(valid_modes)}, 当前为: {lang_mode}")
    
    # 验证自动保存间隔
    if "auto_save_interval" in global_config:
        interval = global_config["auto_save_interval"]
        
        if not isinstance(interval, int):
            errors.append(f"自动保存间隔必须是整数，当前为: {type(interval).__name__}")
        elif interval < 0:
            errors.append(f"自动保存间隔不能为负数: {interval}")
        elif interval > 60:
            errors.append(f"自动保存间隔超过最大值60分钟: {interval}")
    
    return errors


def validate_config_file(config_file_path: str) -> Tuple[bool, List[str]]:
    """
    验证配置文件
    
    Args:
        config_file_path: 配置文件路径
        
    Returns:
        Tuple[bool, List[str]]: (是否有效, 错误信息列表)
    """
    try:
        # 解析路径
        resolved_path = resolve_special_path(config_file_path)
        
        # 检查文件是否存在
        if not os.path.exists(resolved_path):
            return False, [f"配置文件不存在: {config_file_path}"]
        
        # 读取配置文件
        with open(resolved_path, 'r', encoding='utf-8') as f:
            # 根据文件扩展名选择解析方法
            if resolved_path.endswith('.json'):
                config = json.load(f)
            elif resolved_path.endswith('.yaml') or resolved_path.endswith('.yml'):
                config = yaml.safe_load(f)
            else:
                return False, [f"不支持的配置文件格式: {config_file_path}"]
        
        # 验证配置
        errors = validate_config(config)
        return len(errors) == 0, errors
        
    except Exception as e:
        return False, [f"配置文件验证失败: {str(e)}"]


if __name__ == "__main__":
    # 简单测试配置验证
    test_config = {
        "export": {
            "frame_rate": 30,
            "resolution": "1080p",
            "codec": "h264",
            "format": "mp4",
            "output_path": "~/videos/output"
        },
        "storage": {
            "output_path": "~/videos/output",
            "cache_path": "~/videos/cache"
        },
        "model": {
            "language_mode": "auto",
            "quantization": "Q4_K_M",
            "context_length": 2048,
            "generation_params": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
    }
    
    errors = validate_config(test_config)
    if not errors:
        print("配置验证通过!")
    else:
        for error in errors:
            print(f"错误: {error}") 