#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时长分析器测试脚本

用于测试和验证视频时长分析功能。
"""

import os
import sys
import logging
import argparse
from typing import Dict, List, Any

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("duration_analyzer_test")

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timecode.base_analyzer import BaseAnalyzer, analyze_source_duration


def test_duration_analysis(video_path: str, verbose: bool = False) -> None:
    """测试视频时长分析
    
    Args:
        video_path: 视频文件路径
        verbose: 是否显示详细信息
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"测试视频时长分析: {video_path}")
    
    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        return
    
    # 使用便利函数
    try:
        logger.info("使用便利函数测试...")
        duration = analyze_source_duration(video_path)
        logger.info(f"视频时长: {duration:.3f}秒")
    except Exception as e:
        logger.error(f"便利函数分析失败: {str(e)}")
    
    # 使用基础分析器
    try:
        logger.info("\n使用BaseAnalyzer测试...")
        analyzer = BaseAnalyzer()
        
        # 测试时长分析
        duration = analyzer.analyze_source_duration(video_path)
        logger.info(f"分析器计算的视频时长: {duration:.3f}秒")
        
        # 获取并显示元数据
        if verbose:
            logger.info("\n获取视频元数据...")
            metadata = analyzer.get_video_metadata(video_path)
            
            logger.info("\n-- 基本信息 --")
            logger.info(f"时长: {metadata.get('duration', 'N/A')}秒")
            logger.info(f"分辨率: {metadata.get('width', 'N/A')}x{metadata.get('height', 'N/A')}")
            logger.info(f"帧率: {metadata.get('fps', 'N/A')}fps")
            logger.info(f"格式: {metadata.get('format_name', 'N/A')}")
            logger.info(f"编解码器: {metadata.get('codec', 'N/A')}")
            logger.info(f"比特率: {metadata.get('bit_rate', 'N/A')}bit/s")
            
            # 如果有OpenCV数据，对比时长差异
            if 'cv2' in metadata and 'duration' in metadata['cv2']:
                cv_duration = metadata['cv2']['duration']
                ff_duration = metadata.get('duration', 0)
                logger.info(f"\nOpenCV时长: {cv_duration:.3f}秒")
                logger.info(f"FFprobe时长: {ff_duration:.3f}秒")
                logger.info(f"差异: {abs(cv_duration - ff_duration):.3f}秒")
        
        # 与FFprobe命令直接对比
        try:
            import subprocess
            logger.info("\n与FFprobe命令行直接对比...")
            result = subprocess.run([
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                ffprobe_duration = float(result.stdout.strip())
                logger.info(f"FFprobe命令行: {ffprobe_duration:.3f}秒")
                logger.info(f"分析器结果: {duration:.3f}秒")
                logger.info(f"差异: {abs(duration - ffprobe_duration):.3f}秒")
                
                # 验证与标准工具的差异是否在可接受范围内
                if abs(duration - ffprobe_duration) <= 0.003:  # 3毫秒以内的误差
                    logger.info("✓ 验证通过: 结果与FFprobe命令行输出一致")
                else:
                    logger.warning("⚠ 验证注意: 结果与FFprobe命令行输出存在差异")
            else:
                logger.error(f"FFprobe命令执行失败: {result.stderr}")
        except Exception as e:
            logger.error(f"FFprobe命令行对比失败: {str(e)}")
    
    except Exception as e:
        logger.error(f"分析器测试失败: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视频时长分析测试")
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    args = parser.parse_args()
    
    test_duration_analysis(args.video_path, args.verbose)


if __name__ == "__main__":
    main() 