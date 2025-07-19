# 模式实时更新器 (Pattern Updater)

模式实时更新器是VisionAI-ClipsMaster系统的核心组件之一，负责处理流式输入的命中数据，挖掘新模式，并将其合并到模式数据库中，支持实时模式库更新和版本管理。

## 功能特点

- **流式处理**: 支持批量处理新的命中数据
- **模式挖掘**: 从命中数据中挖掘新的模式
- **重要性评估**: 评估模式的重要性和影响力
- **模式合并**: 将重要模式合并到模式数据库
- **版本管理**: 自动创建和管理模式版本
- **配置灵活**: 支持通过配置文件自定义行为

## 架构设计

模式实时更新器与系统的以下组件紧密集成：

1. **模式挖掘器** (`PatternMiner`): 负责从数据中挖掘模式
2. **模式评估器** (`PatternEvaluator`): 评估模式的重要性
3. **数据湖** (`HitPatternLake`): 存储和查询命中数据
4. **版本管理器** (`PatternVersionManager`): 管理模式版本

## 使用方法

### 通过代码调用

```python
from src.core.pattern_updater import PatternUpdater

# 初始化更新器
updater = PatternUpdater(config_path="configs/pattern_updater.yaml")

# 准备命中数据
hit_data = [
    {
        "id": "sample_1",
        "origin_srt": "原始字幕内容...",
        "hit_srt": "命中字幕内容...",
        "metadata": {"views": 10000, "likes": 500}
    }
]

# 调用更新方法
result = updater.streaming_update(hit_data)
print(result)
```

### 通过API调用

```bash
# 更新模式库
curl -X POST "http://localhost:8000/api/v1/patterns/update" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "hit_data": [
      {
        "id": "sample_1",
        "origin_srt": "原始字幕内容...",
        "hit_srt": "命中字幕内容...",
        "metadata": {"views": 10000, "likes": 500}
      }
    ],
    "timeout": 30
  }'

# 查询更新状态
curl -X GET "http://localhost:8000/api/v1/patterns/update/{update_id}" \
  -H "X-API-Key: your_api_key"
```

## 配置说明

可以通过配置文件自定义模式实时更新器的行为：

```yaml
# configs/pattern_updater.yaml

# 批处理设置
batch_size: 50                   # 批处理大小
update_threshold: 0.6            # 模式更新阈值（影响力分数）
min_patterns_for_version: 10     # 创建新版本所需的最小模式数量

# 版本管理
auto_version: true               # 是否自动创建新版本
version_interval: 86400          # 版本更新间隔（秒），默认24小时

# 模式类型配置
pattern_types:                   # 支持的模式类型
  - opening                      # 开场模式
  - climax                       # 高潮模式
  - transition                   # 过渡模式
  - conflict                     # 冲突模式
  - resolution                   # 解决模式
  - ending                       # 结束模式
```

## 流程说明

模式实时更新器的处理流程如下：

1. **接收命中数据**: 接收新的命中数据
2. **数据导入**: 将命中数据导入数据湖
3. **模式挖掘**: 从数据湖中查询最新数据，挖掘新模式
4. **模式评估**: 评估模式的重要性和影响力
5. **模式筛选**: 筛选出重要的模式
6. **模式合并**: 将重要模式合并到模式数据库
7. **版本管理**: 根据配置创建新版本

## 注意事项

- 模式更新是一个计算密集型操作，建议在后台异步执行
- 版本管理需要足够的磁盘空间存储不同版本的模式
- 建议定期清理数据湖中的旧数据，以提高性能 