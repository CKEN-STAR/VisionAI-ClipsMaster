#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
隐私安全适配器演示脚本

展示VisionAI-ClipsMaster项目的隐私保护、数据匿名化和同意管理功能。
"""

import os
import sys
import json
from pprint import pprint
import time
from datetime import datetime
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

print("开始隐私安全适配器演示脚本...")

# 替换真实模块为模拟模块
import src.audience.privacy_guard_mock as mock
sys.modules['src.data.storage_manager'] = mock
sys.modules['src.utils.privacy_manager'] = mock
sys.modules['src.core.privacy_manager'] = mock

try:
    from src.audience.privacy_guard import (
        get_privacy_adapter, anonymize_data, enforce_consent, 
        check_consent, record_consent, ConsentRequiredError
    )
    print("成功导入隐私安全适配器模块")
except Exception as e:
    print(f"导入隐私安全适配器模块时出错: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def demonstrate_privacy_features():
    """演示隐私保护功能"""
    print_section("隐私安全适配器演示")
    
    # 获取隐私适配器
    print("正在获取隐私适配器...")
    try:
        privacy_adapter = get_privacy_adapter()
        print("成功获取隐私适配器")
    except Exception as e:
        print(f"获取隐私适配器时发生错误: {str(e)}")
        traceback.print_exc()
        return
    
    # 设置测试用户ID
    test_user_id = "demo_user_789"
    
    # 演示数据
    sample_user_data = {
        "user_id": test_user_id,
        "name": "张三",
        "age": 28,
        "gender": "male",
        "email": "zhangsan@example.com",
        "phone": "13912345678",
        "location": {
            "latitude": 39.9042,
            "longitude": 116.4074,
            "address": "北京市海淀区中关村南大街5号"
        },
        "preferences": {
            "comedy": 0.85,
            "action": 0.75,
            "drama": 0.45,
            "sci-fi": 0.92,
            "horror": 0.15
        },
        "device_info": {
            "device_id": "ABC123XYZ",
            "platform": "iOS",
            "version": "15.4",
            "language": "zh-CN"
        }
    }
    
    # 演示1：数据匿名化
    print_section("1. 数据匿名化")
    print("\n原始用户数据:")
    pprint(sample_user_data, width=100)
    
    print("\n匿名化处理后的数据:")
    try:
        anonymized_data = anonymize_data(sample_user_data)
        pprint(anonymized_data, width=100)
    except Exception as e:
        print(f"数据匿名化过程中发生错误: {str(e)}")
        traceback.print_exc()
    
    print("\n注意事项:")
    print("- 敏感字段(email, phone)已被移除")
    print("- 年龄数据已添加随机噪声进行模糊化")
    print("- 性别数据有一定概率被替换为'unknown'")
    print("- 位置信息已被降低精度")
    print("- 偏好分数已添加随机噪声")
    
    # 演示2：用户同意管理
    print_section("2. 用户同意管理")
    
    # 查看当前用户的同意状态
    print("\n用户当前同意状态:")
    try:
        all_consents = privacy_adapter.get_all_consents(test_user_id)
        if all_consents:
            pprint(all_consents, width=100)
        else:
            print("用户尚未提供任何同意")
    except Exception as e:
        print(f"获取用户同意状态时发生错误: {str(e)}")
        traceback.print_exc()
    
    # 记录用户同意
    print("\n记录用户同意 - 偏好追踪...")
    try:
        metadata = {
            "ip_address": "192.168.1.100",
            "user_agent": "Demo Browser/1.0",
            "version": "1.2"
        }
        result = record_consent(test_user_id, "preference_tracking", "granted", metadata)
        print(f"记录结果: {'成功' if result else '失败'}")
    except Exception as e:
        print(f"记录用户同意时发生错误: {str(e)}")
        traceback.print_exc()
    
    print("\n记录用户拒绝 - 数据共享...")
    try:
        result = record_consent(test_user_id, "data_sharing", "denied", metadata)
        print(f"记录结果: {'成功' if result else '失败'}")
    except Exception as e:
        print(f"记录用户拒绝时发生错误: {str(e)}")
        traceback.print_exc()
    
    # 再次查看用户同意状态
    print("\n更新后的用户同意状态:")
    try:
        updated_consents = privacy_adapter.get_all_consents(test_user_id)
        pprint(updated_consents, width=100)
    except Exception as e:
        print(f"获取更新后的用户同意状态时发生错误: {str(e)}")
        traceback.print_exc()
    
    # 演示3：同意强制执行
    print_section("3. 同意强制执行")
    
    print("\n尝试访问已同意功能 - 偏好追踪:")
    try:
        if enforce_consent(test_user_id, "preference_tracking"):
            print("✓ 用户已同意，允许访问偏好追踪功能")
    except ConsentRequiredError as e:
        print(f"✗ 拒绝访问: {str(e)}")
    except Exception as e:
        print(f"验证用户同意时发生错误: {str(e)}")
        traceback.print_exc()
    
    print("\n尝试访问未同意功能 - 数据共享:")
    try:
        if enforce_consent(test_user_id, "data_sharing"):
            print("✓ 用户已同意，允许访问数据共享功能")
    except ConsentRequiredError as e:
        print(f"✗ 拒绝访问: {str(e)}")
    except Exception as e:
        print(f"验证用户同意时发生错误: {str(e)}")
        traceback.print_exc()
    
    print("\n尝试访问尚未有记录的功能 - 跨平台整合:")
    try:
        if enforce_consent(test_user_id, "cross_platform_integration"):
            print("✓ 用户已同意，允许访问跨平台整合功能")
    except ConsentRequiredError as e:
        print(f"✗ 拒绝访问: {str(e)}")
    except Exception as e:
        print(f"验证用户同意时发生错误: {str(e)}")
        traceback.print_exc()
    
    # 演示4：敏感数据检测和编辑
    print_section("4. 敏感数据检测和编辑")
    
    print("\n检测数据中的敏感信息:")
    try:
        sensitive_data = privacy_adapter.detect_sensitive_data(sample_user_data)
        pprint(sensitive_data, width=100)
    except Exception as e:
        print(f"检测敏感数据时发生错误: {str(e)}")
        traceback.print_exc()
    
    print("\n编辑数据中的敏感信息:")
    try:
        redacted_data = privacy_adapter.redact_sensitive_data(sample_user_data)
        pprint(redacted_data, width=100)
    except Exception as e:
        print(f"编辑敏感数据时发生错误: {str(e)}")
        traceback.print_exc()
    
    # 演示5：数据保留策略
    print_section("5. 数据保留策略")
    
    print("\n数据保留期限配置:")
    for data_type, days in privacy_adapter.retention_periods.items():
        print(f"- {data_type}: {days}天")
    
    print("\n应用数据保留策略:")
    try:
        retention_result = privacy_adapter.apply_data_retention(test_user_id)
        pprint(retention_result, width=100)
    except Exception as e:
        print(f"应用数据保留策略时发生错误: {str(e)}")
        traceback.print_exc()
    
    print("\n演示完成！")

if __name__ == "__main__":
    try:
        demonstrate_privacy_features()
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        traceback.print_exc() 