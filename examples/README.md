# VisionAI-ClipsMaster 示例工程

本目录包含VisionAI-ClipsMaster的使用示例和开发指南，帮助开发者和用户快速上手短剧混剪系统。

## 目录结构

- `python_example/` - Python SDK调用示例
  - `basic_usage.py` - 基础调用示例
  - `batch_processing.py` - 批量处理示例
  - `advanced_usage.py` - 高级功能示例
  - `training_example.py` - 训练功能示例
  - `test_data/` - 测试数据目录
  - `utils/` - 工具函数

- `postman_collection/` - API测试集合
  - `ClipsMaster_API.postman_collection.json` - Postman测试集合

## 核心功能演示

### 1. 剧本分析与重构

通过 `advanced_usage.py` 演示系统如何分析原始字幕，提取关键情节点，重构为爆款风格剧本。展示了以下核心功能：

- 情感曲线分析
- 剧情关键点识别
- 爆款特征抽取
- 字幕重构与优化

### 2. 模型训练与优化

通过 `training_example.py` 演示如何使用"投喂训练"功能，通过提供原片字幕和爆款字幕对，持续优化模型生成能力：

- 训练样本创建
- 数据增强技术
- 模型微调过程
- 训练效果验证

### 3. 视频剪辑生成

所有示例都演示了从字幕到剪辑的完整流程：

- 字幕解析与处理
- 智能模型选择（中/英文）
- 内存优化策略
- 工程文件导出

## 性能与资源优化

示例中展示了系统的资源优化策略：

- 内存监控与管理
- 模型量化技术
- 分片加载方案
- 不同设备配置适配

## 开始使用

1. 准备测试数据
   ```
   # 将测试视频和字幕放入 python_example/test_data/ 目录
   ```

2. 运行基础示例
   ```
   cd python_example
   python basic_usage.py
   ```

3. 尝试高级功能
   ```
   python advanced_usage.py
   ```

4. 体验训练功能
   ```
   python training_example.py
   ```

## 注意事项

- 默认使用中文模型，英文模型仅保留配置
- 示例中提供了演示模式，即使没有实际视频也可运行
- 完整功能需要在实际系统环境中运行 