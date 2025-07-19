#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 中文启动器
解决所有中文字符显示问题
"""
import sys
import os
import ctypes
from pathlib import Path

def set_console_encoding():
    """设置控制台编码为UTF-8"""
    if sys.platform.startswith('win'):
        try:
            # 使用系统命令更改控制台代码页
            os.system('chcp 65001 > nul')
            print("控制台代码页已设置为UTF-8")
            
            # 使用Windows API直接设置
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleCP(65001)
            kernel32.SetConsoleOutputCP(65001)
        except Exception as e:
            print(f"设置控制台编码时出错: {e}")

def set_environment_variables():
    """设置所有必要的环境变量"""
    # 设置Python编码环境变量
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
    os.environ["LANG"] = "zh_CN.UTF-8"
    os.environ["LC_ALL"] = "zh_CN.UTF-8"
    os.environ["NLS_LANG"] = "SIMPLIFIED CHINESE_CHINA.UTF8"
    
    # 设置Qt环境变量
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_FONT_DPI"] = "96"
    
    print("已设置所有必要的环境变量")

def patch_stdout_encoding():
    """修补标准输出流的编码"""
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    print("已修补标准输出流编码")

def inject_font_fix():
    """注入字体修复"""
    try:
        # 动态修改PyQt5的默认字体
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont, QFontDatabase
        
        # 创建临时应用程序实例
        app = QApplication.instance()
        if not app:
            app = QApplication([])
        
        # 获取所有可用字体
        fontdb = QFontDatabase()
        families = fontdb.families()
        
        # 检查中文字体
        chinese_fonts = []
        priority_fonts = [
            'Microsoft YaHei UI', 'Microsoft YaHei', 
            '微软雅黑', 'SimSun', '宋体', 'SimHei', '黑体'
        ]
        
        for font_name in priority_fonts:
            for family in families:
                if font_name in family:
                    chinese_fonts.append(family)
                    break
        
        if chinese_fonts:
            # 使用第一个找到的中文字体
            selected_font = chinese_fonts[0]
            print(f"已找到中文字体: {selected_font}")
            
            # 创建QFont对象并设置为应用程序默认字体
            font = QFont(selected_font, 12)
            QApplication.setFont(font)
            
            # 存储字体名称以供其他模块使用
            os.environ["CHINESE_FONT"] = selected_font
            
        else:
            print("警告: 未找到可用的中文字体")
            
    except Exception as e:
        print(f"注入字体修复时出错: {e}")

def create_formatter_file():
    """创建Qt格式化器文件"""
    formatter_code = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

def init_qt_font():
    # 创建QApplication实例
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    # 设置字体
    chinese_font = os.environ.get("CHINESE_FONT")
    if chinese_font:
        font = QFont(chinese_font, 12)
        QApplication.setFont(font)
        return True
    return False
    
# 导出函数
__all__ = ['init_qt_font']
"""
    
    try:
        # 创建formatter.py文件
        formatter_path = Path(__file__).parent / "qt_formatter.py"
        with open(formatter_path, "w", encoding="utf-8") as f:
            f.write(formatter_code)
        print(f"创建了Qt格式化器文件: {formatter_path}")
    except Exception as e:
        print(f"创建Qt格式化器文件时出错: {e}")
        
def patch_simple_ui():
    """修补simple_ui.py文件"""
    try:
        # 获取simple_ui.py的路径
        ui_path = Path(__file__).parent / "simple_ui.py"
        if not ui_path.exists():
            print(f"无法找到UI文件: {ui_path}")
            return False
            
        # 读取文件内容
        with open(ui_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查是否已经导入了qt_formatter
        if "import qt_formatter" not in content:
            # 找到main函数
            main_func_pos = content.find("def main():")
            
            if main_func_pos != -1:
                # 在main函数开始处添加导入和初始化代码
                insert_pos = content.find("    app = QApplication(sys.argv)", main_func_pos)
                if insert_pos != -1:
                    new_code = """    # 导入Qt格式化器
    try:
        import qt_formatter
        qt_formatter.init_qt_font()
        print("已初始化Qt中文字体支持")
    except ImportError:
        pass
        
"""
                    # 插入代码
                    modified_content = content[:insert_pos] + new_code + content[insert_pos:]
                    
                    # 保存备份
                    backup_path = ui_path.parent / (ui_path.stem + ".backup.py")
                    with open(backup_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"已创建备份: {backup_path}")
                    
                    # 保存修改后的文件
                    with open(ui_path, "w", encoding="utf-8") as f:
                        f.write(modified_content)
                    print("成功修补UI文件")
                    return True
                else:
                    print("无法找到QApplication实例化代码")
            else:
                print("无法找到main函数")
        else:
            print("UI文件已包含Qt格式化器导入，无需修改")
            return True
                
    except Exception as e:
        print(f"修补UI文件时出错: {e}")
        
    return False

def run_application():
    """运行主应用程序"""
    try:
        # 导入主模块
        from simple_ui import main
        print("正在启动主应用程序...")
        main()
    except Exception as e:
        print(f"启动应用程序时出错: {e}")
        input("\n按Enter键退出...")
        sys.exit(1)

def main():
    """主函数"""
    print("===== VisionAI-ClipsMaster 中文启动器 =====")
    print("正在配置中文环境...")
    
    # 步骤1: 设置控制台编码
    set_console_encoding()
    
    # 步骤2: 设置环境变量
    set_environment_variables()
    
    # 步骤3: 修补标准输出流
    patch_stdout_encoding()
    
    # 步骤4: 注入字体修复
    inject_font_fix()
    
    # 步骤5: 创建格式化器文件
    create_formatter_file()
    
    # 步骤6: 修补UI文件
    patch_simple_ui()
    
    print("中文环境配置完成")
    print("====================================")
    
    # 步骤7: 运行应用程序
    run_application()

if __name__ == "__main__":
    main() 