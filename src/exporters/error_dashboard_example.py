#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误监控看板示例程序

展示如何使用实时错误监控看板，包括错误注入、统计和可视化
"""

import os
import sys
import time
import random
import logging
import threading
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# 确保能够导入src模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入错误监控看板
from src.exporters.error_dashboard import LiveErrorMonitor, get_error_monitor

# 导入异常模块
try:
    from src.utils.exceptions import (
        ClipMasterError, ErrorCode, ModelCorruptionError, MemoryOverflowError,
        UserInputError, ResourceError, VideoProcessError, AudioProcessError,
        InvalidSRTError, ModelLoadError, FileOperationError
    )
except ImportError:
    # 如果无法导入，则使用模拟的异常类
    class ClipMasterError(Exception):
        def __init__(self, message, code=None, **kwargs):
            super().__init__(message)
            self.message = message
            self.code = code
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class ErrorCode:
        MODEL_ERROR = "MODEL_ERROR"
        MEMORY_ERROR = "MEMORY_ERROR"
        FILE_NOT_FOUND = "FILE_NOT_FOUND"
        PERMISSION_DENIED = "PERMISSION_DENIED"
        VALIDATION_ERROR = "VALIDATION_ERROR"
        TIMEOUT_ERROR = "TIMEOUT_ERROR"
        NETWORK_ERROR = "NETWORK_ERROR"
    
    # 定义模拟的错误类型
    ModelCorruptionError = type('ModelCorruptionError', (ClipMasterError,), {"code": "MODEL_ERROR"})
    MemoryOverflowError = type('MemoryOverflowError', (ClipMasterError,), {"code": "MEMORY_ERROR"})
    UserInputError = type('UserInputError', (ClipMasterError,), {"code": "USER_INPUT_ERROR"})
    ResourceError = type('ResourceError', (ClipMasterError,), {"code": "RESOURCE_ERROR"})
    VideoProcessError = type('VideoProcessError', (ClipMasterError,), {"code": "VIDEO_ERROR"})
    AudioProcessError = type('AudioProcessError', (ClipMasterError,), {"code": "AUDIO_ERROR"})
    InvalidSRTError = type('InvalidSRTError', (ClipMasterError,), {"code": "SRT_ERROR"})
    ModelLoadError = type('ModelLoadError', (ClipMasterError,), {"code": "MODEL_ERROR"})
    FileOperationError = type('FileOperationError', (ClipMasterError,), {"code": "FILE_NOT_FOUND"})


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("error_dashboard_example")


class ErrorGenerator:
    """错误生成器类
    
    用于生成各种类型的错误，以测试错误监控看板
    """
    
    def __init__(self):
        """初始化错误生成器"""
        self.components = [
            "model_loader", "srt_parser", "video_processor", 
            "audio_processor", "exporter", "file_manager",
            "scheduler", "network", "ui", "database"
        ]
        
        self.phases = [
            "initialization", "loading", "processing", 
            "exporting", "saving", "validation",
            "rendering", "encoding", "decoding", "cleanup"
        ]
        
        self.error_types = [
            (ModelCorruptionError, "模型文件损坏", {"component": "model_loader", "phase": "loading", "critical": True}),
            (MemoryOverflowError, "内存不足", {"component": "video_processor", "phase": "processing"}),
            (UserInputError, "无效的用户输入参数", {"component": "ui", "phase": "validation", "field": "resolution"}),
            (ResourceError, "资源访问错误", {"component": "file_manager", "phase": "loading", "resource_type": "disk"}),
            (VideoProcessError, "视频处理失败", {"component": "video_processor", "phase": "processing", "video_path": "test.mp4"}),
            (AudioProcessError, "音频处理失败", {"component": "audio_processor", "phase": "processing", "audio_path": "test.wav"}),
            (InvalidSRTError, "SRT格式错误", {"component": "srt_parser", "phase": "loading", "srt_path": "test.srt", "line_number": 42}),
            (ModelLoadError, "模型加载失败", {"component": "model_loader", "phase": "initialization", "model_name": "qwen2.5-7b-zh"}),
            (FileOperationError, "文件不存在", {"component": "file_manager", "phase": "loading", "file_path": "test.json"}),
            (ClipMasterError, "网络连接超时", {"component": "network", "phase": "downloading", "code": "NETWORK_ERROR"}),
            (ValueError, "参数值错误", {}),
            (TypeError, "参数类型错误", {}),
            (KeyError, "键不存在", {}),
            (IndexError, "索引越界", {}),
            (RuntimeError, "运行时错误", {})
        ]
    
    def generate_random_error(self):
        """生成随机错误
        
        Returns:
            Exception: 随机生成的错误对象
        """
        error_class, message, kwargs = random.choice(self.error_types)
        
        # 对于没有组件和阶段的通用异常，随机添加
        if "component" not in kwargs:
            kwargs["component"] = random.choice(self.components)
        if "phase" not in kwargs:
            kwargs["phase"] = random.choice(self.phases)
        
        # 创建自定义错误或标准异常
        if issubclass(error_class, ClipMasterError):
            return error_class(message, **kwargs)
        else:
            # 标准异常没有额外参数
            error = error_class(message)
            # 手动添加属性
            for key, value in kwargs.items():
                setattr(error, key, value)
            return error
    
    def generate_error_dict(self):
        """生成错误字典
        
        Returns:
            Dict[str, Any]: 表示错误的字典
        """
        error_class, message, kwargs = random.choice(self.error_types[:10])  # 只使用自定义错误
        
        # 构建错误字典
        error_dict = {
            "code": getattr(error_class, "code", error_class.__name__),
            "message": message,
            "component": kwargs.get("component", random.choice(self.components)),
            "phase": kwargs.get("phase", random.choice(self.phases)),
            "severity": random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"]),
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加其他属性
        for key, value in kwargs.items():
            if key not in ["component", "phase"]:
                error_dict[key] = value
        
        return error_dict
    
    def generate_specific_error(self, error_type):
        """生成特定类型的错误
        
        Args:
            error_type: 错误类型名称
        
        Returns:
            Exception: 生成的错误对象
        """
        # 查找匹配的错误类型
        for error_class, message, kwargs in self.error_types:
            if error_class.__name__ == error_type:
                if issubclass(error_class, ClipMasterError):
                    return error_class(message, **kwargs)
                else:
                    error = error_class(message)
                    for key, value in kwargs.items():
                        setattr(error, key, value)
                    return error
        
        # 未找到匹配的错误类型，返回通用错误
        return ClipMasterError(f"未知错误类型: {error_type}", code="GENERAL_ERROR")


def dashboard_callback(metrics):
    """错误监控看板回调函数
    
    当错误监控看板更新时调用
    
    Args:
        metrics: 指标数据
    """
    print("\n" + "="*50)
    print("错误监控看板更新")
    print("-"*50)
    print(f"总错误数: {metrics['total_errors']}")
    print(f"最近更新: {metrics['last_update']:.2f}秒前")
    
    if metrics['top_errors']:
        print("\n最常见错误:")
        for error, count in metrics['top_errors']:
            print(f"  {error}: {count}次")
    
    if metrics['top_components']:
        print("\n最常见错误组件:")
        for component, count in metrics['top_components']:
            print(f"  {component}: {count}次")
    
    print("\n错误类别分布:")
    for category, count in metrics['error_categories'].items():
        print(f"  {category}: {count}次")
    
    print("\n最近错误:")
    for error in metrics['recent_errors'][-3:]:
        print(f"  [{error['error_code']}] {error['message']} ({error['component']})")
    
    print("="*50)


def error_injection_thread(error_generator, monitor, duration=60, interval=2.0):
    """错误注入线程
    
    定期生成随机错误并更新错误监控看板
    
    Args:
        error_generator: 错误生成器
        monitor: 错误监控看板
        duration: 持续时间(秒)
        interval: 错误注入间隔(秒)
    """
    logger.info(f"开始错误注入线程，持续{duration}秒，间隔{interval}秒")
    
    end_time = time.time() + duration
    
    try:
        while time.time() < end_time:
            # 生成随机错误
            if random.random() < 0.7:
                # 70%概率使用错误对象
                error = error_generator.generate_random_error()
                error_type = error.__class__.__name__
            else:
                # 30%概率使用错误字典
                error = error_generator.generate_error_dict()
                error_type = error["code"]
            
            # 更新错误监控看板
            monitor.update_dashboard(error)
            
            logger.info(f"注入错误: {error_type}")
            
            # 等待间隔
            time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("错误注入线程被中断")
    except Exception as e:
        logger.error(f"错误注入线程出错: {e}")
    
    logger.info("错误注入线程结束")


def save_dashboard_stats(monitor, output_dir="logs"):
    """保存错误监控看板统计数据
    
    Args:
        monitor: 错误监控看板
        output_dir: 输出目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取仪表盘数据
    dashboard_data = monitor.get_dashboard_data()
    
    # 构建输出文件路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"error_stats_{timestamp}.json")
    
    # 保存为JSON文件
    with open(output_file, "w", encoding="utf-8") as f:
        # 处理不可序列化的对象
        serializable_data = {}
        for key, value in dashboard_data.items():
            # 转换元组列表等复杂类型
            if key in ["top_errors", "top_components"]:
                serializable_data[key] = [[str(item[0]), item[1]] for item in value]
            else:
                serializable_data[key] = value
        
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"已保存错误监控统计数据到: {output_file}")


def main():
    """主函数"""
    print("\n===== 错误监控看板示例 =====\n")
    
    # 获取错误监控看板实例
    monitor = get_error_monitor()
    
    # 注册回调函数
    monitor.register_callback(dashboard_callback)
    
    # 启动监控
    monitor.start_monitoring()
    print("已启动错误监控看板")
    
    # 创建错误生成器
    error_generator = ErrorGenerator()
    
    # 设置运行时间
    run_time = 30  # 30秒
    
    # 启动错误注入线程
    injection_thread = threading.Thread(
        target=error_injection_thread,
        args=(error_generator, monitor, run_time, 1.0)
    )
    injection_thread.daemon = True
    injection_thread.start()
    
    try:
        # 等待错误注入完成
        print(f"错误注入进行中，将持续{run_time}秒...")
        injection_thread.join()
        
        # 显示最终统计
        print("\n===== 错误监控统计 =====\n")
        stats = monitor.stop_monitoring()
        
        print(f"监控时长: {stats['duration']:.2f}秒")
        print(f"总错误数: {stats['total_errors']}")
        print(f"错误类型: {len(stats['error_types'])}种")
        print(f"错误类别: {len(stats['error_categories'])}个")
        
        # 保存统计数据
        save_dashboard_stats(monitor)
        
    except KeyboardInterrupt:
        print("\n用户中断，停止错误监控...")
        monitor.stop_monitoring()
    
    print("\n示例程序运行完成")


if __name__ == "__main__":
    main() 