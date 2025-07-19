#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
释放后校验系统

该模块负责在资源释放后执行校验，确保资源被正确释放，无残留和内存泄漏。
主要功能包括：
1. 模型分片释放验证
2. 缓存文件清理验证
3. 内存地址扫描
4. GPU显存验证（如果可用）
"""

import os
import gc
import sys
import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('post_release_check')

# 导入内存管理相关模块
from src.utils.memory_guard import memory_guard

# 全局资源跟踪
_loaded_shards = set()  # 跟踪已加载的模型分片
_active_caches = {}     # 跟踪活跃的缓存文件
_resource_references = {}  # 跟踪资源引用

# 缓存路径前缀
CACHE_DIR = os.path.join("models", "cache")

def register_shard(res_id: str) -> None:
    """注册模型分片加载
    
    Args:
        res_id: 资源标识符
    """
    global _loaded_shards
    _loaded_shards.add(res_id)
    logger.debug(f"注册模型分片: {res_id}")
    
def unregister_shard(res_id: str) -> None:
    """取消注册模型分片
    
    Args:
        res_id: 资源标识符
    """
    global _loaded_shards
    if res_id in _loaded_shards:
        _loaded_shards.remove(res_id)
        logger.debug(f"取消注册模型分片: {res_id}")
        
def register_cache(res_id: str, file_path: str) -> None:
    """注册缓存文件
    
    Args:
        res_id: 资源标识符
        file_path: 缓存文件路径
    """
    global _active_caches
    _active_caches[res_id] = file_path
    logger.debug(f"注册缓存文件: {res_id} -> {file_path}")
    
def unregister_cache(res_id: str) -> None:
    """取消注册缓存文件
    
    Args:
        res_id: 资源标识符
    """
    global _active_caches
    if res_id in _active_caches:
        del _active_caches[res_id]
        logger.debug(f"取消注册缓存文件: {res_id}")
        
def get_cache_path(res_id: str) -> str:
    """获取缓存文件路径
    
    Args:
        res_id: 资源标识符
        
    Returns:
        str: 缓存文件路径
    """
    global _active_caches
    return _active_caches.get(res_id, "")
    
def is_shard(res_id: str) -> bool:
    """检查资源是否为模型分片
    
    Args:
        res_id: 资源标识符
        
    Returns:
        bool: 是否为模型分片
    """
    return res_id.startswith("shard:") or "model_shard" in res_id
    
def is_cache(res_id: str) -> bool:
    """检查资源是否为缓存文件
    
    Args:
        res_id: 资源标识符
        
    Returns:
        bool: 是否为缓存文件
    """
    return res_id.startswith("cache:") or res_id in _active_caches
    
def is_shard_loaded(res_id: str) -> bool:
    """检查模型分片是否已加载
    
    Args:
        res_id: 资源标识符
        
    Returns:
        bool: 分片是否已加载
    """
    global _loaded_shards
    return res_id in _loaded_shards

def track_resource_reference(res_id: str, obj: Any) -> None:
    """跟踪资源对象引用
    
    Args:
        res_id: 资源标识符
        obj: 资源对象
    """
    global _resource_references
    _resource_references[res_id] = id(obj)
    logger.debug(f"跟踪资源引用: {res_id} -> {id(obj)}")
    
def untrack_resource_reference(res_id: str) -> None:
    """取消跟踪资源对象引用
    
    Args:
        res_id: 资源标识符
    """
    global _resource_references
    if res_id in _resource_references:
        del _resource_references[res_id]
        logger.debug(f"取消跟踪资源引用: {res_id}")
        
def check_reference_exists(res_id: str) -> bool:
    """检查资源引用是否仍然存在
    
    Args:
        res_id: 资源标识符
        
    Returns:
        bool: 引用是否存在
    """
    global _resource_references
    if res_id not in _resource_references:
        return False
        
    ref_id = _resource_references[res_id]
    
    # 扫描所有对象寻找匹配的id
    for obj in gc.get_objects():
        if id(obj) == ref_id:
            return True
            
    return False

def validate_release(res_id: str) -> bool:
    """验证资源是否正确释放
    
    Args:
        res_id: 资源标识符
        
    Returns:
        bool: 验证是否通过
    """
    logger.info(f"验证资源是否彻底释放: {res_id}")
    
    try:
        # 模型分片检查
        if is_shard(res_id):
            if is_shard_loaded(res_id):
                logger.error(f"模型分片释放失败: {res_id}")
                return False
                
        # 缓存文件检查
        elif is_cache(res_id):
            cache_path = get_cache_path(res_id)
            if cache_path and os.path.exists(cache_path):
                logger.error(f"缓存文件释放失败: {res_id} -> {cache_path}")
                return False
                
        # 对象引用检查
        if check_reference_exists(res_id):
            logger.error(f"对象引用释放失败: {res_id}")
            return False
            
        # 内存垃圾回收检查
        gc.collect()
        
        # 验证通过
        logger.info(f"资源释放验证通过: {res_id}")
        return True
        
    except Exception as e:
        logger.error(f"资源释放验证出错: {res_id} - {str(e)}")
        return False

def scan_memory_for_resource(res_id: str) -> List[int]:
    """扫描内存中的资源对象地址
    
    Args:
        res_id: 资源标识符
        
    Returns:
        List[int]: 找到的对象内存地址列表
    """
    found_addresses = []
    
    # 扫描所有当前对象
    for obj in gc.get_objects():
        # 尝试匹配对象属性或名称
        try:
            if hasattr(obj, 'name') and res_id in str(obj.name):
                found_addresses.append(id(obj))
            elif hasattr(obj, 'id') and res_id in str(obj.id):
                found_addresses.append(id(obj))
            elif hasattr(obj, '__dict__') and res_id in str(obj.__dict__):
                found_addresses.append(id(obj))
        except:
            # 忽略无法访问的对象
            pass
            
    return found_addresses

def verify_gpu_memory_release() -> bool:
    """验证GPU显存是否正确释放
    
    Returns:
        bool: 验证是否通过
    """
    try:
        import torch
        if torch.cuda.is_available():
            # 保存当前使用的显存
            current_memory = torch.cuda.memory_allocated()
            
            # 强制执行垃圾回收和缓存清理
            gc.collect()
            torch.cuda.empty_cache()
            
            # 再次检查显存
            new_memory = torch.cuda.memory_allocated()
            
            # 如果释放了大量显存，可能表明有资源未正常释放
            if current_memory - new_memory > 10 * 1024 * 1024:  # 超过10MB
                logger.warning(f"GPU显存异常释放: {(current_memory - new_memory) / 1024 / 1024:.2f}MB")
                return False
                
        return True
    except ImportError:
        logger.debug("PyTorch未安装，跳过GPU显存验证")
        return True
    except Exception as e:
        logger.error(f"GPU显存验证出错: {str(e)}")
        return False

def validate_model_release(model_id: str) -> bool:
    """验证模型是否正确释放
    
    Args:
        model_id: 模型ID
        
    Returns:
        bool: 验证是否通过
    """
    logger.info(f"验证模型释放: {model_id}")
    
    # 使用内存管理器检查模型是否仍在加载
    model = memory_guard.access_model(model_id)
    if model is not None:
        logger.error(f"模型未释放: {model_id}")
        return False
        
    # 检查内存中是否有模型相关对象
    addresses = scan_memory_for_resource(model_id)
    if addresses:
        logger.warning(f"内存中仍有模型相关对象: {model_id}, 地址数量: {len(addresses)}")
        # 仅作为警告，不一定代表泄漏
        
    # 验证GPU显存释放
    if not verify_gpu_memory_release():
        logger.warning(f"GPU显存可能未完全释放: {model_id}")
        # 仅作为警告，因为可能有其他模型在使用GPU
        
    # 检查模型缓存目录
    model_cache_dir = os.path.join(CACHE_DIR, model_id)
    if os.path.exists(model_cache_dir) and os.listdir(model_cache_dir):
        logger.warning(f"模型缓存目录未清空: {model_cache_dir}")
        # 仅作为警告，某些缓存可能是故意保留的
        
    return True

def verify_system_resources() -> Dict[str, Any]:
    """验证系统资源状态
    
    Returns:
        Dict: 系统资源状态报告
    """
    # 获取内存使用情况
    memory_info = psutil.virtual_memory()
    
    # 获取当前进程资源使用
    process = psutil.Process(os.getpid())
    process_memory = process.memory_info().rss / (1024 * 1024)  # MB
    
    # 获取CPU使用率
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # 检查GPU使用情况（如果可用）
    gpu_info = {}
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info = {
                "allocated_memory": torch.cuda.memory_allocated() / (1024 * 1024),  # MB
                "reserved_memory": torch.cuda.memory_reserved() / (1024 * 1024),    # MB
                "device_count": torch.cuda.device_count()
            }
    except ImportError:
        # PyTorch未安装
        pass
        
    # 构建报告
    report = {
        "timestamp": time.time(),
        "system_memory": {
            "total_gb": memory_info.total / (1024 * 1024 * 1024),
            "available_gb": memory_info.available / (1024 * 1024 * 1024),
            "percent_used": memory_info.percent
        },
        "process_memory_mb": process_memory,
        "cpu_percent": cpu_percent,
        "gpu_info": gpu_info,
        "loaded_shards_count": len(_loaded_shards),
        "active_caches_count": len(_active_caches),
    }
    
    return report

def perform_full_system_check() -> Dict[str, Any]:
    """执行完整的系统检查
    
    Returns:
        Dict: 检查结果报告
    """
    logger.info("开始执行完整系统检查...")
    
    # 强制执行垃圾回收
    gc.collect()
    
    # 验证系统资源
    system_report = verify_system_resources()
    
    # 检查是否有未释放的模型
    active_models = memory_guard.get_memory_status()["loaded_models"]
    
    # 检查是否有未删除的缓存文件
    orphaned_caches = []
    for res_id, path in _active_caches.items():
        if os.path.exists(path):
            orphaned_caches.append(res_id)
            
    # 尝试清理孤立的缓存文件
    for res_id in orphaned_caches:
        path = _active_caches[res_id]
        try:
            os.remove(path)
            logger.info(f"已清理孤立缓存文件: {path}")
        except:
            logger.warning(f"无法清理孤立缓存文件: {path}")
            
    # 构建报告
    report = {
        "timestamp": time.time(),
        "system_resources": system_report,
        "active_models": active_models,
        "orphaned_caches": orphaned_caches,
        "loaded_shards": list(_loaded_shards),
        "check_result": "passed" if not orphaned_caches and not _loaded_shards else "warning"
    }
    
    logger.info(f"系统检查完成，结果: {report['check_result']}")
    return report

# 检查主函数，可作为命令行工具使用
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="资源释放验证工具")
    parser.add_argument("--res-id", type=str, help="要验证的资源ID")
    parser.add_argument("--model-id", type=str, help="要验证的模型ID")
    parser.add_argument("--full-check", action="store_true", help="执行完整系统检查")
    args = parser.parse_args()
    
    if args.res_id:
        result = validate_release(args.res_id)
        print(f"资源释放验证结果: {'通过' if result else '失败'}")
        
    elif args.model_id:
        result = validate_model_release(args.model_id)
        print(f"模型释放验证结果: {'通过' if result else '失败'}")
        
    elif args.full_check:
        report = perform_full_system_check()
        print(f"系统检查结果: {report['check_result']}")
        print(f"活跃模型: {report['active_models']}")
        print(f"孤立缓存: {report['orphaned_caches']}")
        
    else:
        print("请指定要验证的资源ID或模型ID，或使用--full-check执行完整检查") 