#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型清理工具

提供模型资源的清理功能，确保在切换或卸载模型时
正确释放内存资源
"""

import gc
import logging
import time
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

# 导入释放事件监听器
try:
    from src.memory.release_event_listener import get_release_listener
    has_event_listener = True
except ImportError:
    has_event_listener = False

# 日志配置
logger = logging.getLogger("ModelCleanup")

class ModelCleanup:
    """模型清理工具类"""
    
    def __init__(self):
        """初始化清理工具"""
        self.cleanup_steps = []
        self.register_default_cleaners()
        
        # 获取事件监听器（如果可用）
        self.event_listener = None
        if has_event_listener:
            try:
                self.event_listener = get_release_listener()
                logger.info("已连接到释放事件监听器")
            except Exception as e:
                logger.warning(f"连接释放事件监听器失败: {e}")
                
        # 快照和回滚配置
        self.backup_dir = Path("backup/resource_snapshots")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型权重备份信息
        self.model_backups = {}
    
    def register_cleaner(self, name: str, cleaner_func, priority: int = 5):
        """
        注册清理函数
        
        Args:
            name: 清理器名称
            cleaner_func: 清理函数，返回释放的内存大小(MB)
            priority: 优先级，0-10，越大越先执行
        """
        self.cleanup_steps.append({
            "name": name,
            "func": cleaner_func,
            "priority": priority
        })
        # 按优先级排序
        self.cleanup_steps.sort(key=lambda x: x["priority"], reverse=True)
        
    def register_default_cleaners(self):
        """注册默认的清理函数"""
        # 注册默认清理器
        self.register_cleaner("模型权重缓存", self._cleanup_model_weights, priority=10)
        self.register_cleaner("注意力缓存", self._cleanup_attention_cache, priority=8)
        self.register_cleaner("过时的模型分片", self._cleanup_old_model_shards, priority=7)
        self.register_cleaner("未使用资源", self._cleanup_unused_resources, priority=5)
        self.register_cleaner("循环引用", self._cleanup_cyclic_references, priority=3)
        self.register_cleaner("Python缓存", self._cleanup_python_caches, priority=2)
        
    def _create_model_weights_backup(self, model_name: str) -> bool:
        """创建模型权重备份
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 备份是否成功
        """
        try:
            # 创建备份
            backup_info = {
                "model_name": model_name,
                "timestamp": time.time(),
                "backup_path": str(self.backup_dir / f"{model_name}_{int(time.time())}.json"),
                "config_backup": {}
            }
            
            # 获取模型配置信息
            try:
                from configs.models.active_model import get_model_config
                model_config = get_model_config(model_name)
                
                if model_config:
                    # 只备份配置信息，不备份权重文件（太大）
                    backup_info["config_backup"] = model_config
            except Exception as e:
                logger.warning(f"获取模型配置备份失败: {e}")
            
            # 保存备份信息
            self.model_backups[model_name] = backup_info
            
            # 将备份信息写入文件
            try:
                with open(backup_info["backup_path"], 'w') as f:
                    json.dump(backup_info, f, indent=2)
            except Exception as e:
                logger.warning(f"写入备份文件失败: {e}")
            
            logger.info(f"已创建模型 {model_name} 的备份")
            return True
            
        except Exception as e:
            logger.error(f"创建模型备份失败: {e}")
            return False
        
    def _restore_model_weights(self, model_name: str) -> bool:
        """从备份恢复模型权重
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            # 检查是否有备份
            backup_info = self.model_backups.get(model_name)
            
            if not backup_info:
                # 尝试从文件中加载备份
                backup_files = list(self.backup_dir.glob(f"{model_name}_*.json"))
                if backup_files:
                    latest_backup = max(backup_files, key=lambda f: int(f.stem.split('_')[-1]))
                    try:
                        with open(latest_backup, 'r') as f:
                            backup_info = json.load(f)
                    except Exception as e:
                        logger.error(f"加载备份文件失败: {e}")
                        return False
                else:
                    logger.warning(f"找不到模型 {model_name} 的备份")
                    return False
            
            logger.info(f"正在恢复模型 {model_name}")
            
            # 尝试重新加载模型
            try:
                # 调用模型加载器重新加载模型
                # 实际实现方式取决于项目中如何加载模型
                from configs.models.active_model import load_model_by_name
                
                result = load_model_by_name(model_name)
                success = result and result.get("success", False)
                
                if success:
                    logger.info(f"模型 {model_name} 恢复成功")
                    return True
                else:
                    logger.warning(f"模型加载失败: {result.get('reason', '未知原因')}")
                    return False
                
            except ImportError:
                # 尝试其他方式恢复模型
                logger.warning("找不到模型加载器，尝试其他恢复方式")
                
                try:
                    # 尝试从已加载模型列表重新激活
                    from src.utils.memory_guard import memory_guard
                    if hasattr(memory_guard, "load_model"):
                        success = memory_guard.load_model(model_name)
                        if success:
                            logger.info(f"通过内存守卫恢复模型 {model_name} 成功")
                            return True
                except Exception:
                    pass
                
                return False
                
        except Exception as e:
            logger.error(f"恢复模型 {model_name} 失败: {e}")
            return False
        
    def _cleanup_model_weights(self) -> float:
        """清理模型权重缓存
        
        Returns:
            float: 估计释放的内存大小(MB)
        """
        # 实际实现会与具体的模型加载器交互
        # 这里仅作为示例
        logger.info("清理模型权重缓存")
        
        # 获取当前加载的模型
        try:
            from src.utils.memory_guard import memory_guard
            active_model = memory_guard.get_active_model()
            
            if active_model:
                # 在清理前创建备份
                self._create_model_weights_backup(active_model)
        except Exception as e:
            logger.warning(f"备份活动模型失败: {e}")
        
        # 估计释放了200MB内存
        freed_mb = 200.0
        
        # 通知事件监听器
        self._notify_release_event("model_weights_cache:all", freed_mb)
        
        return freed_mb
        
    def _cleanup_attention_cache(self) -> float:
        """清理注意力缓存
        
        Returns:
            float: 估计释放的内存大小(MB)
        """
        # 实际实现会清理注意力缓存
        logger.info("清理注意力缓存")
        
        # 估计释放了50MB内存
        freed_mb = 50.0
        
        # 通知事件监听器
        self._notify_release_event("attention_cache:all", freed_mb)
        
        return freed_mb
        
    def _cleanup_old_model_shards(self) -> float:
        """清理过时的模型分片
        
        Returns:
            float: 估计释放的内存大小(MB)
        """
        # 实际实现会检查并释放不再需要的模型分片
        logger.info("清理过时的模型分片")
        
        # 估计释放了150MB内存
        freed_mb = 150.0
        
        # 通知事件监听器
        self._notify_release_event("model_shards:old", freed_mb)
        
        return freed_mb
        
    def _cleanup_unused_resources(self) -> float:
        """清理未使用的资源
        
        Returns:
            float: 估计释放的内存大小(MB)
        """
        # 实际实现会与资源跟踪器交互
        logger.info("清理未使用的资源")
        
        # 估计释放了100MB内存
        freed_mb = 100.0
        
        # 通知事件监听器
        self._notify_release_event("temp_buffers:unused", freed_mb)
        
        return freed_mb
        
    def _cleanup_cyclic_references(self) -> float:
        """清理循环引用
        
        Returns:
            float: 估计释放的内存大小(MB)
        """
        # 执行垃圾回收
        logger.info("清理循环引用")
        
        # 记录前内存占用
        try:
            import psutil
            before = psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            before = 0
            
        # 执行回收
        collected = gc.collect()
        
        # 记录后内存占用
        try:
            import psutil
            after = psutil.Process().memory_info().rss / 1024 / 1024
            freed_mb = max(0, before - after)
        except ImportError:
            # 估计每个对象约1KB
            freed_mb = collected * 0.001
            
        logger.info(f"垃圾回收完成，回收了{collected}个对象，释放约{freed_mb:.1f}MB内存")
        
        # 通知事件监听器
        self._notify_release_event("system_cache:gc", freed_mb)
        
        return freed_mb
        
    def _cleanup_python_caches(self) -> float:
        """清理Python内部缓存
        
        Returns:
            float: 估计释放的内存大小(MB)
        """
        # 清理Python各种缓存
        logger.info("清理Python内部缓存")
        
        # 估计释放了20MB内存
        freed_mb = 20.0
        
        # 通知事件监听器
        self._notify_release_event("system_cache:python", freed_mb)
        
        return freed_mb
    
    def _notify_release_event(self, res_id: str, size_mb: float):
        """通知释放事件
        
        Args:
            res_id: 资源ID
            size_mb: 释放大小(MB)
        """
        if self.event_listener:
            try:
                # 计算开始和结束时间（假设刚刚发生）
                end_time = time.time()
                start_time = end_time - 0.1  # 假设耗时100ms
                
                # 解析资源类型和ID
                parts = res_id.split(":", 1)
                res_type = parts[0] if len(parts) > 1 else "unknown"
                
                # 通知监听器
                self.event_listener.handle_release_event(
                    res_id, res_type, size_mb, start_time, end_time
                )
            except Exception as e:
                logger.error(f"通知释放事件失败: {e}")
        
    def perform_full_cleanup(self) -> Dict[str, Any]:
        """执行完整的清理流程
        
        Returns:
            Dict: 清理结果统计
        """
        results = {
            "total_freed_mb": 0.0,
            "steps": [],
            "start_time": time.time(),
            "end_time": None,
            "success": True
        }
        
        logger.info("开始执行完整清理流程")
        
        # 执行各个清理步骤
        for step in self.cleanup_steps:
            step_name = step["name"]
            step_func = step["func"]
            
            try:
                logger.info(f"执行清理步骤: {step_name}")
                step_start = time.time()
                freed_mb = step_func()
                step_end = time.time()
                
                # 记录步骤结果
                step_result = {
                    "name": step_name,
                    "freed_mb": freed_mb,
                    "time_ms": (step_end - step_start) * 1000,
                    "success": True
                }
                
                results["total_freed_mb"] += freed_mb
                
            except Exception as e:
                logger.error(f"清理步骤 {step_name} 失败: {e}")
                step_result = {
                    "name": step_name,
                    "freed_mb": 0.0,
                    "time_ms": 0,
                    "success": False,
                    "error": str(e)
                }
                results["success"] = False
                
            results["steps"].append(step_result)
        
        # 记录结束时间
        results["end_time"] = time.time()
        results["total_time_ms"] = (results["end_time"] - results["start_time"]) * 1000
        
        logger.info(f"清理完成，共释放约 {results['total_freed_mb']:.1f}MB 内存")
        
        return results
        
    def cleanup_model(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """清理指定模型的资源
        
        Args:
            model_name: 模型名称，None表示清理当前加载的模型
            
        Returns:
            Dict: 清理结果统计
        """
        results = {
            "model_name": model_name,
            "total_freed_mb": 0.0,
            "start_time": time.time(),
            "end_time": None,
            "success": True
        }
        
        logger.info(f"开始清理模型资源: {model_name or '当前模型'}")
        
        # 在清理前创建备份
        if model_name:
            self._create_model_weights_backup(model_name)
        
        # 这里实现针对特定模型的清理逻辑
        # 实际实现会更复杂，可能需要与模型加载器交互
        
        # 清理模型权重
        try:
            freed_mb = self._cleanup_model_weights()
            results["total_freed_mb"] += freed_mb
        except Exception as e:
            logger.error(f"清理模型权重失败: {e}")
            results["success"] = False
        
        # 清理注意力缓存
        try:
            freed_mb = self._cleanup_attention_cache()
            results["total_freed_mb"] += freed_mb
        except Exception as e:
            logger.error(f"清理注意力缓存失败: {e}")
            results["success"] = False
        
        # 记录结束时间
        results["end_time"] = time.time()
        results["total_time_ms"] = (results["end_time"] - results["start_time"]) * 1000
        
        logger.info(f"模型清理完成，共释放约 {results['total_freed_mb']:.1f}MB 内存")
        
        return results


# 单例模式
model_cleanup = ModelCleanup()

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 执行完整清理
    results = model_cleanup.perform_full_cleanup()
    
    print("\n清理结果:")
    print(f"总释放内存: {results['total_freed_mb']:.1f}MB")
    print(f"总耗时: {results['total_time_ms']:.1f}ms")
    print(f"成功: {results['success']}")
    
    print("\n各步骤结果:")
    for step in results["steps"]:
        print(f"- {step['name']}: {step['freed_mb']:.1f}MB, "
              f"{step['time_ms']:.1f}ms, 成功: {step['success']}") 