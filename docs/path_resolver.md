# 跨平台路径解析模块

## 概述

跨平台路径解析模块(`src/config/path_resolver.py`)提供了一系列工具函数，用于在不同操作系统(Windows/macOS/Linux)之间处理路径标记和转换，确保应用程序的路径操作在任何环境下都能正确运行。

## 特性

- **特殊路径标记解析**：解析`~`、`%USERPROFILE%`、`$HOME`和`${VAR}`等特殊路径标记
- **路径存在性确认**：确保目录存在，需要时自动创建
- **跨平台路径转换**：处理不同平台的路径分隔符(`\`vs`/`)
- **应用数据目录**：获取适合当前平台的应用数据存储目录
- **相对路径计算**：计算相对路径和判断子路径关系
- **项目根目录探测**：智能查找项目根目录

## 使用示例

### 导入模块

```python
# 方法1: 直接从模块导入
from src.config.path_resolver import resolve_special_path, ensure_dir_exists, normalize_path

# 方法2: 从配置模块导入
from src.config import resolve_special_path, ensure_dir_exists, normalize_path
```

### 解析特殊路径标记

```python
# 解析用户主目录
user_docs = resolve_special_path("~/Documents")
print(f"用户文档目录: {user_docs}")

# 解析环境变量(Windows)
temp_dir = resolve_special_path("%TEMP%")
print(f"临时目录: {temp_dir}")

# 解析环境变量(Unix/Linux)
home_dir = resolve_special_path("$HOME")
print(f"用户主目录: {home_dir}")

# 解析${VAR}形式的环境变量
path_var = resolve_special_path("${PATH}")
print(f"PATH环境变量: {path_var}")
```

### 确保目录存在

```python
# 确保多级目录存在
data_dir = ensure_dir_exists("~/AppData/VisionAI/data")
print(f"数据目录: {data_dir}")
```

### 获取应用数据目录

```python
# 获取应用数据目录(跨平台)
app_data = get_app_data_dir("MyApp")
print(f"应用数据目录: {app_data}")
# Windows: C:\Users\<用户>\AppData\Roaming\MyApp
# macOS: /Users/<用户>/Library/Application Support/MyApp
# Linux: /home/<用户>/.config/MyApp
```

### 获取临时目录

```python
# 获取进程特定的临时目录
temp_dir = get_temp_dir("myapp_")
print(f"临时目录: {temp_dir}")
# 例如: C:\Users\<用户>\AppData\Local\Temp\myapp_12345
```

### 获取项目根目录

```python
# 获取项目根目录
root_dir = get_project_root()
print(f"项目根目录: {root_dir}")

# 构建项目内部文件路径
config_file = join_paths(root_dir, "configs", "settings.yaml")
print(f"配置文件: {config_file}")
```

### 标准化路径

```python
# 标准化路径分隔符和特殊标记
path = normalize_path("path/to/file")
print(f"标准化路径: {path}")
# Windows: C:\path\to\file
# Unix/Linux: /path/to/file
```

### 处理相对路径

```python
# 计算相对路径
rel_path = get_relative_path("/path/to/file.txt", "/path")
print(f"相对路径: {rel_path}")  # 输出: to/file.txt

# 检查子路径关系
is_sub = is_subpath("/path/to/file.txt", "/path")
print(f"是子路径: {is_sub}")  # 输出: True
```

### 连接路径

```python
# 连接并标准化多个路径部分
full_path = join_paths("~/Documents", "projects", "myproject")
print(f"完整路径: {full_path}")
```

## 主要函数参考

### `resolve_special_path(raw_path)`

将路径中的特殊标记解析为实际路径。

**参数**:
- `raw_path` (str): 原始路径字符串

**返回**:
- 解析后的绝对路径

### `ensure_dir_exists(path)`

确保目录存在，如果不存在则创建。

**参数**:
- `path` (str): 目录路径

**返回**:
- 目录的绝对路径

### `get_app_data_dir(app_name)`

获取应用数据目录，根据不同操作系统返回适当的路径。

**参数**:
- `app_name` (str): 应用名称

**返回**:
- 应用数据目录的绝对路径

### `get_temp_dir(prefix)`

获取临时目录。

**参数**:
- `prefix` (str): 临时目录前缀

**返回**:
- 临时目录的绝对路径

### `get_project_root()`

获取项目根目录路径。

**返回**:
- 项目根目录的Path对象

### `normalize_path(path)`

标准化路径，解析特殊标记并转换为平台适用的格式。

**参数**:
- `path` (str): 原始路径

**返回**:
- 标准化后的路径

### `get_relative_path(path, base_path)`

获取相对于指定基准路径的相对路径。

**参数**:
- `path` (str): 目标路径
- `base_path` (str): 基准路径，默认为项目根目录

**返回**:
- 相对路径

### `is_subpath(path, parent_path)`

检查路径是否是另一个路径的子路径。

**参数**:
- `path` (str): 要检查的路径
- `parent_path` (str): 父路径

**返回**:
- 如果path是parent_path的子路径则返回True

### `join_paths(*paths)`

连接多个路径部分，并标准化结果。

**参数**:
- `*paths` (str): 要连接的路径部分

**返回**:
- 连接并标准化后的路径

## 演示脚本

项目中包含了一个演示脚本，可以用来测试和理解这些功能：

```
python src/demos/path_resolver_demo.py
```

也可以运行特定功能的演示：

```
python src/demos/path_resolver_demo.py --special  # 演示特殊路径解析
python src/demos/path_resolver_demo.py --platform  # 演示跨平台路径转换
python src/demos/path_resolver_demo.py --app-paths  # 演示应用路径
``` 