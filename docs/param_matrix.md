# 参数配置矩阵说明文档

本文档详细说明VisionAI-ClipsMaster中的参数配置矩阵系统，包括各参数的含义、作用和调整建议。

## 参数介绍

参数矩阵控制剧本重构引擎的行为，影响最终生成的混剪效果。不同的参数组合可以产生不同风格的混剪作品。

### 核心参数

| 参数名称 | 取值范围 | 默认值 | 说明 |
|---------|---------|-------|------|
| pace | 0.5-2.0 | 1.0 | 节奏系数，控制剪辑片段的平均时长和变化频率 |
| emotion_intensity | 0-1 | 0.7 | 情感强度，控制情感波动和冲突强度 |
| subplot | 0-5 | 3 | 支线数量，允许保留的叙事支线数量 |
| cliffhanger_freq | 0-1 | 0.4 | 悬念频率，控制悬念点的出现频率 |
| resolution_delay | 0-1 | 0.5 | 悬念密度，控制悬念点与解决点之间的距离 |
| character_focus | 1-5 | 2 | 角色聚焦，重点关注的角色数量 |
| conflict_intensity | 0-1 | 0.6 | 冲突强度，控制矛盾冲突的强度 |
| punchline_ratio | 0-0.3 | 0.15 | 金句保留，决定保留原片金句的比例 |
| context_preservation | 0-1 | 0.5 | 上下文保留，决定场景切换的连续性 |
| linearity | 0-1 | 0.7 | 线性叙事，控制叙事的线性程度，越低越非线性 |

### 全局设置

| 参数名称 | 默认值 | 说明 |
|---------|-------|------|
| min_segment_duration | 1.5 | 最小片段时长(秒)，过短的片段会被过滤 |
| max_total_duration | 120 | 最大总时长(秒)，避免生成过长的混剪 |
| min_total_duration | 20 | 最小总时长(秒)，避免生成过短的混剪 |
| target_duration | 60 | 目标总时长(秒)，系统将尝试接近此时长 |
| max_segments | 15 | 最大片段数，限制混剪中的场景切换次数 |

## 预设风格

系统预设了多种参数组合，适合不同类型的内容和风格需求。

### 默认平衡 (default)

平衡各项参数，适合大多数内容，具有良好的节奏感和情感表达。

```yaml
default:
  pace: 1.0
  emotion_intensity: 0.7
  subplot: 3
  cliffhanger_freq: 0.4
  resolution_delay: 0.5
  character_focus: 2
  conflict_intensity: 0.6
  punchline_ratio: 0.15
  context_preservation: 0.5
  linearity: 0.7
```

### 快节奏 (快节奏)

快速、紧凑的节奏，适合动作场景和冲突密集的内容。减少支线和上下文，聚焦核心冲突。

```yaml
快节奏:
  pace: 1.3                   # 更快的节奏
  emotion_intensity: 0.8      # 较高情感强度
  subplot: 2                  # 减少支线，聚焦主线
  cliffhanger_freq: 0.6       # 较高悬念频率
  resolution_delay: 0.8       # 高悬念密度
  character_focus: 2          # 聚焦核心角色
  conflict_intensity: 0.8     # 高冲突强度
  punchline_ratio: 0.2        # 金句保留适中
  context_preservation: 0.4   # 减少上下文，增加节奏感
  linearity: 0.6              # 相对线性
```

### 深度情感 (深度情感)

强调情感表达和角色内心活动，适合情感丰富的内容。减慢节奏，增加上下文保留，聚焦单一角色。

```yaml
深度情感:
  pace: 0.8                   # 较慢节奏
  emotion_intensity: 0.9      # 高情感强度
  subplot: 2                  # 集中情感线
  cliffhanger_freq: 0.3       # 低悬念频率
  resolution_delay: 0.4       # 低悬念密度
  character_focus: 1          # 单角色聚焦
  conflict_intensity: 0.7     # 中高冲突强度
  punchline_ratio: 0.15       # 金句保留适中
  context_preservation: 0.7   # 高上下文保留
  linearity: 0.8              # 高度线性
```

### 悬念优先 (悬念优先)

突出悬念和未知元素，适合悬疑、惊悚内容。高悬念频率和密度，多支线叙事，非线性结构。

```yaml
悬念优先:
  pace: 0.9                   # 中等节奏
  emotion_intensity: 0.6      # 中等情感强度
  subplot: 3                  # 多支线增加复杂性
  cliffhanger_freq: 0.8       # 高悬念频率
  resolution_delay: 0.9       # 最高悬念密度
  character_focus: 3          # 多角色视角
  conflict_intensity: 0.5     # 中等冲突强度
  punchline_ratio: 0.1        # 低金句保留
  context_preservation: 0.5   # 中等上下文保留
  linearity: 0.4              # 非线性叙事
```

### 剧情紧凑 (剧情紧凑)

精简的剧情表达，适合网剧和短视频内容。快节奏，单一支线，高度线性叙事，保留金句。

```yaml
剧情紧凑:
  pace: 1.2                   # 较快节奏
  emotion_intensity: 0.75     # 中高情感强度
  subplot: 1                  # 最少支线
  cliffhanger_freq: 0.5       # 中等悬念频率
  resolution_delay: 0.6       # 中高悬念密度
  character_focus: 2          # 双角色聚焦
  conflict_intensity: 0.75    # 高冲突强度
  punchline_ratio: 0.25       # 高金句保留
  context_preservation: 0.4   # 低上下文保留
  linearity: 0.85             # 高度线性
```

### 复杂叙事 (复杂叙事)

富含多线叙事和角色关系，适合剧情复杂的长篇作品。慢节奏，多支线，高上下文保留，非线性结构。

```yaml
复杂叙事:
  pace: 0.7                   # 慢节奏
  emotion_intensity: 0.65     # 中等情感强度
  subplot: 5                  # 最多支线
  cliffhanger_freq: 0.4       # 中等悬念频率
  resolution_delay: 0.5       # 中等悬念密度
  character_focus: 4          # 多角色聚焦
  conflict_intensity: 0.65    # 中等冲突强度
  punchline_ratio: 0.1        # 低金句保留
  context_preservation: 0.8   # 高上下文保留
  linearity: 0.3              # 高度非线性
```

## 语言特定调整

系统会根据内容语言自动应用特定的参数调整，以适应不同语言的表达特点。

### 中文内容调整

```yaml
zh:
  context_preservation: +0.1  # 中文需要更高的上下文保留
  linearity: -0.1             # 中文通常线性度略低
  character_focus: +0.2       # 中文更关注角色
```

### 英文内容调整

```yaml
en:
  emotion_intensity: +0.05    # 英文需要更高的情感强度
  punchline_ratio: +0.05      # 英文金句保留比例更高
  pace: +0.1                  # 英文节奏略快
```

## 参数调整建议

1. **对话密集内容**: 增加`pace`和`punchline_ratio`，降低`context_preservation`
2. **动作场景**: 增加`pace`和`conflict_intensity`，降低`linearity`
3. **情感内容**: 增加`emotion_intensity`和`context_preservation`，降低`pace`
4. **悬疑内容**: 增加`cliffhanger_freq`和`resolution_delay`，降低`linearity`
5. **角色众多**: 增加`character_focus`和`subplot`，可能需要降低`linearity`

## 高级应用

可以通过程序代码动态调整参数矩阵，实现更精细的控制：

```python
from src.versioning import prepare_screenplay_params

# 获取自动推荐的参数
params = prepare_screenplay_params(subtitles)

# 使用特定预设
params = prepare_screenplay_params(subtitles, preset_name="快节奏")

# 自定义参数
custom = {
    "emotion_intensity": 0.9,
    "pace": 1.5
}
params = prepare_screenplay_params(subtitles, custom_params=custom)
```

## 参数影响示例

### pace (节奏系数)

- **低值 (0.5-0.8)**: 片段较长，节奏缓慢，适合情感表达和人物刻画
- **中值 (0.9-1.1)**: 平衡的节奏，适合大多数内容
- **高值 (1.2-2.0)**: 片段短促，快节奏，适合动作和紧张场景

### emotion_intensity (情感强度)

- **低值 (0-0.4)**: 情感表达克制，适合理性和分析性内容
- **中值 (0.5-0.7)**: 均衡的情感表达，适合一般叙事
- **高值 (0.8-1.0)**: 强烈的情感波动，适合戏剧性和冲突性内容

### linearity (线性叙事)

- **低值 (0-0.4)**: 高度非线性，可能包含闪回、插叙等复杂结构
- **中值 (0.5-0.7)**: 主要线性但保留一些灵活性
- **高值 (0.8-1.0)**: 严格线性，按时间顺序呈现，适合简单明了的内容 