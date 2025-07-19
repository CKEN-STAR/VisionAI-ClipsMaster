#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存资源锁管理器
提供资源锁定和释放功能，防止资源争用问题
"""

import threading
import logging
import time
from typing import Dict, Set, Any, Optional

logger = logging.getLogger(__name__)

class ResourceLockManager:
    """资源锁管理器，提供资源锁定和释放功能"""
    
    def __init__(self):
        """初始化资源锁管理器"""
        self._locks = {}  # 资源名称 -> 锁对象
        self._ownership = {}  # 资源名称 -> 拥有者ID集合
        self._lock = threading.RLock()  # 用于同步对锁映射的访问
        
    def acquire_lock(self, resource_name: str, owner_id: str, 
                    timeout: float = None, blocking: bool = True) -> bool:
        """
        获取资源锁
        
        Args:
            resource_name: 资源名称
            owner_id: 拥有者ID
            timeout: 获取锁的超时时间，None表示无限等待
            blocking: 是否阻塞等待锁
            
        Returns:
            bool: 是否成功获取锁
        """
        with self._lock:
            # 如果锁不存在，创建一个新锁
            if resource_name not in self._locks:
                self._locks[resource_name] = threading.RLock()
                self._ownership[resource_name] = set()
                
        # 尝试获取锁
        lock = self._locks[resource_name]
        acquired = lock.acquire(blocking=blocking, timeout=timeout if timeout else -1)
        
        if acquired:
            # 记录拥有者
            with self._lock:
                self._ownership[resource_name].add(owner_id)
            logger.debug(f"资源 '{resource_name}' 被 '{owner_id}' 锁定")
        else:
            logger.warning(f"资源 '{resource_name}' 锁定失败，拥有者: '{owner_id}'")
            
        return acquired
        
    def release_lock(self, resource_name: str, owner_id: str) -> bool:
        """
        释放资源锁
        
        Args:
            resource_name: 资源名称
            owner_id: 拥有者ID
            
        Returns:
            bool: 是否成功释放锁
        """
        with self._lock:
            if resource_name not in self._locks:
                logger.warning(f"尝试释放不存在的锁: '{resource_name}'")
                return False
                
            if owner_id not in self._ownership.get(resource_name, set()):
                logger.warning(f"'{owner_id}' 尝试释放未拥有的锁: '{resource_name}'")
                return False
                
            # 释放锁
            try:
                self._locks[resource_name].release()
                self._ownership[resource_name].remove(owner_id)
                logger.debug(f"资源 '{resource_name}' 被 '{owner_id}' 释放")
                return True
            except RuntimeError as e:
                logger.error(f"释放锁 '{resource_name}' 失败: {str(e)}")
                return False
                
    def get_lock_owners(self, resource_name: str) -> Set[str]:
        """
        获取资源锁的当前拥有者
        
        Args:
            resource_name: 资源名称
            
        Returns:
            Set[str]: 拥有者ID集合
        """
        with self._lock:
            return self._ownership.get(resource_name, set()).copy()
            
    def force_release_all(self, owner_id: str) -> int:
        """
        强制释放指定拥有者的所有锁
        
        Args:
            owner_id: 拥有者ID
            
        Returns:
            int: 释放的锁数量
        """
        count = 0
        with self._lock:
            # 查找拥有者拥有的所有锁
            resources_to_release = []
            for resource_name, owners in self._ownership.items():
                if owner_id in owners:
                    resources_to_release.append(resource_name)
                    
            # 释放锁
            for resource_name in resources_to_release:
                try:
                    self._locks[resource_name].release()
                    self._ownership[resource_name].remove(owner_id)
                    count += 1
                    logger.debug(f"强制释放: 资源 '{resource_name}' 被 '{owner_id}' 释放")
                except RuntimeError as e:
                    logger.error(f"强制释放锁 '{resource_name}' 失败: {str(e)}")
                    
        return count

# 全局锁管理器实例
_lock_manager = None

def get_lock_manager() -> ResourceLockManager:
    """
    获取全局锁管理器实例
    
    Returns:
        ResourceLockManager: 锁管理器实例
    """
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = ResourceLockManager()
    return _lock_manager 

# 便捷函数
def acquire_lock(resource_name: str, owner_id: str, timeout: float = None, blocking: bool = True) -> bool:
    """
    获取资源锁
    
    Args:
        resource_name: 资源名称
        owner_id: 拥有者ID
        timeout: 超时时间(秒)
        blocking: 是否阻塞等待
        
    Returns:
        bool: 是否成功获取锁
    """
    return get_lock_manager().acquire_lock(
        resource_name=resource_name,
        owner_id=owner_id,
        timeout=timeout,
        blocking=blocking
    )

def release_lock(resource_name: str, owner_id: str) -> bool:
    """
    释放资源锁
    
    Args:
        resource_name: 资源名称
        owner_id: 拥有者ID
        
    Returns:
        bool: 是否成功释放锁
    """
    return get_lock_manager().release_lock(
        resource_name=resource_name,
        owner_id=owner_id
    ) 