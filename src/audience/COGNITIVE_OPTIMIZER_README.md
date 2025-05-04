# 认知负荷优化器 (CognitiveLoadBalancer)

## 概述

认知负荷优化器是VisionAI-ClipsMaster项目的重要组件，负责分析和优化视频内容的认知复杂度，确保最终输出的混剪视频符合用户的认知处理能力，提高内容有效性和用户体验。该组件动态评估内容复杂度并自适应地简化过于复杂的内容，平衡信息传递和用户认知负荷。

## 主要功能

认知负荷优化器提供以下核心功能：

1. **认知负荷评估**：
   - 计算内容的整体认知复杂度
   - 考虑用户个体认知能力差异
   - 分析内容多维度复杂因素

2. **智能内容优化**：
   - 自动简化过于复杂的内容
   - 保留核心信息和关键元素
   - 多策略联合优化降低认知负荷

3. **用户适应性**：
   - 基于用户认知能力调整内容
   - 考虑注意力水平、处理速度和领域知识
   - 为不同用户提供个性化体验

4. **复杂度管理**：
   - 控制信息密度和节奏
   - 优化场景转换和视觉效果
   - 分解复杂信息为易理解单元

## 实现架构

认知负荷优化器基于以下架构设计：

- **CognitiveLoadBalancer类**：核心优化器类，管理整体流程
- **认知负荷计算**：基于多维度内容特征计算认知负荷
- **简化策略集**：提供多种内容简化方法
- **迭代优化**：通过多次迭代降低内容认知负荷
- **用户适应性**：考虑用户特征进行个性化优化

## 使用方法

### 基本使用

```python
from src.audience import optimize_content, calculate_cognitive_load

# 计算内容认知负荷
content_load = calculate_cognitive_load(content)
print(f"内容认知负荷: {content_load:.2f}")

# 优化内容
optimized_content = optimize_content(content)
```

### 带用户画像的个性化优化

```python
from src.audience import optimize_content

# 用户画像
user_profile = {
    "cognitive_abilities": {
        "attention_span": 0.7,      # 注意力水平
        "processing_speed": 0.6,    # 处理速度
        "domain_knowledge": 0.8     # 领域知识
    }
}

# 针对用户优化内容
personalized_content = optimize_content(content, user_profile)
```

### 直接使用优化器实例

```python
from src.audience import get_cognitive_optimizer

# 获取优化器实例
optimizer = get_cognitive_optimizer()

# 提取内容特征
features = optimizer._extract_content_features(content)
print(f"内容特征: {features}")

# 计算用户能力
user_factors = optimizer._extract_user_factors(user_profile)
capability = optimizer._calculate_user_capability(user_factors)
print(f"用户认知能力: {capability:.2f}")

# 自定义优化
optimized = optimizer.optimize(content, user_profile)
```

## 配置选项

认知负荷优化器提供以下可配置选项：

### 阈值设置

```python
{
    "thresholds": {
        "max_cognitive_load": 0.7,    # 最大认知负荷阈值
        "min_cognitive_load": 0.3,    # 最小认知负荷阈值
        "optimal_load": 0.5           # 最优认知负荷目标
    }
}
```

### 用户因素权重

```python
{
    "user_factors": {
        "attention_span_weight": 0.4,      # 注意力水平权重
        "processing_speed_weight": 0.3,    # 处理速度权重
        "domain_knowledge_weight": 0.3     # 领域知识权重
    }
}
```

### 内容因素权重

```python
{
    "content_factors": {
        "complexity_weight": 0.35,    # 复杂度权重
        "density_weight": 0.25,       # 密度权重
        "pacing_weight": 0.25,        # 节奏权重
        "novelty_weight": 0.15        # 新颖度权重
    }
}
```

### 简化策略配置

```python
{
    "simplification_strategies": {
        "reduce_information_density": true,     # 降低信息密度
        "slow_down_pacing": true,               # 降低节奏
        "chunk_complex_information": true,      # 分块复杂信息
        "reduce_transitions": true,             # 减少转场
        "prioritize_essential_content": true    # 优先核心内容
    }
}
```

## 内容特征与复杂度指标

优化器评估内容认知负荷时考虑以下维度：

1. **复杂度 (Complexity)**：
   - 场景复杂性
   - 内容结构复杂性
   - 概念复杂性

2. **密度 (Density)**：
   - 单位时间内的信息量
   - 元素密集度
   - 信息重叠程度

3. **节奏 (Pacing)**：
   - 场景切换频率
   - 内容流动速度
   - 转折点频率

4. **新颖度 (Novelty)**：
   - 内容创新程度
   - 对用户的熟悉度
   - 认知处理需求

## 简化策略详解

优化器在降低认知负荷时使用以下策略：

### 降低信息密度

减少次要信息和细节，保留核心内容。主要通过筛选场景元素和简化细节来实现，确保关键信息突出。

### 降低节奏

延长场景持续时间，减少场景切换频率，降低内容流动速度，让用户有更多时间处理信息。

### 分块复杂信息

将复杂概念分解为更容易理解的部分，拆分复杂场景为多个简单场景，降低单次认知处理需求。

### 减少转场和特效

减少不必要的视觉干扰，降低转场复杂度和特效使用，减轻视觉处理负担。

### 优先保留核心内容

移除次要内容，保留和强化关键信息，提高内容传递效率。

## 适用场景

认知负荷优化器适用于以下场景：

1. **面向不同认知能力用户的内容适配**
2. **长视频内容的精简和优化**
3. **教育和培训内容的认知负荷管理**
4. **复杂主题的简化呈现**
5. **注意力障碍用户的内容适配**
6. **多平台内容的认知复杂度调整**

## 最佳实践

1. **准确的用户画像**：提供尽可能准确的用户认知能力数据
2. **内容标记**：为内容元素添加重要性标记以指导优化
3. **增量优化**：对复杂内容进行多次迭代优化
4. **关键内容标记**：使用`has_key_information`和`emotional_peak`标记关键场景
5. **平衡信息完整性和认知负荷**：设置合理的优化目标阈值

## 注意事项

1. 过度简化可能导致重要信息丢失，需要平衡优化强度
2. 认知负荷评估是近似计算，应配合实际用户反馈调整
3. 不同类型内容的认知复杂度评估标准可能不同
4. 用户认知能力数据准确性直接影响优化效果
5. 优化后内容应进行人工审核，确保核心信息完整性

## 扩展支持

如需扩展认知负荷优化器功能，可以：

1. 添加新的复杂度评估维度
2. 实现更精细的内容简化策略
3. 集成用户反馈机制动态调整优化强度
4. 添加特定领域的认知负荷模型
5. 实现更智能的内容结构重组算法 