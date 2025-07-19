"""
活动模型配置加载器
用于从配置文件中加载当前激活的模型信息
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'active_model.yaml')

def load_active_model_config() -> Dict[str, Any]:
    """
    加载当前激活的模型配置
    
    Returns:
        Dict: 模型配置信息字典
    
    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置文件格式错误
    """
    try:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"模型配置文件不存在: {CONFIG_PATH}")
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise ValueError("模型配置文件为空")
        
        if 'active_model' not in config:
            raise ValueError("配置中缺少 'active_model' 字段")
        
        logger.info(f"已加载模型配置，当前激活模型: {config['active_model']}")
        return config
    except Exception as e:
        logger.error(f"加载模型配置失败: {str(e)}")
        raise

def get_model_config(model_name: str = None) -> Dict[str, Any]:
    """
    获取指定模型的配置信息
    
    Args:
        model_name: 模型名称，如果为None则返回当前激活模型的配置
    
    Returns:
        Dict: 模型配置信息
    """
    config = load_active_model_config()
    
    # 如果未指定模型名称，使用当前激活模型
    if model_name is None:
        model_name = config['active_model']
    
    # 检查模型是否存在
    if model_name not in config.get('models', {}):
        raise ValueError(f"未找到模型配置: {model_name}")
    
    return config['models'][model_name]

def get_available_models() -> List[str]:
    """
    获取所有可用模型列表
    
    Returns:
        List[str]: 模型名称列表
    """
    config = load_active_model_config()
    return list(config.get('models', {}).keys())

def get_installed_models() -> List[str]:
    """
    获取所有已安装的模型列表
    
    Returns:
        List[str]: 已安装的模型名称列表
    """
    config = load_active_model_config()
    return [
        model_name for model_name, model_config in config.get('models', {}).items()
        if model_config.get('installed', True)  # 默认为True表示已安装
    ]

def set_active_model(model_name: str) -> bool:
    """
    设置当前激活的模型
    
    Args:
        model_name: 要激活的模型名称
    
    Returns:
        bool: 是否设置成功
    """
    try:
        config = load_active_model_config()
        
        # 检查模型是否存在
        if model_name not in config.get('models', {}):
            logger.error(f"模型 {model_name} 不存在")
            return False
        
        # 更新配置
        config['active_model'] = model_name
        
        # 写回文件
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        logger.info(f"已将激活模型设置为: {model_name}")
        return True
    except Exception as e:
        logger.error(f"设置激活模型失败: {str(e)}")
        return False

def get_quantization_info(level: str = 'normal') -> Dict[str, Any]:
    """
    获取指定量化级别的配置信息
    
    Args:
        level: 量化级别，可选值: emergency, low, normal, high, max_quality
        
    Returns:
        Dict: 量化配置信息
    """
    config = load_active_model_config()
    
    quant_config = config.get('quantization', {})
    levels = quant_config.get('levels', {})
    memory_estimates = quant_config.get('memory_estimates', {})
    
    if level not in levels:
        logger.warning(f"未找到量化级别 {level}，使用 normal")
        level = 'normal'
    
    quant_type = levels[level]
    memory_estimate = memory_estimates.get(quant_type, 4.0)
    
    return {
        'level': level,
        'type': quant_type,
        'memory_gb': memory_estimate
    }

def get_optimal_quantization(available_memory_gb: float) -> str:
    """
    根据可用内存获取最优的量化级别
    
    Args:
        available_memory_gb: 可用内存(GB)
        
    Returns:
        str: 适合的量化级别
    """
    config = load_active_model_config()
    quant_config = config.get('quantization', {})
    memory_estimates = quant_config.get('memory_estimates', {})
    
    # 保留1GB系统运行内存
    safe_memory = max(0, available_memory_gb - 1.0)
    
    # 从小到大排序量化级别
    quant_levels = sorted([
        (level, memory_estimates.get(quant_type, 4.0))
        for level, quant_type in quant_config.get('levels', {}).items()
    ], key=lambda x: x[1])
    
    # 选择满足内存要求的最高质量级别
    selected_level = 'normal'  # 默认级别
    for level, memory_req in quant_levels:
        if memory_req <= safe_memory:
            selected_level = level
        else:
            break
    
    return selected_level

if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    try:
        config = load_active_model_config()
        print(f"当前激活模型: {config['active_model']}")
        
        models = get_available_models()
        print(f"可用模型: {models}")
        
        installed = get_installed_models()
        print(f"已安装模型: {installed}")
        
        print(f"Qwen2.5模型配置: {get_model_config('qwen2.5-7b-zh')}")
        
        print(f"标准量化级别配置: {get_quantization_info()}")
        print(f"紧急量化级别配置: {get_quantization_info('emergency')}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}") 