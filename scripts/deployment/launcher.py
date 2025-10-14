#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 主启动器
完全自包含整合包的统一入口点
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional

class VisionAILauncher:
    """VisionAI-ClipsMaster 启动器"""
    
    def __init__(self):
        # 获取应用根目录
        if getattr(sys, 'frozen', False):
            self.app_root = Path(sys.executable).parent
        else:
            self.app_root = Path(__file__).parent.parent
        
        # 设置工作目录
        os.chdir(str(self.app_root))
        
        # 添加应用目录到Python路径
        sys.path.insert(0, str(self.app_root))
        sys.path.insert(0, str(self.app_root / "packaging"))
        
        self.main_script = self.app_root / "simple_ui_fixed.py"
        self.config_file = self.app_root / "config.json"
        
    def load_config(self) -> dict:
        """加载应用配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"配置文件加载失败: {e}")
        
        # 默认配置
        return {
            "app_name": "VisionAI-ClipsMaster",
            "version": "1.0.1",
            "self_contained": True,
            "first_run": True
        }
    
    def save_config(self, config: dict):
        """保存应用配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"配置文件保存失败: {e}")
    
    def show_welcome_message(self):
        """显示欢迎信息"""
        print("=" * 60)
        print("🎬 VisionAI-ClipsMaster v1.0.1")
        print("   AI驱动的短剧混剪工具")
        print("=" * 60)
        print()
    
    def run_startup_validation(self) -> bool:
        """运行启动验证"""
        try:
            from startup_validator import StartupValidator
            
            print("🔍 正在进行系统检查...")
            validator = StartupValidator()
            results = validator.run_full_validation()
            validator.save_validation_report()
            
            return results["overall_status"] in ["ready", "ready_with_warnings"]
            
        except Exception as e:
            print(f"❌ 启动验证失败: {e}")
            print("将尝试直接启动...")
            return True  # 验证失败时仍尝试启动
    
    def setup_model_paths(self):
        """设置模型路径"""
        try:
            from model_path_manager import get_model_path_manager
            
            path_manager = get_model_path_manager()
            
            # 验证自包含性
            verification = path_manager.verify_self_contained()
            if not verification["is_self_contained"]:
                print("⚠️ 检测到外部依赖，正在修复...")
                for dep in verification["external_dependencies"]:
                    print(f"   - {dep}")
            
            print("✅ 模型路径配置完成")
            return True
            
        except Exception as e:
            print(f"❌ 模型路径设置失败: {e}")
            return False
    
    def check_and_download_models(self) -> bool:
        """检查并下载模型"""
        try:
            from model_path_manager import ensure_models_available
            
            print("🤖 检查AI模型...")
            return ensure_models_available()
            
        except Exception as e:
            print(f"❌ 模型检查失败: {e}")
            return False
    
    def launch_main_application(self) -> bool:
        """启动主应用程序"""
        try:
            if not self.main_script.exists():
                print(f"❌ 主程序文件不存在: {self.main_script}")
                return False
            
            print("🚀 启动主程序...")
            print(f"   程序路径: {self.main_script}")
            
            # 直接导入并运行主程序
            try:
                # 确保主程序目录在路径中
                main_dir = self.main_script.parent
                if str(main_dir) not in sys.path:
                    sys.path.insert(0, str(main_dir))
                
                # 导入并运行主程序
                import simple_ui_fixed
                
                # 如果主程序有main函数，调用它
                if hasattr(simple_ui_fixed, 'main'):
                    simple_ui_fixed.main()
                else:
                    # 否则直接运行模块
                    exec(open(self.main_script, encoding='utf-8').read())
                
                return True
                
            except Exception as e:
                print(f"❌ 主程序启动失败: {e}")
                print("尝试使用subprocess启动...")
                
                # 备用方案：使用subprocess
                result = subprocess.run([
                    sys.executable, str(self.main_script)
                ], cwd=str(self.app_root))
                
                return result.returncode == 0
                
        except Exception as e:
            print(f"❌ 应用启动失败: {e}")
            return False
    
    def handle_first_run(self, config: dict):
        """处理首次运行"""
        if config.get("first_run", True):
            print("👋 欢迎使用VisionAI-ClipsMaster！")
            print()
            print("这是您首次运行此程序，系统将进行初始化...")
            print("• 检查系统环境")
            print("• 下载AI模型（如需要）")
            print("• 配置工作环境")
            print()
            
            # 标记为非首次运行
            config["first_run"] = False
            self.save_config(config)
    
    def run(self) -> bool:
        """运行启动器"""
        try:
            # 显示欢迎信息
            self.show_welcome_message()
            
            # 加载配置
            config = self.load_config()
            
            # 处理首次运行
            self.handle_first_run(config)
            
            # 1. 运行启动验证
            if not self.run_startup_validation():
                print("❌ 系统检查未通过，无法启动")
                return False
            
            # 2. 设置模型路径
            if not self.setup_model_paths():
                print("⚠️ 模型路径设置失败，但将继续启动")
            
            # 3. 检查并下载模型
            if not self.check_and_download_models():
                print("⚠️ 模型检查失败，某些功能可能不可用")
            
            # 4. 启动主应用程序
            print()
            print("🎬 启动VisionAI-ClipsMaster主界面...")
            success = self.launch_main_application()
            
            if success:
                print("✅ 程序启动成功")
            else:
                print("❌ 程序启动失败")
            
            return success
            
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断启动")
            return False
        except Exception as e:
            print(f"❌ 启动器异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_error_help(self):
        """显示错误帮助信息"""
        print()
        print("🆘 启动失败帮助:")
        print("1. 检查系统要求:")
        print("   - Windows 10/11 (64位)")
        print("   - 内存: 4GB以上")
        print("   - 硬盘空间: 15GB以上")
        print()
        print("2. 检查网络连接（首次运行需要下载模型）")
        print()
        print("3. 查看日志文件:")
        print(f"   - {self.app_root / 'logs' / 'startup_validation.json'}")
        print(f"   - {self.app_root / 'logs' / 'visionai.log'}")
        print()
        print("4. 尝试以管理员身份运行")
        print()

def main():
    """主函数"""
    launcher = VisionAILauncher()
    
    try:
        success = launcher.run()
        
        if not success:
            launcher.show_error_help()
            print("按回车键退出...")
            input()
            return False
        
        return True
        
    except Exception as e:
        print(f"启动器严重错误: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n按回车键退出...")
        input()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
