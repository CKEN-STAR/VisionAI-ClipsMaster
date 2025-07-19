#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 多语言声明生成器

此模块负责生成各种格式的法律声明文本，包括版权声明、免责声明、隐私声明等。
支持多语言输出，并可针对不同场景（商业、教育等）生成不同内容。

主要功能：
1. 生成完整的法律声明文本
2. 支持多种输出格式（纯文本、HTML、XML、SRT等）
3. 提供声明文本插值功能
4. 整合配置中的特殊场景和格式设置
"""

import os
import logging
import datetime
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple

# 添加项目根目录到路径，以便在standalone模式下运行
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.legal_text_loader import load_legal_text, LegalTextLoader
    from src.utils.log_handler import get_logger
except ImportError:
    # 如果直接运行此文件，尝试相对导入
    sys.path.append(str(current_dir.parent))
    try:
        from utils.legal_text_loader import load_legal_text, LegalTextLoader
        from utils.log_handler import get_logger
    except ImportError:
        print("无法导入必要模块，请确保正确安装和配置。")
        
        # 简单的日志替代
        def get_logger(name):
            logging.basicConfig(level=logging.INFO, 
                               format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            return logging.getLogger(name)

# 配置日志
logger = get_logger("legal_generator")


class LegalGenerator:
    """多语言声明生成器，负责生成各种格式的法律声明文本"""
    
    def __init__(self, app_version: str = "1.0"):
        """
        初始化声明生成器
        
        Args:
            app_version: 应用版本号
        """
        self.app_version = app_version
        self.loader = LegalTextLoader()
        self.logger = logger
    
    def generate_full_disclaimer(self, lang: str = "zh", 
                               case: Optional[str] = None, 
                               variables: Optional[Dict[str, str]] = None) -> str:
        """
        生成完整的版权和免责声明组合文本
        
        Args:
            lang: 语言代码，如'zh', 'en'
            case: 特殊场景，如'commercial', 'educational'等
            variables: 用于替换文本中变量的字典
            
        Returns:
            str: 组合后的声明文本
        """
        # 准备默认变量
        if variables is None:
            variables = {}
        
        default_vars = {
            "current_year": str(datetime.datetime.now().year),
            "app_name": "VisionAI-ClipsMaster",
            "app_version": self.app_version
        }
        merged_vars = {**default_vars, **variables}
        
        # 加载版权声明和免责声明
        copyright_text = load_legal_text("copyright", lang, case, merged_vars)
        disclaimer_text = load_legal_text("disclaimer", lang, case, merged_vars)
        
        # 组合为完整文本
        return f"{copyright_text}\n{disclaimer_text}"
    
    def generate_document_header(self, lang: str = "zh", 
                                case: Optional[str] = None,
                                format_type: str = "document") -> str:
        """
        生成文档头部的法律声明
        
        Args:
            lang: 语言代码，如'zh', 'en'
            case: 特殊场景，如'commercial', 'educational'等
            format_type: 格式类型，如'document', 'video'等
            
        Returns:
            str: 文档头部的法律声明
        """
        # 获取文档格式设置
        format_settings = self.loader.get_format_settings(format_type)
        
        # 组装变量
        variables = {
            "current_year": str(datetime.datetime.now().year),
            "header_position": format_settings.get("header_position", "top")
        }
        
        # 加载版权声明
        copyright_text = load_legal_text("copyright", lang, case, variables)
        
        # 生成头部
        header = f"/* {copyright_text} */\n\n"
        
        return header
    
    def generate_html_footer(self, lang: str = "zh", 
                           case: Optional[str] = None) -> str:
        """
        生成HTML页脚的法律声明
        
        Args:
            lang: 语言代码，如'zh', 'en'
            case: 特殊场景，如'commercial', 'educational'等
            
        Returns:
            str: HTML格式的页脚法律声明
        """
        # 加载必要的法律文本
        copyright_text = load_legal_text("copyright", lang, case)
        disclaimer_text = load_legal_text("disclaimer", lang, case)
        privacy_text = load_legal_text("privacy_notice", lang, case)
        terms_text = load_legal_text("terms_of_use", lang, case)
        
        # 构建HTML页脚
        footer = f"""
<footer class="legal-footer">
    <div class="copyright">{copyright_text}</div>
    <div class="disclaimer">{disclaimer_text}</div>
    <div class="privacy">{privacy_text}</div>
    <div class="terms">{terms_text}</div>
    <div class="attribution">© {datetime.datetime.now().year} VisionAI-ClipsMaster</div>
</footer>
"""
        return footer
    
    def generate_srt_disclaimer(self, lang: str = "zh", 
                              duration: float = 5.0) -> str:
        """
        生成SRT格式的免责声明字幕
        
        Args:
            lang: 语言代码，如'zh', 'en'
            duration: 显示时长（秒）
            
        Returns:
            str: SRT格式的免责声明
        """
        # 加载免责声明
        disclaimer_text = load_legal_text("disclaimer", lang)
        
        # 构建SRT格式字幕
        srt = f"""1
00:00:00,000 --> 00:00:{int(duration):02d},000
{disclaimer_text}

"""
        return srt
    
    def generate_xml_metadata(self, lang: str = "zh", 
                            case: Optional[str] = None,
                            xml_format: str = "premiere") -> str:
        """
        生成XML格式的元数据声明
        
        Args:
            lang: 语言代码，如'zh', 'en'
            case: 特殊场景，如'commercial', 'educational'等
            xml_format: XML格式，如'premiere', 'fcpxml'等
            
        Returns:
            str: XML格式的元数据声明
        """
        # 加载法律文本
        copyright_text = load_legal_text("copyright", lang, case)
        disclaimer_text = load_legal_text("disclaimer", lang, case)
        attribution = load_legal_text("attribution", lang, case)
        
        # 根据不同的XML格式生成元数据
        if xml_format == "premiere":
            metadata = f"""<metadata>
    <copyright>{copyright_text}</copyright>
    <disclaimer>{disclaimer_text}</disclaimer>
    <generator>VisionAI-ClipsMaster v{self.app_version}</generator>
    <attribution>{attribution}</attribution>
    <creationDate>{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}</creationDate>
</metadata>"""
        elif xml_format == "fcpxml":
            metadata = f"""<metadata>
    <md key="com.apple.proapps.spotlight.kMDItemCopyright" value="{copyright_text}"/>
    <md key="com.apple.proapps.spotlight.kMDItemDescription" value="{disclaimer_text}"/>
    <md key="com.apple.proapps.spotlight.kMDItemCreator" value="{attribution}"/>
    <md key="com.apple.proapps.spotlight.kMDItemCreationDate" value="{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}"/>
</metadata>"""
        else:
            metadata = f"""<metadata>
    <copyright>{copyright_text}</copyright>
    <disclaimer>{disclaimer_text}</disclaimer>
</metadata>"""
        
        return metadata
    
    def generate_watermark_config(self, lang: str = "zh") -> Dict[str, Any]:
        """
        生成水印配置
        
        Args:
            lang: 语言代码，如'zh', 'en'
            
        Returns:
            Dict[str, Any]: 水印配置
        """
        # 获取视频格式设置
        format_settings = self.loader.get_format_settings("video")
        
        # 生成水印配置
        watermark_config = {
            "text": f"VisionAI-ClipsMaster v{self.app_version}",
            "position": format_settings.get("watermark_position", "bottom-right"),
            "opacity": format_settings.get("watermark_opacity", 0.8),
            "fontScale": 1.0,
            "color": (255, 255, 255),
            "padding": 10
        }
        
        return watermark_config
    
    def generate_audio_disclaimer(self, lang: str = "zh", 
                                format_type: str = "mp3") -> Dict[str, Any]:
        """
        生成音频文件的免责声明数据
        
        Args:
            lang: 语言代码，如'zh', 'en'
            format_type: 音频格式，如'mp3', 'wav'等
            
        Returns:
            Dict[str, Any]: 音频免责声明数据
        """
        # 获取音频格式设置
        audio_settings = self.loader.get_format_settings("audio")
        
        # 加载法律文本
        copyright_text = load_legal_text("copyright", lang)
        disclaimer_text = load_legal_text("disclaimer", lang)
        
        # 构建音频元数据
        audio_meta = {
            "title": "VisionAI-ClipsMaster Generated Audio",
            "artist": "VisionAI-ClipsMaster",
            "album": "AI Generated Content",
            "comment": f"{copyright_text} {disclaimer_text}",
            "copyright": copyright_text,
            "year": str(datetime.datetime.now().year),
            "credits_position": audio_settings.get("credits_position", "end"),
            "fade_duration": audio_settings.get("fade_duration", 2.0)
        }
        
        return audio_meta
    
    def get_all_legal_texts(self, lang: str = "zh", 
                          case: Optional[str] = None) -> Dict[str, str]:
        """
        获取指定语言和场景的所有法律文本
        
        Args:
            lang: 语言代码，如'zh', 'en'
            case: 特殊场景，如'commercial', 'educational'等
            
        Returns:
            Dict[str, str]: 所有法律文本
        """
        # 所有可能的文本类型
        text_types = [
            "copyright", "disclaimer", "privacy_notice", 
            "terms_of_use", "attribution"
        ]
        
        # 收集所有文本
        result = {}
        for text_type in text_types:
            text = load_legal_text(text_type, lang, case)
            if text:  # 只包含非空文本
                result[text_type] = text
        
        return result


# 简化使用的辅助函数
def generate_full_disclaimer(lang: str = "zh", case: Optional[str] = None, 
                           variables: Optional[Dict[str, str]] = None) -> str:
    """
    生成完整的版权和免责声明组合文本（简化调用）
    
    Args:
        lang: 语言代码，如'zh', 'en'
        case: 特殊场景，如'commercial', 'educational'等
        variables: 用于替换文本中变量的字典
        
    Returns:
        str: 组合后的声明文本
    """
    generator = LegalGenerator()
    return generator.generate_full_disclaimer(lang, case, variables)


def generate_html_footer(lang: str = "zh", case: Optional[str] = None) -> str:
    """
    生成HTML页脚的法律声明（简化调用）
    
    Args:
        lang: 语言代码，如'zh', 'en'
        case: 特殊场景，如'commercial', 'educational'等
        
    Returns:
        str: HTML格式的页脚法律声明
    """
    generator = LegalGenerator()
    return generator.generate_html_footer(lang, case)


def generate_xml_metadata(lang: str = "zh", case: Optional[str] = None, xml_format: str = "premiere") -> str:
    """
    生成XML格式的元数据声明（简化调用）
    
    Args:
        lang: 语言代码，如'zh', 'en'
        case: 特殊场景，如'commercial', 'educational'等
        xml_format: XML格式，如'premiere', 'fcpxml'等
        
    Returns:
        str: XML格式的元数据声明
    """
    generator = LegalGenerator()
    return generator.generate_xml_metadata(lang, case, xml_format)


# 测试代码
if __name__ == "__main__":
    # 创建生成器实例
    generator = LegalGenerator()
    
    print("\n===== 测试不同语言的完整声明 =====")
    print("中文声明:")
    print(generator.generate_full_disclaimer("zh"))
    print("\nEnglish disclaimer:")
    print(generator.generate_full_disclaimer("en"))
    
    print("\n===== 测试不同场景的声明 =====")
    print("默认场景:")
    print(generator.generate_full_disclaimer("zh"))
    print("\n商业场景:")
    print(generator.generate_full_disclaimer("zh", "commercial"))
    print("\n教育场景:")
    print(generator.generate_full_disclaimer("zh", "educational"))
    
    print("\n===== 测试变量替换 =====")
    variables = {
        "app_name": "ClipsMaster Pro",
        "current_year": "2023"
    }
    print(generator.generate_full_disclaimer("zh", variables=variables))
    
    print("\n===== 测试XML元数据 =====")
    print(generator.generate_xml_metadata("zh", xml_format="premiere"))
    
    print("\n===== 测试SRT字幕声明 =====")
    print(generator.generate_srt_disclaimer("zh")) 