# 版本演化追踪器

版本演化追踪器（EvolutionTracker）是一个用于管理和可视化版本谱系关系的工具。它可以帮助开发者和用户追踪不同版本之间的衍生关系，并通过可视化方式展示版本演化路径。

## 功能特点

- **版本关系管理**：记录版本之间的父子关系和演化路径
- **多重父级支持**：支持一个版本从多个父版本派生的情况（代码合并）
- **谱系可视化**：提供直观的D3.js树状图可视化界面
- **参数追踪**：记录每个版本的详细参数信息
- **接口简单**：提供简单直观的API接口

## 安装依赖

版本演化追踪器已集成在混剪工具中，无需额外安装。如果需要单独使用，只需确保安装了以下依赖：

```bash
pip install webbrowser
```

## 使用方法

### 基本使用

```python
from src.versioning import EvolutionTracker, generate_html_visualization

# 初始化追踪器
tracker = EvolutionTracker()

# 添加根版本
tracker.add_version("v1.0.0", None, {"name": "初始版本", "features": ["基础功能"]})

# 添加子版本
tracker.add_version("v1.1.0", "v1.0.0", {"name": "功能增强版", "features": ["基础功能", "增强分析"]})

# 获取版本信息
version_info = tracker.get_version("v1.1.0")

# 生成谱系可视化
tree_data = tracker.visualize_lineage("v1.1.0")
html_path = generate_html_visualization(tree_data, "version_evolution.html")
```

### 使用API接口

可以使用API接口更方便地进行版本管理：

```python
from src.api.version_api import add_version, visualize_version_evolution

# 添加版本
result = add_version("v1.0.0", None, {"name": "初始版本"})

# 生成可视化
viz_result = visualize_version_evolution("v1.0.0")
print(f"可视化路径：{viz_result['visualization_path']}")
```

### 版本合并

支持从多个父版本派生出子版本的情况：

```python
from src.api.version_api import add_version, merge_versions

# 添加两个并行版本
add_version("feature_branch", "main", {"name": "功能分支"})
add_version("bugfix_branch", "main", {"name": "修复分支"})

# 创建合并版本
add_version("release", "feature_branch", {"name": "发布版本"})

# 合并另一个分支
merge_versions("release", "bugfix_branch")
```

### 运行演示

可以通过运行演示脚本体验版本演化追踪器的功能：

```bash
python src/examples/evolution_tracker_demo.py --open
```

这将创建一个示例版本谱系，并在浏览器中打开可视化界面。

## 版本数据结构

每个版本包含以下信息：

- **id**: 版本的唯一标识符
- **parent**: 父版本的ID
- **params**: 版本相关的参数信息
- **created_at**: 版本创建时间
- **children**: 子版本ID列表

## 可视化界面

版本演化追踪器使用D3.js生成交互式的版本谱系可视化界面，具有以下特点：

- 动态力导向图布局
- 节点悬停显示详细信息
- 支持拖拽调整节点位置
- 可视化父子关系连接

## 集成到其他系统

版本演化追踪器可以轻松集成到其他系统中：

```python
from src.versioning import EvolutionTracker

class MySystem:
    def __init__(self):
        self.tracker = EvolutionTracker()
        
    def create_version(self, id, parent=None, params=None):
        # 创建系统版本
        # ...
        
        # 记录到版本追踪器
        self.tracker.add_version(id, parent, params)
```

## 注意事项

- 版本ID必须是唯一的
- 可以通过自定义DB路径将版本信息保存到特定位置
- 可视化结果为HTML文件，可以在任何浏览器中查看 