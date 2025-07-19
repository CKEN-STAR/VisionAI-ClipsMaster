# VisionAI-ClipsMaster 安全访问控制

本文档详细介绍了VisionAI-ClipsMaster项目的安全访问控制系统，包括黄金样本保护、权限管理和审计功能。

## 1. 概述

VisionAI-ClipsMaster的安全访问控制系统旨在提供以下关键功能：

1. **黄金样本保护**：防止重要测试数据被意外修改
2. **文件权限管理**：确保文件具有适当的访问权限
3. **完整性验证**：通过哈希验证确保文件未被篡改
4. **安全审计**：记录所有安全相关操作，便于追踪
5. **Git集成**：使用Git属性和钩子增强版本控制安全性

该系统支持多平台（Windows、Linux、macOS），并通过权限分级确保正确的访问控制。

## 2. 安全访问控制模块

### 2.1 核心组件

安全访问控制系统由以下核心组件组成：

* **AccessControl**：主要访问控制管理器，处理权限和完整性验证
* **AuditLogger**：安全审计日志记录器，记录所有安全事件
* **Git钩子**：在Git操作前自动执行安全检查
* **命令行工具**：方便管理安全设置的CLI工具

### 2.2 文件目录结构

```
src/
  ├── security/
  │   ├── __init__.py           # 模块初始化
  │   └── access_control.py     # 核心访问控制逻辑
  └── cli/
      └── secure_samples.py     # 安全命令行工具
      
scripts/
  ├── install_git_hooks.py      # Git钩子安装脚本
  ├── secure_tests.sh           # Linux/macOS安全脚本
  └── secure_tests.bat          # Windows安全脚本
  
tests/
  └── unit/
      └── test_security_access_control.py  # 安全模块测试
```

## 3. 黄金样本保护

### 3.1 权限控制

黄金样本目录（`tests/golden_samples/`）受到特殊保护：

* **Linux/macOS**：设置为只读权限（`550` - `r-xr-x---`）
* **Windows**：设置为只读属性
* **访问控制**：防止未经授权的更改

### 3.2 完整性验证

系统使用多种机制确保黄金样本的完整性：

* **哈希验证**：每个样本文件都有对应的SHA-256哈希
* **自动验证**：Git钩子在提交/推送前自动验证完整性
* **手动验证**：可随时使用CLI工具验证完整性

### 3.3 Git集成

为了进一步保护黄金样本，系统与Git集成：

* **.gitattributes**：标记黄金样本文件为不可差异比较
* **Git钩子**：在提交前自动检查黄金样本更改
* **过滤器**：使用哈希过滤器处理敏感文件

## 4. 使用指南

### 4.1 设置安全权限

设置黄金样本目录的安全权限：

```bash
# 使用CLI工具
python -m src.cli.secure_samples secure

# 强制修改权限（如果遇到权限问题）
python -m src.cli.secure_samples secure --force
```

### 4.2 验证黄金样本完整性

验证黄金样本的完整性：

```bash
# 使用CLI工具
python -m src.cli.secure_samples verify

# 忽略错误（仅用于调试）
python -m src.cli.secure_samples verify --ignore-errors
```

### 4.3 安装Git钩子

安装Git钩子以自动保护黄金样本：

```bash
# 使用CLI工具
python -m src.cli.secure_samples hooks

# 或直接运行安装脚本
python scripts/install_git_hooks.py
```

### 4.4 查看安全审计日志

查看安全相关操作的审计日志：

```bash
# 显示最近20条日志
python -m src.cli.secure_samples logs

# 显示详细信息
python -m src.cli.secure_samples logs --verbose

# 限制显示数量
python -m src.cli.secure_samples logs --limit 10
```

## 5. 黄金样本管理流程

为了安全地管理黄金样本，请遵循以下流程：

1. **生成新样本**：使用专用工具生成样本
   ```bash
   python -m tests.golden_samples.manage_golden --new "样本描述"
   ```

2. **审查样本**：审查生成的样本，确保质量和安全性

3. **批准样本**：使用管理员权限批准样本（需要管理员权限）
   ```bash
   # Windows (管理员权限)
   python -m tests.golden_samples.manage_golden --approve sample_id
   
   # Linux/macOS (sudo)
   sudo python -m tests.golden_samples.manage_golden --approve sample_id
   ```

4. **验证完整性**：确认样本已正确添加并通过完整性检查
   ```bash
   python -m src.cli.secure_samples verify
   ```

## 6. 安全最佳实践

在使用VisionAI-ClipsMaster时，请遵循以下安全最佳实践：

1. **不直接修改黄金样本**：始终使用管理工具修改黄金样本
2. **定期验证完整性**：定期运行完整性检查
3. **检查审计日志**：定期查看安全审计日志
4. **正确设置权限**：确保目录和文件具有正确的权限
5. **使用Git钩子**：始终使用Git钩子保护代码库
6. **多人审查**：重要的黄金样本更改需要多人审查

## 7. 故障排除

### 7.1 权限问题

如果遇到权限问题：

```bash
# 强制设置权限
python -m src.cli.secure_samples secure --force

# 检查用户是否有足够权限
# Windows：确保以管理员身份运行
# Linux/macOS：尝试使用sudo
```

### 7.2 Git钩子问题

如果Git钩子不工作：

```bash
# 重新安装Git钩子
python -m src.cli.secure_samples hooks

# 检查钩子是否可执行（Linux/macOS）
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/pre-push
```

### 7.3 完整性验证失败

如果完整性验证失败：

1. 检查错误信息，了解哪些文件有问题
2. 查看审计日志，了解最近的更改
3. 从上一个已知好的版本恢复文件
4. 如果是预期的更改，使用管理工具更新哈希

## 8. 开发者指南

如需扩展安全访问控制系统，请参考以下指南：

### 8.1 添加新的安全功能

1. 在`src/security/access_control.py`中添加新方法
2. 在单元测试中添加相应的测试
3. 更新文档，说明新功能的使用方法

### 8.2 修改权限规则

权限规则在`scripts/secure_test_permissions.py`中定义，可根据需要修改。

### 8.3 添加新的审计事件

在`AuditLogger`类中添加新的事件类型，确保正确记录所有安全相关操作。

## 9. 参考

* [Git属性文档](https://git-scm.com/docs/gitattributes)
* [文件权限最佳实践](https://en.wikipedia.org/wiki/File_system_permissions)
* [VisionAI-ClipsMaster测试指南](./TEST_SECURITY.md) 