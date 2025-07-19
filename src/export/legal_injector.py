#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 法律声明注入器

该模块负责在导出过程中，调用版权嵌入引擎，在视频中添加适当的法律声明。
它提供了一个高级API，便于在导出工作流中集成版权声明功能。
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 获取项目根目录
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    sys.path.append(str(PROJECT_ROOT))
except Exception:
    PROJECT_ROOT = Path.cwd()

# 导入相关模块
try:
    from src.utils.log_handler import get_logger
    from src.utils.config_manager import get_config
    from src.exporters.copyright_embedder import CopyrightEngine
except ImportError as e:
    # 设置基本日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("legal_injector")
    logger.error(f"导入错误: {e}")
    
    # 定义一个空的CopyrightEngine类以防导入失败
    class CopyrightEngine:
        def __init__(self):
            pass
        
        def add_legal_disclaimer(self, video_path, output_path=None):
            return video_path
    
    # 定义基本的get_config函数
    def get_config(module):
        return {}

# 配置日志
logger = get_logger("legal_injector")

def legal_injector(video_path: str, output_path: Optional[str] = None, 
                  options: Optional[Dict[str, Any]] = None) -> str:
    """
    向视频添加法律声明的高级API
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径，如果为None则自动生成
        options: 自定义选项字典
        
    Returns:
        处理后的视频路径
    """
    logger.info(f"为视频 {video_path} 注入法律声明")
    
    try:
        # 创建版权引擎
        engine = CopyrightEngine()
        
        # 应用自定义选项（如果有）
        if options:
            for key, value in options.items():
                engine.config[key] = value
        
        # 添加法律声明
        result = engine.add_legal_disclaimer(video_path, output_path)
        
        if result != video_path:
            logger.info(f"法律声明注入成功: {result}")
        else:
            logger.warning("法律声明注入失败，返回原始视频")
        
        return result
    
    except Exception as e:
        logger.error(f"法律声明注入过程中出错: {str(e)}")
        return video_path

def inject_legal_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    在视频元数据中添加法律声明相关信息
    
    Args:
        metadata: 原始元数据字典
        
    Returns:
        更新后的元数据字典
    """
    # 加载配置
    config = get_config("exporters").get("copyright", {})
    
    # 默认元数据
    legal_metadata = {
        "copyright": f"© {config.get('year', '2024')} ClipsMaster",
        "creator": "ClipsMasterAI",
        "rights": "All rights reserved",
        "generated_by": "VisionAI-ClipsMaster",
        "license": config.get("license", "Proprietary")
    }
    
    # 更新元数据
    if "meta" not in metadata:
        metadata["meta"] = {}
    
    metadata["meta"].update(legal_metadata)
    
    # 添加XMP元数据（如果支持）
    if "xmp" not in metadata:
        metadata["xmp"] = {}
    
    metadata["xmp"].update({
        "CreatorTool": "ClipsMasterAI",
        "Rights": "© 2024 ClipsMaster. All rights reserved."
    })
    
    logger.info("法律元数据注入成功")
    return metadata

# 测试代码
if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        # 测试法律声明注入
        result = legal_injector(input_path, output_path)
        print(f"处理完成: {result}")
    else:
        print("用法: python legal_injector.py 输入视频路径 [输出视频路径]") 