# 法律操作审计日志系统

## 概述

VisionAI-ClipsMaster 项目中的法律操作审计日志系统提供了一个全面的解决方案，用于记录和追踪系统中所有与法律相关的操作。这包括版权声明的注入、免责声明的添加以及水印的应用等。此系统确保所有法律操作可被追踪、审计和验证，提高系统的法律合规性和可问责性。

## 主要功能

- **全面记录**：记录所有法律相关操作，包括操作类型、时间、执行者和内容变化
- **自动化集成**：通过装饰器模式，自动化记录法律操作而无需大量修改代码
- **多级详细度**：支持从简单记录到详细审计的多种日志级别
- **导出功能**：支持将审计日志导出为JSON或CSV格式，便于进一步分析
- **内容变更追踪**：记录操作前后的内容，并计算内容变化的百分比
- **会话跟踪**：使用会话ID关联同一会话中的多个操作
- **错误记录**：详细记录操作过程中的错误和异常

## 组件解析

### 1. LegalAuditLogger 类

核心日志记录器类，提供以下功能：

- 自动创建和管理日志目录和文件
- 生成唯一的会话和操作ID
- 记录详细的操作信息和元数据
- 导出审计日志为多种格式

### 2. 日志装饰器

`@log_legal_operation` 装饰器可应用于任何函数，自动记录该函数的执行过程：

```python
from src.exporters.legal_logger import log_legal_operation

@log_legal_operation("copyright_injection")
def add_copyright_to_file(file_path, copyright_text):
    # 函数实现
    pass
```

### 3. 简便函数

系统提供多种简便函数，用于快速记录不同类型的法律操作：

```python
# 基本法律操作记录
log_legal_operation("zh", "版权声明内容")

# 特定类型的法律操作
log_legal_injection(file_path, "xml", "copyright", content_before, content_after)
log_copyright_check(file_path, True, "版权所有 © 2023")
log_disclaimer_addition(file_path, "standard", content_before, content_after)
```

## 使用指南

### 基本用法

1. **简单记录法律操作**

   ```python
   from src.exporters.legal_logger import log_legal_operation
   
   # 记录一个简单的法律操作
   log_legal_operation("zh", "这是版权声明内容")
   ```

2. **使用核心记录器**

   ```python
   from src.exporters.legal_logger import get_legal_logger
   
   # 获取记录器实例
   logger = get_legal_logger()
   
   # 记录详细操作
   logger.log_operation(
       operation_type="copyright_check",
       details={
           "file_path": "/path/to/file.xml",
           "has_copyright": True,
           "source": "manual_check"
       }
   )
   ```

3. **记录法律内容注入**

   ```python
   logger.log_legal_injection(
       file_path="/path/to/file.xml",
       content_type="xml",
       injection_type="disclaimer",
       content_before=original_content,
       content_after=modified_content
   )
   ```

### 使用装饰器

将装饰器应用于处理法律相关内容的函数：

```python
from src.exporters.legal_logger import log_legal_operation

@log_legal_operation("watermark_addition")
def add_watermark_to_video(video_path, watermark_text):
    # 函数实现
    pass
```

装饰器会自动：
- 记录函数名称和参数
- 捕获函数执行前后的文件内容变化
- 记录函数执行状态（成功/失败）
- 记录任何异常

### 导出和分析审计日志

```python
from src.exporters.legal_logger import get_legal_logger

logger = get_legal_logger()

# 导出最近30天的审计日志为JSON
json_path = logger.export_logs(
    output_format="json",
    start_date="2023-05-01",
    end_date="2023-05-31"
)

# 导出特定类型的操作为CSV
csv_path = logger.export_logs(
    output_format="csv",
    operation_types=["copyright_injection", "disclaimer_addition"]
)
```

## 与现有系统集成

法律操作审计日志系统已与以下组件集成：

1. **XML更新器**：记录XML工程文件的修改操作
2. **法律注入器**：记录版权声明和免责声明的注入操作
3. **水印应用器**：记录水印添加操作

**示例集成**：

```python
# 在法律注入器中集成审计日志
def inject_disclaimer_to_xml(xml_file_path, disclaimer_text):
    # 记录操作开始
    logger = get_legal_logger()
    
    try:
        # 读取原始内容
        with open(xml_file_path, 'r') as f:
            original_content = f.read()
        
        # 执行注入操作
        # ...
        
        # 读取修改后的内容
        with open(xml_file_path, 'r') as f:
            modified_content = f.read()
        
        # 记录成功操作
        logger.log_legal_injection(
            file_path=xml_file_path,
            content_type="xml",
            injection_type="disclaimer",
            content_before=original_content,
            content_after=modified_content
        )
        
        return True
    except Exception as e:
        # 记录失败操作
        logger.log_legal_injection(
            file_path=xml_file_path,
            content_type="xml",
            injection_type="disclaimer",
            status="failed",
            error=e
        )
        return False
```

## 配置选项

审计日志系统可通过以下方式进行配置：

1. **日志位置**：默认位于 `logs/legal` 目录，可通过初始化参数修改：
   ```python
   logger = LegalAuditLogger("/custom/path/to/logs")
   ```

2. **日志轮转**：默认单个日志文件最大10MB，保留30个备份文件。

3. **导出选项**：可自定义导出格式、日期范围和操作类型。

## 最佳实践

1. **使用装饰器**：尽可能使用装饰器自动记录操作，减少手动代码
2. **记录前后内容**：记录操作前后的内容，便于追踪变化
3. **定期导出**：定期导出和备份审计日志，确保可长期查询
4. **结构化详情**：使用结构化的详情字段，便于后续分析
5. **错误处理**：确保在异常情况下仍能记录操作，并标记失败状态

## 示例代码

1. **简单日志记录**

   ```python
   from src.exporters.legal_logger import log_legal_operation
   
   def process_copyright():
       # 处理版权信息
       copyright_text = "© 2023 ClipsMaster AI. All rights reserved."
       log_legal_operation("zh", copyright_text)
   ```

2. **完整操作记录**

   ```python
   from src.exporters.legal_logger import get_legal_logger
   
   def add_watermark(video_path, text, position):
       logger = get_legal_logger()
       
       try:
           # 执行水印添加操作
           # ...
           
           # 记录成功
           logger.log_watermark_operation(
               file_path=video_path,
               watermark_type="text",
               text=text,
               position=position
           )
       except Exception as e:
           # 记录失败
           logger.log_watermark_operation(
               file_path=video_path,
               watermark_type="text",
               text=text,
               position=position,
               status="failed",
               error=e
           )
           raise
   ```

3. **使用装饰器模式**

   ```python
   from src.exporters.legal_logger import log_legal_operation
   
   @log_legal_operation("xml_processing")
   def update_xml_metadata(xml_path, metadata):
       # 此函数的执行将自动被记录
       # 包括参数、状态、异常等信息
       pass
   ```

## 演示

请参考 `examples/legal_audit_demo.py` 获取完整的演示示例，包括：

- 手动记录法律操作
- 使用装饰器自动记录操作
- 与法律注入器集成
- 导出审计日志

可通过以下命令运行演示：

```bash
python examples/legal_audit_demo.py
```

## 测试

单元测试位于 `src/tests/export_test/test_legal_logger.py`，可通过以下命令运行：

```bash
python -m unittest src/tests/export_test/test_legal_logger.py
``` 