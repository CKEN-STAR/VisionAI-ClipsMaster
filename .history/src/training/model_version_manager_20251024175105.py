#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型版本管理器
管理训练后的模型版本，支持版本切换和历史追踪
包含智能版本清理机制，避免模型文件过多
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ModelVersionManager:
    """模型版本管理器"""
    
    def __init__(self, base_dir: str = "models/qwen", max_versions: int = 5):
        """
        初始化版本管理器
        
        Args:
            base_dir: 基础目录
            max_versions: 最大保留版本数（默认5个）
        """
        self.base_dir = Path(base_dir)
        self.trained_dir = self.base_dir / "trained"
        self.trained_dir.mkdir(parents=True, exist_ok=True)
        
        self.version_file = self.trained_dir / "versions.json"
        self.max_versions = max_versions
        self.versions = self._load_versions()
        
    def _load_versions(self) -> Dict:
        """加载版本信息"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载版本信息失败: {e}")
                return {"versions": [], "active_version": None}
        return {"versions": [], "active_version": None}
    
    def _save_versions(self):
        """保存版本信息"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(self.versions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存版本信息失败: {e}")
    
    def register_new_version(
        self,
        model_path: str,
        gguf_path: Optional[str] = None,
        training_info: Optional[Dict] = None,
        copy_files: bool = True
    ) -> str:
        """
        注册新的训练版本

        Args:
            model_path: HuggingFace格式模型路径
            gguf_path: GGUF格式模型路径（可选）
            training_info: 训练信息
            copy_files: 是否复制模型文件（默认True）
                       - True: 复制模型到trained目录（传统模式）
                       - False: 只记录路径引用，不复制文件（引用模式）

        Returns:
            版本ID
        """
        version_id = datetime.now().strftime("v%Y%m%d_%H%M%S")

        logger.info(f"📝 注册新版本: {version_id} (copy_files={copy_files})")

        try:
            if copy_files:
                # 传统模式：复制文件到trained目录
                # 创建版本目录
                version_dir = self.trained_dir / version_id
                version_dir.mkdir(parents=True, exist_ok=True)

                # 复制HuggingFace格式模型
                hf_dir = version_dir / "huggingface"
                if Path(model_path).exists():
                    logger.info(f"   复制HF模型: {model_path} -> {hf_dir}")
                    shutil.copytree(model_path, hf_dir, dirs_exist_ok=True)
                else:
                    logger.warning(f"   HF模型路径不存在: {model_path}")

                # 复制GGUF格式模型（如果存在）
                gguf_saved_path = None
                if gguf_path and Path(gguf_path).exists():
                    gguf_dir = version_dir / "gguf"
                    gguf_dir.mkdir(exist_ok=True)
                    gguf_saved_path = gguf_dir / "model.gguf"
                    logger.info(f"   复制GGUF模型: {gguf_path} -> {gguf_saved_path}")
                    shutil.copy2(gguf_path, gguf_saved_path)

                # 记录版本信息
                version_info = {
                    "version_id": version_id,
                    "created_at": datetime.now().isoformat(),
                    "hf_path": str(hf_dir) if hf_dir.exists() else None,
                    "gguf_path": str(gguf_saved_path) if gguf_saved_path and gguf_saved_path.exists() else None,
                    "training_info": training_info or {},
                    "copy_mode": "copy"
                }
            else:
                # 引用模式：只记录路径，不复制文件
                logger.info(f"   引用HF模型: {model_path}")

                # 验证路径存在
                if not Path(model_path).exists():
                    logger.warning(f"   HF模型路径不存在: {model_path}")

                # 记录版本信息（直接使用原始路径）
                version_info = {
                    "version_id": version_id,
                    "created_at": datetime.now().isoformat(),
                    "hf_path": str(Path(model_path).resolve()),  # 使用绝对路径
                    "gguf_path": str(Path(gguf_path).resolve()) if gguf_path and Path(gguf_path).exists() else None,
                    "training_info": training_info or {},
                    "copy_mode": "reference"
                }

            self.versions["versions"].append(version_info)
            self.versions["active_version"] = version_id
            self._save_versions()

            logger.info(f"✅ 版本注册成功: {version_id}")

            # 只在复制模式下自动清理旧版本
            if copy_files:
                self._auto_cleanup_old_versions()

            return version_id

        except Exception as e:
            logger.error(f"❌ 版本注册失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ""
    
    def _auto_cleanup_old_versions(self):
        """自动清理旧版本（保留最近的N个版本）"""
        if len(self.versions["versions"]) <= self.max_versions:
            return
        
        logger.info(f"🧹 开始自动清理旧版本（保留最近{self.max_versions}个）")
        
        # 按创建时间排序
        sorted_versions = sorted(
            self.versions["versions"],
            key=lambda v: v["created_at"],
            reverse=True
        )
        
        # 保留最近的版本
        versions_to_keep = sorted_versions[:self.max_versions]
        versions_to_remove = sorted_versions[self.max_versions:]
        
        # 删除旧版本
        for version in versions_to_remove:
            version_id = version["version_id"]
            logger.info(f"   删除旧版本: {version_id}")
            self._remove_version_files(version_id)
        
        # 更新版本列表
        self.versions["versions"] = versions_to_keep
        self._save_versions()
        
        logger.info(f"✅ 清理完成，保留了{len(versions_to_keep)}个版本")
    
    def _remove_version_files(self, version_id: str):
        """删除版本文件"""
        # 查找版本信息，检查是否为引用模式
        version_info = None
        for v in self.versions["versions"]:
            if v["version_id"] == version_id:
                version_info = v
                break

        # 如果是引用模式，不删除文件，只从列表中移除
        if version_info and version_info.get("copy_mode") == "reference":
            logger.info(f"   引用模式版本，不删除原始文件")
            return

        # 复制模式：删除trained目录下的文件
        version_dir = self.trained_dir / version_id
        if version_dir.exists():
            try:
                shutil.rmtree(version_dir)
                logger.info(f"   已删除目录: {version_dir}")
            except Exception as e:
                logger.error(f"   删除目录失败: {e}")
    
    def cleanup_version(self, version_id: str) -> bool:
        """
        手动清理指定版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            是否成功
        """
        logger.info(f"🧹 手动清理版本: {version_id}")
        
        # 不允许删除当前激活的版本
        if version_id == self.versions.get("active_version"):
            logger.warning(f"   无法删除激活版本: {version_id}")
            return False
        
        # 查找版本
        version_found = False
        for i, version in enumerate(self.versions["versions"]):
            if version["version_id"] == version_id:
                # 删除文件
                self._remove_version_files(version_id)
                
                # 从列表中移除
                self.versions["versions"].pop(i)
                self._save_versions()
                
                version_found = True
                logger.info(f"✅ 版本已清理: {version_id}")
                break
        
        if not version_found:
            logger.warning(f"   版本不存在: {version_id}")
            return False
        
        return True
    
    def cleanup_all_except_active(self) -> int:
        """
        清理所有版本（除了激活版本）
        
        Returns:
            清理的版本数量
        """
        logger.info("🧹 清理所有非激活版本")
        
        active_version = self.versions.get("active_version")
        if not active_version:
            logger.warning("   没有激活版本")
            return 0
        
        versions_to_remove = [
            v for v in self.versions["versions"]
            if v["version_id"] != active_version
        ]
        
        count = 0
        for version in versions_to_remove:
            version_id = version["version_id"]
            self._remove_version_files(version_id)
            count += 1
        
        # 只保留激活版本
        self.versions["versions"] = [
            v for v in self.versions["versions"]
            if v["version_id"] == active_version
        ]
        self._save_versions()
        
        logger.info(f"✅ 已清理{count}个版本")
        return count
    
    def list_versions(self) -> List[Dict]:
        """列出所有版本"""
        return self.versions["versions"]
    
    def get_active_version(self) -> Optional[Dict]:
        """获取当前激活的版本"""
        active_id = self.versions.get("active_version")
        if not active_id:
            return None
        
        for version in self.versions["versions"]:
            if version["version_id"] == active_id:
                return version
        return None
    
    def set_active_version(self, version_id: str) -> bool:
        """设置激活版本"""
        for version in self.versions["versions"]:
            if version["version_id"] == version_id:
                self.versions["active_version"] = version_id
                self._save_versions()
                logger.info(f"✅ 已切换到版本: {version_id}")
                return True

        logger.warning(f"❌ 版本不存在: {version_id}")
        return False

    def update_version_performance(self, version_id: str, performance_score: float) -> bool:
        """
        更新版本的性能分数

        Args:
            version_id: 版本ID
            performance_score: 性能分数（0-1之间）

        Returns:
            是否更新成功
        """
        for version in self.versions["versions"]:
            if version["version_id"] == version_id:
                version["performance_score"] = performance_score
                self._save_versions()
                logger.info(f"✅ 已更新版本 {version_id} 的性能分数: {performance_score:.2%}")
                return True

        logger.warning(f"❌ 版本不存在: {version_id}")
        return False

    def get_version_info(self, version_id: str) -> Optional[Dict]:
        """获取版本信息"""
        for version in self.versions["versions"]:
            if version["version_id"] == version_id:
                return version
        return None
    
    def get_storage_usage(self) -> Dict[str, float]:
        """
        获取存储使用情况
        
        Returns:
            存储使用信息（GB）
        """
        total_size = 0
        version_sizes = {}
        
        for version in self.versions["versions"]:
            version_id = version["version_id"]
            version_dir = self.trained_dir / version_id
            
            if version_dir.exists():
                size = sum(
                    f.stat().st_size
                    for f in version_dir.rglob('*')
                    if f.is_file()
                )
                size_gb = size / (1024 ** 3)
                version_sizes[version_id] = size_gb
                total_size += size_gb
        
        return {
            "total_gb": total_size,
            "versions": version_sizes
        }

