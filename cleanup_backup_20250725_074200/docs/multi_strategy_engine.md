# 多策略生成引擎

## 概述

多策略生成引擎是VisionAI-ClipsMaster的一个核心组件，它允许系统并行运行多种不同的剧本生成策略，生成风格各异的混剪方案。每种策略专注于不同的叙事特点，可以产生非常不同的混剪效果，满足不同的创作需求。

## 特点

- **并行生成**：同时执行多种生成策略，提高效率
- **风格多样**：提供多种预设策略，如倒叙叙事、多线交织、情感放大等
- **可扩展**：基于策略模式设计，便于添加新的生成策略
- **参数集成**：与参数矩阵系统无缝集成，支持精细参数控制
- **完整元数据**：生成结果包含详细策略信息，便于比较和选择

## 内置策略

多策略生成引擎内置了四种基本生成策略：

### 1. 倒叙重构 (ReverseNarrativeStrategy)

颠覆传统线性叙事，创造"倒叙"效果。将剧本按叙事单元反转，创造出"结局先行"的叙事结构，增加作品的悬念和张力。

特点：
- 低线性度 (0.3)
- 高上下文保留 (0.7)
- 高悬念频率 (0.7)
- 较高情感强度 (0.8)

### 2. 多线交织 (ParallelThreadsStrategy)

关注多个角色视角，创造多线叙事效果。识别剧本中的主要角色，为每个角色创建独立"线程"，然后交织这些线程，形成多视角叙事。

特点：
- 关注多角色 (4个)
- 多支线 (4条)
- 中低线性度 (0.4)
- 中高上下文保留 (0.6)

### 3. 情感放大 (EmotionAmplificationStrategy)

强化情感高潮，创造强烈的情感共鸣。识别情感波动明显的片段，并围绕情感高潮点重构剧本，使情感曲线更加起伏。

特点：
- 高情感强度 (0.9)
- 高金句保留率 (0.25)
- 较慢节奏 (0.8)
- 聚焦少数角色 (2个)

### 4. 极简主义 (MinimalistAdaptationStrategy)

削减次要元素，专注核心冲突和主线。识别剧本中最重要的角色和事件，移除次要情节，创造简洁明快的叙事风格。

特点：
- 较快节奏 (1.2)
- 单一主线 (1条)
- 聚焦单一角色 (1个)
- 较低上下文保留 (0.4)
- 高线性度 (0.85)

## 使用方法

### 基本用法

```python
from src.versioning import run_multi_strategy

# 加载字幕
subtitles = parse_srt_file("path/to/subtitles.srt")

# 运行多策略生成 - 使用所有策略
results = run_multi_strategy(subtitles)

# 使用特定策略
results = run_multi_strategy(
    subtitles=subtitles,
    strategies=["倒叙重构", "情感放大"]
)

# 自定义参数
results = run_multi_strategy(
    subtitles=subtitles,
    params={
        "target_duration": 60,
        "max_segments": 12,
        "emotion_intensity": 0.8
    }
)
```

### 结果处理

生成结果是包含多个剧本方案的列表，每个方案包含以下信息：

- `segments`: 生成的剧本片段列表
- `strategy`: 策略信息，包括名称、描述、特点等
- `metadata`: 生成过程的元数据

```python
# 处理生成结果
for result in results:
    strategy = result.get("strategy", {})
    segments = result.get("segments", [])
    
    print(f"策略: {strategy.get('name')}")
    print(f"生成片段数: {len(segments)}")
    
    # 导出为SRT文件
    export_to_srt(segments, f"{strategy.get('name')}_result.srt")
```

## 自定义策略

可以通过继承`GenerationStrategy`基类来创建自定义生成策略：

```python
from src.versioning import GenerationStrategy

class MyCustomStrategy(GenerationStrategy):
    """自定义策略描述"""
    
    def __init__(self):
        super().__init__("我的策略")
    
    def execute(self, base_script, params=None):
        # 自定义策略参数
        strategy_params = {
            "pace": 1.1,
            "linearity": 0.5,
            # 其他参数...
        }
        
        # 合并自定义参数
        if params:
            strategy_params.update(params)
        
        # 实现自定义逻辑...
        
        # 处理后的剧本
        processed_script = process_my_way(base_script)
        
        # 使用基础引擎生成最终剧本
        result = self.screenplay_engineer.generate_screenplay(
            processed_script,
            custom_params=strategy_params
        )
        
        # 添加策略信息
        result["strategy"] = {
            "name": self.name,
            "description": self.__doc__,
            "timestamp": time.time(),
            "custom_info": "自定义信息"
        }
        
        return result
```

注册自定义策略：

```python
# 创建多策略引擎实例
engine = MultiStrategyEngine()

# 注册自定义策略
engine.strategies["我的策略"] = MyCustomStrategy()

# 使用引擎生成
results = engine.generate(subtitles)
```

## 多策略比较

当生成多个结果后，可以比较不同策略的效果，选择最适合的方案：

```python
# 比较不同策略的结果
for result in results:
    strategy = result.get("strategy", {})
    segments = result.get("segments", [])
    
    # 计算总时长
    total_duration = sum(seg.get("end_time", 0) - seg.get("start_time", 0) for seg in segments)
    
    print(f"策略: {strategy.get('name')}")
    print(f"片段数: {len(segments)}")
    print(f"总时长: {total_duration:.1f}秒")
    print("-" * 30)
```

## 高级功能

### 基于内容的策略推荐

系统可以分析原始内容的特点，推荐最适合的生成策略：

```python
from src.versioning import MultiStrategyEngine
from src.versioning.param_manager import get_param_manager

# 分析内容特征
param_manager = get_param_manager()
content_analysis = param_manager.analyze_content(subtitles)

# 根据内容特征选择合适的策略
if content_analysis.get("emotion_variation", 0) > 0.7:
    # 情感波动大，适合情感放大策略
    strategy_names = ["情感放大"]
elif content_analysis.get("character_count", 0) > 3:
    # 角色较多，适合多线交织策略
    strategy_names = ["多线交织"]
else:
    # 其他情况使用默认策略
    strategy_names = ["倒叙重构", "极简主义"]

# 执行选定的策略
engine = MultiStrategyEngine()
results = engine.generate(subtitles, strategy_names)
```

### 策略组合

可以将多个策略的特点组合起来，创建混合效果：

```python
# 创建一个组合多种策略特点的参数集
combined_params = {
    "linearity": 0.3,            # 倒叙重构的低线性度
    "emotion_intensity": 0.9,    # 情感放大的高情感强度
    "character_focus": 1,        # 极简主义的单角色聚焦
    "pace": 1.2                  # 极简主义的快节奏
}

# 使用组合参数生成
results = run_multi_strategy(
    subtitles=subtitles,
    strategies=["倒叙重构"],  # 选择一个基础策略
    params=combined_params    # 使用组合参数
)
```

## 注意事项

1. **性能考虑**：并行执行多个策略可能会消耗较多系统资源，特别是内存
2. **结果一致性**：不同策略可能产生长度和结构差异很大的结果
3. **策略冲突**：某些自定义参数可能与策略的核心特点冲突
4. **语言依赖**：某些策略对特定语言的效果可能有差异

## 总结

多策略生成引擎为VisionAI-ClipsMaster提供了强大的生成能力，可以根据不同的创作需求生成风格多样的混剪方案。通过策略模式的设计，系统可以轻松扩展新的生成策略，满足更多样化的创作需求。 