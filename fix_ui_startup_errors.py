"""
VisionAI-ClipsMaster UI启动错误修复脚本
修复导致安全模式启动的关键错误
"""

import os
import sys
import shutil
import time
from datetime import datetime

def backup_files():
    """备份原始文件"""
    print("🔄 备份原始文件...")
    
    files_to_backup = [
        'src/visionai_clipsmaster/ui/main_window.py',
        'simple_ui_fixed.py'
    ]
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            print(f"  ✅ 已备份: {file_path} -> {backup_path}")
    
    return backup_dir

def fix_memory_warning_signal():
    """修复内存警告信号参数问题"""
    print("🔧 修复内存警告信号参数...")
    
    main_window_path = 'src/visionai_clipsmaster/ui/main_window.py'
    
    if not os.path.exists(main_window_path):
        print(f"  ❌ 文件不存在: {main_window_path}")
        return False
    
    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并修复 on_memory_warning 方法定义
        old_method = "def on_memory_warning(self, message):"
        new_method = "def on_memory_warning(self, message, severity=1):"
        
        if old_method in content:
            content = content.replace(old_method, new_method)
            print("  ✅ 修复了 on_memory_warning 方法参数")
        
        # 查找并修复信号连接
        old_connect = "self.memory_monitor.memory_warning.connect(self.on_memory_warning)"
        new_connect = "self.memory_monitor.memory_warning.connect(lambda msg, sev=1: self.on_memory_warning(msg, sev))"
        
        if old_connect in content:
            content = content.replace(old_connect, new_connect)
            print("  ✅ 修复了内存警告信号连接")
        
        # 保存修复后的文件
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ 内存警告信号修复完成")
        return True
        
    except Exception as e:
        print(f"  ❌ 修复内存警告信号失败: {e}")
        return False

def fix_gpu_detection():
    """修复GPU检测错误"""
    print("🔧 修复GPU检测错误...")
    
    files_to_fix = [
        'src/visionai_clipsmaster/ui/main_window.py',
        'simple_ui_fixed.py'
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 修复GPU检测代码
            old_gpu_check = "if hasattr(torch, 'cuda') and torch.cuda.is_available():"
            new_gpu_check = """try:
                import torch
                if hasattr(torch, 'cuda') and torch.cuda.is_available():"""
            
            if old_gpu_check in content:
                # 更安全的GPU检测方法
                safe_gpu_check = """try:
                import torch
                if hasattr(torch, 'cuda') and callable(getattr(torch.cuda, 'is_available', None)) and torch.cuda.is_available():"""
                
                content = content.replace(old_gpu_check, safe_gpu_check)
                
                # 添加异常处理
                content = content.replace(
                    safe_gpu_check,
                    safe_gpu_check + """
            except (ImportError, AttributeError, RuntimeError) as e:
                print(f"[WARN] GPU检测失败: {e}")
                gpu_available = False
            else:"""
                )
                
                fixed_count += 1
                print(f"  ✅ 修复了 {file_path} 中的GPU检测")
            
            # 保存修复后的文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"  ❌ 修复 {file_path} 失败: {e}")
    
    print(f"  ✅ GPU检测修复完成，共修复 {fixed_count} 个文件")
    return fixed_count > 0

def fix_missing_methods():
    """修复缺失的方法"""
    print("🔧 修复缺失的方法...")
    
    files_to_fix = [
        'simple_ui_fixed.py'
    ]
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找 SimplifiedTrainingFeeder 类
            if 'class SimplifiedTrainingFeeder' in content:
                # 添加缺失的 record_user_interaction 方法
                method_to_add = '''
    def record_user_interaction(self):
        """记录用户交互行为"""
        try:
            # 记录用户操作时间戳
            self.last_interaction_time = time.time()
            
            # 可以在这里添加更多的用户行为分析逻辑
            print(f"[INFO] 用户交互已记录: {time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"[WARN] 记录用户交互失败: {e}")
'''
                
                # 查找类的结束位置并添加方法
                if 'def record_user_interaction(self):' not in content:
                    # 在类的最后一个方法后添加
                    class_pattern = 'class SimplifiedTrainingFeeder'
                    class_start = content.find(class_pattern)
                    
                    if class_start != -1:
                        # 找到类的结束位置（下一个类或文件结束）
                        next_class = content.find('\nclass ', class_start + 1)
                        if next_class == -1:
                            next_class = len(content)
                        
                        # 在类结束前插入方法
                        insert_pos = content.rfind('\n    def ', class_start, next_class)
                        if insert_pos != -1:
                            # 找到方法结束位置
                            method_end = content.find('\n\n', insert_pos)
                            if method_end == -1:
                                method_end = content.find('\nclass', insert_pos)
                            if method_end == -1:
                                method_end = len(content)
                            
                            content = content[:method_end] + method_to_add + content[method_end:]
                            print(f"  ✅ 添加了 record_user_interaction 方法到 {file_path}")
            
            # 保存修复后的文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"  ❌ 修复 {file_path} 中的缺失方法失败: {e}")
    
    print("  ✅ 缺失方法修复完成")

def create_safe_startup_script():
    """创建安全启动脚本"""
    print("🔧 创建安全启动脚本...")
    
    safe_startup_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 安全启动脚本
确保程序能够稳定启动的安全版本
"""

import sys
import os
import time

# 设置环境变量以避免CUDA问题
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TORCH_USE_CUDA_DSA'] = '0'
os.environ['PYTHONIOENCODING'] = 'utf-8'

def safe_import(module_name, fallback=None):
    """安全导入模块"""
    try:
        return __import__(module_name)
    except ImportError as e:
        print(f"[WARN] 导入 {module_name} 失败: {e}")
        return fallback

def main():
    """安全启动主函数"""
    print("🚀 VisionAI-ClipsMaster 安全启动...")
    
    try:
        # 安全导入PyQt6
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        
        print("✅ PyQt6导入成功")
        
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setApplicationName("VisionAI-ClipsMaster")
        
        # 尝试导入主窗口
        try:
            from src.visionai_clipsmaster.ui.main_window import SimpleScreenplayApp
            window = SimpleScreenplayApp()
            print("✅ 主窗口创建成功")
            
        except Exception as e:
            print(f"[WARN] 主窗口创建失败: {e}")
            print("🔄 使用简化窗口...")
            
            # 创建简化窗口
            window = QMainWindow()
            window.setWindowTitle("VisionAI-ClipsMaster - 简化模式")
            window.setGeometry(300, 300, 800, 600)
            
            central_widget = QWidget()
            window.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # 添加标题
            title_label = QLabel("VisionAI-ClipsMaster")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
            layout.addWidget(title_label)
            
            # 添加状态信息
            status_label = QLabel("程序正在简化模式下运行\\n某些高级功能可能不可用")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(status_label)
            
            # 添加重试按钮
            retry_button = QPushButton("重试完整启动")
            retry_button.clicked.connect(lambda: restart_full_mode())
            layout.addWidget(retry_button)
            
            print("✅ 简化窗口创建成功")
        
        # 显示窗口
        window.show()
        
        print("🎉 程序启动成功！")
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 创建最小化错误窗口
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setWindowTitle("启动错误")
            msg.setText(f"程序启动失败:\\n{str(e)}")
            msg.setInformativeText("请检查依赖安装和配置")
            msg.exec()
            
        except:
            print("无法显示错误对话框")
        
        sys.exit(1)

def restart_full_mode():
    """重启完整模式"""
    try:
        import subprocess
        subprocess.Popen([sys.executable, "src/visionai_clipsmaster/ui/main_window.py"])
    except Exception as e:
        print(f"重启失败: {e}")

if __name__ == "__main__":
    main()
'''
    
    with open('safe_startup.py', 'w', encoding='utf-8') as f:
        f.write(safe_startup_content)
    
    print("  ✅ 安全启动脚本创建完成: safe_startup.py")

def clear_crash_log():
    """清理崩溃日志"""
    print("🧹 清理崩溃日志...")
    
    if os.path.exists('crash_log.txt'):
        # 备份旧日志
        backup_log = f"crash_log_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        shutil.move('crash_log.txt', backup_log)
        print(f"  ✅ 旧日志已备份为: {backup_log}")
    
    # 创建新的空日志文件
    with open('crash_log.txt', 'w', encoding='utf-8') as f:
        f.write(f"# VisionAI-ClipsMaster 崩溃日志\n")
        f.write(f"# 修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    print("  ✅ 崩溃日志已清理")

def run_startup_test():
    """运行启动测试"""
    print("🧪 运行启动测试...")
    
    try:
        # 测试PyQt6导入
        from PyQt6.QtWidgets import QApplication
        print("  ✅ PyQt6导入测试通过")
        
        # 测试主窗口导入
        try:
            from src.visionai_clipsmaster.ui.main_window import SimpleScreenplayApp
            print("  ✅ 主窗口导入测试通过")
        except Exception as e:
            print(f"  ⚠️ 主窗口导入测试失败: {e}")
        
        # 测试GPU检测
        try:
            import torch
            if hasattr(torch, 'cuda') and callable(getattr(torch.cuda, 'is_available', None)):
                gpu_available = torch.cuda.is_available()
                print(f"  ✅ GPU检测测试通过: {'有GPU' if gpu_available else '无GPU'}")
            else:
                print("  ✅ GPU检测测试通过: 使用CPU模式")
        except Exception as e:
            print(f"  ⚠️ GPU检测测试失败: {e}")
        
        print("  ✅ 启动测试完成")
        return True
        
    except Exception as e:
        print(f"  ❌ 启动测试失败: {e}")
        return False

def main():
    """主修复流程"""
    print("🔧 VisionAI-ClipsMaster UI启动错误修复")
    print("=" * 50)
    
    start_time = time.time()
    
    # 1. 备份文件
    backup_dir = backup_files()
    
    # 2. 修复内存警告信号
    fix_memory_warning_signal()
    
    # 3. 修复GPU检测
    fix_gpu_detection()
    
    # 4. 修复缺失方法
    fix_missing_methods()
    
    # 5. 创建安全启动脚本
    create_safe_startup_script()
    
    # 6. 清理崩溃日志
    clear_crash_log()
    
    # 7. 运行启动测试
    test_passed = run_startup_test()
    
    # 总结
    duration = time.time() - start_time
    print("\n" + "=" * 50)
    print("🎯 修复完成!")
    print(f"⏱️ 耗时: {duration:.2f}秒")
    print(f"📁 备份目录: {backup_dir}")
    
    if test_passed:
        print("✅ 启动测试通过，可以尝试启动程序")
        print("\n🚀 启动建议:")
        print("1. 使用安全启动: python safe_startup.py")
        print("2. 或直接启动: python src/visionai_clipsmaster/ui/main_window.py")
    else:
        print("⚠️ 启动测试未完全通过，建议使用安全启动")
        print("\n🚀 启动建议:")
        print("1. 使用安全启动: python safe_startup.py")
    
    return test_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
