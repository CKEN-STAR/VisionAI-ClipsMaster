# 法律声明更新器

本文档介绍VisionAI-ClipsMaster的法律声明更新器功能，该功能可以自动检查并更新法律声明模板，确保使用最新的法律文本。

## 功能概述

法律声明更新器提供以下功能：

1. **自动检查更新**：定期检查是否有新版本的法律声明模板
2. **自动下载更新**：当发现新版本时，自动下载并应用更新
3. **更新历史记录**：记录所有的更新历史，便于审计和追踪
4. **自定义配置**：可以自定义更新频率、自动更新设置等

## 配置选项

法律声明更新器可以通过以下选项进行配置：

| 配置项 | 描述 | 默认值 |
|-------|-----|-------|
| `auto_update` | 是否自动更新模板 | `True` |
| `check_interval` | 检查更新的间隔（天） | `7` |
| `update_url` | 更新服务器URL | `https://api.visionai-clips.com/legal_templates` |

## 使用方法

### 基本使用

```python
from src.exporters.legal_updater import check_legal_updates

# 自动检查更新（根据配置的间隔时间）
has_update = check_legal_updates()

if has_update:
    print("检测到法律模板更新！")
```

### 强制检查更新

```python
from src.exporters.legal_updater import check_legal_updates

# 强制检查更新（忽略时间间隔）
has_update = check_legal_updates(force=True)

if has_update:
    print("检测到法律模板更新！")
```

### 手动下载更新

```python
from src.exporters.legal_updater import download_new_templates

# 手动下载最新模板
success = download_new_templates()

if success:
    print("已下载最新法律模板")
else:
    print("下载失败")
```

### 高级配置

```python
from src.exporters.legal_updater import legal_watcher

# 设置是否自动更新
legal_watcher.set_auto_update(True)

# 设置检查间隔（天）
legal_watcher.set_check_interval(14)

# 设置更新服务器URL
legal_watcher.set_update_url("https://new-api.example.com/legal")

# 获取更新历史
history = legal_watcher.get_update_history()
for record in history:
    print(f"版本: {record.get('version')}, 时间: {record.get('date')}")
```

## 更新内容

法律声明模板更新可能包括以下内容：

1. **版权声明更新**：更新版权年份和描述
2. **免责声明更新**：根据最新法规要求更新免责声明内容
3. **隐私声明更新**：根据隐私政策变化更新隐私相关声明
4. **使用条款更新**：更新使用条款和限制

## 集成方式

法律声明更新器与系统的其他组件集成如下：

1. **与法律文本加载器集成**：更新后自动重新加载模板
2. **与导出模块集成**：确保导出内容使用最新的法律声明
3. **与系统日志集成**：记录所有更新操作

## 自动更新流程

自动更新的流程如下：

1. 系统启动或定期运行时，调用`check_legal_updates()`检查更新
2. 如果发现新版本且启用了自动更新，下载并应用新模板
3. 更新完成后，系统会自动重新加载法律文本加载器
4. 所有后续操作将使用更新后的法律声明

## 手动更新流程

如果禁用了自动更新，可以使用以下流程手动更新：

1. 调用`check_legal_updates()`检查是否有更新
2. 如果有更新，提示用户是否下载
3. 用户确认后，调用`download_new_templates()`下载更新
4. 更新完成后，系统会自动重新加载法律文本加载器

## 故障排除

如果遇到更新问题，可以尝试以下方法：

1. **检查网络连接**：确保能够连接到更新服务器
2. **检查配置文件**：查看`configs/legal_updater.json`是否正确
3. **手动强制更新**：使用`check_legal_updates(force=True)`强制检查更新
4. **查看日志**：检查日志文件中的相关错误信息

## 注意事项

- 法律声明更新器需要网络连接才能检查和下载更新
- 更新操作会修改`configs/legal_templates.yaml`文件
- 在生产环境中，建议定期检查更新以确保法律合规性
- 如果需要在离线环境使用，可以禁用自动更新功能 