#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源生命周期管理演示程序

该程序演示VisionAI-ClipsMaster中的资源生命周期管理功能，
展示如何在内存受限情况下智能管理和释放资源。
"""

import os
import sys
import time
import logging
import argparse
import psutil
import numpy as np
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ResourceLifecycleDemo")

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入项目模块
from src.memory.resource_tracker import get_resource_tracker
from src.utils.memory_guard import get_memory_guard
from src.utils.device_manager import get_device_manager

class ResourceDemo:
    """资源生命周期演示类"""
    
    def __init__(self):
        """初始化演示"""
        # 获取资源管理组件
        self.resource_tracker = get_resource_tracker()
        self.memory_guard = get_memory_guard()
        self.device_manager = get_device_manager()
        
        # 创建的资源ID列表
        self.created_resources = []
        
        logger.info("资源生命周期演示初始化完成")
        
    def create_large_buffer(self, size_mb: int, resource_type: str = "temp_buffers") -> str:
        """
        创建指定大小的缓冲区
        
        Args:
            size_mb: 缓冲区大小(MB)
            resource_type: 资源类型
            
        Returns:
            str: 资源ID
        """
        # 创建NumPy数组作为缓冲区
        buffer_size = size_mb * 1024 * 1024 // 8  # 转换为double元素数量
        large_buffer = np.random.random(buffer_size)
        
        # 生成唯一资源ID
        resource_id = f"demo_buffer_{len(self.created_resources):03d}"
        
        # 定义释放回调函数
        def release_callback():
            logger.info(f"释放缓冲区: {resource_id} ({size_mb}MB)")
            # 实际上Python的垃圾回收会自动处理，这里只是演示
        
        # 注册到资源跟踪器
        full_id = self.resource_tracker.register(
            resource_type,
            resource_id,
            large_buffer,
            {"size_mb": size_mb, "creation_time": time.time()},
            release_callback
        )
        
        # 同时注册到内存管理器
        self.memory_guard.register_resource(resource_type, resource_id, large_buffer)
        
        # 添加到已创建资源列表
        self.created_resources.append(full_id)
        
        logger.info(f"已创建 {size_mb}MB 的 {resource_type} 资源: {full_id}")
        return full_id
    
    def simulate_model_shard(self, layer_id: int, size_mb: int = 100) -> str:
        """
        模拟模型分片
        
        Args:
            layer_id: 层ID
            size_mb: 分片大小(MB)
            
        Returns:
            str: 资源ID
        """
        return self.create_large_buffer(size_mb, "model_shards")
    
    def simulate_render_cache(self, frame_id: int, size_mb: int = 50) -> str:
        """
        模拟渲染缓存
        
        Args:
            frame_id: 帧ID
            size_mb: 缓存大小(MB)
            
        Returns:
            str: 资源ID
        """
        return self.create_large_buffer(size_mb, "render_cache")
    
    def simulate_access_pattern(self, duration_sec: int, 
                               access_interval_sec: float = 1.0,
                               access_count: int = None):
        """
        模拟资源访问模式
        
        Args:
            duration_sec: 总持续时间(秒)
            access_interval_sec: 访问间隔(秒)
            access_count: 访问次数限制(如果指定)
        """
        start_time = time.time()
        count = 0
        
        logger.info(f"开始模拟资源访问模式，持续 {duration_sec} 秒")
        
        while (time.time() - start_time < duration_sec and 
               (access_count is None or count < access_count)):
            
            # 如果有资源，随机访问某些资源
            if self.created_resources:
                # 随机选择30%的资源进行访问
                access_indices = np.random.choice(
                    len(self.created_resources),
                    size=max(1, int(len(self.created_resources) * 0.3)),
                    replace=False
                )
                
                for idx in access_indices:
                    if idx < len(self.created_resources):
                        resource_id = self.created_resources[idx]
                        # 更新访问时间
                        self.resource_tracker.touch(resource_id)
                        count += 1
                
                logger.info(f"已访问 {len(access_indices)} 个资源，总访问次数: {count}")
            
            # 等待指定时间
            time.sleep(access_interval_sec)
    
    def demo_resource_creation(self):
        """演示资源创建和过期"""
        logger.info("=== 资源创建和过期演示 ===")
        
        # 1. 创建多种类型的资源
        logger.info("1. 创建临时缓冲区资源")
        for i in range(5):
            self.create_large_buffer(20, "temp_buffers")  # 5个20MB的临时缓冲区
        
        logger.info("2. 创建模型分片资源")
        for i in range(10):
            self.simulate_model_shard(i, 50)  # 10个50MB的模型分片
        
        logger.info("3. 创建渲染缓存资源")
        for i in range(3):
            self.simulate_render_cache(i, 100)  # 3个100MB的渲染缓存
            
        # 显示资源统计
        self.show_resource_stats()
        
        # 2. 等待一段时间，让某些资源过期
        logger.info(f"\n等待35秒，让临时缓冲区过期...")
        time.sleep(35)  # 临时缓冲区30秒后过期
        
        # 3. 检查过期资源
        expired = self.resource_tracker.get_expired()
        logger.info(f"检测到 {len(expired)} 个过期资源: {expired}")
        
        # 4. 释放过期资源
        released = self.resource_tracker.release_expired()
        logger.info(f"已释放 {released} 个过期资源")
        
        # 显示资源统计
        self.show_resource_stats()
        
        # 5. 再次访问某些资源，防止过期
        logger.info("\n访问部分资源，防止过期")
        self.simulate_access_pattern(5, 1.0, 10)
        
        # 显示资源统计
        self.show_resource_stats()
    
    def demo_memory_pressure(self):
        """演示内存压力下的资源释放"""
        logger.info("\n=== 内存压力下的资源释放演示 ===")
        
        # 清理现有资源
        for res_id in list(self.created_resources):
            self.resource_tracker.release(res_id, force=True)
        self.created_resources.clear()
        
        # 1. 创建多个大型资源，占用大量内存
        logger.info("1. 创建多个大型资源，占用内存")
        
        # 获取可用内存的25%
        mem = psutil.virtual_memory()
        target_memory_mb = int(mem.available * 0.25 / (1024 * 1024))
        
        # 创建一个大型临时缓冲区
        logger.info(f"创建 {target_memory_mb}MB 的大型临时缓冲区")
        self.create_large_buffer(target_memory_mb, "temp_buffers")
        
        # 2. 查看内存使用情况
        mem_after = psutil.virtual_memory()
        logger.info(f"内存使用情况: {mem_after.percent}%")
        
        # 显示资源统计
        self.show_resource_stats()
        
        # 3. 创建更多资源，模拟内存压力
        logger.info("\n2. 创建更多资源，增加内存压力")
        for i in range(5):
            buffer_size = target_memory_mb // 10
            logger.info(f"创建 {buffer_size}MB 的渲染缓存")
            self.simulate_render_cache(i, buffer_size)
            time.sleep(1)  # 给系统一些响应时间
            
            # 检查内存情况
            mem_current = psutil.virtual_memory()
            logger.info(f"当前内存使用情况: {mem_current.percent}%")
            
            # 如果内存使用率超过80%，停止创建
            if mem_current.percent > 80:
                logger.warning("内存使用率超过80%，停止创建资源")
                break
        
        # 显示资源统计
        self.show_resource_stats()
        
        # 4. 等待内存守卫或资源跟踪器自动释放资源
        logger.info("\n3. 等待30秒，观察自动资源释放...")
        time.sleep(30)
        
        # 显示资源统计
        self.show_resource_stats()
        
        # 5. 清理剩余资源
        logger.info("\n4. 手动清理所有剩余资源")
        for res_id in list(self.created_resources):
            self.resource_tracker.release(res_id, force=True)
        self.created_resources.clear()
        
        # 显示资源统计
        self.show_resource_stats()
    
    def show_resource_stats(self):
        """显示资源统计信息"""
        # 获取资源跟踪器统计信息
        tracker_stats = self.resource_tracker.get_stats()
        
        # 获取内存使用情况
        mem = psutil.virtual_memory()
        
        logger.info("\n--- 资源统计信息 ---")
        logger.info(f"当前资源数: {tracker_stats['current_count']}")
        logger.info(f"已创建资源总数: {tracker_stats['created']}")
        logger.info(f"已释放资源总数: {tracker_stats['released']}")
        logger.info(f"总访问次数: {tracker_stats['total_access']}")
        logger.info(f"已过期资源数: {tracker_stats['expired_count']}")
        
        # 显示各类型资源数量
        if 'type_counts' in tracker_stats:
            logger.info("\n各类型资源数量:")
            for res_type, count in tracker_stats['type_counts'].items():
                logger.info(f"  {res_type}: {count} 个")
        
        # 显示内存使用情况
        logger.info("\n内存使用情况:")
        logger.info(f"  总内存: {mem.total / (1024**3):.2f} GB")
        logger.info(f"  可用内存: {mem.available / (1024**3):.2f} GB")
        logger.info(f"  内存使用率: {mem.percent}%")
        logger.info("----------------------")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="资源生命周期管理演示")
    parser.add_argument("--demo", choices=["creation", "pressure", "all"], 
                        default="all", help="演示类型")
    args = parser.parse_args()
    
    demo = ResourceDemo()
    
    try:
        if args.demo == "creation" or args.demo == "all":
            demo.demo_resource_creation()
            
        if args.demo == "pressure" or args.demo == "all":
            demo.demo_memory_pressure()
            
    except KeyboardInterrupt:
        logger.info("演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # 清理所有资源
        logger.info("清理所有演示资源...")
        for res_id in list(demo.created_resources):
            demo.resource_tracker.release(res_id, force=True)
            
        logger.info("演示结束")


if __name__ == "__main__":
    main() 