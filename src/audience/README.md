# 用户画像模块

## 概述

用户画像模块（Audience Profile Module）是VisionAI-ClipsMaster短剧混剪项目的核心组件之一，负责对用户的偏好、行为和设备环境进行多维度分析，构建全面的用户画像。这些画像数据将用于以下目的：

1. 为用户提供个性化的混剪模板和建议
2. 根据用户设备性能优化处理参数
3. 基于用户偏好推荐合适的剪辑风格和叙事结构
4. 提供数据驱动的用户体验优化

## 模块结构

用户画像模块由以下主要组件构成：

- `profile_builder.py`: 多维度用户画像构建引擎
- `preference_analyzer.py`: 用户偏好分析器
- `behavior_tracker.py`: 用户行为跟踪器
- `behavior_decoder.py`: 实时行为解码器
- `recommendation_engine.py`: 个性化推荐引擎
- `mock_data_generator.py`: 模拟数据生成器（测试用）
- `test_profile.py`: 用户画像测试脚本
- `test_behavior_decoder.py`: 行为解码器测试脚本
- `run_profile_demo.py`: 一键式演示脚本

## 用户画像维度

该模块构建的用户画像包含以下维度：

- **人口统计维度**: 年龄/性别/地域
- **行为维度**: 观看时长/留存点/交互模式
- **情感维度**: 情感共鸣点/情感曲线偏好
- **技术维度**: 设备类型/网络环境/性能约束
- **内容维度**: 短剧类型/主题偏好/角色偏好
- **剪辑风格维度**: 转场偏好/剪辑节奏/色调风格
- **叙事维度**: 叙事结构/冲突强度/角色焦点
- **节奏维度**: 场景时长/剪辑频率/紧张度构建

## 快速入门

### 创建用户画像

```python
from src.audience.profile_builder import create_user_profile

# 创建用户画像
user_id = "user_123"
profile = create_user_profile(user_id)

# 获取特定维度信息
content_prefs = profile.get("content_preferences")
device_constraints = profile.get("device_constraints")
```

### 获取和更新用户画像

```python
from src.audience.profile_builder import get_user_profile, update_user_profile

# 获取用户画像
profile = get_user_profile(user_id)

# 更新用户画像（仅更新有新数据的维度）
updated_profile = update_user_profile(user_id, partial_update=True)
```

### 解码用户行为偏好

```python
from src.audience.behavior_decoder import decode_user_behavior, decode_realtime_behavior

# 解码用户历史行为
user_id = "user_123"
preferences = decode_user_behavior(user_id, days=30)

# 实时解码单个行为事件
event = {
    "event_type": "view_complete",
    "content_id": "video_456",
    "completion_rate": 0.85,
    "duration": 180,
    "metadata": {"genre": "comedy", "theme": "friendship"}
}
signal = decode_realtime_behavior(user_id, event)
```

## 演示运行

要快速体验用户画像构建功能，可以运行以下命令：

```bash
# 生成模拟数据并测试用户画像构建
python src/audience/run_profile_demo.py

# 测试行为解码器功能
python src/audience/test_behavior_decoder.py
```

## 模拟数据生成

为了测试用户画像功能，您可以使用模拟数据生成器：

```python
from src.audience.mock_data_generator import MockDataGenerator

# 初始化生成器
generator = MockDataGenerator()

# 为测试用户生成所有模拟数据
generator.generate_all_data("test_user_001")
```

## 集成指南

要将用户画像功能集成到您的自定义模块中，请按照以下步骤操作：

1. 导入所需功能
   ```python
   from src.audience.profile_builder import get_user_profile
   from src.audience.behavior_decoder import get_behavior_decoder
   ```

2. 获取用户画像数据
   ```python
   profile = get_user_profile(user_id)
   ```

3. 使用画像数据进行决策
   ```python
   # 检查设备约束
   device_constraints = profile.get("device_constraints", {})
   if device_constraints.get("memory_limit", 0) < 4096:
       # 使用更轻量级的处理模式
       use_lightweight_processing = True
   
   # 根据用户偏好选择剪辑风格
   editing_prefs = profile.get("editing_preferences", {})
   preferred_pace = editing_prefs.get("cutting_pace", "medium")
   ```

4. 实时解码用户行为
   ```python
   # 获取行为解码器
   decoder = get_behavior_decoder()
   
   # 解码用户行为事件
   event_data = {
       "event_type": "replay",
       "content_id": "video_789",
       "position": 45.5,  # 秒
       "metadata": {"genre": "drama", "scene_type": "climax"}
   }
   signal = decoder.decode_realtime_behavior(user_id, event_data)
   
   # 基于解码结果推荐内容
   if "genre:drama" in signal["preference_signals"]:
       strength = signal["preference_signals"]["genre:drama"]["strength"]
       if strength in ["strong_like", "like"]:
           # 推荐更多同类内容
           recommend_similar_content(user_id, "drama")
   ```

## 行为解码器

行为解码器是一个强大的组件，能够将原始用户行为转化为具有实际意义的偏好信号。它提供以下核心功能：

1. **历史行为解码**：分析用户过去30天（可配置）的行为，提取多维度偏好信号
2. **实时行为解码**：针对单个用户行为事件进行即时解码，用于实时推荐
3. **兴趣点识别**：识别用户对内容特定段落的兴趣强度，优化混剪推荐
4. **多维度偏好分析**：包括内容类型、情感反应、叙事结构、节奏和剪辑风格偏好

## 注意事项

- 用户画像数据存储在 `data/profiles` 目录下
- 首次创建画像时，如果没有足够的用户行为数据，某些维度的置信度会较低
- 建议定期更新用户画像以反映用户偏好的变化
- 行为解码结果存储在 `data/preferences` 目录下
- 实时解码信号可用于即时推荐，而完整解码结果适用于长期偏好分析 