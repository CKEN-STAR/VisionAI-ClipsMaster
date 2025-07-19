#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
断点续导出示例

演示如何使用断点续导出功能，包括：
1. 基本使用方法
2. 进度回调处理
3. 异常恢复
4. 与导出器集成
"""

import os
import sys
import time
import random
import signal
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from src.exporters.resume_export import (
    get_export_resumer,
    make_resumable,
    resumable_export_context
)
from src.export.jianying_exporter import JianyingExporter
from src.export.premiere_exporter import PremiereXMLExporter
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("resume_export_example")


def progress_callback(progress: float) -> None:
    """进度回调函数
    
    Args:
        progress: 当前进度(0-1.0)
    """
    # 显示进度条
    width = 50
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percent = int(progress * 100)
    
    print(f"\r导出进度: [{bar}] {percent}% ", end="", flush=True)
    
    if progress >= 1.0:
        print("\n导出完成!")


def create_mock_version() -> Dict[str, Any]:
    """创建模拟版本数据
    
    Returns:
        Dict[str, Any]: 模拟版本数据
    """
    # 创建测试场景
    scenes = []
    total_scenes = 10
    
    for i in range(total_scenes):
        scene = {
            "scene_id": f"scene_{i+1}",
            "text": f"这是第{i+1}个场景的文本内容",
            "start_time": i * 5.0,
            "duration": 5.0,
            "has_audio": True
        }
        scenes.append(scene)
    
    # 创建版本数据
    version = {
        "version_id": "test_version_001",
        "project_name": "断点续传测试项目",
        "scenes": scenes,
        "video_path": "path/to/video.mp4",  # 模拟路径
        "created_at": "2023-05-15 10:30:00"
    }
    
    return version


def simulate_export_with_progress(version: Dict[str, Any], output_path: str) -> None:
    """模拟带进度的导出过程
    
    Args:
        version: 版本数据
        output_path: 输出路径
    """
    logger.info(f"开始导出到: {output_path}")
    
    # 使用导出续传上下文
    with resumable_export_context() as resumer:
        # 获取起始进度
        start_progress = resumer.progress
        logger.info(f"从进度 {start_progress:.2%} 开始导出")
        
        # 模拟导出过程
        total_steps = 20
        completed_steps = int(total_steps * start_progress)
        
        for step in range(completed_steps, total_steps):
            # 计算当前进度
            current_progress = (step + 1) / total_steps
            
            # 更新和显示进度
            resumer.save_state(current_progress)
            progress_callback(current_progress)
            
            # 模拟耗时操作
            time.sleep(0.5)
            
            # 有10%的概率模拟中断
            if random.random() < 0.1 and step < total_steps - 1:
                logger.warning("模拟导出中断!")
                raise KeyboardInterrupt("模拟中断")
    
    # 导出完成，写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"导出完成的数据: {version['version_id']}\n")
        f.write(f"包含 {len(version['scenes'])} 个场景\n")
    
    logger.info(f"导出成功: {output_path}")


def example_basic_usage():
    """基本使用示例"""
    print("\n=== 基本断点续导出示例 ===")
    
    # 创建测试数据
    version = create_mock_version()
    output_path = "test_export_output.txt"
    
    try:
        # 执行导出
        simulate_export_with_progress(version, output_path)
    except KeyboardInterrupt:
        print("\n导出被中断，可以稍后恢复")
    
    # 如果导出中断，模拟稍后恢复
    if get_export_resumer().progress < 1.0:
        print("\n5秒后尝试恢复导出...")
        time.sleep(5)
        
        try:
            # 重新尝试导出，会从上次中断点继续
            simulate_export_with_progress(version, output_path)
        except Exception as e:
            print(f"\n再次中断: {str(e)}")


def example_with_real_exporter():
    """与真实导出器集成示例"""
    print("\n=== 与导出器集成示例 ===")
    
    # 创建测试数据
    version = create_mock_version()
    output_path = "test_export_project.json"
    
    # 创建剪映导出器
    exporter = JianyingExporter()
    
    # 转换为可恢复导出器
    resumable_exporter = make_resumable(exporter)
    
    try:
        # 执行可恢复导出
        result = resumable_exporter.export(
            version, 
            output_path, 
            progress_callback=progress_callback
        )
        print(f"\n导出成功: {result}")
    except Exception as e:
        print(f"\n导出失败: {str(e)}")


def example_handle_interruption():
    """处理中断示例"""
    print("\n=== 中断处理示例 ===")
    
    # 创建测试数据
    version = create_mock_version()
    output_path = "test_export_interrupted.txt"
    
    # 设置信号处理
    def signal_handler(sig, frame):
        print("\n收到中断信号，正在优雅退出...")
        # 不立即退出，让上下文管理器有机会保存状态
        raise KeyboardInterrupt("用户中断")
    
    # 注册信号处理
    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("按Ctrl+C可中断导出...")
        # 使用导出续传上下文
        with resumable_export_context() as resumer:
            # 模拟长时间导出过程
            total_steps = 50
            completed_steps = int(total_steps * resumer.progress)
            
            for step in range(completed_steps, total_steps):
                # 计算当前进度
                current_progress = (step + 1) / total_steps
                
                # 更新和显示进度
                resumer.save_state(current_progress)
                progress_callback(current_progress)
                
                # 模拟耗时操作
                time.sleep(0.3)
    except KeyboardInterrupt:
        print("\n导出已暂停，您可以稍后继续")
        
        # 显示恢复指令
        current_progress = get_export_resumer().progress
        if current_progress > 0:
            print(f"当前进度: {current_progress:.2%}")
            print("可以稍后运行相同命令继续导出")
    finally:
        # 恢复原始信号处理
        signal.signal(signal.SIGINT, original_handler)


def run_all_examples():
    """运行所有示例"""
    print("=== 断点续导出示例 ===\n")
    
    # 清理之前的状态文件
    resumer = get_export_resumer()
    resumer.clear_state()
    
    try:
        example_basic_usage()
        
        # 清理状态，为下一个示例准备
        resumer.clear_state()
        
        example_with_real_exporter()
        
        # 清理状态，为下一个示例准备
        resumer.clear_state()
        
        example_handle_interruption()
    finally:
        # 确保清理状态
        resumer.clear_state()
    
    print("\n=== 示例结束 ===")


if __name__ == "__main__":
    run_all_examples() 