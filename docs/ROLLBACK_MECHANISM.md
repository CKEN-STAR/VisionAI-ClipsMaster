# 异常回滚机制

## 概述

VisionAI-ClipsMaster 异常回滚机制提供了在XML文件操作失败时的安全保障功能。当系统执行关键操作（如修改XML文件、添加片段、更新项目设置等）时，会自动备份原始状态，并在操作失败时恢复到初始状态，确保数据一致性和系统稳定性。

## 功能特点

- **自动备份**：操作前自动创建文件备份
- **异常检测**：捕获操作过程中的各类异常
- **自动恢复**：检测到问题时自动回滚到原始状态
- **验证机制**：确保生成的XML文件格式正确
- **装饰器模式**：通过简单的装饰器应用到任何XML操作函数
- **多级回滚**：支持内存回滚和文件回滚双重保障

## 组件介绍

### 1. LegalRollback

最基础的回滚类，保存原始XML内容并提供恢复功能。

```python
# 使用示例
from src.export.rollback_manager import LegalRollback

# 创建回滚对象
rollback = LegalRollback(original_xml)

# 在操作失败时恢复
rollback.restore("output.xml")
```

### 2. FileRollbackManager

通用文件回滚管理器，支持任意类型文件的备份和恢复。

```python
# 使用示例
from src.export.rollback_manager import FileRollbackManager

manager = FileRollbackManager()

# 备份文件
backup_path = manager.backup_file("project.xml")

# 恢复文件
manager.restore_file("project.xml")

# 清理过期备份
manager.cleanup_backup(max_age_days=7)
```

### 3. XMLRollbackManager

专门针对XML文件操作的回滚管理器，提供内容验证和更强大的回滚功能。

```python
# 使用示例
from src.export.rollback_manager import XMLRollbackManager

manager = XMLRollbackManager()

# 备份XML
manager.backup_xml_content("project.xml")

# 验证XML有效性
is_valid = manager.verify_xml("project.xml")

# 恢复XML
manager.restore_xml_content("project.xml")
```

### 4. with_xml_rollback 装饰器

最常用的功能，通过装饰器模式为XML操作函数添加自动回滚功能。

```python
# 使用示例
from src.export.rollback_manager import with_xml_rollback

@with_xml_rollback
def modify_xml_file(xml_path):
    # 修改XML的代码
    # 如果发生异常或生成无效XML，将自动回滚
    pass
```

### 5. 便捷函数

提供了一系列简单的函数接口，便于直接使用回滚功能。

```python
# 使用示例
from src.export.rollback_manager import backup_xml, restore_xml, backup_file, restore_file, cleanup_backups

# 备份XML
backup_xml("project.xml")

# 恢复XML
restore_xml("project.xml")

# 清理过期备份
cleanup_backups(max_age_days=7)
```

## 在XMLUpdater中的应用

XML更新器已集成回滚机制，所有主要操作函数都应用了`@with_xml_rollback`装饰器：

- `append_clip`：添加单个片段
- `append_clips`：批量添加多个片段
- `add_resource`：添加资源
- `change_project_settings`：修改项目设置

这意味着，当使用XML更新器执行这些操作时，系统会自动处理备份和恢复，无需手动干预。

## 工作原理

1. **装饰器拦截**：`with_xml_rollback`装饰器拦截函数调用
2. **前置备份**：在执行操作前，自动备份XML文件
3. **执行操作**：调用原始函数执行实际操作
4. **验证结果**：检查操作结果，验证XML有效性
5. **异常处理**：捕获所有异常并记录日志
6. **自动回滚**：如果发生异常或XML无效，自动恢复到原始状态

## 高级应用

### 自定义回滚逻辑

可以创建继承自`XMLRollbackManager`的自定义类，实现特定的回滚逻辑：

```python
class CustomRollbackManager(XMLRollbackManager):
    def before_backup(self, xml_path):
        # 在备份前执行自定义逻辑
        pass
        
    def after_restore(self, xml_path):
        # 在恢复后执行自定义逻辑
        pass
```

### 批处理回滚

当处理多个文件时，可以使用事务性操作模式：

```python
# 伪代码示例
manager = XMLRollbackManager()
files_to_process = ["file1.xml", "file2.xml", "file3.xml"]

# 备份所有文件
backups = [manager.backup_xml_content(f) for f in files_to_process]

try:
    # 执行批量操作
    for file in files_to_process:
        process_file(file)
except Exception:
    # 发生异常时回滚所有文件
    for file in files_to_process:
        manager.restore_xml_content(file)
```

## 最佳实践

1. **始终使用装饰器**：为所有修改XML的函数添加`@with_xml_rollback`装饰器
2. **保持小型操作**：将大型操作拆分为多个小型函数，每个函数都有自己的回滚保护
3. **定期清理备份**：使用`cleanup_backups()`函数定期清理过期备份文件
4. **验证重要操作**：在关键步骤后使用`verify_xml()`确认XML有效性
5. **日志记录**：启用详细日志以便调试回滚相关问题

## 性能考虑

回滚机制会在每次操作前创建备份，这可能对性能有一定影响：

- **文件大小**：对于大型XML文件，备份操作可能较慢
- **频繁操作**：频繁小幅修改可能导致大量备份文件
- **空间占用**：备份文件可能占用较多磁盘空间

为缓解这些问题，建议：

- 合并小操作为较大的操作单元
- 定期清理过期备份
- 对非关键操作禁用回滚机制

## 示例

请参考 `examples/rollback_demo.py` 获取完整的演示示例，展示了：

- 手动回滚操作
- 装饰器自动回滚
- XML更新器集成回滚 