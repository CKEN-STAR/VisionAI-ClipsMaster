# 📚 VisionAI-ClipsMaster API 参考文档

> **版本**: v1.1.0
> **更新日期**: 2025年10月10日
> **适用范围**: 开发者和集成者

## 📋 目录

- [🚀 快速开始](#-快速开始)
- [🧠 核心模块](#-核心模块)
- [🎬 剧本重构API](#-剧本重构api)
- [🔄 模型管理API](#-模型管理api)
- [📤 导出功能API](#-导出功能api)
- [🛠️ 工具类API](#-工具类api)
- [⚠️ 错误处理](#-错误处理)
- [📝 示例代码](#-示例代码)

## 🚀 快速开始

### 安装和导入

```python
# 安装依赖
pip install -r requirements.txt

# 导入核心模块
from src.core.model_switcher import ModelSwitcher
from src.core.screenplay_engineer import ScreenplayEngineer
from src.exporters.jianying_pro_exporter import JianyingProExporter
```

### 基本使用流程

```python
# 1. 初始化模型切换器
switcher = ModelSwitcher()

# 2. 创建剧本工程师
engineer = ScreenplayEngineer(switcher)

# 3. 处理字幕文件
result = engineer.reconstruct_screenplay("input.srt")

# 4. 导出结果
exporter = JianyingProExporter()
exporter.export_project(result, "output.json")
```

## 🧠 核心模块

### ModelSwitcher 类

智能模型切换器，负责中英文模型的动态加载和切换。

#### 初始化

```python
class ModelSwitcher:
    def __init__(self, config_path: str = "configs/model_config.yaml"):
        """
        初始化模型切换器
        
        Args:
            config_path (str): 模型配置文件路径
        """
```

#### 主要方法

##### detect_language()

```python
def detect_language(self, text: str) -> str:
    """
    检测文本语言
    
    Args:
        text (str): 待检测的文本
        
    Returns:
        str: 语言代码 ('zh' 或 'en')
        
    Example:
        >>> switcher = ModelSwitcher()
        >>> lang = switcher.detect_language("这是中文文本")
        >>> print(lang)  # 'zh'
    """
```

##### switch_model()

```python
def switch_model(self, language: str) -> bool:
    """
    切换到指定语言的模型
    
    Args:
        language (str): 目标语言 ('zh' 或 'en')
        
    Returns:
        bool: 切换是否成功
        
    Raises:
        ModelNotFoundError: 模型文件不存在
        MemoryError: 内存不足
    """
```

##### get_model_info()

```python
def get_model_info(self) -> dict:
    """
    获取当前模型信息
    
    Returns:
        dict: 模型信息字典
        {
            'name': str,           # 模型名称
            'language': str,       # 支持语言
            'memory_usage': int,   # 内存使用量(MB)
            'quantization': str,   # 量化级别
            'status': str          # 模型状态
        }
    """
```

### ScreenplayEngineer 类

剧本重构工程师，负责分析和重构剧情结构。

#### 初始化

```python
class ScreenplayEngineer:
    def __init__(self, model_switcher: ModelSwitcher):
        """
        初始化剧本工程师
        
        Args:
            model_switcher (ModelSwitcher): 模型切换器实例
        """
```

#### 主要方法

##### reconstruct_screenplay()

```python
def reconstruct_screenplay(
    self, 
    input_file: str, 
    style: str = "viral",
    max_duration: int = 300
) -> dict:
    """
    重构剧本为爆款风格
    
    Args:
        input_file (str): 输入SRT文件路径
        style (str): 重构风格 ('viral', 'dramatic', 'comedy')
        max_duration (int): 最大时长(秒)
        
    Returns:
        dict: 重构结果
        {
            'segments': List[dict],     # 片段列表
            'total_duration': float,    # 总时长
            'style_score': float,       # 风格评分
            'coherence_score': float    # 连贯性评分
        }
        
    Raises:
        FileNotFoundError: 输入文件不存在
        InvalidFormatError: SRT格式错误
    """
```

##### analyze_narrative()

```python
def analyze_narrative(self, subtitles: List[dict]) -> dict:
    """
    分析叙事结构
    
    Args:
        subtitles (List[dict]): 字幕列表
        
    Returns:
        dict: 分析结果
        {
            'plot_points': List[dict],   # 情节点
            'emotion_curve': List[float], # 情感曲线
            'character_arcs': dict,      # 角色弧线
            'pacing_analysis': dict      # 节奏分析
        }
    """
```

## 🎬 剧本重构API

### SRTParser 类

SRT字幕文件解析器。

```python
class SRTParser:
    @staticmethod
    def parse_file(file_path: str) -> List[dict]:
        """
        解析SRT文件
        
        Args:
            file_path (str): SRT文件路径
            
        Returns:
            List[dict]: 字幕条目列表
            [
                {
                    'index': int,           # 序号
                    'start_time': float,    # 开始时间(秒)
                    'end_time': float,      # 结束时间(秒)
                    'text': str,           # 字幕文本
                    'duration': float       # 持续时间(秒)
                }
            ]
        """
    
    @staticmethod
    def validate_format(file_path: str) -> bool:
        """
        验证SRT文件格式
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 格式是否正确
        """
```

### NarrativeAnalyzer 类

叙事分析器，分析剧情结构和情感走向。

```python
class NarrativeAnalyzer:
    def analyze_plot_structure(self, subtitles: List[dict]) -> dict:
        """
        分析情节结构
        
        Args:
            subtitles (List[dict]): 字幕数据
            
        Returns:
            dict: 情节分析结果
            {
                'act_structure': dict,      # 三幕结构
                'turning_points': List[int], # 转折点位置
                'climax_position': int,     # 高潮位置
                'resolution_quality': float # 结局质量评分
            }
        """
    
    def extract_emotion_curve(self, subtitles: List[dict]) -> List[float]:
        """
        提取情感曲线
        
        Args:
            subtitles (List[dict]): 字幕数据
            
        Returns:
            List[float]: 情感强度序列 (0.0-1.0)
        """
```

## 🔄 模型管理API

### ModelManager 类

模型生命周期管理器。

```python
class ModelManager:
    def load_model(self, model_name: str, quantization: str = "Q4_K_M") -> bool:
        """
        加载指定模型
        
        Args:
            model_name (str): 模型名称
            quantization (str): 量化级别
            
        Returns:
            bool: 加载是否成功
        """
    
    def unload_model(self, model_name: str) -> bool:
        """
        卸载模型释放内存
        
        Args:
            model_name (str): 模型名称
            
        Returns:
            bool: 卸载是否成功
        """
    
    def get_memory_usage(self) -> dict:
        """
        获取内存使用情况
        
        Returns:
            dict: 内存使用信息
            {
                'total_memory': int,        # 总内存(MB)
                'used_memory': int,         # 已用内存(MB)
                'model_memory': int,        # 模型占用(MB)
                'available_memory': int     # 可用内存(MB)
            }
        """
```

## 📤 导出功能API

### JianyingProExporter 类

剪映专业版项目导出器。

```python
class JianyingProExporter:
    def export_project(
        self, 
        segments: List[dict], 
        output_path: str,
        project_name: str = "VisionAI_Project"
    ) -> bool:
        """
        导出剪映项目文件
        
        Args:
            segments (List[dict]): 视频片段列表
            output_path (str): 输出文件路径
            project_name (str): 项目名称
            
        Returns:
            bool: 导出是否成功
        """
```

---

**VisionAI-ClipsMaster API 文档** | 版本 v1.0.1 | 更新于 2025-07-25
