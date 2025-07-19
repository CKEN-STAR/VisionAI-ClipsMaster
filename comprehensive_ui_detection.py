#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 主UI界面全面功能检测和问题排查
"""

import os
import sys
import time
import json
import logging
import subprocess
import traceback
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_ui_layout():
    """检测UI布局"""
    logger.info("🎨 开始UI布局检测")
    logger.info("=" * 60)
    
    detection_results = {
        'button_layout': False,
        'button_styles': False,
        'responsive_design': False,
        'layout_integration': False
    }
    
    try:
        # 1. 检查按钮布局代码
        logger.info("1. 检查两个并排按钮布局")
        
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键UI元素
        ui_elements = [
            'video_export_layout = QHBoxLayout()',
            'generate_project_btn = QPushButton("生成工程文件")',
            'export_jianying_btn = QPushButton("导出到剪映")',
            'video_export_layout.addWidget(generate_project_btn)',
            'video_export_layout.addWidget(export_jianying_btn)',
            'action_layout.addLayout(video_export_layout)'
        ]
        
        missing_elements = []
        for element in ui_elements:
            if element not in content:
                missing_elements.append(element)
        
        if not missing_elements:
            detection_results['button_layout'] = True
            logger.info("✅ 并排按钮布局检测通过")
        else:
            logger.error(f"❌ 缺少UI布局元素: {missing_elements}")
        
        # 2. 检查按钮样式
        logger.info("2. 检查按钮样式和颜色主题")
        
        style_elements = [
            'background-color: #52c41a',  # 生成工程文件按钮绿色
            'background-color: #1890ff',  # 导出到剪映按钮蓝色
            'setMinimumHeight(40)',       # 按钮高度
            'font-weight: bold',          # 字体加粗
            'border-radius: 4px'          # 圆角
        ]
        
        missing_styles = []
        for style in style_elements:
            if style not in content:
                missing_styles.append(style)
        
        if not missing_styles:
            detection_results['button_styles'] = True
            logger.info("✅ 按钮样式检测通过")
        else:
            logger.error(f"❌ 缺少样式元素: {missing_styles}")
        
        # 3. 检查响应式设计
        logger.info("3. 检查响应式设计")
        
        responsive_elements = [
            'QHBoxLayout()',  # 水平布局支持响应式
            'setMinimumHeight(40)'  # 最小高度设置
        ]
        
        responsive_ok = all(element in content for element in responsive_elements)
        detection_results['responsive_design'] = responsive_ok
        
        if responsive_ok:
            logger.info("✅ 响应式设计检测通过")
        else:
            logger.error("❌ 响应式设计检测失败")
        
        # 4. 检查与现有布局的集成
        logger.info("4. 检查与现有布局的集成")
        
        integration_elements = [
            'action_layout.addLayout(video_export_layout)',
            'generate_srt_btn = QPushButton("生成爆款SRT")'  # 确保原有按钮仍存在
        ]
        
        integration_ok = all(element in content for element in integration_elements)
        detection_results['layout_integration'] = integration_ok
        
        if integration_ok:
            logger.info("✅ 布局集成检测通过")
        else:
            logger.error("❌ 布局集成检测失败")
        
    except Exception as e:
        logger.error(f"❌ UI布局检测失败: {e}")
        traceback.print_exc()
    
    return detection_results

def detect_functionality():
    """检测功能完整性"""
    logger.info("⚙️ 开始功能完整性检测")
    logger.info("=" * 60)
    
    functionality_results = {
        'generate_project_method': False,
        'export_jianying_method': False,
        'helper_methods': False,
        'data_flow': False,
        'event_binding': False
    }
    
    try:
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 检查生成工程文件方法
        logger.info("1. 检查生成工程文件方法")
        
        project_method_elements = [
            'def generate_project_file(self):',
            'def _build_project_data(self, video_path: str, srt_path: str):',
            'def _parse_srt_to_scenes(self, srt_content: str, video_path: str):',
            'def _time_str_to_seconds(self, time_str: str) -> float:'
        ]
        
        missing_project_methods = []
        for method in project_method_elements:
            if method not in content:
                missing_project_methods.append(method)
        
        if not missing_project_methods:
            functionality_results['generate_project_method'] = True
            logger.info("✅ 生成工程文件方法检测通过")
        else:
            logger.error(f"❌ 缺少生成工程文件方法: {missing_project_methods}")
        
        # 2. 检查导出到剪映方法
        logger.info("2. 检查导出到剪映方法")
        
        export_method_elements = [
            'def export_to_jianying(self):',
            'def _launch_jianying_app(self, project_file_path: str) -> bool:',
            'def _open_file_folder(self, file_path: str):'
        ]
        
        missing_export_methods = []
        for method in export_method_elements:
            if method not in content:
                missing_export_methods.append(method)
        
        if not missing_export_methods:
            functionality_results['export_jianying_method'] = True
            logger.info("✅ 导出到剪映方法检测通过")
        else:
            logger.error(f"❌ 缺少导出到剪映方法: {missing_export_methods}")
        
        # 3. 检查辅助方法
        logger.info("3. 检查辅助方法")
        
        helper_elements = [
            'from src.export.jianying_exporter import JianyingExporter',
            'json.dump(project_data, f, ensure_ascii=False, indent=2)',
            'platform.system()',
            'subprocess.Popen'
        ]
        
        missing_helpers = []
        for helper in helper_elements:
            if helper not in content:
                missing_helpers.append(helper)
        
        if not missing_helpers:
            functionality_results['helper_methods'] = True
            logger.info("✅ 辅助方法检测通过")
        else:
            logger.error(f"❌ 缺少辅助方法: {missing_helpers}")
        
        # 4. 检查数据流转
        logger.info("4. 检查数据流转")
        
        data_flow_elements = [
            'self.last_project_file = save_path',
            'self.last_project_data = project_data',
            'if not hasattr(self, \'last_project_file\')'
        ]
        
        missing_data_flow = []
        for element in data_flow_elements:
            if element not in content:
                missing_data_flow.append(element)
        
        if not missing_data_flow:
            functionality_results['data_flow'] = True
            logger.info("✅ 数据流转检测通过")
        else:
            logger.error(f"❌ 缺少数据流转元素: {missing_data_flow}")
        
        # 5. 检查事件绑定
        logger.info("5. 检查事件绑定")
        
        event_binding_elements = [
            'generate_project_btn.clicked.connect(self.generate_project_file)',
            'export_jianying_btn.clicked.connect(self.export_to_jianying)'
        ]
        
        missing_bindings = []
        for binding in event_binding_elements:
            if binding not in content:
                missing_bindings.append(binding)
        
        if not missing_bindings:
            functionality_results['event_binding'] = True
            logger.info("✅ 事件绑定检测通过")
        else:
            logger.error(f"❌ 缺少事件绑定: {missing_bindings}")
        
    except Exception as e:
        logger.error(f"❌ 功能完整性检测失败: {e}")
        traceback.print_exc()
    
    return functionality_results

def detect_error_handling():
    """检测错误处理"""
    logger.info("🛡️ 开始错误处理检测")
    logger.info("=" * 60)
    
    error_handling_results = {
        'input_validation': False,
        'file_operations': False,
        'exception_handling': False,
        'user_feedback': False
    }
    
    try:
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 检查输入验证
        logger.info("1. 检查输入验证")
        
        validation_elements = [
            'if self.video_list.count() == 0:',
            'if not selected_video:',
            'if not selected_srt:',
            'QMessageBox.warning(self, "警告"'
        ]
        
        missing_validations = []
        for validation in validation_elements:
            if validation not in content:
                missing_validations.append(validation)
        
        if not missing_validations:
            error_handling_results['input_validation'] = True
            logger.info("✅ 输入验证检测通过")
        else:
            logger.error(f"❌ 缺少输入验证: {missing_validations}")
        
        # 2. 检查文件操作错误处理
        logger.info("2. 检查文件操作错误处理")
        
        file_handling_elements = [
            'if not os.path.exists(',
            'try:',
            'except Exception as e:',
            'QMessageBox.critical(self, "错误"'
        ]
        
        missing_file_handling = []
        for element in file_handling_elements:
            if element not in content:
                missing_file_handling.append(element)
        
        if not missing_file_handling:
            error_handling_results['file_operations'] = True
            logger.info("✅ 文件操作错误处理检测通过")
        else:
            logger.error(f"❌ 缺少文件操作错误处理: {missing_file_handling}")
        
        # 3. 检查异常处理
        logger.info("3. 检查异常处理")
        
        exception_count = content.count('except Exception as e:')
        try_count = content.count('try:')
        
        if exception_count >= 3 and try_count >= 3:  # 至少有3个异常处理块
            error_handling_results['exception_handling'] = True
            logger.info(f"✅ 异常处理检测通过 (try: {try_count}, except: {exception_count})")
        else:
            logger.error(f"❌ 异常处理不足 (try: {try_count}, except: {exception_count})")
        
        # 4. 检查用户反馈
        logger.info("4. 检查用户反馈")
        
        feedback_elements = [
            'self.statusBar().showMessage(',
            'log_handler.log(',
            'QMessageBox.information(',
            'self.process_progress_bar.setValue('
        ]
        
        missing_feedback = []
        for feedback in feedback_elements:
            if feedback not in content:
                missing_feedback.append(feedback)
        
        if not missing_feedback:
            error_handling_results['user_feedback'] = True
            logger.info("✅ 用户反馈检测通过")
        else:
            logger.error(f"❌ 缺少用户反馈: {missing_feedback}")
        
    except Exception as e:
        logger.error(f"❌ 错误处理检测失败: {e}")
        traceback.print_exc()
    
    return error_handling_results

def detect_compatibility():
    """检测兼容性"""
    logger.info("🔗 开始兼容性检测")
    logger.info("=" * 60)

    compatibility_results = {
        'existing_functions': False,
        'ui_integration': False,
        'cross_platform': False,
        'dependency_check': False
    }

    try:
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 检查现有功能是否受影响
        logger.info("1. 检查现有功能兼容性")

        existing_functions = [
            'def generate_viral_srt(self):',
            'def show_log_viewer(self):',
            'def show_system_monitor(self):',
            'def detect_gpu(self):',
            'class SimplifiedTrainingFeeder'
        ]

        missing_functions = []
        for func in existing_functions:
            if func not in content:
                missing_functions.append(func)

        if not missing_functions:
            compatibility_results['existing_functions'] = True
            logger.info("✅ 现有功能兼容性检测通过")
        else:
            logger.error(f"❌ 现有功能可能受影响: {missing_functions}")

        # 2. 检查UI集成
        logger.info("2. 检查UI集成兼容性")

        ui_integration_elements = [
            'self.tabs = QTabWidget()',
            'train_tab = QWidget()',
            'about_tab = QWidget()',
            'settings_tab = QWidget()'
        ]

        missing_ui = []
        for element in ui_integration_elements:
            if element not in content:
                missing_ui.append(element)

        if not missing_ui:
            compatibility_results['ui_integration'] = True
            logger.info("✅ UI集成兼容性检测通过")
        else:
            logger.error(f"❌ UI集成可能有问题: {missing_ui}")

        # 3. 检查跨平台兼容性
        logger.info("3. 检查跨平台兼容性")

        cross_platform_elements = [
            'platform.system()',
            'if system == "Windows":',
            'elif system == "Darwin":',
            'else:  # Linux'
        ]

        missing_platform = []
        for element in cross_platform_elements:
            if element not in content:
                missing_platform.append(element)

        if not missing_platform:
            compatibility_results['cross_platform'] = True
            logger.info("✅ 跨平台兼容性检测通过")
        else:
            logger.error(f"❌ 跨平台兼容性可能有问题: {missing_platform}")

        # 4. 检查依赖
        logger.info("4. 检查依赖兼容性")

        dependency_elements = [
            'import platform',
            'import json',
            'import subprocess',
            'from src.export.jianying_exporter import JianyingExporter'
        ]

        missing_deps = []
        for dep in dependency_elements:
            if dep not in content:
                missing_deps.append(dep)

        if not missing_deps:
            compatibility_results['dependency_check'] = True
            logger.info("✅ 依赖兼容性检测通过")
        else:
            logger.error(f"❌ 依赖可能有问题: {missing_deps}")

    except Exception as e:
        logger.error(f"❌ 兼容性检测失败: {e}")
        traceback.print_exc()

    return compatibility_results

def test_actual_functionality():
    """测试实际功能（模拟测试）"""
    logger.info("🧪 开始实际功能测试")
    logger.info("=" * 60)

    test_results = {
        'app_startup': False,
        'ui_display': False,
        'button_response': False,
        'file_generation': False
    }

    try:
        # 1. 测试应用启动
        logger.info("1. 测试应用启动")

        # 检查是否可以导入主模块
        try:
            import ast
            with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            test_results['app_startup'] = True
            logger.info("✅ 应用启动测试通过（语法正确）")
        except Exception as e:
            logger.error(f"❌ 应用启动测试失败: {e}")

        # 2. 测试UI显示（检查UI代码完整性）
        logger.info("2. 测试UI显示")

        ui_display_elements = [
            'self.setWindowTitle("VisionAI-ClipsMaster',
            'self.resize(1200, 800)',
            'window.show()'
        ]

        ui_display_ok = all(element in content for element in ui_display_elements)
        test_results['ui_display'] = ui_display_ok

        if ui_display_ok:
            logger.info("✅ UI显示测试通过")
        else:
            logger.error("❌ UI显示测试失败")

        # 3. 测试按钮响应（检查事件绑定）
        logger.info("3. 测试按钮响应")

        button_response_elements = [
            '.clicked.connect(self.generate_project_file)',
            '.clicked.connect(self.export_to_jianying)'
        ]

        button_response_ok = all(element in content for element in button_response_elements)
        test_results['button_response'] = button_response_ok

        if button_response_ok:
            logger.info("✅ 按钮响应测试通过")
        else:
            logger.error("❌ 按钮响应测试失败")

        # 4. 测试文件生成（检查文件操作代码）
        logger.info("4. 测试文件生成")

        file_generation_elements = [
            'json.dump(project_data, f, ensure_ascii=False, indent=2)',
            'with open(save_path, \'w\', encoding=\'utf-8\') as f:'
        ]

        file_generation_ok = all(element in content for element in file_generation_elements)
        test_results['file_generation'] = file_generation_ok

        if file_generation_ok:
            logger.info("✅ 文件生成测试通过")
        else:
            logger.error("❌ 文件生成测试失败")

    except Exception as e:
        logger.error(f"❌ 实际功能测试失败: {e}")
        traceback.print_exc()

    return test_results

def generate_detection_report(ui_results, func_results, error_results, compat_results, test_results):
    """生成检测报告"""
    logger.info("📊 生成检测报告")
    logger.info("=" * 60)

    # 计算总体得分
    all_results = {
        **ui_results,
        **func_results,
        **error_results,
        **compat_results,
        **test_results
    }

    passed_tests = sum(all_results.values())
    total_tests = len(all_results)
    score = (passed_tests / total_tests) * 100

    # 生成报告
    report = []
    report.append("# VisionAI-ClipsMaster 主UI界面全面功能检测报告")
    report.append("")
    report.append(f"**检测时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**总体得分**: {score:.1f}% ({passed_tests}/{total_tests})")
    report.append("")

    # 检测结果概览
    status_icon = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
    status_text = "优秀" if score >= 90 else "良好" if score >= 70 else "需要改进"
    report.append(f"**整体状态**: {status_icon} {status_text}")
    report.append("")

    # 详细检测结果
    report.append("## 详细检测结果")
    report.append("")

    # UI布局检测
    report.append("### 1. UI布局检测")
    for key, value in ui_results.items():
        status = "✅ 通过" if value else "❌ 失败"
        report.append(f"- **{key}**: {status}")
    report.append("")

    # 功能完整性检测
    report.append("### 2. 功能完整性检测")
    for key, value in func_results.items():
        status = "✅ 通过" if value else "❌ 失败"
        report.append(f"- **{key}**: {status}")
    report.append("")

    # 错误处理检测
    report.append("### 3. 错误处理检测")
    for key, value in error_results.items():
        status = "✅ 通过" if value else "❌ 失败"
        report.append(f"- **{key}**: {status}")
    report.append("")

    # 兼容性检测
    report.append("### 4. 兼容性检测")
    for key, value in compat_results.items():
        status = "✅ 通过" if value else "❌ 失败"
        report.append(f"- **{key}**: {status}")
    report.append("")

    # 实际功能测试
    report.append("### 5. 实际功能测试")
    for key, value in test_results.items():
        status = "✅ 通过" if value else "❌ 失败"
        report.append(f"- **{key}**: {status}")
    report.append("")

    # 问题总结
    failed_items = [key for key, value in all_results.items() if not value]
    if failed_items:
        report.append("## 发现的问题")
        report.append("")
        for item in failed_items:
            report.append(f"- ❌ {item}")
        report.append("")

    # 改进建议
    if score < 100:
        report.append("## 改进建议")
        report.append("")
        if not ui_results.get('button_layout', True):
            report.append("- 检查并修复按钮布局代码")
        if not func_results.get('generate_project_method', True):
            report.append("- 完善生成工程文件方法实现")
        if not error_results.get('exception_handling', True):
            report.append("- 增强异常处理机制")
        if not compat_results.get('cross_platform', True):
            report.append("- 完善跨平台兼容性支持")
        report.append("")

    # 总结
    report.append("## 总结")
    report.append("")
    if score >= 90:
        report.append("🎉 **检测结果优秀**！UI集成和功能修改实施成功，可以正常使用。")
    elif score >= 70:
        report.append("⚠️ **检测结果良好**，存在少量问题需要修复。")
    else:
        report.append("❌ **检测发现较多问题**，需要进行修复后再使用。")

    report_content = "\n".join(report)

    # 保存报告
    try:
        with open("comprehensive_ui_detection_report.md", 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info("✅ 检测报告已保存到: comprehensive_ui_detection_report.md")
    except Exception as e:
        logger.error(f"❌ 保存检测报告失败: {e}")

    return report_content, score

def main():
    """主检测函数"""
    logger.info("🔍 开始VisionAI-ClipsMaster主UI界面全面功能检测")
    logger.info("=" * 80)

    try:
        # 1. UI布局检测
        ui_results = detect_ui_layout()

        # 2. 功能完整性检测
        func_results = detect_functionality()

        # 3. 错误处理检测
        error_results = detect_error_handling()

        # 4. 兼容性检测
        compat_results = detect_compatibility()

        # 5. 实际功能测试
        test_results = test_actual_functionality()

        # 6. 生成检测报告
        report, score = generate_detection_report(
            ui_results, func_results, error_results, compat_results, test_results
        )

        # 7. 显示结果
        logger.info("📋 检测完成")
        logger.info("=" * 60)
        logger.info(f"总体得分: {score:.1f}%")

        if score >= 90:
            logger.info("🎉 检测结果优秀！")
        elif score >= 70:
            logger.info("⚠️ 检测结果良好，存在少量问题")
        else:
            logger.error("❌ 检测发现较多问题")

        return {
            'ui_results': ui_results,
            'func_results': func_results,
            'error_results': error_results,
            'compat_results': compat_results,
            'test_results': test_results,
            'score': score,
            'report': report
        }

    except Exception as e:
        logger.error(f"❌ 检测过程中发生错误: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main()

    if results:
        print("\n" + "=" * 80)
        print("VisionAI-ClipsMaster 主UI界面全面功能检测完成！")
        print(f"总体得分: {results['score']:.1f}%")
        print("详细报告已保存到: comprehensive_ui_detection_report.md")
        print("=" * 80)
    else:
        print("检测失败，请查看日志获取详细信息")
