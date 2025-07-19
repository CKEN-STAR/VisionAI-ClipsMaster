# 质量熔断器（Quality Circuit Breaker）

## 简介

质量熔断器是 VisionAI-ClipsMaster 的核心质量保障组件，用于监控生成内容的质量，当连续检测到多个低质量版本时触发熔断机制，防止质量不合格的内容推送给用户，确保系统输出的持续稳定性。

灵感来自于分布式系统中的熔断器模式（Circuit Breaker Pattern），质量熔断器在内容生成领域提供了类似的保护机制：当系统检测到连续的质量问题时，会自动"断开"生成通路，防止更多低质量内容的产生，直到系统状态恢复正常。

## 核心特性

- **多维度质量评估**：从连贯性、情感流、节奏控制、叙事结构和观众参与度等多个维度评估内容质量
- **自定义质量检查器**：支持添加自定义质量检查逻辑和阈值
- **分级质量标准**：为不同用户组（内部、测试、稳定）设置不同的质量阈值
- **自动恢复机制**：支持半开状态探测和自动恢复
- **质量历史记录**：维护质量检查历史，便于分析和改进
- **REST API 接口**：提供完整的 API 接口，支持状态查询和手动控制

## 工作原理

### 状态转换

质量熔断器有三种工作状态：

1. **关闭状态 (Closed)**：正常工作状态，允许生成内容
2. **开启状态 (Open)**：熔断状态，阻止生成内容，保护系统稳定性
3. **半开状态 (Half-Open)**：恢复探测状态，允许有限的生成请求以测试系统恢复情况

![状态转换图](https://raw.githubusercontent.com/yourusername/VisionAI-ClipsMaster/main/docs/images/circuit_breaker_states.png)

### 状态转换条件

- **关闭→开启**：连续检测到 N 个不合格版本（N 为可配置的熔断阈值）
- **开启→半开**：经过一段时间后（默认5分钟）
- **半开→关闭**：连续检测到 M 个合格版本（M 为可配置的恢复阈值）
- **半开→开启**：在半开状态下检测到不合格版本

## 质量评估维度

质量熔断器通过以下维度评估内容质量：

| 维度 | 描述 | 评估器 |
|------|------|--------|
| 连贯性 | 评估内容的叙事连贯性，包括情节逻辑、角色行为一致性、对话衔接等 | `coherence_checker.py` |
| 情感流 | 评估内容的情感流动性，包括情感变化是否自然、是否有吸引力等 | `emotion_flow_evaluator.py` |
| 节奏控制 | 评估内容的节奏控制，包括叙事节奏、场景长度分布、高潮转折点布局等 | `pacing_evaluator.py` |
| 叙事结构 | 评估内容的叙事结构，包括完整性、三幕结构、情节转折点、角色弧线等 | `narrative_structure_evaluator.py` |
| 观众参与度 | 预测内容对观众的吸引力和参与度，评估内容的潜在传播力 | `audience_engagement_predictor.py` |

## 代码结构

```
src/
├── versioning/
│   ├── quality_circuit_breaker.py   # 质量熔断器核心实现
│   └── README_quality_circuit_breaker.md  # 本文档
├── evaluation/
│   ├── __init__.py                  # 评估模块初始化
│   ├── coherence_checker.py         # 连贯性检查器
│   ├── emotion_flow_evaluator.py    # 情感流评估器
│   ├── pacing_evaluator.py          # 节奏控制评估器
│   ├── narrative_structure_evaluator.py  # 叙事结构评估器
│   └── audience_engagement_predictor.py  # 观众参与度预测器
├── api/
│   └── quality_api.py               # 质量熔断器 API
└── examples/
    └── quality_circuit_breaker_demo.py  # 质量熔断器演示
```

## 使用示例

### 基本使用

```python
from src.versioning.quality_circuit_breaker import QualityGuardian, QualityCollapseError

# 创建质量守护者，设置熔断阈值和恢复阈值
guardian = QualityGuardian(failure_threshold=3, recovery_threshold=2)

# 检查版本质量
try:
    guardian.monitor([version], user_group="stable")
    print("质量检查通过")
except QualityCollapseError as e:
    print(f"质量熔断已触发: {str(e)}")
```

### 添加自定义检查器

```python
# 添加自定义质量检查器
guardian.add_custom_checker(
    "engagement_score",
    lambda v: predict_engagement_score(v),
    threshold=0.7
)
```

### 查看质量检查历史

```python
# 获取最近10条质量检查记录
history = guardian.get_quality_history(limit=10)
for record in history:
    print(f"版本 {record['version_id']}: {'通过' if record['passed'] else '未通过'}")
    for metric, score in record['metrics'].items():
        print(f"  - {metric}: {score:.2f}")
```

## API 接口

质量熔断器提供以下 API 接口：

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/quality/status` | GET | 获取熔断器状态 |
| `/api/quality/history` | GET | 获取质量检查历史 |
| `/api/quality/reset` | POST | 手动重置熔断器 |
| `/api/quality/open` | POST | 手动开启熔断器 |
| `/api/quality/check` | POST | 检查内容质量 |
| `/api/quality/configure` | POST | 配置质量守护者 |

详细接口文档请参考 API 文档。

## 注意事项

- 熔断器在开启状态下会拒绝所有生成请求，确保在集成时处理好这种情况
- 调整熔断阈值和恢复阈值时，需要平衡系统的稳定性和可用性
- 质量评估的各项指标可能需要根据实际内容类型和用户期望进行调整 