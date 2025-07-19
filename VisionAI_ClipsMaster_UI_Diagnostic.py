#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI启动问题诊断脚本

诊断UI启动失败的具体原因并提供修复方案。

作者: CKEN
版本: v1.0
日期: 2025-07-12
"""

import os
import sys
import traceback
import subprocess
from pathlib import Path
from datetime import datetime

class UIStartupDiagnostic:
    """UI启动问题诊断器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.core_path = self.project_root / "VisionAI-ClipsMaster-Core"
        self.ui_file = self.core_path / "simple_ui_fixed.py"
        self.diagnostic_results = {
            "timestamp": datetime.now().isoformat(),
            "python_environment": {},
            "dependencies": {},
            "ui_file_analysis": {},
            "import_tests": {},
            "recommendations": []
        }
        
        print(f"🔍 VisionAI-ClipsMaster UI启动诊断器")
        print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"UI文件路径: {self.ui_file}")
    
    def run_full_diagnostic(self):
        """运行完整诊断"""
        print(f"\n{'='*80}")
        print(f"开始UI启动问题诊断")
        print(f"{'='*80}")
        
        # 1. Python环境检查
        self.check_python_environment()
        
        # 2. 依赖检查
        self.check_dependencies()
        
        # 3. UI文件分析
        self.analyze_ui_file()
        
        # 4. 导入测试
        self.test_imports()
        
        # 5. 尝试启动UI
        self.test_ui_startup()
        
        # 6. 生成修复建议
        self.generate_recommendations()
        
        # 7. 保存诊断报告
        self.save_diagnostic_report()
        
        return self.diagnostic_results
    
    def check_python_environment(self):
        """检查Python环境"""
        print(f"\n{'='*60}")
        print(f"1. Python环境检查")
        print(f"{'='*60}")
        
        env_info = {}
        
        # Python版本
        env_info["python_version"] = sys.version
        env_info["python_executable"] = sys.executable
        env_info["platform"] = sys.platform
        
        print(f"  Python版本: {sys.version}")
        print(f"  Python路径: {sys.executable}")
        print(f"  操作系统: {sys.platform}")
        
        # 检查Python路径
        if "Python313" in sys.executable:
            env_info["python_path_status"] = "GOOD"
            print(f"  ✅ 使用系统Python解释器")
        else:
            env_info["python_path_status"] = "WARNING"
            print(f"  ⚠️ 未使用推荐的系统Python解释器")
        
        # 检查编码设置
        try:
            import locale
            env_info["locale"] = locale.getlocale()
            env_info["encoding"] = sys.getdefaultencoding()
            print(f"  编码设置: {sys.getdefaultencoding()}")
            print(f"  区域设置: {locale.getlocale()}")
        except Exception as e:
            env_info["locale_error"] = str(e)
            print(f"  ⚠️ 编码检查失败: {str(e)}")
        
        self.diagnostic_results["python_environment"] = env_info
    
    def check_dependencies(self):
        """检查依赖"""
        print(f"\n{'='*60}")
        print(f"2. 依赖检查")
        print(f"{'='*60}")
        
        # 关键依赖列表
        critical_deps = [
            ("PyQt6", "PyQt6"),
            ("psutil", "psutil"),
            ("requests", "requests"),
            ("pathlib", "pathlib")
        ]
        
        optional_deps = [
            ("spacy", "spacy"),
            ("numpy", "numpy"),
            ("opencv-python", "cv2")
        ]
        
        dep_status = {}
        
        # 检查关键依赖
        print(f"  关键依赖检查:")
        for dep_name, import_name in critical_deps:
            try:
                __import__(import_name)
                dep_status[dep_name] = {
                    "status": "INSTALLED",
                    "critical": True
                }
                print(f"    ✅ {dep_name}: 已安装")
            except ImportError as e:
                dep_status[dep_name] = {
                    "status": "MISSING",
                    "critical": True,
                    "error": str(e)
                }
                print(f"    ❌ {dep_name}: 缺失 - {str(e)}")
        
        # 检查可选依赖
        print(f"  可选依赖检查:")
        for dep_name, import_name in optional_deps:
            try:
                __import__(import_name)
                dep_status[dep_name] = {
                    "status": "INSTALLED",
                    "critical": False
                }
                print(f"    ✅ {dep_name}: 已安装")
            except ImportError:
                dep_status[dep_name] = {
                    "status": "MISSING",
                    "critical": False
                }
                print(f"    ⚠️ {dep_name}: 缺失（可选）")
        
        # 特别检查PyQt6子模块
        print(f"  PyQt6子模块检查:")
        pyqt6_modules = [
            "PyQt6.QtWidgets",
            "PyQt6.QtCore", 
            "PyQt6.QtGui"
        ]
        
        for module in pyqt6_modules:
            try:
                __import__(module)
                dep_status[f"{module}"] = {"status": "INSTALLED"}
                print(f"    ✅ {module}: 已安装")
            except ImportError as e:
                dep_status[f"{module}"] = {
                    "status": "MISSING",
                    "error": str(e)
                }
                print(f"    ❌ {module}: 缺失 - {str(e)}")
        
        self.diagnostic_results["dependencies"] = dep_status
    
    def analyze_ui_file(self):
        """分析UI文件"""
        print(f"\n{'='*60}")
        print(f"3. UI文件分析")
        print(f"{'='*60}")
        
        ui_analysis = {}
        
        if not self.ui_file.exists():
            ui_analysis["file_exists"] = False
            ui_analysis["error"] = "UI文件不存在"
            print(f"  ❌ UI文件不存在: {self.ui_file}")
            self.diagnostic_results["ui_file_analysis"] = ui_analysis
            return
        
        ui_analysis["file_exists"] = True
        ui_analysis["file_size"] = self.ui_file.stat().st_size
        print(f"  ✅ UI文件存在")
        print(f"  文件大小: {ui_analysis['file_size']} 字节")
        
        # 语法检查
        try:
            with open(self.ui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, str(self.ui_file), 'exec')
            ui_analysis["syntax_valid"] = True
            print(f"  ✅ 语法检查通过")
            
            # 检查关键组件
            key_components = [
                "class VisionAIClipsMaster",
                "def main()",
                "if __name__ == \"__main__\":",
                "QApplication",
                "from PyQt6"
            ]
            
            missing_components = []
            for component in key_components:
                if component not in content:
                    missing_components.append(component)
            
            if not missing_components:
                ui_analysis["components_complete"] = True
                print(f"  ✅ 关键组件完整")
            else:
                ui_analysis["components_complete"] = False
                ui_analysis["missing_components"] = missing_components
                print(f"  ⚠️ 缺少关键组件: {missing_components}")
            
        except SyntaxError as e:
            ui_analysis["syntax_valid"] = False
            ui_analysis["syntax_error"] = {
                "message": str(e),
                "line": e.lineno,
                "offset": e.offset
            }
            print(f"  ❌ 语法错误: {str(e)} (行 {e.lineno})")
        except Exception as e:
            ui_analysis["file_read_error"] = str(e)
            print(f"  ❌ 文件读取错误: {str(e)}")
        
        self.diagnostic_results["ui_file_analysis"] = ui_analysis
    
    def test_imports(self):
        """测试导入"""
        print(f"\n{'='*60}")
        print(f"4. 导入测试")
        print(f"{'='*60}")
        
        import_tests = {}
        
        # 添加项目路径
        if str(self.core_path) not in sys.path:
            sys.path.insert(0, str(self.core_path))
        
        # 测试PyQt6导入
        print(f"  测试PyQt6导入:")
        try:
            from PyQt6.QtWidgets import QApplication, QMainWindow
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            
            import_tests["pyqt6"] = {
                "status": "SUCCESS",
                "components": ["QApplication", "QMainWindow", "Qt", "QFont"]
            }
            print(f"    ✅ PyQt6核心组件导入成功")
        except Exception as e:
            import_tests["pyqt6"] = {
                "status": "FAILED",
                "error": str(e)
            }
            print(f"    ❌ PyQt6导入失败: {str(e)}")
        
        # 测试项目模块导入
        print(f"  测试项目模块导入:")
        project_modules = [
            ("src.core.model_switcher", "ModelSwitcher"),
            ("src.core.language_detector", "LanguageDetector"),
            ("src.training.zh_trainer", "ZhTrainer")
        ]
        
        for module_path, class_name in project_modules:
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                import_tests[module_path] = {"status": "SUCCESS"}
                print(f"    ✅ {module_path}: 成功")
            except Exception as e:
                import_tests[module_path] = {
                    "status": "FAILED",
                    "error": str(e)
                }
                print(f"    ❌ {module_path}: 失败 - {str(e)}")
        
        self.diagnostic_results["import_tests"] = import_tests
    
    def test_ui_startup(self):
        """测试UI启动"""
        print(f"\n{'='*60}")
        print(f"5. UI启动测试")
        print(f"{'='*60}")
        
        startup_test = {}
        
        # 尝试创建QApplication
        print(f"  测试QApplication创建:")
        try:
            from PyQt6.QtWidgets import QApplication
            import sys
            
            # 检查是否已有QApplication实例
            if QApplication.instance() is not None:
                print(f"    ⚠️ QApplication实例已存在")
                startup_test["qapp_creation"] = {
                    "status": "EXISTING",
                    "note": "QApplication实例已存在"
                }
            else:
                # 尝试创建新实例
                app = QApplication(sys.argv)
                startup_test["qapp_creation"] = {
                    "status": "SUCCESS",
                    "app_name": app.applicationName()
                }
                print(f"    ✅ QApplication创建成功")
                
                # 清理
                app.quit()
                del app
                
        except Exception as e:
            startup_test["qapp_creation"] = {
                "status": "FAILED",
                "error": str(e)
            }
            print(f"    ❌ QApplication创建失败: {str(e)}")
        
        # 尝试导入主窗口类
        print(f"  测试主窗口类导入:")
        try:
            # 这里我们不能直接导入，因为可能会触发UI创建
            # 所以我们检查文件中是否定义了主窗口类
            with open(self.ui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "class VisionAIClipsMaster" in content:
                startup_test["main_window_class"] = {
                    "status": "FOUND",
                    "note": "主窗口类定义存在"
                }
                print(f"    ✅ 主窗口类定义存在")
            else:
                startup_test["main_window_class"] = {
                    "status": "NOT_FOUND",
                    "note": "主窗口类定义不存在"
                }
                print(f"    ❌ 主窗口类定义不存在")
                
        except Exception as e:
            startup_test["main_window_class"] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"    ❌ 主窗口类检查失败: {str(e)}")
        
        self.diagnostic_results["ui_startup_test"] = startup_test
    
    def generate_recommendations(self):
        """生成修复建议"""
        print(f"\n{'='*60}")
        print(f"6. 修复建议生成")
        print(f"{'='*60}")
        
        recommendations = []
        
        # 检查依赖问题
        deps = self.diagnostic_results.get("dependencies", {})
        missing_critical = [name for name, info in deps.items() 
                          if info.get("status") == "MISSING" and info.get("critical", False)]
        
        if missing_critical:
            recommendations.append({
                "priority": "HIGH",
                "category": "依赖问题",
                "issue": f"缺少关键依赖: {', '.join(missing_critical)}",
                "solution": f"安装缺少的依赖:\npip install {' '.join(missing_critical)}",
                "command": f"pip install {' '.join(missing_critical)}"
            })
        
        # 检查PyQt6问题
        if "PyQt6" in missing_critical:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "PyQt6问题",
                "issue": "PyQt6未安装或安装不完整",
                "solution": "重新安装PyQt6:\npip uninstall PyQt6\npip install PyQt6",
                "command": "pip install PyQt6"
            })
        
        # 检查Python环境问题
        env = self.diagnostic_results.get("python_environment", {})
        if env.get("python_path_status") == "WARNING":
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Python环境",
                "issue": "未使用推荐的系统Python解释器",
                "solution": "使用系统Python解释器:\nC:\\Users\\13075\\AppData\\Local\\Programs\\Python\\Python313\\python.exe simple_ui_fixed.py"
            })
        
        # 检查UI文件问题
        ui_analysis = self.diagnostic_results.get("ui_file_analysis", {})
        if not ui_analysis.get("syntax_valid", True):
            recommendations.append({
                "priority": "HIGH",
                "category": "UI文件问题",
                "issue": "UI文件存在语法错误",
                "solution": "修复语法错误，检查文件完整性"
            })
        
        # 如果没有发现明显问题，提供通用建议
        if not recommendations:
            recommendations.append({
                "priority": "LOW",
                "category": "通用建议",
                "issue": "未发现明显问题",
                "solution": "尝试以下步骤:\n1. 重启终端\n2. 清理Python缓存\n3. 重新安装依赖"
            })
        
        self.diagnostic_results["recommendations"] = recommendations
        
        # 显示建议
        print(f"  生成了 {len(recommendations)} 条修复建议:")
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec["priority"] == "CRITICAL" else "🟡" if rec["priority"] == "HIGH" else "🟢"
            print(f"    {priority_icon} {i}. [{rec['category']}] {rec['issue']}")
    
    def save_diagnostic_report(self):
        """保存诊断报告"""
        print(f"\n{'='*60}")
        print(f"7. 保存诊断报告")
        print(f"{'='*60}")
        
        # 生成报告文件
        report_file = self.project_root / f"UI_Diagnostic_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.diagnostic_results, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ 诊断报告已保存: {report_file}")
            
        except Exception as e:
            print(f"  ❌ 保存报告失败: {str(e)}")
        
        # 生成Markdown报告
        self.generate_markdown_report()
    
    def generate_markdown_report(self):
        """生成Markdown格式的报告"""
        report_md = self.project_root / f"UI_Diagnostic_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            with open(report_md, 'w', encoding='utf-8') as f:
                f.write("# VisionAI-ClipsMaster UI启动诊断报告\n\n")
                f.write(f"**诊断时间**: {self.diagnostic_results['timestamp']}\n\n")
                
                # Python环境
                f.write("## Python环境\n\n")
                env = self.diagnostic_results.get("python_environment", {})
                f.write(f"- **Python版本**: {env.get('python_version', 'N/A')}\n")
                f.write(f"- **Python路径**: {env.get('python_executable', 'N/A')}\n")
                f.write(f"- **操作系统**: {env.get('platform', 'N/A')}\n\n")
                
                # 依赖状态
                f.write("## 依赖状态\n\n")
                deps = self.diagnostic_results.get("dependencies", {})
                for dep_name, dep_info in deps.items():
                    status_icon = "✅" if dep_info.get("status") == "INSTALLED" else "❌"
                    f.write(f"- {status_icon} **{dep_name}**: {dep_info.get('status', 'UNKNOWN')}\n")
                f.write("\n")
                
                # 修复建议
                f.write("## 修复建议\n\n")
                recommendations = self.diagnostic_results.get("recommendations", [])
                for i, rec in enumerate(recommendations, 1):
                    priority_icon = "🔴" if rec["priority"] == "CRITICAL" else "🟡" if rec["priority"] == "HIGH" else "🟢"
                    f.write(f"### {priority_icon} {i}. {rec['category']}\n\n")
                    f.write(f"**问题**: {rec['issue']}\n\n")
                    f.write(f"**解决方案**:\n```\n{rec['solution']}\n```\n\n")
            
            print(f"  ✅ Markdown报告已保存: {report_md}")
            
        except Exception as e:
            print(f"  ❌ 保存Markdown报告失败: {str(e)}")


def main():
    """主函数"""
    try:
        diagnostic = UIStartupDiagnostic()
        results = diagnostic.run_full_diagnostic()
        
        print(f"\n{'='*80}")
        print(f"诊断完成")
        print(f"{'='*80}")
        
        # 显示关键结果
        recommendations = results.get("recommendations", [])
        critical_issues = [r for r in recommendations if r["priority"] == "CRITICAL"]
        high_issues = [r for r in recommendations if r["priority"] == "HIGH"]
        
        if critical_issues:
            print(f"🔴 发现 {len(critical_issues)} 个关键问题需要立即解决")
        elif high_issues:
            print(f"🟡 发现 {len(high_issues)} 个重要问题需要解决")
        else:
            print(f"🟢 未发现关键问题，可能是环境配置问题")
        
        print(f"\n请查看详细诊断报告获取修复建议。")
        
        return 0 if not critical_issues else 1
        
    except KeyboardInterrupt:
        print("\n诊断被用户中断")
        return 1
    except Exception as e:
        print(f"\n诊断过程出错: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
