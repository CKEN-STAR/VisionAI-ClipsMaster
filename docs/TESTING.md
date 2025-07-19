# VisionAI-ClipsMaster 测试框架

本文档介绍 VisionAI-ClipsMaster 项目的测试框架及其使用方法。测试框架旨在确保项目的各个组件按照预期工作，并且提供了多种测试模板以简化测试用例的编写。

## 测试框架结构

测试框架由以下部分组成：

1. **基础测试模板** (`tests/templates/test_template.py`)：
   - 提供通用的测试环境初始化和清理逻辑
   - 管理测试数据、临时目录和环境变量

2. **专用测试模板**：
   - 模型测试模板 (`tests/templates/model_test_template.py`)：用于测试模型加载、切换等功能
   - 语言检测测试模板 (`tests/templates/language_test_template.py`)：用于测试语言检测和模型切换
   - 内存管理测试模板 (`tests/templates/memory_test_template.py`)：用于测试低内存环境下的性能和容错处理

3. **测试数据生成工具** (`tests/utils/test_data.py`)：
   - 提供测试视频、字幕文件和训练数据的生成功能
   - 支持中英文测试数据
   - 包含无 ffmpeg 环境下的容错处理

4. **测试运行脚本** (`run_tests.py`)：
   - 支持运行所有测试或指定类别的测试
   - 提供命令行接口，方便测试执行

## 使用方法

### 初始化测试环境

在编写或运行测试之前，你需要初始化测试环境：

```bash
# 生成最小测试数据集（快速）
python scripts/init_test_data.py --minimal --quick

# 生成完整测试数据集
python scripts/init_test_data.py
```

### 编写测试用例

#### 1. 基本测试用例

继承 `BaseTestCase` 来创建基本测试用例：

```python
from tests.templates import BaseTestCase

class TestExample(BaseTestCase):
    def test_something(self):
        # 测试代码
        self.assertTrue(True)
```

#### 2. 模型测试用例

继承 `ModelTestCase` 来测试模型相关功能：

```python
from tests.templates import ModelTestCase
from src.core.model_loader import ModelLoader

class TestModel(ModelTestCase):
    def setUp(self):
        super().setUp()
        self.model_loader = ModelLoader(model_dir=self.test_models_dir)

    def test_model_loading(self):
        # 设置模拟模型文件
        self.setup_mock_chinese_model()
        # 加载模型并验证
        self.model_loader.load_model("qwen2.5-7b-zh")
        self.assert_model_loaded(self.model_loader, "qwen2.5-7b-zh")
```

#### 3. 语言检测测试用例

继承 `LanguageTestCase` 来测试语言检测功能：

```python
from tests.templates import LanguageTestCase
from src.core.language_detector import LanguageDetector

class TestLanguageDetector(LanguageTestCase):
    def setUp(self):
        super().setUp()
        self.detector = LanguageDetector(config_dir=self.model_configs_dir)

    def test_chinese_detection(self):
        # 使用预定义的中文样本
        zh_path = self.get_language_sample_path("zh_sample")
        self.assert_language_detected(self.detector, zh_path, "zh")

    def test_custom_content(self):
        # 创建自定义内容的测试文件
        content = "这是自定义测试内容"
        file_path = self.create_custom_subtitle(content, "custom_zh")
        self.assert_language_detected(self.detector, file_path, "zh")
```

#### 4. 内存管理测试用例

继承 `MemoryTestCase` 来测试内存管理功能：

```python
from tests.templates import MemoryTestCase

class TestMemoryManagement(MemoryTestCase):
    def test_memory_usage(self):
        def memory_intensive_function():
            # 执行内存密集型操作
            data = [bytearray(1024 * 1024) for _ in range(10)]  # 分配约10MB内存
            return len(data)

        # 测量内存使用情况
        result, memory_info = self.measure_memory_usage(memory_intensive_function)
        
        # 断言结果和内存使用
        self.assertEqual(result, 10)
        self.assert_memory_increase_within(memory_info, 15)  # 内存增加不超过15MB
        
        # 测试内存恢复
        _, recovery_info = self.test_memory_recovery(memory_intensive_function)
        self.assertGreater(recovery_info["recovered_mb"], 5)  # 至少恢复5MB内存
```

### 运行测试

使用 `run_tests.py` 脚本运行测试：

```bash
# 运行所有测试
python run_tests.py

# 运行特定类别的测试
python run_tests.py --category language

# 运行匹配特定模式的测试
python run_tests.py --pattern "test_language_*.py"

# 启用详细输出
python run_tests.py --verbose
```

### 测试数据

测试框架提供以下测试数据：

1. **测试视频**：
   - 使用 ffmpeg 生成的标准测试视频
   - 在无 ffmpeg 环境下创建占位视频文件

2. **测试字幕**：
   - 中文字幕样本
   - 英文字幕样本
   - 混合语言字幕样本

3. **训练数据对**：
   - 原片字幕 + 混剪字幕对
   - 支持不同复杂度级别 (simple, medium, complex)

4. **黄金标准样本**：
   - 包含视频、原始字幕和期望混剪字幕
   - 包含元数据（重要时间戳等）

## 最佳实践

1. **使用测试模板**：
   - 尽量使用提供的测试模板，避免重复代码
   - 根据测试需求选择合适的模板类

2. **测试数据管理**：
   - 使用 `get_test_file_path()` 和 `get_output_path()` 方法管理测试文件路径
   - 使用测试模板提供的辅助方法创建测试数据

3. **内存测试**：
   - 使用 `measure_memory_usage()` 监控内存使用情况
   - 使用 `test_memory_recovery()` 验证内存是否正确释放

4. **测试命名规范**：
   - 测试文件命名为 `test_*.py`
   - 测试类命名为 `Test*`
   - 测试方法命名为 `test_*`

5. **测试覆盖率**：
   - 确保测试覆盖核心功能
   - 包含正常情况和边界情况的测试

## 常见问题解答

### Q: 如何在测试中模拟不同的内存环境？

A: 使用 `MemoryTestCase` 中的 `simulate_memory_pressure()` 方法来模拟不同的内存压力环境。

### Q: 如何测试模型在不同语言下的行为？

A: 使用 `LanguageTestCase` 提供的语言样本和断言方法，结合 `ModelTestCase` 的模型模拟功能。

### Q: 如何处理测试中的临时文件？

A: 所有测试模板类都会自动管理临时文件，在测试完成后清理。使用 `self.temp_dir` 存储临时文件，它们会在测试完成后被删除。 