# 配置系统测试套件

本目录包含了VisionAI-ClipsMaster项目配置系统的全面测试套件。

## 测试概述

配置系统测试套件验证以下功能：

1. **基本配置操作**：加载、保存、更新和访问配置
2. **配置验证**：确保配置数据符合预期格式和约束
3. **热重载功能**：检测配置文件变化并自动重新加载
4. **安全存储**：敏感配置数据的加密存储和检索
5. **配置迁移**：版本间的配置数据结构迁移
6. **路径解析**：配置中路径变量的解析
7. **环境变量覆盖**：通过环境变量覆盖配置值

## 测试文件

- **test_config.py**: 全面测试套件，包含所有测试类
- **test_config_lifecycle.py**: 简单的配置生命周期测试
- **run_config_tests.py**: 运行所有配置测试的脚本

## 运行测试

### 运行所有测试

```bash
python -m tests.config_test.run_config_tests
```

### 运行单个测试类

```bash
python -m tests.config_test.run_config_tests --test TestConfigLifecycle
```

### 增加输出详细级别

```bash
python -m tests.config_test.run_config_tests -v
```

### 生成测试报告

```bash
python -m tests.config_test.run_config_tests --report
```

## 测试类说明

### TestConfigLifecycle

测试配置的基本生命周期，包括保存、加载和更新配置。

### TestHotReload

测试配置热重载功能，验证当配置文件变化时，系统能自动检测并重新加载配置。

### TestSecureStorage

测试安全存储功能，验证敏感配置数据的加密存储和检索。

### TestConfigMigration

测试配置迁移功能，验证在配置格式版本变化时，能正确迁移旧版本配置。

### TestPathResolver

测试路径解析器，验证配置中包含的路径变量能正确解析。

### TestEnvAdapter

测试环境变量适配器，验证能通过环境变量覆盖配置值。

## 添加新测试

要添加新的测试，请遵循以下步骤：

1. 在适当的测试文件中创建新的测试类或测试方法
2. 在 `run_config_tests.py` 中注册新的测试类
3. 确保新测试可在隔离环境中运行，不依赖特定的系统状态
4. 运行新测试以确保它正常工作 