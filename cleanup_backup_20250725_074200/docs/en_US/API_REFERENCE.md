# VisionAI-ClipsMaster Developer API Documentation

## Table of Contents
1. [API Overview](#api-overview)
2. [Data Structures](#data-structures)
3. [API Definitions](#api-definitions)
4. [Error Codes](#error-codes)
5. [Multilingual & Model Configuration](#multilingual--model-configuration)
6. [Performance Monitoring & Reports](#performance-monitoring--reports)
7. [Advanced Use Cases](#advanced-use-cases)
8. [Developer Tools](#developer-tools)

---

## API Overview

| Path                   | Method | Description        | Notes                   |
|------------------------|--------|--------------------|-------------------------|
| /api/v1/generate       | POST   | Generate video clip| Single video processing |
| /api/v1/batch          | POST   | Batch process videos | Process multiple videos in one request |
| /api/v1/status         | GET    | Query task status  | Get progress and results |
| /api/v1/report         | GET    | Get test report    | Performance and quality reports |
| /api/v1/models         | GET    | Get model status   | Query available models and status |
| /api/v1/monitoring/metrics | GET | Get API performance metrics | Monitor system performance |

---

## Data Structures

### Enum Types

#### QuantizationLevel

```python
class QuantizationLevel(str, Enum):
    """Quantization level enum"""
    Q2_K = "Q2_K"      # Lowest memory usage (~2GB), lower quality
    Q4_K_M = "Q4_K_M"  # Balanced memory usage (~4GB) and quality
    Q5_K_M = "Q5_K_M"  # Higher quality, memory usage ~5GB
    Q8_0 = "Q8_0"      # Highest quality, maximum memory usage (~7GB)
```

#### Language

```python
class Language(str, Enum):
    """Supported languages enum"""
    CHINESE = "zh"
    ENGLISH = "en"
```

#### ExportFormat

```python
class ExportFormat(str, Enum):
    """Export format enum"""
    VIDEO = "video"      # Video file only
    PROJECT = "project"  # Project file only 
    BOTH = "both"        # Both video and project files
```

#### TaskStatus

```python
class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
```

### Request and Response Structures

#### ClipRequest

```python
class ClipRequest(BaseModel):
    """Video clip generation request body"""
    video_path: str                # Video file path, supports relative or absolute path
    srt_path: str                  # Subtitle file path, supports SRT or ASS formats
    quant_level: QuantizationLevel = QuantizationLevel.Q4_K_M  # Quantization level
    lang: Language = Language.CHINESE                          # Processing language
    export_format: ExportFormat = ExportFormat.BOTH            # Export format
    max_duration: Optional[float] = None   # Max output duration (seconds), None means no limit
    narrative_focus: Optional[List[str]] = None  # Narrative focus keywords list
    temperature: float = 0.7       # Generation temperature, controls creativity (0.1-1.0)
    preserve_segments: Optional[List[Dict[str, float]]] = None  # Time segments that must be preserved
```

#### ClipResponse

```python
class ClipResponse(BaseModel):
    """Video clip generation response body"""
    task_id: str         # Task ID, can be used for subsequent status queries
    project_path: Optional[str] = None  # Generated project file path
    video_path: Optional[str] = None    # Generated video file path
    render_time: float   # Rendering time (seconds)
    status: TaskStatus   # Task status
    progress: Optional[float] = None  # Processing progress (0-1), only applicable for processing status
    message: Optional[str] = None     # Detailed information or error description
    metrics: Optional[Dict[str, Any]] = None  # Performance and quality metrics
```

#### BatchClipRequest

```python
class BatchClipRequest(BaseModel):
    """Batch video clip request"""
    clips: List[ClipRequest]  # List of clip requests
    parallel: int = 1         # Number of parallel processes, default is 1
```

#### BatchClipResponse

```python
class BatchClipResponse(BaseModel):
    """Batch video clip response"""
    batch_id: str        # Batch ID
    task_ids: List[str]  # List of task IDs
    status: TaskStatus   # Overall batch status
    completed: int = 0   # Number of completed tasks
    total: int           # Total number of tasks
    message: Optional[str] = None  # Detailed information
```

---

## API Definitions

### 1. Generate Video Clip

**POST** `/api/v1/generate`

Generate a clip for a single video, supporting rich editing parameters.

- **Content-Type**: application/json
- **Request Body**: `ClipRequest`
- **Response Body**: `ClipResponse`

**Request Example**:

```json
{
  "video_path": "/data/input/videos/drama_ep1.mp4",
  "srt_path": "/data/input/subtitles/drama_ep1.srt",
  "quant_level": "Q4_K_M",
  "lang": "en",
  "export_format": "both",
  "max_duration": 180,
  "narrative_focus": ["emotional", "conflict", "climax"],
  "temperature": 0.8,
  "preserve_segments": [
    {"start": 320.5, "end": 325.2},
    {"start": 450.8, "end": 455.3}
  ]
}
```

**Response Example**:

```json
{
  "task_id": "task_20250429_123456",
  "project_path": "/data/output/edit_projects/drama_ep1_remix.fcpxml",
  "video_path": "/data/output/final_videos/drama_ep1_remix.mp4",
  "render_time": 42.7,
  "status": "success",
  "message": "Clip generated successfully",
  "metrics": {
    "input_duration": 1245.6,
    "output_duration": 175.3,
    "compression_ratio": 0.141,
    "memory_peak_mb": 3524
  }
}
```

### 2. Batch Process Videos

**POST** `/api/v1/batch`

Submit multiple video clip tasks in one request, with automatic scheduling and parallel processing.

- **Content-Type**: application/json
- **Request Body**: `BatchClipRequest`
- **Response Body**: `BatchClipResponse`

**Request Example**:

```json
{
  "clips": [
    {
      "video_path": "/data/input/videos/drama_ep1.mp4",
      "srt_path": "/data/input/subtitles/drama_ep1.srt",
      "lang": "en"
    },
    {
      "video_path": "/data/input/videos/drama_ep2.mp4",
      "srt_path": "/data/input/subtitles/drama_ep2.srt",
      "lang": "en"
    }
  ],
  "parallel": 2
}
```

**Response Example**:

```json
{
  "batch_id": "batch_20250429_123456",
  "task_ids": ["task_20250429_123456", "task_20250429_123457"],
  "status": "processing",
  "completed": 0,
  "total": 2,
  "message": "Batch task submitted, processing"
}
```

### 3. Query Task Status

**GET** `/api/v1/status?task_id=task_20250429_123456`

Query the processing status and progress of a single task, including processing, success, or failure status, and detailed metrics.

- **Response Body**:
  ```json
  {
    "task_id": "task_20250429_123456",
    "status": "processing",
    "progress": 0.85,
    "message": "Processing: Rendering final video",
    "metrics": {
      "memory_usage_mb": 3245,
      "elapsed_time": 38.5
    }
  }
  ```

### 4. Get Test Report

**GET** `/api/v1/report?format=html`

Get system performance and test reports, supporting multiple formats.

- **Request Parameters**:
  - `format`: Report format, options: `html`, `json`, `md`
  - `type`: Report type, options: `performance`, `quality`, `all`

- **Response Example**:
  ```json
  {
    "report_url": "/reports/performance_20250429_123456.html",
    "generated_time": "2025-04-29T12:34:56",
    "summary": {
      "overall_status": "healthy",
      "avg_response_time": 245.6,
      "success_rate": 0.992,
      "memory_usage": "3.2GB/4.0GB"
    }
  }
  ```

### 5. API Performance Monitoring

**GET** `/api/v1/monitoring/metrics`

Get API performance monitoring metrics, including response time, success rate, resource usage, etc.

- **Request Parameters**:
  - `time_window`: Optional, time window (minutes), if provided, only return statistics within this time window

- **Response Example**:
  ```json
  {
    "timestamp": "2025-04-29T12:34:56",
    "uptime": 86400.5,
    "endpoints": {
      "POST:/api/v1/generate": {
        "requests": {
          "total": 1250,
          "success": 1245,
          "error": 5,
          "success_rate": 0.996
        },
        "latency": {
          "avg": 2456.3,
          "min": 345.2,
          "max": 12500.8,
          "p95": 4500.2
        }
      }
    },
    "system": {
      "memory": {
        "current": 3245000000,
        "peak": 3856000000,
        "average": 2845000000
      },
      "cpu": {
        "current": 45.6,
        "peak": 92.3,
        "average": 38.5
      }
    }
  }
  ```

---

## Error Codes

| Code     | Message              | Description           | Recommended Action     |
|----------|----------------------|-----------------------|------------------------|
| 0        | success              | Success               | No action needed       |
| 1001     | invalid input        | Invalid input parameter | Check parameter format and value range |
| 1002     | file not found       | File not found        | Check if file path is correct |
| 1003     | model not available  | Model not available   | Download or set correct model path |
| 1004     | unsupported format   | Unsupported format    | Use supported file format |
| 2001     | internal error       | Internal server error | Contact tech support and provide logs |
| 2002     | memory limit exceeded| Memory limit exceeded | Lower quantization level or process in batches |
| 3001     | task timeout         | Task timeout          | Check input file size or adjust timeout parameter |
| 3002     | rendering failed     | Rendering failed      | Check video codec compatibility |

---

## Multilingual & Model Configuration

The system supports both Chinese and English language models, with flexible switching through configuration files and API parameters. Details:

### Chinese Model (Default)
- **Status**: Integrated by default, no additional operation needed
- **Path**: `models/qwen/quantized/qwen2.5-7b-zh.gguf`
- **Quantization Level**: Default Q4_K_M, can be modified in config file
- **Memory Requirement**: ~4GB (depends on quantization level)

### English Model (Optional)
- **Status**: Configuration only, needs to be downloaded for first use
- **Path**: `models/mistral/quantized/mistral-7b-en.gguf`
- **Quantization Level**: Default Q4_K_M, can be modified in config file
- **Memory Requirement**: ~4GB (depends on quantization level)
- **Special Note**: After downloading the model to the specified path, it will be automatically recognized and effective without restarting the service

### Language Switching Methods
1. **API Request Parameter**: Set `lang: "zh"` or `lang: "en"` in the request body
2. **Configuration File**: Modify the default language in `configs/models/active_model.yaml`
3. **Command Line Parameter**: Use `--lang zh` or `--lang en` to start the service

### Language Detection and Fallback
If English processing is requested but the English model is not downloaded, the system will return error code 1003 (model not available) rather than automatically falling back to the Chinese model, to ensure language processing quality.

---

## Performance Monitoring & Reports

The system has built-in complete API performance monitoring and reporting functions, focusing on the following metrics:

### Monitoring Metrics
1. **Request Success Rate**: Track API request success/failure ratio
2. **Average Response Time**: Record response time statistics for each endpoint
3. **Resource Usage Peak**: Monitor memory and CPU usage during API calls
4. **Model Inference Performance**: Track model loading and inference time

### Monitoring Methods
- **Real-time Monitoring**: Get real-time performance data through the `/api/v1/monitoring/metrics` endpoint
- **Historical Reports**: Get historical performance reports through the `/api/v1/report` endpoint
- **Log Files**: Automatically recorded to log files in the `logs/` directory

### Monitoring Configuration
The performance monitoring system configuration is located in the `configs/monitoring.json` file, with customizable parameters including:
- Monitoring sampling frequency
- Performance warning and critical thresholds
- Report retention time
- Integration with external data sources like InfluxDB (optional)

For low-configuration devices, the monitoring system will automatically adjust sampling frequency and storage strategies to reduce resource usage.

---

## Advanced Use Cases

### 1. Custom Clip Style
By adjusting the `narrative_focus` and `temperature` in request parameters, you can control the style and creativity of the generated content. For example, setting `narrative_focus: ["humorous", "contrast"]` can make the system focus more on humor and contrast elements.

### 2. Enhanced Batch Processing
For large-scale video processing needs, you can set more advanced batch processing parameters:

```json
{
  "clips": [...],
  "parallel": 2,
  "priority": "high",
  "notification_url": "https://example.com/webhook",
  "error_policy": "continue"
}
```

This allows setting task priority, completion notification, and error handling policy.

### 3. Performance Optimization with Monitoring API
When processing large videos or batch tasks, you can monitor system resource usage in real-time and dynamically adjust request strategies based on monitoring data. For example, when memory usage is observed to be approaching the threshold, reduce the number of parallel processes.

---

## Developer Tools

### 1. API Benchmark Tool
The system provides a benchmark tool for evaluating API performance and stability:

```bash
python tools/api_benchmark.py --endpoint /api/v1/generate --method POST --payload sample_payload.json --concurrency 10 --requests 100
```

Test results include response time distribution, success rate, throughput, and other metrics, output in HTML and JSON formats.

### 2. Log Analysis Tool
The log analysis tool located at `tools/log_analyzer.py` can extract valuable information from log files, such as error patterns, performance bottlenecks, etc.

### 3. Automated Test Suite
The system has a built-in complete automated test suite, covering unit tests, integration tests, and end-to-end tests. Developers can run these tests to verify API compatibility and functional correctness:

```bash
python -m pytest tests/
```

### 4. Developer Sandbox
The developer sandbox provides a safe environment for trying API calls and model parameter tuning, without affecting the production environment:

```bash
python tools/dev_sandbox.py
```

This will start an interactive environment, supporting rapid prototyping and debugging. 