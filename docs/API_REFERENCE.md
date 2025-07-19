# VisionAI-ClipsMaster 开发者 API 文档

## 目录
1. [接口概览](#接口概览)
2. [数据结构](#数据结构)
3. [接口定义](#接口定义)
4. [错误码说明](#错误码说明)
5. [多语言与模型配置说明](#多语言与模型配置说明)
6. [性能监控与报告](#性能监控与报告)
7. [高级用例](#高级用例)
8. [开发者工具](#开发者工具)

---

## 接口概览

| 路径                   | 方法   | 描述                 | 说明                       |
|------------------------|--------|----------------------|----------------------------|
| /api/v1/generate       | POST   | 生成视频剪辑         | 单个视频剪辑处理           |
| /api/v1/batch          | POST   | 批量处理视频         | 一次请求处理多个视频       |
| /api/v1/status         | GET    | 查询任务状态         | 获取处理进度和结果         |
| /api/v1/report         | GET    | 获取测试报告         | 性能和质量报告             |
| /api/v1/models         | GET    | 获取模型状态         | 查询可用模型和状态         |

---

## 数据结构

### 枚举类型

#### QuantizationLevel

```python
class QuantizationLevel(str, Enum):
    """量化等级枚举"""
    Q2_K = "Q2_K"      # 最低内存占用(~2GB)，质量较低
    Q4_K_M = "Q4_K_M"  # 平衡内存占用(~4GB)和质量
    Q5_K_M = "Q5_K_M"  # 较高质量，内存占用~5GB
    Q8_0 = "Q8_0"      # 最高质量，内存占用最大(~7GB)
```

#### Language

```python
class Language(str, Enum):
    """支持的语言枚举"""
    CHINESE = "zh"
    ENGLISH = "en"
```

#### ExportFormat

```python
class ExportFormat(str, Enum):
    """导出格式枚举"""
    VIDEO = "video"      # 仅视频文件
    PROJECT = "project"  # 仅项目文件 
    BOTH = "both"        # 视频和项目文件
```

#### TaskStatus

```python
class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
```

### 请求与响应结构

#### ClipRequest

```python
class ClipRequest(BaseModel):
    """视频剪辑生成请求体"""
    video_path: str                # 视频文件路径，支持相对路径或绝对路径
    srt_path: str                  # 字幕文件路径，支持SRT或ASS格式
    quant_level: QuantizationLevel = QuantizationLevel.Q4_K_M  # 量化等级
    lang: Language = Language.CHINESE                          # 处理语言
    export_format: ExportFormat = ExportFormat.BOTH            # 导出格式
    max_duration: Optional[float] = None   # 最大输出时长(秒)，None表示不限制
    narrative_focus: Optional[List[str]] = None  # 叙事重点关键词列表
    temperature: float = 0.7       # 生成温度，控制创意度(0.1-1.0)
    preserve_segments: Optional[List[Dict[str, float]]] = None  # 必须保留的片段时间点
```

#### ClipResponse

```python
class ClipResponse(BaseModel):
    """视频剪辑生成响应体"""
    task_id: str         # 任务ID，可用于后续查询状态
    project_path: Optional[str] = None  # 生成的工程文件路径
    video_path: Optional[str] = None    # 生成的视频文件路径
    render_time: float   # 渲染耗时（秒）
    status: TaskStatus   # 任务状态
    progress: Optional[float] = None  # 处理进度(0-1)，仅适用于processing状态
    message: Optional[str] = None     # 详细信息或错误描述
    metrics: Optional[Dict[str, Any]] = None  # 性能和质量指标
```

#### BatchClipRequest

```python
class BatchClipRequest(BaseModel):
    """批量视频剪辑请求"""
    clips: List[ClipRequest]  # 剪辑请求列表
    parallel: int = 1         # 并行处理数量，默认为1
```

#### BatchClipResponse

```python
class BatchClipResponse(BaseModel):
    """批量视频剪辑响应"""
    batch_id: str        # 批次ID
    task_ids: List[str]  # 任务ID列表
    status: TaskStatus   # 批次整体状态
    completed: int = 0   # 已完成任务数量
    total: int           # 总任务数量
    message: Optional[str] = None  # 详细信息
```

---

## 接口定义

### 1. 生成视频剪辑

**POST** `/api/v1/generate`

生成单个视频的剪辑，支持丰富的剪辑参数设置。

- **Content-Type**: application/json
- **Request Body**: `ClipRequest`
- **Response Body**: `ClipResponse`

**请求示例**：

```json
{
  "video_path": "/data/input/videos/drama_ep1.mp4",
  "srt_path": "/data/input/subtitles/drama_ep1.srt",
  "quant_level": "Q4_K_M",
  "lang": "zh",
  "export_format": "both",
  "max_duration": 180,
  "narrative_focus": ["感人", "冲突", "高潮"],
  "temperature": 0.8,
  "preserve_segments": [
    {"start": 320.5, "end": 325.2},
    {"start": 450.8, "end": 455.3}
  ]
}
```

**响应示例**：

```json
{
  "task_id": "task_20250429_123456",
  "project_path": "/data/output/edit_projects/drama_ep1_remix.fcpxml",
  "video_path": "/data/output/final_videos/drama_ep1_remix.mp4",
  "render_time": 42.7,
  "status": "success",
  "message": "剪辑生成成功",
  "metrics": {
    "input_duration": 1245.6,
    "output_duration": 175.3,
    "compression_ratio": 0.141,
    "memory_peak_mb": 3524
  }
}
```

### 2. 批量处理视频

**POST** `/api/v1/batch`

一次请求提交多个视频剪辑任务，系统自动调度和并行处理。

- **Content-Type**: application/json
- **Request Body**: `BatchClipRequest`
- **Response Body**: `BatchClipResponse`

**请求示例**：

```json
{
  "clips": [
    {
      "video_path": "/data/input/videos/drama_ep1.mp4",
      "srt_path": "/data/input/subtitles/drama_ep1.srt",
      "lang": "zh"
    },
    {
      "video_path": "/data/input/videos/drama_ep2.mp4",
      "srt_path": "/data/input/subtitles/drama_ep2.srt",
      "lang": "zh"
    }
  ],
  "parallel": 2
}
```

**响应示例**：

```json
{
  "batch_id": "batch_20250429_123456",
  "task_ids": ["task_20250429_123456", "task_20250429_123457"],
  "status": "processing",
  "completed": 0,
  "total": 2,
  "message": "批量任务已提交，正在处理"
}
```

### 3. 查询任务状态

**GET** `/api/v1/status?task_id=task_20250429_123456`

查询单个任务的处理状态和进度，包括处理中、成功或失败状态，以及详细指标。

- **Response Body**:
  ```json
  {
    "task_id": "task_20250429_123456",
    "status": "processing",
    "progress": 0.85,
    "message": "处理中：正在渲染最终视频",
    "metrics": {
      "memory_usage_mb": 3245,
      "elapsed_time": 38.5
    }
  }
  ```

### 4. 获取测试报告

**GET** `/api/v1/report?format=html`

获取系统性能和测试报告，支持多种格式。

- **请求参数**:
  - `format`: 报告格式，可选值：`html`, `json`, `md`
  - `type`: 报告类型，可选值：`performance`, `quality`, `all`
  
- **Response Body**: 返回对应格式的测试报告内容

### 5. 获取模型状态

**GET** `/api/v1/models`

获取系统中所有可用模型的状态，包括是否已下载、量化等级等信息。

- **Response Body**:
  ```json
  {
    "models": [
      {
        "name": "qwen2.5-7b-zh",
        "language": "zh",
        "status": "loaded",
        "quantization": "Q4_K_M",
        "memory_usage_mb": 3254
      },
      {
        "name": "mistral-7b-en",
        "language": "en",
        "status": "not_downloaded",
        "download_url": "https://huggingface.co/path/to/model"
      }
    ],
    "active_model": "qwen2.5-7b-zh"
  }
  ```

---

## 错误码说明

| code      | message                | 说明                     | 建议处理方式                           |
|-----------|------------------------|--------------------------|----------------------------------------|
| 0         | success                | 成功                     | 正常处理响应结果                       |
| 1001      | invalid_input          | 输入参数错误             | 检查请求参数是否符合要求               |
| 1002      | file_not_found         | 文件不存在               | 确认视频或字幕文件路径是否正确         |
| 1003      | model_not_available    | 模型未配置或未下载       | 下载相应模型或切换到已下载的模型       |
| 1004      | unsupported_format     | 不支持的文件格式         | 转换为支持的格式(mp4/avi/mov/srt/ass)  |
| 1101      | memory_limit_exceeded  | 内存不足                 | 降低量化等级或减少并行任务数量         |
| 1102      | process_timeout        | 处理超时                 | 尝试缩小输入文件或增加超时时间         |
| 2001      | internal_error         | 服务内部错误             | 检查日志或联系管理员                   |
| 2002      | model_error            | 模型推理错误             | 尝试使用不同的量化等级或参数           |
| 2003      | export_failed          | 导出失败                 | 检查输出路径权限或磁盘空间             |

---

## 多语言与模型配置说明

### 模型配置详情

系统默认使用中文模型（Qwen2.5-7B），英文模型（Mistral-7B）仅保留配置，首次不会下载。

- **中文模型**：
  - 路径：`models/qwen/quantized/qwen2.5-7b-zh.gguf`
  - 量化等级：Q4_K_M (默认)
  - 内存需求：约4GB
  - 状态：默认已下载

- **英文模型**：
  - 路径：`models/mistral/quantized/mistral-7b-en.gguf`
  - 量化等级：Q4_K_M (默认)
  - 内存需求：约4GB
  - 状态：配置已预留，首次不下载

### 使用多语言模型

要使用英文模型，您可以：

1. 手动下载模型文件放入配置路径
2. API调用中指定 `"lang": "en"`

系统将自动检测模型是否已下载，如未下载则返回 `model_not_available` 错误。

### 动态切换语言

同一应用实例可以处理不同语言任务，API会根据请求中的语言参数动态加载相应模型。

---

## 性能监控与报告

### 性能指标

API自动收集以下性能指标：

- **响应时间**：每个API调用的响应时间
- **内存使用**：模型推理过程中的内存峰值
- **推理速度**：每秒处理的文本/字幕数量
- **并行效率**：并行任务处理的吞吐量
- **错误率**：各类错误的发生频率

### 获取性能报告

使用 `/api/v1/report` 接口获取详细性能报告：

```bash
curl -X GET "http://localhost:8000/api/v1/report?format=html&type=performance"
```

### 资源监控与预警

系统内置资源监控，当以下指标超过阈值时会触发预警：

- 内存使用率超过80%
- 单个任务处理时间超过10分钟
- API错误率超过5%

---

## 高级用例

### 1. 场景：保留关键剧情片段

当您希望在自动剪辑过程中必须保留某些关键片段时：

```json
{
  "video_path": "/data/input/videos/drama.mp4",
  "srt_path": "/data/input/subtitles/drama.srt",
  "preserve_segments": [
    {"start": 320.5, "end": 325.2},  // 保留这段关键对白
    {"start": 450.8, "end": 455.3}   // 保留这段高潮部分
  ]
}
```

### 2. 场景：导演风格剪辑

通过narrative_focus参数引导剪辑风格：

```json
{
  "video_path": "/data/input/videos/drama.mp4",
  "srt_path": "/data/input/subtitles/drama.srt",
  "narrative_focus": ["悬疑", "反转", "人物特写"],
  "temperature": 0.9  // 提高创意度
}
```

### 3. 场景：低配设备适配

在内存受限设备上运行时的优化配置：

```json
{
  "video_path": "/data/input/videos/drama.mp4",
  "srt_path": "/data/input/subtitles/drama.srt",
  "quant_level": "Q2_K",  // 最低内存需求
  "max_duration": 60      // 限制输出时长减少处理量
}
```

---

## 开发者工具

### API客户端

提供多种语言的客户端SDK：

- Python: `pip install visionai-clipmaster-client`
- JavaScript: `npm install visionai-clipmaster-js`

### 示例代码

#### Python示例

```python
from clipmaster_client import ClipMasterAPI

api = ClipMasterAPI("http://localhost:8000")

# 单个视频处理
response = api.generate_clip(
    video_path="/data/video.mp4",
    srt_path="/data/video.srt",
    lang="zh",
    max_duration=120
)

# 查询状态
while response.status == "processing":
    task_status = api.get_status(response.task_id)
    print(f"进度: {task_status.progress * 100:.1f}%")
    time.sleep(5)

print(f"处理完成：{response.video_path}")
```

#### Curl示例

```bash
# 生成剪辑
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "/data/video.mp4",
    "srt_path": "/data/video.srt",
    "lang": "zh"
  }'

# 查询状态
curl -X GET "http://localhost:8000/api/v1/status?task_id=task_20250429_123456"
```

### 命令行工具

```bash
# 安装CLI工具
pip install visionai-clipmaster-cli

# 生成剪辑
clipmaster generate --video /data/video.mp4 --srt /data/video.srt

# 批量处理
clipmaster batch --input-dir /data/videos --parallel 2
```

---

## 备注

- 所有接口均支持详细日志与错误追踪
- 支持批量任务、超时控制、异常恢复
- 详细参数与扩展请参考源码注释与类型提示 
- API文档可通过 `/docs` 端点在线访问（OpenAPI格式） 