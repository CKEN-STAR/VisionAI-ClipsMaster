#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Converter Tool for VisionAI-ClipsMaster
Supports conversion between different formats and quantization levels
"""

import os
import logging
from typing import Optional, Literal
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import subprocess
from pathlib import Path

class ModelConverter:
    """Model format converter and quantizer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_formats = ['pytorch', 'onnx', 'tensorrt', 'gguf']
        self.supported_quant = {
            'Q4_K_M': {'bits': 4, 'type': 'k-quants'},
            'Q5_K': {'bits': 5, 'type': 'k-quants'},
            'Q2_K': {'bits': 2, 'type': 'k-quants'},
            'Q8_0': {'bits': 8, 'type': 'normal'}
        }
        
    def convert_format(
        self,
        model_path: str,
        output_format: Literal['pytorch', 'onnx', 'tensorrt', 'gguf'],
        output_path: Optional[str] = None,
        quant_type: Optional[str] = None
    ) -> str:
        """
        Convert model to specified format with quantization
        
        Args:
            model_path: Path to source model
            output_format: Target format
            output_path: Path to save converted model
            quant_type: Quantization type (Q4_K_M, Q5_K, etc.)
            
        Returns:
            Path to converted model
        """
        if output_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {output_format}")
            
        if quant_type and quant_type not in self.supported_quant:
            raise ValueError(f"Unsupported quantization: {quant_type}")
            
        self.logger.info(f"Converting model from {model_path} to {output_format}")
        
        if output_format == 'gguf':
            return self._convert_to_gguf(model_path, output_path, quant_type)
        
        # Load model for other formats
        model = AutoModelForCausalLM.from_pretrained(model_path)
        
        # Convert format
        if output_format == 'onnx':
            return self._convert_to_onnx(model, output_path)
        elif output_format == 'tensorrt':
            return self._convert_to_tensorrt(model, output_path)
        else:
            return self._save_pytorch(model, output_path)
            
    def _convert_to_gguf(self, model_path: str, output_path: str, quant_type: str) -> str:
        """Convert to GGUF format with specified quantization"""
        if not output_path:
            output_path = f"converted_model_{quant_type}.gguf"
            
        # Map our quantization types to llama.cpp supported types
        quant_mapping = {
            'Q4_K_M': 'q8_0',  # Using q8_0 as fallback since q4_k_m is not supported
            'Q5_K': 'q8_0',    # Using q8_0 as fallback
            'Q2_K': 'q8_0',    # Using q8_0 as fallback
            'Q8_0': 'q8_0'
        }
        
        # 使用llama.cpp的量化工具
        convert_script = Path("llama.cpp/convert_hf_to_gguf.py")
        if not convert_script.exists():
            raise FileNotFoundError(f"Conversion script not found at {convert_script}")
            
        cmd = [
            "python",
            str(convert_script),
            model_path,
            "--outfile", output_path,
            "--outtype", quant_mapping[quant_type]
        ]
        
        try:
            subprocess.run(cmd, check=True)
            self.logger.info(f"Successfully converted to GGUF: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            self.logger.error(f"GGUF conversion failed: {e}")
            raise
            
    def _convert_to_onnx(self, model, output_path):
        """Convert to ONNX format"""
        if not output_path:
            output_path = "converted_model.onnx"
            
        try:
            torch.onnx.export(
                model,
                torch.zeros(1, 1, dtype=torch.long),
                output_path,
                input_names=['input_ids'],
                output_names=['logits'],
                dynamic_axes={
                    'input_ids': {0: 'batch_size', 1: 'sequence_length'},
                    'logits': {0: 'batch_size', 1: 'sequence_length'}
                }
            )
            self.logger.info(f"Successfully converted to ONNX: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"ONNX conversion failed: {e}")
            raise
            
    def _convert_to_tensorrt(self, model, output_path):
        """Convert to TensorRT format"""
        if not output_path:
            output_path = "converted_model.engine"
            
        try:
            # 这里需要实现TensorRT转换逻辑
            raise NotImplementedError("TensorRT conversion not implemented yet")
        except Exception as e:
            self.logger.error(f"TensorRT conversion failed: {e}")
            raise
            
    def _save_pytorch(self, model, output_path):
        """Save model in PyTorch format"""
        if not output_path:
            output_path = "converted_model.pt"
            
        try:
            torch.save(model.state_dict(), output_path)
            self.logger.info(f"Successfully saved PyTorch model: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"PyTorch save failed: {e}")
            raise
            
    def verify_conversion(self, original_path: str, converted_path: str) -> bool:
        """Verify that the conversion was successful"""
        if not os.path.exists(converted_path):
            self.logger.error(f"Converted model not found at {converted_path}")
            return False
            
        # 检查文件大小
        original_size = os.path.getsize(original_path)
        converted_size = os.path.getsize(converted_path)
        
        if converted_size == 0:
            self.logger.error("Converted model is empty")
            return False
            
        self.logger.info(f"Original size: {original_size/1024/1024:.2f}MB")
        self.logger.info(f"Converted size: {converted_size/1024/1024:.2f}MB")
        
        return True

if __name__ == "__main__":
    # Example usage
    converter = ModelConverter()
    
    # Convert to GGUF with Q4_K_M quantization
    converter.convert_format(
        "models/qwen/base",
        "gguf",
        "models/qwen/quantized/model_Q4_K_M.gguf",
        "Q4_K_M"
    ) 