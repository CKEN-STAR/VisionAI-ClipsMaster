# 剧本分析可视化模块

## 功能介绍

剧本分析可视化模块提供了对短剧混剪分析结果的可视化展示功能，包括：

1. 情感曲线分析 - 直观展示剧情情感起伏
2. 角色关系网络 - 展示角色间的互动和关系
3. 剧情时间线 - 展示剧情发展和关键片段
4. 基础信息统计 - 显示剧本长度、语言等基本信息

## 使用方法

### 命令行工具

```bash
# 生成示例数据并打开可视化报告
python src/visualization/cli.py --sample --open

# 从现有JSON文件生成报告
python src/visualization/cli.py --input path/to/script_data.json --open

# 生成报告并保存到指定位置
python src/visualization/cli.py --input path/to/script_data.json --output path/to/output.html

# 生成PNG格式报告
python src/visualization/cli.py --input path/to/script_data.json --format png
```

### 在代码中使用

```python
# 通过UI面板方式使用
from src.ui.visualization_panel import VisualizationPanel

# 创建面板
panel = VisualizationPanel()

# 从JSON文件生成报告
report_path = panel.visualize_from_json("path/to/script_data.json")

# 打开报告
panel.open_report(report_path)
```

或者直接使用底层API：

```python
from src.visualization.script_visualizer import export_visualization_report

# 生成报告
report_path = export_visualization_report(script_data, "path/to/output.html")
```

## 数据格式

可视化模块接受如下JSON格式的剧本数据：

```json
{
    "process_id": "20250430123456",
    "language": "zh",
    "total_duration": 120.5,
    "template_used": "conflict_resolution,emotional_rollercoaster",
    "key_characters": ["李明", "张红", "王芳"],
    "scene_count": 5,
    "segments": [
        {
            "time": {
                "start": 0,
                "end": 10.5
            },
            "content": "李明：这是一段示例对话",
            "sentiment": {
                "label": "POSITIVE",
                "score": 0.75
            }
        },
        // 更多片段...
    ]
}
```

## 文件结构

- `script_visualizer.py` - 主要可视化功能实现
- `standalone_test.py` - 独立测试脚本，用于测试可视化功能
- `cli.py` - 命令行接口
- `templates/` - HTML模板目录
  - `report_template.html` - 报告HTML模板

## 注意事项

1. 确保先安装所需依赖：`pip install plotly networkx jinja2 matplotlib`
2. 生成的报告保存在 `data/output/reports/` 目录下
3. HTML报告使用浏览器打开查看，支持交互操作 