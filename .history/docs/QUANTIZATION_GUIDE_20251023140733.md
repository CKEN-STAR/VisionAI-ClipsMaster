# VisionAI-ClipsMaster 量化系统使用指南

## 📋 概述

本指南介绍如何使用VisionAI-ClipsMaster的量化系统,降低模型对设备需求,实现低配设备上的模型训练和推理。

## 🎯 核心功能

### 1. AutoGPTQ量化 (INT4/INT8)
- **用途**: 离线量化,生成压缩模型
- **优势**: 模型体积减少75%(INT4)或50%(INT8)
- **适用场景**: 需要长期使用的生产环境

### 2. bitsandbytes量化 (LLM.int8())
- **用途**: 动态量化,加载时自动压缩
- **优势**: 无需预先量化,即插即用
- **适用场景**: 快速测试和开发

### 3. QLoRA微调
- **用途**: 在量化模型上进行LoRA微调
- **优势**: 4GB显存即可微调7B模型
- **适用场景**: 低配设备的投喂训练

## 📦 安装依赖

### 基础依赖
```bash
pip install torch transformers
```

### AutoGPTQ (可选)
```bash
# CUDA 11.8
pip install auto-gptq --extra-index-url https://huggingface.github.io/autogptq-index/whl/cu118/

# CUDA 12.1
pip install auto-gptq --extra-index-url https://huggingface.github.io/autogptq-index/whl/cu121/
```

### bitsandbytes (可选)
```bash
# Linux/Mac
pip install bitsandbytes

# Windows
pip install bitsandbytes-windows
```

### PEFT (QLoRA支持)
```bash
pip install peft accelerate
```

## ⚠️ 重要更新（2025-10-23）

**GPTQ量化已弃用！**

从2025-10-23起，本项目不再支持GPTQ量化模型用于训练。

### 推荐工作流程

1. **训练阶段**：下载FP16原始模型 → 使用LoRA进行微调
2. **推理阶段**：将训练后的模型转换为GGUF格式（INT4/INT8量化）

### 原因

- GPTQ量化模型需要使用`AutoGPTQForCausalLM.from_quantized()`加载
- 本项目使用`AutoModelForCausalLM.from_pretrained()`进行训练
- GPTQ模型不能用于LoRA微调

## 🚀 使用示例

### 示例1: 推荐工作流程（FP16训练 + GGUF推理）

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

# 1. 下载FP16原始模型
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")

# 2. 使用LoRA进行微调
lora_config = LoraConfig(
    r=16,
    lora_alpha=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# 3. 训练模型
# ... 训练代码 ...

# 4. 保存训练后的模型
model.save_pretrained("models/qwen2.5-1.5b/finetuned")

# 5. 转换为GGUF格式用于推理
# 使用llama.cpp/convert_hf_to_gguf.py
```

### 示例2: 使用AutoGPTQ加载量化模型（已弃用）

⚠️ **此方法已弃用，仅供参考**

```python
from src.core.gptq_quantizer import GPTQQuantizer, create_quantize_config

# 初始化量化器
quantizer = GPTQQuantizer()

# 加载已量化的模型
model, tokenizer = quantizer.load_quantized_model(
    "TheBloke/Qwen2.5-7B-GPTQ",  # Hugging Face上的量化模型
    quantize_config=create_quantize_config(bits=4, group_size=128)
)

# 使用模型进行推理
inputs = tokenizer("你好,请介绍一下自己", return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

### 示例2: 使用bitsandbytes加载8bit模型

```python
from src.core.bnb_quantizer import BnBQuantizer

# 初始化量化器
quantizer = BnBQuantizer()

# 加载8bit模型(LLM.int8())
model, tokenizer = quantizer.load_model_8bit(
    "Qwen/Qwen2.5-7B-Instruct",
    device_map="auto",
    llm_int8_threshold=6.0
)

# 使用模型
inputs = tokenizer("Hello, how are you?", return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_length=50)
print(tokenizer.decode(outputs[0]))
```

### 示例3: 使用bitsandbytes加载4bit模型

```python
from src.core.bnb_quantizer import BnBQuantizer

# 初始化量化器
quantizer = BnBQuantizer()

# 加载4bit模型(QLoRA)
model, tokenizer = quantizer.load_model_4bit(
    "Qwen/Qwen2.5-7B-Instruct",
    device_map="auto",
    compute_dtype="float16",
    use_double_quant=True,  # 双重量化,进一步节省内存
    quant_type="nf4"  # NF4量化(推荐)
)

# 查看内存占用
memory_info = quantizer.get_memory_footprint(model)
print(f"模型内存占用: {memory_info['model_memory_gb']}GB")
```

### 示例4: QLoRA微调(投喂训练)

```python
from src.training.model_fine_tuner import ModelFineTuner
import json

# 创建微调器
tuner = ModelFineTuner()

# 配置QLoRA训练
training_config = {
    "quantization": {
        "enabled": True,
        "load_in_4bit": True,  # 启用4bit量化
        "bnb_4bit_compute_dtype": "float16",
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_use_double_quant": True
    },
    "lora": {
        "enabled": True,
        "r": 16,  # LoRA秩
        "lora_alpha": 32,
        "lora_dropout": 0.1
    },
    "training": {
        "batch_size": 1,
        "gradient_accumulation_steps": 8,
        "learning_rate": 2e-5,
        "num_epochs": 3
    }
}

# 准备训练数据(原片字幕→爆款字幕对)
training_data_path = "data/training/my_training_data.json"

# 开始训练
result = tuner.train(
    language="zh",  # 中文模型
    training_data_path=training_data_path,
    training_config=training_config
)

print(f"训练完成: {result['success']}")
print(f"输出目录: {result['output_dir']}")
```

### 示例5: 量化新模型

```python
from src.core.gptq_quantizer import GPTQQuantizer, create_quantize_config

# 初始化量化器
quantizer = GPTQQuantizer()

# 准备校准数据(用于量化优化)
calibration_data = [
    "这是一段用于模型量化校准的示例文本。",
    "短剧混剪需要精准的字幕处理和剧情分析能力。",
    # ... 更多校准数据
]

# 量化模型
output_dir = quantizer.quantize_model(
    model_name_or_path="Qwen/Qwen2.5-7B-Instruct",
    output_dir="models/qwen/qwen2.5-7b-gptq-int4",
    quantize_config=create_quantize_config(bits=4, group_size=128),
    calibration_dataset=calibration_data
)

print(f"量化模型已保存到: {output_dir}")
```

## 📊 性能对比

### 内存占用对比 (Qwen2.5-7B模型)

| 量化方式 | 模型大小 | 内存需求 | 精度保持 | 推理速度 |
|---------|---------|---------|---------|---------|
| FP16 (原始) | 14GB | 16GB | 100% | 1.0x |
| INT8 (LLM.int8()) | 7GB | 8GB | 95% | 0.9x |
| INT4 (GPTQ) | 3.5GB | 4GB | 90% | 0.8x |
| INT4 (NF4) | 3.5GB | 4GB | 92% | 0.8x |

### 设备需求对比

| 设备配置 | 推荐量化方式 | 可训练模型 |
|---------|-------------|-----------|
| 4GB显存 | INT4 + QLoRA | Qwen2.5-7B |
| 8GB显存 | INT8 + LoRA | Qwen2.5-7B |
| 12GB显存 | INT4 | Qwen2.5-14B |
| 24GB显存 | FP16 | Qwen2.5-32B |

## ⚙️ 配置说明

### GPTQ配置参数

```python
GPTQConfig(
    bits=4,              # 量化位数: 2, 3, 4, 8
    group_size=128,      # 分组大小,越小精度越高但速度越慢
    desc_act=False,      # 是否使用描述性激活顺序
    sym=True,            # 是否使用对称量化
    true_sequential=True # 是否使用真正的顺序量化
)
```

### bitsandbytes配置参数

```python
BnBQuantConfig(
    load_in_8bit=False,              # 是否加载为8bit
    load_in_4bit=True,               # 是否加载为4bit
    llm_int8_threshold=6.0,          # LLM.int8()离群值阈值
    bnb_4bit_compute_dtype="float16", # 4bit计算数据类型
    bnb_4bit_use_double_quant=True,  # 是否使用双重量化
    bnb_4bit_quant_type="nf4"        # 4bit量化类型: "fp4" or "nf4"
)
```

## 🔧 故障排除

### 问题1: AutoGPTQ安装失败
```bash
# 解决方案: 使用预编译wheel
pip install auto-gptq --extra-index-url https://huggingface.github.io/autogptq-index/whl/cu118/
```

### 问题2: bitsandbytes在Windows上不可用
```bash
# 解决方案: 使用Windows版本
pip install bitsandbytes-windows
```

### 问题3: CUDA内存不足
```python
# 解决方案: 使用更激进的量化或启用CPU offload
model, tokenizer = quantizer.load_model_4bit(
    "Qwen/Qwen2.5-7B-Instruct",
    device_map="auto",
    max_memory={0: "3GB", "cpu": "8GB"}  # 限制GPU内存,使用CPU辅助
)
```

## 📚 参考资料

- [AutoGPTQ官方文档](https://github.com/PanQiWei/AutoGPTQ)
- [bitsandbytes官方文档](https://github.com/TimDettmers/bitsandbytes)
- [Hugging Face量化指南](https://huggingface.co/docs/transformers/main_classes/quantization)
- [QLoRA论文](https://arxiv.org/abs/2305.14314)
- [PEFT文档](https://huggingface.co/docs/peft)

## 💡 最佳实践

1. **开发阶段**: 使用bitsandbytes 4bit量化,快速迭代
2. **生产部署**: 使用AutoGPTQ量化,获得最佳性能
3. **投喂训练**: 使用QLoRA,在低配设备上微调
4. **内存优化**: 启用梯度检查点和双重量化
5. **质量保证**: 使用NF4量化类型,保持更高精度

