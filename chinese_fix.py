#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的中文显示修复工具 - 解决所有编码和字体问题
"""
import sys
import os
import locale
import ctypes
from pathlib import Path

def fix_console_encoding():
    """修复控制台编码"""
    if sys.platform.startswith('win'):
        # 确保Windows控制台使用UTF-8
        os.system("chcp 65001 > nul")
        
        # 使用Windows API设置控制台代码页
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleCP(65001)
            kernel32.SetConsoleOutputCP(65001)
            print("Windows控制台代码页设置为UTF-8")
        except Exception as e:
            print(f"设置控制台代码页失败: {e}")

def set_environment_variables():
    """设置所有必要的环境变量"""
    # Python编码环境变量
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
    os.environ["LANG"] = "zh_CN.UTF-8"
    os.environ["LC_ALL"] = "zh_CN.UTF-8"
    os.environ["NLS_LANG"] = "SIMPLIFIED CHINESE_CHINA.UTF8"
    
    # PyQt环境变量
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_FONT_DPI"] = "96"
    
    # 强制PyQt使用UTF-8
    if hasattr(sys, 'setdefaultencoding'):
        sys.setdefaultencoding('utf-8')
    
    print("已设置所有必要的环境变量")

def setup_qt_paths():
    """设置PyQt路径"""
    try:
        from PyQt5.QtCore import QLibraryInfo
        plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
        
        if os.path.exists(plugins_path):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path
            print(f"Qt插件路径: {plugins_path}")
        else:
            # 尝试常见路径
            common_paths = [
                os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5', 'Qt', 'plugins'),
                os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins'),
                os.path.join(sys.prefix, 'lib', 'python' + sys.version[:3], 'site-packages', 'PyQt5', 'Qt5', 'plugins')
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = path
                    print(f"已设置Qt插件路径: {path}")
                    break
                    
        # 设置平台
        os.environ["QT_QPA_PLATFORM"] = "windows"
    except Exception as e:
        print(f"设置Qt路径时出错: {e}")

def find_chinese_font():
    """查找系统中的中文字体"""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFontDatabase, QFont
        
        # 创建临时应用程序实例
        temp_app = QApplication.instance()
        if not temp_app:
            temp_app = QApplication([])
        
        # 获取字体数据库并查找中文字体
        fontdb = QFontDatabase()
        all_fonts = fontdb.families()
        
        # 优选字体列表
        chinese_fonts = []
        priority_fonts = ['Microsoft YaHei', '微软雅黑', 'Microsoft YaHei UI', 'SimSun', '宋体', 'SimHei', '黑体']
        
        for font in priority_fonts:
            for available_font in all_fonts:
                if font in available_font:
                    chinese_fonts.append(available_font)
                    break
        
        print(f"找到可用的中文字体: {chinese_fonts}")
        
        if chinese_fonts:
            selected_font = chinese_fonts[0]
            print(f"选择字体: {selected_font}")
            
            # 设置全局默认字体
            default_font = QFont(selected_font, 12)
            QApplication.setFont(default_font)
            
            # 保存所选字体到环境变量，供其他模块使用
            os.environ["CHINESE_FONT"] = selected_font
            
            return selected_font
        else:
            print("警告: 未找到合适的中文字体!")
            return None
            
    except Exception as e:
        print(f"查找中文字体时出错: {e}")
        return None

def patch_simple_ui():
    """修改simple_ui.py，强制使用我们找到的中文字体"""
    try:
        # 获取我们找到的中文字体
        chinese_font = os.environ.get("CHINESE_FONT", "")
        if not chinese_font:
            print("没有找到中文字体，无法修补UI文件")
            return False
            
        # 找到simple_ui.py文件
        ui_file = Path(__file__).parent / "simple_ui.py"
        
        if not ui_file.exists():
            print(f"未找到UI文件: {ui_file}")
            return False
            
        # 读取文件内容
        content = ui_file.read_text(encoding="utf-8")
        
        # 检查是否需要修改setup_ui_style方法
        if "def setup_ui_style" in content and "Windows系统字体优先级" in content:
            # 创建备份
            backup_file = ui_file.parent / (ui_file.stem + ".bak.py")
            if not backup_file.exists():
                backup_file.write_text(content, encoding="utf-8")
                print(f"已创建备份: {backup_file}")
            
            # 修改font_family赋值逻辑，确保直接使用我们找到的中文字体
            import re
            pattern = r"([ \\t]+)font_family = self\\\\\\1get_first_available_font\\\\\\1available_fonts\\\\\\1"
            replacement = r"\\\\\\1font_family = '" + chinese_font + "'  # 直接使用已验证的中文字体"
            
            new_content = re.sub(pattern, replacement, content)
            
            # 如果内容有变化，写回文件
            if new_content != content:
                ui_file.write_text(new_content, encoding="utf-8")
                print(f"已修改UI文件，强制使用字体: {chinese_font}")
                return True
            else:
                print("UI文件不需要修改")
                return True
        else:
            print("UI文件格式不符合预期，无法自动修改")
            return False
            
    except Exception as e:
        print(f"修改UI文件时出错: {e}")
        return False

def main():
    """执行所有修复步骤"""
    print("===== VisionAI-ClipsMaster 中文显示修复工具 =====")
    print("正在执行全面修复...")
    
    # 步骤1: 修复控制台编码
    fix_console_encoding()
    
    # 步骤2: 设置环境变量
    set_environment_variables()
    
    # 步骤3: 设置Qt路径
    setup_qt_paths()
    
    # 步骤4: 查找中文字体
    chinese_font = find_chinese_font()
    
    # 步骤5: 修补UI文件
    if chinese_font:
        patch_result = patch_simple_ui()
        if patch_result:
            print("UI文件修补成功")
        else:
            print("UI文件修补失败，将使用运行时字体替换")
    
    print("修复完成，启动主应用程序...")
    print("======================================")
    
    # 导入并运行主程序
    try:
        from simple_ui import main as app_main
        app_main()
    except Exception as e:
        print(f"启动主程序失败: {e}")
        input("按Enter键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main() 