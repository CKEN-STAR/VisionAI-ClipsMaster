# 质量看板集成

VisionAI-ClipsMaster 项目的质量看板集成模块提供了将质量数据实时更新到各种可视化平台的功能，支持监控系统的运行状态、性能指标和质量门限达成情况。

## 主要功能

1. **多平台支持**：
   - Kibana：用于详细日志和事件分析
   - Grafana：用于性能指标和时间序列可视化
   - PowerBI：用于业务报表和决策支持
   - 本地仪表板：免配置的基本可视化方案

2. **实时质量分数**：
   - 单元测试覆盖率和通过率
   - 性能指标监控（响应时间、内存使用）
   - 合规性指标跟踪

3. **历史趋势对比**：
   - 支持查看历史数据和趋势分析
   - 自动生成时间序列数据

4. **模块健康度热力图**：
   - 直观展示各模块的健康状态
   - 快速定位问题区域

## 设置与配置

### 配置文件

配置文件位于 `configs/dashboard_config.json`，包含各平台的连接设置：

```json
{
  "kibana": {
    "enabled": false,
    "url": "http://localhost:5601",
    "index": "visionai-quality-metrics",
    "api_key": ""
  },
  "grafana": {
    "enabled": false,
    "url": "http://localhost:3000",
    "api_key": "",
    "dashboard_uid": "visionai-quality"
  },
  "powerbi": {
    "enabled": false,
    "dataset_id": "visionai-quality-dataset",
    "workspace_id": "",
    "api_key": ""
  },
  "local_dashboard": {
    "enabled": true,
    "update_interval": 300,
    "history_retention_days": 30,
    "dashboard_path": "reports/dashboard"
  }
}
```

### Kibana 配置

1. 在 Kibana 中创建索引模式 `visionai-quality-metrics*`
2. 创建可视化和仪表板，展示关键指标
3. 在配置文件中启用 Kibana 集成并设置 API 密钥

### Grafana 配置

1. 安装 Grafana 并创建数据源（通常指向 Elasticsearch）
2. 导入项目提供的 Grafana 仪表板模板
3. 在配置文件中启用 Grafana 集成并设置 API 密钥

### PowerBI 配置

1. 在 PowerBI 中创建工作区和数据集
2. 建立报表和仪表板
3. 在配置文件中启用 PowerBI 集成并设置工作区 ID 和 API 密钥

### 本地仪表板

无需额外设置，默认启用，将在 `reports/dashboard` 目录生成 JSON 格式的数据文件。

## 使用方法

### 命令行运行

```bash
# 收集数据并更新所有仪表板
python -m tests.reporting.dashboard_integration --collect

# 显示仪表板连接状态
python -m tests.reporting.dashboard_integration --status

# 使用指定数据文件更新仪表板
python -m tests.reporting.dashboard_integration --data-file path/to/data.json

# 使用自定义配置文件
python -m tests.reporting.dashboard_integration --config-file path/to/config.json
```

### 代码集成

```python
from tests.reporting.dashboard_integration import update_quality_dashboard, collect_and_update_dashboard

# 方法 1: 自动收集数据并更新仪表板
results = collect_and_update_dashboard()

# 方法 2: 使用自定义数据更新仪表板
data = {
    "unit_test": {
        "coverage": 95.0,
        "pass_rate": 100
    },
    "performance": {
        "response_time": 7500,
        "memory_usage": 3500
    },
    "compliance": {
        "privacy": 98.5,
        "legal": 100
    }
}

results = update_quality_dashboard(data)
```

## 监控最佳实践

1. **定期更新**：
   - 设置 CI/CD 流程在每次构建后更新质量数据
   - 生产环境中实现自动定时更新

2. **阈值和告警**：
   - 在 Grafana/Kibana 中设置关键指标的阈值告警
   - 配置邮件或消息通知

3. **数据保留**：
   - 定期备份历史数据
   - 针对不同指标设置合理的数据保留期

4. **安全与访问控制**：
   - 限制仪表板的访问权限
   - 定期轮换 API 密钥

## 故障排除

### 常见问题

1. **无法连接到外部服务**
   - 检查网络连接和防火墙设置
   - 验证 API 密钥和权限设置

2. **数据不显示**
   - 检查数据收集模块是否正常运行
   - 确认数据格式符合预期

3. **权限错误**
   - 确保 API 密钥具有写入权限
   - 检查用户角色和授权设置

### 日志和调试

查看日志文件以获取详细错误信息：

```bash
cat logs/dashboard_integration.log
```

## 定制开发

### 添加新的可视化平台

1. 在 `dashboard_integration.py` 中实现新连接器类或方法
2. 在配置文件中添加相应的配置项
3. 更新文档和测试

### 自定义数据转换

根据需要修改以下方法以自定义数据格式:

- `_format_for_kibana`
- `_format_for_grafana`
- `_format_for_powerbi` 