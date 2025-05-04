#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时间轴精密校验器使用示例

演示如何使用时间轴精密校验器验证字幕与视频的同步精度
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.quality import FrameExactValidator, OCRSubtitleValidator
from src.utils.logger import get_module_logger

# 设置日志
logger = get_module_logger("timecode_validator_example")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="时间轴精密校验器使用示例")
    
    parser.add_argument(
        "--video",
        type=str,
        help="要验证的视频文件路径"
    )
    
    parser.add_argument(
        "--srt",
        type=str,
        help="字幕文件路径"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["basic", "ocr"],
        default="basic",
        help="验证模式: basic(基本检测) 或 ocr(文本识别)"
    )
    
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.5,
        help="容忍的帧数误差，默认0.5帧"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="检测阈值，默认0.7"
    )
    
    parser.add_argument(
        "--batch-file",
        type=str,
        help="批量验证文件列表（CSV格式，每行:字幕路径,视频路径）"
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.batch_file and (not args.video or not args.srt):
        parser.error("必须指定 --video 和 --srt 参数，或者使用 --batch-file 参数")
    
    return args


def validate_single(video_path, srt_path, mode="basic", tolerance=0.5, threshold=0.7):
    """验证单个视频与字幕的同步性
    
    Args:
        video_path: 视频文件路径
        srt_path: 字幕文件路径
        mode: 验证模式，basic或ocr
        tolerance: 容忍的帧数误差
        threshold: 检测阈值
    
    Returns:
        bool: 验证是否通过
    """
    logger.info(f"开始验证视频与字幕同步: {os.path.basename(video_path)}")
    logger.info(f"使用模式: {mode}, 容忍误差: {tolerance}帧, 阈值: {threshold}")
    
    # 创建验证器
    if mode == "ocr":
        validator = OCRSubtitleValidator(tolerance_frames=tolerance, ocr_threshold=threshold)
        logger.info("使用OCR字幕验证器（需要pytesseract库支持）")
    else:
        validator = FrameExactValidator(tolerance_frames=tolerance, ocr_threshold=threshold)
        logger.info("使用基本帧检测验证器")
    
    # 执行验证
    start_time = __import__('time').time()
    result = validator.validate(srt_path, video_path)
    elapsed_time = __import__('time').time() - start_time
    
    # 获取详细结果
    details = validator.get_last_results()
    
    # 打印结果
    print("\n===== 验证结果 =====")
    print(f"视频文件: {os.path.basename(video_path)}")
    print(f"字幕文件: {os.path.basename(srt_path)}")
    print(f"验证状态: {'通过 ✓' if result else '失败 ✗'}")
    if details:
        print(f"字幕总数: {details.get('total_subtitles', 0)}")
        print(f"验证通过: {details.get('valid_subtitles', 0)}")
        print(f"通过率: {details.get('pass_rate', 0):.2%}")
        print(f"容忍误差: {details.get('tolerance_ms', 0):.2f}ms")
        print(f"视频帧率: {details.get('video_fps', 0):.2f}fps")
    print(f"验证耗时: {elapsed_time:.2f}秒")
    
    return result


def validate_batch(batch_file, mode="basic", tolerance=0.5, threshold=0.7):
    """批量验证多个视频与字幕的同步性
    
    Args:
        batch_file: CSV文件路径，包含待验证的字幕和视频对
        mode: 验证模式，basic或ocr
        tolerance: 容忍的帧数误差
        threshold: 检测阈值
    
    Returns:
        Dict[str, bool]: 文件名到验证结果的映射
    """
    logger.info(f"开始批量验证，从文件: {batch_file}")
    logger.info(f"使用模式: {mode}, 容忍误差: {tolerance}帧, 阈值: {threshold}")
    
    # 读取批量文件
    pairs = []
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) >= 2:
                    srt = parts[0].strip()
                    video = parts[1].strip()
                    pairs.append((srt, video))
    except Exception as e:
        logger.error(f"读取批量文件失败: {str(e)}")
        return {}
    
    if not pairs:
        logger.warning("批量文件中未找到有效的验证对")
        return {}
    
    logger.info(f"找到 {len(pairs)} 个待验证的对")
    
    # 创建验证器
    if mode == "ocr":
        validator = OCRSubtitleValidator(tolerance_frames=tolerance, ocr_threshold=threshold)
    else:
        validator = FrameExactValidator(tolerance_frames=tolerance, ocr_threshold=threshold)
    
    # 执行验证
    start_time = __import__('time').time()
    results = validator.validate_batch(pairs)
    elapsed_time = __import__('time').time() - start_time
    
    # 打印结果
    print("\n===== 批量验证结果 =====")
    print(f"验证对总数: {len(pairs)}")
    print(f"通过数量: {sum(1 for r in results.values() if r)}")
    print(f"通过率: {sum(1 for r in results.values() if r) / len(results) if results else 0:.2%}")
    print(f"总耗时: {elapsed_time:.2f}秒")
    print("\n详细结果:")
    
    for video_name, passed in results.items():
        print(f"{video_name}: {'通过 ✓' if passed else '失败 ✗'}")
    
    return results


def main():
    """主函数"""
    args = parse_arguments()
    
    # 单个验证
    if args.video and args.srt:
        validate_single(
            args.video,
            args.srt,
            args.mode,
            args.tolerance,
            args.threshold
        )
    
    # 批量验证
    elif args.batch_file:
        validate_batch(
            args.batch_file,
            args.mode,
            args.tolerance,
            args.threshold
        )


if __name__ == "__main__":
    main() 