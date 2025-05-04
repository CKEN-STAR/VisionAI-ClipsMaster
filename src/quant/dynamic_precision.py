"""动态精度分层配置模块

此模块负责模型不同层的动态精度配置，包括:
1. 注意力层配置
2. 嵌入层配置
3. 前馈层配置
4. 自适应位宽调整
5. 层间依赖分析
"""

import yaml
from typing import Dict, List, Optional, Union
from pathlib import Path
from loguru import logger
import torch
import numpy as np

class DynamicPrecisionConfig:
    """动态精度配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        # 默认配置
        self.default_config = {
            'attention': {
                'bits': 8,    # 注意力层位宽
                'scheme': 'dynamic',  # 量化方案
                'threshold': 0.1      # 精度阈值
            },
            'embedding': {
                'bits': 4,    # 嵌入层位宽
                'scheme': 'static',
                'threshold': 0.2
            },
            'ffn': {
                'bits': 6,    # 前馈层位宽
                'scheme': 'dynamic',
                'threshold': 0.15
            }
        }
        
        self.config = self.default_config.copy()
        if config_path:
            self.load_config(config_path)
            
        # 层间依赖关系
        self.layer_dependencies = {
            'attention': ['embedding'],
            'ffn': ['attention'],
            'embedding': []
        }
        
        # 性能影响权重
        self.impact_weights = {
            'attention': 0.4,
            'embedding': 0.3,
            'ffn': 0.3
        }
    
    def load_config(self, config_path: str):
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                
            # 更新配置，保留默认值
            for layer_type, settings in loaded_config.items():
                if layer_type in self.config:
                    self.config[layer_type].update(settings)
                    
            logger.info(f"已加载配置文件: {config_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            logger.info("使用默认配置")
    
    def get_layer_config(self, layer_type: str) -> Dict:
        """获取层配置
        
        Args:
            layer_type: 层类型
            
        Returns:
            Dict: 层配置
        """
        return self.config.get(layer_type, {})
    
    def adjust_precision(self,
                        layer_type: str,
                        metrics: Dict[str, float],
                        constraints: Optional[Dict] = None) -> Dict:
        """调整层精度
        
        Args:
            layer_type: 层类型
            metrics: 性能指标
            constraints: 约束条件
            
        Returns:
            Dict: 调整后的配置
        """
        if layer_type not in self.config:
            raise ValueError(f"未知的层类型: {layer_type}")
            
        current_config = self.config[layer_type].copy()
        
        # 检查依赖层的配置
        for dep_layer in self.layer_dependencies[layer_type]:
            dep_config = self.config[dep_layer]
            if dep_config['bits'] > current_config['bits']:
                logger.warning(f"{layer_type}层的位宽不应低于{dep_layer}层")
                current_config['bits'] = dep_config['bits']
        
        # 根据性能指标调整
        if metrics.get('accuracy', 1.0) < current_config['threshold']:
            # 精度不足，增加位宽
            current_config['bits'] = min(current_config['bits'] + 2, 8)
            logger.info(f"增加{layer_type}层位宽到{current_config['bits']}bits")
        
        # 应用约束条件
        if constraints:
            if 'max_bits' in constraints:
                current_config['bits'] = min(current_config['bits'], 
                                          constraints['max_bits'])
            if 'min_bits' in constraints:
                current_config['bits'] = max(current_config['bits'],
                                          constraints['min_bits'])
        
        return current_config
    
    def optimize_layer_distribution(self, 
                                 performance_metrics: Dict[str, Dict[str, float]]) -> Dict:
        """优化层间精度分布
        
        Args:
            performance_metrics: 各层性能指标
            
        Returns:
            Dict: 优化后的配置
        """
        optimized_config = {}
        
        # 计算每层的重要性得分
        importance_scores = {}
        for layer_type, metrics in performance_metrics.items():
            accuracy = metrics.get('accuracy', 1.0)
            speed = metrics.get('speed', 1.0)
            memory = metrics.get('memory', 1.0)
            
            # 综合得分计算
            score = (
                accuracy * 0.5 +     # 精度权重
                speed * 0.3 +       # 速度权重
                memory * 0.2        # 内存权重
            ) * self.impact_weights[layer_type]
            
            importance_scores[layer_type] = score
        
        # 根据重要性分配位宽
        total_score = sum(importance_scores.values())
        for layer_type, score in importance_scores.items():
            relative_importance = score / total_score
            
            # 基于重要性动态分配位宽
            base_bits = self.config[layer_type]['bits']
            adjusted_bits = max(4, min(8, round(base_bits * (1 + relative_importance))))
            
            optimized_config[layer_type] = {
                **self.config[layer_type],
                'bits': adjusted_bits
            }
        
        return optimized_config
    
    def analyze_layer_impact(self, layer_configs: Dict) -> Dict[str, float]:
        """分析层配置影响
        
        Args:
            layer_configs: 层配置
            
        Returns:
            Dict[str, float]: 影响分析结果
        """
        impact_analysis = {}
        
        for layer_type, config in layer_configs.items():
            # 计算精度影响
            precision_impact = 1.0 - (config['bits'] / 8.0)
            
            # 计算性能影响
            performance_impact = 0.0
            if config['scheme'] == 'dynamic':
                performance_impact = 0.2  # 动态方案的额外开销
            
            # 计算内存影响
            memory_impact = 1.0 - (config['bits'] / 32.0)  # 相对于FP32
            
            # 综合影响评分
            total_impact = (
                precision_impact * 0.4 +
                performance_impact * 0.3 +
                memory_impact * 0.3
            )
            
            impact_analysis[layer_type] = total_impact
        
        return impact_analysis
    
    def export_config(self, output_path: str):
        """导出配置
        
        Args:
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置已导出到: {output_path}")
        except Exception as e:
            logger.error(f"导出配置失败: {str(e)}")
    
    def validate_config(self) -> bool:
        """验证配置有效性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查必要的层类型
            required_layers = {'attention', 'embedding', 'ffn'}
            if not all(layer in self.config for layer in required_layers):
                return False
            
            # 验证位宽范围
            for layer_type, config in self.config.items():
                if not (4 <= config['bits'] <= 8):
                    logger.error(f"{layer_type}层位宽超出范围[4,8]: {config['bits']}")
                    return False
                
                if config['scheme'] not in ['static', 'dynamic']:
                    logger.error(f"{layer_type}层量化方案无效: {config['scheme']}")
                    return False
                
                if not (0 < config['threshold'] < 1):
                    logger.error(f"{layer_type}层阈值超出范围(0,1): {config['threshold']}")
                    return False
            
            # 验证层间依赖关系
            for layer_type, deps in self.layer_dependencies.items():
                layer_bits = self.config[layer_type]['bits']
                for dep_layer in deps:
                    if self.config[dep_layer]['bits'] > layer_bits:
                        logger.error(f"层间位宽依赖关系不满足: {layer_type} -> {dep_layer}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return False 