# VisionAI-ClipsMaster Python SDK

适用于VisionAI-ClipsMaster API的Python客户端SDK，可轻松集成到任何Python应用程序中。

## 功能特点

- 完整支持VisionAI-ClipsMaster的所有API功能
- 同步和异步调用方式
- 强大的错误处理和自动重试机制
- 内置进度追踪回调
- 支持批量处理任务
- 全面的中英文双模型支持
- 支持Python 3.8及以上版本

## 安装

```bash
pip install clipsmaster-sdk
```

或从源码安装：

```bash
git clone https://github.com/your-username/clipsmaster-sdk.git
cd clipsmaster-sdk/python
pip install -e .
```

## 快速入门

### 基本用法

```python
from clipsmaster_sdk import ClipsMasterClient

# 创建客户端实例
client = ClipsMasterClient(
    api_key="your_api_key_here",
    base_url="http://localhost:8000"  # 默认为localhost:8000
)

# 检查模型状态
model_status = client.get_models_status()
print("模型状态:", model_status)

# 定义进度回调函数（可选）
def on_progress(progress, message):
    print(f"进度: {progress*100:.1f}% - {message}")

# 同步方式生成视频剪辑
result = client.generate_clip_sync(
    video_path="examples/video.mp4",
    srt_path="examples/subtitle.srt",
    lang="zh",  # 使用中文模型
    quant_level="Q4_K_M",  # 平衡的量化等级
    max_duration=180,  # 限制最大输出时长为3分钟
    narrative_focus=["感人", "温馨"],  # 叙事重点关键词
    progress_callback=on_progress  # 进度回调函数
)

print("剪辑完成!")
print(f"项目文件: {result.get('project_path')}")
print(f"视频文件: {result.get('video_path')}")
```

### 异步方式使用

```python
# 创建剪辑任务
task_response = client.generate_clip(
    video_path="examples/video.mp4",
    srt_path="examples/subtitle.srt",
    lang="zh"
)

task_id = task_response.get("task_id")
print(f"任务已创建: {task_id}")

# 稍后检查任务状态
status = client.get_task_status(task_id)
print(f"任务状态: {status.get('status')}")
print(f"进度: {status.get('progress', 0)*100:.1f}%")

# 等待任务完成
result = client.wait_for_task(
    task_id=task_id,
    progress_callback=on_progress
)
```

### 批量处理

```python
from clipsmaster_sdk import ClipRequest

# 创建多个剪辑请求
requests = [
    ClipRequest(
        video_path="examples/video1.mp4",
        srt_path="examples/subtitle1.srt",
        lang="zh"
    ),
    ClipRequest(
        video_path="examples/video2.mp4",
        srt_path="examples/subtitle2.srt",
        lang="zh"
    )
]

# 批量提交任务，最多2个并行处理
batch_response = client.batch_generate(
    clip_requests=requests,
    parallel=2
)

batch_id = batch_response.get("batch_id")
print(f"批量任务已创建: {batch_id}")

# 定义批量进度回调
def on_batch_progress(completed, total, message):
    print(f"批量处理进度: {completed}/{total} - {message}")

# 等待批量任务完成
result = client.wait_for_batch(
    batch_id=batch_id,
    progress_callback=on_batch_progress
)
```

## 完整文档

更多详细用法请参考[API文档](https://visionai.example.com/docs/sdk/python/)。

## 许可证

Copyright © 2025 VisionAI. All rights reserved. 