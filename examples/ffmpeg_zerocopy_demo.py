#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FFmpeg零拷贝集成示例脚本

演示如何使用FFmpeg零拷贝集成进行高效视频处理
展示各种常见视频处理操作，包括剪切、连接、转码等
"""

import os
import sys
import time
import tempfile
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.log_handler import get_logger
from src.exporters.ffmpeg_zerocopy import (
    ZeroCopyFFmpegPipeline,
    StreamingFFmpegPipeline,
    FFmpegSettings,
    FFmpegCodec,
    FFmpegPreset,
    FFmpegProcessor,
    VideoCutProcessor,
    VideoConcatProcessor,
    create_ffmpeg_pipeline,
    create_streaming_ffmpeg_pipeline,
    cut_video,
    concat_videos
)

# 配置日志记录器
logger = get_logger("ffmpeg_zerocopy_demo")


def create_demo_video(output_path: str, duration: int = 10, resolution: str = "720x480") -> str:
    """创建演示视频
    
    Args:
        output_path: 输出路径
        duration: 视频时长(秒)
        resolution: 分辨率
        
    Returns:
        创建的视频路径
    """
    logger.info(f"创建演示视频: {output_path}, 时长: {duration}秒, 分辨率: {resolution}")
    
    try:
        import subprocess
        
        # 检查FFmpeg是否可用
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("未检测到FFmpeg，请确保已安装FFmpeg并添加到PATH中")
            return ""
        
        # 构建命令: 创建彩色测试图案视频
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"testsrc=duration={duration}:size={resolution}:rate=24",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"创建演示视频失败: {result.stderr}")
            return ""
        
        logger.info(f"成功创建演示视频: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"创建演示视频时发生异常: {e}")
        return ""


def demo_basic_cutting():
    """演示基本视频剪切功能"""
    logger.info("=== 演示基本视频剪切 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "ffmpeg_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_input.mp4")
    if not create_demo_video(input_video, duration=30):
        logger.error("无法创建演示视频，跳过剪切演示")
        return
    
    # 输出文件路径
    output_video = os.path.join(temp_dir, "demo_cut.mp4")
    
    # 创建FFmpeg零拷贝管道
    pipeline = create_ffmpeg_pipeline()
    
    # 设置处理参数
    settings = FFmpegSettings(
        video_codec=FFmpegCodec.H264,
        preset=FFmpegPreset.VERYFAST,
        crf=23
    )
    pipeline.set_settings(settings)
    
    try:
        # 开始计时
        start_time = time.time()
        
        # 剪切视频（截取5-15秒部分）
        result = pipeline.cut_video(
            input_path=input_video,
            output_path=output_video,
            start_time=5.0,
            duration=10.0
        )
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        logger.info(f"视频剪切完成: {result}")
        logger.info(f"处理时间: {process_time:.4f}秒")
        
        # 显示输出文件信息
        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            logger.info(f"输出文件大小: {file_size:.2f} MB")
    
    except Exception as e:
        logger.error(f"视频剪切失败: {e}")
    
    finally:
        # 清理管道资源
        pipeline.cleanup()


def demo_video_concat():
    """演示视频连接功能"""
    logger.info("=== 演示视频连接 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "ffmpeg_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建多个演示视频片段
    video_paths: List[str] = []
    for i in range(3):
        video_path = os.path.join(temp_dir, f"segment_{i}.mp4")
        if create_demo_video(video_path, duration=5):
            video_paths.append(video_path)
    
    if len(video_paths) < 2:
        logger.error("无法创建足够的演示视频片段，跳过连接演示")
        return
    
    # 输出文件路径
    output_video = os.path.join(temp_dir, "demo_concat.mp4")
    
    # 创建FFmpeg零拷贝管道
    pipeline = create_ffmpeg_pipeline()
    
    try:
        # 开始计时
        start_time = time.time()
        
        # 连接视频
        result = pipeline.concat_videos(
            input_files=video_paths,
            output_path=output_video
        )
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        logger.info(f"视频连接完成: {result}")
        logger.info(f"处理时间: {process_time:.4f}秒")
        
        # 显示输出文件信息
        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            logger.info(f"输出文件大小: {file_size:.2f} MB")
    
    except Exception as e:
        logger.error(f"视频连接失败: {e}")
    
    finally:
        # 清理管道资源
        pipeline.cleanup()


def demo_streaming_pipeline():
    """演示流式处理管道"""
    logger.info("=== 演示流式处理管道 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "ffmpeg_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_long.mp4")
    if not create_demo_video(input_video, duration=60):
        logger.error("无法创建演示视频，跳过流式处理演示")
        return
    
    # 创建输出目录
    output_dir = os.path.join(temp_dir, "segments")
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建流式处理管道
    pipeline = create_streaming_ffmpeg_pipeline(chunk_size=10)  # 每次处理10秒
    
    # 模拟分段处理
    def segment_generator():
        """生成输入和输出路径对"""
        total_segments = 6  # 共60秒，每段10秒
        for i in range(total_segments):
            # 为每个片段创建一个独立的输出文件
            output_path = os.path.join(output_dir, f"segment_{i}.mp4")
            # 生成处理参数
            start_time = i * 10
            yield (input_video, output_path, start_time, 10.0)
    
    try:
        # 创建自定义处理器
        class SegmentCutProcessor(FFmpegProcessor):
            """片段剪切处理器"""
            
            def process(self, data):
                input_path, output_path, start_time, duration = data
                
                # 创建剪切处理器
                cutter = VideoCutProcessor(
                    start_time=start_time,
                    duration=duration
                )
                
                # 执行剪切
                return cutter.process((input_path, output_path))
        
        # 添加处理器
        pipeline.add_stage(SegmentCutProcessor())
        
        # 开始计时
        start_time = time.time()
        
        # 执行流式处理
        results = list(pipeline.process_stream(segment_generator()))
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        logger.info(f"流式处理完成，共处理 {len(results)} 个片段")
        logger.info(f"总处理时间: {process_time:.4f}秒")
        logger.info(f"平均每段处理时间: {process_time/len(results):.4f}秒")
        
        # 统计输出文件大小
        total_size = 0
        for result_path in results:
            if os.path.exists(result_path):
                total_size += os.path.getsize(result_path)
        
        logger.info(f"总输出大小: {total_size/(1024*1024):.2f} MB")
    
    except Exception as e:
        logger.error(f"流式处理失败: {e}")
    
    finally:
        # 清理管道资源
        pipeline.cleanup()


def demo_factory_functions():
    """演示工厂函数用法"""
    logger.info("=== 演示工厂函数 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "ffmpeg_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_factory.mp4")
    if not create_demo_video(input_video, duration=20):
        logger.error("无法创建演示视频，跳过工厂函数演示")
        return
    
    # 输出文件路径
    output_video = os.path.join(temp_dir, "factory_output.mp4")
    
    try:
        # 开始计时
        start_time = time.time()
        
        # 使用工厂函数剪切视频
        settings = FFmpegSettings(
            video_codec=FFmpegCodec.H264,
            preset=FFmpegPreset.ULTRAFAST,  # 使用超快速预设
            crf=28  # 较低质量
        )
        
        result = cut_video(
            input_path=input_video,
            output_path=output_video,
            start_time=5.0,
            duration=10.0,
            settings=settings
        )
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        logger.info(f"工厂函数处理完成: {result}")
        logger.info(f"处理时间: {process_time:.4f}秒")
        
        # 显示输出文件信息
        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            logger.info(f"输出文件大小: {file_size:.2f} MB")
    
    except Exception as e:
        logger.error(f"工厂函数处理失败: {e}")


def demo_quality_comparison():
    """演示不同质量设置的比较"""
    logger.info("=== 演示质量设置比较 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "ffmpeg_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_quality.mp4")
    if not create_demo_video(input_video, duration=10):
        logger.error("无法创建演示视频，跳过质量比较演示")
        return
    
    # 定义不同的质量设置
    quality_settings = [
        ("high", FFmpegSettings(
            video_codec=FFmpegCodec.H264,
            preset=FFmpegPreset.SLOW,
            crf=18  # 高质量
        )),
        ("medium", FFmpegSettings(
            video_codec=FFmpegCodec.H264,
            preset=FFmpegPreset.MEDIUM,
            crf=23  # 中等质量
        )),
        ("low", FFmpegSettings(
            video_codec=FFmpegCodec.H264,
            preset=FFmpegPreset.VERYFAST,
            crf=28  # 低质量
        ))
    ]
    
    results = []
    
    # 测试每种质量设置
    for quality_name, settings in quality_settings:
        logger.info(f"测试 {quality_name} 质量设置...")
        
        # 输出文件路径
        output_video = os.path.join(temp_dir, f"quality_{quality_name}.mp4")
        
        # 创建管道
        pipeline = create_ffmpeg_pipeline()
        pipeline.set_settings(settings)
        
        try:
            # 开始计时
            start_time = time.time()
            
            # 处理视频
            pipeline.cut_video(
                input_path=input_video,
                output_path=output_video,
                start_time=0.0,
                duration=10.0
            )
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 获取文件大小
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            
            # 记录结果
            results.append({
                "quality": quality_name,
                "preset": settings.preset.value,
                "crf": settings.crf,
                "size_mb": file_size,
                "time_seconds": process_time
            })
            
            logger.info(f"{quality_name} 质量处理完成: 大小={file_size:.2f}MB, 时间={process_time:.4f}秒")
            
        except Exception as e:
            logger.error(f"{quality_name} 质量处理失败: {e}")
        
        finally:
            # 清理管道资源
            pipeline.cleanup()
    
    # 显示比较结果
    if results:
        logger.info("\n质量比较结果:")
        logger.info("=" * 70)
        logger.info(f"{'质量':^10}{'预设':^15}{'CRF':^8}{'大小(MB)':^15}{'耗时(秒)':^15}")
        logger.info("-" * 70)
        
        for result in results:
            logger.info(f"{result['quality']:^10}{result['preset']:^15}{result['crf']:^8}"
                        f"{result['size_mb']:^15.2f}{result['time_seconds']:^15.2f}")
        
        logger.info("=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FFmpeg零拷贝集成示例")
    parser.add_argument("--demo", choices=["all", "cut", "concat", "stream", "factory", "quality"],
                       default="all", help="要运行的演示")
    args = parser.parse_args()
    
    logger.info("=== FFmpeg零拷贝集成演示开始 ===")
    
    # 根据参数选择要运行的演示
    if args.demo in ["all", "cut"]:
        demo_basic_cutting()
    
    if args.demo in ["all", "concat"]:
        demo_video_concat()
    
    if args.demo in ["all", "stream"]:
        demo_streaming_pipeline()
    
    if args.demo in ["all", "factory"]:
        demo_factory_functions()
    
    if args.demo in ["all", "quality"]:
        demo_quality_comparison()
    
    logger.info("=== FFmpeg零拷贝集成演示结束 ===")


if __name__ == "__main__":
    main() 