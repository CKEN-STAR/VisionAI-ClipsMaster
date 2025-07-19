#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态模板引擎演示程序

展示如何使用动态模板引擎根据不同版本生成适配的项目模板。
"""

import os
import sys
import argparse
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入动态模板引擎
try:
    from src.exporters.dynamic_template import create_template_engine
except ImportError as e:
    print(f"导入动态模板引擎出错: {e}")
    sys.exit(1)

def generate_template(version: str, output_format: str, output_file: str = None, params: Dict[str, Any] = None) -> None:
    """生成并输出模板"""
    if params is None:
        params = {}
        
    print(f"生成{output_format}模板 (版本 {version})...")
    
    # 创建模板引擎
    engine = create_template_engine(version)
    
    # 准备默认参数
    default_params = {
        "title": "示例项目",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "video_tracks": 2,
        "audio_tracks": 2,
        "use_nested": True,
        "nested_name": "场景1"
    }
    
    # 合并参数
    template_params = {**default_params, **params}
    
    # 生成模板
    template = engine.generate_template(output_format, template_params)
    
    if not template:
        print(f"生成{output_format}模板失败!")
        return
        
    # 输出模板
    if output_file:
        # 确保目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(template)
            
        print(f"模板已保存到: {output_file}")
    else:
        # 打印到控制台
        print("\n生成的模板:")
        print("-" * 60)
        print(template)
        print("-" * 60)

def list_supported_features(version: str) -> None:
    """列出指定版本支持的特性"""
    print(f"版本 {version} 支持的特性:")
    
    # 创建模板引擎
    engine = create_template_engine(version)
    
    # 检查常见特性
    features = [
        ("multi_track", "多轨道"),
        ("single_track", "单轨道"),
        ("subtitle_track", "字幕轨"),
        ("effects_layer", "效果层"),
        ("nested_sequences", "嵌套序列"),
        ("audio_effects", "音频特效"),
        ("advanced_effects", "高级效果"),
        ("keyframe_animation", "关键帧动画"),
        ("motion_tracking", "运动跟踪")
    ]
    
    # 打印支持的特性
    for feature_id, feature_name in features:
        status = "支持" if engine.is_feature_supported(feature_id) else "不支持"
        print(f"- {feature_name}: {status}")
    
    # 打印分辨率
    max_width, max_height = engine.get_max_resolution()
    print(f"最大分辨率: {max_width}x{max_height}")
    
    # 检查效果支持
    effects = ["blur", "color", "transform", "audio", "transition", "text", "3d"]
    
    print("\n支持的效果:")
    for effect in effects:
        if engine.is_effect_supported(effect):
            print(f"- {effect}")

def compare_versions(versions: List[str]) -> None:
    """比较多个版本的特性支持情况"""
    if len(versions) < 2:
        print("需要至少两个版本进行比较!")
        return
        
    print(f"比较版本: {', '.join(versions)}")
    
    # 创建各版本的模板引擎
    engines = {v: create_template_engine(v) for v in versions}
    
    # 检查常见特性
    features = [
        ("multi_track", "多轨道"),
        ("single_track", "单轨道"),
        ("subtitle_track", "字幕轨"),
        ("effects_layer", "效果层"),
        ("nested_sequences", "嵌套序列"),
        ("audio_effects", "音频特效"),
        ("advanced_effects", "高级效果"),
        ("keyframe_animation", "关键帧动画"),
        ("motion_tracking", "运动跟踪")
    ]
    
    # 打印表头
    header = "特性".ljust(20)
    for v in versions:
        header += f" | {v.ljust(7)}"
    print(header)
    print("-" * (20 + 10 * len(versions)))
    
    # 打印特性支持情况
    for feature_id, feature_name in features:
        row = feature_name.ljust(20)
        for v in versions:
            engine = engines[v]
            status = "√" if engine.is_feature_supported(feature_id) else "×"
            row += f" | {status.center(7)}"
        print(row)
    
    # 打印分辨率
    row = "最大分辨率".ljust(20)
    for v in versions:
        engine = engines[v]
        max_width, max_height = engine.get_max_resolution()
        row += f" | {f'{max_width}x{max_height}'.center(7)}"
    print(row)

def batch_generate(version: str, output_dir: str, formats: List[str] = None) -> None:
    """批量生成各种格式的模板"""
    if formats is None:
        formats = ['xml', 'json', 'text']
        
    print(f"批量生成{version}版本的模板到目录: {output_dir}")
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 准备参数
    params = {
        "title": "批量生成示例",
        "width": 3840,
        "height": 2160,
        "fps": 29.97,
        "video_tracks": 3,
        "audio_tracks": 2,
        "use_nested": True
    }
    
    # 生成各种格式的模板
    for fmt in formats:
        output_file = os.path.join(output_dir, f"template_v{version}.{fmt}")
        generate_template(version, fmt, output_file, params)

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="动态模板引擎演示程序")
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 生成模板命令
    gen_parser = subparsers.add_parser("generate", help="生成模板")
    gen_parser.add_argument("version", help="目标版本号")
    gen_parser.add_argument("--format", "-f", choices=['xml', 'json', 'text'], default='xml', help="输出格式")
    gen_parser.add_argument("--output", "-o", help="输出文件路径")
    gen_parser.add_argument("--title", help="项目标题")
    gen_parser.add_argument("--width", type=int, help="视频宽度")
    gen_parser.add_argument("--height", type=int, help="视频高度")
    gen_parser.add_argument("--fps", type=float, help="帧率")
    gen_parser.add_argument("--video-tracks", type=int, help="视频轨道数")
    gen_parser.add_argument("--audio-tracks", type=int, help="音频轨道数")
    gen_parser.add_argument("--no-nested", action="store_true", help="禁用嵌套序列")
    
    # 列出特性命令
    features_parser = subparsers.add_parser("features", help="列出支持的特性")
    features_parser.add_argument("version", help="目标版本号")
    
    # 比较版本命令
    compare_parser = subparsers.add_parser("compare", help="比较版本")
    compare_parser.add_argument("versions", nargs="+", help="要比较的版本号列表")
    
    # 批量生成命令
    batch_parser = subparsers.add_parser("batch", help="批量生成模板")
    batch_parser.add_argument("version", help="目标版本号")
    batch_parser.add_argument("--output-dir", "-o", required=True, help="输出目录")
    batch_parser.add_argument("--formats", "-f", nargs="+", choices=['xml', 'json', 'text'], help="输出格式列表")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 执行相应的命令
    if args.command == "generate":
        # 收集参数
        params = {}
        if args.title:
            params["title"] = args.title
        if args.width:
            params["width"] = args.width
        if args.height:
            params["height"] = args.height
        if args.fps:
            params["fps"] = args.fps
        if args.video_tracks:
            params["video_tracks"] = args.video_tracks
        if args.audio_tracks:
            params["audio_tracks"] = args.audio_tracks
        if args.no_nested:
            params["use_nested"] = False
            
        generate_template(args.version, args.format, args.output, params)
    elif args.command == "features":
        list_supported_features(args.version)
    elif args.command == "compare":
        compare_versions(args.versions)
    elif args.command == "batch":
        batch_generate(args.version, args.output_dir, args.formats)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"出错: {str(e)}")
        sys.exit(1) 