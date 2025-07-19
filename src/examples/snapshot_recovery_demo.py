#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源快照恢复演示

该脚本演示VisionAI-ClipsMaster资源快照(ReleaseSnapshot)的功能，
展示在资源释放前创建快照和从快照恢复资源的过程。
"""

import os
import sys
import time
import logging
import numpy as np
from tabulate import tabulate
from typing import Dict, Any, List
import copy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SnapshotDemo")

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入项目模块
from src.memory.resource_tracker import get_resource_tracker
from src.memory.release_executor import get_resource_reaper
from src.memory.snapshot import get_release_snapshot

class SnapshotRecoveryDemo:
    """资源快照恢复演示类"""
    
    def __init__(self):
        """初始化演示"""
        # 获取资源管理组件
        self.resource_tracker = get_resource_tracker()
        self.resource_reaper = get_resource_reaper()
        self.snapshot_manager = get_release_snapshot()
        
        # 创建的资源ID列表
        self.created_resources = []
        
        # 直接存储资源对象引用(用于演示)
        self.resource_objects = {}
        
        logger.info("资源快照恢复演示初始化完成")
    
    def create_resources(self):
        """创建不同类型的测试资源"""
        logger.info("创建测试资源...")
        
        # 1. 创建高优先级资源 - 模型分片
        for i in range(2):
            shard_data = np.random.random((500, 500))  # 约2MB
            shard_id = f"model_shards:layer{i}"
            
            # 注册到资源跟踪器
            self.resource_tracker.register(
                "model_shards",
                f"layer{i}",
                shard_data,
                {
                    "size_mb": 2,
                    "layer_index": i,
                    "is_active": (i == 0)
                }
            )
            
            # 存储资源对象引用
            self.resource_objects[shard_id] = shard_data
            
            self.created_resources.append(shard_id)
            logger.info(f"已创建模型分片: {shard_id}")
        
        # 2. 创建中优先级资源 - 渲染缓存
        for i in range(1):
            # 创建一个模拟图像帧
            frame_data = np.zeros((720, 1280, 3), dtype=np.uint8)
            frame_data[:, :, 0] = np.random.randint(0, 255, (720, 1280))
            frame_id = f"render_cache:frame{i}"
            
            # 注册到资源跟踪器
            self.resource_tracker.register(
                "render_cache",
                f"frame{i}",
                frame_data,
                {
                    "size_mb": 2.5,
                    "frame_index": i,
                    "resolution": "720p"
                }
            )
            
            # 存储资源对象引用
            self.resource_objects[frame_id] = frame_data
            
            self.created_resources.append(frame_id)
            logger.info(f"已创建渲染缓存: {frame_id}")
        
        # 3. 创建低优先级资源 - 临时缓冲区
        buffer_data = {"results": [np.random.random(1000) for _ in range(3)]}
        buffer_id = f"temp_buffers:buffer0"
        
        # 注册到资源跟踪器
        self.resource_tracker.register(
            "temp_buffers",
            f"buffer0",
            buffer_data,
            {
                "size_mb": 0.5,
                "buffer_type": "computation",
                "is_temporary": True
            }
        )
        
        # 存储资源对象引用
        self.resource_objects[buffer_id] = buffer_data
        
        self.created_resources.append(buffer_id)
        logger.info(f"已创建临时缓冲区: {buffer_id}")
        
        logger.info(f"共创建了 {len(self.created_resources)} 个测试资源")
    
    def show_resource_info(self):
        """显示当前资源状态"""
        logger.info("===== 当前资源状态 =====")
        
        # 获取所有资源信息
        resources_info = []
        for res_id in self.created_resources:
            info = self.resource_tracker.get_resource_info(res_id)
            if info:
                # 提取资源类型
                res_type = res_id.split(":", 1)[0] if ":" in res_id else "unknown"
                
                # 提取关键信息
                metadata = info.get("metadata", {})
                size_mb = metadata.get("size_mb", 0)
                
                # 获取资源类型配置，确定优先级
                type_config = self.resource_tracker.resource_types.get(res_type, {})
                priority = type_config.get("priority", 999)
                
                # 检查是否有快照
                has_snapshot = self.snapshot_manager.has_snapshot(res_id)
                
                # 添加到资源信息列表
                resources_info.append([
                    res_id,
                    res_type,
                    priority,
                    size_mb,
                    "是" if has_snapshot else "否"
                ])
        
        # 显示资源表格
        headers = ["资源ID", "类型", "优先级", "大小(MB)", "有快照"]
        print("\n当前资源:")
        print(tabulate(resources_info, headers=headers, tablefmt="grid"))
    
    def create_snapshots(self):
        """为高优先级资源创建快照"""
        logger.info("===== 创建资源快照 =====")
        
        snapshot_count = 0
        for res_id in self.created_resources:
            # 获取直接存储的资源对象
            resource = self.resource_objects.get(res_id)
            
            if resource is not None:
                # 获取资源元数据
                metadata = None
                res_info = self.resource_tracker.get_resource_info(res_id)
                if res_info:
                    metadata = res_info.get("metadata", {})
                
                # 创建备份
                from src.memory.snapshot import backup_resource
                backup_data = backup_resource(resource)
                
                if backup_data is not None:
                    # 存储快照
                    self.snapshot_manager.snapshots[res_id] = {
                        'metadata': copy.deepcopy(metadata) if metadata else {},
                        'data': backup_data
                    }
                    self.snapshot_manager.snapshot_times[res_id] = time.time()
                    
                    # 成功创建
                    snapshot_count += 1
                    logger.info(f"成功为 {res_id} 创建快照")
                else:
                    logger.info(f"无法为 {res_id} 创建备份")
            else:
                logger.info(f"无法为 {res_id} 创建快照(无法获取资源对象)")
        
        logger.info(f"已创建 {snapshot_count} 个资源快照")
        
        # 显示快照列表
        snapshots = self.snapshot_manager.list_snapshots()
        if snapshots:
            snapshot_info = []
            for snap in snapshots:
                res_id = snap.get('resource_id')
                age = snap.get('age', 0)
                metadata = snap.get('metadata', {})
                res_type = res_id.split(":", 1)[0] if ":" in res_id else "unknown"
                
                snapshot_info.append([
                    res_id,
                    res_type,
                    f"{age:.1f}秒",
                    metadata.get('size_mb', 0)
                ])
            
            print("\n当前快照:")
            print(tabulate(snapshot_info, headers=["资源ID", "类型", "存在时间", "大小(MB)"], tablefmt="grid"))
        else:
            print("\n没有创建任何快照(可能所有资源优先级都不满足条件)")
    
    def demonstrate_snapshot_recovery(self):
        """演示快照恢复功能"""
        logger.info("===== 快照恢复演示 =====")
        
        # 选择一个模型分片资源进行恢复测试
        shard_id = next((res_id for res_id in self.created_resources 
                        if res_id.startswith("model_shards:")), None)
        
        if not shard_id:
            logger.warning("找不到模型分片资源")
            return
            
        # 检查是否有快照
        if not self.snapshot_manager.has_snapshot(shard_id):
            logger.info(f"为 {shard_id} 创建快照")
            
            # 获取直接存储的资源对象
            resource = self.resource_objects.get(shard_id)
            
            if resource is not None:
                # 获取资源元数据
                metadata = None
                res_info = self.resource_tracker.get_resource_info(shard_id)
                if res_info:
                    metadata = res_info.get("metadata", {})
                
                # 创建备份
                from src.memory.snapshot import backup_resource
                backup_data = backup_resource(resource)
                
                if backup_data is not None:
                    # 存储快照
                    self.snapshot_manager.snapshots[shard_id] = {
                        'metadata': copy.deepcopy(metadata) if metadata else {},
                        'data': backup_data
                    }
                    self.snapshot_manager.snapshot_times[shard_id] = time.time()
                    logger.info(f"成功为 {shard_id} 创建快照")
                else:
                    logger.warning(f"无法为 {shard_id} 创建备份")
            else:
                logger.warning(f"无法为 {shard_id} 创建快照(无法获取资源对象)")
        
        if not self.snapshot_manager.has_snapshot(shard_id):
            logger.warning(f"资源 {shard_id} 没有快照")
            return
            
        # 获取直接存储的资源对象
        resource = self.resource_objects.get(shard_id)
        
        if resource is None:
            logger.warning(f"无法获取资源对象: {shard_id}")
            return
            
        # 记录修改前的状态
        if isinstance(resource, np.ndarray):
            original_data = resource.copy()
            original_shape = resource.shape
            original_sum = resource.sum()
            
            print(f"\n原始资源状态:")
            print(f"  形状: {original_shape}")
            print(f"  数据和: {original_sum:.2f}")
            
            # 修改资源数据
            resource.fill(0.5)
            modified_sum = resource.sum()
            
            print(f"\n修改后资源状态:")
            print(f"  形状: {resource.shape}")
            print(f"  数据和: {modified_sum:.2f}")
            
            # 获取快照数据
            snapshot = self.snapshot_manager.snapshots[shard_id]
            backup_data = snapshot.get('data')
            
            # 手动恢复
            logger.info(f"从快照恢复资源: {shard_id}")
            start_time = time.time()
            
            # 对于NumPy数组，可以直接复制数据
            if isinstance(backup_data, np.ndarray) and resource.shape == backup_data.shape:
                np.copyto(resource, backup_data)
                success = True
            else:
                success = False
                
            elapsed = time.time() - start_time
            
            if success:
                # 检查恢复结果
                restored_sum = resource.sum()
                
                print(f"\n恢复后资源状态:")
                print(f"  形状: {resource.shape}")
                print(f"  数据和: {restored_sum:.2f}")
                print(f"  恢复耗时: {elapsed:.3f}秒")
                
                # 验证恢复是否成功
                if abs(original_sum - restored_sum) < 0.001:
                    logger.info(f"恢复成功！数据与原始状态匹配")
                else:
                    logger.warning(f"恢复后数据与原始状态不匹配")
            else:
                logger.error(f"从快照恢复失败: {shard_id}")
        else:
            logger.warning(f"资源不是NumPy数组，无法演示数据恢复")
    
    def demonstrate_release_with_recovery(self):
        """演示释放后恢复"""
        logger.info("===== 释放后恢复演示 =====")
        
        # 选择一个渲染缓存资源进行释放和恢复测试
        frame_id = next((res_id for res_id in self.created_resources 
                        if res_id.startswith("render_cache:")), None)
        
        if not frame_id:
            logger.warning("找不到渲染缓存资源")
            return
            
        # 确保有快照
        if not self.snapshot_manager.has_snapshot(frame_id):
            logger.info(f"为 {frame_id} 创建快照")
            
            # 获取直接存储的资源对象
            resource = self.resource_objects.get(frame_id)
            
            if resource is not None:
                # 获取资源元数据
                metadata = None
                res_info = self.resource_tracker.get_resource_info(frame_id)
                if res_info:
                    metadata = res_info.get("metadata", {})
                
                # 创建备份
                from src.memory.snapshot import backup_resource
                backup_data = backup_resource(resource)
                
                if backup_data is not None:
                    # 存储快照
                    self.snapshot_manager.snapshots[frame_id] = {
                        'metadata': copy.deepcopy(metadata) if metadata else {},
                        'data': backup_data
                    }
                    self.snapshot_manager.snapshot_times[frame_id] = time.time()
                    logger.info(f"成功为 {frame_id} 创建快照")
                else:
                    logger.warning(f"无法为 {frame_id} 创建备份")
            else:
                logger.warning(f"无法为 {frame_id} 创建快照(无法获取资源对象)")
        
        if not self.snapshot_manager.has_snapshot(frame_id):
            logger.warning(f"无法为 {frame_id} 创建快照")
            return
            
        # 保存原始对象的备份(仅用于验证)
        original_resource = None
        if frame_id in self.resource_objects:
            original_resource = self.resource_objects[frame_id]
            if isinstance(original_resource, np.ndarray):
                original_shape = original_resource.shape
                logger.info(f"原始对象形状: {original_shape}")
        
        # 释放资源
        logger.info(f"释放资源: {frame_id}")
        release_success = self.resource_tracker.release(frame_id, force=True)
        
        if release_success:
            # 从资源列表中移除
            if frame_id in self.created_resources:
                self.created_resources.remove(frame_id)
                
            logger.info(f"资源 {frame_id} 已释放")
            
            # 清除本地引用
            if frame_id in self.resource_objects:
                del self.resource_objects[frame_id]
            
            # 尝试从快照恢复
            logger.info(f"从快照恢复资源: {frame_id}")
            start_time = time.time()
            recovery_success = self.snapshot_manager.rollback(frame_id)
            elapsed = time.time() - start_time
            
            if recovery_success:
                logger.info(f"已成功从快照恢复资源: {frame_id}, 耗时: {elapsed:.3f}秒")
                
                # 恢复后资源应该被重新注册，添加回资源列表
                self.created_resources.append(frame_id)
                
                # 验证资源是否存在
                res_info = self.resource_tracker.get_resource_info(frame_id)
                if res_info:
                    logger.info(f"恢复的资源已重新注册到资源跟踪器")
                    
                    # 尝试获取恢复后的资源对象引用
                    resource = None
                    with self.resource_tracker.lock:
                        if frame_id in self.resource_tracker.resources:
                            res_detail = self.resource_tracker.resources[frame_id]
                            if "ref" in res_detail:
                                ref = res_detail["ref"]
                                if ref:
                                    resource = ref()
                            elif "direct_ref" in res_detail:
                                resource = res_detail["direct_ref"]
                    
                    if resource is not None:
                        # 更新本地引用
                        self.resource_objects[frame_id] = resource
                        
                        # 验证恢复是否成功
                        if isinstance(resource, np.ndarray) and original_resource is not None:
                            if resource.shape == original_shape:
                                logger.info(f"恢复的资源形状与原始一致: {resource.shape}")
                            else:
                                logger.warning(f"恢复的资源形状不一致: 原始={original_shape}, 恢复后={resource.shape}")
                    else:
                        logger.warning(f"无法获取恢复后的资源对象")
                else:
                    logger.warning(f"恢复的资源未重新注册")
            else:
                logger.error(f"从快照恢复失败: {frame_id}")
        else:
            logger.error(f"释放资源失败: {frame_id}")
    
    def cleanup(self):
        """清理所有资源"""
        logger.info("清理所有资源...")
        
        # 清除所有快照
        snapshot_count = self.snapshot_manager.clear_snapshots()
        logger.info(f"已清除 {snapshot_count} 个快照")
        
        # 释放所有剩余资源
        for res_id in list(self.created_resources):
            self.resource_tracker.release(res_id, force=True)
            self.created_resources.remove(res_id)
        
        logger.info("所有资源已清理")


def main():
    """主函数"""
    try:
        # 创建演示对象
        demo = SnapshotRecoveryDemo()
        
        # 创建测试资源
        demo.create_resources()
        
        # 显示资源信息
        demo.show_resource_info()
        
        # 创建快照
        demo.create_snapshots()
        
        # 演示1: 资源快照恢复
        demo.demonstrate_snapshot_recovery()
        
        # 演示2: 释放后恢复
        demo.demonstrate_release_with_recovery()
        
        # 显示最终资源状态
        demo.show_resource_info()
        
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