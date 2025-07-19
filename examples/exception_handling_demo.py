#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 异常处理演示

本示例演示了如何使用错误处理系统处理不同类型的异常，
并展示自动恢复机制的工作原理。
"""

import os
import sys
import time
import random

# 确保可以导入src模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.exceptions import (
    ClipMasterError, 
    ErrorCode,
    MemoryOverflowError,
    ModelCorruptionError,
    ResourceExhaustionError,
    VideoProcessError
)
from src.utils.error_handler import init_error_handler, get_error_handler
from src.utils.error_logger import get_error_logger
from src.core.auto_recovery import auto_heal, register_recovery_strategy
from loguru import logger

# 初始化错误处理器
error_handler = init_error_handler()

# 使用装饰器添加错误处理
@error_handler.with_error_handling(reraise=False)
def process_video(file_path, quality="high"):
    """演示处理视频文件的函数"""
    logger.info(f"处理视频: {file_path}, 质量: {quality}")
    
    # 模拟随机错误
    error_type = random.choice([
        "memory_error", 
        "model_error", 
        "resource_error", 
        "video_error",
        "success"  # 不抛出错误
    ])
    
    # 根据错误类型抛出不同异常
    if error_type == "memory_error":
        logger.warning("内存不足，即将抛出异常")
        raise MemoryOverflowError("处理视频时内存溢出", 
                                 details={"file": file_path, "quality": quality})
    
    elif error_type == "model_error":
        logger.warning("模型文件损坏，即将抛出异常")
        raise ModelCorruptionError("模型权重文件损坏", 
                                  details={"model": "qwen-zh"})
    
    elif error_type == "resource_error":
        logger.warning("资源耗尽，即将抛出异常")
        raise ResourceExhaustionError("GPU显存耗尽", 
                                     details={"resource": "gpu_memory"})
    
    elif error_type == "video_error":
        logger.warning("视频处理失败，即将抛出异常")
        raise VideoProcessError("视频解码失败", 
                               details={"codec": "h264", "file": file_path})
    
    # 成功处理的情况
    logger.success(f"视频 {file_path} 处理成功")
    return {"status": "success", "file": file_path, "quality": quality}

# 演示手动处理异常
def manual_exception_handling():
    """演示手动捕获和处理异常"""
    logger.info("=== 手动异常处理演示 ===")
    
    try:
        # 故意触发异常
        raise ResourceExhaustionError("磁盘空间不足", 
                                     details={"free_space": "100MB"})
    except ClipMasterError as e:
        # 手动处理异常
        logger.warning(f"捕获到异常: {e}")
        error_handler.handle_error(e)
        
        # 检查是否为严重错误
        if hasattr(e, 'critical') and e.critical:
            logger.error("这是一个严重错误，需要进行恢复")
            success = auto_heal(e)
            logger.info(f"自动恢复{'成功' if success else '失败'}")
        else:
            logger.info("这不是严重错误，继续执行")

# 演示使用装饰器处理异常
def decorator_exception_handling():
    """演示使用装饰器处理异常"""
    logger.info("=== 装饰器异常处理演示 ===")
    
    # 定义测试视频路径
    video_files = [
        "/path/to/video1.mp4",
        "/path/to/video2.mp4",
        "/path/to/video3.mp4"
    ]
    
    # 处理多个视频，观察错误处理
    for video in video_files:
        result = process_video(video)
        if result:
            logger.info(f"处理结果: {result}")
        else:
            logger.warning(f"处理 {video} 失败，但程序继续运行")
        
        # 每次处理后暂停，便于观察
        time.sleep(1)

# 演示注册自定义恢复策略
def custom_recovery_strategy():
    """演示如何注册和使用自定义恢复策略"""
    logger.info("=== 自定义恢复策略演示 ===")
    
    # 定义自定义恢复操作
    def custom_recovery_action():
        logger.info("[CustomRecovery] 执行自定义恢复操作")
        return True
    
    # 为特定错误注册自定义恢复策略
    custom_strategy = {
        "action": "custom_action", 
        "priority": 1
    }
    
    # 扩展auto_heal函数支持自定义恢复动作
    original_execute = auto_heal.__globals__['execute_strategies']
    
    def extended_execute(strategies, error_code=None):
        for strategy in strategies:
            if strategy.get('action') == 'custom_action':
                logger.info("执行自定义恢复动作")
                result = custom_recovery_action()
                return result
        return original_execute(strategies, error_code)
    
    # 替换执行函数
    auto_heal.__globals__['execute_strategies'] = extended_execute
    
    # 注册自定义策略
    register_recovery_strategy(ErrorCode.VIDEO_PROCESS_ERROR.value, custom_strategy)
    
    # 测试自定义恢复
    try:
        raise VideoProcessError("视频处理中断")
    except ClipMasterError as e:
        success = auto_heal(e)
        logger.info(f"自定义恢复{'成功' if success else '失败'}")
    
    # 恢复原始函数
    auto_heal.__globals__['execute_strategies'] = original_execute

def main():
    """主函数，运行所有演示"""
    logger.info("开始异常处理系统演示")
    
    # 运行演示
    manual_exception_handling()
    time.sleep(1)
    
    decorator_exception_handling()
    time.sleep(1)
    
    custom_recovery_strategy()
    
    logger.info("演示完成")

if __name__ == "__main__":
    main() 