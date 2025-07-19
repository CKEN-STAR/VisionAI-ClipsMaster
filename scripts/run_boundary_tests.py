#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行边界条件测试的帮助脚本

提供简单的界面来运行各种边界条件测试场景
"""

import os
import sys
import time
import argparse
import logging
from typing import List, Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# 导入边界测试模块
from tests.boundary_cases import (
    BOUNDARY_TEST_MATRIX, 
    EXTENDED_BOUNDARY_TESTS,
    MODEL_CONFIGS,
    BoundaryTestRunner
)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RunBoundaryTests")

def display_menu():
    """显示测试选择菜单"""
    print("\n===== 边界条件测试运行器 =====")
    print("\n标准测试场景:")
    for i, scenario in enumerate(BOUNDARY_TEST_MATRIX, 1):
        print(f"  {i}. {scenario['scenario']} (内存限制: {scenario['mem_limit']}MB)")
    
    print("\n扩展测试场景:")
    for i, scenario in enumerate(EXTENDED_BOUNDARY_TESTS, len(BOUNDARY_TEST_MATRIX) + 1):
        print(f"  {i}. {scenario['scenario']} (内存限制: {scenario['mem_limit']}MB)")
    
    print("\n可用模型:")
    for i, model in enumerate(MODEL_CONFIGS, 1):
        quant_str = ", ".join(model["quant_levels"])
        print(f"  {i}. {model['model_id']} (量化级别: {quant_str})")
    
    print("\n测试选项:")
    print("  a. 运行所有标准测试")
    print("  e. 运行所有测试(标准+扩展)")
    print("  q. 退出")
    
    choice = input("\n请选择要运行的测试 (输入数字或字母): ")
    return choice.strip()

def parse_choice(choice: str, scenarios: List[Dict[str, Any]], models: List[Dict[str, Any]]):
    """解析用户选择"""
    if choice.lower() == 'q':
        print("退出程序")
        sys.exit(0)
    elif choice.lower() == 'a':
        return {"run_all": True, "extended": False}
    elif choice.lower() == 'e':
        return {"run_all": True, "extended": True}
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(scenarios):
            # 选择了测试场景
            scenario = scenarios[choice_num - 1]
            
            # 询问要使用的模型
            print(f"\n已选择场景: {scenario['scenario']}")
            print("请选择要测试的模型:")
            for i, model in enumerate(models, 1):
                print(f"  {i}. {model['model_id']}")
            print("  0. 使用所有模型")
            
            model_choice = input("请选择模型 (输入数字): ")
            model_choice = int(model_choice.strip())
            
            if model_choice == 0:
                return {"scenario": scenario, "model": None}
            elif 1 <= model_choice <= len(models):
                return {"scenario": scenario, "model": models[model_choice - 1]}
            else:
                print("无效的模型选择，使用所有模型")
                return {"scenario": scenario, "model": None}
        else:
            print("无效的选择，运行所有标准测试")
            return {"run_all": True, "extended": False}
    except ValueError:
        print("无效的选择，运行所有标准测试")
        return {"run_all": True, "extended": False}

def run_selected_tests(selection: Dict[str, Any], output_dir: str):
    """运行选择的测试"""
    runner = BoundaryTestRunner(output_dir=output_dir)
    
    if selection.get("run_all", False):
        # 运行所有测试
        extended = selection.get("extended", False)
        if extended:
            logger.info("运行所有测试场景 (标准+扩展)")
            # 注意：原始BoundaryTestRunner只运行BOUNDARY_TEST_MATRIX中的场景
            # 这里我们需要手动运行扩展场景
            
            # 先运行标准测试
            results = runner.run_all_tests()
            
            # 然后运行扩展测试
            for scenario in EXTENDED_BOUNDARY_TESTS:
                for model_config in MODEL_CONFIGS:
                    logger.info(f"运行扩展测试: {scenario['scenario']}, 模型: {model_config['model_id']}")
                    result = runner.run_boundary_test(scenario, model_config)
                    runner.results["tests"].append(result)
                    
                    # 更新统计
                    runner.results["summary"]["total_tests"] += 1
                    if result["passed"]:
                        runner.results["summary"]["passed_tests"] += 1
                        
                    # 记录场景和模型
                    if scenario["scenario"] not in runner.results["summary"]["scenarios_tested"]:
                        runner.results["summary"]["scenarios_tested"].append(scenario["scenario"])
                    
                    # 保存结果
                    runner._save_results()
            
            # 更新失败测试数
            runner.results["summary"]["failed_tests"] = (
                runner.results["summary"]["total_tests"] - runner.results["summary"]["passed_tests"]
            )
            
            # 更新通过率
            total = runner.results["summary"]["total_tests"]
            runner.results["summary"]["pass_rate"] = (
                runner.results["summary"]["passed_tests"] / total if total > 0 else 0
            )
            
            # 保存最终结果
            runner._save_results()
            
        else:
            logger.info("运行所有标准测试场景")
            results = runner.run_all_tests()
            
        # 打印汇总结果
        summary = runner.results["summary"]
        logger.info("=" * 50)
        logger.info("边界条件测试完成")
        logger.info(f"总测试数: {summary['total_tests']}")
        logger.info(f"通过测试数: {summary['passed_tests']}")
        logger.info(f"失败测试数: {summary['failed_tests']}")
        logger.info(f"通过率: {summary['pass_rate']*100:.1f}%")
        logger.info("测试场景: " + ", ".join(summary['scenarios_tested']))
        logger.info("=" * 50)
        
    else:
        # 运行特定测试
        scenario = selection.get("scenario")
        model = selection.get("model")
        
        if scenario and model:
            # 运行单个测试
            logger.info(f"运行特定测试: {scenario['scenario']}, 模型: {model['model_id']}")
            result = runner.run_boundary_test(scenario, model)
            logger.info(f"测试结果: {'通过' if result['passed'] else '失败'}")
            
            # 显示详细结果
            print("\n测试详情:")
            for test_result in result["tests"]:
                status = "通过" if test_result["passed"] else "失败"
                print(f"  - {test_result['test_name']}: {status}")
                
                if test_result["test_name"] == "emergency_release_time" and test_result.get("response_time"):
                    print(f"    响应时间: {test_result['response_time']:.2f}秒 (阈值: {test_result['threshold']}秒)")
                    
                if test_result["test_name"] == "oom_trigger":
                    print(f"    OOM触发: {'是' if test_result['oom_triggered'] else '否'}")
                    
                if test_result["test_name"] == "function_degradation":
                    print(f"    建议量化级别: {test_result['recommended_quant']}")
                    print(f"    决策时间: {test_result['decision_time']:.4f}秒")
                    
        elif scenario:
            # 对所有模型运行特定场景
            logger.info(f"对所有模型运行测试场景: {scenario['scenario']}")
            
            all_passed = True
            for model_config in MODEL_CONFIGS:
                result = runner.run_boundary_test(scenario, model_config)
                if not result["passed"]:
                    all_passed = False
                logger.info(f"  模型 {model_config['model_id']}: {'通过' if result['passed'] else '失败'}")
                
            logger.info(f"场景测试总结: {'全部通过' if all_passed else '部分失败'}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行边界条件测试")
    parser.add_argument("--output-dir", type=str, default="tests/results/boundary",
                      help="测试结果输出目录")
    parser.add_argument("--all", action="store_true", help="运行所有标准测试")
    parser.add_argument("--extended", action="store_true", help="运行所有测试(标准+扩展)")
    parser.add_argument("--scenario", type=str, help="指定测试场景名称")
    parser.add_argument("--model", type=str, help="指定模型ID")
    parser.add_argument("--interactive", action="store_true", help="使用交互式菜单")
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.interactive:
        # 交互式模式
        choice = display_menu()
        all_scenarios = BOUNDARY_TEST_MATRIX + EXTENDED_BOUNDARY_TESTS
        selection = parse_choice(choice, all_scenarios, MODEL_CONFIGS)
        run_selected_tests(selection, args.output_dir)
        
    elif args.all or args.extended:
        # 运行所有测试
        selection = {"run_all": True, "extended": args.extended}
        run_selected_tests(selection, args.output_dir)
        
    elif args.scenario:
        # 运行特定场景
        
        # 查找指定场景
        selected_scenario = None
        all_scenarios = BOUNDARY_TEST_MATRIX + EXTENDED_BOUNDARY_TESTS
        
        for scenario in all_scenarios:
            if scenario["scenario"] == args.scenario:
                selected_scenario = scenario
                break
                
        if not selected_scenario:
            logger.error(f"未找到指定场景: {args.scenario}")
            print("可用场景:")
            for scenario in all_scenarios:
                print(f"  - {scenario['scenario']}")
            return
            
        # 处理模型选择
        selected_model = None
        if args.model:
            for model in MODEL_CONFIGS:
                if model["model_id"] == args.model:
                    selected_model = model
                    break
                    
            if not selected_model:
                logger.error(f"未找到指定模型: {args.model}")
                print("可用模型:")
                for model in MODEL_CONFIGS:
                    print(f"  - {model['model_id']}")
                return
                
        # 运行测试
        selection = {"scenario": selected_scenario, "model": selected_model}
        run_selected_tests(selection, args.output_dir)
        
    else:
        # 显示菜单
        choice = display_menu()
        all_scenarios = BOUNDARY_TEST_MATRIX + EXTENDED_BOUNDARY_TESTS
        selection = parse_choice(choice, all_scenarios, MODEL_CONFIGS)
        run_selected_tests(selection, args.output_dir)

if __name__ == "__main__":
    main() 