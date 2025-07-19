# 内存泄漏追踪系统

VisionAI-ClipsMaster 项目的内存泄漏追踪系统，专为低内存环境（4GB RAM无GPU的设备）设计。

## 功能特点

- **轻量级设计**: 专为低内存环境优化，最小化运行时开销
- **自动检测**: 自动检测内存泄漏并生成报告
- **连续监控**: 支持泄漏趋势分析（连续3次测试同一位置内存增长>2%）
- **可视化报告**: 生成详细的泄漏位置和大小报告
- **命令行工具**: 提供简单易用的命令行接口
- **自动清理**: 检测到泄漏时尝试自动清理内存
- **与已有内存探针系统集成**: 与现有的内存探针系统无缝衔接

## 安装与依赖

内存泄漏追踪系统已内置在VisionAI-ClipsMaster项目中，主要依赖以下Python标准库：

- `tracemalloc`: 内存分配追踪
- `gc`: 垃圾回收控制
- `threading`: 后台监控线程
- `psutil`: 系统内存监控（外部依赖）

## 使用方法

### 命令行使用

#### Windows:

```bash
# 监控内存泄漏
scripts\leak_detector.bat monitor --interval 60 --threshold 2.0

# 检查内存泄漏
scripts\leak_detector.bat check --repeat 3

# 重置追踪器
scripts\leak_detector.bat reset
```

#### Linux/macOS:

```bash
# 监控内存泄漏
./scripts/leak_detector.sh monitor --interval 60 --threshold 2.0

# 检查内存泄漏
./scripts/leak_detector.sh check --repeat 3

# 重置追踪器
./scripts/leak_detector.sh reset
```

### 命令行选项

#### 监控命令 (monitor)

```
--interval INTERVAL    监控间隔（秒），默认60秒
--threshold THRESHOLD  泄漏阈值（百分比），默认2.0%
--consecutive CONSEC   连续检测阈值，默认3次
--duration DURATION    监控持续时间（秒），0表示无限
--log-dir LOG_DIR      日志目录
```

#### 检查命令 (check)

```
--threshold THRESHOLD  泄漏阈值（百分比），默认2.0%
--consecutive CONSEC   连续检测阈值，默认3次
--repeat REPEAT        重复检查次数，默认1次
--interval INTERVAL    重复检查间隔（秒），默认5秒
--log-dir LOG_DIR      日志目录
```

#### 模拟命令 (simulate)

```
--size SIZE            每次泄漏大小（MB），默认10MB
--count COUNT          泄漏对象数量，默认10个
--interval INTERVAL    泄漏间隔（秒），默认2秒
--cleanup              测试结束后清理泄漏
```

### 编程接口

#### 基本用法

```python
from src.memory import enable_leak_tracking, check_leaks, disable_leak_tracking

# 启用内存泄漏追踪（后台监控）
enable_leak_tracking(interval_seconds=300.0)

# 执行可能泄漏的代码...

# 主动检查泄漏
leaks = check_leaks()
if leaks:
    print(f"检测到 {len(leaks)} 个潜在泄漏")

# 禁用泄漏追踪
disable_leak_tracking()
```

#### 高级用法

```python
from src.memory.leak_detector import LeakTracker

# 创建自定义配置的追踪器
tracker = LeakTracker(
    leak_threshold_percent=1.5,   # 1.5%阈值
    consecutive_leaks_threshold=2, # 连续2次视为泄漏
    top_stats_limit=30,           # 跟踪30个最大分配点
    auto_cleanup=True             # 自动清理
)

# 检查泄漏
leaks = tracker.check_for_leaks()

# 获取摘要
summary = tracker.get_leak_summary()

# 保存报告
report_file = tracker.save_leak_report()
```

## 泄漏判定标准

系统使用以下标准判定内存泄漏：

1. **增长阈值**: 特定内存分配点的内存使用增长超过预设阈值（默认2%）
2. **连续性**: 连续多次检测到同一位置内存增长（默认3次）
3. **大小筛选**: 默认只关注大于1MB的内存分配

## 故障排除

### 常见问题

1. **检测不到泄漏**
   - 增加监控间隔时间
   - 降低泄漏阈值（--threshold参数）
   - 降低连续检测阈值（--consecutive参数）

2. **误报**
   - 增加泄漏阈值
   - 增加连续检测阈值
   - 确保在检测前执行垃圾回收

3. **高内存占用**
   - 减少top_stats_limit参数
   - 增加监控间隔
   - 手动触发垃圾回收

### 日志位置

泄漏报告默认保存在用户目录下的 `.visionai/logs/memory/` 文件夹中，可通过 `--log-dir` 参数自定义。

## 实现细节

内存泄漏追踪系统基于Python的`tracemalloc`模块实现，主要功能点：

1. **快照比较**: 比较不同时间点的内存快照
2. **位置追踪**: 跟踪内存分配的源代码位置
3. **统计分析**: 分析内存使用趋势
4. **报告生成**: 生成详细的泄漏报告

## 集成点

本系统与VisionAI-ClipsMaster的其他组件集成：

- 与内存探针系统协同工作
- 可通过应用程序配置启用/禁用
- 支持自动监控关键代码点

## 性能影响

- **内存开销**: 追踪开启时约增加5-10MB内存使用
- **CPU开销**: 后台监控线程的CPU使用率<1%
- **影响最小化**: 专为低端设备优化的轻量级设计

## 贡献者

- VisionAI-ClipsMaster 开发团队 