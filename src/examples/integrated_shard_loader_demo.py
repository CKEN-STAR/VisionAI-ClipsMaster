#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
集成分片加载器演示

此示例展示了按需加载引擎、分片管理器和分片加载适配器如何协同工作，
实现大型模型的高效分片加载和内存管理。
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入所需模块
try:
    from src.core.on_demand_loader import OnDemandLoader, ModelLoadRequest
    from src.core.shard_loader_adapter import ShardLoaderAdapter
    from src.sharding.metadata_manager import MetadataManager
    from src.sharding.cache_manager import ShardManager
    from src.utils.memory_guard import MemoryGuard
    from src.utils.memory_manager import MemoryManager
except ImportError as e:
    logger.error(f"导入模块失败: {str(e)}")
    sys.exit(1)

def print_separator(title=""):
    """打印分隔线"""
    width = 80
    print("\n" + "=" * width)
    if title:
        print(f"{title.center(width)}")
        print("-" * width)

def create_test_environment():
    """创建测试环境
    
    Returns:
        Dict: 包含测试环境中的组件
    """
    print_separator("创建测试环境")
    
    # 创建临时目录
    test_dir = ".test_env"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模型目录结构
    models_dir = os.path.join(test_dir, "models")
    configs_dir = os.path.join(test_dir, "configs")
    cache_dir = os.path.join(test_dir, "cache")
    metadata_dir = os.path.join(test_dir, "metadata")
    
    # 创建目录
    for d in [models_dir, configs_dir, os.path.join(configs_dir, "models"), 
              os.path.join(configs_dir, "models", "available_models"), 
              cache_dir, metadata_dir]:
        os.makedirs(d, exist_ok=True)
    
    # 创建测试模型目录
    test_model_dirs = ["qwen2.5-7b-zh", "test_model"]
    for model_name in test_model_dirs:
        model_dir = os.path.join(models_dir, model_name)
        os.makedirs(model_dir, exist_ok=True)
        # 创建分片目录
        os.makedirs(os.path.join(model_dir, "shards"), exist_ok=True)
    
    # 创建配置文件
    create_test_config_files(configs_dir)
    
    # 创建测试元数据
    metadata_manager = MetadataManager(metadata_dir=metadata_dir)
    create_test_metadata(metadata_manager)
    
    # 创建内存守卫和内存管理器
    memory_guard = MemoryGuard()
    memory_manager = MemoryManager()
    
    # 创建按需加载引擎
    on_demand_loader = OnDemandLoader(
        config_dir=os.path.join(configs_dir, "models"),
        model_dir=models_dir,
        cache_dir=cache_dir,
        memory_guard=memory_guard,
        memory_manager=memory_manager
    )
    
    # 创建分片加载适配器
    shard_loader = ShardLoaderAdapter(
        on_demand_loader=on_demand_loader,
        metadata_manager=metadata_manager,
        models_dir=models_dir,
        cache_dir=cache_dir
    )
    
    print("测试环境创建完成")
    
    return {
        "test_dir": test_dir,
        "models_dir": models_dir,
        "configs_dir": configs_dir,
        "cache_dir": cache_dir,
        "metadata_dir": metadata_dir,
        "memory_guard": memory_guard,
        "memory_manager": memory_manager,
        "on_demand_loader": on_demand_loader,
        "shard_loader": shard_loader,
        "metadata_manager": metadata_manager
    }

def create_test_config_files(configs_dir):
    """创建测试配置文件
    
    Args:
        configs_dir: 配置文件目录
    """
    # 创建active_model.yaml
    active_model_content = """# 活动模型配置
language: zh
model: qwen2.5-7b-zh

# 量化配置
quantization:
  default: int8
  levels:
    int4: {memory_factor: 0.3, quality_factor: 0.7}
    int8: {memory_factor: 0.5, quality_factor: 0.9}
    fp16: {memory_factor: 1.0, quality_factor: 1.0}

# 模型配置
models:
  qwen2.5-7b-zh:
    language: zh
    priority: 1
    installed: true
    memory_estimate: 7000
    prefetch_shards: ["shard_1", "shard_2"]
    max_shards_in_memory: 3
  
  test_model:
    language: zh
    priority: 2
    installed: true
    memory_estimate: 5000
    prefetch_shards: ["shard_1"]
    max_shards_in_memory: 2
"""
    
    with open(os.path.join(configs_dir, "models", "active_model.yaml"), "w", encoding="utf-8") as f:
        f.write(active_model_content)
    
    # 创建qwen2.5-7b-zh.yaml
    qwen_content = """# 千问2.5-7B中文模型配置
name: qwen2.5-7b-zh
language: zh
type: chat
family: qwen
version: 2.5
size: 7B
formats:
  - gguf
  - safetensors

# 模型路径
model_path: models/qwen2.5-7b-zh/model.gguf
tokenizer_path: models/qwen2.5-7b-zh/tokenizer.json

# 分片配置
use_sharding: true
shard_dir: models/qwen2.5-7b-zh/shards
metadata_path: metadata/qwen2.5-7b-zh.json

# 性能设置
context_length: 8192
lora_support: true
kv_cache_enabled: true
"""
    
    with open(os.path.join(configs_dir, "models", "available_models", "qwen2.5-7b-zh.yaml"), 
              "w", encoding="utf-8") as f:
        f.write(qwen_content)
    
    # 创建test_model.yaml
    test_model_content = """# 测试模型配置
name: test_model
language: zh
type: base
family: test
version: 1.0
size: 5B
formats:
  - gguf

# 模型路径
model_path: models/test_model/model.gguf
tokenizer_path: models/test_model/tokenizer.json

# 分片配置
use_sharding: true
shard_dir: models/test_model/shards
metadata_path: metadata/test_model.json

# 性能设置
context_length: 4096
lora_support: false
kv_cache_enabled: true
"""
    
    with open(os.path.join(configs_dir, "models", "available_models", "test_model.yaml"), 
              "w", encoding="utf-8") as f:
        f.write(test_model_content)
        
    logger.info("测试配置文件创建完成")

def create_test_metadata(metadata_manager):
    """创建测试元数据
    
    Args:
        metadata_manager: 元数据管理器
    """
    # 为qwen2.5-7b-zh创建测试元数据
    qwen_metadata = metadata_manager.create_metadata("qwen2.5-7b-zh")
    
    # 添加分片元数据
    qwen_metadata.add_shard(
        shard_id="shard_1",
        layers=["embedding", "positional_encoding"],
        shard_path="shard_1.bin",
        shard_size=100*1024*1024
    )
    
    qwen_metadata.add_shard(
        shard_id="shard_2",
        layers=["attention_1", "ffn_1"],
        depends_on=["shard_1"],
        shard_path="shard_2.bin",
        shard_size=80*1024*1024
    )
    
    qwen_metadata.add_shard(
        shard_id="shard_3",
        layers=["attention_2", "ffn_2"],
        depends_on=["shard_2"],
        shard_path="shard_3.bin",
        shard_size=80*1024*1024
    )
    
    qwen_metadata.add_shard(
        shard_id="shard_4",
        layers=["attention_3", "ffn_3"],
        depends_on=["shard_1"],
        shard_path="shard_4.bin",
        shard_size=80*1024*1024
    )
    
    qwen_metadata.add_shard(
        shard_id="shard_5",
        layers=["decoder_head"],
        depends_on=["shard_3", "shard_4"],
        shard_path="shard_5.bin",
        shard_size=50*1024*1024
    )
    
    # 为test_model创建测试元数据
    test_metadata = metadata_manager.create_metadata("test_model")
    
    test_metadata.add_shard(
        shard_id="shard_1",
        layers=["embedding", "positional_encoding"],
        shard_path="shard_1.bin",
        shard_size=50*1024*1024
    )
    
    test_metadata.add_shard(
        shard_id="shard_2",
        layers=["attention_1", "attention_2"],
        depends_on=["shard_1"],
        shard_path="shard_2.bin",
        shard_size=60*1024*1024
    )
    
    test_metadata.add_shard(
        shard_id="shard_3",
        layers=["ffn_1", "ffn_2"],
        depends_on=["shard_2"],
        shard_path="shard_3.bin",
        shard_size=40*1024*1024
    )
    
    # 保存元数据
    metadata_manager.save_metadata("qwen2.5-7b-zh")
    metadata_manager.save_metadata("test_model")
    
    logger.info("测试元数据创建完成")

def cleanup_test_environment(test_dir):
    """清理测试环境
    
    Args:
        test_dir: 测试目录
    """
    print_separator("清理测试环境")
    
    # 检查目录是否存在
    if os.path.exists(test_dir):
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"已删除测试目录: {test_dir}")
        except Exception as e:
            logger.error(f"删除测试目录失败: {str(e)}")
    
    print("测试环境清理完成")

def demo_integrated_shard_loading(env):
    """演示集成的分片加载功能
    
    Args:
        env: 测试环境
    """
    print_separator("集成分片加载演示")
    
    on_demand_loader = env["on_demand_loader"]
    shard_loader = env["shard_loader"]
    
    # 1. 获取可用模型
    print("\n1. 获取可用模型")
    available_models = on_demand_loader.get_available_models()
    for model in available_models:
        print(f"  - {model['name']} ({model['language']})")
    
    # 2. 模拟加载模型
    print("\n2. 加载模型并触发分片预加载")
    model_name = "qwen2.5-7b-zh"
    print(f"  加载模型: {model_name}")
    
    # 创建加载请求
    request = ModelLoadRequest(
        model_name=model_name,
        language="zh",
        priority=0,
        force_load=True
    )
    
    # 加载模型并通知分片加载适配器
    success = on_demand_loader.load_model(request)
    if success:
        print(f"  模型 {model_name} 加载成功")
        shard_loader.on_model_activated(model_name)
    else:
        print(f"  模型 {model_name} 加载失败")
    
    # 3. 检查分片管理器状态
    print("\n3. 检查分片管理器状态")
    shard_manager = shard_loader.get_shard_manager(model_name)
    if shard_manager:
        # 获取缓存统计
        stats = shard_manager.get_cache_stats()
        print(f"  当前缓存分片数: {stats['current_size']}/{stats['max_size']}")
        print(f"  已缓存分片: {shard_manager.shard_cache.get_cached_shards()}")
    
    # 4. 演示按层加载
    print("\n4. 按层加载分片")
    target_layer = "attention_2"
    print(f"  加载层: {target_layer}")
    
    # 获取包含该层的分片
    shard_data = shard_loader.load_model_layer(model_name, target_layer)
    if shard_data:
        print(f"  层 {target_layer} 已加载，所在分片: {shard_data['id']}")
        
        # 查看当前缓存状态
        stats = shard_manager.get_cache_stats()
        print(f"  当前缓存分片数: {stats['current_size']}/{stats['max_size']}")
        print(f"  已缓存分片: {shard_manager.shard_cache.get_cached_shards()}")
    else:
        print(f"  层 {target_layer} 加载失败")
    
    # 5. 演示加载依赖复杂的分片
    print("\n5. 加载具有复杂依赖的分片")
    target_shard = "shard_5"
    print(f"  加载分片: {target_shard}（依赖于分片3和4）")
    
    # 获取加载顺序
    loading_sequence = shard_manager.get_loading_sequence([target_shard])
    print(f"  加载顺序: {loading_sequence}")
    
    # 加载分片
    shard_data = shard_loader.load_model_shard(model_name, target_shard)
    if shard_data:
        print(f"  分片 {target_shard} 已加载")
        
        # 查看当前缓存状态
        stats = shard_manager.get_cache_stats()
        print(f"  当前缓存分片数: {stats['current_size']}/{stats['max_size']}")
        print(f"  已缓存分片: {shard_manager.shard_cache.get_cached_shards()}")
    else:
        print(f"  分片 {target_shard} 加载失败")
    
    # 6. 演示切换模型
    print("\n6. 切换到另一个模型")
    new_model = "test_model"
    print(f"  切换到模型: {new_model}")
    
    # 卸载当前模型
    shard_loader.on_model_deactivated(model_name)
    
    # 加载新模型
    request = ModelLoadRequest(
        model_name=new_model,
        language="zh",
        priority=0,
        force_load=True
    )
    
    # 加载模型并通知分片加载适配器
    success = on_demand_loader.load_model(request)
    if success:
        print(f"  模型 {new_model} 加载成功")
        shard_loader.on_model_activated(new_model)
        
        # 获取新模型的分片管理器
        new_shard_manager = shard_loader.get_shard_manager(new_model)
        if new_shard_manager:
            # 获取缓存统计
            stats = new_shard_manager.get_cache_stats()
            print(f"  当前缓存分片数: {stats['current_size']}/{stats['max_size']}")
            print(f"  已缓存分片: {new_shard_manager.shard_cache.get_cached_shards()}")
    else:
        print(f"  模型 {new_model} 加载失败")
    
    # 7. 清理所有缓存
    print("\n7. 清理所有模型缓存")
    shard_loader.clear_all_caches()
    print("  所有模型缓存已清理")

def main():
    """主函数"""
    print_separator("集成分片加载器演示")
    print("本示例展示分片加载适配器如何与按需加载引擎协同工作")
    
    try:
        # 创建测试环境
        env = create_test_environment()
        
        # 运行演示
        demo_integrated_shard_loading(env)
        
        # 清理测试环境
        cleanup_test_environment(env["test_dir"])
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print_separator("演示完成")

if __name__ == "__main__":
    main() 