"""
VisionAI-ClipsMaster 基本用法示例

本示例展示了 VisionAI-ClipsMaster 的基本用法，包括：
- 解析SRT字幕文件
- 简单的文本处理
- 生成剪辑提示
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.srt_parser import parse_srt, auto_detect_parse_srt

# 设置输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')


def ensure_output_dir():
    """确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")


def parse_subtitle_example():
    """解析字幕文件示例"""
    print("\n=== SRT字幕解析示例 ===")
    
    # 示例SRT文件路径
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    srt_file = os.path.join(test_data_dir, 'sample.srt')
    
    if not os.path.exists(srt_file):
        print(f"示例文件 {srt_file} 不存在!")
        return False
    
    try:
        # 解析SRT文件
        print(f"解析SRT文件: {srt_file}")
        subtitles = auto_detect_parse_srt(srt_file)
        
        print(f"成功解析字幕，共 {len(subtitles)} 条字幕条目")
        
        # 打印前几条字幕
        for i, subtitle in enumerate(subtitles[:3]):
            print(f"\n字幕 #{subtitle['id']}:")
            print(f"时间: {subtitle['start_time']:.2f}s - {subtitle['end_time']:.2f}s")
            print(f"内容: {subtitle['text']}")
            
            # 计算每条字幕的停留时间（持续时间）
            duration = subtitle['duration']
            print(f"持续时间: {duration:.2f}s")
            
            # 字幕密度计算（字符数/秒）
            char_count = len(subtitle['text'])
            density = char_count / duration if duration > 0 else 0
            print(f"字幕密度: {density:.2f} 字符/秒")
        
        # 保存解析后的数据（示例）
        output_file = os.path.join(OUTPUT_DIR, 'parsed_subtitles.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            for subtitle in subtitles:
                f.write(f"{subtitle['id']} | {subtitle['start_time']:.2f}-{subtitle['end_time']:.2f} | {subtitle['text']}\n")
        
        print(f"\n解析结果已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"解析SRT文件时出错: {str(e)}")
        return False


def main():
    """主函数"""
    print("VisionAI-ClipsMaster 基本用法示例")
    print("=" * 60)
    
    # 确保输出目录存在
    ensure_output_dir()
    
    # 运行字幕解析示例
    if parse_subtitle_example():
        print("✓ 字幕解析示例成功运行")
    else:
        print("✗ 字幕解析示例运行失败")
    
    print("\n示例运行完成! 请查看生成的文件。")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    main() 