#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 增强模型下载器
实现真实有效的模型下载功能，包括进度显示、错误处理和断点续传
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

# 配置日志
logger = logging.getLogger(__name__)

class ModelDownloadThread(QThread):
    """模型下载线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度百分比, 状态信息
    download_completed = pyqtSignal(str, bool)  # 模型名称, 是否成功
    error_occurred = pyqtSignal(str, str)  # 错误类型, 错误信息
    
    def __init__(self, model_name: str, download_config: Dict, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.download_config = download_config
        self.is_cancelled = False
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'VisionAI-ClipsMaster/1.0 (Model Downloader)',
            'Accept': 'application/octet-stream, */*',
            'Accept-Encoding': 'gzip, deflate'
        })
    
    def cancel_download(self):
        """取消下载"""
        self.is_cancelled = True
        logger.info(f"用户取消下载: {self.model_name}")
    
    def run(self):
        """执行下载"""
        try:
            logger.info(f"开始下载模型: {self.model_name}")
            self.progress_updated.emit(0, f"准备下载 {self.model_name}...")
            
            # 创建目标目录
            target_dir = Path(self.download_config['target_dir'])
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载所有文件
            total_files = len(self.download_config['files'])
            for i, file_info in enumerate(self.download_config['files']):
                if self.is_cancelled:
                    return
                
                file_name = file_info['name']
                file_url = file_info['url']
                file_size = file_info.get('size', 0)
                
                self.progress_updated.emit(
                    int((i / total_files) * 100),
                    f"下载文件 {i+1}/{total_files}: {file_name}"
                )
                
                success = self._download_file(file_url, target_dir / file_name, file_size)
                if not success:
                    self.error_occurred.emit("下载失败", f"文件 {file_name} 下载失败")
                    return
            
            # 验证下载完整性
            self.progress_updated.emit(95, "验证文件完整性...")
            if self._verify_download():
                self.progress_updated.emit(100, "下载完成!")
                self.download_completed.emit(self.model_name, True)
            else:
                self.error_occurred.emit("验证失败", "下载的文件不完整或损坏")
                
        except Exception as e:
            logger.error(f"下载过程中发生错误: {str(e)}")
            self.error_occurred.emit("下载错误", str(e))
    
    def _download_file(self, url: str, target_path: Path, expected_size: int = 0) -> bool:
        """下载单个文件"""
        try:
            # 检查是否支持断点续传
            resume_pos = 0
            if target_path.exists():
                resume_pos = target_path.stat().st_size
                if resume_pos == expected_size and expected_size > 0:
                    logger.info(f"文件已存在且完整: {target_path.name}")
                    return True
            
            # 设置请求头支持断点续传
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
                logger.info(f"断点续传: {target_path.name} 从 {resume_pos} 字节开始")
            
            # 发起下载请求
            response = self.session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件总大小
            if 'content-length' in response.headers:
                total_size = int(response.headers['content-length'])
                if resume_pos > 0:
                    total_size += resume_pos
            else:
                total_size = expected_size
            
            # 下载文件
            mode = 'ab' if resume_pos > 0 else 'wb'
            downloaded = resume_pos
            
            with open(target_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.is_cancelled:
                        return False
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress_updated.emit(
                                progress,
                                f"下载 {target_path.name}: {self._format_size(downloaded)}/{self._format_size(total_size)}"
                            )
            
            logger.info(f"文件下载完成: {target_path.name}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求错误: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"文件下载错误: {str(e)}")
            return False
    
    def _verify_download(self) -> bool:
        """验证下载完整性"""
        try:
            target_dir = Path(self.download_config['target_dir'])
            
            for file_info in self.download_config['files']:
                file_path = target_dir / file_info['name']
                
                # 检查文件是否存在
                if not file_path.exists():
                    logger.error(f"文件不存在: {file_path}")
                    return False
                
                # 检查文件大小
                expected_size = file_info.get('size', 0)
                if expected_size > 0:
                    actual_size = file_path.stat().st_size
                    if actual_size != expected_size:
                        logger.error(f"文件大小不匹配: {file_path} (期望: {expected_size}, 实际: {actual_size})")
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
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

class EnhancedModelDownloader(QObject):
    """增强模型下载器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_configs = self._load_download_configs()
        self.current_download = None
        self.progress_dialog = None
        self._last_model_name = None  # 添加状态跟踪

        # 导入智能选择器
        try:
            from .intelligent_model_selector import IntelligentModelSelector, SelectionStrategy
            self.intelligent_selector = IntelligentModelSelector()
            self.has_intelligent_selector = True
        except ImportError:
            self.intelligent_selector = None
            self.has_intelligent_selector = False
            logger.warning("智能模型选择器不可用，将使用基础下载功能")

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
                    selector_models = ["mistral-7b", "qwen2.5-7b"]  # 已知支持的模型
                    available_models.extend(selector_models)
                except Exception as e:
                    logger.debug(f"从智能选择器获取模型列表失败: {e}")

            # 去重并排序
            available_models = sorted(list(set(available_models)))

            return available_models

        except Exception as e:
            logger.error(f"获取可用模型列表失败: {e}")
            return ["mistral-7b", "qwen2.5-7b"]  # 返回默认支持的模型

    def _load_download_configs(self) -> Dict:
        """加载下载配置"""
        return {
            "qwen2.5-7b": {
                "name": "Qwen2.5-7B-Instruct",
                "description": "通义千问2.5-7B指令模型（中文优化）",
                "total_size": 15463424000,  # 约14.4GB
                "target_dir": "models/models/qwen/base",
                "files": [
                    {
                        "name": "model-00001-of-00008.safetensors",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00001-of-00008.safetensors",
                        "size": 1932735488
                    },
                    {
                        "name": "model-00002-of-00008.safetensors", 
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00002-of-00008.safetensors",
                        "size": 1999994880
                    },
                    {
                        "name": "model-00003-of-00008.safetensors",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00003-of-00008.safetensors", 
                        "size": 1999994880
                    },
                    {
                        "name": "model-00004-of-00008.safetensors",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00004-of-00008.safetensors",
                        "size": 1999994880
                    },
                    {
                        "name": "model-00005-of-00008.safetensors",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00005-of-00008.safetensors",
                        "size": 1999994880
                    },
                    {
                        "name": "model-00006-of-00008.safetensors",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00006-of-00008.safetensors",
                        "size": 1999994880
                    },
                    {
                        "name": "model-00007-of-00008.safetensors",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00007-of-00008.safetensors",
                        "size": 1999994880
                    },
                    {
                        "name": "model-00008-of-00008.safetensors",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00008-of-00008.safetensors",
                        "size": 1530715136
                    },
                    {
                        "name": "config.json",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/config.json",
                        "size": 1024
                    },
                    {
                        "name": "generation_config.json",
                        "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/generation_config.json",
                        "size": 256
                    }
                ]
            },
            "mistral-7b": {
                "name": "Mistral-7B-Instruct-v0.1",
                "description": "Mistral-7B指令模型（英文优化）",
                "total_size": 4200000000,  # 约4.2GB (GGUF量化版本)
                "target_dir": "models/mistral/base",
                "files": [
                    {
                        "name": "mistral-7b-instruct-v0.1.q4_k_m.gguf",
                        "url": "https://modelscope.cn/models/LLM-Research/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.q4_k_m.gguf",
                        "size": 4200000000
                    },
                    {
                        "name": "config.json",
                        "url": "https://modelscope.cn/models/AI-ModelScope/Mistral-7B-Instruct-v0.1/resolve/main/config.json",
                        "size": 1024
                    },
                    {
                        "name": "tokenizer.json",
                        "url": "https://modelscope.cn/models/AI-ModelScope/Mistral-7B-Instruct-v0.1/resolve/main/tokenizer.json",
                        "size": 2048
                    },
                    {
                        "name": "tokenizer_config.json",
                        "url": "https://modelscope.cn/models/AI-ModelScope/Mistral-7B-Instruct-v0.1/resolve/main/tokenizer_config.json",
                        "size": 512
                    }
                ]
            }
        }
    
    def download_model(self, model_name: str, parent_widget=None, auto_select: bool = True) -> bool:
        """下载指定模型（支持智能版本选择）"""
        logger.info(f"🚀 开始下载模型: {model_name}, auto_select={auto_select}")
        logger.info(f"🔧 智能选择器状态: {self.has_intelligent_selector}")

        # 重要修复：检查模型名称变化，如果变化则清除状态
        if self._last_model_name and self._last_model_name != model_name:
            logger.info(f"🔄 检测到模型名称变化: {self._last_model_name} -> {model_name}，清除状态")
            self._clear_internal_state()

        # 记录当前模型名称
        self._last_model_name = model_name

        # 额外验证：确保智能选择器状态与当前请求一致
        if self.intelligent_selector and hasattr(self.intelligent_selector, '_last_model_name'):
            if self.intelligent_selector._last_model_name and self.intelligent_selector._last_model_name != model_name:
                logger.info(f"🔄 智能选择器状态不一致，强制清除: {self.intelligent_selector._last_model_name} -> {model_name}")
                self.intelligent_selector.clear_cache()

        if auto_select and self.has_intelligent_selector:
            logger.info("✅ 使用智能下载模式")
            return self._intelligent_download(model_name, parent_widget)
        else:
            logger.info("⚠️ 使用基础下载模式")
            return self._basic_download(model_name, parent_widget)

    def _intelligent_download(self, model_name: str, parent_widget=None) -> bool:
        """智能下载（自动选择最佳版本）"""
        logger.info(f"🤖 开始智能下载: {model_name}")

        try:
            from .intelligent_model_selector import SelectionStrategy, DeploymentTarget
            logger.info("✅ 智能选择器模块导入成功")

            # 强制刷新硬件配置以确保检测到最新的硬件状态
            logger.info("🔄 强制刷新硬件配置...")
            self.intelligent_selector.force_refresh_hardware()

            # 获取智能推荐
            logger.info("🔍 正在获取智能推荐...")
            recommendation = self.intelligent_selector.recommend_model_version(
                model_name=model_name,
                strategy=SelectionStrategy.AUTO_RECOMMEND
            )

            if recommendation:
                # 重要修复：验证推荐结果与请求的模型名称一致性
                if recommendation.model_name != model_name:
                    logger.error(f"❌ 推荐结果模型名称不一致: 请求={model_name}, 推荐={recommendation.model_name}")
                    logger.info("🔄 清除状态并重新获取推荐...")
                    self._clear_internal_state()
                    # 重新获取推荐
                    recommendation = self.intelligent_selector.recommend_model_version(
                        model_name=model_name,
                        strategy=SelectionStrategy.AUTO_RECOMMEND
                    )

                    # 再次验证
                    if recommendation and recommendation.model_name != model_name:
                        logger.error(f"❌ 重新获取后仍然不一致，回退到基础下载")
                        return self._basic_download(model_name, parent_widget)

                # 记录推荐详情
                logger.info(f"✅ 获取推荐成功:")
                logger.info(f"  模型: {recommendation.model_name}")
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

    def _basic_download(self, model_name: str, parent_widget=None) -> bool:
        """基础下载（原有逻辑）"""
        if model_name not in self.download_configs:
            QMessageBox.critical(parent_widget, "错误", f"未知模型: {model_name}")
            return False

        config = self.download_configs[model_name]

        # 显示确认对话框
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
            # 用户取消基础下载确认对话框时返回 None
            # 记录用户取消时间，防止短时间内重复弹窗
            import time
            if parent_widget:
                parent_widget._last_model_dialog_cancel_time = time.time()
            return None
        
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
        self.current_download = ModelDownloadThread(model_name, config, self)
        
        # 连接信号
        self.current_download.progress_updated.connect(self._on_progress_updated)
        self.current_download.download_completed.connect(self._on_download_completed)
        self.current_download.error_occurred.connect(self._on_error_occurred)
        self.progress_dialog.canceled.connect(self.current_download.cancel_download)
        
        # 开始下载
        self.current_download.start()
        
        return True
    
    def _on_progress_updated(self, progress: int, status: str):
        """更新进度"""
        if self.progress_dialog:
            self.progress_dialog.setValue(progress)
            self.progress_dialog.setLabelText(status)
    
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

    def _show_recommendation_dialog(self, recommendation, parent_widget) -> bool:
        """显示智能推荐对话框"""
        logger.info("🎨 开始显示智能推荐对话框")

        # 强化防重复弹窗逻辑：多重检查机制
        # 1. 检查是否有实际的对话框窗口在显示
        if hasattr(parent_widget, '_dialog_instance') and parent_widget._dialog_instance is not None:
            logger.info("⚠️ 检测到实际对话框窗口已在显示中，跳过重复弹窗")
            return None  # 返回 None 表示用户取消，避免触发回退

        # 2. 检查全局对话框标志位（但允许enhanced_downloader管理的对话框）
        # 注意：我们不在这里检查_global_model_dialog_showing，因为这会阻止正常的第一次显示
        # enhanced_downloader会在内部设置这个标志位来管理自己的对话框生命周期

        # 3. 检查是否有任何模态对话框在显示
        from PyQt6.QtWidgets import QApplication
        active_modal_widget = QApplication.activeModalWidget()
        if active_modal_widget is not None:
            logger.info("⚠️ 检测到其他模态对话框正在显示，跳过重复弹窗")
            return None  # 返回 None 表示用户取消，避免触发回退

        # 4. 检查最近的用户取消时间（防止短时间内重复弹窗）
        import time
        current_time = time.time()
        last_cancel_time = getattr(parent_widget, '_last_model_dialog_cancel_time', 0)
        if current_time - last_cancel_time < 0.5:  # 改为0.5秒，进一步减少误触发
            logger.info("⚠️ 检测到用户最近刚取消过下载，跳过重复弹窗")
            return None
        elif last_cancel_time > 0:
            # 如果超过0.5秒，清除取消时间记录
            delattr(parent_widget, '_last_model_dialog_cancel_time')
            logger.info("✅ 清除过期的用户取消时间记录")

        try:
            # 设置防重复标志，表示正在创建对话框
            parent_widget._global_model_dialog_showing = True
            logger.info("🔧 设置对话框标志位，防止重复弹窗")

            # 优化：直接在主线程中创建对话框，避免不必要的线程检查延迟
            logger.info("✅ 在主线程中，直接创建对话框")
            return self._create_dialog_sync(recommendation, parent_widget)

        except Exception as e:
            logger.error(f"❌ 对话框显示失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False
        finally:
            # 清除防重复标志
            if hasattr(parent_widget, '_global_model_dialog_showing'):
                parent_widget._global_model_dialog_showing = False
                logger.info("🔧 清除对话框显示标志位")

    def _create_dialog_sync(self, recommendation, parent_widget) -> bool:
        """同步创建对话框（确保在主线程中执行）"""
        try:
            # 修复导入路径 - 使用安全的路径解析方式
            import sys
            import os
            from pathlib import Path

            # 安全地获取项目根目录
            try:
                current_file = Path(__file__).resolve()
                project_root = current_file.parent.parent.parent
                project_root_str = str(project_root)
                if project_root_str not in sys.path:
                    sys.path.insert(0, project_root_str)
                logger.info(f"✅ 项目根路径设置: {project_root_str}")
            except Exception as e:
                logger.warning(f"⚠️ 无法设置项目根路径: {e}")
                # 回退到当前工作目录
                project_root_str = os.getcwd()
                if project_root_str not in sys.path:
                    sys.path.insert(0, project_root_str)

            # 安全地获取src目录
            try:
                src_path = current_file.parent.parent
                src_path_str = str(src_path)
                if src_path_str not in sys.path:
                    sys.path.insert(0, src_path_str)
                logger.info(f"✅ src路径设置: {src_path_str}")
            except Exception as e:
                logger.warning(f"⚠️ 无法设置src路径: {e}")
                # 回退到src目录
                src_fallback = os.path.join(os.getcwd(), "src")
                if os.path.exists(src_fallback) and src_fallback not in sys.path:
                    sys.path.insert(0, src_fallback)

            # 尝试导入增强对话框
            try:
                from src.ui.enhanced_download_dialog import EnhancedDownloadDialog
                logger.info("✅ 增强对话框模块导入成功 (src.ui路径)")
            except ImportError:
                try:
                    from ui.enhanced_download_dialog import EnhancedDownloadDialog
                    logger.info("✅ 增强对话框模块导入成功 (ui路径)")
                except ImportError:
                    # 安全地使用绝对路径导入
                    try:
                        current_file = Path(__file__).resolve()
                        dialog_path = current_file.parent.parent / "ui" / "enhanced_download_dialog.py"
                        logger.info(f"📁 对话框文件路径: {dialog_path}")
                        logger.info(f"📁 文件存在: {dialog_path.exists()}")

                        if dialog_path.exists():
                            import importlib.util
                            spec = importlib.util.spec_from_file_location("enhanced_download_dialog", str(dialog_path))
                            if spec and spec.loader:
                                dialog_module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(dialog_module)
                                EnhancedDownloadDialog = dialog_module.EnhancedDownloadDialog
                                logger.info("✅ 增强对话框模块导入成功 (绝对路径)")
                            else:
                                raise ImportError("无法创建模块规范")
                        else:
                            raise ImportError(f"对话框文件不存在: {dialog_path}")
                    except Exception as path_error:
                        logger.error(f"❌ 绝对路径导入失败: {path_error}")
                        raise ImportError(f"所有导入方式都失败: {path_error}")

            # 创建增强对话框
            logger.info(f"🔧 创建对话框: model={recommendation.model_name}, variant={recommendation.variant.name}")
            dialog = EnhancedDownloadDialog(
                model_name=recommendation.model_name,
                recommendation=recommendation,
                parent=parent_widget
            )
            logger.info("✅ 增强对话框创建成功")

            # 设置对话框实例引用，用于防重复检查
            parent_widget._dialog_instance = dialog

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

            if result == dialog.DialogCode.Accepted:
                selected_variant = dialog.get_selected_variant()
                if selected_variant:
                    logger.info(f"✅ 用户选择版本: {selected_variant.get('variant', {}).get('name', 'Unknown')}")
                    # 用户确认下载选中版本
                    return self._download_selected_variant(selected_variant, recommendation.model_name, parent_widget)
                else:
                    logger.warning("⚠️ 用户未选择版本")
            else:
                logger.info("ℹ️ 用户取消下载")
                # 记录用户取消时间，防止短时间内重复弹窗
                import time
                if parent_widget:
                    parent_widget._last_model_dialog_cancel_time = time.time()

            # 用户取消时返回特殊值 None，而不是 False
            # False 表示下载失败，None 表示用户取消
            return None

        except ImportError as e:
            # 回退到基础对话框
            logger.warning(f"⚠️ 增强对话框导入失败: {e}")
            logger.warning("🔄 回退到基础对话框")
            return self._show_basic_recommendation_dialog(recommendation, parent_widget)
        except Exception as e:
            logger.error(f"❌ 显示推荐对话框失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            logger.warning("🔄 回退到基础对话框")
            return self._show_basic_recommendation_dialog(recommendation, parent_widget)
        finally:
            # 确保清理对话框相关状态 - 增强版本
            try:
                if hasattr(parent_widget, '_dialog_instance'):
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

                if hasattr(parent_widget, '_global_model_dialog_showing'):
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
        """下载推荐的变体"""
        # 这里需要根据推荐的变体配置实际的下载
        # 暂时使用基础下载逻辑
        variant = recommendation.variant

        # 创建临时配置
        temp_config = {
            'name': variant.name,
            'description': f"智能推荐版本 - {variant.quantization.value}",
            'total_size': int(variant.size_gb * 1024**3),
            'target_dir': f"models/{recommendation.model_name}/{variant.quantization.value}",
            'files': [
                {
                    'name': f"{recommendation.model_name}-{variant.quantization.value}.gguf",
                    'url': f"https://example.com/{recommendation.model_name}/{variant.quantization.value}",
                    'size': int(variant.size_gb * 1024**3)
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
        # 记录用户取消时间，防止短时间内重复弹窗
        import time
        if parent_widget:
            parent_widget._last_model_dialog_cancel_time = time.time()
        return None

    def _download_selected_variant(self, selected_variant: Dict, model_name: str, parent_widget) -> bool:
        """下载用户选中的变体"""
        variant = selected_variant.get('variant')
        if not variant:
            return False

        # 创建下载配置
        download_config = {
            'name': variant.name,
            'description': f"用户选择版本 - {variant.quantization.value}",
            'total_size': int(variant.size_gb * 1024**3),
            'target_dir': f"models/{model_name}/{variant.quantization.value}",
            'files': [
                {
                    'name': f"{model_name}-{variant.quantization.value}.gguf",
                    'url': self._get_download_url(model_name, variant.quantization.value),
                    'size': int(variant.size_gb * 1024**3)
                }
            ]
        }

        return self._execute_download(download_config, parent_widget)

    def _get_download_url(self, model_name: str, quantization_type: str) -> str:
        """获取下载URL"""
        # 这里应该根据实际的下载源配置返回正确的URL
        # 暂时返回示例URL
        base_urls = {
            "qwen2.5-7b": {
                "q4_k_m": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
                "q5_k_m": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf",
                "q8_0": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q8_0.gguf",
                "fp16": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct"
            },
            "mistral-7b": {
                "q4_k_m": "https://hf-mirror.com/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.q4_k_m.gguf",
                "q5_k_m": "https://hf-mirror.com/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.q5_k_m.gguf",
                "q8_0": "https://hf-mirror.com/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.q8_0.gguf",
                "fp16": "https://hf-mirror.com/mistralai/Mistral-7B-Instruct-v0.1"
            }
        }

        return base_urls.get(model_name, {}).get(quantization_type, "https://example.com/model.gguf")

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
