# 模型选择策略方案

## 问题场景

当用户已经有推理模型（基础GGUF模型），然后又训练了最新模型时，系统应该如何选择使用哪个模型？

## 解决方案

### 方案1：自动切换到最新训练模型（默认策略）✅

**工作流程**：
```
1. 用户训练新模型
   ↓
2. 训练完成后自动转换为GGUF
   ↓
3. 自动注册为新版本并设置为激活版本
   ↓
4. 推理时自动使用最新训练的模型
   ↓
5. 如果训练模型不可用，自动降级到基础模型
```

**优点**：
- ✅ 符合"投喂训练"的直观体验
- ✅ 训练后立即生效
- ✅ 自动化程度高
- ✅ 保留基础模型作为降级选项

**实现方式**（当前已实现）：

```python
from src.inference.model_loader import InferenceModelLoader

loader = InferenceModelLoader("qwen2.5-7b-zh")

# 默认行为：优先使用训练后的模型
gguf_path, model_type = loader.get_best_model_path(
    use_trained=True,  # 优先训练模型
    format_type="gguf"
)

# model_type 可能的值:
# - "trained": 使用训练后的模型
# - "base": 使用基础模型（训练模型不可用时）
# - "none": 没有可用模型
```

---

### 方案2：手动选择模型版本

**使用场景**：
- 用户想测试不同版本的模型效果
- 新训练的模型效果不理想，需要回退
- 需要对比不同版本的性能

**实现方式**：

```python
from src.training.model_version_manager import ModelVersionManager

manager = ModelVersionManager(base_dir="models/qwen")

# 1. 列出所有可用版本
versions = manager.list_versions()
for v in versions:
    print(f"{v['version_id']}: {v['created_at']}")
    print(f"  训练信息: {v.get('training_info', {})}")

# 2. 切换到指定版本
manager.set_active_version("v20250110_143022")

# 3. 切换回基础模型（不使用训练模型）
loader = InferenceModelLoader("qwen2.5-7b-zh")
base_path, _ = loader.get_best_model_path(
    use_trained=False,  # 不使用训练模型
    format_type="gguf"
)
```

---

### 方案3：基于性能指标的自动选择

**工作流程**：
```
1. 训练完成后进行性能评估
   ↓
2. 如果新模型性能优于当前模型
   ↓
3. 自动切换到新模型
   ↓
4. 否则保留当前模型，新模型作为备选
```

**实现方式**（需要扩展）：

```python
from src.training.zh_trainer import ZhTrainer
from src.training.model_version_manager import ModelVersionManager

trainer = ZhTrainer()

# 训练新模型
result = trainer.train(training_data)

# 评估新模型性能
if result["success"]:
    # 使用验证集评估
    new_model_score = evaluate_model(result["model_path"], validation_data)
    
    # 获取当前激活模型的性能
    manager = ModelVersionManager(base_dir="models/qwen")
    active_version = manager.get_active_version()
    
    if active_version:
        current_score = active_version.get("performance_score", 0)
        
        # 只有新模型更好时才切换
        if new_model_score > current_score:
            manager.set_active_version(result["version_id"])
            print(f"✅ 切换到新模型（性能提升: {new_model_score - current_score:.2%}）")
        else:
            print(f"⚠️ 保留当前模型（新模型性能未达标）")
```

---

## 推荐配置

### 默认策略（适合大多数用户）

```python
# 配置文件: configs/model_selection.yaml
model_selection:
  strategy: "auto_latest"  # 自动使用最新训练模型
  fallback_to_base: true   # 训练模型不可用时降级到基础模型
  auto_switch: true        # 训练完成后自动切换
```

### 保守策略（适合生产环境）

```python
# 配置文件: configs/model_selection.yaml
model_selection:
  strategy: "manual"       # 手动选择模型
  fallback_to_base: true   # 训练模型不可用时降级到基础模型
  auto_switch: false       # 训练完成后不自动切换
  require_validation: true # 需要验证后才能切换
```

### 性能优先策略（适合高级用户）

```python
# 配置文件: configs/model_selection.yaml
model_selection:
  strategy: "performance_based"  # 基于性能选择
  fallback_to_base: true         # 训练模型不可用时降级到基础模型
  auto_switch: true              # 性能更好时自动切换
  performance_threshold: 0.05    # 性能提升阈值（5%）
```

---

## 实际使用示例

### 场景1：首次训练

```python
from src.training.zh_trainer import ZhTrainer
from src.inference.model_loader import InferenceModelLoader

# 1. 训练模型
trainer = ZhTrainer()
result = trainer.train(training_data)

# 训练完成后：
# - 自动转换为GGUF格式
# - 自动注册为版本 v20250110_143022
# - 自动设置为激活版本

# 2. 推理时自动使用训练后的模型
loader = InferenceModelLoader("qwen2.5-7b-zh")
model_path, model_type = loader.get_best_model_path()

print(f"使用模型: {model_path}")
print(f"模型类型: {model_type}")  # 输出: "trained"
```

### 场景2：多次训练

```python
# 第一次训练
result1 = trainer.train(training_data_1)
# 版本: v20250110_143022（激活）

# 第二次训练
result2 = trainer.train(training_data_2)
# 版本: v20250111_091533（激活）
# 旧版本: v20250110_143022（保留）

# 推理时自动使用最新版本
loader = InferenceModelLoader("qwen2.5-7b-zh")
model_path, _ = loader.get_best_model_path()
# 使用: v20250111_091533
```

### 场景3：版本回退

```python
from src.training.model_version_manager import ModelVersionManager

manager = ModelVersionManager(base_dir="models/qwen")

# 新模型效果不好，回退到上一个版本
manager.set_active_version("v20250110_143022")

# 推理时使用回退后的版本
loader = InferenceModelLoader("qwen2.5-7b-zh")
model_path, _ = loader.get_best_model_path()
# 使用: v20250110_143022
```

### 场景4：使用基础模型

```python
# 不使用任何训练模型，只使用基础GGUF模型
loader = InferenceModelLoader("qwen2.5-7b-zh")
model_path, model_type = loader.get_best_model_path(
    use_trained=False  # 禁用训练模型
)

print(f"模型类型: {model_type}")  # 输出: "base"
```

---

## 版本管理最佳实践

### 1. 定期清理旧版本

```python
from src.training.model_version_manager import ModelVersionManager

manager = ModelVersionManager(base_dir="models/qwen", max_versions=5)

# 自动清理（保留最近5个版本）
# 在注册新版本时自动触发

# 手动清理所有非激活版本
count = manager.cleanup_all_except_active()
print(f"已清理{count}个版本")
```

### 2. 监控存储使用

```python
storage = manager.get_storage_usage()
print(f"总存储: {storage['total_gb']:.2f}GB")

for version_id, size_gb in storage['versions'].items():
    print(f"  {version_id}: {size_gb:.2f}GB")
```

### 3. 版本标注

```python
# 训练时添加详细信息
result = trainer.train(
    training_data,
    training_info={
        "description": "修复字幕生成问题",
        "dataset_source": "用户反馈数据",
        "expected_improvement": "提升10%准确率"
    }
)
```

---

## 总结

**当前实现的策略（方案1）**是最适合"投喂训练"场景的：

✅ **自动化**：训练后自动使用最新模型  
✅ **安全性**：保留基础模型作为降级选项  
✅ **灵活性**：支持手动切换版本  
✅ **可维护性**：自动清理旧版本  

**用户只需要**：
1. 训练模型：`trainer.train(data)`
2. 推理使用：`loader.get_best_model_path()` - 自动使用最新训练模型
3. 如需回退：`manager.set_active_version(old_version_id)`

这种设计既满足了"投喂训练"的简单性，又提供了足够的灵活性来处理各种场景。

