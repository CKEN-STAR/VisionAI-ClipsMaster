#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
推理模型加载器
智能选择最佳可用模型（训练后的模型优先于基础模型）
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from src.training.model_version_manager import ModelVersionManager

logger = logging.getLogger(__name__)

class InferenceModelLoader:
    """推理模型加载器"""
    
    def __init__(self, model_name: str = "Qwen3-1.7B-zh"):
        """
        初始化推理模型加载器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.models_dir = Path("models")
        
        # 确定模型基础目录
        if "qwen" in model_name.lower():
            self.base_dir = self.models_dir / "qwen"
        elif "mistral" in model_name.lower():
            self.base_dir = self.models_dir / "mistral"
        else:
            self.base_dir = self.models_dir / model_name
        
        # 初始化版本管理器
        self.version_manager = ModelVersionManager(base_dir=str(self.base_dir))
    
    def get_best_model_path(
        self,
        use_trained: bool = True,
        format_type: str = "gguf"
    ) -> Tuple[Optional[str], str]:
        """
        获取最佳模型路径
        
        Args:
            use_trained: 是否优先使用训练后的模型
            format_type: 模型格式 ("gguf" 或 "huggingface")
            
        Returns:
            (model_path, model_type): 模型路径和类型
        """
        logger.info(f"🔍 查找最佳模型...")
        logger.info(f"   优先训练模型: {use_trained}")
        logger.info(f"   格式类型: {format_type}")
        
        # 1. 如果优先使用训练后的模型，先查找训练版本
        if use_trained:
            trained_path = self._get_trained_model_path(format_type)
            if trained_path:
                logger.info(f"✅ 使用训练后的模型: {trained_path}")
                return trained_path, "trained"
        
        # 2. 查找基础模型
        base_path = self._get_base_model_path(format_type)
        if base_path:
            logger.info(f"✅ 使用基础模型: {base_path}")
            return base_path, "base"
        
        # 3. 如果没有找到，尝试其他格式
        logger.warning(f"⚠️ 未找到{format_type}格式模型，尝试其他格式...")
        
        alternative_format = "huggingface" if format_type == "gguf" else "gguf"
        
        if use_trained:
            trained_path = self._get_trained_model_path(alternative_format)
            if trained_path:
                logger.info(f"✅ 使用训练后的模型（{alternative_format}）: {trained_path}")
                return trained_path, "trained"
        
        base_path = self._get_base_model_path(alternative_format)
        if base_path:
            logger.info(f"✅ 使用基础模型（{alternative_format}）: {base_path}")
            return base_path, "base"
        
        logger.error("❌ 未找到任何可用模型")
        return None, "none"
    
    def _get_trained_model_path(self, format_type: str) -> Optional[str]:
        """获取训练后的模型路径"""
        try:
            # 获取激活的版本
            active_version = self.version_manager.get_active_version()
            
            if not active_version:
                logger.debug("   没有激活的训练版本")
                return None
            
            # 根据格式类型选择路径
            if format_type == "gguf":
                model_path = active_version.get("gguf_path")
            else:
                model_path = active_version.get("hf_path")
            
            if model_path and Path(model_path).exists():
                return model_path
            
            # 如果激活版本的路径不存在，尝试查找最新的训练模型
            if format_type == "gguf":
                trained_dir = self.base_dir / "quantized" / "trained"
                if trained_dir.exists():
                    # 查找latest.gguf
                    latest_path = trained_dir / "latest.gguf"
                    if latest_path.exists():
                        return str(latest_path)
                    
                    # 查找最新的GGUF文件
                    gguf_files = sorted(
                        trained_dir.glob("trained_*.gguf"),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )
                    if gguf_files:
                        return str(gguf_files[0])
            
            return None
            
        except Exception as e:
            logger.error(f"   获取训练模型路径失败: {e}")
            return None
    
    def _get_base_model_path(self, format_type: str) -> Optional[str]:
        """获取基础模型路径"""
        try:
            if format_type == "gguf":
                # 查找GGUF格式基础模型
                quant_dir = self.base_dir / "quantized"
                if quant_dir.exists():
                    # 查找Q4_K_M量化版本
                    gguf_files = list(quant_dir.glob(f"{self.model_name}_Q4_K_M.gguf"))
                    if gguf_files:
                        return str(gguf_files[0])
                    
                    # 查找任何GGUF文件
                    gguf_files = list(quant_dir.glob("*.gguf"))
                    if gguf_files:
                        return str(gguf_files[0])
            else:
                # 查找HuggingFace格式基础模型
                base_dir = self.base_dir / "base"
                if base_dir.exists() and (base_dir / "config.json").exists():
                    return str(base_dir)
            
            return None
            
        except Exception as e:
            logger.error(f"   获取基础模型路径失败: {e}")
            return None
    
    def list_available_models(self) -> dict:
        """列出所有可用模型"""
        available = {
            "base_models": {},
            "trained_models": []
        }
        
        # 基础模型
        base_gguf = self._get_base_model_path("gguf")
        base_hf = self._get_base_model_path("huggingface")
        
        if base_gguf:
            available["base_models"]["gguf"] = base_gguf
        if base_hf:
            available["base_models"]["huggingface"] = base_hf
        
        # 训练后的模型
        versions = self.version_manager.list_versions()
        for version in versions:
            version_info = {
                "version_id": version["version_id"],
                "created_at": version["created_at"],
                "gguf_path": version.get("gguf_path"),
                "hf_path": version.get("hf_path"),
                "is_active": version["version_id"] == self.version_manager.versions.get("active_version")
            }
            available["trained_models"].append(version_info)
        
        return available
    
    def switch_to_version(self, version_id: str) -> bool:
        """
        切换到指定版本
        
        Args:
            version_id: 版本ID
            
        Returns:
            是否成功
        """
        return self.version_manager.set_active_version(version_id)
    
    def get_model_info(self) -> dict:
        """获取当前模型信息"""
        gguf_path, gguf_type = self.get_best_model_path(use_trained=True, format_type="gguf")
        hf_path, hf_type = self.get_best_model_path(use_trained=True, format_type="huggingface")
        
        info = {
            "model_name": self.model_name,
            "gguf": {
                "path": gguf_path,
                "type": gguf_type,
                "exists": Path(gguf_path).exists() if gguf_path else False
            },
            "huggingface": {
                "path": hf_path,
                "type": hf_type,
                "exists": Path(hf_path).exists() if hf_path else False
            },
            "active_version": self.version_manager.get_active_version(),
            "total_versions": len(self.version_manager.list_versions())
        }
        
        return info

