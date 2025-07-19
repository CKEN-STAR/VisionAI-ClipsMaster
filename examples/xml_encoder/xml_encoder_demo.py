#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML编码器示例

演示如何使用XML编码器处理特殊字符和构建安全的XML内容
"""

import os
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入XML编码器功能
from src.export.xml_encoder import (
    sanitize_xml,
    encode_xml_attribute,
    encode_xml_content,
    wrap_cdata,
    escape_control_chars,
    process_xml_string,
    create_xml_element,
    normalize_file_path
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def print_separator():
    """打印分隔线"""
    print("\n" + "=" * 50 + "\n")

def demo_basic_escaping():
    """演示基本XML转义"""
    print("演示基本XML特殊字符转义:")
    
    raw_text = """<video title="精彩瞬间" artist='佚名'>
    播放时长: 3 & 2 分钟
    视频格式: 1080p > 720p
</video>"""
    
    print("原始文本:")
    print(raw_text)
    
    print("\n转义后文本:")
    escaped_text = sanitize_xml(raw_text)
    print(escaped_text)

def demo_xml_element_creation():
    """演示XML元素创建"""
    print("演示XML元素创建:")
    
    # 创建简单元素
    simple = create_xml_element("video")
    print("\n简单元素:")
    print(simple)
    
    # 创建带属性的元素
    with_attrs = create_xml_element("video", {
        "id": "v12345",
        "title": "精彩时刻",
        "duration": "03:45",
        "special_attr": "引号\"与单引号'"
    })
    print("\n带属性的元素:")
    print(with_attrs)
    
    # 创建带内容的元素
    with_content = create_xml_element("description", content="这是一段<em>重要</em>的描述，包含&特殊字符")
    print("\n带内容的元素:")
    print(with_content)
    
    # 创建带CDATA的元素
    script_content = """function playVideo() {
    if (player.readyState() && duration > 0) {
        player.play();
        console.log("视频开始播放");
    }
}"""
    with_cdata = create_xml_element("script", content=script_content, use_cdata=True)
    print("\n带CDATA的元素:")
    print(with_cdata)
    
    # 创建嵌套结构
    try:
        project = create_xml_element("project", {"version": "3.0"}, 
            create_xml_element("title", content="我的项目") + "\n  " +
            create_xml_element("author", content="张三") + "\n  " +
            create_xml_element("description", content="这是一个<视频>编辑项目 & 测试")
        )
        print("\n嵌套结构:")
        print(project)
    except Exception as e:
        print(f"创建嵌套结构时出错: {e}")

def demo_path_normalization():
    """演示路径标准化"""
    print("演示文件路径标准化:")
    
    # Windows路径
    win_path = r"D:\Projects\VisionAI\素材库\风景 & 人物\video.mp4"
    print(f"\nWindows路径: {win_path}")
    print(f"标准化后: {normalize_file_path(win_path)}")
    
    # Unix路径
    unix_path = "/home/user/projects/视频项目/素材/test<file>.mp4"
    print(f"\nUnix路径: {unix_path}")
    print(f"标准化后: {normalize_file_path(unix_path)}")

def demo_process_xml():
    """演示处理完整XML字符串"""
    print("演示处理完整XML字符串:")
    
    # 创建一个包含特殊字符的XML
    xml_string = """<project>
  <assets>
    <asset id="a1" path="D:\\videos\\raw footage & clips\\clip1.mp4" />
  </assets>
  <timeline>
    <track name="视频轨 1">
      <clip start="00:00:10" duration="00:01:30">
        这里有一些 < > & " ' 特殊字符
      </clip>
    </track>
  </timeline>
</project>"""
    
    print("\n原始XML:")
    print(xml_string)
    
    print("\n处理后XML:")
    processed = process_xml_string(xml_string)
    print(processed)

def main():
    """主函数"""
    print("XML编码器演示程序\n")
    
    # 演示基本XML转义
    demo_basic_escaping()
    print_separator()
    
    # 演示XML元素创建
    demo_xml_element_creation()
    print_separator()
    
    # 演示路径标准化
    demo_path_normalization()
    print_separator()
    
    # 演示处理完整XML
    demo_process_xml()
    
    print("\n演示完成")

if __name__ == "__main__":
    main() 