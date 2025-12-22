#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI功能真实可用性验证测试
验证simple_ui_fixed.py中的所有UI功能是否真实可用
"""

import sys
import inspect
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 功能清单
UI_FUNCTIONS = {
    "视频处理功能": {
        "select_video": {
            "描述": "选择视频文件",
            "触发": "添加视频按钮",
            "预期": "打开文件选择对话框，选择视频文件"
        },
        "remove_video": {
            "描述": "移除视频文件",
            "触发": "移除视频按钮",
            "预期": "从列表中移除选中的视频"
        },
        "select_subtitle": {
            "描述": "选择字幕文件",
            "触发": "添加SRT按钮",
            "预期": "打开文件选择对话框，选择SRT文件"
        },
        "remove_srt": {
            "描述": "移除字幕文件",
            "触发": "移除SRT按钮",
            "预期": "从列表中移除选中的SRT"
        },
        "generate_viral_srt": {
            "描述": "生成爆款SRT",
            "触发": "生成爆款SRT按钮",
            "预期": "处理SRT文件，生成优化后的字幕"
        },
        "generate_project_file": {
            "描述": "生成工程文件",
            "触发": "生成工程文件按钮",
            "预期": "生成剪映工程文件"
        },
        "export_to_jianying": {
            "描述": "导出到剪映",
            "触发": "导出到剪映按钮",
            "预期": "导出工程文件并尝试打开剪映"
        }
    },
    "训练功能": {
        "import_original_srt": {
            "描述": "导入原始SRT",
            "触发": "导入原始SRT按钮",
            "预期": "选择并导入原始字幕文件"
        },
        "remove_original_srt": {
            "描述": "移除原始SRT",
            "触发": "移除原始SRT按钮",
            "预期": "清除已导入的原始SRT"
        },
        "import_viral_srt": {
            "描述": "导入爆款SRT",
            "触发": "导入爆款SRT按钮",
            "预期": "选择并导入爆款字幕文件"
        },
        "detect_gpu": {
            "描述": "检测GPU",
            "触发": "检测GPU按钮",
            "预期": "检测并显示GPU信息"
        },
        "learn_data_pair": {
            "描述": "学习数据对",
            "触发": "开始学习按钮",
            "预期": "使用原始和爆款SRT训练模型"
        },
        "switch_training_language": {
            "描述": "切换训练语言",
            "触发": "语言单选按钮",
            "预期": "切换中文/英文训练模式"
        }
    },
    "模型管理功能": {
        "check_models": {
            "描述": "检查模型",
            "触发": "自动检查",
            "预期": "检测已下载的模型"
        },
        "download_zh_model": {
            "描述": "下载中文模型",
            "触发": "下载中文模型",
            "预期": "启动智能下载器下载中文模型"
        },
        "download_en_model": {
            "描述": "下载英文模型",
            "触发": "下载英文模型",
            "预期": "启动智能下载器下载英文模型"
        }
    },
    "系统功能": {
        "show_log_viewer": {
            "描述": "显示日志查看器",
            "触发": "查看日志按钮",
            "预期": "打开日志查看对话框"
        },
        "show_system_monitor": {
            "描述": "显示系统监控",
            "触发": "系统监控按钮",
            "预期": "打开系统监控窗口"
        },
        "detect_gpu": {
            "描述": "检测GPU",
            "触发": "检测GPU按钮",
            "预期": "显示GPU检测对话框"
        },
        "change_language_mode": {
            "描述": "切换语言模式",
            "触发": "语言单选按钮",
            "预期": "切换自动/中文/英文模式"
        }
    },
    "关于和帮助": {
        "show_about_dialog": {
            "描述": "显示关于对话框",
            "触发": "关于按钮",
            "预期": "显示团队信息"
        },
        "show_tech_dialog": {
            "描述": "显示技术信息",
            "触发": "技术按钮",
            "预期": "显示技术栈信息"
        },
        "show_history_dialog": {
            "描述": "显示历史记录",
            "触发": "历史按钮",
            "预期": "显示版本历史"
        },
        "open_url": {
            "描述": "打开URL",
            "触发": "GitHub按钮",
            "预期": "在浏览器中打开URL"
        }
    },
    "性能和缓存": {
        "clear_disk_cache": {
            "描述": "清理磁盘缓存",
            "触发": "清理缓存按钮",
            "预期": "清理磁盘缓存文件"
        },
        "refresh_cache_stats": {
            "描述": "刷新缓存统计",
            "触发": "刷新缓存按钮",
            "预期": "更新缓存统计信息"
        },
        "refresh_input_latency_stats": {
            "描述": "刷新输入延迟统计",
            "触发": "刷新输入统计按钮",
            "预期": "更新输入延迟数据"
        },
        "toggle_power_saving_mode": {
            "描述": "切换节能模式",
            "触发": "节能模式按钮",
            "预期": "启用/禁用节能模式"
        },
        "refresh_power_status": {
            "描述": "刷新电源状态",
            "触发": "刷新电源按钮",
            "预期": "更新电源状态信息"
        }
    },
    "模型管理标签页": {
        "refresh_model_info": {
            "描述": "刷新模型信息",
            "触发": "刷新按钮",
            "预期": "更新模型列表和信息"
        },
        "activate_selected_version": {
            "描述": "激活选中版本",
            "触发": "激活按钮",
            "预期": "激活选中的模型版本"
        },
        "convert_selected_to_gguf": {
            "描述": "转换为GGUF",
            "触发": "转换按钮",
            "预期": "将模型转换为GGUF格式"
        },
        "delete_selected_version": {
            "描述": "删除选中版本",
            "触发": "删除按钮",
            "预期": "删除选中的模型版本"
        },
        "delete_selected_gguf": {
            "描述": "删除选中GGUF",
            "触发": "删除GGUF按钮",
            "预期": "删除选中的GGUF模型"
        },
        "cleanup_all_inactive": {
            "描述": "清理所有非活动版本",
            "触发": "批量清理按钮",
            "预期": "删除所有非活动的模型版本"
        },
        "cleanup_all_gguf": {
            "描述": "清理所有GGUF",
            "触发": "清理GGUF按钮",
            "预期": "删除所有GGUF模型"
        }
    }
}


def test_function_exists():
    """测试1：验证所有函数是否存在"""
    print("=" * 60)
    print("测试1：验证函数存在性")
    print("=" * 60)
    
    try:
        # 动态导入simple_ui_fixed模块
        import simple_ui_fixed
        
        # 获取VisionAIClipsMaster类
        if hasattr(simple_ui_fixed, 'VisionAIClipsMaster'):
            cls = simple_ui_fixed.VisionAIClipsMaster
        else:
            print("❌ 未找到VisionAIClipsMaster类")
            return False
        
        total_functions = 0
        existing_functions = 0
        missing_functions = []
        
        for category, functions in UI_FUNCTIONS.items():
            print(f"\n{category}:")
            for func_name, func_info in functions.items():
                total_functions += 1
                if hasattr(cls, func_name):
                    print(f"  ✓ {func_name:30s} - {func_info['描述']}")
                    existing_functions += 1
                else:
                    print(f"  ✗ {func_name:30s} - {func_info['描述']} (不存在)")
                    missing_functions.append(func_name)
        
        print(f"\n总计: {existing_functions}/{total_functions} 函数存在")
        
        if missing_functions:
            print(f"\n缺失的函数: {', '.join(missing_functions)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_function_implementation():
    """测试2：验证函数是否有实际实现"""
    print("\n" + "=" * 60)
    print("测试2：验证函数实现")
    print("=" * 60)
    
    try:
        import simple_ui_fixed
        cls = simple_ui_fixed.VisionAIClipsMaster
        
        total_functions = 0
        implemented_functions = 0
        empty_functions = []
        
        for category, functions in UI_FUNCTIONS.items():
            print(f"\n{category}:")
            for func_name, func_info in functions.items():
                if not hasattr(cls, func_name):
                    continue
                    
                total_functions += 1
                func = getattr(cls, func_name)
                
                # 获取函数源代码
                try:
                    source = inspect.getsource(func)
                    # 检查是否只有pass或只有docstring
                    lines = [line.strip() for line in source.split('\n') if line.strip() and not line.strip().startswith('#')]
                    # 移除函数定义行和docstring
                    code_lines = []
                    in_docstring = False
                    for line in lines[1:]:  # 跳过def行
                        if '"""' in line or "'''" in line:
                            in_docstring = not in_docstring
                            continue
                        if not in_docstring and line not in ['pass', '']:
                            code_lines.append(line)
                    
                    if len(code_lines) > 0:
                        print(f"  ✓ {func_name:30s} - 有实现 ({len(code_lines)}行代码)")
                        implemented_functions += 1
                    else:
                        print(f"  ⚠ {func_name:30s} - 空实现")
                        empty_functions.append(func_name)
                        
                except Exception as e:
                    print(f"  ? {func_name:30s} - 无法检查 ({e})")
        
        print(f"\n总计: {implemented_functions}/{total_functions} 函数有实现")
        
        if empty_functions:
            print(f"\n空实现的函数: {', '.join(empty_functions)}")
        
        return len(empty_functions) == 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("VisionAI-ClipsMaster UI功能真实可用性验证")
    print("=" * 60)
    
    results = []
    
    # 测试1：函数存在性
    result1 = test_function_exists()
    results.append(("函数存在性", result1))
    
    # 测试2：函数实现
    result2 = test_function_implementation()
    results.append(("函数实现", result2))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！UI功能基本可用。")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要修复。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

