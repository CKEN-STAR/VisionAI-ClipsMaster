# 实时反馈收集器 (BioFeedbackCollector)

## 功能概述

`BioFeedbackCollector` 是一个用于收集和分析用户生物特征数据的组件，能够帮助VisionAI-ClipsMaster系统实时了解用户的情绪、注意力和参与度状态，从而优化混剪体验和内容推荐。该组件通过可穿戴设备SDK接口获取生物特征数据，进行实时分析，并自动调整系统响应和内容难度。

## 主要特性

- **实时生物特征数据收集**：支持心率、皮电反应、注意力水平等多种生物指标
- **用户参与度分析**：基于生物指标分析用户对内容的兴趣和投入程度
- **自适应内容难度**：根据用户注意力水平自动调整短剧混剪难度
- **会话级反馈跟踪**：为每个用户会话维护独立的反馈历史和适应策略
- **模拟数据支持**：在无实际硬件可用时提供模拟数据，便于开发和测试
- **可配置适应策略**：支持通过配置文件定制适应策略和阈值

## 组件结构

实时反馈收集器由两个主要类组成：

1. **WearableSDK**：可穿戴设备SDK抽象
   - 管理与可穿戴设备的连接
   - 提供生物特征数据流
   - 支持模拟数据生成

2. **BioFeedbackCollector**：反馈收集器核心类
   - 管理用户会话的反馈收集
   - 分析用户参与度和注意力水平
   - 触发内容适应性调整

## 使用方法

### 初始化反馈收集器

```python
from src.realtime import initialize_feedback_collector, get_feedback_collector

# 初始化（通常在应用启动时调用一次）
feedback_collector = await initialize_feedback_collector()

# 在其他地方获取已初始化的实例
feedback_collector = get_feedback_collector()
```

### 为会话注册反馈收集

```python
async def on_new_session(session_id):
    feedback_collector = get_feedback_collector()
    
    # 注册会话进行反馈收集
    success = await feedback_collector.register_session(session_id)
    
    if success:
        print(f"会话 {session_id} 已开始反馈收集")
    else:
        print(f"会话 {session_id} 反馈收集注册失败")
```

### 获取会话反馈指标

```python
def check_session_engagement(session_id):
    feedback_collector = get_feedback_collector()
    
    # 获取会话指标
    metrics = feedback_collector.get_session_metrics(session_id)
    
    # 使用指标
    engagement = metrics.get("metrics", {}).get("engagement_score", 0)
    attention = metrics.get("metrics", {}).get("attention_level", 0)
    
    print(f"会话 {session_id} - 参与度: {engagement:.2f}, 注意力: {attention:.2f}")
    
    return engagement > 0.5  # 根据参与度判断用户是否感兴趣
```

### 处理适应性调整消息

在会话处理循环中接收和处理由反馈收集器触发的适应性调整：

```python
async def process_session_messages(session_id):
    session_manager = get_session_manager()
    
    # 处理待处理消息
    messages = session_manager.process_pending_messages(session_id)
    
    for msg in messages:
        if msg.action == "adaptation":
            # 处理适应性调整消息
            adaptation_type = msg.data.get("type")
            level = msg.data.get("level")
            
            if adaptation_type == "difficulty_decrease":
                # 降低混剪难度
                decrease_mixing_difficulty(session_id, level)
            elif adaptation_type == "difficulty_increase":
                # 增加混剪难度
                increase_mixing_difficulty(session_id, level)
```

### 取消会话反馈收集

```python
def on_session_close(session_id):
    feedback_collector = get_feedback_collector()
    
    # 取消反馈收集
    feedback_collector.unregister_session(session_id)
    
    print(f"会话 {session_id} 的反馈收集已停止")
```

## 配置文件

反馈收集器通过`configs/wearable.json`配置文件进行配置，主要参数包括：

```json
{
  "use_simulation": true,
  "buffer_size": 200,
  "sampling_rate": 5,
  "supported_devices": ["smart_watch", "vr_headset", "armband"],
  "data_types": ["pulse", "gsr", "attention", "emotion"],
  "adaptation": {
    "enabled": true,
    "attention_thresholds": {
      "low": 0.3,
      "high": 0.7
    }
  }
}
```

## 生物指标类型

组件支持多种生物特征数据类型，通过`BioMetricType`枚举定义：

- **PULSE**: 脉搏/心率 (典型值: 60-100 bpm)
- **GSR**: 皮电反应 (典型值: 1-20 microSiemens)
- **ATTENTION**: 注意力水平 (范围: 0-1)
- **EMOTION**: 情绪状态 (范围: -1到1，负面到正面)
- **EYE_TRACKING**: 眼动追踪数据
- **FACIAL**: 面部表情分析数据
- **POSTURE**: 姿势/体态数据
- **VOICE**: 语音音调数据

## 适应性调整

反馈收集器可以根据用户的生物反馈自动触发两种主要的适应性调整：

1. **难度降低** (difficulty_decrease)
   - 触发条件：注意力水平低于阈值 (默认 0.3)
   - 适用场景：用户注意力不集中，可能对当前内容感到困难或无聊

2. **难度提高** (difficulty_increase)
   - 触发条件：注意力水平高于阈值 (默认 0.7)
   - 适用场景：用户高度专注，可能对当前内容掌握良好，需要更具挑战性的内容

## 会话指标说明

反馈收集器为每个会话维护一组关键指标：

- **engagement_score**: 参与度分数 (0-1)，表示用户对内容的整体投入程度
- **attention_level**: 注意力水平 (0-1)，表示用户的专注程度
- **emotional_response**: 情绪响应 (-1到1)，表示用户的情绪状态
- **interaction_count**: 交互计数，记录生物数据交互次数

## 注意事项

1. 生物反馈数据采样率应根据系统性能和实际需求设置，过高的采样率可能增加系统负担
2. 在无实际硬件情况下，系统默认使用模拟数据，适合开发和测试
3. 适应性调整消息是通过标准会话消息队列传递的，需要在应用中适当处理
4. 生物数据的可靠性与硬件质量直接相关，模拟数据的置信度默认较低

## 示例代码

查看`src/realtime/examples/feedback_collector_example.py`获取完整示例。 