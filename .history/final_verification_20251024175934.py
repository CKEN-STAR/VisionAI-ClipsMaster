#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终验证脚本
验证所有功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.training.model_version_manager import ModelVersionManager
from src.training.model_fine_tuner import ModelFineTuner

def final_verification():
    """最终验证"""
    print("=" * 70)
    print("最终验证 - 确保所有功能正常")
    print("=" * 70)
    
    all_passed = True
    
    # 验证1：ModelVersionManager 可以正常初始化
    print("\n验证1：ModelVersionManager 初始化...")
    try:
        version_manager = ModelVersionManager(base_dir="models/qwen", max_versions=5)
        print("   ✅ 初始化成功")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        all_passed = False
        return all_passed
    
    # 验证2：引用模式注册功能
    print("\n验证2：引用模式注册功能...")
    try:
        finetuned_path = "models/qwen/finetuned"
        if not Path(finetuned_path).exists():
            print(f"   ⚠️ 跳过（微调模型不存在）")
        else:
            training_info = {
                "training_type": "VERIFICATION_TEST",
                "dataset_size": 1,
                "training_args": {"num_epochs": 1}
            }
            
            version_id = version_manager.register_new_version(
                model_path=finetuned_path,
                gguf_path=None,
                training_info=training_info,
                copy_files=False  # 引用模式
            )
            
            if version_id:
                print(f"   ✅ 注册成功: {version_id}")
                
                # 验证路径
                version_info = version_manager.get_version_info(version_id)
                if 'finetuned' in version_info.get('hf_path', ''):
                    print("   ✅ 路径正确（finetuned目录）")
                else:
                    print("   ❌ 路径错误")
                    all_passed = False
                
                # 验证复制模式
                if version_info.get('copy_mode') == 'reference':
                    print("   ✅ 复制模式正确（reference）")
                else:
                    print("   ❌ 复制模式错误")
                    all_passed = False
                
                # 验证没有复制文件
                trained_dir = Path("models/qwen/trained")
                if trained_dir.exists():
                    subdirs = [d for d in trained_dir.glob("v*") if d.is_dir()]
                    if len(subdirs) > 0:
                        print(f"   ❌ 发现{len(subdirs)}个版本目录（不应该存在）")
                        all_passed = False
                    else:
                        print("   ✅ 没有复制文件")
                else:
                    print("   ✅ 没有复制文件")
                
                # 清理测试版本
                version_manager.versions["versions"] = []
                version_manager.versions["active_version"] = None
                version_manager._save_versions()
            else:
                print("   ❌ 注册失败")
                all_passed = False
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        all_passed = False
    
    # 验证3：ModelFineTuner 可以正常初始化
    print("\n验证3：ModelFineTuner 初始化...")
    try:
        fine_tuner = ModelFineTuner()
        print("   ✅ 初始化成功")
        
        # 验证版本管理器已初始化
        if hasattr(fine_tuner, 'version_managers'):
            if 'zh' in fine_tuner.version_managers and 'en' in fine_tuner.version_managers:
                print("   ✅ 版本管理器已初始化（zh, en）")
            else:
                print("   ⚠️ 版本管理器初始化不完整")
        else:
            print("   ⚠️ 版本管理器未初始化")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        all_passed = False
    
    # 验证4：原始模型文件完整性
    print("\n验证4：原始模型文件完整性...")
    try:
        finetuned_path = Path("models/qwen/finetuned")
        if finetuned_path.exists():
            required_files = [
                "adapter_model.safetensors",
                "adapter_config.json",
                "tokenizer.json"
            ]
            
            missing_files = []
            for file_name in required_files:
                if not (finetuned_path / file_name).exists():
                    missing_files.append(file_name)
            
            if len(missing_files) == 0:
                print("   ✅ 所有必需文件都存在")
            else:
                print(f"   ❌ 缺少文件: {', '.join(missing_files)}")
                all_passed = False
        else:
            print("   ⚠️ 跳过（微调模型不存在）")
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        all_passed = False
    
    # 验证5：没有遗留的测试文件
    print("\n验证5：检查遗留文件...")
    try:
        test_files = list(Path(".").glob("test_*.py"))
        temp_files = list(Path(".").glob("*.tmp")) + list(Path(".").glob("*.temp"))
        
        if len(test_files) == 0 and len(temp_files) == 0:
            print("   ✅ 没有遗留的测试文件")
        else:
            print(f"   ⚠️ 发现遗留文件:")
            for f in test_files + temp_files:
                print(f"     - {f.name}")
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    # 验证6：代码语法检查
    print("\n验证6：代码语法检查...")
    try:
        import py_compile
        files_to_check = [
            "src/training/model_version_manager.py",
            "src/training/model_fine_tuner.py"
        ]
        
        syntax_errors = []
        for file_path in files_to_check:
            try:
                py_compile.compile(file_path, doraise=True)
            except py_compile.PyCompileError as e:
                syntax_errors.append(f"{file_path}: {e}")
        
        if len(syntax_errors) == 0:
            print("   ✅ 所有文件语法正确")
        else:
            print("   ❌ 发现语法错误:")
            for error in syntax_errors:
                print(f"     - {error}")
            all_passed = False
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        all_passed = False
    
    # 最终结果
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有验证通过！系统正常工作！")
        print("\n下一步：")
        print("1. 运行 python simple_ui_fixed.py 启动UI")
        print('2. 切换到"设置" → "模型管理" → "中文模型 (Qwen)"')
        print('3. 点击"刷新"按钮')
        print("4. 在UI中进行模型训练，验证版本注册功能")
    else:
        print("❌ 部分验证失败，请检查上述错误")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    success = final_verification()
    sys.exit(0 if success else 1)

