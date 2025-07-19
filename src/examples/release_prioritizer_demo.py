#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
释放优先级决策树演示

该脚本演示VisionAI-ClipsMaster中的资源释放优先级决策系统，
展示在内存压力下系统如何智能决定资源释放顺序。
"""

import os
import sys
import time
import logging
import argparse
import psutil
import numpy as np
from typing import Dict, List, Any
import matplotlib.pyplot as plt
from tabulate import tabulate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ReleasePrioritizerDemo")

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入项目模块
from src.memory.resource_tracker import get_resource_tracker
from src.memory.release_prioritizer import get_release_prioritizer
from src.utils.memory_guard import get_memory_guard
from src.utils.device_manager import get_device_manager

class PrioritizerDemo:
    """释放优先级决策树演示类"""
    
    def __init__(self):
        """初始化演示"""
        # 获取资源管理组件
        self.resource_tracker = get_resource_tracker()
        self.release_prioritizer = get_release_prioritizer()
        self.memory_guard = get_memory_guard()
        self.device_manager = get_device_manager()
        
        # 创建的资源ID列表
        self.created_resources = []
        
        logger.info("释放优先级决策树演示初始化完成")
    
    def create_resource(self, resource_type: str, name: str, size_mb: int, 
                       additional_meta: Dict[str, Any] = None) -> str:
        """
        创建测试资源
        
        Args:
            resource_type: 资源类型
            name: 资源名称
            size_mb: 资源大小(MB)
            additional_meta: 附加元数据
            
        Returns:
            str: 资源ID
        """
        # 创建NumPy数组作为数据
        buffer_size = max(1, size_mb * 1024 * 1024 // 8)  # 转换为double元素数量
        data = np.random.random(buffer_size)
        
        # 准备元数据
        metadata = {"size_mb": size_mb, "creation_time": time.time()}
        
        # 添加附加元数据
        if additional_meta:
            metadata.update(additional_meta)
        
        # 注册到资源跟踪器
        full_id = self.resource_tracker.register(
            resource_type,
            name,
            data,
            metadata
        )
        
        # 添加到已创建资源列表
        self.created_resources.append(full_id)
        
        logger.info(f"已创建 {size_mb}MB 的 {resource_type} 资源: {full_id}")
        return full_id
    
    def simulate_different_resources(self):
        """模拟创建不同类型和特性的资源"""
        # 1. 创建临时缓冲区
        for i in range(3):
            self.create_resource(
                "temp_buffers", 
                f"buffer_{i}", 
                50 + i * 20,  # 50MB, 70MB, 90MB
                {"buffer_type": "calculation", "is_partial": True}
            )
        
        # 2. 创建模型分片
        for i in range(5):
            self.create_resource(
                "model_shards", 
                f"layer_{i}", 
                100,  # 每个100MB
                {"layer_index": i, "is_attention": i % 2 == 0}
            )
        
        # 3. 创建渲染缓存
        for i in range(2):
            self.create_resource(
                "render_cache", 
                f"frame_{i}", 
                200,  # 每个200MB
                {"frame_index": i, "compression_enabled": True}
            )
        
        # 4. 创建模型权重缓存
        self.create_resource(
            "model_weights_cache", 
            "qwen2.5-7b-zh", 
            500,  # 500MB (实际会更大，这里是演示)
            {"is_active": True, "model_type": "qwen"}
        )
        
        # 5. 创建字幕索引
        self.create_resource(
            "subtitle_index", 
            "subtitle_idx", 
            30,  # 30MB
            {"language": "zh-CN", "segments": 120}
        )
    
    def simulate_access_patterns(self):
        """模拟不同的资源访问模式"""
        logger.info("模拟资源访问模式...")
        
        # 随机选择一些资源进行访问
        for _ in range(10):
            if self.created_resources:
                # 随机选择30%的资源
                indices = np.random.choice(
                    len(self.created_resources),
                    size=max(1, int(len(self.created_resources) * 0.3)),
                    replace=False
                )
                
                for idx in indices:
                    res_id = self.created_resources[idx]
                    # 更新访问时间
                    self.resource_tracker.touch(res_id)
                
                # 等待一小段时间
                time.sleep(0.5)
        
        # 特别关注模型权重的访问
        model_id = next((res_id for res_id in self.created_resources 
                         if "model_weights_cache" in res_id), None)
        if model_id:
            logger.info(f"频繁访问模型: {model_id}")
            for _ in range(5):
                self.resource_tracker.touch(model_id)
                time.sleep(0.2)
    
    def simulate_aging(self, aging_time: int = 10):
        """
        模拟资源老化
        
        Args:
            aging_time: 老化时间(秒)
        """
        logger.info(f"模拟资源老化 {aging_time} 秒...")
        
        # 特定模式下访问某些资源
        for i in range(aging_time):
            # 每3秒访问一次模型权重
            if i % 3 == 0:
                model_id = next((res_id for res_id in self.created_resources 
                              if "model_weights_cache" in res_id), None)
                if model_id:
                    self.resource_tracker.touch(model_id)
            
            # 每2秒访问一次模型分片
            if i % 2 == 0:
                shard_id = next((res_id for res_id in self.created_resources 
                               if "model_shards" in res_id), None)
                if shard_id:
                    self.resource_tracker.touch(shard_id)
            
            time.sleep(1)
        
        logger.info("资源老化完成")
    
    def demonstrate_prioritized_release(self):
        """演示优先级排序释放"""
        logger.info("=== 优先级排序释放演示 ===")
        
        # 1. 获取所有资源信息
        resources = {}
        resource_info = []
        total_size_mb = 0
        
        for res_id in self.created_resources:
            info = self.resource_tracker.get_resource_info(res_id)
            if info:
                resources[res_id] = info
                
                # 提取关键信息用于显示
                res_type = res_id.split(":", 1)[0] if ":" in res_id else "unknown"
                metadata = info.get("metadata", {})
                size_mb = metadata.get("size_mb", 0)
                
                # 获取资源类型配置
                type_config = self.resource_tracker.resource_types.get(res_type, {})
                priority = type_config.get("priority", 999)
                
                # 计算上次访问时间间隔
                last_access = info.get("last_access", 0)
                access_age = time.time() - last_access
                
                # 添加到资源信息列表
                resource_info.append([
                    res_id, 
                    res_type,
                    priority,
                    f"{access_age:.1f}秒",
                    size_mb,
                    "是" if info.get("is_expired", False) else "否"
                ])
                
                total_size_mb += size_mb
        
        # 2. 显示资源信息表格
        headers = ["资源ID", "类型", "优先级", "上次访问", "大小(MB)", "是否过期"]
        print("\n当前资源信息:")
        print(tabulate(resource_info, headers=headers, tablefmt="grid"))
        print(f"总大小: {total_size_mb} MB")
        
        # 3. 获取释放优先级排序
        priority_list = self.release_prioritizer.calculate_release_priority(
            resources, 
            self.resource_tracker.resource_types
        )
        
        # 4. 显示释放顺序
        print("\n释放优先级顺序:")
        priority_info = []
        for i, res_id in enumerate(priority_list):
            if res_id in resources:
                info = resources[res_id]
                res_type = res_id.split(":", 1)[0] if ":" in res_id else "unknown"
                metadata = info.get("metadata", {})
                size_mb = metadata.get("size_mb", 0)
                
                # 获取释放原因解释
                explanation = self.release_prioritizer.explain_decision(
                    res_id, resources, self.resource_tracker.resource_types
                )
                reasons = ", ".join(explanation.get("release_reason", ["未知"]))
                
                priority_info.append([
                    i + 1,
                    res_id,
                    res_type,
                    size_mb,
                    reasons
                ])
        
        print(tabulate(priority_info, 
                     headers=["顺序", "资源ID", "类型", "大小(MB)", "释放原因"], 
                     tablefmt="grid"))
    
    def demonstrate_memory_pressure_release(self):
        """演示内存压力下的资源释放"""
        logger.info("=== 内存压力下的资源释放演示 ===")
        
        # 计算当前资源总大小
        total_size_mb = 0
        for res_id in self.created_resources:
            info = self.resource_tracker.get_resource_info(res_id)
            if info:
                metadata = info.get("metadata", {})
                size_mb = metadata.get("size_mb", 0)
                total_size_mb += size_mb
        
        # 模拟需要释放的内存
        needed_mb = total_size_mb * 0.3  # 释放30%的资源
        logger.info(f"模拟内存压力，需要释放 {needed_mb:.1f}MB 资源")
        
        # 获取释放候选资源
        candidates = self.resource_tracker.get_release_candidates(needed_mb)
        
        # 显示候选资源
        print("\n释放候选资源:")
        candidate_info = []
        candidate_size_mb = 0
        
        for res_id in candidates:
            info = self.resource_tracker.get_resource_info(res_id)
            if info:
                res_type = res_id.split(":", 1)[0] if ":" in res_id else "unknown"
                metadata = info.get("metadata", {})
                size_mb = metadata.get("size_mb", 0)
                candidate_size_mb += size_mb
                
                candidate_info.append([
                    res_id,
                    res_type,
                    size_mb,
                    f"{candidate_size_mb:.1f}/{needed_mb:.1f}"
                ])
        
        print(tabulate(candidate_info, 
                     headers=["资源ID", "类型", "大小(MB)", "累计/目标(MB)"], 
                     tablefmt="grid"))
        
        # 释放资源
        released_count = self.resource_tracker.release_by_memory_pressure(needed_mb)
        logger.info(f"已释放 {released_count} 个资源，缓解内存压力")
        
        # 更新创建的资源列表
        self.created_resources = [
            res_id for res_id in self.created_resources
            if self.resource_tracker.get_resource_info(res_id) is not None
        ]
    
    def cleanup(self):
        """清理所有资源"""
        logger.info("清理所有资源...")
        
        for res_id in list(self.created_resources):
            self.resource_tracker.release(res_id, force=True)
        
        self.created_resources.clear()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="释放优先级决策树演示")
    parser.add_argument("--demo", choices=["all", "priority", "pressure"], 
                        default="all", help="演示类型")
    args = parser.parse_args()
    
    try:
        # 创建演示对象
        demo = PrioritizerDemo()
        
        # 创建测试资源
        demo.simulate_different_resources()
        
        # 模拟资源访问模式
        demo.simulate_access_patterns()
        
        # 模拟资源老化
        demo.simulate_aging(10)
        
        # 根据选择的演示类型执行不同的演示
        if args.demo in ["all", "priority"]:
            demo.demonstrate_prioritized_release()
        
        if args.demo in ["all", "pressure"]:
            demo.demonstrate_memory_pressure_release()
        
    except KeyboardInterrupt:
        logger.info("演示已被用户中断")
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # 清理资源
        if 'demo' in locals():
            demo.cleanup()
        
        logger.info("演示结束")


if __name__ == "__main__":
    main() 