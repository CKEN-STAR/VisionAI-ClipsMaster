#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能版本推荐器演示

演示版本推荐器功能，包括根据用户配置文件推荐最适合的版本。
"""

import os
import sys
import json
import logging
from pathlib import Path
import random
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# 将项目根目录添加到导入路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入所需模块
from src.versioning.recommender import (
    VersionRecommender,
    get_version_recommender,
    recommend_version
)
from src.versioning.preview_3d import generate_3d_preview

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("version_recommender_demo")

def create_test_versions(count: int = 4):
    """创建测试版本数据
    
    Args:
        count: 要创建的版本数量
        
    Returns:
        版本列表
    """
    versions = []
    
    # 版本类型和特点
    version_types = [
        {
            # 版本1：情感强烈，适合大屏幕，喜剧/动作
            'name': '情感强烈版',
            'genre_score': 0.3,
            'length_score': 0.7,
            'emotion_intensity': 0.8, 
            'device_optimization': 0.8,
            'viewing_time_optimization': 0.6
        },
        {
            # 版本2：简洁版，适合移动设备，短注意力跨度
            'name': '简洁精华版',
            'genre_score': 0.5,
            'length_score': 0.3,
            'emotion_intensity': 0.4,
            'device_optimization': 0.2,
            'viewing_time_optimization': 0.4
        },
        {
            # 版本3：平衡版，适合多数用户
            'name': '标准平衡版',
            'genre_score': 0.5,
            'length_score': 0.5,
            'emotion_intensity': 0.5,
            'device_optimization': 0.5,
            'viewing_time_optimization': 0.5
        },
        {
            # 版本4：叙事深度版，适合文艺片爱好者
            'name': '叙事深度版',
            'genre_score': 0.7,
            'length_score': 0.6,
            'emotion_intensity': 0.3,
            'device_optimization': 0.7,
            'viewing_time_optimization': 0.7
        },
    ]
    
    # 为每个版本创建场景序列
    for i in range(min(count, len(version_types))):
        version_type = version_types[i]
        
        # 确定场景数量（基于版本长度）
        scene_count = int(5 + version_type['length_score'] * 10)
        
        # 创建场景
        scenes = []
        for j in range(scene_count):
            # 基于情感强度和版本类型创建情感曲线
            emotion_base = version_type['emotion_intensity']
            # 情感曲线的基本形状取决于版本类型
            if i == 0:  # 情感强烈版 - 波动大
                emotion = emotion_base * np.sin(j/scene_count * np.pi * 3) * 0.8
            elif i == 1:  # 简洁精华版 - 简单上升
                emotion = -0.2 + (j/scene_count) * emotion_base * 1.5
            elif i == 2:  # 平衡版 - 起伏温和
                emotion = emotion_base * 0.5 * np.sin(j/scene_count * np.pi * 2)
            else:  # 叙事深度版 - 缓慢构建，后期高潮
                emotion = -0.3 + (j/scene_count)**2 * emotion_base * 1.8
                
            scene = {
                "scene_id": f"s{j+1}",
                "text": f"版本{i+1}的场景{j+1}",
                "start_time": j * 5,
                "emotion_score": max(-1.0, min(1.0, emotion))
            }
            
            scenes.append(scene)
            
        # 创建版本对象
        version = {
            "version_id": f"v{i+1}",
            "title": version_type['name'],
            "scenes": scenes
        }
        
        # 添加版本特征
        for key, value in version_type.items():
            version[key] = value
            
        versions.append(version)
        
    return versions

def create_test_user_profiles(count: int = 5):
    """创建测试用户配置文件
    
    Args:
        count: 要创建的用户配置文件数量
        
    Returns:
        用户配置文件列表
    """
    # 预定义一些典型用户
    user_profiles = [
        {
            # 移动设备用户，短注意力跨度，喜欢喜剧
            'name': '通勤时观看的用户',
            'preferred_genre': 'comedy',
            'attention_span': 25,
            'emotional_preference': 0.2,
            'device_type': 'mobile',
            'time_of_day': 'morning'
        },
        {
            # 家庭TV用户，较长注意力跨度，喜欢动作片
            'name': '家庭影院用户',
            'preferred_genre': 'action',
            'attention_span': 75,
            'emotional_preference': 0.7,
            'device_type': 'tv',
            'time_of_day': 'evening'
        },
        {
            # 平板用户，中等注意力跨度，喜欢文艺片
            'name': '休闲时间用户',
            'preferred_genre': 'drama',
            'attention_span': 60,
            'emotional_preference': -0.1,
            'device_type': 'tablet',
            'time_of_day': 'afternoon'
        },
        {
            # 深夜PC用户，长注意力跨度，喜欢纪录片
            'name': '深夜PC用户',
            'preferred_genre': 'documentary',
            'attention_span': 80,
            'emotional_preference': -0.4,
            'device_type': 'desktop',
            'time_of_day': 'night'
        },
        {
            # 青少年用户，中短注意力跨度，强烈情感
            'name': '青少年用户',
            'preferred_genre': 'horror',
            'attention_span': 40,
            'emotional_preference': 0.6,
            'device_type': 'tablet',
            'time_of_day': 'night'
        }
    ]
    
    return user_profiles[:count]

def visualize_recommendation_results(user_profiles, versions, recommendations):
    """可视化推荐结果
    
    Args:
        user_profiles: 用户配置文件列表
        versions: 版本列表
        recommendations: 推荐结果
    """
    # 创建一个热力图，展示哪个用户匹配哪个版本
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 准备数据
    data = np.zeros((len(user_profiles), len(versions)))
    for i, user_rec in enumerate(recommendations):
        for j, rec_idx in enumerate(user_rec):
            # 填充热力图数据 - 第一个推荐得分最高，之后依次降低
            score = 1.0 - (j * 0.25)
            if score > 0:
                data[i, rec_idx] = score
    
    # 定义颜色映射
    cmap = LinearSegmentedColormap.from_list('custom_cmap', ['white', '#ffcccc', '#ff9999', '#ff6666', '#ff3333', 'red'])
    
    # 绘制热力图
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1)
    
    # 设置标签
    ax.set_xticks(np.arange(len(versions)))
    ax.set_yticks(np.arange(len(user_profiles)))
    ax.set_xticklabels([v['title'] for v in versions])
    ax.set_yticklabels([u['name'] for u in user_profiles])
    
    # 旋转X轴标签使其更易读
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # 为每个单元格添加文本注释
    for i in range(len(user_profiles)):
        for j in range(len(versions)):
            text = ax.text(j, i, f"{data[i, j]:.2f}",
                          ha="center", va="center", color="black" if data[i, j] < 0.5 else "white")
    
    # 添加标题和坐标轴标签
    ax.set_title("版本推荐匹配度")
    plt.tight_layout()
    
    # 保存图表
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "version_recommender")
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "recommendation_heatmap.png"), dpi=300, bbox_inches='tight')
    
    # 显示图表
    plt.close()
    
    logger.info(f"推荐热力图已保存到: {os.path.join(output_dir, 'recommendation_heatmap.png')}")

def main():
    """主函数"""
    logger.info("开始版本推荐器演示")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "version_recommender")
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建测试版本
    versions = create_test_versions(4)
    logger.info(f"已创建 {len(versions)} 个测试版本")
    
    # 创建测试用户配置文件
    user_profiles = create_test_user_profiles(5)
    logger.info(f"已创建 {len(user_profiles)} 个测试用户配置文件")
    
    # 保存数据以供检查
    with open(os.path.join(output_dir, "test_versions.json"), 'w', encoding='utf-8') as f:
        json.dump(versions, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(output_dir, "test_user_profiles.json"), 'w', encoding='utf-8') as f:
        json.dump(user_profiles, f, ensure_ascii=False, indent=2)
    
    # 创建推荐器
    recommender = VersionRecommender()
    
    # 生成训练数据并训练模型
    synthetic_data = recommender.generate_synthetic_data(300)
    model_path = os.path.join(output_dir, "recommender_model.joblib")
    logger.info("训练推荐模型...")
    recommender.train(synthetic_data, model_path)
    
    # 为每个用户推荐版本
    recommendations = []
    for i, profile in enumerate(user_profiles):
        logger.info(f"为用户 {i+1} ({profile['name']}) 推荐版本...")
        ranked_versions = recommender.rank_versions(profile, versions)
        recommendations.append(ranked_versions)
        
        best_version = versions[ranked_versions[0]]
        logger.info(f"  推荐第一选择: {best_version['title']}")
        
        # 为每个用户创建报告
        report = f"""
# 用户 {profile['name']} 的版本推荐报告

## 用户配置文件
- 偏好类型: {profile['preferred_genre']}
- 注意力跨度: {profile['attention_span']}
- 情感偏好: {profile['emotional_preference']}
- 设备类型: {profile['device_type']}
- 观看时间: {profile['time_of_day']}

## 推荐版本排序
"""
        for j, idx in enumerate(ranked_versions):
            version = versions[idx]
            report += f"{j+1}. **{version['title']}** (匹配度: {100 - j*20}%)\n"
        
        # 保存报告
        with open(os.path.join(output_dir, f"user_{i+1}_recommendation.md"), 'w', encoding='utf-8') as f:
            f.write(report)
    
    # 可视化推荐结果
    visualize_recommendation_results(user_profiles, versions, recommendations)
    
    # 为前三个版本生成3D预览
    html_3d = generate_3d_preview(versions)
    with open(os.path.join(output_dir, "versions_3d_preview.html"), 'w', encoding='utf-8') as f:
        f.write("<html><head><title>版本3D预览</title></head><body>")
        f.write("<h1>版本3D预览</h1>")
        f.write(html_3d)
        f.write("</body></html>")
    
    logger.info(f"所有演示数据已生成到目录: {output_dir}")
    
    # 显示访问说明
    print(f"""
演示已完成，请查看以下文件:
- 推荐热力图: {os.path.join(output_dir, "recommendation_heatmap.png")}
- 用户推荐报告: {os.path.join(output_dir, "user_1_recommendation.md")} 等
- 版本3D预览: {os.path.join(output_dir, "versions_3d_preview.html")}

您可以在浏览器中打开HTML文件查看可视化结果。
""")

if __name__ == "__main__":
    main() 