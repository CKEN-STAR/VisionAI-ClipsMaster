#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 增强模型下载器
实现真实有效的模型下载功能，包括进度显示、错误处理和断点续传

修复说明：
- 使用threading.Thread（QThread）进行下载
- 通过is_cancelled标志位实现取消功能
- 在下载循环中检查标志位并优雅退出
"""

import os
import sys
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QProgressDialog, QMessageBox, QApplication
import logging

# 🔧 新增：导入huggingface_hub用于snapshot_download
try:
    from huggingface_hub import snapshot_download, HfApi
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    logger.warning("huggingface_hub未安装，将使用传统HTTP下载方式")

# 配置日志
logger = logging.getLogger(__name__)


# ============================================================================
# 下载工作进程函数（在独立进程中运行）
# ============================================================================

def download_worker_process(repo_id: str, local_dir: str, endpoint: Optional[str],
                           progress_queue: Queue, cancel_event: Event):
    """下载工作进程（在独立进程中运行）

    Args:
        repo_id: HuggingFace仓库ID
        local_dir: 本地保存目录
        endpoint: 镜像源endpoint
        progress_queue: 进度队列（用于向主进程发送进度信息）
        cancel_event: 取消事件（主进程设置此事件来取消下载）

    Returns:
        通过progress_queue发送状态信息：
        - {"status": "completed"}: 下载完成
        - {"status": "error", "message": str}: 下载失败
    """
    try:
        # 设置环境变量（如果有endpoint）
        if endpoint:
            os.environ['HF_ENDPOINT'] = endpoint

        # 执行下载
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True,
            max_workers=2,
            endpoint=endpoint,
        )

        # 下载成功
        progress_queue.put({"status": "completed"})

    except Exception as e:
        # 下载失败
        progress_queue.put({"status": "error", "message": str(e)})
    finally:
        # 清理环境变量
        if endpoint and 'HF_ENDPOINT' in os.environ:
            del os.environ['HF_ENDPOINT']


# ============================================================================
# UI类定义
# ============================================================================

class EnhancedProgressDialog(QProgressDialog):
    """增强的进度对话框（显示详细下载信息）"""

    def __init__(self, title: str, parent=None):
        super().__init__(title, "取消", 0, 100, parent)
        self.setWindowTitle("模型下载")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setAutoClose(False)
        self.setAutoReset(False)

        # 下载信息
        self.current_file = ""
        self.download_speed = 0.0
        self.eta_seconds = 0
        self.downloaded_mb = 0.0
        self.total_mb = 0.0

    def update_enhanced_progress(self, progress: int, downloaded_mb: float,
                                total_mb: float, speed_mb: float,
                                eta_seconds: int, filename: str):
        """更新增强的进度信息"""
        self.setValue(progress)
        self.current_file = filename
        self.download_speed = speed_mb
        self.eta_seconds = eta_seconds
        self.downloaded_mb = downloaded_mb
        self.total_mb = total_mb

        # 格式化剩余时间
        if eta_seconds > 0:
            hours = eta_seconds // 3600
            minutes = (eta_seconds % 3600) // 60
            seconds = eta_seconds % 60

            if hours > 0:
                eta_str = f"{hours}小时{minutes}分钟"
            elif minutes > 0:
                eta_str = f"{minutes}分{seconds}秒"
            else:
                eta_str = f"{seconds}秒"
        else:
            eta_str = "计算中..."

        # 更新标签文本
        label_text = f"""下载文件: {filename}
进度: {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({progress}%)
速度: {speed_mb:.2f} MB/s
剩余时间: {eta_str}"""

        self.setLabelText(label_text)

class ModelDownloadThread(QThread):
    """模型下载线程（增强版：支持速度显示、剩余时间、自动清理）"""

    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度百分比, 状态信息
    download_completed = pyqtSignal(str, bool)  # 模型名称, 是否成功
    error_occurred = pyqtSignal(str, str)  # 错误类型, 错误信息
    # 新增：增强的进度信号（进度%, 已下载MB, 总大小MB, 速度MB/s, 剩余秒数, 文件名）
    enhanced_progress_updated = pyqtSignal(int, float, float, float, int, str)

    def __init__(self, model_name: str, download_config: Dict, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.download_config = download_config
        self.is_cancelled = False
        self.is_paused = False  # 新增：暂停标志
        self.session = requests.Session()

        # 下载速度跟踪
        self.start_time = 0
        self.last_update_time = 0
        self.last_downloaded_bytes = 0
        self.download_speeds = []  # 用于平滑速度计算

        # 下载文件跟踪（用于清理）
        self.downloaded_files = []  # 已下载的文件路径
        self.target_directory = None  # 目标目录

        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'VisionAI-ClipsMaster/1.0 (Model Downloader)',
            'Accept': 'application/octet-stream, */*',
            'Accept-Encoding': 'gzip, deflate'
        })
    
    def cancel_download(self):
        """取消下载（会触发清理）"""
        self.is_cancelled = True
        logger.info(f"用户取消下载: {self.model_name}")

    def stop(self):
        """停止下载（UI兼容方法，等同于cancel_download）"""
        self.cancel_download()

    def pause_download(self):
        """暂停下载（不清理，支持断点续传）"""
        self.is_paused = True
        logger.info(f"用户暂停下载: {self.model_name}")

    def resume_download(self):
        """继续下载"""
        self.is_paused = False
        logger.info(f"用户继续下载: {self.model_name}")

    def _download_with_snapshot(self, repo_id: str, local_dir: Path, mirror_sources: list = None) -> bool:
        """使用snapshot_download下载整个模型仓库（支持多源下载）

        Args:
            repo_id: HuggingFace仓库ID（如Qwen/Qwen3-1.7B）
            local_dir: 本地保存目录
            mirror_sources: 镜像源列表，按优先级排序 [{'name': 'HF-Mirror', 'endpoint': 'https://hf-mirror.com'}, ...]

        Returns:
            bool: 下载是否成功
        """
        if not HF_HUB_AVAILABLE:
            logger.error("huggingface_hub未安装，无法使用snapshot_download")
            return False

        # 默认多源下载策略：国内高速镜像 → 阿里云镜像 → HuggingFace官方
        # 更新时间：2025-11-01（经过网络验证，所有镜像源均可用）
        if not mirror_sources:
            mirror_sources = [
                {'name': 'HF-Mirror（国内高速镜像）', 'endpoint': 'https://hf-mirror.com'},  # 公益项目，稳定可靠
                {'name': 'ModelScope（阿里云镜像）', 'endpoint': 'https://www.modelscope.cn'},  # 阿里云支持，企业级稳定
                {'name': 'HuggingFace官方', 'endpoint': None},  # None表示使用官方源，永不失效
            ]

        local_dir.mkdir(parents=True, exist_ok=True)

        # 尝试每个镜像源
        for idx, source in enumerate(mirror_sources):
            source_name = source['name']
            endpoint = source['endpoint']

            try:
                logger.info(f"🚀 [{idx+1}/{len(mirror_sources)}] 尝试从 {source_name} 下载模型: {repo_id}")
                self.progress_updated.emit(5, f"连接到 {source_name}: {repo_id}...")

                # 设置环境变量（如果有endpoint）
                import os
                old_endpoint = os.environ.get('HF_ENDPOINT')
                if endpoint:
                    os.environ['HF_ENDPOINT'] = endpoint
                    logger.info(f"📡 设置镜像源: {endpoint}")

                # 首先获取模型信息和大小
                total_size = 0
                total_size_gb = 0
                try:
                    # 🔧 使用正确的endpoint参数
                    if endpoint:
                        api = HfApi(endpoint=endpoint)
                        logger.info(f"📡 使用镜像API: {endpoint}")
                    else:
                        api = HfApi()
                        logger.info(f"📡 使用官方API: https://huggingface.co")

                    model_info = api.model_info(repo_id)
                    total_size = sum(f.size for f in model_info.siblings if f.size)
                    total_size_gb = total_size / (1024**3)

                    if total_size > 0:
                        logger.info(f"📊 模型总大小: {total_size_gb:.2f} GB")
                        self.progress_updated.emit(10, f"模型大小: {total_size_gb:.2f} GB，开始下载...")
                    else:
                        logger.warning(f"⚠️ API返回的模型大小为0，将仅显示已下载大小")
                        self.progress_updated.emit(10, f"开始下载... (大小未知)")
                except Exception as e:
                    logger.warning(f"⚠️ 无法从 {source_name} 获取模型信息: {e}")
                    logger.warning(f"⚠️ 尝试下一个镜像源...")
                    # 恢复环境变量
                    if endpoint:
                        if old_endpoint:
                            os.environ['HF_ENDPOINT'] = old_endpoint
                        else:
                            os.environ.pop('HF_ENDPOINT', None)
                    continue  # 跳到下一个镜像源

                # 🔧 使用multiprocessing.Process下载（支持真正的取消）
                progress_queue = Queue()
                cancel_event = Event()
                download_error = None

                # 启动下载进程
                download_process = Process(
                    target=download_worker_process,
                    args=(repo_id, str(local_dir), endpoint, progress_queue, cancel_event)
                )
                download_process.start()
                logger.info(f"✅ 下载进程已启动 (PID: {download_process.pid})")

                # 监控下载进度（通过检查目录大小）
                last_progress = 10
                last_downloaded_gb = 0
                cancelled_flag = False
                update_counter = 0  # 用于强制定期更新
                download_completed = False

                while download_process.is_alive() or not download_completed:
                    # 🔧 检查取消标志 - 强制终止下载进程
                    if self.is_cancelled and not cancelled_flag:
                        logger.warning("⚠️ 用户取消下载，正在强制终止下载进程...")
                        cancelled_flag = True
                        cancel_event.set()  # 设置取消标志

                        # 发送取消信号
                        self.progress_updated.emit(0, "正在取消下载...")

                        # 🔧 强制终止下载进程
                        try:
                            logger.info(f"📡 发送SIGTERM信号到进程 {download_process.pid}...")
                            download_process.terminate()  # 发送SIGTERM
                            download_process.join(timeout=2)  # 等待2秒

                            if download_process.is_alive():
                                logger.warning(f"⚠️ 进程未响应SIGTERM，发送SIGKILL...")
                                download_process.kill()  # 强制SIGKILL
                                download_process.join(timeout=1)

                            if not download_process.is_alive():
                                logger.info("✅ 下载进程已成功终止")
                            else:
                                logger.error("❌ 下载进程无法终止")
                        except Exception as e:
                            logger.error(f"❌ 终止下载进程失败: {e}")

                        # 立即清理不完整的下载
                        self._cleanup_snapshot_download(local_dir)

                        raise Exception("用户取消下载")

                    # 检查进程状态队列
                    try:
                        status_msg = progress_queue.get(timeout=0.1)
                        if status_msg["status"] == "completed":
                            logger.info("✅ 下载进程报告：下载完成")
                            download_completed = True
                            break
                        elif status_msg["status"] == "error":
                            download_error = status_msg.get("message", "Unknown error")
                            logger.error(f"❌ 下载进程报告错误: {download_error}")
                            download_completed = True
                            break
                    except queue.Empty:
                        pass  # 队列为空，继续监控

                    # 计算当前下载大小
                    if not cancelled_flag:
                        update_counter += 1
                        try:
                            current_size = sum(f.stat().st_size for f in local_dir.rglob('*') if f.is_file())
                            downloaded_gb = current_size / (1024**3)

                            # 检查是否需要更新UI（大小变化或每2秒强制更新一次）
                            should_update = (
                                abs(downloaded_gb - last_downloaded_gb) > 0.01 or  # 大小变化超过10MB
                                update_counter % 4 == 0  # 每2秒强制更新一次（0.5s * 4）
                            )

                            if should_update:
                                last_downloaded_gb = downloaded_gb

                                if total_size > 0:
                                    # 有总大小信息，显示百分比
                                    progress = int(10 + (current_size / total_size) * 85)  # 10%-95%
                                    if progress > last_progress:
                                        last_progress = progress
                                    self.progress_updated.emit(
                                        progress,
                                        f"下载中... {downloaded_gb:.2f}GB / {total_size_gb:.2f}GB ({progress}%)"
                                    )
                                    logger.debug(f"📊 下载进度: {progress}% ({downloaded_gb:.2f}GB / {total_size_gb:.2f}GB)")
                                else:
                                    # 没有总大小信息，只显示已下载大小
                                    if downloaded_gb > 0:
                                        self.progress_updated.emit(
                                            50,  # 固定在50%
                                            f"下载中... {downloaded_gb:.2f}GB (大小未知)"
                                        )
                                        logger.debug(f"📊 已下载: {downloaded_gb:.2f}GB")
                        except Exception as e:
                            logger.debug(f"计算进度失败: {e}")

                    time.sleep(0.5)  # 每0.5秒检查一次（更快响应）

                # 等待下载进程完成
                if not cancelled_flag and download_process.is_alive():
                    download_process.join(timeout=5)

                # 检查是否有错误
                if download_error and not cancelled_flag:
                    raise Exception(f"下载失败: {download_error}")

                if self.is_cancelled or cancelled_flag:
                    raise Exception("用户取消下载")

                # 恢复环境变量
                if endpoint:
                    if old_endpoint:
                        os.environ['HF_ENDPOINT'] = old_endpoint
                    else:
                        os.environ.pop('HF_ENDPOINT', None)

                logger.info(f"✅ 模型下载完成（来源: {source_name}）")
                self.progress_updated.emit(100, f"下载完成！（来源: {source_name}）")
                return True

            except Exception as e:
                logger.warning(f"❌ 从 {source_name} 下载失败: {e}")

                # 恢复环境变量
                if endpoint:
                    if old_endpoint:
                        os.environ['HF_ENDPOINT'] = old_endpoint
                    else:
                        os.environ.pop('HF_ENDPOINT', None)

                # 🔧 清理不完整的下载文件
                logger.info(f"🧹 清理从 {source_name} 下载的不完整文件...")
                self._cleanup_snapshot_download(local_dir)

                # 如果不是最后一个源，继续尝试下一个
                if idx < len(mirror_sources) - 1:
                    logger.info(f"⏭️ 切换到下一个镜像源...")
                    self.progress_updated.emit(5, f"切换到下一个镜像源...")
                    continue
                else:
                    # 最后一个源也失败了
                    logger.error(f"❌ 所有镜像源都失败了")
                    import traceback
                    logger.error(f"详细错误: {traceback.format_exc()}")

                    # 🔧 最终清理
                    logger.info(f"🧹 清理所有不完整的下载文件...")
                    self._cleanup_snapshot_download(local_dir)
                    return False

        return False

    def _cleanup_snapshot_download(self, local_dir: Path):
        """清理snapshot_download产生的不完整文件

        Args:
            local_dir: 下载目录
        """
        try:
            if not local_dir.exists():
                return

            logger.info(f"🧹 开始清理目录: {local_dir}")

            # 统计清理的文件
            cleaned_count = 0

            # 1. 清理所有临时文件
            temp_patterns = [
                "*.tmp", "*.part", "*.download", "*.crdownload",
                "*.downloading", "*.incomplete", ".locks/*"
            ]

            for pattern in temp_patterns:
                for temp_file in local_dir.rglob(pattern):
                    try:
                        if temp_file.is_file():
                            temp_file.unlink()
                            cleaned_count += 1
                            logger.debug(f"删除临时文件: {temp_file.name}")
                        elif temp_file.is_dir():
                            import shutil
                            shutil.rmtree(temp_file)
                            cleaned_count += 1
                            logger.debug(f"删除临时目录: {temp_file.name}")
                    except Exception as e:
                        logger.warning(f"删除失败: {temp_file}, 错误: {e}")

            # 2. 清理huggingface_hub的缓存锁文件
            locks_dir = local_dir / ".locks"
            if locks_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(locks_dir)
                    cleaned_count += 1
                    logger.debug("删除.locks目录")
                except Exception as e:
                    logger.warning(f"删除.locks目录失败: {e}")

            # 3. 如果目录为空或只有隐藏文件，删除整个目录
            if local_dir.exists():
                visible_files = [f for f in local_dir.rglob('*') if f.is_file() and not f.name.startswith('.')]
                if not visible_files:
                    try:
                        import shutil
                        shutil.rmtree(local_dir)
                        logger.info(f"✅ 删除空目录: {local_dir}")
                    except Exception as e:
                        logger.warning(f"删除目录失败: {local_dir}, 错误: {e}")

            if cleaned_count > 0:
                logger.info(f"✅ 清理完成，共删除 {cleaned_count} 个文件/目录")
            else:
                logger.info("✅ 没有需要清理的文件")

        except Exception as e:
            logger.error(f"清理失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")

    def run(self):
        """执行下载"""
        try:
            logger.info(f"开始下载模型: {self.model_name}")
            self.progress_updated.emit(0, f"准备下载 {self.model_name}...")
            self.start_time = time.time()

            # 创建目标目录
            target_dir = Path(self.download_config['target_dir'])
            target_dir.mkdir(parents=True, exist_ok=True)
            self.target_directory = target_dir

            # 🔧 新增：检查是否使用snapshot_download
            use_snapshot = self.download_config.get('use_snapshot_download', False)
            repo_id = self.download_config.get('repo_id')
            mirror_sources = self.download_config.get('mirror_sources')  # 🔧 获取镜像源配置

            if use_snapshot and repo_id and HF_HUB_AVAILABLE:
                logger.info(f"✅ 使用snapshot_download模式下载: {repo_id}")
                success = self._download_with_snapshot(repo_id, target_dir, mirror_sources)  # 🔧 传递镜像源
                if success:
                    self.download_completed.emit(self.model_name, True)
                else:
                    self.error_occurred.emit("下载失败", "snapshot_download下载失败")
                return

            # 下载所有文件（传统HTTP下载方式）
            total_files = len(self.download_config['files'])
            for i, file_info in enumerate(self.download_config['files']):
                if self.is_cancelled:
                    logger.warning(f"下载被取消，开始清理: {self.model_name}")
                    self.cleanup_incomplete_download()
                    return

                file_name = file_info['name']
                file_url = file_info['url']

                self.progress_updated.emit(
                    int((i / total_files) * 100),
                    f"下载文件 {i+1}/{total_files}: {file_name}"
                )

                # 不再传递expected_size，让_download_file从HTTP响应头获取
                success = self._download_file(file_url, target_dir / file_name)
                if not success:
                    if self.is_cancelled:
                        logger.warning(f"下载被取消，开始清理: {self.model_name}")
                        self.cleanup_incomplete_download()
                    else:
                        logger.error(f"下载失败，开始清理: {file_name}")
                        self.cleanup_incomplete_download()
                        self.error_occurred.emit("下载失败", f"文件 {file_name} 下载失败")
                    return

            # 验证下载完整性
            self.progress_updated.emit(95, "验证文件完整性...")
            if self._verify_download():
                self.progress_updated.emit(100, "下载完成!")
                self.download_completed.emit(self.model_name, True)
                logger.info(f"下载成功完成: {self.model_name}")
            else:
                logger.error(f"文件完整性验证失败，开始清理: {self.model_name}")
                self.cleanup_incomplete_download()
                self.error_occurred.emit("验证失败", "下载的文件不完整或损坏")

        except Exception as e:
            logger.error(f"下载过程中发生错误: {str(e)}")
            logger.warning(f"异常导致下载中断，开始清理: {self.model_name}")
            self.cleanup_incomplete_download()
            self.error_occurred.emit("下载错误", str(e))
    
    def _download_file(self, url: str, target_path: Path, expected_size: int = 0) -> bool:
        """下载单个文件（增强版：支持速度显示、剩余时间）

        注意：expected_size参数已废弃，文件大小从HTTP响应头动态获取
        """
        try:
            # 首先发送HEAD请求获取文件大小
            try:
                head_response = self.session.head(url, timeout=10)
                head_response.raise_for_status()
                expected_size_from_server = int(head_response.headers.get('content-length', 0))
            except Exception as e:
                logger.warning(f"无法获取文件大小（HEAD请求失败）: {e}")
                expected_size_from_server = 0

            # 检查是否支持断点续传
            resume_pos = 0
            if target_path.exists():
                resume_pos = target_path.stat().st_size
                # 如果文件已存在且大小匹配，跳过下载
                if expected_size_from_server > 0 and resume_pos == expected_size_from_server:
                    logger.info(f"文件已存在且完整: {target_path.name}")
                    self.downloaded_files.append(target_path)
                    return True

            # 设置请求头支持断点续传
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
                logger.info(f"断点续传: {target_path.name} 从 {resume_pos} 字节开始")

            # 发起下载请求
            response = self.session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            # 获取文件总大小（优先使用HEAD请求的结果）
            if expected_size_from_server > 0:
                total_size = expected_size_from_server
            elif 'content-length' in response.headers:
                total_size = int(response.headers['content-length'])
                if resume_pos > 0:
                    total_size += resume_pos
            else:
                total_size = 0
                logger.warning(f"无法获取文件大小: {target_path.name}")

            # 下载文件
            mode = 'ab' if resume_pos > 0 else 'wb'
            downloaded = resume_pos
            self.last_downloaded_bytes = downloaded
            self.last_update_time = time.time()

            with open(target_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.is_cancelled:
                        logger.info(f"下载被取消: {target_path.name}")
                        return False

                    # 支持暂停
                    while self.is_paused and not self.is_cancelled:
                        time.sleep(0.1)

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 计算下载速度和剩余时间
                        current_time = time.time()
                        time_diff = current_time - self.last_update_time

                        if time_diff >= 0.5:  # 每0.5秒更新一次
                            bytes_diff = downloaded - self.last_downloaded_bytes
                            speed = bytes_diff / time_diff if time_diff > 0 else 0

                            # 平滑速度计算（使用最近10次的平均值）
                            self.download_speeds.append(speed)
                            if len(self.download_speeds) > 10:
                                self.download_speeds.pop(0)
                            avg_speed = sum(self.download_speeds) / len(self.download_speeds)

                            # 计算剩余时间
                            remaining_bytes = total_size - downloaded
                            eta_seconds = int(remaining_bytes / avg_speed) if avg_speed > 0 else 0

                            # 更新进度
                            if total_size > 0:
                                progress = int((downloaded / total_size) * 100)

                                # 发送增强的进度信号
                                self.enhanced_progress_updated.emit(
                                    progress,
                                    downloaded / (1024 * 1024),  # MB
                                    total_size / (1024 * 1024),   # MB
                                    avg_speed / (1024 * 1024),    # MB/s
                                    eta_seconds,
                                    target_path.name
                                )

                                # 发送旧的进度信号（向后兼容）
                                speed_mb = avg_speed / (1024 * 1024)
                                self.progress_updated.emit(
                                    progress,
                                    f"下载 {target_path.name}: {self._format_size(downloaded)}/{self._format_size(total_size)} ({speed_mb:.1f} MB/s)"
                                )

                            self.last_downloaded_bytes = downloaded
                            self.last_update_time = current_time

            logger.info(f"文件下载完成: {target_path.name}")
            self.downloaded_files.append(target_path)
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求错误: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"文件下载错误: {str(e)}")
            return False
    
    def _verify_download(self) -> bool:
        """验证下载完整性

        注意：不再依赖配置文件中的size字段，而是从服务器动态获取文件大小进行验证
        """
        try:
            target_dir = Path(self.download_config['target_dir'])

            for file_info in self.download_config['files']:
                file_path = target_dir / file_info['name']
                file_url = file_info['url']

                # 检查文件是否存在
                if not file_path.exists():
                    logger.error(f"文件不存在: {file_path}")
                    return False

                # 从服务器获取文件大小
                try:
                    head_response = self.session.head(file_url, timeout=10)
                    head_response.raise_for_status()
                    expected_size = int(head_response.headers.get('content-length', 0))
                except Exception as e:
                    logger.warning(f"无法从服务器获取文件大小: {file_path.name}, 跳过大小验证")
                    expected_size = 0

                # 检查文件大小（使用容差）
                if expected_size > 0:
                    actual_size = file_path.stat().st_size

                    # 根据文件大小使用不同的误差范围
                    # 大文件（>100MB）使用1%误差，小文件使用5%误差
                    if expected_size > 100 * 1024 * 1024:  # 100MB
                        tolerance = expected_size * 0.01  # 1%误差
                    else:
                        tolerance = expected_size * 0.05  # 5%误差

                    if abs(actual_size - expected_size) > tolerance:
                        size_diff_mb = abs(actual_size - expected_size) / (1024 * 1024)
                        tolerance_mb = tolerance / (1024 * 1024)
                        logger.error(f"文件大小不匹配: {file_path} (期望: {expected_size}, 实际: {actual_size}, 差异: {size_diff_mb:.2f}MB, 允许误差: {tolerance_mb:.2f}MB)")
                        return False
                
                # 检查文件哈希（如果提供）
                expected_hash = file_info.get('sha256')
                if expected_hash:
                    actual_hash = self._calculate_file_hash(file_path)
                    if actual_hash != expected_hash:
                        logger.error(f"文件哈希不匹配: {file_path}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证过程中发生错误: {str(e)}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def cleanup_incomplete_download(self):
        """清理不完整的下载文件

        触发场景：
        1. 用户手动取消下载
        2. 网络连接中断
        3. 下载过程中发生错误
        4. 文件完整性验证失败
        """
        try:
            logger.info(f"开始清理不完整的下载: {self.model_name}")

            if not self.target_directory:
                logger.warning("目标目录未设置，跳过清理")
                return

            target_dir = Path(self.target_directory)
            if not target_dir.exists():
                logger.info("目标目录不存在，无需清理")
                return

            cleaned_files = []

            # 清理所有配置中的文件
            for file_info in self.download_config['files']:
                file_path = target_dir / file_info['name']
                file_url = file_info['url']

                if file_path.exists():
                    try:
                        # 从服务器获取文件大小
                        try:
                            head_response = self.session.head(file_url, timeout=10)
                            head_response.raise_for_status()
                            expected_size = int(head_response.headers.get('content-length', 0))
                        except Exception as e:
                            logger.warning(f"无法从服务器获取文件大小: {file_path.name}, 将删除该文件以确保安全")
                            # 如果无法获取服务器文件大小，为了安全起见，删除该文件
                            file_path.unlink()
                            cleaned_files.append(str(file_path))
                            logger.info(f"已删除文件（无法验证完整性）: {file_path.name}")
                            continue

                        # 检查文件是否完整
                        actual_size = file_path.stat().st_size

                        # 根据文件大小使用不同的误差范围
                        # 大文件（>100MB）使用1%误差，小文件使用5%误差
                        if expected_size > 100 * 1024 * 1024:  # 100MB
                            tolerance = expected_size * 0.01  # 1%误差
                        else:
                            tolerance = expected_size * 0.05  # 5%误差

                        # 如果文件不完整，删除它
                        if expected_size > 0 and abs(actual_size - expected_size) > tolerance:
                            file_path.unlink()
                            cleaned_files.append(str(file_path))
                            size_diff_mb = abs(actual_size - expected_size) / (1024 * 1024)
                            logger.info(f"已删除不完整文件: {file_path.name} (期望={expected_size}, 实际={actual_size}, 差异={size_diff_mb:.2f}MB)")
                        else:
                            logger.info(f"文件完整，保留: {file_path.name}")
                    except Exception as e:
                        logger.error(f"处理文件时出错: {file_path}, 错误: {e}")

            # 清理所有临时文件（.tmp, .part, .download, .crdownload等）
            temp_patterns = ["*.tmp", "*.part", "*.download", "*.crdownload", "*.downloading"]
            for pattern in temp_patterns:
                for temp_file in target_dir.glob(pattern):
                    try:
                        temp_file.unlink()
                        cleaned_files.append(str(temp_file))
                        logger.info(f"已删除临时文件: {temp_file.name}")
                    except Exception as e:
                        logger.error(f"删除临时文件失败: {temp_file}, 错误: {e}")

            # 递归清理子目录中的临时文件
            for pattern in temp_patterns:
                for temp_file in target_dir.rglob(pattern):
                    try:
                        temp_file.unlink()
                        cleaned_files.append(str(temp_file))
                        logger.info(f"已删除临时文件: {temp_file}")
                    except Exception as e:
                        logger.error(f"删除临时文件失败: {temp_file}, 错误: {e}")

            # 如果目录为空，删除目录
            if target_dir.exists() and not any(target_dir.iterdir()):
                try:
                    target_dir.rmdir()
                    logger.info(f"已删除空目录: {target_dir}")
                except Exception as e:
                    logger.error(f"删除空目录失败: {target_dir}, 错误: {e}")

            if cleaned_files:
                logger.info(f"清理完成，共删除 {len(cleaned_files)} 个文件")
            else:
                logger.info("没有需要清理的文件")

        except Exception as e:
            logger.error(f"清理不完整下载失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

class EnhancedModelDownloader(QObject):
    """增强模型下载器 - 彻底重构版本"""

    # 版本标识符 - 用于确保新代码被加载
    VERSION = "v3.0_rebuild_20250905_final"

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info(f"🔧 初始化增强模型下载器 - {self.VERSION}")

        self.download_configs = self._load_download_configs()
        self.current_download = None
        self.progress_dialog = None
        self._last_model_name = None  # 添加状态跟踪

        # 初始化对话框管理器
        from .dialog_manager import DialogManager
        self.dialog_manager = DialogManager.get_instance()
        logger.info("✅ 对话框管理器已初始化")

        # 导入智能选择器
        try:
            from .intelligent_model_selector import IntelligentModelSelector, SelectionStrategy
            self.intelligent_selector = IntelligentModelSelector()
            self.has_intelligent_selector = True
            logger.info("✅ 智能模型选择器已加载")
        except ImportError:
            self.intelligent_selector = None
            self.has_intelligent_selector = False
            logger.warning("智能模型选择器不可用，将使用基础下载功能")

        # 启动时检查并清理残留的不完整下载
        self.check_and_cleanup_incomplete_downloads()

        logger.info(f"✅ 增强模型下载器初始化完成 - {self.VERSION}")

    def _clear_internal_state(self):
        """清除内部状态，防止状态污染"""
        logger.info("🔧 清除增强下载器内部状态")
        self._last_model_name = None

        # 强制清除所有可能的状态污染源
        if hasattr(self, '_cached_recommendation'):
            delattr(self, '_cached_recommendation')
        if hasattr(self, '_cached_model_name'):
            delattr(self, '_cached_model_name')
        if hasattr(self, '_last_dialog_model'):
            delattr(self, '_last_dialog_model')

        # 新增：清除跨标签页状态污染源
        if hasattr(self, '_last_tab_context'):
            delattr(self, '_last_tab_context')
        if hasattr(self, '_dialog_context_map'):
            delattr(self, '_dialog_context_map')
        if hasattr(self, '_request_source'):
            delattr(self, '_request_source')

        if self.intelligent_selector:
            # 使用智能选择器的清除缓存方法
            try:
                self.intelligent_selector.clear_cache()
                logger.info("✅ 智能选择器缓存已清除")
            except Exception as e:
                logger.warning(f"⚠️ 清除智能选择器缓存失败: {e}")
                # 回退到重新初始化
                try:
                    from .intelligent_model_selector import IntelligentModelSelector
                    self.intelligent_selector = IntelligentModelSelector()
                    logger.info("✅ 智能选择器已重新初始化")
                except Exception as e2:
                    logger.error(f"❌ 智能选择器重新初始化失败: {e2}")

    def reset_state(self):
        """重置下载器状态，确保状态隔离（公共接口）"""
        logger.info("🔧 重置增强下载器状态")

        # 强制重新加载模块，确保代码修改生效
        self._force_reload_modules()

        self._clear_internal_state()

        # 额外的强制重置措施
        if self.intelligent_selector:
            try:
                # 强制重新初始化智能选择器，确保完全清除状态
                from .intelligent_model_selector import IntelligentModelSelector
                self.intelligent_selector = IntelligentModelSelector()
                logger.info("🔄 智能选择器已强制重新初始化")
            except Exception as e:
                logger.error(f"❌ 智能选择器强制重新初始化失败: {e}")

        logger.info("✅ 增强下载器状态已重置")

    def download_specific_variant(self, model_name: str, variant_info, parent_widget=None):
        """下载指定的模型变体

        Args:
            model_name: 模型名称(如"qwen"或"mistral")
            variant_info: ModelVariantInfo对象
            parent_widget: 父窗口

        Returns:
            bool: 下载是否成功
        """
        try:
            logger.info(f"🚀 开始下载指定变体: {model_name} - {variant_info.name}")

            # TODO: 实现实际的下载逻辑
            # 这里需要调用下载管理器来下载指定的模型文件

            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                parent_widget,
                "下载",
                f"将下载:\n模型: {model_name}\n变体: {variant_info.name}\n大小: {variant_info.size_gb:.1f} GB"
            )

            return True

        except Exception as e:
            logger.error(f"❌ 下载指定变体失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    def _force_reload_modules(self):
        """强制重新加载相关模块，确保代码修改生效"""
        try:
            import sys
            import importlib
            import gc

            logger.info("🔄 开始强制重新加载模块，清除旧版本代码缓存")

            # 需要重新加载的模块列表
            # ⚠️ 重要：不要重新加载enhanced_model_downloader，因为它包含download_worker_process函数
            # 该函数需要被multiprocessing.Process序列化，重新加载会导致pickle错误
            modules_to_reload = [
                # 'src.core.enhanced_model_downloader',  # ❌ 禁止重新加载（包含multiprocessing函数）
                'src.core.intelligent_model_selector',
                'src.ui.enhanced_download_dialog',
                'src.core.dialog_manager'
            ]

            # 强制清除模块缓存
            for module_name in modules_to_reload:
                if module_name in sys.modules:
                    try:
                        # 删除模块引用
                        del sys.modules[module_name]
                        logger.info(f"🗑️ 已删除模块缓存: {module_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除模块缓存失败: {module_name} - {e}")

            # 强制垃圾回收
            gc.collect()

            # 重新导入关键模块
            try:
                from .dialog_manager import DialogManager
                logger.info("✅ DialogManager 重新导入成功")
            except Exception as e:
                logger.error(f"❌ DialogManager 重新导入失败: {e}")

            logger.info("✅ 模块强制重新加载完成")

        except Exception as e:
            logger.error(f"❌ 强制重新加载模块失败: {e}")



    def get_download_status(self) -> Dict[str, Any]:
        """获取下载状态信息

        Returns:
            Dict[str, Any]: 包含下载状态的字典
        """
        try:
            status = {
                "status": "idle",
                "current_download": None,
                "progress": 0.0,
                "speed": 0.0,
                "eta": 0,
                "has_intelligent_selector": self.has_intelligent_selector,
                "last_model": self._last_model_name,
                "timestamp": time.time()
            }

            # 检查当前下载状态
            if self.current_download:
                status["status"] = "downloading"
                status["current_download"] = {
                    "model_name": getattr(self.current_download, 'model_name', 'unknown'),
                    "started_at": getattr(self.current_download, 'started_at', 0)
                }

            # 检查进度对话框状态
            if self.progress_dialog and self.progress_dialog.isVisible():
                status["status"] = "downloading"
                if hasattr(self.progress_dialog, 'value'):
                    status["progress"] = self.progress_dialog.value()

            return status

        except Exception as e:
            logger.error(f"获取下载状态失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }

    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息

        Returns:
            Dict[str, Any]: 包含存储信息的字典
        """
        try:
            import os
            from pathlib import Path

            # 默认模型存储路径
            models_dir = Path("models")
            if not models_dir.exists():
                models_dir.mkdir(parents=True, exist_ok=True)

            # 计算已用空间
            used_space = 0
            model_files = []

            if models_dir.exists():
                for file_path in models_dir.rglob("*"):
                    if file_path.is_file():
                        file_size = file_path.stat().st_size
                        used_space += file_size
                        model_files.append({
                            "name": file_path.name,
                            "path": str(file_path),
                            "size": file_size,
                            "size_gb": file_size / (1024**3)
                        })

            # 获取可用空间
            try:
                disk_usage = os.statvfs(str(models_dir)) if hasattr(os, 'statvfs') else None
                if disk_usage:
                    available_space = disk_usage.f_bavail * disk_usage.f_frsize
                else:
                    # Windows fallback
                    import shutil
                    _, _, available_space = shutil.disk_usage(str(models_dir))
            except Exception:
                available_space = 0

            return {
                "models_dir": str(models_dir.absolute()),
                "used_space_bytes": used_space,
                "used_space_gb": used_space / (1024**3),
                "available_space_bytes": available_space,
                "available_space_gb": available_space / (1024**3),
                "model_files": model_files,
                "total_files": len(model_files),
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"获取存储信息失败: {e}")
            return {
                "error": str(e),
                "models_dir": "models",
                "used_space_gb": 0.0,
                "available_space_gb": 0.0,
                "timestamp": time.time()
            }

    def check_and_cleanup_incomplete_downloads(self):
        """检查并清理残留的不完整下载

        在程序启动时调用，清理上次未完成的下载
        """
        try:
            logger.info("🔍 检查残留的不完整下载...")

            models_dir = Path("models")
            if not models_dir.exists():
                logger.info("模型目录不存在，无需清理")
                return

            cleaned_count = 0

            # 遍历所有下载配置
            for model_name, config in self.download_configs.items():
                target_dir = Path(config['target_dir'])

                if not target_dir.exists():
                    continue

                # 检查每个文件
                for file_info in config['files']:
                    file_path = target_dir / file_info['name']

                    if file_path.exists():
                        expected_size = file_info.get('size', 0)
                        actual_size = file_path.stat().st_size

                        # 如果文件不完整（大小差异超过5%），删除它
                        if expected_size > 0 and abs(actual_size - expected_size) > expected_size * 0.05:
                            try:
                                file_path.unlink()
                                cleaned_count += 1
                                logger.info(f"已清理残留文件: {file_path.name} (期望={expected_size}, 实际={actual_size})")
                            except Exception as e:
                                logger.error(f"清理残留文件失败: {file_path}, 错误: {e}")

                # 清理临时文件
                for temp_file in target_dir.glob("*.tmp"):
                    try:
                        temp_file.unlink()
                        cleaned_count += 1
                        logger.info(f"已清理临时文件: {temp_file.name}")
                    except Exception as e:
                        logger.error(f"清理临时文件失败: {temp_file}, 错误: {e}")

                for part_file in target_dir.glob("*.part"):
                    try:
                        part_file.unlink()
                        cleaned_count += 1
                        logger.info(f"已清理临时文件: {part_file.name}")
                    except Exception as e:
                        logger.error(f"清理临时文件失败: {part_file}, 错误: {e}")

                # 如果目录为空，删除目录
                if target_dir.exists() and not any(target_dir.iterdir()):
                    try:
                        target_dir.rmdir()
                        logger.info(f"已删除空目录: {target_dir}")
                    except Exception as e:
                        logger.error(f"删除空目录失败: {target_dir}, 错误: {e}")

            if cleaned_count > 0:
                logger.info(f"✅ 清理完成，共清理 {cleaned_count} 个残留文件")
            else:
                logger.info("✅ 没有发现残留文件")

        except Exception as e:
            logger.error(f"检查残留下载失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")

    def get_available_models(self) -> List[str]:
        """获取可用模型列表

        Returns:
            List[str]: 可用模型名称列表
        """
        try:
            # 从下载配置中获取支持的模型
            available_models = list(self.download_configs.keys())

            # 如果有智能选择器，也从中获取支持的模型
            if self.intelligent_selector:
                try:
                    from .intelligent_model_selector import IntelligentModelSelector
                    # 支持的模型列表（Qwen3和Mistral系列）
                    selector_models = [
                        "qwen3-0.6b", "qwen3-1.7b", "qwen3-8b", "qwen3-32b",
                        "mistral-7b", "mistral-12b-nemo", "mistral-24b-small", "mistral-large2"
                    ]
                    available_models.extend(selector_models)
                except Exception as e:
                    logger.debug(f"从智能选择器获取模型列表失败: {e}")

            # 去重并排序
            available_models = sorted(list(set(available_models)))

            return available_models

        except Exception as e:
            logger.error(f"获取可用模型列表失败: {e}")
            # 返回默认支持的模型（Qwen3和Mistral系列）
            return ["qwen3-0.6b", "qwen3-1.7b", "qwen3-8b", "qwen3-32b",
                    "mistral-7b", "mistral-12b-nemo", "mistral-24b-small", "mistral-large2"]

    def _load_download_configs(self) -> Dict:
        """
        加载下载配置（已废弃 - 仅作为回退方案）

        注意：此配置仅在智能推荐系统不可用时使用。
        实际下载应通过IntelligentModelSelector自动选择合适的模型变体。

        所有模型现在都使用snapshot_download方式，配置从YAML文件动态加载。
        """
        logger.warning("⚠️ 使用回退下载配置，建议启用智能推荐系统")

        # 返回空配置，强制使用智能推荐系统
        # 如果智能推荐系统不可用，将在download_model中显示错误
        return {}
    
    def download_model(self, model_name: str, parent_widget=None, auto_select: bool = True, tab_context: str = None) -> bool:
        """下载指定模型（支持智能版本选择）"""
        logger.info(f"🚀 开始下载模型: {model_name}, auto_select={auto_select}, 标签页上下文: {tab_context}")
        logger.info(f"🔧 智能选择器状态: {self.has_intelligent_selector}")

        # 重要修复：检查模型名称变化，如果变化则清除状态
        if self._last_model_name and self._last_model_name != model_name:
            logger.info(f"🔄 检测到模型名称变化: {self._last_model_name} -> {model_name}，清除状态")
            self._clear_internal_state()

        # 新增：检查标签页上下文变化
        current_tab_context = tab_context or "unknown"
        if hasattr(self, '_last_tab_context') and self._last_tab_context != current_tab_context:
            logger.info(f"🔄 检测到标签页上下文变化: {self._last_tab_context} -> {current_tab_context}，清除状态")
            self._clear_internal_state()

        # 存储当前标签页上下文
        self._current_tab_context = current_tab_context
        self._last_tab_context = current_tab_context

        # 记录当前模型名称和标签页上下文
        self._last_model_name = model_name
        self._last_tab_context = current_tab_context

        # 额外验证：确保智能选择器状态与当前请求一致
        if self.intelligent_selector and hasattr(self.intelligent_selector, '_last_model_name'):
            if self.intelligent_selector._last_model_name and self.intelligent_selector._last_model_name != model_name:
                logger.info(f"🔄 智能选择器状态不一致，强制清除: {self.intelligent_selector._last_model_name} -> {model_name}")
                self.intelligent_selector.clear_cache()

        if auto_select and self.has_intelligent_selector:
            logger.info("✅ 使用智能下载模式")
            return self._intelligent_download(model_name, parent_widget, tab_context)
        else:
            logger.info("⚠️ 使用基础下载模式")
            return self._basic_download(model_name, parent_widget)

    def _intelligent_download(self, model_name: str, parent_widget=None, tab_context: str = None) -> bool:
        """智能下载（自动选择最佳版本）"""
        logger.info(f"🤖 开始智能下载: {model_name}, 标签页上下文: {tab_context}")

        try:
            from .intelligent_model_selector import SelectionStrategy, DeploymentTarget
            logger.info("✅ 智能选择器模块导入成功")

            # 强制刷新硬件配置以确保检测到最新的硬件状态
            logger.info("🔄 强制刷新硬件配置...")
            self.intelligent_selector.force_refresh_hardware()

            # 获取智能推荐（传递标签页上下文）
            logger.info("🔍 正在获取智能推荐...")
            recommendation = self.intelligent_selector.recommend_model_version(
                model_name=model_name,
                strategy=SelectionStrategy.AUTO_RECOMMEND,
                tab_context=tab_context
            )

            if recommendation:
                # 检查是否因硬件不足而无法推荐任何变体
                if recommendation.variant is None:
                    logger.warning(f"⚠️ 设备硬件不足，无法推荐 {model_name} 的任何变体")
                    logger.warning(f"   推荐理由: {recommendation.reasoning}")

                    # 显示硬件不足的智能推荐对话框（不允许下载）
                    logger.info("🎨 准备显示硬件不足的推荐对话框...")
                    return self._show_hardware_insufficient_dialog(recommendation, parent_widget)

                # 🔧 修复：验证推荐结果与请求的模型系列一致性
                # 通用名称(qwen/mistral)会被智能推荐系统转换为具体模型名称(qwen3-0.6b/mistral-7b)
                # 这是正常的,不应该视为错误
                requested_series = model_name.lower().replace("-", "").replace("_", "")
                recommended_series = recommendation.model_name.lower().replace("-", "").replace("_", "")

                # 检查是否属于同一系列
                is_same_series = False
                if "qwen" in requested_series and "qwen" in recommended_series:
                    is_same_series = True
                elif "mistral" in requested_series and "mistral" in recommended_series:
                    is_same_series = True
                elif requested_series == recommended_series:
                    is_same_series = True

                if not is_same_series:
                    logger.error(f"❌ 推荐结果模型系列不一致: 请求={model_name}, 推荐={recommendation.model_name}")
                    logger.error(f"   这可能是智能推荐系统的bug,回退到基础下载")
                    return self._basic_download(model_name, parent_widget)

                # 记录推荐详情
                logger.info(f"✅ 获取推荐成功:")
                logger.info(f"  请求模型: {model_name}")
                logger.info(f"  推荐模型: {recommendation.model_name}")
                logger.info(f"  变体: {recommendation.variant.name}")
                logger.info(f"  量化: {recommendation.variant.quantization.value}")
                logger.info(f"  大小: {recommendation.variant.size_gb:.1f}GB")
                logger.info(f"  质量保持: {recommendation.variant.quality_retention:.1%}")

                # 显示推荐对话框
                logger.info("🎨 准备显示推荐对话框...")
                return self._show_recommendation_dialog(recommendation, parent_widget)
            else:
                logger.warning(f"⚠️ 无法获取 {model_name} 的智能推荐，回退到基础下载")
                return self._basic_download(model_name, parent_widget)

        except Exception as e:
            logger.error(f"❌ 智能下载失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return self._basic_download(model_name, parent_widget)

    def _basic_download(self, model_name: str, parent_widget=None, skip_confirmation: bool = False) -> bool:
        """基础下载（原有逻辑）

        Args:
            model_name: 模型名称
            parent_widget: 父窗口
            skip_confirmation: 是否跳过确认对话框（智能下载时为True）
        """
        if model_name not in self.download_configs:
            QMessageBox.critical(parent_widget, "错误", f"未知模型: {model_name}")
            return False

        config = self.download_configs[model_name]

        # 如果不跳过确认，显示确认对话框
        if not skip_confirmation:
            total_size_gb = config['total_size'] / (1024**3)
            reply = QMessageBox.question(
                parent_widget,
                "确认下载",
                f"即将下载 {config['name']}\n\n"
                f"描述: {config['description']}\n"
                f"大小: {total_size_gb:.1f} GB\n"
                f"文件数量: {len(config['files'])} 个\n\n"
                f"下载可能需要较长时间，确认继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                logger.info("ℹ️ 用户取消基础下载确认")
                return None
        else:
            logger.info(f"📥 准备下载（跳过确认）: {config['name']}")
        
        # 创建增强的进度对话框
        self.progress_dialog = EnhancedProgressDialog(
            f"下载 {config['name']}...",
            parent_widget
        )
        self.progress_dialog.show()

        # 创建下载线程
        self.current_download = ModelDownloadThread(model_name, config, self)

        # 连接信号
        self.current_download.progress_updated.connect(self._on_progress_updated)
        self.current_download.enhanced_progress_updated.connect(self._on_enhanced_progress_updated)
        self.current_download.download_completed.connect(self._on_download_completed)
        self.current_download.error_occurred.connect(self._on_error_occurred)
        self.progress_dialog.canceled.connect(self.current_download.cancel_download)
        
        # 开始下载
        self.current_download.start()
        
        return True
    
    def _on_progress_updated(self, progress: int, status: str):
        """更新进度（旧版信号，向后兼容）"""
        if self.progress_dialog and not isinstance(self.progress_dialog, EnhancedProgressDialog):
            self.progress_dialog.setValue(progress)
            self.progress_dialog.setLabelText(status)

    def _on_enhanced_progress_updated(self, progress: int, downloaded_mb: float,
                                     total_mb: float, speed_mb: float,
                                     eta_seconds: int, filename: str):
        """更新增强的进度信息"""
        if self.progress_dialog and isinstance(self.progress_dialog, EnhancedProgressDialog):
            self.progress_dialog.update_enhanced_progress(
                progress, downloaded_mb, total_mb, speed_mb, eta_seconds, filename
            )
    
    def _on_download_completed(self, model_name: str, success: bool):
        """下载完成"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        if success:
            QMessageBox.information(
                None,
                "下载完成",
                f"{self.download_configs[model_name]['name']} 下载完成！\n\n"
                f"模型已安装到: {self.download_configs[model_name]['target_dir']}\n"
                f"程序将自动切换到真实AI模式。"
            )
            logger.info(f"模型下载成功: {model_name}")
        else:
            QMessageBox.critical(
                None,
                "下载失败",
                f"{self.download_configs[model_name]['name']} 下载失败！\n\n"
                f"请检查网络连接并重试。"
            )
            logger.error(f"模型下载失败: {model_name}")
        
        self.current_download = None
    
    def _on_error_occurred(self, error_type: str, error_message: str):
        """处理下载错误"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # 显示重试对话框
        reply = QMessageBox.critical(
            None,
            f"下载错误: {error_type}",
            f"下载过程中发生错误:\n{error_message}\n\n是否重试？",
            QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Retry
        )
        
        if reply == QMessageBox.StandardButton.Retry and self.current_download:
            # 重新开始下载
            model_name = self.current_download.model_name
            self.current_download = None
            self.download_model(model_name)
        else:
            self.current_download = None

    def _show_hardware_insufficient_dialog(self, recommendation, parent_widget) -> bool:
        """显示硬件不足的智能推荐对话框（不允许下载）"""
        logger.info(f"🎨 显示硬件不足对话框: {recommendation.model_name}")

        try:
            # 导入超快速智能推荐对话框
            from src.ui.ultrafast_smart_downloader_dialog import UltraFastSmartDownloaderDialog

            # 创建对话框
            dialog = UltraFastSmartDownloaderDialog(recommendation.model_name, parent_widget)

            # 显示对话框（对话框内部会检测到recommendation.variant为None并显示硬件不足信息）
            result = dialog.exec()

            # 硬件不足时，无论用户点击什么都返回False（不允许下载）
            logger.info(f"⚠️ 硬件不足对话框关闭，不允许下载")
            return False

        except Exception as e:
            logger.error(f"❌ 显示硬件不足对话框失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")

            # 回退到简单的消息框
            from PyQt6.QtWidgets import QMessageBox
            msg = "⚠️ 设备硬件不足，无法运行此模型\n\n"
            msg += "\n".join(recommendation.reasoning)
            msg += "\n\n解决方案:\n"
            msg += "\n".join(recommendation.deployment_notes)

            QMessageBox.warning(
                parent_widget,
                "硬件不足",
                msg
            )
            return False

    def _show_recommendation_dialog(self, recommendation, parent_widget) -> bool:
        """显示智能推荐对话框 - 架构重构版本 v4.0 - 20250905"""
        # 版本标识符 - 确保新代码被执行
        version_id = "ARCH_REBUILD_v4.0_20250905_FINAL"
        logger.info(f"🎨 开始显示智能推荐对话框 - {version_id}")

        # 完全移除旧的防重复弹窗逻辑，使用新的DialogManager
        try:
            # 导入DialogManager（每次都重新导入，避免缓存问题）
            import importlib
            import sys

            # 强制重新加载DialogManager模块
            dialog_manager_module_name = 'src.core.dialog_manager'
            if dialog_manager_module_name in sys.modules:
                importlib.reload(sys.modules[dialog_manager_module_name])

            from .dialog_manager import DialogManager
            dialog_manager = DialogManager.get_instance()

            # 获取标签页上下文
            tab_context = getattr(self, '_current_tab_context', 'unknown')
            logger.info(f"🔍 {version_id} - 检查对话框权限: model={recommendation.model_name}, tab={tab_context}")

            # 检查是否可以显示对话框
            if not dialog_manager.can_show_dialog(recommendation.model_name, parent_widget, tab_context):
                logger.info(f"⚠️ {version_id} - DialogManager阻止在 {tab_context} 中重复弹窗 {recommendation.model_name}")
                return False

            # 直接在主线程中创建对话框
            logger.info(f"✅ {version_id} - 在主线程中创建对话框")
            result = self._create_dialog_sync(recommendation, parent_widget, tab_context)

            # 通知对话框管理器对话框已关闭
            dialog_manager.mark_dialog_closed(
                recommendation.model_name,
                tab_context,
                'success' if result else 'cancelled'
            )

            logger.info(f"✅ {version_id} - 对话框处理完成: result={result}")
            return result

        except Exception as e:
            logger.error(f"❌ {version_id} - 对话框显示失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    def _create_dialog_sync(self, recommendation, parent_widget, tab_context: str = None) -> bool:
        """同步创建对话框（确保在主线程中执行）"""
        try:
            # 🔧 修复：导入重构后的智能推荐对话框
            import sys
            import os
            from pathlib import Path

            # 确保项目根目录在sys.path中
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            project_root_str = str(project_root)
            if project_root_str not in sys.path:
                sys.path.insert(0, project_root_str)
                logger.info(f"✅ 添加项目根路径: {project_root_str}")

            # 🔧 根本性重构：导入超快速智能推荐对话框
            # 旧版本: EnhancedSmartDownloaderDialog
            # 新版本: UltraFastSmartDownloaderDialog (根本性重构后的智能推荐对话框)
            UltraFastSmartDownloaderDialog = None
            import_errors = []

            # 方式1: 从src.ui导入
            try:
                from src.ui.ultrafast_smart_downloader_dialog import UltraFastSmartDownloaderDialog
                logger.info("✅ 超快速智能推荐对话框导入成功 (src.ui路径)")
            except ImportError as e:
                import_errors.append(f"src.ui: {str(e)}")
                logger.warning(f"⚠️ src.ui路径导入失败: {e}")

                # 方式2: 从ui导入
                try:
                    from ui.ultrafast_smart_downloader_dialog import UltraFastSmartDownloaderDialog
                    logger.info("✅ 超快速智能推荐对话框导入成功 (ui路径)")
                except ImportError as e2:
                    import_errors.append(f"ui: {str(e2)}")
                    logger.warning(f"⚠️ ui路径导入失败: {e2}")

                    # 方式3: 使用绝对路径动态导入
                    try:
                        dialog_path = current_file.parent.parent / "ui" / "ultrafast_smart_downloader_dialog.py"
                        logger.info(f"📁 尝试绝对路径导入: {dialog_path}")
                        logger.info(f"📁 文件存在: {dialog_path.exists()}")

                        if not dialog_path.exists():
                            raise ImportError(f"对话框文件不存在: {dialog_path}")

                        import importlib.util
                        spec = importlib.util.spec_from_file_location("ultrafast_smart_downloader_dialog", str(dialog_path))
                        if not spec or not spec.loader:
                            raise ImportError("无法创建模块规范")

                        dialog_module = importlib.util.module_from_spec(spec)
                        sys.modules['ultrafast_smart_downloader_dialog'] = dialog_module
                        spec.loader.exec_module(dialog_module)
                        UltraFastSmartDownloaderDialog = dialog_module.UltraFastSmartDownloaderDialog
                        logger.info("✅ 超快速智能推荐对话框导入成功 (绝对路径)")
                    except Exception as e3:
                        import_errors.append(f"absolute: {str(e3)}")
                        logger.error(f"❌ 绝对路径导入失败: {e3}")

            # 如果所有导入方式都失败，抛出详细错误
            if UltraFastSmartDownloaderDialog is None:
                error_msg = "所有导入方式都失败:\n" + "\n".join(f"  - {err}" for err in import_errors)
                logger.error(f"❌ {error_msg}")
                raise ImportError(error_msg)

            # 创建超快速智能推荐对话框
            # 🔧 修复：UltraFastSmartDownloaderDialog只接受model_name和parent两个参数
            logger.info(f"🔧 创建超快速智能推荐对话框: model={recommendation.model_name}, variant={recommendation.variant.name}, context={tab_context}")
            dialog = UltraFastSmartDownloaderDialog(
                model_name=recommendation.model_name,
                parent=parent_widget
            )
            logger.info("✅ 智能推荐对话框创建成功")

            # 连接下载请求信号
            download_result = {'success': False, 'variant_info': None}

            def on_download_requested(model_name, variant_info):
                """处理下载请求信号"""
                logger.info(f"📥 收到下载请求信号: {model_name} - {variant_info.name}")
                download_result['success'] = True
                download_result['variant_info'] = variant_info

            dialog.download_requested.connect(on_download_requested)
            logger.info("✅ 下载请求信号已连接")

            # 设置对话框实例引用，用于防重复检查
            # 🔧 修复：检查parent_widget是否为None
            if parent_widget is not None:
                parent_widget._dialog_instance = dialog
            else:
                logger.warning("⚠️ parent_widget为None，跳过设置_dialog_instance")

            # 显示对话框 - 使用线程安全的方式
            logger.info("🎭 显示对话框...")

            # 确保在主线程中执行对话框
            try:
                from PyQt6.QtCore import QTimer, QEventLoop
                from PyQt6.QtWidgets import QApplication

                # 检查是否在主线程中
                if QApplication.instance() and QApplication.instance().thread() != dialog.thread():
                    logger.warning("⚠️ 对话框不在主线程中，尝试移动到主线程")
                    dialog.moveToThread(QApplication.instance().thread())

                # 使用事件循环确保线程安全
                result = dialog.exec()
                logger.info(f"📋 对话框结果: {result}")

            except Exception as thread_error:
                logger.error(f"❌ 线程安全处理失败: {thread_error}")
                # 回退到基本显示方式
                result = dialog.exec()
                logger.info(f"📋 对话框结果 (回退): {result}")

            # 安全清除对话框实例引用
            try:
                if hasattr(parent_widget, '_dialog_instance'):
                    parent_widget._dialog_instance = None
                    logger.info("🔧 安全清除对话框实例引用")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 清理对话框实例时出错: {cleanup_error}")

            # 检查是否收到下载请求信号
            if download_result['success'] and download_result['variant_info']:
                variant_info = download_result['variant_info']
                logger.info(f"✅ 处理下载请求: {variant_info.name}")

                # 构造selected_variant对象
                selected_variant = {
                    'variant': type('Variant', (), {
                        'name': variant_info.name,
                        'quantization': type('Quantization', (), {'value': variant_info.quantization})(),
                        'size_gb': variant_info.size_gb,
                        'memory_requirement_gb': variant_info.memory_requirement_gb,
                        'quality_retention': variant_info.quality_retention,
                        'inference_speed_relative': variant_info.inference_speed_relative
                    })()
                }

                # 用户确认下载选中版本
                return self._download_selected_variant(selected_variant, recommendation.model_name, parent_widget)

            elif result == dialog.DialogCode.Accepted:
                # 兼容旧的处理方式（如果信号没有触发）
                selected_variant = dialog.get_selected_variant()
                if selected_variant:
                    logger.info(f"✅ 用户选择版本（兼容模式）: {selected_variant.get('variant', {}).get('name', 'Unknown')}")
                    return self._download_selected_variant(selected_variant, recommendation.model_name, parent_widget)
                else:
                    logger.warning("⚠️ 用户未选择版本")
            else:
                logger.info("ℹ️ 用户取消下载")

            # 用户取消时返回特殊值 None，而不是 False
            # False 表示下载失败，None 表示用户取消
            return None

        except ImportError as e:
            # 🔧 修复：详细记录导入失败原因
            logger.error(f"❌ 增强对话框导入失败: {e}")
            import traceback
            logger.error(f"导入失败详细信息:\n{traceback.format_exc()}")
            logger.error(f"当前sys.path: {sys.path[:5]}")  # 只显示前5个路径
            logger.error(f"当前工作目录: {os.getcwd()}")

            # 移除基础推荐对话框回退，避免多重弹窗
            # 直接显示错误提示并返回
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                parent_widget,
                "对话框加载失败",
                f"无法加载智能推荐对话框。\n\n"
                f"错误: {str(e)}\n\n"
                f"请检查程序安装是否完整，或联系技术支持。"
            )
            return False

        except Exception as e:
            logger.error(f"❌ 显示推荐对话框失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")

            # 移除基础推荐对话框回退，避免多重弹窗
            # 直接显示错误提示并返回
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                parent_widget,
                "对话框显示失败",
                f"智能推荐对话框显示失败。\n\n"
                f"错误: {str(e)}\n\n"
                f"请重试或联系技术支持。"
            )
            return False
        finally:
            # 确保清理对话框相关状态 - 增强版本
            # 🔧 修复：检查parent_widget是否为None
            try:
                if parent_widget is not None and hasattr(parent_widget, '_dialog_instance'):
                    dialog_instance = getattr(parent_widget, '_dialog_instance', None)
                    if dialog_instance:
                        # 安全关闭对话框
                        try:
                            if hasattr(dialog_instance, 'close'):
                                dialog_instance.close()
                            if hasattr(dialog_instance, 'deleteLater'):
                                dialog_instance.deleteLater()
                        except Exception as close_error:
                            logger.warning(f"⚠️ 关闭对话框时出错: {close_error}")

                    parent_widget._dialog_instance = None
                    logger.info("🔧 清除对话框实例引用")

                if parent_widget is not None and hasattr(parent_widget, '_global_model_dialog_showing'):
                    parent_widget._global_model_dialog_showing = False
                    logger.info("🔧 清除对话框显示标志位")

                # 强制垃圾回收
                import gc
                gc.collect()
                logger.info("🔧 执行垃圾回收")

            except Exception as cleanup_error:
                logger.error(f"❌ 最终清理时出错: {cleanup_error}")
                # 即使清理失败，也要确保标志位被重置
                try:
                    if hasattr(parent_widget, '_global_model_dialog_showing'):
                        parent_widget._global_model_dialog_showing = False
                except:
                    pass

    def _show_alternatives_dialog(self, recommendation, parent_dialog):
        """显示替代选项对话框"""
        # 这里可以实现显示所有可选版本的对话框
        # 暂时简化为消息框
        alternatives_text = "可选版本:\n\n"
        for i, alt in enumerate(recommendation.alternative_options[:3], 1):
            if hasattr(alt, 'variant'):
                variant = alt['variant']
                alternatives_text += f"{i}. {variant.name} ({variant.size_gb:.1f}GB)\n"
                alternatives_text += f"   理由: {alt.get('reason', '无')}\n\n"

        QMessageBox.information(parent_dialog, "其他选项", alternatives_text)

    def _download_recommended_variant(self, recommendation, parent_widget) -> bool:
        """下载推荐的变体（从配置文件读取真实URL）"""
        variant = recommendation.variant
        model_name = recommendation.model_name

        # 从配置文件读取下载URL
        download_url = self._get_variant_download_url(model_name, variant.quantization.value)

        if not download_url or download_url.startswith("https://example.com"):
            logger.error(f"无法获取有效的下载URL: {model_name} - {variant.quantization.value}")
            QMessageBox.critical(
                parent_widget,
                "下载错误",
                f"无法获取模型下载URL。\n\n"
                f"模型: {model_name}\n"
                f"量化类型: {variant.quantization.value}\n\n"
                f"请检查配置文件或联系技术支持。"
            )
            return False

        # 创建下载配置（使用HuggingFace格式的.safetensors文件）
        temp_config = {
            'name': variant.name,
            'description': f"智能推荐版本 - {variant.quantization.value} (HuggingFace格式)",
            'total_size': int(variant.size_gb * 1024**3),
            'target_dir': f"models/{model_name}/{variant.quantization.value}",
            'files': [
                {
                    'name': "model.safetensors",  # HuggingFace标准格式（可能带量化）
                    'url': download_url,
                    'size': int(variant.size_gb * 1024**3)
                },
                {
                    'name': "config.json",
                    'url': download_url.replace("/resolve/main/model.safetensors", "/resolve/main/config.json"),
                    'size': 1024
                },
                {
                    'name': "tokenizer.json",
                    'url': download_url.replace("/resolve/main/model.safetensors", "/resolve/main/tokenizer.json"),
                    'size': 2048
                }
            ]
        }

        # 使用基础下载逻辑
        return self._execute_download(temp_config, parent_widget)

    def _show_basic_recommendation_dialog(self, recommendation, parent_widget) -> bool:
        """显示基础推荐对话框（回退方案）"""
        from PyQt6.QtWidgets import QMessageBox

        variant = recommendation.variant

        # 创建详细的推荐信息
        message = f"""🤖 智能推荐版本

📋 推荐版本: {variant.name}
📊 大小: {variant.size_gb:.1f} GB
💾 内存需求: {variant.memory_requirement_gb:.1f} GB
🎯 质量保持: {variant.quality_retention:.1%}
⚡ 推理速度: {variant.inference_speed_factor:.1%}
🖥️ CPU兼容: {'是' if variant.cpu_compatible else '否'}
🔧 置信度: {recommendation.confidence_score:.1%}

💡 推荐理由:
{chr(10).join(f"• {reason}" for reason in recommendation.reasoning[:3])}

确认下载此版本？"""

        reply = QMessageBox.question(
            parent_widget,
            "智能模型推荐",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            return self._download_recommended_variant(recommendation, parent_widget)

        # 用户取消基础推荐对话框时也返回 None
        logger.info("ℹ️ 用户取消基础推荐对话框")
        return None

    def _download_selected_variant(self, selected_variant: Dict, model_name: str, parent_widget) -> bool:
        """下载用户选中的变体（优先使用snapshot_download）"""
        variant = selected_variant.get('variant')
        if not variant:
            return False

        # 🔧 新增：首先尝试从配置文件获取repo_id和镜像源配置
        repo_id, use_snapshot, mirror_sources = self._get_repo_id_from_config(model_name)

        if use_snapshot and repo_id and HF_HUB_AVAILABLE:
            logger.info(f"✅ 使用snapshot_download下载: {repo_id}")

            # 创建下载配置（snapshot模式）
            download_config = {
                'name': variant.name,
                'description': f"用户选择版本 - {variant.quantization.value} (snapshot_download)",
                'total_size': int(variant.size_gb * 1024**3),
                'target_dir': f"models/{model_name}/{variant.quantization.value}",
                'use_snapshot_download': True,
                'repo_id': repo_id,
                'mirror_sources': mirror_sources,  # 🔧 新增：传递镜像源配置
                'files': []  # snapshot_download不需要files列表
            }

            return self._execute_download(download_config, parent_widget)

        # 回退到传统HTTP下载方式
        logger.info(f"⚠️ 使用传统HTTP下载方式（snapshot_download不可用）")

        # 从配置文件读取下载URL
        download_url = self._get_variant_download_url(model_name, variant.quantization.value)

        if not download_url or download_url.startswith("https://example.com"):
            logger.error(f"无法获取有效的下载URL: {model_name} - {variant.quantization.value}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                parent_widget,
                "下载错误",
                f"无法获取模型下载URL。\n\n"
                f"模型: {model_name}\n"
                f"量化类型: {variant.quantization.value}\n\n"
                f"请检查配置文件或联系技术支持。"
            )
            return False

        # 创建下载配置（使用HuggingFace格式的.safetensors文件）
        download_config = {
            'name': variant.name,
            'description': f"用户选择版本 - {variant.quantization.value} (HuggingFace格式)",
            'total_size': int(variant.size_gb * 1024**3),
            'target_dir': f"models/{model_name}/{variant.quantization.value}",
            'files': [
                {
                    'name': "model.safetensors",  # HuggingFace标准格式（可能带量化）
                    'url': download_url,
                    'size': int(variant.size_gb * 1024**3)
                },
                {
                    'name': "config.json",
                    'url': download_url.replace("/resolve/main/model.safetensors", "/resolve/main/config.json"),
                    'size': 1024
                },
                {
                    'name': "tokenizer.json",
                    'url': download_url.replace("/resolve/main/model.safetensors", "/resolve/main/tokenizer.json"),
                    'size': 2048
                }
            ]
        }

        return self._execute_download(download_config, parent_widget)

    def _get_repo_id_from_config(self, model_name: str) -> tuple[str, bool, list]:
        """从配置文件获取HuggingFace repo_id、是否使用snapshot_download和镜像源配置

        Returns:
            tuple: (repo_id, use_snapshot_download, mirror_sources)
        """
        try:
            # 尝试多个可能的配置文件名
            possible_filenames = [
                f"{model_name}.yaml",
                f"{model_name}-zh.yaml",
                f"{model_name}-en.yaml",
            ]

            config_file = None
            for filename in possible_filenames:
                test_path = Path(f"configs/models/available_models/{filename}")
                if test_path.exists():
                    config_file = test_path
                    break

            if not config_file:
                logger.warning(f"配置文件不存在: {model_name}")
                return None, False, None

            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 获取repo_id和use_snapshot_download配置
            model_config = config.get('model', {})
            download_config = config.get('download', {})

            repo_id = model_config.get('hf_model_id')
            use_snapshot = download_config.get('use_snapshot_download', False)

            # 🔧 新增：读取source_priority配置
            source_priority = download_config.get('source_priority', ['hf_mirror', 'modelscope', 'huggingface'])

            # 构建镜像源列表
            mirror_sources = []
            source_map = {
                'hf_mirror': {
                    'name': 'HF-Mirror（国内高速镜像）',
                    'endpoint': 'https://hf-mirror.com',
                    'url_key': 'hf_mirror_url'
                },
                'modelscope': {
                    'name': 'ModelScope（阿里云镜像）',
                    'endpoint': 'https://www.modelscope.cn',
                    'url_key': 'modelscope_url'
                },
                'huggingface': {
                    'name': 'HuggingFace官方',
                    'endpoint': None,  # None表示使用官方源
                    'url_key': 'hf_url'
                }
            }

            for source_key in source_priority:
                if source_key in source_map:
                    source_info = source_map[source_key]
                    # 验证URL是否存在
                    if source_info['url_key'] in download_config:
                        mirror_sources.append({
                            'name': source_info['name'],
                            'endpoint': source_info['endpoint']
                        })

            logger.info(f"📋 配置: repo_id={repo_id}, use_snapshot={use_snapshot}, sources={len(mirror_sources)}个")
            return repo_id, use_snapshot, mirror_sources

        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            return None, False, None

    def _get_variant_download_url(self, model_name: str, quantization_type: str) -> str:
        """从配置文件获取变体的下载URL（HuggingFace格式）"""
        try:
            # 尝试多个可能的配置文件名
            possible_filenames = [
                f"{model_name}.yaml",  # 例如：qwen3-1.7b.yaml
                f"{model_name}-zh.yaml",  # 例如：qwen3-1.7b-zh.yaml
                f"{model_name}-en.yaml",  # 例如：mistral-7b-en.yaml
            ]

            config_file = None
            for filename in possible_filenames:
                test_path = Path(f"configs/models/available_models/{filename}")
                if test_path.exists():
                    config_file = test_path
                    logger.info(f"找到配置文件: {config_file}")
                    break

            if not config_file:
                logger.error(f"配置文件不存在: {model_name} (尝试了 {possible_filenames})")
                return None

            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 获取量化变体配置
            variants = config.get('quantization_variants', {})

            # 查找匹配的量化类型
            for variant_key, variant_config in variants.items():
                if variant_config.get('quantization_type') == quantization_type:
                    download_url = variant_config.get('download_url')
                    if download_url:
                        # 确保URL指向.safetensors文件
                        if not download_url.endswith('/model.safetensors'):
                            download_url = f"{download_url}/resolve/main/model.safetensors"
                        logger.info(f"找到下载URL: {model_name} - {quantization_type} -> {download_url}")
                        return download_url

            # 如果没有找到，尝试从download配置中获取
            download_config = config.get('download', {})
            quantized_versions = download_config.get('quantized_versions', {})

            # 映射量化类型到配置键
            quant_key_mapping = {
                'int8': 'int8_128',
                'int4': 'int4_128',
                'int8_perchannel': 'int8_perchannel',
                'int4_perchannel': 'int4_perchannel',
                'fp16': 'fp16'
            }

            config_key = quant_key_mapping.get(quantization_type, quantization_type)
            base_url = quantized_versions.get(config_key)

            if base_url:
                # 🔧 修复：优先使用HuggingFace URL（支持/resolve/main/格式）
                # ModelScope不支持/resolve/main/格式，会返回404错误
                hf_url = download_config.get('hf_url')
                hf_mirror_url = download_config.get('hf_mirror_url')

                # 优先级：HF-Mirror > HuggingFace > ModelScope
                if hf_mirror_url:
                    download_url = f"{hf_mirror_url}/resolve/main/model.safetensors"
                    logger.info(f"✅ 使用HF-Mirror URL: {model_name} - {quantization_type} -> {download_url}")
                    return download_url
                elif hf_url:
                    download_url = f"{hf_url}/resolve/main/model.safetensors"
                    logger.info(f"✅ 使用HuggingFace URL: {model_name} - {quantization_type} -> {download_url}")
                    return download_url
                else:
                    # ModelScope不支持/resolve/main/格式，返回None
                    logger.warning(f"⚠️ ModelScope URL不支持直接文件下载，请配置HuggingFace URL: {base_url}")
                    return None

            logger.warning(f"未找到下载URL: {model_name} - {quantization_type}")
            return None

        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None

    def _get_download_url(self, model_name: str, quantization_type: str) -> str:
        """获取下载URL（已弃用，使用_get_variant_download_url代替）"""
        logger.warning("_get_download_url已弃用，请使用_get_variant_download_url")
        return self._get_variant_download_url(model_name, quantization_type)

    def _execute_download(self, config: Dict, parent_widget) -> bool:
        """执行实际下载"""
        # 创建进度对话框
        self.progress_dialog = QProgressDialog(
            f"下载 {config['name']}...",
            "取消",
            0, 100,
            parent_widget
        )
        self.progress_dialog.setWindowTitle("模型下载")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()

        # 创建下载线程
        self.current_download = ModelDownloadThread(config['name'], config, self)

        # 连接信号
        self.current_download.progress_updated.connect(self._on_progress_updated)
        self.current_download.download_completed.connect(self._on_download_completed)
        self.current_download.error_occurred.connect(self._on_error_occurred)
        self.progress_dialog.canceled.connect(self.current_download.cancel_download)

        # 开始下载
        self.current_download.start()

        return True
