#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bitsandbytes量化器
实现LLM.int8()动态量化,支持8bit/4bit模型加载和训练

基于bitsandbytes官方文档: https://github.com/TimDettmers/bitsandbytes
Hugging Face集成文档: https://huggingface.co/docs/transformers/main_classes/quantization
"""

import os
import logging
from typing import Dict, Optional, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 尝试导入bitsandbytes
try:
    import bitsandbytes as bnb
    HAS_BNB = True
except ImportError:
    logger.warning("bitsandbytes未安装,量化功能不可用。请运行: pip install bitsandbytes")
    HAS_BNB = False

# 尝试导入transformers
try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig
    )
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# 尝试导入torch
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class BnBQuantConfig:
    """bitsandbytes量化配置"""
    load_in_8bit: bool = False  # 是否加载为8bit
    load_in_4bit: bool = False  # 是否加载为4bit
    llm_int8_threshold: float = 6.0  # LLM.int8()离群值阈值
    llm_int8_has_fp16_weight: bool = False  # 是否保留FP16权重
    bnb_4bit_compute_dtype: str = "float16"  # 4bit计算数据类型
    bnb_4bit_use_double_quant: bool = True  # 是否使用双重量化
    bnb_4bit_quant_type: str = "nf4"  # 4bit量化类型: "fp4" or "nf4"
    
    def to_transformers_config(self) -> 'BitsAndBytesConfig':
        """转换为Transformers的BitsAndBytesConfig"""
        if not HAS_TRANSFORMERS:
            raise ImportError("transformers未安装")
        
        # 确定计算数据类型
        if self.bnb_4bit_compute_dtype == "float16":
            compute_dtype = torch.float16
        elif self.bnb_4bit_compute_dtype == "bfloat16":
            compute_dtype = torch.bfloat16
        else:
            compute_dtype = torch.float32
        
        return BitsAndBytesConfig(
            load_in_8bit=self.load_in_8bit,
            load_in_4bit=self.load_in_4bit,
            llm_int8_threshold=self.llm_int8_threshold,
            llm_int8_has_fp16_weight=self.llm_int8_has_fp16_weight,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=self.bnb_4bit_use_double_quant,
            bnb_4bit_quant_type=self.bnb_4bit_quant_type
        )


class BnBQuantizer:
    """bitsandbytes量化器"""
    
    def __init__(self):
        """初始化量化器"""
        if not HAS_BNB:
            raise ImportError(
                "bitsandbytes未安装。请运行: pip install bitsandbytes\n"
                "Windows用户可能需要: pip install bitsandbytes-windows"
            )
        
        if not HAS_TRANSFORMERS:
            raise ImportError("transformers未安装。请运行: pip install transformers>=4.30.0")
        
        if not HAS_TORCH:
            raise ImportError("PyTorch未安装。请运行: pip install torch")
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if self.device == "cpu":
            logger.warning("⚠️ 未检测到CUDA,bitsandbytes量化需要GPU支持")
        
        logger.info(f"bitsandbytes量化器初始化完成,使用设备: {self.device}")
    
    def load_model_8bit(
        self,
        model_name_or_path: str,
        device_map: str = "auto",
        max_memory: Optional[Dict[int, str]] = None,
        llm_int8_threshold: float = 6.0,
        trust_remote_code: bool = True
    ) -> tuple:
        """
        加载8bit量化模型(LLM.int8())
        
        Args:
            model_name_or_path: 模型名称或路径
            device_map: 设备映射策略
            max_memory: 最大内存限制
            llm_int8_threshold: 离群值阈值(默认6.0)
            trust_remote_code: 是否信任远程代码
            
        Returns:
            (model, tokenizer) 元组
        """
        logger.info(f"加载8bit量化模型: {model_name_or_path}")
        
        try:
            # 创建量化配置
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=llm_int8_threshold,
                llm_int8_has_fp16_weight=False  # 不保留FP16权重以节省内存
            )
            
            # 加载tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name_or_path,
                trust_remote_code=trust_remote_code
            )
            
            # 加载模型
            model = AutoModelForCausalLM.from_pretrained(
                model_name_or_path,
                quantization_config=quantization_config,
                device_map=device_map,
                max_memory=max_memory,
                trust_remote_code=trust_remote_code
            )
            
            logger.info(f"✅ 8bit模型加载成功")
            logger.info(f"   模型设备: {model.device}")
            logger.info(f"   量化类型: LLM.int8()")
            logger.info(f"   离群值阈值: {llm_int8_threshold}")
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"❌ 加载8bit模型失败: {str(e)}")
            raise
    
    def load_model_4bit(
        self,
        model_name_or_path: str,
        device_map: str = "auto",
        max_memory: Optional[Dict[int, str]] = None,
        compute_dtype: str = "float16",
        use_double_quant: bool = True,
        quant_type: str = "nf4",
        trust_remote_code: bool = True
    ) -> tuple:
        """
        加载4bit量化模型(QLoRA)
        
        Args:
            model_name_or_path: 模型名称或路径
            device_map: 设备映射策略
            max_memory: 最大内存限制
            compute_dtype: 计算数据类型("float16", "bfloat16", "float32")
            use_double_quant: 是否使用双重量化(进一步节省内存)
            quant_type: 量化类型("nf4"推荐, "fp4"备选)
            trust_remote_code: 是否信任远程代码
            
        Returns:
            (model, tokenizer) 元组
        """
        logger.info(f"加载4bit量化模型: {model_name_or_path}")
        
        try:
            # 确定计算数据类型
            if compute_dtype == "float16":
                dtype = torch.float16
            elif compute_dtype == "bfloat16":
                dtype = torch.bfloat16
            else:
                dtype = torch.float32
            
            # 创建量化配置
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=dtype,
                bnb_4bit_use_double_quant=use_double_quant,
                bnb_4bit_quant_type=quant_type
            )
            
            # 加载tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name_or_path,
                trust_remote_code=trust_remote_code
            )
            
            # 加载模型
            model = AutoModelForCausalLM.from_pretrained(
                model_name_or_path,
                quantization_config=quantization_config,
                device_map=device_map,
                max_memory=max_memory,
                trust_remote_code=trust_remote_code
            )
            
            logger.info(f"✅ 4bit模型加载成功")
            logger.info(f"   模型设备: {model.device}")
            logger.info(f"   量化类型: {quant_type}")
            logger.info(f"   计算类型: {compute_dtype}")
            logger.info(f"   双重量化: {use_double_quant}")
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"❌ 加载4bit模型失败: {str(e)}")
            raise
    
    def load_model_with_config(
        self,
        model_name_or_path: str,
        config: BnBQuantConfig,
        device_map: str = "auto",
        max_memory: Optional[Dict[int, str]] = None,
        trust_remote_code: bool = True
    ) -> tuple:
        """
        使用自定义配置加载模型
        
        Args:
            model_name_or_path: 模型名称或路径
            config: BnBQuantConfig配置对象
            device_map: 设备映射策略
            max_memory: 最大内存限制
            trust_remote_code: 是否信任远程代码
            
        Returns:
            (model, tokenizer) 元组
        """
        logger.info(f"使用自定义配置加载模型: {model_name_or_path}")
        
        try:
            # 转换为Transformers配置
            quantization_config = config.to_transformers_config()
            
            # 加载tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_name_or_path,
                trust_remote_code=trust_remote_code
            )
            
            # 加载模型
            model = AutoModelForCausalLM.from_pretrained(
                model_name_or_path,
                quantization_config=quantization_config,
                device_map=device_map,
                max_memory=max_memory,
                trust_remote_code=trust_remote_code
            )
            
            logger.info(f"✅ 模型加载成功")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"❌ 加载模型失败: {str(e)}")
            raise
    
    def get_memory_footprint(self, model) -> Dict[str, Any]:
        """
        获取模型内存占用
        
        Args:
            model: 已加载的模型
            
        Returns:
            内存占用信息字典
        """
        try:
            # 获取模型内存占用
            memory_footprint = model.get_memory_footprint()
            memory_gb = memory_footprint / (1024 ** 3)
            
            # 获取GPU内存占用(如果可用)
            gpu_memory = {}
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    allocated = torch.cuda.memory_allocated(i) / (1024 ** 3)
                    reserved = torch.cuda.memory_reserved(i) / (1024 ** 3)
                    gpu_memory[f"cuda:{i}"] = {
                        "allocated_gb": round(allocated, 2),
                        "reserved_gb": round(reserved, 2)
                    }
            
            return {
                "model_memory_gb": round(memory_gb, 2),
                "gpu_memory": gpu_memory
            }
            
        except Exception as e:
            logger.error(f"获取内存占用失败: {str(e)}")
            return {"error": str(e)}


def create_8bit_config(llm_int8_threshold: float = 6.0) -> BnBQuantConfig:
    """
    创建8bit量化配置的便捷函数
    
    Args:
        llm_int8_threshold: 离群值阈值
        
    Returns:
        BnBQuantConfig对象
    """
    return BnBQuantConfig(
        load_in_8bit=True,
        load_in_4bit=False,
        llm_int8_threshold=llm_int8_threshold
    )


def create_4bit_config(
    compute_dtype: str = "float16",
    use_double_quant: bool = True,
    quant_type: str = "nf4"
) -> BnBQuantConfig:
    """
    创建4bit量化配置的便捷函数
    
    Args:
        compute_dtype: 计算数据类型
        use_double_quant: 是否使用双重量化
        quant_type: 量化类型
        
    Returns:
        BnBQuantConfig对象
    """
    return BnBQuantConfig(
        load_in_8bit=False,
        load_in_4bit=True,
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=use_double_quant,
        bnb_4bit_quant_type=quant_type
    )


if __name__ == "__main__":
    # 示例使用
    if HAS_BNB and HAS_TRANSFORMERS:
        quantizer = BnBQuantizer()
        
        # 示例1: 加载8bit模型
        # model, tokenizer = quantizer.load_model_8bit(
        #     "Qwen/Qwen3-1.7B-Instruct",
        #     device_map="auto"
        # )

        # 示例2: 加载4bit模型
        # model, tokenizer = quantizer.load_model_4bit(
        #     "Qwen/Qwen3-1.7B-Instruct",
        #     device_map="auto",
        #     compute_dtype="float16",
        #     quant_type="nf4"
        # )
        
        print("bitsandbytes量化器初始化成功")
    else:
        print("bitsandbytes或transformers未安装")

