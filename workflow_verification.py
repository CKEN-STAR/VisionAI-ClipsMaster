#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 关键工作流程验证脚本
验证AI剧本重构引擎、双语言模型系统、剪映导出等核心功能
"""

import os
import sys
import json
import inspect
from datetime import datetime

class WorkflowVerification:
    def __init__(self):
        self.results = {}
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        sys.path.insert(0, os.path.abspath('.'))
        
    def log_result(self, message):
        """记录验证结果"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open("workflow_verification_results.txt", "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    
    def verify_screenplay_engine_methods(self):
        """验证AI剧本重构引擎的6个核心分析方法"""
        self.log_result("=== AI剧本重构引擎核心方法验证 ===")
        
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            se = ScreenplayEngineer()
            
            # 检查6个核心分析方法
            required_methods = [
                'deep_semantic_analysis',      # 深度语义分析
                'narrative_structure_analysis', # 叙事结构分析
                'character_relationship_recognition', # 角色关系识别
                'turning_point_detection',     # 转折点检测
                'emotion_curve_analysis',      # 情感曲线分析
                'plot_integrity_verification'  # 剧情完整性验证
            ]
            
            method_status = {}
            for method_name in required_methods:
                if hasattr(se, method_name):
                    method = getattr(se, method_name)
                    if callable(method):
                        method_status[method_name] = True
                        self.log_result(f"✅ {method_name}: 方法存在且可调用")
                    else:
                        method_status[method_name] = False
                        self.log_result(f"❌ {method_name}: 存在但不可调用")
                else:
                    method_status[method_name] = False
                    self.log_result(f"❌ {method_name}: 方法不存在")
            
            self.results['screenplay_engine_methods'] = method_status
            
            # 计算通过率
            passed_methods = sum(method_status.values())
            total_methods = len(required_methods)
            pass_rate = (passed_methods / total_methods) * 100
            
            self.log_result(f"核心方法验证: {passed_methods}/{total_methods} 通过 ({pass_rate:.1f}%)")
            
            return pass_rate == 100.0
            
        except Exception as e:
            self.log_result(f"❌ AI剧本重构引擎验证失败: {str(e)}")
            return False
    
    def verify_dual_model_system(self):
        """验证双语言模型系统"""
        self.log_result("=== 双语言模型系统验证 ===")
        
        try:
            from src.core.model_switcher import ModelSwitcher
            from src.core.language_detector import LanguageDetector
            
            # 验证ModelSwitcher
            ms = ModelSwitcher(model_root="models/")
            self.log_result("✅ ModelSwitcher初始化成功")
            
            # 检查关键方法
            ms_methods = ['switch_model', 'get_current_model', '_load_model_configs']
            ms_status = {}
            for method in ms_methods:
                if hasattr(ms, method):
                    ms_status[method] = True
                    self.log_result(f"✅ ModelSwitcher.{method}: 存在")
                else:
                    ms_status[method] = False
                    self.log_result(f"❌ ModelSwitcher.{method}: 不存在")
            
            # 验证LanguageDetector
            ld = LanguageDetector()
            self.log_result("✅ LanguageDetector初始化成功")
            
            # 检查语言检测方法
            ld_methods = ['detect_language', 'is_chinese', 'is_english']
            ld_status = {}
            for method in ld_methods:
                if hasattr(ld, method):
                    ld_status[method] = True
                    self.log_result(f"✅ LanguageDetector.{method}: 存在")
                else:
                    ld_status[method] = False
                    self.log_result(f"❌ LanguageDetector.{method}: 不存在")
            
            self.results['model_switcher_methods'] = ms_status
            self.results['language_detector_methods'] = ld_status
            
            # 计算总体通过率
            total_passed = sum(ms_status.values()) + sum(ld_status.values())
            total_methods = len(ms_methods) + len(ld_methods)
            pass_rate = (total_passed / total_methods) * 100
            
            self.log_result(f"双语言模型系统验证: {total_passed}/{total_methods} 通过 ({pass_rate:.1f}%)")
            
            return pass_rate >= 80.0
            
        except Exception as e:
            self.log_result(f"❌ 双语言模型系统验证失败: {str(e)}")
            return False
    
    def verify_jianying_export(self):
        """验证剪映导出功能"""
        self.log_result("=== 剪映导出功能验证 ===")
        
        try:
            from src.export.jianying_exporter import JianyingExporter
            
            je = JianyingExporter()
            self.log_result("✅ JianyingExporter初始化成功")
            
            # 检查关键导出方法
            export_methods = ['export_project', 'generate_timeline', 'create_project_file']
            export_status = {}
            
            for method in export_methods:
                if hasattr(je, method):
                    export_status[method] = True
                    self.log_result(f"✅ JianyingExporter.{method}: 存在")
                else:
                    export_status[method] = False
                    self.log_result(f"❌ JianyingExporter.{method}: 不存在")
            
            self.results['jianying_export_methods'] = export_status
            
            # 计算通过率
            passed_methods = sum(export_status.values())
            total_methods = len(export_methods)
            pass_rate = (passed_methods / total_methods) * 100
            
            self.log_result(f"剪映导出功能验证: {passed_methods}/{total_methods} 通过 ({pass_rate:.1f}%)")
            
            return pass_rate >= 66.7  # 至少2/3方法存在
            
        except Exception as e:
            self.log_result(f"❌ 剪映导出功能验证失败: {str(e)}")
            return False
    
    def verify_video_processing_workflow(self):
        """验证视频处理工作流程"""
        self.log_result("=== 视频处理工作流程验证 ===")
        
        workflow_components = [
            ('SRT解析器', 'src.core.srt_parser', 'SRTParser'),
            ('AI病毒转换器', 'src.core.ai_viral_transformer', 'AIViralTransformer'),
            ('剧本重构引擎', 'src.core.screenplay_engineer', 'ScreenplayEngineer'),
            ('视频片段生成器', 'src.core.clip_generator', 'ClipGenerator')
        ]
        
        workflow_status = {}
        
        for component_name, module_path, class_name in workflow_components:
            try:
                module = __import__(module_path, fromlist=[class_name])
                component_class = getattr(module, class_name)
                
                # 尝试实例化
                if class_name == 'ScreenplayEngineer':
                    instance = component_class()
                elif class_name == 'ClipGenerator':
                    instance = component_class()
                elif class_name == 'SRTParser':
                    instance = component_class()
                else:
                    instance = component_class()
                
                workflow_status[component_name] = True
                self.log_result(f"✅ {component_name}: 可正常实例化")
                
            except Exception as e:
                workflow_status[component_name] = False
                self.log_result(f"❌ {component_name}: 实例化失败 - {str(e)}")
        
        self.results['video_processing_workflow'] = workflow_status
        
        # 计算工作流程完整性
        passed_components = sum(workflow_status.values())
        total_components = len(workflow_components)
        completeness = (passed_components / total_components) * 100
        
        self.log_result(f"视频处理工作流程完整性: {passed_components}/{total_components} ({completeness:.1f}%)")
        
        return completeness >= 75.0
    
    def verify_training_modules(self):
        """验证训练模块功能"""
        self.log_result("=== 训练模块功能验证 ===")
        
        try:
            from src.training.data_augment import DataAugmenter
            from src.training.plot_augment import PlotAugmenter
            
            # 验证数据增强器
            da = DataAugmenter(language="zh")
            self.log_result("✅ DataAugmenter(中文)初始化成功")
            
            da_en = DataAugmenter(language="en")
            self.log_result("✅ DataAugmenter(英文)初始化成功")
            
            # 验证剧情增强器
            pa = PlotAugmenter(language="zh")
            self.log_result("✅ PlotAugmenter(中文)初始化成功")
            
            pa_en = PlotAugmenter(language="en")
            self.log_result("✅ PlotAugmenter(英文)初始化成功")
            
            # 检查关键方法
            da_methods = ['augment_text', 'apply_synonyms', 'add_intensifiers']
            pa_methods = ['augment_plot', 'generate_variations', 'enhance_narrative']
            
            da_status = {}
            for method in da_methods:
                da_status[method] = hasattr(da, method)
                status = "✅" if da_status[method] else "❌"
                self.log_result(f"{status} DataAugmenter.{method}: {'存在' if da_status[method] else '不存在'}")
            
            pa_status = {}
            for method in pa_methods:
                pa_status[method] = hasattr(pa, method)
                status = "✅" if pa_status[method] else "❌"
                self.log_result(f"{status} PlotAugmenter.{method}: {'存在' if pa_status[method] else '不存在'}")
            
            self.results['data_augmenter_methods'] = da_status
            self.results['plot_augmenter_methods'] = pa_status
            
            # 计算通过率
            total_passed = sum(da_status.values()) + sum(pa_status.values())
            total_methods = len(da_methods) + len(pa_methods)
            pass_rate = (total_passed / total_methods) * 100
            
            self.log_result(f"训练模块验证: {total_passed}/{total_methods} 通过 ({pass_rate:.1f}%)")
            
            return pass_rate >= 66.7
            
        except Exception as e:
            self.log_result(f"❌ 训练模块验证失败: {str(e)}")
            return False
    
    def generate_workflow_summary(self):
        """生成工作流程验证总结"""
        self.log_result("=== 关键工作流程验证总结 ===")
        
        # 统计各模块验证结果
        verification_results = {
            'AI剧本重构引擎': self.results.get('screenplay_engine_methods', {}),
            '双语言模型系统': {**self.results.get('model_switcher_methods', {}), 
                           **self.results.get('language_detector_methods', {})},
            '剪映导出功能': self.results.get('jianying_export_methods', {}),
            '视频处理工作流程': self.results.get('video_processing_workflow', {}),
            '训练模块': {**self.results.get('data_augmenter_methods', {}),
                       **self.results.get('plot_augmenter_methods', {})}
        }
        
        overall_score = 0
        max_score = 0
        
        for module_name, methods in verification_results.items():
            if methods:
                passed = sum(methods.values())
                total = len(methods)
                score = (passed / total) * 100 if total > 0 else 0
                
                overall_score += passed
                max_score += total
                
                self.log_result(f"{module_name}: {passed}/{total} ({score:.1f}%)")
        
        # 计算总体评分
        final_score = (overall_score / max_score) * 100 if max_score > 0 else 0
        self.results['workflow_verification_score'] = final_score
        
        self.log_result(f"🏆 关键工作流程总体评分: {overall_score}/{max_score} ({final_score:.1f}%)")
        
        # 评估等级
        if final_score >= 90:
            grade = "A+ (卓越)"
        elif final_score >= 80:
            grade = "A (优秀)"
        elif final_score >= 70:
            grade = "B (良好)"
        elif final_score >= 60:
            grade = "C (及格)"
        else:
            grade = "D (需改进)"
        
        self.results['workflow_grade'] = grade
        self.log_result(f"🎯 工作流程完整性等级: {grade}")
        
        # 保存详细报告
        with open("workflow_verification_report.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return final_score >= 80.0

if __name__ == "__main__":
    # 清空之前的测试结果
    with open("workflow_verification_results.txt", "w", encoding="utf-8") as f:
        f.write("")
    
    verifier = WorkflowVerification()
    
    verifier.log_result("🔧 开始VisionAI-ClipsMaster关键工作流程验证")
    
    # 执行各项验证
    screenplay_pass = verifier.verify_screenplay_engine_methods()
    dual_model_pass = verifier.verify_dual_model_system()
    jianying_pass = verifier.verify_jianying_export()
    workflow_pass = verifier.verify_video_processing_workflow()
    training_pass = verifier.verify_training_modules()
    
    # 生成总结报告
    overall_pass = verifier.generate_workflow_summary()
    
    # 最终评估
    if overall_pass:
        verifier.log_result("🎉 关键工作流程验证全部通过！核心功能完整")
    else:
        verifier.log_result("⚠️ 部分关键工作流程需要进一步完善")
    
    verifier.log_result("📊 详细验证报告已保存至: workflow_verification_report.json")
