#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
转换训练后的模型为GGUF格式

完整流程：
1. 合并LoRA适配器到基础模型
2. 转换合并后的模型为GGUF格式
3. 验证转换结果

使用方法：
    python convert_trained_model.py
"""

import sys
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def convert_trained_model(
    base_model: str = "models/qwen3-1.7b/base",
    lora_adapter: str = "models/qwen/finetuned",
    merged_output: str = "models/qwen/merged",
    gguf_output: str = "models/qwen/quantized/trained_Q4_K_M.gguf",
    quant_type: str = "Q4_K_M"
):
    """
    转换训练后的模型为GGUF格式
    
    Args:
        base_model: 基础模型路径
        lora_adapter: LoRA适配器路径
        merged_output: 合并后模型输出路径
        gguf_output: GGUF模型输出路径
        quant_type: 量化类型
    """
    from models.converters.model_converter import ModelConverter
    
    converter = ModelConverter()
    
    print("=" * 70)
    print("🚀 开始转换训练后的模型为GGUF格式")
    print("=" * 70)
    
    # 验证路径
    print("\n📋 配置信息:")
    print(f"  基础模型: {base_model}")
    print(f"  LoRA适配器: {lora_adapter}")
    print(f"  合并输出: {merged_output}")
    print(f"  GGUF输出: {gguf_output}")
    print(f"  量化类型: {quant_type}")
    
    # 检查基础模型
    if not Path(base_model).exists():
        logger.error(f"❌ 基础模型不存在: {base_model}")
        logger.info("💡 提示: 请确保基础模型已下载到指定路径")
        return False
    
    # 检查LoRA适配器
    if not Path(lora_adapter).exists():
        logger.error(f"❌ LoRA适配器不存在: {lora_adapter}")
        logger.info("💡 提示: 请先完成模型训练")
        return False
    
    try:
        # 步骤1：合并LoRA
        print("\n" + "=" * 70)
        print("步骤1/2：合并LoRA适配器到基础模型")
        print("=" * 70)
        print("⏳ 正在加载模型和适配器...")
        print("   这可能需要几分钟，请耐心等待...")
        
        merged_path = converter.merge_lora_to_base(
            base_model_path=base_model,
            lora_adapter_path=lora_adapter,
            output_path=merged_output
        )
        
        # 检查合并结果
        merged_size = Path(merged_path).stat().st_size / 1024 / 1024
        print(f"\n✅ 合并完成!")
        print(f"   输出路径: {merged_path}")
        print(f"   文件大小: {merged_size:.2f} MB")
        
        # 步骤2：转换为GGUF
        print("\n" + "=" * 70)
        print("步骤2/2：转换为GGUF格式")
        print("=" * 70)
        print(f"⏳ 正在转换为 {quant_type} 量化...")
        print("   这可能需要几分钟，请耐心等待...")
        
        gguf_path = converter.convert_format(
            model_path=merged_path,
            output_format='gguf',
            output_path=gguf_output,
            quant_type=quant_type
        )
        
        # 检查转换结果
        gguf_size = Path(gguf_path).stat().st_size / 1024 / 1024
        compression_ratio = (1 - gguf_size / merged_size) * 100
        
        print(f"\n✅ 转换完成!")
        print(f"   输出路径: {gguf_path}")
        print(f"   文件大小: {gguf_size:.2f} MB")
        print(f"   压缩率: {compression_ratio:.1f}%")
        
        # 总结
        print("\n" + "=" * 70)
        print("🎉 所有步骤完成！")
        print("=" * 70)
        print(f"\n📦 最终GGUF模型: {gguf_path}")
        print(f"📊 文件大小: {gguf_size:.2f} MB")
        print(f"🔧 量化类型: {quant_type}")
        
        print("\n💡 下一步:")
        print("  1. 使用llama-cpp-python加载GGUF模型进行推理")
        print("  2. 在UI中测试模型效果")
        print("  3. 如需其他量化类型，可重新运行转换（步骤2）")
        
        # 可选：清理合并后的模型
        print("\n⚠️  提示:")
        print(f"  合并后的模型占用 {merged_size:.2f} MB 磁盘空间")
        print(f"  如果磁盘空间紧张，可以删除: {merged_path}")
        print(f"  （删除后如需重新转换，需要重新执行合并步骤）")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("VisionAI-ClipsMaster - 训练模型转GGUF工具")
    print("=" * 70)
    
    # 默认配置
    success = convert_trained_model()
    
    if success:
        print("\n✅ 转换成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 转换失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()

