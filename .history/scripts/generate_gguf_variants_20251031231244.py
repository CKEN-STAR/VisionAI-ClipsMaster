#!/usr/bin/env python
"""
生成GGUF模型变体配置代码
"""

# 模型配置：每个元组包含9个元素
# (模型key, 参数量, FP16大小GB, Q2_K大小GB, Q4_K_M大小GB, Q5_K大小GB, Q8_0大小GB, 最小内存GB, CPU兼容)
MODELS = [
    ("qwen3-0.6b", "0.5B", 1.0, 0.2, 0.3, 0.4, 0.55, 2.5, True),
    ("Qwen3-1.7B", "1.5B", 3.0, 0.6, 0.9, 1.1, 1.6, 5.5, True),
    ("qwen3-1.7b", "3B", 6.0, 1.2, 1.8, 2.2, 3.2, 7.0, True),
    ("Qwen3-1.7B", "7B", 14.0, 2.8, 4.1, 5.0, 7.5, 10.0, False),
    ("qwen3-32b", "14B", 28.0, 5.6, 8.2, 10.0, 15.0, 14.0, False),
    ("qwen3-32b", "32B", 64.0, 12.8, 18.5, 22.5, 34.0, 20.0, False),
    ("mistral-7b", "7B", 14.4, 2.9, 4.1, 5.1, 7.7, 8.0, True),
    ("mistral-12b-nemo", "12B", 24.0, 4.8, 7.0, 8.5, 13.0, 12.0, False),
    ("mistral-24b-small", "24B", 48.0, 9.6, 14.0, 17.0, 26.0, 16.0, False),
    ("mistral-large2", "123B", 123.0, 24.6, 35.0, 42.5, 66.0, 32.0, False),
]

# GGUF量化配置：(类型, 质量保持率, 推理速度因子)
GGUF_QUANTS = [
    ("Q2_K", 0.85, 0.95),
    ("Q4_K_M", 0.95, 0.85),
    ("Q5_K", 0.97, 0.80),
    ("Q8_0", 0.99, 0.75),
]

def generate_variant_code(model_key, param_size, fp16_size, q2k_size, q4km_size, q5k_size, q8_size, min_mem, cpu_compat):
    """生成单个模型的所有变体代码"""
    
    # 确定显示名称
    if "qwen" in model_key:
        display_prefix = f"Qwen3-{param_size}-Instruct"
        lang = "中文"
    else:
        if "nemo" in model_key:
            display_prefix = f"Mistral-Nemo-{param_size}-Instruct"
        elif "small" in model_key:
            display_prefix = f"Mistral-Small-{param_size}-Instruct"
        elif "large" in model_key:
            display_prefix = f"Mistral-Large-2-Instruct"
        else:
            display_prefix = f"Mistral-{param_size}-Instruct"
        lang = "英文"
    
    # 大小映射
    size_map = {
        "Q2_K": q2k_size,
        "Q4_K_M": q4km_size,
        "Q5_K": q5k_size,
        "Q8_0": q8_size,
    }
    
    # 内存需求映射（GGUF推理内存 = 模型大小 + 2GB缓冲）
    mem_map = {
        "Q2_K": q2k_size + 2.0,
        "Q4_K_M": q4km_size + 2.0,
        "Q5_K": q5k_size + 2.5,
        "Q8_0": q8_size + 3.0,
    }
    
    code_lines = []
    code_lines.append(f'            # {display_prefix} {lang}模型 - 4个GGUF变体')
    code_lines.append(f'            "{model_key}": [')
    
    for quant_type, quality, speed in GGUF_QUANTS:
        size_gb = size_map[quant_type]
        mem_gb = mem_map[quant_type]
        
        code_lines.append(f'                ModelVariant(')
        code_lines.append(f'                    name="{display_prefix}-{quant_type}",')
        code_lines.append(f'                    quantization=QuantizationType.{quant_type},')
        code_lines.append(f'                    size_gb={size_gb},')
        code_lines.append(f'                    memory_requirement_gb={mem_gb},')
        code_lines.append(f'                    inference_speed_factor={speed},')
        code_lines.append(f'                    quality_retention={quality},')
        code_lines.append(f'                    cpu_compatible={cpu_compat},')
        code_lines.append(f'                    gpu_memory_min_gb={mem_gb}')
        code_lines.append(f'                ),')
    
    code_lines.append(f'            ],')
    code_lines.append('')
    
    return '\n'.join(code_lines)

def main():
    """生成所有模型变体代码"""
    print("=" * 80)
    print("生成GGUF模型变体配置代码")
    print("=" * 80)
    print()
    
    all_code = []
    all_code.append("        return {")
    
    for model_data in MODELS:
        code = generate_variant_code(*model_data)
        all_code.append(code)
    
    all_code.append("        }")
    
    full_code = '\n'.join(all_code)
    
    # 保存到文件
    output_file = "scripts/generated_gguf_variants.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_code)
    
    print(f"✅ 代码已生成并保存到: {output_file}")
    print(f"📊 总计生成: {len(MODELS)} 个模型 × 4 个GGUF变体 = {len(MODELS) * 4} 个变体")
    print()
    print("请将生成的代码复制到 src/core/quantization_analysis.py 的 _initialize_model_variants 方法中")

if __name__ == "__main__":
    main()

