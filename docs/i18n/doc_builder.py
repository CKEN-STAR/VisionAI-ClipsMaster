#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 文档国际化构建工具

负责构建多语言版本的文档，支持英文、中文和日文等多种语言。
使用mkdocs进行文档构建，保持统一风格和格式。
"""

import os
import json
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Union, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocLocalizer:
    """文档国际化构建器
    
    负责构建和管理多语言文档，支持多种语言的文档生成和更新。
    使用mkdocs作为文档构建工具，支持主题定制和搜索功能。
    """
    
    # 支持的语言列表 (语言代码: 语言名称)
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "zh": "中文",
        "ja": "日本語"
    }
    
    def __init__(self, docs_root: str = "docs", build_dir: str = "docs/build"):
        """初始化文档构建器
        
        Args:
            docs_root: 文档根目录
            build_dir: 构建输出目录
        """
        self.docs_root = Path(docs_root)
        self.build_dir = Path(build_dir)
        
        # 确保构建目录存在
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查mkdocs是否已安装
        try:
            subprocess.run(["mkdocs", "--version"], check=True, capture_output=True)
            logger.info("已检测到mkdocs")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("未检测到mkdocs，请先安装：pip install mkdocs")
    
    def build_all(self):
        """构建多语言文档"""
        # 按照图片中的实现方式
        for lang in ["en", "zh", "ja"]:
            self._build_doc(lang)
        
        # 生成索引页面
        self.generate_doc_index()
        
        logger.info("所有语言文档构建完成")
    
    def _build_doc(self, lang: str) -> None:
        """单语言文档构建
        
        为特定语言构建文档。
        
        Args:
            lang: 语言代码，如"en", "zh", "ja"
        """
        logger.info(f"构建{self.SUPPORTED_LANGUAGES.get(lang, lang)}文档...")
        
        # 确保配置文件存在
        config_path = self.docs_root / lang / "mkdocs.yml"
        if not config_path.exists():
            self._ensure_mkdocs_config(lang)
        
        # 构建命令 - 与图片中完全一致
        cmd = f"mkdocs build -f docs/{lang}/mkdocs.yml"
        
        try:
            # 执行构建
            result = subprocess.run(
                cmd, 
                shell=True, 
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"{lang}文档构建成功")
        except subprocess.SubprocessError as e:
            logger.error(f"{lang}文档构建失败: {e}")
            if hasattr(e, 'stderr'):
                logger.error(e.stderr)
    
    def ensure_language_dirs(self) -> None:
        """确保所有语言目录结构存在
        
        创建每种语言需要的目录结构，包括源文档和构建目录。
        """
        for lang in self.SUPPORTED_LANGUAGES:
            # 创建语言源目录
            lang_dir = self.docs_root / lang
            lang_dir.mkdir(exist_ok=True)
            
            # 创建构建输出目录
            build_lang_dir = self.build_dir / lang
            build_lang_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建基本的mkdocs配置文件（如果不存在）
            self._ensure_mkdocs_config(lang)
            
            logger.info(f"已确保{lang}语言文档目录结构")
    
    def _ensure_mkdocs_config(self, lang: str) -> None:
        """确保mkdocs配置文件存在
        
        为指定语言创建基本的mkdocs配置文件，如果文件已存在则不覆盖。
        
        Args:
            lang: 语言代码
        """
        config_path = self.docs_root / lang / "mkdocs.yml"
        
        if not config_path.exists():
            language_name = self.SUPPORTED_LANGUAGES.get(lang, "Documentation")
            
            # 基本配置
            config_content = f"""site_name: VisionAI-ClipsMaster {language_name}
site_description: VisionAI-ClipsMaster短剧混剪AI项目文档
site_author: VisionAI Team
docs_dir: .
site_dir: ../build/{lang}
theme:
  name: material
  language: {lang}
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.expand
    - navigation.indexes
    - search.highlight
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: 切换到深色模式
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: 切换到浅色模式
markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight
  - pymdownx.inlinehilite
  - toc:
      permalink: true
nav:
  - 首页: index.md
  - 用户指南: USER_GUIDE.md
  - API参考: API_REFERENCE.md
  - 错误代码: ERROR_CODES.md
"""
            
            # 写入配置文件
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)
            
            logger.info(f"已创建{lang}语言的mkdocs配置文件")
            
            # 创建索引文件
            index_path = self.docs_root / lang / "index.md"
            if not index_path.exists():
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(f"# VisionAI-ClipsMaster {self.SUPPORTED_LANGUAGES.get(lang)}\n\n"
                            f"欢迎使用VisionAI-ClipsMaster短剧混剪AI项目文档。\n\n"
                            f"## 快速开始\n\n"
                            f"- [用户指南](USER_GUIDE.md)\n"
                            f"- [API参考](API_REFERENCE.md)\n"
                            f"- [错误代码](ERROR_CODES.md)\n")
    
    def sync_documents(self, source_lang: str = "en") -> None:
        """同步文档结构
        
        将源语言的文档结构同步到目标语言，确保所有语言版本有相同的文档文件。
        不会覆盖已存在的文档，只会创建不存在的文档文件。
        
        Args:
            source_lang: 源语言代码
        """
        target_langs = [lang for lang in self.SUPPORTED_LANGUAGES if lang != source_lang]
        
        source_dir = self.docs_root / source_lang
        if not source_dir.exists():
            logger.error(f"源语言目录不存在: {source_dir}")
            return
        
        # 获取源语言所有markdown文件
        source_files = list(source_dir.glob("*.md"))
        
        for target_lang in target_langs:
            target_dir = self.docs_root / target_lang
            target_dir.mkdir(exist_ok=True)
            
            logger.info(f"同步文档从{source_lang}到{target_lang}...")
            
            for source_file in source_files:
                target_file = target_dir / source_file.name
                
                # 如果目标文件不存在，创建一个基于源文件的框架
                if not target_file.exists():
                    with open(source_file, "r", encoding="utf-8") as sf:
                        source_content = sf.read()
                    
                    # 提取标题并创建基本框架
                    lines = source_content.split("\n")
                    title = "# 文档"
                    for line in lines:
                        if line.startswith("# "):
                            title = line
                            break
                    
                    with open(target_file, "w", encoding="utf-8") as tf:
                        tf.write(f"{title}\n\n*此文档需要翻译*\n\n")
                    
                    logger.info(f"已创建{target_lang}语言文档框架: {target_file.name}")

    def generate_doc_index(self) -> None:
        """生成文档索引页面
        
        创建一个索引页面，链接到所有语言版本的文档。
        """
        index_path = self.build_dir / "index.html"
        
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 文档</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .language-selector {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 30px;
        }
        .language-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            width: 200px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            text-decoration: none;
            color: inherit;
        }
        .language-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .language-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 8px;
            color: #3498db;
        }
        .language-name {
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <h1>VisionAI-ClipsMaster 文档</h1>
    <p>选择您偏好的语言版本:</p>
    
    <div class="language-selector">
"""
        
        # 添加语言卡片
        for lang_code, lang_name in self.SUPPORTED_LANGUAGES.items():
            html_content += f"""
        <a href="{lang_code}/index.html" class="language-card">
            <div class="language-title">{lang_code.upper()}</div>
            <div class="language-name">{lang_name}</div>
        </a>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info("已生成文档索引页面")


# 主函数
if __name__ == "__main__":
    # 实例化文档构建器
    doc_builder = DocLocalizer()
    
    # 确保目录结构
    doc_builder.ensure_language_dirs()
    
    # 同步文档结构
    doc_builder.sync_documents()
    
    # 构建所有语言文档
    doc_builder.build_all()
    
    logger.info("文档构建完成")
