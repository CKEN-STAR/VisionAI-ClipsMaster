# 历史数据分析模块

## 简介

历史数据分析模块为VisionAI-ClipsMaster提供了强大的系统性能监控和分析功能。该模块专门针对4GB RAM/无GPU的低资源环境进行了优化设计，可以帮助用户识别潜在问题，优化系统配置，提高系统的可靠性和性能。

主要功能：

1. **内存使用趋势分析**：监控和分析系统内存和进程内存的使用情况，识别潜在的内存泄漏。
2. **缓存性能分析**：评估缓存命中率和效率，提供优化建议。
3. **OOM风险预测**：预测潜在的内存溢出风险，并提供预防措施。
4. **自动报告生成**：生成日报和周报，包含完整的系统性能分析和建议。
5. **可视化仪表盘**：直观展示性能指标和趋势。

## 安装依赖

```bash
pip install tabulate matplotlib psutil numpy pandas
```

如果需要使用可视化仪表盘，还需要安装：

```bash
pip install PyQt6 pyqtgraph
```

## 使用方法

### 命令行工具

历史数据分析模块提供了便捷的命令行工具：

```bash
# 查看帮助
python src/monitor/cli.py --help

# 启动数据采集（每5分钟采集一次）
python src/monitor/cli.py collect --interval 300

# 生成每日报告
python src/monitor/cli.py report --daily

# 生成每周报告
python src/monitor/cli.py report --weekly

# 列出现有报告
python src/monitor/cli.py report --list

# 分析最近7天的内存趋势
python src/monitor/cli.py analyze --memory --days 7

# 分析最近7天的缓存性能
python src/monitor/cli.py analyze --cache --days 7

# 分析最近7天的OOM风险
python src/monitor/cli.py analyze --oom --days 7

# 启动可视化仪表盘
python src/monitor/cli.py dashboard
```

### API使用

历史数据分析模块也提供了Python API，可以在其他模块中直接使用：

```python
from src.monitor.history_analyzer import (
    start_collection, 
    generate_daily_report,
    analyze_memory_trends,
    analyze_cache_performance,
    analyze_oom_risks
)

# 启动数据采集
start_collection(interval=300)  # 每5分钟采集一次

# 生成每日报告
report = generate_daily_report()

# 分析内存趋势
memory_analysis = analyze_memory_trends(days=7)

# 分析缓存性能
cache_analysis = analyze_cache_performance(days=7)

# 分析OOM风险
oom_analysis = analyze_oom_risks(days=7)
```

### HTTP API

通过Flask API可以在Web界面中访问历史数据分析功能：

```
GET /api/history/reports/daily - 获取最新的每日报告
GET /api/history/reports/weekly - 获取最新的每周报告
GET /api/history/reports/list - 获取报告列表
GET /api/history/analysis/memory?days=7 - 获取内存分析
GET /api/history/analysis/cache?days=7 - 获取缓存分析
GET /api/history/analysis/oom?days=7 - 获取OOM风险分析
POST /api/history/reports/generate/daily - 生成每日报告
POST /api/history/reports/generate/weekly - 生成每周报告
```

## 报告类型

### 每日报告

每日报告包含最近24小时的系统性能概览，包括：

- 峰值和平均内存使用率
- 缓存命中率
- 系统警告和错误数量
- 预测的内存趋势

### 每周报告

每周报告提供更加详细的系统性能分析，包括：

- 每日内存使用趋势图表
- 缓存性能变化趋势
- OOM风险评估及预测
- 系统优化建议

## 配置

历史数据分析模块的配置存储在以下位置：

- 数据库文件：`data/metrics/history.db`
- 报告存储目录：`data/reports`

## 集成到主应用

历史数据分析模块已与主应用集成，在系统状态栏中添加了内存监控指示器，点击可打开历史数据分析仪表盘。

## 性能考虑

历史数据分析模块设计为轻量级，对系统性能影响最小：

1. 采用SQLite作为数据存储，无需额外的数据库服务器
2. 数据采集默认间隔为5分钟，可根据需要调整
3. 采用多线程设计，不会阻塞主应用程序
4. 报告生成任务在后台运行，不影响用户操作
5. 数据库使用索引优化查询性能

## 故障排除

### 常见问题

1. **无法启动数据采集**：
   - 检查是否有足够的磁盘空间
   - 确保有data目录的写入权限

2. **报告生成失败**：
   - 检查是否有足够的数据点（至少需要1天的数据）
   - 查看日志获取详细错误信息

3. **仪表盘无法启动**：
   - 确保已安装PyQt6和pyqtgraph
   - 检查是否有窗口系统支持（远程服务器可能不支持图形界面）

### 日志位置

日志文件存储在：`logs/monitor.log`

## 未来计划

1. 增加更多的性能指标监控
2. 改进机器学习算法，提高OOM预测准确率
3. 添加更多可视化图表类型
4. 开发监控系统整体健康评分系统

## 贡献指南

如果您想为历史数据分析模块做出贡献，请：

1. 遵循现有的代码结构和命名规范
2. 确保新功能不会增加过多的系统资源消耗
3. 为新功能添加适当的文档和测试
4. 提交合并请求前先在低资源环境中测试性能影响 