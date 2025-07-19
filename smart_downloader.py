#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 智能下载器
支持断点续传、镜像切换、进度监控
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

@dataclass
class DownloadTask:
    """下载任务"""
    name: str
    url: str
    local_path: Path
    size: int
    checksum: str
    priority: int = 1
    mirrors: List[str] = None

class SmartDownloader:
    """智能下载器"""

    def __init__(self, cache_dir: Path = None, max_workers: int = 3):
        self.cache_dir = cache_dir or Path("downloads")
        self.cache_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.progress_callbacks: List[Callable] = []
        self.download_stats = {
            "total_bytes": 0,
            "downloaded_bytes": 0,
            "current_speed": 0,
            "eta_seconds": 0
        }
        self._lock = threading.Lock()
        
        # 镜像配置
        self.mirrors = {
            "modelscope": "https://modelscope.cn/models/{model_id}/resolve/main/{filename}",
            "huggingface": "https://huggingface.co/{model_id}/resolve/main/{filename}",
            "github": "https://github.com/{repo}/releases/download/{tag}/{filename}"
        }
    
    def add_progress_callback(self, callback: Callable):
        """添加进度回调"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, task_name: str, progress: float, speed: float):
        """通知进度更新"""
        with self._lock:
            self.download_stats["current_speed"] = speed
            
        for callback in self.progress_callbacks:
            try:
                callback(task_name, progress, speed, self.download_stats)
            except Exception as e:
                print(f"进度回调错误: {e}")
    
    def _get_file_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        if not file_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _download_with_resume(self, task: DownloadTask) -> bool:
        """支持断点续传的下载"""
        local_path = self.cache_dir / task.local_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 检查是否已存在且校验和正确
        if local_path.exists():
            if self._get_file_checksum(local_path) == task.checksum:
                print(f"✅ {task.name} 已存在且校验正确")
                return True
            else:
                print(f"🔄 {task.name} 校验失败，重新下载")
        
        # 获取已下载大小
        resume_pos = local_path.stat().st_size if local_path.exists() else 0
        
        # 尝试多个镜像
        urls_to_try = [task.url] + (task.mirrors or [])

        for url in urls_to_try:
            try:
                print(f"📥 开始下载 {task.name} 从 {url}")

                headers = {}
                if resume_pos > 0:
                    headers['Range'] = f'bytes={resume_pos}-'
                    print(f"🔄 断点续传，从 {resume_pos} 字节开始")

                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0)) + resume_pos
                downloaded = resume_pos

                mode = 'ab' if resume_pos > 0 else 'wb'
                with open(local_path, mode) as f:
                    start_time = time.time()
                    last_update = start_time

                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # 更新进度
                            current_time = time.time()
                            if current_time - last_update > 0.5:  # 每0.5秒更新一次
                                elapsed = current_time - start_time
                                speed = (downloaded - resume_pos) / elapsed if elapsed > 0 else 0
                                progress = downloaded / total_size if total_size > 0 else 0

                                self._notify_progress(task.name, progress, speed)
                                last_update = current_time
                
                # 验证下载完整性
                if task.checksum and self._get_file_checksum(local_path) != task.checksum:
                    print(f"❌ {task.name} 校验失败")
                    local_path.unlink(missing_ok=True)
                    continue

                print(f"✅ {task.name} 下载完成")
                return True

            except Exception as e:
                print(f"❌ 下载失败 {url}: {e}")
                continue
        
        print(f"💥 {task.name} 所有镜像下载失败")
        return False
    
    def download_batch(self, tasks: List[DownloadTask]) -> Dict[str, bool]:
        """批量下载"""
        # 按优先级排序
        tasks.sort(key=lambda x: x.priority, reverse=True)
        
        # 计算总大小
        total_size = sum(task.size for task in tasks)
        with self._lock:
            self.download_stats["total_bytes"] = total_size
            self.download_stats["downloaded_bytes"] = 0
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._download_with_resume, task): task 
                for task in tasks
            }
            
            for future in future_to_task:
                task = future_to_task[future]
                try:
                    success = future.result()
                    results[task.name] = success
                    
                    if success:
                        with self._lock:
                            self.download_stats["downloaded_bytes"] += task.size
                    
                except Exception as e:
                    print(f"任务 {task.name} 执行异常: {e}")
                    results[task.name] = False
        
        return results
    
    def create_model_download_tasks(self, 
                                  models_config: Dict,
                                  quantization_level: str = "balanced") -> List[DownloadTask]:
        """创建模型下载任务"""
        tasks = []
        
        for model_name, config in models_config.items():
            if config.get("auto_download", True):
                # 根据量化级别选择文件
                quant_config = config.get("quantization_options", {})
                quant_name = quant_config.get(quantization_level, "Q4_K_M")
                
                # 构建下载任务
                task = DownloadTask(
                    name=f"{model_name}-{quant_name}",
                    url=self._build_download_url(config, quant_name),
                    local_path=Path(config["path"].format(quantization=quant_name)),
                    size=self._estimate_model_size(quant_name),
                    checksum="",  # 实际使用时需要提供真实校验和
                    priority=2 if config["language"] == "zh" else 1,  # 中文模型优先
                    mirrors=self._get_model_mirrors(config, quant_name)
                )
                tasks.append(task)
        
        return tasks
    
    def _build_download_url(self, config: Dict, quantization: str) -> str:
        """构建下载URL"""
        primary_source = config.get("download_sources", {}).get("primary", "modelscope")
        
        if primary_source == "modelscope":
            model_id = config["modelscope_id"]
            filename = f"model-{quantization.lower()}.gguf"
            return self.mirrors["modelscope"].format(
                model_id=model_id, 
                filename=filename
            )
        else:
            model_id = config["huggingface_id"] 
            filename = f"model-{quantization.lower()}.gguf"
            return self.mirrors["huggingface"].format(
                model_id=model_id,
                filename=filename
            )
    
    def _get_model_mirrors(self, config: Dict, quantization: str) -> List[str]:
        """获取模型镜像列表"""
        mirrors = []
        
        # 添加备用源
        fallback_source = config.get("download_sources", {}).get("fallback")
        if fallback_source:
            if fallback_source == "modelscope":
                model_id = config["modelscope_id"]
            else:
                model_id = config["huggingface_id"]
            
            filename = f"model-{quantization.lower()}.gguf"
            mirror_url = self.mirrors[fallback_source].format(
                model_id=model_id,
                filename=filename
            )
            mirrors.append(mirror_url)
        
        return mirrors
    
    def _estimate_model_size(self, quantization: str) -> int:
        """估算模型大小"""
        size_map = {
            "Q2_K": 1800 * 1024 * 1024,    # 1.8GB
            "Q4_K_M": 2600 * 1024 * 1024,  # 2.6GB
            "Q5_K": 3800 * 1024 * 1024,    # 3.8GB
            "FP16": 14400 * 1024 * 1024    # 14.4GB
        }
        return size_map.get(quantization, 2600 * 1024 * 1024)

def main():
    """主函数 - 演示智能下载器"""
    downloader = SmartDownloader()
    
    # 添加进度回调
    def progress_callback(task_name, progress, speed, stats):
        speed_mb = speed / (1024 * 1024)
        print(f"📥 {task_name}: {progress:.1%} 完成, 速度: {speed_mb:.1f} MB/s")
    
    downloader.add_progress_callback(progress_callback)
    
    # 示例下载任务
    tasks = [
        DownloadTask(
            name="测试文件",
            url="https://httpbin.org/bytes/1024",
            local_path=Path("test.bin"),
            size=1024,
            checksum="",
            priority=1
        )
    ]
    
    print("🚀 开始下载测试...")
    results = downloader.download_batch(tasks)
    
    print("\n📊 下载结果:")
    for task_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {task_name}: {status}")

if __name__ == "__main__":
    main()
