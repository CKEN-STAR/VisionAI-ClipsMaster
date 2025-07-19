# VisionAI-ClipsMaster 语言包热加载指南

本文档介绍了VisionAI-ClipsMaster中语言包热加载功能的使用方法和技术细节。

## 概述

语言包热加载功能允许在不重启应用程序的情况下，实时更新语言资源文件并立即应用变更。这对于以下场景特别有用：

- 开发过程中测试翻译
- 修正语言资源中的错误
- 添加新的翻译条目
- 调整界面文本

热加载系统会自动监控语言资源文件的变更，并在检测到修改后立即重新加载资源并更新界面。

## 主要特性

- **实时监控文件变更**：监视translations目录下的语言文件
- **自动重新加载**：检测到变更后自动重新加载资源
- **实时更新UI**：无需重启应用即可看到变更效果
- **防抖处理**：避免频繁刷新导致的性能问题
- **自动备份**：在更新前自动备份原始文件
- **变更通知**：提供回调机制，通知应用程序语言资源已更新

## 使用方法

### 基本用法

```python
from ui.i18n import get_hot_reload_manager

# 获取热加载管理器实例
hot_reload = get_hot_reload_manager()

# 热加载管理器会自动监视translations目录下的语言文件
# 无需其他配置即可运行
```

### 注册重载回调

```python
from ui.i18n import register_reload_callback

# 注册语言重新加载回调函数
def on_language_reloaded(lang_code):
    print(f"语言 {lang_code} 已被重新加载")
    # 执行UI更新操作
    
register_reload_callback(on_language_reloaded)
```

### 创建新的语言文件

```python
from ui.i18n import create_language_file

# 创建新的语言资源文件
file_path = create_language_file("fr_FR")
if file_path:
    print(f"已创建法语资源文件: {file_path}")
```

### 手动获取被监视的文件

```python
from ui.i18n import get_hot_reload_manager

hot_reload = get_hot_reload_manager()
watched_files = hot_reload.get_watched_files()

print(f"当前监视的文件数: {len(watched_files)}")
for file in watched_files:
    print(f"- {file}")
```

## 工作原理

语言包热加载功能基于以下工作流程：

1. **初始化**：创建`QFileSystemWatcher`实例，监视translations目录及其中的语言文件
2. **监控变更**：监听文件和目录变更事件
3. **防抖处理**：使用定时器防抖，避免频繁重新加载
4. **文件备份**：变更前创建带时间戳的备份文件
5. **重新加载**：根据文件类型（JSON或QM）采取不同的加载策略
6. **发送通知**：通过信号机制通知应用程序变更已应用

### 文件监视

系统会监视以下类型的变更：
- **文件修改**：编辑现有语言文件内容
- **文件创建**：在translations目录下创建新的语言文件
- **文件删除**：删除不再需要的语言文件

### 防抖机制

为了避免频繁的文件保存操作导致多次重新加载，系统实现了防抖机制：
- 检测到变更后，系统不会立即重新加载
- 启动3秒倒计时定时器
- 3秒内如有新的变更，重置定时器
- 定时器结束后才执行实际的重新加载操作

### 备份策略

系统会在重新加载前自动创建语言文件备份：
- 备份存储在`translations/backups`目录下
- 文件名格式为`{原文件名}_{时间戳}.{扩展名}`（例如：`zh_CN_20250624_103045.json`）
- 保留完整的修改历史，便于恢复之前的版本

## 支持的文件类型

语言包热加载功能支持以下类型的语言资源文件：

| 文件类型 | 描述 | 处理方式 |
|--------|------|---------|
| JSON | 纯文本格式的语言资源文件 | 解析JSON并更新内存中的资源 |
| QM | Qt编译后的二进制翻译文件 | 通知Qt翻译系统重新加载 |

## 使用最佳实践

### 1. 编辑语言文件

建议使用以下方法编辑语言资源文件：

- **通过演示程序**：使用`hot_reload_demo.py`内置的编辑器
- **使用外部编辑器**：使用支持JSON语法高亮的编辑器（如VS Code）
- **确保有效的JSON**：编辑完成后验证JSON格式是否有效

### 2. 调整更新频率

根据需要调整防抖定时器延迟：

```python
# 设置更长的防抖延迟（例如5秒）
hot_reload = get_hot_reload_manager()
hot_reload.reload_timer.setInterval(5000)
```

### 3. 添加新的翻译键

向现有语言文件添加新的翻译键时：

- 确保键名符合项目命名规范
- 添加完整的翻译内容，不要留空
- 确保新键添加到正确的嵌套级别

### 4. 备份管理

系统会自动创建备份，但建议定期清理备份目录：

```python
import os
import shutil

# 清理超过30天的备份文件
backup_dir = "ui/i18n/translations/backups"
for backup in os.listdir(backup_dir):
    backup_path = os.path.join(backup_dir, backup)
    file_age = (time.time() - os.path.getmtime(backup_path)) / 86400  # 转换为天
    if file_age > 30:
        os.remove(backup_path)
```

## 调试提示

如果热加载功能未正常工作，请检查以下几点：

1. **文件权限**：确保应用程序有权读写语言文件
2. **文件格式**：验证JSON文件格式是否有效
3. **文件编码**：确保使用UTF-8编码保存文件
4. **监视状态**：检查文件是否在被监视列表中
5. **系统限制**：某些操作系统对文件监视有限制，可能需要调整

## 演示程序

项目提供了完整的演示程序`hot_reload_demo.py`，展示语言包热加载功能的各个方面：

- 查看和管理语言文件
- 监控被监视的文件
- 编辑语言资源
- 测试热加载效果

运行演示程序：

```bash
python hot_reload_demo.py
```

## 实现细节

语言包热加载功能通过以下技术实现：

- **QFileSystemWatcher**：Qt提供的文件系统监视器
- **Signal/Slot机制**：用于通知语言变更
- **JSON解析**：处理语言资源文件
- **定时器防抖**：避免频繁重新加载

核心类和函数位于`ui/i18n/hot_reload.py`文件中：

- `LanguageHotReload`：主要类，提供热加载功能
- `get_hot_reload_manager()`：获取单例实例
- `create_language_file()`：创建新的语言文件
- `register_reload_callback()`：注册变更回调 