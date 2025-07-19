#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本适配器示例

演示如何使用版本适配器在不同版本格式之间进行转换
"""

import os
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.export.version_adapter import (
    adapt_for_version,
    get_supported_versions,
    get_version_aliases,
    get_version_features
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

def demo_version_info():
    """演示获取版本信息"""
    print("支持的版本:")
    versions = get_supported_versions()
    for v in versions:
        features = get_version_features(v)
        print(f"版本 {v}: 支持功能 {', '.join(features)}")
    
    print("\n版本别名:")
    aliases = get_version_aliases()
    for alias, version in aliases.items():
        print(f"{alias} -> {version}")

def demo_downgrade():
    """演示版本降级功能"""
    print("\n演示版本降级 - 从3.0降级到2.9")
    
    xml_3_0 = """<?xml version="1.0" encoding="UTF-8"?>
<project version="3.0">
  <tracks>
    <track id="main_video_track">
      <segments>
        <segment id="seg1" start="10.5" duration="5.0"/>
      </segments>
    </track>
    <track id="aux_video_track">
      <segments/>
    </track>
    <subtitle_track>
      <segments/>
    </subtitle_track>
  </tracks>
  <effects>
    <effect id="fx1" type="blur"/>
    <effect id="fx2" type="color"/>
    <effect id="fx3" type="transition"/>
  </effects>
</project>"""
    
    print("原始XML (3.0版):")
    print(xml_3_0)
    
    # 降级到2.9
    adapted_2_9 = adapt_for_version(xml_3_0, "2.9")
    print("\n降级后XML (2.9版):")
    print(adapted_2_9)
    
    # 降级到2.5
    adapted_2_5 = adapt_for_version(xml_3_0, "2.5")
    print("\n降级后XML (2.5版):")
    print(adapted_2_5)
    
    # 降级到2.0
    adapted_2_0 = adapt_for_version(xml_3_0, "2.0")
    print("\n降级后XML (2.0版):")
    print(adapted_2_0)

def demo_upgrade():
    """演示版本升级功能"""
    print("\n演示版本升级 - 从2.0升级到3.0")
    
    xml_2_0 = """<?xml version="1.0" encoding="UTF-8"?>
<project version="2.0">
  <tracks>
    <track id="main_video_track">
      <segments>
        <segment id="seg1" start="10.5" duration="5.0"/>
      </segments>
    </track>
  </tracks>
</project>"""
    
    print("原始XML (2.0版):")
    print(xml_2_0)
    
    # 升级到3.0
    adapted_3_0 = adapt_for_version(xml_2_0, "3.0")
    print("\n升级后XML (3.0版):")
    print(adapted_3_0)

def demo_alias_conversion():
    """演示使用版本别名进行转换"""
    print("\n演示使用版本别名进行转换")
    
    xml_3_0 = """<?xml version="1.0" encoding="UTF-8"?>
<project version="3.0">
  <tracks>
    <track id="main_video_track">
      <segments>
        <segment id="seg1" start="10.5" duration="5.0"/>
      </segments>
    </track>
    <track id="aux_video_track">
      <segments/>
    </track>
  </tracks>
  <effects>
    <effect id="fx1" type="blur"/>
  </effects>
</project>"""
    
    # 使用别名降级到移动版
    adapted_mobile = adapt_for_version(xml_3_0, "移动版")
    print("使用'移动版'别名降级后:")
    print(adapted_mobile)
    
    # 使用别名降级到基础版
    adapted_basic = adapt_for_version(xml_3_0, "基础版")
    print("\n使用'基础版'别名降级后:")
    print(adapted_basic)

def demo_nested_sequence():
    """演示嵌套序列展开"""
    print("\n演示嵌套序列展开")
    
    xml_with_nested = """<?xml version="1.0" encoding="UTF-8"?>
<project version="3.0">
  <tracks>
    <track id="main_video_track">
      <segments>
        <nested_sequence id="nested1">
          <segment id="inner1" start="0" duration="3.0"/>
          <segment id="inner2" start="3.0" duration="2.0"/>
        </nested_sequence>
      </segments>
    </track>
  </tracks>
</project>"""
    
    print("原始XML (带嵌套序列):")
    print(xml_with_nested)
    
    # 降级到2.9，展开嵌套序列
    adapted = adapt_for_version(xml_with_nested, "2.9")
    print("\n降级后XML (嵌套序列已展开):")
    print(adapted)

def main():
    """主函数"""
    print("版本适配器演示程序\n")
    
    # 打印版本信息
    demo_version_info()
    print_separator()
    
    # 演示版本降级
    demo_downgrade()
    print_separator()
    
    # 演示版本升级
    demo_upgrade()
    print_separator()
    
    # 演示使用版本别名
    demo_alias_conversion()
    print_separator()
    
    # 演示嵌套序列展开
    demo_nested_sequence()
    
    print("\n演示完成")

if __name__ == "__main__":
    main() 