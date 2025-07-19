"""
深度对比学习模型

该模块实现了基于对比学习的短剧混剪训练策略，包含：
1. 三元组损失函数（Triplet Margin Loss）
2. 难样本挖掘（Hard Negative Mining）
3. 课程学习（Curriculum Learning）
4. 表示学习优化

通过对比学习训练模型识别原片与爆款混剪之间的模式差异，支持低资源环境下的模型训练。
"""

import os
import json
import yaml
import random
import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union, Callable
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from loguru import logger

from src.utils.memory_guard import track_memory
from src.utils.exceptions import ModelError, ErrorCode


class TripletMarginLoss(nn.Module):
    """
    三元组损失函数
    
    计算锚点样本（原片）与正样本（爆款）之间的相似度，并保持与负样本（随机/硬负样本）的距离
    """
    
    def __init__(self, margin: float = 1.0, reduction: str = 'mean'):
        """
        初始化三元组损失函数
        
        Args:
            margin: 边界值，控制正负样本之间的最小距离
            reduction: 归约方式，'none', 'mean', 'sum'
        """
        super(TripletMarginLoss, self).__init__()
        self.margin = margin
        self.reduction = reduction
    
    def forward(self, anchor: torch.Tensor, positive: torch.Tensor, 
                negative: torch.Tensor) -> torch.Tensor:
        """
        计算三元组损失
        
        Args:
            anchor: 锚点样本特征（原片）
            positive: 正样本特征（爆款）  
            negative: 负样本特征（随机/硬负样本）
            
        Returns:
            计算得到的损失值
        """
        # 计算欧氏距离
        distance_positive = F.pairwise_distance(anchor, positive)
        distance_negative = F.pairwise_distance(anchor, negative)
        
        # 计算三元组损失
        losses = F.relu(distance_positive - distance_negative + self.margin)
        
        # 应用归约方法
        if self.reduction == 'none':
            return losses
        elif self.reduction == 'mean':
            return losses.mean()
        elif self.reduction == 'sum':
            return losses.sum()
        else:
            raise ValueError(f"Unsupported reduction mode: {self.reduction}")


class DramaContrastiveDataset(Dataset):
    """
    短剧对比学习数据集
    
    将原片样本与对应的爆款样本组织为三元组形式
    """
    
    def __init__(self, data_path: str, transform: Optional[Callable] = None, 
                 hard_negative_mining: bool = False, use_curriculum: bool = False):
        """
        初始化数据集
        
        Args:
            data_path: 数据路径，包含原片-爆款对
            transform: 数据转换函数
            hard_negative_mining: 是否使用难样本挖掘
            use_curriculum: 是否使用课程学习
        """
        self.data_path = data_path
        self.transform = transform
        self.hard_negative_mining = hard_negative_mining
        self.use_curriculum = use_curriculum
        
        # 读取数据
        self.pairs = self._load_data()
        
        # 初始化难样本记录
        self.hard_negative_cache = {}
        
        # 课程学习难度等级
        self.curriculum_level = 0
        self.max_curriculum_levels = 3
        
        logger.info(f"加载了 {len(self.pairs)} 个原片-爆款对")
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """加载原片-爆款对数据"""
        try:
            if os.path.isdir(self.data_path):
                # 目录形式，加载多个文件
                pairs = []
                for file_name in os.listdir(self.data_path):
                    if file_name.endswith('.json'):
                        file_path = os.path.join(self.data_path, file_name)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            pairs.extend(json.load(f))
                return pairs
            else:
                # 单一文件
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return []
    
    def __len__(self) -> int:
        """获取数据集大小"""
        return len(self.pairs)
    
    def __getitem__(self, index: int) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        获取一个三元组样本
        
        Args:
            index: 样本索引
            
        Returns:
            三元组 (anchor, positive, negative)
        """
        # 获取锚点和正样本
        anchor = self.pairs[index]['origin']
        positive = self.pairs[index]['hit']
        
        # 根据策略选择负样本
        if self.hard_negative_mining and index in self.hard_negative_cache:
            # 使用缓存的难负样本
            negative_index = self.hard_negative_cache[index]
            negative = self.pairs[negative_index]['hit']
        else:
            # 随机选择负样本（不同于当前锚点的样本）
            negative_index = random.choice([i for i in range(len(self.pairs)) if i != index])
            negative = self.pairs[negative_index]['hit']
        
        # 应用转换
        if self.transform:
            anchor = self.transform(anchor)
            positive = self.transform(positive)
            negative = self.transform(negative)
        
        # 课程学习：根据难度级别调整样本
        if self.use_curriculum:
            positive, negative = self._apply_curriculum(positive, negative)
        
        return anchor, positive, negative
    
    def _apply_curriculum(self, positive: Dict[str, Any], negative: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        应用课程学习策略
        
        根据当前课程难度调整正负样本的差异度
        
        Args:
            positive: 正样本
            negative: 负样本
            
        Returns:
            调整后的 (positive, negative)
        """
        # 根据课程级别调整样本难度
        if self.curriculum_level == 0:
            # 初级：增强正负样本差异
            pass
        elif self.curriculum_level == 1:
            # 中级：保持原样
            pass
        elif self.curriculum_level == 2:
            # 高级：增加挑战性
            pass
        
        return positive, negative
    
    def update_hard_negatives(self, indices: List[int], hard_negative_indices: List[int]):
        """
        更新难负样本缓存
        
        Args:
            indices: 原样本索引
            hard_negative_indices: 对应的难负样本索引
        """
        for idx, neg_idx in zip(indices, hard_negative_indices):
            self.hard_negative_cache[idx] = neg_idx
    
    def update_curriculum_level(self, level: int):
        """
        更新课程学习难度级别
        
        Args:
            level: 新的难度级别
        """
        self.curriculum_level = min(level, self.max_curriculum_levels - 1)
        logger.info(f"课程学习难度更新为 {self.curriculum_level}")


class DramaContrastiveModel(nn.Module):
    """
    短剧对比学习模型
    
    使用预训练编码器提取特征，通过对比学习方式训练识别爆款模式
    """
    
    def __init__(self, model_path: Optional[str] = None, hidden_size: int = 768):
        """
        初始化模型
        
        Args:
            model_path: 预训练模型路径，None时使用默认配置
            hidden_size: 隐藏层大小
        """
        super(DramaContrastiveModel, self).__init__()
        
        # 加载配置
        self.config = self._load_config()
        
        # 设置模型路径
        if model_path:
            self.model_path = model_path
        else:
            self.model_path = self.config.get("model_path", "models/shared/bert-base-chinese")
        
        # 初始化编码器（使用轻量级方案，适合低资源环境）
        self._init_encoder()
        
        # 映射层
        self.projection = nn.Sequential(
            nn.Linear(hidden_size, 512),
            nn.ReLU(),
            nn.Linear(512, 256)
        )
        
        # 损失函数
        margin = self.config.get("margin", 1.0)
        self.loss_fn = TripletMarginLoss(margin=margin)
        
        logger.info(f"短剧对比学习模型初始化完成，使用编码器: {self.model_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join("configs", "contrastive_learning.yaml")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info("加载对比学习配置成功")
                return config
        except Exception as e:
            logger.warning(f"加载配置失败: {e}")
        
        # 默认配置
        return {
            "model_path": "models/shared/bert-base-chinese",
            "margin": 1.0,
            "learning_rate": 1e-5,
            "batch_size": 8,
            "epochs": 10,
            "use_hard_negative_mining": True,
            "use_curriculum_learning": True
        }
    
    def _init_encoder(self):
        """初始化编码器"""
        try:
            # 轻量级解决方案：使用预训练好的词向量和简单RNN
            # 在低资源环境中避免加载完整的BERT模型
            import gensim.downloader as gensim_downloader
            
            # 检查是否有预缓存的词向量
            cache_dir = Path(os.path.expanduser("~/.cache/visionai/embeddings"))
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            vectors_path = cache_dir / "word2vec_cn.model"
            
            if vectors_path.exists():
                from gensim.models import KeyedVectors
                self.word_vectors = KeyedVectors.load(str(vectors_path))
                vocab_size = len(self.word_vectors.key_to_index)
                vector_size = self.word_vectors.vector_size
            else:
                # 先使用小型词向量模型
                try:
                    self.word_vectors = gensim_downloader.load("glove-wiki-gigaword-100")
                    vocab_size = len(self.word_vectors.key_to_index)
                    vector_size = self.word_vectors.vector_size
                except Exception:
                    # 如果下载失败，使用随机初始化的词向量
                    logger.warning("无法下载预训练词向量，使用随机初始化")
                    vocab_size = 10000  # 假设词表大小
                    vector_size = 100   # 词向量维度
            
            # 创建嵌入层和编码器
            self.embedding = nn.Embedding(vocab_size, vector_size)
            
            # 使用GRU作为编码器
            self.encoder = nn.GRU(
                input_size=vector_size,
                hidden_size=768,
                num_layers=2,
                batch_first=True,
                bidirectional=True
            )
            
            # 如果加载了预训练词向量，初始化嵌入层
            if hasattr(self, 'word_vectors'):
                embedding_matrix = np.zeros((vocab_size, vector_size))
                for word, i in self.word_vectors.key_to_index.items():
                    if i < vocab_size:  # 只使用vocab_size个词
                        embedding_matrix[i] = self.word_vectors[word]
                self.embedding.weight.data.copy_(torch.from_numpy(embedding_matrix))
            
            logger.info(f"使用轻量级编码器: 词表大小={vocab_size}, 向量维度={vector_size}")
            
        except ImportError:
            logger.warning("无法导入gensim，使用随机初始化的编码器")
            # 如果无法加载预训练模型，使用随机初始化的编码器
            vocab_size = 10000  # 假设词表大小
            vector_size = 100   # 词向量维度
            
            self.embedding = nn.Embedding(vocab_size, vector_size)
            self.encoder = nn.GRU(
                input_size=vector_size,
                hidden_size=768,
                num_layers=2,
                batch_first=True,
                bidirectional=True
            )
    
    @track_memory("contrastive_model_forward")
    def forward(self, anchor, positive, negative):
        """
        前向传播
        
        Args:
            anchor: 锚点样本（原片）
            positive: 正样本（爆款）
            negative: 负样本（随机或难样本）
            
        Returns:
            三元组损失值
        """
        # 编码样本
        anchor_encoded = self._encode(anchor)
        positive_encoded = self._encode(positive)
        negative_encoded = self._encode(negative)
        
        # 投影到特征空间
        anchor_projection = self.projection(anchor_encoded)
        positive_projection = self.projection(positive_encoded)
        negative_projection = self.projection(negative_encoded)
        
        # 归一化特征向量
        anchor_norm = F.normalize(anchor_projection, p=2, dim=1)
        positive_norm = F.normalize(positive_projection, p=2, dim=1)
        negative_norm = F.normalize(negative_projection, p=2, dim=1)
        
        # 计算损失
        loss = self.loss_fn(anchor_norm, positive_norm, negative_norm)
        
        return loss
    
    def _encode(self, x):
        """编码输入数据"""
        # 这里简化处理，假设x已经是词索引序列
        # 实际应用中需要分词并转换为索引
        
        # 应用嵌入层
        embedded = self.embedding(x)
        
        # 通过编码器
        output, hidden = self.encoder(embedded)
        
        # 使用最后一个时间步的隐藏状态
        # 双向GRU，连接前向和后向的最后隐藏状态
        hidden = torch.cat((hidden[-2], hidden[-1]), dim=1)
        
        return hidden
    
    def encode_script(self, script: str) -> torch.Tensor:
        """
        编码脚本文本
        
        Args:
            script: 脚本文本
            
        Returns:
            编码后的特征向量
        """
        # TODO: 实现文本编码
        # 简化实现，返回随机特征
        return torch.randn(1, 768)
    
    def save(self, path: str):
        """
        保存模型
        
        Args:
            path: 保存路径
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': self.config
        }, path)
        logger.info(f"模型已保存到 {path}")
    
    def load(self, path: str):
        """
        加载模型
        
        Args:
            path: 模型路径
        """
        try:
            checkpoint = torch.load(path, map_location='cpu')
            self.load_state_dict(checkpoint['model_state_dict'])
            self.config = checkpoint.get('config', self.config)
            logger.info(f"模型已加载自 {path}")
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise ModelError(f"加载模型失败: {e}", ErrorCode.MODEL_LOAD_ERROR)


class HardNegativeMiner:
    """
    难样本挖掘器
    
    在训练过程中找出最具挑战性的负样本，提高模型的鉴别能力
    """
    
    def __init__(self, model, dataloader, device='cpu'):
        """
        初始化难样本挖掘器
        
        Args:
            model: 对比学习模型
            dataloader: 数据加载器
            device: 计算设备
        """
        self.model = model
        self.dataloader = dataloader
        self.device = device
    
    @track_memory("hard_negative_mining")
    def mine_hard_negatives(self, top_k: int = 5) -> Dict[int, int]:
        """
        挖掘难负样本
        
        Args:
            top_k: 每个样本保留的最难负样本数量
            
        Returns:
            样本索引到难负样本索引的映射
        """
        logger.info("开始难负样本挖掘...")
        self.model.eval()
        
        # 计算所有样本的特征向量
        sample_indices = []
        features = []
        
        with torch.no_grad():
            for i, (indices, anchors, _) in enumerate(tqdm(self.dataloader, desc="特征提取")):
                batch_features = self.model._encode(anchors.to(self.device))
                features.append(batch_features.cpu())
                sample_indices.extend(indices.tolist())
        
        # 合并特征
        features = torch.cat(features, dim=0)
        
        # 计算样本间的相似度矩阵
        similarity = torch.mm(features, features.t())
        
        # 对每个样本找出最难的负样本
        hard_negative_indices = {}
        
        for i, idx in enumerate(sample_indices):
            # 排除自身
            sim_scores = similarity[i].clone()
            sim_scores[i] = -float('inf')
            
            # 找出最相似的样本作为难负样本
            _, hard_indices = sim_scores.topk(min(top_k, len(sample_indices) - 1))
            hard_negative_indices[idx] = sample_indices[hard_indices[0].item()]
        
        logger.info(f"难负样本挖掘完成，找到 {len(hard_negative_indices)} 个难样本")
        return hard_negative_indices


class CurriculumScheduler:
    """
    课程学习调度器
    
    控制训练过程中的课程难度，逐步增加训练难度
    """
    
    def __init__(self, dataset, num_epochs, steps_per_level=None):
        """
        初始化课程学习调度器
        
        Args:
            dataset: 对比学习数据集
            num_epochs: 总训练轮数
            steps_per_level: 每个难度级别的步数，默认为总步数的三分之一
        """
        self.dataset = dataset
        self.num_epochs = num_epochs
        self.max_levels = dataset.max_curriculum_levels
        
        if steps_per_level is None:
            self.steps_per_level = num_epochs // self.max_levels
        else:
            self.steps_per_level = steps_per_level
    
    def update(self, epoch: int):
        """
        更新课程难度
        
        Args:
            epoch: 当前训练轮数
        """
        level = min(epoch // self.steps_per_level, self.max_levels - 1)
        self.dataset.update_curriculum_level(level)
        
        return level


def train_contrastive_model(
    data_path: str,
    model_save_path: str,
    learning_rate: float = 1e-5,
    batch_size: int = 8,
    epochs: int = 10,
    use_hard_negative_mining: bool = True,
    use_curriculum_learning: bool = True,
    device: str = 'cpu'
):
    """
    训练对比学习模型
    
    Args:
        data_path: 训练数据路径
        model_save_path: 模型保存路径
        learning_rate: 学习率
        batch_size: 批次大小
        epochs: 训练轮数
        use_hard_negative_mining: 是否使用难样本挖掘
        use_curriculum_learning: 是否使用课程学习
        device: 计算设备
    
    Returns:
        训练好的模型
    """
    # 创建数据集
    dataset = DramaContrastiveDataset(
        data_path=data_path,
        hard_negative_mining=use_hard_negative_mining,
        use_curriculum=use_curriculum_learning
    )
    
    # 创建数据加载器
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0  # 低资源环境设置为0
    )
    
    # 创建模型
    model = DramaContrastiveModel().to(device)
    
    # 优化器
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    # 课程学习调度器
    if use_curriculum_learning:
        curriculum_scheduler = CurriculumScheduler(dataset, epochs)
    
    # 训练循环
    logger.info(f"开始训练，总轮数: {epochs}")
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        # 更新课程难度
        if use_curriculum_learning:
            level = curriculum_scheduler.update(epoch)
            logger.info(f"Epoch {epoch+1}/{epochs}，课程难度: {level+1}/{dataset.max_curriculum_levels}")
        else:
            logger.info(f"Epoch {epoch+1}/{epochs}")
        
        # 难样本挖掘
        if use_hard_negative_mining and epoch > 0 and epoch % 2 == 0:
            miner = HardNegativeMiner(model, dataloader, device)
            hard_negatives = miner.mine_hard_negatives()
            for idx, neg_idx in hard_negatives.items():
                dataset.hard_negative_cache[idx] = neg_idx
        
        # 训练步骤
        for i, (anchor, positive, negative) in enumerate(tqdm(dataloader, desc=f"Epoch {epoch+1}")):
            # 转移到设备
            anchor = anchor.to(device)
            positive = positive.to(device)
            negative = negative.to(device)
            
            # 前向传播
            loss = model(anchor, positive, negative)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        # 输出训练信息
        avg_loss = total_loss / len(dataloader)
        logger.info(f"Epoch {epoch+1}/{epochs}, 平均损失: {avg_loss:.4f}")
        
        # 每10轮保存一次模型
        if (epoch + 1) % 10 == 0:
            model.save(f"{model_save_path}_epoch{epoch+1}.pt")
    
    # 保存最终模型
    model.save(model_save_path)
    
    logger.info(f"训练完成，模型已保存到 {model_save_path}")
    return model 