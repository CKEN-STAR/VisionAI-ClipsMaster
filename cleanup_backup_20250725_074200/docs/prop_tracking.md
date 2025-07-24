# 道具线索追踪系统

本文档介绍如何使用VisionAI-ClipsMaster项目中的道具线索追踪系统。该系统用于追踪视频剪辑中道具的使用一致性，帮助创作者避免混剪过程中出现道具突然出现或消失等连续性错误。

## 功能概述

道具线索追踪系统提供以下主要功能：

1. **道具出现记录** - 追踪并记录道具首次出现的场景及其来源
2. **道具使用追踪** - 跟踪道具在不同场景中的使用情况和状态变化
3. **道具消失验证** - 确认道具的消失是否合理（如被销毁、交给他人等）
4. **道具一致性检查** - 检查角色在各场景中持有的道具是否一致
5. **道具时间线分析** - 提供道具在整个视频中的使用历史和状态变化

## 使用方法

### 基本用法

最简单的使用方式是通过`track_props`函数分析场景序列中的道具使用情况：

```python
from src.logic import track_props

# 准备场景数据
scenes = [
    {
        "id": "scene1",
        "character": "小明",
        "props": ["手机", {"name": "钥匙", "origin": "抽屉"}],
        "tags": ["origin"]
    },
    # 更多场景...
]

# 执行道具追踪
result = track_props(scenes)

# 处理结果
print(f"发现 {len(result['issues'])} 个道具使用问题")
for issue in result['issues']:
    print(f"- {issue['message']}")
```

### 高级用法

如需更灵活的控制，可以直接使用`PropTracker`类：

```python
from src.logic import PropTracker

tracker = PropTracker()

# 追踪道具使用
issues = tracker.track_prop_usage(scenes)

# 获取特定道具的时间线
key_timeline = tracker.get_prop_timeline("钥匙")
for record in key_timeline:
    print(f"场景 {record['scene_id']} - 状态: {record['status']}")

# 获取角色持有的道具
character_props = tracker.get_character_props("小明")
print(f"小明持有的道具: {character_props}")
```

## 输入数据格式

道具追踪系统处理的场景数据应包含以下格式的道具信息：

### 场景结构

```python
{
    "id": "scene1",               # 场景ID
    "character": "角色名",         # 场景中的主要角色（可选）
    "props": [...],               # 场景中出现的道具（列表、集合或字典）
    "tags": ["tag1", "tag2"],     # 场景标签（可选）
    "text": "场景描述文本"         # 场景文本内容（可选）
}
```

### 道具表示方式

道具可以用以下几种方式表示：

1. **简单字符串**：只表示道具名称
   ```python
   "props": ["手机", "钥匙", "背包"]
   ```

2. **详细字典**：包含道具的名称、来源、状态等信息
   ```python
   "props": [
       {"name": "手机", "status": "present"},
       {"name": "钥匙", "origin": "抽屉", "status": "obtained"}
   ]
   ```

3. **混合列表**：同时包含简单字符串和详细字典
   ```python
   "props": ["手机", {"name": "钥匙", "status": "lost"}]
   ```

4. **字典格式**：使用键值对表示道具及其属性
   ```python
   "props": {
       "手机": {"status": "present"},
       "钥匙": "正在使用"
   }
   ```

### 道具状态类型

系统支持以下道具状态：

- `"present"` - 存在（默认状态）
- `"obtained"` - 获得
- `"created"` - 创建
- `"lost"` - 丢失
- `"destroyed"` - 销毁
- `"given"` - 给予他人
- `"returned"` - 归还
- `"using"` - 正在使用
- `"hidden"` - 隐藏
- `"stored"` - 存储
- `"inactive"` - 未激活
- `"found"` - 被发现

## 结果解析

`track_props`函数返回的结果包含以下内容：

```python
{
    "issues": [
        {
            "type": "prop_origin",        # 问题类型
            "prop": "道具名称",           # 相关道具
            "scene_id": "scene2",         # 场景ID
            "scene_index": 1,             # 场景索引
            "message": "问题描述信息"      # 人类可读的问题描述
        },
        # 更多问题...
    ],
    "statistics": {
        "total_props": 5,                 # 总道具数量
        "props_with_issues": 2,           # 有问题的道具数量
        "prop_details": {                 # 各道具详情
            "手机": {
                "appearances": 4,         # 出现次数
                "origin": "从抽屉里拿出",  # 来源
                "last_status": "present", # 最后状态
                "characters": ["小明", "小红"] # 相关角色
            },
            # 更多道具...
        }
    }
}
```

## 问题类型

系统可能检测到的道具问题类型包括：

1. **prop_origin** - 道具未说明来源，突然出现
2. **prop_continuity** - 角色持有的道具在某场景中消失
3. **prop_unresolved** - 道具的最终去向未交代

## 特殊场景处理

系统会自动识别某些特殊类型的场景，在这些场景中可能不需要显示角色持有的所有道具：

- **闪回场景**（tags包含"flashback"或"闪回"）
- **梦境场景**（tags包含"dream"或"梦境"）
- **特写场景**（tags包含"closeup"或"特写"）
- **过渡场景**（type为"transition"或"过渡"）
- **蒙太奇场景**（type为"montage"或"蒙太奇"）

## 示例

以下是一个完整的使用示例：

```python
from src.logic import PropTracker

# 创建场景数据
scenes = [
    {
        "id": "scene1",
        "character": "张三",
        "text": "张三从抽屉里拿出钥匙和手机。",
        "props": [
            {"name": "钥匙", "origin": "抽屉", "status": "obtained"},
            {"name": "手机", "origin": "抽屉", "status": "obtained"}
        ],
        "tags": ["origin"]
    },
    {
        "id": "scene2",
        "character": "张三",
        "text": "张三走在街上，看着手机导航。",
        "props": ["手机", "钥匙"]
    },
    {
        "id": "scene3",
        "character": "张三",
        "text": "张三发现钥匙不见了。",
        "props": ["手机"]
    }
]

# 创建追踪器
tracker = PropTracker()
issues = tracker.track_prop_usage(scenes)

# 输出问题
for issue in issues:
    print(f"{issue['message']}")

# 输出钥匙的时间线
key_timeline = tracker.get_prop_timeline("钥匙")
for record in key_timeline:
    print(f"场景 {record['scene_id']} - 状态: {record['status']}")
```

## 实现位置

本组件的实现位于`src/logic/prop_continuity.py`。 