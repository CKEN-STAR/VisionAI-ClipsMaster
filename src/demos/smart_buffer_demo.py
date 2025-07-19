#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能缓冲区演示

演示如何使用SmartBuffer类高效处理视频和图像数据，
展示零拷贝操作、内存映射和缓冲区管理功能。
"""

import os
import time
import numpy as np
import cv2
from pathlib import Path

from src.utils.smart_buffer import SmartBuffer, BufferStrategy, BufferAccessMode
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("smart_buffer_demo")

def main():
    """智能缓冲区演示主函数"""
    logger.info("=== 智能缓冲区演示开始 ===")
    
    # 创建智能缓冲区实例
    buffer = SmartBuffer(
        name="DemoBuffer", 
        capacity=1024 * 1024 * 1024,  # 1GB容量
        strategy=BufferStrategy.LRU,  # 最近最少使用策略
        enable_mmap=True
    )
    
    # 演示1: 基本分配和访问
    demo_basic_operations(buffer)
    
    # 演示2: 视频处理
    demo_video_processing(buffer)
    
    # 演示3: 大数据集处理
    demo_large_dataset(buffer)
    
    # 演示4: 零拷贝操作
    demo_zero_copy(buffer)
    
    # 显示最终统计信息
    stats = buffer.get_stats()
    logger.info("=== 缓冲区性能统计 ===")
    for key, value in stats.items():
        if key.endswith('size') or key.endswith('_size'):
            logger.info(f"{key}: {value/1024/1024:.2f} MB")
        elif key.endswith('percent') or key.endswith('ratio'):
            logger.info(f"{key}: {value:.2f}%")
        else:
            logger.info(f"{key}: {value}")
    
    # 清理缓冲区
    buffer.clear()
    logger.info("=== 智能缓冲区演示结束 ===")


def demo_basic_operations(buffer):
    """演示基本的缓冲区操作"""
    logger.info("\n--- 演示1: 基本缓冲区操作 ---")
    
    # 分配数组
    array1 = buffer.allocate("demo.array1", (1000, 1000), np.float32)
    logger.info(f"分配数组1: 形状={array1.shape}, 类型={array1.dtype}")
    
    # 填充数据
    array1.fill(1.0)
    logger.info("数组1已填充数据")
    
    # 获取数组
    retrieved = buffer.get("demo.array1")
    logger.info(f"检索数组1: 平均值={np.mean(retrieved)}")
    
    # 存入新数据
    new_array = np.random.rand(500, 500).astype(np.float32)
    buffer.put("demo.array2", new_array)
    logger.info(f"存入数组2: 形状={new_array.shape}")
    
    # 检查存在性和字典式访问
    logger.info(f"数组1在缓冲区中: {'demo.array1' in buffer}")
    logger.info(f"数组3在缓冲区中: {'demo.array3' in buffer}")
    
    # 字典式访问
    try:
        value = buffer["demo.array1"]
        logger.info(f"字典式访问数组1: 形状={value.shape}")
    except Exception as e:
        logger.error(f"访问错误: {e}")
    
    # 释放缓冲区
    buffer.release("demo.array1")
    logger.info("数组1已释放")
    logger.info(f"数组1在缓冲区中: {'demo.array1' in buffer}")


def demo_video_processing(buffer):
    """演示视频处理"""
    logger.info("\n--- 演示2: 视频处理 ---")
    
    # 创建示例视频文件
    video_path = create_sample_video()
    
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("无法打开视频文件")
        return
    
    # 获取视频信息
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    logger.info(f"视频信息: {width}x{height}, {frame_count}帧, {fps}FPS")
    
    # 尝试使用内存映射
    try:
        logger.info("尝试使用内存映射读取视频...")
        start_time = time.time()
        video_data = buffer.map_file(video_path)
        logger.info(f"映射视频完成, 耗时: {time.time() - start_time:.4f}秒")
    except Exception as e:
        logger.warning(f"内存映射失败: {e}, 将采用传统方法")
        video_data = None
    
    # 如果映射失败，使用传统方法读取
    if video_data is None:
        # 分配帧缓冲区
        logger.info("使用传统方法分配帧缓冲区...")
        frames_buffer = buffer.allocate(
            "video.frames", 
            (frame_count, height, width, 3), 
            np.uint8
        )
        
        # 读取所有帧
        start_time = time.time()
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frames_buffer[frame_idx] = frame
            frame_idx += 1
        
        logger.info(f"读取{frame_idx}帧完成, 耗时: {time.time() - start_time:.4f}秒")
    
    cap.release()
    
    # 清理临时文件
    if os.path.exists(video_path):
        os.remove(video_path)


def demo_large_dataset(buffer):
    """演示大数据集处理"""
    logger.info("\n--- 演示3: 大数据集处理 ---")
    
    # 模拟大数据集
    data_size = (1000, 1000, 3)  # 约3MB
    chunks = 10
    
    logger.info(f"创建大数据集: {chunks}个{data_size}的块")
    
    # 分配各个块
    for i in range(chunks):
        chunk_key = f"dataset.chunk{i}"
        chunk = buffer.allocate(chunk_key, data_size, np.float32)
        
        # 填充随机数据
        chunk.fill(i * 0.1)
        
        logger.info(f"块{i}已分配和填充")
    
    # 模拟数据处理
    logger.info("模拟数据处理...")
    start_time = time.time()
    
    for i in range(chunks):
        chunk_key = f"dataset.chunk{i}"
        chunk = buffer.get(chunk_key)
        
        # 处理数据 (简单操作)
        processed = np.sqrt(chunk) + 5
        
        # 存回结果
        result_key = f"dataset.result{i}"
        buffer.put(result_key, processed)
    
    logger.info(f"处理完成, 耗时: {time.time() - start_time:.4f}秒")
    
    # 释放原始块，只保留结果
    for i in range(chunks):
        buffer.release(f"dataset.chunk{i}")
    
    logger.info("已释放原始数据块，保留处理结果")


def demo_zero_copy(buffer):
    """演示零拷贝操作"""
    logger.info("\n--- 演示4: 零拷贝操作 ---")
    
    # 创建源数据
    source_data = np.ones((2000, 2000), dtype=np.float32)
    source_data *= 3.0
    
    # 存入缓冲区
    buffer.put("zerocopy.source", source_data)
    logger.info("源数据已存入缓冲区")
    
    # 使用视图进行零拷贝操作
    start_time = time.time()
    
    # 创建区域视图
    region = (slice(500, 1500), slice(500, 1500))
    view = buffer.view("zerocopy.source", region)
    
    logger.info(f"创建视图: 形状={view.shape}, 内存地址={hex(view.__array_interface__['data'][0])}")
    logger.info(f"原始数据地址={hex(buffer.get('zerocopy.source').__array_interface__['data'][0])}")
    
    # 视图操作
    original_sum = np.sum(view)
    view += 1.0  # 修改视图也会修改原始数据
    new_sum = np.sum(buffer.view("zerocopy.source", region))
    
    logger.info(f"视图操作前后和: {original_sum} -> {new_sum}")
    logger.info(f"零拷贝操作耗时: {time.time() - start_time:.6f}秒")
    
    # 复制操作
    buffer.copy("zerocopy.source", "zerocopy.dest", region)
    logger.info("使用copy()在缓冲区间复制数据")
    
    # 验证复制结果
    dest_view = buffer.get("zerocopy.dest")
    logger.info(f"目标数据: 形状={dest_view.shape}, 和={np.sum(dest_view)}")


def create_sample_video(duration=3, size=(640, 480), fps=30):
    """创建示例视频文件用于测试
    
    Args:
        duration: 视频时长(秒)
        size: 视频尺寸(宽,高)
        fps: 帧率
        
    Returns:
        str: 视频文件路径
    """
    # 创建临时目录
    temp_dir = Path("./temp")
    temp_dir.mkdir(exist_ok=True)
    
    # 视频文件路径
    video_path = str(temp_dir / "sample_video.mp4")
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, size)
    
    if not out.isOpened():
        logger.error("无法创建视频文件")
        return None
    
    # 生成帧
    total_frames = duration * fps
    for i in range(total_frames):
        # 创建颜色渐变帧
        frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        
        # 添加一些动态效果
        progress = i / total_frames
        radius = int(min(size) / 3 * (0.5 + 0.5 * np.sin(progress * 6.28)))
        center = (int(size[0] / 2), int(size[1] / 2))
        color = (
            int(255 * np.sin(progress * 6.28)), 
            int(255 * np.cos(progress * 3.14)), 
            int(255 * (0.5 + 0.5 * np.sin(progress * 9.42)))
        )
        
        # 绘制圆形
        cv2.circle(frame, center, radius, color, -1)
        
        # 添加文本
        text = f"Frame: {i}/{total_frames}"
        cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # 写入帧
        out.write(frame)
    
    # 释放资源
    out.release()
    
    logger.info(f"示例视频已创建: {video_path} ({duration}秒, {size[0]}x{size[1]}, {fps}FPS)")
    return video_path


if __name__ == "__main__":
    main() 