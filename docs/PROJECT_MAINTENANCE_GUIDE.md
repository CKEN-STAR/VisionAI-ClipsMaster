# 项目维护指南

## 概述

本文档提供VisionAI-ClipsMaster项目的日常维护指南，包括测试数据清理、代码质量检查、性能优化等。

---

## 测试数据管理

### 清理测试数据

项目提供了便捷的测试数据清理工具：

```bash
# 清理所有测试数据
python scripts/tools/cleanup_test_data.py --all

# 只清理特定类型的数据
python scripts/tools/cleanup_test_data.py --outputs    # 清理测试输出
python scripts/tools/cleanup_test_data.py --projects   # 清理测试项目
python scripts/tools/cleanup_test_data.py --videos     # 清理测试视频
python scripts/tools/cleanup_test_data.py --reports    # 清理旧报告
```

### 保留的文件

以下文件会被保留：
- `data/output/真实测试项目/`：用于验证剪映导出功能的真实草稿
- 非测试相关的项目文件
- 用户创建的实际项目

---

## 代码质量检查

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest test/test_jianying_export.py

# 运行带覆盖率的测试
pytest --cov=src --cov-report=html
```

### 代码格式化

```bash
# 使用black格式化代码
black src/

# 使用isort整理导入
isort src/

# 使用flake8检查代码质量
flake8 src/
```

---

## 性能优化

### 内存使用监控

```python
from src.utils.memory_monitor import MemoryMonitor

# 创建监控器
monitor = MemoryMonitor()

# 开始监控
monitor.start()

# 执行操作
# ...

# 获取报告
report = monitor.get_report()
print(report)
```

### 性能分析

```bash
# 使用cProfile分析性能
python -m cProfile -o profile.stats simple_ui_fixed.py

# 查看分析结果
python -m pstats profile.stats
```

---

## 日志管理

### 日志位置

- **应用日志**：`logs/app.log`
- **错误日志**：`logs/error.log`
- **性能日志**：`logs/performance.log`

### 日志清理

```bash
# 清理旧日志（保留最近7天）
python tools/cleanup_logs.py --days 7

# 清理所有日志
python tools/cleanup_logs.py --all
```

---

## 依赖管理

### 更新依赖

```bash
# 更新所有依赖到最新版本
pip install --upgrade -r requirements.txt

# 更新特定依赖
pip install --upgrade package_name

# 生成新的requirements.txt
pip freeze > requirements.txt
```

### 检查依赖安全性

```bash
# 使用safety检查依赖安全性
pip install safety
safety check

# 使用pip-audit检查
pip install pip-audit
pip-audit
```

---

## 数据库维护

### 备份数据

```bash
# 备份用户数据
python tools/backup_data.py --output backups/

# 恢复数据
python tools/restore_data.py --input backups/backup_20250105.zip
```

### 清理缓存

```bash
# 清理模型缓存
python tools/cleanup_cache.py --models

# 清理视频缓存
python tools/cleanup_cache.py --videos

# 清理所有缓存
python tools/cleanup_cache.py --all
```

---

## 版本发布

### 发布前检查清单

- [ ] 运行所有测试并确保通过
- [ ] 更新版本号（`__version__.py`）
- [ ] 更新CHANGELOG.md
- [ ] 清理测试数据
- [ ] 检查代码质量
- [ ] 更新文档
- [ ] 创建Git标签

### 发布流程

```bash
# 1. 更新版本号
# 编辑 src/__version__.py

# 2. 提交更改
git add .
git commit -m "Release v1.0.0"

# 3. 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 4. 推送到远程
git push origin main
git push origin v1.0.0

# 5. 创建发布包
python setup.py sdist bdist_wheel
```

---

## 故障排除

### 常见问题

#### 1. 内存不足

**症状**：程序运行缓慢或崩溃

**解决方案**：
```bash
# 使用更小的模型
python simple_ui_fixed.py --model-size Q2_K

# 限制并发数
python simple_ui_fixed.py --max-workers 2
```

#### 2. 模型加载失败

**症状**：提示模型文件不存在

**解决方案**：
```bash
# 重新下载模型
python tools/download_models.py --force

# 检查模型完整性
python tools/verify_models.py
```

#### 3. 视频处理错误

**症状**：视频导出失败

**解决方案**：
```bash
# 检查FFmpeg安装
ffmpeg -version

# 重新安装FFmpeg
# Windows: 下载并安装FFmpeg
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
```

---

## 监控和告警

### 性能监控

```python
from src.utils.performance_monitor import PerformanceMonitor

# 创建监控器
monitor = PerformanceMonitor()

# 监控函数执行
@monitor.track
def process_video(video_path):
    # 处理视频
    pass

# 获取统计信息
stats = monitor.get_stats()
print(stats)
```

### 错误告警

```python
from src.utils.error_handler import ErrorHandler

# 创建错误处理器
handler = ErrorHandler(
    email_alerts=True,
    log_errors=True
)

# 处理错误
try:
    # 执行操作
    pass
except Exception as e:
    handler.handle_error(e)
```

---

## 安全维护

### 定期检查

- [ ] 检查依赖安全性（每月）
- [ ] 更新安全补丁（及时）
- [ ] 审查访问日志（每周）
- [ ] 备份重要数据（每天）

### 安全配置

```python
# config/security.yaml
security:
  enable_encryption: true
  max_file_size: 1GB
  allowed_extensions:
    - .mp4
    - .srt
    - .json
  rate_limiting:
    enabled: true
    max_requests: 100
    time_window: 60  # seconds
```

---

## 文档维护

### 更新文档

- 代码更改后及时更新相关文档
- 保持README.md与实际功能同步
- 更新API文档
- 添加新功能的使用示例

### 文档生成

```bash
# 生成API文档
python tools/generate_docs.py --output docs/api/

# 生成用户手册
python tools/generate_manual.py --output docs/manual/
```

---

## 最佳实践

### 代码提交

- 使用有意义的提交信息
- 每次提交只包含一个逻辑更改
- 提交前运行测试
- 使用分支进行功能开发

### 代码审查

- 所有代码更改都应经过审查
- 检查代码质量和性能
- 确保测试覆盖率
- 验证文档更新

### 性能优化

- 定期进行性能分析
- 优化热点代码
- 减少内存使用
- 提高响应速度

---

## 工具脚本

### 可用工具

| 工具 | 描述 | 使用方法 |
|------|------|---------|
| `cleanup_test_data.py` | 清理测试数据 | `python scripts/tools/cleanup_test_data.py --all` |
| `export_to_jianying.py` | 导出到剪映 | `python scripts/tools/export_to_jianying.py --help` |
| `download_models.py` | 下载AI模型 | `python scripts/tools/download_models.py` |
| `verify_models.py` | 验证模型完整性 | `python scripts/tools/verify_models.py` |
| `backup_data.py` | 备份用户数据 | `python scripts/tools/backup_data.py` |
| `generate_docs.py` | 生成文档 | `python scripts/tools/generate_docs.py` |

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- **GitHub Issues**：https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues
- **Email**：support@visionai-clipsmaster.com
- **文档**：https://visionai-clipsmaster.readthedocs.io/

---

**文档版本**：1.0  
**最后更新**：2025-10-05  
**维护者**：VisionAI-ClipsMaster Team  

