#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型初始化脚本（集成智能推荐下载器版本）
下载并准备基础模型用于训练和推理
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.enhanced_model_downloader import EnhancedModelDownloader
from src.core.intelligent_model_selector import IntelligentModelSelector
from models.converters.model_converter import ModelConverter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelSetup:
    """模型初始化管理器（集成智能推荐下载器）"""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.converter = ModelConverter()
        self.downloader = EnhancedModelDownloader()
        self.selector = IntelligentModelSelector()
        
    def setup_base_model(self, model_name: str = "qwen2.5-7b-zh") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        设置基础模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            (success, hf_path, gguf_path): 成功标志、HF格式路径、GGUF格式路径
        """
        logger.info("=" * 70)
        logger.info(f"📥 开始设置模型: {model_name}")
        logger.info("=" * 70)
        
        try:
            # 1. 使用智能推荐下载器下载模型
            logger.info("🤖 使用智能推荐下载器...")
            
            # 获取智能推荐
            recommendation = self.selector.recommend_model_version(model_name)
            
            if not recommendation:
                logger.error(f"❌ 无法获取模型推荐: {model_name}")
                return False, None, None
            
            logger.info(f"✅ 推荐模型: {recommendation.model_name}")
            logger.info(f"   变体: {recommendation.variant.name}")
            logger.info(f"   量化: {recommendation.variant.quantization.value}")
            logger.info(f"   大小: {recommendation.variant.size_gb:.1f}GB")
            logger.info(f"   质量保持: {recommendation.variant.quality_retention:.1%}")
            
            # 2. 执行下载（使用智能下载器）
            logger.info("📥 开始下载模型...")
            success = self.downloader.download_model(
                model_name=model_name,
                auto_select=True  # 使用智能推荐
            )
            
            if not success:
                logger.error(f"❌ 模型下载失败: {model_name}")
                logger.info("💡 提示：您可以手动下载模型并放置到正确的目录")
                return False, None, None
            
            # 3. 确定下载后的模型路径
            base_path = self._get_downloaded_model_path(model_name)
            
            if not base_path or not base_path.exists():
                logger.error(f"❌ 下载的模型路径不存在: {base_path}")
                logger.info("💡 尝试查找其他可能的路径...")
                base_path = self._find_model_path(model_name)
                
                if not base_path:
                    logger.error("❌ 无法找到下载的模型")
                    return False, None, None
            
            logger.info(f"✅ 模型已下载到: {base_path}")
            
            # 4. 转换为GGUF格式用于推理
            logger.info("🔄 开始转换为GGUF格式...")
            gguf_path = self._convert_to_gguf(model_name, base_path)
            
            if gguf_path:
                logger.info("=" * 70)
                logger.info(f"✅ 模型设置完成!")
                logger.info(f"   HF格式: {base_path}")
                logger.info(f"   GGUF格式: {gguf_path}")
                logger.info("=" * 70)
                return True, str(base_path), str(gguf_path)
            else:
                logger.warning("=" * 70)
                logger.warning(f"⚠️ GGUF转换失败，但HF格式可用")
                logger.warning(f"   HF格式: {base_path}")
                logger.warning("   您仍然可以使用HF格式进行训练")
                logger.warning("=" * 70)
                return True, str(base_path), None
                
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ 模型设置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("=" * 70)
            return False, None, None
    
    def _get_downloaded_model_path(self, model_name: str) -> Optional[Path]:
        """获取下载后的模型路径"""
        # 根据模型名称确定路径
        if "qwen" in model_name.lower():
            base_path = self.models_dir / "qwen" / "base"
        elif "mistral" in model_name.lower():
            base_path = self.models_dir / "mistral" / "base"
        else:
            base_path = self.models_dir / model_name / "base"
        
        # 检查路径是否存在且包含模型文件
        if base_path.exists() and (base_path / "config.json").exists():
            return base_path
        
        return None
    
    def _find_model_path(self, model_name: str) -> Optional[Path]:
        """查找模型路径（尝试多个可能的位置）"""
        possible_paths = [
            self.models_dir / "models" / "qwen" / "base",
            self.models_dir / "qwen" / "base",
            self.models_dir / model_name,
            Path("models") / "cache" / model_name,
            Path(".cache") / "huggingface" / "hub" / model_name
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "config.json").exists():
                logger.info(f"📁 找到模型路径: {path}")
                return path
        
        return None
    
    def _convert_to_gguf(self, model_name: str, base_path: Path) -> Optional[str]:
        """转换模型为GGUF格式"""
        try:
            # 创建量化目录
            if "qwen" in model_name.lower():
                quant_dir = self.models_dir / "qwen" / "quantized"
            elif "mistral" in model_name.lower():
                quant_dir = self.models_dir / "mistral" / "quantized"
            else:
                quant_dir = self.models_dir / model_name / "quantized"
            
            quant_dir.mkdir(parents=True, exist_ok=True)
            
            # GGUF输出路径
            gguf_path = quant_dir / f"{model_name}_Q4_K_M.gguf"
            
            if gguf_path.exists():
                logger.info(f"✅ GGUF模型已存在: {gguf_path}")
                return str(gguf_path)
            
            logger.info(f"🔄 转换模型为GGUF格式...")
            logger.info(f"   源路径: {base_path}")
            logger.info(f"   目标路径: {gguf_path}")
            
            # 执行转换
            self.converter.convert_format(
                str(base_path),
                "gguf",
                str(gguf_path),
                "Q4_K_M"
            )
            
            # 验证转换结果
            if gguf_path.exists():
                logger.info(f"✅ GGUF模型已保存: {gguf_path}")
                return str(gguf_path)
            else:
                logger.error(f"❌ GGUF转换失败，文件不存在")
                return None
                
        except Exception as e:
            logger.error(f"❌ GGUF转换失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def verify_setup(self, model_name: str = "qwen2.5-7b-zh") -> bool:
        """验证模型设置是否成功"""
        logger.info("=" * 70)
        logger.info(f"🔍 验证模型设置: {model_name}")
        logger.info("=" * 70)
        
        # 检查HF格式
        hf_path = self._get_downloaded_model_path(model_name)
        if not hf_path:
            hf_path = self._find_model_path(model_name)
        
        hf_ok = hf_path and hf_path.exists() and (hf_path / "config.json").exists()
        
        # 检查GGUF格式
        if "qwen" in model_name.lower():
            gguf_path = self.models_dir / "qwen" / "quantized" / f"{model_name}_Q4_K_M.gguf"
        elif "mistral" in model_name.lower():
            gguf_path = self.models_dir / "mistral" / "quantized" / f"{model_name}_Q4_K_M.gguf"
        else:
            gguf_path = self.models_dir / model_name / "quantized" / f"{model_name}_Q4_K_M.gguf"
        
        gguf_ok = gguf_path.exists()
        
        logger.info(f"   HF格式: {'✅' if hf_ok else '❌'} {hf_path if hf_ok else '不存在'}")
        logger.info(f"   GGUF格式: {'✅' if gguf_ok else '❌'} {gguf_path if gguf_ok else '不存在'}")
        logger.info("=" * 70)
        
        return hf_ok or gguf_ok

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="VisionAI-ClipsMaster 模型初始化（集成智能推荐下载器）"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen2.5-7b-zh",
        help="模型名称 (默认: qwen2.5-7b-zh)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="仅验证模型设置，不执行下载"
    )
    
    args = parser.parse_args()
    
    setup = ModelSetup()
    
    if args.verify_only:
        # 仅验证
        success = setup.verify_setup(args.model)
        sys.exit(0 if success else 1)
    else:
        # 执行设置
        success, hf_path, gguf_path = setup.setup_base_model(args.model)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

