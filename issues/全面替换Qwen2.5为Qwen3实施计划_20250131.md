# 全面替换Qwen2.5为Qwen3实施计划

**创建时间**: 2025-01-31  
**优先级**: P0 (CRITICAL)  
**预计工作量**: 2-3小时

---

## 📋 任务概述

根据用户要求，全面替换Qwen2.5为Qwen3，包括：
1. 模型配置文件
2. 智能推荐下载器
3. 下载链接
4. 所有相关代码

同时回答用户的4个问题：
1. 模型训练是否可行？
2. 优化1是否会导致视频前后不连贯？
3. 辅助模块使用方案1
4. 全面替换Qwen2.5为Qwen3

---

## 🔍 问题1：模型训练是否可行？

### 用户问题

> "我原本是打算使用模型训练，训练出一个知道为何精彩的，投入大量示例来进行训练，能做到吗"

### 答案：可以，但需要注意以下几点

#### ✅ 项目已支持模型训练

根据代码分析，项目已经实现了完整的模型训练功能：

1. **TrainingFeeder**（`src/training/training_feeder.py`）
   - 管理训练数据对
   - 支持原片→爆款的训练数据格式

2. **ModelFineTuner**（`src/training/model_fine_tuner.py`）
   - 支持LoRA微调
   - 支持中英文模型训练

3. **ZhTrainer**（`src/training/zh_trainer.py`）
   - 专门的中文模型训练器
   - 支持Qwen系列模型

4. **训练配置**（`configs/training_policy.yaml`）
   - 完整的训练参数配置
   - 支持课程学习

#### 📊 训练数据要求

**格式**：
```python
training_data = [
    {
        "original": "原始字幕文本",
        "viral": "爆款改写后的字幕文本"
    },
    ...
]
```

**数量要求**：
- **最少**：100对训练数据
- **推荐**：500-1000对训练数据
- **理想**：2000+对训练数据

**质量要求**：
- 原片和爆款字幕必须配对
- 爆款字幕必须是高质量的（真实的爆款视频字幕）
- 需要标注"为何精彩"（可以通过分析结果实现）

#### ⚠️ 挑战和限制

1. **数据收集困难**
   - 需要大量真实的爆款视频字幕
   - 需要人工标注"为何精彩"

2. **训练成本高**
   - 需要GPU（至少8GB显存）
   - 训练时间长（数小时到数天）

3. **效果不确定**
   - 小模型（1.5B-1.7B）训练效果有限
   - 可能需要更大的模型（7B-8B）

#### 💡 建议的训练策略

**方案1：使用现有训练素材**
- 使用`D:\Material\短剧素材\训练素材\请君入我怀`中的数据
- 提取原片和成片的配对数据
- 添加分析结果作为"为何精彩"的标注

**方案2：增量训练**
- 先使用少量高质量数据（100对）进行初步训练
- 验证效果后，逐步增加训练数据
- 使用用户反馈优化训练数据

**方案3：混合方案**
- 使用训练后的模型 + 规则引擎
- 模型负责理解"为何精彩"
- 规则引擎负责确保数量和质量

### 结论

**可以进行模型训练，但建议先实施短期方案（优化Prompt + 升级Qwen3），验证效果后再考虑训练**。

---

## 🔍 问题2：优化1是否会导致视频前后不连贯？

### 用户问题

> "如果使用优化1的话，模型不先理解全部内容的话，会不会导致最后视频前后不连贯"

### 答案：不会，原因如下

#### 当前流程分析

**步骤0：理解整个故事**（已实现）
```python
# 构建提示词：让AI理解整个故事
prompt = self._build_story_understanding_prompt(all_subtitles, language, analysis_results)

# 生成回答
response = self._generate_response(prompt, language)

# 解析故事摘要
story_summary = self._parse_story_summary(response, language)
```

**步骤1：逐集提取关键对话**（当前实现）
```python
for episode_idx, episode_subtitles in enumerate(all_subtitles):
    # 构建提示词：让AI根据故事摘要，提取当前集的关键对话
    prompt = self._build_key_dialogue_extraction_prompt(
        story_summary, episode_subtitles, episode_idx, language
    )
```

**关键点**：
- ✅ **步骤0已经理解了整个故事**
- ✅ **步骤1使用了story_summary**
- ✅ **每集提取时都知道整个故事的上下文**

#### 优化1的改进

**优化前**：
```python
prompt = f"""你是一个专业的短剧剪辑师，精通短视频平台的流量密码和用户心理。

【任务】
从第{episode_idx + 1}集中提取关键对话，用于后续混剪。

【整个故事摘要】
{story_summary}

【第{episode_idx + 1}集完整字幕】
{current_episode_text}

【提取要求】
1. **根据故事摘要理解当前集的作用**
2. **提取关键对话**
3. **保留约30%-50%的对话**
```

**优化后**：
```python
prompt = f"""你是一个专业的短剧剪辑师。

【整个故事摘要】
{story_summary}

【任务】
从第{episode_idx + 1}集的{len(current_episode_subtitles)}条字幕中，选择{target_count}条关键对话。

【第{episode_idx + 1}集完整字幕】
{current_episode_text}

【选择标准】
1. 包含重要剧情信息的对话
2. 包含情感强烈的对话
3. 包含人物关系变化的对话
4. 对话长度较长的（超过5个字）

【输出要求】
- 必须选择{target_count}条对话
- 只输出序号，用逗号分隔
```

**改进点**：
- ✅ **仍然使用story_summary**（保持全局理解）
- ✅ **简化任务描述**（降低模型负担）
- ✅ **明确数量要求**（提高成功率）

### 结论

**优化1不会导致视频前后不连贯，因为：**
1. ✅ **步骤0已经理解了整个故事**
2. ✅ **步骤1仍然使用story_summary作为上下文**
3. ✅ **只是简化了任务描述，没有移除全局理解**

---

## 🔍 问题3：辅助模块使用方案1

### 确认

✅ 使用方案1：在关键对话提取阶段使用分析结果

**实施内容**：
1. 修改`_build_key_dialogue_extraction_prompt()`方法
2. 添加`analysis_result`参数
3. 从叙事分析中提取关键情节点
4. 从节奏分析中提取建议片段
5. 提供具体的选择提示

---

## 🔍 问题4：全面替换Qwen2.5为Qwen3

### 需要修改的文件清单

#### 1. 配置文件（6个文件）

**1.1 主配置文件**
- `configs/model_config.yaml`
  - 修改`active_models.chinese`
  - 修改`available_models.chinese`列表

**1.2 模型配置文件**（需要创建/修改）
- `configs/models/available_models/qwen3-0.6b-zh.yaml`（已存在）
- `configs/models/available_models/qwen3-1.7b-zh.yaml`（已存在）
- `configs/models/available_models/qwen3-8b-zh.yaml`（已存在）
- `configs/models/available_models/qwen3-32b-zh.yaml`（已存在）

**1.3 删除旧配置文件**
- `configs/models/available_models/qwen2.5-0.5b-zh.yaml`
- `configs/models/available_models/qwen2.5-1.5b-zh.yaml`
- `configs/models/available_models/qwen2.5-3b-zh.yaml`（如果存在）
- `configs/models/available_models/qwen2.5-7b-zh.yaml`（如果存在）
- `configs/models/available_models/qwen2.5-14b-zh.yaml`（如果存在）
- `configs/models/available_models/qwen2.5-32b-zh.yaml`（如果存在）

#### 2. 智能推荐下载器（1个文件）

**2.1 下载配置**
- `src/core/intelligent_model_selector.py`
  - 修改`create_multi_tier_download_config()`函数
  - 更新Qwen模型的下载链接

#### 3. 模型管理器（2个文件）

**3.1 Qwen模型**
- `src/models/qwen.py`
  - 修改默认模型名称

**3.2 配置模块**
- `configs/model_config.py`
  - 修改`get_default_model_config()`函数

#### 4. UI层面（1个文件）

**4.1 主界面集成**
- `src/ui/main_ui_integration.py`
  - 更新预定义模型列表

#### 5. 训练模块（1个文件）

**5.1 中文训练器**
- `src/training/zh_trainer.py`
  - 修改`self.model_name`

---

## 📝 详细修改计划

### 阶段1：配置文件修改

#### 1.1 修改`configs/model_config.yaml`

**修改内容**：
```yaml
# 当前激活的模型
active_models:
  chinese: qwen3-0.6b-zh  # 从qwen2.5-0.5b-zh改为qwen3-0.6b-zh
  english: mistral-7b-en

# 可用模型列表
available_models:
  chinese:
    - qwen3-0.6b-zh      # 入门级设备
    - qwen3-1.7b-zh      # 进阶级设备
    - qwen3-8b-zh        # 中高级设备
    - qwen3-32b-zh       # 旗舰级设备
  english:
    - mistral-7b-en
    - mistral-12b-nemo-en
    - mistral-24b-small-en
    - mistral-large2-en
```

#### 1.2 检查Qwen3配置文件是否存在

**需要确认的文件**：
- `configs/models/available_models/qwen3-0.6b-zh.yaml`
- `configs/models/available_models/qwen3-1.7b-zh.yaml`
- `configs/models/available_models/qwen3-8b-zh.yaml`
- `configs/models/available_models/qwen3-32b-zh.yaml`

**如果不存在，需要创建**（参考qwen2.5的配置文件格式）

#### 1.3 删除Qwen2.5配置文件

**删除的文件**：
- `configs/models/available_models/qwen2.5-0.5b-zh.yaml`
- `configs/models/available_models/qwen2.5-1.5b-zh.yaml`
- 其他qwen2.5相关配置文件

---

### 阶段2：智能推荐下载器修改

#### 2.1 修改`src/core/intelligent_model_selector.py`

**修改`create_multi_tier_download_config()`函数**：

**当前代码**（line 841-866）：
```python
return {
    "qwen3-4b": {
        "fp16": {
            "name": "Qwen3-4B-Instruct-FP16",
            "size_gb": 8.0,
            "urls": ["https://modelscope.cn/models/qwen/Qwen3-4B-Instruct"],
            "target_dir": "models/qwen/qwen3-4b/base"
        }
    },
    "qwen3-8b": {
        "fp16": {
            "name": "Qwen3-8B-Instruct-FP16",
            "size_gb": 16.0,
            "urls": ["https://modelscope.cn/models/qwen/Qwen3-8B-Instruct"],
            "target_dir": "models/qwen/qwen3-8b/base"
        }
    },
    ...
}
```

**需要添加**：
```python
return {
    "qwen3-0.6b": {
        "fp16": {
            "name": "Qwen3-0.6B-Instruct-FP16",
            "size_gb": 1.2,
            "urls": ["https://modelscope.cn/models/qwen/Qwen3-0.6B-Instruct"],
            "target_dir": "models/qwen/qwen3-0.6b/base"
        }
    },
    "qwen3-1.7b": {
        "fp16": {
            "name": "Qwen3-1.7B-Instruct-FP16",
            "size_gb": 3.4,
            "urls": ["https://modelscope.cn/models/qwen/Qwen3-1.7B-Instruct"],
            "target_dir": "models/qwen/qwen3-1.7b/base"
        }
    },
    "qwen3-4b": {
        "fp16": {
            "name": "Qwen3-4B-Instruct-FP16",
            "size_gb": 8.0,
            "urls": ["https://modelscope.cn/models/qwen/Qwen3-4B-Instruct"],
            "target_dir": "models/qwen/qwen3-4b/base"
        }
    },
    "qwen3-8b": {
        "fp16": {
            "name": "Qwen3-8B-Instruct-FP16",
            "size_gb": 16.0,
            "urls": ["https://modelscope.cn/models/qwen/Qwen3-8B-Instruct"],
            "target_dir": "models/qwen/qwen3-8b/base"
        }
    },
    "qwen3-32b": {
        "fp16": {
            "name": "Qwen3-32B-Instruct-FP16",
            "size_gb": 64.0,
            "urls": ["https://modelscope.cn/models/qwen/Qwen3-32B-Instruct"],
            "target_dir": "models/qwen/qwen3-32b/base"
        }
    },
    ...
}
```

---

### 阶段3：模型管理器修改

#### 3.1 修改`src/models/qwen.py`

**查找并修改默认模型名称**：
```python
# 从
self.model_name = "qwen2.5-7b-zh"

# 改为
self.model_name = "qwen3-1.7b-zh"
```

#### 3.2 修改`configs/model_config.py`

**修改`get_default_model_config()`函数**：
```python
# 从
"default_models": {
    "zh": "qwen2.5-7b-zh",
    "en": "mistral-7b-en"
}

# 改为
"default_models": {
    "zh": "qwen3-1.7b-zh",
    "en": "mistral-7b-en"
}
```

---

### 阶段4：UI层面修改

#### 4.1 修改`src/ui/main_ui_integration.py`

**更新预定义模型列表**：
```python
# 从
models = [
    "qwen2.5-0.5b (入门级)",
    "qwen2.5-1.5b (进阶级)",
    "qwen2.5-7b (中高级)",
    "qwen2.5-32b (旗舰级)",
    ...
]

# 改为
models = [
    "qwen3-0.6b (入门级)",
    "qwen3-1.7b (进阶级)",
    "qwen3-8b (中高级)",
    "qwen3-32b (旗舰级)",
    ...
]
```

---

### 阶段5：训练模块修改

#### 5.1 修改`src/training/zh_trainer.py`

**修改模型名称**：
```python
# 从
self.model_name = "Qwen2.5-7B"

# 改为
self.model_name = "Qwen3-1.7B"
```

---

## ✅ 验证清单

完成所有修改后，需要验证：

1. ✅ 配置文件加载正常
2. ✅ 智能推荐下载器显示Qwen3模型
3. ✅ 模型下载链接正确
4. ✅ UI显示Qwen3模型列表
5. ✅ 训练模块使用Qwen3模型

---

**下一步**: 请确认是否立即开始实施？

