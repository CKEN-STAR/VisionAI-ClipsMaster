#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 多语言声明生成器演示程序

此脚本演示如何使用多语言声明生成器的各种功能，包括：
1. 生成不同语言的声明文本
2. 针对不同场景生成声明文本
3. 生成不同格式的声明
4. 使用变量替换功能
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from src.export.legal_generator import LegalGenerator, generate_full_disclaimer
    from src.utils.log_handler import get_logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

# 配置日志
logger = get_logger("demo_legal_generator")


def demo_basic_usage():
    """演示基本的声明生成功能"""
    print("\n===== 基本声明生成 =====")
    
    # 创建生成器实例
    generator = LegalGenerator()
    
    # 生成中文声明
    zh_disclaimer = generator.generate_full_disclaimer("zh")
    print(f"中文声明:\n{zh_disclaimer}")
    
    # 生成英文声明
    en_disclaimer = generator.generate_full_disclaimer("en")
    print(f"\nEnglish disclaimer:\n{en_disclaimer}")
    
    # 使用辅助函数生成声明
    simple_disclaimer = generate_full_disclaimer("zh")
    print(f"\n使用辅助函数生成声明:\n{simple_disclaimer}")


def demo_special_cases():
    """演示针对特殊场景的声明生成"""
    print("\n===== 特殊场景的声明生成 =====")
    
    generator = LegalGenerator()
    
    # 默认场景
    default_disclaimer = generator.generate_full_disclaimer("zh")
    print(f"默认场景声明:\n{default_disclaimer}")
    
    # 商业场景
    commercial_disclaimer = generator.generate_full_disclaimer("zh", "commercial")
    print(f"\n商业场景声明:\n{commercial_disclaimer}")
    
    # 教育场景
    educational_disclaimer = generator.generate_full_disclaimer("zh", "educational")
    print(f"\n教育场景声明:\n{educational_disclaimer}")


def demo_variable_substitution():
    """演示变量替换功能"""
    print("\n===== 变量替换功能 =====")
    
    generator = LegalGenerator()
    
    # 准备不同的变量集
    variables1 = {
        "app_name": "ClipsMaster Pro",
        "current_year": "2023",
        "app_version": "2.1.0"
    }
    
    variables2 = {
        "app_name": "VisionAI Enterprise",
        "current_year": "2024",
        "app_version": "3.0.0"
    }
    
    # 生成带变量替换的声明
    disclaimer1 = generator.generate_full_disclaimer("zh", variables=variables1)
    print(f"变量集1的声明:\n{disclaimer1}")
    
    disclaimer2 = generator.generate_full_disclaimer("zh", variables=variables2)
    print(f"\n变量集2的声明:\n{disclaimer2}")
    
    # 在不同场景中使用变量
    commercial = generator.generate_full_disclaimer("zh", "commercial", variables1)
    print(f"\n商业场景中的变量替换:\n{commercial}")
    
    educational = generator.generate_full_disclaimer("zh", "educational", variables2)
    print(f"\n教育场景中的变量替换:\n{educational}")


def demo_different_formats():
    """演示生成不同格式的声明"""
    print("\n===== 不同格式的声明 =====")
    
    generator = LegalGenerator()
    
    # 文档头部
    document_header = generator.generate_document_header("zh")
    print(f"文档头部:\n{document_header}")
    
    # HTML页脚
    html_footer = generator.generate_html_footer("zh")
    print(f"\nHTML页脚:\n{html_footer}")
    
    # SRT字幕
    srt_disclaimer = generator.generate_srt_disclaimer("zh", 5.0)
    print(f"\nSRT字幕:\n{srt_disclaimer}")
    
    # XML元数据
    xml_metadata = generator.generate_xml_metadata("zh", xml_format="premiere")
    print(f"\nXML元数据 (Premiere):\n{xml_metadata}")
    
    fcpxml_metadata = generator.generate_xml_metadata("zh", xml_format="fcpxml")
    print(f"\nXML元数据 (FCPXML):\n{fcpxml_metadata}")


def demo_watermark_config():
    """演示生成水印配置"""
    print("\n===== 水印配置生成 =====")
    
    generator = LegalGenerator()
    
    # 生成水印配置
    watermark_config = generator.generate_watermark_config("zh")
    print(f"水印配置:\n{json.dumps(watermark_config, ensure_ascii=False, indent=2)}")


def demo_audio_metadata():
    """演示生成音频元数据"""
    print("\n===== 音频元数据生成 =====")
    
    generator = LegalGenerator()
    
    # 生成MP3元数据
    mp3_metadata = generator.generate_audio_disclaimer("zh", "mp3")
    print(f"MP3元数据:\n{json.dumps(mp3_metadata, ensure_ascii=False, indent=2)}")
    
    # 生成WAV元数据
    wav_metadata = generator.generate_audio_disclaimer("zh", "wav")
    print(f"\nWAV元数据:\n{json.dumps(wav_metadata, ensure_ascii=False, indent=2)}")


def demo_get_all_texts():
    """演示获取所有法律文本"""
    print("\n===== 获取所有法律文本 =====")
    
    generator = LegalGenerator()
    
    # 获取中文法律文本
    zh_texts = generator.get_all_legal_texts("zh")
    print("中文法律文本:")
    for text_type, text in zh_texts.items():
        print(f"  {text_type}: {text}")
    
    # 获取英文法律文本
    en_texts = generator.get_all_legal_texts("en")
    print("\nEnglish legal texts:")
    for text_type, text in en_texts.items():
        print(f"  {text_type}: {text}")
    
    # 获取商业场景法律文本
    commercial_texts = generator.get_all_legal_texts("zh", "commercial")
    print("\n商业场景法律文本:")
    for text_type, text in commercial_texts.items():
        print(f"  {text_type}: {text}")


def demo_integration_example():
    """演示在实际场景中的集成应用"""
    print("\n===== 实际场景集成应用 =====")
    
    generator = LegalGenerator()
    
    def export_video(title: str, author: str, is_commercial: bool = False):
        """模拟视频导出流程"""
        # 确定语言和场景
        lang = "zh"  # 可以根据用户设置动态选择
        case = "commercial" if is_commercial else None
        
        # 准备变量
        variables = {
            "app_name": "VisionAI-ClipsMaster",
            "current_year": "2023",
            "title": title,
            "author": author
        }
        
        # 生成声明文本
        disclaimer = generator.generate_full_disclaimer(lang, case, variables)
        
        # 生成XML元数据
        xml_metadata = generator.generate_xml_metadata(lang, case, "premiere")
        
        # 生成水印配置
        watermark_config = generator.generate_watermark_config(lang)
        
        # 生成SRT字幕
        srt_disclaimer = generator.generate_srt_disclaimer(lang, 5.0)
        
        # 构建导出数据
        export_data = {
            "title": title,
            "author": author,
            "is_commercial": is_commercial,
            "disclaimer": disclaimer,
            "xml_metadata": xml_metadata,
            "watermark": watermark_config,
            "srt_disclaimer": srt_disclaimer,
            "export_time": "2023-05-05 15:30:00"
        }
        
        return export_data
    
    # 模拟非商业视频导出
    non_commercial_export = export_video("AI演示视频", "测试用户")
    print("非商业视频导出数据:")
    print(json.dumps(non_commercial_export, ensure_ascii=False, indent=2))
    
    # 模拟商业视频导出
    commercial_export = export_video("企业宣传片", "企业用户", True)
    print("\n商业视频导出数据:")
    print(json.dumps(commercial_export, ensure_ascii=False, indent=2))


def main():
    """主函数"""
    print("===== VisionAI-ClipsMaster 多语言声明生成器演示 =====")
    
    # 运行各个演示函数
    demo_basic_usage()
    demo_special_cases()
    demo_variable_substitution()
    demo_different_formats()
    demo_watermark_config()
    demo_audio_metadata()
    demo_get_all_texts()
    demo_integration_example()
    
    print("\n演示完成!")


if __name__ == "__main__":
    main() 