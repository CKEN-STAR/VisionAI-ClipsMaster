#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源释放执行器演示

该脚本演示VisionAI-ClipsMaster资源释放执行器(ResourceReaper)的功能，
展示不同类型资源的释放过程和执行器与资源跟踪器的集成。
"""

import os
import sys
import time
import logging
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ResourceReaperDemo")

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入项目模块
from src.memory.resource_tracker import get_resource_tracker
from src.memory.release_executor import get_resource_reaper
from src.utils.memory_guard import get_memory_guard

class ResourceReaperDemo:
    """资源释放执行器演示类"""
    
    def __init__(self):
        """初始化演示"""
        # 获取资源管理组件
        self.resource_tracker = get_resource_tracker()
        self.resource_reaper = get_resource_reaper()
        self.memory_guard = get_memory_guard()
        
        # 创建的资源ID列表
        self.created_resources = []
        
        logger.info("资源释放执行器演示初始化完成")
    
    def create_resources(self):
        """创建不同类型的测试资源"""
        logger.info("创建测试资源...")
        
        # 1. 创建大型NumPy数组作为模型分片
        for i in range(3):
            shard_data = np.random.random((1000, 1000))  # 约8MB
            shard_id = f"model_shards:layer{i}"
            
            # 注册到资源跟踪器
            self.resource_tracker.register(
                "model_shards",
                f"layer{i}",
                shard_data,
                {
                    "size_mb": 8,
                    "layer_index": i,
                    "is_active": (i == 0)
                }
            )
            
            self.created_resources.append(shard_id)
            logger.info(f"已创建模型分片: {shard_id}")
        
        # 2. 创建模拟渲染缓存
        for i in range(2):
            # 创建一个模拟图像帧
            frame_data = np.zeros((1080, 1920, 3), dtype=np.uint8)
            frame_data[:, :, 0] = np.random.randint(0, 255, (1080, 1920))
            frame_id = f"render_cache:frame{i}"
            
            # 注册到资源跟踪器
            self.resource_tracker.register(
                "render_cache",
                f"frame{i}",
                frame_data,
                {
                    "size_mb": 6,
                    "frame_index": i,
                    "resolution": "1080p",
                    "persist_to_disk": True,
                    "persist_path": f"temp/frames/frame{i}.jpg"
                }
            )
            
            self.created_resources.append(frame_id)
            logger.info(f"已创建渲染缓存: {frame_id}")
            
        # 3. 创建模拟临时缓冲区
        for i in range(5):
            buffer_data = {"results": [np.random.random(10000) for _ in range(5)]}
            buffer_id = f"temp_buffers:buffer{i}"
            
            # 注册到资源跟踪器
            self.resource_tracker.register(
                "temp_buffers",
                f"buffer{i}",
                buffer_data,
                {
                    "size_mb": 4,
                    "buffer_type": "computation",
                    "is_temporary": True
                }
            )
            
            self.created_resources.append(buffer_id)
            logger.info(f"已创建临时缓冲区: {buffer_id}")
        
        # 4. 创建模拟字幕索引
        subtitle_data = {
            "segments": [
                {"id": i, "text": f"字幕段落 {i}", "start": i*10, "end": (i+1)*10} 
                for i in range(20)
            ],
            "language": "zh-CN",
            "total_duration": 200
        }
        
        # 注册到资源跟踪器
        self.resource_tracker.register(
            "subtitle_index",
            "main_subtitles",
            subtitle_data,
            {
                "size_mb": 2,
                "language": "zh-CN",
                "incremental_release": True,
                "total_segments": 20
            }
        )
        
        self.created_resources.append("subtitle_index:main_subtitles")
        logger.info("已创建字幕索引: subtitle_index:main_subtitles")
        
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
                create_time = info.get("create_time", 0)
                last_access = info.get("last_access", 0)
                is_expired = info.get("is_expired", False)
                
                # 计算存活时间
                age = time.time() - create_time
                
                # 添加到资源信息列表
                resources_info.append([
                    res_id,
                    res_type,
                    size_mb,
                    f"{age:.1f}秒",
                    "是" if is_expired else "否"
                ])
        
        # 显示资源表格
        headers = ["资源ID", "类型", "大小(MB)", "存活时间", "是否过期"]
        print("\n当前资源:")
        print(tabulate(resources_info, headers=headers, tablefmt="grid"))
    
    def demonstrate_direct_release(self):
        """演示直接使用资源释放执行器释放资源"""
        logger.info("===== 直接释放演示 =====")
        
        # 选择一个临时缓冲区进行释放
        buffer_id = next((res_id for res_id in self.created_resources 
                         if res_id.startswith("temp_buffers:")), None)
        
        if not buffer_id:
            logger.warning("找不到临时缓冲区资源")
            return
            
        # 获取资源信息
        info = self.resource_tracker.get_resource_info(buffer_id)
        if not info:
            logger.warning(f"找不到资源信息: {buffer_id}")
            return
            
        resource = None
        if "ref" in info:
            ref = info.get("ref")
            if ref:
                resource = ref()
        
        # 显示释放前状态
        logger.info(f"即将释放资源: {buffer_id}")
        print(f"释放前资源跟踪器统计: {self.resource_tracker.get_stats()['current_count']} 个资源")
        print(f"释放前执行器统计: {self.resource_reaper.get_stats()['total_released']} 个已释放")
        
        # 直接使用资源释放执行器
        start_time = time.time()
        success = self.resource_reaper.release(buffer_id, resource, info.get("metadata"))
        elapsed = time.time() - start_time
        
        # 显示结果
        if success:
            logger.info(f"使用资源释放执行器成功释放: {buffer_id}, 耗时: {elapsed:.3f}秒")
        else:
            logger.error(f"使用资源释放执行器释放失败: {buffer_id}")
        
        # 从列表中移除
        if buffer_id in self.created_resources:
            self.created_resources.remove(buffer_id)
        
        # 显示释放后状态
        print(f"释放后资源跟踪器统计: {self.resource_tracker.get_stats()['current_count']} 个资源")
        print(f"释放后执行器统计: {self.resource_reaper.get_stats()['total_released']} 个已释放")
        
        # 显示执行器统计信息的详细内容
        reaper_stats = self.resource_reaper.get_stats()
        print("\n资源释放执行器统计:")
        for key, value in reaper_stats.items():
            if key == "by_type":
                print("  按类型统计:")
                for t, count in value.items():
                    print(f"    - {t}: {count}个")
            else:
                print(f"  {key}: {value}")
    
    def demonstrate_tracker_integration(self):
        """演示资源跟踪器集成资源释放执行器"""
        logger.info("===== 资源跟踪器集成演示 =====")
        
        # 选择一个模型分片资源进行释放
        shard_id = next((res_id for res_id in self.created_resources 
                        if res_id.startswith("model_shards:")), None)
        
        if not shard_id:
            logger.warning("找不到模型分片资源")
            return
            
        # 显示释放前状态
        logger.info(f"即将通过资源跟踪器释放: {shard_id}")
        print(f"释放前资源跟踪器统计: {self.resource_tracker.get_stats()['current_count']} 个资源")
        print(f"释放前执行器统计: {self.resource_reaper.get_stats()['total_released']} 个已释放")
        
        # 使用资源跟踪器释放资源
        start_time = time.time()
        success = self.resource_tracker.release(shard_id, force=True)
        elapsed = time.time() - start_time
        
        # 显示结果
        if success:
            logger.info(f"通过资源跟踪器成功释放: {shard_id}, 耗时: {elapsed:.3f}秒")
        else:
            logger.error(f"通过资源跟踪器释放失败: {shard_id}")
        
        # 从列表中移除
        if shard_id in self.created_resources:
            self.created_resources.remove(shard_id)
        
        # 显示释放后状态
        print(f"释放后资源跟踪器统计: {self.resource_tracker.get_stats()['current_count']} 个资源")
        print(f"释放后执行器统计: {self.resource_reaper.get_stats()['total_released']} 个已释放")
    
    def demonstrate_type_specific_release(self):
        """演示类型特定的释放操作"""
        logger.info("===== 类型特定释放演示 =====")
        
        # 选择一个渲染缓存资源进行释放
        render_id = next((res_id for res_id in self.created_resources 
                         if res_id.startswith("render_cache:")), None)
        
        if not render_id:
            logger.warning("找不到渲染缓存资源")
            return
            
        # 获取资源信息
        info = self.resource_tracker.get_resource_info(render_id)
        if not info:
            logger.warning(f"找不到资源信息: {render_id}")
            return
            
        # 显示释放前状态和资源特定信息
        logger.info(f"即将释放渲染缓存: {render_id}")
        
        metadata = info.get("metadata", {})
        print(f"\n渲染缓存信息:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        # 使用资源跟踪器释放资源
        start_time = time.time()
        success = self.resource_tracker.release(render_id, force=True)
        elapsed = time.time() - start_time
        
        # 显示结果
        if success:
            logger.info(f"成功释放渲染缓存: {render_id}, 耗时: {elapsed:.3f}秒")
            
            # 检查是否已创建持久化文件
            persist_path = metadata.get("persist_path")
            if persist_path and os.path.exists(persist_path):
                file_size = os.path.getsize(persist_path) / (1024)  # KB
                print(f"已将渲染缓存持久化到磁盘: {persist_path}, 大小: {file_size:.1f}KB")
                
                # 可选: 展示图像
                # plt.figure(figsize=(8, 4.5))
                # plt.imshow(plt.imread(persist_path))
                # plt.title(f"持久化帧: {render_id}")
                # plt.show()
            else:
                print("帧未持久化到磁盘")
        else:
            logger.error(f"释放渲染缓存失败: {render_id}")
        
        # 从列表中移除
        if render_id in self.created_resources:
            self.created_resources.remove(render_id)
    
    def demonstrate_incremental_release(self):
        """演示增量释放操作"""
        logger.info("===== 增量释放演示 =====")
        
        # 获取字幕索引资源
        subtitle_id = "subtitle_index:main_subtitles"
        
        if subtitle_id not in self.created_resources:
            logger.warning("找不到字幕索引资源")
            return
            
        # 获取资源信息
        info = self.resource_tracker.get_resource_info(subtitle_id)
        if not info:
            logger.warning(f"找不到资源信息: {subtitle_id}")
            return
            
        # 获取字幕数据引用
        subtitle_data = None
        if "ref" in info:
            ref = info.get("ref")
            if ref:
                subtitle_data = ref()
        
        if not subtitle_data:
            logger.warning("字幕数据为空")
            return
        
        # 显示释放前的段落数量
        segments_before = len(subtitle_data.get("segments", []))
        logger.info(f"释放前字幕段落数量: {segments_before}")
        
        # 使用资源释放执行器进行增量释放
        metadata = info.get("metadata", {})
        success = self.resource_reaper.release(subtitle_id, subtitle_data, metadata)
        
        # 检查释放后的段落数量
        if success:
            segments_after = len(subtitle_data.get("segments", []))
            logger.info(f"增量释放后字幕段落数量: {segments_after}")
            
            if segments_after < segments_before:
                logger.info(f"成功增量释放字幕数据，保留了 {segments_after} 个最新段落")
            else:
                logger.warning("增量释放可能未生效")
    
    def cleanup(self):
        """清理所有资源"""
        logger.info("清理所有资源...")
        
        # 释放所有剩余资源
        for res_id in list(self.created_resources):
            self.resource_tracker.release(res_id, force=True)
            self.created_resources.remove(res_id)
        
        # 显示清理后的统计信息
        reaper_stats = self.resource_reaper.get_stats()
        logger.info(f"已释放总计 {reaper_stats['total_released']} 个资源")
        logger.info(f"预估释放内存: {reaper_stats['estimated_mb_freed']:.1f}MB")


def main():
    """主函数"""
    try:
        # 创建演示对象
        demo = ResourceReaperDemo()
        
        # 创建测试资源
        demo.create_resources()
        
        # 显示资源信息
        demo.show_resource_info()
        
        # 演示1: 直接使用资源释放执行器
        demo.demonstrate_direct_release()
        
        # 演示2: 资源跟踪器集成
        demo.demonstrate_tracker_integration()
        
        # 演示3: 类型特定的释放操作
        demo.demonstrate_type_specific_release()
        
        # 演示4: 增量释放
        demo.demonstrate_incremental_release()
        
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