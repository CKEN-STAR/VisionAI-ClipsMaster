# 多维度比对引擎

多维度比对引擎是VisionAI-ClipsMaster项目的核心质量控制组件，用于从多个维度评估视频和字幕的相似度。该引擎能够比较测试输出和黄金样本在视频和字幕两个大类、共9个具体维度上的相似程度，为内容比对、质量控制和回归测试提供客观量化的评估标准。

## 核心特性

- **多维度评估**：同时从视频和字幕两大方面进行全面评估
- **客观量化**：每个维度提供0-1的量化评分，便于自动化测试
- **丰富报告**：支持文本、JSON和HTML三种报告格式
- **自动推断**：能够自动查找匹配的黄金样本，简化使用流程
- **命令行工具**：提供易用的命令行工具，支持批处理脚本

## 比对维度

### 视频维度

| 维度 | 描述 | 评分标准 |
|------|------|----------|
| duration | 视频时长匹配度 | 测试视频与黄金样本的时长相似程度 |
| resolution | 分辨率匹配度 | 测试视频与黄金样本的分辨率和宽高比 |
| color_hist | 色彩分布相似度 | 基于HSV直方图的色彩分布对比 |
| fingerprint | 视频指纹相似度 | 基于视频指纹提取引擎的内容相似度 |
| keyframe_psnr | 关键帧质量相似度 | 基于均匀采样帧的PSNR信噪比 |

### 字幕维度

| 维度 | 描述 | 评分标准 |
|------|------|----------|
| timecode | 时间码对齐度 | 字幕时间点的匹配程度 |
| text_sim | 文本相似度 | 字幕文本内容的相似程度 |
| entity_match | 实体匹配度 | 字幕中人名、地名等关键实体的匹配 |
| length_ratio | 长度比例 | 字幕总字符数的比例 |

## 使用方法

### Python 代码中使用

```python
from tests.golden_samples.compare_engine import compare_files, CompareResult

# 比较测试输出和黄金样本
result = compare_files('path/to/test_output', 'path/to/golden_sample')

# 检查比对结果
print(f"总体得分: {result.total_score:.2f}")
print(f"视频得分: {result.video_score:.2f}")
print(f"字幕得分: {result.subtitle_score:.2f}")

# 判断是否通过
if result.is_passed():
    print("测试通过!")
else:
    print("测试失败!")

# 访问详细得分
for dimension, score in result.scores["video"].items():
    print(f"视频-{dimension}: {score:.2f}")

for dimension, score in result.scores["subtitle"].items():
    print(f"字幕-{dimension}: {score:.2f}")
```

### 命令行工具

项目提供了方便的命令行工具用于执行多维度比对：

#### Windows

```bash
# 基础用法
scripts\multi_dimension_compare.bat path\to\test_output

# 指定黄金样本和输出格式
scripts\multi_dimension_compare.bat path\to\test_output --golden path\to\golden_sample --format html --output report.html

# 调整通过阈值
scripts\multi_dimension_compare.bat path\to\test_output --threshold 0.75
```

#### 通用Python脚本

```bash
# 基础用法
python scripts/multi_dimension_compare.py path/to/test_output

# 指定黄金样本和输出格式
python scripts/multi_dimension_compare.py path/to/test_output --golden path/to/golden_sample --format json --output report.json

# 调整通过阈值
python scripts/multi_dimension_compare.py path/to/test_output --threshold 0.75
```

## 报告格式

### 文本报告 (默认)

简洁的文本格式报告，显示总体得分和各维度详细得分：

```
多维度比对结果:
==================================================
总体得分: 0.85 (85%) ✓
视频得分: 0.88 (88%)
字幕得分: 0.82 (82%)
--------------------------------------------------
详细分数:
  video:
    duration: 0.95 (95%)
    resolution: 1.00 (100%)
    color_hist: 0.87 (87%)
    fingerprint: 0.83 (83%)
    keyframe_psnr: 0.75 (75%)
  subtitle:
    timecode: 0.90 (90%)
    text_sim: 0.85 (85%)
    entity_match: 0.80 (80%)
    length_ratio: 0.75 (75%)
```

### JSON报告

结构化的JSON格式，便于自动化处理和进一步分析：

```json
{
  "summary": {
    "total_score": 0.85,
    "video_score": 0.88,
    "subtitle_score": 0.82,
    "passed": true,
    "test_file": "test_output",
    "golden_sample": "golden_sample",
    "elapsed_time": 1.25
  },
  "details": {
    "video": {
      "duration": 0.95,
      "resolution": 1.0,
      "color_hist": 0.87,
      "fingerprint": 0.83,
      "keyframe_psnr": 0.75
    },
    "subtitle": {
      "timecode": 0.9,
      "text_sim": 0.85,
      "entity_match": 0.8,
      "length_ratio": 0.75
    }
  }
}
```

### HTML报告

可视化HTML报告，包含图表和颜色编码，便于人工查看：

- 总体摘要信息
- 彩色条形图展示各维度得分
- 维度说明和评分解释
- 通过/失败状态直观显示

## 黄金样本推断

当未明确指定黄金样本路径时，多维度比对引擎会按以下规则自动查找匹配的黄金样本：

1. 在黄金样本库(`tests/golden_samples`目录)的语言子目录(zh/en)中查找同名文件
2. 在测试输出的同目录下查找以`golden_`为前缀的同名文件

这种自动推断机制简化了测试流程，特别是在批量测试场景下。

## 调优与扩展

### 调整比对阈值

可以通过`--threshold`参数调整通过阈值（默认为0.8）。对于不同的应用场景，可能需要调整该阈值：

- 质量控制：建议使用较高阈值(0.85-0.9)
- 回归测试：建议使用中等阈值(0.75-0.85)
- 内容监测：可使用较低阈值(0.6-0.75)

### 添加新维度

要添加新的比对维度，需要在`GoldenComparator`类中实现相应的评分方法，并将其添加到`video_compare`或`subtitle_compare`方法的返回字典中。

## 性能考虑

- 视频比对是最耗时的部分，特别是处理高分辨率或长时间视频时
- 字幕比对相对较快，即使对大型字幕文件也是如此
- 对于批量处理，建议使用并行执行或任务队列

## 实际应用

多维度比对引擎可用于以下应用场景：

- **质量控制**：确保视频处理输出符合预期标准
- **回归测试**：验证系统更新后功能的正确性
- **A/B测试**：比较不同算法或参数的效果
- **性能基准**：建立视频处理的质量基准
- **批量验证**：大规模数据集的自动化验证

## 依赖库

- OpenCV (cv2)：视频处理和图像分析
- NumPy：数组操作和数值计算
- SciPy：用于相似度计算
- difflib：文本相似度分析 