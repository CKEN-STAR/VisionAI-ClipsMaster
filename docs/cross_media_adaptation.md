# 跨媒介模式迁移 (Cross-Media Pattern Adaptation)

跨媒介模式迁移是VisionAI-ClipsMaster系统的高级功能，允许将在一种媒介类型（如电影）中表现良好的叙事模式，自动适配到其他媒介类型（如短视频、互动剧、广播剧、漫画等）。

## 功能概述

跨媒介模式迁移解决了以下核心问题：

1. **媒介特性差异**：不同媒介类型具有不同的叙事特点、长度限制和表现形式。
2. **受众期望差异**：不同媒介的受众有不同的期望和消费习惯。
3. **表现手法差异**：每种媒介有其独特的表现手法和最佳实践。

跨媒介适配器能够智能地分析模式特点，根据目标媒介的特性进行自动转换，保留模式的核心价值同时优化其表现形式。

## 支持的媒介类型

系统当前支持以下媒介类型的适配：

| 媒介类型 | 英文标识 | 核心特点 | 适配策略 |
|----------|----------|----------|----------|
| 短视频   | short_video | 时长短、节奏快、钩子强 | 时长压缩、叙事密度提高 |
| 互动剧   | interactive | 多分支、玩家决策、结果差异 | 添加分支、决策点 |
| 广播剧   | radio_drama | 纯音频、声音表现、听觉焦点 | 增强音频提示、语音强调 |
| 漫画     | comic | 视觉分镜、静态表现、关键画面 | 关键词突出、面板规划 |
| 电影     | movie | 视听结合、叙事完整、场景丰富 | 保持原有特性 |
| 网剧     | web_series | 剧集化、连续性、钩子设计 | 集末钩子、角色聚焦 |
| 动画     | animation | 夸张表现、风格化、动态展示 | 视觉夸张、动态强调 |

## 适配流程

跨媒介模式迁移遵循以下流程：

1. **模式分析**：分析原始模式的类型、特性和核心内容
2. **媒介映射**：确定适配目标媒介类型的特性要求
3. **特性调整**：根据媒介差异调整模式特性（如时长、分支、音频等）
4. **记录适配**：记录适配历史和方法，便于追踪和分析
5. **版本管理**：支持以版本为单位进行批量适配和管理

## 使用方法

### Python API

```python
from src.adaptation.cross_media import CrossMediaAdapter

# 初始化适配器
adapter = CrossMediaAdapter(config_path="configs/adaptation/cross_media.yaml")

# 单个模式适配
original_pattern = {...}  # 原始模式数据
adapted_pattern = adapter.adapt_pattern(original_pattern, "短视频")

# 批量适配
patterns = [...]  # 模式列表
adapted_patterns = adapter.batch_adapt_patterns(patterns, "互动剧")

# 版本适配
adapter.create_adapted_version("v1.0", "广播剧")  # 从v1.0版本适配到广播剧
```

### HTTP API

系统提供了RESTful API接口用于跨媒介模式迁移：

#### 获取支持的媒介类型

```
GET /api/v1/adaptation/media-types
```

响应：
```json
[
  "短视频",
  "互动剧",
  "广播剧",
  "漫画",
  "电影",
  "网剧",
  "动画"
]
```

#### 单次适配模式

```
POST /api/v1/adaptation/adapt
```

请求体：
```json
{
  "patterns": [
    {
      "id": "pattern_1",
      "type": "climax",
      "media_type": "电影",
      "data": {
        "description": "高潮类型叙事模式",
        "duration": 180.0,
        "position": 0.7,
        "sentiment": 0.8
      }
    }
  ],
  "target_media_type": "短视频"
}
```

#### 版本适配

```
POST /api/v1/adaptation/version/adapt
```

请求体：
```json
{
  "source_version": "v1.0",
  "target_media_type": "互动剧"
}
```

## 配置说明

跨媒介适配器使用YAML配置文件来定义适配规则和参数。配置文件位于`configs/adaptation/cross_media.yaml`，主要包含以下部分：

1. **媒介类型列表**：定义支持的所有媒介类型
2. **适配规则**：每种媒介类型的具体适配规则和参数
3. **模式适配方法**：针对不同模式类型和目标媒介的具体适配方法
4. **媒介特定调整**：每种媒介的特定调整参数
5. **质量检查**：适配质量的检查参数

详细配置示例：

```yaml
# 跨媒介模式迁移配置

# 支持的媒介类型
media_types:
  - 短视频
  - 互动剧
  - 广播剧
  - 漫画
  - 电影
  - 网剧
  - 动画

# 各媒介类型的适配规则
adaptation_rules:
  # 短视频适配规则
  短视频:
    duration_factor: 0.4       # 时长缩短到40%
    narrative_density: 2.0     # 叙事密度提高1倍
    pattern_priorities:        # 优先保留的模式类型
      - climax                 # 高潮
      - conflict               # 冲突
    focus_areas:               # 重点关注区域
      - opening                # 开场
      - ending                 # 结束
```

## 适配示例

### 电影模式 → 短视频

原电影模式：
```json
{
  "id": "pattern_1",
  "type": "climax",
  "media_type": "电影",
  "description": "主角面临最终抉择的高潮场景",
  "duration": 240.0,
  "position": 0.8,
  "sentiment": 0.7,
  "keywords": ["抉择", "高潮", "转折"],
  "narrative_density": 0.8
}
```

适配到短视频后：
```json
{
  "id": "pattern_1",
  "type": "climax",
  "media_type": "短视频",
  "description": "主角面临最终抉择的高潮场景",
  "duration": 72.0,
  "position": 0.8,
  "sentiment": 0.7,
  "keywords": ["抉择", "高潮", "转折"],
  "narrative_density": 1.6,
  "adapted": true,
  "source_media": "电影",
  "target_media": "短视频",
  "adaptation_method": "intensify",
  "quick_hook": true,
  "attention_grabbing": true,
  "preservation_priority": "high",
  "adaptation_history": [
    {
      "timestamp": "2023-05-01T12:30:45.123456",
      "from": "电影",
      "to": "短视频",
      "method": "intensify"
    }
  ]
}
```

## 注意事项

1. **保留核心内容**：跨媒介适配会保留模式的核心内容和情感意图，只调整表现形式。
2. **适配历史追踪**：每次适配都会记录历史信息，便于分析和回溯。
3. **批量适配效率**：批量适配比单个模式适配更高效，特别是处理大量模式时。
4. **质量控制**：系统会检查适配质量，确保适配后的模式仍然保持有效。
5. **版本管理**：推荐使用版本管理方式进行适配，便于整体维护和更新。 