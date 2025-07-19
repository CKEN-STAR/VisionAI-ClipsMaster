#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本预览演示

演示版本三维预览和对比功能。此示例展示了如何可视化比较不同版本的剧本。
"""

import os
import sys
import json
import logging
from pathlib import Path
import random

# 将项目根目录添加到导入路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入所需模块
from src.versioning.preview_3d import (
    generate_3d_preview,
    compare_version_emotions,
    visualize_version_diff,
    VersionPreviewGenerator
)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("version_preview_demo")

def create_test_versions(count: int = 3):
    """创建测试版本数据
    
    Args:
        count: 要创建的版本数量
        
    Returns:
        版本列表
    """
    versions = []
    
    # 版本情感曲线模式
    patterns = [
        # 上升曲线
        lambda i, n: 0.1 + (0.8 * i / n),
        # 下降曲线
        lambda i, n: 0.9 - (0.8 * i / n),
        # 先上升后下降
        lambda i, n: 0.1 + (1.6 * i / n) if i < n/2 else 0.9 - (1.6 * (i - n/2) / n),
        # 先下降后上升
        lambda i, n: 0.9 - (1.6 * i / n) if i < n/2 else 0.1 + (1.6 * (i - n/2) / n),
        # 波浪形
        lambda i, n: 0.5 + 0.4 * ((-1) ** (i // 2)) * (1 - i / n),
    ]
    
    # 为每个版本使用不同的情感模式
    for v in range(count):
        pattern = patterns[v % len(patterns)]
        scene_count = random.randint(5, 10)
        
        scenes = []
        for i in range(scene_count):
            # 计算情感得分
            base_emotion = pattern(i, scene_count)
            # 添加随机波动
            emotion = min(1.0, max(-1.0, base_emotion + random.uniform(-0.1, 0.1)))
            
            scene = {
                "scene_id": f"s{i+1}",
                "text": f"版本{v+1}的场景{i+1}",
                "start_time": i * 5,
                "emotion_score": emotion
            }
            
            scenes.append(scene)
            
        version = {
            "version_id": f"v{v+1}",
            "title": f"测试版本 {v+1}",
            "scenes": scenes
        }
        
        versions.append(version)
        
    return versions

def main():
    """主函数"""
    logger.info("开始版本预览演示")
    
    # 创建测试版本
    versions = create_test_versions(3)
    logger.info(f"已创建 {len(versions)} 个测试版本")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "version_preview")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存版本数据
    for i, version in enumerate(versions):
        with open(os.path.join(output_dir, f"version_{i+1}.json"), 'w', encoding='utf-8') as f:
            json.dump(version, f, ensure_ascii=False, indent=2)
    
    # 创建预览生成器
    preview_gen = VersionPreviewGenerator()
    
    # 生成单个版本预览
    for i, version in enumerate(versions):
        html_preview = preview_gen.create_version_preview(version)
        with open(os.path.join(output_dir, f"preview_v{i+1}.html"), 'w', encoding='utf-8') as f:
            f.write("<html><head><title>版本预览</title></head><body>")
            f.write(f"<h1>版本 {i+1} 预览</h1>")
            f.write(html_preview)
            f.write("</body></html>")
    
    # 生成3D对比预览
    html_3d = generate_3d_preview(versions)
    with open(os.path.join(output_dir, "3d_comparison.html"), 'w', encoding='utf-8') as f:
        f.write("<html><head><title>3D版本对比</title></head><body>")
        f.write("<h1>3D版本对比</h1>")
        f.write(html_3d)
        f.write("</body></html>")
    
    # 生成情感对比预览
    html_emotion = compare_version_emotions(versions)
    with open(os.path.join(output_dir, "emotion_comparison.html"), 'w', encoding='utf-8') as f:
        f.write("<html><head><title>情感曲线对比</title></head><body>")
        f.write("<h1>情感曲线对比</h1>")
        f.write(html_emotion)
        f.write("</body></html>")
    
    # 生成全面对比
    html_all = preview_gen.compare_versions(versions, mode='all')
    with open(os.path.join(output_dir, "full_comparison.html"), 'w', encoding='utf-8') as f:
        f.write("<html><head><title>全面版本对比</title></head><body>")
        f.write("<h1>全面版本对比</h1>")
        f.write(html_all)
        f.write("</body></html>")
    
    # 生成差异对比 (版本1 vs 版本2)
    html_diff = visualize_version_diff(versions[0], versions[1])
    with open(os.path.join(output_dir, "version_diff.html"), 'w', encoding='utf-8') as f:
        f.write("<html><head><title>版本差异</title></head><body>")
        f.write("<h1>版本1 vs 版本2 差异</h1>")
        f.write(html_diff)
        f.write("</body></html>")
    
    logger.info(f"所有预览已生成到目录: {output_dir}")
    
    # 显示访问说明
    print(f"""
演示已完成，请查看以下文件:
- 3D预览：{os.path.join(output_dir, "3d_comparison.html")}
- 情感曲线：{os.path.join(output_dir, "emotion_comparison.html")}
- 全面对比：{os.path.join(output_dir, "full_comparison.html")}
- 版本差异：{os.path.join(output_dir, "version_diff.html")}

您可以在浏览器中打开这些HTML文件查看可视化结果。
""")

if __name__ == "__main__":
    main() 