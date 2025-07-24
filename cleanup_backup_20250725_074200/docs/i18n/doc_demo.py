#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 文档国际化演示脚本

此脚本演示如何使用文档国际化功能创建和管理多语言文档。
"""

import os
import sys
import logging
from pathlib import Path

# 添加父目录到路径，以便能够导入doc_builder模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docs.i18n.doc_builder import DocLocalizer

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数：演示文档国际化功能"""
    logger.info("开始文档国际化演示")
    
    # 创建示例文档
    create_example_docs()
    
    # 实例化文档构建器
    doc_builder = DocLocalizer()
    
    # 确保目录结构
    doc_builder.ensure_language_dirs()
    
    # 同步文档结构（从英文同步到其他语言）
    doc_builder.sync_documents(source_lang="en")
    
    # 生成文档索引
    doc_builder.generate_doc_index()
    
    logger.info("文档国际化演示完成")
    
    logger.info("\n您可以使用以下命令构建文档:")
    logger.info("python docs/i18n/build_docs.py build")
    logger.info("\n或使用完整工作流:")
    logger.info("python docs/i18n/build_docs.py all")

def create_example_docs():
    """创建示例文档
    
    在英文文档目录中创建几个示例文档，用于演示文档国际化功能。
    """
    logger.info("创建示例文档")
    
    # 确保英文文档目录存在
    en_dir = Path("docs/en")
    en_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建示例文档
    
    # 快速入门文档
    quickstart = en_dir / "QUICKSTART.md"
    with open(quickstart, "w", encoding="utf-8") as f:
        f.write("""# VisionAI-ClipsMaster Quick Start Guide

This guide will help you get started with VisionAI-ClipsMaster for creating AI-powered short video clips.

## Installation

```bash
pip install visionai-clipsmaster
```

## Basic Usage

```python
from visionai_clipsmaster import VideoEditor

# Initialize the editor
editor = VideoEditor()

# Load a source video
editor.load_video("source_video.mp4")

# Generate AI-powered clips
clips = editor.generate_clips(duration=30)

# Save the best clip
clips[0].save("best_clip.mp4")
```

## Next Steps

- Check out the [User Guide](USER_GUIDE.md) for more details
- See the [API Reference](API_REFERENCE.md) for comprehensive documentation
- Learn about [Advanced Features](ADVANCED_FEATURES.md)
""")
    
    # 高级功能文档
    advanced = en_dir / "ADVANCED_FEATURES.md"
    with open(advanced, "w", encoding="utf-8") as f:
        f.write("""# Advanced Features

VisionAI-ClipsMaster offers several advanced features for professional video editing.

## Scene Detection

Automatically detect scene changes in your videos:

```python
from visionai_clipsmaster import SceneDetector

detector = SceneDetector()
scenes = detector.detect_scenes("my_video.mp4")

for scene in scenes:
    print(f"Scene from {scene.start_time} to {scene.end_time}")
```

## Emotion Analysis

Analyze emotions in your video:

```python
from visionai_clipsmaster import EmotionAnalyzer

analyzer = EmotionAnalyzer()
emotions = analyzer.analyze_video("my_video.mp4")

# Get the most emotional moments
highlights = emotions.get_highlights(top=5)
```

## Custom Models

Use your own custom models:

```python
from visionai_clipsmaster import VideoEditor

editor = VideoEditor()
editor.load_custom_model("my_model.pkl")
```
""")
    
    logger.info("示例文档创建完成")

if __name__ == "__main__":
    main() 