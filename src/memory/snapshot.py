#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源释放快照

该模块负责在释放资源前创建快照，允许在释放后恢复资源，增强系统安全性。
主要功能：
1. 重要资源释放前的快照创建
2. 快速资源状态恢复
3. 快照生命周期管理
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Set, Tuple
import copy
import weakref
import gc
import json
import traceback

# 配置日志
logger = logging.getLogger("ReleaseSnapshot")

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

class ReleaseSnapshot:
    """资源释放快照管理器，负责创建和恢复资源快照"""
    
    def __init__(self):
        """初始化资源快照管理器"""
        # 快照存储: {resource_id: {'metadata': {...}, 'data': object}}
        self.snapshots = {}
        
        # 快照创建时间: {resource_id: creation_time}
        self.snapshot_times = {}
        
        # 快照配置
        self.config = {
            "max_snapshots": 20,           # 最大快照数量
            "snapshot_ttl": 600,           # 快照保留时间(10分钟)
            "snapshot_priority_threshold": 3,  # 优先级阈值(<=3的资源才创建快照)
            "auto_cleanup_interval": 120    # 自动清理间隔(2分钟)
        }
        
        # 快照互斥锁，防止并发问题
        self.lock = threading.RLock()
        
        # 启动自动清理线程
        self.should_stop = False
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_expired_snapshots,
            daemon=True,
            name="snapshot-cleanup"
        )
        self.cleanup_thread.start()
        
        logger.info("资源快照管理器初始化完成")
    
    def take_snapshot(self, res_id: str, res_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        创建资源快照
        
        Args:
            res_id: 资源ID
            res_metadata: 资源元数据(可选)
            
        Returns:
            bool: 是否成功创建快照
        """
        from src.memory.resource_tracker import get_resource_tracker
        
        with self.lock:
            try:
                tracker = get_resource_tracker()
                
                # 如果未提供元数据，尝试从资源跟踪器获取
                if res_metadata is None:
                    res_info = tracker.get_resource_info(res_id)
                    if res_info:
                        res_metadata = res_info.get("metadata", {})
                
                # 检查资源优先级是否满足快照条件
                if res_metadata:
                    # 资源类型
                    res_type = res_id.split(":", 1)[0] if ":" in res_id else "unknown"
                    
                    # 获取资源类型的配置
                    type_config = tracker.resource_types.get(res_type, {})
                    priority = type_config.get("priority", 999)
                    
                    # 如果优先级低于阈值，不创建快照
                    if priority > self.config["snapshot_priority_threshold"]:
                        logger.debug(f"资源优先级({priority})低于阈值({self.config['snapshot_priority_threshold']})，不创建快照: {res_id}")
                        return False
                
                # 获取资源对象
                resource = self._get_resource_object(res_id)
                if resource is None:
                    logger.warning(f"无法获取资源对象，快照创建失败: {res_id}")
                    return False
                
                # 创建备份
                backup_data = backup_resource(resource)
                if backup_data is None:
                    logger.warning(f"资源备份失败: {res_id}")
                    return False
                
                # 存储快照
                self.snapshots[res_id] = {
                    'metadata': copy.deepcopy(res_metadata) if res_metadata else {},
                    'data': backup_data
                }
                self.snapshot_times[res_id] = time.time()
                
                # 控制快照数量
                self._enforce_snapshot_limit()
                
                logger.info(f"已创建资源快照: {res_id}")
                return True
                
            except Exception as e:
                logger.error(f"创建快照失败 {res_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return False
    
    def rollback(self, res_id: str) -> bool:
        """
        从快照恢复资源
        
        Args:
            res_id: 资源ID
            
        Returns:
            bool: 是否成功恢复
        """
        with self.lock:
            if res_id not in self.snapshots:
                logger.warning(f"找不到资源快照: {res_id}")
                return False
            
            try:
                # 获取快照
                snapshot = self.snapshots[res_id]
                
                # 恢复资源
                success = restore_resource(res_id, snapshot)
                
                if success:
                    logger.info(f"已从快照恢复资源: {res_id}")
                    
                    # 恢复后可以选择性删除快照以节省内存
                    # del self.snapshots[res_id]
                    # if res_id in self.snapshot_times:
                    #     del self.snapshot_times[res_id]
                    
                return success
                
            except Exception as e:
                logger.error(f"从快照恢复失败 {res_id}: {str(e)}")
                return False
    
    def has_snapshot(self, res_id: str) -> bool:
        """
        检查是否存在资源快照
        
        Args:
            res_id: 资源ID
            
        Returns:
            bool: 是否存在快照
        """
        with self.lock:
            return res_id in self.snapshots
    
    def get_snapshot_info(self, res_id: str) -> Optional[Dict[str, Any]]:
        """
        获取快照信息
        
        Args:
            res_id: 资源ID
            
        Returns:
            Optional[Dict]: 快照信息，如果不存在则返回None
        """
        with self.lock:
            if res_id not in self.snapshots:
                return None
                
            snapshot = self.snapshots[res_id]
            snapshot_time = self.snapshot_times.get(res_id, 0)
            
            # 返回快照信息的副本
            return {
                'resource_id': res_id,
                'creation_time': snapshot_time,
                'age': time.time() - snapshot_time,
                'metadata': snapshot.get('metadata', {})
            }
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        获取所有快照信息
        
        Returns:
            List[Dict]: 快照信息列表
        """
        with self.lock:
            result = []
            
            for res_id in self.snapshots:
                info = self.get_snapshot_info(res_id)
                if info:
                    result.append(info)
                    
            # 按创建时间排序
            result.sort(key=lambda x: x.get('creation_time', 0), reverse=True)
            
            return result
    
    def delete_snapshot(self, res_id: str) -> bool:
        """
        删除资源快照
        
        Args:
            res_id: 资源ID
            
        Returns:
            bool: 是否成功删除
        """
        with self.lock:
            if res_id not in self.snapshots:
                return False
                
            # 删除快照
            del self.snapshots[res_id]
            if res_id in self.snapshot_times:
                del self.snapshot_times[res_id]
                
            logger.info(f"已删除资源快照: {res_id}")
            return True
    
    def clear_snapshots(self) -> int:
        """
        清除所有快照
        
        Returns:
            int: 已清除的快照数量
        """
        with self.lock:
            count = len(self.snapshots)
            
            self.snapshots.clear()
            self.snapshot_times.clear()
            
            # 建议进行垃圾回收
            gc.collect()
            
            logger.info(f"已清除所有快照，共 {count} 个")
            return count
    
    def _enforce_snapshot_limit(self) -> None:
        """控制快照数量，超出限制时删除最旧的快照"""
        if len(self.snapshots) <= self.config["max_snapshots"]:
            return
            
        # 获取所有快照，按时间排序
        items = list(self.snapshot_times.items())
        items.sort(key=lambda x: x[1])
        
        # 计算需要删除的数量
        delete_count = len(items) - self.config["max_snapshots"]
        
        # 删除最旧的快照
        for i in range(delete_count):
            res_id = items[i][0]
            if res_id in self.snapshots:
                del self.snapshots[res_id]
                if res_id in self.snapshot_times:
                    del self.snapshot_times[res_id]
                    
        logger.debug(f"已删除 {delete_count} 个旧快照以控制数量")
    
    def _cleanup_expired_snapshots(self) -> None:
        """自动清理过期快照的线程函数"""
        while not self.should_stop:
            try:
                time.sleep(self.config["auto_cleanup_interval"])
                
                with self.lock:
                    current_time = time.time()
                    expired_snapshots = []
                    
                    # 找出所有过期快照
                    for res_id, creation_time in list(self.snapshot_times.items()):
                        if current_time - creation_time > self.config["snapshot_ttl"]:
                            expired_snapshots.append(res_id)
                    
                    # 删除过期快照
                    for res_id in expired_snapshots:
                        if res_id in self.snapshots:
                            del self.snapshots[res_id]
                        if res_id in self.snapshot_times:
                            del self.snapshot_times[res_id]
                    
                    if expired_snapshots:
                        logger.info(f"已自动清理 {len(expired_snapshots)} 个过期快照")
                        
                        # 建议进行垃圾回收
                        gc.collect()
                
            except Exception as e:
                logger.error(f"快照清理线程异常: {str(e)}")
    
    def _get_resource_object(self, res_id: str) -> Any:
        """
        获取资源对象引用
        
        Args:
            res_id: 资源ID
            
        Returns:
            Any: 资源对象或None
        """
        from src.memory.resource_tracker import get_resource_tracker
        
        tracker = get_resource_tracker()
        
        # 尝试直接从资源跟踪器的内部字典获取资源
        try:
            with tracker.lock:  # 确保线程安全
                if hasattr(tracker, 'resources') and res_id in tracker.resources:
                    res_info = tracker.resources[res_id]
                    
                    # 尝试获取弱引用
                    if "ref" in res_info:
                        ref = res_info["ref"]
                        if ref:
                            resource = ref()
                            if resource is not None:
                                return resource
                    
                    # 尝试获取直接引用
                    if "direct_ref" in res_info:
                        resource = res_info["direct_ref"]
                        if resource is not None:
                            return resource
        except Exception as e:
            logger.warning(f"直接访问资源对象失败: {res_id}, 错误: {str(e)}")
        
        # 如果直接访问失败，尝试获取资源信息并通过环境查询对象
        try:
            # 解析资源类型和ID
            if ":" in res_id:
                res_type, specific_id = res_id.split(":", 1)
            else:
                res_type = "unknown"
                specific_id = res_id
                
            # 查找特定类型的系统变量或自定义查找逻辑
            if res_type == "model_shards":
                # 可以添加特定于模型分片的查找逻辑
                pass
            elif res_type == "render_cache":
                # 可以添加特定于渲染缓存的查找逻辑
                pass
            elif res_type == "temp_buffers":
                # 可以添加特定于临时缓冲区的查找逻辑
                pass
        except Exception as e:
            logger.warning(f"通过环境查询资源对象失败: {res_id}, 错误: {str(e)}")
        
        # 所有尝试失败，返回None
        return None
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        更新快照配置
        
        Args:
            new_config: 新配置
        """
        with self.lock:
            # 更新配置
            for key, value in new_config.items():
                if key in self.config:
                    self.config[key] = value
                    
            logger.info(f"已更新快照配置: {new_config}")
    
    def stop(self) -> None:
        """停止清理线程"""
        self.should_stop = True
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
            logger.info("快照清理线程已停止")
    
    def __del__(self):
        """析构函数"""
        self.stop()


def backup_resource(resource: Any) -> Any:
    """
    创建资源对象的备份
    
    Args:
        resource: 资源对象
        
    Returns:
        Any: 资源备份或None
    """
    try:
        # 处理不同类型的资源
        if resource is None:
            return None
            
        # 处理NumPy数组
        if hasattr(resource, 'copy') and callable(resource.copy):
            # 对于支持copy方法的对象(如NumPy数组)
            return resource.copy()
            
        # 处理简单字典和列表
        elif isinstance(resource, dict):
            return copy.deepcopy(resource)
        elif isinstance(resource, list):
            return copy.deepcopy(resource)
            
        # 对于复杂对象，如果实现了自定义的snapshot方法
        elif hasattr(resource, 'snapshot') and callable(resource.snapshot):
            return resource.snapshot()
            
        # 对于一般对象，尝试使用deepcopy
        else:
            try:
                return copy.deepcopy(resource)
            except:
                logger.warning(f"无法创建对象深拷贝: {type(resource)}")
                return None
                
    except Exception as e:
        logger.error(f"备份资源失败: {str(e)}")
        return None


def restore_resource(res_id: str, snapshot: Dict[str, Any]) -> bool:
    """
    从快照恢复资源
    
    Args:
        res_id: 资源ID
        snapshot: 快照数据
        
    Returns:
        bool: 是否成功恢复
    """
    from src.memory.resource_tracker import get_resource_tracker
    
    try:
        # 获取原始备份数据
        backup_data = snapshot.get('data')
        if backup_data is None:
            logger.warning(f"快照数据为空: {res_id}")
            return False
            
        # 获取资源跟踪器
        tracker = get_resource_tracker()
        
        # 检查资源是否仍然存在
        res_info = tracker.resources.get(res_id)
        if not res_info:
            # 资源已被彻底删除，需要重新注册
            resource_type = res_id.split(":", 1)[0] if ":" in res_id else "unknown"
            resource_name = res_id.split(":", 1)[1] if ":" in res_id else res_id
            
            # 注册恢复的资源
            tracker.register(
                resource_type,
                resource_name,
                backup_data,
                snapshot.get('metadata')
            )
            logger.info(f"已重新注册恢复的资源: {res_id}")
            return True
            
        # 资源仍然存在，更新现有资源
        if "ref" in res_info:
            ref = res_info["ref"]
            if ref:
                # 获取当前资源
                current = ref()
                if current is not None:
                    # 尝试使用恢复方法
                    if hasattr(current, 'restore') and callable(current.restore):
                        return current.restore(backup_data)
                        
                    # 否则，只能更新可变对象内部状态
                    if isinstance(current, dict) and isinstance(backup_data, dict):
                        current.clear()
                        current.update(backup_data)
                        return True
                    elif isinstance(current, list) and isinstance(backup_data, list):
                        current.clear()
                        current.extend(backup_data)
                        return True
                    
                    # 其他类型无法直接恢复，返回失败
                    logger.warning(f"无法恢复资源类型: {type(current)}")
                    return False
                    
        elif "direct_ref" in res_info:
            current = res_info["direct_ref"]
            
            # 尝试使用恢复方法
            if hasattr(current, 'restore') and callable(current.restore):
                return current.restore(backup_data)
                
            # 否则，只能更新可变对象内部状态
            if isinstance(current, dict) and isinstance(backup_data, dict):
                current.clear()
                current.update(backup_data)
                return True
            elif isinstance(current, list) and isinstance(backup_data, list):
                current.clear()
                current.extend(backup_data)
                return True
                
            # 其他类型无法直接恢复，返回失败
            logger.warning(f"无法恢复资源类型: {type(current)}")
            return False
        
        # 如果上述方法都无法恢复，返回失败
        logger.warning(f"无法恢复资源: {res_id}")
        return False
        
    except Exception as e:
        logger.error(f"恢复资源失败 {res_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# 单例模式
_release_snapshot = None

def get_release_snapshot() -> ReleaseSnapshot:
    """获取资源快照管理器单例"""
    global _release_snapshot
    if _release_snapshot is None:
        _release_snapshot = ReleaseSnapshot()
    return _release_snapshot


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试资源快照功能
    snapshot_manager = get_release_snapshot()
    
    # 创建测试资源
    test_resource = {"data": [1, 2, 3, 4, 5], "name": "test"}
    
    # 测试创建快照
    from src.memory.resource_tracker import get_resource_tracker
    tracker = get_resource_tracker()
    
    # 注册测试资源
    res_id = tracker.register("model_shards", "test_resource", test_resource, {"priority": 1})
    
    # 创建快照
    snapshot_manager.take_snapshot(res_id)
    
    # 修改资源
    test_resource["data"] = [10, 20, 30]
    
    # 恢复资源
    snapshot_manager.rollback(res_id)
    
    # 检查恢复结果
    print(f"恢复后的资源: {test_resource}")  # 应该是原始数据 

def create_snapshot(include_objects: bool = False, include_system: bool = True) -> Dict[str, Any]:
    """
    创建当前内存使用情况的快照
    
    Args:
        include_objects: 是否包括对象统计信息
        include_system: 是否包括系统内存信息
        
    Returns:
        Dict: 内存快照数据
    """
    snapshot = {
        "timestamp": time.time(),
        "iso_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "process_info": {}
    }
    
    try:
        # 进程信息
        if has_psutil:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            snapshot["process_info"] = {
                "pid": process.pid,
                "name": process.name(),
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024),
                "cpu_percent": process.cpu_percent(),
                "threads": len(process.threads()),
                "create_time": process.create_time()
            }
            
        # 系统内存信息
        if include_system and has_psutil:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            snapshot["system_info"] = {
                "total_mb": vm.total / (1024 * 1024),
                "available_mb": vm.available / (1024 * 1024),
                "used_mb": vm.used / (1024 * 1024),
                "free_mb": vm.free / (1024 * 1024),
                "percent": vm.percent,
                "swap_total_mb": swap.total / (1024 * 1024),
                "swap_used_mb": swap.used / (1024 * 1024),
                "swap_percent": swap.percent,
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=0.1)
            }
            
        # 对象统计
        if include_objects:
            # 触发垃圾回收，确保统计准确
            gc.collect()
            
            # 获取所有对象
            objects = gc.get_objects()
            
            # 对象类型统计
            type_counts = {}
            for obj in objects:
                obj_type = type(obj).__name__
                if obj_type not in type_counts:
                    type_counts[obj_type] = 0
                type_counts[obj_type] += 1
                
            # 按数量排序
            sorted_types = sorted(
                type_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # 取前50种类型
            top_types = sorted_types[:50]
            
            snapshot["object_stats"] = {
                "total_objects": len(objects),
                "gc_counts": gc.get_count(),
                "top_types": dict(top_types)
            }
            
        # Python内存分配器信息
        try:
            import tracemalloc
            if not tracemalloc.is_tracing():
                tracemalloc.start()
                snapshot["tracemalloc"] = {"just_started": True}
            else:
                current, peak = tracemalloc.get_traced_memory()
                snapshot["tracemalloc"] = {
                    "current_mb": current / (1024 * 1024),
                    "peak_mb": peak / (1024 * 1024),
                    "just_started": False
                }
        except ImportError:
            snapshot["tracemalloc"] = {"available": False}
            
    except Exception as e:
        logger.error(f"创建内存快照失败: {str(e)}")
        snapshot["error"] = {
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        
    return snapshot

def save_snapshot(snapshot: Dict[str, Any], file_path: Optional[str] = None) -> str:
    """
    保存内存快照到文件
    
    Args:
        snapshot: 内存快照数据
        file_path: 保存文件路径，为None时自动生成
        
    Returns:
        str: 保存的文件路径
    """
    if file_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_path = f"memory_snapshot_{timestamp}.json"
        
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        # 写入JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2)
            
        logger.info(f"内存快照已保存到: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"保存内存快照失败: {str(e)}")
        return ""

def load_snapshot(file_path: str) -> Dict[str, Any]:
    """
    从文件加载内存快照
    
    Args:
        file_path: 快照文件路径
        
    Returns:
        Dict: 内存快照数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        logger.info(f"已加载内存快照: {file_path}")
        return snapshot
    except Exception as e:
        logger.error(f"加载内存快照失败: {str(e)}")
        return {"error": str(e)}

def compare_snapshots(snapshot1: Dict[str, Any], snapshot2: Dict[str, Any]) -> Dict[str, Any]:
    """
    比较两个内存快照
    
    Args:
        snapshot1: 第一个快照(较早)
        snapshot2: 第二个快照(较晚)
        
    Returns:
        Dict: 比较结果
    """
    if "error" in snapshot1 or "error" in snapshot2:
        return {"error": "快照包含错误，无法比较"}
        
    # 计算时间差
    time_diff = snapshot2["timestamp"] - snapshot1["timestamp"]
    
    result = {
        "start_time": snapshot1["iso_time"],
        "end_time": snapshot2["iso_time"],
        "duration_seconds": time_diff,
        "changes": {}
    }
    
    # 比较进程内存
    if "process_info" in snapshot1 and "process_info" in snapshot2:
        proc1 = snapshot1["process_info"]
        proc2 = snapshot2["process_info"]
        
        if "rss_mb" in proc1 and "rss_mb" in proc2:
            rss_diff = proc2["rss_mb"] - proc1["rss_mb"]
            rss_percent = (rss_diff / proc1["rss_mb"]) * 100 if proc1["rss_mb"] > 0 else 0
            
            result["changes"]["rss_mb"] = {
                "start": proc1["rss_mb"],
                "end": proc2["rss_mb"],
                "diff": rss_diff,
                "percent": rss_percent,
                "rate_mb_per_min": (rss_diff / time_diff) * 60 if time_diff > 0 else 0
            }
    
    # 比较对象统计
    if "object_stats" in snapshot1 and "object_stats" in snapshot2:
        obj1 = snapshot1["object_stats"]
        obj2 = snapshot2["object_stats"]
        
        if "total_objects" in obj1 and "total_objects" in obj2:
            obj_diff = obj2["total_objects"] - obj1["total_objects"]
            obj_percent = (obj_diff / obj1["total_objects"]) * 100 if obj1["total_objects"] > 0 else 0
            
            result["changes"]["total_objects"] = {
                "start": obj1["total_objects"],
                "end": obj2["total_objects"],
                "diff": obj_diff,
                "percent": obj_percent
            }
            
        # 比较前10种类型的变化
        if "top_types" in obj1 and "top_types" in obj2:
            type_changes = {}
            all_types = set(list(obj1["top_types"].keys()) + list(obj2["top_types"].keys()))
            
            for type_name in all_types:
                count1 = obj1["top_types"].get(type_name, 0)
                count2 = obj2["top_types"].get(type_name, 0)
                diff = count2 - count1
                
                if abs(diff) > 0:
                    type_changes[type_name] = {
                        "start": count1,
                        "end": count2,
                        "diff": diff,
                        "percent": (diff / count1) * 100 if count1 > 0 else 100
                    }
            
            # 按变化量排序
            sorted_changes = sorted(
                type_changes.items(),
                key=lambda x: abs(x[1]["diff"]),
                reverse=True
            )
            
            result["changes"]["object_types"] = dict(sorted_changes[:20])
    
    # 添加评估结果
    if "changes" in result and "rss_mb" in result["changes"]:
        rss_rate = result["changes"]["rss_mb"]["rate_mb_per_min"]
        
        if rss_rate > 1.0:
            result["assessment"] = "可能存在内存泄漏"
            result["severity"] = "高" if rss_rate > 5.0 else "中"
        elif rss_rate > 0.1:
            result["assessment"] = "轻微内存增长"
            result["severity"] = "低"
        elif rss_rate < -1.0:
            result["assessment"] = "内存明显减少，可能是垃圾回收或内存优化的结果"
            result["severity"] = "无"
        else:
            result["assessment"] = "内存使用稳定"
            result["severity"] = "无"
    
    return result 

def restore_snapshot(snapshot_file: str) -> bool:
    """
    从快照恢复内存状态（尽可能）
    
    Args:
        snapshot_file: 快照文件路径
        
    Returns:
        bool: 是否成功恢复
    """
    try:
        # 加载快照
        snapshot = load_snapshot(snapshot_file)
        if "error" in snapshot:
            logger.error(f"无法恢复快照，加载失败: {snapshot['error']}")
            return False
            
        logger.info(f"正在尝试从快照恢复 ({snapshot['iso_time']})")
        
        # 强制执行垃圾回收
        gc.collect(0)
        gc.collect(1)
        gc.collect(2)
        
        # 记录恢复前状态
        before = create_snapshot()
        
        # 尝试恢复
        # 注意：完全恢复实际上是不可能的，我们只能尽量接近
        
        # 如果使用了tracemalloc，重置它
        try:
            import tracemalloc

            if tracemalloc.is_tracing():
                tracemalloc.stop()
                tracemalloc.start()
                logger.info("已重置tracemalloc")
        except ImportError:
            pass
            
        # 再次强制垃圾回收
        gc.collect()
        
        # 创建恢复后的快照
        after = create_snapshot()
        
        # 比较恢复效果
        comparison = compare_snapshots(before, after)
        
        if "changes" in comparison and "rss_mb" in comparison["changes"]:
            change = comparison["changes"]["rss_mb"]["diff"]
            direction = "减少" if change < 0 else "增加"
            logger.info(f"内存使用{direction}了 {abs(change):.2f}MB")
            
        return True
    except Exception as e:
        logger.error(f"恢复快照失败: {str(e)}")
        return False 

def delete_snapshot(snapshot_file: str) -> bool:
    """
    删除内存快照文件
    
    Args:
        snapshot_file: 快照文件路径
        
    Returns:
        bool: 是否成功删除
    """
    try:
        if not os.path.isfile(snapshot_file):
            logger.warning(f"无法删除快照，文件不存在: {snapshot_file}")
            return False
            
        os.remove(snapshot_file)
        logger.info(f"已删除快照文件: {snapshot_file}")
        return True
    except Exception as e:
        logger.error(f"删除快照文件失败: {str(e)}")
        return False 