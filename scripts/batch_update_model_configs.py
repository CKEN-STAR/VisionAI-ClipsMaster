#!/usr/bin/env python
"""
批量更新模型配置文件：移除GPTQ，改用FP16+GGUF
"""

import yaml
from pathlib import Path

# 模型配置映射（模型名 -> FP16大小, GGUF Q4大小, GGUF Q8大小）
MODEL_SIZES = {
    "qwen3-1.7b-zh": ("6.0GB", "1.8GB", "3.2GB"),
    "Qwen3-1.7B-zh": ("14.0GB", "4.1GB", "7.5GB"),
    "qwen3-32b-zh": ("28.0GB", "8.2GB", "15.0GB"),
    "qwen3-32b-zh": ("64.0GB", "18.5GB", "34.0GB"),
    "mistral-7b-en": ("14.4GB", "4.1GB", "7.7GB"),
    "mistral-12b-nemo-en": ("24.0GB", "7.0GB", "13.0GB"),
    "mistral-24b-small-en": ("48.0GB", "14.0GB", "26.0GB"),
    "mistral-large2-en": ("123.0GB", "35.0GB", "66.0GB"),
}

def update_model_config(yaml_path: Path):
    """更新单个模型配置文件"""
    print(f"\n处理: {yaml_path.name}")
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    model_name = config['model']['name']
    
    # 跳过已经处理过的文件
    if config['model'].get('model_format') == 'fp16':
        print(f"  ✓ 已经是FP16格式，跳过")
        return
    
    # 获取模型大小
    if model_name in MODEL_SIZES:
        fp16_size, q4_size, q8_size = MODEL_SIZES[model_name]
    else:
        print(f"  ⚠ 未找到 {model_name} 的大小配置，跳过")
        return
    
    # 1. 修改model_format
    config['model']['model_format'] = 'fp16'
    
    # 2. 更新大小信息
    config['model']['size_fp16'] = fp16_size
    config['model']['size_gguf_q4'] = q4_size
    config['model']['size_gguf_q8'] = q8_size
    
    # 移除旧的GPTQ大小字段
    config['model'].pop('size_int4', None)
    config['model'].pop('size_int8', None)
    
    # 3. 更新quantization配置
    config['quantization'] = {
        'gguf_default_level': 'Q4_K_M',
        'gguf_emergency_level': 'Q2_K',
        'gguf_performance_level': 'Q8_0',
        'qlora_config': {
            'load_in_4bit': True,
            'bnb_4bit_compute_dtype': 'float16',
            'bnb_4bit_use_double_quant': True,
            'bnb_4bit_quant_type': 'nf4'
        }
    }
    
    # 4. 更新download配置
    if 'qwen' in model_name:
        model_id = config['model']['hf_model_id']
        modelscope_id = config['model']['modelscope_id']
        
        config['download'] = {
            'fp16_model': {
                'modelscope_url': f"https://www.modelscope.cn/models/{modelscope_id}",
                'hf_mirror_url': f"https://hf-mirror.com/{model_id}",
                'hf_url': f"https://huggingface.co/{model_id}"
            },
            'gguf_models': {
                'q4_k_m': {
                    'modelscope_url': f"https://www.modelscope.cn/models/{model_id}-GGUF",
                    'hf_mirror_url': f"https://hf-mirror.com/{model_id}-GGUF",
                    'filename': f"{model_name.replace('-zh', '')}-instruct-q4_k_m.gguf"
                },
                'q8_0': {
                    'modelscope_url': f"https://www.modelscope.cn/models/{model_id}-GGUF",
                    'hf_mirror_url': f"https://hf-mirror.com/{model_id}-GGUF",
                    'filename': f"{model_name.replace('-zh', '')}-instruct-q8_0.gguf"
                }
            },
            'resume_download': True,
            'max_retries': 3,
            'timeout': 300
        }
    elif 'mistral' in model_name:
        model_id = config['model']['hf_model_id']
        
        config['download'] = {
            'fp16_model': {
                'modelscope_url': f"https://www.modelscope.cn/models/{model_id}",
                'hf_mirror_url': f"https://hf-mirror.com/{model_id}",
                'hf_url': f"https://huggingface.co/{model_id}"
            },
            'gguf_models': {
                'q4_k_m': {
                    'hf_mirror_url': f"https://hf-mirror.com/{model_id}-GGUF",
                    'hf_url': f"https://huggingface.co/{model_id}-GGUF",
                    'filename': f"{model_name.replace('-en', '')}-q4_k_m.gguf"
                },
                'q8_0': {
                    'hf_mirror_url': f"https://hf-mirror.com/{model_id}-GGUF",
                    'hf_url': f"https://huggingface.co/{model_id}-GGUF",
                    'filename': f"{model_name.replace('-en', '')}-q8_0.gguf"
                }
            },
            'resume_download': True,
            'max_retries': 3,
            'timeout': 300
        }
    
    # 保存更新后的配置
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"  ✓ 更新完成")

def main():
    """主函数"""
    config_dir = Path("configs/models/available_models")
    
    # 需要更新的文件列表
    files_to_update = [
        "qwen3-1.7b-zh.yaml",
        "Qwen3-1.7B-zh.yaml",
        "qwen3-32b-zh.yaml",
        "qwen3-32b-zh.yaml",
        "mistral-7b-en.yaml",
        "mistral-12b-nemo-en.yaml",
        "mistral-24b-small-en.yaml",
        "mistral-large2-en.yaml",
    ]
    
    print("=" * 60)
    print("批量更新模型配置文件：移除GPTQ，改用FP16+GGUF")
    print("=" * 60)
    
    for filename in files_to_update:
        yaml_path = config_dir / filename
        if yaml_path.exists():
            try:
                update_model_config(yaml_path)
            except Exception as e:
                print(f"  ✗ 更新失败: {e}")
        else:
            print(f"\n⚠ 文件不存在: {filename}")
    
    print("\n" + "=" * 60)
    print("✅ 批量更新完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

