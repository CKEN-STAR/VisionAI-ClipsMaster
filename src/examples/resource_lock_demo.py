#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源锁定机制演示

该脚本演示VisionAI-ClipsMaster资源锁定机制的使用方式，
展示如何在多线程环境下安全访问共享资源。
"""

import os
import sys
import time
import logging
import threading
import random
from tabulate import tabulate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LockDemo")

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入项目模块
from src.memory.lock_manager import get_resource_lock, read_locked, write_locked
from src.memory.resource_tracker import get_resource_tracker

class ResourceLockDemo:
    """资源锁定机制演示类"""
    
    def __init__(self):
        """初始化演示"""
        # 获取资源组件
        self.resource_tracker = get_resource_tracker()
        self.lock_manager = get_resource_lock()
        
        # 共享资源字典
        self.shared_resources = {}
        
        # 演示运行标志
        self.running = False
        
        # 操作统计
        self.stats = {
            "read_success": 0,
            "read_failed": 0,
            "write_success": 0,
            "write_failed": 0,
            "lock_timeouts": 0
        }
        
        # 统计互斥锁
        self.stats_lock = threading.Lock()
        
        logger.info("资源锁定演示初始化完成")
    
    def create_test_resources(self, count: int = 5) -> None:
        """
        创建测试资源
        
        Args:
            count: 要创建的资源数量
        """
        logger.info(f"创建 {count} 个测试资源...")
        
        resource_types = ["model_shards", "temp_buffers", "render_cache"]
        
        for i in range(count):
            resource_type = random.choice(resource_types)
            resource_id = f"demo_resource_{i}"
            
            # 创建资源数据
            resource_data = {
                "id": resource_id,
                "type": resource_type,
                "value": 0,  # 初始值为0
                "access_count": 0
            }
            
            # 注册到资源跟踪器
            full_id = self.resource_tracker.register(
                resource_type,
                resource_id,
                resource_data,
                {"size_mb": 10, "is_demo": True}
            )
            
            # 添加到共享资源字典
            self.shared_resources[resource_id] = resource_data
            
            logger.info(f"已创建资源: {full_id}")
            
        logger.info(f"已创建 {len(self.shared_resources)} 个测试资源")
    
    def read_resource(self, res_id: str, thread_name: str, timeout: float = 5.0) -> None:
        """
        读取资源演示
        
        Args:
            res_id: 资源ID
            thread_name: 线程名称
            timeout: 超时时间
        """
        logger.info(f"[{thread_name}] 尝试读取资源 {res_id}")
        
        # 使用上下文管理器获取读锁
        with read_locked(res_id, timeout) as acquired:
            if acquired:
                # 更新统计信息
                with self.stats_lock:
                    self.stats["read_success"] += 1
                
                # 安全读取共享资源
                if res_id in self.shared_resources:
                    resource = self.shared_resources[res_id]
                    value = resource["value"]
                    access_count = resource["access_count"]
                    
                    # 更新访问计数
                    resource["access_count"] = access_count + 1
                    
                    # 通知资源跟踪器访问了资源
                    self.resource_tracker.touch(res_id)
                    
                    logger.info(f"[{thread_name}] 成功读取资源 {res_id}，值: {value}，访问次数: {access_count + 1}")
                    
                    # 模拟读取操作耗时
                    time.sleep(random.uniform(0.5, 2.0))
            else:
                # 获取锁超时
                with self.stats_lock:
                    self.stats["read_failed"] += 1
                    self.stats["lock_timeouts"] += 1
                
                logger.warning(f"[{thread_name}] 读取资源 {res_id} 超时")
    
    def write_resource(self, res_id: str, thread_name: str, timeout: float = 5.0) -> None:
        """
        写入资源演示
        
        Args:
            res_id: 资源ID
            thread_name: 线程名称
            timeout: 超时时间
        """
        logger.info(f"[{thread_name}] 尝试写入资源 {res_id}")
        
        # 使用上下文管理器获取写锁
        with write_locked(res_id, timeout) as acquired:
            if acquired:
                # 更新统计信息
                with self.stats_lock:
                    self.stats["write_success"] += 1
                
                # 安全写入共享资源
                if res_id in self.shared_resources:
                    resource = self.shared_resources[res_id]
                    old_value = resource["value"]
                    
                    # 更新值
                    new_value = old_value + random.randint(1, 10)
                    resource["value"] = new_value
                    
                    # 更新访问计数
                    resource["access_count"] = resource["access_count"] + 1
                    
                    # 通知资源跟踪器访问了资源
                    self.resource_tracker.touch(res_id)
                    
                    logger.info(f"[{thread_name}] 成功写入资源 {res_id}，值: {old_value} -> {new_value}")
                    
                    # 模拟写入操作耗时
                    time.sleep(random.uniform(1.0, 3.0))
            else:
                # 获取锁超时
                with self.stats_lock:
                    self.stats["write_failed"] += 1
                    self.stats["lock_timeouts"] += 1
                
                logger.warning(f"[{thread_name}] 写入资源 {res_id} 超时")
    
    def run_concurrent_access(self, duration: int = 30) -> None:
        """
        运行并发访问演示
        
        Args:
            duration: 演示持续时间(秒)
        """
        if not self.shared_resources:
            logger.error("没有可用的测试资源，请先创建资源")
            return
            
        logger.info(f"开始并发访问演示，将持续 {duration} 秒...")
        
        # 重置运行标志和统计信息
        self.running = True
        self.stats = {
            "read_success": 0,
            "read_failed": 0,
            "write_success": 0,
            "write_failed": 0,
            "lock_timeouts": 0
        }
        
        # 创建线程组
        threads = []
        max_threads = 10
        
        # 开始时间
        start_time = time.time()
        
        # 创建并启动访问线程
        thread_id = 0
        
        try:
            while self.running and time.time() - start_time < duration:
                # 如果活动线程数量低于上限，创建新线程
                active_threads = [t for t in threads if t.is_alive()]
                if len(active_threads) < max_threads:
                    thread_id += 1
                    thread_name = f"Thread-{thread_id}"
                    
                    # 随机选择一个资源
                    res_id = random.choice(list(self.shared_resources.keys()))
                    
                    # 随机决定是读取还是写入操作
                    if random.random() < 0.7:  # 70%概率是读取操作
                        thread = threading.Thread(
                            target=self.read_resource,
                            args=(res_id, thread_name, random.uniform(1.0, 5.0)),
                            name=thread_name
                        )
                    else:  # 30%概率是写入操作
                        thread = threading.Thread(
                            target=self.write_resource,
                            args=(res_id, thread_name, random.uniform(1.0, 5.0)),
                            name=thread_name
                        )
                    
                    # 将线程添加到线程组并启动
                    threads.append(thread)
                    thread.start()
                
                # 短暂休眠，避免太频繁创建线程
                time.sleep(0.5)
                
                # 每5秒显示一次当前状态
                elapsed = time.time() - start_time
                if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                    self.show_current_status()
            
            # 等待所有线程完成
            for t in threads:
                if t.is_alive():
                    t.join(timeout=1.0)
            
            # 显示最终统计信息
            logger.info("并发访问演示完成")
            self.show_final_stats()
            
        except KeyboardInterrupt:
            logger.info("演示被用户中断")
            self.running = False
            
            # 等待线程完成
            for t in threads:
                if t.is_alive():
                    t.join(timeout=1.0)
    
    def show_current_status(self) -> None:
        """显示当前锁状态"""
        # 获取所有锁的状态
        lock_states = self.lock_manager.get_all_locks()
        
        # 显示活跃的锁
        active_locks = [lock for lock in lock_states if lock["is_locked"]]
        if active_locks:
            logger.info(f"当前活跃锁: {len(active_locks)} 个")
            for lock in active_locks:
                res_id = lock["resource_id"]
                readers = lock["readers"]
                writers = lock["writers"]
                status = "写锁" if writers > 0 else "读锁"
                
                logger.info(f"  资源 {res_id}: {status}, 读者={readers}, 写者={writers}")
                
                # 显示持有锁的线程
                for thread in lock.get("threads", []):
                    thread_name = thread["thread_name"]
                    lock_type = thread["lock_type"]
                    held_time = thread.get("held_time", 0)
                    
                    logger.info(f"    线程 {thread_name} 持有 {lock_type} 锁 {held_time:.1f}秒")
    
    def show_final_stats(self) -> None:
        """显示最终统计信息"""
        with self.stats_lock:
            stats = dict(self.stats)
            
        # 创建表格数据
        operation_data = [
            ["读操作成功", stats["read_success"]],
            ["读操作失败", stats["read_failed"]],
            ["写操作成功", stats["write_success"]],
            ["写操作失败", stats["write_failed"]],
            ["锁超时次数", stats["lock_timeouts"]]
        ]
        
        # 计算成功率
        total_read = stats["read_success"] + stats["read_failed"]
        total_write = stats["write_success"] + stats["write_failed"]
        total_ops = total_read + total_write
        
        read_success_rate = (stats["read_success"] / total_read * 100) if total_read > 0 else 0
        write_success_rate = (stats["write_success"] / total_write * 100) if total_write > 0 else 0
        overall_success_rate = ((stats["read_success"] + stats["write_success"]) / total_ops * 100) if total_ops > 0 else 0
        
        rate_data = [
            ["读操作成功率", f"{read_success_rate:.1f}%"],
            ["写操作成功率", f"{write_success_rate:.1f}%"],
            ["总体成功率", f"{overall_success_rate:.1f}%"]
        ]
        
        print("\n操作统计:")
        print(tabulate(operation_data, tablefmt="grid"))
        
        print("\n成功率:")
        print(tabulate(rate_data, tablefmt="grid"))
        
        # 显示资源状态
        print("\n资源状态:")
        resource_data = []
        for res_id, resource in self.shared_resources.items():
            resource_data.append([
                res_id,
                resource["type"],
                resource["value"],
                resource["access_count"]
            ])
        
        print(tabulate(
            resource_data,
            headers=["资源ID", "类型", "当前值", "访问次数"],
            tablefmt="grid"
        ))
    
    def demonstrate_lock_upgrading(self) -> None:
        """演示锁升级和降级"""
        logger.info("=== 锁升级与降级演示 ===")
        
        # 选择一个资源用于演示
        if not self.shared_resources:
            logger.error("没有可用的测试资源，请先创建资源")
            return
            
        res_id = list(self.shared_resources.keys())[0]
        logger.info(f"使用资源 {res_id} 演示锁升级与降级")
        
        # 1. 首先获取读锁
        logger.info("1. 获取读锁")
        if self.lock_manager.acquire_read(res_id):
            resource = self.shared_resources[res_id]
            value = resource["value"]
            logger.info(f"   读取值: {value}")
            
            # 2. 尝试升级到写锁
            logger.info("2. 尝试升级到写锁")
            if self.lock_manager.acquire_write(res_id):
                logger.info("   成功升级到写锁")
                
                # 更新值
                old_value = resource["value"]
                new_value = old_value + 100
                resource["value"] = new_value
                logger.info(f"   更新值: {old_value} -> {new_value}")
                
                # 3. 释放写锁
                logger.info("3. 释放写锁")
                self.lock_manager.release_write(res_id)
                
                # 4. 可以继续使用读锁
                logger.info("4. 在释放写锁后可以继续使用读锁")
                value = resource["value"]
                logger.info(f"   读取值: {value}")
                
                # 5. 释放读锁
                logger.info("5. 释放读锁")
                self.lock_manager.release_read(res_id)
            else:
                logger.error("   升级到写锁失败")
                self.lock_manager.release_read(res_id)
        else:
            logger.error("   获取读锁失败")
    
    def demonstrate_lock_timeout(self) -> None:
        """演示锁超时自动释放"""
        logger.info("=== 锁超时自动释放演示 ===")
        
        # 选择一个资源用于演示
        if not self.shared_resources:
            logger.error("没有可用的测试资源，请先创建资源")
            return
            
        res_id = list(self.shared_resources.keys())[0]
        logger.info(f"使用资源 {res_id} 演示锁超时自动释放")
        
        # 临时缩短超时时间
        original_timeout = self.lock_manager.lock_timeout
        self.lock_manager.lock_timeout = 5  # 设为5秒
        
        logger.info(f"临时设置锁超时时间为 {self.lock_manager.lock_timeout} 秒")
        
        # 创建一个获取写锁但不释放的线程
        def acquire_and_sleep(res_id):
            thread_name = threading.current_thread().name
            logger.info(f"[{thread_name}] 获取写锁 {res_id} 并长时间持有")
            
            if self.lock_manager.acquire_write(res_id):
                logger.info(f"[{thread_name}] 成功获取写锁，将持有60秒(但锁超时时间为5秒)")
                try:
                    # 睡眠60秒，但锁应该在5秒后被自动释放
                    time.sleep(60)
                except:
                    pass
                logger.info(f"[{thread_name}] 线程结束")
        
        # 启动持有锁线程
        holder_thread = threading.Thread(
            target=acquire_and_sleep,
            args=(res_id,),
            name="LockHolder"
        )
        holder_thread.daemon = True  # 设为守护线程
        holder_thread.start()
        
        # 等待2秒，确保锁已被获取
        time.sleep(2)
        
        # 显示当前锁状态
        logger.info("当前锁状态:")
        lock_states = self.lock_manager.get_all_locks()
        for lock in lock_states:
            if lock["resource_id"] == res_id:
                logger.info(f"  资源 {res_id}: 读者={lock['readers']}, 写者={lock['writers']}, 锁定={lock['is_locked']}")
                
                # 显示持有锁的线程
                for thread in lock.get("threads", []):
                    logger.info(f"    线程 {thread['thread_name']} 持有 {thread['lock_type']} 锁 {thread.get('held_time', 0):.1f}秒")
        
        # 等待10秒，让锁超时并被自动释放
        logger.info("等待10秒，让锁超时并被自动释放...")
        time.sleep(10)
        
        # 再次显示锁状态
        logger.info("超时后锁状态:")
        lock_states = self.lock_manager.get_all_locks()
        for lock in lock_states:
            if lock["resource_id"] == res_id:
                logger.info(f"  资源 {res_id}: 读者={lock['readers']}, 写者={lock['writers']}, 锁定={lock['is_locked']}")
        
        # 尝试获取写锁，应该能够成功
        logger.info("尝试在超时后获取写锁")
        if self.lock_manager.acquire_write(res_id):
            logger.info("成功获取写锁，锁已被自动释放")
            self.lock_manager.release_write(res_id)
        else:
            logger.error("获取写锁失败，锁可能未被自动释放")
        
        # 恢复原始超时时间
        self.lock_manager.lock_timeout = original_timeout
        logger.info(f"恢复锁超时时间为 {original_timeout} 秒")
    
    def cleanup(self) -> None:
        """清理资源"""
        logger.info("清理演示资源...")
        
        # 释放所有测试资源
        for res_id in list(self.shared_resources.keys()):
            # 构建完整资源ID
            full_id = None
            for resource_type in ["model_shards", "temp_buffers", "render_cache"]:
                test_id = f"{resource_type}:{res_id}"
                # 检查资源是否存在
                if test_id in self.resource_tracker.resources:
                    full_id = test_id
                    break
            
            # 释放资源
            if full_id:
                self.resource_tracker.release(full_id, force=True)
                logger.info(f"已释放资源: {full_id}")
                
        # 清空字典
        self.shared_resources.clear()
        
        logger.info("所有演示资源已清理")


def main():
    """主函数"""
    print("=== VisionAI-ClipsMaster 资源锁定机制演示 ===")
    print("此演示展示了如何在多线程环境下安全访问共享资源")
    print()
    
    try:
        # 创建演示对象
        demo = ResourceLockDemo()
        
        # 创建测试资源
        demo.create_test_resources(5)
        
        # 演示锁升级和降级
        demo.demonstrate_lock_upgrading()
        
        # 演示锁超时自动释放
        demo.demonstrate_lock_timeout()
        
        # 运行并发访问演示
        print("\n按Ctrl+C可以中断演示")
        demo.run_concurrent_access(30)
        
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # 清理资源
        if 'demo' in locals():
            demo.cleanup()
        
        print("\n演示结束")


if __name__ == "__main__":
    main() 