#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
元数据驱动剪辑引擎示例脚本

演示如何使用元数据驱动剪辑引擎进行视频剪辑操作
展示元数据剪辑描述的创建、处理和管理
"""

import os
import sys
import time
import tempfile
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.log_handler import get_logger
from src.exporters.metaclip_engine import (
    MetaClip,
    MetaClipEngine,
    MetaClipProcessor,
    OperationType,
    CodecMode,
    generate_metadata_clip,
    get_metaclip_engine
)
from src.exporters.ffmpeg_zerocopy import (
    create_ffmpeg_pipeline, 
    FFmpegSettings, 
    FFmpegCodec, 
    FFmpegPreset
)

# 配置日志记录器
logger = get_logger("metaclip_demo")


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


def demo_basic_slice():
    """演示基本切片功能"""
    logger.info("=== 演示基本切片功能 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "metaclip_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_input.mp4")
    if not create_demo_video(input_video, duration=30):
        logger.error("无法创建演示视频，跳过切片演示")
        return
    
    # 输出文件路径
    output_video = os.path.join(temp_dir, "demo_slice.mp4")
    
    # 创建元数据剪辑描述
    meta_clip = generate_metadata_clip(
        src=input_video,
        in_point=5.0,
        out_point=15.0,
        operation=OperationType.SLICE.value,
        codec=CodecMode.COPY.value,
        output=output_video
    )
    
    # 创建元数据驱动剪辑引擎
    engine = get_metaclip_engine()
    
    try:
        # 开始计时
        start_time = time.time()
        
        # 处理剪辑
        result = engine.process(meta_clip)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 输出结果
        logger.info(f"切片处理结果: {json.dumps(result, indent=2)}")
        logger.info(f"处理时间: {process_time:.4f}秒")
        
        # 检查输出文件
        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            logger.info(f"输出文件大小: {file_size:.2f} MB")
        else:
            logger.warning(f"未找到输出文件: {output_video}")
    
    except Exception as e:
        logger.error(f"切片处理失败: {e}")
    
    finally:
        # 清理资源
        engine.cleanup()


def demo_concat():
    """演示视频连接功能"""
    logger.info("=== 演示视频连接功能 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "metaclip_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建多个演示视频片段
    video_paths = []
    for i in range(3):
        video_path = os.path.join(temp_dir, f"segment_{i}.mp4")
        if create_demo_video(video_path, duration=5):
            video_paths.append(video_path)
    
    if len(video_paths) < 2:
        logger.error("无法创建足够的演示视频片段，跳过连接演示")
        return
    
    # 输出文件路径
    output_video = os.path.join(temp_dir, "demo_concat.mp4")
    
    # 创建元数据剪辑描述
    meta_clip = generate_metadata_clip(
        src=video_paths,
        in_point=None,
        out_point=None,
        operation=OperationType.CONCAT.value,
        codec=CodecMode.COPY.value,
        output=output_video
    )
    
    # 创建元数据驱动剪辑引擎
    engine = get_metaclip_engine()
    
    try:
        # 开始计时
        start_time = time.time()
        
        # 处理剪辑
        result = engine.process(meta_clip)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 输出结果
        logger.info(f"连接处理结果: {json.dumps(result, indent=2)}")
        logger.info(f"处理时间: {process_time:.4f}秒")
        
        # 检查输出文件
        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            logger.info(f"输出文件大小: {file_size:.2f} MB")
        else:
            logger.warning(f"未找到输出文件: {output_video}")
    
    except Exception as e:
        logger.error(f"连接处理失败: {e}")
    
    finally:
        # 清理资源
        engine.cleanup()


def demo_nested_operations():
    """演示嵌套操作功能"""
    logger.info("=== 演示嵌套操作功能 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "metaclip_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_nested.mp4")
    if not create_demo_video(input_video, duration=30):
        logger.error("无法创建演示视频，跳过嵌套操作演示")
        return
    
    # 输出文件路径
    temp_output1 = os.path.join(temp_dir, "temp_slice1.mp4")
    temp_output2 = os.path.join(temp_dir, "temp_slice2.mp4")
    final_output = os.path.join(temp_dir, "demo_nested_result.mp4")
    
    # 创建父操作（连接）
    parent_clip = MetaClip(
        operation=OperationType.CONCAT.value,
        src=[temp_output1, temp_output2],
        codec=CodecMode.COPY.value,
        params={"output": final_output}
    )
    
    # 添加子操作（切片）
    child_clip1 = MetaClip(
        operation=OperationType.SLICE.value,
        src=input_video,
        in_point=5.0,
        out_point=10.0,
        codec=CodecMode.COPY.value,
        params={"output": temp_output1}
    )
    
    child_clip2 = MetaClip(
        operation=OperationType.SLICE.value,
        src=input_video,
        in_point=15.0,
        out_point=20.0,
        codec=CodecMode.COPY.value,
        params={"output": temp_output2}
    )
    
    # 将子操作添加到父操作
    parent_clip.add_child(child_clip1)
    parent_clip.add_child(child_clip2)
    
    # 创建元数据驱动剪辑引擎
    engine = get_metaclip_engine()
    
    try:
        # 开始计时
        start_time = time.time()
        
        # 处理嵌套操作
        result = engine.process(parent_clip)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 输出结果
        logger.info(f"嵌套操作处理结果: {json.dumps(result, indent=2)}")
        logger.info(f"处理时间: {process_time:.4f}秒")
        
        # 检查输出文件
        if os.path.exists(final_output):
            file_size = os.path.getsize(final_output) / (1024 * 1024)
            logger.info(f"最终输出文件大小: {file_size:.2f} MB")
        else:
            logger.warning(f"未找到最终输出文件: {final_output}")
    
    except Exception as e:
        logger.error(f"嵌套操作处理失败: {e}")
    
    finally:
        # 清理资源
        engine.cleanup()


def demo_batch_processing():
    """演示批量处理功能"""
    logger.info("=== 演示批量处理功能 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "metaclip_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_batch.mp4")
    if not create_demo_video(input_video, duration=60):
        logger.error("无法创建演示视频，跳过批量处理演示")
        return
    
    # 创建多个元数据剪辑描述
    meta_clips = []
    for i in range(5):
        output_path = os.path.join(temp_dir, f"batch_slice_{i}.mp4")
        start_time = i * 10
        end_time = start_time + 5
        
        meta_clip = generate_metadata_clip(
            src=input_video,
            in_point=start_time,
            out_point=end_time,
            operation=OperationType.SLICE.value,
            codec=CodecMode.COPY.value,
            output=output_path
        )
        meta_clips.append(meta_clip)
    
    # 创建元数据驱动剪辑引擎
    engine = get_metaclip_engine()
    
    try:
        # 开始计时
        start_time = time.time()
        
        # 批量处理
        results = engine.batch_process(meta_clips)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 输出结果
        logger.info(f"批量处理结果: {len(results)} 个操作完成")
        logger.info(f"总处理时间: {process_time:.4f}秒")
        logger.info(f"平均每个操作时间: {process_time/len(results):.4f}秒")
        
        # 检查输出文件
        total_size = 0
        successful_files = 0
        for i, result in enumerate(results):
            output_path = os.path.join(temp_dir, f"batch_slice_{i}.mp4")
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                total_size += file_size
                successful_files += 1
                logger.info(f"输出文件 {i+1}: {file_size:.2f} MB")
        
        logger.info(f"成功生成文件数: {successful_files}/{len(results)}")
        logger.info(f"总输出大小: {total_size:.2f} MB")
    
    except Exception as e:
        logger.error(f"批量处理失败: {e}")
    
    finally:
        # 清理资源
        engine.cleanup()


def demo_json_serialization():
    """演示JSON序列化功能"""
    logger.info("=== 演示JSON序列化功能 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "metaclip_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # JSON文件路径
    json_path = os.path.join(temp_dir, "metaclip_demo.json")
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_json.mp4")
    if not create_demo_video(input_video, duration=30):
        logger.error("无法创建演示视频，跳过JSON序列化演示")
        return
    
    # 创建元数据剪辑描述
    meta_clips = [
        generate_metadata_clip(
            src=input_video,
            in_point=5.0,
            out_point=10.0,
            operation=OperationType.SLICE.value,
            codec=CodecMode.COPY.value,
            output=os.path.join(temp_dir, "json_slice1.mp4")
        ),
        generate_metadata_clip(
            src=input_video,
            in_point=15.0,
            out_point=20.0,
            operation=OperationType.SLICE.value,
            codec=CodecMode.COPY.value,
            output=os.path.join(temp_dir, "json_slice2.mp4")
        )
    ]
    
    # 创建元数据驱动剪辑引擎
    engine = get_metaclip_engine()
    
    try:
        # 保存到JSON文件
        success = engine.save_to_json(meta_clips, json_path)
        
        if not success:
            logger.error("保存到JSON文件失败")
            return
        
        # 从JSON文件加载
        loaded_clips = engine.load_from_json(json_path)
        
        logger.info(f"成功从JSON加载 {len(loaded_clips)} 个元数据剪辑描述")
        
        # 显示加载的剪辑描述
        for i, clip in enumerate(loaded_clips):
            logger.info(f"剪辑描述 {i+1}: {clip}")
        
        # 使用加载的剪辑描述进行处理
        logger.info("使用加载的剪辑描述进行处理...")
        results = engine.batch_process(loaded_clips)
        
        logger.info(f"处理完成，成功处理 {sum(1 for r in results if r.get('status') == 'success')} 个操作")
    
    except Exception as e:
        logger.error(f"JSON序列化演示失败: {e}")
    
    finally:
        # 清理资源
        engine.cleanup()


def demo_ffmpeg_integration():
    """演示与FFmpeg零拷贝集成功能"""
    logger.info("=== 演示与FFmpeg零拷贝集成功能 ===")
    
    # 创建临时目录
    temp_dir = os.path.join(tempfile.gettempdir(), "metaclip_demo")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建演示视频
    input_video = os.path.join(temp_dir, "demo_ffmpeg.mp4")
    if not create_demo_video(input_video, duration=30):
        logger.error("无法创建演示视频，跳过FFmpeg集成演示")
        return
    
    # 输出文件路径
    output_video = os.path.join(temp_dir, "ffmpeg_integration.mp4")
    
    # 创建自定义处理器，集成FFmpeg零拷贝
    class FFmpegSliceProcessor(MetaClipProcessor):
        """FFmpeg切片处理器"""
        
        def __init__(self):
            """初始化FFmpeg切片处理器"""
            super().__init__("FFmpegSliceProcessor")
        
        def process(self, meta_clip: MetaClip) -> Dict[str, Any]:
            """处理使用FFmpeg切片
            
            Args:
                meta_clip: 元数据剪辑描述
                
            Returns:
                Dict[str, Any]: 处理结果
            """
            # 验证操作类型
            if meta_clip.operation != OperationType.SLICE.value:
                raise ValueError(f"操作类型不匹配: 预期 {OperationType.SLICE.value}, 实际 {meta_clip.operation}")
            
            # 验证参数
            if meta_clip.in_point is None or meta_clip.out_point is None:
                raise ValueError("切片操作需要设置in_point和out_point参数")
            
            # 计算持续时间
            duration = meta_clip.out_point - meta_clip.in_point
            
            # 获取输出路径
            output_path = meta_clip.params.get("output", "")
            if not output_path:
                raise ValueError("未指定输出路径")
            
            # 创建FFmpeg设置
            settings = FFmpegSettings(
                video_codec=FFmpegCodec.H264,
                preset=FFmpegPreset.FAST,
                crf=23
            )
            
            # 创建FFmpeg零拷贝管道
            try:
                # 开始计时
                start_time = time.time()
                
                # 创建管道
                pipeline = create_ffmpeg_pipeline()
                pipeline.set_settings(settings)
                
                # 执行切片
                pipeline.cut_video(
                    input_path=meta_clip.src,
                    output_path=output_path,
                    start_time=meta_clip.in_point,
                    duration=duration
                )
                
                # 计算处理时间
                process_time = time.time() - start_time
                
                # 返回结果
                return {
                    "status": "success",
                    "operation": meta_clip.operation,
                    "src": meta_clip.src,
                    "in_point": meta_clip.in_point,
                    "out_point": meta_clip.out_point,
                    "duration": duration,
                    "output": output_path,
                    "process_time": process_time
                }
                
            except Exception as e:
                logger.error(f"FFmpeg处理失败: {str(e)}")
                return {
                    "status": "error",
                    "operation": meta_clip.operation,
                    "error": str(e)
                }
    
    # 创建元数据剪辑描述
    meta_clip = generate_metadata_clip(
        src=input_video,
        in_point=5.0,
        out_point=15.0,
        operation=OperationType.SLICE.value,
        codec=CodecMode.COPY.value,
        output=output_video
    )
    
    # 创建元数据驱动剪辑引擎
    engine = get_metaclip_engine()
    
    try:
        # 注册自定义FFmpeg处理器
        engine.processors[OperationType.SLICE.value] = FFmpegSliceProcessor()
        
        # 开始计时
        start_time = time.time()
        
        # 处理剪辑
        result = engine.process(meta_clip)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 输出结果
        logger.info(f"FFmpeg集成处理结果: {json.dumps(result, indent=2)}")
        logger.info(f"总处理时间: {process_time:.4f}秒")
        
        # 检查输出文件
        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            logger.info(f"输出文件大小: {file_size:.2f} MB")
        else:
            logger.warning(f"未找到输出文件: {output_video}")
    
    except Exception as e:
        logger.error(f"FFmpeg集成演示失败: {e}")
    
    finally:
        # 清理资源
        engine.cleanup()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="元数据驱动剪辑引擎示例")
    parser.add_argument("--demo", choices=["all", "slice", "concat", "nested", "batch", "json", "ffmpeg"],
                      default="all", help="要运行的演示")
    args = parser.parse_args()
    
    logger.info("=== 元数据驱动剪辑引擎演示开始 ===")
    
    # 根据参数选择要运行的演示
    if args.demo in ["all", "slice"]:
        demo_basic_slice()
    
    if args.demo in ["all", "concat"]:
        demo_concat()
    
    if args.demo in ["all", "nested"]:
        demo_nested_operations()
    
    if args.demo in ["all", "batch"]:
        demo_batch_processing()
    
    if args.demo in ["all", "json"]:
        demo_json_serialization()
    
    if args.demo in ["all", "ffmpeg"]:
        demo_ffmpeg_integration()
    
    logger.info("=== 元数据驱动剪辑引擎演示结束 ===")


if __name__ == "__main__":
    main() 