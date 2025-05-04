# 实时A/B测试路由器 (ABRouter)

## 概述

实时A/B测试路由器是VisionAI-ClipsMaster项目的重要组件，用于基于用户画像特征动态路由不同的内容变体或功能变体，实现精准的A/B测试和个性化内容推送。该组件支持复杂的多变量测试、行为追踪和结果分析，帮助开发者优化混剪策略和提升用户体验。

## 主要功能

实时A/B测试路由器提供以下核心功能：

1. **智能变体路由**：
   - 基于用户特征向量自动分配最佳内容变体
   - 支持余弦相似度计算匹配度
   - 缓存路由决策减少计算开销

2. **测试管理**：
   - 创建和配置A/B测试实验
   - 支持多变量测试
   - 管理测试状态和生命周期

3. **行为追踪**：
   - 记录用户与变体的交互行为
   - 统计关键性能指标
   - 提供数据安全管理

4. **结果分析**：
   - 自动计算变体性能指标
   - 分析效果差异及显著性
   - 生成数据驱动的优化建议

## 实现架构

实时A/B测试路由器基于以下架构设计：

- **ABRouter类**：核心路由器，协调各功能模块
- **特征编码**：将用户画像转换为特征向量
- **相似度计算**：使用余弦相似度匹配最佳变体
- **事件管理**：追踪和存储用户行为事件
- **结果分析**：计算和比较各变体的性能指标

## 使用方法

### 变体路由

```python
from src.audience import route_variant

# 定义变体列表
variants = [
    {
        "id": "variant_1",
        "name": "标准版内容",
        "description": "标准节奏和剪辑风格",
        "feature_vector": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    },
    {
        "id": "variant_2",
        "name": "快节奏版内容",
        "description": "快速剪辑和高能量内容",
        "feature_vector": [0.9, 0.3, 0.8, 0.2, 0.7, 0.4]
    }
]

# 为用户分配最佳变体
best_variant = route_variant("user_123", variants)
print(f"分配变体: {best_variant['name']}")
```

### 创建A/B测试

```python
from src.audience import create_ab_test

# 创建A/B测试
test_config = {
    "metrics": ["completion_rate", "engagement_time"],
    "assignment_strategy": "weighted"
}

test = create_ab_test("test_123", variants, test_config)
```

### 记录用户事件

```python
from src.audience import record_ab_event

# 记录用户查看事件
record_ab_event("user_123", "variant_1", "view", {"duration": 45})

# 记录用户完成事件
record_ab_event("user_123", "variant_1", "completion", {"full": True})

# 记录用户互动事件
record_ab_event("user_123", "variant_1", "interaction", {"type": "like"})
```

### 分析测试结果

```python
from src.audience import analyze_ab_results

# 分析测试结果
results = analyze_ab_results("test_123")

# 查看各变体性能
for metric, values in results["metrics"].items():
    print(f"{metric}:")
    for variant_id, value in values.items():
        print(f"  {variant_id}: {value}")

# 查看推荐建议
for recommendation in results["recommendations"]:
    print(f"- {recommendation}")
```

## 配置选项

实时A/B测试路由器提供以下可配置选项：

### 分配策略

- `random`: 随机分配策略
- `deterministic`: 确定性分配策略（基于用户ID）
- `weighted`: 加权分配策略（基于相似度分数）

### 指标类型

默认支持的测试指标：

- `completion_rate`: 完成率
- `engagement_time`: 参与时间
- `interaction_count`: 互动次数
- `share_rate`: 分享率
- `retention_impact`: 留存影响
- `conversion_rate`: 转化率

### 缓存设置

- `cache_ttl`: 缓存有效期（秒），默认为3600秒（1小时）

## 特征向量设计

为确保有效的变体匹配，特征向量设计应遵循以下原则：

1. **一致性**: 用户向量和变体向量应使用相同的维度和范围
2. **归一化**: 向量值应当归一化处理，通常在[0,1]范围内
3. **相关性**: 向量维度应代表与用户体验相关的特征
4. **完整性**: 包含足够的维度以捕捉重要差异

典型的特征维度可能包括：内容类型、节奏偏好、情感共鸣、视觉风格等。

## 注意事项

1. 确保变体特征向量与用户特征向量维度匹配，否则路由器会自动截断或延展向量
2. 对于新用户或无画像用户，系统会使用默认向量，可能导致较低的匹配精度
3. 高频路由请求应利用缓存机制减少计算负担
4. 分析结果需要足够的样本量才具有统计意义
5. 多变量测试需要更大的用户群体才能获得可靠结果

## 扩展支持

如需扩展A/B测试路由器功能，可以：

1. 添加新的分配策略
2. 增加更多的性能指标
3. 实现更复杂的特征向量编码
4. 添加统计显著性测试
5. 集成预测模型优化路由决策 