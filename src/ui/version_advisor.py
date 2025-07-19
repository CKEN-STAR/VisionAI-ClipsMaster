#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本建议模块

该模块提供根据视频规格推荐最适合的版本功能。
主要功能：
1. 分析视频规格（分辨率、HDR等）
2. 推荐最适合的版本
3. 提供版本相关提示
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)

# 设置日志记录器
logger = get_logger("version_advisor")

# 版本功能映射
VERSION_FEATURES = {
    "3.0.0": {
        "max_resolution": (3840, 2160),  # 4K
        "supports_hdr": True,
        "supports_nested_sequences": True,
        "supports_effects_layers": True,
        "supports_keyframes": True,
        "supports_3d_effects": True,
        "supports_color_grading": True,
        "supports_audio_effects": True,
        "supports_multi_track": True,
        "display_name": "专业版 (3.0.0)"
    },
    "2.9.5": {
        "max_resolution": (1920, 1080),  # 1080p
        "supports_hdr": False,
        "supports_nested_sequences": False,
        "supports_effects_layers": True,
        "supports_keyframes": True,
        "supports_3d_effects": False,
        "supports_color_grading": True,
        "supports_audio_effects": True,
        "supports_multi_track": True,
        "display_name": "高级版 (2.9.5)"
    },
    "2.5.0": {
        "max_resolution": (1920, 1080),  # 1080p
        "supports_hdr": False,
        "supports_nested_sequences": False,
        "supports_effects_layers": False,
        "supports_keyframes": False,
        "supports_3d_effects": False,
        "supports_color_grading": False,
        "supports_audio_effects": False,
        "supports_multi_track": True,
        "display_name": "标准版 (2.5.0)"
    },
    "2.0.0": {
        "max_resolution": (1280, 720),  # 720p
        "supports_hdr": False,
        "supports_nested_sequences": False,
        "supports_effects_layers": False,
        "supports_keyframes": False,
        "supports_3d_effects": False,
        "supports_color_grading": False,
        "supports_audio_effects": False,
        "supports_multi_track": False,
        "display_name": "基础版 (2.0.0)"
    }
}

def get_version_specifications() -> Dict[str, Dict[str, Any]]:
    """
    从配置文件加载版本规格
    
    Returns:
        Dict[str, Dict[str, Any]]: 版本规格字典
    """
    try:
        # 尝试从配置文件加载版本规格
        config_path = os.path.join(root_dir, 'configs', 'version_specifications.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                spec = json.load(f)
                return spec
    except Exception as e:
        logger.error(f"加载版本规格失败: {e}")
    
    # 如果加载失败，返回默认值
    return {}

def suggest_version(video_spec: Dict[str, Any]) -> str:
    """
    根据视频规格推荐最佳适配版本
    
    Args:
        video_spec: 视频规格，包含分辨率、HDR等信息
        
    Returns:
        str: 推荐的版本号
    """
    logger.info(f"分析视频规格: {video_spec}")
    
    # 提取视频规格
    resolution = video_spec.get('resolution', [1920, 1080])
    has_hdr = video_spec.get('hdr', False)
    has_effects = video_spec.get('effects', False)
    has_audio_effects = video_spec.get('audio_effects', False)
    has_multi_track = video_spec.get('multi_track', False)
    
    # 确保分辨率是两元组
    if isinstance(resolution, list) and len(resolution) >= 2:
        width, height = resolution[0], resolution[1]
    elif isinstance(resolution, dict):
        width = resolution.get('width', 1920)
        height = resolution.get('height', 1080)
    else:
        width, height = 1920, 1080
    
    # 确保数值类型
    try:
        width = int(width)
        height = int(height)
    except (ValueError, TypeError):
        width, height = 1920, 1080
    
    # 根据规格推荐版本
    if width > 1920 or height > 1080 or has_hdr:
        # 4K 或 HDR 需要 3.0.0 版本
        return "3.0.0+"
    elif has_effects or has_audio_effects:
        # 复杂效果需要 2.9.5 版本
        return "2.9.5"
    elif has_multi_track:
        # 多轨需要 2.5.0 版本
        return "2.5.0"
    else:
        # 基本编辑可以使用 2.0.0 版本
        return "2.9.5"

def get_version_features(version: str) -> Dict[str, Any]:
    """
    获取指定版本的功能列表
    
    Args:
        version: 版本号
        
    Returns:
        Dict[str, Any]: 版本功能字典
    """
    # 清理版本号
    cleaned_version = version.strip().replace('+', '')
    
    # 检查是否是完整版本号
    if cleaned_version not in VERSION_FEATURES:
        # 尝试匹配主要版本号
        for v in VERSION_FEATURES:
            if v.startswith(cleaned_version):
                return VERSION_FEATURES[v]
        
        # 如果无法匹配，返回最高版本
        return VERSION_FEATURES["3.0.0"]
    
    return VERSION_FEATURES[cleaned_version]

def suggest_version_with_reason(video_spec: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    推荐版本并给出原因
    
    Args:
        video_spec: 视频规格
        
    Returns:
        Tuple[str, List[str]]: 推荐的版本和原因列表
    """
    version = suggest_version(video_spec)
    features = get_version_features(version)
    reasons = []
    
    # 分辨率提示
    resolution = video_spec.get('resolution', [1920, 1080])
    if isinstance(resolution, list) and len(resolution) >= 2:
        width, height = resolution[0], resolution[1]
    elif isinstance(resolution, dict):
        width = resolution.get('width', 1920)
        height = resolution.get('height', 1080)
    else:
        width, height = 1920, 1080
        
    try:
        width = int(width)
        height = int(height)
    except (ValueError, TypeError):
        width, height = 1920, 1080
    
    if width > 1920 or height > 1080:
        reasons.append(f"视频分辨率 {width}x{height} 超过1080p，需要3.0.0版本支持4K")
    
    # HDR提示
    if video_spec.get('hdr', False):
        reasons.append("视频包含HDR内容，需要3.0.0版本支持HDR")
    
    # 效果提示
    if video_spec.get('effects', False):
        reasons.append("视频包含特效，建议使用2.9.5或更高版本")
    
    # 音频效果提示
    if video_spec.get('audio_effects', False):
        reasons.append("视频包含音频效果，建议使用2.9.5或更高版本")
    
    # 多轨提示
    if video_spec.get('multi_track', False):
        reasons.append("项目使用多轨编辑，建议使用2.5.0或更高版本")
    
    # 如果没有特定原因，提供默认建议
    if not reasons:
        reasons.append("基于默认设置推荐，适合基本视频编辑需求")
    
    return version, reasons

def generate_version_info_html(video_spec: Dict[str, Any]) -> str:
    """
    生成版本信息HTML
    
    Args:
        video_spec: 视频规格
        
    Returns:
        str: HTML格式的版本信息
    """
    version, reasons = suggest_version_with_reason(video_spec)
    features = get_version_features(version)
    
    html = f"""
    <div class="version-info">
        <h3>推荐版本: {features['display_name']}</h3>
        <div class="version-reasons">
            <p><strong>推荐原因:</strong></p>
            <ul>
    """
    
    for reason in reasons:
        html += f"<li>{reason}</li>\n"
    
    html += """
            </ul>
        </div>
        <div class="version-features">
            <p><strong>版本功能:</strong></p>
            <ul>
    """
    
    max_width, max_height = features["max_resolution"]
    html += f"<li>最大分辨率: {max_width}x{max_height}</li>\n"
    
    if features["supports_hdr"]:
        html += "<li>支持HDR</li>\n"
    
    if features["supports_nested_sequences"]:
        html += "<li>支持嵌套序列</li>\n"
    
    if features["supports_effects_layers"]:
        html += "<li>支持效果层</li>\n"
    
    if features["supports_keyframes"]:
        html += "<li>支持关键帧</li>\n"
    
    if features["supports_3d_effects"]:
        html += "<li>支持3D效果</li>\n"
    
    if features["supports_color_grading"]:
        html += "<li>支持色彩分级</li>\n"
    
    if features["supports_audio_effects"]:
        html += "<li>支持音频效果</li>\n"
    
    if features["supports_multi_track"]:
        html += "<li>支持多轨道编辑</li>\n"
    
    html += """
            </ul>
        </div>
    </div>
    """
    
    return html

if __name__ == "__main__":
    # 示例：测试版本建议功能
    test_specs = [
        {
            "resolution": [3840, 2160],
            "hdr": True,
            "effects": True,
            "audio_effects": True,
            "multi_track": True,
        },
        {
            "resolution": [1920, 1080],
            "hdr": False,
            "effects": True,
            "audio_effects": False,
            "multi_track": True,
        },
        {
            "resolution": [1280, 720],
            "hdr": False,
            "effects": False,
            "audio_effects": False,
            "multi_track": True,
        },
        {
            "resolution": [1280, 720],
            "hdr": False,
            "effects": False,
            "audio_effects": False,
            "multi_track": False,
        }
    ]
    
    for i, spec in enumerate(test_specs):
        version, reasons = suggest_version_with_reason(spec)
        print(f"\n测试 {i+1}:")
        print(f"视频规格: {spec}")
        print(f"推荐版本: {version}")
        print("推荐原因:")
        for reason in reasons:
            print(f"  - {reason}") 