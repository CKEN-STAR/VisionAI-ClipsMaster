#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复VideoProcessor类冲突问题
合并两个VideoProcessor类定义，确保所有方法都可用
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_videoprocessor_conflict():
    """修复VideoProcessor类冲突"""
    logger.info("🔧 开始修复VideoProcessor类冲突问题")
    
    ui_file = "simple_ui_fixed.py"
    
    # 创建备份
    backup_file = f"simple_ui_fixed_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(ui_file, backup_file)
    logger.info(f"✅ 已创建备份文件: {backup_file}")
    
    try:
        # 读取原文件
        with open(ui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 找到两个VideoProcessor类的位置
        first_class_start = content.find("class VideoProcessor(QObject):")
        if first_class_start == -1:
            logger.error("❌ 未找到第一个VideoProcessor类")
            return False
        
        # 找到第二个VideoProcessor类
        second_class_start = content.find("class VideoProcessor(QObject):", first_class_start + 1)
        if second_class_start == -1:
            logger.error("❌ 未找到第二个VideoProcessor类")
            return False
        
        logger.info(f"📍 第一个VideoProcessor类位置: {first_class_start}")
        logger.info(f"📍 第二个VideoProcessor类位置: {second_class_start}")
        
        # 提取第一个类的内容（包含get_srt_info方法）
        # 找到第一个类的结束位置（下一个类定义之前）
        first_class_end = second_class_start
        
        # 向前查找，找到第一个类的实际结束位置
        lines = content[:first_class_end].split('\n')
        first_class_lines = []
        in_first_class = False
        
        for i, line in enumerate(lines):
            if "class VideoProcessor(QObject):" in line and not in_first_class:
                in_first_class = True
                first_class_lines.append(line)
            elif in_first_class:
                # 如果遇到新的类定义或者非缩进行，说明第一个类结束
                if line.strip() and not line.startswith((' ', '\t')) and not line.startswith('#'):
                    if line.startswith('class ') and 'VideoProcessor' not in line:
                        break
                first_class_lines.append(line)
        
        first_class_content = '\n'.join(first_class_lines)
        
        # 提取第二个类的内容
        second_class_content = content[second_class_start:]
        
        # 找到第二个类的结束位置
        second_class_lines = second_class_content.split('\n')
        merged_class_lines = []
        
        # 开始合并类
        logger.info("🔄 开始合并VideoProcessor类...")
        
        # 从第二个类开始（保留其信号定义）
        in_class = False
        for line in second_class_lines:
            if "class VideoProcessor(QObject):" in line:
                in_class = True
                merged_class_lines.append(line)
                merged_class_lines.append('    """视频处理器 - 核心视频处理逻辑（合并版本）"""')
                merged_class_lines.append('')
            elif in_class:
                # 如果遇到新的类定义，停止
                if line.strip() and not line.startswith((' ', '\t')) and line.startswith('class ') and 'VideoProcessor' not in line:
                    break
                merged_class_lines.append(line)
        
        # 添加第一个类中的get_srt_info方法
        logger.info("📝 添加get_srt_info方法...")
        
        # 找到第一个类中的get_srt_info方法
        first_class_lines_list = first_class_content.split('\n')
        get_srt_info_lines = []
        in_get_srt_info = False
        
        for line in first_class_lines_list:
            if "def get_srt_info(srt_path):" in line:
                in_get_srt_info = True
                get_srt_info_lines.append('')
                get_srt_info_lines.append(line)
            elif in_get_srt_info:
                if line.strip() and not line.startswith((' ', '\t')) and line.startswith('def '):
                    break
                elif line.strip() and not line.startswith((' ', '\t')) and not line.startswith('#'):
                    if not line.strip().startswith('@'):
                        break
                get_srt_info_lines.append(line)
        
        # 将get_srt_info方法插入到合并的类中
        # 找到合适的插入位置（在最后一个方法之后）
        insert_position = len(merged_class_lines) - 1
        while insert_position > 0 and not merged_class_lines[insert_position].strip():
            insert_position -= 1
        
        # 插入get_srt_info方法
        for line in get_srt_info_lines:
            merged_class_lines.insert(insert_position + 1, line)
            insert_position += 1
        
        # 重新构建文件内容
        new_content_parts = []
        
        # 添加第一个VideoProcessor类之前的内容
        new_content_parts.append(content[:first_class_start])
        
        # 添加合并后的VideoProcessor类
        merged_class_content = '\n'.join(merged_class_lines)
        new_content_parts.append(merged_class_content)
        
        # 添加第二个VideoProcessor类之后的内容
        # 找到第二个类的结束位置
        remaining_content = content[second_class_start:]
        remaining_lines = remaining_content.split('\n')
        
        # 跳过第二个VideoProcessor类
        skip_lines = 0
        in_second_class = False
        for i, line in enumerate(remaining_lines):
            if "class VideoProcessor(QObject):" in line:
                in_second_class = True
                skip_lines = i
            elif in_second_class and line.strip() and not line.startswith((' ', '\t')):
                if line.startswith('class ') and 'VideoProcessor' not in line:
                    skip_lines = i
                    break
        
        if skip_lines > 0:
            remaining_content = '\n'.join(remaining_lines[skip_lines:])
            new_content_parts.append(remaining_content)
        
        # 写入修复后的文件
        new_content = ''.join(new_content_parts)
        
        with open(ui_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info("✅ VideoProcessor类冲突修复完成")
        logger.info(f"📄 备份文件: {backup_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 修复过程中发生错误: {str(e)}")
        # 恢复备份
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, ui_file)
            logger.info("🔄 已从备份恢复原文件")
        return False

def verify_fix():
    """验证修复结果"""
    logger.info("🔍 验证修复结果...")
    
    try:
        # 尝试导入并测试
        import sys
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        
        from simple_ui_fixed import VideoProcessor
        
        # 检查方法是否存在
        methods_to_check = ['generate_viral_srt', 'generate_video', 'get_srt_info']
        missing_methods = []
        
        for method in methods_to_check:
            if not hasattr(VideoProcessor, method):
                missing_methods.append(method)
        
        if missing_methods:
            logger.error(f"❌ 仍然缺少方法: {missing_methods}")
            return False
        else:
            logger.info("✅ 所有必需方法都已可用")
            return True
            
    except Exception as e:
        logger.error(f"❌ 验证过程中发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    print("🔧 VisionAI-ClipsMaster VideoProcessor类冲突修复工具")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists("simple_ui_fixed.py"):
        print("❌ 未找到simple_ui_fixed.py文件")
        return False
    
    # 执行修复
    if fix_videoprocessor_conflict():
        print("✅ VideoProcessor类冲突修复成功")
        
        # 验证修复结果
        if verify_fix():
            print("✅ 修复验证通过，所有方法都可用")
            return True
        else:
            print("⚠️ 修复验证失败，可能需要手动检查")
            return False
    else:
        print("❌ VideoProcessor类冲突修复失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
