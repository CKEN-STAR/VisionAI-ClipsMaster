#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络连通性检测器 - VisionAI-ClipsMaster
提供网络诊断、连通性预检等功能
"""

import asyncio
import aiohttp
import socket
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import platform
import subprocess
import json

logger = logging.getLogger(__name__)

class NetworkStatus(Enum):
    """网络状态"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    OFFLINE = "offline"

@dataclass
class ConnectivityResult:
    """连通性检测结果"""
    url: str
    accessible: bool
    response_time: float
    status_code: Optional[int] = None
    error: Optional[str] = None
    timestamp: float = 0

@dataclass
class NetworkDiagnostics:
    """网络诊断结果"""
    overall_status: NetworkStatus
    internet_accessible: bool
    dns_working: bool
    avg_response_time: float
    accessible_sources: int
    total_sources: int
    recommendations: List[str]
    detailed_results: Dict[str, ConnectivityResult]

class NetworkConnectivityChecker:
    """网络连通性检测器"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = 30
        self.test_urls = {
            "google_dns": "8.8.8.8",
            "cloudflare_dns": "1.1.1.1",
            "baidu": "https://www.baidu.com",
            "google": "https://www.google.com",
            "github": "https://github.com",
            "modelscope": "https://modelscope.cn",
            "huggingface": "https://huggingface.co"
        }
    
    async def check_internet_connectivity(self) -> bool:
        """检查基本互联网连通性"""
        try:
            # 尝试连接多个知名DNS服务器
            dns_servers = ["8.8.8.8", "1.1.1.1", "114.114.114.114"]
            
            for dns in dns_servers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((dns, 53))
                    sock.close()
                    
                    if result == 0:
                        logger.info(f"成功连接到DNS服务器 {dns}")
                        return True
                except Exception as e:
                    logger.debug(f"连接DNS服务器 {dns} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"检查互联网连通性失败: {e}")
            return False
    
    async def check_dns_resolution(self) -> bool:
        """检查DNS解析功能"""
        try:
            test_domains = ["www.baidu.com", "www.google.com", "github.com"]
            
            for domain in test_domains:
                try:
                    socket.gethostbyname(domain)
                    logger.info(f"DNS解析 {domain} 成功")
                    return True
                except socket.gaierror:
                    logger.debug(f"DNS解析 {domain} 失败")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"检查DNS解析失败: {e}")
            return False
    
    async def check_url_connectivity(self, url: str, timeout: int = None) -> ConnectivityResult:
        """检查单个URL的连通性"""
        if timeout is None:
            timeout = self.timeout
        
        result = ConnectivityResult(
            url=url,
            accessible=False,
            response_time=0,
            timestamp=time.time()
        )
        
        try:
            if not self.session:
                client_timeout = aiohttp.ClientTimeout(total=timeout)
                self.session = aiohttp.ClientSession(timeout=client_timeout)
            
            start_time = time.time()
            
            async with self.session.head(url, allow_redirects=True) as response:
                end_time = time.time()
                
                result.response_time = (end_time - start_time) * 1000  # 毫秒
                result.status_code = response.status
                result.accessible = response.status < 400
                
                if result.accessible:
                    logger.info(f"URL {url} 可访问 (HTTP {response.status}, {result.response_time:.1f}ms)")
                else:
                    logger.warning(f"URL {url} 不可访问 (HTTP {response.status})")
                
        except asyncio.TimeoutError:
            result.error = "连接超时"
            result.response_time = timeout * 1000
            logger.warning(f"URL {url} 连接超时")
            
        except aiohttp.ClientError as e:
            result.error = f"客户端错误: {str(e)}"
            logger.warning(f"URL {url} 客户端错误: {e}")
            
        except Exception as e:
            result.error = f"未知错误: {str(e)}"
            logger.error(f"URL {url} 检查失败: {e}")
        
        return result
    
    async def check_multiple_urls(self, urls: List[str]) -> Dict[str, ConnectivityResult]:
        """并发检查多个URL的连通性"""
        logger.info(f"开始检查 {len(urls)} 个URL的连通性...")
        
        tasks = []
        for url in urls:
            task = asyncio.create_task(self.check_url_connectivity(url))
            tasks.append((url, task))
        
        results = {}
        for url, task in tasks:
            try:
                result = await task
                results[url] = result
            except Exception as e:
                logger.error(f"检查URL {url} 时发生错误: {e}")
                results[url] = ConnectivityResult(
                    url=url,
                    accessible=False,
                    response_time=0,
                    error=str(e),
                    timestamp=time.time()
                )
        
        return results
    
    def ping_host(self, host: str, count: int = 3) -> Tuple[bool, float]:
        """Ping主机检查连通性"""
        try:
            system = platform.system().lower()
            
            if system == "windows":
                cmd = ["ping", "-n", str(count), host]
            else:
                cmd = ["ping", "-c", str(count), host]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            end_time = time.time()
            
            if result.returncode == 0:
                response_time = (end_time - start_time) * 1000 / count
                logger.info(f"Ping {host} 成功 (平均 {response_time:.1f}ms)")
                return True, response_time
            else:
                logger.warning(f"Ping {host} 失败")
                return False, 0
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Ping {host} 超时")
            return False, 0
        except Exception as e:
            logger.error(f"Ping {host} 错误: {e}")
            return False, 0
    
    async def comprehensive_network_diagnosis(self) -> NetworkDiagnostics:
        """综合网络诊断"""
        logger.info("开始综合网络诊断...")
        
        # 1. 检查基本互联网连通性
        internet_accessible = await self.check_internet_connectivity()
        
        # 2. 检查DNS解析
        dns_working = await self.check_dns_resolution()
        
        # 3. 检查关键URL连通性
        url_results = await self.check_multiple_urls(list(self.test_urls.values()))
        
        # 4. 分析结果
        accessible_count = sum(1 for result in url_results.values() if result.accessible)
        total_count = len(url_results)
        
        response_times = [result.response_time for result in url_results.values() if result.accessible]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 5. 确定整体网络状态
        overall_status = self._determine_network_status(
            internet_accessible, dns_working, accessible_count, total_count, avg_response_time
        )
        
        # 6. 生成建议
        recommendations = self._generate_recommendations(
            internet_accessible, dns_working, accessible_count, total_count, avg_response_time
        )
        
        return NetworkDiagnostics(
            overall_status=overall_status,
            internet_accessible=internet_accessible,
            dns_working=dns_working,
            avg_response_time=avg_response_time,
            accessible_sources=accessible_count,
            total_sources=total_count,
            recommendations=recommendations,
            detailed_results=url_results
        )
    
    def _determine_network_status(
        self, 
        internet_accessible: bool, 
        dns_working: bool, 
        accessible_count: int, 
        total_count: int, 
        avg_response_time: float
    ) -> NetworkStatus:
        """确定网络状态等级"""
        if not internet_accessible:
            return NetworkStatus.OFFLINE
        
        accessibility_ratio = accessible_count / total_count if total_count > 0 else 0
        
        if accessibility_ratio >= 0.8 and avg_response_time < 1000:
            return NetworkStatus.EXCELLENT
        elif accessibility_ratio >= 0.6 and avg_response_time < 2000:
            return NetworkStatus.GOOD
        elif accessibility_ratio >= 0.4 or dns_working:
            return NetworkStatus.FAIR
        else:
            return NetworkStatus.POOR
    
    def _generate_recommendations(
        self, 
        internet_accessible: bool, 
        dns_working: bool, 
        accessible_count: int, 
        total_count: int, 
        avg_response_time: float
    ) -> List[str]:
        """生成网络优化建议"""
        recommendations = []
        
        if not internet_accessible:
            recommendations.append("无法连接到互联网，请检查网络连接")
            recommendations.append("确认网络电缆连接或WiFi状态")
            return recommendations
        
        if not dns_working:
            recommendations.append("DNS解析异常，建议更换DNS服务器")
            recommendations.append("可尝试使用 8.8.8.8 或 114.114.114.114")
        
        accessibility_ratio = accessible_count / total_count if total_count > 0 else 0
        
        if accessibility_ratio < 0.5:
            recommendations.append("多数网站无法访问，可能存在网络限制")
            recommendations.append("建议检查防火墙或代理设置")
        
        if avg_response_time > 3000:
            recommendations.append("网络响应较慢，建议优化网络环境")
            recommendations.append("可尝试重启路由器或联系网络服务商")
        elif avg_response_time > 1000:
            recommendations.append("网络响应一般，建议关闭其他网络应用")
        
        if len(recommendations) == 0:
            recommendations.append("网络状态良好，可以正常下载")
        
        return recommendations
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None
