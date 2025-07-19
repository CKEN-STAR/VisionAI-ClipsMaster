# VisionAI-ClipsMaster JavaScript SDK

适用于VisionAI-ClipsMaster API的JavaScript客户端SDK，支持在浏览器和Node.js环境中使用。

## 功能特点

- 完整支持VisionAI-ClipsMaster的所有API功能
- 基于Promise的现代化异步接口
- 内置错误处理和自动重试机制
- 进度跟踪回调
- 批量处理支持
- 支持浏览器和Node.js环境
- 零依赖，轻量级实现

## 安装

### NPM

```bash
npm install clipsmaster-sdk
```

### 浏览器直接引用

```html
<script src="https://cdn.jsdelivr.net/npm/clipsmaster-sdk@1.0.0/dist/clipsmaster-sdk.min.js"></script>
```

## 快速入门

### Node.js环境

```javascript
const { ClipsMasterClient } = require('clipsmaster-sdk');

// 创建客户端实例
const client = new ClipsMasterClient({
  apiKey: 'your_api_key_here',
  baseUrl: 'http://localhost:8000', // 默认值
  enableLogging: true  // 启用日志
});

// 定义进度回调函数
const onProgress = (progress, message) => {
  console.log(`进度: ${progress*100}% - ${message}`);
};

// 异步使用
async function generateClip() {
  try {
    // 检查模型状态
    const modelStatus = await client.getModelsStatus();
    console.log('模型状态:', modelStatus);
    
    // 生成视频剪辑并等待完成
    const result = await client.generateClipSync({
      videoPath: '/path/to/video.mp4',
      srtPath: '/path/to/subtitle.srt',
      lang: 'zh', // 使用中文模型
      maxDuration: 180, // 限制最大输出时长为3分钟
      narrativeFocus: ['感人', '温馨'], // 叙事重点关键词
      progressCallback: onProgress // 进度回调
    });
    
    console.log('剪辑完成!');
    console.log(`项目文件: ${result.project_path}`);
    console.log(`视频文件: ${result.video_path}`);
  } catch (error) {
    console.error('处理出错:', error.message);
  }
}

generateClip();
```

### 浏览器环境

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/clipsmaster-sdk@1.0.0/dist/clipsmaster-sdk.min.js"></script>
</head>
<body>
  <div id="progress">0%</div>
  <script>
    // 获取SDK对象
    const { ClipsMasterClient } = window.ClipsMaster;
    
    // 创建客户端实例
    const client = new ClipsMasterClient({
      apiKey: 'your_api_key_here',
      baseUrl: 'http://localhost:8000'
    });
    
    // 定义进度回调
    function updateProgress(progress, message) {
      document.getElementById('progress').textContent = 
        `${Math.floor(progress*100)}% - ${message}`;
    }
    
    // 获取模型状态
    client.getModelsStatus()
      .then(status => {
        console.log('模型状态:', status);
      })
      .catch(error => {
        console.error('获取模型状态失败:', error);
      });
    
    // 创建任务
    async function startTask() {
      try {
        const result = await client.generateClipSync({
          videoPath: document.getElementById('videoPath').value,
          srtPath: document.getElementById('srtPath').value,
          progressCallback: updateProgress
        });
        
        alert('任务完成!');
        console.log(result);
      } catch (error) {
        alert(`处理失败: ${error.message}`);
      }
    }
  </script>
</body>
</html>
```

## API 参考

### 创建客户端

```javascript
const client = new ClipsMasterClient({
  apiKey: 'your_api_key',        // 必须
  baseUrl: 'http://api.example', // 可选，默认http://localhost:8000
  timeout: 30000,                // 可选，超时时间(毫秒)，默认30秒
  maxRetries: 3,                 // 可选，最大重试次数，默认3次
  retryDelay: 2000,              // 可选，重试延迟(毫秒)，默认2秒
  enableLogging: false           // 可选，是否启用日志，默认false
});
```

### 主要方法

- `getModelsStatus()` - 获取模型状态
- `generateClip(options)` - 创建视频剪辑任务
- `getTaskStatus(taskId)` - 获取任务状态
- `cancelTask(taskId)` - 取消任务
- `batchGenerate(options)` - 批量创建视频剪辑任务
- `getBatchStatus(batchId)` - 获取批量任务状态
- `waitForTask(options)` - 等待任务完成
- `waitForBatch(options)` - 等待批量任务完成
- `generateClipSync(options)` - 创建视频剪辑任务并同步等待完成

## 错误处理

SDK会抛出`APIError`类型的错误，包含以下属性：

- `statusCode` - HTTP状态码
- `message` - 错误描述
- `endpoint` - 请求的API端点

```javascript
try {
  await client.generateClip({...});
} catch (error) {
  if (error.name === 'APIError') {
    console.error(`API错误 (${error.statusCode}): ${error.message}`);
  } else {
    console.error(`其他错误: ${error.message}`);
  }
}
```

## 完整文档

更多详细用法请参考[API文档](https://visionai.example.com/docs/sdk/javascript/)。

## 许可证

Copyright © 2025 VisionAI. All rights reserved. 