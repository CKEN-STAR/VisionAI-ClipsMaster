#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异常回滚机制演示

演示如何使用回滚机制来保护XML文件操作，确保在操作失败时能够恢复到原始状态。
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.export.rollback_manager import (
    with_xml_rollback,
    backup_xml,
    restore_xml,
    XMLRollbackManager
)
from src.export.xml_updater import XMLUpdater


def create_sample_xml(output_path: str) -> str:
    """
    创建示例XML文件
    
    Args:
        output_path: 输出文件路径
        
    Returns:
        str: 文件路径
    """
    # 创建基本XML结构
    root = ET.Element("project")
    
    # 添加元数据节点
    meta = ET.SubElement(root, "meta")
    ET.SubElement(meta, "generator").text = "ClipsMaster Demo"
    ET.SubElement(meta, "copyright").text = "ClipsMaster 2023"
    
    # 添加资源节点
    resources = ET.SubElement(root, "resources")
    video = ET.SubElement(resources, "video", {
        "id": "video1",
        "path": "sample.mp4",
        "name": "示例视频"
    })
    
    # 添加时间轴节点
    timeline = ET.SubElement(root, "timeline")
    track = ET.SubElement(timeline, "track", {"type": "video"})
    clip = ET.SubElement(track, "clip", {
        "resourceId": "video1",
        "start": "0",
        "duration": "10"
    })
    
    # 创建XML树并保存
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    
    print(f"已创建示例XML文件: {output_path}")
    return output_path


def demo_manual_rollback():
    """演示手动回滚功能"""
    print("\n===== 手动回滚演示 =====")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 创建示例XML
        create_sample_xml(tmp_path)
        
        # 显示原始内容
        print("\n原始XML内容:")
        with open(tmp_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            print(original_content[:200] + "...")
        
        # 备份XML
        manager = XMLRollbackManager()
        backup_result = manager.backup_xml_content(tmp_path)
        print(f"\n备份结果: {'成功' if backup_result else '失败'}")
        
        # 修改XML (故意破坏格式)
        print("\n正在修改XML (故意破坏格式)...")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<project>
  <meta>
    <generator>Modified Content</generator>
  </meta>
  <broken>
    <format>This is intentionally broken XML
</project>""")
        
        # 显示修改后的内容
        print("\n修改后的XML内容:")
        with open(tmp_path, "r", encoding="utf-8") as f:
            modified_content = f.read()
            print(modified_content[:200] + "...")
        
        # 验证XML (应该失败)
        validation_result = manager.verify_xml(tmp_path)
        print(f"\nXML验证结果: {'有效' if validation_result else '无效'}")
        
        # 手动恢复
        print("\n执行手动回滚...")
        restore_result = manager.restore_xml_content(tmp_path)
        print(f"回滚结果: {'成功' if restore_result else '失败'}")
        
        # 显示恢复后的内容
        print("\n恢复后的XML内容:")
        with open(tmp_path, "r", encoding="utf-8") as f:
            restored_content = f.read()
            print(restored_content[:200] + "...")
        
        # 验证恢复后的XML
        validation_result = manager.verify_xml(tmp_path)
        print(f"\nXML验证结果: {'有效' if validation_result else '无效'}")
        
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def demo_decorator_rollback():
    """演示装饰器自动回滚功能"""
    print("\n===== 装饰器自动回滚演示 =====")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 创建示例XML
        create_sample_xml(tmp_path)
        
        # 定义带装饰器的函数
        @with_xml_rollback
        def modify_xml_safely(xml_path):
            """安全修改XML"""
            tree = ET.parse(xml_path)
            root = tree.getroot()
            generator = root.find(".//generator")
            generator.text = "Modified Safely"
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
            return True
        
        @with_xml_rollback
        def modify_xml_with_error(xml_path):
            """错误修改XML"""
            # 先做一些有效的修改
            tree = ET.parse(xml_path)
            root = tree.getroot()
            generator = root.find(".//generator")
            generator.text = "Modified But Will Fail"
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
            
            # 然后故意破坏XML
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write("""<?xml version="1.0" encoding="UTF-8"?>
<project>
  <meta>
    <generator>This XML will be broken
  </meta>
</project>""")
            return True
        
        # 显示原始内容
        print("\n原始XML内容:")
        with open(tmp_path, "r", encoding="utf-8") as f:
            print(f.read()[:200] + "...")
        
        # 安全修改
        print("\n执行安全修改...")
        result = modify_xml_safely(tmp_path)
        print(f"修改结果: {'成功' if result else '失败'}")
        
        # 显示安全修改后的内容
        print("\n安全修改后的XML内容:")
        with open(tmp_path, "r", encoding="utf-8") as f:
            print(f.read()[:200] + "...")
        
        # 错误修改 (应该自动回滚)
        print("\n执行错误修改 (预期会自动回滚)...")
        result = modify_xml_with_error(tmp_path)
        print(f"修改结果: {'成功' if result else '失败'}")
        
        # 显示回滚后的内容
        print("\n回滚后的XML内容:")
        with open(tmp_path, "r", encoding="utf-8") as f:
            print(f.read()[:200] + "...")
        
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def demo_xml_updater_rollback():
    """演示XML更新器的自动回滚功能"""
    print("\n===== XML更新器自动回滚演示 =====")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 创建示例XML
        create_sample_xml(tmp_path)
        
        # 初始化XML更新器
        updater = XMLUpdater()
        
        # 显示原始内容
        print("\n原始XML内容:")
        with open(tmp_path, "r", encoding="utf-8") as f:
            print(f.read()[:200] + "...")
        
        # 正常添加片段
        print("\n正常添加新片段...")
        new_clip = {
            'resource_id': 'video1',
            'start_time': 15.0,
            'duration': 5.0,
            'name': '新片段_正常'
        }
        result = updater.append_clip(tmp_path, new_clip)
        print(f"添加结果: {'成功' if result else '失败'}")
        
        # 显示添加后的内容
        print("\n添加片段后的XML内容:")
        with open(tmp_path, "r", encoding="utf-8") as f:
            print(f.read()[:200] + "...")
        
        # 备份当前内容
        with open(tmp_path, "r", encoding="utf-8") as f:
            correct_content = f.read()
        
        # 尝试添加无效资源 (应该失败并回滚)
        print("\n添加无效资源 (预期会自动回滚)...")
        # 手动破坏文件以模拟操作过程中的失败
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(correct_content.replace("</project>", "<broken>"))
        
        result = updater.add_resource(tmp_path, {'id': 'invalid', 'path': 'nonexistent.mp4'})
        print(f"添加结果: {'成功' if result else '失败'}")
        
        # 显示回滚后的内容
        print("\n回滚后的XML内容 (应该与之前相同):")
        with open(tmp_path, "r", encoding="utf-8") as f:
            current_content = f.read()
            print(current_content[:200] + "...")
        
        # 验证内容是否恢复
        is_restored = current_content == correct_content
        print(f"\n内容是否成功恢复: {'是' if is_restored else '否'}")
        
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def main():
    """主函数"""
    print("=" * 50)
    print("XML异常回滚机制演示")
    print("=" * 50)
    
    # 演示手动回滚
    demo_manual_rollback()
    
    # 演示装饰器自动回滚
    demo_decorator_rollback()
    
    # 演示XML更新器的自动回滚
    demo_xml_updater_rollback()
    
    print("\n" + "=" * 50)
    print("演示完成")
    print("=" * 50)


if __name__ == "__main__":
    main() 