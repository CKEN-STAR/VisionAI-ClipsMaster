# 模式发现算法库

模式发现算法库是VisionAI-ClipsMaster的核心组件之一，负责从叙事单元中挖掘出常见模式和结构，为短视频创作和分析提供数据支持。

## 主要功能

模式发现算法库提供以下核心功能：

1. **频繁项集挖掘**：使用FP-Growth算法识别共现的叙事元素和场景特征
2. **序列模式挖掘**：使用PrefixSpan算法发现叙事结构中的时序模式
3. **叙事模式分析**：综合分析节拍转换模式和情感流模式
4. **叙事指纹提取**：从节拍序列中提取关键特征，形成该叙事结构的"指纹"

## 算法说明

### FP-Growth算法

FP-Growth (Frequent Pattern Growth) 是一种高效的频繁项集挖掘算法，不需要产生候选项，而是使用FP树结构来存储数据，大大提高了挖掘效率。

在叙事分析中，FP-Growth主要用于发现以下模式：
- 共现的节拍类型组合
- 经常一起出现的情感状态
- 常见的节拍类型转换模式

### PrefixSpan算法

PrefixSpan (Prefix-projected Sequential pattern mining) 是一种高效的序列模式挖掘算法，它使用前缀投影的方式避免生成候选序列，减少内存使用和计算量。

在叙事分析中，PrefixSpan主要用于发现以下模式：
- 节拍类型的时序模式，如"铺垫->升级->高潮->解决"
- 情感变化的序列模式，如"平稳->上升->高潮->下降"
- 情节发展的典型路径

### 叙事模式分析

叙事模式分析器综合了多种挖掘算法，专注于识别叙事单元中的模式，包括：
- 节拍类型转换模式：如何从一种节拍类型过渡到另一种
- 情感变化模式：情感如何随着叙事发展而变化
- 情感强度模式：情感强度的波动规律

### 叙事指纹

叙事指纹是对叙事结构的一种数字化表示，类似于人的指纹能够唯一标识一个人一样，叙事指纹能够反映一个故事的结构特征。叙事指纹包含：

- 节拍类型分布：各种节拍类型的比例
- 情感特征：平均情感值、情感方差、情感范围
- 主导转换：最常见的节拍类型转换
- 节拍数量：整个叙事包含的节拍数量

## 使用方法

### 基本用法

```python
from src.algorithms.pattern_mining import PatternMiner
from src.core.narrative_unit_splitter import NarrativeUnitSplitter

# 第一步：分割叙事节拍
splitter = NarrativeUnitSplitter()
beats = splitter.split_into_beats(text)

# 第二步：创建模式挖掘器
miner = PatternMiner()

# 第三步：挖掘模式（支持多种方法）
# 使用FP-Growth
fp_patterns = miner.mine(data, method='fp-growth')

# 使用PrefixSpan
seq_patterns = miner.mine(data, method='sequence')

# 使用叙事模式分析器
narrative_analyzer = miner.algorithms['narrative']
patterns = narrative_analyzer.discover_patterns([beats])

# 提取叙事指纹
fingerprint = miner.extract_narrative_fingerprint(beats)
```

### 命令行工具

我们提供了命令行工具方便快速分析文本文件：

```bash
python tools/pattern_finder.py --input <文本文件路径> [--output <输出路径>] [--method fp-growth|sequence|narrative]
```

参数说明：
- `--input`: 输入文本文件路径（必须）
- `--output`: 输出文件路径（可选，JSON格式）
- `--method`: 挖掘方法，支持fp-growth、sequence、narrative（默认为narrative）

### 配置文件

可以通过`configs/pattern_mining_config.yaml`文件调整算法参数：

```yaml
# FP-Growth算法配置
fp_growth:
  min_support: 0.1  # 最小支持度阈值(0-1)
  
# PrefixSpan算法配置
prefix_span:
  min_support: 0.1  # 最小支持度阈值(0-1)
  max_len: 5  # 最大模式长度
  
# 叙事模式分析配置
narrative_analysis:
  min_support: 0.1  # 最小支持度阈值
  # ... 其他配置项
```

## 实际应用场景

1. **短视频脚本分析**：挖掘成功短视频的叙事模式，提供创作指导
2. **叙事结构推荐**：基于叙事指纹，为创作者推荐适合的叙事结构
3. **视频分类标签**：自动为视频添加叙事类型标签，如"反转剧情"、"情感升华"等
4. **情感曲线预测**：预测视频的情感变化曲线，辅助视频拍摄和剪辑
5. **内容质量评估**：评估视频叙事结构的完整性和吸引力

## 性能考量

- 使用内存优化技术，适合在资源受限环境中运行
- 大型数据集建议增加min_support值以减少计算量
- 多线程处理仅在大型数据集时开启以避免额外开销

## 未来拓展

1. 支持更多专业级模式挖掘算法，如SPADE和SPAM
2. 整合深度学习模型，提高叙事模式识别的准确性
3. 实现跨语言、跨文化的叙事模式对比分析
4. 增加互动式可视化界面，直观展示叙事模式 