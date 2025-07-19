# VisionAI-ClipsMaster SDK

VisionAI-ClipsMaster提供多语言SDK，方便开发者在不同平台上集成短剧混剪功能。

## 可用SDK

本项目提供以下语言的SDK实现：

- **[Python SDK](./python/README.md)** - 适用于Python应用程序
- **[JavaScript SDK](./javascript/README.md)** - 适用于Web应用程序和Node.js
- **[Java SDK](./java/README.md)** - 适用于Java应用程序和Android平台

## 功能概述

所有SDK均提供以下核心功能：

- **短剧混剪生成** - 输入短剧原片和字幕，输出剧情重构的混剪视频
- **模型查询** - 获取可用语言模型和量化级别
- **进度追踪** - 实时跟踪混剪生成进度
- **批量处理** - 支持批量提交多个混剪任务
- **错误处理** - 完善的错误处理和重试机制

## 系统要求

### Python SDK
- Python 3.8+
- 依赖包: requests

### JavaScript SDK
- 浏览器环境: 现代浏览器支持ES6
- Node.js环境: Node.js 14.0+
- 零外部依赖

### Java SDK
- Java 11+
- Maven或Gradle构建工具
- 依赖包: Jackson (JSON处理)

## 快速入门

所有SDK使用相似的API设计，以下是一个通用流程：

1. 创建API客户端实例
2. 提交混剪生成请求
3. 等待任务完成，接收进度回调
4. 获取并处理生成结果

详细用法请参考各SDK的README文档。

## 授权和支持

这些SDK是VisionAI-ClipsMaster项目的一部分，使用专有许可证。

如需技术支持或报告问题，请通过以下方式联系我们：
- Email: support@visionai.example.com
- GitHub: https://github.com/visionai/clipsmaster-sdk/issues

## 许可证

Copyright © 2025 VisionAI. All rights reserved. 