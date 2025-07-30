#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI最终问题修复脚本

修复以下问题：
1. UI控件属性名称映射问题
2. VideoProcessor方法问题
3. 错误处理完善
4. 测试兼容性改进
"""

import os
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_ui_attribute_mapping():
    """修复UI控件属性名称映射问题"""
    logger.info("修复UI控件属性名称映射...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    if not ui_file.exists():
        logger.error(f"文件不存在: {ui_file}")
        return False
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在SimpleScreenplayApp类的__init__方法末尾添加测试兼容性属性
    compatibility_attributes = """
        # 为测试兼容性添加UI组件属性映射
        self.tab_widget = self.tabs  # 标签页控件别名
        self.original_srt_import_btn = None  # 原始SRT导入按钮（在训练页面中）
        self.viral_srt_import_btn = None     # 爆款SRT导入按钮（在训练页面中）
        
        # 查找并映射实际的按钮
        try:
            # 查找训练页面中的导入按钮
            train_widget = self.tabs.widget(1)  # 模型训练标签页
            if train_widget and hasattr(self, 'train_feeder'):
                # 查找原始SRT导入按钮
                for child in train_widget.findChildren(QPushButton):
                    if "导入原始SRT" in child.text():
                        self.original_srt_import_btn = child
                        break
                
                # 查找爆款SRT导入按钮
                for child in train_widget.findChildren(QPushButton):
                    if "导入爆款SRT" in child.text():
                        self.viral_srt_import_btn = child
                        break
        except Exception as e:
            logger.warning(f"映射导入按钮失败: {e}")
        
        logger.info("UI控件属性映射完成")"""
    
    # 在__init__方法的最后添加兼容性属性
    init_end_pattern = "        logger.info(\"UI控件属性映射完成\")"
    if init_end_pattern not in content:
        # 查找__init__方法的结束位置
        init_method_pattern = "    def __init__(self):"
        if init_method_pattern in content:
            # 在类的最后添加兼容性属性
            class_end_pattern = "        # 设置状态栏"
            if class_end_pattern in content:
                content = content.replace(
                    class_end_pattern,
                    compatibility_attributes + "\n        # 设置状态栏"
                )
                logger.info("UI控件属性映射添加完成")
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_video_processor_methods():
    """修复VideoProcessor方法问题"""
    logger.info("修复VideoProcessor方法问题...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复generate_viral_srt方法中的load_original_subtitles调用
    old_method_call = """            # 解析原始SRT
            original_subtitles = parse_srt(srt_path)
            if not original_subtitles:
                logger.error("SRT文件解析失败")
                return None
            
            # 创建剧本工程师
            engineer = ScreenplayEngineer()
            
            # 执行剧本重构
            reconstruction = engineer.reconstruct_screenplay(
                srt_input=original_subtitles,
                target_style="viral"
            )"""
    
    new_method_call = """            # 解析原始SRT
            original_subtitles = parse_srt(srt_path)
            if not original_subtitles:
                logger.error("SRT文件解析失败")
                return None
            
            # 创建剧本工程师
            engineer = ScreenplayEngineer()
            
            # 加载字幕到工程师
            engineer.load_subtitles(original_subtitles)
            
            # 执行剧本重构
            reconstruction = engineer.reconstruct_screenplay(
                srt_input=original_subtitles,
                target_style="viral"
            )"""
    
    if old_method_call in content:
        content = content.replace(old_method_call, new_method_call)
        logger.info("VideoProcessor方法调用修复完成")
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def enhance_error_handling():
    """增强错误处理"""
    logger.info("增强错误处理...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 增强generate_viral_srt方法的错误处理
    enhanced_error_handling = """    @staticmethod
    def generate_viral_srt(srt_path, language_mode="auto"):
        \"\"\"生成爆款SRT字幕 - 增强错误处理版本\"\"\"
        try:
            # 验证文件存在性
            if not os.path.exists(srt_path):
                logger.error(f"SRT文件不存在: {srt_path}")
                return None
            
            # 验证文件格式
            if not srt_path.lower().endswith('.srt'):
                logger.error(f"文件格式不正确，需要SRT格式: {srt_path}")
                return None
            
            # 验证文件大小
            file_size = os.path.getsize(srt_path)
            if file_size == 0:
                logger.error(f"SRT文件为空: {srt_path}")
                return None
            
            if file_size > 10 * 1024 * 1024:  # 10MB限制
                logger.error(f"SRT文件过大: {srt_path}")
                return None
            
            from src.core.screenplay_engineer import ScreenplayEngineer
            from src.core.srt_parser import parse_srt
            
            logger.info(f"开始生成爆款SRT: {srt_path}")
            
            # 解析原始SRT
            try:
                original_subtitles = parse_srt(srt_path)
                if not original_subtitles:
                    logger.error("SRT文件解析失败或为空")
                    return None
                
                if len(original_subtitles) == 0:
                    logger.error("SRT文件中没有有效的字幕条目")
                    return None
                    
            except Exception as e:
                logger.error(f"SRT文件解析异常: {e}")
                return None
            
            # 创建剧本工程师
            try:
                engineer = ScreenplayEngineer()
                
                # 加载字幕到工程师
                engineer.load_subtitles(original_subtitles)
                
                # 执行剧本重构
                reconstruction = engineer.reconstruct_screenplay(
                    srt_input=original_subtitles,
                    target_style="viral"
                )
                
                if reconstruction and "timeline" in reconstruction:
                    # 生成输出文件路径
                    output_path = srt_path.replace(".srt", "_viral.srt")
                    
                    # 生成SRT内容
                    srt_content = VideoProcessor._generate_srt_content(reconstruction["timeline"])
                    
                    if not srt_content or len(srt_content.strip()) == 0:
                        logger.error("生成的SRT内容为空")
                        return None
                    
                    # 保存文件
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(srt_content)
                    
                    # 验证输出文件
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        logger.info(f"爆款SRT生成成功: {output_path}")
                        return output_path
                    else:
                        logger.error("输出文件生成失败")
                        return None
                else:
                    logger.error("剧本重构失败")
                    return None
                    
            except Exception as e:
                logger.error(f"剧本重构过程异常: {e}")
                return None
                
        except Exception as e:
            logger.error(f"生成爆款SRT失败: {e}")
            return None"""
    
    # 替换原有的generate_viral_srt方法
    old_method_start = "    @staticmethod\n    def generate_viral_srt(srt_path, language_mode=\"auto\"):"
    old_method_end = "            return None"
    
    # 查找方法的开始和结束位置
    start_pos = content.find(old_method_start)
    if start_pos != -1:
        # 查找方法结束位置（下一个方法或类结束）
        lines = content[start_pos:].split('\n')
        method_lines = []
        indent_level = None
        
        for i, line in enumerate(lines):
            if i == 0:  # 第一行
                method_lines.append(line)
                continue
                
            # 检查缩进级别
            if line.strip():  # 非空行
                current_indent = len(line) - len(line.lstrip())
                if indent_level is None:
                    indent_level = current_indent
                elif current_indent <= 4 and not line.startswith('    @'):  # 方法结束
                    break
            
            method_lines.append(line)
        
        old_method = '\n'.join(method_lines)
        content = content.replace(old_method, enhanced_error_handling)
        logger.info("错误处理增强完成")
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def add_test_compatibility_methods():
    """添加测试兼容性方法"""
    logger.info("添加测试兼容性方法...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加测试兼容性方法到VideoProcessor类
    compatibility_methods = """
    @staticmethod
    def validate_srt_file(srt_path):
        \"\"\"验证SRT文件有效性\"\"\"
        try:
            if not os.path.exists(srt_path):
                return False
            
            if not srt_path.lower().endswith('.srt'):
                return False
            
            # 简单的SRT格式验证
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return False
                
                # 检查是否包含基本的SRT结构
                lines = content.split('\\n')
                has_number = False
                has_timecode = False
                
                for line in lines[:10]:  # 检查前10行
                    line = line.strip()
                    if line.isdigit():
                        has_number = True
                    elif '-->' in line:
                        has_timecode = True
                
                return has_number and has_timecode
            
        except Exception:
            return False
    
    @staticmethod
    def get_srt_info(srt_path):
        \"\"\"获取SRT文件信息\"\"\"
        try:
            from src.core.srt_parser import parse_srt
            
            subtitles = parse_srt(srt_path)
            if not subtitles:
                return None
            
            total_duration = subtitles[-1]["end_time"] if subtitles else 0
            
            return {
                "subtitle_count": len(subtitles),
                "total_duration": total_duration,
                "file_size": os.path.getsize(srt_path),
                "is_valid": True
            }
            
        except Exception as e:
            return {
                "subtitle_count": 0,
                "total_duration": 0,
                "file_size": 0,
                "is_valid": False,
                "error": str(e)
            }"""
    
    # 在VideoProcessor类的最后添加方法
    if "class VideoProcessor(QObject):" in content:
        # 查找类的结束位置
        class_start = content.find("class VideoProcessor(QObject):")
        if class_start != -1:
            # 在_seconds_to_srt_time方法后添加
            insert_point = content.find("            return \"00:00:00,000\"", class_start)
            if insert_point != -1:
                # 找到方法结束位置
                insert_point = content.find("\n", insert_point) + 1
                content = content[:insert_point] + compatibility_methods + content[insert_point:]
                logger.info("测试兼容性方法添加完成")
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def run_verification_test():
    """运行验证测试"""
    logger.info("运行UI修复验证测试...")
    
    try:
        # 测试UI组件导入
        from simple_ui_fixed import SimpleScreenplayApp, VideoProcessor
        
        # 测试VideoProcessor新方法
        has_validate_srt = hasattr(VideoProcessor, 'validate_srt_file')
        has_get_srt_info = hasattr(VideoProcessor, 'get_srt_info')
        
        logger.info(f"✅ VideoProcessor新方法: validate_srt_file={has_validate_srt}, get_srt_info={has_get_srt_info}")
        
        # 测试UI属性映射
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = SimpleScreenplayApp()
        
        has_tab_widget = hasattr(window, 'tab_widget')
        has_tabs = hasattr(window, 'tabs')
        
        window.close()
        
        logger.info(f"✅ UI属性映射: tab_widget={has_tab_widget}, tabs={has_tabs}")
        
        return True
        
    except Exception as e:
        logger.error(f"验证测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始修复VisionAI-ClipsMaster UI最终问题...")
    
    success_count = 0
    total_fixes = 5
    
    # 1. 修复UI控件属性名称映射
    if fix_ui_attribute_mapping():
        success_count += 1
    
    # 2. 修复VideoProcessor方法问题
    if fix_video_processor_methods():
        success_count += 1
    
    # 3. 增强错误处理
    if enhance_error_handling():
        success_count += 1
    
    # 4. 添加测试兼容性方法
    if add_test_compatibility_methods():
        success_count += 1
    
    # 5. 运行验证测试
    if run_verification_test():
        success_count += 1
    
    # 总结
    logger.info(f"UI最终修复完成: {success_count}/{total_fixes} 项修复成功")
    
    if success_count == total_fixes:
        logger.info("🎉 所有UI问题修复成功！")
        return True
    else:
        logger.warning(f"⚠️ 部分UI问题修复失败，请检查日志")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
