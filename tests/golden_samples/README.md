# VisionAI-ClipsMaster 黄金样本库

黄金样本库是VisionAI-ClipsMaster项目的标准测试数据集，用于系统性能评估、回归测试和质量控制。该库提供了一系列覆盖各种场景的标准化视频和字幕样本，确保系统在不同情况下的稳定性和准确性。

## 样本内容

黄金样本库包含以下类型的样本：

### 中文样本 (zh/)

| 样本名称 | 类型 | 时长 | 特点 |
|---------|-----|------|------|
| base_30s | 剧情混剪 | 30秒 | 基础视频样本，包含标准字幕 |
| edge_5s | 超短视频 | 5秒 | 极短视频边界情况测试 |
| dialog_heavy | 对白密集型 | 45秒 | 包含密集对话的视频测试 |
| action_scene | 动作场景 | 25秒 | 包含快速场景切换的视频测试 |
| special_chars | 特殊字符 | 20秒 | 包含特殊符号和表情的字幕测试 |

### 英文样本 (en/)

| 样本名称 | 类型 | 时长 | 特点 |
|---------|-----|------|------|
| complex_1m | 多场景切换 | 60秒 | 包含多场景转换的较长视频 |
| multi_speaker | 多人对话 | 40秒 | 包含多人对话场景的视频 |
| narrative | 旁白主导 | 35秒 | 以旁白为主的视频场景 |
| empty_segments | 空白片段 | 15秒 | 包含无字幕空白片段的视频 |

## 使用方法

### 生成样本

```bash
# Windows
scripts\generate_golden_samples.bat

# 强制重新生成所有样本
scripts\generate_golden_samples.bat --force

# 仅验证现有样本
scripts\generate_golden_samples.bat --verify-only
```

### 在测试中使用

```python
# 导入样本测试模块
from tests.unit_test.test_golden_sample_processing import TestGoldenSampleProcessing

# 或者直接加载样本数据
from pathlib import Path
import json

# 加载样本元数据
project_root = Path(__file__).resolve().parents[2]
metadata_path = project_root / "tests" / "golden_samples" / "metadata.json"

with open(metadata_path, 'r', encoding='utf-8') as f:
    metadata = json.load(f)
    samples = metadata.get("samples", [])

# 获取特定类型的样本
zh_samples = [s for s in samples if s["lang"] == "zh"]
short_samples = [s for s in samples if s["type"] == "超短视频"]
```

## 样本验证

所有样本文件都包含校验和哈希值，以确保文件完整性。使用以下命令验证样本库：

```bash
python tests/golden_samples/verify_samples.py --verbose
```

## 样本格式

每个样本包含以下文件：

1. **视频文件 (.mp4)**: 测试用视频文件
2. **字幕文件 (.srt)**: 对应的SRT格式字幕

## 元数据结构

`metadata.json` 文件包含所有样本的详细信息，包括：

- 样本名称、类型、语言
- 视频和字幕文件路径
- 文件哈希值用于完整性验证
- 样本持续时间信息

## 扩展黄金样本库

要添加新的黄金样本，请修改 `tests/golden_samples/generate_samples.py` 文件中的 `create_golden_samples()` 函数：

```python
# 添加新样本
new_sample = {"name": "new_sample", "duration": 15, "lang": "zh", "type": "新类型"}
samples.append(new_sample)
```

然后运行：

```bash
scripts\generate_golden_samples.bat --force
```

## 注意事项

- 所有样本文件均为测试目的创建，不应用于生产环境
- 黄金样本库假设在没有FFMPEG的环境中运行，因此创建了占位视频文件
- 如果更改了样本内容，请确保更新相关测试以反映这些变化 