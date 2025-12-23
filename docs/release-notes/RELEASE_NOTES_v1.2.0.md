# 🎬 VisionAI-ClipsMaster v1.2.0 发布说明

> **发布日期**: 2025年12月22日
> **版本类型**: 云端AI集成版
> **构建状态**: Production Ready ✅

## 📋 版本概览

VisionAI-ClipsMaster v1.2.0 是一个重大功能更新版本，引入了**云端AI推理模式**，支持调用云端大模型API进行字幕重构，同时优化了叙事连贯性算法，并提供了便携版打包功能。

## ✨ 主要更新内容

### 🌐 云端AI推理模式（全新功能）

#### 1. 双平台支持
- **硅基流动 (SiliconFlow)**: https://cloud.siliconflow.cn
  - 无需绑定阿里云账号，注册即用
  - 支持Qwen3-235B和DeepSeek-V3.2模型
  
- **魔搭社区 (ModelScope)**: https://modelscope.cn
  - 阿里云生态，需绑定阿里云账号
  - 支持Qwen3-235B-FP8和DeepSeek-V3模型

#### 2. 顶级大模型支持
| 模型 | 参数规模 | 特点 |
|------|----------|------|
| **Qwen3-235B** | 235B (MoE) | 通义千问最新版，中文理解能力强 |
| **DeepSeek-V3.2** | 671B (MoE) | DeepSeek最新版，推理能力出色 |

#### 3. 混合推理架构
- **本地模式**: 使用本地GGUF模型，无需网络，隐私安全
- **云端模式**: 调用云端API，无需GPU，效果更好
- **无缝切换**: 一键切换推理模式，配置自动保存

#### 4. 云端配置管理
- API密钥安全存储
- 连接测试功能
- 配置持久化（`configs/cloud_api_config.json`）

### 🧠 叙事连贯性优化

#### 1. 10大智能策略
在云端模式中实现了叙事连贯性优化算法：

1. **场景完整性检测**: 确保场景开头和结尾都被包含
2. **因果关系补充**: "起因"和"结果"成对出现
3. **问答完整性**: 问句必须配回答
4. **指代消解**: 确保指代词有明确的指代对象
5. **情感反应补充**: 情感反应需要前文触发事件
6. **转折词处理**: 转折内容需要前文对比
7. **递进词处理**: 递进内容需要前文基础
8. **小间隙填补**: 智能填补2-4条的对话间隙
9. **半句话检测**: 避免以连接词开头的孤立对话
10. **场景分组**: 基于时间间隙识别场景边界

#### 2. 保留比例调整
- 关键对白保留比例默认为**75%**（可通过配置调整）
- 配置位置: `configs/narrative_config.yaml`
- 参数: `key_dialogue_extraction.retention_ratio`

### 📦 便携版打包功能

#### 1. PyInstaller打包配置
- 新增 `visionai_portable.spec` 打包规范文件
- 新增 `build_portable.py` 安全打包脚本
- 支持一键生成完全自包含的便携版

#### 2. 便携版特性
- ✅ 包含Python解释器和所有依赖
- ✅ 包含FFmpeg视频处理工具
- ✅ 包含配置文件和资源
- ✅ 双击即可运行，无需安装
- ✅ 删除文件夹即可完全卸载

### 🧹 项目清理优化

#### 1. 删除的冗余内容
- 临时日志文件 (`logs/`)
- 测试输出文件 (`output/`)
- 临时报告 (`reports/`)
- SDK示例 (`sdk/`)
- IDE历史 (`.history/`)
- 构建缓存 (`build/`, `node_modules/`)

#### 2. 精简的组件
- `llama.cpp`: 仅保留转换脚本和gguf-py
- `tools/ffmpeg`: 删除ffplay和文档，仅保留核心工具

#### 3. 项目体积
- 清理前: ~1GB+
- 清理后: ~216MB（不含.venv和.git）

---

## 🔧 技术实现

### 新增文件
```
src/core/cloud_ai_engine.py      # 云端AI推理引擎
src/config/cloud_api_config.py   # 云端API配置管理
configs/cloud_api_config.json    # 云端配置存储（运行时生成）
visionai_portable.spec           # PyInstaller打包规范
build_portable.py                # 便携版打包脚本
```

### 修改文件
```
simple_ui_fixed.py               # 添加云端模式UI控件
src/core/real_ai_engine.py       # 同步叙事连贯性优化
configs/narrative_config.yaml    # 调整保留比例参数
requirements.txt                 # 补全依赖清单
```

---

## 📋 依赖更新

### 新增依赖
```
pandas>=2.0.0          # 数据处理
networkx>=3.0          # 图形分析
tabulate>=0.9.0        # 表格格式化
aiofiles>=23.0.0       # 异步文件操作
chardet>=5.0.0         # 字符编码检测
lxml>=4.9.0            # XML处理
watchdog>=3.0.0        # 文件监控
langdetect>=1.0.9      # 语言检测
sentencepiece>=0.1.99  # 分词器
loguru>=0.7.0          # 高级日志
gguf>=0.6.0            # GGUF格式支持
```

---

## 🚀 升级指南

### 从v1.1.0升级

1. **更新代码**
   ```bash
   git pull origin main
   ```

2. **安装新依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置云端API（可选）**
   - 启动程序后，在AI模式下拉框选择"云端模式"
   - 选择平台和模型
   - 填写API密钥
   - 点击"测试连接"验证

### 获取API密钥

#### 硅基流动（推荐）
1. 访问 https://cloud.siliconflow.cn
2. 注册账号（无需绑定其他账号）
3. 进入控制台 → API密钥 → 创建密钥

#### 魔搭社区
1. 访问 https://modelscope.cn
2. 注册账号并绑定阿里云账号
3. 进入个人中心 → API Token → 创建Token

---

## ⚠️ 已知问题

1. **魔搭社区API限制**: 需要绑定阿里云账号才能使用，否则会返回401错误
2. **云端模式网络依赖**: 云端模式需要稳定的网络连接
3. **API调用限制**: 各平台有不同的调用频率限制，请参考平台文档

---

## 🙏 致谢

感谢以下平台提供的API支持：
- 硅基流动 (SiliconFlow)
- 魔搭社区 (ModelScope)
- 通义千问团队 (Qwen)
- DeepSeek团队

---

## 📝 完整更新日志

```
v1.2.0 (2025-12-22)
├── 新增: 云端AI推理模式
│   ├── 硅基流动平台支持
│   ├── 魔搭社区平台支持
│   ├── Qwen3-235B模型支持
│   ├── DeepSeek-V3.2模型支持
│   ├── 本地/云端模式切换
│   └── API配置持久化
├── 优化: 叙事连贯性算法
│   ├── 10大智能策略
│   ├── 保留比例默认75%（可配置）
│   └── 云端模式专属优化
├── 新增: 便携版打包功能
│   ├── PyInstaller配置
│   └── 安全打包脚本
├── 优化: 项目清理
│   ├── 删除冗余文件
│   ├── 精简llama.cpp
│   └── 体积从1GB+降至216MB
└── 修复: 依赖清单补全
```
