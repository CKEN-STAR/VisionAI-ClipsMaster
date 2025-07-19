#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 法律文本加载器演示程序

此脚本演示如何使用法律文本加载器功能，包括:
1. 加载不同语言的法律文本
2. 特殊场景法律文本处理
3. 格式设置获取
4. 变量替换与自定义
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from src.utils.legal_text_loader import LegalTextLoader, load_legal_text
    from src.utils.log_handler import get_logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

# 配置日志
logger = get_logger("demo_legal_text")


def demo_basic_usage():
    """演示基本的法律文本加载功能"""
    print("\n===== 基本法律文本加载 =====")
    
    # 加载默认语言的法律文本
    copyright_text = load_legal_text("copyright")
    disclaimer_text = load_legal_text("disclaimer")
    
    print(f"版权声明 (默认语言): {copyright_text}")
    print(f"免责声明 (默认语言): {disclaimer_text}")
    
    # 加载英文版法律文本
    en_copyright = load_legal_text("copyright", "en")
    en_disclaimer = load_legal_text("disclaimer", "en")
    
    print(f"Copyright (English): {en_copyright}")
    print(f"Disclaimer (English): {en_disclaimer}")
    
    # 尝试加载不存在的文本类型
    nonexistent = load_legal_text("nonexistent_type")
    print(f"不存在的文本类型: '{nonexistent}'")


def demo_special_cases():
    """演示特殊场景法律文本"""
    print("\n===== 特殊场景法律文本 =====")
    
    # 加载默认免责声明
    default_disclaimer = load_legal_text("disclaimer")
    print(f"默认免责声明: {default_disclaimer}")
    
    # 加载商业场景免责声明
    commercial_disclaimer = load_legal_text("disclaimer", case="commercial")
    print(f"商业场景免责声明: {commercial_disclaimer}")
    
    # 加载教育场景免责声明
    educational_disclaimer = load_legal_text("disclaimer", case="educational")
    print(f"教育场景免责声明: {educational_disclaimer}")
    
    # 加载英文特殊场景免责声明
    en_commercial = load_legal_text("disclaimer", "en", "commercial")
    print(f"Commercial Disclaimer (English): {en_commercial}")


def demo_variable_substitution():
    """演示变量替换功能"""
    print("\n===== 变量替换功能 =====")
    
    # 准备变量
    variables = {
        "app_name": "ClipsMaster Pro",
        "user_name": "测试用户",
        "project_name": "演示项目"
    }
    
    # 加载带变量的文本
    attribution = load_legal_text("attribution", variables=variables)
    print(f"带变量替换的归属声明: {attribution}")
    
    # 使用当前年份变量
    copyright_with_year = load_legal_text("copyright", variables={"current_year": "2023"})
    print(f"自定义年份版权声明: {copyright_with_year}")


def demo_format_settings():
    """演示获取不同格式的设置"""
    print("\n===== 格式设置获取 =====")
    
    loader = LegalTextLoader()
    
    # 获取视频格式设置
    video_settings = loader.get_format_settings("video")
    print(f"视频格式设置: {json.dumps(video_settings, ensure_ascii=False, indent=2)}")
    
    # 获取文档格式设置
    document_settings = loader.get_format_settings("document")
    print(f"文档格式设置: {json.dumps(document_settings, ensure_ascii=False, indent=2)}")
    
    # 获取音频格式设置
    audio_settings = loader.get_format_settings("audio")
    print(f"音频格式设置: {json.dumps(audio_settings, ensure_ascii=False, indent=2)}")


def demo_integration_example():
    """演示在实际场景中的应用"""
    print("\n===== 实际应用场景演示 =====")
    
    def generate_video_metadata(title: str, creator: str, is_commercial: bool = False) -> Dict[str, Any]:
        """生成视频元数据"""
        lang = "zh"  # 可以根据用户设置或内容语言动态选择
        case = "commercial" if is_commercial else None
        
        # 准备变量
        variables = {
            "title": title,
            "creator": creator,
            "current_year": "2023"
        }
        
        # 构建元数据
        metadata = {
            "title": title,
            "creator": creator,
            "legal": {
                "copyright": load_legal_text("copyright", lang, case, variables),
                "disclaimer": load_legal_text("disclaimer", lang, case, variables),
                "terms_of_use": load_legal_text("terms_of_use", lang, variables),
                "attribution": load_legal_text("attribution", lang, variables)
            },
            "format_settings": LegalTextLoader().get_format_settings("video")
        }
        
        return metadata
    
    # 生成示例元数据
    print("生成非商业视频元数据:")
    non_commercial = generate_video_metadata("AI混剪演示", "VisionAI用户")
    print(json.dumps(non_commercial, ensure_ascii=False, indent=2))
    
    print("\n生成商业视频元数据:")
    commercial = generate_video_metadata("产品宣传片", "企业用户", True)
    print(json.dumps(commercial, ensure_ascii=False, indent=2))


def demo_reload_templates():
    """演示重新加载模板功能"""
    print("\n===== 重新加载模板 =====")
    
    loader = LegalTextLoader()
    
    # 显示当前版权声明
    print(f"当前版权声明: {loader.get_legal_text('copyright')}")
    
    # 重新加载模板
    success = loader.reload_templates()
    print(f"重新加载模板{'成功' if success else '失败'}")
    
    # 再次显示版权声明
    print(f"重新加载后版权声明: {loader.get_legal_text('copyright')}")


def main():
    """主函数"""
    print("===== VisionAI-ClipsMaster 法律文本加载器演示 =====")
    
    # 运行各个演示函数
    demo_basic_usage()
    demo_special_cases()
    demo_variable_substitution()
    demo_format_settings()
    demo_integration_example()
    demo_reload_templates()
    
    print("\n演示完成!")


if __name__ == "__main__":
    main() 