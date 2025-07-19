#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误消息系统使用示例

演示如何在不同场景下使用错误消息系统：
1. 基本错误消息生成
2. 从异常对象获取用户友好消息
3. 与错误日志系统集成
4. 多语言支持
5. 格式化器的使用
"""

import os
import sys
import traceback
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.exporters.error_messages import (
    generate_user_message,
    get_error_message,
    format_error,
    format_code,
    set_default_language,
    ErrorMessageFormatter
)
from src.exporters.error_logger import log_export_error
from src.exporters.error_logger_integration import (
    log_classified_error,
    log_and_get_user_message
)

# 尝试导入异常类
try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
except ImportError:
    # 如果导入失败，创建模拟类用于示例
    class ErrorCode:
        FORMAT_ERROR = 0x3F0
        MEMORY_ERROR = 0x3EC
        MODEL_ERROR = 0x3ED
        CONFIG_ERROR = 0x3F5
    
    # 简化的ClipMasterError实现
    class ClipMasterError(Exception):
        """示例用的自定义异常类"""
        def __init__(self, code, message=None, details=None):
            self.code = code
            self.message = message or "Error occurred"
            self.details = details or {}
            super().__init__(self.message)


def example_basic_message_generation():
    """基本错误消息生成示例"""
    print("\n=== 基本错误消息生成示例 ===")
    
    # 生成简单错误消息
    msg = generate_user_message("0xE100", "zh")
    print(f"简单错误消息 (中文): {msg}")
    
    # 生成英文错误消息
    msg = generate_user_message("0xE100", "en")
    print(f"简单错误消息 (英文): {msg}")
    
    # 带变量的错误消息
    msg = generate_user_message("0xE201", "zh", format="MP4")
    print(f"带变量的错误消息: {msg}")
    
    # 多变量错误消息
    msg = generate_user_message("0xE203", "zh", min_width=640, min_height=480)
    print(f"多变量错误消息: {msg}")


def example_from_exception():
    """从异常对象获取用户友好消息示例"""
    print("\n=== 从异常对象获取用户友好消息示例 ===")
    
    # 创建自定义异常
    error = ClipMasterError(
        ErrorCode.FORMAT_ERROR,  # 0x3F0
        "视频格式不支持",
        {"format": "AVI", "supported_formats": ["MP4", "MOV"]}
    )
    
    # 从异常获取用户友好消息
    msg = get_error_message(error, "zh")
    print(f"从异常获取消息 (中文): {msg}")
    
    msg = get_error_message(error, "en")
    print(f"从异常获取消息 (英文): {msg}")
    
    # 处理标准异常
    try:
        # 引发标准异常
        x = 1 / 0
    except Exception as e:
        msg = get_error_message(e, "zh")
        print(f"标准异常消息: {msg}")


def example_integration_with_logger():
    """与错误日志系统集成示例"""
    print("\n=== 与错误日志系统集成示例 ===")
    
    # 由于集成系统依赖项可能不完整，这部分可能会失败
    print("注意: 由于依赖项不完整，集成示例可能会失败")
    print("这是正常的，可以忽略相关错误\n")
    
    try:
        # 创建测试异常
        error = ClipMasterError(
            ErrorCode.MODEL_ERROR,  # 0x3ED
            "模型加载失败",
            {"model_name": "yolov5", "path": "/models/yolov5.pt"}
        )
        
        # 尝试记录错误并获取用户友好消息
        try:
            user_msg = log_and_get_user_message(error, phase="MODEL_LOADING", lang="zh")
            print(f"记录并获取用户消息: {user_msg}")
        except Exception as e:
            print(f"记录并获取用户消息失败: {str(e)}")
        
        # 尝试仅记录错误
        try:
            log_classified_error(error, phase="MODEL_LOADING", video_hash="abc123")
            print("错误已记录到日志")
        except Exception as e:
            print(f"记录错误失败: {str(e)}")
        
        # 尝试使用基础日志记录器
        try:
            log_export_error(error, phase="MODEL_LOADING")
            print("错误已记录到基础日志")
        except Exception as e:
            print(f"记录到基础日志失败: {str(e)}")
    except Exception as e:
        print(f"集成示例失败: {e}")


def example_formatter_usage():
    """格式化器使用示例"""
    print("\n=== 格式化器使用示例 ===")
    
    # 创建格式化器
    formatter = ErrorMessageFormatter(default_lang="zh")
    
    # 创建测试异常
    error = ClipMasterError(
        ErrorCode.MEMORY_ERROR,  # 0x3EC
        "内存不足",
        {"required_memory": 4096, "available_memory": 2048}
    )
    
    # 使用格式化器
    msg = formatter.format_error(error)
    print(f"格式化错误 (默认语言): {msg}")
    
    # 切换默认语言
    formatter.set_default_language("en")
    msg = formatter.format_error(error)
    print(f"格式化错误 (切换语言): {msg}")
    
    # 格式化错误代码
    msg = formatter.format_code(ErrorCode.FORMAT_ERROR, "zh")
    print(f"格式化错误代码: {msg}")


def example_convenience_functions():
    """便捷函数示例"""
    print("\n=== 便捷函数示例 ===")
    
    # 设置默认语言
    set_default_language("zh")
    print("默认语言已设置为中文")
    
    # 创建测试异常
    error = ClipMasterError(
        ErrorCode.CONFIG_ERROR,  # 0x3F5
        "项目格式错误"
    )
    
    # 使用便捷函数
    msg = format_error(error)
    print(f"格式化错误: {msg}")
    
    # 格式化错误代码
    msg = format_code("0xE500")
    print(f"格式化错误代码: {msg}")
    
    # 切换默认语言并使用便捷函数
    set_default_language("en")
    msg = format_error(error)
    print(f"英文格式化错误: {msg}")


def run_all_examples():
    """运行所有示例"""
    print("=== 错误消息系统使用示例 ===")
    
    # 运行各个示例
    example_basic_message_generation()
    example_from_exception()
    example_integration_with_logger()
    example_formatter_usage()
    example_convenience_functions()
    
    print("\n=== 示例结束 ===")


if __name__ == "__main__":
    run_all_examples() 