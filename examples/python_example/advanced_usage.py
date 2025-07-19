"""
VisionAI-ClipsMaster 高级用法示例

本示例展示了 VisionAI-ClipsMaster 的一些高级功能，包括：
- 多格式字幕解析
- 内存优化
- 自定义处理流程
- 批量处理
- 并行处理
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.srt_parser import parse_subtitle, auto_detect_parse_srt, is_valid_srt
from src.utils.memory_manager import MemoryManager
from src.utils.error_handler import ErrorHandler

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')


def ensure_output_dir():
    """确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")


def multi_format_subtitle_demo():
    """多格式字幕解析演示"""
    test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    
    # SRT格式字幕解析
    srt_file = os.path.join(test_dir, 'sample.srt')
    if not os.path.exists(srt_file):
        logger.warning(f"示例文件 {srt_file} 不存在，跳过SRT解析演示")
    else:
        logger.info("解析SRT格式字幕文件...")
        try:
            # 自动检测编码
            subtitles = auto_detect_parse_srt(srt_file)
            logger.info(f"成功解析字幕，共 {len(subtitles)} 条字幕条目")
            
            # 显示部分字幕内容
            for subtitle in subtitles[:3]:  # 只显示前3条
                logger.info(f"ID: {subtitle['id']}, 时间: {subtitle['start_time']:.2f}s - {subtitle['end_time']:.2f}s")
                logger.info(f"内容: {subtitle['text']}")
                logger.info("-" * 40)
        except Exception as e:
            logger.error(f"解析SRT文件时出错: {str(e)}")
    
    # 通用字幕解析（支持多种格式）
    logger.info("\n使用通用字幕解析器（可处理多种格式）...")
    try:
        # 此函数会自动检测格式并选择合适的解析器
        subtitles = parse_subtitle(srt_file, auto_detect_format=True)
        logger.info(f"成功解析字幕，使用通用解析器，共 {len(subtitles)} 条字幕条目")
    except Exception as e:
        logger.error(f"使用通用解析器时出错: {str(e)}")
    
    # 验证字幕文件格式
    logger.info("\n验证字幕文件格式...")
    if is_valid_srt(srt_file):
        logger.info(f"{srt_file} 是有效的SRT格式")
    else:
        logger.info(f"{srt_file} 不是有效的SRT格式")
    
    # 尝试无效文件
    invalid_file = os.path.join(test_dir, 'non_existent.srt')
    if not is_valid_srt(invalid_file):
        logger.info(f"{invalid_file} 不是有效的SRT格式或文件不存在")


def memory_optimization_demo():
    """内存优化演示"""
    logger.info("\n内存优化演示...")
    
    memory_manager = MemoryManager()
    memory_manager.monitor_start()
    
    # 模拟大量字幕处理
    large_subtitles = []
    for i in range(1000):
        large_subtitles.append({
            "id": i,
            "start_time": i * 5.0,
            "end_time": i * 5.0 + 4.5,
            "duration": 4.5,
            "text": f"这是第 {i} 条测试字幕，用于内存测试。" * 20  # 创建大量文本以消耗内存
        })
    
    # 显示内存使用情况
    memory_usage = memory_manager.get_memory_usage()
    logger.info(f"当前内存使用: {memory_usage['used_mb']:.2f} MB, 可用: {memory_usage['available_mb']:.2f} MB")
    
    # 清理内存
    large_subtitles = None
    memory_manager.optimize_memory()
    
    # 再次显示内存使用情况
    memory_usage = memory_manager.get_memory_usage()
    logger.info(f"优化后内存使用: {memory_usage['used_mb']:.2f} MB, 可用: {memory_usage['available_mb']:.2f} MB")
    
    memory_manager.monitor_stop()


def error_handling_demo():
    """错误处理演示"""
    logger.info("\n错误处理演示...")
    
    error_handler = ErrorHandler()
    
    # 生成无效的SRT内容
    invalid_content = """这不是一个有效的SRT格式。
    缺少时间戳和索引号。"""
    
    # 使用错误处理器捕获并处理异常
    with error_handler.capture("字幕解析"):
        from src.parsers.srt_decoder import SRTDecoder
        decoder = SRTDecoder()
        decoder.parse(invalid_content)
    
    # 检查是否发生了错误
    if error_handler.has_errors():
        errors = error_handler.get_errors()
        logger.info(f"共捕获到 {len(errors)} 个错误:")
        for i, error in enumerate(errors):
            logger.info(f"错误 {i+1}: {error['message']} ({error['exception_type']})")
    
    # 清除错误
    error_handler.clear_errors()


def main():
    """主函数"""
    logger.info("VisionAI-ClipsMaster 高级用法示例")
    logger.info("=" * 60)
    
    # 确保输出目录存在
    ensure_output_dir()
    
    # 多格式字幕解析演示
    multi_format_subtitle_demo()
    
    # 内存优化演示
    memory_optimization_demo()
    
    # 错误处理演示
    error_handling_demo()
    
    logger.info("\n演示完成!")


if __name__ == "__main__":
    main() 