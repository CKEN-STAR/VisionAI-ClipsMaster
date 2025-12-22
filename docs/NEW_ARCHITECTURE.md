# VisionAI-ClipsMaster 新架构说明

> 📅 更新日期：2025-01
> 
> 🎯 架构版本：v2.0 - FP16+QLoRA+GGUF

## 📋 架构概述

项目已从GPTQ架构迁移到更现代化的FP16+QLoRA+GGUF架构，实现训练和推理的完全分离。

### 旧架构（已废弃）
```
GPTQ量化模型 → QLoRA训练 → 保存LoRA适配器 → ❌ 无法转换为GGUF
```

**问题**：
- GPTQ模型无法转换为GGUF格式
- 训练后的模型无法用于推理
- 训练和推理流程断裂

### 新架构（推荐）
```
FP16基础模型 → QLoRA训练（4bit量化） → 合并LoRA适配器 → 转换为GGUF → 推理
```

**优势**：
- ✅ 完整的训练→推理流程
- ✅ 训练时内存需求与GPTQ相同（4bit量化）
- ✅ 推理时使用高效的GGUF格式
- ✅ 支持多级GGUF量化（Q2_K/Q4_K_M/Q5_K/Q8_0）

## 🔄 完整工作流程

### 1. 下载阶段
```bash
# 下载FP16基础模型（约3GB）
python scripts/download_model.py --model qwen2.5-1.5b --format fp16
```

**配置文件**：`configs/models/available_models/qwen2.5-1.5b-zh.yaml`
```yaml
model:
  model_format: fp16  # FP16格式
  size_fp16: 3.0GB    # FP16模型大小

download:
  fp16_model:
    modelscope_url: https://www.modelscope.cn/models/Qwen/Qwen2.5-1.5B-Instruct
```

### 2. 训练阶段
```python
from src.training.zh_trainer import ZhTrainer

trainer = ZhTrainer()
result = trainer.train(training_data)

# 训练流程：
# 1. 加载FP16基础模型（3GB）
# 2. 使用QLoRA进行4bit量化训练（内存需求：8GB显存）
# 3. 保存LoRA适配器（约100MB）
# 4. 合并LoRA适配器到FP16基础模型
# 5. 转换为GGUF格式（Q4_K_M，约0.9GB）
```

**训练配置**：
```python
qlora_config = {
    "load_in_4bit": True,                    # 4bit量化
    "bnb_4bit_compute_dtype": "float16",     # 计算精度
    "bnb_4bit_use_double_quant": True,       # 双重量化
    "bnb_4bit_quant_type": "nf4"             # NF4量化类型
}

lora_config = {
    "r": 16,                                 # LoRA秩
    "lora_alpha": 32,                        # LoRA alpha
    "target_modules": ["q_proj", "v_proj"],  # 目标模块
    "lora_dropout": 0.1                      # Dropout
}
```

### 3. 推理阶段
```python
from src.models.qwen import QwenModel

# 优先加载GGUF模型
model = QwenModel(model_path="models/qwen2.5-1.5b/gguf/q4_k_m.gguf")

# 如果GGUF不存在，回退到FP16模型
# model = QwenModel(model_path="models/qwen2.5-1.5b/fp16")
```

## 📊 内存需求对比

| 阶段 | 旧架构（GPTQ） | 新架构（FP16+QLoRA+GGUF） | 说明 |
|------|---------------|-------------------------|------|
| **下载大小** | 0.75GB (GPTQ INT4) | 3GB (FP16) | FP16更大 |
| **训练内存** | 8GB显存 | 8GB显存 | **相同**（都用QLoRA 4bit） |
| **推理内存** | 4GB | 4GB | **相同**（都用量化模型） |
| **训练后可用** | ❌ 不能转GGUF | ✅ 能转GGUF | **关键区别** |

## 🎯 GGUF量化级别

| 量化级别 | 模型大小 | 质量保留 | 推荐场景 |
|---------|---------|---------|---------|
| **Q2_K** | 0.6GB | 85% | 极低配设备（4GB内存） |
| **Q4_K_M** | 0.9GB | 95% | **推荐**（8GB内存） |
| **Q5_K** | 1.1GB | 97% | 高质量（12GB内存） |
| **Q8_0** | 1.6GB | 99% | 极高质量（16GB内存） |

## 🔧 迁移指南

### 从GPTQ迁移到FP16+GGUF

1. **删除旧的GPTQ模型**：
```bash
rm -rf models/qwen2.5-1.5b/int4
rm -rf models/qwen2.5-1.5b/int8
```

2. **下载FP16模型**：
```bash
python scripts/download_model.py --model qwen2.5-1.5b --format fp16
```

3. **重新训练**（如果有训练需求）：
```bash
python scripts/train_model.py --model qwen2.5-1.5b --data training_data/
```

4. **转换为GGUF**（训练后自动完成，也可手动转换）：
```bash
python scripts/convert_to_gguf.py --model models/qwen2.5-1.5b/fp16 --quant Q4_K_M
```

## 📝 配置文件变更

### 模型配置（YAML）

**旧配置**（已废弃）：
```yaml
model:
  model_format: gptq
  size_int4: 0.75GB
  size_int8: 1.5GB

quantization:
  gptq_config:
    bits: 4
    group_size: 128
```

**新配置**（推荐）：
```yaml
model:
  model_format: fp16
  size_fp16: 3.0GB
  size_gguf_q4: 0.9GB
  size_gguf_q8: 1.6GB

quantization:
  gguf_default_level: Q4_K_M
  gguf_emergency_level: Q2_K
  gguf_performance_level: Q8_0
  
  qlora_config:  # 训练时量化
    load_in_4bit: true
    bnb_4bit_compute_dtype: float16
    bnb_4bit_use_double_quant: true
    bnb_4bit_quant_type: nf4

download:
  fp16_model:
    modelscope_url: https://www.modelscope.cn/models/Qwen/Qwen2.5-1.5B-Instruct
  gguf_models:
    q4_k_m:
      modelscope_url: https://www.modelscope.cn/models/Qwen/Qwen2.5-1.5B-Instruct-GGUF
      filename: qwen2_5-1_5b-instruct-q4_k_m.gguf
```

## 🚀 性能对比

### 训练性能
- **内存占用**：相同（8GB显存）
- **训练速度**：相同（都用4bit量化）
- **训练质量**：FP16基础模型质量更高

### 推理性能
- **内存占用**：相同（4GB）
- **推理速度**：GGUF更快（llama.cpp优化）
- **推理质量**：GGUF Q4_K_M ≈ GPTQ INT4

## 📚 相关文档

- [GGUF转换指南](GGUF_CONVERSION_SETUP.md)
- [QLoRA训练指南](QLORA_TRAINING.md)
- [模型配置说明](MODEL_CONFIG.md)

## ❓ 常见问题

### Q1: 为什么要废弃GPTQ？
A: GPTQ模型无法转换为GGUF格式，导致训练后的模型无法用于推理。新架构解决了这个问题。

### Q2: 训练内存需求会增加吗？
A: 不会。新架构使用QLoRA 4bit量化，内存需求与GPTQ相同（8GB显存）。

### Q3: 已有的GPTQ模型怎么办？
A: GPTQ模型仍可用于推理，但不推荐用于训练。建议下载FP16模型进行训练。

### Q4: 如何选择GGUF量化级别？
A: 推荐使用Q4_K_M（95%质量，0.9GB）。如果内存受限，使用Q2_K；如果追求质量，使用Q8_0。

### Q5: 旧的训练数据还能用吗？
A: 可以。训练数据格式没有变化，可以直接用于新架构的训练。

## 🔗 技术参考

- [llama.cpp GGUF文档](https://github.com/ggerganov/llama.cpp)
- [PEFT QLoRA文档](https://github.com/huggingface/peft)
- [bitsandbytes文档](https://github.com/TimDettmers/bitsandbytes)
- [Qwen2.5官方GGUF模型](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF)

