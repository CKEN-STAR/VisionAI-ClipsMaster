#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实世界工作流程测试
测试完整的短剧混剪工作流程：从SRT输入到最终视频输出
"""

import os
import sys
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime
import logging

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealWorldWorkflowTest:
    """真实世界工作流程测试类"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="workflow_test_")
        self.test_results = {}
        
    def create_realistic_test_data(self):
        """创建更真实的测试数据"""
        # 创建一个更长的、更真实的短剧SRT文件
        realistic_srt = """1
00:00:01,000 --> 00:00:04,500
【第一集】霸道总裁的秘密

2
00:00:05,000 --> 00:00:08,200
林小雨刚刚大学毕业，怀着忐忑的心情走进了这家知名企业

3
00:00:08,700 --> 00:00:12,300
她没想到，命运会让她遇到传说中的冰山总裁——陈墨轩

4
00:00:12,800 --> 00:00:16,100
"你就是新来的实习生？"陈墨轩冷漠地看着她

5
00:00:16,600 --> 00:00:20,400
林小雨紧张得说不出话，只能点点头

6
00:00:20,900 --> 00:00:24,700
"记住，在我这里，只有结果，没有借口"

7
00:00:25,200 --> 00:00:28,800
就这样，林小雨开始了她的职场生涯

8
00:00:29,300 --> 00:00:33,100
但她不知道，这个冷酷的总裁内心深处隐藏着什么秘密

9
00:00:33,600 --> 00:00:37,400
【第二集】意外的相遇

10
00:00:37,900 --> 00:00:41,700
一个月后，林小雨已经适应了公司的节奏

11
00:00:42,200 --> 00:00:46,000
这天晚上，她加班到很晚，准备离开公司

12
00:00:46,500 --> 00:00:50,300
电梯里，她意外地遇到了还在加班的陈墨轩

13
00:00:50,800 --> 00:00:54,600
"这么晚还不回家？"陈墨轩难得地开口问道

14
00:00:55,100 --> 00:00:58,900
"项目还没完成，我想再检查一遍"林小雨诚实地回答

15
00:00:59,400 --> 00:01:03,200
陈墨轩看着她认真的样子，心中涌起一丝异样的感觉

16
00:01:03,700 --> 00:01:07,500
【第三集】渐生情愫

17
00:01:08,000 --> 00:01:11,800
从那天起，陈墨轩开始注意这个努力的女孩

18
00:01:12,300 --> 00:01:16,100
他发现林小雨总是最早到公司，最晚离开

19
00:01:16,600 --> 00:01:20,400
"你为什么这么拼命？"有一天，他忍不住问道

20
00:01:20,900 --> 00:01:24,700
"因为我想证明自己，想在这个城市站稳脚跟"

21
00:01:25,200 --> 00:01:29,000
林小雨的话让陈墨轩想起了年轻时的自己

22
00:01:29,500 --> 00:01:33,300
那个为了梦想而奋斗的少年，如今已经变成了冷漠的总裁

23
00:01:33,800 --> 00:01:37,600
【第四集】危机来临

24
00:01:38,100 --> 00:01:41,900
就在两人关系微妙变化的时候，公司遭遇了危机

25
00:01:42,400 --> 00:01:46,200
竞争对手恶意收购，陈墨轩面临着前所未有的挑战

26
00:01:46,700 --> 00:01:50,500
"总裁，我们该怎么办？"秘书焦急地问道

27
00:01:51,000 --> 00:01:54,800
陈墨轩紧握双拳，眼中闪过一丝决绝

28
00:01:55,300 --> 00:01:59,100
这时，林小雨主动提出了一个大胆的方案

29
00:01:59,600 --> 00:02:03,400
"如果我们能拿下这个项目，就能扭转局面"

30
00:02:03,900 --> 00:02:07,700
【第五集】携手并肩

31
00:02:08,200 --> 00:02:12,000
为了拯救公司，陈墨轩和林小雨开始并肩作战

32
00:02:12,500 --> 00:02:16,300
他们日夜不停地工作，为了同一个目标而努力

33
00:02:16,800 --> 00:02:20,600
在这个过程中，两人的心越来越近

34
00:02:21,100 --> 00:02:24,900
"谢谢你，小雨"陈墨轩第一次叫她的名字

35
00:02:25,400 --> 00:02:29,200
林小雨感到心跳加速，脸颊微微发红

36
00:02:29,700 --> 00:02:33,500
【大结局】爱的告白

37
00:02:34,000 --> 00:02:37,800
最终，他们成功拯救了公司

38
00:02:38,300 --> 00:02:42,100
在庆祝的那个夜晚，陈墨轩终于说出了心里话

39
00:02:42,600 --> 00:02:46,400
"小雨，你愿意和我一起，面对未来的每一天吗？"

40
00:02:46,900 --> 00:02:50,700
林小雨含泪点头，两人紧紧拥抱在一起

41
00:02:51,200 --> 00:02:55,000
从此，他们不仅是工作伙伴，更是人生伴侣

42
00:02:55,500 --> 00:02:59,300
这就是一个关于爱情、奋斗和成长的故事"""

        # 保存测试SRT文件
        srt_path = Path(self.temp_dir) / "realistic_drama.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(realistic_srt)
            
        return str(srt_path)
        
    def test_complete_workflow(self):
        """测试完整工作流程"""
        logger.info("开始测试完整工作流程...")
        
        try:
            # 1. 创建测试数据
            srt_path = self.create_realistic_test_data()
            logger.info(f"创建测试SRT文件: {srt_path}")
            
            # 2. 测试SRT解析
            from src.core.srt_parser import SRTParser
            parser = SRTParser()
            subtitles = parser.parse_srt_file(srt_path)
            
            self.test_results['srt_parsing'] = {
                'success': len(subtitles) > 0,
                'subtitle_count': len(subtitles),
                'total_duration': max(sub.get('end_time', 0) for sub in subtitles) if subtitles else 0
            }
            
            # 3. 测试语言检测
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()

            # 读取文件内容进行检测
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            detected_lang = detector.detect_language(content)
            
            self.test_results['language_detection'] = {
                'detected_language': detected_lang,
                'expected_language': 'zh',
                'correct': detected_lang == 'zh'
            }
            
            # 4. 测试剧本重构
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            
            # 加载字幕
            engineer.load_subtitles(srt_path)
            
            # 分析剧情
            plot_analysis = engineer.analyze_plot()
            
            # 重构剧本
            reconstructed = engineer.reconstruct_screenplay(target_style="viral")
            
            self.test_results['script_reconstruction'] = {
                'analysis_success': bool(plot_analysis),
                'reconstruction_success': bool(reconstructed),
                'original_segments': len(subtitles),
                'reconstructed_segments': len(reconstructed.get('segments', [])) if reconstructed else 0,
                'compression_ratio': self.calculate_compression_ratio(subtitles, reconstructed)
            }
            
            # 5. 测试剪映导出
            if reconstructed and 'segments' in reconstructed:
                from src.exporters.jianying_pro_exporter import JianyingProExporter
                exporter = JianyingProExporter()
                
                output_path = Path(self.temp_dir) / "workflow_test_project.json"
                export_success = exporter.export_project(reconstructed['segments'], str(output_path))
                
                self.test_results['jianying_export'] = {
                    'export_success': export_success,
                    'output_file_exists': output_path.exists(),
                    'file_size': output_path.stat().st_size if output_path.exists() else 0
                }
            
            # 6. 测试模型切换
            from src.core.model_switcher import ModelSwitcher
            switcher = ModelSwitcher()
            
            switch_success = switcher.switch_model('zh')
            model_info = switcher.get_model_info()
            
            self.test_results['model_switching'] = {
                'switch_success': switch_success,
                'current_model': model_info.get('current_model'),
                'available_models': model_info.get('available_models')
            }
            
            return True
            
        except Exception as e:
            logger.error(f"工作流程测试失败: {str(e)}")
            self.test_results['error'] = str(e)
            return False
            
    def calculate_compression_ratio(self, original_subtitles, reconstructed_script):
        """计算压缩比例"""
        try:
            if not original_subtitles or not reconstructed_script:
                return 0.0
                
            original_count = len(original_subtitles)
            reconstructed_count = len(reconstructed_script.get('segments', []))
            
            if original_count == 0:
                return 0.0
                
            return (original_count - reconstructed_count) / original_count
            
        except Exception:
            return 0.0
            
    def generate_workflow_report(self):
        """生成工作流程测试报告"""
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'test_environment': {
                'temp_directory': self.temp_dir,
                'python_version': sys.version,
                'platform': sys.platform
            },
            'workflow_results': self.test_results,
            'overall_success': self.evaluate_overall_success()
        }
        
        # 保存报告
        report_path = f"workflow_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        logger.info(f"工作流程测试报告已保存: {report_path}")
        
        # 打印摘要
        self.print_workflow_summary()
        
        return report
        
    def evaluate_overall_success(self):
        """评估整体成功率"""
        success_count = 0
        total_count = 0
        
        for test_name, result in self.test_results.items():
            if test_name == 'error':
                continue
                
            total_count += 1
            if isinstance(result, dict):
                if result.get('success', False) or result.get('export_success', False) or result.get('switch_success', False):
                    success_count += 1
                    
        return success_count / total_count if total_count > 0 else 0.0
        
    def print_workflow_summary(self):
        """打印工作流程测试摘要"""
        print("\n" + "="*80)
        print("真实世界工作流程测试报告")
        print("="*80)
        
        for test_name, result in self.test_results.items():
            if test_name == 'error':
                print(f"❌ 测试失败: {result}")
                continue
                
            print(f"\n📋 {test_name.replace('_', ' ').title()}:")
            for key, value in result.items():
                print(f"   {key}: {value}")
                
        overall_success = self.evaluate_overall_success()
        print(f"\n🎯 整体成功率: {overall_success:.1%}")
        
        if overall_success >= 0.8:
            print("✅ 工作流程测试通过！系统可以正常处理真实短剧数据。")
        else:
            print("⚠️ 工作流程存在问题，需要进一步优化。")
            
        print("="*80)

def main():
    """主函数"""
    print("开始真实世界工作流程测试...")
    
    test = RealWorldWorkflowTest()
    
    try:
        success = test.test_complete_workflow()
        report = test.generate_workflow_report()
        
        return success
        
    except Exception as e:
        logger.error(f"测试执行异常: {str(e)}")
        return False
    finally:
        # 清理临时文件
        import shutil
        try:
            shutil.rmtree(test.temp_dir)
            logger.info(f"已清理临时目录: {test.temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录失败: {str(e)}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
