#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源释放执行器

该模块负责执行各种资源的具体释放操作，实现了不同类型资源的安全释放策略。
主要功能：
1. 不同资源类型的专用释放逻辑
2. 资源释放安全检查
3. 释放操作日志和统计
4. 与资源跟踪器的无缝集成
"""

import os
import gc
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
import weakref
import numpy as np

# 尝试导入PyTorch(可选)
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# 引入熔断效果验证系统
try:
    from src.fuse.effect_validator import get_validator, ValidationResult
    _validator_available = True
except ImportError:
    _validator_available = False

# 配置日志
logger = logging.getLogger("ResourceReaper")

class ResourceReaper:
    """资源释放执行器，负责执行各种资源的具体释放操作"""
    
    def __init__(self):
        """初始化资源释放执行器"""
        # 资源释放计数
        self.release_stats = {
            "total_released": 0,
            "by_type": {},
            "emergency_releases": 0,
            "last_release_time": 0,
            "estimated_mb_freed": 0
        }
        
        # 资源释放锁，防止并发释放导致问题
        self.release_lock = threading.RLock()
        
        # 类型特定的释放处理器
        self.type_handlers = {
            "model_shards": self._release_model_shard,
            "model_weights_cache": self._release_model_weights,
            "render_cache": self._release_render_cache,
            "temp_buffers": self._release_temp_buffer,
            "audio_cache": self._release_audio_cache,
            "subtitle_index": self._release_subtitle_index
        }
        
        logger.info("资源释放执行器初始化完成")
    
    def release(self, res_id: str, resource: Any = None, metadata: Dict[str, Any] = None) -> bool:
        """
        执行资源释放操作
        
        Args:
            res_id: 资源ID
            resource: 资源对象(可选)
            metadata: 资源元数据(可选)
            
        Returns:
            bool: 是否成功释放
        """
        with self.release_lock:
            try:
                # 分离资源类型和ID
                if ":" in res_id:
                    res_type, specific_id = res_id.split(":", 1)
                else:
                    res_type = "unknown"
                    specific_id = res_id
                
                logger.debug(f"执行资源释放操作: {res_id}")
                start_time = time.time()
                
                # 释放前检查资源是否被锁定
                if metadata and metadata.get("is_locked", False):
                    logger.warning(f"资源被锁定，无法释放: {res_id}")
                    return False
                
                # 如果找不到特定处理器，使用通用处理器
                if res_type in self.type_handlers:
                    success = self.type_handlers[res_type](specific_id, resource, metadata)
                else:
                    # 通用释放方法
                    success = self._generic_release(res_id, resource, metadata)
                
                if success:
                    # 更新释放统计
                    self.release_stats["total_released"] += 1
                    self.release_stats["by_type"][res_type] = self.release_stats["by_type"].get(res_type, 0) + 1
                    self.release_stats["last_release_time"] = time.time()
                    
                    # 估计释放的内存
                    size_mb = 0
                    if metadata:
                        size_mb = metadata.get("size_mb", 0)
                    self.release_stats["estimated_mb_freed"] += size_mb
                    
                    # 记录释放时间
                    elapsed = time.time() - start_time
                    logger.info(f"资源释放成功: {res_id}, 耗时: {elapsed:.3f}秒, 预估释放: {size_mb}MB")
                
                # 建议进行垃圾回收
                gc.collect()
                
                return success
            
            except Exception as e:
                logger.error(f"资源释放失败 {res_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return False
    
    def _generic_release(self, res_id: str, resource: Any, metadata: Dict[str, Any]) -> bool:
        """
        通用资源释放方法
        
        Args:
            res_id: 资源ID
            resource: 资源对象
            metadata: 资源元数据
            
        Returns:
            bool: 是否成功释放
        """
        try:
            # 如果是NumPy数组
            if isinstance(resource, np.ndarray):
                del resource
                return True
            
            # 如果是字典或列表，清空内容
            elif isinstance(resource, (dict, list)):
                if isinstance(resource, dict):
                    resource.clear()
                else:
                    del resource[:]
                return True
            
            # 如果是可释放对象(实现了release或close方法)
            elif hasattr(resource, 'release'):
                resource.release()
                return True
            elif hasattr(resource, 'close'):
                resource.close()
                return True
            
            # 对于其他类型对象，直接删除引用
            elif resource is not None:
                del resource
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"通用释放失败 {res_id}: {str(e)}")
            return False
    
    def _release_model_shard(self, shard_id: str, shard: Any, metadata: Dict[str, Any]) -> bool:
        """
        释放模型分片
        
        Args:
            shard_id: 分片ID
            shard: 分片对象
            metadata: 分片元数据
            
        Returns:
            bool: 是否成功释放
        """
        try:
            # 检查是否是PyTorch张量
            if HAS_TORCH and isinstance(shard, torch.Tensor):
                # 释放张量
                del shard
                
                # 清空CUDA缓存
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
                logger.debug(f"已释放模型分片: {shard_id}")
                
            else:
                # 使用通用释放方法
                return self._generic_release(f"model_shards:{shard_id}", shard, metadata)
                
            return True
            
        except Exception as e:
            logger.error(f"释放模型分片失败 {shard_id}: {str(e)}")
            return False
    
    def _release_model_weights(self, model_id: str, model: Any, metadata: Dict[str, Any]) -> bool:
        """
        释放模型权重
        
        Args:
            model_id: 模型ID
            model: 模型对象
            metadata: 模型元数据
            
        Returns:
            bool: 是否成功释放
        """
        try:
            # 检查是否是字典格式(包含模型和tokenizer)
            if isinstance(model, dict) and 'model' in model:
                # 分别释放模型和分词器
                if 'tokenizer' in model:
                    tokenizer = model.get('tokenizer')
                    if tokenizer is not None:
                        del tokenizer
                
                actual_model = model.get('model')
                if actual_model is not None:
                    # 如果模型有内部状态，尝试清除
                    if hasattr(actual_model, 'cpu'):
                        try:
                            # 将模型移到CPU以释放GPU内存
                            actual_model.cpu()
                        except:
                            pass
                    
                    # 删除模型
                    del actual_model
                
                # 清空字典
                model.clear()
            else:
                # 使用通用释放方法
                return self._generic_release(f"model_weights_cache:{model_id}", model, metadata)
            
            # 如果使用PyTorch，清空CUDA缓存
            if HAS_TORCH and torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.debug(f"已释放模型权重: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"释放模型权重失败 {model_id}: {str(e)}")
            return False
    
    def _release_render_cache(self, frame_id: str, frame: Any, metadata: Dict[str, Any]) -> bool:
        """
        释放渲染缓存
        
        Args:
            frame_id: 帧ID
            frame: 帧对象
            metadata: 帧元数据
            
        Returns:
            bool: 是否成功释放
        """
        try:
            # 检查是否可以直接删除
            if frame is not None:
                # 检查是否需要保存到临时文件(如果配置了持久化)
                if metadata and metadata.get("persist_to_disk", False):
                    persist_path = metadata.get("persist_path")
                    if persist_path:
                        try:
                            import cv2
                            os.makedirs(os.path.dirname(persist_path), exist_ok=True)
                            cv2.imwrite(persist_path, frame)
                            logger.debug(f"已将帧持久化到磁盘: {persist_path}")
                        except Exception as pe:
                            logger.warning(f"帧持久化失败 {frame_id}: {str(pe)}")
                
                # 释放帧对象
                del frame
            
            logger.debug(f"已释放渲染缓存: {frame_id}")
            return True
            
        except Exception as e:
            logger.error(f"释放渲染缓存失败 {frame_id}: {str(e)}")
            return False
    
    def _release_temp_buffer(self, buffer_id: str, buffer: Any, metadata: Dict[str, Any]) -> bool:
        """
        释放临时缓冲区
        
        Args:
            buffer_id: 缓冲区ID
            buffer: 缓冲区对象
            metadata: 缓冲区元数据
            
        Returns:
            bool: 是否成功释放
        """
        # 临时缓冲区通常是简单对象，使用通用释放方法即可
        return self._generic_release(f"temp_buffers:{buffer_id}", buffer, metadata)
    
    def _release_audio_cache(self, audio_id: str, audio: Any, metadata: Dict[str, Any]) -> bool:
        """
        释放音频缓存
        
        Args:
            audio_id: 音频ID
            audio: 音频对象
            metadata: 音频元数据
            
        Returns:
            bool: 是否成功释放
        """
        try:
            # 如果是NumPy数组，直接删除
            if isinstance(audio, np.ndarray):
                del audio
                return True
                
            # 如果是可关闭对象，调用close方法
            if hasattr(audio, 'close'):
                audio.close()
                
            # 删除引用
            del audio
            
            logger.debug(f"已释放音频缓存: {audio_id}")
            return True
            
        except Exception as e:
            logger.error(f"释放音频缓存失败 {audio_id}: {str(e)}")
            return False
    
    def _release_subtitle_index(self, index_id: str, index: Any, metadata: Dict[str, Any]) -> bool:
        """
        释放字幕索引
        
        Args:
            index_id: 索引ID
            index: 索引对象
            metadata: 索引元数据
            
        Returns:
            bool: 是否成功释放
        """
        try:
            # 检查是否支持增量释放
            if metadata and metadata.get("incremental_release", False):
                # 如果支持增量释放，只释放部分内容
                if isinstance(index, dict):
                    # 找出访问时间最早的部分
                    if "segments" in index and len(index["segments"]) > 10:
                        # 保留最近的10个段落
                        index["segments"] = index["segments"][-10:]
                        logger.debug(f"增量释放字幕索引: {index_id}, 保留最新10个段落")
                        return True
            
            # 不支持增量释放或不适合增量释放，完全释放
            del index
            
            logger.debug(f"已释放字幕索引: {index_id}")
            return True
            
        except Exception as e:
            logger.error(f"释放字幕索引失败 {index_id}: {str(e)}")
            return False
    
    def release_multiple(self, resource_ids: List[str], resources: Dict[str, Any] = None, 
                        metadata: Dict[str, Dict[str, Any]] = None) -> int:
        """
        批量释放多个资源
        
        Args:
            resource_ids: 资源ID列表
            resources: 资源对象字典 {资源ID: 资源对象}
            metadata: 资源元数据字典 {资源ID: 元数据}
            
        Returns:
            int: 成功释放的资源数量
        """
        success_count = 0
        
        for res_id in resource_ids:
            # 获取资源对象和元数据
            resource = None
            meta = None
            
            if resources and res_id in resources:
                resource = resources[res_id]
                
            if metadata and res_id in metadata:
                meta = metadata[res_id]
                
            # 执行释放
            if self.release(res_id, resource, meta):
                success_count += 1
                
        return success_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取资源释放统计信息
        
        Returns:
            Dict: 统计信息
        """
        with self.release_lock:
            # 返回统计信息的副本
            stats = dict(self.release_stats)
            stats["last_updated"] = time.time()
            return stats
    
    def get_handler_for_type(self, resource_type: str) -> Optional[Callable]:
        """
        获取指定资源类型的处理器
        
        Args:
            resource_type: 资源类型
            
        Returns:
            Optional[Callable]: 处理器函数或None
        """
        return self.type_handlers.get(resource_type)
    
    def register_handler(self, resource_type: str, handler: Callable) -> None:
        """
        注册自定义资源处理器
        
        Args:
            resource_type: 资源类型
            handler: 处理器函数
        """
        self.type_handlers[resource_type] = handler
        logger.info(f"已注册资源处理器: {resource_type}")

    def execute_release_action(self, action_name: str, **kwargs) -> bool:
        """
        执行释放操作并返回结果
        
        Args:
            action_name: 操作名称
            **kwargs: 传递给操作的参数
            
        Returns:
            操作是否成功
        """
        try:
            # 记录操作前状态
            before_mem = self._get_memory_info()
            
            # 执行操作
            logger.info(f"执行释放操作: {action_name}")
            if action_name in self.available_actions:
                result = self.available_actions[action_name](**kwargs)
                
                # 记录操作后状态
                after_mem = self._get_memory_info()
                
                # 计算释放效果
                released_mb = (before_mem['used'] - after_mem['used']) / (1024 * 1024)
                logger.info(f"操作 {action_name} 释放了 {released_mb:.2f}MB 内存")
                
                # 记录操作效果
                self.action_history.append({
                    "action": action_name,
                    "timestamp": time.time(),
                    "memory_before": before_mem['used'],
                    "memory_after": after_mem['used'],
                    "memory_released": before_mem['used'] - after_mem['used'],
                    "success": result is not False
                })
                
                # 如果验证器可用，验证操作效果
                if _validator_available:
                    validator = get_validator()
                    validation_success = validator.validate(action_name)
                    logger.info(f"操作 {action_name} 效果验证: {'成功' if validation_success else '失败'}")
                
                return result is not False
            else:
                logger.warning(f"未知的释放操作: {action_name}")
                return False
                
        except Exception as e:
            logger.error(f"执行释放操作 {action_name} 时发生错误: {str(e)}")
            logger.debug(traceback.format_exc())
            return False

# 单例模式
_resource_reaper = None

def get_resource_reaper() -> ResourceReaper:
    """获取资源释放执行器单例"""
    global _resource_reaper
    if _resource_reaper is None:
        _resource_reaper = ResourceReaper()
    return _resource_reaper


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试资源释放执行器
    reaper = get_resource_reaper()
    
    # 创建测试资源
    test_buffer = np.zeros(1000000)  # 约8MB的NumPy数组
    test_dict = {"data": [1] * 1000000}  # 大字典
    test_list = [1] * 1000000  # 大列表
    
    # 测试释放
    print("开始测试资源释放...")
    
    reaper.release("temp_buffers:test_buffer", test_buffer, {"size_mb": 8})
    reaper.release("temp_buffers:test_dict", test_dict, {"size_mb": 8})
    reaper.release("temp_buffers:test_list", test_list, {"size_mb": 8})
    
    # 检查是否释放成功
    print("释放后尝试访问对象...")
    try:
        print(test_buffer.shape)  # 应该抛出异常
        print("错误: NumPy数组未成功释放")
    except:
        print("正确: NumPy数组已释放")
        
    # 显示统计信息
    print("\n资源释放统计:")
    stats = reaper.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}") 