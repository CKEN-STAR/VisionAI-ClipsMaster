#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Converter Tool for VisionAI-ClipsMaster
Supports conversion between different formats and quantization levels
"""

import os
import sys
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
            'Q4_K_S': {'bits': 4, 'type': 'k-quants'},
            'Q5_K_S': {'bits': 5, 'type': 'k-quants'},
            'Q6_K': {'bits': 6, 'type': 'k-quants'},
            'Q8_0': {'bits': 8, 'type': 'normal'},
            'F16': {'bits': 16, 'type': 'float'},
            'F32': {'bits': 32, 'type': 'float'},
            'BF16': {'bits': 16, 'type': 'bfloat'},
            'TQ1_0': {'bits': 1, 'type': 'ternary'},
            'TQ2_0': {'bits': 2, 'type': 'ternary'}
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
        """
        Convert to GGUF format with specified quantization

        Two-step process:
        1. Convert HF model to F16 GGUF format
        2. Quantize F16 GGUF to target quantization (if needed)
        """
        if not output_path:
            output_path = f"converted_model_{quant_type}.gguf"

        # 验证源模型路径
        model_path_obj = Path(model_path)
        if not model_path_obj.exists():
            raise FileNotFoundError(f"Source model not found at {model_path}")

        # 创建输出目录
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # K-quants需要两步转换
        k_quants = ['Q4_K_M', 'Q5_K', 'Q2_K', 'Q4_K_S', 'Q5_K_S', 'Q6_K']
        needs_quantize = quant_type in k_quants

        # Step 1: Convert HF to F16 GGUF
        if needs_quantize:
            # 创建临时F16文件
            temp_f16_path = output_path_obj.parent / f"{output_path_obj.stem}_temp_f16.gguf"
            self.logger.info(f"K-quants detected, using two-step conversion:")
            self.logger.info(f"  Step 1: HF -> F16 GGUF (temp file)")
            self.logger.info(f"  Step 2: F16 GGUF -> {quant_type} GGUF")
            intermediate_path = temp_f16_path
            intermediate_type = 'f16'
        else:
            # 直接转换到目标格式
            intermediate_path = output_path_obj
            # convert_hf_to_gguf.py支持的类型
            type_mapping = {
                'F32': 'f32',
                'F16': 'f16',
                'BF16': 'bf16',
                'Q8_0': 'q8_0',
                'TQ1_0': 'tq1_0',
                'TQ2_0': 'tq2_0'
            }
            intermediate_type = type_mapping.get(quant_type, 'f16')

        # 使用llama.cpp的转换脚本
        convert_script = Path("llama.cpp/convert_hf_to_gguf.py")
        if not convert_script.exists():
            raise FileNotFoundError(f"Conversion script not found at {convert_script}")

        # Step 1: HF to GGUF (F16 or target type)
        cmd = [
            sys.executable,
            str(convert_script),
            str(model_path_obj),
            "--outfile", str(intermediate_path),
            "--outtype", intermediate_type
        ]

        self.logger.info(f"Starting GGUF conversion (Step 1):")
        self.logger.info(f"  Source: {model_path}")
        self.logger.info(f"  Intermediate: {intermediate_path}")
        self.logger.info(f"  Type: {intermediate_type}")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )

            if result.stdout:
                self.logger.debug(f"Conversion output:\n{result.stdout}")

            if not intermediate_path.exists():
                raise FileNotFoundError(f"Intermediate file not found: {intermediate_path}")

            file_size = intermediate_path.stat().st_size
            self.logger.info(f"Step 1 completed: {file_size / 1024 / 1024:.2f} MB")

        except subprocess.CalledProcessError as e:
            error_msg = f"Step 1 failed with return code {e.returncode}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        # Step 2: Quantize (if needed)
        if needs_quantize:
            self.logger.info(f"\nStarting quantization (Step 2):")
            self.logger.info(f"  Input: {intermediate_path}")
            self.logger.info(f"  Output: {output_path_obj}")
            self.logger.info(f"  Quantization: {quant_type}")

            # 注意：这里需要llama.cpp编译的quantize工具
            # 如果没有编译，我们提供一个友好的错误信息
            quantize_exe = Path("llama.cpp/build/bin/quantize.exe")
            if not quantize_exe.exists():
                # 尝试其他可能的路径
                alt_paths = [
                    Path("llama.cpp/quantize.exe"),
                    Path("llama.cpp/build/quantize.exe"),
                    Path("llama.cpp/build/Release/quantize.exe"),
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        quantize_exe = alt_path
                        break
                else:
                    # 将F16文件移动到最终位置
                    final_f16_path = output_path_obj.parent / f"{output_path_obj.stem}_f16.gguf"

                    try:
                        if intermediate_path.exists():
                            intermediate_path.rename(final_f16_path)
                            self.logger.info(f"F16 GGUF saved to: {final_f16_path}")
                    except Exception as rename_error:
                        self.logger.warning(f"Failed to rename temp file: {rename_error}")
                        final_f16_path = intermediate_path

                    error_msg = (
                        f"Quantize tool not found. K-quants ({quant_type}) require llama.cpp to be compiled.\n"
                        f"Please either:\n"
                        f"1. Compile llama.cpp (see docs/GGUF_CONVERSION_SETUP.md)\n"
                        f"2. Use a supported quantization type: F32, F16, BF16, Q8_0\n"
                        f"\nThe F16 GGUF file has been created at: {final_f16_path}\n"
                        f"You can manually quantize it later using llama.cpp's quantize tool."
                    )
                    self.logger.warning(error_msg)

                    # 返回F16文件路径而不是抛出异常
                    self.logger.info(f"\n⚠️ Returning F16 GGUF instead of {quant_type}")
                    return str(final_f16_path)

            # 执行量化
            cmd = [
                str(quantize_exe),
                str(intermediate_path),
                str(output_path_obj),
                quant_type
            ]

            try:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )

                if result.stdout:
                    self.logger.debug(f"Quantization output:\n{result.stdout}")

                # 清理临时文件
                if intermediate_path.exists():
                    intermediate_path.unlink()
                    self.logger.debug(f"Cleaned up temp file: {intermediate_path}")

            except subprocess.CalledProcessError as e:
                error_msg = f"Step 2 (quantization) failed with return code {e.returncode}"
                if e.stderr:
                    error_msg += f"\nError: {e.stderr}"
                self.logger.error(error_msg)

                # 清理临时文件
                if intermediate_path.exists():
                    intermediate_path.unlink()

                raise RuntimeError(error_msg) from e

        # 验证最终输出
        if not output_path_obj.exists():
            raise FileNotFoundError(f"Output file not found: {output_path_obj}")

        file_size = output_path_obj.stat().st_size
        self.logger.info(f"\n✅ Successfully converted to GGUF: {output_path_obj}")
        self.logger.info(f"   File size: {file_size / 1024 / 1024:.2f} MB")
        self.logger.info(f"   Quantization: {quant_type}")

        return str(output_path_obj)
            
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