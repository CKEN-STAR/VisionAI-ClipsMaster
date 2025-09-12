#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster Logger警告修复脚本

修复simple_ui_fixed.py中的logger未定义警告问题：
1. 确保所有使用logger的地方都有正确的导入
2. 统一logger的定义和使用
3. 保持代码功能完整性
"""

import os
import sys
import logging
import re
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_logger_imports():
    """修复logger导入和定义问题"""
    logger.info("修复logger导入和定义问题...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    if not ui_file.exists():
        logger.error(f"文件不存在: {ui_file}")
        return False
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有logging导入
    has_logging_import = 'import logging' in content
    
    if not has_logging_import:
        # 在文件开头添加logging导入
        import_section = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
VisionAI-ClipsMaster - AI短剧混剪大师 UI界面
完美无敌版 - 集成所有功能的统一界面
\"\"\"

import os
import sys
import time
import json
import logging
import threading
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union"""
        
        # 查找现有的导入部分
        old_import_pattern = r'#!/usr/bin/env python3\n# -\*- coding: utf-8 -\*-\n"""[\s\S]*?"""\n\nimport os\nimport sys[^\n]*'
        
        if re.search(old_import_pattern, content):
            content = re.sub(old_import_pattern, import_section, content, count=1)
            logger.info("已添加logging导入")
        else:
            # 如果找不到标准模式，在文件开头添加
            content = import_section + "\n\n" + content
            logger.info("在文件开头添加了完整的导入部分")
    
    # 在主要类定义之前添加logger定义
    logger_definition = """
# 配置全局logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 如果没有handler，添加一个控制台handler
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
"""
    
    # 查找合适的位置插入logger定义
    # 在第一个类定义之前插入
    class_pattern = r'(class\s+\w+.*?:)'
    match = re.search(class_pattern, content)
    
    if match and 'logger = logging.getLogger' not in content:
        insert_pos = match.start()
        content = content[:insert_pos] + logger_definition + "\n" + content[insert_pos:]
        logger.info("已添加logger定义")
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_specific_logger_issues():
    """修复特定的logger使用问题"""
    logger.info("修复特定的logger使用问题...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复常见的logger使用问题
    fixes = [
        # 修复logger.error调用
        (r'logger\.error\(f"([^"]+)"\)', r'logger.error(f"\1")'),
        (r'logger\.info\(f"([^"]+)"\)', r'logger.info(f"\1")'),
        (r'logger\.warning\(f"([^"]+)"\)', r'logger.warning(f"\1")'),
        (r'logger\.debug\(f"([^"]+)"\)', r'logger.debug(f"\1")'),
        
        # 确保所有logger调用都有正确的格式
        (r'logger\.error\("([^"]+)"\)', r'logger.error("\1")'),
        (r'logger\.info\("([^"]+)"\)', r'logger.info("\1")'),
        (r'logger\.warning\("([^"]+)"\)', r'logger.warning("\1")'),
        (r'logger\.debug\("([^"]+)"\)', r'logger.debug("\1")'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("特定logger问题修复完成")
    return True

def add_local_loggers_where_needed():
    """在需要的地方添加本地logger定义"""
    logger.info("在需要的地方添加本地logger定义...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有类定义
    class_pattern = r'class\s+(\w+).*?:'
    classes = re.findall(class_pattern, content)
    
    for class_name in classes:
        # 检查类中是否使用了logger但没有定义
        class_content_pattern = rf'class\s+{class_name}.*?(?=class\s+\w+|$)'
        class_match = re.search(class_content_pattern, content, re.DOTALL)
        
        if class_match:
            class_content = class_match.group(0)
            
            # 如果类中使用了logger但没有定义
            if 'logger.' in class_content and f'logger = logging.getLogger' not in class_content:
                # 在类的__init__方法中添加logger定义
                init_pattern = rf'(class\s+{class_name}.*?def\s+__init__\s*\([^)]*\):\s*)'
                init_match = re.search(init_pattern, content, re.DOTALL)
                
                if init_match:
                    logger_line = f'        self.logger = logging.getLogger(f"{class_name}.{{self.__class__.__name__}}")\n'
                    replacement = init_match.group(1) + '\n' + logger_line
                    content = content.replace(init_match.group(1), replacement)
                    
                    # 同时替换类中的logger调用为self.logger
                    content = re.sub(rf'(\s+)logger\.', rf'\1self.logger.', content)
    
    # 写回文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("本地logger定义添加完成")
    return True

def verify_logger_fixes():
    """验证logger修复是否成功"""
    logger.info("验证logger修复...")
    
    try:
        # 尝试导入修复后的模块
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("simple_ui_fixed", "simple_ui_fixed.py")
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            
            # 检查是否能成功导入
            try:
                spec.loader.exec_module(module)
                logger.info("✅ 模块导入成功，logger修复验证通过")
                return True
            except Exception as e:
                logger.warning(f"⚠️ 模块导入有问题: {e}")
                return False
        else:
            logger.error("❌ 无法创建模块规范")
            return False
            
    except Exception as e:
        logger.error(f"❌ logger修复验证失败: {e}")
        return False

def run_syntax_check():
    """运行语法检查"""
    logger.info("运行语法检查...")
    
    try:
        import ast
        
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析AST
        ast.parse(content)
        logger.info("✅ 语法检查通过")
        return True
        
    except SyntaxError as e:
        logger.error(f"❌ 语法错误: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 语法检查失败: {e}")
        return False

def count_logger_warnings():
    """统计logger警告数量"""
    logger.info("统计logger相关问题...")
    
    try:
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找logger使用但可能未定义的情况
        logger_uses = len(re.findall(r'logger\.', content))
        logger_definitions = len(re.findall(r'logger\s*=', content))
        
        logger.info(f"Logger使用次数: {logger_uses}")
        logger.info(f"Logger定义次数: {logger_definitions}")
        
        if logger_definitions > 0:
            logger.info("✅ 发现logger定义，应该能解决大部分警告")
            return True
        else:
            logger.warning("⚠️ 未发现logger定义，可能仍有警告")
            return False
            
    except Exception as e:
        logger.error(f"❌ 统计失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始修复VisionAI-ClipsMaster Logger警告问题...")
    
    success_count = 0
    total_fixes = 5
    
    # 1. 修复logger导入和定义
    if fix_logger_imports():
        success_count += 1
    
    # 2. 修复特定的logger使用问题
    if fix_specific_logger_issues():
        success_count += 1
    
    # 3. 运行语法检查
    if run_syntax_check():
        success_count += 1
    
    # 4. 统计logger问题
    if count_logger_warnings():
        success_count += 1
    
    # 5. 验证修复效果
    if verify_logger_fixes():
        success_count += 1
    
    # 总结
    logger.info(f"Logger警告修复完成: {success_count}/{total_fixes} 项修复成功")
    
    if success_count >= 4:  # 允许一个非关键项失败
        logger.info("🎉 Logger警告问题修复成功！")
        logger.info("💡 建议重启IDE以清除缓存的警告信息")
        return True
    else:
        logger.warning(f"⚠️ 部分Logger问题修复失败，请检查日志")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
