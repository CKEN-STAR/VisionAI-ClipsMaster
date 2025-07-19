"""
优化器工具模块

提供低资源环境下的优化器配置和训练辅助工具
"""

import os
import yaml
import math
import torch
import logging
from typing import Dict, Any, Optional, Union, List
from torch.optim import Optimizer
from torch.optim.lr_scheduler import _LRScheduler
from loguru import logger


class LinearWarmupScheduler(_LRScheduler):
    """
    带预热期的线性学习率调度器
    适合低资源环境下的模型训练
    """
    
    def __init__(
        self,
        optimizer: Optimizer,
        warmup_steps: int,
        max_steps: int,
        min_lr_ratio: float = 0.0,
        last_epoch: int = -1
    ):
        """
        初始化线性预热学习率调度器
        
        Args:
            optimizer: PyTorch优化器
            warmup_steps: 预热步数
            max_steps: 总训练步数
            min_lr_ratio: 最小学习率比例
            last_epoch: 上一轮索引
        """
        self.warmup_steps = warmup_steps
        self.max_steps = max_steps
        self.min_lr_ratio = min_lr_ratio
        super(LinearWarmupScheduler, self).__init__(optimizer, last_epoch)
    
    def get_lr(self):
        """获取当前学习率"""
        step = self.last_epoch
        
        # 预热阶段
        if step < self.warmup_steps:
            return [base_lr * (float(step) / float(max(1, self.warmup_steps)))
                    for base_lr in self.base_lrs]
        
        # 线性衰减阶段
        if step > self.max_steps:
            return [base_lr * self.min_lr_ratio for base_lr in self.base_lrs]
        
        decay_ratio = (step - self.warmup_steps) / (self.max_steps - self.warmup_steps)
        coeff = 1.0 - (1.0 - self.min_lr_ratio) * decay_ratio
        return [base_lr * coeff for base_lr in self.base_lrs]


def create_optimizer(
    model: torch.nn.Module,
    optimizer_name: str = "Adam",
    learning_rate: float = 2e-5,
    weight_decay: float = 0.01,
    **kwargs
) -> Optimizer:
    """
    创建优化器
    
    Args:
        model: 模型
        optimizer_name: 优化器名称，支持"Adam", "AdamW", "SGD"
        learning_rate: 学习率
        weight_decay: 权重衰减
        **kwargs: 其他优化器参数
        
    Returns:
        PyTorch优化器
    """
    # 区分权重衰减和不衰减参数
    no_decay = ["bias", "LayerNorm.weight"]
    
    optimizer_params = [
        {
            "params": [p for n, p in model.named_parameters() 
                       if not any(nd in n for nd in no_decay)],
            "weight_decay": weight_decay,
        },
        {
            "params": [p for n, p in model.named_parameters() 
                       if any(nd in n for nd in no_decay)],
            "weight_decay": 0.0,
        },
    ]
    
    # 创建优化器
    if optimizer_name.lower() == "adam":
        return torch.optim.Adam(optimizer_params, lr=learning_rate, **kwargs)
    elif optimizer_name.lower() == "adamw":
        return torch.optim.AdamW(optimizer_params, lr=learning_rate, **kwargs)
    elif optimizer_name.lower() == "sgd":
        return torch.optim.SGD(optimizer_params, lr=learning_rate, momentum=0.9, **kwargs)
    else:
        raise ValueError(f"不支持的优化器: {optimizer_name}")


def create_scheduler(
    optimizer: Optimizer,
    scheduler_name: str = "linear_warmup",
    num_training_steps: int = 1000,
    num_warmup_steps: int = 100,
    **kwargs
) -> Optional[_LRScheduler]:
    """
    创建学习率调度器
    
    Args:
        optimizer: PyTorch优化器
        scheduler_name: 调度器名称，支持"linear_warmup", "cosine", "constant"
        num_training_steps: 总训练步数
        num_warmup_steps: 预热步数
        **kwargs: 其他调度器参数
        
    Returns:
        学习率调度器或None
    """
    if scheduler_name == "linear_warmup":
        return LinearWarmupScheduler(
            optimizer,
            warmup_steps=num_warmup_steps,
            max_steps=num_training_steps,
            min_lr_ratio=kwargs.get("min_lr_ratio", 0.0)
        )
    elif scheduler_name == "cosine":
        from torch.optim.lr_scheduler import CosineAnnealingLR
        return CosineAnnealingLR(
            optimizer, 
            T_max=num_training_steps - num_warmup_steps,
            eta_min=kwargs.get("min_lr", 0)
        )
    elif scheduler_name == "constant":
        return None
    else:
        raise ValueError(f"不支持的调度器: {scheduler_name}")


class MemoryOptimizedTrainer:
    """
    内存优化训练器
    
    针对低资源环境优化的训练器，包含梯度累积、混合精度训练等功能
    """
    
    def __init__(
        self,
        model: torch.nn.Module,
        optimizer: Optimizer,
        scheduler: Optional[_LRScheduler] = None,
        gradient_accumulation_steps: int = 1,
        max_grad_norm: float = 1.0,
        use_mixed_precision: bool = False,
        use_gradient_checkpointing: bool = False
    ):
        """
        初始化训练器
        
        Args:
            model: 要训练的模型
            optimizer: 优化器
            scheduler: 学习率调度器
            gradient_accumulation_steps: 梯度累积步数
            max_grad_norm: 梯度裁剪值
            use_mixed_precision: 是否使用混合精度训练
            use_gradient_checkpointing: 是否使用梯度检查点
        """
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.max_grad_norm = max_grad_norm
        self.use_mixed_precision = use_mixed_precision
        self.global_step = 0  # 初始化全局步数
        
        # 配置混合精度训练
        self.scaler = torch.cuda.amp.GradScaler() if use_mixed_precision else None
        
        # 启用梯度检查点（如果模型支持）
        if use_gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"):
            model.gradient_checkpointing_enable()
            logger.info("启用梯度检查点以节省内存")
    
    def train_step(self, batch, return_loss: bool = True):
        """
        执行一步训练
        
        Args:
            batch: 一个批次的数据
            return_loss: 是否返回损失值
            
        Returns:
            训练损失（如果return_loss为True）
        """
        # 提取批次数据（假设batch是三元组形式的）
        anchor, positive, negative = batch
        
        # 切换到训练模式
        self.model.train()
        
        # 混合精度上下文
        amp_ctx = torch.cuda.amp.autocast() if self.use_mixed_precision else nullcontext()
        
        with amp_ctx:
            # 前向传播
            loss = self.model(anchor, positive, negative)
            
            # 梯度累积
            loss = loss / self.gradient_accumulation_steps
        
        # 反向传播
        if self.scaler:
            self.scaler.scale(loss).backward()
        else:
            loss.backward()
        
        loss_value = loss.item() * self.gradient_accumulation_steps
        
        # 检查是否需要更新参数
        if (self.global_step + 1) % self.gradient_accumulation_steps == 0:
            # 梯度裁剪
            if self.max_grad_norm > 0:
                if self.scaler:
                    self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
            
            # 更新参数
            if self.scaler:
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                self.optimizer.step()
            
            # 更新学习率
            if self.scheduler:
                self.scheduler.step()
            
            # 梯度清零
            self.optimizer.zero_grad()
        
        # 增加全局步数
        self.global_step += 1
        
        if return_loss:
            return loss_value
    
    @staticmethod
    def get_memory_usage():
        """获取当前显存/内存使用情况"""
        if torch.cuda.is_available():
            # 获取当前设备的显存
            current_device = torch.cuda.current_device()
            memory_allocated = torch.cuda.memory_allocated(current_device) / (1024 ** 2)  # MB
            memory_reserved = torch.cuda.memory_reserved(current_device) / (1024 ** 2)    # MB
            return {
                "allocated_mb": memory_allocated,
                "reserved_mb": memory_reserved
            }
        else:
            # 在CPU环境下，尝试使用psutil获取内存使用
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                return {
                    "rss_mb": memory_info.rss / (1024 ** 2),  # 常驻内存，MB
                    "vms_mb": memory_info.vms / (1024 ** 2)   # 虚拟内存，MB
                }
            except ImportError:
                return {"error": "无法获取内存使用情况，psutil未安装"}


class nullcontext:
    """简单的空上下文管理器，用于条件上下文"""
    
    def __enter__(self):
        return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def load_optimizer_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载优化器配置
    
    Args:
        config_path: 配置文件路径，为None时使用默认配置
        
    Returns:
        配置字典
    """
    # 默认配置
    default_config = {
        "optimizer": {
            "name": "Adam",
            "learning_rate": 2e-5,
            "weight_decay": 0.01,
            "eps": 1e-8
        },
        "scheduler": {
            "name": "linear_warmup",
            "warmup_ratio": 0.1,
            "min_lr_ratio": 0.0
        },
        "training": {
            "gradient_accumulation_steps": 1,
            "max_grad_norm": 1.0,
            "use_mixed_precision": False,
            "use_gradient_checkpointing": False
        }
    }
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"已加载优化器配置: {config_path}")
            
            # 合并配置
            merged_config = default_config.copy()
            for key in config:
                if key in merged_config and isinstance(config[key], dict) and isinstance(merged_config[key], dict):
                    merged_config[key].update(config[key])
                else:
                    merged_config[key] = config[key]
                    
            return merged_config
        except Exception as e:
            logger.error(f"加载优化器配置失败: {e}")
    
    logger.info("使用默认优化器配置")
    return default_config 