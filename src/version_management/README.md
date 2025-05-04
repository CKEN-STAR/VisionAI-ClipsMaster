# 模式版本管理系统

模式版本管理系统负责管理和维护不同版本的叙事模式模型和配置，支持版本之间的切换、比较和元数据管理。

## 功能特性

- 版本创建与管理：支持创建新版本、查看可用版本和切换当前版本
- 版本元数据：记录版本信息、创建日期、作者、数据信息和兼容性
- 版本比较：对比不同版本间的配置和元数据差异
- 配置管理：为不同版本维护独立的配置文件
- 模型管理：为不同版本维护独立的模型文件
- 平台适配：针对不同平台（抖音、快手、YouTube等）的优化参数

## 目录结构

```
models/narrative_patterns/
  ├── v1.0/                  # 版本1.0目录
  │   ├── metadata.json      # 版本元数据
  │   ├── pattern_config.yaml # 模式配置
  │   └── fp-growth.model    # 模型文件
  ├── v1.1/                  # 版本1.1目录
  │   ├── metadata.json 
  │   ├── pattern_config.yaml
  │   └── fp-growth.model
  └── latest/                # 当前版本链接
      ├── metadata.json
      ├── pattern_config.yaml
      └── current_version.txt
```

## 使用方法

### 1. 创建新版本

```python
from src.version_management.pattern_version_manager import create_new_version

# 创建新版本
create_new_version(
    version_name="v1.2", 
    description="增强版模式库", 
    author="开发者", 
    base_version="v1.1"
)
```

### 2. 切换版本

```python
from src.version_management.pattern_version_manager import set_current_version

# 切换到指定版本
set_current_version("v1.1")
```

### 3. 获取版本信息

```python
from src.version_management.pattern_version_manager import get_version_metadata

# 获取当前版本的元数据
metadata = get_version_metadata()

# 获取指定版本的元数据
metadata = get_version_metadata("v1.0")
```

### 4. 获取版本配置

```python
from src.version_management.pattern_version_manager import get_pattern_config

# 获取当前版本配置
config = get_pattern_config()

# 获取指定版本配置
config = get_pattern_config("v1.0")
```

### 5. 比较版本差异

```python
from src.version_management.pattern_version_manager import compare_versions

# 比较两个版本的差异
diff = compare_versions("v1.0", "v1.1")
```

## 简化集成

为了简化集成，可以使用`src.utils.pattern_loader`模块：

```python
from src.utils.pattern_loader import (
    get_current_pattern_config,
    get_recommended_combinations,
    get_pattern_parameters,
    get_evaluation_weights,
    get_version_info,
    switch_pattern_version
)

# 获取当前版本信息
version_info = get_version_info()

# 获取当前配置
config = get_current_pattern_config()

# 获取特定模式类型的参数
opening_params = get_pattern_parameters("opening")

# 切换版本
switch_pattern_version("v1.0")
```

## 示例脚本

- `demo_pattern_version_manager.py`：完整功能演示
- `demo_pattern_version_simple.py`：简化集成演示 