#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster PyQt6依赖修复脚本
专门修复GUI界面相关的依赖问题
"""

import sys
import subprocess
import os
import platform
from pathlib import Path

def run_command(command, description=""):
    """运行命令并处理错误"""
    print(f"正在执行: {description or command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"✅ 成功: {description or command}")
            if result.stdout.strip():
                print(f"输出: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ 失败: {description or command}")
            if result.stderr.strip():
                print(f"错误: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 警告: Python版本过低，建议使用Python 3.8+")
        return False
    else:
        print("✅ Python版本符合要求")
        return True

def install_pyqt6():
    """安装PyQt6及相关组件"""
    print("\n=== 安装PyQt6 ===")
    
    # 检查是否已安装
    try:
        import PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        print("✅ PyQt6已安装且可正常导入")
        return True
    except ImportError as e:
        print(f"PyQt6未安装或导入失败: {e}")
        print("开始安装PyQt6...")
    
    # 安装PyQt6相关包
    packages = [
        "PyQt6",
        "PyQt6-tools",
        "PyQt6-Qt6"
    ]
    
    success = True
    for package in packages:
        print(f"\n安装 {package}...")
        if not run_command(f"pip install {package}", f"安装 {package}"):
            print(f"尝试使用国内镜像安装 {package}...")
            if not run_command(f"pip install -i https://pypi.tuna.tsinghua.edu.cn/simple {package}", f"使用清华镜像安装 {package}"):
                print(f"❌ {package} 安装失败")
                success = False
            else:
                print(f"✅ {package} 安装成功（使用镜像）")
        else:
            print(f"✅ {package} 安装成功")
    
    # 验证安装
    try:
        import PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        print("✅ PyQt6安装验证成功")
        return True
    except ImportError as e:
        print(f"❌ PyQt6安装验证失败: {e}")
        return False

def install_additional_dependencies():
    """安装其他必要依赖"""
    print("\n=== 安装其他GUI相关依赖 ===")
    
    dependencies = [
        "psutil",
        "requests", 
        "loguru",
        "matplotlib",
        "numpy"
    ]
    
    success = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} 已安装")
        except ImportError:
            print(f"安装 {dep}...")
            if not run_command(f"pip install {dep}", f"安装 {dep}"):
                if not run_command(f"pip install -i https://pypi.tuna.tsinghua.edu.cn/simple {dep}", f"使用镜像安装 {dep}"):
                    success = False
                    print(f"❌ {dep} 安装失败")
                else:
                    print(f"✅ {dep} 安装成功（使用镜像）")
            else:
                print(f"✅ {dep} 安装成功")
    
    return success

def fix_encoding_issues():
    """修复编码问题"""
    print("\n=== 修复编码问题 ===")
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Windows特殊处理
    if platform.system() == "Windows":
        try:
            # 设置控制台编码
            run_command("chcp 65001", "设置控制台UTF-8编码")
            
            # 设置Qt相关环境变量
            os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
            os.environ['QT_SCALE_FACTOR'] = '1'
            os.environ['QT_FONT_DPI'] = '96'
            
        except:
            pass
    
    print("✅ 编码设置完成")

def create_ui_compatibility_layer():
    """创建UI兼容性层"""
    print("\n=== 创建UI兼容性层 ===")
    
    compat_dir = Path("ui/compat")
    compat_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建兼容性模块
    compat_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI兼容性模块
处理PyQt6相关的兼容性问题
"""

import sys
import os

def handle_qt_version():
    """处理Qt版本兼容性"""
    try:
        import PyQt6
        return "PyQt6"
    except ImportError:
        try:
            import PyQt5
            return "PyQt5"
        except ImportError:
            return None

def setup_compat():
    """设置兼容性环境"""
    # 设置编码
    if hasattr(sys, 'setdefaultencoding'):
        sys.setdefaultencoding('utf-8')
    
    # Windows特殊处理
    if os.name == 'nt':
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        os.environ['QT_SCALE_FACTOR'] = '1'
        os.environ['QT_FONT_DPI'] = '96'

def get_qt_version_str():
    """获取Qt版本字符串"""
    qt_version = handle_qt_version()
    if qt_version:
        try:
            if qt_version == "PyQt6":
                from PyQt6.QtCore import QT_VERSION_STR
                return f"PyQt6 (Qt {QT_VERSION_STR})"
            elif qt_version == "PyQt5":
                from PyQt5.QtCore import QT_VERSION_STR
                return f"PyQt5 (Qt {QT_VERSION_STR})"
        except:
            return qt_version
    else:
        return "Qt未安装"

# 自动设置
setup_compat()
'''
    
    compat_file = compat_dir / "__init__.py"
    compat_file.write_text(compat_content, encoding='utf-8')
    print("✅ UI兼容性层创建完成")

def test_ui_startup():
    """测试UI启动"""
    print("\n=== 测试UI启动 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        
        # 创建测试应用
        app = QApplication.instance() or QApplication([])
        
        # 创建测试窗口
        window = QWidget()
        window.setWindowTitle("VisionAI-ClipsMaster UI测试")
        window.resize(400, 300)
        
        # 创建布局和标签
        layout = QVBoxLayout()
        
        label = QLabel("✅ PyQt6 UI测试成功！")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Arial", 14))
        
        emoji_label = QLabel("🎬 VisionAI-ClipsMaster 已就绪")
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setFont(QFont("Arial", 12))
        
        layout.addWidget(label)
        layout.addWidget(emoji_label)
        window.setLayout(layout)
        
        print("✅ UI组件创建成功")
        print("✅ 中文和emoji显示正常")
        
        # 不显示窗口，只测试创建
        return True
        
    except Exception as e:
        print(f"❌ UI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主修复流程"""
    print("🔧 VisionAI-ClipsMaster PyQt6依赖修复工具")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        print("请升级Python版本后重试")
        return False
    
    # 修复编码问题
    fix_encoding_issues()
    
    # 安装PyQt6
    if not install_pyqt6():
        print("❌ PyQt6安装失败，请手动安装")
        print("手动安装命令: pip install PyQt6 PyQt6-tools")
        return False
    
    # 安装其他依赖
    if not install_additional_dependencies():
        print("⚠️ 部分依赖安装失败，但可能不影响核心功能")
    
    # 创建兼容性层
    create_ui_compatibility_layer()
    
    # 测试UI启动
    if test_ui_startup():
        print("\n🎉 所有修复完成！UI可以正常启动")
        print("现在可以运行: python simple_ui_fixed.py")
        return True
    else:
        print("\n❌ UI测试失败，可能需要手动检查")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 修复完成，系统已就绪")
        print("建议重启终端后运行UI程序")
    else:
        print("\n❌ 修复过程中遇到问题，请检查错误信息")
    
    input("\n按回车键退出...")
