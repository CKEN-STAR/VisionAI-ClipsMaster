# VisionAI-ClipsMaster 训练模块使用指南

## 📖 概述

VisionAI-ClipsMaster训练模块是一个专为短剧混剪设计的AI训练系统，支持双模型独立训练（英文Mistral-7B + 中文Qwen2.5-7B），具备完整的剧本重构能力和4GB内存设备兼容性。

## 🎯 核心功能

### 1. 双模型独立训练
- **英文模型**: Mistral-7B，专门处理英文剧本重构
- **中文模型**: Qwen2.5-7B，专门处理中文剧本重构
- **独立性**: 两个模型完全分离，互不干扰

### 2. 剧本重构训练
- **原片-爆款配对学习**: 学习从原始字幕到爆款字幕的转换模式
- **叙事结构优化**: 自动提取高潮点和关键情节
- **时间轴精准映射**: 保持≤0.5秒的时间精度

### 3. 内存优化
- **4GB设备兼容**: 峰值内存≤3.8GB
- **Q2_K量化**: 默认使用最优量化策略
- **动态内存管理**: 自动监控和释放内存

## 🚀 快速开始

### 1. 环境准备

```bash
# 使用系统Python解释器
C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe

# 安装依赖
pip install psutil torch transformers
```

### 2. 基础使用

```python
from training.en_trainer import EnTrainer
from training.zh_trainer import ZhTrainer

# 英文训练器
en_trainer = EnTrainer()

# 中文训练器  
zh_trainer = ZhTrainer()

# 执行训练
def progress_callback(progress, step):
    print(f"进度: {progress:.1%} - {step}")
    return True  # 继续训练

result = en_trainer.train(progress_callback)
print(f"训练结果: {result}")
```

### 3. UI界面训练

```python
from ui.training_panel import TrainingPanel
from PyQt6.QtWidgets import QApplication

app = QApplication([])
panel = TrainingPanel()
panel.show()
app.exec()
```

## 📊 训练数据格式

### 原片-爆款字幕配对

```json
{
  "original_subtitles": [
    {"start": 0, "end": 3, "text": "这是原始剧情的详细描述"},
    {"start": 3, "end": 6, "text": "包含了复杂的情节发展"}
  ],
  "viral_subtitles": [
    {"start": 0, "end": 2, "text": "震惊！真相大白"},
    {"start": 2, "end": 4, "text": "接下来让人意想不到"}
  ],
  "metadata": {
    "source": "drama_series_01",
    "quality": "high",
    "language": "zh"
  }
}
```

### 数据目录结构

```
data/training/
├── en/                     # 英文训练数据
│   ├── hit_subtitles/      # 爆款字幕
│   ├── raw_pairs/          # 原始配对数据
│   └── augmented_data/     # 增强数据
└── zh/                     # 中文训练数据
    ├── hit_subtitles/      # 爆款字幕
    ├── raw_pairs/          # 原始配对数据
    └── augmented_data/     # 增强数据
```

## ⚙️ 配置说明

### 模型配置 (configs/model_config.yaml)

```yaml
# 4GB内存优化配置
models:
  mistral-7b-en:
    quantization_level: "Q2_K"
    memory_requirement: 2800  # MB
  qwen2.5-7b-zh:
    quantization_level: "Q2_K"
    memory_requirement: 2800  # MB

# 内存限制
memory_limits:
  max_total_memory: 3800  # MB
  emergency_threshold: 3600  # MB
```

### 训练参数

```yaml
training:
  batch_size: 4
  learning_rate: 1e-5
  max_epochs: 10
  validation_split: 0.2
```

## 🔧 高级功能

### 1. 断点续训

训练过程支持自动断点保存和恢复：

```python
# 训练会自动保存断点到 checkpoints/ 目录
# 重新启动训练时会自动从断点恢复
result = trainer.train(progress_callback)
```

### 2. 内存监控

```python
# 获取实时内存使用情况
memory_info = trainer.get_memory_usage()
print(f"系统内存: {memory_info['system_total_gb']:.1f} GB")
print(f"进程内存: {memory_info['process_rss_mb']:.1f} MB")
```

### 3. 异常处理

训练器具备完整的异常处理机制：

- **步骤级重试**: 单个步骤失败时自动重试3次
- **内存保护**: 内存使用率>90%时自动停止
- **断点保存**: 异常时自动保存进度

### 4. 数据增强

```python
from training.data_augment import DataAugmenter

augmenter = DataAugmenter()

# 中文文本增强
zh_texts = augmenter.augment_text("原始文本", "zh")

# 英文文本增强
en_texts = augmenter.augment_text("Original text", "en")
```

## 📈 性能优化

### 1. 内存优化策略

- **Q2_K量化**: 将7B模型压缩到2.8GB
- **动态卸载**: 非活跃模型自动卸载
- **批处理优化**: 小批量处理减少内存峰值

### 2. 设备选择策略

```python
from utils.device_manager import HybridDevice

device_manager = HybridDevice()

# 自动选择最佳设备
device = device_manager.select_device(model_size=2.8*1024**3)
print(f"选择设备: {device}")
```

### 3. 训练加速

- **CPU优化**: 支持AVX2指令集加速
- **多线程**: 自动检测CPU核心数
- **内存映射**: 减少内存拷贝开销

## 🐛 故障排除

### 常见问题

1. **内存不足**
   ```
   错误: Memory usage too high
   解决: 检查系统内存，关闭其他程序
   ```

2. **模型加载失败**
   ```
   错误: Model loading failed
   解决: 检查模型文件路径和权限
   ```

3. **训练中断**
   ```
   解决: 重新启动训练，会自动从断点恢复
   ```

### 日志分析

训练日志保存在 `logs/` 目录：

```bash
# 查看最新日志
tail -f logs/training.log

# 搜索错误信息
grep "ERROR" logs/training.log
```

## 📚 API参考

### EnTrainer / ZhTrainer

```python
class EnTrainer:
    def __init__(self, model_path: Optional[str] = None)
    def load_training_data(self, data_path: str) -> bool
    def train(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]
    def save_model(self, save_path: str) -> bool
    def load_model(self, model_path: str) -> bool
    def get_memory_usage(self) -> Dict[str, Any]
```

### TrainingPanel

```python
class TrainingPanel(QWidget):
    def start_training(self)
    def stop_training(self)
    def update_progress(self, progress: float, step: str)
    def training_completed(self, result: Dict[str, Any])
    def training_error(self, error_msg: str)
```

## 🔄 更新日志

### v1.1.0 (2025-07-12)
- ✅ 添加Q2_K默认量化配置
- ✅ 增强异常处理和断点续训
- ✅ 完善内存监控功能
- ✅ 优化GPU检测接口

### v1.0.0 (2025-07-11)
- ✅ 双模型独立训练系统
- ✅ 4GB内存设备兼容
- ✅ UI训练面板集成
- ✅ 剧本重构核心功能

## 📞 技术支持

如有问题，请参考：

1. **测试报告**: `VisionAI_ClipsMaster_Training_Module_Test_Report.md`
2. **配置文件**: `configs/model_config.yaml`
3. **示例代码**: `tests/` 目录下的测试文件

---

**开发者**: CKEN  
**项目地址**: GitHub @CKEN  
**更新时间**: 2025-07-12
