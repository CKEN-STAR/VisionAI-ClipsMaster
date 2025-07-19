#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全审计追踪演示脚本

展示如何使用安全审计功能记录敏感操作、模型参数调整和日志查看等行为。
"""

import os
import sys
import time
import json
import datetime
from pathlib import Path

# 确保能够正确导入项目模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 导入审计追踪模块
from src.dashboard.audit_trail import (
    AuditTrail, AuditLevel, AuditCategory,
    get_audit_trail, log_view_action, log_data_access,
    log_model_operation, log_parameter_change, audit_log
)

def print_section(title):
    """打印分隔标题"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, '-'))
    print("="*80)

# 设置一个模拟用户
class MockUser:
    """模拟用户"""
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

# 创建模拟用户
admin_user = MockUser(1, "admin", "administrator")
normal_user = MockUser(2, "user", "standard")

def demo_basic_logging():
    """演示基本日志记录功能"""
    print_section("基本审计日志记录")
    
    # 获取审计追踪实例
    audit = get_audit_trail()
    
    # 使用便捷函数记录查看操作
    print("记录查看操作...")
    log_view_action(admin_user, "view_dashboard")
    
    # 记录数据访问
    print("记录数据访问...")
    log_data_access(
        admin_user, 
        data_type="subtitle", 
        resource_id="subtitle_12345", 
        operation="download"
    )
    
    # 记录模型操作
    print("记录模型操作...")
    model_params = {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 1024
    }
    log_model_operation(
        admin_user,
        model_name="qwen2.5-7b-zh",
        operation="inference",
        parameters=model_params
    )
    
    # 记录参数变更
    print("记录参数变更...")
    log_parameter_change(
        admin_user,
        param_name="temperature",
        old_value=0.7,
        new_value=0.8,
        component="text_generation"
    )
    
    print("基本日志记录完成。")

# 使用装饰器记录敏感操作
@audit_log(category=AuditCategory.DATA_ACCESS, level=AuditLevel.HIGH)
def sensitive_data_operation(user, data_id):
    """模拟敏感数据操作"""
    print(f"用户 {user.username} 正在访问敏感数据 {data_id}")
    # 模拟处理
    time.sleep(1)
    return {"status": "success", "data_id": data_id}

@audit_log(category=AuditCategory.MODEL_OPERATION, level=AuditLevel.MEDIUM)
def adjust_model_parameters(user, model_name, **parameters):
    """模拟调整模型参数"""
    print(f"用户 {user.username} 正在调整模型 {model_name} 的参数")
    # 模拟参数调整
    time.sleep(0.5)
    return {"status": "success", "model": model_name, "parameters": parameters}

def demo_decorator_logging():
    """演示使用装饰器记录日志"""
    print_section("使用装饰器记录审计日志")
    
    # 调用带有装饰器的函数
    print("执行敏感数据操作...")
    result1 = sensitive_data_operation(admin_user, "classified_data_456")
    print(f"操作结果: {result1}")
    
    print("\n执行模型参数调整...")
    result2 = adjust_model_parameters(
        admin_user, 
        "qwen2.5-7b-zh", 
        temperature=0.9, 
        top_p=0.95, 
        repetition_penalty=1.2
    )
    print(f"操作结果: {result2}")
    
    # 模拟错误情况
    try:
        print("\n触发异常操作...")
        adjust_model_parameters(normal_user, "unknown_model")
    except Exception as e:
        print(f"预期的异常: {e}")
    
    print("装饰器日志记录演示完成。")

def demo_log_reading():
    """演示读取审计日志"""
    print_section("读取审计日志")
    
    # 获取审计追踪实例
    audit = get_audit_trail()
    
    # 导出日志（模拟功能）
    print("尝试导出今天的审计日志...")
    today = datetime.datetime.today()
    
    try:
        # 导出日志
        output_file = os.path.join(project_root, "logs", "demo_audit_export.json")
        success = audit.export_logs(
            output_file=output_file,
            start_date=today,
            end_date=today
        )
        
        if success:
            print(f"日志已成功导出到 {output_file}")
            
            # 读取导出的文件
            log_file = audit.current_log_file
            print(f"\n当前审计日志文件: {log_file}")
            
            if os.path.exists(log_file):
                print("\n读取最近的5条日志记录:")
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[-5:]):
                        # 解析JSON
                        try:
                            record = json.loads(line)
                            # 简化输出
                            simplified = {
                                "id": record.get("id", "未知ID"),
                                "timestamp": record.get("timestamp", "未知时间"),
                                "action": record.get("action", "未知操作"),
                                "user": record.get("user", "未知用户")
                            }
                            print(f"{i+1}. {json.dumps(simplified, ensure_ascii=False)}")
                        except json.JSONDecodeError:
                            print(f"{i+1}. 无法解析: {line[:50]}...")
            else:
                print(f"警告: 找不到日志文件 {log_file}")
        else:
            print("导出日志失败")
    except Exception as e:
        print(f"读取日志时出错: {e}")
    
    print("审计日志读取演示完成。")

def demo_sensitive_access():
    """演示敏感数据访问记录"""
    print_section("敏感数据访问记录")
    
    # 模拟核心算法访问
    print("记录核心算法访问...")
    log_data_access(
        admin_user,
        data_type="algorithm",
        resource_id="core_script_generation_algorithm",
        operation="view",
        extra_details={
            "algorithm_version": "2.5.0",
            "access_reason": "performance_tuning"
        }
    )
    
    # 模拟预测模型参数调整
    print("记录模型参数调整...")
    old_params = {
        "temperature": 0.7,
        "top_p": 0.9,
        "repetition_penalty": 1.1,
        "max_tokens": 2048
    }
    
    new_params = {
        "temperature": 0.8,
        "top_p": 0.92,
        "repetition_penalty": 1.2,
        "max_tokens": 4096
    }
    
    # 记录每个参数的变化
    for param, old_value in old_params.items():
        new_value = new_params.get(param)
        if new_value != old_value:
            print(f"参数变更: {param} = {old_value} -> {new_value}")
            log_parameter_change(
                admin_user,
                param_name=param,
                old_value=old_value,
                new_value=new_value,
                component="qwen2.5-7b-zh"
            )
    
    # 记录原始日志查看
    print("记录日志查看操作...")
    log_view_action(admin_user, "view_system_logs")
    
    print("敏感数据访问记录演示完成。")

def main():
    """主演示函数"""
    print("\n欢迎使用VisionAI-ClipsMaster安全审计追踪演示！")
    
    # 运行所有演示
    demo_basic_logging()
    demo_decorator_logging()
    demo_sensitive_access()
    demo_log_reading()
    
    print("\n\n演示完成！所有审计日志已记录到系统。")
    print(f"日志路径: {get_audit_trail().log_dir}")

if __name__ == "__main__":
    main() 