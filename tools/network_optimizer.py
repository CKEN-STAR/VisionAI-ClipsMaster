#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网络优化器 - 针对中国大陆网络环境优化

提供镜像源选择、下载加速、断点续传等功能
"""

import os
import sys
import time
import json
import requests
import threading
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

class NetworkOptimizer:
    """网络优化器"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        
        # 中国大陆CDN节点配置
        self.cdn_nodes = {
            "华为云": {
                "base_url": "https://mirrors.huaweicloud.com/",
                "regions": ["cn-north-1", "cn-east-2", "cn-south-1"],
                "priority": 1
            },
            "阿里云": {
                "base_url": "https://mirrors.aliyun.com/",
                "regions": ["cn-hangzhou", "cn-beijing", "cn-shenzhen"],
                "priority": 2
            },
            "腾讯云": {
                "base_url": "https://mirrors.cloud.tencent.com/",
                "regions": ["ap-beijing", "ap-shanghai", "ap-guangzhou"],
                "priority": 3
            },
            "清华大学": {
                "base_url": "https://mirrors.tuna.tsinghua.edu.cn/",
                "regions": ["main"],
                "priority": 4
            },
            "中科大": {
                "base_url": "https://mirrors.ustc.edu.cn/",
                "regions": ["main"],
                "priority": 5
            }
        }
        
        # 模型文件下载源配置
        self.model_sources = {
            "HuggingFace": {
                "base_url": "https://huggingface.co/",
                "mirror_url": "https://hf-mirror.com/",
                "priority": 1
            },
            "ModelScope": {
                "base_url": "https://modelscope.cn/",
                "mirror_url": "https://modelscope.cn/",
                "priority": 2
            },
            "OpenI": {
                "base_url": "https://openi.org.cn/",
                "mirror_url": "https://openi.org.cn/",
                "priority": 3
            }
        }
        
        self.selected_cdn = None
        self.download_stats = {
            'total_downloaded': 0,
            'total_time': 0,
            'average_speed': 0
        }
        
    def test_network_speed(self, url, timeout=5, test_size_kb=100):
        """测试网络速度"""
        try:
            # 构造测试URL
            if not url.endswith('/'):
                url += '/'
            test_url = urljoin(url, 'speedtest/')
            
            start_time = time.time()
            
            # 发送HEAD请求测试连接
            response = requests.head(test_url, timeout=timeout, allow_redirects=True)
            
            if response.status_code in [200, 301, 302, 404]:  # 404也算连通
                latency = time.time() - start_time
                
                # 尝试下载小文件测试速度
                try:
                    download_start = time.time()
                    response = requests.get(
                        test_url, 
                        timeout=timeout,
                        stream=True,
                        headers={'Range': f'bytes=0-{test_size_kb * 1024}'}
                    )
                    
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=1024):
                        downloaded += len(chunk)
                        if downloaded >= test_size_kb * 1024:
                            break
                            
                    download_time = time.time() - download_start
                    speed_kbps = downloaded / 1024 / download_time if download_time > 0 else 0
                    
                    return {
                        'latency': latency,
                        'speed_kbps': speed_kbps,
                        'success': True
                    }
                    
                except:
                    # 如果下载测试失败，只返回延迟
                    return {
                        'latency': latency,
                        'speed_kbps': 0,
                        'success': True
                    }
            else:
                return {
                    'latency': float('inf'),
                    'speed_kbps': 0,
                    'success': False
                }
                
        except Exception as e:
            return {
                'latency': float('inf'),
                'speed_kbps': 0,
                'success': False,
                'error': str(e)
            }
            
    def select_best_cdn(self, test_timeout=5):
        """选择最佳CDN节点"""
        print("[INFO] 正在测试CDN节点性能...")
        
        results = {}
        
        # 并发测试所有CDN节点
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_cdn = {
                executor.submit(
                    self.test_network_speed, 
                    cdn_info["base_url"], 
                    test_timeout
                ): cdn_name
                for cdn_name, cdn_info in self.cdn_nodes.items()
            }
            
            for future in as_completed(future_to_cdn):
                cdn_name = future_to_cdn[future]
                try:
                    result = future.result()
                    results[cdn_name] = result
                    
                    if result['success']:
                        print(f"[INFO] {cdn_name}: 延迟 {result['latency']:.2f}s, "
                              f"速度 {result['speed_kbps']:.1f} KB/s")
                    else:
                        print(f"[WARN] {cdn_name}: 连接失败")
                        
                except Exception as e:
                    print(f"[ERROR] {cdn_name}: 测试异常 - {e}")
                    results[cdn_name] = {
                        'latency': float('inf'),
                        'speed_kbps': 0,
                        'success': False
                    }
                    
        # 选择最佳CDN（优先考虑延迟，其次考虑速度）
        available_cdns = {
            name: result for name, result in results.items() 
            if result['success']
        }
        
        if available_cdns:
            # 综合评分：延迟权重70%，速度权重30%
            def calculate_score(result):
                latency_score = 1 / (result['latency'] + 0.1)  # 延迟越低分数越高
                speed_score = result['speed_kbps'] / 1000  # 速度分数
                return latency_score * 0.7 + speed_score * 0.3
                
            best_cdn = max(available_cdns.items(), key=lambda x: calculate_score(x[1]))
            self.selected_cdn = best_cdn[0]
            
            print(f"[OK] 选择CDN: {self.selected_cdn}")
            print(f"     延迟: {best_cdn[1]['latency']:.2f}s")
            print(f"     速度: {best_cdn[1]['speed_kbps']:.1f} KB/s")
            
            return True
        else:
            print("[ERROR] 所有CDN节点都不可用")
            return False
            
    def download_with_resume(self, url, filepath, progress_callback=None, chunk_size=8192):
        """支持断点续传的下载功能"""
        try:
            # 检查文件是否已存在（断点续传）
            resume_pos = 0
            if filepath.exists():
                resume_pos = filepath.stat().st_size
                print(f"[INFO] 检测到未完成下载，从 {resume_pos} 字节继续")
                
            # 设置请求头
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
                
            # 开始下载
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            if resume_pos > 0:
                total_size += resume_pos
                
            downloaded = resume_pos
            start_time = time.time()
            
            # 确保目录存在
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            mode = 'ab' if resume_pos > 0 else 'wb'
            with open(filepath, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            elapsed_time = time.time() - start_time
                            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                            
                            progress_callback({
                                'progress': progress,
                                'downloaded': downloaded,
                                'total': total_size,
                                'speed': speed,
                                'elapsed': elapsed_time
                            })
                            
            # 更新统计信息
            total_time = time.time() - start_time
            self.download_stats['total_downloaded'] += downloaded - resume_pos
            self.download_stats['total_time'] += total_time
            
            if self.download_stats['total_time'] > 0:
                self.download_stats['average_speed'] = (
                    self.download_stats['total_downloaded'] / 
                    self.download_stats['total_time']
                )
                
            print(f"[OK] 下载完成: {filepath}")
            print(f"     大小: {downloaded / 1024 / 1024:.1f} MB")
            print(f"     用时: {total_time:.1f}s")
            print(f"     速度: {(downloaded - resume_pos) / total_time / 1024:.1f} KB/s")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 下载失败: {e}")
            return False
            
    def get_optimized_url(self, original_url, resource_type="general"):
        """获取优化后的URL"""
        if not self.selected_cdn:
            if not self.select_best_cdn():
                return original_url
                
        # 根据资源类型选择最佳镜像
        if resource_type == "model":
            # 模型文件使用专用镜像
            for source_name, source_info in self.model_sources.items():
                if source_info["base_url"] in original_url:
                    optimized_url = original_url.replace(
                        source_info["base_url"],
                        source_info["mirror_url"]
                    )
                    print(f"[INFO] 模型URL优化: {source_name} -> 镜像")
                    return optimized_url
                    
        elif resource_type == "package":
            # Python包使用CDN加速
            cdn_info = self.cdn_nodes[self.selected_cdn]
            # 这里可以添加包镜像逻辑
            pass
            
        return original_url
        
    def get_download_stats(self):
        """获取下载统计信息"""
        return self.download_stats.copy()
        
    def reset_stats(self):
        """重置统计信息"""
        self.download_stats = {
            'total_downloaded': 0,
            'total_time': 0,
            'average_speed': 0
        }


# 全局网络优化器实例
network_optimizer = NetworkOptimizer()

def get_optimized_download_url(url, resource_type="general"):
    """获取优化后的下载URL"""
    return network_optimizer.get_optimized_url(url, resource_type)

def download_with_optimization(url, filepath, progress_callback=None):
    """使用网络优化的下载功能"""
    optimized_url = get_optimized_download_url(url)
    return network_optimizer.download_with_resume(
        optimized_url, filepath, progress_callback
    )


if __name__ == "__main__":
    # 测试网络优化器
    optimizer = NetworkOptimizer()
    
    print("测试CDN节点选择...")
    success = optimizer.select_best_cdn()
    
    if success:
        print(f"\n下载统计: {optimizer.get_download_stats()}")
    else:
        print("网络优化器测试失败")
