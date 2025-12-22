#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGPTQ量化器（已弃用）

⚠️ 警告：此模块已弃用！
从2025-10-23起，本项目不再支持GPTQ量化模型。

原因：
1. GPTQ量化模型需要使用AutoGPTQForCausalLM.from_quantized()加载
2. 本项目使用AutoModelForCausalLM.from_pretrained()进行训练
3. GPTQ模型不能用于LoRA微调

推荐工作流程：
1. 下载FP16原始模型
2. 使用LoRA进行微调
3. 将训练后的模型转换为GGUF格式用于推理

基于AutoGPTQ官方文档: https://github.com/PanQiWei/AutoGPTQ
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 尝试导入AutoGPTQ
try:
    from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
    from transformers import AutoTokenizer
    HAS_AUTO_GPTQ = True
except ImportError:
    logger.warning("AutoGPTQ未安装,量化功能不可用。请运行: pip install auto-gptq")
    HAS_AUTO_GPTQ = False

# 尝试导入torch
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class GPTQConfig:
    """GPTQ量化配置"""
    bits: int = 4  # 量化位数: 2, 3, 4, 8
    group_size: int = 128  # 分组大小,越小精度越高但速度越慢
    desc_act: bool = False  # 是否使用描述性激活顺序
    sym: bool = True  # 是否使用对称量化
    true_sequential: bool = True  # 是否使用真正的顺序量化
    damp_percent: float = 0.01  # 阻尼百分比
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "bits": self.bits,
            "group_size": self.group_size,
            "desc_act": self.desc_act,
            "sym": self.sym,
            "true_sequential": self.true_sequential,
            "damp_percent": self.damp_percent
        }


class GPTQQuantizer:
    """AutoGPTQ量化器"""
    
    def __init__(self):
        """初始化量化器"""
        if not HAS_AUTO_GPTQ:
            raise ImportError(
                "AutoGPTQ未安装。请运行: pip install auto-gptq\n"
                "或者: pip install auto-gptq --extra-index-url https://huggingface.github.io/autogptq-index/whl/cu118/"
            )
        
        if not HAS_TORCH:
            raise ImportError("PyTorch未安装。请运行: pip install torch")
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"GPTQ量化器初始化完成,使用设备: {self.device}")
    
    def load_quantized_model(
        self,
        model_name_or_path: str,
        quantize_config: Optional[GPTQConfig] = None,
        device_map: str = "auto",
        max_memory: Optional[Dict[int, str]] = None,
        trust_remote_code: bool = True
    ) -> tuple:
        """
        加载已量化的GPTQ模型
        
        Args:
            model_name_or_path: 模型名称或路径
            quantize_config: 量化配置,如果为None则从模型配置加载
            device_map: 设备映射策略
            max_memory: 最大内存限制,例如 {0: "4GB", "cpu": "8GB"}
            trust_remote_code: 是否信任远程代码
            
        Returns:
            (model, tokenizer) 元组
        """
        logger.info(f"加载GPTQ量化模型: {model_name_or_path}")
        
        try:
            # 加载tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name_or_path,
                trust_remote_code=trust_remote_code
            )
            
            # 准备量化配置
            if quantize_config is None:
                # 从模型配置加载
                quantize_config_dict = None
            else:
                quantize_config_dict = BaseQuantizeConfig(**quantize_config.to_dict())
            
            # 加载量化模型
            model = AutoGPTQForCausalLM.from_quantized(
                model_name_or_path,
                quantize_config=quantize_config_dict,
                device_map=device_map,
                max_memory=max_memory,
                trust_remote_code=trust_remote_code,
                use_safetensors=True  # 优先使用safetensors格式
            )
            
            logger.info(f"✅ GPTQ模型加载成功")
            logger.info(f"   模型设备: {model.device}")
            logger.info(f"   量化位数: {model.quantize_config.bits}bit")
            logger.info(f"   分组大小: {model.quantize_config.group_size}")
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"❌ 加载GPTQ模型失败: {str(e)}")
            raise
    
    def quantize_model(
        self,
        model_name_or_path: str,
        output_dir: str,
        quantize_config: GPTQConfig,
        calibration_dataset: Optional[List[str]] = None,
        batch_size: int = 1,
        use_triton: bool = False
    ) -> str:
        """
        量化模型并保存
        
        Args:
            model_name_or_path: 原始模型名称或路径
            output_dir: 输出目录
            quantize_config: 量化配置
            calibration_dataset: 校准数据集(文本列表)
            batch_size: 批次大小
            use_triton: 是否使用Triton加速
            
        Returns:
            输出目录路径
        """
        logger.info(f"开始量化模型: {model_name_or_path}")
        logger.info(f"量化配置: {quantize_config.bits}bit, group_size={quantize_config.group_size}")
        
        try:
            # 加载tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name_or_path,
                trust_remote_code=True
            )
            
            # 准备校准数据
            if calibration_dataset is None:
                # 使用默认校准数据
                calibration_dataset = self._get_default_calibration_data()
            
            # 准备量化配置
            quantize_config_obj = BaseQuantizeConfig(**quantize_config.to_dict())
            
            # 加载模型
            logger.info("加载原始模型...")
            model = AutoGPTQForCausalLM.from_pretrained(
                model_name_or_path,
                quantize_config=quantize_config_obj,
                trust_remote_code=True
            )
            
            # 准备校准数据
            logger.info(f"准备校准数据: {len(calibration_dataset)}条样本")
            examples = []
            for text in calibration_dataset[:128]:  # 最多使用128条样本
                examples.append(tokenizer(text, return_tensors="pt"))
            
            # 执行量化
            logger.info("执行量化...")
            model.quantize(
                examples,
                batch_size=batch_size,
                use_triton=use_triton
            )
            
            # 保存量化模型
            logger.info(f"保存量化模型到: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)
            model.save_quantized(output_dir, use_safetensors=True)
            tokenizer.save_pretrained(output_dir)
            
            logger.info(f"✅ 模型量化完成: {output_dir}")
            return output_dir
            
        except Exception as e:
            logger.error(f"❌ 模型量化失败: {str(e)}")
            raise
    
    def _get_default_calibration_data(self) -> List[str]:
        """获取默认校准数据"""
        return [
            "这是一段用于模型量化校准的示例文本。",
            "The quick brown fox jumps over the lazy dog.",
            "人工智能技术正在快速发展,改变着我们的生活。",
            "Machine learning models require careful calibration for optimal performance.",
            "短剧混剪需要精准的字幕处理和剧情分析能力。",
            "Video editing with AI can significantly improve content quality.",
            "数据处理是关键环节,实时渲染需要强大硬件。",
            "Natural language processing enables better understanding of context.",
        ] * 16  # 重复以达到足够的样本数
    
    def get_model_info(self, model_path: str) -> Dict[str, Any]:
        """
        获取量化模型信息
        
        Args:
            model_path: 模型路径
            
        Returns:
            模型信息字典
        """
        try:
            # 检查配置文件
            config_path = Path(model_path) / "quantize_config.json"
            if not config_path.exists():
                return {"error": "未找到量化配置文件"}
            
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # 估算模型大小
            model_files = list(Path(model_path).glob("*.safetensors")) + \
                         list(Path(model_path).glob("*.bin"))
            total_size_mb = sum(f.stat().st_size for f in model_files) / (1024 * 1024)
            
            return {
                "quantization_bits": config.get("bits", "unknown"),
                "group_size": config.get("group_size", "unknown"),
                "model_size_mb": round(total_size_mb, 2),
                "desc_act": config.get("desc_act", False),
                "sym": config.get("sym", True),
                "config": config
            }
            
        except Exception as e:
            logger.error(f"获取模型信息失败: {str(e)}")
            return {"error": str(e)}


def create_quantize_config(
    bits: int = 4,
    group_size: int = 128,
    desc_act: bool = False
) -> GPTQConfig:
    """
    创建量化配置的便捷函数
    
    Args:
        bits: 量化位数(2, 3, 4, 8)
        group_size: 分组大小
        desc_act: 是否使用描述性激活顺序
        
    Returns:
        GPTQConfig对象
    """
    return GPTQConfig(
        bits=bits,
        group_size=group_size,
        desc_act=desc_act
    )


if __name__ == "__main__":
    # 示例使用
    if HAS_AUTO_GPTQ:
        quantizer = GPTQQuantizer()
        
        # 示例1: 加载已量化模型
        # model, tokenizer = quantizer.load_quantized_model(
        #     "TheBloke/Llama-2-7B-GPTQ",
        #     quantize_config=create_quantize_config(bits=4)
        # )

        # 示例2: 量化新模型
        # output_dir = quantizer.quantize_model(
        #     "Qwen/Qwen3-1.7B-Instruct",
        #     "models/qwen/qwen3-1.7b-gptq-int4",
        #     quantize_config=create_quantize_config(bits=4, group_size=128)
        # )
        
        print("GPTQ量化器初始化成功")
    else:
        print("AutoGPTQ未安装,请先安装: pip install auto-gptq")

