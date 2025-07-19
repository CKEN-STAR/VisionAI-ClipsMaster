# VisionAI-ClipsMaster Java SDK

适用于VisionAI-ClipsMaster API的Java客户端SDK，可轻松集成到任何Java项目中。

## 功能特点

- 完整支持VisionAI-ClipsMaster的所有API功能
- 同步和异步调用方式
- 自动重试和错误处理机制
- 进度追踪回调
- 批量处理支持
- 支持Java 11及以上版本
- 流式Builder API设计

## 安装

### Maven

```xml
<dependency>
    <groupId>com.visionai</groupId>
    <artifactId>clipsmaster-sdk</artifactId>
    <version>1.0.0</version>
</dependency>
```

### Gradle

```groovy
implementation 'com.visionai:clipsmaster-sdk:1.0.0'
```

## 快速入门

### 基本用法

```java
import com.visionai.clipsmaster.ClipsMasterClient;
import java.util.Map;
import java.util.Arrays;

public class ClipsMasterExample {
    public static void main(String[] args) {
        try {
            // 使用Builder模式创建客户端
            ClipsMasterClient client = new ClipsMasterClient.Builder("your_api_key_here")
                .baseUrl("http://localhost:8000")
                .timeout(30)            // 超时时间(秒)
                .maxRetries(3)          // 最大重试次数
                .enableLogging(true)    // 启用日志
                .build();
            
            // 检查模型状态
            Map<String, Object> modelStatus = client.getModelsStatus();
            System.out.println("模型状态: " + modelStatus);
            
            // 定义进度回调
            ClipsMasterClient.ProgressCallback progressCallback = (progress, message) -> {
                System.out.printf("进度: %.1f%% - %s%n", progress * 100, message);
            };
            
            // 生成视频剪辑并等待完成
            Map<String, Object> result = client.generateClipSync(
                "/path/to/video.mp4",    // 视频文件路径
                "/path/to/subtitle.srt", // 字幕文件路径
                "zh",                    // 使用中文模型
                "Q4_K_M",                // 平衡的量化等级
                "both",                  // 同时导出视频和工程文件
                180.0,                   // 限制最大输出时长为3分钟
                Arrays.asList("感人", "温馨"), // 叙事重点关键词
                0.7,                     // 生成温度
                null,                    // 无必须保留的片段
                2,                       // 轮询间隔(秒)
                3600,                    // 超时时间(秒)
                progressCallback         // 进度回调函数
            );
            
            System.out.println("剪辑完成!");
            System.out.println("项目文件: " + result.get("project_path"));
            System.out.println("视频文件: " + result.get("video_path"));
            
        } catch (ClipsMasterClient.APIError e) {
            System.err.printf("API错误 (%d): %s [endpoint: %s]%n", 
                e.getStatusCode(), e.getMessage(), e.getEndpoint());
        } catch (Exception e) {
            System.err.println("处理出错: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```

### 异步调用

```java
import java.util.concurrent.CompletableFuture;

// 异步创建剪辑任务
CompletableFuture<Map<String, Object>> future = client.generateClipAsync(
    "/path/to/video.mp4",
    "/path/to/subtitle.srt",
    "zh",
    "Q4_K_M",
    "both",
    180.0,
    Arrays.asList("感人", "温馨"),
    0.7,
    null
);

// 添加完成回调
future.thenAccept(taskResponse -> {
    String taskId = (String) taskResponse.get("task_id");
    System.out.println("任务已创建: " + taskId);
    
    // 获取任务状态...
}).exceptionally(throwable -> {
    System.err.println("处理失败: " + throwable.getMessage());
    return null;
});

// 等待任务完成
Map<String, Object> taskResponse = future.join();
```

### 简化调用

```java
// 使用默认参数的简化方法
Map<String, Object> result = client.generateClipSync(
    "/path/to/video.mp4",
    "/path/to/subtitle.srt",
    progressCallback
);
```

## 错误处理

SDK会抛出`APIError`类型的异常，包含以下属性：

- `statusCode` - HTTP状态码
- `message` - 错误描述
- `endpoint` - 请求的API端点

```java
try {
    Map<String, Object> result = client.generateClip(...);
} catch (ClipsMasterClient.APIError e) {
    System.err.printf("API错误 (%d): %s [endpoint: %s]%n", 
        e.getStatusCode(), e.getMessage(), e.getEndpoint());
} catch (Exception e) {
    System.err.println("其他错误: " + e.getMessage());
}
```

## 完整文档

更多详细用法请参考[API文档](https://visionai.example.com/docs/sdk/java/)。

## 依赖项

- Java 11+
- Jackson (JSON处理)
- Java HTTP Client (JDK 11内置)

## 许可证

Copyright © 2025 VisionAI. All rights reserved. 