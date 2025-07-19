#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
对比学习模型演示脚本

演示如何使用深度对比学习模型进行原片和爆款剧本模式的对比学习
"""

import os
import json
import torch
import logging
import argparse
import numpy as np
from pathlib import Path
from loguru import logger

from models.contrastive_learner import (
    DramaContrastiveModel, 
    train_contrastive_model,
    DramaContrastiveDataset
)


def create_sample_data(output_path, num_samples=20):
    """
    创建示例数据用于演示
    
    Args:
        output_path: 输出路径
        num_samples: 样本数量
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 创建简单的示例数据，包含原片和爆款对
    pairs = []
    
    # 模拟剧本片段
    original_fragments = [
        "李明走进教室，看到同学们都已经到齐了。今天我们讨论一下期末考试复习计划。",
        "王红站在舞台上，有些紧张，这是她第一次公开演讲。",
        "张伟接到了一个陌生电话，对方自称是医院的人，说他父亲出了车祸。",
        "两人在咖啡厅闲聊，讨论着最近的电影和书籍。",
        "老李默默收拾着儿子的房间，看着照片上儿子的笑容。"
    ]
    
    # 对应的爆款风格片段
    hit_fragments = [
        "李明猛地推开教室门，全班同学齐刷刷回头！\"期末考试\"三个字瞬间点燃了教室的紧张氛围！",
        "聚光灯下的王红双手颤抖，这是她人生中最重要的时刻，台下数百双眼睛死死盯着她！",
        "刺耳的电话铃声划破寂静，张伟接起电话，\"您父亲出了车祸\"，他的世界在这一刻崩塌！",
        "咖啡厅一角，两人交谈中的眼神电光火石，看似闲聊却暗藏玄机！",
        "老李颤抖的手抚过儿子的照片，眼泪无声滑落，十年了，儿子再也没回过家..."
    ]
    
    # 生成示例数据
    for i in range(num_samples):
        idx = i % len(original_fragments)
        original = original_fragments[idx]
        hit = hit_fragments[idx]
        
        # 添加一些随机变化
        if i > len(original_fragments):
            original = original.replace("，", "，" + f"随机文本{i}，")
            hit = hit.replace("！", f"！震惊{i}！")
        
        pairs.append({
            "id": i,
            "origin": {
                "text": original,
                "features": {
                    "emotion": np.random.uniform(0, 0.5),
                    "intensity": np.random.uniform(0, 0.5),
                    "suspense": np.random.uniform(0, 0.4)
                }
            },
            "hit": {
                "text": hit,
                "features": {
                    "emotion": np.random.uniform(0.6, 1.0),
                    "intensity": np.random.uniform(0.7, 1.0),
                    "suspense": np.random.uniform(0.6, 0.9)
                }
            }
        })
    
    # 保存到文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    
    logger.info(f"创建了 {num_samples} 个示例数据对，保存至 {output_path}")
    return output_path


def tokenize_text(text, max_length=128):
    """将文本转换为简单的整数序列（模拟分词）"""
    # 在实际应用中，这里应该使用真正的分词器
    # 这里仅用简单的字符级表示作为演示
    chars = list(text[:max_length])
    # 简单哈希转换成整数ID
    ids = [hash(c) % 10000 for c in chars]
    return torch.tensor(ids).unsqueeze(0)  # 添加批次维度


class SimpleTransform:
    """简单的数据转换器，用于演示"""
    
    def __init__(self, max_length=128):
        self.max_length = max_length
    
    def __call__(self, sample):
        """转换样本为模型输入格式"""
        if isinstance(sample, dict) and "text" in sample:
            # 处理字典形式的样本
            text = sample["text"]
            return tokenize_text(text, self.max_length)
        else:
            # 未知格式，返回随机张量
            return torch.randint(0, 10000, (1, min(len(str(sample)), self.max_length)))


def demo_contrastive_learning():
    """演示对比学习模型的使用"""
    logger.info("=== 深度对比学习模型演示 ===")
    
    # 准备目录
    data_dir = Path("data/demo")
    data_dir.mkdir(parents=True, exist_ok=True)
    model_dir = Path("models/saved")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建示例数据
    sample_data_path = create_sample_data(str(data_dir / "contrastive_samples.json"), num_samples=30)
    
    # 创建数据转换器
    transform = SimpleTransform(max_length=128)
    
    # 加载数据集
    logger.info("加载数据集...")
    dataset = DramaContrastiveDataset(
        data_path=sample_data_path,
        transform=transform,
        hard_negative_mining=True,
        use_curriculum=True
    )
    
    # 检查数据集
    logger.info(f"数据集大小: {len(dataset)}")
    
    # 获取一个样本
    anchor, positive, negative = dataset[0]
    logger.info(f"样本形状: anchor={anchor.shape}, positive={positive.shape}, negative={negative.shape}")
    
    # 初始化模型
    logger.info("初始化对比学习模型...")
    model = DramaContrastiveModel()
    
    # 演示前向传播
    logger.info("计算对比损失...")
    loss = model(anchor, positive, negative)
    logger.info(f"三元组损失: {loss.item():.4f}")
    
    # 训练模型（少量轮次用于演示）
    logger.info("开始模型训练演示...")
    trained_model = train_contrastive_model(
        data_path=sample_data_path,
        model_save_path=str(model_dir / "contrastive_model_demo.pt"),
        learning_rate=1e-4,
        batch_size=4,
        epochs=3,  # 演示用少量轮次
        use_hard_negative_mining=True,
        use_curriculum_learning=True
    )
    
    # 演示模型使用
    logger.info("模型使用演示...")
    
    # 创建一些测试文本
    test_original = "李小明在课堂上打瞌睡，被老师发现了。"
    test_hit = "李小明课堂瞌睡被抓包！老师暴怒，全班哗然！"
    test_negative = "小区门口新开了一家便利店，商品种类很齐全。"
    
    # 编码文本
    logger.info("编码测试文本...")
    with torch.no_grad():
        # 将文本转换为模型输入格式
        original_encoded = trained_model.encode_script(test_original)
        hit_encoded = trained_model.encode_script(test_hit)
        negative_encoded = trained_model.encode_script(test_negative)
        
        # 计算特征相似度
        sim_positive = torch.cosine_similarity(original_encoded, hit_encoded)
        sim_negative = torch.cosine_similarity(original_encoded, negative_encoded)
        
        logger.info(f"原片与爆款相似度: {sim_positive.item():.4f}")
        logger.info(f"原片与无关文本相似度: {sim_negative.item():.4f}")
    
    logger.info("对比学习模型演示完成!")


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="深度对比学习模型演示")
    args = parser.parse_args()
    
    # 运行演示
    demo_contrastive_learning() 