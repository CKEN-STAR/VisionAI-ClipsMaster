# VisionAI-ClipsMaster 模型训练使用指南

**指南版本**: 1.0  
**更新日期**: 2025-10-17  
**适用版本**: v1.1.0+

---

## 📚 目录

1. [快速开始](#快速开始)
2. [数据准备](#数据准备)
3. [训练配置](#训练配置)
4. [启动训练](#启动训练)
5. [监控训练](#监控训练)
6. [使用训练后的模型](#使用训练后的模型)
7. [常见问题](#常见问题)

---

## 🚀 快速开始

### 最简单的训练示例

```python
from src.training.zh_trainer import ZhTrainer

# 1. 创建训练器
trainer = ZhTrainer(use_gpu=True)

# 2. 准备训练数据
training_data = [
    {
        "original": "这是一个普通的剧本",
        "viral": "【震撼】这是一个令人震惊的爆款剧本！"
    },
    {
        "original": "今天天气很好",
        "viral": "【独家】今天的天气好到让人难以置信！"
    }
]

# 3. 启动训练
result = trainer.train(training_data)

# 4. 查看结果
print(f"训练成功: {result['success']}")
print(f"模型保存到: ./results_zh/")
```

---

## 📊 数据准备

### 数据格式要求

#### 格式1: Python字典列表（推荐）

```python
training_data = [
    {
        "original": "原始字幕文本",
        "viral": "爆款改写后的字幕文本"
    },
    {
        "original": "...",
        "viral": "..."
    }
]
```

#### 格式2: JSON文件

```json
{
    "data": [
        {
            "original": "原始字幕文本",
            "viral": "爆款改写后的字幕文本"
        }
    ]
}
```

#### 格式3: SRT字幕文件对

```python
from src.training.training_feeder import TrainingFeeder

feeder = TrainingFeeder(data_dir="data/training")

# 添加训练数据对
feeder.add_training_pair(
    original_files=["original1.srt", "original2.srt"],
    viral_file="viral.srt"
)

training_data = feeder.get_training_data()
```

### 数据质量要求

| 要求 | 说明 |
|------|------|
| 最少样本数 | 10个（推荐50+） |
| 文本长度 | 10-1000字符 |
| 语言一致性 | 中文数据用中文训练器，英文用英文训练器 |
| 数据质量 | 爆款字幕应该是高质量的改写 |

### 数据增强（可选）

```python
from src.training.data_augment import DataAugmenter

augmenter = DataAugmenter()

# 增强训练数据
augmented_data = augmenter.augment(
    training_data,
    augmentation_ratio=0.3  # 增加30%的数据
)
```

---

## ⚙️ 训练配置

### 基础配置

```python
from src.training.zh_trainer import ZhTrainer

trainer = ZhTrainer(
    model_path=None,  # 使用默认模型路径
    use_gpu=True      # 使用GPU加速
)

# 查看配置
print(trainer.config)
# 输出:
# {
#     "model_name": "Qwen2.5-7B",
#     "language": "zh",
#     "max_seq_length": 2048,
#     "batch_size": 2,
#     "learning_rate": 3e-5,
#     "epochs": 5,
#     "quantization": "Q4_K_M",
#     "memory_limit": 3.8  # GB
# }
```

### 自定义配置

```python
# 修改配置
trainer.config.update({
    "batch_size": 1,
    "learning_rate": 2e-5,
    "epochs": 3,
    "max_seq_length": 512
})
```

### 配置文件方式

编辑 `configs/training_policy.yaml`:

```yaml
zh_training:
  model_name: "qwen2.5-7b-zh"
  
  # 训练参数
  training:
    learning_rate:
      initial: 2e-5
    batch_size:
      train: 1
      gradient_accumulation_steps: 8
    epochs:
      max: 3
  
  # LoRA配置
  lora:
    rank: 16
    alpha: 32
    dropout: 0.1
```

---

## 🎯 启动训练

### 方式1: 直接调用（推荐）

```python
from src.training.zh_trainer import ZhTrainer

trainer = ZhTrainer(use_gpu=True)

# 定义进度回调
def progress_callback(progress, message):
    print(f"[{progress:.1%}] {message}")

# 启动训练
result = trainer.train(
    training_data=training_data,
    progress_callback=progress_callback
)

# 检查结果
if result['success']:
    print("✅ 训练成功！")
    print(f"模型保存到: ./results_zh/")
else:
    print(f"❌ 训练失败: {result['error']}")
```

### 方式2: 使用ModelFineTuner

```python
from src.training.model_fine_tuner import ModelFineTuner

fine_tuner = ModelFineTuner()

# 设置回调
fine_tuner.set_callbacks(
    progress_callback=lambda stage, progress: print(f"{stage}: {progress:.1%}"),
    log_callback=lambda msg: print(f"[LOG] {msg}")
)

# 启动微调
result = fine_tuner.fine_tune_model(
    language="zh",
    training_data_path="data/training_data.json",
    validation_data_path="data/validation_data.json"
)
```

### 方式3: 增量训练

```python
from src.training.zh_trainer import ZhTrainer
from src.training.model_version_manager import ModelVersionManager

trainer = ZhTrainer(use_gpu=True)
manager = ModelVersionManager(base_dir="models/qwen")

# 获取已训练的模型版本
version_info = manager.get_active_version()

# 使用新数据继续训练
result = trainer.incremental_training(
    training_data=new_training_data,
    version_info=version_info,
    num_epochs=3,
    batch_size=1,
    learning_rate=1e-5  # 更小的学习率
)
```

---

## 📈 监控训练

### 实时监控

```python
def progress_callback(progress, message):
    """进度回调函数"""
    print(f"[{progress:6.1%}] {message}")

result = trainer.train(
    training_data=training_data,
    progress_callback=progress_callback
)

# 输出示例:
# [ 5.0%] 初始化中文训练环境...
# [10.0%] 加载中文模型...
# [20.0%] 配置LoRA微调...
# [30.0%] 准备训练数据...
# [40.0%] 配置训练参数...
# [50.0%] 开始真实训练...
# [90.0%] 保存模型...
# [100.0%] 训练完成
```

### 查看训练日志

```bash
# 查看最新的训练日志
tail -f logs/training/training.log

# 查看特定训练的日志
grep "training_zh_" logs/training/training.log
```

### 训练结果分析

```python
# 查看训练结果
print(f"训练成功: {result['success']}")
print(f"训练损失: {result.get('train_loss', 'N/A')}")
print(f"验证损失: {result.get('eval_loss', 'N/A')}")
print(f"训练时间: {result.get('processing_time', 'N/A')}秒")
print(f"模型保存路径: {result.get('output_dir', 'N/A')}")
```

---

## 🔄 使用训练后的模型

### 加载训练后的模型

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# 加载基础模型
base_model_path = "Qwen/Qwen2.5-7B-Instruct"
model = AutoModelForCausalLM.from_pretrained(base_model_path)
tokenizer = AutoTokenizer.from_pretrained(base_model_path)

# 加载LoRA适配器
lora_path = "./results_zh"
model = PeftModel.from_pretrained(model, lora_path)

# 合并权重（可选）
model = model.merge_and_unload()
```

### 使用模型进行推理

```python
# 准备输入
input_text = "这是一个普通的剧本"
inputs = tokenizer(input_text, return_tensors="pt")

# 生成输出
outputs = model.generate(
    **inputs,
    max_length=256,
    temperature=0.7,
    top_p=0.9,
    do_sample=True
)

# 解码输出
result = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(result)
```

### 版本管理

```python
from src.training.model_version_manager import ModelVersionManager

manager = ModelVersionManager(base_dir="models/qwen")

# 获取所有版本
versions = manager.get_all_versions()
for version in versions:
    print(f"版本: {version['version_id']}")
    print(f"创建时间: {version['created_at']}")
    print(f"训练信息: {version['training_info']}")

# 获取活跃版本
active = manager.get_active_version()
print(f"当前活跃版本: {active['version_id']}")

# 切换版本
manager.set_active_version("v20251017_162039")

# 清理旧版本
manager.cleanup_all_except_active()
```

---

## ❓ 常见问题

### Q1: 训练需要多长时间？

**A**: 取决于数据量和硬件：
- 10个样本 + GPU: ~5-10分钟
- 100个样本 + GPU: ~30-60分钟
- 1000个样本 + GPU: ~5-10小时

### Q2: 需要多少训练数据？

**A**: 
- 最少: 10个样本（演示）
- 推荐: 50-100个样本（基础效果）
- 最佳: 500+个样本（显著改进）

### Q3: 如何处理内存不足？

**A**: 
```python
# 减小批次大小
trainer.config["batch_size"] = 1

# 启用梯度检查点
training_args.gradient_checkpointing = True

# 使用CPU训练
trainer = ZhTrainer(use_gpu=False)
```

### Q4: 如何评估训练效果？

**A**:
```python
# 使用验证集
result = trainer.train(
    training_data=train_data,
    validation_data=val_data
)

# 查看验证损失
print(f"验证损失: {result['eval_loss']}")

# 手动测试
test_input = "测试输入"
output = model.generate(...)
print(output)
```

### Q5: 如何继续训练已有模型？

**A**:
```python
# 使用增量训练
result = trainer.incremental_training(
    training_data=new_data,
    version_info=version_info,
    num_epochs=3,
    learning_rate=1e-5  # 更小的学习率
)
```

---

## 📞 获取帮助

- 查看日志: `logs/training/training.log`
- 查看示例: `examples/training_example.py`
- 运行测试: `python tests/test_real_training.py`

---

**祝您训练顺利！** 🎉

