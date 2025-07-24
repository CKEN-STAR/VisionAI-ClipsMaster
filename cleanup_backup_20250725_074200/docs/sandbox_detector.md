# 逻辑漏洞沙盒检测器

## 概述

逻辑漏洞沙盒检测器是VisionAI-ClipsMaster的一个重要模块，专门用于检测和验证视频剧本中可能存在的逻辑漏洞和不一致性。该模块采用"沙盒"方法，通过模拟插入常见逻辑缺陷并分析其检出能力，来评估脚本逻辑的稳健性，帮助创作者构建逻辑自洽的内容。

## 主要功能

1. **逻辑缺陷检测**：检测脚本中可能存在的时间跳跃、道具传送、角色分身等逻辑问题。
2. **缺陷注入测试**：通过向脚本中注入人工缺陷，测试检测器的性能和脚本的稳定性。
3. **压力测试**：注入多种典型逻辑错误，计算缺陷检出率，评估脚本的逻辑健壮性。
4. **修复建议生成**：针对检测到的逻辑问题，提供具体的修复建议。
5. **脚本评分**：基于检测到的缺陷数量和严重程度，对脚本的逻辑完整性进行评分。

## 核心类和接口

### 主要类

- **LogicSandbox**：逻辑沙盒检测器，包含检测和注入缺陷的核心功能。
- **LogicDefect**：逻辑缺陷数据类，描述检测到的缺陷及其属性。
- **LogicSandboxError**：逻辑沙盒错误异常，用于处理检测过程中的错误。

### 主要枚举

- **LogicDefectType**：逻辑缺陷类型枚举，定义了各种可能的逻辑问题类型。

### 关键方法

- `detect_defects()`：检测脚本中的逻辑缺陷。
- `inject_defect()`：向脚本中注入人工缺陷。
- `stress_test()`：进行压力测试，评估脚本的逻辑健壮性。
- `validate_logic_sandbox()`：便捷函数，一次性获取完整的逻辑分析结果。

## 支持的缺陷类型

| 缺陷类型 | 描述 | 严重程度 |
|---------|------|---------|
| **TIME_JUMP** | 时间跳跃：场景时间线异常跳跃，如时间倒流 | High |
| **PROP_TELEPORT** | 道具传送：道具无故出现或消失，未交代去向 | Medium |
| **CHARACTER_CLONE** | 角色分身：角色同时出现在不同场景 | High |
| **CHARACTER_SWAP** | 角色互换：角色特征/性格突然互换 | Medium |
| **CAUSALITY_BREAK** | 因果断裂：事件因果关系断裂，如结果出现在原因之前 | Critical |
| **DIALOGUE_MISMATCH** | 对话错位：人物对话与角色设定不符 | Medium |
| **EMOTION_FLIP** | 情感翻转：情感突然不合理转变 | High |
| **KNOWLEDGE_ERROR** | 知识错误：常识性错误或专业知识错误 | Low |
| **CONSTRAINT_BREAK** | 约束违反：违反物理或世界观规则 | Medium |
| **MOTIVATION_LOSS** | 动机丢失：角色行为失去合理动机 | High |

## 使用示例

### 基本使用

```python
from src.logic.sandbox_detector import validate_logic_sandbox

# 创建脚本数据
script = {
    "scenes": [
        {
            "id": "scene1",
            "timestamp": 1000,
            "characters": ["主角", "配角"],
            "props": ["宝剑", "地图"]
        },
        {
            "id": "scene2",
            "timestamp": 2000,
            "characters": ["主角", "配角"],
            "props": ["宝剑", "地图"]
        }
    ]
}

# 验证脚本
result = validate_logic_sandbox(script)

# 处理结果
if result["defect_count"] > 0:
    print(f"检测到 {result['defect_count']} 个逻辑缺陷")
    for defect in result["defects"]:
        print(f"- {defect['description']}")
        if "suggested_fix" in defect:
            print(f"  建议修复: {defect['suggested_fix']}")
else:
    print("未检测到逻辑缺陷，脚本评分:", result["score"])
```

### 进行压力测试

```python
from src.logic.sandbox_detector import validate_logic_sandbox

# 创建脚本数据
script = {...}  # 您的脚本数据

# 进行带压力测试的验证
result = validate_logic_sandbox(script, stress_test=True)

# 处理压力测试结果
if "stress_test" in result:
    print(f"压力测试检出率: {result['stress_test']['detection_rate']:.2%}")
    print(result["stress_test"]["description"])
```

### 手动注入缺陷

```python
from src.logic.sandbox_detector import LogicSandbox

# 创建沙盒实例和脚本
sandbox = LogicSandbox()
script = {...}  # 您的脚本数据

# 注入时间跳跃缺陷
defect_config = {"type": "TIME_JUMP", "value": -500}
corrupted_script = sandbox.inject_defect(script, defect_config)

# 检测注入后的脚本
defects = sandbox.detect_defects(corrupted_script)
```

## 脚本格式要求

沙盒检测器支持以下格式的脚本：

```json
{
    "scenes": [
        {
            "id": "scene1",
            "timestamp": 1000,  // 毫秒时间戳
            "characters": [
                {"name": "角色名", "traits": ["特性1", "特性2"]},
                // 或简单字符串数组
                "配角名"
            ],
            "props": [
                {"name": "道具名", "state": "状态"},
                // 或简单字符串数组
                "简单道具名"
            ],
            "dialogues": [
                {"character": "角色名", "text": "对话内容", "emotion": "情感状态"}
            ],
            "emotion": "场景情感",  // 或数值 [-1.0 到 1.0]
            
            // 可选的因果关系标记
            "is_cause": true,    // 指示此场景是某个结果的原因
            "cause_for": "scene2" // 指示此场景是哪个场景的原因
        },
        // 更多场景...
    ]
}
```

## 常见问题与解决方案

### 为什么检测器没有发现我脚本中的逻辑问题？

检测器主要关注结构化数据中的逻辑关系，如时间戳、道具状态和角色位置等。如果逻辑问题更多与情节内容相关，可能需要:

1. 添加更详细的场景描述和元数据
2. 确保时间戳准确反映场景发生顺序
3. 明确标记因果关系（使用`is_cause`和`cause_for`属性）

### 如何处理误报？

有时检测器可能会将合理的情况误判为逻辑缺陷：

1. 检查缺陷的`confidence`值，低于0.8的可能是误报
2. 在特殊情况下（如闪回场景），可以在场景中添加`special_type: "flashback"`等标记
3. 调整检测器的阈值：`sandbox.config["detection_threshold"] = 0.8`

### 缺陷严重程度如何确定？

严重程度基于对观众理解和故事流畅性的影响：
- **Critical**：完全破坏故事连贯性，如严重因果断裂
- **High**：明显影响理解，但不至于完全失去连贯性
- **Medium**：造成困惑，但不会严重影响整体理解
- **Low**：小错误，可能被大多数观众忽略

## 最佳实践

1. **早期验证**：在脚本初期就进行验证，避免逻辑问题累积
2. **增量检查**：每添加新场景后重新验证，快速定位新引入的问题
3. **压力测试**：对重要场景进行压力测试，评估其稳健性
4. **注重因果**：明确标记场景之间的因果关系，帮助检测器更准确分析
5. **完整元数据**：提供完整的场景元数据，包括时间戳、角色、道具状态等

## 进阶用法

### 自定义缺陷检测器

```python
from src.logic.sandbox_detector import LogicSandbox, LogicDefect, LogicDefectType

class CustomSandbox(LogicSandbox):
    def __init__(self):
        super().__init__()
        
        # 注册自定义检测器
        self.defect_detectors["custom_detector"] = self._detect_custom_problem
    
    def _detect_custom_problem(self, script):
        defects = []
        # 自定义检测逻辑
        return defects
```

### 设置检测阈值

```python
sandbox = LogicSandbox()
# 提高检测阈值，减少误报
sandbox.config["detection_threshold"] = 0.85
# 调整严重程度权重
sandbox.config["severity_weights"]["low"] = 0.3
```

## 参考资料

- 查看`examples/sandbox_detector_demo.py`获取更多使用示例
- 查看`tests/test_sandbox_detector.py`了解更多功能细节
- 尝试独立测试脚本`sandbox_detector_standalone.py`快速体验功能 