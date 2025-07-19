# 实时错误检测器

实时错误检测器提供在导出过程中实时检测和处理各类错误的功能，集成了项目中的各种验证器，为导出流程提供了全面的错误检测和报告能力。

## 主要功能

- **多阶段错误检测**：在导出流程的不同阶段进行专门的错误检测
- **实时监控**：对导出过程进行实时监控，及时发现问题
- **错误分类与分析**：集成异常分类系统，对错误进行分类并分析模式
- **错误报告生成**：生成结构化的错误报告，便于分析和修复
- **钩子机制**：支持自定义检测钩子，扩展检测能力

## 使用方法

### 基础用法

```python
from src.exporters.error_detector import get_error_detector, DetectionPhase

# 获取错误检测器
detector = get_error_detector()

# 在特定阶段进行检测
context = {"template": {...}}  # 上下文信息
detector.detect_errors(DetectionPhase.PRE_XML_GENERATE, context)

# 检查结果
validation_result = detector.get_validation_result()
if validation_result.is_valid:
    print("检测通过")
else:
    print(f"检测失败: {len(validation_result.errors)} 个错误")
    
# 生成报告
report = detector.generate_report(format="json")
```

### 使用装饰器

```python
from src.exporters.error_detector import with_error_detection, DetectionPhase

# 使用装饰器自动进行错误检测
@with_error_detection(DetectionPhase.PRE_FFMPEG_EXECUTE)
def execute_ffmpeg(params):
    # 函数执行前会进行 PRE_FFMPEG_EXECUTE 阶段的检测
    # 函数执行后会自动进行 POST_FFMPEG_EXECUTE 阶段的检测
    return {"ffmpeg_output": "...", "return_code": 0}
```

### 实时监控

```python
from src.exporters.error_detector import get_error_detector

detector = get_error_detector()

# 启动实时监控
detector.start_realtime_monitoring({"export_type": "video"})

# 进行导出操作...

# 停止监控并获取统计
stats = detector.stop_realtime_monitoring()
print(f"检测到 {stats['stats']['errors_detected']} 个错误")
```

## 检测阶段

错误检测器定义了以下检测阶段：

- `PRE_EXPORT`：导出前检查
- `PRE_XML_GENERATE`：XML生成前检查
- `POST_XML_GENERATE`：XML生成后检查
- `PRE_LEGAL_INJECT`：法律声明注入前检查
- `POST_LEGAL_INJECT`：法律声明注入后检查
- `PRE_FFMPEG_EXECUTE`：FFmpeg执行前检查
- `POST_FFMPEG_EXECUTE`：FFmpeg执行后检查
- `POST_EXPORT`：导出后检查
- `CUSTOM`：自定义检查点

## 扩展检测能力

```python
from src.exporters.error_detector import get_error_detector, DetectionPhase

detector = get_error_detector()

# 定义自定义检测钩子
def check_audio_quality(context):
    # 检查音频质量
    audio_data = context.get('audio_data')
    if not audio_data:
        return False
        
    # 进行检查...
    return True

# 注册钩子
detector.register_hook(DetectionPhase.PRE_FFMPEG_EXECUTE, check_audio_quality)
```

## 集成异常分类系统

错误检测器与异常分类系统集成，提供了更强大的错误分类和处理能力：

```python
from src.exporters.error_detector import get_error_detector

detector = get_error_detector()

# 分类错误
try:
    # 执行某些操作...
    raise ValueError("参数错误")
except Exception as e:
    # 分类错误
    classification = detector.classify_error(e)
    print(f"错误严重度: {classification['severity']}")
    print(f"建议操作: {classification['recommended_action']}")
    
    # 添加错误
    detector.add_error(e)
```

## 错误模式分析

```python
from src.exporters.error_detector import get_error_detector

detector = get_error_detector()

# 分析错误模式
patterns = detector.analyze_error_patterns()
print(f"常见错误: {patterns['common_error_codes']}")
print(f"错误热点: {patterns['error_hotspots']}")
print(f"恢复成功率: {patterns['recovery_success_rate']}%")
```

## 与其他组件集成

错误检测器与以下组件紧密集成：

- **错误报告器**：用于生成结构化的错误报告
- **异常分类系统**：对错误进行分类和分析
- **全局错误处理器**：处理无法自动恢复的错误

通过这些集成，错误检测器提供了全面的错误检测、分析和处理能力，确保导出流程的可靠性和质量。 