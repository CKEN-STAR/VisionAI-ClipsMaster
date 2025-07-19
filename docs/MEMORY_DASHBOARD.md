# VisionAI-ClipsMaster 内存监控仪表盘使用指南

本文档详细介绍了VisionAI-ClipsMaster项目中内存监控仪表盘的使用方法和功能，该仪表盘用于实时监控和可视化系统资源使用情况，特别适用于在资源受限环境下（4GB RAM/无GPU）的使用场景。

## 1. 概述

内存监控仪表盘是VisionAI-ClipsMaster的一个重要组成部分，它提供了以下功能：

- 实时系统和进程内存使用率监控
- 5分钟内存使用趋势图表
- 各组件内存占用排行
- 与预警系统集成，支持多级预警
- 轻量级设计，适用于资源受限环境

## 2. 启动仪表盘

有多种方式可以启动内存监控仪表盘：

### 2.1 从主界面启动

在VisionAI-ClipsMaster主界面上，您可以通过以下方式启动仪表盘：

- 点击工具栏上的"内存监控"按钮
- 通过"视图"菜单中的"内存监控仪表盘"项
- 点击状态栏上的内存状态指示器

### 2.2 独立启动

您也可以独立启动内存监控仪表盘：

```bash
# 从项目根目录执行
python -m src.ui.memory_dashboard
```

## 3. 仪表盘功能区介绍

### 3.1 概览标签页

![概览标签页](../resources/images/memory_dashboard_overview.png)

#### 3.1.1 仪表盘

顶部显示两个仪表盘：

- **系统内存**：显示整个系统的内存使用率（百分比）
- **进程内存**：显示当前进程的内存使用量（MB）

这些仪表盘使用颜色编码来指示内存使用状态：
- 绿色：正常（<80%）
- 黄色：警告（80-90%）
- 橙色：错误（90-95%）
- 红色：严重（>95%）

#### 3.1.2 内存趋势图

中部显示内存使用趋势图，展示最近5分钟的内存使用率变化。这有助于观察内存使用模式和潜在的内存泄漏。

#### 3.1.3 组件内存排行

底部显示各组件的内存占用排行表，按内存使用量从高到低排序。主要组件包括：

- **Qwen模型**：中文模型的内存占用
- **缓存系统**：模型分片缓存的内存占用
- **视频处理**：视频处理组件的内存占用
- **UI界面**：界面组件的内存占用
- **其他组件**：其他各种系统组件的内存占用

### 3.2 预警记录标签页

![预警记录标签页](../resources/images/memory_dashboard_alerts.png)

这个标签页显示最近的内存和资源预警记录，包括：

- **级别**：预警级别（INFO、WARNING、ERROR、CRITICAL）
- **时间**：预警发生时间
- **资源**：发生预警的资源类型和名称
- **值**：触发预警的值

预警记录按时间倒序排列，最新的预警显示在顶部。

## 4. 集成到其他界面

除了独立的仪表盘窗口，您还可以将内存监控组件集成到自己的自定义界面中。

### 4.1 集成内存监控小组件

```python
from src.ui.components.memory_visualization import create_embedded_memory_widget

# 在您的窗口中创建内存监控组件
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建布局
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 添加内存监控组件
        self.memory_widget = create_embedded_memory_widget(self)
        layout.addWidget(self.memory_widget)
        
        # 添加其他UI组件
        # ...
        
        self.setCentralWidget(central_widget)
```

### 4.2 添加状态栏指示器

```python
from src.ui.components.memory_visualization import create_status_indicator
from src.ui.dashboard_integration import get_dashboard_launcher

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建状态栏
        statusbar = self.statusBar()
        
        # 添加内存状态指示器
        self.memory_indicator = create_status_indicator(self)
        statusbar.addPermanentWidget(self.memory_indicator)
        
        # 连接点击事件到仪表盘启动
        dashboard_launcher = get_dashboard_launcher()
        self.memory_indicator.clicked.connect(dashboard_launcher.launch_dashboard)
```

## 5. 预警系统集成

内存监控仪表盘与VisionAI-ClipsMaster的预警系统紧密集成，当内存使用超过阈值时会触发相应级别的预警：

- **WARNING (80%)**：发送UI通知、记录日志
- **ERROR (90%)**：发送UI通知、记录日志、用户提示
- **CRITICAL (95%)**：发送UI通知、记录日志、用户提示、紧急保存、释放资源

预警触发后，系统会采取相应的措施，如清理缓存、卸载未使用的模型等，以防止程序崩溃。

## 6. 与Mistral英文模型兼容性

尽管当前配置中没有加载Mistral英文模型，但内存监控仪表盘已经设计为兼容英文模型。一旦英文模型被加载，内存监控系统将自动监控和显示其资源使用情况，无需进行任何代码修改。

在组件内存排行中，将会增加"Mistral模型"条目来显示英文模型的内存占用。

## 7. 性能考虑

内存监控仪表盘设计为轻量级，对系统性能影响极小：

- 默认监控间隔为1-5秒，可根据需要调整
- 支持暂停监控以进一步减少资源占用
- 可以在不需要时关闭窗口，后台监控仍会继续工作

## 8. 故障排除

如果您在使用内存监控仪表盘时遇到问题：

1. **仪表盘无法启动**：检查PyQt6和pyqtgraph是否已安装
2. **数据不更新**：检查监控服务是否正在运行
3. **显示异常值**：可能是监控系统临时故障，尝试重启仪表盘

## 9. 配置选项

内存监控仪表盘的配置与预警系统配置位于同一文件中：`configs/alert_config.yaml`

您可以在该文件中调整以下参数：

```yaml
# 内存相关阈值（百分比）
memory:
  warning: 80    # 内存使用率80%触发警告
  error: 90      # 内存使用率90%触发错误
  critical: 95   # 内存使用率95%触发严重错误

# UI通知相关配置  
ui_notification:
  enabled: true
  duration:      # 通知显示时间（秒）
    warning: 5
    error: 10
    critical: 30
``` 