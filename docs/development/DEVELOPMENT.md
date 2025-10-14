# 🔧 VisionAI-ClipsMaster 开发指南

> **开发者文档** | 代码结构、开发规范和测试指南

## 📋 目录

- [🚀 开发环境设置](#-开发环境设置)
- [🏗️ 项目架构](#-项目架构)
- [📝 编码规范](#-编码规范)
- [🧪 测试指南](#-测试指南)
- [🔄 开发流程](#-开发流程)
- [📦 模块开发](#-模块开发)
- [🐛 调试技巧](#-调试技巧)
- [📚 文档编写](#-文档编写)

## 🚀 开发环境设置

### 系统要求
- **Python**: 3.11+ (推荐 3.13)
- **Git**: 最新版本
- **IDE**: VS Code / PyCharm (推荐)
- **内存**: 8GB+ RAM (开发环境)

### 环境配置

```bash
# 1. 克隆仓库
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 2. 创建开发环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装开发依赖
pip install -r requirements.txt
pip install -r requirements/requirements-dev.txt

# 4. 安装预提交钩子
pre-commit install

# 5. 验证环境
python -m pytest test/ -v
```

### IDE配置

#### VS Code 配置
创建 `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["test/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

#### PyCharm 配置
1. 设置Python解释器为虚拟环境
2. 启用代码检查和格式化
3. 配置测试运行器为pytest

## 🏗️ 项目架构

### 核心模块结构

```
src/
├── core/                    # 核心功能模块
│   ├── model_switcher.py   # 模型切换器
│   ├── screenplay_engineer.py # 剧本工程师
│   ├── srt_parser.py       # 字幕解析器
│   ├── narrative_analyzer.py # 叙事分析器
│   └── clip_generator.py   # 视频生成器
├── training/               # 训练模块
│   ├── en_trainer.py      # 英文训练器
│   ├── zh_trainer.py      # 中文训练器
│   └── data_augment.py    # 数据增强
├── exporters/             # 导出模块
│   ├── base_exporter.py   # 基础导出器
│   └── jianying_pro_exporter.py # 剪映导出器
└── utils/                 # 工具模块
    ├── file_checker.py    # 文件检查
    ├── memory_guard.py    # 内存监控
    └── log_handler.py     # 日志处理
```

### 设计模式

#### 1. 策略模式 (Strategy Pattern)
```python
# 不同的重构策略
class ReconstructionStrategy:
    def reconstruct(self, subtitles: List[dict]) -> dict:
        raise NotImplementedError

class ViralStrategy(ReconstructionStrategy):
    def reconstruct(self, subtitles: List[dict]) -> dict:
        # 爆款风格重构逻辑
        pass

class DramaticStrategy(ReconstructionStrategy):
    def reconstruct(self, subtitles: List[dict]) -> dict:
        # 剧情风格重构逻辑
        pass
```

#### 2. 工厂模式 (Factory Pattern)
```python
class ModelFactory:
    @staticmethod
    def create_model(language: str, config: dict):
        if language == "zh":
            return QwenModel(config)
        elif language == "en":
            return MistralModel(config)
        else:
            raise ValueError(f"Unsupported language: {language}")
```

#### 3. 观察者模式 (Observer Pattern)
```python
class ProcessingObserver:
    def update(self, progress: float, message: str):
        pass

class UIProgressObserver(ProcessingObserver):
    def update(self, progress: float, message: str):
        # 更新UI进度条
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
```

## 📝 编码规范

### Python代码风格

#### 1. 命名规范
```python
# 类名：PascalCase
class ModelSwitcher:
    pass

# 函数名和变量名：snake_case
def detect_language(text: str) -> str:
    model_name = "qwen2.5-7b"
    return language_code

# 常量：UPPER_SNAKE_CASE
MAX_MEMORY_USAGE = 4096
DEFAULT_TIMEOUT = 30
```

#### 2. 类型注解
```python
from typing import List, Dict, Optional, Union

def process_subtitles(
    subtitles: List[Dict[str, Union[str, float]]], 
    style: str = "viral",
    max_duration: Optional[int] = None
) -> Dict[str, any]:
    """
    处理字幕数据
    
    Args:
        subtitles: 字幕列表
        style: 处理风格
        max_duration: 最大时长
        
    Returns:
        处理结果字典
    """
    pass
```

#### 3. 文档字符串
```python
def analyze_narrative(self, subtitles: List[dict]) -> dict:
    """
    分析叙事结构
    
    这个方法分析输入字幕的叙事结构，包括情节点、情感曲线
    和角色发展轨迹。
    
    Args:
        subtitles (List[dict]): 字幕数据列表，每个元素包含：
            - index (int): 字幕序号
            - start_time (float): 开始时间（秒）
            - end_time (float): 结束时间（秒）
            - text (str): 字幕文本
    
    Returns:
        dict: 分析结果，包含：
            - plot_points (List[dict]): 关键情节点
            - emotion_curve (List[float]): 情感强度曲线
            - character_arcs (dict): 角色发展弧线
            - pacing_score (float): 节奏评分
    
    Raises:
        ValueError: 当字幕数据格式不正确时
        ProcessingError: 当分析过程出错时
    
    Example:
        >>> analyzer = NarrativeAnalyzer()
        >>> subtitles = [
        ...     {"index": 1, "start_time": 0.0, "end_time": 5.0, "text": "开场"}
        ... ]
        >>> result = analyzer.analyze_narrative(subtitles)
        >>> print(result['pacing_score'])
        0.85
    """
    pass
```

### 错误处理

#### 1. 自定义异常
```python
class VisionAIError(Exception):
    """VisionAI基础异常类"""
    pass

class ModelNotFoundError(VisionAIError):
    """模型文件未找到"""
    pass

class ProcessingTimeoutError(VisionAIError):
    """处理超时"""
    def __init__(self, timeout: int, operation: str):
        self.timeout = timeout
        self.operation = operation
        super().__init__(f"Operation '{operation}' timed out after {timeout}s")
```

#### 2. 异常处理模式
```python
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def error_handler(operation: str):
    """统一错误处理上下文管理器"""
    try:
        yield
    except ModelNotFoundError as e:
        logger.error(f"Model error in {operation}: {e}")
        raise
    except ProcessingTimeoutError as e:
        logger.error(f"Timeout in {operation}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in {operation}: {e}")
        raise ProcessingError(f"Failed to {operation}: {e}")

# 使用示例
def load_model(model_name: str):
    with error_handler("load model"):
        # 模型加载逻辑
        pass
```

## 🧪 测试指南

### 测试结构

```
test/
├── unit_test/              # 单元测试
│   ├── test_model_switcher.py
│   ├── test_srt_parser.py
│   └── test_narrative_analyzer.py
├── integration_test/       # 集成测试
│   ├── test_workflow.py
│   └── test_export_pipeline.py
├── stress_test/           # 压力测试
│   └── test_memory_usage.py
└── conftest.py           # pytest配置
```

### 单元测试示例

```python
import pytest
from unittest.mock import Mock, patch
from src.core.model_switcher import ModelSwitcher

class TestModelSwitcher:
    
    @pytest.fixture
    def switcher(self):
        """测试用的模型切换器实例"""
        return ModelSwitcher()
    
    def test_detect_language_chinese(self, switcher):
        """测试中文语言检测"""
        text = "这是一个中文测试文本"
        result = switcher.detect_language(text)
        assert result == "zh"
    
    def test_detect_language_english(self, switcher):
        """测试英文语言检测"""
        text = "This is an English test text"
        result = switcher.detect_language(text)
        assert result == "en"
    
    @patch('src.core.model_switcher.load_model')
    def test_switch_model_success(self, mock_load, switcher):
        """测试模型切换成功"""
        mock_load.return_value = True
        result = switcher.switch_model("zh")
        assert result is True
        mock_load.assert_called_once()
    
    def test_switch_model_invalid_language(self, switcher):
        """测试无效语言参数"""
        with pytest.raises(ValueError):
            switcher.switch_model("invalid")
    
    @pytest.mark.parametrize("language,expected", [
        ("zh", "qwen2.5-7b"),
        ("en", "mistral-7b"),
    ])
    def test_get_model_name(self, switcher, language, expected):
        """参数化测试模型名称获取"""
        result = switcher.get_model_name(language)
        assert expected in result
```

### 集成测试示例

```python
import pytest
import tempfile
from pathlib import Path
from src.core.screenplay_engineer import ScreenplayEngineer
from src.core.model_switcher import ModelSwitcher

class TestWorkflowIntegration:
    
    @pytest.fixture
    def temp_srt_file(self):
        """创建临时SRT文件"""
        content = """1
00:00:01,000 --> 00:00:05,000
这是第一句话

2
00:00:06,000 --> 00:00:10,000
这是第二句话
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
            f.write(content)
            return f.name
    
    def test_complete_workflow(self, temp_srt_file):
        """测试完整工作流程"""
        # 1. 初始化组件
        switcher = ModelSwitcher()
        engineer = ScreenplayEngineer(switcher)
        
        # 2. 处理文件
        result = engineer.reconstruct_screenplay(temp_srt_file)
        
        # 3. 验证结果
        assert 'segments' in result
        assert 'total_duration' in result
        assert len(result['segments']) > 0
        
        # 清理
        Path(temp_srt_file).unlink()
```

### 性能测试

```python
import pytest
import time
import psutil
from src.utils.memory_guard import MemoryGuard

class TestPerformance:
    
    def test_memory_usage_limit(self):
        """测试内存使用限制"""
        guard = MemoryGuard()
        initial_memory = guard.get_memory_info()['process']
        
        # 执行内存密集操作
        # ... 测试代码 ...
        
        final_memory = guard.get_memory_info()['process']
        memory_increase = final_memory - initial_memory
        
        # 内存增长不应超过1GB
        assert memory_increase < 1024, f"Memory increased by {memory_increase}MB"
    
    @pytest.mark.timeout(30)
    def test_processing_speed(self):
        """测试处理速度"""
        start_time = time.time()
        
        # 执行处理操作
        # ... 测试代码 ...
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 处理时间不应超过30秒
        assert processing_time < 30, f"Processing took {processing_time}s"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest test/unit_test/test_model_switcher.py

# 运行带覆盖率的测试
pytest --cov=src --cov-report=html

# 运行性能测试
pytest test/stress_test/ -v

# 运行标记的测试
pytest -m "not slow"
```

## 🔄 开发流程

### Git工作流

#### 1. 分支策略
```bash
# 主分支
main                    # 生产版本
develop                 # 开发版本

# 功能分支
feature/ai-model-optimization
feature/ui-improvements
feature/export-enhancement

# 修复分支
fix/memory-leak
fix/srt-parser-bug

# 发布分支
release/v1.1.0
```

#### 2. 提交规范
```bash
# 功能提交
git commit -m "feat(core): 添加新的AI模型支持"

# 修复提交
git commit -m "fix(parser): 修复SRT时间码解析错误"

# 文档提交
git commit -m "docs(api): 更新API参考文档"

# 测试提交
git commit -m "test(unit): 添加模型切换器单元测试"
```

#### 3. 代码审查
```bash
# 创建Pull Request前
git checkout feature/new-feature
git rebase main
git push origin feature/new-feature

# 代码审查检查清单
- [ ] 代码符合编码规范
- [ ] 添加了适当的测试
- [ ] 更新了相关文档
- [ ] 通过了所有测试
- [ ] 没有引入新的安全漏洞
```

## 📦 模块开发

### 创建新模块

#### 1. 模块结构
```python
# src/new_module/__init__.py
"""新模块包"""

from .main_class import MainClass
from .helper_functions import helper_function

__all__ = ['MainClass', 'helper_function']
__version__ = '1.1.0'
```

#### 2. 主类实现
```python
# src/new_module/main_class.py
import logging
from typing import Dict, List, Optional
from ..utils.base_class import BaseClass

logger = logging.getLogger(__name__)

class MainClass(BaseClass):
    """新模块的主要类"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self._initialize()
    
    def _initialize(self):
        """初始化模块"""
        logger.info("Initializing new module")
        # 初始化逻辑
    
    def process(self, data: List[Dict]) -> Dict:
        """处理数据的主要方法"""
        try:
            result = self._internal_process(data)
            logger.info(f"Processing completed, result: {len(result)} items")
            return result
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
    
    def _internal_process(self, data: List[Dict]) -> Dict:
        """内部处理逻辑"""
        # 实现处理逻辑
        pass
```

#### 3. 配置文件
```yaml
# configs/new_module_config.yaml
new_module:
  enabled: true
  parameters:
    threshold: 0.8
    max_iterations: 100
  logging:
    level: INFO
    file: "logs/new_module.log"
```

### 模块集成

#### 1. 注册模块
```python
# src/core/module_registry.py
from ..new_module import MainClass

MODULE_REGISTRY = {
    'new_module': MainClass,
    # 其他模块...
}

def get_module(name: str, config: dict):
    """获取模块实例"""
    if name not in MODULE_REGISTRY:
        raise ValueError(f"Unknown module: {name}")
    return MODULE_REGISTRY[name](config)
```

#### 2. 配置集成
```python
# src/core/config_manager.py
def load_module_config(module_name: str) -> dict:
    """加载模块配置"""
    config_path = f"configs/{module_name}_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
```

## 🐛 调试技巧

### 日志调试

#### 1. 配置日志
```python
# src/utils/logger_config.py
import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: str = None):
    """配置日志系统"""
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 文件处理器
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers
    )
```

#### 2. 使用日志
```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug(f"Processing {len(data)} items")
    
    try:
        result = complex_operation(data)
        logger.info(f"Processing successful: {len(result)} results")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

### 性能分析

#### 1. 内存分析
```python
import tracemalloc
import psutil

def memory_profile(func):
    """内存分析装饰器"""
    def wrapper(*args, **kwargs):
        # 开始内存跟踪
        tracemalloc.start()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # 获取内存使用情况
            current, peak = tracemalloc.get_traced_memory()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"Function: {func.__name__}")
            print(f"Memory usage: {final_memory - initial_memory:.2f} MB")
            print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
            
            tracemalloc.stop()
    
    return wrapper

@memory_profile
def memory_intensive_function():
    # 内存密集型操作
    pass
```

#### 2. 时间分析
```python
import time
import functools

def timing_profile(func):
    """时间分析装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    
    return wrapper

@timing_profile
def slow_function():
    # 耗时操作
    pass
```

## 📚 文档编写

### API文档

使用Sphinx自动生成API文档：

```python
def process_subtitles(subtitles: List[Dict], style: str = "viral") -> Dict:
    """
    处理字幕数据生成混剪方案
    
    Args:
        subtitles: 字幕数据列表
        style: 处理风格，可选值：
            - "viral": 爆款风格
            - "dramatic": 剧情风格
            - "comedy": 搞笑风格
    
    Returns:
        包含处理结果的字典：
        
        .. code-block:: python
        
            {
                'segments': [
                    {
                        'start_time': 0.0,
                        'end_time': 5.0,
                        'text': '片段文本',
                        'importance': 0.9
                    }
                ],
                'total_duration': 120.5,
                'style_score': 0.85
            }
    
    Raises:
        ValueError: 当style参数无效时
        ProcessingError: 当处理过程出错时
    
    Example:
        >>> subtitles = [{'start_time': 0, 'end_time': 5, 'text': '开场'}]
        >>> result = process_subtitles(subtitles, style="viral")
        >>> print(result['total_duration'])
        5.0
    
    Note:
        此函数会自动检测字幕语言并选择合适的AI模型进行处理。
        处理时间取决于字幕长度和系统性能。
    
    See Also:
        :func:`analyze_narrative`: 叙事结构分析
        :func:`export_project`: 项目导出功能
    """
    pass
```

### 用户文档

使用Markdown编写用户友好的文档：

```markdown
## 🎬 视频处理功能

### 基本使用

1. **上传文件**
   ```bash
   python simple_ui_fixed.py
   ```
   
2. **选择处理模式**
   - 快速模式：适合预览和测试
   - 标准模式：平衡质量和速度
   - 高质量模式：最佳输出质量

3. **开始处理**
   点击"开始处理"按钮，系统将自动：
   - 检测字幕语言
   - 加载对应AI模型
   - 分析剧情结构
   - 生成混剪方案

### 高级设置

#### 自定义处理参数

编辑 `configs/clip_settings.json`：

```json
{
  "style": {
    "viral": {
      "emotion_threshold": 0.7,
      "pacing_factor": 1.2,
      "hook_strength": 0.9
    }
  }
}
```

#### 批量处理

```bash
python src/api/cli_interface.py \
  --input-dir "input/" \
  --output-dir "output/" \
  --style viral \
  --max-duration 60
```
```

---

## 📞 开发支持

- **技术讨论**: [GitHub Discussions](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/discussions)
- **Bug报告**: [GitHub Issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
- **代码审查**: 提交Pull Request
- **邮件联系**: [peresbreedanay7156@gmail.com](mailto:peresbreedanay7156@gmail.com)

---

**开始您的VisionAI-ClipsMaster开发之旅！** 🚀👨‍💻
