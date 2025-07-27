#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 错误处理修复脚本

修复错误处理测试失败的问题：
1. 修复VideoProcessor.generate_viral_srt()的错误处理
2. 更新UI桥接模块的文件验证
3. 确保无效文件返回None而不是备用内容
"""

import os
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_video_processor_error_handling():
    """修复VideoProcessor的错误处理"""
    logger.info("修复VideoProcessor错误处理...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复第二个generate_viral_srt方法的错误处理
    old_backup_logic = """        # 备用方案：原有的实现
        try:

            from src.core.screenplay_engineer import import_srt, generate_screenplay
            from src.versioning.param_manager import prepare_params
            # 检测语言
            subtitles = import_srt(srt_file_path)
            text_content = " ".join([s.get("text", "") for s in subtitles])
            # 如果提供了语言模式且不是auto，直接使用该语言
            if language_mode and language_mode != "auto":
                language = language_mode
            else:

                # 否则自动检测
                language = "zh" if any("\\u4e00" <= char <= "\\u9fff" for char in text_content) else "en"
            # 准备参数 - 使用默认值，由模型自主决定最佳参数
            params = prepare_params(language=language, style="viral")
            print(f"使用AI模型自主生成爆款剧本，语言: {language}")
            # 生成爆款剧本
            output = generate_screenplay(subtitles, language, params=params)
            viral_subtitles = output.get("screenplay", [])
            # 写入新SRT文件
            output_path = os.path.splitext(srt_file_path)[0] + "_viral.srt"
            with open(output_path, "w", encoding="utf-8") as f:
                for i, sub in enumerate(viral_subtitles, 1):

                    f.write(f"{i}\\n")
                    f.write(f"{sub.get('start_time')} --> {sub.get('end_time')}\\n")
                    f.write(f"{sub.get('text')}\\n\\n")
            return output_path
        except Exception as e:

            print(f"生成爆款SRT出错: {e}")
            return None"""
    
    new_backup_logic = """        # 严格验证文件有效性 - 不使用备用方案
        try:
            # 首先验证文件存在性和基本格式
            if not os.path.exists(srt_file_path):
                print(f"[ERROR] SRT文件不存在: {srt_file_path}")
                return None
            
            # 验证文件大小
            file_size = os.path.getsize(srt_file_path)
            if file_size == 0:
                print(f"[ERROR] SRT文件为空: {srt_file_path}")
                return None
            
            # 验证文件扩展名
            if not srt_file_path.lower().endswith('.srt'):
                print(f"[ERROR] 文件不是SRT格式: {srt_file_path}")
                return None
            
            from src.core.screenplay_engineer import import_srt, generate_screenplay
            from src.versioning.param_manager import prepare_params
            
            # 尝试解析SRT文件
            subtitles = import_srt(srt_file_path)
            
            # 验证解析结果
            if not subtitles or len(subtitles) == 0:
                print(f"[ERROR] SRT文件解析失败或无有效内容: {srt_file_path}")
                return None
            
            # 验证字幕内容质量
            valid_subtitles = [s for s in subtitles if s.get("text", "").strip()]
            if len(valid_subtitles) == 0:
                print(f"[ERROR] SRT文件中没有有效的文本内容: {srt_file_path}")
                return None
            
            text_content = " ".join([s.get("text", "") for s in valid_subtitles])
            if len(text_content.strip()) < 5:  # 至少需要5个字符
                print(f"[ERROR] SRT文件内容过短，无法处理: {srt_file_path}")
                return None
            
            # 检测语言
            if language_mode and language_mode != "auto":
                language = language_mode
            else:
                # 自动检测语言
                language = "zh" if any("\\u4e00" <= char <= "\\u9fff" for char in text_content) else "en"
            
            # 准备参数
            params = prepare_params(language=language, style="viral")
            print(f"使用AI模型生成爆款剧本，语言: {language}")
            
            # 生成爆款剧本
            output = generate_screenplay(valid_subtitles, language, params=params)
            viral_subtitles = output.get("screenplay", [])
            
            # 验证生成结果
            if not viral_subtitles or len(viral_subtitles) == 0:
                print(f"[ERROR] 爆款剧本生成失败: {srt_file_path}")
                return None
            
            # 写入新SRT文件
            output_path = os.path.splitext(srt_file_path)[0] + "_viral.srt"
            with open(output_path, "w", encoding="utf-8") as f:
                for i, sub in enumerate(viral_subtitles, 1):
                    f.write(f"{i}\\n")
                    f.write(f"{sub.get('start_time')} --> {sub.get('end_time')}\\n")
                    f.write(f"{sub.get('text')}\\n\\n")
            
            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"[SUCCESS] 爆款SRT生成成功: {output_path}")
                return output_path
            else:
                print(f"[ERROR] 输出文件生成失败: {output_path}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 生成爆款SRT出错: {e}")
            return None"""
    
    if old_backup_logic in content:
        content = content.replace(old_backup_logic, new_backup_logic)
        logger.info("VideoProcessor错误处理修复完成")
    else:
        logger.warning("未找到需要修复的备用逻辑代码")
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_ui_bridge_validation():
    """修复UI桥接模块的文件验证"""
    logger.info("修复UI桥接模块文件验证...")
    
    ui_bridge_file = Path("ui_bridge.py")
    
    if not ui_bridge_file.exists():
        logger.warning("ui_bridge.py文件不存在，跳过修复")
        return True
    
    # 读取文件内容
    with open(ui_bridge_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复generate_viral_srt方法的文件验证
    old_validation = """        try:
            # 先加载原始字幕文件（使用正确的方法名）
            subtitles = self.screenplay_engineer.load_subtitles(srt_file_path)
            if not subtitles:
                logger.error("加载原始字幕失败")
                return None"""
    
    new_validation = """        try:
            # 严格验证输入文件
            if not os.path.exists(srt_file_path):
                logger.error(f"SRT文件不存在: {srt_file_path}")
                return None
            
            # 验证文件大小
            file_size = os.path.getsize(srt_file_path)
            if file_size == 0:
                logger.error(f"SRT文件为空: {srt_file_path}")
                return None
            
            # 验证文件扩展名
            if not srt_file_path.lower().endswith('.srt'):
                logger.error(f"文件不是SRT格式: {srt_file_path}")
                return None
            
            # 先加载原始字幕文件（使用正确的方法名）
            subtitles = self.screenplay_engineer.load_subtitles(srt_file_path)
            if not subtitles or len(subtitles) == 0:
                logger.error("加载原始字幕失败或文件无有效内容")
                return None
            
            # 验证字幕内容质量
            valid_subtitles = [s for s in subtitles if s.get("text", "").strip()]
            if len(valid_subtitles) == 0:
                logger.error("SRT文件中没有有效的文本内容")
                return None"""
    
    if old_validation in content:
        content = content.replace(old_validation, new_validation)
        logger.info("UI桥接模块文件验证修复完成")
    else:
        logger.warning("未找到需要修复的验证代码")
    
    # 写回文件
    with open(ui_bridge_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_first_video_processor():
    """修复第一个VideoProcessor类的错误处理"""
    logger.info("修复第一个VideoProcessor类的错误处理...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找第一个generate_viral_srt方法并增强其错误处理
    # 这个方法在第1777行附近
    old_first_method = """            # 验证文件大小
            file_size = os.path.getsize(srt_path)
            if file_size == 0:
                logger.error(f"SRT文件为空: {srt_path}")
                return None
            
            if file_size > 10 * 1024 * 1024:  # 10MB限制
                logger.error(f"SRT文件过大: {srt_path}")
                return None"""
    
    new_first_method = """            # 验证文件大小
            file_size = os.path.getsize(srt_path)
            if file_size == 0:
                logger.error(f"SRT文件为空: {srt_path}")
                return None
            
            if file_size > 10 * 1024 * 1024:  # 10MB限制
                logger.error(f"SRT文件过大: {srt_path}")
                return None
            
            # 验证文件内容格式
            try:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    content_preview = f.read(1000)  # 读取前1000字符
                    if not content_preview.strip():
                        logger.error(f"SRT文件内容为空: {srt_path}")
                        return None
                    
                    # 简单的SRT格式验证
                    lines = content_preview.split('\\n')
                    has_number = False
                    has_timecode = False
                    
                    for line in lines[:20]:  # 检查前20行
                        line = line.strip()
                        if line.isdigit():
                            has_number = True
                        elif '-->' in line:
                            has_timecode = True
                    
                    if not (has_number and has_timecode):
                        logger.error(f"SRT文件格式无效: {srt_path}")
                        return None
                        
            except Exception as e:
                logger.error(f"SRT文件读取失败: {srt_path}, {e}")
                return None"""
    
    if old_first_method in content:
        content = content.replace(old_first_method, new_first_method)
        logger.info("第一个VideoProcessor类错误处理修复完成")
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def run_error_handling_test():
    """运行错误处理测试验证"""
    logger.info("运行错误处理测试验证...")
    
    try:
        import tempfile
        from simple_ui_fixed import VideoProcessor
        
        temp_dir = tempfile.mkdtemp(prefix="error_test_")
        
        # 测试1: 不存在的文件
        result1 = VideoProcessor.generate_viral_srt("nonexistent.srt")
        test1_pass = result1 is None
        
        # 测试2: 空文件
        empty_file = Path(temp_dir) / "empty.srt"
        empty_file.touch()
        result2 = VideoProcessor.generate_viral_srt(str(empty_file))
        test2_pass = result2 is None
        
        # 测试3: 无效格式文件
        invalid_file = Path(temp_dir) / "invalid.srt"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("这不是一个有效的SRT文件")
        result3 = VideoProcessor.generate_viral_srt(str(invalid_file))
        test3_pass = result3 is None
        
        # 测试4: 有效文件（应该成功）
        valid_file = Path(temp_dir) / "valid.srt"
        with open(valid_file, 'w', encoding='utf-8') as f:
            f.write("""1
00:00:00,000 --> 00:00:03,000
这是一个有效的测试字幕

2
00:00:03,000 --> 00:00:06,000
用于验证正常处理流程
""")
        result4 = VideoProcessor.generate_viral_srt(str(valid_file))
        test4_pass = result4 is not None
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # 统计结果
        passed_tests = sum([test1_pass, test2_pass, test3_pass, test4_pass])
        total_tests = 4
        
        logger.info(f"错误处理测试结果: {passed_tests}/{total_tests} 通过")
        logger.info(f"  - 不存在文件: {'✅' if test1_pass else '❌'}")
        logger.info(f"  - 空文件: {'✅' if test2_pass else '❌'}")
        logger.info(f"  - 无效格式: {'✅' if test3_pass else '❌'}")
        logger.info(f"  - 有效文件: {'✅' if test4_pass else '❌'}")
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"错误处理测试验证失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始修复VisionAI-ClipsMaster错误处理问题...")
    
    success_count = 0
    total_fixes = 4
    
    # 1. 修复VideoProcessor错误处理
    if fix_video_processor_error_handling():
        success_count += 1
    
    # 2. 修复UI桥接模块验证
    if fix_ui_bridge_validation():
        success_count += 1
    
    # 3. 修复第一个VideoProcessor类
    if fix_first_video_processor():
        success_count += 1
    
    # 4. 运行错误处理测试验证
    if run_error_handling_test():
        success_count += 1
    
    # 总结
    logger.info(f"错误处理修复完成: {success_count}/{total_fixes} 项修复成功")
    
    if success_count == total_fixes:
        logger.info("🎉 所有错误处理问题修复成功！")
        return True
    else:
        logger.warning(f"⚠️ 部分错误处理问题修复失败，请检查日志")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
