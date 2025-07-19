#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户友好错误提示生成模块

为VisionAI-ClipsMaster项目提供多语言、用户友好的错误提示信息：
1. 错误代码映射到不同语言的用户友好消息
2. 支持变量插值，使错误消息更具体
3. 与错误日志系统集成
4. 支持多语言（中文、英文）
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.log_handler import get_logger

# 获取日志记录器
logger = get_logger("error_messages")

# 错误代码映射到多语言消息
ERROR_MAPPING = {
    # 项目格式和配置错误 (0xE1xx)
    "0xE100": {
        "zh": "工程文件格式错误(代码:E100), 建议检查XML模板",
        "en": "Project format error (Code:E100), check XML template"
    },
    "0xE101": {
        "zh": "缺少法律声明(代码:E101), 请联系技术支持",
        "en": "Missing legal notice (Code:E101), contact support"
    },
    "0xE102": {
        "zh": "配置文件损坏(代码:E102), 请重新安装程序",
        "en": "Configuration file corrupted (Code:E102), reinstall application"
    },
    
    # 视频处理错误 (0xE2xx)
    "0xE200": {
        "zh": "视频文件损坏(代码:E200), 请检查视频文件完整性",
        "en": "Video file corrupted (Code:E200), check video file integrity"
    },
    "0xE201": {
        "zh": "不支持的视频格式(代码:E201), 当前格式: {format}",
        "en": "Unsupported video format (Code:E201), current format: {format}"
    },
    "0xE202": {
        "zh": "视频解码失败(代码:E202), 尝试使用其他编解码器",
        "en": "Video decoding failed (Code:E202), try different codec"
    },
    "0xE203": {
        "zh": "视频分辨率过低(代码:E203), 最低要求: {min_width}x{min_height}",
        "en": "Video resolution too low (Code:E203), minimum required: {min_width}x{min_height}"
    },
    
    # 音频处理错误 (0xE3xx)
    "0xE300": {
        "zh": "音频提取失败(代码:E300), 请检查视频音轨",
        "en": "Audio extraction failed (Code:E300), check video audio track"
    },
    "0xE301": {
        "zh": "音频质量过低(代码:E301), 建议使用更高质量的音频",
        "en": "Audio quality too low (Code:E301), consider using higher quality audio"
    },
    
    # 模型和AI错误 (0xE4xx)
    "0xE400": {
        "zh": "AI模型加载失败(代码:E400), 请检查模型文件是否完整",
        "en": "AI model loading failed (Code:E400), check model file integrity"
    },
    "0xE401": {
        "zh": "AI推理失败(代码:E401), {details}",
        "en": "AI inference failed (Code:E401), {details}"
    },
    "0xE402": {
        "zh": "未找到所需模型(代码:E402), 模型: {model_name}",
        "en": "Required model not found (Code:E402), model: {model_name}"
    },
    "0xE403": {
        "zh": "模型版本不兼容(代码:E403), 需要版本: {required}, 当前版本: {current}",
        "en": "Model version incompatible (Code:E403), required version: {required}, current: {current}"
    },
    
    # 系统资源错误 (0xE5xx)
    "0xE500": {
        "zh": "内存不足(代码:E500), 需要至少{required_memory}MB内存",
        "en": "Insufficient memory (Code:E500), at least {required_memory}MB required"
    },
    "0xE501": {
        "zh": "磁盘空间不足(代码:E501), 需要至少{required_space}GB可用空间",
        "en": "Insufficient disk space (Code:E501), at least {required_space}GB free space required"
    },
    "0xE502": {
        "zh": "GPU内存不足(代码:E502), 建议关闭其他程序或降低处理分辨率",
        "en": "Insufficient GPU memory (Code:E502), close other applications or lower processing resolution"
    },
    
    # 导出错误 (0xE6xx)
    "0xE600": {
        "zh": "导出路径不可写(代码:E600), 请检查权限或选择其他路径",
        "en": "Export path not writable (Code:E600), check permissions or choose different path"
    },
    "0xE601": {
        "zh": "导出格式不支持(代码:E601), 支持的格式: {supported_formats}",
        "en": "Export format not supported (Code:E601), supported formats: {supported_formats}"
    },
    "0xE602": {
        "zh": "导出中断(代码:E602), 原因: {reason}",
        "en": "Export interrupted (Code:E602), reason: {reason}"
    },
    
    # 网络错误 (0xE7xx)
    "0xE700": {
        "zh": "网络连接失败(代码:E700), 请检查网络连接",
        "en": "Network connection failed (Code:E700), check network connection"
    },
    "0xE701": {
        "zh": "服务器响应超时(代码:E701), 请稍后重试",
        "en": "Server response timeout (Code:E701), please try again later"
    },
    "0xE702": {
        "zh": "下载失败(代码:E702), 资源: {resource}",
        "en": "Download failed (Code:E702), resource: {resource}"
    },
    
    # 权限和授权错误 (0xE8xx)
    "0xE800": {
        "zh": "授权验证失败(代码:E800), 请检查许可证",
        "en": "Authorization failed (Code:E800), check license"
    },
    "0xE801": {
        "zh": "许可证过期(代码:E801), 请续订",
        "en": "License expired (Code:E801), please renew"
    },
    "0xE802": {
        "zh": "功能未授权(代码:E802), 功能: {feature}",
        "en": "Feature not authorized (Code:E802), feature: {feature}"
    },
    
    # 一般错误 (0xEFxx)
    "0xEF00": {
        "zh": "未知错误(代码:EF00), 请联系技术支持",
        "en": "Unknown error (Code:EF00), contact technical support"
    },
    "0xEF01": {
        "zh": "操作被用户取消(代码:EF01)",
        "en": "Operation cancelled by user (Code:EF01)"
    },
    
    # 兼容项目已有的错误代码（从ErrorCode枚举中获取的）
    "0x3E8": {  # GENERAL_ERROR
        "zh": "通用错误(代码:3E8), 请检查操作后重试",
        "en": "General error (Code:3E8), please check and try again"
    },
    "0x3E9": {  # FILE_NOT_FOUND
        "zh": "文件未找到(代码:3E9), 路径: {path}",
        "en": "File not found (Code:3E9), path: {path}"
    },
    "0x3EA": {  # PERMISSION_DENIED
        "zh": "权限被拒绝(代码:3EA), 请检查文件/目录权限",
        "en": "Permission denied (Code:3EA), check file/directory permissions"
    },
    "0x3EB": {  # DEPENDENCY_ERROR
        "zh": "依赖项错误(代码:3EB), 缺少: {dependency}",
        "en": "Dependency error (Code:3EB), missing: {dependency}"
    },
    "0x3EC": {  # MEMORY_ERROR
        "zh": "内存错误(代码:3EC), 请关闭其他应用程序释放内存",
        "en": "Memory error (Code:3EC), close other applications to free memory"
    },
    "0x3ED": {  # MODEL_ERROR
        "zh": "模型错误(代码:3ED), 描述: {description}",
        "en": "Model error (Code:3ED), description: {description}"
    },
    "0x3EE": {  # VALIDATION_ERROR
        "zh": "验证错误(代码:3EE), {field}: {message}",
        "en": "Validation error (Code:3EE), {field}: {message}"
    },
    "0x3EF": {  # PROCESSING_ERROR
        "zh": "处理错误(代码:3EF), 步骤: {step}",
        "en": "Processing error (Code:3EF), step: {step}"
    },
    "0x3F0": {  # FORMAT_ERROR
        "zh": "格式错误(代码:3F0), 请检查输入格式",
        "en": "Format error (Code:3F0), check input format"
    },
    "0x3F1": {  # NETWORK_ERROR
        "zh": "网络错误(代码:3F1), 请检查网络连接",
        "en": "Network error (Code:3F1), check network connection"
    },
    "0x3F2": {  # USER_INPUT_ERROR
        "zh": "用户输入错误(代码:3F2), {field}: {message}",
        "en": "User input error (Code:3F2), {field}: {message}"
    },
    "0x3F3": {  # SYSTEM_ERROR
        "zh": "系统错误(代码:3F3), 请重启应用",
        "en": "System error (Code:3F3), restart application"
    },
    "0x3F4": {  # TIMEOUT_ERROR
        "zh": "超时错误(代码:3F4), 操作: {operation}",
        "en": "Timeout error (Code:3F4), operation: {operation}"
    },
    "0x3F5": {  # CONFIG_ERROR
        "zh": "配置错误(代码:3F5), 项: {item}",
        "en": "Configuration error (Code:3F5), item: {item}"
    }
}


def generate_user_message(code: str, lang: str = 'zh', **kwargs) -> str:
    """生成用户友好的错误提示信息
    
    Args:
        code: 错误代码，格式为十六进制字符串，如"0xE100"
        lang: 语言代码 ('zh'为中文, 'en'为英文)
        **kwargs: 格式化参数，用于在错误消息中替换变量
    
    Returns:
        str: 格式化后的用户友好错误消息
    """
    # 标准化错误代码格式
    if not code.startswith("0x"):
        code = f"0x{code.upper()}"
    
    # 获取对应语言的错误消息
    error_msg = ERROR_MAPPING.get(code, {}).get(lang)
    
    # 如果没有找到对应的错误消息，返回通用错误
    if not error_msg:
        if lang == 'zh':
            return f"未知错误 (代码:{code})"
        else:
            return f"Unknown error (Code:{code})"
    
    # 替换错误消息中的变量
    try:
        if kwargs:
            error_msg = error_msg.format(**kwargs)
    except KeyError as e:
        logger.warning(f"格式化错误消息时缺少参数: {e}")
    except Exception as e:
        logger.warning(f"格式化错误消息失败: {e}")
    
    return error_msg


def get_error_message(error: Exception, lang: str = 'zh', **kwargs) -> str:
    """从异常对象获取用户友好的错误消息
    
    Args:
        error: 异常对象，应该是ClipMasterError或其子类
        lang: 语言代码
        **kwargs: 额外格式化参数
    
    Returns:
        str: 用户友好的错误消息
    """
    from src.utils.exceptions import ClipMasterError, ErrorCode
    
    # 检查是否是我们的自定义错误
    if isinstance(error, ClipMasterError) and hasattr(error, 'code'):
        # 获取错误代码的十六进制表示
        code = error.code
        
        # 处理不同类型的错误代码
        if hasattr(code, 'value'):  # ErrorCode枚举
            code_hex = f"0x{code.value:X}"
        elif isinstance(code, int):  # 整数值
            code_hex = f"0x{code:X}"
        elif isinstance(code, str):  # 字符串值
            if code.startswith("0x"):
                code_hex = code.upper()
            else:
                code_hex = f"0x{code.upper()}"
        else:
            # 无法识别的代码类型，使用通用错误
            code_hex = "0xEF00"
        
        # 合并来自异常的详情和额外提供的参数
        params = {}
        if hasattr(error, 'details') and error.details:
            params.update(error.details)
        params.update(kwargs)
        
        # 生成错误消息
        return generate_user_message(code_hex, lang, **params)
    
    # 如果不是我们的自定义错误，返回通用错误消息
    if lang == 'zh':
        return f"程序错误: {str(error)}"
    else:
        return f"Application error: {str(error)}"


def translate_error_code(code: Union[str, int, 'ErrorCode'], lang: str = 'zh') -> str:
    """将错误代码转换为用户友好的错误描述
    
    Args:
        code: 错误代码，可以是字符串、整数或ErrorCode枚举
        lang: 语言代码
    
    Returns:
        str: 错误描述
    """
    from src.utils.exceptions import ErrorCode
    
    # 将ErrorCode枚举转换为十六进制字符串
    if isinstance(code, ErrorCode):
        code_hex = f"0x{code.value:X}"
    # 将整数转换为十六进制字符串
    elif isinstance(code, int):
        code_hex = f"0x{code:X}"
    # 确保字符串格式正确
    elif isinstance(code, str):
        if code.startswith("0x"):
            code_hex = code.upper()
        else:
            code_hex = f"0x{code.upper()}"
    else:
        code_hex = "0xEF00"  # 未知错误
    
    # 获取错误描述
    return generate_user_message(code_hex, lang)


class ErrorMessageFormatter:
    """错误消息格式化工具类"""
    
    def __init__(self, default_lang: str = 'zh'):
        """初始化错误消息格式化器
        
        Args:
            default_lang: 默认语言
        """
        self.default_lang = default_lang
    
    def format_error(self, error: Exception, lang: str = None, **kwargs) -> str:
        """格式化错误为用户友好消息
        
        Args:
            error: 异常对象
            lang: 语言代码，如果为None则使用默认语言
            **kwargs: 额外格式化参数
            
        Returns:
            str: 格式化后的错误消息
        """
        return get_error_message(error, lang or self.default_lang, **kwargs)
    
    def format_code(self, code: Union[str, int, 'ErrorCode'], lang: str = None) -> str:
        """格式化错误代码为用户友好消息
        
        Args:
            code: 错误代码
            lang: 语言代码，如果为None则使用默认语言
            
        Returns:
            str: 格式化后的错误消息
        """
        return translate_error_code(code, lang or self.default_lang)
    
    def set_default_language(self, lang: str) -> None:
        """设置默认语言
        
        Args:
            lang: 语言代码
        """
        self.default_lang = lang


# 创建默认格式化器
default_formatter = ErrorMessageFormatter()

# 快速访问函数
format_error = default_formatter.format_error
format_code = default_formatter.format_code
set_default_language = default_formatter.set_default_language 