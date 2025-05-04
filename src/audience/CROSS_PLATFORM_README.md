# 跨平台习惯融合模块 (CrossPlatformIntegrator)

## 概述

跨平台习惯融合模块是VisionAI-ClipsMaster项目的重要组件，用于整合用户在多个内容平台（如抖音、B站、YouTube等）上的行为习惯和偏好，构建统一的用户画像，为内容变形和推荐系统提供更全面的数据支持。

## 主要功能

跨平台习惯融合模块提供以下核心功能：

1. **平台数据获取**：
   - 从各大平台（抖音、B站、YouTube等）获取用户习惯数据
   - 支持通过API直接获取和本地存储数据缓存
   - 数据自动刷新和有效期管理

2. **跨平台数据整合**：
   - 将不同平台的异构数据转换为统一格式
   - 基于平台权重对数据进行加权融合
   - 解决跨平台数据冲突和补充

3. **统一偏好表达**：
   - 生成跨平台统一的用户偏好表达
   - 提供分类偏好、内容格式偏好、活跃时段等多维度偏好数据
   - 支持偏好来源追踪和置信度评估

## 实现架构

跨平台习惯融合模块采用以下架构设计：

- **CrossPlatformIntegrator类**：核心整合引擎，协调各平台数据获取和融合
- **平台数据获取器**：针对各平台的专用数据获取逻辑
- **平台权重体系**：定义各平台数据的重要程度
- **融合算法**：实现跨平台数据的智能融合
- **缓存管理**：优化性能的数据缓存机制

## 使用方法

### 基本用法

```python
from src.audience import get_platform_integrator, integrate_user_habits

# 方法1：获取整合器实例，直接调用方法
integrator = get_platform_integrator()
integrated_data = integrator.integrate_habits(user_id)

# 方法2：使用便捷函数
integrated_data = integrate_user_habits(user_id)
```

### 获取统一偏好表达

```python
from src.audience import get_unified_preference

# 获取用户的跨平台统一偏好
unified_preference = get_unified_preference(user_id)

# 使用统一偏好进行内容个性化
category_preferences = unified_preference.get("category_preferences", {})
format_preferences = unified_preference.get("format_preferences", {})
```

### 获取特定平台数据

```python
from src.audience import get_platform_habit

# 获取抖音平台习惯数据
douyin_data = get_platform_habit(user_id, "douyin")

# 获取B站平台习惯数据
bilibili_data = get_platform_habit(user_id, "bilibili")

# 获取YouTube平台习惯数据
youtube_data = get_platform_habit(user_id, "youtube")
```

## 统一偏好结构

统一偏好表达具有以下结构：

```python
{
    "category_preferences": {
        "搞笑": {
            "score": 0.85,
            "platforms": ["douyin", "bilibili"]
        },
        "科技": {
            "score": 0.75,
            "platforms": ["bilibili", "youtube"]
        }
        # 更多分类...
    },
    "format_preferences": {
        "短视频": {
            "score": 0.8,
            "platforms": ["douyin", "youtube"]
        },
        "直播": {
            "score": 0.3,
            "platforms": ["douyin", "bilibili", "youtube"]
        }
        # 更多格式...
    },
    "active_time_slots": ["18:00-22:00", "12:00-13:00", "7:00-9:00"],
    "watch_duration": {
        "average": 210.5,
        "unit": "seconds"
    },
    "platform_coverage": {
        "douyin": true,
        "bilibili": true,
        "youtube": true
    },
    "updated_at": "2025-05-03T12:30:45.123456"
}
```

## 注意事项

1. 跨平台融合需要用户事先绑定相关平台账号
2. API访问需要配置相应的访问令牌和权限
3. 统一偏好数据会自动缓存24小时，减少重复计算
4. 各平台数据获取失败不会影响整体融合，会使用可用数据进行部分融合
5. 平台权重可通过配置文件调整，影响各平台数据在融合过程中的重要程度

## 扩展支持

要添加新平台支持，可按照以下步骤操作：

1. 在CrossPlatformIntegrator类中添加新的平台数据获取方法（如`_get_new_platform_habits`）
2. 实现平台数据处理方法（如`_process_new_platform_data`）
3. 在`integrate_habits`方法中添加对新平台的支持
4. 在`get_platform_habit`方法中添加新平台的分支处理
5. 更新平台权重配置，添加新平台的权重值 