# XML编码器 (XML Encoder)

XML编码器模块提供了处理XML特殊字符转义的功能，确保生成的XML内容符合标准规范。

## 主要功能

1. **XML特殊字符转义**  
   处理XML中的保留字符（`&`, `<`, `>`, `"`, `'`），确保它们被正确转义为对应的实体引用。

2. **属性值和内容编码**  
   专门处理XML属性值和元素内容中的特殊字符，避免XML解析错误。

3. **CDATA处理**  
   对包含大量特殊字符的内容使用CDATA包装，避免繁琐的转义操作。

4. **控制字符处理**  
   处理不可见的控制字符，避免XML文档中出现非法字符。

5. **XML元素创建**  
   提供便捷的API创建安全的XML元素，自动进行适当的字符转义。

6. **文件路径标准化**  
   处理文件路径中的特殊字符和平台差异，确保在XML中正确呈现。

## 使用示例

### 基本字符转义

```python
from src.export.xml_encoder import sanitize_xml

# 处理包含特殊字符的文本
text = '<video title="示例" & 测试>'
escaped = sanitize_xml(text)
print(escaped)  # 输出: &lt;video title=&quot;示例&quot; &amp; 测试&gt;
```

### 创建XML元素

```python
from src.export.xml_encoder import create_xml_element

# 创建带属性和内容的XML元素
element = create_xml_element(
    "video", 
    {"id": "v1", "title": "带特殊字符的\"标题\""},
    content="这是<em>内容</em>描述"
)
print(element)
# 输出: <video id="v1" title="带特殊字符的&quot;标题&quot;">这是&lt;em&gt;内容&lt;/em&gt;描述</video>
```

### 使用CDATA包装

```python
from src.export.xml_encoder import wrap_cdata

# 使用CDATA包装大块文本
script = """
function play() {
  if (condition && value > 0) {
    console.log("Playing <video>");
  }
}
"""
cdata_content = wrap_cdata(script)
print(cdata_content)
# 输出: <![CDATA[...]]> 包裹的内容
```

### 处理文件路径

```python
from src.export.xml_encoder import normalize_file_path

# 标准化文件路径
win_path = r"C:\Projects\My Videos & Photos\video.mp4"
normalized = normalize_file_path(win_path)
print(normalized)  # 输出: C:/Projects/My Videos &amp; Photos/video.mp4
```

## 完整处理XML字符串

```python
from src.export.xml_encoder import process_xml_string

# 处理完整的XML字符串
xml = '<project><title>我的项目 & 测试</title></project>'
processed = process_xml_string(xml)
print(processed)
# 输出: 带有XML声明且特殊字符被正确转义的文档
```

## 注意事项

- 在处理大量XML输出时，优先使用CDATA包装而非逐字符转义，以提高性能
- 处理用户输入时务必进行彻底的XML转义，防止XML注入攻击
- 不同环境中的文件路径应先进行标准化，再进行XML编码 