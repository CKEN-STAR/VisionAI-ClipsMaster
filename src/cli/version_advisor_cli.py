#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本建议命令行工具

提供命令行接口，根据视频规格建议最适合的ClipsMaster版本。
"""

import os
import sys
import json
import argparse
import textwrap
from typing import Dict, Any, List, Optional

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.ui.version_advisor import (
        suggest_version_with_reason,
        get_version_features
    )
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

# ANSI颜色代码
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

def print_color(text, color="", bold=False):
    """打印彩色文本"""
    prefix = BOLD if bold else ""
    print(f"{prefix}{color}{text}{RESET}")

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print_color(f"  {text}  ", BLUE, bold=True)
    print("=" * 60)

def print_section(text):
    """打印章节标题"""
    print("\n" + "-" * 40)
    print_color(f"  {text}  ", CYAN, bold=True)
    print("-" * 40)

def format_list(items, prefix="• "):
    """格式化列表"""
    return "\n".join(f"{prefix}{item}" for item in items)

def parse_resolution(value):
    """解析分辨率字符串"""
    if "x" in value.lower():
        parts = value.lower().split("x")
        if len(parts) >= 2:
            try:
                width = int(parts[0].strip())
                height = int(parts[1].strip())
                return [width, height]
            except ValueError:
                pass
    
    # 支持常见分辨率别名
    if value.lower() in ["720p", "hd"]:
        return [1280, 720]
    elif value.lower() in ["1080p", "fullhd", "fhd"]:
        return [1920, 1080]
    elif value.lower() in ["4k", "uhd"]:
        return [3840, 2160]
    
    # 如果无法解析，返回默认值
    print_color(f"警告: 无法解析分辨率 '{value}'，使用默认值 1920x1080", YELLOW)
    return [1920, 1080]

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="ClipsMaster 版本建议工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        示例:
          python version_advisor_cli.py -r 1920x1080 -e -m
          python version_advisor_cli.py -r 4k -h -e -a -m
          python version_advisor_cli.py -p pro
          python version_advisor_cli.py -f video_spec.json
        """)
    )
    
    # 添加参数
    parser.add_argument("-r", "--resolution", type=str, 
                      help="视频分辨率，格式为WIDTHxHEIGHT，或使用别名：720p, 1080p, 4k")
    parser.add_argument("-d", "--hdr", action="store_true", 
                      help="视频是否包含HDR内容")
    parser.add_argument("-e", "--effects", action="store_true", 
                      help="是否使用视频特效")
    parser.add_argument("-a", "--audio-effects", action="store_true", 
                      help="是否使用音频特效")
    parser.add_argument("-m", "--multi-track", action="store_true", 
                      help="是否使用多轨编辑")
    
    # 预设选项
    parser.add_argument("-p", "--preset", type=str, choices=["basic", "film", "pro"],
                      help="使用预设：basic(基础编辑), film(影视制作), pro(专业制作)")
    
    # 文件选项
    parser.add_argument("-f", "--file", type=str,
                      help="从JSON文件加载视频规格")
    parser.add_argument("-o", "--output", type=str,
                      help="将建议结果输出到文件")
    
    # 显示选项
    parser.add_argument("-v", "--verbose", action="store_true",
                      help="显示详细信息")
    parser.add_argument("-j", "--json", action="store_true",
                      help="以JSON格式输出结果")
    
    return parser.parse_args()

def get_spec_from_preset(preset):
    """根据预设获取视频规格"""
    if preset == "basic":
        return {
            "resolution": [1280, 720],
            "hdr": False,
            "effects": False,
            "audio_effects": False,
            "multi_track": False
        }
    elif preset == "film":
        return {
            "resolution": [1920, 1080],
            "hdr": False,
            "effects": True,
            "audio_effects": True,
            "multi_track": True
        }
    elif preset == "pro":
        return {
            "resolution": [3840, 2160],
            "hdr": True,
            "effects": True,
            "audio_effects": True,
            "multi_track": True
        }
    else:
        return {}

def get_spec_from_args(args):
    """从命令行参数获取视频规格"""
    # 从预设获取
    if args.preset:
        return get_spec_from_preset(args.preset)
    
    # 从文件获取
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print_color(f"错误: 无法加载文件 '{args.file}': {str(e)}", RED, bold=True)
            sys.exit(1)
    
    # 从参数获取
    spec = {
        "resolution": [1920, 1080],  # 默认分辨率
        "hdr": args.hdr,
        "effects": args.effects,
        "audio_effects": args.audio_effects,
        "multi_track": args.multi_track
    }
    
    # 解析分辨率
    if args.resolution:
        spec["resolution"] = parse_resolution(args.resolution)
    
    return spec

def print_spec_summary(spec):
    """打印视频规格摘要"""
    print_section("视频规格")
    
    # 分辨率
    resolution = spec.get("resolution", [1920, 1080])
    if isinstance(resolution, list) and len(resolution) >= 2:
        width, height = resolution[0], resolution[1]
        print(f"分辨率: {width} x {height}")
    
    # HDR
    hdr = spec.get("hdr", False)
    print(f"HDR: {'是' if hdr else '否'}")
    
    # 特效
    effects = spec.get("effects", False)
    print(f"视频特效: {'是' if effects else '否'}")
    
    # 音频特效
    audio_effects = spec.get("audio_effects", False)
    print(f"音频特效: {'是' if audio_effects else '否'}")
    
    # 多轨
    multi_track = spec.get("multi_track", False)
    print(f"多轨编辑: {'是' if multi_track else '否'}")

def print_version_recommendation(version, reasons, features):
    """打印版本建议"""
    print_section("版本建议")
    
    # 显示推荐版本
    print_color(f"推荐版本: {features['display_name']}", GREEN, bold=True)
    
    # 显示原因
    print("\n推荐原因:")
    print(format_list(reasons))
    
    # 显示版本功能
    print("\n版本功能:")
    
    feature_list = []
    
    # 添加分辨率
    max_width, max_height = features["max_resolution"]
    feature_list.append(f"最大分辨率: {max_width}x{max_height}")
    
    # 添加其他功能
    if features["supports_hdr"]:
        feature_list.append("支持HDR")
    
    if features["supports_nested_sequences"]:
        feature_list.append("支持嵌套序列")
    
    if features["supports_effects_layers"]:
        feature_list.append("支持效果层")
    
    if features["supports_keyframes"]:
        feature_list.append("支持关键帧")
    
    if features["supports_3d_effects"]:
        feature_list.append("支持3D效果")
    
    if features["supports_color_grading"]:
        feature_list.append("支持色彩分级")
    
    if features["supports_audio_effects"]:
        feature_list.append("支持音频效果")
    
    if features["supports_multi_track"]:
        feature_list.append("支持多轨道编辑")
    
    print(format_list(feature_list))

def generate_json_output(version, reasons, features, spec):
    """生成JSON输出"""
    output = {
        "input_spec": spec,
        "recommendation": {
            "version": version,
            "display_name": features["display_name"],
            "reasons": reasons,
            "features": {
                "max_resolution": features["max_resolution"],
                "supports_hdr": features["supports_hdr"],
                "supports_nested_sequences": features["supports_nested_sequences"],
                "supports_effects_layers": features["supports_effects_layers"],
                "supports_keyframes": features["supports_keyframes"],
                "supports_3d_effects": features["supports_3d_effects"],
                "supports_color_grading": features["supports_color_grading"],
                "supports_audio_effects": features["supports_audio_effects"],
                "supports_multi_track": features["supports_multi_track"]
            }
        }
    }
    
    return json.dumps(output, indent=2, ensure_ascii=False)

def main():
    """主函数"""
    args = parse_args()
    
    # 从参数获取视频规格
    spec = get_spec_from_args(args)
    
    # 获取版本建议
    version, reasons = suggest_version_with_reason(spec)
    features = get_version_features(version)
    
    # 处理输出
    if args.json:
        # JSON输出
        output = generate_json_output(version, reasons, features, spec)
        if args.output:
            # 输出到文件
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"结果已保存到文件: {args.output}")
            except Exception as e:
                print_color(f"错误: 无法写入文件 '{args.output}': {str(e)}", RED, bold=True)
                sys.exit(1)
        else:
            # 输出到控制台
            print(output)
    else:
        # 控制台输出
        print_header("ClipsMaster 版本建议")
        
        # 如果是详细模式，先打印规格摘要
        if args.verbose:
            print_spec_summary(spec)
        
        # 打印建议
        print_version_recommendation(version, reasons, features)
        
        # 如果需要输出到文件
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write("ClipsMaster 版本建议\n\n")
                    f.write(f"推荐版本: {features['display_name']}\n\n")
                    
                    f.write("推荐原因:\n")
                    for reason in reasons:
                        f.write(f"• {reason}\n")
                    
                    f.write("\n版本功能:\n")
                    
                    max_width, max_height = features["max_resolution"]
                    f.write(f"• 最大分辨率: {max_width}x{max_height}\n")
                    
                    if features["supports_hdr"]:
                        f.write("• 支持HDR\n")
                    
                    if features["supports_nested_sequences"]:
                        f.write("• 支持嵌套序列\n")
                    
                    if features["supports_effects_layers"]:
                        f.write("• 支持效果层\n")
                    
                    if features["supports_keyframes"]:
                        f.write("• 支持关键帧\n")
                    
                    if features["supports_3d_effects"]:
                        f.write("• 支持3D效果\n")
                    
                    if features["supports_color_grading"]:
                        f.write("• 支持色彩分级\n")
                    
                    if features["supports_audio_effects"]:
                        f.write("• 支持音频效果\n")
                    
                    if features["supports_multi_track"]:
                        f.write("• 支持多轨道编辑\n")
                
                print(f"\n结果已保存到文件: {args.output}")
            except Exception as e:
                print_color(f"错误: 无法写入文件 '{args.output}': {str(e)}", RED, bold=True)
                sys.exit(1)

if __name__ == "__main__":
    main() 