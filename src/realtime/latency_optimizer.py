#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
交互延迟优化器

通过地理分布式缓存、智能路由和连接管理优化实时交互延迟，
提高短剧混剪过程中的用户体验和响应速度。
"""

import os
import math
import time
import json
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import ipaddress
import socket
import heapq
from functools import lru_cache

# 配置日志记录器
logger = logging.getLogger(__name__)

class GeoDistributedCache:
    """地理分布式缓存
    
    管理分布在不同地理位置的边缘节点缓存，
    优化数据访问延迟和网络传输效率。
    """
    
    def __init__(self, cache_config: Optional[Dict[str, Any]] = None):
        """初始化地理分布式缓存
        
        Args:
            cache_config: 缓存配置，包含边缘节点信息等
        """
        self.nodes: List[Dict[str, Any]] = []
        self.node_lock = threading.RLock()
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl: Dict[str, float] = {}
        self.default_ttl = 3600  # 默认缓存时间（秒）
        self.config = cache_config or self._load_default_config()
        self.initialize_nodes()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认缓存配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        default_config = {
            "max_cache_size_mb": 100,
            "default_ttl": 3600,
            "edge_nodes": [
                {"id": "cn-east", "location": {"lat": 31.2304, "lng": 121.4737}, "region": "华东"},
                {"id": "cn-north", "location": {"lat": 39.9042, "lng": 116.4074}, "region": "华北"},
                {"id": "cn-south", "location": {"lat": 22.5431, "lng": 114.0579}, "region": "华南"},
                {"id": "cn-southwest", "location": {"lat": 30.5728, "lng": 104.0668}, "region": "西南"},
                {"id": "cn-northwest", "location": {"lat": 34.3416, "lng": 108.9398}, "region": "西北"}
            ],
            "connect_timeout": 2.0,
            "retry_count": 3,
            "path_mapping": {
                "models": "/models",
                "data": "/data/cache",
                "temp": "/tmp/cache"
            }
        }
        
        # 尝试从配置文件加载
        config_path = os.path.join("configs", "edge_cache.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    # 合并配置
                    for key, value in user_config.items():
                        default_config[key] = value
                logger.info(f"已加载边缘节点缓存配置: {config_path}")
            except Exception as e:
                logger.warning(f"加载边缘节点缓存配置失败: {str(e)}")
        
        return default_config
    
    def initialize_nodes(self) -> None:
        """初始化边缘节点
        
        基于配置加载边缘节点信息，并进行初始健康检查。
        """
        with self.node_lock:
            self.nodes = []
            edge_nodes = self.config.get("edge_nodes", [])
            
            # 添加本地节点
            local_node = {
                "id": "local",
                "location": {"lat": 0, "lng": 0},  # 默认位置
                "region": "本地",
                "status": "active",
                "latency": 0,
                "last_check": time.time(),
                "health": 100
            }
            
            # 尝试获取本地地理位置（如果可用）
            try:
                local_ip = self._get_local_ip()
                geo_info = self._get_geo_from_ip(local_ip)
                if geo_info and "lat" in geo_info and "lng" in geo_info:
                    local_node["location"] = geo_info
                    local_node["region"] = geo_info.get("region", "本地")
            except Exception as e:
                logger.debug(f"获取本地地理位置失败: {str(e)}")
            
            self.nodes.append(local_node)
            
            # 添加配置的远程节点
            for node in edge_nodes:
                node_info = {
                    "id": node.get("id", f"node-{len(self.nodes)}"),
                    "location": node.get("location", {"lat": 0, "lng": 0}),
                    "region": node.get("region", "未知区域"),
                    "endpoint": node.get("endpoint", ""),
                    "status": "unknown",
                    "latency": -1,
                    "last_check": 0,
                    "health": 0
                }
                self.nodes.append(node_info)
            
            logger.info(f"已初始化 {len(self.nodes)} 个边缘节点")
    
    def _get_local_ip(self) -> str:
        """获取本地IP地址
        
        Returns:
            str: 本地IP地址
        """
        try:
            # 创建一个连接到公共DNS的套接字
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def _get_geo_from_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """根据IP获取地理位置信息
        
        Args:
            ip: IP地址
            
        Returns:
            Optional[Dict[str, Any]]: 地理位置信息
        """
        # 这里可以集成真实的IP地理位置服务
        # 现在返回默认中国大陆位置
        return {
            "lat": 34.7725, 
            "lng": 113.7266,
            "region": "中国大陆"
        }
    
    @staticmethod
    def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """计算两点间的球面距离（km）
        
        使用Haversine公式计算两个地理坐标点之间的距离。
        
        Args:
            lat1: 第一点纬度
            lng1: 第一点经度
            lat2: 第二点纬度
            lng2: 第二点经度
            
        Returns:
            float: 距离（千米）
        """
        # 将经纬度转换为弧度
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # 地球半径（千米）
        return c * r
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """获取所有边缘节点信息
        
        Returns:
            List[Dict[str, Any]]: 边缘节点列表
        """
        with self.node_lock:
            return self.nodes.copy()
    
    async def get_nearest_node(self, location: Dict[str, float]) -> Dict[str, Any]:
        """获取最近的边缘节点
        
        基于地理位置和当前节点健康状态，选择最佳节点。
        
        Args:
            location: 用户位置（包含lat和lng键）
            
        Returns:
            Dict[str, Any]: 最佳边缘节点信息
        """
        if not location or "lat" not in location or "lng" not in location:
            # 如果没有位置信息，返回本地节点
            return self.nodes[0]
        
        with self.node_lock:
            # 计算每个节点到用户的距离并考虑节点健康状态
            node_scores = []
            user_lat = location["lat"]
            user_lng = location["lng"]
            
            for node in self.nodes:
                # 如果节点不健康，跳过
                if node.get("status") == "down":
                    continue
                
                node_lat = node["location"]["lat"]
                node_lng = node["location"]["lng"]
                
                # 计算距离分数（越近越好）
                distance = self.haversine(user_lat, user_lng, node_lat, node_lng)
                distance_score = 1000 / (distance + 10)  # 避免除以零并归一化
                
                # 计算健康分数
                health_score = node.get("health", 0) / 100
                
                # 计算延迟分数
                latency = node.get("latency", 100)
                latency_score = 1 / (latency + 1)  # 避免除以零
                
                # 综合评分（可以调整各因素的权重）
                total_score = distance_score * 0.5 + health_score * 0.3 + latency_score * 0.2
                
                node_scores.append((-total_score, node))  # 负分数用于堆排序
            
            # 使用堆排序获取最佳节点
            if node_scores:
                heapq.heapify(node_scores)
                return node_scores[0][1]
            else:
                # 如果没有可用节点，返回本地节点
                return self.nodes[0]
    
    async def check_node_health(self, node_id: str) -> Dict[str, Any]:
        """检查边缘节点健康状态
        
        Args:
            node_id: 节点ID
            
        Returns:
            Dict[str, Any]: 更新后的节点信息
        """
        with self.node_lock:
            node = next((n for n in self.nodes if n["id"] == node_id), None)
            if not node:
                return {"id": node_id, "status": "unknown", "error": "节点不存在"}
            
            # 更新节点检查时间
            node["last_check"] = time.time()
            
            # 如果是本地节点，直接返回健康状态
            if node["id"] == "local":
                node["status"] = "active"
                node["health"] = 100
                node["latency"] = 0
                return node
            
            # 检查远程节点健康状态
            try:
                # 测量延迟
                start_time = time.time()
                # 这里可以添加真实的健康检查逻辑
                await asyncio.sleep(0.01)  # 模拟网络延迟
                latency = (time.time() - start_time) * 1000  # 转换为毫秒
                
                # 更新节点状态
                node["status"] = "active"
                node["latency"] = latency
                node["health"] = min(100, max(0, 100 - latency / 10))  # 简单的健康度计算
            except Exception as e:
                logger.warning(f"节点健康检查失败 ({node_id}): {str(e)}")
                node["status"] = "down"
                node["health"] = 0
                node["latency"] = -1
            
            return node
    
    async def check_all_nodes(self) -> List[Dict[str, Any]]:
        """检查所有边缘节点的健康状态
        
        Returns:
            List[Dict[str, Any]]: 更新后的节点列表
        """
        tasks = []
        with self.node_lock:
            for node in self.nodes:
                tasks.append(self.check_node_health(node["id"]))
        
        results = await asyncio.gather(*tasks)
        return results
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """添加或更新缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存生存时间（秒）
            
        Returns:
            bool: 是否成功添加或更新
        """
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            self.cache[key] = {"value": value, "timestamp": time.time()}
            self.cache_ttl[key] = time.time() + ttl
            return True
        except Exception as e:
            logger.error(f"添加缓存失败: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值或None（如果不存在或已过期）
        """
        try:
            if key not in self.cache:
                return None
            
            # 检查是否过期
            if key in self.cache_ttl and time.time() > self.cache_ttl[key]:
                del self.cache[key]
                del self.cache_ttl[key]
                return None
            
            return self.cache[key]["value"]
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None
    
    def clear_expired(self) -> int:
        """清理过期缓存
        
        Returns:
            int: 清理的缓存项数量
        """
        try:
            now = time.time()
            expired_keys = [k for k, v in self.cache_ttl.items() if now > v]
            
            for key in expired_keys:
                if key in self.cache:
                    del self.cache[key]
                del self.cache_ttl[key]
            
            return len(expired_keys)
        except Exception as e:
            logger.error(f"清理过期缓存失败: {str(e)}")
            return 0


class LagReducer:
    """延迟优化器
    
    通过智能路由和连接管理优化实时交互延迟，
    提高短剧混剪过程中的响应速度和用户体验。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化延迟优化器
        
        Args:
            config: 优化器配置
        """
        self.edge_nodes = GeoDistributedCache(config)
        self.connection_pool: Dict[str, Dict[str, Any]] = {}
        self.stats: Dict[str, Any] = {
            "requests": 0,
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "avg_latency": 0,
            "start_time": time.time()
        }
        self.maintenance_task = None
        self.running = False
    
    async def start(self):
        """启动延迟优化器"""
        if self.running:
            return
        
        self.running = True
        # 初始检查所有节点
        await self.edge_nodes.check_all_nodes()
        # 启动维护任务
        self.maintenance_task = asyncio.create_task(self._maintenance_routine())
        logger.info("延迟优化器已启动")
    
    async def stop(self):
        """停止延迟优化器"""
        self.running = False
        if self.maintenance_task:
            self.maintenance_task.cancel()
            try:
                await self.maintenance_task
            except asyncio.CancelledError:
                pass
            self.maintenance_task = None
        logger.info("延迟优化器已停止")
    
    async def _maintenance_routine(self):
        """维护例程"""
        try:
            while self.running:
                # 每60秒执行一次节点健康检查
                await asyncio.sleep(60)
                if not self.running:
                    break
                
                # 检查节点健康
                await self.edge_nodes.check_all_nodes()
                
                # 清理过期缓存
                cleared = self.edge_nodes.clear_expired()
                if cleared > 0:
                    logger.debug(f"已清理 {cleared} 个过期缓存项")
        except asyncio.CancelledError:
            logger.info("维护例程已取消")
        except Exception as e:
            logger.error(f"维护例程出错: {str(e)}")
    
    async def get_nearest_edge(self, user_location: Dict[str, float]) -> Dict[str, Any]:
        """基于地理位置的边缘计算节点选择
        
        Args:
            user_location: 用户位置（包含lat和lng键）
            
        Returns:
            Dict[str, Any]: 最佳边缘节点信息
        """
        return await self.edge_nodes.get_nearest_node(user_location)
    
    async def optimize_connection(self, session_id: str, user_location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """优化用户连接
        
        根据用户位置和网络状况优化连接参数，提供最佳交互体验。
        
        Args:
            session_id: 会话ID
            user_location: 用户位置（可选）
            
        Returns:
            Dict[str, Any]: 优化参数
        """
        # 记录请求
        self.stats["requests"] += 1
        
        try:
            # 如果没有提供位置，尝试从之前的连接获取
            if not user_location and session_id in self.connection_pool:
                user_location = self.connection_pool[session_id].get("location")
            
            # 使用默认位置
            if not user_location:
                user_location = {"lat": 35.0, "lng": 105.0}  # 中国中部默认位置
            
            # 获取最近的边缘节点
            start_time = time.time()
            nearest_edge = await self.get_nearest_edge(user_location)
            lookup_time = (time.time() - start_time) * 1000  # 毫秒
            
            # 计算优化参数
            optimization = {
                "session_id": session_id,
                "edge_node": nearest_edge["id"],
                "region": nearest_edge["region"],
                "protocol": "websocket",  # 默认协议
                "buffer_size": 1024,      # 默认缓冲区大小
                "compression": "auto",    # 自动压缩
                "latency": nearest_edge.get("latency", 0),
                "lookup_time": lookup_time,
                "timestamp": time.time()
            }
            
            # 保存连接信息
            self.connection_pool[session_id] = {
                "location": user_location,
                "edge_node": nearest_edge["id"],
                "last_access": time.time(),
                "optimization": optimization
            }
            
            # 更新统计信息
            self.stats["hits"] += 1
            self.stats["avg_latency"] = ((self.stats["avg_latency"] * (self.stats["requests"] - 1)) + 
                                         lookup_time) / self.stats["requests"]
            
            return optimization
        except Exception as e:
            logger.error(f"优化连接失败: {str(e)}")
            self.stats["errors"] += 1
            
            # 返回默认优化参数
            return {
                "session_id": session_id,
                "edge_node": "local",
                "region": "默认",
                "protocol": "websocket",
                "buffer_size": 1024,
                "compression": "none",
                "latency": 0,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取延迟优化器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        uptime = time.time() - self.stats["start_time"]
        hit_rate = (self.stats["hits"] / max(1, self.stats["requests"])) * 100
        
        return {
            "uptime": uptime,
            "requests": self.stats["requests"],
            "hits": self.stats["hits"],
            "hit_rate": hit_rate,
            "avg_latency": self.stats["avg_latency"],
            "errors": self.stats["errors"],
            "active_connections": len(self.connection_pool),
            "edge_nodes": len(self.edge_nodes.get_nodes())
        }


# 单例模式
_lag_reducer_instance = None
_instance_lock = threading.Lock()

def get_lag_reducer() -> LagReducer:
    """获取延迟优化器单例实例
    
    Returns:
        LagReducer: 延迟优化器实例
    """
    global _lag_reducer_instance
    
    if _lag_reducer_instance is None:
        with _instance_lock:
            if _lag_reducer_instance is None:
                _lag_reducer_instance = LagReducer()
    
    return _lag_reducer_instance

async def initialize_lag_reducer(config: Optional[Dict[str, Any]] = None) -> LagReducer:
    """初始化延迟优化器
    
    Args:
        config: 优化器配置
        
    Returns:
        LagReducer: 延迟优化器实例
    """
    global _lag_reducer_instance
    
    with _instance_lock:
        _lag_reducer_instance = LagReducer(config)
        await _lag_reducer_instance.start()
    
    return _lag_reducer_instance 