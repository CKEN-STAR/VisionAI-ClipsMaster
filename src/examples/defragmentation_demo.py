#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存碎片整理演示

该脚本演示VisionAI-ClipsMaster内存碎片整理功能，
展示如何在资源释放后整理内存碎片，优化内存使用。
"""

import os
import sys
import time
import logging
import numpy as np
from tabulate import tabulate
import gc
import platform
import psutil
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DefragDemo")

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入项目模块
from src.memory.resource_tracker import get_resource_tracker
from src.memory.defragmenter import get_memory_defragmenter, compact_memory

class DefragmentationDemo:
    """内存碎片整理演示类"""
    
    def __init__(self):
        """初始化演示"""
        # 获取资源管理组件
        self.resource_tracker = get_resource_tracker()
        self.defragmenter = get_memory_defragmenter()
        
        # 创建的资源ID列表
        self.created_resources = []
        
        # 用于演示的大型数据对象
        self.large_objects = []
        
        logger.info("内存碎片整理演示初始化完成")
        logger.info(f"当前操作系统: {platform.system()} {platform.release()}")
    
    def show_memory_info(self) -> Dict[str, float]:
        """显示内存使用信息"""
        # 获取当前进程内存信息
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # 计算使用的物理内存(MB)
        used_mb = memory_info.rss / (1024 * 1024)
        
        # 获取系统内存信息
        system_memory = psutil.virtual_memory()
        total_mb = system_memory.total / (1024 * 1024)
        available_mb = system_memory.available / (1024 * 1024)
        used_percent = system_memory.percent
        
        # 输出内存信息
        memory_data = [
            ["进程内存使用", f"{used_mb:.2f} MB"],
            ["系统总内存", f"{total_mb:.2f} MB"],
            ["系统可用内存", f"{available_mb:.2f} MB"],
            ["系统内存使用率", f"{used_percent:.1f}%"]
        ]
        
        print("\n当前内存使用情况:")
        print(tabulate(memory_data, tablefmt="grid"))
        
        return {
            "process_used_mb": used_mb,
            "system_total_mb": total_mb,
            "system_available_mb": available_mb,
            "system_used_percent": used_percent
        }
    
    def allocate_memory(self, size_mb: int = 200) -> None:
        """
        分配一定大小的内存
        
        Args:
            size_mb: 要分配的内存大小(MB)
        """
        logger.info(f"分配 {size_mb}MB 内存...")
        
        # 计算需要分配多少个大小为1MB的数组
        num_arrays = size_mb
        arrays_per_batch = 20
        batches = num_arrays // arrays_per_batch
        
        for batch in range(batches):
            batch_arrays = []
            for i in range(arrays_per_batch):
                # 每个数组约1MB
                array = np.random.random((250, 1000))  # 约1MB
                batch_arrays.append(array)
            
            self.large_objects.append(batch_arrays)
            
            # 显示进度
            allocated = (batch + 1) * arrays_per_batch
            logger.info(f"已分配 {allocated}MB/{size_mb}MB")
            
            # 注册一些资源(每批次注册一个)
            self._register_test_resource(f"batch_{batch}", arrays_per_batch)
        
        # 显示内存使用信息
        self.show_memory_info()
    
    def _register_test_resource(self, name: str, size_mb: float) -> None:
        """
        注册测试资源到资源跟踪器
        
        Args:
            name: 资源名称
            size_mb: 资源大小(MB)
        """
        # 创建一个测试资源对象
        resource_data = {"name": name, "size": size_mb}
        
        # 随机选择资源类型
        resource_types = ["model_shards", "temp_buffers", "render_cache"]
        resource_type = resource_types[len(self.created_resources) % len(resource_types)]
        
        # 注册资源
        resource_id = self.resource_tracker.register(
            resource_type,
            f"test_{name}",
            resource_data,
            {"size_mb": size_mb}
        )
        
        self.created_resources.append(resource_id)
        logger.debug(f"已注册资源: {resource_id}, 大小: {size_mb}MB")
    
    def fragment_memory(self) -> None:
        """通过分配和释放对象来制造内存碎片"""
        logger.info("开始制造内存碎片...")
        
        # 创建一些大小不同的对象
        fragment_objects = []
        
        # 1. 创建不同大小的数组，形成碎片
        for i in range(30):
            # 大小从0.5MB到5MB不等
            size = np.random.randint(128, 1280)
            array = np.random.random((size, size))  # 0.5MB~5MB
            fragment_objects.append(array)
            
        logger.info("已创建30个不同大小的数组")
        
        # 2. 随机释放一半对象，留下空洞
        indices = list(range(len(fragment_objects)))
        np.random.shuffle(indices)
        half = len(indices) // 2
        
        for i in range(half):
            fragment_objects[indices[i]] = None
            
        logger.info(f"已随机释放 {half} 个数组")
        
        # 3. 重新分配一些大对象
        for i in range(5):
            # 分配约10MB的对象
            array = np.random.random((1600, 1600))  # 约10MB
            fragment_objects.append(array)
            
        logger.info("已重新分配5个大数组")
        
        # 4. 随机释放一些大对象中的元素
        if self.large_objects:
            for batch in self.large_objects[:len(self.large_objects)//2]:
                # 在每个批次中随机释放一半
                for i in range(len(batch)//2):
                    batch[i] = None
                    
            logger.info("已随机释放大型数据对象中的元素")
        
        # 强制保留引用，防止垃圾回收
        self.fragment_objects = fragment_objects
        
        # 显示内存使用信息
        self.show_memory_info()
    
    def release_memory(self, amount_mb: int = 500) -> None:
        """
        释放指定大小的内存
        
        Args:
            amount_mb: 要释放的内存大小(MB)
        """
        logger.info(f"释放约 {amount_mb}MB 内存...")
        
        # 获取内存使用前状态
        memory_before = self.show_memory_info()
        
        # 1. 释放大型对象
        released_mb = 0
        if self.large_objects:
            batch_size = len(self.large_objects[0]) if self.large_objects[0] else 0
            batch_mb = batch_size  # 每个数组约1MB
            
            batches_to_release = min(
                len(self.large_objects), 
                amount_mb // batch_mb + (1 if amount_mb % batch_mb > 0 else 0)
            )
            
            for i in range(batches_to_release):
                if i < len(self.large_objects):
                    self.large_objects[i] = None
                    released_mb += batch_mb
            
            # 重建列表，删除空元素
            self.large_objects = [batch for batch in self.large_objects if batch is not None]
            
        # 2. 释放资源跟踪器中的资源
        resources_to_release = min(len(self.created_resources), (amount_mb - released_mb) // 10)
        
        for i in range(resources_to_release):
            if i < len(self.created_resources):
                res_id = self.created_resources[i]
                self.resource_tracker.release(res_id, force=True)
                released_mb += 10  # 假设每个资源约10MB
                
                # 通知碎片整理器有资源被释放
                self.defragmenter.notify_resource_released(10)
        
        # 重建列表，删除已释放的资源
        self.created_resources = self.created_resources[resources_to_release:]
        
        # 3. 释放碎片对象
        if hasattr(self, 'fragment_objects') and self.fragment_objects:
            self.fragment_objects = None
            released_mb += 50  # 假设碎片对象约50MB
        
        # 显示释放后的内存状态
        logger.info(f"已释放约 {released_mb}MB 内存")
        
        # 获取内存使用后状态
        memory_after = self.show_memory_info()
        
        # 计算实际释放的内存
        actual_released = max(0, memory_before["process_used_mb"] - memory_after["process_used_mb"])
        logger.info(f"实际减少内存使用: {actual_released:.2f}MB")
    
    def demonstrate_defragmentation(self) -> None:
        """演示内存碎片整理"""
        logger.info("===== 内存碎片整理演示 =====")
        
        # 1. 显示当前内存状态
        logger.info("当前内存状态:")
        memory_before = self.show_memory_info()
        
        # 2. 执行内存碎片整理
        logger.info("执行内存碎片整理...")
        start_time = time.time()
        success = compact_memory()
        elapsed = time.time() - start_time
        
        if success:
            logger.info(f"内存碎片整理成功，耗时: {elapsed:.3f}秒")
        else:
            logger.warning("内存碎片整理失败")
        
        # 3. 显示整理后内存状态
        logger.info("整理后内存状态:")
        memory_after = self.show_memory_info()
        
        # 4. 计算内存减少
        memory_reduced = max(0, memory_before["process_used_mb"] - memory_after["process_used_mb"])
        percent_reduced = (memory_reduced / memory_before["process_used_mb"] * 100 
                          if memory_before["process_used_mb"] > 0 else 0)
        
        logger.info(f"内存减少: {memory_reduced:.2f}MB ({percent_reduced:.1f}%)")
        
        # 5. 显示整理器状态
        status = self.defragmenter.get_status()
        
        status_data = [
            ["总整理次数", status["total_compacts"]],
            ["上次定时整理", f"{time.time() - status['last_auto_compact']:.0f}秒前" 
                       if status['last_auto_compact'] > 0 else "从未"],
            ["上次触发整理", f"{time.time() - status['last_trigger_compact']:.0f}秒前"
                       if status['last_trigger_compact'] > 0 else "从未"],
            ["待整理释放内存", f"{status['released_since_compact']:.1f}MB"],
            ["自动整理间隔", f"{status['config']['auto_compact_interval']}秒"],
            ["释放阈值", f"{status['config']['resource_release_threshold']}MB"]
        ]
        
        print("\n碎片整理器状态:")
        print(tabulate(status_data, tablefmt="grid"))
    
    def demonstrate_automatic_defrag(self) -> None:
        """演示自动碎片整理触发"""
        logger.info("===== 自动碎片整理触发演示 =====")
        
        # 1. 更新碎片整理器配置，使用更小的阈值以便演示
        self.defragmenter.update_config({
            "resource_release_threshold": 100,  # 降低阈值到100MB
            "auto_compact_interval": 300        # 降低间隔到5分钟
        })
        
        logger.info("已更新碎片整理器配置:")
        logger.info(f"  释放阈值: 100MB")
        logger.info(f"  自动整理间隔: 300秒")
        
        # 2. 分配一些内存
        self.allocate_memory(150)
        
        # 3. 释放内存，超过阈值，触发自动整理
        logger.info("释放内存，超过阈值，应触发自动整理...")
        self.release_memory(120)
        
        # 等待一小段时间，让自动整理有机会触发
        time.sleep(2)
        
        # 4. 显示整理器状态
        status = self.defragmenter.get_status()
        
        status_data = [
            ["总整理次数", status["total_compacts"]],
            ["上次触发整理", f"{time.time() - status['last_trigger_compact']:.0f}秒前"
                       if status['last_trigger_compact'] > 0 else "从未"],
            ["待整理释放内存", f"{status['released_since_compact']:.1f}MB"]
        ]
        
        print("\n触发后碎片整理器状态:")
        print(tabulate(status_data, tablefmt="grid"))
        
        # 检查是否触发了整理
        if time.time() - status['last_trigger_compact'] < 10:
            logger.info("自动整理已成功触发")
        else:
            logger.warning("自动整理可能未触发，请检查日志")
    
    def cleanup(self):
        """清理所有资源"""
        logger.info("清理所有资源...")
        
        # 释放大型对象
        self.large_objects = None
        
        # 释放碎片对象
        if hasattr(self, 'fragment_objects'):
            self.fragment_objects = None
        
        # 释放所有注册的资源
        for res_id in list(self.created_resources):
            self.resource_tracker.release(res_id, force=True)
        
        self.created_resources = []
        
        # 调用垃圾回收
        gc.collect()
        
        logger.info("所有资源已清理")


def main():
    """主函数"""
    try:
        # 创建演示对象
        demo = DefragmentationDemo()
        
        # 显示初始内存状态
        demo.show_memory_info()
        
        # 分配内存
        demo.allocate_memory(200)
        
        # 制造内存碎片
        demo.fragment_memory()
        
        # 演示1: 手动整理
        demo.demonstrate_defragmentation()
        
        # 演示2: 自动触发整理
        demo.demonstrate_automatic_defrag()
        
    except KeyboardInterrupt:
        logger.info("演示已被用户中断")
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
        import traceback

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        logger.error(traceback.format_exc())
    finally:
        # 清理资源
        if 'demo' in locals():
            demo.cleanup()
        
        logger.info("演示结束")


if __name__ == "__main__":
    main() 