# 引用完整性检查模块

本模块提供了一组用于验证XML中资源引用完整性的工具，确保所有引用都指向有效的资源，ID格式正确且唯一，没有孤立资源，并且引用关系没有循环。这是VisionAI-ClipsMaster导出工作流程的关键组件，用于确保导出内容的引用完整性。

## 功能概述

- 验证所有clip元素引用的资源ID存在
- 验证所有资源ID格式正确且唯一
- 检测未被引用的孤立资源
- 检测引用循环
- 提供自动修复功能，包括创建缺失资源和移除孤立资源

## 主要函数

### 资源引用验证

```python
from src.exporters.reference_checker import check_asset_references

# 检查所有clip引用的asset是否存在
try:
    check_asset_references(xml_root)
    print("所有clip引用的asset存在")
except ReferenceError as e:
    print(f"引用错误: {str(e)}")
```

### ID唯一性验证

```python
from src.exporters.reference_checker import check_id_uniqueness

# 验证所有ID唯一性
try:
    check_id_uniqueness(xml_root)
    print("所有ID唯一性验证通过")
except ReferenceError as e:
    print(f"ID唯一性错误: {str(e)}")
```

### 孤立资源检查

```python
from src.exporters.reference_checker import check_orphaned_assets

# 检查未被引用的孤立资源
orphaned = check_orphaned_assets(xml_root)
if orphaned:
    print("发现孤立资源:")
    for asset_type, ids in orphaned.items():
        print(f"  {asset_type}: {', '.join(ids)}")
else:
    print("未发现孤立资源")
```

### 引用循环检测

```python
from src.exporters.reference_checker import check_reference_cycles

# 检查引用循环
cycles = check_reference_cycles(xml_root)
if cycles:
    print("发现引用循环:")
    for cycle in cycles:
        print(f"  {' -> '.join(cycle)}")
else:
    print("未发现引用循环")
```

### 综合引用完整性验证

```python
from src.exporters.reference_checker import check_reference_integrity

# 全面验证XML文件引用完整性
result = check_reference_integrity("path/to/file.xml", strict=False)

if result["valid"]:
    print("引用完整性验证通过")
else:
    print("引用完整性验证失败:")
    for error in result["errors"]:
        print(f"  错误: {error}")
    
    if result["warnings"]:
        print("警告:")
        for warning in result["warnings"]:
            print(f"  警告: {warning}")
```

### 引用问题自动修复

```python
from src.exporters.reference_checker import fix_missing_references, remove_orphaned_assets

# 修复缺失引用
fixed, fixed_path = fix_missing_references("path/to/file.xml")
if fixed:
    print(f"缺失引用已修复，保存到: {fixed_path}")

# 移除孤立资源
fixed, fixed_path = remove_orphaned_assets("path/to/file.xml")
if fixed:
    print(f"孤立资源已移除，保存到: {fixed_path}")
```

### 综合验证与修复

```python
from src.exporters.reference_checker import validate_references

# 验证并自动修复XML文件的引用完整性问题
result = validate_references("path/to/file.xml", auto_fix=True, strict=False)

if result["valid"]:
    if "fixed" in result and result["fixed"]:
        print("引用问题已自动修复，验证通过")
    else:
        print("引用完整性验证通过")
else:
    print("引用完整性验证失败，无法自动修复")
```

## 命令行使用

该模块也可以作为独立脚本使用:

```bash
python -m src.exporters.reference_checker path/to/file.xml --fix --strict
```

参数说明:
- `--fix`: 自动修复引用问题
- `--strict`: 使用严格验证模式（孤立资源也被视为错误）
- `--output`: 指定修复后的输出文件路径

## 返回值格式

验证函数通常返回包含详细信息的字典:

```python
{
    "valid": True/False,         # 验证是否通过
    "errors": [],                # 错误列表
    "warnings": [],              # 警告列表
    "orphaned_assets": {},       # 孤立资源信息
    "fixed": True/False          # 是否进行了修复（仅在auto_fix=True时）
}
```

## 集成到其他模块

引用完整性检查可以集成到导出前验证流程中:

```python
from src.exporters.reference_checker import validate_references

def validate_before_export(xml_path):
    # 进行引用完整性验证
    ref_result = validate_references(xml_path, auto_fix=True)
    
    if not ref_result["valid"]:
        raise Exception("引用完整性验证失败，无法导出")
    
    # 继续其他验证和导出步骤...
``` 